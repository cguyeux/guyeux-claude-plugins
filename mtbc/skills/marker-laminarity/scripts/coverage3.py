#!/usr/bin/env python3
"""Turn `report.json` per-gene coverage into the UNKNOWN mask that three-state needs.

Our `spdi.txt` files list presences only. A SPDI absent from a strain's file is
either genuinely absent or sitting in a region that was never covered, and
collapsing the two into "absent" is what manufactures four-gamete conflicts: a
lineage marker carried by 606 of 618 profiles crosses every subclade marker
merely because a dozen strains have a hole where it sits.

The information to tell them apart is already on disk. Each strain's
`report.json` carries `genes[]` with `percent_missing` and `mean_coverage` for
the 3 978 H37Rv genes. A SPDI whose position falls in a gene that is missing in
that strain is UNKNOWN, not absent.

Limits worth stating rather than hiding: the resolution is the GENE, not the
base, so a covered gene with a hole at the exact SPDI position still reads as
frankly absent; and an intergenic SPDI has no gene to ask, so its policy is
explicit (`--intergenic`), defaulting to absent.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import scipy.sparse as sp

GENE_RE = re.compile(r"locus_tag=([^;]+)")


def load_gene_intervals(gff3: Path):
    """`(starts, ends, locus_tags)` for every gene, sorted by start (1-based inclusive)."""
    starts, ends, tags = [], [], []
    with gff3.open() as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) < 9 or f[2] != "gene":
                continue
            m = GENE_RE.search(f[8])
            if not m:
                continue
            starts.append(int(f[3]))
            ends.append(int(f[4]))
            tags.append(m.group(1))
    order = np.argsort(np.asarray(starts))
    return (
        np.asarray(starts)[order],
        np.asarray(ends)[order],
        [tags[i] for i in order],
    )


def position_to_gene(positions, starts, ends):
    """Map each 1-based position to a gene index, or -1 when intergenic.

    Genes may overlap in H37Rv; `searchsorted` gives the last gene starting at or
    before the position, which is the right answer for the vast majority and never
    silently claims a hit outside the interval.
    """
    pos = np.asarray(positions, dtype=np.int64)
    k = np.searchsorted(starts, pos, side="right") - 1
    ok = (k >= 0) & (pos <= np.where(k >= 0, ends[np.clip(k, 0, len(ends) - 1)], -1))
    return np.where(ok, k, -1)


def strain_gene_coverage(report: Path, tag2idx, n_genes):
    """(percent_missing, mean_coverage) vectors over the reference gene order."""
    pm = np.zeros(n_genes, dtype=np.float16)
    dp = np.full(n_genes, np.inf, dtype=np.float16)
    d = json.loads(report.read_text())
    for g in d.get("genes", ()):
        j = tag2idx.get(g["locus_tag"])
        if j is None:
            continue
        pm[j] = min(float(g.get("percent_missing", 0.0)), 1.0)
        dp[j] = min(float(g.get("mean_coverage", 0.0)), 60000.0)
    return pm, dp


def build_unknown_mask(
    strain_dirs,
    marker_positions,
    marker_gene_idx,
    gene_tags,
    max_missing: float = 0.10,
    min_depth: float = 5.0,
    cache: Path | None = None,
    chrom: str = "NC_000962.3",
    verbose: bool = True,
):
    """(n_strains, n_markers) sparse bool: True where the strain cannot be asked.

    `cache` (an .npz path) stores the RAW per-gene coverage, not the thresholded
    result: each `report.json` is ~2 MB of JSON and a lineage has thousands of
    them, so re-reading them merely to try another threshold would make the
    sensitivity analysis unaffordable, which is exactly the analysis that decides
    whether the residual crossings are coverage artefacts or real signal.
    """
    tag2idx = {t: i for i, t in enumerate(gene_tags)}
    n, k = len(strain_dirs), len(marker_positions)
    ng = len(gene_tags)

    if cache is not None and cache.is_file():
        z = np.load(cache)
        PM, DP = z["percent_missing"], z["mean_coverage"]
        if PM.shape[0] != n:
            raise ValueError(f"cache holds {PM.shape[0]} strains, {n} requested; delete it")
    else:
        PM = np.zeros((n, ng), dtype=np.float16)
        DP = np.full((n, ng), np.inf, dtype=np.float16)
        for i, d in enumerate(strain_dirs):
            rep = Path(d) / chrom / "report.json"
            if not rep.is_file():
                continue
            PM[i], DP[i] = strain_gene_coverage(rep, tag2idx, ng)
            if verbose and (i + 1) % 500 == 0:
                print(f"    coverage: {i+1}/{n} reports read", flush=True)
        if cache is not None:
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(cache, percent_missing=PM, mean_coverage=DP)

    miss = sp.csr_matrix(
        (PM.astype(np.float32) > max_missing) | (DP.astype(np.float32) < min_depth)
    )

    # project gene-level missingness onto markers
    gi = np.asarray(marker_gene_idx)
    known = np.where(gi >= 0)[0]
    if known.size == 0:
        return sp.csr_matrix((n, k), dtype=bool)
    P = sp.csr_matrix(
        (np.ones(known.size, np.int8), (gi[known], known)),
        shape=(len(gene_tags), k),
    )
    return (miss @ P).astype(bool).tocsr()


def spdi_positions(markers):
    """Parse `NC_000962.3:position:ref:alt` into GFF3-compatible 1-based positions.

    SPDI positions are 0-BASED and GFF3 is 1-based inclusive, so this adds one.
    Not a detail: getting it wrong shifts every marker by one base and silently
    reassigns those sitting on a gene boundary. Verified on H37Rv rather than
    assumed: over 200 random SPDI from a real `spdi.txt`, the reference allele
    matches the NC_000962.3 sequence 200/200 read 0-based and 44/200 read 1-based
    (those 44 are homopolymers, where the shift is invisible).
    """
    out = []
    for s in markers:
        p = s.split(":")
        try:
            out.append(int(p[1]) + 1)
        except (IndexError, ValueError):
            out.append(-1)
    return np.asarray(out, dtype=np.int64)
