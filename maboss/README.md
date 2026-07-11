# maboss — plugin

Academic toolkit for **MaBoSS** (Markovian Boolean Stochastic Simulator) and the
**CoLoMoTo** ecosystem, for the Guyeux group (FEMTO-ST, Université Marie et Louis Pasteur).
Ground truth captured from the official refcard, the pyMaBoSS source, and the
`colomoto-docker` repository (July 2026).

## Skills

**MaBoSS core**
- `maboss-model` — author/validate `.bnd`/`.cfg` Boolean models (refcard grammar)
- `pymaboss` — drive the pyMaBoSS Python API (load, run, mutate, probtraj, CCT evaluator)
- `maboss-ecosystem` — navigate WebMaBoSS, repositories, positioning vs INDRA
- `maboss-advanced` — UPMaBoSS/PopMaBoSS, mutant scans, sensitivity, CCT verdicts

**Getting & fixing models**
- `colomoto-run` — run the CoLoMoTo Docker notebook (gateway to all ~27 tools)
- `biolqm-convert` — robust format conversion (bioLQM); fix a degenerate GINsim→`.bnd` export
- `model-repositories` — import from BioModels / Cell Collective / GINsim / CaSQ

**Analysis**
- `boolean-attractors` — compute & label attractors/phenotypes (mpbn/PyBoolNet/pyStableMotifs)
- `bn-control` — reprogram toward a target attractor (Pint/CABEAN/pyStableMotifs/ActoNet)

**Data & therapeutics**
- `model-inference` — build a model from data (BoNesis/Caspo/scBoolSeq)
- `pydruglogics` — in-silico drug perturbations & synergy (PyDrugLogics/NORDic)
- `astrologics` — reason over ENSEMBLES of models (sysbio-curie)

## MCP server (`mcp/`)

A running MCP server over MaBoSS (Python FastMCP, stdio, Docker `FROM` the mabossDemo
backend image which already ships pyMaBoSS). Tools: `maboss_sample_model`,
`maboss_model_nodes`, `maboss_run_simulation` (mutations + initial conditions),
**`maboss_attractors`** (mpbn), `maboss_query_cct` (Oscar Dufossez's evaluator),
`maboss_convert_model` (SBML-qual/BoolNet), `maboss_import_biomodels`. See `mcp/README.md`.

```bash
docker build --network=host -t maboss-mcp:v1 mcp/
claude mcp add maboss -- docker run -i --rm maboss-mcp:v1
```

## Design note

Skills carry the KNOWLEDGE to drive each tool (many CoLoMoTo tools are Java/OCaml/conda,
run via `colomoto-run`); the MCP server exposes the pip-installable subset (MaBoSS + mpbn)
as live, callable tools. Cross-project learnings live in `~/.claude/knowledge/maboss.md`.
