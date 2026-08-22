#!/usr/bin/env python3
"""Fit a Bernoulli LBM on a binary strain x marker matrix, driving C. Lecarpentier's engine.

We do NOT maintain a second EM engine: `_fit_lbm` (random restarts) followed by
`_em_cpu` (chunked variational EM) come from `tblearn_biclustering`, frozen at the
commit recorded in PROVENANCE. Only the data plumbing is ours, because the upstream
loader goes through their TBLearn MCP whereas our matrix comes from `bdd/actuelle`.

Two carrier floors have to be neutralised, not one. The obvious one is the fetch
floor (`build_matrix.py --min-carriers`). The second is hidden inside
`StaircaseLBM.fit`, which re-filters columns to MAF in [0.02, 0.98]; on 8 744
strains that silently drops every marker carried by fewer than 175 of them. We
bypass the staircase and call the engine directly, so the only floor is ours.

Outputs (in `--out`): fit.npz (z, w, alpha, ll), fit.json (metadata).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import scipy.sparse as sp

# Where C. Lecarpentier's repository is checked out; override with $BICLUSTERING_REPO.
# `git clone https://github.com/cdarthos/bi-clustering` anywhere: no install needed, the
# package imports as-is (verified with numpy 2.5 / scipy 1.18 / Python 3.14).
BICLUST = Path(os.environ.get("BICLUSTERING_REPO", Path.home() / "docs/codes/bi-clustering"))


def _engine():
    if not (BICLUST / "tblearn_biclustering").is_dir():
        raise SystemExit(
            f"bi-clustering engine not found at {BICLUST}. Clone "
            "https://github.com/cdarthos/bi-clustering and point $BICLUSTERING_REPO at it."
        )
    sys.path.insert(0, str(BICLUST))
    from tblearn_biclustering.core.em import _em_cpu, _soft
    from tblearn_biclustering.core.kernels import _fit_lbm, _icl

    return _fit_lbm, _em_cpu, _soft, _icl


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("data", type=Path, help="directory holding matrix.npz")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("-g", type=int, required=True, help="strain blocks")
    ap.add_argument("-m", type=int, required=True, help="marker blocks")
    ap.add_argument("--n-init", type=int, default=3)
    ap.add_argument("--max-iter", type=int, default=60)
    ap.add_argument("--tol", type=float, default=1e-5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n-jobs", type=int, default=None)
    a = ap.parse_args()

    _fit_lbm, _em_cpu, _soft, _icl = _engine()
    X = sp.load_npz(a.data / "matrix.npz").astype(np.float64)

    # Progress goes to a FILE, not only to stdout. A fit on a large pool runs for hours, and
    # stdout is routinely swallowed: piping the command into `tail`, or any buffered consumer,
    # yields nothing until the process exits. That cost a full hour of blind waiting on the L3
    # g=120 run (2026-08-10) with no way to tell "still fitting" from "died". The output
    # directory is therefore created UP FRONT — it used to appear only on success, so a crashed
    # or killed run left no trace at all of what it had been doing.
    a.out.mkdir(parents=True, exist_ok=True)
    log_path = a.out / "progress.log"

    def note(msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        with log_path.open("a") as fh:
            fh.write(line + "\n")

    note(f"matrix {X.shape}  nnz={X.nnz}  target g={a.g} m={a.m}  "
         f"n_init={a.n_init} max_iter={a.max_iter} n_jobs={a.n_jobs}")

    t0 = time.time()
    note(f"phase 1/2: {a.n_init} random restart(s), parallel workers")
    f = _fit_lbm(X, a.g, a.m, a.n_init, a.max_iter, a.tol, a.seed, n_jobs=a.n_jobs)
    t_init = time.time() - t0
    note(f"phase 1/2 done ({t_init:.0f}s)  ll={f['ll']:.0f}")

    R, S = _soft(f["z"], a.g), _soft(f["w"], a.m)
    # Single-process from here: the parallel workers are gone and only the parent burns CPU.
    # Worth stating, because "the workers vanished" reads as a crash when it is normal progress.
    note("phase 2/2: variational EM in the parent process (workers are expected to be gone)")
    R, S, alpha, ll = _em_cpu(X, R, S, a.max_iter, a.tol, verbose=False, n_threads=a.n_jobs)
    z, w = R.argmax(1), S.argmax(1)
    elapsed = time.time() - t0
    note(f"phase 2/2 done  ll={ll:.0f}  total {elapsed:.0f}s")

    np.savez_compressed(a.out / "fit.npz", z=z, w=w, alpha=alpha, ll=ll)
    meta = dict(
        g=a.g,
        m=a.m,
        n_init=a.n_init,
        max_iter=a.max_iter,
        tol=a.tol,
        seed=a.seed,
        n_strains=int(X.shape[0]),
        n_markers=int(X.shape[1]),
        ll=float(ll),
        icl=float(_icl(X, z, w, 1.0)),
        blocks_used=int(len(np.unique(z))),
        marker_blocks_used=int(len(np.unique(w))),
        seconds=round(elapsed, 1),
    )
    (a.out / "fit.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
