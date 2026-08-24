"""Offline smoke test for coevolution.py (Mantel / partial Mantel). No network.

Validates the core statistics on data with a KNOWN structure:
  - a genetic matrix built as 2*geo + small noise must give a strong, significant
    Mantel correlation with the geographic matrix;
  - controlling for an unrelated third matrix must leave that signal essentially
    intact (partial Mantel).

    python3 smoke_test.py
"""
from __future__ import annotations

import sys

import numpy as np

from coevolution import mantel_test, partial_mantel


def _sym(a: np.ndarray) -> np.ndarray:
    a = np.abs(a + a.T)
    np.fill_diagonal(a, 0.0)
    return a


def main() -> int:
    pos = np.arange(6.0)
    geo = np.abs(pos[:, None] - pos[None, :])           # 1-D isolation-by-distance
    rng = np.random.default_rng(0)
    gen = _sym(2.0 * geo + 0.02 * rng.standard_normal((6, 6)))   # genetic ~ 2*geo
    ctl = _sym(rng.standard_normal((6, 6)))             # unrelated control

    m = mantel_test(gen, geo, n_perm=999)
    print(f"mantel r={m['r']:.3f} p={m['p_value']:.3f} significant={m['significant']}")
    if not (m["r"] > 0.8 and m["significant"]):
        print(f"FAIL: expected strong significant Mantel, got {m}", file=sys.stderr)
        return 2

    pm = partial_mantel(gen, geo, ctl, n_perm=499)
    print(f"partial mantel (control=unrelated) r_partial={pm['r_partial']:.3f}")
    if not pm["r_partial"] > 0.7:
        print(f"FAIL: controlling for noise should keep the signal, got {pm}", file=sys.stderr)
        return 2

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
