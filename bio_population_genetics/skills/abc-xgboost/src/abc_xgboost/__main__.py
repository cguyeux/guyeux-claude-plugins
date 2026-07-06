"""Shell CLI for the abc-xgboost skill (run via a venv with xgboost+shap+sklearn).

    PY=/home/christophe/venvs/abc311/bin/python
    $PY -m abc_xgboost demo                                   # TYK2 P1104A-like decline
    $PY -m abc_xgboost infer --observed freqs.csv --n 8000
    $PY -m abc_xgboost simulate --s 0.25 --f0 0.12 --h 0.5    # sanity: one trajectory

`--observed` is a CSV of allele frequencies ordered oldest -> newest (one per line, or
`bin,freq`); omit it (or use `demo`) for the bundled TYK2-like trajectory.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys

import numpy as np

from .abc import DEFAULT_BINS, infer
from .wf import sample_at, simulate

# TYK2 P1104A-like decline (~10% -> ~3% over ~3000 yr), sampled at DEFAULT_BINS.
TYK2_DEMO = [0.10, 0.07, 0.045, 0.029]


def _read_obs(path: str) -> list[float]:
    freqs: list[float] = []
    with open(path) as f:
        for row in csv.reader(f):
            if not row or row[0].lstrip().startswith("#"):
                continue
            try:
                freqs.append(float(row[-1]))
            except ValueError:
                continue
    if not freqs:
        raise SystemExit(f"no numeric frequencies parsed from {path}")
    return freqs


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="abc-xgboost")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("infer", help="infer s + regime for an observed trajectory")
    pi.add_argument("--observed", default=None, help="CSV of freqs oldest->newest (default: TYK2 demo)")
    pi.add_argument("--n", type=int, default=5000, help="number of simulations")
    pi.add_argument("--h", type=float, default=0.0, help="dominance (0=recessive TYK2, 0.5=additive)")

    pd = sub.add_parser("demo", help="run on the synthetic TYK2 P1104A-like decline")
    pd.add_argument("--n", type=int, default=5000)
    pd.add_argument("--h", type=float, default=0.0)

    ps = sub.add_parser("simulate", help="print one trajectory sampled at the bins")
    ps.add_argument("--s", type=float, required=True)
    ps.add_argument("--f0", type=float, default=0.10)
    ps.add_argument("--ne", type=float, default=5000)
    ps.add_argument("--h", type=float, default=0.0)

    args = p.parse_args(argv)
    rng = np.random.default_rng(0)

    if args.cmd == "simulate":
        traj = simulate(args.f0, args.s, args.ne, 120, rng, h=args.h)
        print("bins (generations):", list(DEFAULT_BINS))
        print("freqs:", [round(float(x), 4) for x in sample_at(traj, DEFAULT_BINS)])
        return 0

    obs = TYK2_DEMO if (args.cmd == "demo" or not args.observed) else _read_obs(args.observed)
    res = infer(obs, n=args.n, rng=rng, h=args.h)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
