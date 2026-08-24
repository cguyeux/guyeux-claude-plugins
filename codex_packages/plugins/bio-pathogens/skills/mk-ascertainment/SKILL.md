---

name: mk-ascertainment
description: >-
  McDonald-Kreitman test and ascertainment-bias simulation for MTBC
  tier-stratified SPDI variants: is the non-synonymous excess among
  core-exclusive (lineage-defining) variants genuine, or an artefact of the
  exclusivity filter? Writes a per-gene MK table for `mtbc-gene` (pathway mode).

  Use when: a sub-lineage characterisation reports a high dN/dS or NS excess
  and ascertainment bias is questioned. Needs a tier-annotated CSV.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# McDonald-Kreitman Test & Ascertainment Bias Quantification

Outil d'analyse pour les manuscrits de caractérisation de sous-lignées MTBC.
Transforme une observation descriptive (« 33 dN, 0 dS ») en test statistique
publié et reconnu, avec quantification du biais d'ascertainment.

## Contexte scientifique

Quand on identifie une nouvelle sous-lignée MTBC par data-mining (TBannotator),
les variants « core-exclusifs » (fixés dans la lignée, absents ailleurs) montrent
souvent un excès de non-synonymes. Deux explications possibles :

1. **Signal biologique** : sélection positive ou contrainte fonctionnelle sur les
   mutations fondatrices de la lignée
2. **Artefact** : le filtre d'exclusivité élimine préférentiellement les synonymes
   (neutres → plus partagés avec les lignées sœurs → exclus)

Ce skill distingue les deux en appliquant trois tests complémentaires.

## Quand utiliser ce skill

Dès qu'une caractérisation de sous-lignée rapporte un **dN/dS élevé** ou un
**excès de non-synonymes parmi les marqueurs SPDI core-exclusifs**, et qu'un
**reviewer** (ou les auteurs eux-mêmes) demande si le biais d'ascertainment
n'explique pas à lui seul le signal. Le skill fournit la réponse chiffrée et
le texte de Limitations correspondant (voir « Intégration manuscrit »).

**Prérequis** : un CSV tier-annoté portant les comptes NS/S par tier (sortie
d'`annotate_spdis.py` ou équivalent, voir « Entrées requises »).

## Les trois analyses

### A. Test de McDonald-Kreitman (MK)

Compare le ratio NS:S entre deux classes de variants :

| Classe | Source | Filtre exclusivité |
|--------|--------|--------------------|
| **Divergence fixée** (Tier 1-2) | Core-exclusive à la lignée | Oui (cross-lignée) |
| **Polymorphisme** (Tier 4) | Clade-defining (intra-lignée) | Non |

Le Tier 4 n'est PAS soumis au filtre cross-lignée → le test MK contrôle
naturellement le biais d'ascertainment.

**Statistiques rapportées :**
- Fisher's exact test (p-value)
- Direction of Selection (DoS, Stoletzki & Eyre-Walker 2011)
- Proportion de substitutions adaptatives (alpha = 1 - NI)
- Bootstrap CI sur le DoS (10 000 réplicats)

**Analyses de sensibilité** : Tier 4 seul, Tier 3-4, Tier 3-7, Tier 4-7
comme polymorphisme alternatif.

### B. p_syn exact (Nei-Gojobori genome-wide)

Calcule la fraction exacte de sites synonymes sur tout le génome H37Rv
(~1 319 440 codons) par la méthode Nei-Gojobori (1986) :

- Pour chaque codon, compter les 9 mutations ponctuelles possibles
- Classifier chacune comme synonyme ou non-synonyme
- Sommer sur tous les CDS

Résultat typique pour H37Rv : **p_syn ≈ 0.262** (vs 0.25 standard, 0.22
GC-adjusted utilisé dans les manuscrits précédents).

Permet un test binomial exact : P(0 S | n, p_syn).

### C. Simulation du biais d'ascertainment

Modèle paramétrique :
1. N variants codants core (Tier 1-3) suivent le ratio NS:S genome-wide
2. Les S sont partagés avec les lignées sœurs b× plus souvent que les NS
3. Après filtrage d'exclusivité, on obtient les variants Tier 1-2

Sweep de b de 1.0 (pas de biais) à 4.0 (biais extrême), 100 000
simulations par valeur. Rapporte le **biais critique** : valeur de b
à partir de laquelle P(100% NS) > 0.05.

## Table MK par gène et chaînage vers les voies

Le test ci-dessus est *poolé* (génome entier). Pour relier la sélection à des voies
métaboliques précises et alimenter une fiche Atlas, le script `scripts/mk_per_gene.py`
calcule le **même test MK gène par gène** et écrit une table tidy directement consommée
par `mtbc-gene` en mode pathway (`--from-selection`) :

```bash
python scripts/mk_per_gene.py data/mk_input_annotated.csv --out mk_per_gene.tsv
# colonnes : locus_tag  gene  Dn  Ds  Pn  Ps  DoS  NI  alpha  p_fisher  q_value
```

Mêmes conventions de tiers (fixé = Tier 1-2 → Dn/Ds ; polymorphisme = Tier 4 → Pn/Ps,
ajustables par `--fixed-tiers` / `--poly-tiers`) et mêmes formules que le test poolé
(DoS, NI, alpha = 1 − NI, Fisher exact via scipy ; BH-FDR sur l'ensemble des gènes). La
table se branche ensuite sur la narration de voie, qui applique son sas de significativité :

```bash
SK=../mtbc-gene
"$SK/run_pathway.sh" --from-selection mk_per_gene.tsv --lineage <id> --paragraph
```

Chaîne complète `annotate_spdis → mk_per_gene → mtbc-gene pathway → Atlas`, sans étape
manuelle ; la fiche n'écrit la section `selection` que si le sas conclut.

**Limite de puissance (à connaître).** Le MK par gène est *sous-dimensionné* en intra-lignée
MTBC : la plupart des gènes n'ont qu'une poignée de substitutions (souvent Dn=1, Ds=0), donc
aucun ne survit individuellement à la correction FDR. C'est attendu et honnête (c'est
précisément pourquoi le test de référence est poolé). Validé sur L4.13 : 1889 gènes testés,
0 significatif → aucune section écrite. Un gène réellement sous sélection forte (Dn ≫ Ds avec
polymorphisme neutre) passe bien le sas et mappe sur sa voie (vérifié sur ESX-1). Pour un
signal *à l'échelle d'une voie*, pooler les comptes sur un ensemble de gènes (cf. le test
poolé ci-dessus, ou une colonne de catégorie fonctionnelle).

## Entrées requises

### Fichier CSV tier-annoté (obligatoire)

Format attendu (colonnes minimales) :

```
SPDI,Effect,Tier
NC_000962.3:2269880:A:C,missense_variant,1
NC_000962.3:...,synonymous_variant,4
```

Les valeurs `Effect` reconnues :
- **NS** : `missense_variant`, `stop_gained`, `stop_lost`
- **S** : `synonymous_variant`
- Autres (frameshift, intergenic, etc.) : ignorées pour le MK test

Le fichier est typiquement `supplementary_table_S3_annotated.csv`, produit
par `annotate_spdis.py` (Phase 4 du pipeline).

### Référence H37Rv (pour Nei-Gojobori)

- `NC_000962.3.gb`, séquence GenBank
- `NC_000962.3.gff3`, coordonnées CDS

Ces fichiers sont dans le répertoire racine de chaque sous-projet ou dans
`investigate_phylo/resources/`.

## Sorties

| Fichier | Contenu |
|---------|---------|
| `fig_mk_test_simulation.pdf` | Figure composite 4 panneaux (test poolé) |
| Texte stdout | Résultats numériques pour intégration manuscrit |
| `mk_per_gene.tsv` (script `mk_per_gene.py`) | Table MK **par gène** (Dn/Ds/Pn/Ps, DoS, NI, alpha, p_fisher, q_value), consommée par `mtbc-gene` pathway `--from-selection` |

### Les 4 panneaux de la figure

- **A** : Table de contingence MK (Dn, Ds, Pn, Ps) avec p-value et DoS
- **B** : Distribution nulle du nombre de NS parmi n variants aléatoires
- **C** : Fraction NS attendue après filtrage en fonction du biais
- **D** : P(100% NS) en fonction du biais, avec seuils alpha

## Utilisation

### Invocation directe

```bash
/bio:mk-ascertainment reproducibility/data/supplementary_table_S3_annotated.csv
```

### Invocation programmatique

```bash
cd <projet>/reproducibility/
python scripts/mk_test_and_ascertainment.py
```

### Adaptation à une nouvelle lignée

Le script est paramétré par :
1. Le chemin du CSV tier-annoté
2. Les chemins GB/GFF3 (défaut : `../../NC_000962.3.*`)
3. Le répertoire de sortie

Pour une nouvelle lignée (ex. L4.16), il suffit de :
1. Copier le script dans `L4.16/reproducibility/scripts/`
2. Ajuster les chemins en tête de fichier
3. Exécuter

## Intégration avec d'autres skills

| Skill | Relation |
|-------|----------|
| `bio:spdi-annotation` | Produit le CSV tier-annoté en entrée |
| `bio:convergent-evolution` | Le MK test renforce l'interprétation des convergences eccC2 |
| `bio:molecular-clock` | Complémentaire : datation vs pression de sélection |
| `bio:lineage-comparison` | Compare les profils MK entre lignées |
| `bio:mtbc-gene` (pathway) | Consomme `mk_per_gene.tsv` (`--from-selection`), narre les voies sous sélection avec sas de significativité, alimente la fiche Atlas |

## Intégration manuscrit

### Texte type pour Results (§ Core Mutational Profile)

> To disentangle this signal from the ascertainment bias inherent to the
> core-exclusive filter, we applied a McDonald-Kreitman-like framework
> (McDonald & Kreitman 1991) comparing fixed divergence (Tier 1-2:
> Dn non-synonymous, Ds synonymous) against within-lineage polymorphism
> (Tier 4: Pn non-synonymous, Ps synonymous). Fisher's exact test yields
> p = [VALUE], with DoS = [VALUE] (95% bootstrap CI: [LO, HI]).

### Texte type pour Limitations

> A simulation-based analysis (Supplementary Figure SX) directly quantifies
> the ascertainment bias: synonymous variants would need to be shared with
> sister lineages ≥[CRITICAL]× more often than non-synonymous variants for
> the observed ratio to become compatible with neutral expectation (P > 0.05).

### Références à ajouter

```bibtex
@article{McDonald1991,
  author  = {McDonald, John H and Kreitman, Martin},
  title   = {Adaptive protein evolution at the {Adh} locus in {Drosophila}},
  journal = {Nature},
  year    = {1991},
  volume  = {351},
  pages   = {652--654},
  doi     = {10.1038/351652a0}
}

@article{Stoletzki2011,
  author  = {Stoletzki, Nina and Eyre-Walker, Adam},
  title   = {Estimation of the neutrality index},
  journal = {Molecular Biology and Evolution},
  year    = {2011},
  volume  = {28},
  number  = {1},
  pages   = {63--70},
  doi     = {10.1093/molbev/msq249}
}
```

## Dépendances

```bash
pip install numpy scipy matplotlib
```

Python ≥ 3.9.

## Valeurs de référence (L4.15)

Pour calibration lors de l'application à d'autres lignées :

| Métrique | Valeur L4.15 |
|----------|-------------|
| p_syn Nei-Gojobori (H37Rv) | 0.2621 |
| MK Fisher p (Tier 1-2 vs 4) | 1.1 × 10⁻⁸ |
| DoS | +0.481 [+0.397, +0.565] |
| Alpha | +0.984 |
| Biais critique | 3.7× |
| Dn:Ds | 33:0 |
| Pn:Ps (Tier 4) | 68:63 |

## Codex script path note

Bundled script paths in this packaged copy are relative to the directory containing this `SKILL.md`. For sibling packaged skills, resolve the sibling directory in the same plugin cache before running scripts.
