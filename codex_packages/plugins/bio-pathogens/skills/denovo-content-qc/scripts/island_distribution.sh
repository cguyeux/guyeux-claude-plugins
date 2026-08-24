#!/usr/bin/env bash
# P16 — distribution des îlots d'une lignée par génome de référence.
# Teste la SPÉCIFICITÉ d'îlots "absents de H37Rv" : extrait chaque îlot du génome fermé de la
# lignée (coord.), le BLASTe (qcov) contre un panel de génomes de référence, et écrit une matrice
# îlot x référence. Un îlot présent chez une lignée éloignée (ex. M. bovis animale) N'EST PAS
# spécifique de la lignée étudiée : c'est du contenu ancestral que H37Rv a perdu.
#
# RÉUTILISABLE : pour compléter la matrice (P16.2/P16.3), ajouter une ligne "nom|chemin.fasta" à
# REFS (un génome de référence par lignée), puis relancer. Aucune dépendance hors blastn/samtools.
#
# Sortie : résultats/P16_distribution_matrix.tsv  (colonnes = îlot, len, puis qcov% par référence)
set -euo pipefail
cd "$(dirname "$0")/.."                        # racine projet L8 (contient cahier_de_labo.md)
GENOME=data/ref/CP048071.1.fasta               # génome fermé de la lignée étudiée (L8 / RW-TB008)
RES=résultats; TMP=$(mktemp -d)
OUT=$RES/P16_distribution_matrix.tsv

# Îlots : nom  coordonnées (sur GENOME). Éditer ici si le génome change.
ISLANDS="
cobF_ilot 1050833-1054895
TbD1_mmpS6-mmpL6 1766344-1769893
RvD1_mamB 2264834-2269887
pknH_ilot 2211038-2215585
adenylate_cyclase 1484198-1485198
PPE50 3490028-3491358
PPE55 3735255-3735997
mannosidase 738274-738863
"

# Panel de références : nom|fasta. Ajouter ici un génome par lignée pour compléter la matrice.
REFS=(
  "H37Rv_L4|../investigate_phylo/resources/NC_000962.3.fasta"
  "M.bovis_animale|../investigate_phylo/resources/LT708304.1.fasta"
  "M.leprae_outgroup|../investigate_phylo/resources/NC_002677.1.fasta"
)

gid=$(head -1 "$GENOME" | sed 's/>//;s/ .*//')
# 1) extraire les îlots
ISL_FA=$TMP/islands.fasta; : > "$ISL_FA"
declare -A LEN
while read -r name coords; do
  [ -z "${name:-}" ] && continue
  samtools faidx "$GENOME" "${gid}:${coords}" 2>/dev/null | sed "1s/.*/>${name}/" >> "$ISL_FA"
done <<< "$ISLANDS"

# 2) bases BLAST des références présentes
names=(); dbs=()
for entry in "${REFS[@]}"; do
  rn=${entry%%|*}; rp=${entry#*|}
  if [ -f "$rp" ]; then
    makeblastdb -in "$rp" -dbtype nucl -out "$TMP/db_$rn" >/dev/null 2>&1
    names+=("$rn"); dbs+=("$TMP/db_$rn")
  else
    echo "WARN référence introuvable, ignorée : $rp" >&2
  fi
done

# 3) matrice qcov (0 -> "absent")
{
  printf "ilot\tlen"; for n in "${names[@]}"; do printf "\t%s" "$n"; done; printf "\n"
  while read -r name coords; do
    [ -z "${name:-}" ] && continue
    s=${coords%-*}; e=${coords#*-}; len=$((e - s + 1))
    printf "%s\t%s" "$name" "$len"
    for db in "${dbs[@]}"; do
      q=$(blastn -query "$ISL_FA" -db "$db" -outfmt "6 qseqid qcovs" -max_target_seqs 1 2>/dev/null \
            | awk -v i="$name" '$1==i && !f{v=$2; f=1} END{print (f?v:0)}')
      printf "\t%s%%" "${q:-0}"
    done
    printf "\n"
  done <<< "$ISLANDS"
} > "$OUT"

rm -rf "$TMP"
echo "Matrice -> $OUT"
column -t -s $'\t' "$OUT"
