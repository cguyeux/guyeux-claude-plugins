---
name: yersinia-resources
description: >-
  Academic research database client (Guyeux group, FEMTO-ST) for genus Yersinia:
  Yersiniomics multi-omics database, BIGSdb-Pasteur Yersinia (genus-wide cgMLST
  and species identification), the Y. enterocolitica cgMLST surveillance scheme,
  plus the routes for plague palaeogenomics of published research isolates
  (ancient Y. pestis genomes). Use when: identifying or typing a Yersinia isolate,
  looking for a cgMLST scheme for the genus, situating an ancient Y. pestis genome
  in the published phylogeny (Black Death, Silk Road, Bronze Age lineages), or
  transposing an MTBC method to Y. pestis.
argument-hint: "<souche|question> [--cgmlst] [--ancien]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebFetch
---

# Yersinia : ressources et voies d'analyse

## Pourquoi ce skill existe

*Y. pestis* apparaît dans treize de nos SKILL.md, toujours **de biais** : par l'ADN ancien
(`spaam-community`, `spaam-ancient-metagenome-dir`), par la géographie historique (`orbis`, `owtrad`,
`pleiades`), par les bases généralistes (`enterobase`, `ncbi-pathogen-detection`). Aucun skill ne
portait les ressources **propres au genre**. C'est ce trou que celui-ci comble, sans dupliquer les
autres, vers lesquels il renvoie.

## Trois ressources du genre

| ressource | ce qu'elle apporte | accès |
|---|---|---|
| **BIGSdb-Pasteur Yersinia** | cgMLST à l'échelle du **genre entier**, identification d'espèce et typage ; l'instance de référence | `bigsdb.pasteur.fr/yersinia`, `10.1128/spectrum.00504-24` |
| **Y. enterocolitica cgMLST** | schéma et base de surveillance génomique en France, détection d'événements groupés | même instance BIGSdb |
| **Yersiniomics** | base **multi-omique** interactive du genre (génomique, transcriptomique, protéomique) | fiche bio.tools `yersiniomics` |

> [!IMPORTANT]
> **Le cgMLST est ici la méthode de référence, contrairement au MTBC.** *Yersinia* n'est pas quasi
> clonal comme le complexe tuberculosis : la comparaison entre isolats passe par les allèles, pas par
> des barcodes SNP de lignée. Ne pas transposer mécaniquement les réflexes MTBC. L'outillage cgMLST
> local est `pymlst` (plugin `bio_bacteria`), qui construit une base d'allèles locale et rend
> distances et arbres.

## Transposer une méthode MTBC vers Y. pestis, et ce qui résiste

La base de connaissances porte une entrée dédiée à cet exercice
(`toolkit-transfer-clonal-bacteria`) : la dichotomie utile est **moteur** contre **infrastructure**.
Une méthode agnostique de l'espèce se transfère par simple changement de référence
(H37Rv → CO92 pour *Y. pestis*) ; ce qui ne se transfère pas, c'est l'infrastructure, à commencer par
la base de 136 800 génomes préanalysés, qui n'a pas d'équivalent.

Deux outils du plugin s'y prêtent particulièrement :

- **`pathotypr`** (marqueurs SNP fournis par l'utilisateur, hors ligne, agnostique du pathogène,
  `github.com/PathoGenOmics-Lab/pathotypr`, AGPL) : la voie la plus directe pour appliquer une banque
  de marqueurs maison à *Y. pestis* sans réécrire un classifieur ;
- **`panisa`** : le mobilome ab initio ne demande qu'un BAM, donc il fonctionne tel quel sur *Yersinia*
  (IS100, IS1541 y sont abondantes et jouent un rôle dans l'évolution du genre).

## ADN ancien : ne pas rouvrir ce qui existe

Pour un génome ancien de *Y. pestis* (Peste noire, Justinienne, lignées de l'âge du Bronze),
l'itinéraire est déjà outillé ailleurs : `spaam-ancient-metagenome-dir` pour l'inventaire des jeux
publiés, `spaam-community` pour les méthodes de paléogénomique, `bayesian-skyline` et
`beast2-dating` pour la datation, `paleoclimate` et `orbis`/`owtrad` pour le cadre géo-historique.
Ce skill ne fait que pointer vers eux.

> [!CAUTION]
> **La damage pattern est une condition d'admissibilité, pas un détail.** Un génome ancien sans
> profil de déamination attendu, sans court fragment, sans authentification, n'est pas un génome
> ancien : c'est une contamination moderne possible. Toute conclusion phylogénétique sur du matériel
> ancien exige cette vérification en amont, et `spaam-community` en porte les critères.
>
> Et **un réservoir n'est pas une chaîne de transmission** : la présence de *Y. pestis* chez un rongeur
> (marmottes d'Asie centrale, cf. la ressource `iMarmot` repérée par `biotools`) documente un foyer
> enzootique, elle ne prouve pas un lien avec un épisode épidémique humain daté.

## Composition

**`yersinia-resources`** (situer, typer) → `pymlst` (clonalité cgMLST) → `panisa` (mobilome) →
`iqtree-lsd2` / `beast2-dating` (phylogénie, datation) → `geo-map` (cartographie) →
`spaam-*` pour tout ce qui est ancien. `biotools --preset yersinia` pour la veille outillage.
