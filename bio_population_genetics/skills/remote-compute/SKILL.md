---
name: remote-compute
description: >-
  Deploy long, memory-hungry, disk-hungry or GPU computations of the Guyeux group
  (FEMTO-ST) onto the two remote machines available over SSH: `mp` (standalone
  64-thread / 125 GB / 51 TB box, no scheduler) and `mh` (mesohelios Slurm
  cluster login node, A100 and L40 GPUs, 1 TB bigmem nodes, BeeGFS). Covers the
  choice between them, sbatch recipes, data staging, quota and filesystem traps,
  and job monitoring. Use when a computation needs more RAM, more disk, more
  cores, a GPU, or more wall-clock time than the laptop can give, or when asked
  to run something "sur mp", "sur mh", "sur le cluster", "en GPU", "en batch".
argument-hint: "<description du calcul> [--need gpu|ram=<Go>|disk=<Go>|cpus=<n>|hours=<h>]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# Déployer un calcul sur mp ou mh

## Préalable absolu

Les deux machines passent par le rebond `bilbo` et ne sont joignables que **VPN monté**. Claude ne
peut pas le monter (`sudo`, mot de passe) : demander à l'utilisateur de taper `! sudo vpn up`.

> [!WARNING]
> Un échec SSH donne `Connection timed out during banner exchange`, qui ressemble à une panne
> serveur. C'est le VPN dans la quasi-totalité des cas. Ne jamais conclure d'un échec SSH qu'un
> fichier ou une souche est absent de la machine.

## Sonder avant de choisir

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/remote-compute/scripts/remote_probe.py
python3 ${CLAUDE_PLUGIN_ROOT}/skills/remote-compute/scripts/remote_probe.py --need "gpu,ram=400"
```

La sonde donne charge, RAM libre, espace, quotas, nœuds Slurm libres, file d'attente, et une
recommandation. L'inventaire statique ne suffit pas : sur `mh` les nœuds passent en `drain` (3 des 5
nœuds GPU l'étaient au 2026-08-17), sur `mp` un pipeline peut tourner sans prévenir.

## Les deux machines (relevé du 2026-08-17)

| | `mp` (mesoprivate1) | `mh` (mesointeractive, cluster mesohelios) |
|---|---|---|
| OS | Ubuntu 20.04 | Rocky 8.7 |
| CPU | 2× Xeon Gold 6226R, **64 threads** (32 cœurs, HT) | frontale 4× Xeon Gold 6252, 96 cœurs ; nœuds de calcul 24 à 128 c |
| RAM | **125 Go**, plafond dur | 92 Go (mpi), 93-251 Go (smp), **503 Go** (gpu), **1 To** (bigmem, gpu_l40) |
| GPU | **aucun** | **3× A100-PCIE-40GB** par nœud gpu (5 nœuds), **2× L40** sur gpu_l40 |
| Ordonnanceur | **aucun**, tout à la main | **Slurm** (compte `disc`, QOS `normal`) |
| Durée max | illimitée | 8 jours (`mpi`, `smp`, `bigmem`, `visu`), **12 jours** (`gpu`, `gpu_l40`) |
| Espace de travail | **`/data/cguyeux`** (xfs 51 To, ~21,6 To libres) | **`/Work/Users/cguyeux`** (BeeGFS, quota **1024 Gio**, 221 Gio pris) ; `/Scratch` 1,1 To |
| À ne PAS utiliser | `/` et `$HOME` : **97 % pleins, 7 Go libres** | `$HOME` `/Home/Users/cguyeux` : **17 Go d'un quota de 20 Go** |
| Python | 3.8.10 système ; `samtools`/`bcftools` dans `/usr/bin` ; pas de conda | 3.6.8 système, donc **charger un module** |
| Autres | partagée : `/data` porte aussi `coffea`, `ncaron`, `predictops` | Lmod, apptainer, MATLAB, Gurobi, R 4.1.3, nextflow, modules `deep/pytorch-gpu`, `tensorflow-gpu`, `rapids-gpu`, `whisper` |

## Quelle machine

- **GPU** (torch, Boltz, RAPIDS, Whisper) : `mh`, partition `gpu` (A100 40 Go) ou `gpu_l40`. `mp` n'a
  aucun GPU, ne jamais y router du CUDA.
- **Plus de 125 Go de RAM** : `mh`, partitions `bigmem` ou `gpu_l40` (1 To), ou `gpu` (503 Go).
  Attention : `mpi` et `smp` ne donnent que ~92 Go par nœud, moins que `mp`.
- **Beaucoup de disque** (plusieurs To, FASTQ, CRAM, données intermédiaires) : `mp` et son `/data`.
  Le quota BeeGFS de `mh` est de 1 Tio seulement, déjà à 22 %.
- **Calcul long sans découpage possible** (au-delà de 8 jours) : `mp`, qui n'a pas de limite de
  temps. Sur `mh` il faudrait un job avec reprise.
- **Disponibilité immédiate** : `mp` (aucune file). Sur `mh` la partition `smp` était encombrée par
  41 jobs en attente d'un autre utilisateur au moment du relevé.
- **Parallélisme au-delà de 64 threads** : `mh` multi-nœuds (`mpi`, 24 c/nœud, 16 nœuds), mais
  seulement si le code sait vraiment faire du MPI. Sinon `mp` et ses 64 threads valent mieux qu'un
  job MPI qui n'utilise qu'un cœur.
- **Données TBannotator** (`results/`, `report.json`, `samples.tsv`) : `mp` obligatoirement, c'est là
  qu'elles vivent. Voir `fetch-tbannotator`.

## Ce qui est déjà installé (relevé du 2026-08-17)

Ne pas supposer qu'un outil est présent : les deux machines sont maigres.

- **`mp`** : `raxmlHPC` et `treetime` dans `/usr/bin`, plus `samtools` et `bcftools`. Python 3.8.10
  système. **Pas** de conda, **pas** de Lmod, ni `iqtree2`, ni `raxml-ng`, ni BEAST2, ni `mafft`.
- **`mh`** : **rien de phylogénétique**. En revanche Lmod (`anaconda3@2022.10` donne Python 3.9.13
  avec numpy/scipy/pandas, `miniconda3`, `nextflow`, `r@4.1.3`), `apptainer/1.1.8`, et dix
  environnements conda existants.

> [!NOTE]
> **`~/.conda` de `mh` est déjà un symlink vers `/Work/Users/cguyeux/.conda`** (depuis 2021) : les
> environnements conda ne consomment donc **pas** le quota NFS de 20 Go, contrairement à ce qu'on
> pourrait croire en lisant `du -sh ~` (qui ne suit pas les symlinks, d'où des chiffres qui ne
> s'additionnent pas). Le quota était mangé par `~/.cache/pip` (**8,7 Go**, purgé le 2026-08-17 avec
> `pip cache purge`, ramenant l'occupation de 81 % à 41 %) et par `~/.local/lib` (**8,2 Go** de
> `pip install --user` : torch, les bibliothèques `nvidia`, tensorflow, xgboost, pour python 3.6, 3.8
> et 3.9). Ces derniers ne sont pas un cache : ne pas les supprimer sans vérifier, et savoir qu'un
> `torch` installé en `--user` **masque** celui du module `deep/pytorch-gpu`, ce qui est une cause
> classique de « le module ne marche pas ».

### Environnement phylo prêt à l'emploi sur `mh` (créé le 2026-08-17)

`/Work/Users/cguyeux/envs/phylo`, monté avec micromamba 2.9.0 (`/Work/Users/cguyeux/bin/micromamba`,
plus rapide que le solveur `classic` de conda 23.3.1 disponible par module) :

| outil | version | appel |
|---|---|---|
| IQ-TREE | 3.1.3 | binaire nommé **`iqtree`**, pas `iqtree2` |
| RAxML-NG | 2.0.2 | **exige `LD_LIBRARY_PATH`**, voir ci-dessous |
| MAFFT | 7.526 | direct |
| TreeTime | 0.12.1 | direct (également dans `/usr/bin` sur `mp`) |
| FastTree, SeqKit | | direct |

```bash
# Recette qui marche pour tout l'environnement, y compris raxml-ng
P=/Work/Users/cguyeux/envs/phylo
ssh mh "LD_LIBRARY_PATH=$P/lib $P/bin/iqtree -s aln.fa -m GTR+G -T 8"
```

> [!WARNING]
> **Deux pièges de cet environnement, tous deux vérifiés.** (1) `raxml-ng` échoue sur
> `GLIBCXX_3.4.29 not found` : le `libstdc++` de Rocky 8 est trop ancien, et ni `micromamba run` ni
> `micromamba activate` ne corrigent le tir. Il faut **exporter `LD_LIBRARY_PATH=$PREFIX/lib`**,
> testé bon. (2) Sur BeeGFS, micromamba n'a pas pu faire de liens durs : les bibliothèques de l'env
> sont des **symlinks vers `/Work/Users/cguyeux/conda_pkgs`**. Un `micromamba clean` ou une purge de
> ce cache de 1,1 Go **casserait l'environnement**. Ne pas le nettoyer.

Smoke test passé : arbre JC sur 5 séquences produit par `iqtree`, Newick correct.

## Recettes

Modèles complets dans `references/sbatch_templates.sh` (CPU, GPU A100, bigmem, plus le lancement
sans ordonnanceur sur `mp`). L'essentiel :

```bash
# mh : soumettre, suivre, récupérer
scp travail.py mh:/Work/Users/cguyeux/monprojet/
ssh mh 'cd /Work/Users/cguyeux/monprojet && sbatch job.sbatch'
ssh mh 'squeue -u cguyeux'
ssh mh 'sacct -j <jobid> -o JobID,State,Elapsed,MaxRSS,ReqTRES%40'

# mh : test interactif court avant de soumettre un long job (2 min, alloué en quelques secondes)
ssh mh 'srun -p gpu --gres=gpu:A100:1 -t 00:05:00 --mem=8G nvidia-smi'

# mp : pas d'ordonnanceur, donc détacher explicitement et journaliser
ssh mp 'cd /data/cguyeux/monprojet && setsid nohup python3 travail.py > run_$(date +%Y%m%d_%H%M).log 2>&1 < /dev/null & disown'
```

> [!IMPORTANT]
> **`module load` ne marche pas en SSH non interactif.** La fonction shell de Lmod n'est pas définie,
> et `module load` échoue **en silence** : le job continue avec le Python 3.6.8 du système. Toujours
> passer par un shell de login :
> ```bash
> ssh mh 'bash -lc "module load anaconda3@2022.10/gcc-12.1.0 && python3 -V"'   # -> 3.9.13
> ```
> Dans un script `sbatch`, les `module load` fonctionnent normalement (Slurm ouvre un shell de login).

## Pièges vérifiés

- **Tuer une commande locale ne tue pas le processus distant.** Un `timeout` local ou un job
  d'arrière-plan interrompu laisse la commande tourner sur la machine distante, orpheline. Vécu le
  2026-08-17 : un `du -sh /data/current` a continué à charger `mp` après l'arrêt local. Vérifier
  après coup (`ssh mp 'ps -eo pid,etime,cmd | grep monmotif'`) et tuer explicitement.
- **Un `grep` sur `ps` se compte lui-même.** La ligne de commande envoyée par SSH contient le motif
  cherché. Écrire le motif de façon à ne pas apparaître littéralement (`snakemak[e]`) **et** exclure
  les wrappers (`grep -v "bash -c"`), sinon on croit qu'un pipeline tourne alors que non.
- **Écrire au mauvais endroit fait échouer le job en plein calcul**, pas au démarrage : `/` de `mp` a
  7 Go libres, donc pas de `/tmp` volumineux (utiliser `/data/cguyeux/tmp`), et `$HOME` de `mh` est à
  85 % de son quota NFS.
- **Le transfert passe par le rebond `bilbo`.** Pour de gros volumes, compresser avant
  (`tar czf - | ssh mp 'tar xzf - -C /data/cguyeux/…'`) et éviter les millions de petits fichiers,
  qui coûtent bien plus que leur taille.
- **`mp` est partagée.** Avant un calcul qui prend les 64 threads, vérifier qu'aucun run TBannotator
  n'est en cours (la sonde le dit) et que `/data` ne va pas être rempli au détriment des autres.

## Après le calcul

Rapatrier les résultats, pas les intermédiaires. Consigner dans le cahier de labo du projet le
`jobid` Slurm ou le fichier de log, la machine, la partition, le temps écoulé et le `MaxRSS` observé
(`sacct`) : c'est ce qui permet de dimensionner correctement la fois suivante au lieu de redemander
au hasard. Les mesures de dimensionnement d'un calcul répété méritent une entrée dans
`~/.claude/knowledge/`.
