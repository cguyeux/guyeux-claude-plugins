---

name: tb-cli
description: >-
  Academic research CLI (Guyeux group, FEMTO-ST) for peer-reviewed
  Mycobacterium tuberculosis complex (MTBC) comparative-genomics and
  phylogenomics work, via the `tb` command (JSON; wraps TBannotator, NCBI,
  PubMed, BDD). Use when: MTBC lineages, research strains by SRA, SPDI/SNP
  annotations, published variants in katG/rpoB/embB, AMR-allele cataloguing
  for an article, regions-of-difference analysis, PubMed mining, or
  TBannotator queries.
allowed-tools: [Bash(tb *)]
---

> [!WARNING]
> **[2026-09-08] Les requêtes de ce skill qui filtrent sur un système de lignée MAISON ne rendent
> plus rien.** Le MCP TBannotator est arrêté ; le serveur `tblearn` qui le remplace ne porte que
> huit systèmes **externes** (Coll, Coscolla, Freschi, Lipworth, Napier, Palittapongarnpim,
> Shitikov, Stucki). `system_name = 'guyeux'` et `system_name = 'tblearn'` y rendent **zéro ligne
> sans lever d'erreur**, ce qu'un script lira comme « aucune souche ne satisfait le critère ».
>
> **Substitution, décidée le 2026-09-08 :** les lignées maison se lisent désormais dans la base
> LOCALE `bdd/actuelle/`, qui fait déjà autorité selon
> `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`, via le skill `bdd-bridge` :
>
> ```bash
> B=~/docs/environnement/plugins/mtbc/skills/bdd-bridge/scripts
> export TBANNOTATOR_BDD=~/docs/codes/mtbc/bdd
> python3 $B/bdd_query.py clades                # tous les clades et leurs effectifs
> python3 $B/bdd_query.py denominator <clade>   # effectif réellement exploitable
> python3 $B/bdd_query.py strains <clade>       # souches d'un clade
> ```
>
> `tblearn` reste utilisable pour tout le reste (SPDI, QC, métadonnées, RD, IS, CRISPR) et pour
> **comparer** à une taxonomie externe, mais ce n'est plus la source des lignées maison. Toute
> requête qui filtre sur `system_name` doit d'abord vérifier que le filtre a matché :
> `SELECT system_name, count(*) FROM mv_strain_lineage WHERE system_name = '<x>' GROUP BY 1;`
> — zéro ligne signifie « ce système n'existe pas ici », jamais « aucune souche ».
>
> Détail complet : `~/.agents/knowledge/tblearn-migration.md`.


# TB CLI : Mycobacterium tuberculosis Analysis

`tb` is a compact CLI returning JSON. It wraps TBannotator, NCBI, PubMed, and local BDD reports.

## Quick start

Run any command below. Use `-p` for pretty JSON. Parse the JSON output and present a clear synthesis to the user.

If the user invoked this skill directly: execute `tb $ARGUMENTS`.

## Commands

### Lineage & strain analysis (local BDD)

| Command | When to use |
|---------|-------------|
| `tb lineages` | User asks for an overview of all lineages or strain counts |
| `tb lineage <code>` | User asks about a specific lineage (e.g. L4.11), auto-includes sub-lineages and _proto |
| `tb lineage-spdis <code>` | User asks about SPDI frequencies or variants across a lineage |
| `tb strain <sra>` | User asks about a specific strain by SRA accession (SNP count, missing RD, QC) |
| `tb spdis <sra>` | User asks for the SPDI list of a strain |
| `tb missing-rd <sra>` | User asks about missing Regions of Difference for a strain |

### Gene & variant analysis (remote: TBannotator, NCBI)

| Command | When to use |
|---------|-------------|
| `tb gene-summary <gene>` | User asks about a gene (katG, rpoB, embB, etc.), returns info, markers, mutations |
| `tb variant-summary <spdi>` | User asks about a specific SPDI variant, returns annotation + lineage distribution |
| `tb tba-query <sql>` | User needs custom SQL on TBannotator (e.g. counting strains, filtering metadata) |

### Literature (remote: PubMed)

| Command | When to use |
|---------|-------------|
| `tb literature <query>` | User asks for publications on a TB topic |
| `tb gene-literature <gene>` | User asks for publications about a specific gene |

### Utility

- `tb cache-clear`, clear all cached results
- `tb cache-purge`, remove expired cache entries
- `tb version`, show version info

## Global options

- `-p` / `--pretty`, pretty-printed JSON
- `-v` / `--verbose`, debug logging to stderr
- `--no-cache`, skip local cache
- `-k N` / `--top N`, max results for literature commands

## Workflow guidelines

1. **Always parse the JSON**, never dump raw JSON to the user unless they explicitly ask for it
2. **Synthesize results**, present findings as a clear, structured summary with key insights
3. **Chain commands** when appropriate, e.g. `tb lineage L4.15` then `tb lineage-spdis L4.15` for a complete lineage profile
4. **Quote SPDI strings**, always wrap SPDI values in quotes: `tb variant-summary "NC_000962.3:2155168:C:T"`
5. **Use `-p` for debugging**, if a command fails or output is unclear, retry with `-p`

## Domain context

- **BDD structure**: `BDD/<lineage>/<SRA>/NC_000962.3/report.json`
- **Fast SPDI access**: `BDD/<lineage>/<SRA>/NC_000962.3/spdi.txt`
- `_proto` directories (e.g. L4.5_proto) = basal/ancestral strains, included automatically
- `Ignore/` and `L4.9_putatif/` are always excluded
- Large dirs (L4.1, L4.3, L4.8) may contain noise from ongoing sorting

> Rather than hard-coding per-lineage exclusion lists, prefer deferring to the `bdd/actuelle/` directory convention: `ignore/` is excluded and `a_ranger/` is unclassified (not yet placed). This stays correct as sorting progresses.

> **Source de vérité (cf. `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`)** : dans TBannotator, `system_name='guyeux' (ex-'Senelle')` EST le système maison (= moi/Guyeux), mais c'est un **snapshot** susceptible d'être en retard sur la taxonomie vivante. Pour tout clade récent du cycle multi-signal (L1.\*, Bovis1.\*, BCG.\*, L6 profond), recouper le label avec `bdd/actuelle/` + `barcoding_v2/barcode_complete.tsv`. Ne jamais lire `snp_barcoding.csv` (v1 obsolète) ni `strain_lineages.csv` (périmé) comme référence taxonomique.

## Codex packaging note

This packaged copy targets Codex. MCP tool names in `allowed-tools` are prerequisites: verify them with `codex mcp list` in the active profile before relying on live queries.
