---
name: ani-panel-classify
description: >-
  Academic research toolkit for peer-reviewed pathogen-genomics research (Guyeux group,
  FEMTO-ST). Classifies a genome into a clade, phylogenomic group or species by whole-genome
  ANI (skani) against a curated, paramétrable panel of type-strain reference genomes — the
  runner the MTBC taxonomic anti-false-positive guard-fou (species-id) prescribes but does
  not itself execute. Genus-agnostic: the panel (group labels, species, strains, GenBank/
  RefSeq accessions) is supplied as a TSV, nothing genus-specific is hardcoded. Use when a
  genome needs to be assigned to a named phylogenomic group defined by ANI in the published
  literature (e.g. Leptospira P1/P2/S1/S2 pathogenicity clades), when validating that a
  reconstructed clade in `bdd/hors_mtbc/` or a sibling genus project is ANI-coherent with its
  type strains, or when `species-id`'s BLAST/Mash methods are too coarse (need a group finer
  than genus/species, or a panel wider than the fixed NTM set `species-id` ships with).
argument-hint: "<FASTA...> --panel <panel.tsv> [--mode fast|medium|slow] [--min-af N]"
allowed-tools: Bash, Read, Write, Edit, Glob
user-invocable: true
---

# /ani-panel-classify — Classement par ANI contre un panel de souches types

Classe un ou plusieurs génomes requêtes dans un groupe (clade, groupe
phylogénomique, espèce...) défini par un panel de souches types, en
mesurant l'ANI (Average Nucleotide Identity) via **skani** contre chaque
référence du panel et en retenant le meilleur hit.

Ce skill comble un trou identifié dans l'outillage du dépôt : le
garde-fou taxonomique anti-faux-positif MTBC (`species-id`, cf. son
avertissement en tête de fichier) **prescrit** skani contre un panel
incluant les espèces proches, mais aucun script du dépôt ne l'exécutait
avant celui-ci — `species-id` ne fait que du BLAST rpoB/16S ou du Mash
screen contre le sketch RefSeq global, avec un panel NTM non
paramétrable en dur. `/ani-panel-classify` est le runner générique :
un panel = un TSV, valable pour n'importe quel genre du dépôt.

---

## Ce que ce skill fait, et ce qu'il ne fait pas

- **Fait** : télécharge (et met en cache) les génomes de référence du
  panel depuis NCBI par accession, calcule l'ANI de chaque requête
  contre chaque référence via `skani dist`, assigne le groupe de la
  meilleure référence, et signale un placement incertain (deux
  meilleurs hits de groupes différents à moins de 1 point d'ANI).
- **Ne fait pas** : construire le panel lui-même. Le panel (quelles
  souches types, quelles accessions, quelle source bibliographique)
  est une décision scientifique par genre, à documenter par une revue
  de littérature (`/lit-review`) et à figer dans un TSV versionné —
  jamais improvisée par le skill.
- **Ne remplace pas** `species-id` : `species-id` répond « est-ce le
  bon genre/la bonne espèce, ou une contamination/un mislabel ? » avec
  BLAST/Mash, rapide et sans panel à construire. `/ani-panel-classify`
  répond « dans quel groupe **paramétré par la littérature** ce génome
  tombe-t-il ? », plus lent (skani + téléchargement) mais seul capable
  de distinguer des groupes plus fins que l'espèce ou définis par un
  papier précis (clades de pathogénicité, sous-lignées ANI...).

---

## Format du panel (TSV, colonnes obligatoires)

```
group	species	strain	accession	source
P1	Leptospira interrogans	Fiocruz L1-130	GCF_000017685.1	vincent2019taxonomy
```

- `group` : l'étiquette assignée à une requête dont le meilleur hit est
  cette référence (ex. `P1`, `P2`, `S1`, `S2` pour Leptospira ; ou un nom
  d'espèce si le panel classe au niveau espèce).
- `species`, `strain` : texte libre, pour la lisibilité du rapport.
- `accession` : accession GenBank/RefSeq (`GCA_...`/`GCF_...`) de
  l'assemblage de la souche type — c'est la seule colonne qui pilote le
  téléchargement.
- `source` : clé de citation ou DOI de la publication qui a établi cette
  assignation groupe/souche. Traçabilité uniquement, ignorée par la
  logique du script — mais **obligatoire** : un panel sans provenance
  n'est pas publiable.

Chaque panel versionné vit dans `panels/<genre>_<description>.tsv` de ce
skill (ex. `panels/leptospira_p1_p2_s1_s2.tsv`), pour être réutilisé sans
reconstruction par tout projet du dépôt qui étudie ce genre.

---

## Déclenchement

```bash
python3 scripts/classify_by_panel.py query.fasta --panel panels/leptospira_p1_p2_s1_s2.tsv
python3 scripts/classify_by_panel.py *.fasta --panel panels/leptospira_p1_p2_s1_s2.tsv -o resultats.tsv
python3 scripts/classify_by_panel.py query.fasta --panel panels/X.tsv --mode fast   # panel de souches proches
```

- `--mode` (défaut `slow`) : préréglage skani. **`slow` par défaut**
  parce que ce runner sert typiquement à comparer des génomes
  **divergents** entre groupes (des clades qui peuvent être à 75-85 %
  d'ANI l'un de l'autre) — skani documente que `slow` donne une
  fraction alignée nettement plus fiable sur les génomes distants que
  `fast`/`medium`. Basculer sur `fast` seulement pour un panel de
  souches proches (même espèce, ANI > 95 % attendu partout) où la
  vitesse compte plus que la précision sur les couples distants.
- `--min-af` (défaut 15 %) : fraction alignée minimale (le plus petit
  des deux sens ref/query) pour retenir un hit. Un ANI calculé sur une
  fraction alignée trop faible n'est pas interprétable — augmenter ce
  seuil si le panel couvre des génomes très divergents où même le
  meilleur hit reste peu aligné (drapeau à lire, pas à ignorer).
- Les génomes du panel sont mis en cache par accession
  (`--cache-dir`, défaut `~/.cache/ani-panel-classify/`) : un panel
  réutilisé sur plusieurs projets ne re-télécharge rien après le
  premier appel.

---

## Interprétation du rapport

```
query                     verdict_group  best_species             best_strain     best_accession   ani    align_fraction_min  note
souche_inconnue.fasta     P1             Leptospira interrogans   Fiocruz L1-130  GCF_000017685.1  92.14  87.30
```

- `ani` / `align_fraction_min` : lire les deux ensemble. Un ANI élevé
  sur une fraction alignée faible (< 50 %) est un artefact potentiel
  (petite portion de génome partagée, pas une vraie proximité globale)
  — recouper avec un deuxième hit ou une méthode indépendante avant de
  conclure.
- Un `AVERTISSEMENT` sur stderr signale un placement ambigu (deux
  groupes différents à moins de 1 point d'ANI) : ne jamais écrire une
  assignation de clade dans un manuscrit sans lever cette ambiguïté
  (panel plus dense localement, ou marqueur indépendant).
- `verdict_group = NON_CLASSE` : aucun hit au-dessus de `--min-af` —
  le génome est probablement hors du périmètre du panel (autre genre,
  contamination), pas un genre poussé à un mauvais extrême du panel.

---

## Intégration avec l'écosystème

- **`species-id`** (plugin `bacteria`) : premier passage (genre/espèce,
  BLAST/Mash, rapide). `/ani-panel-classify` prend le relais quand une
  question plus fine que l'espèce se pose, ou quand `species-id` a déjà
  confirmé le bon genre et qu'il reste à trancher le groupe.
- **`lit-review`** : source de vérité pour construire un panel — la
  provenance de chaque souche type et de sa borne ANI de groupe doit
  venir d'une revue de littérature tracée, jamais d'une mémoire non
  vérifiée du modèle.
- **`strain-qc`**, **`variant-reality-check`** (plugin `mtbc`) :
  garde-fous complémentaires une fois le genre/groupe confirmé — ce
  skill répond « quel groupe ? », pas « ce génome est-il exploitable ? ».
- Le garde-fou taxonomique générique du dépôt (`mtbc/CLAUDE.md` §
  Validation taxonomique) reste la référence pour la règle de méthode
  (skani sur génome filtré, jamais BLAST length-weighted sur assemblage
  complet) ; ce skill en est l'implémentation exécutable.

---

## Points de vigilance

1. **Téléchargement NCBI** : `curl` vers l'API REST NCBI Datasets v2,
   pas de dépendance à la CLI `datasets` (absente du poste au moment de
   l'écriture de ce skill). Respecter le rate-limiting NCBI implicite
   pour un panel de plusieurs dizaines de souches (pas de parallélisme
   agressif côté téléchargement).
2. **Cache par accession** : si une accession est retirée/remplacée sur
   NCBI (assemblage suppressed), le fichier caché devient périmé sans
   avertissement — vider `--cache-dir` pour cette accession en cas de
   doute.
3. **Le panel n'est jamais complet** : un `verdict_group` n'est fiable
   que dans la mesure où le panel couvre toute la diversité connue du
   genre. Une revue de littérature qui découvre une espèce/un clade non
   représenté doit se traduire par une ligne de panel ajoutée, jamais
   par un silence.
