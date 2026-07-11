---
name: colomoto-run
description: >-
  Run the CoLoMoTo Interactive Notebook (Docker image colomoto/colomoto-docker) that
  bundles ~27 Boolean/logical network tools (MaBoSS, GINsim, bioLQM, PyBoolNet, mpbn,
  Pint, CABEAN, pyStableMotifs, CaSQ, NuSMV, BoNesis, Caspo, scBoolSeq, PyDrugLogics,
  NORDic, AEON.py, BooleanNet, boolSim, BNS, minibn, ERODE, CellCollective, ...) in one
  reproducible Jupyter environment. Use when a task needs a CoLoMoTo tool that is NOT
  pip-installable in a slim image (Java/OCaml/conda deps: bioLQM, GINsim, Pint, CABEAN),
  when reproducing a published qualitative-modelling analysis, or to open a .zginml /
  SBML-qual / .bnd model in a full toolchain. Triggers: "lancer colomoto", "colomoto
  notebook", "run the CoLoMoTo docker", "tool X is conda-only", "reproduce this .ipynb".
---

# colomoto-run — the CoLoMoTo notebook, gateway to the whole ecosystem

**When to use.** Any time a CoLoMoTo tool is needed that does not install cleanly in a
pip/slim image (bioLQM, GINsim, Pint, CABEAN need Java/OCaml/conda). The image already
has ALL of them pinned to reproducible versions (archived on Zenodo, DOI in the repo).

## Launch (helper script)

```bash
pip install -U colomoto-docker
colomoto-docker                         # latest image, opens Jupyter in the browser
colomoto-docker -V 2024-04-01           # a specific reproducible tag
colomoto-docker --bind .                # mount the current dir (else files are ephemeral)
```
Files inside the container are deleted on stop EXCEPT the `persistent/` directory and
anything under a `--bind` mount.

## Launch (plain docker, headless — for scripting/agents)

```bash
docker run --rm -v "$PWD":/notebook/work colomoto/colomoto-docker:latest \
  python -c "import maboss, biolqm, mpbn; print('ok')"
```
Caveat (this environment): pulling `colomoto/colomoto-docker` is ~3 GB and has failed/
been killed before — pull once, patiently, and reuse. For MaBoSS-only + attractors, the
lightweight `maboss-mcp` image (see the mcp/ folder) is enough and avoids the big pull.

## Inventory by function (authoritative: `tools/index.md` of the repo)

- Edit/convert: **GINsim**, **bioLQM**, **CaSQ**, CellCollective, minibn
- Simulate: **MaBoSS**, BooleanNet, **mpbn**, R-BoolNet
- Attractors/trap spaces: **PyBoolNet**, **mpbn**, boolSim, BNS, **AEON.py**, **pyStableMotifs**, BooN
- Control/reprogramming: **Pint**, **CABEAN**, pyStableMotifs, ActoNet, Caspo-control
- Inference/data: **BoNesis**, **Caspo**, **scBoolSeq**
- Model checking/reduction: **NuSMV**, ERODE
- Therapeutic: **PyDrugLogics**, **NORDic**
- Ensembles: **AstroLogics** (sysbio-curie)

Get the up-to-date list: `curl -fsSL https://raw.githubusercontent.com/colomoto/colomoto-docker/master/tools/index.md`.
Each tool has its own skill in this plugin (biolqm-convert, boolean-attractors, bn-control, ...).
