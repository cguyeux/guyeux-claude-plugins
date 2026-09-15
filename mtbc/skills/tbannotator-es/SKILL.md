---
name: tbannotator-es
description: >-
  Academic research database client for the TBannotator Elasticsearch indices
  (strain, snp, gene, is, rd) used in peer-reviewed MTBC phylogenomics by the
  Guyeux group (FEMTO-ST). Exposes fields absent from the PostgreSQL server:
  CRISPR spacer statistics, fastp quality and mapping metrics, missing genes and
  regions of difference with coverage, insertion sequences, published
  antimicrobial-resistance allele annotations with source DOI, and sample
  metadata (coordinates, host, isolation source, BioProject). Also reproduces the
  web interface's clade-exclusivity score. Use when: looking for markers
  exclusive to a clade, filtering published research isolates on sequencing
  quality, or querying IS/RD/CRISPR content of strains.
argument-hint: "<question ou requete Elasticsearch>"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# TBannotator Elasticsearch : accès en lecture

## Ne pas confondre trois sources

| Source | Skill | Contenu |
|---|---|---|
| PostgreSQL v3.6 (IDEEV) | `tbannotator-mcp` | ~255 000 souches, 13 systèmes de classification de lignées, arbres NJ/RAxML |
| Elasticsearch (webapp) | **ce skill** | mêmes souches, mais champs de terrain : QC, couverture, CRISPR, IS, RD, résistances sourcées, métadonnées d'échantillon |
| SQLite littérature | `tbmonitor-papers` | ~190 000 résumés PubMed TB |

> [!WARNING]
> **Un résultat vide ici ne veut pas dire « absent de TBannotator ».** Les deux
> bases sont alimentées par des chaînes différentes et désynchronisent, comme
> `mp` et le serveur HTTP dans `fetch-tbannotator`. Croiser avant de conclure.

## État de l'accès (à vérifier avant de s'en servir)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/tbannotator-es/scripts/tbannotator_es_mcp.py --selftest
```

Au 2026-08-17 ce test **échoue** : le cluster n'est pas exposé. Le nginx de
l'instance (`https://tbannotator.82.64.250.114.nip.io`) ne route que `/` vers la
webapp Remix et `/fastapi/` vers l'API ; Elasticsearch écoute en interne. Deux
déblocages possibles :

1. **Exposition en lecture côté serveur.** Le rôle `readonly` (privilège `read`
   sur tous les indices, plus `monitor`) est déjà défini dans
   `compose/es_entrypoint/roles.yml` du dépôt amont : la lecture externe est
   prévue par conception, il ne manque qu'une route nginx et un identifiant
   propre. C'est une question à poser à Clément Lecarpentier, pas un
   développement.
2. **Tunnel SSH** vers l'hôte du cluster, puis `TBANNOTATOR_ES_URL=https://127.0.0.1:<port_local>`.

Tant qu'aucun des deux n'existe, ce skill ne peut rien produire, et c'est
préférable à des chiffres inventés.

## Configuration

Aucun secret dans le dépôt. Renseigner `~/.config/tbannotator_es.env` (chmod 600) :

```
TBANNOTATOR_ES_URL=https://127.0.0.1:9200
TBANNOTATOR_ES_USER=readonly
TBANNOTATOR_ES_PASSWORD=...
TBANNOTATOR_ES_INSECURE=1
```

`TBANNOTATOR_ES_INSECURE=1` est nécessaire tant que le déploiement utilise un
certificat auto-signé. Ne jamais réutiliser un identifiant lu dans les dépôts
publics du groupe : ceux qui y traînent sont à considérer comme compromis.

## Deux modes

**Serveur MCP** (cinq outils : `es_health`, `es_search`, `es_get`,
`es_aggregate`, `es_exclusivity`) :

```bash
claude mcp add --scope user tbannotator-es -- ~/docs/codes/mtbc/annotation_mtbc/site/.venv/bin/python ${CLAUDE_PLUGIN_ROOT}/skills/tbannotator-es/scripts/tbannotator_es_mcp.py
```

Le venv du site est nécessaire uniquement pour le mode serveur (paquet `mcp`).

**CLI de secours**, bibliothèque standard seule, utile pour un test ponctuel ou
depuis un cluster :

```bash
python3 scripts/tbannotator_es_mcp.py --selftest
python3 scripts/tbannotator_es_mcp.py --get strain SRR1234567
python3 scripts/tbannotator_es_mcp.py --agg strain lineages.lineageNames --size 30
python3 scripts/tbannotator_es_mcp.py --exclusivity '{"term": {"lineages.lineageNames": "L6.1.1"}}'
```

## Champs qui justifient ce skill

Le document `strain` porte, en plus des lignées et des SNP :

- `crisprStats` par locus (couverture, profondeur, qualité) : matière directe
  pour `crispr-spacer-null` et le spoligotypage in silico ;
- `quality.afterFiltering` (sortie fastp complète) et `mappingStats`
  (profondeur moyenne, % bases couvertes, MAPQ) : critères de tri pour
  `strain-qc`, appliqués en agrégation sur des dizaines de milliers de souches ;
- `missingGenes` et `missingRegionsOfDifference` avec `percentMissing`,
  `meanCoverage`, `quality` : délétions avec leur niveau de preuve, pas un
  simple booléen ;
- `insertionSequences` avec `highQuality`, position et orientation ;
- `resistances` et `phenotypicResistances` avec `drug`, `source`, `sourceDoi`,
  `isPhenotypic` : permet de séparer génotypique et phénotypique, et de remonter
  à l'article ;
- `run.samples[]` : `coordinates`, `collectedAt`, `host`, `hostHiv`,
  `isolationSource`, plus `experiment.study.bioProjectId` : de quoi alimenter
  `geo-map` et `bioproject-scout` sans repasser par l'ENA.

## Exclusivité de clade : ce que le score veut dire

`es_exclusivity` reproduit exactement le calcul de l'interface web : quatre
agrégations `significant_terms` en une passe, sur `snps.spdi`,
`missingGenes.gene.id`, `insertionSequences.id` et
`missingRegionsOfDifference.id`, avec l'heuristique painless
`subset_freq / (superset_freq - subset_freq + subset_size)`.

Le score vaut 1 pour un marqueur présent dans tout le sous-ensemble et nulle
part ailleurs, et décroît avec le nombre de porteurs extérieurs.

> [!WARNING]
> **Trois pièges avant de publier un chiffre issu d'ici.** Ce n'est pas une
> p-valeur, donc pas de correction de tests multiples à invoquer, mais pas de
> significativité à revendiquer non plus. `min_doc_count = 1` (choix du front,
> conservé pour comparabilité) fait remonter des singletons : filtrer sur
> `in_set_count`. Surtout, le fond de comparaison par défaut est l'ensemble des
> souches ayant le champ ; « exclusif au sein de la lignée » exige de passer le
> clade parent en `background_ids`, sinon on mesure un artefact de cadrage.

Comparer systématiquement le résultat aux marqueurs déjà connus de la lignée
(`mtbc-lineages`, `pectinated-subclade-mining`) avant d'annoncer une nouveauté.

## Dérive amont

Les noms de champs viennent du front, qui évolue hors de notre contrôle. Lancer
`tbannotator-upstream` en cas de résultat vide inattendu : une agrégation sur un
champ renommé renvoie zéro bucket sans lever d'erreur.
