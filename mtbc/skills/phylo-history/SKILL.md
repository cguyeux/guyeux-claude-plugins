---
name: phylo-history
description: >-
  Analyse le placement phylogénétique d'une souche MTBC dans les arbres où elle
  a figuré (investigate_phylo/history/, Newick archivés) : k plus proches
  voisins par distance patristique, sister clade, stabilité lignée/voisinage.

  Use when: doubtful lineage assignment, placement unstable across
  reconstructions, long-branch attraction, diagnostic before manual
  reclassification.

  Portée : développé sur le MTBC, applicable à toute bactérie clonale (Yersinia,
  Leptospira...) — distance patristique et stabilité de voisinage ne dépendent pas
  de l'organisme. Hors MTBC : fournir le répertoire d'arbres Newick archivés.
argument-hint: "<SRA> [--k N] [--format human|json]"
user-invocable: true
allowed-tools: Bash, Read, Glob
---

# /phylo-history : Diagnostic phylogénétique d'une souche

Pour une souche SRA donnée, récupère tous les arbres dans lesquels elle a
figuré (via l'historique `investigate_phylo/history/strain_history.json`),
charge chaque Newick disponible et analyse la position de la souche :
voisins, sister clade, stabilité inter-arbres.

## Déclenchement

```
/phylo-history SRR18391710
/phylo-history SRR25515834 --k 10
/phylo-history ERR1023220 --format json
```

## Pré-requis

- Le répertoire `investigate_phylo/` doit être accessible depuis le cwd
  (chemin typique : `mtbc/investigate_phylo/`).
- L'historique doit avoir été alimenté au moins une fois par `get_phylo.py`
  (sinon la souche n'est dans aucun arbre et rien à analyser).
- `biopython` doit être installé (`Bio.Phylo`).

## Étapes

### Phase 0 : Localiser investigate_phylo/

Chercher `investigate_phylo/history/strain_history.json` en remontant depuis
le cwd, ou dans `mtbc/investigate_phylo/`. Si absent : prévenir l'utilisateur
qu'aucun historique n'a été enregistré.

### Phase 1 : Lancer l'analyse

Depuis `investigate_phylo/` :

```bash
python analyze_strain_phylo.py <SRA> --k 5 --format human
```

Le script produit :
- Liste des arbres où la souche figure (tree_id, étude, date, n_taxa)
- Pour chaque arbre : feuille correspondante, lignée enregistrée vs lignée
  dans le Newick, sister clade, k plus proches voisins avec distance
  patristique et lignée de chaque voisin
- Résumé de stabilité :
  - `lineage_stable` : la souche garde-t-elle toujours la même lignée ?
  - `neighbor_jaccard` : indice de Jaccard des voisins entre arbres (≥0.5
    = voisinage cohérent)
  - `common_neighbors` : souches présentes dans TOUS les arbres

### Phase 2 : Interpréter les résultats

Selon ce que renvoie le script, formuler un diagnostic :

**Cas 1 : Tout stable** (`lineage_stable=true`, `neighbor_jaccard>=0.5`) :
la souche est correctement classée, son voisinage est cohérent entre
reconstructions. Rien à signaler.

**Cas 2 : Lignée instable** (plusieurs lignées assignées entre arbres) :
examiner le fichier `history/strain_history.json` de la souche
(`lineage_timeline`) pour comprendre quand le changement a eu lieu, arbre
successif ? déplacement manuel (`event: move`) ? Vérifier si la composition
des voisins diverge entre arbres.

**Cas 3 : Voisinage instable** (`neighbor_jaccard<0.5`) alors que la
lignée est stable : signal de long-branch attraction ou d'un arbre mal
résolu localement. Comparer les branch lengths entre arbres ; si la souche
a une branche très longue, suspecter un problème de qualité (coverage,
contamination) et croiser avec `report.json` (`mapping_stats.mean_depth`,
`quality.after_filtering.gc_content`).

**Cas 4, Discordance lignée enregistrée vs Newick** : la souche a été
déplacée dans `bdd/` mais l'arbre a été fait avant le déplacement. C'est
normal si le tree_id est ancien. Suggérer de relancer `get_phylo.py` si
on veut un arbre reflétant l'état courant.

**Cas 5 : SRA introuvable dans un arbre** (`found_in_tree=false`) :
- `Newick introuvable` : le run s'est arrêté avant l'écriture du bestTree
  et les fichiers n'ont pas été archivés dans `experiments/`. Aucune
  analyse possible pour cet arbre.
- `SRA absent des feuilles` : la souche a été marquée `included` dans
  l'index mais est absente du Newick, probablement éliminée lors d'une
  étape RAxML post-metadata (rare). Inspecter manuellement.

### Phase 3 : Recommandations concrètes

À partir du diagnostic, proposer une action :

- **Reclasser** : si les voisins d'une souche sont majoritairement d'une
  lignée différente de celle enregistrée, suggérer un `deplacer_souches.py`
  vers la lignée dominante des voisins (avec confirmation humaine).
- **Re-séquencer / ignorer** : si la branche est anormalement longue et
  la qualité du `report.json` est faible, déplacer vers `bdd/ignore/`.
- **Attendre le prochain arbre** : si l'instabilité est récente et qu'un
  arbre plus grand est en préparation, recommander d'attendre.
- **Investiguer plus loin** : lancer `/lineage-subdivision explore` sur la lignée
  parente pour confirmer qu'elle forme bien un clade.
- **Croiser avec la littérature** : quand le diagnostic pointe vers une étude
  publiée qui a peut-être déjà caractérisé cette souche ou sa sister clade,
  la chercher via le skill `tbmonitor-papers` (recherche par SRA, BioProject
  ou code de lignée dans les titres et résumés).

## Sorties attendues

Le skill doit produire, dans l'ordre :
1. Le résultat brut de `analyze_strain_phylo.py` (format human).
2. Un diagnostic structuré (cas 1-5 ci-dessus).
3. Une action recommandée, clairement justifiée par les chiffres.

## Exemple d'interprétation

```
SRR21276930 a figuré dans 2 arbres (20260405_150702_test, 20260407_085424_test).
Lignée enregistrée : L4.4.2 (stable).
Voisins : Jaccard 0.83, 8 voisins communs tous L4.4.2.
Sister clade : 12 feuilles, 11 L4.4.2 + 1 L4.4.

→ Diagnostic (cas 1) : placement stable et cohérent. Aucune action requise.
```

```
SRR30679919 a figuré dans 3 arbres.
Lignée enregistrée : L4.11 → L4.11.1 → L4.11 (instable).
Voisins : Jaccard 0.40, lignées majoritaires dans le voisinage variables.

→ Diagnostic (cas 2 + 3) : placement instable, probable artefact de
  branche longue. Vérifier `bdd/actuelle/L4.11/SRR30679919/NC_000962.3/
  report.json` → mean_depth et covered_bases_percent.
  Action : si qualité OK, attendre un arbre plus large ; sinon ignorer.
```

## Portée réelle de l'historique, et quand passer à `/phylo-forest`

Ce skill lit `investigate_phylo/history/strain_history.json`, qui n'est alimenté
que par un appel explicite à `get_phylo.py`. Mesuré le 2026-08-30 : **3 arbres
archivés, aucun depuis le 2026-05-15**, alors que le dépôt porte environ
1 500 arbres de résultat. Un diagnostic rendu ici est donc, sauf coïncidence,
fondé sur trois reconstructions de mai 2026 — ce qui reste utile, mais n'est pas
« tous les arbres où la souche a figuré », et ne doit pas être présenté comme tel.

Pour la même question sur la forêt entière, utiliser `/phylo-forest`, qui
moissonne les Newick existants sans rien demander :

```bash
F=~/docs/environnement/plugins/phylo/skills/phylo-forest/scripts/forest.py
python3 $F find --taxa <SRA>          # tous les arbres contenant cette souche
python3 $F support --taxa <SRA>,<voisins présumés>   # ce voisinage tient-il ?
```

Garde-fou propre à la comparaison inter-arbres : une souche peut changer de
place simplement parce que ses voisins ne sont pas dans l'arbre suivant. Ne
comparer que des arbres à échantillonnage comparable avant de conclure à une
instabilité de la souche elle-même.
