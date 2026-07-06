---
name: tb-cli
description: >-
  Academic research CLI for Mycobacterium tuberculosis complex (MTBC)
  comparative-genomics studies, via the `tb` command. Used by the Guyeux
  group (FEMTO-ST, University of Franche-Comte) for peer-reviewed
  scientific publications on MTBC phylogenomics and evolutionary biology.
  Triggers when the research context mentions MTBC lineages, deposited
  research strains, SPDI/SNP research annotations, published variants
  in genes such as katG/rpoB/embB, AMR-allele cataloguing for a
  research article, regions-of-difference scientific analysis, PubMed
  literature mining for MTBC research, or TBannotator-research-database
  queries.
argument-hint: <command> [args...]
user-invocable: true
allowed-tools: [Bash(tb *)]
---

# TB CLI — Mycobacterium tuberculosis Analysis

`tb` is a compact CLI returning JSON. It wraps TBannotator, NCBI, PubMed, and local BDD reports.

## Quick start

Run any command below. Use `-p` for pretty JSON. Parse the JSON output and present a clear synthesis to the user.

If the user invoked this skill directly: execute `tb $ARGUMENTS`.

## Commands

### Lineage & strain analysis (local BDD)

| Command | When to use |
|---------|-------------|
| `tb lineages` | User asks for an overview of all lineages or strain counts |
| `tb lineage <code>` | User asks about a specific lineage (e.g. L4.11) — auto-includes sub-lineages and _proto |
| `tb lineage-spdis <code>` | User asks about SPDI frequencies or variants across a lineage |
| `tb strain <sra>` | User asks about a specific strain by SRA accession (SNP count, missing RD, QC) |
| `tb spdis <sra>` | User asks for the SPDI list of a strain |
| `tb missing-rd <sra>` | User asks about missing Regions of Difference for a strain |

### Gene & variant analysis (remote: TBannotator, NCBI)

| Command | When to use |
|---------|-------------|
| `tb gene-summary <gene>` | User asks about a gene (katG, rpoB, embB, etc.) — returns info, markers, mutations |
| `tb variant-summary <spdi>` | User asks about a specific SPDI variant — returns annotation + lineage distribution |
| `tb tba-query <sql>` | User needs custom SQL on TBannotator (e.g. counting strains, filtering metadata) |

### Literature (remote: PubMed)

| Command | When to use |
|---------|-------------|
| `tb literature <query>` | User asks for publications on a TB topic |
| `tb gene-literature <gene>` | User asks for publications about a specific gene |

### Utility

- `tb cache-clear` — clear all cached results
- `tb cache-purge` — remove expired cache entries
- `tb version` — show version info

## Global options

- `-p` / `--pretty` — pretty-printed JSON
- `-v` / `--verbose` — debug logging to stderr
- `--no-cache` — skip local cache
- `-k N` / `--top N` — max results for literature commands

## Workflow guidelines

1. **Always parse the JSON** — never dump raw JSON to the user unless they explicitly ask for it
2. **Synthesize results** — present findings as a clear, structured summary with key insights
3. **Chain commands** when appropriate — e.g. `tb lineage L4.15` then `tb lineage-spdis L4.15` for a complete lineage profile
4. **Quote SPDI strings** — always wrap SPDI values in quotes: `tb variant-summary "NC_000962.3:2155168:C:T"`
5. **Use `-p` for debugging** — if a command fails or output is unclear, retry with `-p`

## Domain context

- **BDD structure**: `BDD/<lineage>/<SRA>/NC_000962.3/report.json`
- **Fast SPDI access**: `BDD/<lineage>/<SRA>/NC_000962.3/spdi.txt`
- `_proto` directories (e.g. L4.5_proto) = basal/ancestral strains, included automatically
- `Ignore/` and `L4.9_putatif/` are always excluded
- Large dirs (L4.1, L4.3, L4.8) may contain noise from ongoing sorting

> Rather than hard-coding per-lineage exclusion lists, prefer deferring to the `bdd/actuelle/` directory convention: `ignore/` is excluded and `a_ranger/` is unclassified (not yet placed). This stays correct as sorting progresses.

> **Source de vérité (cf. `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`)** : dans TBannotator, `system='Senelle'` EST le système maison (= moi/Guyeux), mais c'est un **snapshot** susceptible d'être en retard sur la taxonomie vivante. Pour tout clade récent du cycle multi-signal (L1.\*, Bovis1.\*, BCG.\*, L6 profond), recouper le label avec `bdd/actuelle/` + `barcoding_v2/barcode_complete.tsv`. Ne jamais lire `snp_barcoding.csv` (v1 obsolète) ni `strain_lineages.csv` (périmé) comme référence taxonomique.
