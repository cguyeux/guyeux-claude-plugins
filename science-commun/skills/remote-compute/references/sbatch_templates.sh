# Modèles de soumission pour mh (Slurm, cluster Helios) et de lancement pour mp (sans ordonnanceur).
# Relevé de configuration : 2026-09-04, QOS mises à jour le 2026-09-07. Compte Slurm `disc`,
# user cguyeux, QOS par DÉFAUT `normal`, QOS `3gpu` et `cpu-96` attachées et à demander à la main.
# Ne pas exécuter ce fichier : y copier le bloc voulu dans un `job.sbatch`.
# Détail des partitions, plafonds et pièges : references/helios_slurm.md

# RAPPELS QUI COÛTENT CHER SI ON LES OUBLIE
#   - QOS `normal` (celle par défaut) : 48 cœurs ET 1 SEUL GPU en simultané, tous jobs confondus.
#     Deux jobs GPU ne tournent pas en parallèle ; le second attend avec QOSMaxCpuPerUserLimit.
#   - Depuis le 2026-09-07 les QOS `3gpu` et `cpu-96` sont attachées au compte, mais elles ne
#     s'appliquent PAS toutes seules : sans `#SBATCH --qos=3gpu`, le job retombe sur `normal` et
#     son plafond d'un GPU. `cpu-96` n'a d'effet que sur la partition `mpi` (calcul MPI réel).
#     Ces QOS sont prêtées au cas par cas : prévenir meso-admins@univ-fcomte.fr en fin de campagne.
#   - --time est OBLIGATOIRE en pratique : sans lui, gpu / gpu_l40 / bigmem / visu tuent le
#     job à 4 heures alors que la partition en autorise 8 à 12 jours.
#   - shebang `#!/bin/bash -l` : sans le shell de login, `module load` ne fait rien.
#   - travailler dans /Work/Users/cguyeux (mh) ou /data/cguyeux (mp), JAMAIS dans $HOME
#     (quota 20 Go, et $HOME est en LECTURE SEULE sur les nœuds de calcul) ni sur / (100 % plein sur mp) ;
#   - un `module load` validé sur la frontale peut être introuvable dans le job : le MODULEPATH
#     dépend de la micro-architecture du nœud. Tester par un srun sur la partition CIBLE.
#   - demander la mémoire réellement nécessaire : un --mem surdimensionné fait attendre
#     le job pour rien, un --mem trop juste le fait tuer par l'OOM killer en pleine nuit ;
#     mesurer une fois avec `seff <id>` ou `jobinfo <id>`, puis ajuster.

# ============================================================================ #
# 1. CPU mono-nœud (partition smp : 5 nœuds, 32 c et 96 Go chacun)
#    Sur smp, n'utiliser NI -N NI -n : seulement --cpus-per-task (32 au maximum).
# ============================================================================ #
cat > job_cpu.sbatch <<'EOF'
#!/bin/bash -l
#SBATCH --job-name=calcul_cpu
#SBATCH --partition=smp
#SBATCH --cpus-per-task=32
#SBATCH --mem=80G
#SBATCH --time=2-00:00:00
#SBATCH --output=/Work/Users/cguyeux/%x_%j.out
#SBATCH --error=/Work/Users/cguyeux/%x_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=christophe.guyeux@univ-fcomte.fr

set -euo pipefail
module purge
module load anaconda3@2022.10/gcc-12.1.0

cd /Work/Users/cguyeux/monprojet
echo "hôte=$(hostname) job=$SLURM_JOB_ID cœurs=$SLURM_CPUS_PER_TASK début=$(date -Is)"

# Faire consommer au code le nombre de cœurs ALLOUÉ, pas tous ceux du nœud :
# une bibliothèque BLAS qui ouvre 96 threads dans une allocation de 32 s'effondre.
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK

srun python3 travail.py --threads "$SLURM_CPUS_PER_TASK"
echo "fin=$(date -Is)"
EOF

# ============================================================================ #
# 2. GPU. La partition ouverte est `gpu` (5 nœuds, 3x A100-PCIE 40 Go, 64 c, 515 Go), souvent
#    encombrée avec plusieurs noeuds en drain. `gpu_l40` (2x L40 48 Go, 128 c, 1 To) est visible
#    dans sinfo mais c'est une partition PRIVEE financee par un tiers : ne pas s'y router de sa
#    propre initiative, une demande d'autorisation est en cours (Kamel Mazouzi, 2026-09-04).
#    Mémoire par défaut : 16 Go par cœur. Consigne officielle : ne pas dépasser --mem=128G.
#    --qos=3gpu (depuis le 2026-09-07) permet jusqu'à 3 jobs GPU d'un carte chacun EN PARALLELE.
#    Le laisser en place même pour un job GPU isolé ne coûte rien et évite d'oublier la ligne
#    quand le job devient un lot. Pour un entraînement multi-cartes dans UN job, voir le bloc 2bis.
# ============================================================================ #
cat > job_gpu.sbatch <<'EOF'
#!/bin/bash -l
#SBATCH --job-name=calcul_gpu
#SBATCH --partition=gpu
#SBATCH --qos=3gpu
#SBATCH --gres=gpu:A100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=/Work/Users/cguyeux/%x_%j.out
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=christophe.guyeux@univ-fcomte.fr

set -euo pipefail
# $HOME est en LECTURE SEULE sur les noeuds : rediriger tout ce qui ecrit dans ~
export XDG_CACHE_HOME=$WORK/.cache MPLCONFIGDIR=$WORK/.mplconfig HF_HOME=$WORK/.hf
module purge
module load deep/pytorch-gpu/2.0.1        # ou tensorflow-gpu/2.12.0, rapids-gpu/23.04

nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv   # trace : quel GPU a servi
# ASSERTION, pas un simple print : depuis le passage du driver en 550, un environnement conda
# cree avant peut retomber en CPU EN SILENCE et bruler des heures GPU pour rien.
python3 -c "import torch; assert torch.cuda.is_available(), 'GPU non vu'; print(torch.cuda.get_device_name(0))"

cd /Work/Users/cguyeux/monprojet
python3 entrainement.py
EOF

# ============================================================================ #
# 2bis. LOT de prédictions GPU indépendantes, le cas qui a motivé la QOS 3gpu : N tâches
#    sans lien entre elles (prédictions de structures, inférences, OCR de scans), qui
#    s'exécutaient en SÉRIE sous la QOS normal. Avec --qos=3gpu, trois tournent de front.
#    Le %3 est essentiel : au-delà, les tâches attendraient de toute façon en PD.
#    ATTENTION : ceci fait tourner 3 jobs d'UNE carte chacun, ce qui est sûr. Un
#    entraînement DISTRIBUÉ sur 3 cartes dans un seul job (--gres=gpu:A100:3) est permis
#    par la QOS mais la communication inter-cartes n'a JAMAIS été benchmarkée par le
#    mésocentre (Kamel Mazouzi, 2026-09-04) : la mesurer sur un cas court avant de bâtir
#    un plan de calcul dessus, le gain peut être nul voire négatif en PCIe sans NVLink.
# ============================================================================ #
cat > job_gpu_array.sbatch <<'EOF'
#!/bin/bash -l
#SBATCH --job-name=lot_gpu
#SBATCH --partition=gpu
#SBATCH --qos=3gpu
#SBATCH --array=1-60%3            # 60 tâches, 3 de front, une carte chacune
#SBATCH --gres=gpu:A100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --output=/Work/Users/cguyeux/%x_%A_%a.out

set -euo pipefail
export XDG_CACHE_HOME=$WORK/.cache MPLCONFIGDIR=$WORK/.mplconfig HF_HOME=$WORK/.hf
module purge
module load deep/pytorch-gpu/2.0.1
python3 -c "import torch; assert torch.cuda.is_available(), 'GPU non vu'"

cd /Work/Users/cguyeux/monprojet
ENTREE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" liste_entrees.txt)
python3 predire.py "$ENTREE"
EOF

# ============================================================================ #
# 3. Très grosse mémoire (partition bigmem : node4-27, 48 c, 1 To)
#    Attention : 48 c, c'est exactement le plafond CPU de la QOS normal. Un job qui prend
#    les 48 cœurs bloque tous les autres jobs CPU de l'utilisateur. La QOS cpu-96 ne sert à
#    RIEN ici : elle est attachée à la partition mpi, pas à bigmem ni à smp.
# ============================================================================ #
cat > job_bigmem.sbatch <<'EOF'
#!/bin/bash -l
#SBATCH --job-name=calcul_bigmem
#SBATCH --partition=bigmem
#SBATCH --cpus-per-task=32
#SBATCH --mem=700G
#SBATCH --time=2-00:00:00
#SBATCH --output=/Work/Users/cguyeux/%x_%j.out

set -euo pipefail
module purge
module load anaconda3@2022.10/gcc-12.1.0
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
cd /Work/Users/cguyeux/monprojet
srun python3 assemblage_matrice.py
EOF

# ============================================================================ #
# 4. Tableau de jobs : un job par échantillon, la bonne façon de paralléliser un
#    traitement massivement parallèle. À placer sur smp (jamais sur mpi, réservé au MPI).
#    Le suffixe %N borne la concurrence, ce qui évite de saturer sa propre QOS.
# ============================================================================ #
cat > job_array.sbatch <<'EOF'
#!/bin/bash -l
#SBATCH --job-name=lot
#SBATCH --partition=smp
#SBATCH --array=1-100%8           # 100 tâches, 8 simultanées au plus (8×4 c = 32 ≤ 48)
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/Work/Users/cguyeux/logs/lot_%A_%a.out

set -euo pipefail
module purge
module load anaconda3@2022.10/gcc-12.1.0
ECHANTILLON=$(sed -n "${SLURM_ARRAY_TASK_ID}p" /Work/Users/cguyeux/monprojet/liste.txt)
python3 traiter.py "$ECHANTILLON"
EOF

# ============================================================================ #
# 4bis. MPI multi-nœuds, le SEUL cas où la QOS cpu-96 (attachée le 2026-09-07) sert à
#    quelque chose. Partition `mpi` : 16 nœuds node4-1..20, 24 cœurs et 94 Go chacun,
#    MaxTime 8 j mais DEFAULT 1 j, donc --time obligatoire au-delà.
#    Contraintes propres à cette partition, non négociables :
#      - --ntasks doit être DIVISIBLE PAR 24 (un nœud entier par tranche de 24) ;
#      - ne JAMAIS utiliser -N / --nodes, Slurm place lui-même ;
#      - lancer par `srun`, jamais `mpirun`.
#    96 cœurs = 4 nœuds. Sans --qos=cpu-96 le job serait plafonné à 48 cœurs et resterait
#    en PD (QOSMaxCpuPerUserLimit). Vérifier que le code fait VRAIMENT du MPI : un code
#    seulement multithread n'ira pas plus vite sur 4 nœuds, et mp (64 threads, aucune
#    file d'attente) reste alors le meilleur choix.
# ============================================================================ #
cat > job_mpi.sbatch <<'EOF'
#!/bin/bash -l
#SBATCH --job-name=calcul_mpi
#SBATCH --partition=mpi
#SBATCH --qos=cpu-96
#SBATCH --ntasks=96                # multiple de 24 ; 96 = 4 nœuds pleins
#SBATCH --mem-per-cpu=3872M        # défaut de la partition, ne pas dépasser 94 Go/nœud
#SBATCH --time=1-00:00:00
#SBATCH --output=/Work/Users/cguyeux/%x_%j.out

set -euo pipefail
export XDG_CACHE_HOME=$WORK/.cache MPLCONFIGDIR=$WORK/.mplconfig
module purge
# Piège de micro-architecture : openmpi est compilé skylake_avx512. Un module qui charge
# sur la frontale peut être introuvable sur un nœud d'une autre génération. Valider par un
# srun court sur la partition CIBLE avant de soumettre le vrai job.
module load openmpi

cd /Work/Users/cguyeux/monprojet
srun ./mon_binaire_mpi --entree donnees.h5     # srun, PAS mpirun
EOF

# ============================================================================ #
# 5. Traitement à IO intensives : calculer dans le SCRATCH LOCAL du nœud, pas sur BeeGFS.
#    $JOBSCRATCH (= $TMPDIR = /tmp/jobscratch/<jobid>/) existe sur TOUTES les partitions et est
#    efface a la fin du job ; $GPU_SCRATCH_DIR n'existe QUE sur la partition gpu (vide sur
#    gpu_l40, verifie) et survit au job mais est purge a la demande.
#    Copier les entrees, calculer en local, rapatrier les seules sorties utiles.
# ============================================================================ #
cat > job_scratch.sbatch <<'EOF'
#!/bin/bash -l
#SBATCH --job-name=io_lourd
#SBATCH --partition=smp
#SBATCH --cpus-per-task=16
#SBATCH --mem=48G
#SBATCH --time=08:00:00
#SBATCH --output=/Work/Users/cguyeux/%x_%j.out

set -euo pipefail
PROJET=/Work/Users/cguyeux/monprojet
LOCAL=${GPU_SCRATCH_DIR:-${JOBSCRATCH:-${TMPDIR:-/tmp/$SLURM_JOB_ID}}}
mkdir -p "$LOCAL"

cp -a "$PROJET"/entrees/. "$LOCAL"/       # une seule grosse lecture BeeGFS
cd "$LOCAL"
module purge && module load anaconda3@2022.10/gcc-12.1.0
python3 "$PROJET"/analyse.py --in "$LOCAL" --out "$LOCAL"/sorties

mkdir -p "$PROJET"/resultats
cp -a "$LOCAL"/sorties/. "$PROJET"/resultats/   # on ne rapatrie QUE les sorties utiles
EOF

# ============================================================================ #
# 6. Chaîner sans supervision locale : la parade au polling SSH.
#    Slurm attend lui-même la fin du job précédent, et lui ne prend pas une coupure
#    de VPN pour un échec de calcul.
# ============================================================================ #
# ID=$(ssh mh 'cd /Work/Users/cguyeux/monprojet && sbatch --parsable etape1.sbatch')
# ssh mh "cd /Work/Users/cguyeux/monprojet && sbatch -d afterok:$ID etape2.sbatch"
#   afterok    : seulement si l'étape précédente a réussi
#   afterany   : quoi qu'il arrive
#   afternotok : seulement en cas d'échec (utile pour un job de diagnostic)
#   singleton  : après tout job de MÊME NOM du même utilisateur
#
# Différer un démarrage :        sbatch --begin=now+2hours job.sbatch
# Prolonger un job DÉJÀ lancé :  scontrol update JobId=<id> TimeLimit=4-0
# Écarter un nœud douteux :      sbatch -x node4-24 job.sbatch

# ============================================================================ #
# Soumission et suivi (depuis le poste local)
# ============================================================================ #
# ssh mh 'cd /Work/Users/cguyeux/monprojet && sbatch job_gpu.sbatch'
# ssh mh 'squeue --me -o "%.10i %.9P %.20j %.2t %.10M %.6D %R"'
# ssh mh 'squeue --start'                                # départ estimé d'un job en attente
# ssh mh 'jobinfo <jobid>'                               # attente, walltime, MaxMem, disque lu/écrit
# ssh mh 'seff <jobid>'                                  # efficacité CPU et mémoire
# ssh mh 'sacct -j <jobid> -o JobID,JobName%20,State,Elapsed,MaxRSS,ReqTRES%40'
# ssh mh 'scancel <jobid>'
# ssh mh 'sinfo -o "%.12P %.5a %.14l %.6D %.6t %.20N %.8m %.12G"'   # avant de promettre un délai
# ssh mh 'ssh node4-22 nvidia-smi'                       # autorisé TANT QU'UN JOB Y TOURNE
#
# Valider un `module load` sur la partition CIBLE, pas sur la frontale :
# ssh mh 'srun -p gpu --gres=gpu:A100:1 -t 00:05:00 --mem=8G bash -lc "module load X && nvidia-smi"'

# ============================================================================ #
# 7. mp : AUCUN ordonnanceur, donc tout est manuel
# ============================================================================ #
# Le rebond bilbo est LENT : un ConnectTimeout de 15 s produit un faux
# « Connection timed out during banner exchange » sur une machine parfaitement vivante.
# Toujours au moins -o ConnectTimeout=45, et ne jamais conclure d'un échec SSH que le
# processus distant est mort ni qu'un fichier est absent.
#
# Vérifier d'abord qu'on ne va pas concurrencer le pipeline TBannotator :
#   python3 <skill remote-compute>/scripts/remote_probe.py
#
# Lancer en détaché (survit à la fermeture de la session SSH) :
# ssh mp 'cd /data/cguyeux/monprojet && setsid nohup python3 travail.py \
#         > run_$(date +%Y%m%d_%H%M).log 2>&1 < /dev/null & disown'
#
# Suivre :
# ssh mp 'tail -20 /data/cguyeux/monprojet/run_*.log'
# ssh mp 'ps -eo pid,etime,pcpu,rss,cmd | grep "travai[l].py"'
#
# Arrêter (motif écrit pour ne pas s'auto-apparier) :
# ssh mp 'pkill -u cguyeux -f "travai[l].py"'
#
# Limiter l'empreinte quand on partage la machine (64 threads au total) :
# ssh mp 'cd /data/cguyeux/monprojet && setsid nohup nice -n 10 taskset -c 0-31 \
#         python3 travail.py > run.log 2>&1 < /dev/null & disown'
