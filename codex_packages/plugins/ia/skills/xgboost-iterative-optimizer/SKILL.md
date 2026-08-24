---

name: xgboost-iterative-optimizer
description: >-
  Iterative XGBoost model optimization using a scientific ML researcher workflow.
  Diagnose prediction errors through VISUAL INSPECTION of predicted-vs-actual
  curves (primary), reinforced by SHAP, residual analysis, and metrics.
  Improve models through feature engineering, hyperparameter tuning, objective
  function selection, and ensemble strategies.

  Use when: XGBoost predictions are poor, MAE/RMSE needs reduction, residuals
  show patterns, model under/overfits, or "predictions are too flat/biased."
---

# XGBoost Iterative Optimizer

**Role**: Experienced ML researcher who iteratively improves XGBoost regression models.

**Core constraint**: XGBoost only. `num_boost_round=100_000` with `early_stopping_rounds`.

**Primary diagnostic**: ALWAYS look at the curves first. A metric is just a number.

For complete code templates (plotting, SHAP, residuals, ensembles), see [references/code-templates.md](references/code-templates.md).

## 1. Optimization loop

```
VISUAL INSPECT -> DIAGNOSE -> HYPOTHESIZE -> EXPERIMENT -> COMPARE -> EVALUATE -> LOG -> REPEAT
```

### Session initialization

Create an experiment log at `/tmp/{model_name}_optim_log.md` tracking baseline metrics, each experiment, and decisions.

## 2. Diagnostic phase

### 2.0 Visual diagnostic (PRIMARY)

Generate pred-vs-actual plots for: last 2 weeks, last month, worst week. **Look at them** and answer:

| Question | If YES |
|---|---|
| Predicted curve flat/smooth? | Increase `max_depth`, reduce regularization |
| Peaks under-predicted? | Add sample weighting, asymmetric loss |
| Phase delay? | Add recent lags (lag1, lag2) |
| Low variability? (std_ratio < 0.8) | Increase depth, reduce reg |
| Weekly pattern missing? | Add cyclic features, `is_weekend` |

**Key metric**: `std_ratio = std(y_pred) / std(y_true)`. Target: 0.95-1.05.

### 2.1 Residual analysis

Plot: distribution, residuals vs predicted, residuals over time, reliability curve, error by hour, QQ plot.

### 2.2 Diagnostic decision tree

| Observation | Action |
|---|---|
| Systematic bias | Huber loss or asymmetric loss |
| Heteroscedasticity | Log-transform target or `reg:gamma` |
| Temporal patterns in residuals | Add cyclic features, lag residuals |
| Heavy tails | Huber loss, cap target |
| Flat predictions | Increase `max_depth`, add high-variance features |
| High error at specific hours | Hour-specific features |
| Predictions lag behind reality | Add recent lags, reduce `min_child_weight` |

### 2.3 SHAP analysis

Focus on HIGH ERROR samples, compare mean |SHAP| between high-error and low-error to find features driving errors.

## 3. Hypothesis generation

### Feature engineering (priority order)

| Category | Features |
|---|---|
| Temporal | `hour_sin/cos`, `dow_sin/cos`, `is_holiday`, `day_of_year` |
| Lag enrichment | `target_lag{1..168}`, `same_hour_yesterday/last_week` |
| Rolling stats | `rolling_mean_{3,6,12,24,48,168}`, `rolling_std/min/max` |
| Interaction | `feature_A * feature_B` for top SHAP pairs |
| Residual feedback | `residual_lag1` |
| External | Weather, calendar, events |

### Hyperparameter tuning (priority order)

1. `max_depth` (4->6->8->10)
2. `learning_rate` (0.1->0.03->0.01->0.005)
3. `min_child_weight` (1->5->15->30->50)
4. `subsample` / `colsample_bytree` (0.6->0.8->0.95)
5. `gamma` (0->0.1->0.5->1.0)
6. `reg_alpha` / `reg_lambda` (0.001->0.1->1->10)

### Objective functions

| Objective | Use when |
|---|---|
| `reg:squarederror` | Symmetric errors, no outliers |
| `reg:pseudohubererror` | Outliers present |
| `reg:tweedie` | Right-skewed count data |
| `reg:gamma` | Strictly positive, heteroscedastic |
| Custom asymmetric | Under-predicting is worse |

### Ensemble strategies

| Strategy | Expected gain |
|---|---|
| Multi-seed (3-5 seeds, average) | +1-3% |
| Multi-depth (4, 6, 8, weighted) | +1-5% |
| Stacked residual correction | +2-5% |
| Temporal (day/night separate) | +3-10% |

## 4. Experimentation protocol

1. **One change at a time.** Never change features AND hyperparams simultaneously.
2. **Same evaluation.** Always TimeSeriesSplit, never random KFold.
3. **Track everything.** Update experiment log after every trial.
4. **Visual before/after.** Compare curves, not just numbers.

### Metrics (supporting evidence, not primary)

Report: MAE, RMSE, R2, Bias, std_ratio, MAE_high (>=60), Bias_high.

**Hierarchy**: visual impression > std_ratio > MAE by bin > MAE/RMSE global.

### Convergence criteria

Stop when: curves follow actual (shape, amplitude, timing) + MAE improvement < 0.5% for 3 experiments + std_ratio 0.90-1.10. **Never stop** if curve looks flat or phase-shifted.

## 5. User communication

At each iteration:
```
### Iteration {n}: {hypothesis}
**Hypothesis**: {what and why}
**Change**: {specific change}
**Result**: MAE {new} vs {baseline} ({delta_pct}%)
**Decision**: Keep / Reject
**Next**: {planned action}
```
