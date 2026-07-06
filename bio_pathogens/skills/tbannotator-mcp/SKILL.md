---
name: tbannotator-mcp
description: >-
  Query TBannotator v3.6 MCP server (~274,800 MTBC genomes) via PostgreSQL.
  Access strain metadata, lineage classifications (Coll, Gagneux, Senelle...),
  SNP/SPDI frequencies, phylogenetic trees (NJ, RAxML), drug resistance profiles.

  Use when: counting strains per lineage, getting metadata for a lineage code,
  finding core-exclusive markers, validating supplementary files, or building
  phylogenetic trees for an MTBC lineage characterisation article.
argument-hint: "<SQL query or question about MTBC strains>"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres, mcp__tbannotator__tool_get_schema, mcp__tbannotator__tool_get_version, mcp__tbannotator__tool_build_nj_tree, mcp__tbannotator__tool_submit_raxml_job
---

# TBannotator MCP Server — Usage Guide

## Overview

The TBannotator MCP server (`tbannotator`) exposes the **TBannotator v3.6 PostgreSQL database** containing ~274,800 MTBC whole-genome sequences. It provides five tools for querying genomic metadata, lineage classifications, SNP markers, phylogenetic analysis, and more.

**MCP Name**: `tbannotator`  
**Endpoint**: `https://darthos.freeboxos.fr/mcp/sse` (SSE transport)

> **Companion server: tbmonitor** — for TB **literature** (PubMed corpus, MeSH, citations, BibTeX) use the `tbmonitor-papers` skill, which targets a separate MCP server (`Tuberculosis Research Papers v3.2.4`, SQLite read-only, ~190 000 PubMed TB abstracts). The two are designed to compose: tbannotator for **genomes/strains**, tbmonitor for the **published literature about those genomes**. Endpoint: `https://tbmonitor.82.64.250.114.nip.io/mcp` (HTTP). Register locally with `claude mcp add --transport http --scope user tbmonitor https://tbmonitor.82.64.250.114.nip.io/mcp` (URL likely to migrate to a permanent domain).

## Available Tools

### 1. `tool_get_version`
Returns the server version. Use to verify connectivity.

### 2. `tool_get_schema`
Returns the full database schema (tables, views, columns, constraints). **Use this first** when exploring the database structure.

### 3. `tool_query_postgres`
Execute read-only SQL (`SELECT`) queries on the database. This is the primary data access tool.

#### Key Materialized Views

| View | Description |
|---|---|
| `mv_strain_metadata` | Geography, collection date, antibiogram, spoligotype, IS6110, etc. |
| `mv_strain_classification` | Lineage assignments by multiple systems (Coll, Gagneux, Shitikov, Freschi, Napier, Stucki, TBannotator/Senelle) |
| `mv_spdi_mutations` | SNP/SPDI frequencies across strains |
| `mv_lineage_markers` | Core-exclusive markers per lineage |
| `mv_protein_effect_diversity` | Shannon/Simpson diversity per gene |

#### Example Queries

**Count strains per lineage (Gagneux system):**
```sql
SELECT lineage_code, COUNT(*) as n
FROM mv_strain_classification
WHERE system = 'Gagneux'
GROUP BY lineage_code
ORDER BY n DESC
LIMIT 20;
```

**Get all L4.15 strains with metadata:**
```sql
SELECT m.sra_id, m.country, m.collection_date, m.dr_type
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.sra_id = c.sra_id
WHERE c.system = 'Senelle' AND c.lineage_code = '4.15';
```

**Find core-exclusive markers for a lineage:**
```sql
SELECT * FROM mv_lineage_markers
WHERE lineage = 'L4.15' AND marker_type = 'core_exclusive';
```

**Check SPDI mutation frequency in a lineage:**
```sql
SELECT spdi, gene, effect, frequency
FROM mv_spdi_mutations
WHERE lineage = 'L4.15'
ORDER BY frequency DESC
LIMIT 50;
```

### 4. `tool_build_nj_tree`

Build a Neighbor-Joining tree in memory. Fast (minutes) but less accurate than RAxML. Good for exploratory validation before launching a long RAxML job.

**Parameters:**

| Paramètre | Type | Default | Description |
|-----------|------|---------|-------------|
| `strain_sql` | string | (requis) | SQL query returning a `strain_id` column |
| `max_strains` | int | 5000 | Maximum strains (NJ is O(n³)) |
| `remove_invariant` | bool | true | Remove invariant SNP positions before distance computation |

**Retour** : Newick string.

**Exemple :**
```
tool_build_nj_tree(
  strain_sql = "SELECT sra_id AS strain_id FROM mv_strain_classification WHERE system='Senelle' AND lineage_code LIKE '4.15%'",
  max_strains = 5000,
  remove_invariant = true
)
```

### 5. `tool_submit_raxml_job`

Submit an asynchronous RAxML-NG phylogenetic inference job. Returns a `job_id` immediately; poll status via `tool_query_postgres`.

**Modes d'opération :**

| Mode | Paramètres clés | Cas d'usage |
|------|----------------|-------------|
| 1 (Matrix) | `strain_sql` + `model` | Phylogénie standard d'une lignée |
| 2 (Clustering) | `clustering_job_id` | Gros jeux (>5000 souches) |
| 3 (Contextual) | `strain_sql` + `reference_raxml_job_id` | Placement sur arbre existant |

**Parameters:**

| Paramètre | Type | Default | Description |
|-----------|------|---------|-------------|
| `strain_sql` | string | — | SQL returning `strain_id` (modes 1 & 3) |
| `snp_matrix_job_id` | int | auto | Completed matrix job ID (auto-resolved) |
| `clustering_job_id` | int | — | Completed clustering job (mode 2) |
| `reference_raxml_job_id` | int | — | Reference tree for contextual placement (mode 3) |
| `model` | string | `GTR+G` | Evolution model |
| `starting_trees` | string | `pars{2},rand{2}` | Starting tree strategy |
| `raxml_timeout` | int | 604800 | Timeout in seconds (7 days) |
| `seed` | int | 42 | Random seed |
| `filter_variants` | list | `['all']` | `all`, `no_core0`, `no_core0_excl0`, `no_char0` |
| `use_clustering` | bool | true | Pre-cluster query strains (mode 3) |
| `hdbscan_min_cluster_size` | int | 50 | HDBSCAN param (mode 2/3) |
| `hdbscan_min_samples` | int | 10 | HDBSCAN param (mode 2/3) |
| `cluster_selection_epsilon` | float | 0.5 | HDBSCAN param (mode 2/3) |
| `max_query_strains` | int | 1000 | Max query strains (mode 3) |

**Exemple Mode 1 (standard) :**
```
tool_submit_raxml_job(
  strain_sql = "SELECT sra_id AS strain_id FROM mv_strain_classification WHERE system='Senelle' AND lineage_code LIKE '4.15%'",
  model = "GTR+G",
  starting_trees = "pars{2},rand{2}",
  seed = 42
)
```

**Polling du statut :**
```sql
SELECT id, status, strain_count, snp_count, model,
       created_at, started_at, completed_at, error_message
FROM job_raxml WHERE id = {job_id};
```

| Status | Signification |
|--------|--------------|
| `pending` | En attente |
| `building_matrix` | Construction matrice SNP |
| `running` | RAxML-NG en cours |
| `completed` | Terminé → télécharger le Newick |
| `failed` | Erreur (voir `error_message`) |

**Téléchargement du Newick :**
```bash
curl -o tree.nwk "https://darthos.freeboxos.fr/mcp/download/tree_newick/{job_id}"
```

Voir aussi le skill `/raxml` pour un workflow guidé complet.

## Classification Systems

The database stores lineage assignments from multiple nomenclature systems:

| System | Field in `mv_strain_classification` |
|---|---|
| TBannotator (Guyeux/Senelle) | `system = 'Senelle'` |
| Coll et al. 2014 | `system = 'Coll'` |
| Stucki et al. 2016 | `system = 'Stucki'` |
| Freschi et al. 2021 | `system = 'Freschi'` |
| Napier et al. 2020 | `system = 'Napier'` |
| Shitikov et al. 2017 | `system = 'Shitikov'` |
| Gagneux (broad) | `system = 'Gagneux'` |

> **Source de vérité (cf. `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`)** : dans TBannotator, `system='Senelle'` EST le système maison (= moi/Guyeux), mais c'est un **snapshot** susceptible d'être en retard sur la taxonomie vivante. Pour tout clade récent du cycle multi-signal (L1.\*, Bovis1.\*, BCG.\*, L6 profond), recouper le label avec `bdd/actuelle/` + `barcoding_v2/barcode_complete.tsv`. Ne jamais lire `snp_barcoding.csv` (v1 obsolète) ni `strain_lineages.csv` (périmé) comme référence taxonomique.

## Common Workflows

### Lineage Characterisation Article
1. **Identify strains**: Query `mv_strain_classification` for all strains of the target lineage
2. **Get metadata**: Join with `mv_strain_metadata` for geography, DR, collection dates
3. **Find markers**: Query `mv_lineage_markers` for core-exclusive SPDIs
4. **Validate counts**: Cross-check strain counts against manuscript figures
5. **Build tree**: Use `tool_build_nj_tree` or `tool_submit_raxml_job`

### Cross-Validating Supplementary Files
Use SQL queries to validate CSV files (e.g., `snp_barcoding.csv`, `strain_lineages.csv`) against the live database. Attention : ces deux CSV ne sont PAS la référence taxonomique courante ; pour la vérité taxonomique vivante, comparer contre `barcoding_v2/barcode_complete.tsv` (cf. note en section *Classification Systems*), pas contre `snp_barcoding.csv` (v1 obsolète) ni `strain_lineages.csv` (périmé).
```sql
-- Verify strain count for a lineage
SELECT COUNT(DISTINCT sra_id)
FROM mv_strain_classification
WHERE system = 'Senelle' AND lineage_code LIKE '4.15%';
```

## Important Notes

- The `Senelle` classification system corresponds to the TBannotator/Guyeux nomenclature used in L4.11, L4.14, L4.15 articles.
- Lineage codes in the database may use formats like `4.15` (without `L` prefix). Always verify with `tool_get_schema` or a test query.
- The server is hosted on a personal Freebox; availability may vary.
- Queries are read-only (`SELECT` only). No data modification is possible.
