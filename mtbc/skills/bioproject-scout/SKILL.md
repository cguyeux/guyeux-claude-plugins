---
name: bioproject-scout
description: >-
  Recherche des BioProjects NCBI recents, ou anciens toujours actifs, pertinents
  pour le MTBC : filtrables par espece (M. africanum, M. bovis...), pays,
  mot-cle de resistance. Recoupe chaque candidat avec TBannotator
  (tb_ncbi_strain) pour distinguer jamais-ingere / partiellement ingere / deja
  couvert, enrichit bioproject_geo, prepare la liste d'accessions SRA a ingerer
  en priorite (handoff vers /fetch-tbannotator, seul point d'ingestion reel).

  Use when: veille periodique sur une espece/lignee avant caracterisation,
  recherche de cohortes recentes par pays ou phenotype de resistance,
  verification qu'aucun depot recent n'a ete manque. Portee : developpe sur le
  MTBC, la recherche NCBI elle-meme (parametree par organisme) s'applique a
  toute bacterie clonale (Yersinia, Leptospira...), mais le recoupement
  jamais-ingere/deja-couvert passe par TBannotator et n'existe pas hors MTBC.
argument-hint: "<organisme|mot-cle> [--country <pays>] [--resistance <mot-cle,...>] [--since YYYY-MM-DD] [--min-runs N]"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebFetch, mcp__tbannotator__tool_query_postgres
---

> [!WARNING]
> **[2026-09-08] TABLES ABSENTES du serveur tblearn.** Ce skill interroge 2 objet(s) qui
> n'existent plus depuis le remplacement du MCP TBannotator. Contrairement au filtre `system_name`,
> ces requêtes ne rendent pas un ensemble vide : elles **lèvent une erreur** `relation does not exist`.
>
> | table citée ici | remplacer par | fondement |
> |---|---|---|
> | `mv_spdi_mutations` | **tb_report_spdi ⋈ tb_report_spdi_annotations sur spdi_id** | le variant dans la première, l'annotation (`locus_tag`, `hgvs_p`, `impact`) dans la seconde |
> | `tb_ncbi_strain` | **mv_strain_metadata** | porte `run_accession`, `tax_id`, `scientific_name`, `study_accession`, `center_name`, `first_public` |
>
> Correspondances établies en comparant les colonnes, pas devinées. Détail et schéma complet :
> `~/.agents/knowledge/tblearn-migration.md`.


# /bioproject-scout — Veille BioProject NCBI pour le MTBC

## Objectif, et ce que ce skill n'est PAS

Répond à : « des dépôts NCBI récents (ou des BioProjects existants qui continuent à recevoir de
nouveaux runs) pertinents pour `<espèce / pays / résistance>` ont-ils échappé au pipeline
d'ingestion TBannotator ? »

Ce n'est **pas** un outil de géolocalisation par souche (→ `sra-geolocate`), ni le mécanisme
d'ingestion lui-même (→ `fetch-tbannotator`).

> [!IMPORTANT]
> **Il n'existe PAS d'outil MCP `sra_to_add`.** Vérifié sur le schéma complet du serveur
> `tbannotator` (2026-08-10, `tool_get_schema`) : 5 tools MCP (`tool_get_version`,
> `tool_get_schema`, `tool_query_postgres`, `tool_build_nj_tree`, `tool_submit_raxml_job`), aucune
> table ni fonction `sra_to_add`. Le vrai mécanisme d'ingestion, déjà documenté et éprouvé, est
> l'ajout d'accessions à `mp:/data/current/run/config/samples.tsv` (SSH sur `mp`, VPN requis), suivi du
> lancement (séparé, sur demande explicite) du pipeline Snakemake — procédure intégrale dans
> `/fetch-tbannotator` § « When a strain is in neither location ». **Ce skill prépare la liste
> d'entrée, il n'ingère rien lui-même.**
>
> **Depuis le 2026-08-17, un `sra_to_add` LOCAL existe** (script, pas outil MCP) :
> `${CLAUDE_PLUGIN_ROOT}/skills/fetch-tbannotator/scripts/sra_to_add.py`. Lui passer directement le
> `candidates.tsv` produit ici : `sra_to_add.py --queue --file candidates.tsv`, il en extrait les
> accessions, les qualifie
> (ENA + file distante + déjà annoté) et n'empile que ce qui est réellement à ingérer. Le
> `new_sras.txt` manuel de l'étape 2 ci-dessous reste valable mais n'est plus nécessaire.

## Préalable — consultation mémoire projet

1. `global_supplementary/bioproject_geo/bioproject_metadata.tsv` (table maître cumulative, 1366+
   BioProjects connus au 2026-05-31) et son `README.md` : consulter/étendre AVANT toute recherche
   pays — ne jamais reconstruire le gazetteer, réutiliser `sweep_bioprojects.py`.
2. `barcoding_v2/SOURCES_OF_TRUTH.md` : si la cible est une lignée précise plutôt qu'une espèce,
   noter son marqueur SPDI racine (table dans `sra-geolocate` § Mode BULK) pour un recoupement
   post-ingestion par `mv_spdi_mutations` — l'organisme déclaré NCBI ne descend jamais au niveau
   lignée.
3. `cahier_de_labo.md` : vérifier qu'une veille identique n'a pas déjà été faite récemment
   (`grep -i bioproject-scout` ou le nom de l'espèce).

## Étape 0 — sanity check avant une campagne large

`scripts/scout_bioprojects.py` s'appuie sur des regex sur le XML brut NCBI (même style que
`sweep_bioprojects.py` et `sra-geolocate`, pas de client Entrez tiers). Avant de lancer une
recherche à fort `--since`/`retmax`, valider sur un cas connu : un BioProject MTBC récent et déjà
familier (ex. un de ceux cités dans `bioproject_geo/README.md`) doit ressortir avec le bon
`n_runs_recent` et le bon pays. Si le script renvoie 0 résultat sur un cas connu, diagnostiquer
avant de conclure à une absence de dépôts récents — c'est le script qui ne capte rien, pas NCBI qui
est vide (même discipline que le témoin positif de `/fetch-tbannotator`).

## Étape 1 — Découverte des candidats sur NCBI

Deux angles, à cascader :

### 1a. BioProjects récemment CRÉÉS (signal faible sur du MTBC établi)
```
esearch db=bioproject term='"<organisme>"[Organism] AND ("<depuis>"[Create Date] : "3000"[Create Date])'
```

### 1b. Runs SRA récemment DÉPOSÉS, y compris sous un BioProject ancien — angle PRINCIPAL
```
esearch db=sra term='"<organisme>"[Organism] AND ("<depuis>"[PDAT] : "3000"[PDAT])'
```
Beaucoup de grands projets de surveillance MTBC (créés il y a des années) reçoivent des runs en
continu ; c'est ce flux-là, pas la création de nouveaux BioProjects, qui signale le mieux « quelque
chose de neuf pertinent pour ma lignée ». Pour chaque UID SRA trouvé, `esummary db=sra` (champ
`ExpXml`) donne BioProject + organisme + accession Run en un aller-retour (même motif que
`sra-geolocate` Phase 2 § BioProject ID → Run accession). **Agréger par BioProject** :
`n_runs_recent`, plage de dates de dépôt.

Outil :
```
python3 scripts/scout_bioprojects.py --organism "Mycobacterium africanum" --since 2025-01-01 \
    [--country Nigeria] [--resistance "MDR,rifampicin,multidrug,XDR,isoniazid"] [--min-runs 1] \
    --out candidates.tsv
```
stdlib seule (urllib + xml.etree), respecte le rate-limit NCBI (3 req/s, pas de clé API). Réutilise
directement `parse_country`/`efetch_bioproject` de `sweep_bioprojects.py` (import, `sys.path` vers
`bioproject_geo/`, surchargeable par `$BIOPROJECT_GEO_DIR`) — **aucune duplication** du gazetteer
pays ni de la logique efetch. Sortie TSV : `bioproject, n_runs_recent, date_min, date_max,
organism_declared, title, country_guess, country_confidence, resistance_hit`.

> [!WARNING]
> Rappel ISOLEMENT vs SÉQUENÇAGE (cf. `sra-geolocate`) : `country_guess` vient du titre/description
> CONTENU du BioProject, jamais de l'institution soumettrice. `resistance_hit` est un signal
> **lexical grossier** (mots-clés dans titre/description), pas un phénotype confirmé — à vérifier
> après ingestion via `resistance-profiler`/`resistance-catalogue`, jamais à citer tel quel dans un
> manuscrit.

## Étape 2 — Recoupement avec TBannotator (déjà ingéré ou non)

**En UNE requête groupée**, jamais une boucle par BioProject (coût O(1), même discipline que le
Mode BULK de `sra-geolocate`) :
```sql
SELECT ncbi_bioproject, COUNT(*) AS n_known
FROM tb_ncbi_strain
WHERE ncbi_bioproject = ANY(ARRAY['PRJxxxx','PRJyyyy', ...])
GROUP BY ncbi_bioproject;
```
Joindre à `n_runs_recent` de l'étape 1 :

| condition | statut | priorité |
|---|---|---|
| `n_known` absent ou 0 | **jamais ingéré** | haute |
| `0 < n_known < n_runs_recent` | **partiellement ingéré** (le BioProject a grossi) | moyenne — cibler les runs nouveaux, pas tout le BioProject |
| `n_known >= n_runs_recent` | déjà couvert | basse |

> [!NOTE]
> `n_known` compte les runs **enregistrés** dans `tb_ncbi_strain`, pas forcément **annotés** avec un
> `report.json` exploitable. Cf. le piège documenté dans `fetch-tbannotator` : présence en base ne
> garantit pas rapport disponible (désynchronisation `mp` ↔ MV, purge du rolling window). Si le
> chiffre est décisif, sonder les deux routes avant de conclure, ne pas s'arrêter à `n_known`.

## Étape 3 — Enrichissement du cache central et classement

1. Ajouter les BioProjects nouvellement vus à la table maître :
   ```
   python3 global_supplementary/bioproject_geo/sweep_bioprojects.py <candidats_nouveaux.txt>
   ```
   (ne refetch pas les accessions déjà connues du cache).
2. Classer et **afficher le tableau à l'utilisateur avant toute action d'ingestion** : priorité
   haute (jamais ingéré + `n_runs_recent` élevé + pays/résistance pertinents) → basse (déjà
   couvert).

## Étape 4 — Handoff vers l'ingestion (jamais automatique)

Pour les seuls BioProjects retenus par l'utilisateur :
1. Résoudre les accessions **Run** (SRR/ERR/DRR, pas Sample) : `elink bioproject→sra` puis
   `esummary` par UID — motif exact de `sra-geolocate` Phase 2 § « BioSample ID → Run accession »,
   transposable BioProject → Run.
2. Écrire `new_sras.txt` (une accession par ligne).
3. Passer la main à `/fetch-tbannotator` avec ces accessions : c'est LUI qui documente et exécute
   l'ajout dédupliqué à `mp:/data/current/run/config/samples.tsv` (backup daté, dédup, header
   préservé). **Ne jamais lancer le pipeline sans demander explicitement** : `samples.tsv` porte
   aussi le travail en cours d'autres campagnes, et le lancement mobilise un serveur partagé —
   l'append seul suffit la plupart du temps, la prochaine exécution planifiée l'absorbera.

## Sortie attendue

Tableau consolidé à l'écran (accession, titre tronqué, organisme déclaré, pays inféré + confiance,
`n_runs_recent`, statut TBannotator, indice résistance) + fichier `candidates.tsv` + entrée
`cahier_de_labo.md` si la veille aboutit à une décision d'ingestion ou à un résultat négatif notable
(« rien de neuf pertinent depuis `<date>` »).

## Intégration avec l'écosystème

- **`bioproject_geo/`** : cache central réutilisé et enrichi (`sweep_bioprojects.py`,
  `bioproject_metadata.tsv`), jamais reconstruit depuis zéro.
- **`sra-geolocate`** : mêmes recettes Entrez (BioProject↔SRA, cascade géo), même piège isolement
  vs séquençage, même piège isolement vs déclaration (pathogènes « voyageurs »).
- **`fetch-tbannotator`** : seul point d'ingestion réel ; ce skill ne fait QUE préparer sa liste
  d'entrée, jamais l'inverse.
- **`tbannotator-mcp`** : requêtes `tb_ncbi_strain` / `mv_strain_metadata` pour le recoupement
  d'ingestion et, après coup, `mv_spdi_mutations` pour le recoupement par lignée.
- **`species-id` / `strain-qc`** : QC post-ingestion — un organisme NCBI déclaré
  « M. tuberculosis »/« M. africanum » peut être une mycobactérie voisine misclassifiée (cf. garde-fou
  taxonomique du `CLAUDE.md` racine). Ce skill ne fait aucune vérification d'espèce, seulement de
  couverture.
- **`resistance-profiler` / `resistance-catalogue`** : confirmation du phénotype de résistance
  post-ingestion — `resistance_hit` n'est qu'un indice lexical de repérage.
