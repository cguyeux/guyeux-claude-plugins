#!/usr/bin/env python3
"""stratified_cmh.py -- Cochran-Mantel-Haenszel + Breslow-Day for a bacterial GWAS on a
CLONAL population, stratified by lineage (or any other confounder with discrete strata).

Consolidates a pattern independently reforged at least 4 times in this repo (mtbc/Rv2566
phase_p2_4_cmh_lineage_tbm.py, mtbc/Rv1125 phase1_p1_3_i_cmh_snp_lignee.py,
mtbc/tissue_tropism_mtbc phase3_cmh_prjna1028637.py + phase4_homoplasy_confirm.py,
mtbc/mixed_infections_multimarker phase9_p91_lineage_confound.py) -- each rewritten "adapte
de" the previous one instead of calling a shared function. See SKILL.md for why this
consolidation is the whole point of the skill, not a nice-to-have.

Two DIFFERENT questions this module answers -- never conflate them (KB lesson, 2026-08-30,
tuberculosis.md "[2026-08-30] Un CMH cohorte/lignee-niveau non significatif ne dit RIEN d'un
CMH SNP-par-SNP sur le meme locus"):
  1. COHORT-level: is LINEAGE ITSELF associated with the phenotype in this cohort? (tests
     population-structure confounding in general, no reference to any specific locus)
  2. LOCUS-level: is CARRYING THIS SPECIFIC VARIANT associated with the phenotype, once
     lineage is stratified out? (the actual GWAS test for one candidate)
A non-significant (1) does NOT imply a non-significant (2) for a given locus, and vice
versa -- always run the level the question actually needs, and if uncertain, run both.

Two implementations of the same math are provided:
  - `cmh_statsmodels()`: `statsmodels.stats.contingency_tables.StratifiedTable`, exact,
    the one already used and cross-checked across 3 projects. Default -- use this if
    statsmodels is available (it almost always is in this environment).
  - `cmh_pure_python()`: dependency-free continuity-corrected CMH (Mantel & Haenszel 1959)
    plus a chi2(1) survival function via `math.erfc` (exact closed form, no scipy). Use
    this only when statsmodels/scipy genuinely cannot be installed (e.g. a portable SLURM
    package) -- it does not compute a Breslow-Day heterogeneity test or a confidence
    interval, only the CMH p-value and the pooled Mantel-Haenszel odds ratio.

Both take the SAME input shape: a list of 2x2 tables, one per stratum, each
`[[a, b], [c, d]]` = `[[exposed_case, exposed_control], [unexposed_case, unexposed_control]]`
(exposed = carries the variant / belongs to the lineage being tested; case = has the
phenotype of interest, e.g. TBM). Column and row order matters for the sign of the odds
ratio but not for the p-value.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class CMHResult:
    n_strata_total: int
    n_strata_informative: int
    cmh_statistic: float | None
    cmh_pvalue: float | None
    or_pooled_mh: float | None
    or_ci: tuple[float, float] | None
    breslow_day_statistic: float | None
    breslow_day_pvalue: float | None
    note: str = ""

    @property
    def significant(self) -> bool | None:
        return None if self.cmh_pvalue is None else self.cmh_pvalue < 0.05

    @property
    def heterogeneous(self) -> bool | None:
        """True if Breslow-Day flags the pooled OR as unsafe to read as a single number --
        i.e. the effect direction or size genuinely differs between strata (as opposed to
        just sampling noise), the single most common way a "significant CMH" result gets
        over-read in a manuscript draft."""
        return None if self.breslow_day_pvalue is None else self.breslow_day_pvalue < 0.05


def build_strata_tables(
    per_stratum_counts: dict[str, tuple[int, int, int, int]],
    *,
    min_informative: int = 2,
) -> tuple[list[list[list[int]]], list[str], list[str]]:
    """Turn `{stratum_name: (a, b, c, d)}` into the `tables` list `cmh_*` expects, dropping
    strata where a margin is zero (the Mantel-Haenszel variance formula divides by
    `n*n*(n-1)` per stratum and a zero row/column margin makes a stratum uninformative
    without raising an error -- silently including it does not crash, it just adds a
    stratum with `var` contribution 0/well-defined but `a`/`b` degenerate; excluding it
    explicitly, as done identically in Rv2566/Rv1125, is the safe and auditable choice).

    Returns `(tables, strata_used, strata_excluded)` -- keep the excluded list in any
    report you write, a reviewer will ask why a stratum was dropped.
    """
    tables, used, excluded = [], [], []
    for name, (a, b, c, d) in per_stratum_counts.items():
        informative = (a + c) > 0 and (b + d) > 0 and (a + b) > 0 and (c + d) > 0
        if informative:
            tables.append([[a, b], [c, d]])
            used.append(name)
        else:
            excluded.append(name)
    if len(tables) < min_informative:
        return [], used, excluded + used  # nothing usable; report everything as excluded
    return tables, used, excluded


def cmh_statsmodels(tables: list[list[list[int]]]) -> CMHResult:
    """Preferred implementation. Requires `statsmodels` (already a dependency of every
    project in this repo that has run this test so far)."""
    n = len(tables)
    if n < 2:
        return CMHResult(n, n, None, None, None, None, None, None,
                          note=f"CMH non calculable : {n} strate(s) informative(s) (<2 requises)")
    from statsmodels.stats.contingency_tables import StratifiedTable

    st = StratifiedTable(tables)
    mh_test = st.test_null_odds()
    ci_low, ci_high = st.oddsratio_pooled_confint()
    bd = st.test_equal_odds()
    return CMHResult(
        n_strata_total=n, n_strata_informative=n,
        cmh_statistic=float(mh_test.statistic), cmh_pvalue=float(mh_test.pvalue),
        or_pooled_mh=float(st.oddsratio_pooled), or_ci=(float(ci_low), float(ci_high)),
        breslow_day_statistic=float(bd.statistic), breslow_day_pvalue=float(bd.pvalue),
    )


def _chi2_1df_sf(x: float) -> float:
    """Exact chi-squared(1 df) survival function via `erfc` -- no scipy needed."""
    return math.erfc(math.sqrt(x / 2.0)) if x > 0 else 1.0


def cmh_pure_python(tables: list[list[list[int]]]) -> CMHResult:
    """Dependency-free fallback (Mantel-Haenszel 1959, continuity-corrected). No Breslow-Day,
    no confidence interval -- use `cmh_statsmodels` unless statsmodels is truly unavailable."""
    n = len(tables)
    if n < 1:
        return CMHResult(n, n, None, None, None, None, None, None,
                          note="CMH non calculable : 0 strate")
    num = var = ad = bc = 0.0
    for (a, b), (c, d) in tables:
        m = a + b + c + d
        if m < 2:
            continue
        r1, c1 = a + b, a + c
        num += a - (r1 * c1) / m
        var += (r1 * (m - r1) * c1 * (m - c1)) / (m * m * (m - 1))
        ad += a * d / m
        bc += b * c / m
    if var <= 0:
        return CMHResult(n, n, None, None, None, None, None, None,
                          note="CMH non calculable : variance nulle (toutes strates degenerees)")
    stat = max(abs(num) - 0.5, 0.0) ** 2 / var
    p = _chi2_1df_sf(stat)
    or_pooled = (ad / bc) if bc > 0 else float("inf")
    return CMHResult(
        n_strata_total=n, n_strata_informative=n,
        cmh_statistic=stat, cmh_pvalue=p, or_pooled_mh=or_pooled, or_ci=None,
        breslow_day_statistic=None, breslow_day_pvalue=None,
        note="pure-python fallback: pas de Breslow-Day ni d'IC, verifier l'homogeneite a la main",
    )


def cmh(tables: list[list[list[int]]], *, prefer_statsmodels: bool = True) -> CMHResult:
    """Convenience entry point: try statsmodels, fall back to pure Python if unavailable."""
    if prefer_statsmodels:
        try:
            return cmh_statsmodels(tables)
        except ImportError:
            pass
    return cmh_pure_python(tables)
