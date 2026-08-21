---
name: pymlst
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST) for assessing bacterial
  clonality by core-genome and whole-genome MLST with pyMLST (Biguenet, Bordy,
  Atchon, Hocquet, Valot, Microbial Genomics 2023). Builds a local SQLite allele
  database from assembled genomes, calls cgMLST/wgMLST profiles, and produces
  allelic distance matrices, minimum-spanning trees and per-gene alignments for
  published research isolates of any bacterium (non-tuberculous mycobacteria,
  Pseudomonas, Klebsiella, Salmonella, Staphylococcus...). Use when: deciding
  whether isolates form a clonal group, typing a strain against a PubMLST or
  cgMLST scheme, or producing a distance matrix for a peer-reviewed manuscript.
argument-hint: "<repertoire d'assemblages FASTA | souche> [--scheme <schema>] [--wg|--cla]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# pyMLST : clonalité par cgMLST / wgMLST

## Provenance

Biguenet A, Bordy A, Atchon A, Hocquet D, Valot B. *Introduction and benchmarking of pyMLST:
open-source software for assessing bacterial clonality using core genome MLST.* Microbial Genomics
2023, 9(11), `10.1099/mgen.0.001126`. Le moteur officiel est
[`bvalot/pyMLST`](https://github.com/bvalot/pyMLST). La présente version du wrapper a été auditée
contre le commit `389679b18dad9f92c3f212b98fb6d9878f95bb5a`, pyMLST 2.3.2, sous
GPL-3.0-or-later. Le wrapper n'embarque aucun fichier du moteur. Voir `PROVENANCE.md` pour les
empreintes et les tests. L'équipe de Besançon (Chrono-environnement / CHU) doit être citée ; ne pas
présenter pyMLST comme un outil du groupe Guyeux.

## Quand cet outil est le bon, et quand il ne l'est pas

> [!IMPORTANT]
> **Ne pas l'utiliser pour typer du MTBC.** Le complexe tuberculosis est quasi clonal, sans
> recombinaison notable : sa structure se lit par **barcodes SNP de lignée** (`mtbc-lineages`,
> systèmes `guyeux`/`tblearn`/Coll/Napier via `tbannotator-mcp`), pas par MLST, et il n'existe pas de
> schéma cgMLST d'usage pour lui. Y appliquer pyMLST donnerait un résultat interprétable de travers.
>
> Le cas d'emploi est **hors MTBC** : mycobactéries non tuberculeuses (*M. abscessus*, *M. avium*),
> et les genres où le cgMLST est la référence de comparaison entre isolats.

Question à laquelle il répond : « ces isolats forment-ils un groupe clonal, et à quelle distance
allélique ? » Question à laquelle il ne répond pas : « quelle est l'histoire évolutive profonde de ce
clade ? » (là, alignement de SNP au génome entier plus `iqtree-lsd2`).

## Trois familles de commandes

| famille | rôle | commandes |
|---|---|---|
| `wgMLST` | wgMLST/cgMLST sur base locale | `create`, `add`, `add2`, `import`, `remove`, `mlst`, `distance`, `msa`, `gene`, `sequence`, `strain`, `stats`, `subgraph`, `recombination` |
| `claMLST` | MLST classique (7 gènes) | `create`, `import`, `search`, `search2`, `info`, `remove` |
| `pyTyper` | autres typages | `search` |

Le paquet installe aussi `pyMLST` pour les commandes communes, notamment `configure`. La recherche
dans des assemblages requiert BLAT, la recherche dans des lectures requiert KMA, et la production
d'alignements multiples requiert MAFFT. Vérifier ces exécutables avant un lot :

```bash
pyMLST --version
command -v wgMLST
command -v blat
command -v kma
command -v mafft
```

Enchaînement typique, base locale SQLite puis analyse :

```bash
wgMLST create --species <espece> --version <version_schema> base.db schema.fasta
wgMLST add --strain <identifiant> base.db assemblage.fasta
wgMLST mlst --output profils.tsv base.db
wgMLST distance --output distances.tsv base.db
wgMLST msa --output core.fasta base.db
```

Entrées : assemblages FASTA (`.fasta`, `.fna.gz` compressés acceptés). Donc **si on part de lectures
brutes, assembler d'abord** : c'est exactement ce que fait `bactrline`, qui appelle d'ailleurs pyMLST
en fin de course.

## Pièges à connaître avant d'interpréter

**La distance allélique n'est pas une distance évolutive.** Un allèle diffère qu'il porte un SNP ou
vingt : la matrice compresse l'information et ne se convertit pas en temps. Pour de la datation,
passer par les SNP (`molecular-clock`, `iqtree-lsd2`).

**Le schéma choisi détermine le résultat.** Deux schémas cgMLST de la même espèce ne donnent pas les
mêmes distances : consigner le schéma, sa source et sa version dans le manuscrit, sinon le chiffre
n'est pas reproductible. La commande `stats` sert à cela, elle documente la base réellement utilisée.

**Les gènes manquants faussent les comparaisons.** Un assemblage fragmenté perd des loci et paraît
artificiellement distant. Vérifier la complétude du core (`stats`, et le QC d'assemblage de
`bactrline` : QUAST, CheckM2) avant de conclure à une divergence.

**La base est un fichier**, donc versionner ou au moins horodater `base.db` : ajouter des souches
modifie les distances de toutes les autres si le core change.

## Où calculer

Une base de quelques dizaines d'assemblages tient sur le portable. Au-delà, ou pour un `add2` de
plusieurs centaines de génomes, passer sur `mp` ou `mh` : voir `remote-compute`. Vérifier la version
réellement installée avant l'analyse ; ne pas confondre un ancien environnement bioconda avec le
commit 2.3.2 audité ici.

## Composition

`bactrline` (lectures brutes → assemblages QC) → **`pymlst`** (clonalité) → `sci-figure` /
`geo-map` (MST, carte des isolats). Pour le mobilome des mêmes souches, `panisa`. Pour la résistance,
`card` et `resistance-catalogue`.
