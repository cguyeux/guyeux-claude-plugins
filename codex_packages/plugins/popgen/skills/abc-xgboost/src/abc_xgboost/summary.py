"""Summary statistics of an allele-frequency time series (the ABC features)."""
from __future__ import annotations

import numpy as np


def summary_from_freqs(freqs) -> np.ndarray:
    """Feature vector from frequencies sampled at ordered time bins (oldest -> newest)."""
    f = np.asarray(freqs, dtype=float)
    f0, fend = f[0], f[-1]
    decline = f0 - fend
    rel_decline = decline / f0 if f0 > 0 else 0.0
    diffs = np.diff(f) if len(f) > 1 else np.array([0.0])
    extra = np.array([
        decline, rel_decline, fend, float(f.max()), float(f.min()),
        float(diffs.mean()), float(diffs.min()),
    ])
    return np.concatenate([f, extra])


def feature_names(n_bins: int) -> list[str]:
    return (
        [f"freq_bin{i}" for i in range(n_bins)]
        + ["decline", "rel_decline", "f_end", "f_max", "f_min", "mean_diff", "min_diff"]
    )
