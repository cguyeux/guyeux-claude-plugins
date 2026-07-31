---
name: causal-inference
description: Causal inference and counterfactual reasoning for machine learning. Use to estimate Average / Conditional / Individual Treatment Effects (ATE/CATE/ITE), test causal hypotheses behind a predictive model, identify confounders via DAGs, and validate findings with refutation tests and sensitivity analyses. Triggers when the user mentions DoWhy, EconML, CausalML, causal-learn, do-calculus, backdoor/frontdoor/instrumental variables, propensity score matching, double machine learning (DML), causal forests, counterfactual, treatment effect heterogeneity, sensitivity analysis (E-value, Rosenbaum bounds), causal discovery (PC, FCI, GES, LiNGAM, NOTEARS), or wants to move from "X is correlated with Y" to "X causes Y" in an ML context.
version: 0.1
license: MIT
---

# Causal Inference - Estimating Causal Hypotheses behind ML Models

Predictive ML answers *"what is Y given X?"*, causal inference answers *"what would Y be if we set X = x?"*. The two questions look similar but require fundamentally different assumptions, estimators, and validation strategies. A model with R² = 0.95 can still produce *causally meaningless* coefficients if confounders are not addressed.

This skill provides a rigorous, end-to-end workflow combining **DoWhy** (the unifying causal API), **EconML** (ML estimators for heterogeneous effects), **CausalML** (Uber's uplift / meta-learners) and **causal-learn** (causal discovery from observational data), with the statistical safeguards expected in scientific publications.

## When to Use

- A predictive model is suspected to capture **spurious associations** (Simpson's paradox, confounding, collider bias).
- Estimating the **Average Treatment Effect (ATE)** of an intervention from observational data (no RCT available).
- Estimating **Conditional / Individual Treatment Effects (CATE / ITE)** to identify subgroups with heterogeneous response (precision medicine, personalized policy).
- Testing **counterfactual** questions: *"What would have happened to patient i if we had not given treatment T?"*.
- Auditing an ML model for **causal validity** before deploying it as a decision-support tool.
- **Causal discovery**: learning a plausible DAG structure from observational data when no expert prior is available.
- Performing **sensitivity analysis** to quantify how strong an unmeasured confounder would need to be to overturn a conclusion.
- Writing the *causal assumptions* section of a scientific paper (target trial emulation, ROBINS-I checklist).

## Reference Documentation

- **DoWhy**: https://www.pywhy.org/dowhy/main/
- **EconML**: https://econml.azurewebsites.net/
- **CausalML (Uber)**: https://causalml.readthedocs.io/
- **causal-learn**: https://causal-learn.readthedocs.io/
- **PyWhy ecosystem (umbrella)**: https://www.pywhy.org/
- Foundational reading: Pearl 2009 *Causality*; Hernán & Robins *Causal Inference: What If* (free PDF: https://miguelhernan.org/whatifbook); Imbens & Rubin 2015.

## Conceptual Foundation

### The Causal Hierarchy (Pearl's Ladder)

| Level | Question | Example | Tool |
|-------|----------|---------|------|
| 1. Association | P(Y \| X) | "Patients on drug A have lower mortality." | sklearn, statsmodels |
| 2. Intervention | P(Y \| do(X)) | "If we *give* drug A, what is mortality?" | DoWhy, EconML |
| 3. Counterfactual | P(Y_x \| X', Y') | "Would *this* patient have died without drug A?" | DoWhy + structural models |

ML lives natively on Level 1. Moving up requires *external* assumptions that cannot be tested from the data alone, they must be made explicit through a causal graph.

### Identifying Assumptions (must be stated and defended)

1. **SUTVA** : Stable Unit Treatment Value Assumption: no interference between units, single version of treatment.
2. **Ignorability / Conditional exchangeability**, given the adjustment set Z, treatment is independent of potential outcomes: `Y(0), Y(1) ⊥ T | Z`.
3. **Positivity / Overlap**, for every covariate stratum, both treated and untreated units exist: `0 < P(T=1 | Z) < 1`.
4. **Consistency**, observed outcome equals the potential outcome under the received treatment.
5. **No unmeasured confounding** OR explicit instrument / front-door / proximal identification.

State each assumption in the methods section. Skipping this is the single most common reason causal papers are rejected.

## Quick Reference

### Installation

```bash
pip install dowhy econml causal-learn causalml networkx graphviz
# Optional: pip install pygraphviz   # nicer DAG layouts
```

### Standard Imports

```python
import numpy as np
import pandas as pd
import networkx as nx
import dowhy
from dowhy import CausalModel
import econml
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
```

## The DoWhy 4-Step Workflow (Canonical Pattern)

DoWhy enforces a discipline that separates *identification* (a graph-theoretic question, no data needed) from *estimation* (a statistical question), and adds *refutation* as a first-class step.

```python
from dowhy import CausalModel

# ── Step 1. MODEL ──────────────────────────────────────────────
# Encode prior knowledge as a DAG (GML or DOT string, or a NetworkX graph)
graph = """
graph [directed 1
  node [id "T" label "Treatment"]
  node [id "Y" label "Outcome"]
  node [id "W1" label "Age"]
  node [id "W2" label "Comorbidity"]
  node [id "Z"  label "Instrument"]
  edge [source "W1" target "T"]
  edge [source "W1" target "Y"]
  edge [source "W2" target "T"]
  edge [source "W2" target "Y"]
  edge [source "Z"  target "T"]
  edge [source "T"  target "Y"]
]
"""
model = CausalModel(data=df, treatment="T", outcome="Y", graph=graph)
model.view_model()  # renders the DAG — sanity-check the structure

# ── Step 2. IDENTIFY ───────────────────────────────────────────
# Ask: is the causal effect identifiable from the observed variables?
estimand = model.identify_effect(proceed_when_unidentifiable=False)
print(estimand)  # backdoor / frontdoor / IV expression(s)

# ── Step 3. ESTIMATE ───────────────────────────────────────────
estimate = model.estimate_effect(
    estimand,
    method_name="backdoor.propensity_score_weighting",
    target_units="ate",          # or "att", "atc", or a callable
    confidence_intervals=True,
    test_significance=True,
)
print(f"ATE = {estimate.value:.3f}  CI = {estimate.get_confidence_intervals()}")

# ── Step 4. REFUTE ─────────────────────────────────────────────
# A causal estimate that survives no refutation test is not trustworthy.
for refuter in [
    "random_common_cause",        # adding noise covariate must NOT change estimate
    "placebo_treatment_refuter",  # randomized T must give estimate ≈ 0
    "data_subset_refuter",        # estimate must be stable across random subsets
    "add_unobserved_common_cause" # bound the effect of plausible hidden confounders
]:
    res = model.refute_estimate(estimand, estimate, method_name=refuter)
    print(res)
```

**Reading the refutation output**: a *passed* refutation means the test could not falsify the estimate. Report all four; never cherry-pick.

## Identification Strategies : Choosing the Right Estimator

| Strategy | When to use | DoWhy `method_name` |
|----------|------------|---------------------|
| **Backdoor adjustment** | All confounders observed | `backdoor.linear_regression`, `backdoor.propensity_score_matching`, `backdoor.propensity_score_weighting`, `backdoor.propensity_score_stratification` |
| **Doubly Robust** | Want robustness to misspecification of either outcome OR propensity model | `backdoor.econml.dr.LinearDRLearner` (via EconML) |
| **Double / Debiased ML** | Many high-dimensional confounders, want ML nuisance models with valid CIs | `backdoor.econml.dml.LinearDML`, `CausalForestDML` |
| **Instrumental Variable** | Unmeasured confounding but a valid instrument exists | `iv.instrumental_variable`, `iv.linear_instrumental_variable` |
| **Front-door** | Mediator fully captures the causal pathway, confounders unobserved | `frontdoor.two_stage_regression` |
| **Regression Discontinuity** | Treatment assigned by a sharp threshold on a running variable | `iv.regression_discontinuity` |
| **Mediation** | Decompose total effect into direct + indirect | `mediation.two_stage_regression` |

## Heterogeneous Treatment Effects with EconML

When the question shifts from *"does T work on average?"* to *"for whom does T work?"*, switch to CATE estimators. They couple flexible ML (gradient boosting, neural nets, random forests) with the orthogonalisation tricks needed for valid inference.

```python
from econml.dml import CausalForestDML
from econml.dr import DRLearner
from econml.metalearners import XLearner, TLearner, SLearner

# ── Causal Forest with Double ML ──────────────────────────────
cf = CausalForestDML(
    model_t=GradientBoostingClassifier(),   # propensity model
    model_y=GradientBoostingRegressor(),    # outcome model
    discrete_treatment=True,
    n_estimators=2000,
    min_samples_leaf=10,
    cv=5,                                   # cross-fitting → valid CIs
    random_state=0,
)
cf.fit(Y=df["Y"], T=df["T"], X=df[cate_features], W=df[confounders])

# Point estimates and 95 % CIs for every unit
cate = cf.effect(df[cate_features])
lb, ub = cf.effect_interval(df[cate_features], alpha=0.05)

# Feature importance for treatment-effect heterogeneity (NOT outcome)
print(cf.feature_importances_)

# Best Linear Projection — interpretable summary of CATE drivers
print(cf.summary())
```

**Meta-learner cheat sheet**:

- **S-Learner**: single model, T as feature. Underfits heterogeneity when effect is small.
- **T-Learner**: separate models for T=0, T=1. Overfits with class imbalance.
- **X-Learner**: imputes counterfactuals, cross-fits. Best when class sizes are very unequal.
- **R-Learner / DR-Learner**: Neyman-orthogonal losses, robust to nuisance misspecification. **Default scientific choice**.

## Validation Beyond Refutation : Sensitivity Analysis

A passed refutation is necessary, not sufficient. Quantify *how strong* an unmeasured confounder would have to be to nullify the result.

### E-value (VanderWeele & Ding, 2017)

```python
# Manual E-value for a risk ratio RR > 1
def e_value(rr):
    return rr + np.sqrt(rr * (rr - 1))

print(f"E-value = {e_value(1.8):.2f}")
# Interpretation: an unmeasured confounder would need to be associated with both
# treatment and outcome by a risk ratio of at least E-value to fully explain RR.
```

### Rosenbaum Bounds (matched designs)

Available via `dowhy.causal_refuters.add_unobserved_common_cause` with `effect_strength_on_treatment` and `effect_strength_on_outcome` swept across a grid. Plot the resulting effect surface, the *tipping point* is the configuration where ATE crosses zero.

### Partial R² Sensitivity (Cinelli & Hazlett, 2020)

Implemented in `sensemakr` (R) and `PySensemakr`:

```python
from sensemakr import Sensemakr
sens = Sensemakr(model=ols_results, treatment="T",
                 benchmark_covariates=["education"], kd=[1, 2, 3])
sens.summary()
sens.plot()
```

Report the *robustness value* RV_q, the minimum strength of confounding (in partial R² units) that would reduce the estimated effect by q %.

## Causal Discovery : When the DAG Is Not Known

Use only when expert knowledge is insufficient. Always treat the output as a *hypothesis* to be validated experimentally, not as ground truth.

```python
from causallearn.search.ConstraintBased.PC import pc
from causallearn.search.ConstraintBased.FCI import fci
from causallearn.search.ScoreBased.GES import ges
from causallearn.search.FCMBased import lingam

# PC algorithm — assumes causal sufficiency (no hidden confounders)
cg = pc(data.values, alpha=0.05, indep_test="fisherz")
cg.draw_pydot_graph(labels=list(data.columns))

# FCI — allows latent confounders, returns a PAG
g, edges = fci(data.values, alpha=0.05)

# GES — score-based, returns a CPDAG
record = ges(data.values, score_func="local_score_BIC")

# LiNGAM — exploits non-Gaussianity for full DAG identification
model = lingam.DirectLiNGAM()
model.fit(data)
print(model.adjacency_matrix_)
```

For continuous, differentiable discovery: **NOTEARS** (`pip install notears`) and **DAGMA** formulate DAG learning as a continuous optimisation under an acyclicity constraint.

**Critical caveat**: discovery algorithms output *Markov-equivalence classes* (CPDAGs / PAGs), not unique DAGs. Several causal structures may fit the data equally well. Always combine with domain expertise and orient ambiguous edges by intervention experiments when possible.

## Critical Rules

### ✅ DO

- **Draw the DAG first, look at the data second.** The graph encodes assumptions that the data cannot teach you.
- **Justify every adjustment.** Adjusting on a *collider* or a *mediator* induces bias rather than removing it.
- **Use cross-fitting** (sample-splitting) when nuisance functions are estimated with ML, this is what makes DML inference valid.
- **Check positivity / overlap** before any propensity-based method: plot the propensity score distribution by treatment arm.
- **Run all four refuters** and at least one quantitative sensitivity analysis.
- **Pre-register** the DAG, adjustment set, estimator, and refutation plan when possible.
- **Report effects on the additive scale** (ATE) AND a multiplicative scale (RR / OR), readers from different fields will look for different things.

### ❌ DON'T

- **Don't adjust for post-treatment variables** (mediators, colliders downstream of T), this opens spurious paths.
- **Don't interpret feature importance from a predictive model as causal effect.** Importance reflects predictive value given correlated covariates, not intervention effect.
- **Don't use the same data to discover the DAG and to estimate the effect** without holding out a confirmation set.
- **Don't trust an estimate that survives no refutation test.**
- **Don't use propensity score matching with extreme positivity violations**, discard non-overlapping units and report the trimmed estimand explicitly.

## Anti-Patterns (NEVER)

```python
# ❌ BAD: feeding the entire feature set to an ML model and reading
# the coefficient of T as the causal effect.
model = GradientBoostingRegressor().fit(X_with_T_and_mediators, y)
# Mediators ABSORB the indirect effect; colliders OPEN spurious paths.

# ✅ GOOD: identify the adjustment set FIRST via the DAG.
adjustment_set = model.identify_effect().get_backdoor_variables()
# Only then fit on Y, T, adjustment_set.

# ❌ BAD: claiming "the estimate is robust" because p < 0.05.
# p-values address sampling variability, not unmeasured confounding.

# ✅ GOOD: report E-value, partial R² robustness value, and refuter outputs.

# ❌ BAD: choosing the estimator that gives the "expected" sign.
# ✅ GOOD: pre-specify the estimator; report all variants in supplementary.
```

## Practical Workflows

### 1. Auditing an ML Model for Causal Validity

```python
def audit_ml_for_causal_claim(df, treatment, outcome, dag, ml_features):
    """Test whether an ML model's reliance on `treatment` is causally justified."""
    model = CausalModel(data=df, treatment=treatment, outcome=outcome, graph=dag)
    estimand = model.identify_effect()

    # 1. Pure-ML coefficient (predictive)
    from sklearn.ensemble import GradientBoostingRegressor
    gbm = GradientBoostingRegressor().fit(df[ml_features], df[outcome])
    # SHAP value of `treatment` ≈ predictive contribution

    # 2. Causal estimate via DML
    causal = model.estimate_effect(
        estimand,
        method_name="backdoor.econml.dml.LinearDML",
        method_params={"init_params": {"discrete_treatment": False, "cv": 5}},
    )

    # 3. Discrepancy diagnoses
    return {
        "predictive_signal": "see SHAP report",
        "causal_ate": causal.value,
        "causal_ci": causal.get_confidence_intervals(),
        "refuters": {r: model.refute_estimate(estimand, causal, method_name=r)
                     for r in ["random_common_cause", "placebo_treatment_refuter"]},
    }
```

### 2. Target Trial Emulation Skeleton

```python
# Hernán & Robins framework — emulate a hypothetical RCT with observational data.
trial_spec = {
    "eligibility":  "df['age'].between(40, 75) & df['baseline_dx'] == 1",
    "treatment":    "drug_A",
    "comparator":   "drug_B",
    "outcome":      "5y_mortality",
    "assignment":   "as observed (no randomization)",
    "followup":     "from time-zero (first eligible visit) to event/censoring",
    "estimand":     "per-protocol ATE; ITT not applicable in observational data",
    "analysis":     "IPTW with stabilized weights; censoring weights for loss-to-followup",
}
# Each row of trial_spec maps to a methodological choice that must be defended.
```

### 3. Heterogeneous Effect Discovery

```python
from econml.cate_interpreter import SingleTreeCateInterpreter, SingleTreePolicyInterpreter

# After fitting CausalForestDML `cf` (see EconML section)
interp = SingleTreeCateInterpreter(include_model_uncertainty=True, max_depth=3)
interp.interpret(cf, df[cate_features])
interp.plot(feature_names=cate_features)  # tree of CATE-drivers

policy = SingleTreePolicyInterpreter(risk_level=None, max_depth=3)
policy.interpret(cf, df[cate_features], sample_treatment_costs=0.0)
policy.plot(feature_names=cate_features)  # optimal-policy tree
```

## Reporting Checklist (for scientific manuscripts)

A causal-inference section that satisfies reviewers should contain:

1. **Causal question** in PICO form (Population, Intervention, Comparator, Outcome).
2. **DAG** (figure) with citations supporting each edge / non-edge.
3. **Identification strategy** (backdoor / frontdoor / IV / DML) and the assumed adjustment set.
4. **Estimator** with hyperparameters, cross-fitting scheme, and software versions.
5. **Positivity / overlap** diagnostic (propensity score plot or covariate balance table).
6. **Point estimate, 95 % CI, and a relative-scale equivalent**.
7. **At least three refuters** (random common cause, placebo, subset).
8. **Quantitative sensitivity analysis** (E-value or robustness value).
9. **Statement of remaining limitations**, what assumptions could still be violated, and the direction of the resulting bias.

This roughly maps to the **ROBINS-I** checklist for non-randomized studies and the **STROBE** extension for causal claims.

## Common Pitfalls and Solutions

### Collider Conditioning ("Berkson's Bias")

Adjusting for a variable that is a *common effect* of T and Y opens a non-causal path. Use `dowhy`'s `model.view_model()` and trace every path manually before fitting.

### Positivity Violations

```python
# Diagnosis
ps = LogisticRegression().fit(W, T).predict_proba(W)[:, 1]
import matplotlib.pyplot as plt
for t in [0, 1]:
    plt.hist(ps[T == t], bins=40, alpha=0.5, label=f"T={t}", density=True)
plt.legend(); plt.xlabel("Propensity score")
# Solution: trim units with ps < 0.05 or ps > 0.95 and report the *trimmed* estimand.
```

### Time-Varying Treatment & Confounding

Standard adjustment fails when confounders are themselves affected by past treatment (treatment-confounder feedback). Use **g-methods**: g-formula, marginal structural models with IPTW, or g-estimation. See `zEpid` and `pylife-lines` for Python implementations.

### Mediator vs Confounder Confusion

A variable that lies *on* the causal path is a mediator (do not adjust for it if you want the *total* effect). A variable that *causes* both T and Y is a confounder (must adjust). The DAG is the only way to tell them apart.

## Going Further

- **Proximal causal inference** (Tchetgen Tchetgen et al.): identification with unmeasured confounders via negative-control variables.
- **Synthetic controls** (`pysyncon`, `SparseSC`): single-unit interventions over time.
- **Difference-in-Differences** (`differences`, `pydid`): policy changes with parallel-trends assumption.
- **Bayesian causal inference** (`bcf`, `bartcause`): credible intervals with informative priors on confounding.
- **Causal representation learning**: `CausalNex` (Bayesian-network-based ML) and `causalml`'s uplift trees for marketing/policy.

Causal inference is where machine learning earns the right to be called *scientific*. The estimators are sophisticated, but the harder work is upstream: writing down the DAG, defending the assumptions, and pre-committing to the refutation plan. Done well, this turns "X predicts Y" into a defensible "X causes Y" claim that survives peer review.
