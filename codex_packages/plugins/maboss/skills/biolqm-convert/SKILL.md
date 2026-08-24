---

name: biolqm-convert
description: >-
  Convert logical/Boolean models between formats robustly with bioLQM (the CoLoMoTo
  Logical Qualitative Modelling toolkit): SBML-qual to MaBoSS .bnd/.cfg to BoolNet
  .bnet to GINML/.zginml, plus model reduction, booleanization and determinization.
  Use this to REGENERATE a complete MaBoSS model from a GINsim .zginml or an SBML-qual
  export, especially to FIX a degenerate .bnd (an export where most nodes came out as
  `rate_up = 0;` with no `logic =`, so they are frozen OFF and the model has no dynamics).
  Triggers: "convert zginml to maboss", "bnd is degenerate / frozen", "most nodes have no
  logic", "sbml-qual to bnd", "biolqm", "re-export the GINsim model", "model has no dynamics".
---

# biolqm-convert : robust format conversion (and fixing broken exports)

**Why it matters (our case).** A GINsim `.zginml` -> MaBoSS export can be DEGENERATE:
most nodes get `Node X { rate_up = 0; rate_down = $u_X; }` with NO `logic =` line, so
they can never turn on and the network has no real dynamics (only a trivial attractor).
Diagnose in 2 greps on the `.bnd`: `grep -c "logic ="` (regulated nodes) vs
`grep -c "rate_up = 0;"` (frozen). If the second dominates, the file is broken -> re-export.

**bioLQM needs Java** -> run it inside the CoLoMoTo image (see the `colomoto-run` skill),
not a slim pip venv.

## Conversions

```python
import biolqm
lqm = biolqm.load("model.zginml")          # GINsim native (or .sbml, .bnet, .lp, ...)
biolqm.save(lqm, "model.bnd")               # -> MaBoSS .bnd (+ .cfg alongside)
biolqm.save(lqm, "model.sbml", "sbml")      # -> SBML-qual
biolqm.save(lqm, "model.bnet", "bnet")      # -> BoolNet
```
Format is inferred from the extension, or forced with the 2nd argument. The MaBoSS export
writes the FULL logic (`rate_up = @logic ? $u : 0`), unlike a broken zginml->bnd.

## GINsim path (also Java)

```python
import ginsim
lrg = ginsim.load("model.zginml")
ginsim.service("MaBoSS").export(lrg, "model.bnd")   # GINsim's own MaBoSS export
```

## Pip-only fallback for SBML-qual (no Java)

If you only have SBML-qual, pyMaBoSS converts it without Java (already used by the
maboss-mcp `maboss_convert_model` tool and mabossDemo's import):
```python
import maboss
maboss.sbml_to_bnd_and_cfg("model.sbml", "model.bnd", "model.cfg")
```

## Reduction / determinization (bioLQM)

```python
red = biolqm.reduce(lqm, "duplicate")      # remove pseudo-nodes / simplify
det = biolqm.determinize(lqm)              # multivalued -> Boolean if needed
```

After a clean conversion, hand the `.bnd`/`.cfg` to the `pymaboss` / `boolean-attractors`
skills (or the maboss-mcp tools) to simulate and extract attractors.

## Codex packaging note

This packaged copy targets Codex. MCP tool names in `allowed-tools` are prerequisites: verify them with `codex mcp list` in the active profile before relying on live queries.
