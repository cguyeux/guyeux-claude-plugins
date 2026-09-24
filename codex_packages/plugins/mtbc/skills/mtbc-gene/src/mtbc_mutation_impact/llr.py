"""Validated variant-effect scoring with the ESM-1v protein language model.

WHY THIS MODULE EXISTS
----------------------
The ESM Atlas sparse-autoencoder (SAE) feature deltas returned by
``core.impact_of`` are an *interpretability lens*: they are dictionary
elements learned to reconstruct the model's internal representations, with no
validated mapping to the functional impact of a point mutation. Counting how
many SAE features "flip" at a mutated residue is therefore a hypothesis
generator, NOT a quantitative impact predictor, and must never be reported as
variant-effect evidence in a manuscript (lesson learned on the
rehumanisation_L6L9L10 study, 2026-05-30).

The validated, deep-mutational-scanning-calibrated approach is the ESM-1v
zero-shot score of Meier et al. 2021 (NeurIPS 34:29287): a masked-marginal
log-likelihood ratio at the mutated residue,

    LLR = log p(alt | masked context) - log p(wt | masked context)

LLR << 0  => substitution disfavoured by the language model (candidate
            damaging / loss-of-function).
LLR ~ 0   => tolerated drift.
LLR > 0   => substitution favoured over the wild-type residue.

A common heuristic threshold for "strongly disfavoured" is LLR < -7.5, but it
is not calibrated for bacterial proteins; prefer reporting the distribution and
flagging outliers rather than a hard call.

REQUIREMENTS
------------
``torch`` and ``fair-esm`` (``pip install fair-esm``). These are heavy and are
NOT declared as hard dependencies of this skill. If torch is broken inside a
fresh venv under recent Python, create the venv with
``python -m venv --system-site-packages`` so it inherits a working system torch,
then ``pip install fair-esm`` into it. The model weights (~2.6 GB for
esm1v_t33_650M_UR90S_1) download on first use to ``$TORCH_HOME``.

USAGE
-----
    from mtbc_mutation_impact.llr import load_model, llr_of, score_many
    model, alphabet = load_model()
    print(llr_of("eccE1", "G346A", model, alphabet))      # one variant
    rows = score_many([("eccE1", "G346A"), ("katG", "S315T")])  # loads once

    # CLI
    python -m mtbc_mutation_impact.llr eccE1 G346A

RESIDUES OUTSIDE THE H37Rv PROTEIN (regions of difference)
------------------------------------------------------------
``llr_of`` resolves `gene` against the H37Rv CDS catalogue, so it cannot score
a residue that H37Rv does not have -- e.g. a position inside a region of
difference deleted in H37Rv (TbD1 truncates mmpS6 + the 5' end of mmpL6 in the
modern lineage; RD1/RD9/etc truncate other genes in BCG or other strains).
Use ``llr_of_protein`` with the full-length protein of a strain that carries
the intact locus instead (translate its CDS with the same ``translate_cds``
used here, so table-11 initiator handling matches):

    from mtbc_gene_function import translate_cds
    from mtbc_mutation_impact.llr import llr_of_protein
    protein, _truncated = translate_cds(mbovis_cds_dna)   # e.g. LT708304.1 CDS
    print(llr_of_protein(protein, "N551K", label="mmpL6_Mbovis_AF2122_97"))

    # CLI
    python -m mtbc_mutation_impact.llr --protein-fasta mbovis_mmpL6.faa mmpL6_Mbovis N551K
"""
from __future__ import annotations

import re
import sys

from mtbc_gene_function import extract_cds, translate_cds

MUT_RE = re.compile(r"^([A-Z])(\d+)([A-Z])$")
DEFAULT_MODEL = "esm1v_t33_650M_UR90S_1"  # Meier et al. 2021 variant-effect model
MAXLEN = 1022  # ESM-1v context window (1024 incl. <cls>/<eos>)


class LLRError(Exception):
    """Raised on a malformed mutation, a WT mismatch, or a missing dependency."""


def _require_esm():
    try:
        import torch  # noqa: F401
        import esm  # noqa: F401
    except Exception as exc:  # pragma: no cover - environment dependent
        raise LLRError(
            "ESM-1v scoring needs torch + fair-esm. Install with "
            "`pip install fair-esm` (use a venv created with "
            "`--system-site-packages` if a fresh-venv torch is broken)."
        ) from exc
    return torch, esm


def load_model(name: str = DEFAULT_MODEL):
    """Load an ESM model + alphabet once; reuse across many variants."""
    _, esm = _require_esm()
    model, alphabet = getattr(esm.pretrained, name)()
    model.eval()
    return model, alphabet


def _wt_protein(query: str) -> str:
    dna, _ = extract_cds(query)
    prot, _trunc = translate_cds(dna)
    return prot


def _window(seq: str, pos0: int) -> tuple[str, int]:
    """Return a <=MAXLEN window of seq and the new 0-based index of pos0."""
    if len(seq) <= MAXLEN:
        return seq, pos0
    half = MAXLEN // 2
    start = max(0, min(pos0 - half, len(seq) - MAXLEN))
    return seq[start:start + MAXLEN], pos0 - start


def llr_of_protein(protein: str, mutation: str, model=None, alphabet=None,
                    label: str = "custom") -> dict:
    """Masked-marginal ESM-1v LLR for one <REF><POS><ALT> mutation on an EXPLICIT
    protein sequence, bypassing the H37Rv gene resolver entirely.

    Use this when the mutated residue does not exist in the H37Rv protein: a
    region of difference deleted relative to H37Rv (TbD1, RD1, RD9, any
    BCG/animal-lineage deletion) truncates or removes the H37Rv CDS, so
    ``llr_of("mmpL6", ...)`` cannot resolve a residue that only exists in the
    intact locus of another strain. Pass the full-length protein of a strain
    that carries the intact locus instead (e.g. M. bovis AF2122/97 for
    TbD1-affected genes), translated with the same ``translate_cds`` used for
    H37Rv (table-11 initiator handling) so numbering conventions match.

    Returns a dict with gene (=label), mutation, wt_len, p_wt, p_alt, llr,
    windowed -- same shape as ``llr_of``.
    """
    m = MUT_RE.match(mutation.strip())
    if not m:
        raise LLRError(f"Bad mutation {mutation!r}; expected e.g. S315T")
    ref, pos, alt = m.group(1), int(m.group(2)), m.group(3)

    pos0 = pos - 1
    if pos0 >= len(protein):
        raise LLRError(f"pos {pos} beyond protein length {len(protein)} for {label}")
    if protein[pos0] != ref:
        raise LLRError(f"WT mismatch for {label} {mutation}: seq has {protein[pos0]} at {pos}")

    torch, _ = _require_esm()
    if model is None or alphabet is None:
        model, alphabet = load_model()
    bc = alphabet.get_batch_converter()

    sub, idx = _window(protein, pos0)
    _, _, toks = bc([("wt", sub)])
    toks = toks.clone()
    tok_pos = idx + 1  # +1 for prepended <cls>
    toks[0, tok_pos] = alphabet.mask_idx
    with torch.no_grad():
        logits = model(toks)["logits"]
    logp = torch.log_softmax(logits[0, tok_pos], dim=-1)
    p_wt = float(logp[alphabet.get_idx(ref)])
    p_alt = float(logp[alphabet.get_idx(alt)])
    return {
        "gene": label, "mutation": mutation, "ref": ref, "pos": pos, "alt": alt,
        "wt_len": len(protein), "p_wt": round(p_wt, 4), "p_alt": round(p_alt, 4),
        "llr": round(p_alt - p_wt, 4), "windowed": len(protein) > MAXLEN,
    }


def llr_of(gene: str, mutation: str, model=None, alphabet=None) -> dict:
    """Masked-marginal ESM-1v LLR for one <REF><POS><ALT> protein mutation,
    resolving `gene` against the H37Rv CDS catalogue.

    Returns a dict with gene, mutation, wt_len, p_wt, p_alt, llr, windowed.
    """
    prot = _wt_protein(gene)
    return llr_of_protein(prot, mutation, model, alphabet, label=gene)


def score_many(pairs, name: str = DEFAULT_MODEL) -> list[dict]:
    """Score a list of (gene, mutation) pairs, loading the model once.

    A pair that fails (bad mutation, WT mismatch) yields a dict with an
    ``error`` key instead of an ``llr`` key, so the batch never aborts.
    """
    model, alphabet = load_model(name)
    out = []
    for gene, mut in pairs:
        try:
            out.append(llr_of(gene, mut, model, alphabet))
        except LLRError as exc:
            out.append({"gene": gene, "mutation": mut, "error": str(exc)})
    return out


def _read_fasta_protein(path: str) -> str:
    """Read a single-record protein FASTA (header ignored) into one sequence string."""
    chunks: list[str] = []
    with open(path) as f:
        for line in f:
            if line.startswith(">"):
                continue
            chunks.append(line.strip())
    return "".join(chunks).upper()


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    usage = ("usage: python -m mtbc_mutation_impact.llr <gene> <MUT>  e.g. eccE1 G346A\n"
              "       python -m mtbc_mutation_impact.llr --protein-fasta <fasta> <label> <MUT>"
              "  (residue absent from H37Rv, e.g. inside a region of difference)")
    if argv and argv[0] == "--protein-fasta":
        if len(argv) != 4:
            print(usage, file=sys.stderr)
            return 2
        protein = _read_fasta_protein(argv[1])
        rec = llr_of_protein(protein, argv[3], label=argv[2])
    else:
        if len(argv) != 2:
            print(usage, file=sys.stderr)
            return 2
        rec = llr_of(argv[0], argv[1])
    print(f"{rec['gene']} {rec['mutation']}: LLR={rec['llr']:+.3f} "
          f"(p_wt={rec['p_wt']}, p_alt={rec['p_alt']}, len={rec['wt_len']}"
          f"{', windowed' if rec['windowed'] else ''})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
