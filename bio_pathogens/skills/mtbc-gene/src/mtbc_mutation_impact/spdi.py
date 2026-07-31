"""Convert a nucleotide SPDI (NC_000962.3:POS:REF:ALT) into a protein-level
gene + mutation pair, then delegate to `impact_of`.

Leverages the existing `spdi-annotation` skill's `annotate_spdis.py` module,
which already implements the gene lookup, strand handling and codon
translation correctly. We load it once via importlib (no source duplication).
"""
from __future__ import annotations

import importlib.util
import os
import sys
import threading
from dataclasses import dataclass
from pathlib import Path

from esm_atlas_cli import EsmAtlasClient

from .core import ImpactReport, impact_of


SPDI_ANNOTATION_SCRIPT = Path(
    os.environ.get(
        "SPDI_ANNOTATION_PY",
        "~/docs/codes/claude_plugins/bio_pathogens/skills/spdi-annotation/scripts/annotate_spdis.py",
    )
).expanduser()
H37RV_GFF3 = Path(
    os.environ.get(
        "MTBC_H37RV_GFF3",
        "~/docs/codes/mtbc/investigate_phylo/resources/NC_000962.3.gff3",
    )
).expanduser()
H37RV_GB = Path(
    os.environ.get(
        "MTBC_H37RV_GB",
        "~/docs/codes/mtbc/investigate_phylo/resources/NC_000962.3.gb",
    )
).expanduser()


class SpdiError(Exception):
    pass


_lock = threading.Lock()
_state: dict = {"loaded": False, "module": None, "genome": None, "gene_index": None}


def _ensure_loaded() -> None:
    if _state["loaded"]:
        return
    with _lock:
        if _state["loaded"]:
            return
        if not SPDI_ANNOTATION_SCRIPT.exists():
            raise SpdiError(f"spdi-annotation module not found at {SPDI_ANNOTATION_SCRIPT}")
        spec = importlib.util.spec_from_file_location("annotate_spdis", str(SPDI_ANNOTATION_SCRIPT))
        if spec is None or spec.loader is None:
            raise SpdiError(f"Could not load {SPDI_ANNOTATION_SCRIPT}")
        module = importlib.util.module_from_spec(spec)
        sys.modules["annotate_spdis"] = module
        spec.loader.exec_module(module)

        if not H37RV_GFF3.exists():
            raise SpdiError(f"Missing GFF3 at {H37RV_GFF3}")
        if not H37RV_GB.exists():
            raise SpdiError(f"Missing GenBank at {H37RV_GB}")

        _state["module"] = module
        _state["gene_index"] = module.load_gene_index(str(H37RV_GFF3))
        _state["genome"] = module.load_genome_sequence(str(H37RV_GB))
        _state["loaded"] = True


def _parse_spdi(spdi: str) -> tuple[str, int, str, str]:
    """`NC_000962.3:2155168:C:G` → ('NC_000962.3', 2155168, 'C', 'G')."""
    parts = spdi.strip().split(":")
    if len(parts) != 4:
        raise SpdiError(f"Bad SPDI {spdi!r}; expected REF:POS:REF:ALT (4 colon-separated fields)")
    ref_chrom, pos_str, ref, alt = parts
    try:
        pos = int(pos_str)
    except ValueError as e:
        raise SpdiError(f"Bad SPDI position {pos_str!r}") from e
    if not (ref and alt and ref != alt):
        raise SpdiError(f"SPDI ref/alt empty or identical: {spdi!r}")
    return ref_chrom, pos, ref.upper(), alt.upper()


@dataclass
class SpdiAnnotation:
    spdi: str
    chrom: str
    pos: int
    ref_nt: str
    alt_nt: str
    gene: str | None
    locus_tag: str | None
    strand: str | None
    product: str | None
    effect: str
    hgvs_p: str | None
    is_protein_changing: bool


def spdi_to_protein_mutation(spdi: str) -> SpdiAnnotation:
    """Resolve a SPDI to a gene + protein mutation string.

    Returns a SpdiAnnotation. `hgvs_p` is the protein-coordinate mutation
    ready for `impact_of(gene, mut)` if `is_protein_changing` is True; for
    synonymous, stop_gained, intergenic, or frameshift variants, the
    annotation is returned but `is_protein_changing` is False.
    """
    _ensure_loaded()
    chrom, pos, ref, alt = _parse_spdi(spdi)
    module = _state["module"]
    gene_info, *_ = module.find_gene_at_position(_state["gene_index"], pos)
    if not gene_info:
        return SpdiAnnotation(
            spdi=spdi, chrom=chrom, pos=pos, ref_nt=ref, alt_nt=alt,
            gene=None, locus_tag=None, strand=None, product=None,
            effect="intergenic", hgvs_p=None, is_protein_changing=False,
        )

    effect, hgvs = module.get_codon_change(_state["genome"], gene_info, pos, ref, alt)
    is_missense = effect == "missense_variant" and hgvs and len(hgvs) >= 3
    return SpdiAnnotation(
        spdi=spdi, chrom=chrom, pos=pos, ref_nt=ref, alt_nt=alt,
        gene=gene_info.get("gene"),
        locus_tag=gene_info.get("locus_tag"),
        strand=gene_info.get("strand"),
        product=gene_info.get("product"),
        effect=effect, hgvs_p=hgvs,
        is_protein_changing=bool(is_missense),
    )


def impact_of_spdi(spdi: str, *, client: EsmAtlasClient | None = None,
                   max_labels: int = 5) -> ImpactReport:
    """Convert SPDI → (gene, AA mutation) then run `impact_of`.

    Raises:
        SpdiError: if the SPDI is malformed, intergenic, synonymous, frameshift,
                   stop-gained, or otherwise not a single-residue missense.
    """
    ann = spdi_to_protein_mutation(spdi)
    if not ann.is_protein_changing:
        raise SpdiError(
            f"{spdi}: effect={ann.effect!r}, not a missense substitution; "
            f"per-residue ESM comparison is not meaningful here."
        )
    target = ann.gene or ann.locus_tag
    if not target:
        raise SpdiError(f"{spdi}: gene resolved but no gene name or locus tag available")
    return impact_of(target, ann.hgvs_p, client=client, max_labels=max_labels)
