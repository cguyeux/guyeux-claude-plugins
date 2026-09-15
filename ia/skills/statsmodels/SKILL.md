---
name: statsmodels
description: Advanced statistical modeling and hypothesis testing. Complementary to SciPy's stats module, it provides classes and functions for the estimation of many different statistical models, as well as for conducting statistical tests and statistical data exploration. Use for linear regression, GLM, time series analysis, ANOVA, survival analysis, causal inference, and statistical hypothesis testing. Load when working with OLS, WLS, logistic regression, Poisson regression, ARIMA, SARIMAX, statistical diagnostics, p-values, confidence intervals, or R-style statistical analysis.
version: 0.14
license: BSD-3-Clause
---

# Statsmodels - Statistical Modeling & Inference

Statsmodels is the bridge between Python and the rigor of R-style statistical analysis. It allows users to estimate models using formulas (via patsy), perform extensive diagnostic tests, and produce detailed summary tables that are the standard in academic publishing.

## When to Use

- Estimating Linear Regression models with detailed diagnostics (OLS, WLS).
- Generalized Linear Models (GLM): Logistic, Poisson, Gamma regression.
- Time Series Analysis (ARIMA, SARIMAX, VAR, State Space models).
- Statistical hypothesis testing (t-tests, ANOVA, normality, heteroscedasticity).
- Survival analysis (Kaplan-Meier, Cox Proportional Hazards).
- Estimating treatment effects and causal inference.
- Non-parametric statistics (Kernel Density Estimation).
- **Mixed-effects models (MixedLM) and GEE**, to control for the non-independence
  created by shared ancestry: clonal lineages, structured populations, related
  languages or cultures. See "Mixed Models" below; this is the standard answer
  when a reviewer objects that the samples are not independent.
- **Multiple-testing correction** (`statsmodels.stats.multitest`), Benjamini-Hochberg
  FDR for genome-scale scans.

## Reference Documentation

**Official docs**: https://www.statsmodels.org/stable/  
**Formula API**: https://www.statsmodels.org/stable/example_formulas.html  
**Search patterns**: `sm.OLS`, `smf.ols`, `sm.tsa`, `results.summary()`, `statsmodels.api`

## Core Principles

### Statsmodels vs. scikit-learn

| Feature | scikit-learn | Statsmodels |
|---------|--------------|-------------|
| Goal | Prediction (Accuracy) | Inference (Explanation/p-values) |
| Interface | fit / predict | fit / summary |
| Pre-processing | Pipeline objects | Formulas (Patsy) or design matrices |
| Diagnostics | Cross-validation | Residue analysis, p-values, CI |

### The Two APIs

- **API (statsmodels.api)**: Requires explicit addition of a constant (intercept) and uses NumPy-like arrays.
- **Formula API (statsmodels.formula.api)**: Uses R-style formulas (`y ~ x1 + x2`) and works directly with Pandas DataFrames. (Recommended for most users).

## Quick Reference

### Installation

```bash
pip install statsmodels patsy
```

### Standard Imports

```python
import statsmodels.api as sm
import statsmodels.formula.api as smf
import pandas as pd
import numpy as np
```

### Basic Pattern - Ordinary Least Squares (OLS)

```python
import statsmodels.formula.api as smf

# 1. Define model with R-style formula
# 'y ~ x1 + x2' means: y = beta0 + beta1*x1 + beta2*x2
# One row per isolate; C(...) marks a categorical predictor.
model = smf.ols('root_to_tip ~ collection_year + C(lineage)', data=df)

# 2. Fit the model
results = model.fit()

# 3. Print the comprehensive results table
print(results.summary())

# 4. Access specific values
p_values = results.pvalues
params = results.params # beta coefficients
```

## Critical Rules

### ✅ DO

- **Check Residuals** - Always plot and test residuals (`results.resid`) for normality and homoscedasticity.
- **Add a Constant** - If using the `sm.api` (not formula), remember `X = sm.add_constant(X)` or your model will pass through the origin (beta0 = 0).
- **Use Categorical Variables** - Use the `C()` operator in formulas (e.g., `y ~ C(region)`) to automatically create dummy variables.
- **Specify Covariance Type** - Use `cov_type='HC3'` or `'cluster'` if you suspect non-constant variance (heteroscedasticity).
- **Interpret R-squared carefully** - High R-squared doesn't imply a good model if the residuals are patterned.
- **Check for Multicollinearity** - Use VIF (Variance Inflation Factor) to ensure predictors aren't highly correlated.

### ❌ DON'T

- **Assume Prediction is Inference** - Just because a model has a high R-squared doesn't mean the coefficients represent real-world causal effects.
- **Ignore the Intercept** - Most physical and social processes require a constant term.
- **Overfit with too many predictors** - Use AIC/BIC metrics to penalize complex models.
- **Extrapolate beyond the range** - Statistical models are only valid within the domain of the training data.

## Anti-Patterns (NEVER)

```python
import statsmodels.api as sm

# ❌ BAD: Forgetting the intercept in Array API
model = sm.OLS(y, X) # This forces the line through (0,0)
results = model.fit()

# ✅ GOOD: Add the constant
X = sm.add_constant(X)
model = sm.OLS(y, X).fit()

# ❌ BAD: Ignoring categorical data strings
# smf.ols('price ~ color', data=df) # Might fail if 'color' isn't numeric

# ✅ GOOD: Explicitly tell Statsmodels it's categorical
smf.ols('price ~ C(color)', data=df).fit()

# ❌ BAD: Only looking at R-squared
# print(results.rsquared) # Tells only part of the story

# ✅ GOOD: Inspecting the whole summary
print(results.summary()) # Check p-values, F-stat, Jarque-Bera
```

## Regression Analysis

### Linear Models (OLS, WLS)

```python
# Multiple Linear Regression with interactions
# 'x1 * x2' includes x1, x2, and the interaction term x1:x2
model = smf.ols('y ~ x1 * x2 + np.log(x3)', data=df).fit()

# Weighted Least Squares (for heteroscedastic data)
wls_model = sm.WLS(y, X, weights=1.0/variance_estimates).fit()
```

### Generalized Linear Models (GLM)

```python
# Logistic Regression (Binary outcome)
logit_model = smf.logit('admit ~ gre + gpa + C(rank)', data=df).fit()

# Poisson Regression (Count data)
poisson_model = smf.poisson('num_awards ~ math + C(prog)', data=df).fit()

# Negative Binomial (For over-dispersed counts)
nb_model = smf.glm('y ~ x1', data=df, family=sm.families.NegativeBinomial()).fit()
```

## Time Series Analysis (tsa)

### Stationarity and Modeling

```python
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.statespace.sarimax import SARIMAX

# 1. Test for Stationarity (Augmented Dickey-Fuller)
adf_result = adfuller(df['sales'])
print(f"ADF P-value: {adf_result[1]}") # p < 0.05 means stationary

# 2. SARIMAX (Seasonal ARIMA with eXogenous variables)
model = SARIMAX(df['sales'], 
                order=(1, 1, 1), 
                seasonal_order=(1, 1, 0, 12),
                exog=df['advertising'])
results = model.fit()

# 3. Forecasting
forecast = results.get_forecast(steps=12)
conf_int = forecast.conf_int()
```

## ANOVA and Hypothesis Testing

```python
from statsmodels.stats.anova import anova_lm

# Perform ANOVA on OLS model
model = smf.ols('yield ~ C(fertilizer) + C(soil)', data=df).fit()
anova_table = anova_lm(model, typ=2)

# Post-hoc tests (Tukey's HSD)
from statsmodels.stats.multicomp import pairwise_tukeyhsd
tukey = pairwise_tukeyhsd(endog=df['yield'], groups=df['fertilizer'], alpha=0.05)
print(tukey)
```

## Model Diagnostics

### Residual Analysis

```python
import statsmodels.stats.api as sms

# 1. Test for Heteroscedasticity (Breusch-Pagan)
name = ['Lagrange multiplier statistic', 'p-value', 'f-value', 'f p-value']
test = sms.het_breuschpagan(results.resid, results.model.exog)
print(dict(zip(name, test)))

# 2. Test for Normality (Omnibus)
# Included in results.summary() by default. 

# 3. Check for Outliers (Influence)
influence = results.get_influence()
cooks_d = influence.cook_distance[0]
```

## Practical Workflows

### 1. Robust Scientific Reporting Pipeline

```python
def analyze_experiment(df):
    """Rigorous analysis of an experimental dataset."""
    # 1. Fit model
    model = smf.ols('outcome ~ treatment + age + gender', data=df).fit()
    
    # 2. Diagnostic Plots (requires matplotlib)
    import matplotlib.pyplot as plt
    sm.graphics.plot_regress_exog(model, 'treatment')
    
    # 3. Check for Multicollinearity
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    # (calculation for VIF...)
    
    return model.summary()
```

### 2. Mixed Models: Controlling for Lineage or Population Structure

**This is the most important section of this skill for the group's work.** Isolates
from the same clade, or individuals from the same population, are not independent
observations. Fitting a plain GLM to them inflates every test statistic, and the
inflation grows with sample size, so a bigger dataset makes the problem worse. The
same issue is Galton's problem in the cross-cultural data behind the `wals` and
`d-place` skills.

```python
from statsmodels.regression.mixed_linear_model import MixedLM

# Continuous outcome, random intercept per lineage.
# groups= is the clustering variable; it is NOT a fixed effect.
md = MixedLM.from_formula('branch_length ~ gc_content + C(host)',
                          groups='lineage', data=df)
res = md.fit()
print(res.summary())
print("variance between lineages:", res.cov_re.iloc[0, 0])
```

Read `cov_re` first. If the between-group variance is close to zero the grouping
carries no signal and a plain OLS was fine; if it is large relative to `res.scale`
(the residual variance), the naive model was badly wrong and the mixed fit is the
one to report. The ratio is the intraclass correlation:
`icc = cov_re / (cov_re + scale)`.

Random slopes, when the effect of a predictor itself varies by lineage:

```python
md = MixedLM.from_formula('phenotype ~ allele', groups='lineage',
                          re_formula='~allele', data=df)
res = md.fit()
```

For a **binary** outcome (resistant / susceptible, presence / absence) `MixedLM`
does not apply. Use a GEE with an exchangeable working correlation, which gives
population-averaged coefficients with cluster-robust standard errors:

```python
import statsmodels.api as sm
import statsmodels.formula.api as smf

gee = smf.gee('resistant ~ mutation + C(lineage_group)', groups='cluster_id',
              data=df, family=sm.families.Binomial(),
              cov_struct=sm.cov_struct.Exchangeable())
res = gee.fit()
print(res.summary())
print(res.cov_struct.summary())   # estimated within-cluster correlation
```

The cheapest fallback, when the model must stay a plain GLM, is cluster-robust
standard errors. It does not change the coefficients, only their uncertainty,
which is usually where the damage is:

```python
res = smf.ols('y ~ x', data=df).fit(cov_type='cluster',
                                    cov_kwds={'groups': df['lineage']})
```

Convergence notes: `MixedLM` is fragile with few groups (below roughly 5 to 10 the
variance component is poorly identified, and a fixed effect for group is the more
honest choice) and with unscaled predictors. If the fit warns about a singular
random-effect covariance, drop the random slope and keep the random intercept.

### 3. Multiple Testing Across Sites or Genes

```python
from statsmodels.stats.multitest import multipletests

reject, qvals, _, _ = multipletests(pvals, alpha=0.05, method='fdr_bh')
```

Benjamini-Hochberg (`fdr_bh`) is the default for genome-scale scans: Bonferroni
over millions of linked positions is both far too conservative and wrong in its
independence assumption. Use `fdr_by` when tests may be negatively dependent, and
`holm` only for a handful of pre-registered hypotheses. Always report the number
of tests actually performed.

### 4. Worked Example: Resistance Allele Association

```python
# One row per isolate. 'cluster' groups isolates within a transmission cluster.
gee = smf.gee('resistant ~ C(allele) + year',
              groups='cluster', data=iso,
              family=sm.families.Binomial(),
              cov_struct=sm.cov_struct.Exchangeable()).fit()

# Odds ratios with confidence intervals, ready for a manuscript table
import numpy as np
or_table = np.exp(pd.concat([gee.params, gee.conf_int()], axis=1))
or_table.columns = ['OR', 'CI_low', 'CI_high']
```

### 5. Worked Example: Counting SNPs per Branch

SNP counts are counts, so Poisson, not OLS on a log. Check for overdispersion
before trusting it, and switch to negative binomial if the Pearson chi-squared
over the residual degrees of freedom is much above 1.

```python
pois = smf.glm('n_snp ~ np.log(branch_time) + C(lineage)', data=df,
               family=sm.families.Poisson()).fit()
dispersion = pois.pearson_chi2 / pois.df_resid
if dispersion > 1.5:
    nb = smf.glm('n_snp ~ np.log(branch_time) + C(lineage)', data=df,
                 family=sm.families.NegativeBinomial()).fit()
```

Use an offset rather than a predictor when the exposure is known exactly, for
instance callable genome length: `offset=np.log(df['callable_bp'])`.

### 7. Survival Analysis

```python
from statsmodels.duration.hazard_regression import PHReg

# Cox Proportional Hazards Model
model = PHReg.from_formula('time ~ age + C(treatment)', data=df, status=df['event'])
results = model.fit()
print(results.summary())
```

## Performance Optimization

### Using numba for Likelihoods

While Statsmodels is primarily written in Python and Cython, some of the newer time series modules utilize optimized numerical backends for faster fitting of state-space models.

### Formulas vs Design Matrices

For very large datasets (1M+ rows), creating the design matrix with patsy can be memory-intensive. In these cases, construct your X matrix manually and use `sm.OLS(y, X)`.

## Common Pitfalls and Solutions

### Singular Matrix Error

"LinAlgError: Singular matrix" means your predictors are perfectly correlated (e.g., including both temp_celsius and temp_fahrenheit).

```python
# ✅ Solution: Remove redundant columns
df = df.drop('redundant_col', axis=1)
```

### Categorical Leakage (The Dummy Variable Trap)

Including intercept and dummy variables for ALL categories creates perfect multicollinearity.

```python
# ❌ Problem: y ~ dummy_cat1 + dummy_cat2 + dummy_cat3 + intercept 
# ✅ Solution: Statsmodels/Patsy automatically drops one category (ref category)
# to avoid this. Don't try to force all dummies in!
```

### Non-Stationary Time Series

Predicting a non-stationary series leads to "spurious regression".

```python
# ✅ Solution: Difference your data first
df['diff_y'] = df['y'].diff()
# Or use ARIMA with integrated term (d=1)
```

Statsmodels is the gold standard for statistical validity in the Python ecosystem. It moves beyond black-box predictions to provide the transparency and mathematical rigor required for high-stakes scientific and economic decision-making.
