---
name: tbannotator-mcp
description: >-
  Query the tblearn MCP server (successor of TBannotator, ~256,000 MTBC genomes)
  via read-only PostgreSQL: strain metadata, lineage classifications from EIGHT
  EXTERNAL systems (Coll, Coscolla, Freschi, Lipworth, Napier, Palittapongarnpim,
  Shitikov, Stucki), SNP/SPDI frequencies, drug resistance. Use when: counting
  strains per lineage, getting metadata for a lineage code, finding core-exclusive
  markers, or validating supplementary files. WARNING (2026-09-08): the in-house
  classifications (tblearn, guyeux/ex-Senelle) are NO LONGER in this database and a
  query naming them returns zero rows without error; tree building (NJ, RAxML) is
  gone with the old server. See ~/.agents/knowledge/tblearn-migration.md.
argument-hint: "<SQL query or question about MTBC strains>"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres, mcp__tbannotator__tool_get_schema, mcp__tbannotator__tool_submit_accession, mcp__tbannotator__tool_submission_state, mcp__tbannotator__tool_make_a_request, mcp__tbannotator__tool_read_requests
---

> [!WARNING]
> **[2026-09-08] TABLES ABSENTES du serveur tblearn.** Ce skill interroge 4 objet(s) qui
> n'existent plus depuis le remplacement du MCP TBannotator. Contrairement au filtre `system_name`,
> ces requêtes ne rendent pas un ensemble vide : elles **lèvent une erreur** `relation does not exist`.
>
> | table citée ici | remplacer par | fondement |
> |---|---|---|
> | `job_raxml` | **aucun équivalent** | la file de jobs est morte avec le serveur ; passer par `bdd-bridge/scripts/phylo_job.py` |
> | `mv_lineage_markers` | **tb_lineage_marker** | mêmes colonnes (`lineage_code`, `spdi_variant_name`, `lineage_level`, `lineage_parent`, `is_negative`) |
> | `mv_spdi_mutations` | **tb_report_spdi ⋈ tb_report_spdi_annotations sur spdi_id** | le variant dans la première, l'annotation (`locus_tag`, `hgvs_p`, `impact`) dans la seconde |
> | `mv_strain_reference_snp_distance` | **la colonne snp_count de mv_strain_lineage ou tb_report_strain** | commentaire du schéma : « Distance to the H37Rv reference, in number of SNPs » |
>
> Correspondances établies en comparant les colonnes, pas devinées. Détail et schéma complet :
> `~/.agents/knowledge/tblearn-migration.md`.


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


# TBannotator MCP Server : Usage Guide

## Overview

> [!WARNING]
> **Migrated on 2026-09-08 — read `~/.agents/knowledge/tblearn-migration.md` before any query.**
> The historical TBannotator MCP endpoint (`tbannotator.82.64.250.114.nip.io/mcp`) is **dead, HTTP
> 404**. The MCP server keyed `tbannotator` now points to **`tblearn` 4.0.3**, which changes three
> things that silently break old habits:
>
> 1. **Three tools instead of five, as of 2026-09-08.** `tool_query_postgres` and
>    `tool_get_schema` survive; **`tool_build_nj_tree`, `tool_submit_raxml_job` and
>    `tool_get_version` are gone**, so the tree-building paths of this skill and of `raxml` no
>    longer have a server behind them. **Update 2026-09-22 : four more tools appeared**
>    (`tool_submit_accession`, `tool_submission_state`, `tool_make_a_request`,
>    `tool_read_requests` — § « 6-9 » plus bas), portant le total à **sept**. La doc officielle
>    (`https://tblearn.tbannotator.ideev.universite-paris-saclay.fr/docs/`) publie plusieurs
>    versions par semaine côté IDEEV (Clément Lecarpentier) : revérifier `/docs/mcp/` en cas de
>    doute avant de conclure qu'un outil manque.
> 2. **The in-house lineage systems are gone.** The database carries eight systems, all external:
>    Coll, Coscolla, Freschi, Lipworth, Napier, Palittapongarnpim, Shitikov, Stucki. Neither
>    `tblearn` nor `guyeux`/ex-Senelle is among them, and asking for one returns **zero rows with no
>    error**. `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md` remains the authority for
>    in-house lineages; this server is now an *external comparison* source.
> 3. **The query argument is `sql`, not `query`**, and every tool call needs the bearer token
>    (`~/.config/tblearn/token`) even though `initialize` and `tools/list` succeed without it.
>
> The old host still serves a REST API (`/fastapi/openapi.json`, 21 gene-centric endpoints plus
> embeddings and a strain/SPDI matrix builder) which tblearn does not replace.

The `tbannotator` MCP server exposes the **tblearn read-only PostgreSQL database** containing
~256,575 MTBC whole-genome sequences (`tb_report_strain`, measured 2026-09-08). Materialised views
are rebuilt in batch every fifteen minutes and are empty right after a deployment: query `tb_refresh`
(`object_name`, `refreshed_at`, `row_count`) before concluding anything about recently ingested
strains. The schema's own comments carry a standing prohibition worth repeating: lineage, geography,
host and status are **a posteriori validation labels only, and none may enter an inference path**.

> **Migré 2026-07-31 vers l'infra IDEEV / Université Paris-Saclay.** Ancien endpoint `darthos.freeboxos.fr` : **il RÉPOND encore** (vérifié le 2026-09-06, HTTP 200, hôte distinct — Freebox IPv6 contre 129.175.188.8) et sert des données **identiques** (255 182 souches, mêmes bornes, même somme de contrôle sur les noms, `report.json` identique octet pour octet). Ne pas s'y fier pour autant : les deux ne coïncident que parce que la base est **gelée depuis février 2026**, le temps de la reprise de TBannotator par C. Lecarpentier. À la première nouvelle alimentation, un client resté sur l'ancien hôte lira des données périmées **sans aucune erreur**. Un point unique de configuration existe côté dépôt : `mtbc/investigate_phylo/tbannotator_endpoint.py` (variable `TBANNOTATOR_MCP_URL`). **13 systèmes de classification** ; le **défaut est désormais `tblearn`** (classifieur ML) ; le système « maison » du groupe a été **renommé `Senelle` → `guyeux`**. Nouveaux systèmes vs anciennes notes : `tblearn`, `Thawornwattana`. Conventions de colonnes du serveur actuel : clé souche = **`strain_id`** (+ `strain_name`), champ système = **`system_name`** (les anciens exemples en `sra_id`/`system` sont périmés).

**MCP Name**: `tbannotator`  
**Endpoint**: `https://tblearn.tbannotator.ideev.universite-paris-saclay.fr/mcp/sse` (SSE transport)

> **Companion server: tbmonitor**, for TB **literature** (PubMed corpus, MeSH, citations, BibTeX) use the `tbmonitor-papers` skill, which targets a separate MCP server (`Tuberculosis Research Papers v3.2.4`, SQLite read-only, ~190 000 PubMed TB abstracts). The two are designed to compose: tbannotator for **genomes/strains**, tbmonitor for the **published literature about those genomes**. Endpoint: `https://tbmonitor.82.64.250.114.nip.io/mcp` (HTTP). Register locally with `claude mcp add --transport http --scope user tbmonitor https://tbmonitor.82.64.250.114.nip.io/mcp` (URL likely to migrate to a permanent domain).

## Détecter une dérive de schéma (outil, `scripts/`)

Une migration serveur casse SILENCIEUSEMENT les exemples SQL des skills (cas réel du 2026-07-31 :
`tb_report_snp` disparue, `dr_type` inexistante, `strain_id` devenu un entier, deux vues
matérialisées présentes mais NON peuplées). Deux scripts rendent la dérive détectable :

```bash
# 1) dumper le schéma courant (nécessite le paquet `mcp` : venv du site annotation_mtbc)
~/docs/codes/mtbc/en_cours/annotation_mtbc/site/.venv/bin/python scripts/dump_schema.py -o /tmp/schema.csv
# → signale aussi les vues matérialisées NON PEUPLÉES

# 2) auditer tous les SKILL.md contre ce schéma
python3 scripts/check_schema_drift.py --schema-csv /tmp/schema.csv \
    --skills-dir ~/docs/environnement/plugins
```

Détecte : objets inexistants, colonnes qualifiées (`alias.col`) inexistantes, vues matérialisées
non peuplées. Ignore les blocs visant une autre base (tbmonitor/SQLite) et les CTE.
**Limite assumée** : ce n'est pas un parseur SQL (colonnes non qualifiées et sous-requêtes non
résolues) → un rapport vide ne prouve pas que les requêtes s'exécutent, seulement qu'aucune
rupture de ce type ne subsiste. Validé le 2026-07-31 : 169 SKILL.md, 0 rupture, et un test
d'injection confirme que le détecteur voit toujours un vrai bug (témoin positif obligatoire).

## Available Tools

### 1. `tool_get_version` — SUPPRIMÉ, ne pas utiliser

Gone since the 2026-09-08 migration (cf. banner above). No direct replacement is needed:
`tool_get_schema` and a trivial `tool_query_postgres` call both prove connectivity.

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

### 4-5. `tool_build_nj_tree` / `tool_submit_raxml_job` — SUPPRIMÉS, ne pas utiliser

Ces deux outils n'existent plus depuis la migration du 2026-09-08 (cf. bandeau en tête de ce
fichier) : le serveur `tblearn` n'expose que la lecture SQL et, depuis le 2026-09-22, la
soumission d'accessions et de demandes (§ ci-dessous). La construction d'arbre passe désormais
par `bdd-bridge/scripts/phylo_job.py` (`align`, `run`, `submit`), local ou en paquet SLURM
portable pour `mh` — voir le skill `/raxml`, entièrement réécrit pour cette voie.

### 6. `tool_submit_accession` (nouveau, 2026-09-22)

Met en file une accession INSDC publique (run, sample, study ou project) pour ingestion par le
pipeline tblearn — équivalent conversationnel de `POST /api/v1/submissions/accession`. Aucun
quota documenté pour les accessions publiques (le plafond `MAX_STRAINS=10` du changelog 0.17 vise
la file de fond des dépôts personnalisés, pas ce chemin). Une accession publique ne demande aucun
secret et devient consultable par tous une fois traitée. Usage : demander l'ajout à la base
partagée d'un génome public absent de `tb_report_strain`, plutôt que de laisser une analyse
reposer sur un sous-ensemble incomplet sans le signaler.

### 7. `tool_submission_state` (nouveau, 2026-09-22)

Suit l'état d'une soumission (accession ou dépôt de rapport) à travers les sessions. À appeler
après `tool_submit_accession` pour savoir si l'ingestion est terminée avant d'interroger la
souche par `tool_query_postgres`.

### 8-9. `tool_make_a_request` / `tool_read_requests` (nouveaux, 2026-09-22)

Déposent et relisent une demande de fonctionnalité ou de correction auprès de l'équipe tblearn
(table `tb_request`). À réserver à un vrai besoin de fonctionnalité côté serveur, pas à un
usage exploratoire — la demande est visible de l'équipe qui maintient le serveur.

Détail complet et pointeur vers la doc officielle (`/docs/`, mise à jour régulièrement côté
IDEEV) : `~/.agents/knowledge/tblearn-migration.md`, section « Quatre nouveaux outils MCP ».

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

## PIÈGE MAJEUR : `host` est du texte libre non harmonisé (mesuré le 2026-08-10)

`mv_strain_metadata.host` porte **252 valeurs distinctes** pour 165 511 souches, recopiées
telles quelles depuis les BioSample. Filtrer sur le binôme canonique **rate silencieusement
la moitié de la cible** :

```sql
-- ce que l'on écrit spontanément
WHERE host = 'Bos taurus'                    -->  4 728 souches
-- ce qui est réellement bovin
WHERE host ILIKE ANY(ARRAY['%bos taurus%','%cattle%','%bovine%','%cow%',
                           '%calf%','%heifer%','%bull%'])   -->  8 261 souches, 14 étiquettes
```

**43 % des souches bovines manquent** avec le filtre canonique. Les étiquettes réelles
incluent `Cattle` (1 639), `Bovine` (792), `BOVINE` (351), `Dairy cattle` (337), `cattle`
(128), `Cow` (121). Même fragmentation ailleurs : `Homo sapiens` / `Homo sapiens sapiens`
(2 258) / `Human/Culture` (233) / `Homosapiens` (183) / `"""Homo sapiens` (126, guillemets
parasites) ; blaireau réparti sur `Meles meles` (196) / `BADGER` (195) / `Badger` (124) ;
cervidés sur `Deer` (133) / `Cervid` (105).

C'est la pire classe d'erreur : **la requête aboutit, le résultat est plausible, et il est
faux**. Elle touche directement toute analyse hôte-spécifique (`animal_vs_human`,
`convergent-evolution`, `tissue-tropism-mtbc`, `coevolution`).

Règle : **ne jamais filtrer `host` par égalité.** Toujours (a) lister d'abord les valeurs
présentes (`GROUP BY host ORDER BY count(*) DESC`), (b) construire un `ILIKE ANY(...)`
couvrant les variantes de casse, les noms vernaculaires et les binômes, (c) rapporter le
nombre d'étiquettes agrégées dans le manuscrit. Le même contrôle vaut pour
`isolation_source`.

## Important Notes

- The `guyeux` classification system (renamed from `Senelle` on the 2026-07-31 IDEEV migration) corresponds to the TBannotator/Guyeux nomenclature used in L4.11, L4.14, L4.15 articles. The **default** system is now `tblearn` (ML-based).
- Lineage codes in the database may use formats like `4.15` (without `L` prefix). Always verify with `tool_get_schema` or a test query.
- The server is hosted on a personal Freebox; availability may vary.
- Queries are read-only (`SELECT` only). No data modification is possible.
