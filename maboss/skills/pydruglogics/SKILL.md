---
name: pydruglogics
description: >-
  Build and optimize Boolean models and run in-silico drug perturbations and synergy
  predictions with PyDrugLogics (DrugLogics stack), and network-oriented drug repurposing
  with NORDic. Use for cancer-oriented questions: predict single/combination drug effects
  on a signalling model, screen synergies, or repurpose drugs against a target phenotype.
  Aligned with the Curie/cancer-signalling context. Triggers: "drug synergy", "drug
  perturbation in silico", "combination therapy prediction", "pydruglogics", "druglogics",
  "drug repurposing", "NORDic", "which drug combination".
---

# pydruglogics — in-silico drug perturbations & synergy

Cancer-oriented layer on top of Boolean models. Needs the CoLoMoTo image or a proper
conda/pip env (see `colomoto-run`).

## PyDrugLogics — perturbations & synergy

```python
import pydruglogics
# 1) a Boolean model (from .bnet / MaBoSS logic), 2) a training/observation set,
# 3) drug->target mapping. Optimize the model, then score perturbations.
model = pydruglogics.BooleanModel(file="model.bnet")
# calibrate against observed steady-state readouts, then:
predictions = pydruglogics.Predictions(model, perturbations=drug_panel)
predictions.run()            # synergy scores (e.g. HSA/Bliss) per drug combination
```
Workflow: a drug = fixing its target node(s) OFF (inhibitor) or ON; a combination = several
fixings; synergy = combined effect vs single-agent expectation on a phenotype output.

## NORDic — network-oriented repurposing of drugs

```python
import NORDic
# build/curate a network for a disease, score/rank drugs by their network effect
```
Use to rank candidate drugs by how they push the network away from a disease attractor.

**Tie-in.** A predicted drug combination is a set of node fixings -> validate it in MaBoSS
(apply as mutations, check the attractor with the `boolean-attractors` skill / maboss-mcp).
Relates to the `bn-control` skill (control set = drug target set).
