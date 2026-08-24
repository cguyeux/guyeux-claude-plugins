"""Offline smoke test for molecular_clock.py root-to-tip regression. No network.

Builds a perfectly clock-like star tree (root-to-tip distance = 0.001*(year-2000))
and checks the regression recovers rate ~ 0.001 and R^2 ~ 1, with a bootstrap CI that
brackets the true rate. Exercises the true-patristic path (needs biopython, present).

    python3 smoke_test.py
"""
from __future__ import annotations

import os
import sys
import tempfile

from molecular_clock import load_dates, parse_newick_distances, root_to_tip_regression

TREE = "(A:0.005,B:0.010,C:0.015,D:0.020,E:0.025);"
DATES = "strain_id,date\nA,2005\nB,2010\nC,2015\nD,2020\nE,2025\n"


def main() -> int:
    td = tempfile.mkdtemp(prefix="molclock_smoke_")
    tp, dp = os.path.join(td, "t.nwk"), os.path.join(td, "d.csv")
    with open(tp, "w") as f:
        f.write(TREE)
    with open(dp, "w") as f:
        f.write(DATES)

    dist = parse_newick_distances(tp)
    dates = load_dates(dp)
    res = root_to_tip_regression(dist, dates)[0]
    lo, hi = res["rate_boot_ci95_lo"], res["rate_boot_ci95_hi"]
    print(f"n={res['n_samples']} rate={res['rate_per_year']:.2e} R2={res['r_squared']:.4f} "
          f"boot95=[{lo:.2e},{hi:.2e}] quality={res['signal_quality']}")

    if res["n_samples"] != 5:
        print("FAIL: expected 5 matched strains", file=sys.stderr)
        return 2
    if res["r_squared"] < 0.99:
        print(f"FAIL: expected R2~1 on a clock-like tree, got {res['r_squared']}", file=sys.stderr)
        return 2
    if abs(res["rate_per_year"] - 0.001) > 1e-4:
        print(f"FAIL: expected rate~0.001/yr, got {res['rate_per_year']}", file=sys.stderr)
        return 2
    if lo is None or not (lo - 1e-9 <= 0.001 <= hi + 1e-9):
        print(f"FAIL: bootstrap CI should bracket 0.001, got [{lo},{hi}]", file=sys.stderr)
        return 2

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
