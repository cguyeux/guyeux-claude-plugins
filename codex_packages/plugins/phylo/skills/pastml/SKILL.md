---

name: pastml
description: >-
  Academic research toolkit for peer-reviewed evolutionary genomics. PastML (Institut
  Pasteur) for fast maximum-likelihood ancestral character reconstruction of discrete
  characters (location, host, antimicrobial-resistance allele, lineage) on a rooted tree,
  with compressed-tree HTML output; scales to 10^4 to 10^5 tips. Use when inferring the
  geographic origin of an MTBC sublineage in a research collection, reconstructing ancestral
  host jumps of zoonotic Mycobacterium, dating the emergence of a resistance allele on a
  published phylogeny, or mapping any discrete trait onto an existing tree.
---

# PastML : Fast Ancestral Character Reconstruction

> [!TIP]
> **Au-delà de quelques milliers de feuilles**, la reconstruction d'états ancestraux sature la
> mémoire locale : `mp` (125 Go, disponible sans file d'attente) ou `mh` `bigmem` (1 To). PastML
> reste à ajouter à l'environnement `/Work/Users/cguyeux/envs/phylo` (`micromamba install -p … pastml`). Voir le skill `remote-compute` (sonde d'état, modèles `sbatch`, pièges). Prérequis : VPN monté (`sudo vpn up`).


## Overview

**PastML** is a fast Maximum-Likelihood method for **Ancestral Character
Reconstruction (ACR)** on rooted phylogenetic trees, designed by
**Sohta A. Ishikawa**, **Anna Zhukova**, **Wataru Iwasaki**, and
**Olivier Gascuel** at the **Unité Bioinformatique Évolutive, Institut
Pasteur** (Paris) and the University of Tokyo. It reconstructs the
most likely state of a discrete character (location, host,
phenotype, lineage, …) at every internal node of a tree and visualises
the result as an **interactive HTML compressed tree** that automatically
collapses tree regions where the state is uniform, surfacing only the
regions where state changes occurred.

The novelty over earlier ACR tools is two-fold:

1. **Speed and scale.** Linear-time algorithms scale to 10⁴–10⁵-tip trees.
2. **Decision-theoretic state assignment.** Uses the **Brier score** to
   pick a single state where uncertainty is low, and a *set* of states
   where uncertainty is high, avoiding the false confidence of
   single-state predictions everywhere.

- **Reference**: Ishikawa S.A., Zhukova A., Iwasaki W. & Gascuel O.
  *A Fast Likelihood Method to Reconstruct and Visualize Ancestral
  Scenarios.* **Molecular Biology and Evolution** 36(9): 2069–2085 (2019).
  DOI: `10.1093/molbev/msz131`
- **GitHub**: `https://github.com/evolbioinfo/pastml`
- **PyPI**: `https://pypi.org/project/pastml/`
- **Web server**: `https://pastml.pasteur.fr/`
- **Institut Pasteur project page**: `https://research.pasteur.fr/en/software/pastml/`
- **License**: **GPL-3.0**
- **Latest version (verified)**: **1.9.51** (April 2025)

## Why it matters for MTBC × anthropology

PastML is the **trait-mapping layer** that complements `nextstrain`
(which builds and visualises the tree itself). For your TB work
its specific niches:

1. **Geographic ancestral reconstruction at scale.** When you have a
   pre-built MTBC phylogeny (from IQ-TREE / RAxML / TBannotator) and
   you want to ask *"where did this lineage originate?"*, PastML
   gives you a fast answer with confidence intervals, without having
   to re-run the full Augur pipeline.
2. **Ancestral host inference for zoonotic *Mycobacterium*.** Mapping
   `host = {Homo sapiens, Bos taurus, Capra hircus, Phocidae, …}` onto
   an MTBC tree reconstructs the **most likely host at the root and at
   each internal split**. This is the most direct way to test
   host-jump hypotheses for *M. bovis*, *M. caprae*, *M. pinnipedii*,
   *M. orygis*, etc.
3. **Drug-resistance emergence patterns.** Mapping resistance
   genotypes (`rpoB`, `katG`, `inhA`, …) onto the tree reveals whether
   resistance emerged once-and-spread, or independently many times.
   Ishikawa et al. used exactly this approach for HIV; the method
   transposes directly to MTBC.
4. **Compressed-tree visualisation.** The HTML output collapses
   uniform regions automatically, so even a 10 000-tip MTBC tree
   becomes a navigable, slide-friendly figure with state changes
   prominently surfaced.

## Algorithm in one paragraph

For each character (geography, host, …) and each tree node, PastML
computes the likelihood of every possible state given the tip
annotations and the tree topology, under one of several models:

- **MPPA** (*Maximum a Posteriori with Brier score*), the default;
  assigns one state when confident, several states when uncertain
- **MAP** (*Maximum a Posteriori*), single-state, may overstate
  certainty
- **JOINT**, joint reconstruction across the whole tree
- **DOWNPASS / ACCTRAN / DELTRAN**, parsimony alternatives
- **F81 / JC / EFT**, substitution models

Then it collapses subtrees with uniform predicted state into single
nodes (the *metanodes*) and exports an interactive HTML.

## Installation

**Recommended: `uv` with isolated Python 3.11.** This is the only
method confirmed to work on the local machine (Arch Linux, Python
3.14 system default, May 2026). Installs `pastml` and its scientific
stack (`scipy`, `numpy`, `pandas`, `ete3`) in ~30 seconds without
root access and without polluting the system Python.

```bash
# Install uv if absent: see https://docs.astral.sh/uv/
# Then create an isolated environment with Python 3.11
~/.local/bin/uv venv --python 3.11 ~/venvs/pastml311

# Install pastml into that environment
~/.local/bin/uv pip install --python ~/venvs/pastml311/bin/python pastml

# Verify
~/venvs/pastml311/bin/pastml --version
# → pastml 1.9.51 (May 2026)
```

To use the binary in subsequent commands, either reference its
absolute path (`~/venvs/pastml311/bin/pastml`) or activate the venv
(`source ~/venvs/pastml311/bin/activate`).

### Methods that DO NOT work (verified 2026-05-09)

Documenting failure modes so a future invocation does not waste time:

```bash
# ❌ pip install pastml --user
# Fails on Python 3.14: scipy build error (numpy metadata generation
# fails in scipy's build dependency chain). Python 3.14 is too recent
# for scipy's published wheels (May 2026).

# ❌ pipx install pastml
# Same scipy build issue. Internal pipx metadata also gets corrupted
# by the partial install, requiring manual venv removal.

# ❌ docker run -v $(pwd):/data:rw -t evolbioinfo/pastml ...
# Docker 29.4.x on Arch Linux: TTRPC "Yunix" runtime protocol bug.
# Fails before container starts. May work on other Docker versions.

# ❌ singularity / podman
# Not installed on the local machine.
```

If the `uv` route fails on a different machine, fall back to:
1. `conda create -n pastml python=3.11 && conda activate pastml && pip install pastml`
2. Docker on a machine with a working runtime
3. Web server: <https://pastml.pasteur.fr/>

Verify install:

```bash
~/venvs/pastml311/bin/pastml --help
```

## Inputs and outputs

### Input 1 : rooted phylogenetic tree

A **rooted** Newick tree. PastML does not root unrooted trees for you;
use `nw_reroot` (Newick utilities), `gotree`, or specify an outgroup
upstream.

```bash
# Example: a tree from IQ-TREE
iqtree -s alignment.fasta -nt AUTO
# → produces alignment.fasta.treefile
```

### Input 2 : character annotation table

TSV or CSV with tip IDs in the first column and one column per
character to reconstruct.

```
strain	country	host	rpoB_mut	lineage
SRR123	Ghana	Homo sapiens	S531L	L4.15
SRR456	Peru	Homo sapiens	WT	L4.1
SRR789	UK	Bos taurus	WT	M.bovis
...
```

Use `--data_sep $'\t'` for TSV or `--data_sep ,` for CSV. Missing
values are allowed.

### Outputs

- **`<name>.html_compressed.html`**, the interactive collapsed map
  (the main deliverable)
- **`<name>.html.html`**, the full uncollapsed tree (slower to render)
- **`marginal_probabilities.tab`**, per-node posterior probabilities
  for each state
- **`combined_ancestral_states.tab`**, single most-likely state per node
- **`named.tree_<column>.nwk`**, the tree with internal nodes labelled
  by reconstructed state

## Workflows

### Workflow 1 : Geographic ancestral reconstruction of an MTBC sublineage

Goal: given a TBannotator subtree of L4.15 isolates, reconstruct the
most likely country of origin of the lineage.

```bash
pastml \
  --tree L4_15.tree.nwk \
  --data L4_15.metadata.tsv \
  --data_sep $'\t' \
  --columns country \
  --html_compressed L4_15_geo.html \
  --work_dir L4_15_pastml \
  --threads 8
```

Open `L4_15_geo.html` in a browser. The compressed tree highlights
the inferred geographic origin and the major dispersal events along
the backbone.

### Workflow 2 : Ancestral host inference for zoonotic MTBC

Goal: confirm the *M. pinnipedii* pre-Columbian Andean host-jump
hypothesis (Bos2014, Vagene2022) using PastML on a tree that mixes
modern *M. pinnipedii*, modern *M. tuberculosis*, and the 6 ancient
samples from `spaam-ancient-metagenome-dir`.

```bash
pastml \
  --tree mtbc_combined.nwk \
  --data mtbc_combined.tsv \
  --data_sep $'\t' \
  --columns host species \
  --html_compressed pinnipedii_host.html \
  --work_dir pinnipedii_run
```

Look for the host change at the *M. pinnipedii* split. If PastML
infers *Phocidae* as ancestral and *Homo sapiens* as derived, that
is direct visual support for the host-jump narrative.

### Workflow 3 : Drug-resistance emergence pattern

Goal: test whether `rpoB S450L` (rifampicin resistance) emerged once
or multiple times in your MTBC corpus.

```bash
pastml \
  --tree mtb.tree.nwk \
  --data mtb_amr.tsv \
  --columns rpoB_S450L \
  --html_compressed rpoB_evolution.html
```

Count the number of independent transitions from `WT` to `S450L` along
the tree branches in `marginal_probabilities.tab`. Multiple transitions
support an "emerges-under-treatment" model; a single transition
supports a "spreads-clonally" model.

### Workflow 4 : Joint reconstruction of multiple characters

PastML can reconstruct several characters simultaneously, which is
useful for asking compositional questions.

```bash
pastml \
  --tree mtb.tree.nwk \
  --data mtb_full.tsv \
  --columns country host lineage rpoB_mut \
  --html_compressed mtb_multi.html
```

The output annotates each compressed metanode with all four
reconstructed characters at once.

### Workflow 5 : Python API for programmatic use

```python
from pastml.acr import pastml_pipeline

pastml_pipeline(
    tree="L4_15.tree.nwk",
    data="L4_15.metadata.tsv",
    data_sep="\t",
    columns=["country", "host"],
    html_compressed="L4_15_pastml.html",
    work_dir="L4_15_pastml",
    threads=8,
    prediction_method="MPPA",
    model="F81",
)
```

The Python API returns the same files as the CLI but lets you embed
PastML in a larger Snakemake / Nextflow workflow without shelling out.

## Caveats

- **Tree must be rooted.** Use an outgroup or an explicit rooting
  command before passing to PastML.
- **Discrete characters only.** PastML does not handle continuous
  characters (use BEAST or `phytools::contMap` in R for those).
- **Sampling bias propagates into the reconstruction.** If your
  *M. tuberculosis* sample is 80% from one country, PastML will
  infer that country as the most likely ancestral state, regardless
  of biological reality. **Subsample for balance** before
  reconstruction (mirror the `nextstrain` Workflow 4 approach).
- **MPPA is conservative, by design.** When two or more states are
  near-equally likely, MPPA returns *all* of them; this is more
  honest than picking one but can clutter the visualisation. Tune
  with `--prediction_method MAP` for a single-state output if needed,
  but report the trade-off.
- **Compressed tree obscures branch length information.** The
  HTML output is good for narrative but not for divergence-time
  arguments. Pair with a TimeTree / Augur view when divergence
  times matter.
- **No built-in dating.** PastML maps states onto an existing tree
  but does not date nodes. For dating, use TreeTime / Augur upstream.
- **Sample-tree mismatch.** Tip IDs in the tree must exactly match
  the first column of the data table. Pre-process for whitespace,
  prefixes, and case.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`nextstrain`** | Build and time-scale the tree first; then PastML maps additional characters |
| **TBannotator MCP** | Source of MTBC trees and per-strain metadata |
| **`spaam-ancient-metagenome-dir`** | Ancient tip annotations (host, age, lineage) |
| **`enterobase`** | Alternative source of bacterial trees and HierCC labels |
| **`bovine-genomics`** | Host-side context for *M. bovis* host inference |
| **`pleiades`**, **`orbis`**, **`owtrad`** | Historical-place context for the reconstructed origin |
| **TreeTime** | Upstream dating; PastML works on the dated tree |
| **IQ-TREE / RAxML / FastTree** | Tree-building backends |
| **gotree / nw_utils** | Rooting and tree manipulation utilities |
| **ete3 / dendropy** (Python) | Programmatic tree manipulation around PastML |

## Citation

```bibtex
@article{ishikawa2019pastml,
  title   = {A Fast Likelihood Method to Reconstruct and Visualize
             Ancestral Scenarios},
  author  = {Ishikawa, Sohta A. and Zhukova, Anna and Iwasaki, Wataru and
             Gascuel, Olivier},
  journal = {Molecular Biology and Evolution},
  volume  = {36},
  number  = {9},
  pages   = {2069--2085},
  year    = {2019},
  doi     = {10.1093/molbev/msz131}
}
```

When PastML's MPPA prediction method is used, also cite the Brier-score
foundation (a footnote in the 2019 paper).

## Codex packaging note

This packaged copy targets Codex. MCP tool names in `allowed-tools` are prerequisites: verify them with `codex mcp list` in the active profile before relying on live queries.
