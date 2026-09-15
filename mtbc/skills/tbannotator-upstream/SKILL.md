---
name: tbannotator-upstream
description: >-
  Academic research tooling: watch the upstream public GitLab of the TBannotator
  webapp (gitlab.com/tbannotator/webapp) for changes that would silently
  invalidate our MTBC skills: repository commits, live FastAPI routes,
  Elasticsearch document schema, and the definition of the clade-exclusivity
  score. Peer-reviewed phylogenomics context, Guyeux group (FEMTO-ST). Use when:
  a TBannotator query returns unexpectedly empty results, before relying on the
  Elasticsearch field names in an analysis, or to review what changed upstream
  since the last pinned state.
argument-hint: "[--pin] [--json]"
user-invocable: true
allowed-tools: Bash, Read, Edit, Grep, WebFetch
---

# Veille sur le GitLab amont de TBannotator

## Ce que ce skill surveille, et pourquoi

La plateforme web TBannotator (thèse de Clément Lecarpentier) est développée
hors de ce dépôt, dans le sous-groupe **public** `gitlab.com/tbannotator/webapp`
(quatre dépôts : `remix_app`, `fastapi`, `helm`, `compose`). Plusieurs de nos
skills MTBC encodent des hypothèses sur cette plateforme : noms d'indices
Elasticsearch, champs des documents `strain`, routes de l'API, et surtout la
définition du score d'exclusivité.

> [!WARNING]
> **Une dérive amont ne provoque pas d'erreur, elle produit un faux résultat
> biologique.** Une requête sur un champ renommé renvoie zéro document, ce qui
> se lit comme « aucun marqueur exclusif à ce clade » alors que c'est un bug de
> schéma. C'est le même piège que la migration PostgreSQL du 2026-07-31
> (`tb_report_snp` disparue), détecté après coup. Ici, on le détecte avant.

## Usage

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/tbannotator-upstream/scripts/check_upstream.py
python3 ${CLAUDE_PLUGIN_ROOT}/skills/tbannotator-upstream/scripts/check_upstream.py --pin
```

Sans argument : compare l'amont à l'état épinglé dans
`references/upstream_pinned.json`. Codes de sortie : `0` inchangé, `1` dérive
détectée, `2` amont injoignable ou référence absente (ne **pas** lire un `2`
comme un `0`). Avec `--pin` : réécrit la référence, à faire seulement après
avoir lu le rapport de dérive et corrigé les skills concernés, sinon on efface
la trace de ce qui a bougé. Le fichier épinglé est versionné, son diff Git est
le journal des évolutions de la plateforme.

Aucun jeton ni clé SSH : les quatre dépôts sont publics et le script n'utilise
que la bibliothèque standard.

## Quatre signaux, du plus grossier au plus fin

1. **Dépôts du groupe** : apparition, disparition, passage en privé.
2. **SHA de tête** de chaque dépôt, avec titre et date du commit.
3. **Routes de l'instance vivante**, lues dans son `openapi.json`. Détecte un
   endpoint ajouté ou retiré sans rien cloner. Attention : l'inventaire OpenAPI
   ne dit rien du bon fonctionnement (voir « État connu » ci-dessous).
4. **Schéma des documents ES**, extrait des `interface` TypeScript de
   `remix_app/app/utils/elasticsearch.server.ts`, plus les indices interrogés,
   les quatre champs agrégés pour l'exclusivité, et le script painless du score.

Le signal 4 est le seul qui casse silencieusement des analyses ; les trois
autres sont du contexte pour l'interpréter.

## Où vit la vérité du schéma

Le mapping Elasticsearch lui-même **n'est dans aucun de ces quatre dépôts** :
l'indexation est faite par le pipeline C# Dataflow (chaîne Senelle), ailleurs.
Le front est donc la source de vérité la plus lisible sur la forme réelle des
documents, d'où l'extraction depuis le TypeScript plutôt que depuis un mapping.
Si un jour le mapping est publié, le surveiller à la place.

## État connu au 2026-08-17 (première mise en place)

- Instance vivante : `https://tbannotator.82.64.250.114.nip.io`, API ouverte
  sans authentification sous `/fastapi/`, 21 routes, certificat auto-signé.
- Cinq indices : `strain`, `snp`, `gene`, `is`, `rd`.
- Exclusivité = `significant_terms` sur `snps.spdi`, `missingGenes.gene.id`,
  `insertionSequences.id`, `missingRegionsOfDifference.id`, avec l'heuristique
  painless `subset_freq / (superset_freq - subset_freq + subset_size)`.
- **Panne en production** : `/genes/{locus_tag}/snps`, `/snps/details`,
  `/snps/matrix` et `/lineage-analysis-report` renvoient toutes
  `500 [Errno 13] Permission denied: '/cache/embeddings'` (droits sur le volume
  monté). Seules les routes `genes/*` de consultation fonctionnent. Ne pas bâtir
  d'analyse sur les routes SNP tant que le script ne signale pas leur retour.
- `/genes/categories/list` renvoie une liste vide alors que `functionalCategory`
  existe dans le type `Gene`.

## Skills dépendants à vérifier en cas de dérive

`tbannotator-es` (requêtes ES directes), `tbannotator-mcp` (base PostgreSQL, qui
est une **autre** source, à ne pas confondre), et tout skill consommant les
champs `crisprStats`, `mappingStats`, `quality`, `missingGenes`,
`insertionSequences`, `resistances` : `crispr-spacer-null`, `strain-qc`,
`resistance-profiler`, `fetch-tbannotator`.

## Automatisation (optionnelle)

Le script est silencieux quand rien ne bouge et sort en code 1 sinon, donc il se
place tel quel dans une tâche planifiée hebdomadaire. Ne pas le brancher sur
`SessionStart` : l'amont bouge de l'ordre de quelques commits par an, un appel
réseau à chaque session serait du bruit pour rien.
