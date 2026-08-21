---
name: mixed-infection
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST) for detecting mixed
  infections and within-host heterogeneity in published MTBC research isolates,
  with QuantTB (Anglin/Abeel lab, BMC Genomics 2020) for identifying and
  quantifying co-infecting strains, and binoSNP (Research Center Borstel,
  Scientific Reports 2020) for low-frequency antimicrobial-resistance alleles
  under a binomial model. Use when: a strain shows an impossible marker
  combination or an inflated variant count, a resistance allele appears at
  intermediate frequency, a candidate new sublineage must be ruled out as an
  artefact of co-infection, or within-host diversity is the object itself.
argument-hint: "<souche|liste> [--quantify] [--resistance]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# Infections mixtes et hétérogénéité intra-hôte

## Pourquoi cela compte au-delà de la clinique

Une infection mixte n'est pas seulement un fait épidémiologique : c'est un **générateur de faux
résultats phylogénomiques**. Deux souches dans un même échantillon produisent, après appel de
variants majoritaire, un profil chimérique qui porte des marqueurs de deux lignées à la fois. Les
conséquences sont exactement celles que nos travaux de subdivision cherchent à éviter :

- une combinaison de marqueurs **impossible** au regard de la nomenclature, lue à tort comme une
  lignée nouvelle ;
- un **compte de variants anormalement élevé** (les positions hétérozygotes s'ajoutent) ;
- des marqueurs « exclusifs » d'un clade candidat qui ne sont que le second génotype présent ;
- une résistance apparemment discordante entre génotype et phénotype, parce que l'allèle résistant
  n'est porté que par une fraction de la population.

> [!IMPORTANT]
> **Avant d'annoncer un clade nouveau à faible effectif, écarter l'infection mixte.** C'est un modèle
> nul alternatif au même titre que l'homoplasie ou l'erreur de placement, et il est testable. La
> discipline du dépôt sur les marqueurs (voir `taxonomy-node-validation` dans la base de
> connaissances) mesure la fuite et le portage, mais un profil chimérique peut passer ces filtres.

## Deux outils, deux questions

| outil | question | référence |
|---|---|---|
| **QuantTB** | combien de souches dans cet échantillon, et dans quelles proportions ? | Abeel lab, *BMC Genomics* 2020, `10.1186/s12864-020-6486-3`, GPL-3.0, `github.com/AbeelLab/quanttb` |
| **binoSNP** | cet allèle de résistance existe-t-il à basse fréquence ? | Research Center Borstel (`ngs-fzb`), *Sci Rep* 2020, `10.1038/s41598-020-64708-8`, GPL-3.0, workflow R |

QuantTB travaille sur des SNP et compare l'échantillon à une base de génotypes de référence : il
identifie **et** quantifie. binoSNP teste chaque position candidate sous un **modèle binomial**, ce qui
lui permet d'appeler un allèle minoritaire là où un appel majoritaire le rejette.

Note de provenance utile : binoSNP vient de **Borstel**, avec qui le groupe a déjà un dossier
(`~/docs/codes/mtbc/Borstel/`). L'outil et l'interlocuteur vont ensemble.

## Ce que nos données permettent, et ce qu'elles ne permettent pas

> [!WARNING]
> **Le `bdd/` local ne conserve pas le signal sous-clonal.** `spdi.txt` et le `report.json` portent des
> appels majoritaires. Pour toute question d'hétérogénéité intra-hôte, il faut remonter aux données
> qui gardent les comptes d'allèles : `annotated.vcf` et `mapped.cram` sur `mp`
> (`/data/current/run/results/<SRA>/`), où les champs de profondeur par allèle existent. Voir
> `fetch-tbannotator` et `remote-compute` (VPN requis).
>
> **Et le seuil d'appel de la chaîne masque le phénomène par construction** : les critères sont
> profondeur ≥ 10, qualité d'erreur < 5 %, et **≥ 90 % des lectures soutenant la mutation**. Un allèle
> présent chez 30 % de la population est donc invisible dans nos sorties standard, non parce qu'il
> n'existe pas, mais parce qu'il a été filtré. C'est la raison même d'utiliser ces deux outils.

## Garde-fous d'interprétation

**Une fraction n'est pas une preuve de co-infection.** Un allèle à fréquence intermédiaire peut venir
d'une contamination croisée en laboratoire, d'un mapping ambigu dans une région répétée (PE/PPE, IS),
ou d'une duplication. Vérifier la position contre les régions masquées avant de conclure, et exiger
plusieurs positions cohérentes plutôt qu'une seule.

**La profondeur commande, ici encore.** Détecter une sous-population à 5 % demande une profondeur qui
la rende comptable : sur nos souches MTBC (36× à 538×, mesuré) c'est jouable, sur une cohorte à 5× non.
Trier sur `meandepth` de `coverage_stats.tsv` avant de lancer.

**Distinguer les trois explications d'un phénotype discordant** : allèle minoritaire réel, mutation
hors du catalogue interrogé (`resistance-catalogue`), ou résistance non génétique. Les trois demandent
des vérifications différentes, et seule la première relève de ce skill.

## Composition

`fetch-tbannotator` (obtenir VCF et CRAM) → **`mixed-infection`** (l'échantillon est-il pur ?) →
`strain-qc` (la souche est-elle exploitable ?) → `mtbc-lineages` / `pectinated-subclade-mining` (le
clade candidat survit-il à l'écartement de l'infection mixte ?) → `resistance-profiler` pour le volet
allèles de résistance.
