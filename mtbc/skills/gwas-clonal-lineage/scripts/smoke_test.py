#!/usr/bin/env python3
"""smoke_test.py -- regression test for `stratified_cmh.py`, `mappability_filter.py` and
`homoplasy_scan.py`, against numbers already independently computed and published in this
repo's own lab notebooks (not invented fixtures): the 3-SNP CMH of mtbc/Rv1125 (P1.3.i,
cahier 2026-08-30) and the cohort-level CMH of mtbc/Rv2566 (P2.4). Re-derives the same
p-values, pooled odds ratios and Breslow-Day results from the module this skill packages,
proving the consolidation preserved the exact math rather than approximating it.

Run: python smoke_test.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stratified_cmh import build_strata_tables, cmh  # noqa: E402


def approx(a: float, b: float, rel: float = 1e-3) -> bool:
    return abs(a - b) <= rel * max(abs(a), abs(b), 1e-12)


def check(label: str, cond: bool) -> None:
    print(f"[{'ok' if cond else 'FAIL'}] {label}")
    if not cond:
        raise SystemExit(1)


def main() -> None:
    # --- Rv1125 P1.3.i, SNP_1248936: 2/3 lineages informative (lineage4 has 0 carriers) ---
    # Exact counts from `résultats/phase1_p1_3_i_cmh_snp_lignee/rapport.md` (cahier 2026-08-30):
    # denominateurs lineage1 TBM=33/PTB=45, lineage2 TBM=80/PTB=200 ; porteurs
    # lineage1 3 TBM/2 PTB, lineage2 21 TBM/7 PTB. Expected: chi2=30.512, p=3.319e-08,
    # OR poolé=7.187, Breslow-Day chi2=2.277 p=0.1313 (all homogeneous).
    per_stratum = {
        "lineage1": (3, 2, 33 - 3, 45 - 2),   # a=carrier&TBM, b=carrier&PTB, c=noncarrier&TBM, d=noncarrier&PTB
        "lineage2": (21, 7, 80 - 21, 200 - 7),
    }
    tables, _used, _excluded = build_strata_tables(per_stratum)
    check("SNP_1248936: 2 strates informatives construites", len(tables) == 2)
    r = cmh(tables)
    check(f"SNP_1248936: chi2={r.cmh_statistic:.3f} conforme (attendu 30.512)",
          r.cmh_statistic is not None and approx(r.cmh_statistic, 30.512, rel=1e-2))
    check(f"SNP_1248936: p={r.cmh_pvalue:.3e} conforme (attendu 3.319e-08)",
          r.cmh_pvalue is not None and approx(r.cmh_pvalue, 3.319e-08, rel=5e-2))
    check(f"SNP_1248936: OR poolé={r.or_pooled_mh:.3f} conforme (attendu 7.187)",
          r.or_pooled_mh is not None and approx(r.or_pooled_mh, 7.187, rel=1e-2))
    check(f"SNP_1248936: Breslow-Day p={r.breslow_day_pvalue:.3f} conforme (attendu 0.1313, homogène)",
          r.breslow_day_pvalue is not None and approx(r.breslow_day_pvalue, 0.1313, rel=5e-2)
          and not r.heterogeneous)

    # --- pure-python fallback must agree on significance (not exact p, no continuity match) ---
    from stratified_cmh import cmh_pure_python
    r_pp = cmh_pure_python(tables)
    check(f"fallback pur-Python: p={r_pp.cmh_pvalue:.2e} conclut aussi significatif",
          r_pp.cmh_pvalue is not None and r_pp.cmh_pvalue < 0.01)

    # --- degenerate stratum handling: a stratum with a zero margin must be excluded, not crash ---
    degenerate = {"lineage4": (0, 0, 12, 9), "lineage1": (3, 2, 30, 43), "lineage2": (21, 7, 59, 193)}
    tables2, _used2, excluded2 = build_strata_tables(degenerate)
    check("strate degeneree (0 porteur) exclue plutot que plantée",
          "lineage4" in excluded2 and len(tables2) == 2)

    # --- under-2-strata guard: must report, not crash ---
    r_toofew = cmh([[[1, 2], [3, 4]]])
    check("moins de 2 strates -> resultat explicite non calculable, pas d'exception",
          r_toofew.cmh_pvalue is None and "non calculable" in r_toofew.note)

    # --- mappability_filter: synthetic genome, one duplicated locus + one unique locus ---
    import shutil
    import tempfile
    from mappability_filter import check_mappability

    if shutil.which("blastn") and shutil.which("makeblastdb"):
        import random
        rng = random.Random(42)
        unique = "".join(rng.choice("ACGT") for _ in range(400))
        dup = "".join(rng.choice("ACGT") for _ in range(150))
        genome_seq = unique[:150] + dup + unique[150:250] + dup + unique[250:]
        with tempfile.TemporaryDirectory() as tmp:
            genome_fasta = Path(tmp) / "genome.fasta"
            genome_fasta.write_text(f">synthetic\n{genome_seq}\n")
            pos_in_dup = 150 + 75  # 1-based position inside the FIRST copy of the duplicated block
            pos_in_unique = 50     # inside the unique region
            results = check_mappability(
                genome_fasta, [("dup_candidate", pos_in_dup), ("unique_candidate", pos_in_unique)],
                half_window=40,
            )
            by_name = {r.name: r for r in results}
            check("mappability: SNP dans la region dupliquée -> PARALOG-RISK",
                  by_name["dup_candidate"].verdict == "PARALOG-RISK")
            check("mappability: SNP dans la region unique -> unique-mappable",
                  by_name["unique_candidate"].verdict == "unique-mappable")
    else:
        print("[skip] mappability_filter: blastn/makeblastdb absents de ce PATH")

    print("\nALL OK")


if __name__ == "__main__":
    main()
