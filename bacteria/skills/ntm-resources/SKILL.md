---
name: ntm-resources
description: >-
  Academic research database client (Guyeux group, FEMTO-ST) for non-tuberculous
  mycobacteria (NTM): NTM-DB genomic resource, Mabellini structural proteome of
  M. abscessus, and MAC-INMV-SSR genotyping of the M. avium complex including
  subsp. paratuberculosis. Use when: identifying or typing an NTM isolate from
  published research data, looking for a genomic or structural resource for
  M. abscessus, M. avium or another environmental mycobacterium, or checking
  whether an MTBC method transposes to an NTM species.
argument-hint: "<espece|souche|question> [--genotypage] [--structure]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebFetch
---

# Mycobactéries non tuberculeuses : ressources

## Pourquoi séparer les NTM du MTBC

Les NTM (*M. abscessus*, *M. avium*, *M. ulcerans*, *M. marinum*, *M. chelonae*...) ne se traitent pas
comme le complexe tuberculosis, pour trois raisons de fond qui commandent tout le reste :

1. **Elles sont environnementales et non obligatoirement pathogènes** : la diversité intra-espèce est
   bien plus grande, et le concept de « lignée » au sens MTBC n'y a pas d'équivalent direct.
2. **Elles recombinent**, donc la clonalité se lit par cgMLST ou par identité de génome
   (voir `pymlst`), pas par barcodes SNP.
3. **Aucune chaîne préanalysée n'existe** pour elles chez nous : il faut assembler
   (`bactrline`) avant de comparer.

Corollaire : un réflexe MTBC appliqué tel quel à une NTM donne un résultat interprétable de travers.
La base de connaissances porte l'analyse générale de ce transfert (`toolkit-transfer-clonal-bacteria`).

## Trois ressources

| ressource | contenu | accès et citation |
|---|---|---|
| **NTM-DB** | base génomique dédiée aux NTM, avec outils intégrés ; la plus récente des trois | [site](https://ngdc.cncb.ac.cn/ntmdb/), [prépublication](https://doi.org/10.1101/2025.07.22.666127) |
| **Mabellini** | protéome **structural** de *M. abscessus* à l'échelle du génome, évaluation de cibles antimicrobiennes prospectives | [site historique](https://www.mabellinidb.science/), [article](https://doi.org/10.1093/database/baz113) |
| **MAC-INMV-SSR** | génotypage du complexe *M. avium*, dont *M. avium* subsp. *paratuberculosis*, par SSR et MIRU-VNTR | [site historique](http://mac-inmv.tours.inra.fr/), [article](https://doi.org/10.1016/j.meegid.2019.104075) |

> [!NOTE]
> **NTM-DB est décrit par une prépublication de 2025, mais sa version 1.0 est annoncée en ligne depuis
> 2023.** Vérifier sa complétude et sa fraîcheur pour l'espèce visée avant de s'y fier comme source
> unique. Mabellini (article de 2019) et MAC-INMV-SSR (article paru en 2020) sont plus anciens. Lors de
> l'audit du 2026-08-21, NTM-DB répondait, tandis que les deux sites historiques n'étaient pas
> reproductiblement joignables depuis l'hôte d'audit. Ce constat de transport ne prouve ni leur arrêt
> définitif ni l'absence de leurs données ailleurs.

> [!CAUTION]
> **Accès public ne signifie pas licence générale de redistribution.** La licence affichée par NTM-DB
> couvre son site, mais les séquences et métadonnées issues de GenBank, RefSeq ou d'articles gardent
> leur provenance et leurs conditions propres. Les licences des contenus de Mabellini et de
> MAC-INMV-SSR n'ont pas été établies par cet audit. Citer la ressource et son article, conserver les
> identifiants d'origine, et ne pas redistribuer en bloc sans droits explicites.

Les statuts, preuves et limites exactes sont consignés dans `references/resources.json` et
`PROVENANCE.md`. Les relire avant toute collecte automatisée ou affirmation de disponibilité.

## Le piège taxonomique, propre à ce groupe

> [!WARNING]
> **Les noms de genre ont été éclatés.** Une partie des anciennes « *Mycobacterium* » sont devenues
> *Mycobacteroides* (dont *M. abscessus*), *Mycolicibacterium* et *Mycolicibacter*.
> Conséquences pratiques : une recherche par nom rate la moitié des entrées selon la base interrogée,
> et deux articles peuvent parler du même organisme sous deux binômes. Toujours chercher les deux
> formes, et fixer dans le manuscrit le binôme retenu avec sa source. `species-id` traite
> l'identification, `ontologies` la mise en correspondance des noms.

## Enchaînement type pour un isolat NTM

1. **Identifier l'espèce** avant tout (`species-id`, Kraken2 via `bactrline`) : une comparaison
   d'allèles entre deux espèces différentes ne veut rien dire.
2. **Assembler** si l'on part de lectures (`bactrline` : SPAdes ou Flye, QC par QUAST et CheckM2).
3. **Typer** par cgMLST avec `pymlst`, en consignant le schéma et sa version, ou par MIRU-VNTR/SSR pour
   le complexe *M. avium* (MAC-INMV-SSR).
4. **Mobilome** avec `panisa` si les éléments mobiles sont en jeu : les NTM en portent beaucoup, et
   aucun panel préétabli ne les couvre.
5. **Structure** avec Mabellini pour *M. abscessus*, ou `boltz` pour une prédiction de complexe.

## Composition

`bactrline` (assemblage) → `species-id` (qui est-ce ?) → **`ntm-resources`** (quelles bases) →
`pymlst` (clonalité) → `panisa` (mobilome) → `card` / `resistance-catalogue` (résistance) →
`biotools --preset mycobacteries` pour la veille.
