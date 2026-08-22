#!/usr/bin/env python3
"""CLI: check whether a marker set is compatible with a tree, and diagnose the conflicts.

Two ways in:

  --pool bdd/actuelle/L6 [--markers barcode_complete.tsv --prefix L6]
      Strains are every `<dir>/<strain>/NC_000962.3/spdi.txt` found recursively
      under the pool. Markers are either the barcode entries whose entity starts
      with `--prefix`, or (without `--markers`) every SPDI carried by at least
      `--min-carriers` strains.

  --matrix DIR
      A directory holding `matrix.npz` + `strains.txt` + `markers.txt`.

Outputs a report on stdout, and with `--out DIR`: report.json, crossings.tsv,
laminar_tree.nwk, removed_markers.txt.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import scipy.sparse as sp

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser import write_browser  # noqa: E402
from coverage3 import (  # noqa: E402
    build_unknown_mask,
    load_gene_intervals,
    position_to_gene,
    spdi_positions,
)
from laminarity import (  # noqa: E402
    LaminarTree,
    RelationMask,
    combinatorial_bound,
    dedupe_profiles,
    dedupe_taxa,
    explain_crossing,
)


def load_pool(pool: Path, chrom="NC_000962.3", seen=None):
    """Every strain under `pool`, recursively, with its SPDI set and its directory.

    Deduplicates on strain NAME, and it is not a precaution: `bdd/actuelle` holds
    strains stored twice under a doubled path, `<clade>/<strain>/<strain>/<chrom>/`
    alongside `<clade>/<strain>/<chrom>/`, with identical content (23 such cases in
    L6 alone, verified 2026-08-10). A plain rglob counts those strains twice and
    silently doubles their weight.
    """
    seen = set() if seen is None else seen
    strains, profiles, dirs = [], [], []
    for f in sorted(pool.rglob(f"*/{chrom}/spdi.txt")):
        name = f.parent.parent.name
        if name in seen:
            continue
        seen.add(name)
        strains.append(name)
        dirs.append(f.parent.parent)
        profiles.append({ln.strip() for ln in f.read_text().splitlines() if ln.strip()})
    return strains, profiles, dirs


def barcode_markers(tsv: Path, prefix: str):
    """SPDI listed as positive markers for entities starting with `prefix`."""
    out: dict[str, list[str]] = defaultdict(list)
    with tsv.open() as fh:
        header = fh.readline().rstrip("\n").split("\t")
        ie, isp, iro = header.index("entity"), header.index("spdi"), header.index("role")
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) <= max(ie, isp, iro):
                continue
            if p[iro] == "positive" and p[ie].startswith(prefix):
                out[p[isp]].append(p[ie])
    return out


def load_excluded_positions(files):
    """Positions to drop before anything else: one integer per line (files like
    `traces_mask_positions.txt` / `resistance_positions.txt` in mtbc/global_supplementary/
    traces_mask). Distinct from `--gff3` three-state UNKNOWN: this is a flat blacklist of
    KNOWN-bad positions (homoplasy, PE/PPE, IS, resistance), applied BEFORE min-carriers.
    """
    positions: set[int] = set()
    for f in files:
        for line in f.read_text().splitlines():
            line = line.strip()
            if line.isdigit():
                positions.add(int(line))
    return positions


def spdi_pos(spdi: str) -> int:
    try:
        return int(spdi.split(":")[1])
    except (IndexError, ValueError):
        return -1


def build(strains, profiles, marker_list, min_carriers):
    if marker_list is None:
        cnt: dict[str, int] = defaultdict(int)
        for pr in profiles:
            for s in pr:
                cnt[s] += 1
        marker_list = sorted(s for s, c in cnt.items() if c >= min_carriers)
    idx = {s: j for j, s in enumerate(marker_list)}
    rows, cols = [], []
    for i, pr in enumerate(profiles):
        for s in pr:
            j = idx.get(s)
            if j is not None:
                rows.append(i)
                cols.append(j)
    X = sp.csr_matrix(
        (np.ones(len(rows), np.int8), (np.asarray(rows), np.asarray(cols))),
        shape=(len(strains), len(marker_list)),
    )
    X.data[:] = 1
    return X, marker_list


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--pool",
        type=Path,
        action="append",
        help="repeatable: a lineage lives in sibling directories (L6, L6.1, L6.2...), "
        "not nested under one, so pass them all",
    )
    src.add_argument("--matrix", type=Path)
    src.add_argument(
        "--fit",
        type=Path,
        help="a binary-coclustering fit directory (fit.npz). Reads the LBM's own three "
        "states off alpha: ON > --on-thr, OFF < 1 - --on-thr, the band between is UNKNOWN. "
        "This is the recommended way to turn a co-clustering into candidate clades: the "
        "taxonomic unit is the present-set of a MARKER BLOCK over the strain blocks, never "
        "a strain block taken alone",
    )
    ap.add_argument("--on-thr", type=float, default=0.9, help="with --fit: the ON threshold on alpha")
    ap.add_argument("--markers", type=Path, help="barcode_complete.tsv")
    ap.add_argument("--prefix", default="", help="entity prefix in the barcode")
    ap.add_argument("--min-carriers", type=int, default=3)
    ap.add_argument(
        "--exclude-positions",
        type=Path,
        action="append",
        help="repeatable: file of known-bad positions (one integer per line, e.g. "
        "mtbc/global_supplementary/traces_mask/traces_mask_positions.txt + "
        "resistance_positions.txt), dropped from every profile before min-carriers. "
        "Without it, --pool reads raw unmasked SPDI, which on an MTBC pool is dominated "
        "by PE/PPE, IS and resistance homoplasy and produces a crossing count that "
        "mostly has nothing to do with any specific candidate clade (verified: on a "
        "32-strain Bovis pool, masking cut present-sets 292->92 and crossings against a "
        "known-clean 5-strain candidate 129->20, most of the residual at fragility <=2).",
    )
    ap.add_argument("--max-markers", type=int, default=6000, help="cap after deduplication")
    ap.add_argument("--top-crossings", type=int, default=25)
    ap.add_argument(
        "--strain-level",
        action="store_true",
        help="P12.6.1.2 (coclustering_lineages): before the standard marker-removal "
        "laminarisation, drop the few minority TAXA that break a crossing instead of the "
        "whole marker, for crossings whose fragility is within --strain-tolerance. Only the "
        "markers still crossing afterwards go through the usual whole-marker removal. "
        "Recovers present-sets that laminar() would otherwise sacrifice for a handful of "
        "exceptional taxa -- but note that with --fit, taxa are STRAIN BLOCKS: an exception "
        "drops a whole block, not an individual real strain. For real-strain-resolution "
        "cleanup, build a real-strain x aggregate-marker matrix and pass it via --matrix.",
    )
    ap.add_argument(
        "--strain-tolerance",
        type=float,
        default=0.05,
        help=">=1: absolute taxon count. <1: fraction of the smaller marker's size. "
        "A crossing is repaired at strain level only when its fragility is at or below "
        "this budget (default 0.05, i.e. 5%% of the smaller marker).",
    )
    ap.add_argument("--out", type=Path)
    ap.add_argument(
        "--gff3",
        type=Path,
        help="H37Rv GFF3; enables THREE-STATE mode, where a SPDI sitting in a gene "
        "this strain has no coverage for is UNKNOWN instead of absent",
    )
    ap.add_argument("--max-missing", type=float, default=0.10)
    ap.add_argument("--min-depth", type=float, default=5.0)
    ap.add_argument("--coverage-cache", type=Path)
    a = ap.parse_args()

    UNK_pre = None  # three-state mask when reading a fit
    nb_strains = None  # strains behind each strain block, likewise
    if a.pool:
        strains, profiles, strain_dirs = [], [], []
        seen: set[str] = set()  # shared across pools: a strain must be counted once
        for p in a.pool:
            s, pr, dd = load_pool(p, seen=seen)
            strains += s
            profiles += pr
            strain_dirs += dd
        if not strains:
            print(f"no strain under {', '.join(str(p) for p in a.pool)}", file=sys.stderr)
            return 1
        if a.exclude_positions:
            excluded = load_excluded_positions(a.exclude_positions)
            before = sum(len(pr) for pr in profiles)
            profiles = [{s for s in pr if spdi_pos(s) not in excluded} for pr in profiles]
            after = sum(len(pr) for pr in profiles)
            print(
                f"--exclude-positions: {len(excluded)} position(s) loaded, "
                f"{before - after} SPDI occurrence(s) dropped ({100 * (before - after) / max(before, 1):.0f}%)",
                file=sys.stderr,
            )
        mk = None
        marker_entity = {}
        if a.markers:
            bm = barcode_markers(a.markers, a.prefix)
            mk = sorted(bm)
            marker_entity = {s: ",".join(sorted(set(v))) for s, v in bm.items()}
        X, markers = build(strains, profiles, mk, a.min_carriers)
    elif a.fit:
        f = np.load(a.fit / "fit.npz")
        alpha, w, z = f["alpha"], f["w"], f["z"]
        used = sorted(set(int(v) for v in z))
        sizes = np.bincount(np.asarray(w), minlength=alpha.shape[1])
        live_mb = np.where(sizes > 0)[0]
        A = alpha[np.ix_(used, live_mb)]
        on, off = A > a.on_thr, A < (1.0 - a.on_thr)
        strains = [f"block{b}" for b in used]  # taxa are STRAIN BLOCKS here
        markers = [f"mb{int(j)}({int(sizes[j])})" for j in live_mb]
        X = sp.csr_matrix(on.astype(np.int8))
        UNK_pre = sp.csr_matrix((~on & ~off).astype(np.int8))
        marker_entity = {}
        strain_dirs = None
        nb_strains = np.bincount(np.asarray(z), minlength=alpha.shape[0])[used]
        print(f"from fit       {len(used)} strain blocks, {len(live_mb)} marker blocks")
        print(
            f"               alpha cells: ON {int(on.sum())} ({100*on.mean():.1f}%)  "
            f"OFF {int(off.sum())} ({100*off.mean():.1f}%)  "
            f"UNKNOWN {int((~on & ~off).sum())} ({100*(~on & ~off).mean():.1f}%)"
            "   <- if UNKNOWN dominates, laminarity is bought with ignorance"
        )
    else:
        X = sp.load_npz(a.matrix / "matrix.npz")
        strains = (a.matrix / "strains.txt").read_text().split()
        markers = (a.matrix / "markers.txt").read_text().split()
        marker_entity = {}
        strain_dirs = None

    n0, k0 = X.shape
    carriers = np.asarray(X.sum(0)).ravel()
    live = np.where(carriers > 0)[0]
    X, markers = X[:, live].tocsr(), [markers[j] for j in live]

    UNK = None
    if UNK_pre is not None:
        UNK = UNK_pre[:, live].tocsr()
    if a.gff3:
        if strain_dirs is None:
            print("--gff3 needs --pool (report.json lives next to spdi.txt)", file=sys.stderr)
            return 1
        starts, ends, tags = load_gene_intervals(a.gff3)
        gi = position_to_gene(spdi_positions(markers), starts, ends)
        print(
            f"three-state    {int((gi >= 0).sum())}/{len(markers)} markers mapped to a gene; "
            f"intergenic markers stay frankly absent"
        )
        UNK = build_unknown_mask(
            strain_dirs,
            spdi_positions(markers),
            gi,
            tags,
            max_missing=a.max_missing,
            min_depth=a.min_depth,
            cache=a.coverage_cache,
        )
        UNK = UNK.multiply(X == 0).tocsr()  # a called SPDI is never unknown
        print(
            f"               UNKNOWN cells {UNK.nnz} "
            f"({100*UNK.nnz/(X.shape[0]*max(X.shape[1],1)):.2f}% of the matrix)"
        )

    Xt, taxa_groups = dedupe_taxa(X)
    Xu, marker_groups = dedupe_profiles(Xt)
    # with --fit a taxon is a strain BLOCK, so its weight is its strain count,
    # not the number of merged taxa
    weights = (
        np.array([int(nb_strains[list(g)].sum()) for g in taxa_groups])
        if nb_strains is not None
        else np.array([len(g) for g in taxa_groups])
    )
    labels = [strains[g[0]] for g in taxa_groups]

    UNKu = None
    if UNK is not None:
        # a taxon merges several strains: it is unknown only where ALL of them are,
        # which is the conservative choice (it keeps as much frank OFF as possible)
        rows = []
        for g in taxa_groups:
            sub = UNK[g, :]
            rows.append((np.asarray(sub.sum(0)).ravel() == len(g)).astype(np.int8))
        UNKu = sp.csr_matrix(np.vstack(rows))[:, [g[0] for g in marker_groups]]

    bound = combinatorial_bound(Xu.shape[1], Xt.shape[0])

    print(f"strains        {n0}  -> {Xt.shape[0]} distinct profiles")
    print(f"markers        {k0}  -> {len(markers)} carried -> {Xu.shape[1]} distinct present-sets")
    print(
        f"combinatorial  {bound['distinct_present_sets']} present-sets for at most "
        f"{bound['max_clades_on_tree']} clades on a tree "
        f"-> excess {bound['excess']}"
        + ("  PROVABLY INCOMPATIBLE" if bound["provably_incompatible"] else "  (no free verdict)")
    )

    if Xu.shape[1] > a.max_markers:
        keep = np.argsort(-np.asarray(Xu.sum(0)).ravel())[: a.max_markers]
        keep.sort()
        print(
            f"  capped to the {a.max_markers} largest present-sets "
            f"(pairwise matrix is O(k^2)); rerun with --max-markers to widen"
        )
        Xu = Xu[:, keep].tocsc()
        marker_groups = [marker_groups[j] for j in keep]
        if UNKu is not None:
            UNKu = UNKu[:, keep]

    off = None
    if UNKu is not None:
        ON = np.asarray(Xu.toarray(), dtype=bool)
        off = ~ON & ~np.asarray(UNKu.toarray(), dtype=bool)
    rel = RelationMask(Xu, columns=[markers[g[0]] for g in marker_groups], off=off)
    counts = rel.counts()
    classes = rel.classify()
    pairs = rel.incoherent_pairs()
    print(
        f"relations      nested {counts['emboite']}  disjoint {counts['disjoint']}  "
        f"equal {counts['egal']}  CROSSING {counts['incoherent']}"
    )
    ncls = {c: int((classes == c).sum()) for c in ("laminaire", "co-support", "incoherent", "isole")}
    print(f"markers        {ncls}")

    diags = sorted(
        (explain_crossing(rel, i, j, taxa_labels=labels) for i, j in pairs),
        key=lambda d: d["fragility"],
    )
    if diags:
        frag = np.array([d["fragility"] for d in diags])
        print(
            f"fragility      min {frag.min()}  median {int(np.median(frag))}  max {frag.max()}  "
            f"| {int((frag <= 2).sum())}/{len(frag)} crossings hang on <= 2 strains"
        )
        print(f"\ntop {min(a.top_crossings, len(diags))} most fragile crossings:")
        for d in diags[: a.top_crossings]:
            ei = marker_entity.get(d["marker_i"], "")
            ej = marker_entity.get(d["marker_j"], "")
            print(
                f"  frag={d['fragility']:5d}  {d['marker_i']} ({d['n_i']}) x "
                f"{d['marker_j']} ({d['n_j']})  shared={d['shared']}"
                + (f"  [{ei} | {ej}]" if ei or ej else "")
            )
            print(f"       witnesses: {', '.join(d['witnesses'])}")

    sl = None
    lam_source = rel
    if a.strain_level:
        sl = rel.laminar_strain_level(tolerance=a.strain_tolerance)
        lam_source = sl.remaining
        n_left = len(sl.remaining.incoherent_pairs())
        print(
            f"\nstrain-level   {len(sl.resolved)}/{len(pairs)} crossing(s) repaired by dropping "
            f"{len(sl.exceptions)} taxon-marker exception(s) (tolerance={a.strain_tolerance})"
            + ("  <- taxa are STRAIN BLOCKS here (--fit)" if nb_strains is not None else "")
        )
        print(f"               {n_left} crossing(s) left for standard marker-level removal")

    lam = lam_source.laminar()
    tree = LaminarTree(lam, labels=labels)
    print(
        f"\nlaminarisation {rel.nc} -> {lam.nc} markers "
        f"({len(lam.removed)} removed, {100*len(lam.removed)/max(rel.nc,1):.1f}%)"
    )
    print(f"tree           {len(tree.clades)} clades, {len(tree.branches)} basal branches")

    if a.out:
        a.out.mkdir(parents=True, exist_ok=True)
        report = {
            "n_strains": n0,
            "n_distinct_taxa": int(Xt.shape[0]),
            "n_markers": k0,
            "n_distinct_present_sets": int(Xu.shape[1]),
            "combinatorial_bound": bound,
            "relation_counts": counts,
            "marker_classes": ncls,
            "n_crossings": len(pairs),
            "n_removed_for_laminarity": len(lam.removed),
            "n_clades": len(tree.clades),
            "n_basal_branches": len(tree.branches),
            "residual_crossings": tree.n_crossings,
        }
        if sl is not None:
            report["strain_level"] = {
                "tolerance": a.strain_tolerance,
                "taxa_are_strain_blocks": nb_strains is not None,
                "n_crossings_resolved": len(sl.resolved),
                "n_taxon_marker_exceptions": len(sl.exceptions),
                "n_crossings_left_for_marker_removal": len(sl.remaining.incoherent_pairs()),
            }
        (a.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        if sl is not None:
            with (a.out / "strain_exceptions.tsv").open("w") as fh:
                fh.write("taxon\tmarker\n")
                for t, m in sl.exceptions:
                    fh.write(f"{labels[t]}\t{lam_source.columns[m]}\n")
        with (a.out / "crossings.tsv").open("w") as fh:
            fh.write("fragility\tmarker_i\tn_i\tmarker_j\tn_j\tshared\tonly_i\tonly_j\twitnesses\n")
            for d in diags:
                fh.write(
                    f"{d['fragility']}\t{d['marker_i']}\t{d['n_i']}\t{d['marker_j']}\t{d['n_j']}\t"
                    f"{d['shared']}\t{d['only_i']}\t{d['only_j']}\t{','.join(d['witnesses'])}\n"
                )
        (a.out / "laminar_tree.nwk").write_text(tree.newick(weights=weights) + "\n")
        (a.out / "removed_markers.txt").write_text("\n".join(str(c) for c in lam.removed) + "\n")

        # linked browser: the reduced matrix, never the raw one (see browser.py)
        ON = np.asarray(Xu.toarray(), dtype=bool)
        state = ON.astype(np.uint8)
        if UNKu is not None:
            state[np.asarray(UNKu.toarray(), dtype=bool) & ~ON] = 2
        col_of = {c: j for j, c in enumerate(rel.columns)}
        clades = tree.clades
        clade_rows = [sorted(c) for c in clades]
        clade_markers = [
            [col_of[m] for m in tree.clade_markers[c] if m in col_of] for c in clades
        ]
        clade_weight = [int(weights[list(c)].sum()) for c in clades]
        marker_clade = np.full(rel.nc, -1, dtype=int)
        for ci, ms in enumerate(clade_markers):
            for j in ms:
                marker_clade[j] = ci
        depth = {}
        for ci, c in enumerate(clades):
            d, p = 0, tree.parent.get(c)
            while p is not None and p != tree.universe:
                d += 1
                p = tree.parent.get(p)
            depth[ci] = d
        order = sorted(range(len(clades)), key=lambda ci: (-len(clades[ci]), ci))
        write_browser(
            a.out / "browser.html",
            state=state,
            rel=rel.matrix,
            markers=rel.columns,
            marker_class=list(classes),
            marker_size=rel.sizes,
            marker_clade=marker_clade,
            clade_rows=clade_rows,
            clade_markers=clade_markers,
            clade_weight=clade_weight,
            tree_order=[{"i": ci, "depth": depth[ci]} for ci in order],
            title=f"marker-laminarity — {a.prefix or (a.matrix.name if a.matrix else 'pool')}",
            subtitle=(
                f"{n0} strains &rarr; {Xt.shape[0]} profiles · {rel.nc} distinct present-sets · "
                f"{len(pairs)} crossings · {len(tree.clades)} clades"
            ),
        )
        print(f"\nwritten to {a.out}   (open browser.html over file://)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
