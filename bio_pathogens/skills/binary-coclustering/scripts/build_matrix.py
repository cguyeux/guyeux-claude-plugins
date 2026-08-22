#!/usr/bin/env python3
"""Build a binary strain x SPDI matrix from a `bdd/actuelle` lineage pool.

Reads every `<pool>/<strain>/NC_000962.3/spdi.txt`, keeps the SPDI whose carrier
count falls inside `[min_carriers, n - min_carriers]` (a variant carried by
everybody or by almost nobody separates nothing), and writes a CSR matrix.

The carrier floor is the *ceiling on resolution*: a subclade of k strains is
structurally invisible to a run whose floor is above k. The upstream repository
defaults to 100 carriers, which is far too coarse for our pools; the default
here is 3.

Outputs (in `--out`):
  matrix.npz     scipy CSR, rows = strains, cols = SPDI
  strains.txt    row labels, one per line
  markers.txt    column labels (SPDI strings), one per line
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp


def read_pool(pool: Path, chrom: str = "NC_000962.3"):
    """Return (strains, list-of-SPDI-lists, missing) for every strain under `pool`.

    Recursive on purpose: a lineage lives in sibling directories (`L6`, `L6.1`,
    `L6.2`...), and a flattened pool holds its strains directly. Both shapes are
    handled by walking down to `*/<chrom>/spdi.txt`.
    """
    strains, profiles, missing = [], [], []
    seen = set()
    for f in sorted(pool.rglob(f"*/{chrom}/spdi.txt")):
        name = f.parent.parent.name
        if name.startswith("_") or name in seen:
            continue
        seen.add(name)
        strains.append(name)
        profiles.append([ln.strip() for ln in f.read_text().splitlines() if ln.strip()])
    for d in sorted(p for p in pool.iterdir() if p.is_dir() and not p.name.startswith("_")):
        if not (d / chrom / "spdi.txt").is_file() and d.name not in seen:
            missing.append(d.name)
    return strains, profiles, missing


def build_on_vocabulary(strains, profiles, markers):
    """CSR matrix over an IMPOSED marker vocabulary, in that exact order.

    Required to place new strains on a frozen model: the columns must line up with
    the ones the model was fitted on, so no carrier filter and no reordering here.
    Markers the new strains do not carry stay empty columns, which is the correct
    representation — the model will read them as absences.
    """
    idx = {s: j for j, s in enumerate(markers)}
    rows, cols = [], []
    for i, spdi in enumerate(profiles):
        for s in spdi:
            j = idx.get(s)
            if j is not None:
                rows.append(i)
                cols.append(j)
    X = sp.csr_matrix(
        (np.ones(len(rows), dtype=np.int8), (np.asarray(rows), np.asarray(cols))),
        shape=(len(strains), len(markers)),
    )
    X.data[:] = 1
    return X


def build(strains, profiles, min_carriers: int):
    """CSR matrix with the carrier filter applied on both tails."""
    vocab: dict[str, int] = {}
    rows, cols = [], []
    for i, spdi in enumerate(profiles):
        for s in spdi:
            j = vocab.get(s)
            if j is None:
                j = len(vocab)
                vocab[s] = j
            rows.append(i)
            cols.append(j)
    n, d = len(strains), len(vocab)
    X = sp.csr_matrix(
        (np.ones(len(rows), dtype=np.int8), (np.asarray(rows), np.asarray(cols))),
        shape=(n, d),
    )
    X.data[:] = 1  # duplicate SPDI lines in a file must not become a 2
    carriers = np.asarray(X.sum(0)).ravel()
    keep = np.where((carriers >= min_carriers) & (carriers <= n - min_carriers))[0]
    inv = {j: s for s, j in vocab.items()}
    markers = [inv[int(j)] for j in keep]
    return X[:, keep].tocsr(), markers, carriers


def report_redundancy(X) -> dict:
    """Report where the matrix is redundant. Printed at build time on purpose.

    Two sessions spent hours in 2026-08 reasoning about "pseudo-replication" on the wrong
    axis, because this was never measured up front. The numbers are cheap here and they
    govern three later decisions, so they are no longer optional:

    - ROWS are essentially never duplicated at a low carrier floor: 8 744 L3 strains give
      8 744 distinct profiles, 1 364 L6 strains give 1 363. A handful of low-frequency
      markers individualises every strain. The `(g-1)/2 log n` ICL term is therefore fine.
    - COLUMNS are massively redundant: 72 100 L3 markers for 19 728 distinct present-sets,
      Kish d_eff = 2 642, largest co-segregating group 157 markers for ONE evolutionary
      event. The log-likelihood sums over columns, so that event counts 157 times, while
      the penalty only sees `d` through logarithms. ICL is thus biased toward MORE blocks
      than the data support — do not pick `m` on raw ICL alone.
    - The compression is in RARE markers, so it buys far less compute than the column count
      suggests: dropping 72.6 % of L3 columns removes only 4.4 % of the non-zeros (the dropped
      columns average 10.4 carriers, the kept ones 598.3), and the dominant EM term is
      O(nnz.(g+m)), not O(d.g.m). Measured: 25 % faster on L3, 34 % on L6, never the 3.7x the
      column count suggests.

    Hence the predictive criterion, which spares building the deduplicated matrix to find out.
    Cost is `nnz.(g+m) + d.g.m` and deduplication only touches the second term, so it pays off
    only when `nnz/d << g.m/(g+m)`: mean carriers per marker small against the block dimensions.
    L3 gives 171 vs 75 and L6 87 vs 27 — the sparse term dominates both times. Deduplication
    would only really pay on a very sparse matrix fitted with large g and m.

    Deduplicating by present-set leaves `w` unchanged (it is a function of the present-set)
    but NOT `z`: the row E step sums over columns. On a clonal organism that multiplicity is
    branch-length information. Legitimate for SELECTING (g, m), a modelling choice for
    ESTIMATING `z`.
    """
    Xc = X.tocsc()
    seen: dict[bytes, int] = {}
    for j in range(Xc.shape[1]):
        key = np.sort(Xc.indices[Xc.indptr[j]:Xc.indptr[j + 1]]).astype(np.int64).tobytes()
        seen[key] = seen.get(key, 0) + 1
    sizes = np.array(list(seen.values()), dtype=float)
    d_eff = float(sizes.sum() ** 2 / (sizes ** 2).sum())
    Xr = X.tocsr()
    rows = {np.sort(Xr.indices[Xr.indptr[i]:Xr.indptr[i + 1]]).astype(np.int64).tobytes()
            for i in range(Xr.shape[0])}
    print(f"row profiles  {len(rows)} distinct / {X.shape[0]} strains"
          f"{'  (no duplication: row-side pseudo-replication is a myth here)' if len(rows) == X.shape[0] else ''}")
    print(f"present-sets  {len(seen)} distinct / {X.shape[1]} markers"
          f"   Kish d_eff={d_eff:.0f}   largest co-segregating group={int(sizes.max())}")
    carriers_per_marker = X.nnz / max(X.shape[1], 1)
    if len(seen) < X.shape[1]:
        print("              -> ICL is biased toward more blocks: do not pick m on raw ICL alone")
        # would deduplicating be worth it computationally? cost = nnz.(g+m) + d.g.m
        print(f"              -> dedup pays off only if nnz/d={carriers_per_marker:.0f} << g.m/(g+m); "
              f"e.g. g=120,m=200 gives 75 -> "
              f"{'worth it' if carriers_per_marker < 75 else 'NOT worth it, fit the full matrix'}")
    return {"row_profiles": len(rows), "present_sets": len(seen), "d_eff": d_eff,
            "largest_group": int(sizes.max()), "carriers_per_marker": carriers_per_marker}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "pool",
        type=Path,
        nargs="+",
        help="one or more pool directories: bdd/actuelle/L3, or bdd/actuelle/L6*",
    )
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--min-carriers", type=int, default=3)
    ap.add_argument("--chrom", default="NC_000962.3")
    ap.add_argument(
        "--vocabulary",
        type=Path,
        help="a markers.txt to reuse verbatim, instead of building one. Required when "
        "the matrix will be placed on a model fitted elsewhere (place_strains.py)",
    )
    a = ap.parse_args()

    strains, profiles, missing = [], [], []
    for p in a.pool:
        s, pr, ms = read_pool(p, a.chrom)
        strains += s
        profiles += pr
        missing += ms
    if not strains:
        print(f"no strain with a spdi.txt under {', '.join(map(str, a.pool))}", file=sys.stderr)
        return 1
    if a.vocabulary:
        markers = a.vocabulary.read_text().split()
        X = build_on_vocabulary(strains, profiles, markers)
        carriers = np.asarray(X.sum(0)).ravel()
    else:
        X, markers, carriers = build(strains, profiles, a.min_carriers)

    a.out.mkdir(parents=True, exist_ok=True)
    sp.save_npz(a.out / "matrix.npz", X)
    (a.out / "strains.txt").write_text("\n".join(strains) + "\n")
    (a.out / "markers.txt").write_text("\n".join(markers) + "\n")

    dens = X.nnz / (X.shape[0] * max(X.shape[1], 1))
    print(f"pool          {', '.join(map(str, a.pool[:3]))}"
          f"{f' (+{len(a.pool)-3} more)' if len(a.pool) > 3 else ''}")
    print(f"strains       {len(strains)}  (no spdi.txt: {len(missing)})")
    print(f"SPDI total    {len(carriers)}")
    print(f"SPDI kept     {X.shape[1]}  (carriers in [{a.min_carriers}, {len(strains)-a.min_carriers}])")
    print(f"matrix        {X.shape}  nnz={X.nnz}  density={dens:.5f}")
    report_redundancy(X)
    if missing[:5]:
        print(f"missing spdi  {', '.join(missing[:5])}{' ...' if len(missing) > 5 else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
