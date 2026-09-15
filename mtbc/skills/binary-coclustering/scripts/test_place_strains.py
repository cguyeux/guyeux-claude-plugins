#!/usr/bin/env python3
"""Regression tests for frozen-model placement. Run: python3 test_place_strains.py

Synthetic on purpose: strains are generated FROM a known `alpha`, so the right
answer is known and the two traps (clonal pseudo-replication, "fits nowhere") can
be exhibited rather than asserted in prose.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp

sys.path.insert(0, str(Path(__file__).resolve().parent))
from place_strains import diagnose, place  # noqa: E402

ALPHA = np.array(
    [
        [0.95, 0.05, 0.05, 0.5],
        [0.05, 0.95, 0.05, 0.5],
        [0.05, 0.05, 0.95, 0.5],  # marker block 3 is uninformative on purpose
    ]
)


def _synth(seed=0, n_markers=200):
    rng = np.random.default_rng(seed)
    w = rng.integers(0, ALPHA.shape[1], n_markers)
    rows = [(rng.random(n_markers) < ALPHA[i][w]).astype(np.int8) for i in range(ALPHA.shape[0])]
    return sp.csr_matrix(np.vstack(rows)), w, rng


def test_argmax_recovers_the_generating_block():
    X, w, _ = _synth()
    best, _, _, _ = diagnose(place(X, ALPHA, w, weight="block"))
    assert best.tolist() == [0, 1, 2], best


def test_marker_weighting_saturates_and_block_weighting_does_not():
    """The trap, made visible: counting every marker treats one evolutionary event
    as m_j independent observations, and every posterior collapses onto 0/1."""
    X, w, _ = _synth()
    _, p_block, _, _ = diagnose(place(X, ALPHA, w, weight="block"))
    _, p_marker, _, _ = diagnose(place(X, ALPHA, w, weight="marker"))
    assert (p_marker > 0.999).all(), p_marker
    assert (p_block < 0.999).all(), p_block


def test_random_profile_is_flagged_as_fitting_nowhere():
    X, w, rng = _synth()
    Xr = sp.csr_matrix((rng.random((1, X.shape[1])) < 0.5).astype(np.int8))
    _, p, Hn, _ = diagnose(place(Xr, ALPHA, w, weight="block"))
    assert Hn[0] > 0.30, Hn  # diffuse responsibility, the signal we are after
    assert p[0] < 0.8, p


def test_argmax_survives_the_wrong_weighting():
    """Only the confidence is wrong under `marker`, not the assignment."""
    X, w, _ = _synth()
    b1, _, _, _ = diagnose(place(X, ALPHA, w, weight="block"))
    b2, _, _, _ = diagnose(place(X, ALPHA, w, weight="marker"))
    assert b1.tolist() == b2.tolist()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed")
