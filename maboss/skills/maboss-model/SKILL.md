---
name: maboss-model
description: >-
  Author, read and validate MaBoSS Boolean-model files: the .bnd (node logic and transition
  rates) and .cfg (initial states, external variables, run parameters) pair. Encodes the
  official MaBoSS Reference Card grammar for engine 2.6.6: node syntax, the @ node-variable
  and $ external-variable prefixes, the operator set, rate_up / rate_down / logic semantics
  (rates derived from logic when omitted), .cfg keys (istate weights, is_internal, refstate,
  time_tick, max_time, sample_count, thread_count, seeding, statdist), the CLI, and the
  output files (_probtraj.csv, _fp.csv, _statdist.csv). Use when writing or fixing a .bnd or
  .cfg, explaining a node's logic or rate idiom, choosing istate priors, deciding which
  nodes are internal, distinguishing a driver node from a derived one, or debugging why a
  model does not simulate. Pairs with pymaboss (to run it) and maboss-ecosystem (where
  models come from). Limit of 64 nodes unless the engine was recompiled.
argument-hint: "[path-to.bnd|.cfg]   # e.g. review backend/app/data/sample_model/cancer_signaling.bnd"
allowed-tools: Read, Write, Edit, Bash
user-invocable: true
---

# /maboss-model : write & validate MaBoSS .bnd/.cfg models

Ground truth: the official **MaBoSS Reference Card**
(`github.com/sysbio-curie/MaBoSS/blob/master/engine/doc/MaBoSS-RefCard.pdf`), engine 2.6.6.
A model is always a **couple**: `.bnd` (logic) + `.cfg` (parameters).

## .bnd : network description

```
node NODE_NAME {
  logic = (A & !B) | (C ^ D);        // ! NOT, & / && AND, | / || OR, ^ XOR, ? : ternary
  rate_up   = @logic ? $u_NODE : 0;  // @ = a node variable's value; $ = an external variable
  rate_down = @logic ? 0 : $d_NODE;
}
```

- Node/variable names: `[a-zA-Z_][a-zA-Z0-9_]*`. Comments: `//` or `/* */` (C/Java style).
- **Three variables have algorithmic meaning**: `rate_up` (transition rate 0→1), `rate_down` (1→0),
  and `logic`. **If you omit the rates, MaBoSS derives them from `logic`**:
  `rate_up = @logic ? 1.0 : 0.0; rate_down = @logic ? 0.0 : 1.0`. So `node X { logic = (A & B); }`
  alone is a valid, complete node. The `@logic ? $u_X : 0` idiom is ONLY to make rates tunable via
  `$u_X`/`$d_X` in the .cfg, do not present it as mandatory.
- **Driver node** (holds its random initial state, no upstream regulation): `logic = (NODE);`
  (self-reference). Useful for an input you want at 50/50 in baseline then force in a perturbation.
- `@` prefixes a node-variable value inside an expression (`@logic`, `@rate_up`); `$` prefixes an
  external variable that MUST be defined in the .cfg (`$u_X`).

## .cfg : parameters (with defaults)

```
$u_X = 1.0; $d_X = 1.0;                 // external variables used by the .bnd (error if used & undefined)
X.istate = 0.5 [0], 0.5 [1];            // weighted initial prior: proba [state]; negative int / absent = random
X.is_internal = FALSE;                  // FALSE => node observed in output (default FALSE)
X.refstate = 0;                         // reference state for Hamming distance (optional)
time_tick = 0.5;  max_time = 1000;      // output granularity; trajectory length
sample_count = 10000;                   // number of stochastic trajectories
discrete_time = FALSE;                  // FALSE = continuous time (Gillespie); TRUE = jump process
use_physrandgen = TRUE;                 // FALSE + seed_pseudorandom = N  for reproducibility
thread_count = 1;
```

- `NODE.istate = 0.5 [0], 0.5 [1];` is `proba [state_value]`, order is by state, not by probability.
- To make results reproducible: `use_physrandgen = FALSE; seed_pseudorandom = <int>;`.
- Internal nodes (`is_internal = TRUE`) are hidden from the state-probability output, use for
  intermediates you do not want cluttering results.

## CLI & outputs

```
MaBoSS -c model.cfg -o out_prefix model.bnd     # run
MaBoSS -t model.bnd > model.cfg                 # generate a full .cfg TEMPLATE from a .bnd (handy!)
MaBoSS -l -c model.cfg model.bnd                # print the derived logical expressions
MaBoSS -c model.cfg -d model.bnd                # dump the fully-resolved config
```
Outputs: **`out_prefix_probtraj.csv`** (time evolution of node/state probabilities, the main result),
`out_prefix_fp.csv` (fixed points + probabilities), `out_prefix_statdist.csv` (stationary distribution),
`out_prefix_run.txt` (summary).

## Validation checklist (what to check when reviewing/writing a model)

1. Every `$var` used in `.bnd` is defined in the `.cfg` (else MaBoSS errors).
2. Every node referenced in a `logic` expression is a declared `node` (typos = silent 0).
3. Driver/input nodes use `logic = (SELF);` if they must keep their initial state.
4. `is_internal` set intentionally (observed vs hidden). istate priors present for nodes you want
   at a defined baseline (else random).
5. ≤64 nodes (default engine build). For more, the engine must be recompiled (`make MAXNODES=100`).
6. To sanity-check: `MaBoSS -t model.bnd` regenerates a template .cfg you can diff against yours.

Run the model and read `_probtraj.csv` with the **`pymaboss`** skill. For where models come from
(BioModels, CellCollective, WebMaBoSS, GINsim export) and how they map to cancer types, see
**`maboss-ecosystem`**.
