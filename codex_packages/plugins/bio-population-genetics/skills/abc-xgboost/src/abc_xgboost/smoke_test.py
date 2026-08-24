"""Offline smoke test for abc-xgboost (needs xgboost+shap+sklearn). No network.

Validates the ABC-XGBoost machinery on simulations where the selection coefficient is
identifiable (ADDITIVE, h=0.5): the XGBoost regressor must recover s on held-out
sims, acceptance-rejection ABC must recover a planted strong s, and SHAP must rank the
summary statistics. (With h=0 / recessive -- the TYK2 default -- s is only weakly
identifiable at low frequency; that is a real caveat, not a code bug.)

    /home/christophe/venvs/abc311/bin/python -m abc_xgboost.smoke_test
"""
from __future__ import annotations

import sys

import numpy as np

from .abc import (abc_reject, fit_classifier, fit_regressor, shap_top,
                  simulate_dataset, REGIMES)
from .summary import summary_from_freqs
from .wf import sample_at, simulate


def main() -> int:
    rng = np.random.default_rng(0)
    ds = simulate_dataset(800, rng=rng, h=0.5)          # additive -> s identifiable
    X = ds["X"]
    perm = rng.permutation(len(X))
    cut = int(0.8 * len(X))
    tr, va = perm[:cut], perm[cut:]

    # 1. regressor recovers s on held-out simulations
    reg = fit_regressor(X[tr], ds["s"][tr], X[va], ds["s"][va])
    pred = reg.predict(X[va])
    corr = float(np.corrcoef(pred, ds["s"][va])[0, 1])
    print(f"regressor corr(pred, true s) = {corr:.2f}")
    if not corr > 0.6:
        print(f"FAIL: expected regressor corr > 0.6, got {corr:.2f}", file=sys.stderr)
        return 2

    # 2. ABC recovers a planted strong (additive) selection
    rng2 = np.random.default_rng(1)
    obs = summary_from_freqs(sample_at(simulate(0.12, 0.25, 5000, 120, rng2, h=0.5), ds["bins"]))
    post = abc_reject(obs, X, ds["s"])
    print(f"ABC posterior s = {post['s_median']:.3f} [{post['s_q025']:.3f}, {post['s_q975']:.3f}]")
    if not post["s_median"] > 0.10:
        print(f"FAIL: ABC should recover strong s for the planted obs, got {post}", file=sys.stderr)
        return 2

    # 3. classifier + SHAP exercised
    clf = fit_classifier(X[tr], ds["regime"][tr], X[va], ds["regime"][va])
    pred_regime = REGIMES[int(clf.predict(obs.reshape(1, -1))[0])]
    top = shap_top(reg, X[va], ds["feature_names"], k=4)
    print(f"planted-obs regime = {pred_regime}; SHAP top = {[t[0] for t in top]}")
    if pred_regime != "strong" or not top:
        print(f"FAIL: classifier/SHAP sanity (regime={pred_regime}, top={top})", file=sys.stderr)
        return 2

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
