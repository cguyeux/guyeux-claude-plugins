# Modèles de soumission pour mh (Slurm) et de lancement pour mp (sans ordonnanceur).
# Relevé de configuration : 2026-08-17. Compte Slurm `disc`, QOS `normal`, user cguyeux.
# Ne pas exécuter ce fichier : y copier le bloc voulu dans un `job.sbatch`.
#
# RAPPELS QUI COÛTENT CHER SI ON LES OUBLIE
#   - travailler dans /Work/Users/cguyeux (mh) ou /data/cguyeux (mp), JAMAIS dans $HOME
#     (quota 20 Go sur mh) ni sur / (97 % plein sur mp) ;
#   - demander la mémoire réellement nécessaire : un --mem surdimensionné fait attendre
#     le job pour rien, un --mem trop juste le fait tuer par l'OOM killer en pleine nuit ;
#   - --time trop court = job tué à l'échéance sans préavis ; trop long = priorité dégradée.
#     Mesurer une fois avec `sacct -j <id> -o MaxRSS,Elapsed`, puis ajuster.

# ============================================================================ #
# 1. CPU mono-nœud (partition smp : 32 à 48 c, 93 à 251 Go)
# ============================================================================ #
cat > job_cpu.sbatch <<'EOF'
#!/bin/bash
#SBATCH --job-name=calcul_cpu
#SBATCH --partition=smp
#SBATCH --nodes=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=80G
#SBATCH --time=2-00:00:00
#SBATCH --output=/Work/Users/cguyeux/%x_%j.out
#SBATCH --error=/Work/Users/cguyeux/%x_%j.err

set -euo pipefail
module load anaconda3@2022.10/gcc-12.1.0

cd /Work/Users/cguyeux/monprojet
echo "hôte=$(hostname) job=$SLURM_JOB_ID cœurs=$SLURM_CPUS_PER_TASK début=$(date -Is)"

# Faire consommer au code le nombre de cœurs ALLOUÉ, pas tous ceux du nœud :
# une bibliothèque BLAS qui ouvre 96 threads dans une allocation de 32 s'effondre.
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK

python3 travail.py --threads "$SLURM_CPUS_PER_TASK"
echo "fin=$(date -Is)"
EOF

# ============================================================================ #
# 2. GPU (partition gpu : 3× A100-PCIE-40GB par nœud, 503 Go RAM, 64 c)
#    Variante gpu_l40 : --partition=gpu_l40 --gres=gpu:L40:1 (1 To RAM, 128 c)
# ============================================================================ #
cat > job_gpu.sbatch <<'EOF'
#!/bin/bash
#SBATCH --job-name=calcul_gpu
#SBATCH --partition=gpu
#SBATCH --gres=gpu:A100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=/Work/Users/cguyeux/%x_%j.out

set -euo pipefail
module load deep/pytorch-gpu/2.0.1        # ou tensorflow-gpu/2.12.0, rapids-gpu/23.04

nvidia-smi --query-gpu=name,memory.total --format=csv    # trace : quel GPU a servi
python3 -c "import torch; print('cuda', torch.cuda.is_available(), torch.cuda.get_device_name(0))"

cd /Work/Users/cguyeux/monprojet
python3 entrainement.py
EOF

# ============================================================================ #
# 3. Très grosse mémoire (partition bigmem : 1 nœud, 48 c, 1 To)
# ============================================================================ #
cat > job_bigmem.sbatch <<'EOF'
#!/bin/bash
#SBATCH --job-name=calcul_bigmem
#SBATCH --partition=bigmem
#SBATCH --nodes=1
#SBATCH --cpus-per-task=48
#SBATCH --mem=900G
#SBATCH --time=2-00:00:00
#SBATCH --output=/Work/Users/cguyeux/%x_%j.out

set -euo pipefail
module load anaconda3@2022.10/gcc-12.1.0
cd /Work/Users/cguyeux/monprojet
python3 assemblage_matrice.py
EOF

# ============================================================================ #
# 4. Tableau de jobs (un job par échantillon, la bonne façon de paralléliser
#    un traitement embarrassingly parallel sur un cluster)
# ============================================================================ #
cat > job_array.sbatch <<'EOF'
#!/bin/bash
#SBATCH --job-name=lot
#SBATCH --partition=mpi
#SBATCH --array=1-100%10          # 100 tâches, 10 simultanées au plus
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/Work/Users/cguyeux/logs/lot_%A_%a.out

set -euo pipefail
module load anaconda3@2022.10/gcc-12.1.0
ECHANTILLON=$(sed -n "${SLURM_ARRAY_TASK_ID}p" /Work/Users/cguyeux/monprojet/liste.txt)
python3 traiter.py "$ECHANTILLON"
EOF

# ============================================================================ #
# Soumission et suivi (depuis le poste local)
# ============================================================================ #
# ssh mh 'cd /Work/Users/cguyeux/monprojet && sbatch job_gpu.sbatch'
# ssh mh 'squeue -u cguyeux -o "%.10i %.9P %.20j %.2t %.10M %.6D %R"'
# ssh mh 'sacct -j <jobid> -o JobID,JobName%20,State,Elapsed,MaxRSS,ReqTRES%40'
# ssh mh 'scancel <jobid>'
# ssh mh 'sinfo -p gpu -N -o "%N %c %m %G %t"'          # avant de promettre un délai
#
# Test interactif court avant de soumettre un long job (recommandé) :
# ssh mh 'srun -p gpu --gres=gpu:A100:1 -t 00:05:00 --mem=8G nvidia-smi'

# ============================================================================ #
# 5. mp : AUCUN ordonnanceur, donc tout est manuel
# ============================================================================ #
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
