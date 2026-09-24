"""Wright-Fisher forward simulation of a derived allele under selection + drift.

Diploid model with a dominance coefficient h (A = derived allele, deleterious if s>0):

    w_AA = 1 - s ,  w_Aa = 1 - h*s ,  w_aa = 1

  h = 0   -> recessive  (only homozygotes affected; the TYK2 P1104A model)
  h = 0.5 -> additive
  h = 1   -> dominant

Per generation: deterministic selection on the allele frequency p, then binomial
drift with 2*Ne gene copies. The recessive case gives the slow decline (e.g. ~10% ->
~3% over ~120 generations under s~0.2) seen for TYK2 P1104A; a haploid model would
collapse far too fast.
"""
from __future__ import annotations

import numpy as np


def selection_step(p: float, s: float, h: float) -> float:
    """One deterministic generation of diploid selection on derived-allele freq p."""
    w_aa = 1.0
    w_Aa = 1.0 - h * s
    w_AA = 1.0 - s
    wbar = p * p * w_AA + 2 * p * (1.0 - p) * w_Aa + (1.0 - p) * (1.0 - p) * w_aa
    if wbar <= 0:
        return 0.0
    pp = (p * p * w_AA + p * (1.0 - p) * w_Aa) / wbar
    return min(1.0, max(0.0, pp))


def simulate(f0: float, s: float, ne: float, generations: int,
             rng: np.random.Generator, h: float = 0.0) -> np.ndarray:
    """Return the derived-allele frequency trajectory (length generations+1)."""
    two_n = max(2, int(round(2 * ne)))
    f = float(f0)
    traj = np.empty(generations + 1, dtype=float)
    traj[0] = f
    for g in range(1, generations + 1):
        pp = selection_step(f, s, h)
        f = rng.binomial(two_n, pp) / two_n
        traj[g] = f
    return traj


def sample_at(traj: np.ndarray, bins) -> np.ndarray:
    """Allele frequency at the given generation indices (clamped to the trajectory)."""
    last = len(traj) - 1
    return np.array([traj[min(int(b), last)] for b in bins], dtype=float)
