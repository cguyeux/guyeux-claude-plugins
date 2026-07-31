---
name: boolean-attractors
description: >-
  Compute and label the ATTRACTORS (stable states / phenotypes) of a Boolean model with
  mpbn (Most Permissive), PyBoolNet or pyStableMotifs, starting from a MaBoSS .bnd/.cfg
  via `maboss.to_minibn`. Use this to identify the discrete states a model can settle in
  (e.g. epithelial / hybrid / mesenchymal, proliferative / apoptotic) which a single
  MaBoSS run only reports as node probabilities, not as named attractors. Also covers
  fixed points and trap spaces. Triggers: "find the attractors", "epithelial and
  mesenchymal states", "stable states / fixed points", "phenotypes of the model",
  "trap spaces", "which steady states", "mpbn", "pyboolnet attractors".
---

# boolean-attractors : from probabilities to named states

**Key idea.** MaBoSS gives P(node ON) at steady state (a mixture over attractors). To get
the *discrete states themselves* (phenotypes), compute the network's attractors. mpbn is
pip-installable (no Java) and reads a MaBoSS model via `maboss.to_minibn`.

## Ready-made: the maboss-mcp tool

The `maboss-mcp` server (this plugin's `mcp/` folder) exposes **`maboss_attractors`**:
give it `bnd`+`cfg` (optionally `output_nodes` = phenotype markers) and it returns each
attractor's active-node signature. Verified on the cancer_signaling sample -> 4 attractors
(proliferative BRAF/ERK/MAPK/Proliferation; apoptotic Apoptosis/EGFR; two immune ones).

## Direct (Python, in the maboss-mcp or colomoto image)

```python
import maboss, mpbn
sim = maboss.load("model.bnd", "model.cfg")
bn  = maboss.to_minibn(sim)                 # colomoto minibn, pure Python
mbn = mpbn.MPBooleanNetwork(bn)
for a in mbn.attractors():                  # a: {node: 0 | 1 | '*'}
    active = sorted(k for k,v in a.items() if v == 1)
    print(active)                           # <- label by signature (E vs M markers)
# reachable attractors from a specific initial state:
mbn.attractors(reachable_from={"BMP":0, "TGFB_L":0, "GF":0})
```
`'*'` = free/oscillating node. **Label each attractor** by its markers: epithelial =
Ecad/miR200/TightJunc ON & ZEB/SNAI/VIM OFF; mesenchymal = the reverse; hybrid = mixed.

## Trap spaces : ALSO mpbn, no PyBoolNet needed (installed)

mpbn computes trap spaces directly; do NOT reach for PyBoolNet (absent from the image) just
for these:
```python
mbn.fixedpoints()            # iterator over fixed points
mbn.minimal_trapspaces()     # minimal trap spaces (= the MP attractors)
mbn.maximal_trapspaces()     # maximal trap spaces
mbn.principal_trapspace()    # the smallest trap space containing everything
mbn.count_fixedpoints(); mbn.count_minimal_trapspaces()   # counts, instant even on 61 nodes
```
Vécu (MET model, 61 nodes): 25 fixed points = 25 minimal trap spaces, so every attractor is a
point fixe with no intermediate non-singleton trap space, trap-space structure only becomes
interesting on **mutated** models or with inputs percolated (`constraints={...}`).

## Options that need the CoLoMoTo image (only if mpbn falls short)

- **PyBoolNet**, exact asynchronous attractors and prime-implicant trap spaces:
  `pyboolnet.trap_spaces.compute_trap_spaces(primes, "min")` (needs a `.bnet`, see biolqm-convert).
- **pyStableMotifs**, attractors + the **stable motifs** that feed target control:
  `sm.AttractorRepertoire.from_primes(primes).summary()`. Use it when you specifically need the
  stable-motif decomposition; for plain reachability/control, AEON.py (see `bn-control`) is installed.

**Pitfall.** If ALL attractors are trivial/identical regardless of inputs, suspect a
degenerate `.bnd` (frozen nodes) -> fix it first with the `biolqm-convert` skill.
