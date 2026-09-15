#!/usr/bin/env bash
# panisa_campaign.sh -- inventaire ab initio d'IS sur les souches P. aeruginosa deja
# mappees par la chaine TBannotator (mp:/data/current/run/references_results/NC_002516.2).
#
# POURQUOI CE SCRIPT EXISTE
#   Le module IS de la chaine mappe les sequences clippees contre un panel des 22 IS du
#   MTBC. Sur P. aeruginosa il rend donc un fichier VIDE (en-tete seul, 92 octets), sans
#   erreur. Le signal brut est pourtant present. panISa (Treepong, Guyeux, Meunier,
#   Couchoud, Hocquet, Valot, Bioinformatics 2018) travaille ab initio et peut exploiter
#   ces alignements tels quels.
#
# CONTROLE FALSIFIANT, INTEGRE ET NON OPTIONNEL
#   PAO1 est une reference LOINTAINE pour une partie de l'espece (genome accessoire
#   massif). Une souche divergente produit des lectures clippees partout, et panISa les
#   lira comme des sites d'insertion. On releve donc pour chaque souche le nombre de sites
#   ET le nombre de SNP (proxy de divergence a PAO1) :
#     - si n_sites correle avec n_snp, la table est dominee par l'artefact de reference
#       et ne doit pas etre interpretee comme un inventaire d'IS ;
#     - si elle ne correle pas, le signal est propre.
#   Ce n'est pas une metrique de confort : c'est ce qui decide si la campagne complete
#   vaut la peine d'etre lancee.
#
# CHOIX D'IMPLEMENTATION
#   - Pas de suppression de fichiers : chaque travailleur REUTILISE un BAM temporaire
#     unique qu'il ecrase (`samtools view -o` tronque), d'ou une empreinte bornee a
#     ~45 Mo par travailleur au lieu de 45 Mo par souche.
#   - Pas d'ordonnanceur sur mp : parallelisme par decoupage de la liste en N tranches,
#     une boucle sequentielle par tranche, lancees en arriere-plan. `nice` par politesse,
#     la machine est partagee.
#   - Rien n'est ecrit dans /data/current (propriete de gsenelle) ni dans $HOME (le / de
#     mp est a 97 %). Tout va dans /data/cguyeux.
#
# USAGE  bash panisa_campaign.sh <fichier_selection> <n_souches> <n_travailleurs>
#        fichier_selection : lignes `souche<TAB>profondeur<TAB>couverture`

set -uo pipefail

SEL=${1:?fichier de selection}
LIMIT=${2:-200}
WORKERS=${3:-8}

BASE=/data/cguyeux/panisa_pao1
SRC=/data/current/run/references_results/NC_002516.2
REF_SRC=/data/current/run/resources/NC_002516.2.fasta
ENV=/data/cguyeux/envs/bacto
REF=/data/cguyeux/ref/NC_002516.2.fasta

export LD_LIBRARY_PATH=$ENV/lib
export PATH=$ENV/bin:$PATH            # einverted est appele en SOUS-PROCESSUS par panISa

mkdir -p "$BASE"/{out,logs,tmp} /data/cguyeux/ref

# Reference recopiee puis indexee CHEZ NOUS : `samtools view -T` veut un .fai, et
# /data/current/run/resources est en ecriture pour gsenelle, pas pour nous.
if [ ! -s "$REF" ]; then cp "$REF_SRC" "$REF"; fi
if [ ! -s "$REF.fai" ]; then samtools faidx "$REF"; fi

head -n "$LIMIT" "$SEL" > "$BASE"/lot_courant.tsv
split -n l/"$WORKERS" -d --additional-suffix=.tsv "$BASE"/lot_courant.tsv "$BASE"/tranche_

traiter_tranche() {
  local tranche=$1 slot=$2
  local bam="$BASE/tmp/w${slot}.bam"
  while IFS=$'\t' read -r souche depth cov; do
    [ -z "${souche:-}" ] && continue
    local cram="$SRC/$souche/mapped.cram"
    local vcf="$SRC/$souche/annotated.vcf"
    local out="$BASE/out/$souche.txt"
    [ -s "$out" ] && continue                      # idempotent : deja fait, on saute
    [ -s "$cram" ] || { echo -e "$souche\tCRAM_ABSENT" >> "$BASE/logs/erreurs.tsv"; continue; }

    if ! nice -n 10 samtools view -b -T "$REF" -o "$bam" "$cram" 2>>"$BASE/logs/w$slot.err"; then
      echo -e "$souche\tCONVERSION_ECHOUEE" >> "$BASE/logs/erreurs.tsv"; continue
    fi
    nice -n 10 samtools index "$bam" 2>>"$BASE/logs/w$slot.err"
    if ! nice -n 10 panISa.py -o "$out" "$bam" 2>>"$BASE/logs/w$slot.err"; then
      echo -e "$souche\tPANISA_ECHOUE" >> "$BASE/logs/erreurs.tsv"; continue
    fi

    local n_sites n_snp n_ir
    n_sites=$(( $(wc -l < "$out") - 1 ))
    n_ir=$(awk -F'\t' 'NR>1 && $7!="No IR"' "$out" | wc -l)
    n_snp=$(grep -vc '^#' "$vcf" 2>/dev/null || echo 0)
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$souche" "$depth" "$cov" "$n_sites" "$n_ir" "$n_snp" \
      >> "$BASE/resume_w$slot.tsv"
  done < "$tranche"
}

echo "campagne : $(wc -l < "$BASE"/lot_courant.tsv) souches, $WORKERS travailleurs, debut $(date -Is)"
slot=0
for t in "$BASE"/tranche_*.tsv; do
  traiter_tranche "$t" "$slot" &
  slot=$((slot+1))
done
wait

printf 'souche\tprofondeur\tcouverture\tn_sites\tn_sites_avec_IR\tn_snp\n' > "$BASE"/resume.tsv
cat "$BASE"/resume_w*.tsv >> "$BASE"/resume.tsv 2>/dev/null
echo "fin $(date -Is) : $(( $(wc -l < "$BASE"/resume.tsv) - 1 )) souches traitees"
