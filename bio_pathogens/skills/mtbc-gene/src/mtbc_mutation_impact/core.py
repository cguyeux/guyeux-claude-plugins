"""Compare ESM Atlas per-residue SAE activations between WT and mutant at the
position of a point mutation.

The Atlas returns `per_residue_activations` as a sparse COO tensor:
    {"indices": [[rows...], [cols...]], "values": [floats...], "shape": [L, F]}

This module:
1. Resolves the gene → protein via mtbc_gene_function.
2. Validates the mutation against the WT sequence.
3. Looks up WT then MT in the Atlas (cache-backed).
4. Extracts the activation rows at position N-1 from each.
5. Aligns by feature index and classifies into gained / lost / amplified
   / attenuated buckets.
6. Resolves feature labels for the most-changed features.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from esm_atlas_cli import EsmAtlasClient, EsmAtlasError, hash_sequence
from mtbc_gene_function import annotate_gene, extract_cds, translate_cds


MUT_RE = re.compile(r"^([A-Z])(\d+)([A-Z])$")
AMP_FACTOR = 2.0  # |MT| > AMP_FACTOR * |WT|  → "amplified"
ATT_FACTOR = 0.5  # |MT| < ATT_FACTOR * |WT|  → "attenuated"
SMALL_EPS = 1e-6


class MutationError(Exception):
    """Raised when the mutation string is malformed or inconsistent with the WT."""


@dataclass
class ImpactReport:
    gene: str | None
    locus_tag: str | None
    product: str | None
    mutation: str
    ref: str
    pos: int
    alt: str
    wt_hash: str
    mt_hash: str
    wt_vector: list[dict] = field(default_factory=list)
    mt_vector: list[dict] = field(default_factory=list)
    gained: list[dict] = field(default_factory=list)
    lost: list[dict] = field(default_factory=list)
    amplified: list[dict] = field(default_factory=list)
    attenuated: list[dict] = field(default_factory=list)
    paragraph: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _parse_mutation(s: str) -> tuple[str, int, str]:
    m = MUT_RE.match(s.strip())
    if not m:
        raise MutationError(f"Bad mutation {s!r}; expected e.g. S315T")
    return m.group(1), int(m.group(2)), m.group(3)


def _row_at(per_residue: dict, pos_zero: int) -> dict[int, float]:
    """Extract feature_index → activation map for one residue row."""
    indices = per_residue.get("indices") or []
    values = per_residue.get("values") or []
    if not indices or not values:
        return {}
    rows, cols = indices[0], indices[1]
    out: dict[int, float] = {}
    for i, r in enumerate(rows):
        if r == pos_zero:
            out[cols[i]] = float(values[i])
    return out


def _classify(wt_row: dict[int, float], mt_row: dict[int, float]) -> dict[str, list[tuple[int, float, float]]]:
    """Return four buckets : gained, lost, amplified, attenuated.

    Each entry is `(feature_index, wt_activation, mt_activation)`.
    """
    all_idx = sorted(set(wt_row) | set(mt_row))
    gained, lost, amplified, attenuated = [], [], [], []
    for idx in all_idx:
        w = wt_row.get(idx, 0.0)
        m = mt_row.get(idx, 0.0)
        if abs(w) < SMALL_EPS and abs(m) >= SMALL_EPS:
            gained.append((idx, w, m))
        elif abs(m) < SMALL_EPS and abs(w) >= SMALL_EPS:
            lost.append((idx, w, m))
        elif abs(w) >= SMALL_EPS and abs(m) >= SMALL_EPS:
            ratio = abs(m) / abs(w)
            if ratio >= AMP_FACTOR:
                amplified.append((idx, w, m))
            elif ratio <= ATT_FACTOR:
                attenuated.append((idx, w, m))
    return {"gained": gained, "lost": lost, "amplified": amplified, "attenuated": attenuated}


def _hydrate_with_labels(client: EsmAtlasClient, entries: list[tuple[int, float, float]],
                         max_labels: int = 5) -> list[dict]:
    """Attach a label to the top entries (those with the largest |MT|-|WT|)."""
    ordered = sorted(entries, key=lambda e: abs(e[2]) - abs(e[1]), reverse=True)
    out: list[dict] = []
    for i, (idx, w, m) in enumerate(ordered):
        item = {"index": idx, "wt_activation": w, "mt_activation": m, "label": None}
        if i < max_labels:
            try:
                meta = client.feature_meta(idx)
                item["label"] = meta.get("label") or meta.get("description")
            except EsmAtlasError:
                pass
        out.append(item)
    return out


def _paragraph(report: ImpactReport) -> str:
    gene = report.gene or report.locus_tag
    head = f"{gene} {report.mutation} ({report.product or 'unknown product'})."
    counts = (
        f" Local ESM SAE diff at residue {report.pos}: "
        f"{len(report.gained)} gained, {len(report.lost)} lost, "
        f"{len(report.amplified)} amplified, {len(report.attenuated)} attenuated."
    )
    most = sorted(
        report.gained + report.amplified,
        key=lambda f: (f.get("mt_activation") or 0) - (f.get("wt_activation") or 0),
        reverse=True,
    )[:3]
    tail = ""
    if most:
        labels = [m.get("label") for m in most if m.get("label")]
        if labels:
            tail = " Most increased features at this position: " + "; ".join(labels) + "."
    return head + counts + tail + " Interpretation is hypothesis-generating, not diagnostic."


def impact_of(gene_or_locus: str, mutation: str,
              *, client: EsmAtlasClient | None = None,
              max_labels: int = 5) -> ImpactReport:
    """End-to-end ESM impact estimation for one point mutation."""
    ref, pos, alt = _parse_mutation(mutation)
    if ref == alt:
        raise MutationError("Reference and alternate residues are identical")

    ann = annotate_gene(gene_or_locus, topk_features=5, client=client)
    dna, _ = extract_cds(gene_or_locus)
    wt_protein, _ = translate_cds(dna)
    if not (1 <= pos <= len(wt_protein)):
        raise MutationError(f"Position {pos} out of range for {gene_or_locus} (length {len(wt_protein)})")
    actual_ref = wt_protein[pos - 1]
    if actual_ref != ref:
        raise MutationError(
            f"Residue at position {pos} is {actual_ref!r}, not {ref!r}; mutation {mutation} invalid"
        )

    mt_protein = wt_protein[: pos - 1] + alt + wt_protein[pos:]

    own_client = client is None
    cli = client or EsmAtlasClient()
    try:
        wt = cli.lookup_sequence(wt_protein, topk_features=5)
        mt = cli.lookup_sequence(mt_protein, topk_features=5)
    finally:
        if own_client:
            # do not close; we still need it to hydrate labels below
            pass

    wt_pra = wt.get("per_residue_activations") or {}
    mt_pra = mt.get("per_residue_activations") or {}
    wt_row = _row_at(wt_pra, pos - 1)
    mt_row = _row_at(mt_pra, pos - 1)

    buckets = _classify(wt_row, mt_row)

    cli2 = client or EsmAtlasClient()
    try:
        report = ImpactReport(
            gene=ann.gene,
            locus_tag=ann.locus_tag,
            product=ann.product,
            mutation=mutation,
            ref=ref, pos=pos, alt=alt,
            wt_hash=hash_sequence(wt_protein),
            mt_hash=hash_sequence(mt_protein),
            wt_vector=[{"index": k, "activation": v} for k, v in sorted(wt_row.items())],
            mt_vector=[{"index": k, "activation": v} for k, v in sorted(mt_row.items())],
            gained=_hydrate_with_labels(cli2, buckets["gained"], max_labels=max_labels),
            lost=_hydrate_with_labels(cli2, buckets["lost"], max_labels=max_labels),
            amplified=_hydrate_with_labels(cli2, buckets["amplified"], max_labels=max_labels),
            attenuated=_hydrate_with_labels(cli2, buckets["attenuated"], max_labels=max_labels),
        )
        report.paragraph = _paragraph(report)
        return report
    finally:
        if own_client:
            cli2.close()
