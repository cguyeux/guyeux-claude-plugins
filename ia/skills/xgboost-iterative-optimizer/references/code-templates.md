---
name: xgboost-iterative-optimizer
description: |
  Iterative XGBoost model optimization using a scientific ML researcher workflow.
  Diagnose prediction errors through VISUAL INSPECTION of predicted-vs-actual
  curves (primary), reinforced by SHAP, residual analysis, and metrics.
  Improve models through feature engineering, hyperparameter tuning, objective
  function selection, and ensemble strategies. Track experiments systematically.

  Use when: XGBoost predictions are poor, MAE/RMSE needs reduction, residuals
  show patterns, model under/overfits, or "predictions are too flat/biased."
---

# XGBoost Iterative Optimizer

**Role**: You are an experienced ML researcher who iteratively improves XGBoost regression models through principled diagnosis, experimentation, and convergence tracking.

**Core constraint**: XGBoost only. `num_boost_round=100_000` with `early_stopping_rounds`. No other boosting library.

**Primary diagnostic**: **ALWAYS look at the curves first.** A metric (MAE, RMSE) is just a number — a prediction close to the hourly mean can have a good MAE while capturing none of the signal dynamics. Use your multimodal vision to see what the model gets right and wrong, then use metrics as supporting evidence.

---

## 1. Optimization Loop

Every optimization session follows this cycle. **Never skip the visual diagnostic phase.**

```
👁️ VISUAL INSPECT → DIAGNOSE → HYPOTHESIZE → EXPERIMENT → 👁️ COMPARE → EVALUATE → LOG → REPEAT
```

### 1.1 Session Initialization

At the start of each session, create an **experiment log** file:

```python
# /tmp/{model_name}_optim_log.md
"""
# Optimization Log: {model_name}
## Baseline
- MAE: {baseline_mae} | RMSE: {baseline_rmse}
- Target: mean={mean}, std={std}, min={min}, max={max}
- Samples: {n} | Features: {n_features}
- Hyperparams: {params}

## Experiments
| # | Hypothesis | Change | MAE | RMSE | Δ% | Keep? |
|---|-----------|--------|-----|------|-----|-------|
"""
```

**Always inform the user** of:
- Current iteration number and which phase (diagnose/experiment/evaluate)
- The hypothesis being tested and the scientific rationale
- Quantitative results vs baseline and vs previous best
- Decision (keep/reject) and next planned action

---

## 2. Diagnostic Phase (DIAGNOSE)

### 2.0 Visual Diagnostic — Predicted vs Actual (PRIMARY)

> **This is the MOST IMPORTANT diagnostic step.** Generate comparison plots, then
> **look at them with your multimodal vision** to diagnose issues before touching
> any metric. A flat predicted curve with MAE=7.5 looks very different from a
> dynamic predicted curve with MAE=7.5.

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd, numpy as np

# IMPORTANT: Use yesterday (J-1) as the right boundary, not ts_test.max().
# The latest CSV files may not have been received yet, creating an artificial
# drop at the end of the dataset that is NOT a real signal to diagnose.
yesterday = pd.Timestamp.now().normalize() - pd.Timedelta(days=1)
# If holdout ends before yesterday, use the holdout max instead
end_date = min(ts_test.max(), yesterday)

# Generate 3 comparison windows: last 2 weeks, last month, a zoomed "worst week"
fig, axes = plt.subplots(3, 1, figsize=(18, 12), sharex=False)

# 1. Last 2 weeks — detailed view (ending yesterday)
last_2w = (ts_test >= end_date - pd.Timedelta(days=14)) & (ts_test <= end_date)
if last_2w.sum() > 10:
    axes[0].plot(ts_test[last_2w], y_test[last_2w], 'b-', lw=1.2, label='Réel')
    axes[0].plot(ts_test[last_2w], y_pred[last_2w], 'r-', lw=1.2, alpha=0.8, label='Prédit')
    axes[0].fill_between(ts_test[last_2w], y_test[last_2w], y_pred[last_2w], alpha=0.15, color='red')
    axes[0].axhline(60, c='orange', ls='--', alpha=0.4, label='Seuil 60')
    axes[0].set_title('Dernières 2 semaines (→ J-1) — Prédit vs Réel')
    axes[0].legend()

# 2. Last month — broader trend (ending yesterday)
last_month = (ts_test >= end_date - pd.Timedelta(days=30)) & (ts_test <= end_date)
if last_month.sum() > 10:
    axes[1].plot(ts_test[last_month], y_test[last_month], 'b-', lw=0.8, alpha=0.8, label='Réel')
    axes[1].plot(ts_test[last_month], y_pred[last_month], 'r-', lw=0.8, alpha=0.6, label='Prédit')
    axes[1].axhline(60, c='orange', ls='--', alpha=0.4)
    axes[1].set_title('Dernier mois (→ J-1) — Vue d\'ensemble')
    axes[1].legend()

# 3. Worst week (highest MAE) — where the model fails most
residuals_abs = np.abs(y_pred - y_test)
if len(ts_test) > 84:  # at least 1 week
    rolling_mae = pd.Series(residuals_abs).rolling(84, center=True).mean()
    worst_center = rolling_mae.idxmax()
    worst_start = max(0, worst_center - 42)
    worst_end = min(len(ts_test), worst_center + 42)
    sl = slice(worst_start, worst_end)
    axes[2].plot(ts_test.iloc[sl], y_test[sl], 'b-', lw=1.2, label='Réel')
    axes[2].plot(ts_test.iloc[sl], y_pred[sl], 'r-', lw=1.2, alpha=0.8, label='Prédit')
    axes[2].fill_between(ts_test.iloc[sl], y_test[sl], y_pred[sl], alpha=0.2, color='red')
    axes[2].set_title(f'Pire semaine (MAE={residuals_abs[sl].mean():.1f})')
    axes[2].legend()

plt.tight_layout()
plt.savefig('/tmp/{model_name}_visual_diagnostic.png', dpi=150)
```

**After generating the plot, VIEW IT and answer these questions:**

| Question | What to look for | If YES → Action |
|---|---|---|
| **Is the predicted curve flat/smooth?** | Prédit lacks the amplitude/peaks of réel | Increase `max_depth`, reduce regularization, add high-variance features |
| **Are peaks under-predicted?** | Predicted peaks are lower than actual | Add sample weighting (emphasize high values), use asymmetric loss |
| **Is there a phase delay?** | Predicted peaks arrive AFTER actual peaks | Add more recent lags (lag1, lag2), check `extra_shift` is correct |
| **Is the variability right?** | Compare `std(pred) / std(real)` visually | If ratio < 0.8, model is too conservative; increase depth, reduce reg |
| **Does the model miss specific events?** | Sudden spikes completely missed | Add external features (weather, events), or increase ensemble diversity |
| **Is the weekly pattern captured?** | Weekend/weekday rhythm visible in both? | Add cyclic features, `is_weekend` interactions |
| **Are nocturnal valleys captured?** | Night-time drops followed correctly? | Check `hours_since_8am`, hour-based interactions |

> **Key insight**: `std_ratio = std(y_pred) / std(y_true)` is the single best
> numeric proxy for visual quality. A ratio of 0.85 means the model is "too flat"
> and misses 15% of the signal variability. Target: 0.95-1.05.

---

### 2.1 Residual Analysis

This is the **second most informative diagnostic** (after visual inspection). Plot and analyze residuals (predicted − actual).

```python
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

residuals = y_pred - y_true

# 1. Distribution: should be centered, symmetric, light-tailed
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
axes[0,0].hist(residuals, bins=50, edgecolor='k', alpha=0.7)
axes[0,0].axvline(0, c='r', ls='--')
axes[0,0].set_title(f'Residual Distribution (skew={residuals.skew():.2f}, kurt={residuals.kurtosis():.2f})')

# 2. Residuals vs Predicted: should show no pattern (homoscedasticity)
axes[0,1].scatter(y_pred, residuals, alpha=0.1, s=5)
axes[0,1].axhline(0, c='r', ls='--')
axes[0,1].set_title('Residuals vs Predicted')

# 3. Residuals vs Time: should show no trend or seasonality
axes[0,2].plot(residuals.values[-2000:], alpha=0.5, lw=0.5)
axes[0,2].axhline(0, c='r', ls='--')
axes[0,2].set_title('Residuals over Time (last 2000)')

# 4. Reliability plot: predicted vs actual (binned)
bins = pd.qcut(y_pred, q=20, duplicates='drop')
reliability = pd.DataFrame({'pred': y_pred, 'actual': y_true}).groupby(bins).mean()
axes[1,0].plot(reliability['pred'], reliability['actual'], 'bo-')
axes[1,0].plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--')
axes[1,0].set_title('Reliability Curve (pred vs actual)')

# 5. Error by hour/day (temporal patterns in errors)
if 'hour' in df.columns:
    err_by_hour = pd.DataFrame({'abs_err': np.abs(residuals), 'hour': df['hour'].iloc[-len(residuals):]})
    err_by_hour.groupby('hour')['abs_err'].mean().plot(ax=axes[1,1], kind='bar')
    axes[1,1].set_title('MAE by Hour')

# 6. QQ plot of residuals vs normal
from scipy import stats
stats.probplot(residuals, dist="norm", plot=axes[1,2])
axes[1,2].set_title('QQ Plot')

plt.tight_layout()
plt.savefig('/tmp/{model_name}_diagnostic.png', dpi=150)
print("Diagnostic saved to /tmp/{model_name}_diagnostic.png")
```

### 2.2 Diagnostic Decision Tree

Based on the residual analysis:

| Observation | Diagnosis | Action |
|---|---|---|
| **Systematic bias** (residuals not centered at 0) | Model consistently over/under-predicts | Try Huber loss (`reg:pseudohubererror`) or asymmetric loss |
| **Heteroscedasticity** (fan shape in residuals vs predicted) | Variance depends on prediction magnitude | Log-transform target, or use `reg:gamma` / `reg:tweedie` |
| **Temporal patterns** in residuals | Missing temporal features or seasonality | Add cyclic features (sin/cos), holiday flags, or lag residuals |
| **Heavy tails** (outliers in QQ plot) | Extreme events poorly captured | Use Huber loss, add extreme-event features, or cap target |
| **Flat predictions** (low variance in y_pred vs y_true) | Under-fitting or insufficient feature variability | Increase `max_depth`, reduce regularization, add high-variance features |
| **High error at specific hours** | Time-dependent bias | Add hour-specific features or train separate models per time slot |
| **Predictions lag behind reality** | Stale features, insufficient recent information | Add more recent lags (lag1, lag2), reduce `min_child_weight` |

### 2.3 SHAP Value Analysis

Use SHAP to understand **why** the model makes specific errors.

```python
import shap

explainer = shap.TreeExplainer(bst)

# Sample for speed (SHAP on full dataset is slow)
sample_idx = np.random.choice(len(X_test), min(2000, len(X_test)), replace=False)
X_sample = X_test.iloc[sample_idx] if hasattr(X_test, 'iloc') else X_test[sample_idx]
shap_values = explainer.shap_values(xgboost.DMatrix(X_sample, feature_names=feature_cols))

# Global importance
shap.summary_plot(shap_values, X_sample, feature_names=feature_cols, show=False)
plt.tight_layout()
plt.savefig('/tmp/{model_name}_shap_summary.png', dpi=150)

# Focus on HIGH ERROR samples
high_error_mask = np.abs(residuals[sample_idx]) > np.percentile(np.abs(residuals), 90)
if high_error_mask.sum() > 10:
    shap_high_error = shap_values[high_error_mask]
    shap_low_error = shap_values[~high_error_mask]
    # Compare mean |SHAP| between high and low error
    diff = np.abs(shap_high_error).mean(axis=0) - np.abs(shap_low_error).mean(axis=0)
    top_diff = np.argsort(-diff)[:15]
    print("Features driving HIGH errors (need attention):")
    for i in top_diff:
        print(f"  {feature_cols[i]}: Δ|SHAP| = {diff[i]:.4f}")
```

### 2.4 Feature-Target Correlation Analysis

```python
# Mutual information and Spearman correlation with target
from sklearn.feature_selection import mutual_info_regression
from scipy.stats import spearmanr

mi_scores = mutual_info_regression(X_train.fillna(0), y_train, random_state=42)
correlations = [spearmanr(X_train.iloc[:, i].fillna(0), y_train).statistic 
                for i in range(X_train.shape[1])]

feature_analysis = pd.DataFrame({
    'feature': feature_cols,
    'mutual_info': mi_scores,
    'spearman_r': correlations,
    'variance': X_train.var().values,
    'null_pct': X_train.isnull().mean().values
}).sort_values('mutual_info', ascending=False)

print("Top features by mutual information:")
print(feature_analysis.head(20).to_string())
print("\nPotentially useless features (MI < 0.01):")
print(f"  {(feature_analysis['mutual_info'] < 0.01).sum()} features")
```

---

## 3. Hypothesis Generation (HYPOTHESIZE)

After diagnosis, generate **ranked hypotheses**. Test them one at a time.

### 3.1 Feature Engineering Hypotheses

| Category | Features to Try | When |
|---|---|---|
| **Temporal** | `hour_sin/cos`, `dow_sin/cos`, `month_sin/cos`, `is_holiday`, `day_of_year` | Always — temporal structure is fundamental |
| **Lag enrichment** | `target_lag{1..168}`, `target_same_hour_yesterday/last_week` | When recent trends matter |
| **Rolling statistics** | `rolling_mean_{3,6,12,24,48,168}`, `rolling_std`, `rolling_min/max` | When variability or trend matters |
| **Interaction** | `feature_A * feature_B` for top SHAP pairs | When SHAP shows nonlinear dependencies |
| **Residual feedback** | `residual_lag1` (error at t-1 as feature) | When residuals show autocorrelation |
| **External data** | Weather (temperature, humidity, wind), calendar effects, events | When internal features plateau |
| **Derived ratios** | `feature_A / feature_B`, `feature - rolling_mean` (anomaly) | When relative changes matter more than absolutes |

### 3.2 Hyperparameter Hypotheses

Test in this priority order:

1. **`max_depth`** (4→6→8→10): Controls model complexity. If predictions are flat, increase.
2. **`learning_rate`** (0.1→0.03→0.01→0.005): Lower = more robust but slower. Always with early stopping.
3. **`min_child_weight`** (1→5→15→30→50): Higher = more regularization, smoother predictions.
4. **`subsample`** and **`colsample_bytree`** (0.6→0.8→0.95): Stochastic regularization.
5. **`gamma`** (0→0.1→0.5→1.0): Minimum loss reduction for split. Higher = more conservative.
6. **`reg_alpha`** (L1) and **`reg_lambda`** (L2) (0.001→0.1→1→10): Explicit regularization.

### 3.3 Objective Function Hypotheses

| Objective | `params['objective']` | Use When |
|---|---|---|
| **Squared Error** (default) | `reg:squarederror` | Symmetric errors, no outliers |
| **Absolute Error** | Custom via `obj` parameter | Care about median, not mean |
| **Huber Loss** | `reg:pseudohubererror` + `huber_slope` | Outliers present, want robustness |
| **Quantile** | Custom gradient/hessian | Need prediction intervals |
| **Tweedie** | `reg:tweedie` + `tweedie_variance_power` | Right-skewed count data |
| **Gamma** | `reg:gamma` | Strictly positive targets, heteroscedastic |

Custom MAE objective (use with `eval_metric='mae'`):
```python
def mae_obj(predt, dtrain):
    """Gradient and hessian for MAE (L1 loss) with smoothing."""
    y = dtrain.get_label()
    residual = predt - y
    epsilon = 1e-6  # smoothing to avoid zero hessian
    grad = np.sign(residual)
    hess = np.ones_like(residual) / (np.abs(residual) + epsilon)
    return grad, hess

# Usage: xgboost.train(params, dtrain, obj=mae_obj, ...)
```

### 3.4 Ensemble Hypotheses

| Strategy | Description | Expected Gain |
|---|---|---|
| **Multi-seed** | Train 3-5 models with different `seed`, average predictions | +1-3% (reduces variance) |
| **Multi-depth** | Train models at depth 4, 6, 8, weighted average | +1-5% (captures different scales) |
| **Stacked** | Train XGBoost on residuals of first XGBoost | +2-5% (corrects systematic bias) |
| **Temporal ensemble** | Separate models for day/night or weekday/weekend | +3-10% if temporal heterogeneity |

---

## 4. Experimentation Protocol (EXPERIMENT)

### 4.1 Rules

1. **One change at a time.** Never change features AND hyperparams simultaneously.
2. **Same evaluation protocol.** Always use TimeSeriesSplit (never random KFold).
3. **Track everything.** Update the experiment log after every trial.
4. **Keep the baseline.** Always compare to the original model, not just the previous attempt.
5. **👁️ Visual before/after.** Generate pred-vs-real plot BEFORE and AFTER each experiment. Compare them visually.

### 4.2 Visual Before/After Comparison

**After each experiment**, generate a comparison plot showing the PREVIOUS best
and the NEW prediction overlaid on the actual signal. **View it** to judge
whether the change genuinely improved the model's behavior.

```python
# Before/after comparison on last 2 weeks
fig, ax = plt.subplots(1, 1, figsize=(18, 5))
last_2w = ts_test >= ts_test.max() - pd.Timedelta(days=14)
ax.plot(ts_test[last_2w], y_test[last_2w], 'b-', lw=1.2, label='Réel')
ax.plot(ts_test[last_2w], y_pred_before[last_2w], 'gray', lw=1, alpha=0.5, label=f'Avant (MAE={mae_before:.2f})')
ax.plot(ts_test[last_2w], y_pred_after[last_2w], 'r-', lw=1.2, alpha=0.8, label=f'Après (MAE={mae_after:.2f})')
ax.axhline(60, c='orange', ls='--', alpha=0.4)
ax.set_title(f'Exp {n}: {hypothesis} — Δ={delta_pct:+.2f}%')
ax.legend()
plt.tight_layout()
plt.savefig(f'/tmp/{model_name}_exp{n}_comparison.png', dpi=150)
```

**Key visual checks:**
- Does the new prediction follow the peaks better?
- Is the amplitude closer to reality?
- Has the phase delay been reduced?
- Has new noise/artifacts appeared?

> **Critical**: A 0.1% MAE improvement is meaningless if the curve looks identical.
> Conversely, a 0.1% MAE degradation may be acceptable if the curve now captures
> peaks that were completely missed before.

### 4.3 Evaluation Metrics (Supporting Evidence)

Metrics reinforce visual assessment. Report ALL of these:
```python
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

mae = mean_absolute_error(y_true, y_pred)
rmse = np.sqrt(mean_squared_error(y_true, y_pred))
r2 = r2_score(y_true, y_pred)
bias = np.mean(y_pred - y_true)  # systematic over/under-prediction
std_ratio = np.std(y_pred) / np.std(y_true)  # signal variability capture

# Conditional metrics (high targets)
hm = y_true >= 60
mae_high = np.abs(y_pred[hm] - y_true[hm]).mean() if hm.sum() > 0 else 0
bias_high = (y_pred[hm] - y_true[hm]).mean() if hm.sum() > 0 else 0

print(f"MAE={mae:.3f} RMSE={rmse:.3f} R²={r2:.4f} Bias={bias:.3f} StdR={std_ratio:.3f}")
print(f"HIGH≥60: MAE={mae_high:.2f} Bias={bias_high:.2f}")
```

**Metric hierarchy** (from most to least informative):
1. 👁️ **Visual impression** — does the curve look good?
2. **std_ratio** — is the predicted variability close to reality? Target: 0.95-1.05
3. **MAE by bin** — where do the errors concentrate?
4. **MAE / RMSE global** — overall summary, but can mask issues

### 4.4 Convergence Criteria

Stop iterating when:
- **👁️ Visual inspection** shows the predicted curve closely follows the actual in shape, amplitude, and timing
- **MAE improvement < 0.5%** for 3 consecutive experiments
- **std_ratio** is between 0.90 and 1.10
- SHAP analysis shows **no actionable pattern** in residuals
- But: **never stop** if the predicted curve visually looks flat or phase-shifted

---

## 5. Feature Selection Protocol

### 5.1 Two-Phase Selection

```python
# Phase 1: Remove features with near-zero importance (fast)
bst_quick = xgboost.train(params, dtrain, num_boost_round=200, verbose_eval=0)
importances = bst_quick.get_score(importance_type='gain')
keep = [f for f in feature_cols if f in importances and importances[f] > 0]
# Always keep temporal features
for f in feature_cols:
    if any(k in f for k in ['lag', 'sin', 'cos', 'hour', 'dow', 'month', 'ma', 'std']):
        if f not in keep:
            keep.append(f)

# Phase 2: Iterative removal of weakest features (if N > 300)
# Remove bottom 10%, retrain, check if MAE worsens. Repeat until it does.
```

### 5.2 Feature Variance Check

```python
# Features with near-zero variance are useless
low_var = X_train.var() < 1e-6
if low_var.sum() > 0:
    print(f"Removing {low_var.sum()} near-zero-variance features")
    X_train = X_train.loc[:, ~low_var]
```

---

## 6. Advanced Techniques

### 6.1 Stacked Residual Correction

When the base model has systematic bias:

```python
# Step 1: Train base model
bst1 = xgboost.train(params, dtrain, ...)
residuals = y_train - bst1.predict(dtrain)

# Step 2: Train correction model on residuals
dtrain_resid = xgboost.DMatrix(X_train, label=residuals)
bst2 = xgboost.train(params_conservative, dtrain_resid, ...)
# Use lower max_depth (3-4) to avoid stacking overfitting

# Step 3: Final prediction = base + correction
y_final = bst1.predict(dtest) + bst2.predict(dtest)
```

### 6.2 Multi-Seed Ensemble

```python
predictions = []
for seed in [42, 137, 256, 314, 628]:
    params['seed'] = seed
    bst = xgboost.train(params, dtrain, num_boost_round=100_000,
                        evals=[(dval, 'val')], early_stopping_rounds=50,
                        verbose_eval=0)
    predictions.append(bst.predict(dtest))
y_ensemble = np.mean(predictions, axis=0)
```

### 6.3 Monotone Constraints

When domain knowledge dictates: "more X → more Y":

```python
# feature index : +1 for increasing, -1 for decreasing, 0 for unconstrained
params['monotone_constraints'] = '(0,1,-1,0,...)'
```

### 6.4 Custom Asymmetric Loss

When under-predicting is worse than over-predicting (or vice versa):

```python
def asymmetric_mse(predt, dtrain, alpha=2.0):
    """Penalizes under-prediction alpha times more than over-prediction."""
    y = dtrain.get_label()
    residual = predt - y
    weight = np.where(residual < 0, alpha, 1.0)
    grad = 2 * residual * weight
    hess = 2 * weight
    return grad, hess
```

---

## 7. User Communication Protocol

**At each iteration, inform the user with a structured update:**

```markdown
### Iteration {n}: {hypothesis_name}
**Hypothesis**: {what you're testing and why}
**Change**: {specific parameter/feature change}
**Result**: MAE {new} vs {baseline} ({delta_pct}%)
**Decision**: ✅ Keep / ❌ Reject
**Next**: {what you'll try next}
```

**At session end, provide summary table:**

```markdown
| # | Experiment | MAE | Δ vs Baseline | Status |
|---|-----------|-----|---------------|--------|
| 0 | Baseline | 7.53 | — | 📊 |
| 1 | max_depth 5→8 | 7.41 | -1.6% | ✅ |
| 2 | + lag residuals | 7.38 | -2.0% | ✅ |
| 3 | Huber loss | 7.42 | -1.5% | ❌ |
| **Best** | **#2** | **7.38** | **-2.0%** | 🏆 |
```

---

## 8. Checklist Before Declaring Convergence

- [ ] 👁️ **Visual: predicted curve closely follows actual** in shape, amplitude, and phase
- [ ] 👁️ **Visual: peaks are captured** — not just the mean level but the extremes
- [ ] **std_ratio** (std_pred / std_real) between 0.90 and 1.10
- [ ] Reliability curve shows predictions close to the diagonal
- [ ] Residuals are approximately centered and symmetric
- [ ] No temporal pattern in errors (by hour, day of week, month)
- [ ] SHAP values show no single feature dominating unexpectedly
- [ ] Holdout MAE is within 5% of CV MAE (no overfitting)
- [ ] At least 5 experiments logged with diminishing returns
- [ ] Model size is reasonable (< 5000 trees with early stopping)
- [ ] User has been informed of final performance and limitations
- [ ] Before/after visual comparison saved for the final iteration
