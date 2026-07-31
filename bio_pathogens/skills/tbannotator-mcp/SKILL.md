---
name: tbannotator-mcp
description: >-
  Query TBannotator v3.6 MCP server (~255,000 MTBC genomes) via PostgreSQL:
  strain metadata, lineage classifications (default: tblearn; also guyeux [ex-Senelle],
  Coll, Napier, Freschi, Shitikov23, Thawornwattana...), SNP/SPDI
  frequencies, phylogenetic trees (NJ, RAxML), drug resistance. Use when:
  counting strains per lineage, getting metadata for a lineage code, finding
  core-exclusive markers, validating supplementary files, or building trees for
  an MTBC lineage characterisation article.
argument-hint: "<SQL query or question about MTBC strains>"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres, mcp__tbannotator__tool_get_schema, mcp__tbannotator__tool_get_version, mcp__tbannotator__tool_build_nj_tree, mcp__tbannotator__tool_submit_raxml_job
---

# TBannotator MCP Server : Usage Guide

## Overview

The TBannotator MCP server (`tbannotator`) exposes the **TBannotator v3.6 PostgreSQL database** containing ~255,000 MTBC whole-genome sequences (`tb_report_strain`: 255,182; ~250,000 classified). It provides five tools for querying genomic metadata, lineage classifications, SNP markers, phylogenetic analysis, and more.

> **Migré 2026-07-31 vers l'infra IDEEV / Université Paris-Saclay.** Ancien endpoint `darthos.freeboxos.fr` MORT. **13 systèmes de classification** ; le **défaut est désormais `tblearn`** (classifieur ML) ; le système « maison » du groupe a été **renommé `Senelle` → `guyeux`**. Nouveaux systèmes vs anciennes notes : `tblearn`, `Thawornwattana`. Conventions de colonnes du serveur actuel : clé souche = **`strain_id`** (+ `strain_name`), champ système = **`system_name`** (les anciens exemples en `sra_id`/`system` sont périmés).

**MCP Name**: `tbannotator`  
**Endpoint**: `https://tblearn.tbannotator.ideev.universite-paris-saclay.fr/mcp/sse` (SSE transport)

> **Companion server: tbmonitor**, for TB **literature** (PubMed corpus, MeSH, citations, BibTeX) use the `tbmonitor-papers` skill, which targets a separate MCP server (`Tuberculosis Research Papers v3.2.4`, SQLite read-only, ~190 000 PubMed TB abstracts). The two are designed to compose: tbannotator for **genomes/strains**, tbmonitor for the **published literature about those genomes**. Endpoint: `https://tbmonitor.82.64.250.114.nip.io/mcp` (HTTP). Register locally with `claude mcp add --transport http --scope user tbmonitor https://tbmonitor.82.64.250.114.nip.io/mcp` (URL likely to migrate to a permanent domain).

## Détecter une dérive de schéma (outil, `scripts/`)

Une migration serveur casse SILENCIEUSEMENT les exemples SQL des skills (cas réel du 2026-07-31 :
`tb_report_snp` disparue, `dr_type` inexistante, `strain_id` devenu un entier, deux vues
matérialisées présentes mais NON peuplées). Deux scripts rendent la dérive détectable :

```bash
# 1) dumper le schéma courant (nécessite le paquet `mcp` : venv du site annotation_mtbc)
~/docs/codes/mtbc/annotation_mtbc/site/.venv/bin/python scripts/dump_schema.py -o /tmp/schema.csv
# → signale aussi les vues matérialisées NON PEUPLÉES

# 2) auditer tous les SKILL.md contre ce schéma
python3 scripts/check_schema_drift.py --schema-csv /tmp/schema.csv \
    --skills-dir ~/docs/codes/claude_plugins
```

Détecte : objets inexistants, colonnes qualifiées (`alias.col`) inexistantes, vues matérialisées
non peuplées. Ignore les blocs visant une autre base (tbmonitor/SQLite) et les CTE.
**Limite assumée** : ce n'est pas un parseur SQL (colonnes non qualifiées et sous-requêtes non
résolues) → un rapport vide ne prouve pas que les requêtes s'exécutent, seulement qu'aucune
rupture de ce type ne subsiste. Validé le 2026-07-31 : 169 SKILL.md, 0 rupture, et un test
d'injection confirme que le détecteur voit toujours un vrai bug (témoin positif obligatoire).

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
| `mv_strain_metadata` | `strain_id`, `strain_name`, `species_group`, geography (`geo_country`, lat/lon), `collection_date_parsed`, host, antibiogram (`antibiogram_inh/rif/pza/emb`), platform, bioproject |
| `mv_strain_classification` | Lineage assignments per system (`system_name`, `lineage_code`, `lineage_level_1/2`, `confidence_score`). Systems : **tblearn** (défaut, ML), **guyeux** (ex-Senelle, système maison), Napier, Shitikov23, Coll, Freschi, Shuaib, Stucki, Thawornwattana, Shitikov, Coscolla, Palittapongarnpim, Gagneux |
| `mv_spdi_mutations` | par SNP/SPDI : `spdi_variant_name`, `mutation`, `mutation_type`, `strain_count` |
| `mv_protein_position_mutations` | mutations protéiques par gène : `locus_tag`, `hgvs_p`, `impact`, `protein_position`, `strain_count` |
| `mv_protein_effect_diversity` | diversité par gène : `locus_tag`, `mutation_count`, `shannon_diversity`, `simpson_diversity` |
| `mv_lineage_markers` | marqueurs SPDI définissant chaque lignée (`lineage_code`, `spdi_variant_name`, `spdi_variant_position`) |
| `mv_classification_conflicts` | **(nouveau)** souches dont les systèmes désaccordent (`nb_conflicts`, `conflict_level`) |
| `mv_cross_system_classification` | **(nouveau)** accord pairwise entre systèmes par souche |
| `mv_strain_reference_snp_distance` | distance SNP souche↔souches de référence |

#### Example Queries

> Conventions serveur actuel : clé souche = `strain_id` (+ `strain_name`) ; champ système = `system_name` ;
> système par défaut = **`tblearn`** ; système maison = **`guyeux`** (ex-`Senelle`). Filtrer MTB via
> `mv_strain_metadata.species_group = 'M. tuberculosis'`.

**Count strains per lineage (Gagneux system):**
```sql
SELECT lineage_code, COUNT(*) AS n
FROM mv_strain_classification
WHERE system_name = 'Gagneux'
GROUP BY lineage_code
ORDER BY n DESC
LIMIT 20;
```

**Get all L4.15 strains (guyeux system) with metadata:**
```sql
SELECT m.strain_id, m.strain_name, m.geo_country, m.collection_date_parsed,
       m.antibiogram_inh, m.antibiogram_rif
FROM mv_strain_classification c
JOIN mv_strain_metadata m ON m.strain_id = c.strain_id
WHERE c.system_name = 'guyeux' AND c.lineage_code LIKE '4.15%';
```

**Lineage-defining SPDI markers (per system):**
```sql
SELECT lineage_code, spdi_variant_name, spdi_variant_position
FROM mv_lineage_markers
WHERE lineage_code = '4.15';
```

**Most frequent SNPs across strains:**
```sql
SELECT spdi_variant_name, mutation, mutation_type, strain_count
FROM mv_spdi_mutations
ORDER BY strain_count DESC
LIMIT 50;
```

**Per-gene protein mutations (e.g. katG = Rv1908c):**

> ⚠ `mv_protein_position_mutations` et `mv_protein_effect_diversity` **ne sont PAS peuplées** côté serveur
> (`has not been populated`, vérifié 2026-07-31) → passer par les TABLES. Coût ~40 s : filtrer par `locus_tag`.
> Validé : Rv1908c `p.Ser315Thr` = 64 770 souches ; `p.Arg463Leu` = 145 516 (polymorphisme de lignée).

```sql
SELECT a.locus_tag, a.hgvs_p, a.annotation_type,
       COUNT(DISTINCT ss.strain_id) AS n_strains
FROM tb_report_spdi_annotations a
JOIN tb_report_spdi s         ON s.spdi_variant_name = a.spdi_variant_name
JOIN tb_report_strain_spdi ss ON ss.spdi_id = s.spdi_id
WHERE a.locus_tag = 'Rv1908c' AND a.annotation_type = 'missense_variant'
GROUP BY a.locus_tag, a.hgvs_p, a.annotation_type
ORDER BY n_strains DESC
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
  strain_sql = "SELECT strain_id FROM mv_strain_classification WHERE system_name='guyeux' AND lineage_code LIKE '4.15%'",
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
| `strain_sql` | string |, | SQL returning `strain_id` (modes 1 & 3) |
| `snp_matrix_job_id` | int | auto | Completed matrix job ID (auto-resolved) |
| `clustering_job_id` | int |, | Completed clustering job (mode 2) |
| `reference_raxml_job_id` | int |, | Reference tree for contextual placement (mode 3) |
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
  strain_sql = "SELECT strain_id FROM mv_strain_classification WHERE system_name='guyeux' AND lineage_code LIKE '4.15%'",
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
curl -o tree.nwk "https://tblearn.tbannotator.ideev.universite-paris-saclay.fr/mcp/download/tree_newick/{job_id}"
```

Voir aussi le skill `/raxml` pour un workflow guidé complet.

## Classification Systems

The database stores lineage assignments from multiple nomenclature systems:

| System | Field in `mv_strain_classification` (`system_name`) | Souches classées |
|---|---|---|
| **tblearn (défaut, ML)** | `system_name = 'tblearn'` | 248 457 |
| **guyeux (maison, ex-Senelle)** | `system_name = 'guyeux'` | 250 622 |
| Napier et al. 2020 | `system_name = 'Napier'` | 250 592 |
| Shitikov 2023 | `system_name = 'Shitikov23'` | 250 033 |
| Coll et al. 2014 | `system_name = 'Coll'` | 248 771 |
| Freschi et al. 2021 | `system_name = 'Freschi'` | 232 711 |
| Shuaib | `system_name = 'Shuaib'` | 117 269 |
| Stucki et al. 2016 | `system_name = 'Stucki'` | 94 450 |
| Thawornwattana | `system_name = 'Thawornwattana'` | 78 976 |
| Shitikov et al. 2017 | `system_name = 'Shitikov'` | 78 770 |
| Coscolla | `system_name = 'Coscolla'` | 60 048 |
| Palittapongarnpim | `system_name = 'Palittapongarnpim'` | 54 726 |
| Gagneux (broad) | `system_name = 'Gagneux'` | 15 146 |

> **Source de vérité (cf. `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`)** : dans TBannotator, `system_name='guyeux'` (anciennement `'Senelle'`) EST le système maison (= moi/Guyeux), mais c'est un **snapshot** susceptible d'être en retard sur la taxonomie vivante. Pour tout clade récent du cycle multi-signal (L1.\*, Bovis1.\*, BCG.\*, L6 profond), recouper le label avec `bdd/actuelle/` + `barcoding_v2/barcode_complete.tsv`. Ne jamais lire `snp_barcoding.csv` (v1 obsolète) ni `strain_lineages.csv` (périmé) comme référence taxonomique.

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
SELECT COUNT(DISTINCT strain_id)
FROM mv_strain_classification
WHERE system_name = 'guyeux' AND lineage_code LIKE '4.15%';
```

## Important Notes

- The `guyeux` classification system (renamed from `Senelle` on the 2026-07-31 IDEEV migration) corresponds to the TBannotator/Guyeux nomenclature used in L4.11, L4.14, L4.15 articles. The **default** system is now `tblearn` (ML-based).
- Lineage codes in the database may use formats like `4.15` (without `L` prefix). Always verify with `tool_get_schema` or a test query.
- The server is hosted on a personal Freebox; availability may vary.
- Queries are read-only (`SELECT` only). No data modification is possible.
