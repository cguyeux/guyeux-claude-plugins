---
name: ml-model-explainer
description: >-
  Explain the predictions of a fitted model with SHAP values, permutation and built-in
  feature importance, and per-instance decision paths, with plots. Use when the user asks
  why a model predicted a given outcome, which features drive it, how to produce a SHAP
  summary or waterfall plot for a manuscript figure, or how to audit a model before trusting
  its ranking. For the underlying scikit-learn inspection API and the LIME/SHAP trade-offs,
  see sklearn-explainability.
---

# ML Model Explainer

Explain machine learning model predictions using SHAP and feature importance.

## Features

- **SHAP Values**: Explain individual predictions
- **Feature Importance**: Global feature rankings
- **Decision Paths**: Trace prediction logic
- **Visualizations**: Waterfall, force plots, summary plots
- **Multiple Models**: Support for tree-based, linear, neural networks
- **Batch Explanations**: Explain multiple predictions

## Quick Start

```python
import sys
sys.path.insert(0, "<skill_path>/scripts")
from ml_model_explainer import MLModelExplainer

expl = MLModelExplainer()
expl.load_model(model, X_test)      # background frame; see the note below

# SHAP values for the whole frame (explain() takes a DataFrame, not a row)
shap_values = expl.explain(X_test)

# Per-instance waterfall: (instance_index, output_path)
expl.plot_waterfall(0, "waterfall_0.png")

# Global summary plot
expl.plot_summary("summary.png")

# Global importance as a sorted DataFrame (feature, importance)
importance = expl.feature_importance()
```

Three things the signatures do not make obvious:

- `explain()` expects a 2D DataFrame. Passing a single row as `X_test[0]` (a
  Series, or a column for a DataFrame) raises rather than explaining one instance.
  For one instance, pass `X_test.iloc[[0]]` and then use `instance_index=0`.
- `plot_waterfall(instance_index, output)` takes the index first and the output
  path second. It reads the feature values from the frame given to `load_model`,
  so pass the **same frame** to `load_model` and to `explain`, otherwise the plot
  shows the right SHAP values against the wrong feature values.
- `feature_importance()` averages `|SHAP|` over rows. For a multiclass model the
  SHAP array has a trailing class axis; select one class first
  (`expl.shap_values = shap_values[..., k]`) or the mean collapses the classes
  together.

The explainer is selected from the model type: `TreeExplainer` for trees and
ensembles (exact and fast), `LinearExplainer` for models with `coef_`, and
`KernelExplainer` otherwise (approximate and much slower). If a run is
unexpectedly slow, the model fell through to the kernel path.

## CLI Usage

```bash
python3 <skill_path>/scripts/ml_model_explainer.py \
  --model model.pkl --data test.csv --output explanations/
```

The model is loaded with `pickle`, so it must have been saved by a compatible
scikit-learn version in the same environment.

## Dependencies

- shap>=0.42.0
- scikit-learn>=1.3.0
- pandas>=2.0.0
- numpy>=1.24.0
- matplotlib>=3.7.0
