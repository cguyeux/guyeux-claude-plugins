---

name: phylo-narrative
description: >-
  Rédige un paragraphe pour un manuscrit scientifique décrivant le placement
  phylogénétique d'une souche MTBC à travers les arbres dans lesquels elle
  a figuré. Exploite investigate_phylo/history/ et les fichiers Newick
  archivés pour produire une narration sourcée sur les voisins, la sister
  clade, la stabilité de l'assignation et le voisinage inter-reconstructions.

  Use when: writing the Results section of a lineage paper and needing a
  justified sentence about a strain's placement; documenting why a strain
  was retained, reclassified or excluded; preparing supplementary material
  describing the phylogenetic position of outlier strains; responding to
  a reviewer asking for evidence about a specific strain's lineage.

  Portée : développé sur le MTBC, applicable à toute bactérie clonale (Yersinia,
  Leptospira...) — la narration décrit un placement dans un arbre, pas une biologie
  particulière. Hors MTBC : fournir le répertoire d'arbres Newick archivés.
allowed-tools: Bash, Read, Glob
---

# /phylo-narrative — Narration phylogénétique d'une souche pour manuscrit

Produit un paragraphe prêt à coller dans un manuscrit (Results,
Supplementary Material, ou rebuttal à un reviewer) décrivant la position
phylogénétique d'une souche MTBC, en s'appuyant sur les arbres déjà
reconstruits et archivés dans `investigate_phylo/experiments/`.

## Déclenchement

```
/phylo-narrative SRR18391710
/phylo-narrative SRR25515834 --k 8
```

## Pré-requis

- Le répertoire `investigate_phylo/` doit être accessible depuis le cwd
  (typiquement `mtbc/investigate_phylo/` depuis un article).
- `investigate_phylo/history/strain_history.json` doit exister (sinon
  aucun arbre n'a été enregistré).
- `biopython` est requis (`Bio.Phylo`).

## Étapes

### Phase 0 — Localiser investigate_phylo/

Remonter depuis le cwd pour trouver `investigate_phylo/`. Depuis un
sous-projet article typique (`L4.15/article/`, `methodology/article/`…),
c'est `../../investigate_phylo/`.

### Phase 1 — Produire la narration brute

```bash
cd <chemin vers investigate_phylo>
python analyze_strain_phylo.py <SRA> --k <N> --format narrative
```

Le script renvoie un paragraphe anglais structuré selon ces éléments :
- Nombre d'arbres analysés + tree_ids
- Stabilité (ou non) de la lignée assignée
- Composition de la lignée dominante dans le voisinage immédiat
- Indice de Jaccard du voisinage entre reconstructions
- Composition de la sister clade immédiate

### Phase 2 — Enrichir la narration avec des chiffres

Relancer en mode `--format json` pour récupérer les valeurs exactes à
injecter comme arguments précis dans la prose :

```bash
python analyze_strain_phylo.py <SRA> --k <N> --format json
```

Utiliser les champs suivants pour enrichir le paragraphe :
- `summary.assigned_lineages` — lister toutes les lignées historiques
- `summary.neighbor_jaccard` — citer l'indice exact (2 décimales)
- `trees[i].nearest_neighbors[*].patristic_distance` — citer la distance
  au plus proche voisin pour quantifier la proximité
- `trees[i].sister_clade.size` et `lineage_composition` — décrire
  précisément la sister clade
- `strain_entry.lineage_timeline` (depuis `query_history.py <SRA>` si
  nécessaire) — documenter les déplacements manuels avec leur date

### Phase 3 — Adapter au contexte du manuscrit

Relire la prose du script et l'adapter au ton et au contexte :

- **Results section** : phrase factuelle, présent ou passé selon le
  style du manuscrit. Inclure les tree_ids uniquement si la section
  les documente ailleurs ; sinon les remplacer par « across
  reconstructions » ou « in all phylogenies » .
- **Supplementary / strain notes** : garder les tree_ids et timestamps
  pour la traçabilité complète.
- **Rebuttal à un reviewer** : commencer par « As requested by the
  reviewer, we examined the phylogenetic position of strain X… » puis
  enchaîner avec la narration du script.

### Phase 4 — Vérifier la cohérence avec le manuscrit

Avant de proposer le paragraphe :
1. Vérifier que la lignée affirmée dans la prose est bien celle utilisée
   dans le reste du manuscrit (grep dans `main.tex` ou `.bib` du
   sous-projet).
2. Si `analyze_strain_phylo.py` signale une instabilité et que le
   manuscrit affirme une appartenance unique, prévenir l'utilisateur
   plutôt que de masquer la divergence.
3. Ne jamais inventer de bootstrap support : les arbres RAxML-NG en
   `BIN+G` (modèle utilisé par `get_phylo.py`) ne produisent pas de
   bootstraps par défaut. Si le reviewer demande du support, renvoyer
   vers un bootstrap dédié (commande séparée).

## Règles de style à respecter

- **Anglais scientifique uniquement** (les articles MTBC de Christophe
  Guyeux sont rédigés en anglais).
- **Pas de « we believe », « seems to »** : utiliser un langage factuel
  (« strain X clustered within », « its 5 nearest neighbours were »).
- **Toujours citer les n_taxa de l'arbre** pour contextualiser : une
  proximité dans un arbre de 50 taxa ne dit pas la même chose qu'un
  arbre de 2000 taxa.
- **Patristic distances en 4 décimales** pour être lisible.
- **Une seule phrase par idée**, puis enchaînement logique.

## Sorties attendues

Le skill doit produire, dans l'ordre :
1. Le paragraphe narratif brut du script (mode `narrative`).
2. Une version retravaillée adaptée au contexte donné par l'utilisateur
   (Results / Supp / Rebuttal).
3. Une note technique entre crochets `[tree_ids, dates, distances]` que
   l'utilisateur peut garder ou retirer.

## Exemple complet

**Entrée** : `/phylo-narrative SRR25515834`

**Sortie brute** (du script) :
> Strain SRR25515834 was included in 1 independently reconstructed
> phylogenetic tree (tree IDs: 20260407_085424_test) and consistently
> clustered within lineage L4.4.2. In the most recent reconstruction
> (20260407_085424_test, n=200 taxa), its 5 nearest neighbours by
> patristic distance were dominated by lineage L4.4.2 (5/5). Its
> immediate sister clade in that tree contains 1 taxa, predominantly
> from lineage L4.4.2.

**Sortie adaptée Results** :
> Strain SRR25515834 clustered unambiguously within lineage L4.4.2 in
> our reconstructed phylogeny (n = 200 taxa), with its five nearest
> neighbours by patristic distance (minimum 0.0013 substitutions per
> site) all belonging to L4.4.2 and an immediate sister taxon from the
> same lineage.

**Sortie Supp** (plus verbeux, tree_id gardé) :
> Strain SRR25515834 was included in the tree 20260407_085424_test
> (n = 200 taxa, 200404 informative SPDIs) and was placed within the
> L4.4.2 clade. Its five nearest neighbours by patristic distance were
> SRR25515553 (L4.4.2, d = 0.0013), SRR10040533 (L4.4.2, d = 0.0021),
> SRR21277048 (L4.4.2, d = 0.0023), SRR21291145 (L4.4.2, d = 0.0023)
> and ERR2179762 (L4.4.2, d = 0.0023), confirming unambiguous
> assignment to L4.4.2.
