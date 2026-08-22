#!/usr/bin/env python3
"""Regression tests on cases whose answer is known by hand. Run: python3 test_laminarity.py

Small on purpose: the point is that each case has ONE right answer derivable from
the definition of a perfect phylogeny, so a failure localises the bug instead of
signalling that something, somewhere, drifted.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp

sys.path.insert(0, str(Path(__file__).resolve().parent))
from laminarity import (  # noqa: E402
    LaminarTree,
    RelationMask,
    combinatorial_bound,
    dedupe_profiles,
    dedupe_taxa,
    explain_crossing,
)

# P12.6.1.2 (coclustering_lineages): laminar_strain_level's two test cases share the
# fixture from test_fragility_counts_the_smaller_side -- x ON in 3 taxa, y in 2, they
# share 1, so the crossing's fragility is 1 (taxon "d", the sole exclusive carrier of y).
_XY_ON = np.array([[1, 1], [1, 0], [1, 0], [0, 1], [0, 0]], bool)


def test_laminar_set_rebuilds_its_tree():
    """m0={a,b}, m1={c,d}, m2=all: nested and disjoint only, so ((a,b),(c,d))."""
    ON = np.array([[1, 0, 1], [1, 0, 1], [0, 1, 1], [0, 1, 1]], bool)
    r = RelationMask(ON, columns=["m0", "m1", "m2"])
    assert r.counts()["incoherent"] == 0
    t = LaminarTree(r.laminar(), labels=list("abcd"))
    assert t.newick() == "((a,b),(c,d));", t.newick()


def test_four_gametes_is_one_crossing():
    """All four combinations 11/10/01/00 present: the textbook conflict."""
    ON = np.array([[1, 1], [1, 0], [0, 1], [0, 0]], bool)
    assert RelationMask(ON, columns=["x", "y"]).counts()["incoherent"] == 1


def test_unknown_overhang_creates_no_crossing():
    """Same data, but the overhang of x past y falls on UNKNOWN: no frank conflict."""
    ON = np.array([[1, 1], [1, 0], [0, 1], [0, 0]], bool)
    off = np.array([[0, 0], [0, 0], [1, 0], [1, 1]], bool)  # b is UNKNOWN for y
    assert RelationMask(ON, columns=["x", "y"], off=off).counts()["incoherent"] == 0


def test_combinatorial_bound():
    assert combinatorial_bound(10, 5)["provably_incompatible"]
    assert combinatorial_bound(10, 5)["excess"] == 6
    assert not combinatorial_bound(3, 5)["provably_incompatible"]


def test_dedupe_both_axes():
    X = sp.csr_matrix(np.array([[1, 1, 0], [1, 1, 0], [0, 0, 1]]))
    Xt, _ = dedupe_taxa(X)
    Xu, _ = dedupe_profiles(Xt)
    assert Xt.shape[0] == 2 and Xu.shape[1] == 2


def test_fragility_counts_the_smaller_side():
    """x is ON in 3 taxa, y in 2, they share 1: overhangs are 2 and 1, fragility 1."""
    ON = np.array([[1, 1], [1, 0], [1, 0], [0, 1], [0, 0]], bool)
    r = RelationMask(ON, columns=["x", "y"])
    (i, j), = r.incoherent_pairs()
    d = explain_crossing(r, i, j, taxa_labels=list("abcde"))
    assert d["fragility"] == 1, d
    assert d["witnesses"] == ["d"], d


def test_strain_level_repairs_crossing_below_tolerance():
    """tolerance=1 (absolute): the single-taxon fragility is within budget, so the
    crossing is resolved by dropping that one taxon from y rather than removing
    either marker whole."""
    r = RelationMask(_XY_ON, columns=["x", "y"])
    sl = r.laminar_strain_level(tolerance=1)
    assert sl.remaining.counts()["incoherent"] == 0, sl
    assert sl.exceptions == [(3, 1)], sl.exceptions  # taxon "d", marker "y"
    assert sl.resolved == [(0, 1, 1)], sl.resolved


def test_strain_level_respects_tolerance():
    """tolerance=0: the same fragility-1 crossing exceeds the budget and is left
    untouched -- no exception taken, no marker sacrificed either."""
    r = RelationMask(_XY_ON, columns=["x", "y"])
    sl = r.laminar_strain_level(tolerance=0)
    assert sl.exceptions == []
    assert sl.remaining.counts()["incoherent"] == 1


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed")
