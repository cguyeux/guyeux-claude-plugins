---
name: pymaboss
description: >-
  Drive the real pyMaBoSS Python API (colomoto/pyMaBoSS, bindings over the MaBoSS
  C++ engine). Covers loading (maboss.load / loadBNet / loadSBML / loadTabularQual),
  the Simulation object (.run, .mutate(node, ON|OFF|WT), .copy, .update_parameters,
  .get_logical_rules), copy_and_mutate / set_output / set_nodes_istate,
  extracting results (get_nodes_probtraj, get_states_probtraj,
  get_last_nodes_probtraj), interop (to_biolqm, to_minibn), the MaBoSS server client
  (MaBoSSClient), UPMaBoSS (UpdatePopulation), Ensemble and PopMaBoSS, Jupyter
  widgets, AND crucially the temporal-logic / CCT assertion evaluator
  `maboss.temporal_logic.MaBoSSEvaluator.querying(query, cfg, bnd, [istate],
  [output])` written by Oscar Dufossez — the real implementation of the P/T/Pmax/
  Pmin/Tmax/Tmin/Inc/Dec query grammar (node:A, state:A--B, `/ [constraints]
  [mutations]`). Install: `conda install -c colomoto pymaboss` then
  `python -m maboss_setup` for the binaries.

  Use when: running a MaBoSS model from Python, applying a knock-out/over-expression,
  reading P(node) at the last time point, checking a directional literature claim
  ("does inhibiting X decrease Y?") via MaBoSSEvaluator instead of reimplementing an
  evaluator, or wiring a real pyMaBoSS runner (e.g. mabossDemo's PyMaBoSSRunner stub).
  Pairs with `maboss-model` (write the files) and `maboss-ecosystem` (who/what).
argument-hint: "[task]   # e.g. 'run BRAF knockout on cancer_signaling and read P(EGFR)'"
allowed-tools: Read, Write, Edit, Bash
user-invocable: true
---

# /pymaboss — the real pyMaBoSS API (and Oscar's CCT evaluator)

pyMaBoSS = Python interface over the MaBoSS C++ engine. API surface below is from the
`colomoto/pyMaBoSS` source tree (master, July 2026), not a reconstruction.

## Install

```
conda install -c colomoto pymaboss        # recommended (ships the binaries)
python -m maboss_setup                     # or fetch binaries into ~/.local/share/maboss/bin
# pip install maboss                        # bindings only, you must provide the MaBoSS binary
```
The `maboss` package looks for the `MaBoSS` binary on PATH / `~/.local/share/maboss/bin`.

## Load, run, mutate, read

```python
import maboss

sim   = maboss.load("model.bnd", "model.cfg")   # also: loadBNet, loadSBML (SBML-qual), loadTabularQual
res   = sim.run()                                # baseline simulation

# probabilities (pandas DataFrames indexed by time)
p_traj   = res.get_nodes_probtraj()              # P(node active) over time
p_last   = res.get_last_nodes_probtraj()         # last time point only
s_traj   = res.get_states_probtraj()             # P(state) over time
p_egfr   = res.get_last_nodes_probtraj()["EGFR"].iloc[-1]

# mutations: states are ON / OFF / WT  (convention: KO -> OFF, over-expr/MUT -> ON)
mut  = maboss.copy_and_mutate(sim, ["BRAF"], "OFF")   # returns a NEW mutated Simulation
mut.mutate("EGFR", "ON")                              # further mutations in place
res2 = mut.run()

# other helpers
maboss.set_output(sim, ["EGFR", "Proliferation"])     # restrict observed nodes
sim.update_parameters(sample_count=5000, thread_count=4)
list(sim.network)                                     # node names
```

- `Simulation.run(cmaboss=False, only_final_state=False, ...)`; `cmaboss=True` uses the in-process
  cMaBoSS C-API (no temp files, faster for loops).
- Interop: `maboss.to_biolqm(model)`, `maboss.to_minibn(model)` bridge to bioLQM / colomoto minibn.
- Server mode: `MaBoSSClient` talks to a running MaBoSS server (this is what WebMaBoSS uses).
- Populations: `UpdatePopulation` (UPMaBoSS), `PopSimulation` (PopMaBoSS), `Ensemble`.
- In Jupyter, importing `maboss` registers widgets + a "MaBoSS" menu (via `colomoto_jupyter`).

## CCT / temporal-logic evaluator — DO NOT reimplement it

`maboss.temporal_logic.MaBoSSEvaluator` (author: **Oscar Dufossez**, in pyMaBoSS master) IS the
assertion/query engine. mabossDemo's "MCCT" grammar == this CCT. Call it, don't rebuild it.

```python
from maboss.temporal_logic import MaBoSSEvaluator
MaBoSSEvaluator.help()   # prints the full grammar
res = MaBoSSEvaluator.querying(query, cfg_file, bnd_file, [initial_state], [output_setting])
```

Grammar (from `MaBoSSEvaluator.help()`):
- Query types: `P` (probability), `T` (time periods), `Pmax`/`Pmin`, `Tmin`/`Tmax`,
  **`Inc`/`Dec`** (compare TWO simulations → **a mutation is REQUIRED**; look at the last period).
- Targets: `node:A` (or `node:A,B` = joint), `state:A--B` (a state = a vector of nodes joined by `--`),
  logical-not `node:!A`. The special empty state is `state:<nil>`.
- Form: `QUERY(target) OP value [ logical_constraint ] [ mutations ]`; mutations are `node:ON/OFF`
  comma-separated; `compare:mut:state` compares against another mutated simulation.
- Examples: `Inc(node:A) / [ ] [ B:ON ]`, `Dec(node:A) / [ A & C ] [ B:ON ]`,
  `P(node:A,B) = ? [ node:!C & (D > 0.5) ]`, `T(state:A--B) >= 0.0 [ !C ]`,
  `Pmax(node:A) >= 0.5`, `Tmin(node:A,B) >= 0.3`.
- There is also a `Visualiser` (`evolution_over_time`, `display_results_and_queries`).

## Wiring a real runner (e.g. mabossDemo PyMaBoSSRunner)

Write the current `.bnd`/`.cfg` to temp files, build the CCT query from the decomposition
(`Inc`/`Dec`, `node:TARGET`, `[ mutations ]`), call `MaBoSSEvaluator.querying(...)`, and map the
returned comparison onto the app's `{baseline, perturbed, delta, verdict, caveats}` shape. This is
exactly what the stub in `maboss_runner.py` anticipated (`tl.MaBoSSEvaluator.querying`). Keep the
mock as offline fallback. Requires the real pyMaBoSS + engine in the image (conda colomoto), which
is NOT pip-only — see `maboss-ecosystem` for deployment implications.
