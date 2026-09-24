#!/usr/bin/env python3
"""homoplasy_scan.py -- is a GWAS hit a CONVERGENT marker of the phenotype, or just a marker
of one clonally-expanded sub-clade that happens to carry both the variant and the phenotype
by pure linkage?

Generalises `tissue_tropism_mtbc/analyses/phase4_homoplasy_confirm.py`. Rationale: a variant
that arose ONCE, early, in a sub-clade that later expanded and happens to be enriched for
the phenotype (sampling/ascertainment, not causation) will look identical to a genuinely
causal, repeatedly-arisen variant under a SINGLE lineage-level CMH stratification -- both
pass. The distinguishing test does not need a reconstructed tree: MTBC clade codes in this
repo's database (`bdd/actuelle/<clade>/<strain>/`) already encode a nested taxonomy as a
dotted prefix (e.g. `L4.3.4.2`), so re-running the SAME stratified CMH at increasing prefix
DEPTH (D=1 major lineage ... D=4 fine sub-clade) is a free, tree-free homoplasy probe:
  - A variant that is a SYNAPOMORPHY of one sub-clade becomes monomorphic (present in ALL or
    NONE of the strain in its own stratum) as D increases past the node where it arose --
    its contribution to the CMH statistic vanishes, because a monomorphic stratum carries no
    information (the `build_strata_tables` "informative" test already excludes it).
  - A variant CONVERGENTLY present in several independent sub-clades stays POLYMORPHIC within
    strata at every depth, and its signal survives.
This does not replace an actual phylogenetic homoplasy test (a variant appearing on multiple
branches of a real tree) -- it is the cheap, always-available proxy when only clade-code
strings are on hand, not a substitute when a tree already exists (in that case, use the
`convergent-evolution` or `pastml` skills instead, which test homoplasy directly on the tree).

Two outputs per candidate:
  1. `signal_survives_at_depth`: dict `{depth: CMHResult}` -- does the stratified CMH stay
     significant as D increases? A signal that dies as D increases is compatible with a
     clonal/linkage explanation (does not PROVE it, since power also drops as strata get
     smaller and more strata become uninformative -- report both possibilities).
  2. Descriptive homoplasy indices among phenotype-positive carriers: number of distinct
     depth-3 sub-lineages, and a clonality index (fraction of carriers in the single largest
     complete clade) -- a convergent variant has many distinct sub-lineages and low
     clonality; a clonal marker has one dominant sub-lineage and high clonality.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from stratified_cmh import CMHResult, build_strata_tables, cmh


@dataclass
class HomoplasyReport:
    signal_survives_at_depth: dict[int, CMHResult]
    n_distinct_sublineages_d3: int
    clonality_index: float
    interpretation: str


def _prefix(clade: str, depth: int) -> str:
    """`clade` like `L4.3.4.2` -> prefix at `depth` dot-separated components."""
    parts = clade.split(".")
    return ".".join(parts[:depth]) if depth <= len(parts) else clade


def scan_depths(
    strains: list[tuple[str, bool, str]],
    carrier_ids: set[str],
    *,
    depths: tuple[int, ...] = (1, 2, 3, 4),
    min_informative: int = 2,
) -> dict[int, CMHResult]:
    """`strains`: list of `(strain_id, is_case, clade_code)` for the WHOLE tested cohort
    (case = has the phenotype of interest, e.g. TBM). `carrier_ids`: strain ids carrying the
    candidate variant. Returns one `CMHResult` per depth in `depths`."""
    out = {}
    for depth in depths:
        counts: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])  # a,b,c,d
        for sid, is_case, clade in strains:
            strat = _prefix(clade, depth)
            carries = sid in carrier_ids
            idx = (0 if carries else 2) + (0 if is_case else 1)
            counts[strat][idx] += 1
        per_stratum = {k: tuple(v) for k, v in counts.items()}
        tables, _, _ = build_strata_tables(per_stratum, min_informative=min_informative)
        out[depth] = cmh(tables) if tables else CMHResult(
            len(per_stratum), 0, None, None, None, None, None, None,
            note="0 strate informative a cette profondeur",
        )
    return out


def homoplasy_indices(
    strains: list[tuple[str, bool, str]],
    carrier_ids: set[str],
    *,
    sublineage_depth: int = 3,
) -> tuple[int, float]:
    """Among CASE carriers only (phenotype-positive AND carrying the variant): number of
    distinct sub-lineages at `sublineage_depth`, and the clonality index (fraction sitting in
    the single largest one)."""
    case_carrier_clades = [clade for sid, is_case, clade in strains if is_case and sid in carrier_ids]
    if not case_carrier_clades:
        return 0, 0.0
    sublineages = Counter(_prefix(c, sublineage_depth) for c in case_carrier_clades)
    n_distinct = len(sublineages)
    clonality = max(sublineages.values()) / len(case_carrier_clades)
    return n_distinct, clonality


def homoplasy_report(
    strains: list[tuple[str, bool, str]],
    carrier_ids: set[str],
    *,
    depths: tuple[int, ...] = (1, 2, 3, 4),
    sublineage_depth: int = 3,
) -> HomoplasyReport:
    by_depth = scan_depths(strains, carrier_ids, depths=depths)
    n_sub, clonality = homoplasy_indices(strains, carrier_ids, sublineage_depth=sublineage_depth)

    survives = [d for d, r in by_depth.items() if r.significant]
    max_depth_tested = max(by_depth)
    if max_depth_tested in survives:
        verdict = (
            f"signal survit jusqu'a la profondeur maximale testee (D={max_depth_tested}) "
            f"et {n_sub} sous-lignee(s) distincte(s) portent le variant chez les cas "
            f"(clonalite={clonality:.2f}) -- compatible avec un variant CONVERGENT, "
            "pas seulement un marqueur de sous-clade."
        )
    elif clonality > 0.9 and n_sub <= 1:
        verdict = (
            f"signal disparait a mesure que D augmente et {n_sub} sous-lignee domine "
            f"(clonalite={clonality:.2f}) -- compatible avec un marqueur d'expansion "
            "clonale d'UN sous-clade, pas une convergence independante. Ne prouve pas la "
            "causalite dans un sens ou l'autre, mais affaiblit l'hypothese convergente."
        )
    else:
        verdict = (
            "resultat intermediaire (signal affaibli mais sous-lignees multiples, ou "
            "inverse) -- ne pas trancher automatiquement, lire le detail par profondeur."
        )
    return HomoplasyReport(by_depth, n_sub, clonality, verdict)
