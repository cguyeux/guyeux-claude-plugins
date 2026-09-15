# `mh` / Helios — référence Slurm

Source : documentation officielle du mésocentre (`https://mesoservices.univ-fcomte.fr`, ex
`mesodoc.univ-fcomte.fr`), croisée avec une sonde directe du cluster le **2026-09-04**.
Quand la doc et `scontrol`/`sinfo` divergent, **c'est `scontrol` qui a raison** : la doc contient
plusieurs valeurs périmées, signalées plus bas.

> Le wiki `mesowiki.univ-fcomte.fr` documente l'**autre** cluster (Lumière, SGE, CentOS 6). Il ne
> décrit PAS Helios. N'y chercher ni `sbatch`, ni les partitions, ni les modules d'Helios.

## 1. Plafonds par utilisateur — la contrainte qui surprend le plus

Le compte est `disc`. La QOS **par défaut** reste `normal`, mais depuis le **2026-09-07** deux QOS
supérieures sont **attachées au compte `cguyeux`** et utilisables à la demande :

Plafonds relevés par `sacctmgr show qos` le 2026-09-08, colonne `MaxTRESPerUser` :

| QOS | plafond simultané, tous jobs confondus | statut pour nous |
|---|---|---|
| **`normal`** | **`cpu=48`** et **`gres/gpu=1`** | **QOS par défaut**, celle qui s'applique sans `--qos` |
| **`3gpu`** | **`gres/gpu=3`**, et **aucune limite CPU** | **attachée depuis le 2026-09-07**, à demander par `--qos=3gpu` |
| **`cpu-96`** | **`cpu=96`**, et aucune limite GPU | **attachée depuis le 2026-09-07**, à demander par `--qos=cpu-96` |
| `cpu-64`, `cpu-72`, `cpu-128` | 64 / 72 / 128 cœurs | non attachées, sur demande |
| `2gpu`, `meso` | 2 ou 3 GPU | non attachées, sur demande |

**Une QOS ne cumule pas ses limites avec `normal`** : un job tourne sous UNE QOS. Sous `--qos=3gpu`
le plafond de 48 cœurs disparaît donc, ce qui compte dès que trois jobs GPU demandent 16 cœurs
chacun. Vérifié empiriquement le 2026-09-08 : trois `sbatch --gres=gpu:A100:1 --qos=3gpu` soumis
d'affilée passent les trois en `RUNNING` simultanément (deux sur `node4-25`, un sur `node4-21`),
là où sous `normal` on obtient 1 `R` et 2 `PD`.

Toutes les partitions n'acceptent pas toutes les QOS (`scontrol show partition`, 2026-09-08) :

| partition | `AllowQos` |
|---|---|
| `gpu`, `smp`, `bigmem` | `ALL` |
| `mpi` | `normal,cpu-72,cpu-96,cpu-128` (donc **pas `cpu-64`**) |
| `gpu_l40` | `normal,2gpu,cpu-128` (donc **`3gpu` y est REFUSÉE**) |

Deux conséquences. La QOS `3gpu` ne vaut que sur la partition `gpu` : si l'accès à `gpu_l40` est un
jour accordé par son financeur, il faudra y demander `2gpu`, pas `3gpu`. Le refus est vérifié et non
déduit, `sbatch --test-only -p gpu_l40 --qos=3gpu ...` rendant `allocation failure: Invalid qos
specification` (2026-09-08). Un ajout automatique de `--qos=3gpu` à un lot de `.sbatch` doit donc
filtrer sur la partition, sans quoi les jobs `gpu_l40` sont rejetés à la soumission. Et si `cpu-96` est
techniquement acceptée sur `smp` et `bigmem` (`AllowQos=ALL`), l'administrateur a écrit qu'elle
« est utile uniquement avec des calculs MPI » : l'utiliser pour empiler des jobs `smp` détournerait
un privilège prêté au cas par cas. La réponse honnête à un besoin de plus de 48 cœurs non-MPI reste
`mp` et ses 64 threads, sans file d'attente.

Conséquences directes :

- **Une QOS attachée ne s'applique pas toute seule.** Sans `#SBATCH --qos=3gpu`, le job tourne sous
  `normal` et reste plafonné à UN GPU : lancer trois jobs `--gres=gpu:1` n'en fait pas tourner
  trois, deux restent `PD` avec la raison `QOSMaxCpuPerUserLimit`. Un job qui attend avec cette
  raison n'est pas mal dimensionné, il attend **vos propres** jobs, et le plus souvent il ne
  manquait qu'une ligne `--qos`.
- **48 cœurs cumulés au maximum sous `normal`.** Deux jobs `-c 32` ne passent pas ensemble.
  `cpu-96` relève ce plafond **uniquement sur la partition `mpi`** : elle ne change rien sur `smp`,
  `bigmem` ou `gpu`, et ne sert donc qu'à un code faisant réellement du MPI.
- **La communication inter-cartes n'a jamais été benchmarkée** par le mésocentre (Kamel Mazouzi,
  2026-09-04). `3gpu` est sûre pour faire tourner trois jobs indépendants d'une carte chacun ;
  pour un entraînement distribué sur trois cartes dans un seul job, mesurer d'abord sur un cas
  court avant d'en faire l'hypothèse d'un plan de calcul.
- **Ces QOS sont prêtées, pas acquises.** Le mésocentre les attribue au cas par cas et demande
  expressément d'être prévenu à la fin des travaux pour les retirer : écrire à
  `meso-admins@univ-fcomte.fr` en fin de campagne. Helios est décrit par ses administrateurs comme
  « très limité en ressources », préfiguration de MesoBFC.
- Les autres QOS s'obtiennent **sur demande** par le même canal : mail direct à Kamel Mazouzi,
  responsable technique, avec `meso-admins@univ-fcomte.fr` en copie. C'est le canal qui a toujours
  abouti, alors que l'adresse de tickets `svpmeso@` ne porte en pratique que des notifications
  automatiques. Délai constaté : demande le vendredi 2026-09-04, activation le lundi 2026-09-07.
  Le demander est un geste de quelques minutes, à faire AVANT de découper artificiellement un
  calcul pour tenir dans 48 cœurs.
- Vérifier ce qu'on a réellement, plutôt que de croire ce tableau :
  `sacctmgr -n show associations user=$USER format=Account,User,QOS%60`.

## 2. Partitions (sonde du 2026-09-04)

| partition | nœuds | c/nœud | RAM/nœud | GPU | MaxTime | **DefaultTime** | **DefMemPerCPU** |
|---|---|---|---|---|---|---|---|
| `mpi` | 16 (`node4-1..20`) | 24 | 94 Go | — | 8 j | **1 j** | 3872 Mo |
| `smp` | 5 (`node4-9..12,26`) | 32 | 96 Go | — | 8 j | **1 j** | 2750 Mo |
| `gpu` | 5 (`node4-21..25`) | 64 | **515 Go** | **3× A100-PCIE 40 Go** | **12 j** | **4 h** | **16 Go** |
| `gpu_l40` | 1 (`node4-28`) | 128 | **1 To** | **2× L40 48 Go** | **12 j** | **4 h** | 8058 Mo |
| `bigmem` | 1 (`node4-27`) | 48 | **1 To** | — | 8 j | **4 h** | 4 Go |
| `visu` | 1 (`m3sovisu`) | 64 | 252 Go | 3× A40 | 8 j | 4 h | 4 Go |

> [!WARNING]
> **Sans `--time`, un job GPU, bigmem ou visu est tué à 4 heures**, alors que la partition en
> autorise 8 à 12 jours. C'est la façon la plus bête de perdre une nuit de calcul. Toujours écrire
> `--time` explicitement.

Divergences connues de la doc officielle, tranchées par la sonde : la page « bases de Slurm »
annonce des nœuds GPU à 252 Go et 32 cœurs (Slurm en déclare 515 Go et 64) et un walltime GPU par
défaut de 8 h (Slurm dit 4 h) ; `bigmem` n'a plus que `node4-27`, `m3sovisu` étant passé en `drain`
et rattaché à `visu`.

> [!CAUTION]
> **`gpu_l40` est une partition PRIVÉE, financée par un tiers**, information donnée par Kamel
> Mazouzi le 2026-09-04. Elle apparaît dans `sinfo` et se laisse sonder, mais **ne pas s'y router de
> sa propre initiative** : ses ressources appartiennent à quelqu'un d'autre. Une demande
> d'autorisation auprès du financeur est en cours. Tant qu'elle n'a pas abouti, la partition GPU
> ouverte est `gpu`, et elle seule.

C'est d'autant plus tentant que `gpu` est encombrée : au relevé, trois jobs concurrents sur un seul
nœud utilisable, trois autres en `drain`/`inval`, pendant que `node4-28` était `idle` avec ses deux
L40 de 48 Go et son téraoctet de RAM. La bonne réponse à cette asymétrie est la demande, pas le
contournement.

## 3. Contraintes de forme par partition

- **`mpi`** : `--ntasks` doit être **divisible par 24**. Ne jamais utiliser `-N`/`--nodes`. Lancer
  avec **`srun`**, jamais `mpirun`.
- **`smp`** : ne jamais utiliser `-N` ni `-n`, seulement `--cpus-per-task` (maximum 32, limite
  matérielle). Y placer aussi les tableaux de jobs.
- **`gpu` / `gpu_l40`** : `--gres=gpu:1`. La consigne officielle est de **ne pas dépasser
  `--mem=128G` par job**. Mémoire par défaut 16 Go par cœur, donc souvent suffisante sans `--mem`.
- **`bigmem`** : la page officielle écrit `--mem` max 250G dans son propre modèle, ce qui contredit
  le téraoctet de `node4-27` ; demander ce dont on a besoin et vérifier l'acceptation du job.

## 4. Le piège des modules : `MODULEPATH` dépend du nœud

Vérifié le 2026-09-04 par un `srun` sur `node4-22`. Les modules sont produits par Spack et
**rangés par micro-architecture** :

| où | `MODULEPATH` |
|---|---|
| frontale `mesohelios1` (Intel Skylake) | `helios-modules` + **zen4** + **zen2** + **x86_64** + **skylake_avx512** |
| nœud GPU `node4-2x` (AMD Zen2) | `helios-modules` + `x86_64` + `zen2` + `/opt/nvidia/hpc_sdk/modulefiles` |

La frontale voit **tout**, un nœud de calcul ne voit que **sa** pile. Un `module load` répété avec
succès sur la frontale peut donc échouer dans le job, notamment tout ce qui est compilé
`skylake_avx512` : `openmpi`, `gromacs`, `namd`, `quantum-espresso`, `octave`, `freefem`,
`r@4.1.3` version skylake. Sur les nœuds GPU il ne reste, côté Spack, que `anaconda3@2021.05`,
`gcc`, `r@4.1.3` (zen2) et `anaconda3@2022.10`, `miniconda3@4.10.3`, `nextflow@23.04.3`, `gsl_2.8`
(x86_64).

**Règle** : valider un `module load` par un `srun` court **sur la partition cible**, jamais sur la
frontale. Les modules de `/Softs/helios-modules` (voir §6), eux, sont visibles partout.

## 4 bis. Écrire un `sbatch` qui ne se sabote pas

Motifs communs à tous les scripts officiels du mésocentre, et raisons de les reprendre.

| motif | pourquoi |
|---|---|
| `#!/bin/bash -l` | sans le shell de login, `module` n'existe pas dans le job |
| `module purge` avant tout `module load` | `sbatch` exporte l'environnement de la frontale (`--export=ALL` par défaut) ; un module hérité peut masquer celui du job |
| `#SBATCH --output=%x.%J.out` et `--error=%x.%J.out` | `%x` nom du job, `%J` identifiant ; pointer les deux sur le même fichier fusionne les flux |
| `--mem=0` | demande **toute** la mémoire du nœud, sans avoir à connaître sa capacité |
| `export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK` | un outil multithread mal élevé ouvre sinon autant de fils que le nœud a de cœurs, et sur-souscrit l'allocation |
| `scontrol show hostnames` | fabrique la liste des nœuds alloués, pour un outil qui ne parle pas Slurm : machinefile, cluster Dask ou Ray monté à la main dans le job |

> [!IMPORTANT]
> **`$HOME` étant en lecture seule sur les nœuds de calcul, tout outil qui écrit dans `~` au runtime
> échoue ou perd son état** : caches `~/.cache`, `~/.config`, matplotlib, Hugging Face, R, Nextflow,
> cargo. Deux parades, la seconde étant celle que le mésocentre emploie lui-même dans ses propres
> scripts :
> ```bash
> export XDG_CACHE_HOME=$WORK/.cache
> export MPLCONFIGDIR=$WORK/.mplconfig
> export HF_HOME=$WORK/.hf
> export R_LIBS_USER=$WORK/R/library
> # ou, pour un logiciel tiers qu'on ne peut pas reconfigurer, avant `module purge` :
> export HOME=$WORK
> ```

**Compiler sur la frontale, exécuter dans un job** : figer le chemin des bibliothèques dans le
binaire avec `-Wl,-rpath,<prefix>/lib` plutôt que compter sur un `module load` refait dans le job.
C'est la version propre du contournement `LD_LIBRARY_PATH` qu'exige déjà `raxml-ng` dans
l'environnement `phylo`. Pour un petit code C, `gcc $(gsl-config --cflags --libs)
-Wl,-rpath,$(gsl-config --prefix)/lib prog.c -o prog` (module `gsl_2.8/gcc-12.1.0`).

Les installations, compilations et téléchargements se font **sur la frontale**, pas dans un job.
Rediriger systématiquement le préfixe d'installation vers `$WORK` : `pkg prefix ~/WORK/octave_packages`
pour Octave, `R_LIBS_USER` pour R, `PYTHONUSERBASE` ou `--target` pour pip.

**Conda dans un `sbatch` : `conda run`, jamais `conda activate`.** Le shell d'un job n'est pas
interactif, et `conda activate` échoue tant qu'on n'a pas sourcé `conda.sh`. Le mésocentre
recommande la forme en une ligne :

```bash
module load miniconda3@4.10.3/gcc-12.1.0
conda run -n monEnv python travail.py
```

Et pour ne pas remplir les 20 Go de `$HOME`, déporter une fois pour toutes les paquets et les
environnements, ce que le mésocentre fait aussi par un `meso_setup_conda` à usage unique :

```bash
conda config --add pkgs_dirs $WORK/.conda/pkgs
conda config --add envs_dirs $WORK/.conda/envs
```

**Trois pièges d'environnement Python qui coûtent des heures.**

- `module avail` écrit sur **stderr** : `module avail 2>&1 | grep -i <nom>`, sinon un `grep` naïf ne
  trouve jamais rien.
- **Sur-abonnement BLAS dans un tableau de jobs** : huit tâches qui ouvrent chacune autant de
  threads BLAS que le nœud a de cœurs, c'est 8 × 32 threads sur 32 cœurs, et l'effondrement.
  Dans un `--array`, imposer `export MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`.
  À l'inverse, pour un calcul d'algèbre dense unique, vérifier qu'on est bien sur un BLAS threadé
  (`numpy.show_config()`) : le BLAS de référence netlib est mono-thread, et l'écart mesuré par le
  mésocentre sur une résolution dense atteint un facteur 20.
- Un `pip install --user` fait dans un conteneur écrit dans le `~/.local` de l'hôte, **partagé par
  tous les conteneurs et tous les environnements** — c'est le mécanisme exact par lequel un `torch`
  installé en `--user` masque celui d'un module. Neutraliser par `export PYTHONNOUSERSITE=1` quand
  ce n'est pas voulu.

**Conteneurs** : `apptainer exec --nv image cmd` passe les GPU au conteneur (valable A100 comme L40).
Un binaire compilé **dans** une image doit être **exécuté dans** cette image, sinon l'éditeur de
liens de l'hôte redonne l'erreur de `glibc` qu'on croyait contournée.

> [!CAUTION]
> **Règle de conduite du mésocentre, qui vise directement nos arborescences** : « ne pas enregistrer
> des milliers de fichiers dans un seul répertoire, les répartir en sous-répertoires ». Sur un
> système de fichiers parallèle, un répertoire à cent mille entrées effondre le service de
> métadonnées **pour tous les utilisateurs**. Avec 1,07 million de fichiers sur `$WORK` et une
> base locale organisée à raison d'un fichier par souche, c'est une contrainte à vérifier avant de
> transférer une arborescence entière sur BeeGFS.

> [!NOTE]
> **Le driver NVIDIA est passé en version 550** (`550.163.01`, vérifié sur `node4-28` le 2026-09-04)
> et le mésocentre prévient qu'un environnement conda créé avant peut cesser d'utiliser le GPU. La
> panne est silencieuse : le code tombe en CPU sans erreur. **Toujours commencer un job GPU par une
> assertion** `python3 -c "import torch; assert torch.cuda.is_available()"` ou l'équivalent
> TensorFlow, plutôt que de découvrir après coup qu'on a payé des heures GPU pour du CPU.

Deux avertissements de gouvernance : un module **visible** dans `module avail` n'est pas forcément
**accessible** (Comsol et VASP 6 sont restreints à des groupes), donc tester tôt ; et `/opt`
contient des logiciels installés hors Spack, **invisibles de `module avail`**, à chercher à la main
quand un outil semble absent.

> [!WARNING]
> **Trois pièges de `module`, tous vérifiés le 2026-09-04 sur `node4-28`.**
> (1) **`module load X | tail` ne charge rien** : le pipeline crée un sous-shell, le module y est
> chargé puis l'environnement meurt avec lui, et la commande reste « introuvable » alors que
> `module list` la déclare chargée. Ne jamais filtrer la sortie d'un `module load`.
> (2) **Certains modules définissent une FONCTION shell et non un binaire** : `gnina/1.3.2` installe
> `gnina()` qui enveloppe `apptainer exec --nv …`. `which gnina` ne renvoie donc rien, et l'appel ne
> survit ni à `xargs`, ni à un `subprocess` Python, ni à un pipeline. Diagnostiquer par
> `type <commande>`, pas par `which`, et écrire la forme `apptainer exec` complète dans un script.
> (3) Le `MODULEPATH` d'un nœud **`gpu_l40`** (Zen4) est encore différent de celui d'un nœud `gpu`
> (Zen2) : `helios-modules`, `x86_64`, **zen4**, `nvidia/hpc_sdk`. Les modules `deep/*` sont bien
> présents sur les deux, ce qui a été confirmé en chargeant réellement `deep/whisper/v20250625`
> (`/Softs/helios/gpu/miniconda-envs/whisper/bin/whisper`) et `deep/chandra-ocr/0.1.8`.

## 5. Suivi, chaînage, prolongation

```bash
squeue --me                      # mes jobs
squeue --start                   # date de démarrage estimée d'un job PD
scontrol show job <id>           # tout le détail d'un job vivant
jobinfo <id>                     # outil maison : attente, walltime utilisé, MaxMem, MaxDisk R/W
seff <id>                        # efficacité CPU et mémoire d'un job fini
sacct -j <id> -o JobID,State,Elapsed,MaxRSS,ReqTRES%40
scontrol update JobId=<id> TimeLimit=4-0     # PROLONGER un job déjà lancé
```

> [!TIP]
> **Chaîner par dépendances plutôt que superviser par SSH.** `sbatch -d afterok:<id> suite.sbatch`
> (aussi `afterany`, `afternotok`, `singleton`) fait attendre le job suivant sans qu'aucune boucle
> locale n'interroge le cluster. C'est la parade structurelle au piège de supervision décrit dans
> `SKILL.md` : une boucle `ssh` qui prend une coupure de VPN pour un échec de calcul a déjà empilé
> 23 doublons d'un même job. Slurm sait faire cette attente lui-même, et il ne se trompe pas.

**On peut se connecter en SSH à un nœud où l'on a un job en cours** (`ssh node4-22`) pour y lancer
`top` ou `nvidia-smi` ; la connexion est fermée dès la fin du job.

## 6. Modules utiles (relevé du 2026-09-04, `/Softs/helios-modules`, visibles partout)

| module | pour quoi |
|---|---|
| `deep/whisper/v20250625` | transcription audio et vidéo, GPU (`--model turbo|large`, `--output_format`) |
| `deep/chandra-ocr/0.1.8` | OCR de documents complexes : **manuscrit**, tableaux, formules, formulaires |
| `deep/pytorch-gpu/2.0.1`, `deep/tensorflow-gpu/2.12.0`, `deep/rapids-gpu/23.04` | piles GPU prêtes |
| `gnina/1.3.2` | docking moléculaire par apprentissage profond (charge `apptainer`) |
| `namd3-gpu/3.0.2`, `3.1-alpha4` | dynamique moléculaire GPU |
| `gurobi/13.0.2` | solveur, **licence académique fournie**, rien à configurer |
| `apptainer/1.1.8` | conteneurs (`apptainer run docker://…`) |
| `nextflow@23.04.3/gcc-12.1.0` | workflows nf-core (charger `openjdk` avec) |
| `qgis/3.44.7` | SIG, headless via `qgis_process` + `export QT_QPA_PLATFORM=offscreen` |
| `matlab/r2023b-campus` | licence campus, toutes toolboxes |
| `nix/2.28.5`, `guix/1.3.0` | gestionnaires de paquets fonctionnels, **accès sur demande** |
| `miniconda3@4.10.3/gcc-12.1.0` | la base conda recommandée dès qu'on installe des paquets |

`deep/chandra-ocr` mérite d'être connu hors calcul scientifique : c'est la réponse GPU au cas des
**PDF scannés sans couche texte**, où la chaîne `pdftotext`/`markitdown` renvoie du vide en silence.

Conda : `pip` doit être **installé par conda dans l'environnement** avant tout `pip install`, sinon
l'installation part dans la mauvaise pile. Le cache Hugging Face se place dans `$WORK/.cache`.

## 7. Stockage — et les scratchs locaux, largement sous-utilisés

| espace | système | quota | sauvegarde | remarque |
|---|---|---|---|---|
| `/Home/Users/<login>` (`$HOME`) | NFS | **20 Go** | oui, quotidienne | **lecture seule sur les nœuds de calcul** |
| `/Work/Users/<login>` (`$WORK`) | BeeGFS | **1 To** | non | espace de travail obligatoire |
| `/Work/Projects/<nom>`, `/Work/Groups/<nom>` | BeeGFS | **3 To** | non | **sur demande**, la voie officielle pour dépasser 1 To |
| `$GPU_SCRATCH_DIR` | SSD local du nœud GPU | — | non | **partition `gpu` seulement**, vide sur `gpu_l40` ; purgé à la demande |
| `$JOBSCRATCH` = `$TMPDIR` | local | — | non | `/tmp/jobscratch/<jobid>/`, **toutes partitions**, effacé à la fin du job |
| `/tmp` (nœuds CPU), `/Scratch` (GPU, bigmem) | local | 1 To / 3,5 à 5,8 To | non | |

> [!TIP]
> **Pour tout traitement à IO intensives, travailler dans le scratch local du nœud, pas sur
> BeeGFS.** Copier les entrées au début du job, calculer dans `$GPU_SCRATCH_DIR` ou `$TMPDIR`,
> recopier les seules sorties utiles vers `$WORK` à la fin. BeeGFS est un système partagé : des
> millions de petites lectures y pénalisent tout le cluster, et la consigne officielle est
> explicitement de ne pas le stresser.

Le mésocentre fournit un récapitulatif d'un coup d'œil, `/Work/Commun/bin/meso-quota` (l'alias
`meso-quota` n'existe que dans un shell interactif), qui donne l'occupation de `$WORK` et de
`$HOME` face à leurs quotas. Pour le compte de fichiers, passer par
`beegfs-ctl --getquota --uid $USER`.

État au 2026-09-04 : `$WORK` occupé à 273,6 Gio sur 1024 Gio, mais **1 066 357 fichiers** (contre
775 k en août). Le nombre d'inodes croît plus vite que le volume ; c'est lui qui deviendra gênant.

Déporter les gros dot-directories de `$HOME` vers `$WORK` par symlink est la pratique recommandée
par le mésocentre lui-même (`ln -s $WORK/.seiscomp ~/.seiscomp` dans sa propre doc). C'est déjà
fait pour `~/.conda` ; `~/.cache` et `~/.local` sont les suivants sur la liste.

## 8. Frontale : ce qu'elle interdit

- **Redémarrage automatique tous les jours à 04h00.** C'est la cause racine, documentée par le
  mésocentre, du fait que rien de détaché ne survit sur la frontale : `setsid nohup … & disown` n'y
  résiste pas. Tout ce qui dure plus de quelques minutes passe par `sbatch`.
- **Aucun calcul sur la frontale.** Les processus lourds y sont tués sans avertissement.
- **VS Code Remote-SSH et les IDE distants sont interdits** : ils lancent des services de fond et
  sont tués automatiquement.
- Les alias du profil (`cdw`, `cdh`, `meso-quota`, `svgl`) **ne sont pas résolus** dans un
  `ssh mh 'commande'` non interactif. Utiliser les chemins complets, par exemple
  `/Work/Commun/bin/meso-quota` et `/Softs/helios/visu/svgl`, ou passer par `bash -lc "…"`.
