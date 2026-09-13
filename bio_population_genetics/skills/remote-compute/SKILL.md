---
name: remote-compute
description: >-
  Deploy long, memory-hungry, disk-hungry or GPU computations onto the two remote
  machines reachable over SSH: `mp` (standalone 64-thread / 125 GB / 51 TB box, no
  scheduler) and `mh` (Helios, the Slurm cluster of the Mesocentre de calcul de
  Franche-Comte: A100 and L40 GPUs, 1 TB bigmem node, BeeGFS). Any discipline, not
  only bioinformatics: model training, LLM inference, audio transcription, OCR of
  scanned documents, simulation, optimisation, GIS, MATLAB, large data processing.
  Covers choosing between the two, Slurm QOS ceilings, sbatch recipes, module and
  architecture traps, data staging, local scratch, job chaining, and the
  mesocentre's other services. Use when a computation needs more RAM, disk, cores,
  a GPU or more wall-clock time than the laptop can give, or when asked to run
  something "sur mp", "sur mh", "sur le cluster", "en GPU", "en batch", "sur
  Helios", "au mesocentre".
argument-hint: "<description du calcul> [--need gpu|ram=<Go>|disk=<Go>|cpus=<n>|hours=<h>]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# Déployer un calcul sur mp ou mh

Ce skill ne concerne pas que la bioinformatique. Tout calcul qui déborde le portable relève de lui :
entraînement et inférence de modèles, transcription audio, OCR de documents scannés, simulation,
optimisation sous Gurobi, traitement SIG, MATLAB, gros volumes de données.

## Préalable absolu

Toutes les machines du mésocentre passent par le rebond `bilbo` et ne sont joignables que **VPN
monté** : `mp` (mesoprivate1), `mh` (mesohelios1), `ml` (mesologin1, cluster Lumière) et `ms`
(mesoshared), plus `tickets.femto-st.fr` et les autres services internes.

**[2026-09-06] Le VPN se monte tout seul, ne plus le demander à l'utilisateur.** L'affirmation
inverse, portée ici depuis le 2026-08-17, n'avait jamais été vérifiée : `sudo -n -l` montre un
`NOPASSWD: ALL` sur cette machine, donc `sudo -n /usr/local/bin/vpn up` réussit sans interaction.
Premier geste de toute session distante, idempotent et à coût nul si le tunnel est déjà debout :

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/remote-compute/scripts/vpn_ensure.sh mp   # ou mh, ml, ms
```

Le script monte le tunnel si besoin, attend l'adresse `10.248.x.x`, puis teste `bilbo` **et** l'hôte
visé avec `ConnectTimeout=45`. Il ne bascule sur « demander à l'utilisateur » que si `sudo -n`
échoue vraiment. Sous-commandes du script système : `up`, `down`, `status`, `mtu` — pas de `toggle`.

> [!WARNING]
> Un échec SSH donne `Connection timed out during banner exchange`, qui ressemble à une panne
> serveur. C'est le VPN dans la plupart des cas — relancer `vpn_ensure.sh` avant tout autre
> diagnostic — et **le rebond `bilbo` lui-même dans les autres** :
> vérifié le 2026-09-04, `mp` renvoie cette erreur avec `ConnectTimeout=15` et répond normalement
> avec `ConnectTimeout=45`. Toujours utiliser **`-o ConnectTimeout=45`** au minimum, et ne jamais
> conclure d'un échec SSH qu'un fichier est absent ou qu'un processus distant est mort.

## Sonder avant de choisir

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/remote-compute/scripts/remote_probe.py
python3 ${CLAUDE_PLUGIN_ROOT}/skills/remote-compute/scripts/remote_probe.py --need "gpu,ram=400"
```

La sonde donne charge, RAM libre, espace, quotas, nœuds Slurm libres, file d'attente, et une
recommandation. L'inventaire statique ne suffit pas : sur `mh` les nœuds passent en `drain` (3 des 5
nœuds GPU l'étaient au 2026-09-04, comme au 2026-08-17), sur `mp` un pipeline peut tourner sans
prévenir (load 25 au dernier relevé).

## Les deux machines (relevé du 2026-09-04)

| | `mp` (mesoprivate1) | `mh` (Helios, frontale `mesohelios1`) |
|---|---|---|
| OS | Ubuntu 20.04 | Rocky 8 |
| CPU | 2× Xeon Gold 6226R, **64 threads** | frontale 96 c ; nœuds de calcul 24 à 128 c |
| RAM | **125 Go**, plafond dur | 94-96 Go (`mpi`, `smp`), **515 Go** (`gpu`), **1 To** (`bigmem`, `gpu_l40`) |
| GPU | **aucun** | **3× A100 40 Go** par nœud (5 nœuds), **2× L40 48 Go**, 3× A40 (visu) |
| Ordonnanceur | **aucun**, tout à la main | **Slurm** (compte `disc`, QOS par défaut `normal` ; `3gpu` et `cpu-96` attachées depuis le 2026-09-07, à demander explicitement) |
| Durée max | illimitée | 8 jours (`mpi`, `smp`, `bigmem`, `visu`), **12 jours** (`gpu`, `gpu_l40`) |
| Espace de travail | **`/data/cguyeux`** (xfs 51 To, ~21 To libres) | **`/Work/Users/cguyeux`** (BeeGFS, quota **1 To**, 274 Go pris, 1,07 M fichiers) |
| À ne PAS utiliser | `/` et `$HOME` : **100 % pleins, 1,4 Go libres** au 2026-09-04 | `$HOME` : quota 20 Go, et **lecture seule sur les nœuds de calcul** |
| Python | 3.8.10 système ; `samtools`/`bcftools` ; pas de conda | 3.6.8 système, donc **charger un module** |
| Autres | partagée : `/data` porte aussi `coffea`, `ncaron`, `predictops` | Lmod, apptainer, MATLAB, Gurobi, R, nextflow, `deep/pytorch-gpu`, `tensorflow-gpu`, `rapids-gpu`, `whisper`, `chandra-ocr`, `gnina` |

## Quelle machine

- **GPU** (torch, Boltz, RAPIDS, Whisper, OCR, LLM local) : `mh`, partition **`gpu`** (A100 40 Go),
  avec `--qos=3gpu` dès qu'on veut faire tourner plusieurs jobs GPU en parallèle : un lot de
  prédictions indépendantes passe ainsi de la série à trois de front.
  `mp` n'a aucun GPU, ne jamais y router du CUDA. La partition `gpu_l40` est plus attirante sur le
  papier (48 Go de VRAM, 1 To de RAM, 128 cœurs, presque toujours libre) mais **c'est une partition
  PRIVÉE, financée par un tiers** (Kamel Mazouzi, 2026-09-04) : ne pas s'y router de sa propre
  initiative, une demande est en cours auprès du financeur.
- **Plus de 125 Go de RAM** : `mh`, partition `bigmem` (1 To) ou `gpu` (515 Go). `gpu_l40` a
  aussi 1 To mais elle est privée, voir ci-dessus.
  Attention : `mpi` et `smp` ne donnent que ~95 Go par nœud, **moins que `mp`**.
- **Beaucoup de disque** (plusieurs To, FASTQ, CRAM, vidéos, données intermédiaires) : `mp` et son
  `/data`. Le quota BeeGFS de `mh` est de 1 To, et un espace `/Work/Projects/<nom>` de 3 To se
  demande aux admins.
- **Calcul long sans découpage possible** (au-delà de 8 jours) : `mp`, sans limite de temps. Sur
  `mh`, chaîner par `--dependency` avec reprise.
- **Disponibilité immédiate** : `mp` (aucune file), sous réserve que le pipeline n'y tourne pas.
- **Parallélisme au-delà de 64 threads** : `mh` multi-nœuds (`mpi`) avec `--qos=cpu-96`, mais
  seulement si le code fait vraiment du MPI : cette QOS est attachée à `mpi` et ne relève le
  plafond ni sur `smp` ni sur `bigmem`, où l'on reste à 48 cœurs. Sinon `mp` et ses 64 threads
  valent mieux.
- **Données TBannotator** (`results/`, `report.json`, `samples.tsv`) : `mp` obligatoirement.
- **Une troisième machine existe et n'est pas utilisée** : le cluster Lumière est vivant (1162
  cœurs, 68 hôtes actifs au 2026-09-04), avec `mesoshared` à **96 cœurs et 256 Go sans ordonnanceur**
  et une file GPU portant **4× V100 32 Go**. Notre clé n'y est pas déposée et il faut des
  algorithmes SSH hérités : l'accès se demande. Détail dans `references/mesocentre_services.md`.

> [!IMPORTANT]
> **Les QOS `3gpu` et `cpu-96` sont attachées au compte `cguyeux` depuis le 2026-09-07**
> (mail meso-admins, effet immédiat), mais **la QOS par défaut reste `normal`**, qui plafonne à
> 48 cœurs et UN SEUL GPU tous jobs confondus. Sans `--qos`, rien ne change : trois jobs
> `--gres=gpu:1` ne tournent toujours pas en parallèle et deux attendent en `PD` avec la raison
> `QOSMaxCpuPerUserLimit`. **Il faut donc écrire explicitement `#SBATCH --qos=3gpu` dans tout job
> GPU** dès qu'on veut plus d'une carte à la fois, et `#SBATCH --qos=cpu-96` pour un job MPI large.
>
> Trois réserves qui limitent la portée de cette élévation :
> - **`cpu-96` ne sert qu'au MPI** (Kamel Mazouzi, 2026-09-04, confirmé par meso-admins le
>   2026-09-07) : elle est attachée à la partition `mpi` et reste sans effet sur `smp` ou `bigmem`.
>   Un code multithread qui ne fait pas de MPI ne gagne rien à la demander, et `mp` avec ses
>   64 threads reste souvent le meilleur choix.
> - **`3gpu` n'impose aucun plafond CPU** (`MaxTRESPerUser=gres/gpu=3` seulement, relevé
>   2026-09-08) : sous cette QOS la limite de 48 cœurs de `normal` disparaît, ce qui compte dès que
>   trois jobs GPU demandent 16 cœurs chacun. En revanche `3gpu` est **refusée sur `gpu_l40`**
>   (`AllowQos=normal,2gpu,cpu-128`) : si cette partition privée est un jour ouverte, il faudra y
>   demander `2gpu`.
> - **La communication inter-cartes n'a jamais été benchmarkée** par le mésocentre. Trois GPU
>   valent donc de façon sûre pour trois jobs indépendants en parallèle (le cas de nos lots de
>   prédictions de structures), pas pour un entraînement distribué sur trois cartes, qui reste à
>   mesurer avant d'être promis dans un plan de calcul.
> - **Ces QOS sont attribuées au cas par cas et doivent être rendues.** Le mésocentre demande
>   explicitement d'être prévenu à la fin des travaux pour les retirer. Prévoir le mail de
>   restitution à `meso-admins@univ-fcomte.fr` quand la campagne de calcul se termine, plutôt que
>   de laisser un privilège dormant sur un cluster « très limité en ressources ».
>
> **Le contrôle de restitution est outillé**, pour que l'engagement ne repose pas sur la mémoire :
>
> ```bash
> bash ${CLAUDE_PLUGIN_ROOT}/skills/remote-compute/scripts/qos_restitution_check.sh [jours]
> ```
>
> Il monte le VPN au besoin puis répond à une seule question, sur un critère mécanique et non sur
> une impression : aucun job soumis sous QOS prêtée depuis N jours (défaut 14) et aucun job en
> file. Sortie 0 si la campagne est active (ne rien faire), 1 si elle est terminée (rendre les
> QOS), 2 si le cluster est injoignable (rien n'est conclu, surtout ne pas en déduire une fin de
> campagne). À lancer quand le rappel de restitution remonte, plutôt que de deviner.
>
> Le canal qui aboutit pour ce genre de demande n'est pas l'adresse de tickets `svpmeso@` mais le
> mail direct à Kamel Mazouzi, responsable technique, avec `meso-admins@univ-fcomte.fr` en copie :
> demande envoyée le vendredi 2026-09-04, QOS actives le lundi 2026-09-07. D'autres QOS existent
> (`cpu-64`, `cpu-72`, `cpu-128`, `2gpu`) et s'obtiennent par la même voie. Helios est par ailleurs
> décrit par son administrateur comme « très limité en ressources », préfiguration du futur
> MesoBFC : calibrer ses demandes en conséquence.

## Tâches courantes, et où elles vont

Un tableau de routage pour les besoins qui ne sont pas de la phylogénomique, et qui restent
aujourd'hui traités en local faute d'y penser.

| besoin | où | comment |
|---|---|---|
| transcrire un long enregistrement | `mh`, `gpu` | `module load deep/whisper/v20250625` puis `whisper --model large --language French --output_format all` |
| OCR d'un lot de scans, y compris manuscrits | `mh`, `gpu` | `module load deep/chandra-ocr/0.1.8` puis `chandra --method hf ENTREE SORTIE` |
| inférence ou fine-tuning d'un LLM ouvert | `mh`, `gpu` (A100 40 Go) | conda dédié, cache Hugging Face dans `$WORK/.cache`, quantification 4 bits pour les modèles de 7 B et plus |
| optimisation sous Gurobi | `mh`, `smp` | `module load gurobi/13.0.2`, **licence académique fournie**, rien à configurer |
| traitement SIG en lot | `mh`, `smp` | `module load qgis/3.44.7`, `export QT_QPA_PLATFORM=offscreen`, `qgis_process run` |
| MATLAB en lot | `mh`, `smp` | `module load matlab/r2023b-campus` puis `matlab -nodisplay -batch script` |
| workflow Nextflow ou nf-core | `mh`, `smp` | `module load openjdk@11.0.14.1_1` puis `nextflow@23.04.3` |
| héberger une base de travail interrogeable | `mesodb.univ-fcomte.fr` | PostgreSQL 17.5, PostGIS, MariaDB, 128 Go de RAM, sur demande à `meso-admins@univ-fcomte.fr` |
| exploration interactive courte sur GPU | JupyterHub | `https://mesohelios1.univ-fcomte.fr`, profil Slurm 1 GPU, 4 h |
| gros volumes de données brutes | `mp` | `/data/cguyeux`, 51 To, pas de quota, pas de file |

## Ce qui est déjà installé (relevé du 2026-09-04)

Ne pas supposer qu'un outil est présent : les deux machines sont maigres.

- **`mp`** : `raxmlHPC` et `treetime` dans `/usr/bin`, plus `samtools` et `bcftools`. Python 3.8.10
  système. **Pas** de conda, **pas** de Lmod, ni `iqtree2`, ni `raxml-ng`, ni BEAST2, ni `mafft`.
- **`mh`** : rien de phylogénétique en module, mais Lmod avec `miniconda3@4.10.3`,
  `anaconda3@2022.10`, `nextflow@23.04.3`, `r@4.1.3`, `apptainer/1.1.8`, `gurobi/13.0.2` (licence
  fournie), `matlab/r2023b-campus`, `qgis/3.44.7`, et surtout les modules GPU prêts à l'emploi :
  `deep/pytorch-gpu/2.0.1`, `deep/tensorflow-gpu/2.12.0`, `deep/rapids-gpu/23.04`,
  **`deep/whisper/v20250625`** (transcription), **`deep/chandra-ocr/0.1.8`** (OCR de manuscrits,
  tableaux, formulaires), `gnina/1.3.2` (docking), `namd3-gpu`.

`deep/chandra-ocr` est la réponse GPU aux **PDF scannés sans couche texte**, où
`pdftotext`/`markitdown` renvoient du vide en silence. `deep/whisper` couvre la transcription de
réunions et d'entretiens.

### Environnement phylo prêt à l'emploi sur `mh`

`/Work/Users/cguyeux/envs/phylo`, monté avec micromamba (`/Work/Users/cguyeux/bin/micromamba`) :

| outil | version | appel |
|---|---|---|
| IQ-TREE | 3.1.3 | binaire nommé **`iqtree`**, pas `iqtree2` |
| RAxML-NG | 2.0.2 | **exige `LD_LIBRARY_PATH`**, voir ci-dessous |
| **BEAST 2** | **2.7.7** | `beast`, `beauti`, `densitree` |
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
> `micromamba activate` ne corrigent le tir. Il faut **exporter `LD_LIBRARY_PATH=$PREFIX/lib`**.
> (2) Sur BeeGFS, micromamba n'a pas pu faire de liens durs : les bibliothèques de l'env sont des
> **symlinks vers `/Work/Users/cguyeux/conda_pkgs`** (4,6 Go). Un `micromamba clean` ou une purge de
> ce cache **casserait l'environnement**. Ne pas le nettoyer.

## Recettes

Modèles complets dans `references/sbatch_templates.sh` (CPU, GPU, bigmem, tableau de jobs, scratch
local, chaînage par dépendances, et lancement sans ordonnanceur sur `mp`). Partitions, plafonds,
modules et pièges détaillés dans **`references/helios_slurm.md`**. Services annexes du mésocentre
(base de données hébergée, JupyterHub, visualisation 3D, cluster Lumière, GENCI, tarifs) dans
**`references/mesocentre_services.md`**.

```bash
# mh : soumettre, suivre, récupérer
scp travail.py mh:/Work/Users/cguyeux/monprojet/
ssh mh 'cd /Work/Users/cguyeux/monprojet && sbatch job.sbatch'
ssh mh 'squeue --me'
ssh mh 'jobinfo <jobid>'     # outil maison : attente, walltime, MaxMem, disque lu/écrit
ssh mh 'seff <jobid>'        # efficacité CPU et mémoire, une fois le job fini

# mh : test interactif court avant de soumettre un long job
ssh mh 'srun -p gpu --gres=gpu:A100:1 -t 00:05:00 --mem=8G nvidia-smi'

# mp : pas d'ordonnanceur, donc détacher explicitement et journaliser
ssh mp 'cd /data/cguyeux/monprojet && setsid nohup python3 travail.py > run_$(date +%Y%m%d_%H%M).log 2>&1 < /dev/null & disown'
```

> [!IMPORTANT]
> **`module load` ne marche pas en SSH non interactif.** La fonction shell de Lmod n'est pas
> définie, et `module load` échoue **en silence** : le job continue avec le Python 3.6.8 du système.
> Toujours passer par un shell de login, et donner aux scripts `sbatch` le shebang `#!/bin/bash -l` :
> ```bash
> ssh mh 'bash -lc "module load anaconda3@2022.10/gcc-12.1.0 && python3 -V"'   # -> 3.9.13
> ```
> Même remarque pour les alias du profil : `cdw`, `meso-quota`, `svgl` ne sont pas résolus en SSH
> non interactif. Utiliser `/Work/Commun/bin/meso-quota`, `/Softs/helios/visu/svgl`, ou `bash -lc`.

> [!WARNING]
> **Le `MODULEPATH` dépend de la micro-architecture du nœud.** La frontale (Intel Skylake) voit
> toutes les piles Spack, un nœud GPU (AMD Zen2) ne voit que la sienne. Un `module load` validé sur
> la frontale peut donc être **introuvable dans le job**, notamment tout ce qui est compilé
> `skylake_avx512` (`openmpi`, `gromacs`, `namd`, `quantum-espresso`, `octave`, `freefem`).
> Valider un `module load` par un `srun` court **sur la partition cible**. Vérifié le 2026-09-04.

> [!TIP]
> **Chaîner par `--dependency` plutôt que superviser par SSH.**
> `ID=$(sbatch --parsable etape1.sbatch)` puis `sbatch -d afterok:$ID etape2.sbatch`. Slurm attend
> lui-même, sans qu'aucune boucle locale n'interroge le cluster, et il ne prend pas une coupure de
> VPN pour un échec de calcul. C'est la parade structurelle aux deux pièges de supervision décrits
> plus bas. Pour un job déjà lancé qui va manquer de temps : `scontrol update JobId=<id> TimeLimit=4-0`.

## Pièges vérifiés

- **`module load` dans un pipeline ne charge rien.** `module load X 2>&1 | tail -2` s'exécute dans un
  sous-shell : le module est bien chargé, puis l'environnement modifié meurt avec le sous-shell, et
  la commande attendue reste « introuvable » alors que `module list` la donnerait pour chargée.
  Vérifié le 2026-09-04 en croyant à tort que `deep/whisper` était cassé. Ne jamais filtrer la sortie
  d'un `module load` ; pour le rendre bavard, l'appeler seul puis inspecter `$PATH`.
- **Certains modules définissent une FONCTION shell, pas un binaire.** `gnina/1.3.2` installe
  `gnina()` qui enveloppe `apptainer exec --nv`. Donc `which gnina` ne renvoie aucun chemin, et
  l'appel ne survit ni à un `xargs`, ni à un `subprocess` Python, ni à un pipeline. Vérifier par
  `type <commande>` plutôt que par `which`, et appeler la forme `apptainer exec` complète dans un
  script.
- **`$GPU_SCRATCH_DIR` n'existe que sur la partition `gpu`** : il est VIDE sur `gpu_l40` (vérifié sur
  `node4-28`). Le repli portable est `$JOBSCRATCH`, égal à `$TMPDIR`, qui vaut
  `/tmp/jobscratch/<jobid>/` sur toutes les partitions et disparaît à la fin du job. Écrire
  `LOCAL=${GPU_SCRATCH_DIR:-${JOBSCRATCH:-$TMPDIR}}` plutôt que de supposer l'une des deux variables.
- **Le driver NVIDIA est passé en 550** (`550.163.01`, vérifié le 2026-09-04) et un environnement
  conda créé avant peut **cesser d'utiliser le GPU sans lever la moindre erreur** : le code tombe en
  CPU et le job brûle des heures GPU pour rien. Cela vise les environnements partagés de
  `/Work/Users/cguyeux/envs/`. Commencer tout job GPU par une **assertion**, pas un affichage :
  `python3 -c "import torch; assert torch.cuda.is_available()"`.
- **`$HOME` étant en lecture seule sur les nœuds, tout outil qui écrit dans `~` au runtime échoue**
  ou perd son état : `~/.cache`, matplotlib, Hugging Face, R, Nextflow, cargo. Rediriger
  (`XDG_CACHE_HOME`, `MPLCONFIGDIR`, `HF_HOME`, `R_LIBS_USER`) ou, pour un logiciel tiers
  irréductible, `export HOME=$WORK` avant `module purge`, comme le fait le mésocentre lui-même.
- **Sans `--time`, un job GPU, bigmem ou visu est tué à 4 heures**, alors que la partition en
  autorise 8 à 12 jours. Toujours écrire `--time` explicitement.
- **`$HOME` de `mh` est en LECTURE SEULE sur les nœuds de calcul**, pas sur la frontale : un script
  qui écrit dans `~` marche en interactif et échoue en `sbatch`. Tout écrire sous `$WORK`.
- **La frontale de `mh` redémarre tous les jours à 04h00.** C'est la cause racine, documentée par le
  mésocentre, du fait que rien de détaché n'y survit, même avec `setsid nohup … & disown`. Tout ce
  qui dure plus de quelques minutes passe par `sbatch`. Les IDE distants (VS Code Remote-SSH) y sont
  explicitement interdits et tués automatiquement.
- **Pour un traitement à IO intensives, travailler dans le scratch local du nœud**, pas sur BeeGFS :
  `$GPU_SCRATCH_DIR` (nœuds GPU), `$JOBSCRATCH`/`$TMPDIR` (effacé en fin de job), `/tmp` (1 To sur
  les nœuds CPU). Copier les entrées, calculer, rapatrier les seules sorties utiles.
- **Tuer une commande locale ne tue pas le processus distant.** Un `timeout` local ou un job
  d'arrière-plan interrompu laisse la commande tourner sur la machine distante, orpheline. Vérifier
  après coup (`ssh mp 'ps -eo pid,etime,cmd | grep monmotif'`) et tuer explicitement.
- **Un `grep` sur `ps` se compte lui-même.** Écrire le motif de façon à ne pas apparaître
  littéralement (`snakemak[e]`) **et** exclure les wrappers (`grep -v "bash -c"`).
- **Écrire au mauvais endroit fait échouer le job en plein calcul**, pas au démarrage. La racine de
  `mp` est à **100 %, 1,4 Go libres** au 2026-09-04, contre 7 Go en août : la marge se referme, et
  un `/tmp` volumineux y ferait tomber la machine pour tout le monde, pipeline TBannotator compris.
  Utiliser `/data/cguyeux/tmp`, et signaler la saturation plutôt que de contourner en silence.
- **Le transfert passe par le rebond `bilbo`.** Pour de gros volumes, compresser avant
  (`tar czf - | ssh mp 'tar xzf - -C /data/cguyeux/…'`) et éviter les millions de petits fichiers.
  Sur `mh`, c'est le nombre d'inodes (1,07 M en septembre contre 775 k en août) qui deviendra
  contraignant avant le volume.
- **`mp` est partagée.** Avant un calcul qui prend les 64 threads, vérifier qu'aucun run TBannotator
  n'est en cours (la sonde le dit) et que `/data` ne va pas être rempli au détriment des autres.
- **Sur `mh`, un `nohup`/`setsid … & disown` lancé DIRECTEMENT dans une commande `ssh` non
  interactive peut être tué avec la connexion**, malgré le détachement apparent. Vécu à deux
  reprises le 2026-08-26. Parade fiable : ne PAS tenter de détacher sur le nœud frontal pour un
  calcul long — exécuter la commande SANS backgrounding distant via un `ssh` bloquant lancé en tâche
  de fond LOCALE (`run_in_background: true` côté Claude Code), ou, mieux, passer par `sbatch`.
- **Une boucle de supervision LOCALE qui interroge une machine distante par `ssh` NE DOIT JAMAIS
  interpréter un `ssh` qui échoue (VPN coupé, `bilbo` injoignable, timeout) comme une preuve que le
  process distant a disparu.** Vécu le 2026-08-31 (`mtbc/Rv1125`, P1.5.c) : un script d'attente
  polling `pgrep -f ... via ssh` toutes les 5 min a conclu à tort à l'échec de 3 jobs Boltz
  d'affilée en 2 minutes réelles (un motif temporel impossible pour un vrai calcul CPU) — le VPN
  s'était coupé pendant l'attente, et `ssh` retournait un statut d'échec de CONNEXION (typiquement
  124/143 sous `timeout`, ou 255 nativement) indiscernable, dans un simple `if ! ssh ...; then`, du
  cas où la commande distante s'exécute et répond "absent". **Toujours capturer le code de sortie de
  `ssh` lui-même et le distinguer explicitement de celui de la commande distante**
  (`ssh ... cmd; rc=$?; if [ $rc -ge 124 ] || [ $rc -eq 255 ]; then continue; fi` plutôt qu'un
  `if ! ssh ...` fondu) — une connexion perdue doit faire RÉESSAYER au cycle suivant, jamais
  conclure à un état du job distant. Symptôme reconnaissable : plusieurs "échecs" consécutifs
  séparés de quelques dizaines de secondes au lieu de l'intervalle de poll attendu.
- **Corollaire immédiat, tout aussi coûteux : un `launch_job` distant qui RETENTE après un `ssh` en
  échec DOIT revérifier qu'aucune instance n'est déjà en cours AVANT de relancer.** Vécu la même
  session : l'établissement de la connexion SSH via `bilbo` peut à lui seul consommer tout le budget
  de timeout alors que le job distant a bien démarré. La boucle a interprété ce timeout comme un
  échec de lancement et a relancé : **23 doublons du même job en moins de 15 minutes**, ~90 Gio de
  RAM sur les 125 de `mp`, load average à 175. Correctif : dans `launch_job`, TOUJOURS commencer par
  un `pgrep` de contrôle (via le même `ssh_check` distinguant connexion perdue de réponse réelle) et
  ne lancer QUE si ce contrôle répond explicitement "absent". Nettoyage a posteriori :
  `pgrep -f "<motif>" | grep -v -E "^(<pid a garder>)$" | xargs -r kill -KILL` (garder l'instance la
  PLUS ANCIENNE), puis vérifier `free -h`.

## Après le calcul

Rapatrier les résultats, pas les intermédiaires. Consigner dans le cahier de labo du projet le
`jobid` Slurm ou le fichier de log, la machine, la partition, le temps écoulé et le `MaxRSS` observé
(`seff` ou `jobinfo`) : c'est ce qui permet de dimensionner correctement la fois suivante au lieu de
redemander au hasard. Les mesures de dimensionnement d'un calcul répété méritent une entrée dans
`~/.claude/knowledge/remote-compute.md`.

Un article dont un calcul est passé par `mh` doit citer le mésocentre dans ses remerciements :
« Computations have been performed on the supercomputer facilities of the Mésocentre de calcul de
Franche-Comté. »
