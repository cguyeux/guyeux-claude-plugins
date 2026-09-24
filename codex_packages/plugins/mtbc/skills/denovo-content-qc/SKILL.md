---

name: denovo-content-qc
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST) : trier le contenu génomique
  "absent de H37Rv" d'une lignée MTBC (L8, L9, L10, écotypes animaux) assemblé de
  novo. Module ancestral, accessoire de pangénome, ou CONTAMINANT ? Outils
  contamination_filter, pangenome_map, island_distribution (BLAST vs H37Rv,
  M. bovis, M. leprae). Use when: trier des contigs de novo, mesurer l'accessoire
  d'une souche, valider un "îlot spécifique".
  Portée : développé sur le MTBC, applicable à toute bactérie clonale (Yersinia,
  Leptospira...) — la question « ancestral, accessoire ou contaminant ? » est générique et
  se pose avec plus d'acuité hors MTBC (plasmides, pangénome plus ouvert). Hors MTBC :
  fournir le panel de génomes de référence du genre pour le BLAST.
---

# denovo-content-qc : QC du contenu de novo "H37Rv-absent" d'une lignée MTBC

Quand on caractérise une lignée/sous-lignée MTBC basale ou rare, on assemble de novo les
reads qui NE mappent PAS sur H37Rv (le contenu H37Rv-absent), et on interprète les contigs
comme des "îlots ancestraux". Trois erreurs guettent, que ce skill outille :

1. **Contaminant pris pour un îlot** : un contig d'ADN étranger dans la run (plasmide, phage,
   autre organisme) ressemble à un "nouveau" module. → `contamination_filter.py`.
2. **"Absent de H37Rv" confondu avec "spécifique de la lignée"** : H37Rv est une L4 (moderne,
   génome réduit) ; du contenu absent de H37Rv est souvent ancestral et conservé ailleurs, y
   compris chez les lignées ANIMALES. → `island_distribution.sh`.
3. **"Absent du génome fermé d'UNE souche" confondu avec "contaminant"** : une lignée a un
   pangénome (génome accessoire variable par souche). L'absence du génome fermé d'une souche
   ne prouve pas la contamination. → `contamination_filter.py` (verdict PANGENOME_CANDIDATE
   vs SINGLETON_REVIEW) + `pangenome_map.sh`.

## Les trois outils (dans `scripts/`)

### 1. `contamination_filter.py` : trier les contigs vs le génome FERMÉ de la lignée
Pour chaque contig de chaque assemblage `spades_*_unmapped`, BLASTn sur le génome fermé de la
lignée (ex. CP048071.1 pour L8). Verdicts :
- **L8_CLOSED_GENOME** : présent (qcov ≥ 50 %, id ≥ 90 %) → vrai contenu de lignée (SUFFISANT).
- **PANGENOME_CANDIDATE** : absent du génome fermé mais présent chez ≥ 2 souches → accessoire probable.
- **SINGLETON_REVIEW** : absent, 1 seule souche, couverture correcte → contaminant OU élément privé,
  à trancher par ID d'espèce (BLAST nt / skani / species-id).
- **LOW_COV_SINGLETON** : absent, 1 souche, faible couverture.
Colonne GC% + hit sur panel mycobactérien (M. bovis/M. leprae). Sortie TSV.
**Principe clé** : présent-dans-le-génome-fermé est SUFFISANT pour "vrai" ; absent n'est PAS
suffisant pour "contaminant" (pangénome). Auto-validation : les vrais îlots reviennent à 100 % qcov.

### 2. `pangenome_map.sh` : pangénome par mapping (bwa + samtools)
Mappe les reads de chaque souche sur le génome fermé de la lignée. Sortie par souche : breadth
(% couvert), profondeur moyenne, fenêtres à couverture 0 ≥ 500 pb (= régions de la référence
absentes de la souche = versant réciproque du pangénome), fraction de reads non mappés (= contenu
EN PLUS de la référence), + extraction des reads non mappés (pour assemblage de l'accessoire).
Inclure la souche d'origine du génome fermé comme CONTRÔLE POSITIF (doit s'auto-mapper ~100 %).
Discriminant contaminant vs accessoire mycobactérien : GC% des reads non mappés (~65 % = myco)
+ fraction mappant sur M. bovis (représentant large du MTBC).

### 3. `island_distribution.sh` : spécificité d'un îlot par BLAST vs panel
Extrait chaque îlot du génome fermé (coordonnées) et le BLASTe (qcov) contre un panel de génomes
de référence : H37Rv (L4), M. bovis (lignée ANIMALE, le meilleur "second point" local, s'il a
l'îlot, ce n'est PAS spécifique de la lignée étudiée), M. leprae (outgroup distant). Matrice
îlot × référence. Un îlot vraiment restreint est absent de H37Rv ET de M. bovis. Extensible :
ajouter un génome par lignée dans `REFS` pour compléter la matrice.

## Adaptation à une nouvelle lignée (comme mk-ascertainment)

Les scripts utilisent un résolveur de racine projet (remonte jusqu'à `cahier_de_labo.md`) et
attendent, sous la racine du projet lignée :
- `data/ref/<GENOME_FERME>.fasta` (+ index BWA/BLAST) = génome fermé de référence de la lignée.
- `résultats/assemblies/spades_<SRA>_unmapped/contigs.fasta` = assemblages des reads non-mappés.
- `data/reads/<SRA>_{1,2}.fastq[.gz]` = reads bruts (pour pangenome_map).
Points à éditer par lignée (marqués dans les scripts) : le nom du génome fermé, les COORDONNÉES
des îlots (`ISLANDS` dans island_distribution.sh), les seuils. Le panel mycobactérien
(M. bovis LT708304.1, M. leprae NC_002677.1) vit dans `investigate_phylo/resources/`.

## Pièges documentés (KB tuberculosis.md)

- Un "portrait" narratif généré par LLM peut contredire ses propres dumps bruts → toujours croiser
  avec le mapping/BLAST réel (GC%, couverture, présence dans le génome fermé).
- `/usr/bin/spades.py` peut être cassé (Python 3.14) → utiliser le SPAdes de l'env conda `tbannot`.
- Un NS/S de marqueurs lignée-définissants > ~3 = drapeau d'artefact, pas de sélection (voir
  mk-ascertainment).

## Couverture et place dans l'écosystème

Champ d'application : les projets de caractérisation de lignées/sous-lignées MTBC
**basales ou rares** : L8, L9, L10, ainsi que les **écotypes animaux** (M. bovis,
M. caprae, M. pinnipedii, M. microti…).

Trois usages typiques : (1) on vient d'assembler de novo les reads non-mappés-H37Rv
d'une lignée et on veut trier vrai-contenu vs contaminant ; (2) on veut mesurer le
génome accessoire propre d'une souche ; (3) on veut **prouver qu'un « îlot spécifique »
l'est vraiment** (vs conservé ailleurs) **avant de l'écrire dans un manuscrit**.

Skills complémentaires :

| Skill | Rôle distinct |
|---|---|
| `strain-qc` | QC d'une souche (qualité du séquençage/assemblage), en amont |
| `species-id` | identification d'espèce d'un contaminant repéré ici |
| `pangenome-enrichment` | pangénome calculé sur génomes complets (pas par mapping) |

## Origine

Extrait du projet `mtbc/L8/` (réanalyse de la lignée 8, 2026-07), où ces trois outils ont
disqualifié un faux "Helitron-MtL8", réfuté des "îlots spécifiques L8" (M. bovis les a à 100 %),
et confirmé que RW-TB008 représente bien le cœur L8.

## Codex workflow guardrail

This packaged copy imports a Claude-origin project workflow into Codex. Before writing project registers, moving BDD files, changing Atlas content, appending remote queues, archiving a project, or launching remote compute, require an explicit user request in the current turn. Use recoverable operations only, keep project provenance boundaries, and follow the global rule that files are moved to the trash rather than permanently deleted.
