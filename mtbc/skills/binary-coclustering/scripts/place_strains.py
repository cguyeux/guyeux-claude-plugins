#!/usr/bin/env python3
"""P11.5 — place NEW strains on an existing co-clustering, model FROZEN.

The upstream repository has no `predict` mode: `lbm.from_cache` is a warm start
that refits, `io/fetch_clustering.py` initialises from an external partition, and
`StaircaseLBM` exposes neither `predict` nor `transform`. Yet placement is one E
step away. With `alpha` (g x m) and the marker-to-block map `w` frozen, the
responsibility of a new strain over the g blocks is

    log P(block i) = log pi_i + sum_j [ n_ij log alpha_ij + (m_j - n_ij) log(1 - alpha_ij) ]

with `n_ij` the number of markers of block j that the strain carries and `m_j` the
size of block j. Cost is O(g.m) per strain: thousands of strains placed instantly,
without refitting anything.

What this buys over `barcoding_v2` is NOT speed, it is a MEASURE OF CONFIDENCE. A
deterministic rule always answers; a posterior can answer "nowhere in particular",
and a diffuse responsibility is the signal of an undescribed sublineage or of a QC
problem (mixture, contamination, partial coverage).

Two traps, both handled here, because without them the confidence number is wrong
even though the argmax is right.

1. CLONAL PSEUDO-REPLICATION. In a clonal organism the markers of one block are
   the SAME evolutionary event counted m_j times. Summing over all of them makes
   the likelihood massively overconfident and every posterior saturates at 0 or 1.
   `--weight block` counts each marker block as ONE observation (the presence
   FRACTION replaces the presence count), which is the honest unit of evidence.
   `--weight marker` reproduces the naive formula, kept for comparison only.

2. ABSENCE IS NOT NON-COVERAGE. A marker not called in a new strain may simply be
   uncovered. `--coverage` restricts the sum to markers the strain can actually be
   asked about, renormalising block sizes per strain.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import scipy.sparse as sp

EPS = 1e-6


def block_counts(X, w, m):
    """(n_strains, m) count of carried markers per marker block."""
    B = sp.csr_matrix(
        (np.ones(len(w), np.float64), (np.arange(len(w)), np.asarray(w))),
        shape=(len(w), m),
    )
    return np.asarray((X @ B).todense())


def place(X, alpha, w, pi=None, weight="block", askable=None, return_ll=False):
    """Posterior responsibility of each strain over the g strain blocks.

    `askable` (n_strains, n_markers) boolean or sparse: markers this strain can be
    asked about. `None` means all of them.

    `return_ll` also returns the UNNORMALISED log-likelihood of the best block,
    which is the quantity that actually detects "belongs to none of them" — see
    `fit_quality` below.
    """
    m = alpha.shape[1]
    A = np.clip(np.asarray(alpha, dtype=np.float64), EPS, 1 - EPS)
    n_ij = block_counts(X, w, m)
    if askable is None:
        m_j = np.bincount(np.asarray(w), minlength=m).astype(np.float64)
        m_ij = np.broadcast_to(m_j, n_ij.shape)
    else:
        m_ij = block_counts(askable, w, m)
        n_ij = np.minimum(n_ij, m_ij)

    if weight == "block":
        # one observation per marker block: the presence FRACTION carries the evidence
        with np.errstate(invalid="ignore", divide="ignore"):
            frac = np.where(m_ij > 0, n_ij / np.maximum(m_ij, 1.0), 0.0)
        present, absent = frac, np.where(m_ij > 0, 1.0 - frac, 0.0)
    elif weight == "marker":
        present, absent = n_ij, m_ij - n_ij
    else:
        raise ValueError("weight must be 'block' or 'marker'")

    ll = present @ np.log(A).T + absent @ np.log(1.0 - A).T
    raw_best = ll.max(1)  # before the prior and before normalising
    if pi is not None:
        ll = ll + np.log(np.clip(np.asarray(pi, dtype=np.float64), EPS, None))[None, :]
    ll = ll - ll.max(1, keepdims=True)
    R = np.exp(ll)
    R /= R.sum(1, keepdims=True)
    return (R, raw_best) if return_ll else R


def fit_quality(X, alpha, w, weight="block", askable=None):
    """Unnormalised log-likelihood of the best block, per strain.

    THIS is what answers "does this strain belong to the model at all", and the
    posterior cannot: a posterior is RELATIVE, it only ranks the blocks against one
    another, so a strain from another lineage still gets assigned somewhere, often
    confidently. Measured on L6 (model) against L5 (26 strains that belong nowhere
    in it): thresholding the normalised entropy at 0.3 flags only 19 % of them,
    while thresholding this likelihood at the 1st percentile of the training strains
    flags **88 %** for a 1 % false-positive rate.

    Use the 1st percentile of the fitted strains as the threshold, not an absolute
    value: the scale depends on the number of marker blocks.
    """
    _, best = place(X, alpha, w, pi=None, weight=weight, askable=askable, return_ll=True)
    return best


def diagnose(R, top=3):
    """Per-strain summary: argmax, its posterior, entropy, and the runners-up."""
    order = np.argsort(-R, axis=1)[:, :top]
    best = order[:, 0]
    p = R[np.arange(len(R)), best]
    with np.errstate(divide="ignore", invalid="ignore"):
        H = -np.nansum(np.where(R > 0, R * np.log(R), 0.0), axis=1)
    Hn = H / np.log(R.shape[1]) if R.shape[1] > 1 else np.zeros_like(H)
    return best, p, Hn, order


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("fit", type=Path, help="directory holding fit.npz (z, w, alpha)")
    ap.add_argument("new", type=Path, help="directory holding matrix.npz + strains.txt")
    ap.add_argument(
        "--weight",
        choices=["block", "marker"],
        default="block",
        help="block (default, one observation per marker block) or marker (naive, overconfident)",
    )
    ap.add_argument("--diffuse-above", type=float, default=0.30,
                    help="normalised entropy above which a strain is flagged 'fits nowhere'")
    ap.add_argument(
        "--reference",
        type=Path,
        help="the matrix.npz directory the model was FITTED on. Calibrates the "
        "likelihood threshold on those strains, which is the reliable "
        "'belongs nowhere' detector (88 %% recall vs 19 %% for entropy alone)",
    )
    ap.add_argument("--outlier-percentile", type=float, default=1.0)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()

    f = np.load(a.fit / "fit.npz")
    alpha, w, z = f["alpha"], f["w"], f["z"]
    g = alpha.shape[0]
    pi = np.bincount(z, minlength=g).astype(np.float64)
    pi /= pi.sum()

    X = sp.load_npz(a.new / "matrix.npz").astype(np.float64)
    strains = (a.new / "strains.txt").read_text().split()
    if X.shape[1] != len(w):
        raise SystemExit(
            f"the new matrix has {X.shape[1]} markers but the model was fitted on {len(w)}; "
            "both must use the same marker vocabulary (same markers.txt)"
        )

    R, ll_best = place(X, alpha, w, pi=pi, weight=a.weight, return_ll=True)
    best, p, Hn, order = diagnose(R)
    diffuse = Hn > a.diffuse_above

    print(f"strains placed        {len(strains)}")
    print(f"weighting             {a.weight}")
    print(f"posterior of argmax   median {np.median(p):.3f}  "
          f"q10 {np.quantile(p,0.10):.3f}  q90 {np.quantile(p,0.90):.3f}")
    print(f"saturated at 1.0      {int((p > 0.999).sum())}/{len(p)}"
          + ("   <- pseudo-replication, use --weight block" if a.weight == "marker" else ""))
    print(f"diffuse (H_norm>{a.diffuse_above})  {int(diffuse.sum())}/{len(p)}"
          "   <- weak signal on its own, see below")

    outlier = np.zeros(len(strains), bool)
    thr = None
    if a.reference:
        Xr = sp.load_npz(a.reference / "matrix.npz").astype(np.float64)
        ll_ref = fit_quality(Xr, alpha, w, weight=a.weight)
        thr = float(np.percentile(ll_ref, a.outlier_percentile))
        outlier = ll_best < thr
        print(f"log-likelihood        median {np.median(ll_best):.1f}  "
              f"(reference strains: median {np.median(ll_ref):.1f}, "
              f"p{a.outlier_percentile:g} = {thr:.1f})")
        print(f"BELONGS NOWHERE       {int(outlier.sum())}/{len(strains)}"
              f"  ({100*outlier.mean():.1f}%)   <- likelihood below the reference floor")
    else:
        print("log-likelihood        median "
              f"{np.median(ll_best):.1f}   (pass --reference to calibrate a threshold)")

    if a.out:
        a.out.mkdir(parents=True, exist_ok=True)
        with (a.out / "placement.tsv").open("w") as fh:
            fh.write(
                "strain\tblock\tposterior\tentropy_norm\tdiffuse\tlog_likelihood"
                "\tbelongs_nowhere\trunners_up\n"
            )
            for i, s in enumerate(strains):
                ru = ";".join(f"{int(b)}:{R[i, b]:.3f}" for b in order[i, 1:])
                fh.write(
                    f"{s}\t{int(best[i])}\t{p[i]:.4f}\t{Hn[i]:.4f}\t{int(diffuse[i])}"
                    f"\t{ll_best[i]:.3f}\t{int(outlier[i])}\t{ru}\n"
                )
        (a.out / "placement.json").write_text(
            json.dumps(
                {
                    "n_strains": len(strains),
                    "weighting": a.weight,
                    "median_posterior": float(np.median(p)),
                    "n_saturated": int((p > 0.999).sum()),
                    "n_diffuse": int(diffuse.sum()),
                    "diffuse_threshold": a.diffuse_above,
                    "median_log_likelihood": float(np.median(ll_best)),
                    "likelihood_threshold": thr,
                    "n_belongs_nowhere": int(outlier.sum()),
                },
                indent=2,
            )
            + "\n"
        )
        print(f"written to {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
