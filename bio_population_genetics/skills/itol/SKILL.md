---
name: itol
description: >-
  Upload, annotate and export phylogenetic tree figures via iTOL (Interactive
  Tree Of Life), using scripts/itol_pipeline.py (itolapi). Turns a Newick/Nexus
  tree plus annotation tracks (lineage colour ranges, branch colours, bootstrap
  symbols) into SVG/PDF/PNG, with presets (article, supplement, presentation,
  poster) and batch export. Use when: a final MTBC lineage tree figure for a
  manuscript or slide, an annotated RAxML/IQ-TREE tree.
---

# iTOL : Annotated Phylogenetic Tree Figures (upload / export pipeline)

## Overview

`scripts/itol_pipeline.py` is an end-to-end wrapper around iTOL (Interactive Tree Of
Life): it uploads a tree (**Newick or Nexus**) plus iTOL annotation files, configures
the display, and exports publication-quality figures (SVG / PDF / PNG) with
programmatic legends, instead of clicking through the iTOL web UI. It
uses the `itolapi` library when available and falls back to direct HTTP `requests`
otherwise. Companion module `scripts/presets.py` holds the export presets, MTBC
legends, and comparison configurations; `scripts/itol_api_legacy.py` is the older
direct-API client kept for reference.

## Requirements

- An iTOL account with batch/API access (programmatic export needs an **iTOL
  subscription** — this is a paid tier, not the free web account).
- `pip install itolapi` (recommended) or `pip install requests` (fallback).
- API key resolved from, in order: `--api-key/-k`, the `ITOL_API_KEY` env var, or
  `~/.config/itol/api_key`.

**Before starting: check whether an API key is actually configured**
(`echo $ITOL_API_KEY` or `cat ~/.config/itol/api_key`). If neither exists, this
whole skill is a dead end — there is no local/offline mode, `upload` and
`export` both hard-fail without a key (see `resolve_api_key()` in
`itol_pipeline.py`). For a manuscript or slide figure of a tree that does not
need iTOL's interactive web feature set (drag-and-drop annotation editing,
persistent shareable links, SmartView-style large-tree navigation), use the
**`etetoolkit`** skill (ETE 4) instead: local rendering, no account, no API
key, PNG via SmartView (`ete4[render-sm]`) or PNG/PDF/SVG via the legacy Qt
treeview (`ete4[treeview]`) — see its `references/visualization.md`. Reach
for iTOL specifically when the destination is the interactive web view itself,
when annotation tracks must stay editable by a co-author without touching
code, or when a subscription is already available; reach for `etetoolkit`
for a one-off static vector figure, which is the common case for a single
focused clade tree going straight into a LaTeX manuscript.

## Usage

Run the pipeline directly (`python3 scripts/itol_pipeline.py <subcommand>`).

### One-step pipeline (upload + export)

```bash
python3 scripts/itol_pipeline.py pipeline tree.nwk lineages.txt bootstrap.txt \
    --project "MTBC_L4" --tree-name "L4.15 RAxML" --preset article \
    --output-dir figures/ --base-name l4_15_tree --legend lineage_colors
```

### Step by step

```bash
# 1. upload, get a tree id
python3 scripts/itol_pipeline.py upload tree.nwk lineages.txt --project "MTBC_L4"
# 2. export a rendered figure (override display options as needed)
python3 scripts/itol_pipeline.py export <tree_id> -o fig.svg --preset article \
    --display-mode 2 --line-width 2 --font-size 12 --align-labels \
    --bootstrap --bootstrap-type 2 --bootstrap-min 70 --datasets lineage,resistance
# 3. or export the same tree in several presets at once
python3 scripts/itol_pipeline.py batch-export <tree_id> \
    --presets article,supplement,presentation --output-dir figures/ --base-name tree
```

`--datasets` (comma-separated) selects which uploaded annotation datasets are visible
in a given export; `--legend NAME` (repeatable) injects a named legend from
`presets.MTBC_LEGENDS`. `display-mode` is 1=rectangular, 2=circular, 3=unrooted.

## Export presets (`presets.EXPORT_PRESETS`)

| Preset | Format | Layout | Tuned for |
|---|---|---|---|
| `article` | SVG | circular | manuscript main figure (bootstrap symbols ≥ 70, ranges legend) |
| `supplement` | PDF | rectangular | supplementary tree (text bootstrap ≥ 60) |
| `presentation` | PNG | circular | slides (thicker lines, larger font) |
| `poster` | SVG | circular | posters (largest fonts, bootstrap symbols ≥ 80) |

Override any preset field on the `export`/`pipeline` command (e.g. `--format pdf`,
`--line-width 3`). Comparison mode renders the same tree with different visible
datasets via `presets.COMPARISON_CONFIGS` (e.g. `lineage_overview`).

## Annotation files

iTOL annotation tracks are plain-text dataset files (one per track), uploaded
alongside the tree:

- `DATASET_COLORSTRIP` / `TREE_COLORS`, lineage colour ranges and branch colours.
- `DATASET_SYMBOL` / bootstrap display, node support.
- `DATASET_BINARY` / `DATASET_HEATMAP`, presence/absence (RD, resistance alleles).

Several MTBC skills emit such tracks directly (see Integration). Keep one `.txt` per
track and pass them all to `upload`/`pipeline`.

## Integration with other skills

| Tool | Role |
|---|---|
| `raxml`, `iqtree-lsd2` | produce the `.nwk` tree that iTOL renders |
| `phylogeography`, `resistance-profiler`, `ancestral-reconstruction` | emit iTOL annotation `.txt` tracks (country, AMR, ancestral states) |
| `mtbc-lineages` | lineage colour scheme for the colour-strip track |
| `pastml` | alternative: compressed-tree HTML for ancestral states (no iTOL account needed) |
| `etetoolkit` | alternative: local static PNG/PDF/SVG rendering of the same `.nwk`, no iTOL account needed — preferred default for a one-off manuscript/slide figure |
