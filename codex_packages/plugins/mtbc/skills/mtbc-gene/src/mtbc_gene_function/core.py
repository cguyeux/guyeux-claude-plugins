"""H37Rv gene → ESM Atlas functional annotation.

Resolves a gene name (`katG`) or locus tag (`Rv1908c`) against the H37Rv CDS
fasta bundled in the Guyeux group MTBC pipeline, translates the CDS using the
bacterial translation table (table 11, with GTG/TTG initiator → M), then calls
the `esm-atlas-cli` client to fetch the SAE features. Falls back gracefully
when ESM Atlas is unavailable: still returns the H37Rv-side annotation alone.
"""
from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .local import LocalAnnotation, LocalAnnotationUnavailable


def _esm():
    """Lazy import of the esm-atlas-cli client (OPTIONAL: the skill answers from the
    curated annotation_mtbc source first and only enriches with ESM Atlas if present)."""
    from esm_atlas_cli import (
        EsmAtlasClient, EsmAtlasError, EsmAtlasUnavailable, hash_sequence,
    )
    return EsmAtlasClient, EsmAtlasError, EsmAtlasUnavailable, hash_sequence


DEFAULT_CDS_FASTA = Path(
    os.environ.get(
        "MTBC_H37RV_CDS_FASTA",
        "~/docs/codes/mtbc/en_cours/investigate_phylo/resources/NC_000962.3_CDS.fasta",
    )
).expanduser()


# Standard genetic code (NCBI table 11 = bacterial; identical to table 1 in the
# body of the gene; only difference is alternative initiator codons → M).
CODON_TABLE = {
    "TTT": "F", "TTC": "F", "TTA": "L", "TTG": "L",
    "CTT": "L", "CTC": "L", "CTA": "L", "CTG": "L",
    "ATT": "I", "ATC": "I", "ATA": "I", "ATG": "M",
    "GTT": "V", "GTC": "V", "GTA": "V", "GTG": "V",
    "TCT": "S", "TCC": "S", "TCA": "S", "TCG": "S",
    "CCT": "P", "CCC": "P", "CCA": "P", "CCG": "P",
    "ACT": "T", "ACC": "T", "ACA": "T", "ACG": "T",
    "GCT": "A", "GCC": "A", "GCA": "A", "GCG": "A",
    "TAT": "Y", "TAC": "Y", "TAA": "*", "TAG": "*",
    "CAT": "H", "CAC": "H", "CAA": "Q", "CAG": "Q",
    "AAT": "N", "AAC": "N", "AAA": "K", "AAG": "K",
    "GAT": "D", "GAC": "D", "GAA": "E", "GAG": "E",
    "TGT": "C", "TGC": "C", "TGA": "*", "TGG": "W",
    "CGT": "R", "CGC": "R", "CGA": "R", "CGG": "R",
    "AGT": "S", "AGC": "S", "AGA": "R", "AGG": "R",
    "GGT": "G", "GGC": "G", "GGA": "G", "GGG": "G",
}


class GeneNotFound(Exception):
    """Raised when the gene name or locus tag is not in the H37Rv CDS fasta."""


@dataclass
class GeneAnnotation:
    gene: str | None
    locus_tag: str | None
    product: str | None
    protein_hash: str
    length_aa: int
    truncated: bool = False
    top_features: list[dict] = field(default_factory=list)
    cluster: dict | None = None
    function_summary: str = ""
    source: str = "annotation_mtbc (curated) + H37Rv NC_000962.3 + ESM Atlas (fallback)"
    esm_available: bool = True
    # curated annotation_mtbc channels (PRIMARY source)
    local_available: bool = False
    is_hypothetical: bool | None = None
    ec: list = field(default_factory=list)
    uniprot_function: str | None = None
    pfam: list = field(default_factory=list)
    string_partners: dict | None = None
    conservation: dict | None = None
    structural_candidate: dict | None = None
    evidence: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


_HEADER_FIELD_RE = re.compile(r"\[(\w+)=([^\]]+)\]")


def _parse_header_fields(header: str) -> dict[str, str]:
    """Parse `>lcl|... [gene=X] [locus_tag=Y] [protein=Z]` into a dict."""
    return {k: v.strip() for k, v in _HEADER_FIELD_RE.findall(header)}


def find_gene_header(query: str, cds_fasta: Path = DEFAULT_CDS_FASTA) -> tuple[str, dict[str, str]]:
    """Search the CDS fasta for the first header matching gene name or locus tag.

    Returns `(header_line, fields)` where `fields` is the parsed `[k=v]` dict.
    Raises GeneNotFound otherwise.
    """
    if not cds_fasta.exists():
        raise GeneNotFound(f"CDS fasta missing: {cds_fasta}")
    q = query.strip()
    q_lower = q.lower()
    with cds_fasta.open() as f:
        for line in f:
            if not line.startswith(">"):
                continue
            fields = _parse_header_fields(line)
            gene = (fields.get("gene") or "").lower()
            locus = (fields.get("locus_tag") or "").lower()
            if gene == q_lower or locus == q_lower:
                return line.strip(), fields
    raise GeneNotFound(f"{query!r} not found in {cds_fasta.name}")


def extract_cds(query: str, cds_fasta: Path = DEFAULT_CDS_FASTA) -> tuple[str, dict[str, str]]:
    """Return the DNA CDS string + parsed header fields for `query`."""
    target_header, fields = find_gene_header(query, cds_fasta)
    chunks: list[str] = []
    in_target = False
    with cds_fasta.open() as f:
        for line in f:
            if line.startswith(">"):
                if in_target:
                    break
                in_target = line.strip() == target_header
                continue
            if in_target:
                chunks.append(line.strip())
    return "".join(chunks).upper(), fields


def translate_cds(dna: str) -> tuple[str, bool]:
    """Translate a CDS string with table-11-style initiator handling.

    Returns `(protein, truncated)` where `truncated` is True if an internal
    stop codon was hit before the end of the CDS (pseudogene or frameshift).
    """
    dna = dna.upper().replace("U", "T")
    aa: list[str] = []
    if dna[:3] in {"GTG", "TTG"}:
        aa.append("M")
        i = 3
    else:
        i = 0
    full_codons = len(dna) // 3
    while i + 3 <= len(dna):
        codon = dna[i : i + 3]
        c = CODON_TABLE.get(codon, "X")
        if c == "*":
            truncated = (i // 3) < (full_codons - 1)
            return "".join(aa), truncated
        aa.append(c)
        i += 3
    return "".join(aa), False


def _summarise(a: GeneAnnotation) -> str:
    """Neutral function paragraph, led by the CURATED annotation_mtbc channels and
    only then enriched by ESM Atlas (the opposite priority to the legacy behaviour)."""
    parts: list[str] = []
    head = a.gene or a.locus_tag or "Unknown gene"
    if a.product:
        parts.append(f"{head} ({a.product}, {a.length_aa} aa).")
    else:
        parts.append(f"{head} ({a.length_aa} aa)" + (", hypothetical." if a.is_hypothetical else "."))

    # 1. curated UniProt function (the primary answer when present)
    if a.uniprot_function:
        fn = a.uniprot_function
        if len(fn) > 320:
            fn = fn[:317] + "..."
        ec = f" (EC {', '.join(a.ec)})" if a.ec else ""
        parts.append(f"UniProt{ec}: {fn}")

    # 2. Pfam domains
    if a.pfam:
        doms = "; ".join(d.get("pfam_name") or d.get("description") or "" for d in a.pfam[:3])
        if doms:
            parts.append(f"Pfam: {doms}.")

    # 3. conservation / selection across the project strains
    if a.conservation:
        sel = a.conservation.get("selection")
        pnps = a.conservation.get("pN_pS")
        n = a.conservation.get("n_strains")
        if sel:
            tail = f" (pN/pS={pnps})." if pnps is not None else "."
            parts.append(f"Across {n} strains: {sel}{tail}")
        if a.conservation.get("pseudogene_flag"):
            parts.append("Flagged as a possible pseudogene.")

    # 4. STRING partners (guilt-by-association)
    if a.string_partners and a.string_partners.get("n_partners"):
        parts.append(f"STRING: {a.string_partners['n_partners']} functional partners.")

    # 5. dark gene with a Foldseek structural lead
    if a.is_hypothetical and a.structural_candidate:
        sug = (a.structural_candidate.get("suggested") or "")[:120]
        if sug:
            parts.append(f"Dark gene; Foldseek structural match suggests: {sug}.")

    # 6. ESM Atlas (secondary enrichment)
    if a.esm_available and a.top_features:
        labels = [f.get("label") or f.get("description") or "" for f in a.top_features[:3]]
        labels = [s for s in labels if s]
        if labels:
            parts.append("ESM SAE: " + "; ".join(labels) + ".")

    if not a.local_available and not a.esm_available:
        parts.append("(no annotation_mtbc and no ESM Atlas; H37Rv catalogue only.)")
    return " ".join(parts)


def annotate_gene(query: str, *, topk_features: int = 10,
                  cds_fasta: Path | None = None,
                  client=None, annotation_dir: Path | None = None,
                  use_esm: bool = True) -> GeneAnnotation:
    """Annotate a gene, CURATED-source first: annotation_mtbc -> H37Rv catalogue ->
    ESM Atlas (enrichment / fallback). Works fully offline if ESM Atlas (or its client)
    is unavailable, and from annotation_mtbc alone if the CDS fasta is absent."""
    fasta = cds_fasta or DEFAULT_CDS_FASTA

    # ── sequence from the H37Rv CDS (for the ESM hash + product/length fallback) ──
    protein, truncated, fields = "", False, {}
    try:
        dna, fields = extract_cds(query, fasta)
        protein, truncated = translate_cds(dna)
    except GeneNotFound:
        pass  # CDS fasta may be missing; the curated source can still answer

    ann = GeneAnnotation(
        gene=fields.get("gene"),
        locus_tag=fields.get("locus_tag"),
        product=fields.get("protein"),
        protein_hash="",
        length_aa=len(protein),
        truncated=truncated,
    )

    # ── 1. PRIMARY: curated annotation_mtbc ──────────────────────────────────
    local = LocalAnnotation(annotation_dir)
    if local.available():
        try:
            rec = local.record(query)
            ann.local_available = True
            ann.locus_tag = ann.locus_tag or rec.rv
            ann.gene = ann.gene or rec.gene
            ann.is_hypothetical = rec.is_hypothetical
            ann.length_aa = ann.length_aa or (rec.length_aa or 0)
            ann.pfam = rec.pfam
            ann.string_partners = rec.string
            ann.conservation = rec.conservation
            ann.structural_candidate = rec.structural_candidate
            ann.evidence = list(rec.channels)
            if rec.uniprot:
                ann.uniprot_function = rec.uniprot.get("function")
                ann.ec = rec.uniprot.get("ec") or []
                if rec.uniprot.get("protein_name"):
                    ann.product = rec.uniprot["protein_name"]   # curated name beats CDS product
            if not ann.product:
                ann.product = rec.product or rec.product_pgap
        except LocalAnnotationUnavailable:
            pass

    # ── 2. SECONDARY: ESM Atlas (optional enrichment) ────────────────────────
    if use_esm and protein:
        try:
            EsmAtlasClient, EsmAtlasError, EsmAtlasUnavailable, hash_sequence = _esm()
        except Exception:
            ann.esm_available = False
        else:
            ann.protein_hash = hash_sequence(protein)
            own_client = client is None
            cli = client or EsmAtlasClient()
            try:
                data = cli.lookup(ann.protein_hash, topk_features=topk_features)
                features_raw = data.get("sae_features") or data.get("topk_features") or []
                ann.top_features = [
                    {"index": f.get("index") or f.get("feature_index"),
                     "activation": f.get("activation") or f.get("value"),
                     "label": f.get("label") or f.get("description")}
                    for f in features_raw
                ]
                rep_hash = data.get("cluster_rep_protein_hash")
                target = rep_hash or ann.protein_hash
                try:
                    cl = cli.cluster(target)
                    ann.cluster = {"size": cl.get("cluster_size") or cl.get("size"),
                                   "pct_characterized": cl.get("cluster_pct_characterized"),
                                   "rep_hash": target}
                except EsmAtlasError:
                    ann.cluster = None
            except (EsmAtlasUnavailable, EsmAtlasError):
                ann.esm_available = False
            finally:
                if own_client:
                    cli.close()
    else:
        ann.esm_available = False

    if not fields and not ann.local_available:
        raise GeneNotFound(
            f"{query!r} not found in the H37Rv CDS fasta or annotation_mtbc."
        )

    ann.function_summary = _summarise(ann)
    return ann
