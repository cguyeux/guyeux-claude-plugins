---

name: bactrline
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST) wrapping bactRline, the
  Snakemake workflow of B. Valot for bacterial genome assembly and
  characterisation: read trimming (TrimGalore, Filtlong), assembly (SPAdes for
  Illumina, Flye for Oxford Nanopore), quality control (QUAST, Kraken2, CheckM2),
  annotation and typing (AMRFinderPlus, pyMLST), optional plasmid detection
  (Platon, PlasClass). Use when: turning raw reads or SRA accessions of a
  published research isolate into an assembled, QC'd and typed genome for any
  bacterium beyond the MTBC (non-tuberculous mycobacteria, other genera), or when
  an analysis needs assemblies that do not exist yet.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# bactRline : assemblage et caractérisation de génomes bactériens

## Provenance et statut

Le moteur décrit est le workflow Snakemake officiel
[`bvalot/bactrline`](https://github.com/bvalot/bactrline), développé par Adeline Gagnon,
Ana Temtem et Benoît Valot. La présente version du wrapper a été auditée contre le commit
`b87e2b19198629f453a8c05607b18ae7aa8a80fb` du 2026-07-07. Ce commit est distribué sous
GPL-3.0-only. Le wrapper n'embarque aucun fichier du moteur. Voir `PROVENANCE.md` pour les
empreintes et les limites de redistribution.

> [!WARNING]
> **Épingler un commit.** Sans release publiée, l'amont peut changer entre deux exécutions et rendre
> un résultat non reproductible. Le commit audité ci-dessus est le défaut reproductible de ce skill.
> Un commit plus récent n'est utilisable qu'après nouvel audit de la licence, de la configuration et
> du dry-run, avec consignation du SHA dans le cahier de laboratoire.

```bash
git clone https://github.com/bvalot/bactrline.git
git -C bactrline checkout --detach b87e2b19198629f453a8c05607b18ae7aa8a80fb
```

## Ce qu'il enchaîne

| étape | outils | remarque |
|---|---|---|
| prétraitement | TrimGalore (Illumina), Filtlong (ONT) | |
| assemblage | SPAdes (courtes), Flye (longues) | c'est l'étape coûteuse |
| QC | QUAST, Kraken2, CheckM2 | Kraken2 et CheckM2 exigent de **grosses bases** |
| annotation, typage | AMRFinderPlus, pyMLST | voir le skill `pymlst` |
| plasmides (option) | Platon, PlasClass | |

Entrées : Illumina appairé, Oxford Nanopore, ou **accessions SRA**. Sorties : trois rapports dans
`workflow/reports/` (qualité d'assemblage, annotation MLST + résistances + virulence, résumé génique).

## La vraie difficulté n'est pas le pipeline, ce sont les bases de données

> [!IMPORTANT]
> Kraken2, CheckM2 et AMRFinderPlus téléchargent chacun une base : plusieurs dizaines de gigaoctets
> au total. Trois conséquences.
>
> 1. **Ne jamais les laisser atterrir dans `$HOME`.** Sur `mh`, le quota est de 20 Go, et sur `mp` le
>    `/` est à 97 % avec 7 Go libres. Les bases vont dans `/data/cguyeux/db/` (mp, 21,6 To libres) ou
>    `/Work/Users/cguyeux/db/` (mh, quota BeeGFS de 1 Tio dont ~800 Gio disponibles).
> 2. **`snakemake --use-conda` crée aussi des environnements**, qui prennent plusieurs gigaoctets.
>    Poser `CONDA_PKGS_DIRS` et `--conda-prefix` hors de `$HOME` pour la même raison.
> 3. Les télécharger **une fois**, les réutiliser entre projets, et noter où elles sont : refaire un
>    téléchargement de 50 Go parce qu'on a oublié le chemin est le coût caché de ce genre de chaîne.

## Où faire tourner

L'assemblage est exactement le profil « calcul distant » : plusieurs heures par génome, quelques
gigaoctets de fichiers intermédiaires par échantillon.

- **`mp`** quand il y a du volume : 64 threads, `/data` avec 21,6 To libres, aucune file d'attente,
  aucune limite de temps. C'est le choix par défaut pour un lot.
- **`mh`** pour paralléliser franchement : un job Slurm par échantillon en tableau (`--array`), sur
  `mpi` ou `smp`. Mais le quota BeeGFS de 1 Tio devient contraignant si on garde les intermédiaires.

Recettes `sbatch`, sonde d'état des deux machines et pièges (VPN, `module load` en SSH non
interactif) : skill `remote-compute`.

```bash
# toujours commencer par un essai à blanc, puis UN échantillon
snakemake --snakefile workflow/Snakefile --configfile config/config.yml --use-conda --conda-prefix /data/cguyeux/conda_envs --dry-run
snakemake --snakefile workflow/Snakefile --configfile config/config.yml --use-conda --conda-prefix /data/cguyeux/conda_envs --cores 16
```

## Garde-fous

**Un assemblage n'est pas une vérité.** CheckM2 (complétude, contamination) et QUAST (N50, nombre de
contigs) ne sont pas décoratifs : un assemblage fragmenté fait perdre des loci à `pymlst` et paraître
une souche artificiellement distante, et une contamination détectée par Kraken2 invalide tout ce qui
suit. Lire les trois rapports avant d'utiliser les assemblages en aval.

**Ne pas ré-assembler ce qui existe.** Pour le MTBC, la chaîne TBannotator porte déjà `contigs.fasta`
et les alignements (`mapped.cram`) pour ~136 800 souches : voir `fetch-tbannotator`. Ce pipeline sert
aux espèces et aux isolats **qui n'y sont pas**.

**Vérifier la littérature avant de séquencer ou d'assembler en masse** (`lit-review`) : un assemblage
public existe peut-être déjà chez NCBI, auquel cas `bioproject-scout` et `ncbi-pathogen-detection`
coûtent infiniment moins cher qu'une campagne de calcul.

## Composition

**`bactrline`** (lectures → assemblages QC) → `pymlst` (clonalité) et `panisa` (mobilome ab initio)
→ `card` / `resistance-catalogue` (résistance) → `sci-figure`, `geo-map` (figures).
