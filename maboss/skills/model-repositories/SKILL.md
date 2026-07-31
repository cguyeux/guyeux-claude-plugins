---
name: model-repositories
description: >-
  Find and import existing Boolean/logical cancer & signalling models into a MaBoSS-ready
  form, from BioModels (REST API), Cell Collective, the GINsim model repository, and CaSQ
  (build an executable model from a CellDesigner/SBML interaction map). Use when you need a
  real published model instead of hand-writing a .bnd, or to feed the mabossDemo catalog /
  the maboss-mcp import tool. Triggers: "import a model", "BioModels", "Cell Collective",
  "GINsim repository", "find a published Boolean model", "CaSQ", "map to executable model",
  "get the Selvaggio EMT model".
---

# model-repositories : get a real model, don't hand-write one

## BioModels (REST, no auth) : the most programmatic source

```bash
# 1) find candidates (many Boolean cancer models: Montagud2022 prostate, Verlingue2016, ...)
curl -fsSL "https://www.ebi.ac.uk/biomodels/search?query=boolean%20model&format=json"
# 2) list a model's files -> main file name (DON'T guess {id}.xml, causes 400/404)
curl -fsSL "https://www.ebi.ac.uk/biomodels/model/files/MODEL1611180000?format=json"
# 3) download the main SBML-qual, then convert (pyMaBoSS, no Java)
```
```python
import maboss
maboss.sbml_to_bnd_and_cfg("Model.sbml", "m.bnd", "m.cfg")
```
Prefer a native `.bnd`/`.cfg` pair if the deposit ships one (many CoLoMoTo deposits do) ->
no conversion. This is exactly what the maboss-mcp **`maboss_import_biomodels`** tool and
mabossDemo's import endpoint (`POST /api/models/import`) do; reuse them.

## Cell Collective

Public repository (cellcollective.org). Export a model as SBML-qual or tabular, then
`maboss.loadSBML(...)` / `maboss.loadTabularQual(...)` (pyMaBoSS). The colomoto image has a
`cellcollective` python module for programmatic fetch.

## GINsim model repository

`ginsim.org` hosts curated `.zginml` models (incl. the EMT/metastasis models). Load with
GINsim/bioLQM and export to MaBoSS (see the `biolqm-convert` skill). Preferred when you
need the COMPLETE logic (a raw `.zginml`->`.bnd` export can be degenerate).

## CaSQ : from a pathway map to a model

```bash
casq input_map.xml output_model.sbml      # CellDesigner/SBML map -> SBML-qual Boolean model
```
Then convert to MaBoSS as above. Use when you have a curated interaction map but no
executable model yet.

**Caveat**: not every SBML is qualitative; conversion raises "not a qualitative sbml" or
"multivalued formulas" -> catch and report (the mabossDemo import returns a clean 400).
