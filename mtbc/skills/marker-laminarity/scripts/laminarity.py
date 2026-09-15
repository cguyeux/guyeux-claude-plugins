#!/usr/bin/env python3
"""Is this marker set compatible with a tree, and if not, who breaks what?

A binary marker (SPDI, RD, IS insertion, spacer) partitions the strains into a
present-set and its complement. A set of such markers admits a perfect phylogeny
iff the present-sets form a LAMINAR family: any two are nested or disjoint, never
crossing. A crossing is the four-gamete conflict, and it means at least one of the
two markers is homoplasic, mis-called, or that the clade it is supposed to define
does not exist.

Three states, not two
---------------------
Our `spdi.txt` files record presences only, so a marker that is not listed for a
strain is either genuinely absent or simply not covered. Collapsing both into
"absent" manufactures crossings. When coverage information is available, pass an
`unknown` mask: a marker that is ON in strain s and UNKNOWN in strain t does not
overrule anything, and only a FRANK disagreement on both sides counts as a
crossing. On `chain10k` upstream this took the conflict count from 41 566 to 1 956.

Credit
------
The relation algebra (five codes, frank three-state overhang, greedy vertex-cover
laminarisation, strongly-connected condensation into a tree) is C. Lecarpentier's,
from `github.com/cdarthos/bi-clustering` (`phylo/relations.py`, `phylo/why.py`),
the code side of his thesis. This is a frozen, standalone re-expression for raw
strain x marker matrices rather than LBM blocks: no dependency on that repository,
no `alpha`, no elbow. Any publication built on it owes him the method.

Everything here is numpy + scipy only.
"""

from __future__ import annotations

from collections import defaultdict, deque

import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components

__all__ = [
    "RelationMask",
    "LaminarMask",
    "LaminarTree",
    "StrainLevelResult",
    "combinatorial_bound",
    "dedupe_profiles",
    "dedupe_taxa",
    "explain_crossing",
]

EGAL, CONTENU, CONTIENT, DISJOINT, INCOHERENT = 0, 1, 2, 3, 4
NAMES = {0: "egal", 1: "contenu", 2: "contient", 3: "disjoint", 4: "incoherent"}


# --------------------------------------------------------------------------- #
# Free diagnostics, before any real computation                               #
# --------------------------------------------------------------------------- #
def combinatorial_bound(n_distinct_profiles: int, n_taxa: int) -> dict:
    """A tree on `n_taxa` leaves admits at most `n_taxa - 1` distinct non-trivial
    clades. If the markers realise more distinct present-sets than that, the excess
    is MATHEMATICALLY forced to be incompatible, whatever the biology. Costs nothing
    and is worth running before any pairwise matrix.
    """
    ceiling = max(n_taxa - 1, 0)
    return {
        "distinct_present_sets": int(n_distinct_profiles),
        "max_clades_on_tree": int(ceiling),
        "excess": int(max(0, n_distinct_profiles - ceiling)),
        "provably_incompatible": bool(n_distinct_profiles > ceiling),
    }


def dedupe_profiles(X):
    """Collapse markers sharing an identical present-set.

    Returns `(Xu, groups)` where `Xu` keeps one column per distinct profile and
    `groups[k]` lists the original column indices behind it. Co-supporting markers
    carry no extra topological information, and on clonal data they are the large
    majority; deduplicating first is what makes the O(k^2) relation matrix tractable.

    Caveat if you reuse this to FIT a model rather than to compute relations. For a
    Bernoulli LBM the marker-block assignment `w` is unchanged (it is a function of
    the present-set alone), but the STRAIN assignment `z` is not: the row E step sums
    over columns, so a present-set replicated 157 times contributes 157 times. On a
    clonal organism that multiplicity IS the branch-length information, so
    deduplicating moves the model from "weighted by divergence" to "one branch, one
    event". Legitimate for SELECTING (g, m) — those 157 mutations are correlated, not
    157 independent observations — but a modelling choice, not a free optimisation,
    when ESTIMATING the strain partition.
    """
    X = sp.csc_matrix(X)
    sig2cols: dict[bytes, list[int]] = defaultdict(list)
    for j in range(X.shape[1]):
        rows = X.indices[X.indptr[j] : X.indptr[j + 1]]
        sig2cols[np.sort(rows).astype(np.int64).tobytes()].append(j)
    keys = list(sig2cols)
    groups = [sig2cols[k] for k in keys]
    keep = [g[0] for g in groups]
    return X[:, keep].tocsc(), groups


def dedupe_taxa(X):
    """Collapse strains carrying an identical marker profile into one weighted taxon.

    Topologically free (identical taxa are interchangeable leaves), and it keeps the
    dense relation matrix affordable.

    DO NOT expect this to be where the compression is. The intuition that a clonal
    organism yields thousands of identical genomes is WRONG on a full marker matrix,
    and it was measured: at a floor of 3 carriers, 8 744 L3 strains give 8 744
    distinct profiles, 1 364 L6 strains give 1 363. A handful of low-frequency
    markers individualises every strain. Row compression only appears on a
    RESTRICTED marker set (a curated backbone: 1 364 L6 strains -> 618 profiles on
    4 864 barcode markers).

    The real redundancy is on the COLUMNS, see `dedupe_profiles`: L3, 72 100 markers
    for 19 728 distinct present-sets; the largest co-segregating group is 157 markers
    for one evolutionary event.

    Returns `(Xu, groups)`, `groups[k]` listing the original rows.
    """
    X = sp.csr_matrix(X)
    sig2rows: dict[bytes, list[int]] = defaultdict(list)
    for i in range(X.shape[0]):
        cols = X.indices[X.indptr[i] : X.indptr[i + 1]]
        sig2rows[np.sort(cols).astype(np.int64).tobytes()].append(i)
    groups = [sig2rows[k] for k in sig2rows]
    keep = [g[0] for g in groups]
    return X[keep, :].tocsr(), groups


# --------------------------------------------------------------------------- #
# Pairwise relations                                                          #
# --------------------------------------------------------------------------- #
class RelationMask:
    """Directed relation between every pair of markers, over their present-sets.

    Parameters
    ----------
    present : (n_taxa, n_markers) bool or sparse
        ON cells: the marker is frankly present in that taxon.
    columns : sequence, optional
        Original marker identifiers, aligned on the columns.
    off : (n_taxa, n_markers) bool or sparse, optional
        Frankly-absent cells. `None` means binary mode, OFF = not-ON, which is the
        classical four-gamete test. Supplying it switches to three states: whatever
        is neither ON nor OFF is UNKNOWN and creates NO crossing.

    Attributes
    ----------
    matrix : (k, k) int8   `matrix[i, j]` is the relation of i towards j
    sizes  : (k,)          size of each ON-set
    inter  : (k, k)        |ON_i AND ON_j|
    beyond : (k, k)        |ON_i AND OFF_j|, the frank overhang of i past j
    """

    EGAL, CONTENU, CONTIENT, DISJOINT, INCOHERENT = EGAL, CONTENU, CONTIENT, DISJOINT, INCOHERENT
    NOMS = NAMES

    def __init__(self, present, columns=None, off=None):
        ON = self._as_dense_bool(present)
        if ON.ndim != 2:
            raise ValueError("present must be 2D (taxa x markers)")
        self.nb, self.nc = ON.shape
        self.columns = list(range(self.nc)) if columns is None else list(columns)
        if len(self.columns) != self.nc:
            raise ValueError(f"{len(self.columns)} identifiers for {self.nc} markers")
        if off is None:
            OFF = ~ON
        else:
            OFF = self._as_dense_bool(off)
            if OFF.shape != ON.shape:
                raise ValueError("off must have the same shape as present")
            if (ON & OFF).any():
                raise ValueError("a cell cannot be both ON and OFF")
        self.present = ON
        self.sizes = ON.sum(0).astype(np.int64)
        oni = ON.astype(np.int64)
        overlap = oni.T @ oni
        beyond = oni.T @ OFF.astype(np.int64)
        si, sj = self.sizes[:, None], self.sizes[None, :]
        ib, jb = beyond > 0, beyond.T > 0
        M = np.full((self.nc, self.nc), EGAL, np.int8)
        M[si > sj] = CONTIENT  # no frank overhang either way: decide by ON-set size
        M[si < sj] = CONTENU
        M[ib & ~jb] = CONTIENT  # i frankly overhangs j, not the reverse
        M[jb & ~ib] = CONTENU
        M[ib & jb] = INCOHERENT  # both overhang: a genuine crossing
        M[overlap == 0] = DISJOINT  # never ON together: disjoint wins over all
        self.inter, self.beyond, self.matrix = overlap, beyond, M

    @staticmethod
    def _as_dense_bool(A):
        return np.asarray(A.toarray() if sp.issparse(A) else A, dtype=bool)

    def counts(self):
        iu, ju = np.triu_indices(self.nc, 1)
        c = self.matrix[iu, ju].copy()
        c[c == CONTIENT] = CONTENU
        return {
            "egal": int((c == EGAL).sum()),
            "emboite": int((c == CONTENU).sum()),
            "disjoint": int((c == DISJOINT).sum()),
            "incoherent": int((c == INCOHERENT).sum()),
        }

    def incoherent_pairs(self):
        iu, ju = np.triu_indices(self.nc, 1)
        m = self.matrix[iu, ju] == INCOHERENT
        return list(zip(iu[m].tolist(), ju[m].tolist()))

    def classify(self):
        """Label each marker: incoherent > co-support > laminar > isolated."""
        M, nc = self.matrix, self.nc
        offdiag = ~np.eye(nc, dtype=bool)
        has_inc = ((M == INCOHERENT) & offdiag).any(1)
        has_eq = ((M == EGAL) & offdiag).any(1)
        has_nest = (((M == CONTENU) | (M == CONTIENT)) & offdiag).any(1)
        classes = np.full(nc, "isole", dtype=object)
        classes[has_nest] = "laminaire"
        classes[has_eq & ~has_inc] = "co-support"
        classes[has_inc] = "incoherent"
        return classes

    def laminar(self, priority=None):
        """Greedy vertex cover on the crossing graph until zero incoherence.

        Relations depend only on present-sets, so dropping a third marker never
        changes the relation between two others: sub-indexing the matrix is exact.
        By default the most-crossing marker goes first. Passing `priority` (higher
        is better, aligned on the columns) instead builds the laminar set
        incrementally by decreasing priority, so a crossing is always paid for by
        the LESS trustworthy of the two markers, which is a principled tiebreak
        rather than a degree count.
        """
        INC = self.matrix == INCOHERENT
        if priority is None:
            keep = np.ones(self.nc, bool)
            removed = []
            while INC[np.ix_(keep, keep)].any():
                deg = (INC & keep[None, :]).sum(1) * keep
                v = int(np.argmax(deg))
                keep[v] = False
                removed.append(self.columns[v])
            return LaminarMask(self, np.where(keep)[0], removed)
        pr = np.asarray(priority, dtype=float)
        if len(pr) != self.nc:
            raise ValueError(f"{len(pr)} priorities for {self.nc} markers")
        accepted, removed, acc = [], [], np.zeros(self.nc, bool)
        for i in np.argsort(-pr, kind="stable"):
            i = int(i)
            if acc.any() and (INC[i] & acc).any():
                removed.append(self.columns[i])
            else:
                accepted.append(i)
                acc[i] = True
        return LaminarMask(self, np.sort(np.asarray(accepted, dtype=int)), removed)

    def laminar_strain_level(self, tolerance=0.05, max_iter=None):
        """Resolve crossings by dropping the few MINORITY TAXA that break them,
        instead of dropping an entire marker (`laminar`).

        A crossing (i, j) has a `fragility` (`explain_crossing`): the smaller of
        its two frank overhangs, i.e. the number of taxa on the side that would
        have to disappear for the pair to stop crossing. When that number is
        small relative to the marker's own size, it reads as a handful of
        exceptional taxa (a sequencing accident, a mixed sample, or a genuine
        but marginal sub-signal) rather than a real topological objection to
        either marker — P12.6.1 on `coclustering_lineages` found the MAJORITY
        side forming a clean sub-clade on an independent ML tree in 3/3 spot
        checks of severe crossings, with the minority typically < 1% of the
        witness pool. Dropping just those taxa from the smaller side's
        present-set keeps both markers instead of sacrificing one whole marker
        for the sake of a few outliers, which is what `laminar()` does.

        `tolerance`: a crossing is eligible for strain-level repair when its
        fragility is at most `tolerance` (an absolute taxon count if
        `tolerance >= 1`) or at most `tolerance * min(size_i, size_j)` (a
        fraction, if `tolerance < 1`). Crossings above the threshold are left
        untouched — this is a first pass, not a replacement for `laminar()`:
        call it on `.remaining` for whatever is left.

        Returns a `StrainLevelResult`.
        """
        ON = self.present.copy()
        exceptions: list[tuple[int, int]] = []
        resolved: list[tuple[int, int, int]] = []
        rel = self
        iteration = 0
        while True:
            iteration += 1
            pairs = rel.incoherent_pairs()
            if not pairs:
                break
            progressed = False
            for i, j in pairs:
                d = explain_crossing(rel, i, j)
                frag = d["fragility"]
                thr = tolerance if tolerance >= 1 else tolerance * min(d["n_i"], d["n_j"])
                if frag > thr or frag == 0:
                    continue
                ONi, ONj = rel.present[:, i], rel.present[:, j]
                i_is_smaller = d["only_i"] <= d["only_j"]
                side_mask = (ONi & ~ONj) if i_is_smaller else (ONj & ~ONi)
                marker_idx = i if i_is_smaller else j
                for t in np.where(side_mask)[0]:
                    ON[t, marker_idx] = False
                    exceptions.append((int(t), marker_idx))
                resolved.append((i, j, int(frag)))
                progressed = True
            if not progressed:
                break
            rel = RelationMask(ON, columns=self.columns)
            if max_iter and iteration >= max_iter:
                break
        return StrainLevelResult(
            present=ON, columns=self.columns, exceptions=exceptions,
            resolved=resolved, remaining=rel,
        )

    def __len__(self):
        return self.nc

    def __repr__(self):
        c = self.counts()
        return (
            f"RelationMask({self.nc} markers, {self.nb} taxa; nested {c['emboite']}, "
            f"crossing {c['incoherent']}, disjoint {c['disjoint']}, equal {c['egal']})"
        )


class LaminarMask:
    """The crossing-free sub-matrix, plus the list of markers sacrificed for it."""

    def __init__(self, source, keep_idx, removed_cols):
        keep_idx = np.asarray(keep_idx, dtype=int)
        self.source = source
        self.matrix = source.matrix[np.ix_(keep_idx, keep_idx)].copy()
        self.present = source.present[:, keep_idx].copy()
        self.columns = [source.columns[i] for i in keep_idx]
        self.sizes = np.asarray(source.sizes)[keep_idx].astype(np.int64)
        self.removed = list(removed_cols)
        self.nc = len(self.columns)
        if (self.matrix == INCOHERENT).any():
            raise AssertionError("LaminarMask still holds a crossing")

    def __len__(self):
        return self.nc

    def __repr__(self):
        return f"LaminarMask({self.nc} laminar markers, {len(self.removed)} removed)"


class StrainLevelResult:
    """Output of `RelationMask.laminar_strain_level`.

    Attributes
    ----------
    present : (n_taxa, n_markers) bool
        The ON matrix with exception cells cleared. Same shape as the input:
        no marker or taxon is dropped, only individual cells.
    columns : the marker identifiers, unchanged.
    exceptions : list[(taxon_idx, marker_idx)]
        Every cell cleared to resolve a crossing — the traceability trail.
    resolved : list[(marker_i, marker_j, fragility)]
        Crossings fixed this way, with the fragility they were resolved at.
    remaining : RelationMask
        Relations recomputed on `present`. Crossings above tolerance (or
        created by interactions between repairs) are still there: run
        `.laminar()` on this for a standard marker-level cleanup of whatever
        is left.
    """

    def __init__(self, present, columns, exceptions, resolved, remaining):
        self.present = present
        self.columns = list(columns)
        self.exceptions = exceptions
        self.resolved = resolved
        self.remaining = remaining

    def __repr__(self):
        n_left = len(self.remaining.incoherent_pairs())
        return (
            f"StrainLevelResult({len(self.resolved)} crossing(s) resolved, "
            f"{len(self.exceptions)} taxon-marker exception(s), {n_left} crossing(s) remaining)"
        )


# --------------------------------------------------------------------------- #
# Tree                                                                        #
# --------------------------------------------------------------------------- #
class LaminarTree:
    """Read a laminar marker set as an UNROOTED tree.

    Frank present-sets do not nest strictly (a descendant can be ON where its
    ancestor is UNKNOWN), so frank-containment is not even an order: it can cycle.
    We therefore condense the strongly-connected components of the `c <= d` graph,
    then close each component downwards. The reference (all-absent, H37Rv here) is
    the frame, NOT the ancestor: the tree stays unrooted.
    """

    def __init__(self, lam, labels=None):
        present = np.asarray(lam.present, dtype=bool)
        self.n_taxa = int(present.shape[0])
        self.universe = frozenset(range(self.n_taxa))
        self.removed = list(lam.removed)
        self.n_laminar = int(lam.nc)
        self.labels = list(labels) if labels is not None else list(range(self.n_taxa))
        cols = list(lam.columns)
        nc = present.shape[1]
        ON = [frozenset(np.where(present[:, c])[0].tolist()) for c in range(nc)]

        adj = (lam.matrix == CONTENU) | (lam.matrix == EGAL)
        np.fill_diagonal(adj, False)
        ncomp, comp = connected_components(sp.csr_matrix(adj), directed=True, connection="strong")
        comp_on = [set() for _ in range(ncomp)]
        comp_cols = [[] for _ in range(ncomp)]
        for c in range(nc):
            comp_on[comp[c]] |= ON[c]
            comp_cols[comp[c]].append(c)
        preds = {v: set() for v in range(ncomp)}
        succ = {u: set() for u in range(ncomp)}
        ii, jj = np.where(adj)
        for c, d in zip(ii.tolist(), jj.tolist()):
            u, v = int(comp[c]), int(comp[d])
            if u != v:
                preds[v].add(u)
                succ[u].add(v)

        indeg = {v: len(preds[v]) for v in range(ncomp)}
        q = deque(v for v in range(ncomp) if indeg[v] == 0)
        closed: dict[int, set] = {}
        while q:
            u = q.popleft()
            s = set(comp_on[u])
            for w in preds[u]:
                s |= closed[w]
            closed[u] = s
            for v in succ[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)

        self.clade_markers = defaultdict(list)
        for v in range(ncomp):
            cl = frozenset(closed.get(v, ()))
            if cl:
                self.clade_markers[cl].extend(cols[c] for c in comp_cols[v])
        self.clades = sorted(
            (cl for cl in self.clade_markers if 0 < len(cl) < self.n_taxa), key=len
        )
        self.parent = {}
        for s in self.clades:
            sup = [t for t in self.clades if s < t]
            self.parent[s] = min(sup, key=len) if sup else self.universe
        self.children = defaultdict(list)
        for s in self.clades:
            self.children[self.parent[s]].append(s)
        self.branches = self.children[self.universe]

    @property
    def n_crossings(self):
        cl = self.clades
        return sum(
            1
            for i in range(len(cl))
            for j in range(i + 1, len(cl))
            if (cl[i] & cl[j]) and not (cl[i] <= cl[j] or cl[j] <= cl[i])
        )

    def smallest_clade(self):
        return {
            b: min((t for t in self.clades if b in t), key=len, default=self.universe)
            for b in range(self.n_taxa)
        }

    def newick(self, weights=None):
        """Unrooted Newick. Unary nodes are suppressed: a clade holding a single
        part is not a branching point, so we emit the part directly."""
        own = defaultdict(list)
        sm = self.smallest_clade()
        for b in range(self.n_taxa):
            own[sm[b]].append(b)

        def leaf(b):
            name = str(self.labels[b]).replace(",", "_").replace(":", "_").replace(" ", "_")
            return f"{name}:{int(weights[b])}" if weights is not None else name

        def emit(node):
            parts = [leaf(b) for b in own[node]]
            parts += [emit(c) for c in sorted(self.children[node], key=lambda t: -len(t))]
            return parts[0] if len(parts) == 1 else "(" + ",".join(parts) + ")"

        return emit(self.universe) + ";"

    def __repr__(self):
        return (
            f"LaminarTree({self.n_laminar} laminar markers, {len(self.clades)} clades, "
            f"{len(self.branches)} branches, {len(self.removed)} removed, "
            f"{self.n_crossings} residual crossings)"
        )


# --------------------------------------------------------------------------- #
# Why does it cross?                                                          #
# --------------------------------------------------------------------------- #
def explain_crossing(rel: RelationMask, i: int, j: int, taxa_labels=None, max_witnesses=12):
    """Diagnose one crossing: how fragile it is, and which taxa carry it.

    `fragility` is `min(overhang_ij, overhang_ji)`: the smaller side is the number
    of taxa whose removal would kill the conflict. A fragility of 1 or 2 is one
    sequencing accident or one contaminated strain, not a phylogenetic signal; a
    fragility in the hundreds is a real topological disagreement. The witnesses
    are exactly those taxa, so the claim is checkable by hand.
    """
    ON = rel.present
    ONi, ONj = ON[:, i], ON[:, j]
    OFFj = ~ONj if rel.beyond is None else None
    # recompute frank OFF from the stored overhang convention
    both = np.where(ONi & ONj)[0]
    only_i = np.where(ONi & ~ONj)[0]
    only_j = np.where(ONj & ~ONi)[0]
    del OFFj
    frag = int(min(len(only_i), len(only_j)))
    side = only_i if len(only_i) <= len(only_j) else only_j
    lab = (lambda k: str(taxa_labels[k])) if taxa_labels is not None else str
    return {
        "marker_i": rel.columns[i],
        "marker_j": rel.columns[j],
        "n_i": int(ONi.sum()),
        "n_j": int(ONj.sum()),
        "shared": int(len(both)),
        "only_i": int(len(only_i)),
        "only_j": int(len(only_j)),
        "fragility": frag,
        "witnesses": [lab(k) for k in side[:max_witnesses]],
        "witnesses_truncated": bool(len(side) > max_witnesses),
    }
