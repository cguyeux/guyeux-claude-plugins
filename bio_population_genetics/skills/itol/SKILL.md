---
name: itol
description: >-
  Upload, annotate, and export publication-quality phylogenetic tree figures via
  iTOL (Interactive Tree Of Life) using the bundled itolapi pipeline
  (scripts/itol_pipeline.py). Turns a Newick/Nexus tree plus annotation tracks
  (lineage colour ranges, branch colours, bootstrap symbols, datasets) into
  SVG/PDF/PNG figures with presets tuned for an article, a supplement, a
  presentation, or a poster, plus batch export and comparison mode.

  Use when: producing a final MTBC lineage tree figure for a manuscript or a slide,
  rendering an annotated RAxML/IQ-TREE tree with lineage colour ranges and bootstrap
  support, exporting the same tree in several formats/presets at once, or scripting
  iTOL uploads and exports instead of clicking through the web UI.
---

# iTOL — Annotated Phylogenetic Tree Figures (upload / export pipeline)

## Overview

`scripts/itol_pipeline.py` is an end-to-end wrapper around iTOL (Interactive Tree Of
Life): it uploads a tree plus iTOL annotation files, configures the display, and
exports publication-quality figures (SVG / PDF / PNG) with programmatic legends. It
uses the `itolapi` library when available and falls back to direct HTTP `requests`
otherwise. Companion module `scripts/presets.py` holds the export presets, MTBC
legends, and comparison configurations; `scripts/itol_api_legacy.py` is the older
direct-API client kept for reference.

## Requirements

- An iTOL account with batch/API access (programmatic export needs an iTOL
  subscription).
- `pip install itolapi` (recommended) or `pip install requests` (fallback).
- API key resolved from, in order: `--api-key/-k`, the `ITOL_API_KEY` env var, or
  `~/.config/itol/api_key`.

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

- `DATASET_COLORSTRIP` / `TREE_COLORS` — lineage colour ranges and branch colours.
- `DATASET_SYMBOL` / bootstrap display — node support.
- `DATASET_BINARY` / `DATASET_HEATMAP` — presence/absence (RD, resistance alleles).

Several MTBC skills emit such tracks directly (see Integration). Keep one `.txt` per
track and pass them all to `upload`/`pipeline`.

## Integration with other skills

| Tool | Role |
|---|---|
| `raxml`, `iqtree-lsd2` | produce the `.nwk` tree that iTOL renders |
| `phylogeography`, `resistance-profiler`, `ancestral-reconstruction` | emit iTOL annotation `.txt` tracks (country, AMR, ancestral states) |
| `mtbc-lineages` | lineage colour scheme for the colour-strip track |
| `pastml` | alternative: compressed-tree HTML for ancestral states (no iTOL account needed) |
