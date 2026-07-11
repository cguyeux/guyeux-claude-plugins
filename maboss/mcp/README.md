# maboss_mcp — MCP server over MaBoSS

Exposes the MaBoSS Boolean stochastic simulator as MCP tools, so an agent
(Claude Code, etc.) can run simulations, apply mutations, evaluate CCT/MCCT
assertions, and import Boolean models.

## Tools

| tool | what it does |
|------|--------------|
| `maboss_sample_model` | returns a bundled `cancer_signaling` `.bnd`/`.cfg` to try the others |
| `maboss_model_nodes` | lists the node names in a `.bnd` |
| `maboss_run_simulation` | runs the real engine → P(node) baseline (+ perturbed under `NODE:ON/OFF` mutations) |
| `maboss_query_cct` | evaluates a CCT assertion (`Inc(node:EGFR) / [] [ BRAF:OFF ] [ 5% digits:3 ]`) via Oscar Dufossez's `MaBoSSEvaluator` |
| `maboss_convert_model` | SBML-qual / BoolNet → MaBoSS `.bnd`/`.cfg` (pyMaBoSS) |
| `maboss_import_biomodels` | fetch a Boolean model from BioModels by id (e.g. `MODEL1611180000`) → `.bnd`/`.cfg` |

## Why Docker

pyMaBoSS + the compiled MaBoSS engine do not install cleanly in a local venv on
recent Python (the project's constraint). The server therefore runs inside a
Docker image built `FROM` the project's backend image (which already ships
pyMaBoSS), with only the MCP SDK added. Transport is **stdio**.

## Build

```bash
docker build --network=host -t maboss-mcp:v1 .
```

(The base image `rg.fr-par.scw.cloud/mabossdemo/backend:v15` must be available
locally, or replace it with any image that has pyMaBoSS installed.)

## Register in Claude Code

Add to your MCP config (`~/.claude/settings.json`, or a project `.mcp.json`):

```json
{
  "mcpServers": {
    "maboss": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "maboss-mcp:v1"]
    }
  }
}
```

Or with the CLI:

```bash
claude mcp add maboss -- docker run -i --rm maboss-mcp:v1
```

`maboss_import_biomodels` needs outbound internet (default Docker bridge is fine).
Everything else is offline.

## Smoke test (without the MCP protocol)

The logic lives in plain `_functions`; call them directly:

```bash
docker run --rm --entrypoint python -v "$PWD":/mcp maboss-mcp:v1 -c \
  "import sys; sys.path.insert(0,'/mcp'); import server; s=server._sample_model(); \
   print(server._run_simulation(s['bnd'], s['cfg'], ['BRAF:OFF'])['perturbed']['EGFR'])"
```
