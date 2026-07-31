---
name: model-inference
description: >-
  Build or refine a Boolean model FROM DATA and constraints: BoNesis (synthesis of Boolean
  networks from an influence graph + dynamical properties, via Answer Set Programming),
  Caspo (learn logic models from phosphoproteomic signalling data), scBoolSeq (binarise
  single-cell RNA-seq and generate synthetic data from Boolean dynamics), and R-BoolNet
  reconstruction. Use when you have observations (steady states, time series, perturbation
  responses, scRNA-seq) and want a model consistent with them, or to enumerate all models
  fitting the data. Triggers: "infer a Boolean model", "learn model from data", "synthesize
  network", "BoNesis", "Caspo", "scBoolSeq", "binarize scRNA-seq", "fit model to observations".
---

# model-inference : data -> Boolean model

Needs the CoLoMoTo image or a clingo-enabled env (see `colomoto-run`; BoNesis/Caspo use ASP).

## BoNesis : synthesis from architecture + dynamics

```python
import bonesis
dom = bonesis.InfluenceGraph.from_sif("interactions.sif")   # allowed influences
bo  = bonesis.BoNesis(dom, data={ "epithelial": {...}, "mesenchymal": {...} })  # observed configs
bo.fixed_points(bonesis.configurations(...))                # impose these as fixed points
models = list(bo.boolean_networks(limit=10))                # enumerate consistent BNs
```
Enumerate ALL Boolean networks whose attractors/reachability match your constraints -> then
export each to MaBoSS and simulate.

## Caspo : learn logic models from signalling data

```python
# CASPO: given a PKN (prior knowledge network) + phospho time/dose data, learn the family
# of logic models explaining the data (Answer Set Programming).
```
Good when you have perturbation-readout signalling data and a prior network.

## scBoolSeq : single-cell binarisation

```python
import scboolseq
bin_data = scboolseq.scBoolSeq().binarize(expression_df)     # scRNA-seq -> Boolean states
```
Turns scRNA-seq into Boolean observations you can feed to BoNesis/Caspo, or use to label
attractors (which single-cell cluster = which attractor).

**Tie-in.** Inferred models -> MaBoSS (`.bnd`/`.cfg`) -> simulate + attractors + CCT checks
(the other maboss skills / mabossDemo coherency bench).
