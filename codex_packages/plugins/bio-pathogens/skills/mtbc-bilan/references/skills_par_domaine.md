# Skills par domaine analytique -- catalogue de reference

Reference de `mtbc-bilan`. Sert deux fois : en Phase 7.3 pour associer un skill
a chaque piste hierarchisee, et en phase D2 du mode `--deepen` pour classifier
les skills disponibles et reperer les methodes jamais mobilisees.

## Association piste -> skill (Phase 7.3, texte integral)

### 7.3 Association aux skills

Pour chaque piste, associer explicitement un ou plusieurs skills
existants du plugin `bio/` :
- Phylogenie / datation : `/raxml`, `/iqtree-lsd2`, `/molecular-clock`,
  `/bayesian-skyline`, `/pastml`
- Structure de population : `/lineage-subdivision`, `/tsne-hdbscan`,
  `/phylo-history`, `/snp-distance`
- Annotation / evolution : `/spdi-annotation`, `/convergent-evolution`,
  `/coevolution`, `/mk-ascertainment`, `/pangenome-enrichment`
- Epidemiologie / phenotype : `/lineage-comparison`,
  `/resistance-profiler`, `/phylogeography`
- BDD / queries : `/tb-cli`, `/tbannotator-mcp`, `/fetch-tbannotator`
- Manuscrit / litterature : `/lit-review`, `/claim-check`,
  `/manuscript-review`, `/reviewer-response`, `/bib-check`

Si aucun skill existant ne convient pour une piste haute priorite :
suggerer explicitement la creation d'un nouveau skill.

**Regle d'honnetete** : ne PAS gonfler la liste. Si moins de 3 pistes
haute priorite emergent honnetement, assumer une sortie courte.


---

## Classification par domaine (phase D2 du mode `--deepen`, texte integral)

## Phase 3 -- Inventaire des skills et methodes non mobilises

C'est la phase la plus originale de ce skill. L'objectif est de
confronter les capacites analytiques disponibles (via les skills du
plugin bio/) avec ce qui a ete effectivement fait dans le projet,
pour identifier les **angles morts methodologiques**.

### Etapes

1. **Lister les skills des plugins bio** (scindes en deux depuis) :
   ```bash
   ls ~/docs/codes/claude_plugins/bio_pathogens/skills/ \
      ~/docs/codes/claude_plugins/bio_population_genetics/skills/
   ```

2. **Classifier chaque skill par domaine** (utiliser la description
   du skill, pas son nom) :
   - Phylogenie / datation
   - Structure de population / clustering
   - Annotation / evolution moleculaire
   - Epidemiologie / phenotype / resistance
   - Phylogeographie / cartes
   - Coevolution / contexte historique
   - Bases de donnees / queries
   - Litterature / manuscrit
   - Visualisation

3. **Pour chaque skill d'analyse** (exclure les skills de manuscrit
   et de BDD qui sont des outils, pas des methodes) :
   - Lire le frontmatter (description) du SKILL.md
   - Determiner si la methode correspondante a ete utilisee dans le
     projet : chercher des traces dans le cahier, les scripts, les
     resultats
   - Classer en :
     - **Utilise** : methode clairement appliquee (script, resultat,
       mention dans le cahier)
     - **Pertinent non utilise** : la methode serait applicable aux
       donnees du projet mais n'a jamais ete lancee
     - **Non pertinent** : la methode ne s'applique pas a ce projet
       (ex : bovine-genomics pour un projet L4 humain)

4. **Pour chaque skill "pertinent non utilise"**, evaluer :
   - **Ce qu'il apporterait** : quelle question scientifique il
     pourrait aider a resoudre
   - **Ce qu'il faudrait** : donnees necessaires (disponibles ou non),
     prerequis (arbre, matrice, etc.)
   - **Effort estime** : rapide (< 1h), modere (1-4h), lourd (> 4h)

### Affichage intermediaire

```
Phase 3/4 : Inventaire des methodes
  Skills analyses disponibles : 42
  Utilises dans ce projet     : 8
  Pertinents non utilises     : 6
  Non pertinents              : 28

  Methodes non exploitees :
    - /bayesian-skyline   : demographie Ne(t), arbre date requis
    - /convergent-evolution: mutations paralleles, matrice SPDI requise
    - /coevolution        : tests Mantel/PACo, donnees humaines requises
    - /thd                : succes epidemique, arbre date requis
    - /mk-ascertainment   : selection, SPDI par tier requis
    - /ancestral-reconstruction : etats ancestraux, arbre + metadata requis
```
