---
name: astrologics
description: >-
  Analyse ENSEMBLES of Boolean models with AstroLogics (sysbio-curie, the same group as
  pyMaBoSS/WebMaBoSS): compare many candidate monotonous Boolean models, study the
  variability of their dynamics/attractors, and reason about a family of models rather than
  a single one. Use when model inference (BoNesis/Caspo) yields MANY models consistent with
  the data and you need to characterise the ensemble, quantify uncertainty across models,
  or pick robust predictions. Also a natural collaboration point with the Noel/Dufossez
  group. Triggers: "ensemble of models", "many candidate models", "model variability",
  "AstroLogics", "robust prediction across models", "which predictions hold for all models".
---

# astrologics — reasoning over a family of Boolean models

When inference (see `model-inference`) returns an ENSEMBLE (dozens/hundreds of Boolean
networks all consistent with the data), a single simulation is not enough — you want the
predictions that are ROBUST across the ensemble. AstroLogics (Python `astrologics`,
sysbio-curie) is built for monotonous Boolean model ensembles.

## Typical flow

```python
import astrologics
# 1) an ensemble: e.g. BoNesis-enumerated models, or perturbations of a base model
ens = astrologics.Ensemble(models)             # list of Boolean networks
# 2) analyse dynamics/attractors across the ensemble
ens.attractors()                                # attractor landscape per model
ens.summary()                                   # which phenotypes are shared vs model-specific
# 3) robust predictions: properties (e.g. "TGFB_L=1 -> mesenchymal attractor reachable")
#    that hold for ALL / a majority of the ensemble
```
(See https://astrologics.readthedocs.io for the current API.)

## Why it matters for us

- Turns "here is one model's answer" into "here is what is robust across all plausible
  models" — the honest way to report a Boolean-model prediction under structural uncertainty.
- Same group as pyMaBoSS/WebMaBoSS (Vincent Noel) and the CCT (Oscar Dufossez): a concrete
  collaboration surface, and a way to combine an ENSEMBLE with MaBoSS stochastic simulation
  and CCT assertion checking (mabossDemo coherency bench applied per-model).

**Tie-in.** For each ensemble member, export to MaBoSS and run the coherency bench / CCT
assertions (the `maboss-advanced` skill / mabossDemo) — an assertion "supported by 95% of
the ensemble" is far stronger than "supported by one model".
