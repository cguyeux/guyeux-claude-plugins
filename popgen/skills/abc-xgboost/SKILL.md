---
name: abc-xgboost
description: >-
  Approximate Bayesian Computation (ABC) accelerated by an XGBoost regressor/classifier
  with SHAP interpretation, to infer the selection coefficient and the
  demography x selection scenario behind an ancient allele-frequency trajectory. Built
  for the TYK2 P1104A question (Kerner et al. 2021, axe 2 of TYK2-MTBC-coevolution): is
  an observed decline reproducible, how strong was selection, and which summary
  statistics carry the signal. Simulates trajectories with a diploid Wright-Fisher model
  (dominance h: recessive for TYK2), trains XGBoost on the simulations, and compares
  XGBoost point estimates with acceptance-rejection ABC posteriors.

  Use when: estimating the selection coefficient s on a human (or pathogen) allele from
  ancient DNA frequencies through time, comparing neutral vs weak vs strong selection
  scenarios, replicating or extending Kerner 2021 on TYK2 P1104A, or building a
  simulation-based-inference baseline before a full coalescent (msprime/SLiM) study.
---

# ABC-XGBoost : selection inference for allele-frequency trajectories

## Overview

Given an allele frequency observed at several ancient time points (e.g. from the
`aadr` cohort), this skill answers: **what selection coefficient, and which scenario,
best explains the trajectory?** It draws many `(s, f0, Ne)` from a prior, simulates
each with a forward Wright-Fisher model, summarises each trajectory, then learns the
mapping summary -> s with **XGBoost** (regressor for continuous s, classifier for the
neutral/weak/strong regime) and explains it with **SHAP**. Acceptance-rejection ABC on
the same simulations gives a posterior on s for cross-checking.

The selection model is diploid with a dominance coefficient `h` (`w_AA=1-s`,
`w_Aa=1-h*s`, `w_aa=1`; A = derived allele): `h=0` recessive (the TYK2 P1104A model,
only homozygotes affected), `h=0.5` additive, `h=1` dominant.

## Requirements

Needs `xgboost + shap + scikit-learn` (plus numpy/scipy), which are not on the system
Python (3.14). Use the dedicated venv:

```bash
PY=/home/christophe/venvs/abc311/bin/python    # Python 3.11; pip install xgboost shap scikit-learn
SRC=<this skill>/src
```

## Usage

```bash
# 1. TYK2 P1104A-like demo (~10% -> ~3% decline), recessive (h=0)
PYTHONPATH="$SRC" $PY -m abc_xgboost demo --n 8000

# 2. your own ancient trajectory (CSV of freqs oldest -> newest, or bin,freq per line)
PYTHONPATH="$SRC" $PY -m abc_xgboost infer --observed freqs.csv --n 8000 --h 0

# 3. self-check + one-trajectory sanity
PYTHONPATH="$SRC" $PY -m abc_xgboost.smoke_test
PYTHONPATH="$SRC" $PY -m abc_xgboost simulate --s 0.21 --f0 0.10 --h 0
```

`infer` returns JSON: `s_point_estimate` (XGBoost regressor), `regime_classified`,
`abc_posterior` (`s_median`, 95% interval), `shap_top` (the summary statistics that
drive the estimate), and `n_simulations`. Python API: `from abc_xgboost import infer,
simulate_dataset, fit_regressor, abc_reject, shap_top`.

## Reading the output

- `s_point_estimate` and the ABC `s_median` should agree; a wide `abc_posterior`
  interval means s is weakly identified by these data.
- `shap_top` names the informative summaries (typically the early/mid frequencies and
  the steepest inter-bin drop), report them so the inference is not a black box.

## Important caveats

- **Recessive identifiability (the TYK2 case).** With `h=0` at low allele frequency,
  selection acts as ~`s*f^2`, so very different `s` produce nearly the same trajectory:
  expect a WIDE posterior on `s`. The skill's self-check therefore validates the
  machinery in the ADDITIVE regime (`h=0.5`, where the regressor recovers s with
  corr ~0.9). For TYK2, report the interval honestly rather than a single `s`.
- **Drift dominates at small Ne / low f.** Confounding between drift and weak selection
  is real; widen the prior on `Ne` and report the scenario comparison, not just a point.
- **Wright-Fisher, not coalescent.** This is allele-frequency-trajectory inference, a
  fast baseline. For genealogy-based summary statistics or linked selection, move to a
  coalescent/forward simulator (msprime / SLiM), this skill is the quick first pass.

## Integration with other skills

| Tool | Role |
|---|---|
| `aadr` | the observed ancient allele-frequency trajectory (filter cohort, bin by date) |
| `neolithic-14c` / `p3k14c` | calendar/radiocarbon framing of the time bins |
| `coevolution` | couples the inferred selection date to MTBC lineage TMRCA (axe 4) |
| `modern-human-reference-panels` | present-day allele frequency as the final time point |
| `bayesian-skyline` | demographic Ne(t) prior informing the simulations |
