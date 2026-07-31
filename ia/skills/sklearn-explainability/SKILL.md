---
name: sklearn-explainability
description: >-
  scikit-learn sub-skill for interpreting a fitted model: permutation importance, partial
  dependence and ICE curves, coefficient interpretation under collinearity, and SHAP/LIME
  integration. Use when the user asks which features matter and why, when a feature-
  importance ranking must be defended in a paper, when built-in impurity importances look
  suspicious on high-cardinality features, or when producing an interpretability figure. For
  a fast SHAP path on tree models, use TreeExplainer rather than the model-agnostic
  explainer.
version: 1.4
license: BSD-3-Clause
---

# scikit-learn - Explainability & Interpretability

In scientific research, a model's "why" is as important as its "what". This guide focuses on tools that reveal the decision-making process of machine learning models, ensuring they are scientifically valid and not just overfitting on artifacts.

## When to Use

- Validating that a model uses physically meaningful features (e.g., in drug discovery).
- Identifying biases or "shortcuts" the model has learned from the training data.
- Explaining individual predictions to non-experts (Local explanations).
- Ranking the global impact of variables on a complex system (Global explanations).
- Scientific auditing and regulatory compliance.

## Core Principles

### 1. Model-Specific vs. Model-Agnostic

- **Model-Specific**: Tools like `feature_importances_` in Random Forests. Fast but tied to one architecture.
- **Model-Agnostic**: Tools like SHAP or Permutation Importance. Work on any model (SVM, MLP, etc.) but are more compute-intensive.

### 2. Global vs. Local Explanations

- **Global**: How does the feature "Temperature" affect the model overall?
- **Local**: Why did the model predict "Reaction Failed" for this specific sample?

### 3. Feature Importance vs. Feature Contribution

Importance tells you if a feature is used; Contribution tells you how it changed the output (positive or negative).

## Quick Reference: Built-in Inspection

```python
from sklearn.inspection import permutation_importance, PartialDependenceDisplay

# 1. Permutation Importance (Better than default tree importance)
result = permutation_importance(model, X_test, y_test, n_repeats=10)
print(result.importances_mean)

# 2. Partial Dependence Plots (How one feature affects prediction)
PartialDependenceDisplay.from_estimator(model, X, features=['temp', 'pressure'])
```

## Critical Rules

### ✅ DO

- **Prefer Permutation Importance over default RandomForest.feature_importances_** - Default importance is biased toward high-cardinality features (like unique IDs).
- **Use PartialDependenceDisplay** - To visualize the relationship between a feature and the target (Linear, Exponential, or Sigmoid).
- **Scale Features before Interpretability** - Many models (like Logistic Regression) require scaling for their coefficients (β) to be comparable.
- **Check Feature Correlations** - If two features are highly correlated, importance will be split between them, making both look "less important" than they are.

### ❌ DON'T

- **Don't trust coefficients (β) of unregularized models** - High variance in coefficients can lead to false conclusions about feature importance.
- **Don't use Feature Importance on Training Data** - Always calculate it on the Test Set to see what features actually help with generalization.
- **Don't confuse Correlation with Causation** - ML models show which features are predictive, not necessarily which ones are causative.

## Interpretation Patterns

### 1. SHAP Integration (The Gold Standard)

```python
import shap

# Let shap dispatch on the model object. For tree ensembles (RandomForest,
# GradientBoosting, XGBoost, LightGBM) this selects TreeExplainer: exact
# Shapley values, and orders of magnitude faster than the agnostic path.
explainer = shap.Explainer(model, X_train)
shap_values = explainer(X_test)

# Visualize global importance
shap.plots.bar(shap_values)

# Visualize local explanation for the first sample
shap.plots.waterfall(shap_values[0])
```

**Do not write `shap.Explainer(model.predict, X_test)`.** Passing the bound
`predict` method hides the model type, so shap falls back to the model-agnostic
Permutation or Kernel explainer: approximate values, and minutes-to-hours instead
of seconds on a forest. Pass the estimator itself.

| Model family | Explainer selected | Cost |
|---|---|---|
| Tree ensembles | `TreeExplainer` | fast, exact |
| Linear models | `LinearExplainer` | fast, exact (given the background) |
| Neural nets (torch/tf) | `DeepExplainer` / `GradientExplainer` | moderate |
| Anything else, or a bare callable | `PermutationExplainer` / `KernelExplainer` | slow, approximate |

For multiclass output, `shap_values` gains a trailing class axis: index it
(`shap_values[..., k]`) before plotting, or the plot silently shows class 0.

Background data matters. `shap.Explainer(model, X_train)` uses `X_train` as the
reference distribution; on a large training set pass a summary
(`shap.sample(X_train, 100)` or `shap.kmeans(X_train, 25)`) rather than the whole
matrix, and keep it fixed across figures so values stay comparable.

### 2. Partial Dependence (PDP) for Science

```python
from sklearn.inspection import PartialDependenceDisplay

# Check if the model learned the correct physical law
# (e.g., does the reaction rate increase with temperature?)
fig, ax = plt.subplots(figsize=(8, 4))
PartialDependenceDisplay.from_estimator(model, X, [0, (0, 1)], ax=ax)
# [0] is a 1D plot, [(0, 1)] is a 2D interaction plot
```

### Advanced: Feature Contribution for a Linear Model

For a single prediction from a linear or logistic model, the contribution of each
feature is exactly `coef * value`, summing with the intercept to the log-odds.
This is worth computing by hand rather than reaching for SHAP: it is exact,
instant, and directly reportable in a manuscript.

```python
import numpy as np
import pandas as pd

def explain_linear(model, sample, feature_names):
    """sample: 1-row DataFrame or 2D array of shape (1, n_features)."""
    x = np.asarray(sample).ravel()
    coef = np.ravel(model.coef_)          # binary case; multiclass: model.coef_[k]
    contrib = coef * x
    logit = float(model.intercept_[0] + contrib.sum())
    return pd.DataFrame({
        "feature": feature_names,
        "value": x,
        "coef": coef,
        "contribution": contrib,
    }).sort_values("contribution", key=np.abs, ascending=False), logit

table, logit = explain_linear(clf, X_test.iloc[[0]], X_test.columns)
print(table.head(10))
print("log-odds:", logit, "-> p =", 1 / (1 + np.exp(-logit)))
```

Two caveats. The contributions are on the scale the model was fitted on, so if a
`StandardScaler` sits in the pipeline the coefficients refer to standardised
units: pull the fitted scaler out and report either the standardised
contributions or `coef / scale_` in original units, but say which. And with
correlated predictors, an individual coefficient is not the effect of that
feature alone, whatever its magnitude.

## Practical Workflows: Validating a Scientific Model

### Step 1: Detect "Leakage" Features

If a feature has 99% importance and wasn't expected to, it's likely a data leak (e.g., a sample timestamp or ID).

### Step 2: Stability Analysis

Run permutation importance with different random seeds. If the top features change significantly, the model is unstable and unreliable.

### Step 3: Interaction Check

Use 2D PDP to see if the model captured the interaction between features (e.g., Pressure only matters if Temperature > 100°C).

## Common Pitfalls

### The "Default Importance" Bias

In RandomForest, features with many categories (like Serial_Number) look very important because the tree can split on them many times.

```python
# ✅ Solution: Use Permutation Importance on the test set instead.
```

### Multicollinearity Ghosting

If Feature_A and Feature_B are 100% correlated, the model might only use one.

```python
# ✅ Solution: Use hierarchical clustering on features or check VIF 
# before interpreting importance.
```

Explainability turns Machine Learning into a true scientific tool. It allows researchers to move beyond the "Black Box" and extract new hypotheses directly from trained models.
