"""ABC-XGBoost engine: simulate -> summarise -> learn (XGBoost) -> explain (SHAP).

Compares demography x selection scenarios for an allele-frequency trajectory and
estimates the selection coefficient s, both by acceptance-rejection ABC and by an
XGBoost regressor/classifier trained on the simulations (with SHAP for which summary
statistics drive the inference). Built for the TYK2 P1104A question (Kerner 2021,
axe 2): is the observed decline reproducible, and which scenario fits best?
"""
from __future__ import annotations

import numpy as np

from .summary import feature_names, summary_from_freqs
from .wf import sample_at, simulate

GENERATIONS = 120                 # ~3000 yr at 25 yr / human generation
DEFAULT_BINS = (0, 40, 80, 120)   # generations sampled (ancient -> present)
REGIMES = ("neutral", "weak", "strong")


def regime_of(s: float) -> str:
    return "neutral" if s < 0.01 else ("weak" if s < 0.10 else "strong")


def simulate_dataset(n, *, rng, bins=DEFAULT_BINS, generations=GENERATIONS,
                     s_max=0.4, f0_range=(0.05, 0.20),
                     ne_choices=(1000, 5000, 10000), h=0.0) -> dict:
    """Draw n (s, f0, Ne) from the prior, simulate, and summarise. Returns arrays."""
    nb = len(bins)
    X = np.empty((n, nb + 7))
    s_arr = np.empty(n)
    regime = np.empty(n, dtype=int)
    f0_arr = np.empty(n)
    ne_arr = np.empty(n)
    for i in range(n):
        s = float(rng.uniform(0.0, s_max))
        f0 = float(rng.uniform(*f0_range))
        ne = float(rng.choice(ne_choices))
        traj = simulate(f0, s, ne, generations, rng, h=h)
        X[i] = summary_from_freqs(sample_at(traj, bins))
        s_arr[i], f0_arr[i], ne_arr[i] = s, f0, ne
        regime[i] = REGIMES.index(regime_of(s))
    return {"X": X, "s": s_arr, "regime": regime, "f0": f0_arr, "ne": ne_arr,
            "feature_names": feature_names(nb), "bins": list(bins)}


def _build(reg: bool, **extra):
    import xgboost as xgb
    cls = xgb.XGBRegressor if reg else xgb.XGBClassifier
    kw = dict(n_estimators=500, max_depth=4, learning_rate=0.05, subsample=0.85,
              colsample_bytree=0.85, n_jobs=4, random_state=0, **extra)
    try:                              # early stopping is OBLIGATOIRE (KB), xgboost >=1.6
        return cls(early_stopping_rounds=30, **kw)
    except TypeError:                 # older xgboost: no constructor arg
        return cls(**kw)


def _fit(model, x_tr, y_tr, x_val, y_val):
    try:
        model.fit(x_tr, y_tr, eval_set=[(x_val, y_val)], verbose=False)
    except TypeError:
        model.fit(x_tr, y_tr)
    return model


def fit_regressor(x_tr, y_tr, x_val, y_val):
    """XGBoost regressor estimating the continuous selection coefficient s."""
    return _fit(_build(True), x_tr, y_tr, x_val, y_val)


def fit_classifier(x_tr, y_tr, x_val, y_val):
    """XGBoost classifier of the selection regime (neutral / weak / strong)."""
    return _fit(_build(False), x_tr, y_tr, x_val, y_val)


def shap_top(model, X, names, k=6):
    """Top-k summary statistics by mean |SHAP| (robust to list / 2-D / 3-D output)."""
    import shap
    vals = shap.TreeExplainer(model).shap_values(X)
    if isinstance(vals, list):                       # one array per class
        arr = np.mean([np.abs(v).mean(0) for v in vals], axis=0)
    else:
        a = np.asarray(vals)
        feat_axes = [ax for ax in range(a.ndim) if a.shape[ax] == len(names)]
        fa = feat_axes[-1] if feat_axes else a.ndim - 1
        other = tuple(ax for ax in range(a.ndim) if ax != fa)
        arr = np.abs(a).mean(axis=other) if other else np.abs(a)
    order = np.argsort(arr)[::-1][:k]
    return [(names[i], float(arr[i])) for i in order]


def abc_reject(obs_x, X, s, *, accept_frac=0.05, min_keep=50) -> dict:
    """Acceptance-rejection ABC: keep the closest accept_frac of sims (standardised
    Euclidean distance on the summary stats) and report the posterior on s."""
    mu = X.mean(0)
    sd = X.std(0) + 1e-9
    z = (X - mu) / sd
    z0 = (np.asarray(obs_x) - mu) / sd
    d = np.sqrt(((z - z0) ** 2).sum(1))
    k = max(min_keep, int(accept_frac * len(X)))
    idx = np.argsort(d)[:k]
    post = s[idx]
    return {"n_accepted": int(k), "s_median": float(np.median(post)),
            "s_q025": float(np.percentile(post, 2.5)),
            "s_q975": float(np.percentile(post, 97.5))}


def infer(observed_freqs, *, n=5000, rng=None, bins=DEFAULT_BINS, h=0.0, **prior) -> dict:
    """End-to-end: simulate, train XGBoost, and infer s + regime for an observed
    allele-frequency trajectory (oldest -> newest, sampled at `bins`)."""
    rng = rng or np.random.default_rng(0)
    ds = simulate_dataset(n, rng=rng, bins=bins, h=h, **prior)
    X, names = ds["X"], ds["feature_names"]
    perm = rng.permutation(len(X))
    cut = int(0.8 * len(X))
    tr, va = perm[:cut], perm[cut:]
    reg = fit_regressor(X[tr], ds["s"][tr], X[va], ds["s"][va])
    clf = fit_classifier(X[tr], ds["regime"][tr], X[va], ds["regime"][va])
    obs = summary_from_freqs(observed_freqs)
    return {
        "s_point_estimate": float(reg.predict(obs.reshape(1, -1))[0]),
        "regime_classified": REGIMES[int(clf.predict(obs.reshape(1, -1))[0])],
        "abc_posterior": abc_reject(obs, X, ds["s"]),
        "shap_top": shap_top(reg, X[va], names),
        "n_simulations": int(n),
    }
