---
name: bn-control
description: >-
  Find interventions (mutations / node fixings) that REPROGRAM a Boolean network toward a
  desired attractor/phenotype or away from an undesired one, or PROVE none exists. The
  workhorses AEON.py (formal control) and mpbn (reachability) are already in the maboss-mcp
  image; Pint / CABEAN / pyStableMotifs are alternatives that need the CoLoMoTo image. Use for
  "which perturbations induce/block EMT", "drive the model to the apoptotic state", "minimal
  interventions to reach a phenotype", "is state X reachable at all". Triggers: "control the
  network", "reprogramming", "which mutations reach state X", "block/induce EMT",
  "target control", "reachability", "permanent vs temporary control", "AEON control".
---

# bn-control — reprogramming a Boolean model toward a target state

Prerequisite: know your target attractor/phenotype (use the `boolean-attractors` skill).

**What is already installed** (image `maboss-mcp:v2`, verified 2026-07-10): `biodivine_aeon`
(AEON.py) 1.4.2 and `mpbn` 4.4 — between them they cover reachability AND formal control with
zero extra install. Pint, CABEAN, pyStableMotifs and ActoNet are NOT in the image; reach for
them (via `colomoto-run`) only when you need something AEON+mpbn cannot give.

## mpbn — reachability & minimal-intervention screen (installed, fastest)

Most Permissive semantics **over-approximates** asynchronous/MaBoSS reachability. So
*unreachable in mpbn* ⇒ *unreachable everywhere* (a PROOF), while *reachable in mpbn* must be
replayed in MaBoSS before any positive claim.

```python
import maboss, mpbn
m = mpbn.MPBooleanNetwork(maboss.to_minibn(maboss.load("m.bnd","m.cfg")))
m.reachability(x, y)                      # is config y reachable from config x? (True/False)
list(m.attractors(reachable_from=start))  # which attractors are reachable from a start state
m["GF"] = 0                               # fix a node OFF (a knock-out); m[node]=1 for ON
```
Screen of single/double interventions: mutate (`m[node]=v`), then check whether the target
phenotype's read-out becomes reachable. Vécu MET model: this exact screen proved the M→E
reversion is topologically impossible for GF=1 fixed points (P(E)=0, not just <0.1).

## AEON.py — formal control, incl. PERMANENT vs TEMPORARY (installed)

```python
import biodivine_aeon as ba
bn = ba.BooleanNetwork.from_bnet(bnet_text).infer_valid_graph()   # infer_valid_graph is REQUIRED
g  = ba.AsynchronousGraph(bn)
# color-perturbation pairs guaranteeing the target attractor is reached:
ba.Control.attractor_permanent(g, source, target)   # intervention held forever
ba.Control.attractor_temporary(g, source, target)   # transient intervention suffices
ba.Control.attractor_one_step(g, source, target)    # single-step
ba.Control.phenotype_permanent(g, phenotype_space)  # target a PHENOTYPE, not one attractor
```
`temporary` vs `permanent` separates true network hysteresis (irreversibility WITHOUT
epigenetic memory) from interventions that must be maintained — a clean therapeutic reading.

## GOTCHAS (verified on the 61-node MET model, save yourself the debugging)

- `BooleanNetwork.from_bnet(...)` raises `RuntimeError: No update functions satisfy given
  constraints` on a raw `.bnet` (self-regulated inputs violate inferred essentiality). Fix:
  `bn = bn.infer_valid_graph()` before building the graph.
- Never put the phenotype **read-out** nodes in the perturbation space — the controller would
  return the absurd "force E=1". Perturb the biological nodes; use the read-outs only as the
  target phenotype (`phenotype_permanent`).
- Self-regulated inputs (`logic=(SELF)`) multiply attractors — percolate them first
  (`ba.Percolation.percolate_subspace`, or mpbn `constraints=`).

## Options that need the CoLoMoTo image (only if AEON+mpbn fall short)

- **pyStableMotifs** — target control via stable motifs: `sm.drivers.knock_to_partial_state({...}, primes, max_drivers=3)`.
- **Pint** — `model.reachability(goal=...)`, `model.oneshot_mutations_for_cut(goal=...)` (cut sets).
- **CABEAN** — source/target attractor control incl. SEQUENTIAL control (drive A→B→C in stages).
- **ActoNet** — abduction-based perturbations enforcing a chosen fixed point.

**Always validate a control set back in MaBoSS**: apply it as mutations (`maboss_run_simulation`)
and check the resulting probabilities/attractor (`maboss_attractors`). A set that works in mpbn
Most-Permissive can still leave the target rare in the stochastic dynamics (vécu: GF:OFF+OVOL1:ON
made E reachable but only P(E)=0.04, the population piling up in the hybrid state).
