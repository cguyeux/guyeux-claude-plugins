---
name: maboss-advanced
description: >-
  Go beyond a single MaBoSS run: population-level dynamics with UPMaBoSS (UpdatePopulation)
  and PopMaBoSS, model Ensembles, mutant/parameter scans, sensitivity to rates and initial
  states, and the CCT/MCCT assertion evaluator (maboss.temporal_logic.MaBoSSEvaluator).
  Use when a plain baseline-vs-perturbed simulation is not enough: cell-population fate
  proportions over time, systematic single/double mutant screens, or checking directional
  literature claims (Inc/Dec) programmatically. Triggers: "UPMaBoSS", "PopMaBoSS",
  "population dynamics", "mutant scan", "sensitivity analysis", "cell fate proportions",
  "double mutants", "CCT / MCCT verdict", "MaBoSSEvaluator".
---

# maboss-advanced : populations, scans, sensitivity, CCT

## UPMaBoSS : dynamics of a cell population (division/death feedback)

```python
import maboss
from maboss import UpdatePopulation
sim = maboss.load("model.bnd", "model.cfg")
up  = UpdatePopulation(sim, division_node="Proliferation", death_node="Apoptosis")
res = up.run()
res.plot_population()          # population size / node proportions over update rounds
```

## PopMaBoSS : explicit population simulation

`maboss.PopSimulation` (PopMaBoSS engine) for population-level stochastic simulation; see
the `pymaboss` skill for the API surface.

## Mutant / parameter scans

```python
import itertools
nodes = ["BRAF", "EGFR", "TGFB_L"]
for muts in itertools.product([None,"ON","OFF"], repeat=len(nodes)):
    s = sim.copy()
    for n, st in zip(nodes, muts):
        if st: s.mutate(n, st)
    last = s.run().get_last_nodes_probtraj().iloc[-1]
    ...   # collect verdict per mutant combination -> a screen
```
(The maboss-mcp `maboss_run_simulation` tool wraps single runs with mutations + istate.)

## Sensitivity

- to rates: `sim.param["$u_X"] = ...` then re-run; sweep and watch P(target).
- to initial state: `sim.network.set_istate(node, {0:p0, 1:p1})` (random 0.5/0.5 to explore).

## CCT / MCCT verdict (Oscar Dufossez's evaluator)

```python
import maboss.temporal_logic as tl
res = tl.MaBoSSEvaluator.querying(["Inc(node:EGFR) / [] [ BRAF:OFF ] [ 5% digits:3 ]"],
                                  sim_cfg="model.cfg", sim_bnd="model.bnd")   # cfg BEFORE bnd
# res[0]: DataFrame with '<T> from master/mutation', 'Difference <T>', 'Increase/Decrease <T>'
```
Exposed as the maboss-mcp `maboss_query_cct` tool. See KB `maboss.md` for grammar + gotchas.
