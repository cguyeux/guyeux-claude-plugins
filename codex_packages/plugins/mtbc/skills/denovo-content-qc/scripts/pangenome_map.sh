#!/usr/bin/env bash
# P18 — pangénome L8 par mapping sur le génome fermé CP048071.1 (RW-TB008).
# Pour chaque souche : breadth/depth de couverture du génome L8 fermé (ce qu'elle PARTAGE avec
# RW-TB008), fenêtres à couverture 0 (ce que RW-TB008 a et qu'elle N'A PAS), et fraction de reads
# non mappés (ce qu'elle a EN PLUS de RW-TB008). SRR10828835 = RW-TB008 = contrôle positif.
set -euo pipefail
cd "$(dirname "$0")/.."                       # racine projet L8
REF=data/ref/CP048071.1.fasta
OUT=résultats/pangenome
mkdir -p "$OUT"
THREADS=4
SUMMARY="$OUT/summary.tsv"
echo -e "strain\trole\tbreadth%_CP048071\tmean_depth\tpct_reads_unmapped\tn_zerocov_windows>=500bp\ttotal_zerocov_bp" > "$SUMMARY"

declare -A READS1 READS2 ROLE
READS1[ERR12115321]=data/reads/ERR12115321_1.fastq.gz; READS2[ERR12115321]=data/reads/ERR12115321_2.fastq.gz; ROLE[ERR12115321]=autre_ITM2018
READS1[SRR10828835]=data/reads/SRR10828835_1.fastq.gz; READS2[SRR10828835]=data/reads/SRR10828835_2.fastq.gz; ROLE[SRR10828835]=RWTB008_controle
READS1[SRR1173284]=data/reads/SRR1173284_1.fastq;       READS2[SRR1173284]=data/reads/SRR1173284_2.fastq;       ROLE[SRR1173284]=autre_B2-7505

for S in ERR12115321 SRR10828835 SRR1173284; do
  echo "### $S (${ROLE[$S]})"
  BAM="$OUT/${S}_vs_CP048071.sorted.bam"
  bwa mem -t $THREADS "$REF" "${READS1[$S]}" "${READS2[$S]}" 2>"$OUT/${S}.bwa.log" \
    | samtools sort -@ $THREADS -m 1G -o "$BAM" -
  samtools index "$BAM"

  # couverture (breadth = % du génome couvert >=1x ; meandepth)
  read -r breadth meandepth < <(samtools coverage "$BAM" | awk 'NR==2{print $6" "$7}')
  # fraction de reads non mappés (= contenu en plus de RW-TB008)
  tot=$(samtools view -c "$BAM"); unm=$(samtools view -c -f 4 "$BAM")
  pctunm=$(awk -v u=$unm -v t=$tot 'BEGIN{printf "%.3f", t? 100*u/t:0}')
  # fenêtres à couverture 0 >=500 bp (= régions de RW-TB008 absentes de cette souche)
  read -r nz totz < <(samtools depth -a "$BAM" | awk '
    $3==0{ if(run==0) start=$2; run++; next }
    { if(run>=500){ n++; tp+=run } run=0 }
    END{ if(run>=500){ n++; tp+=run } print (n?n:0)" "(tp?tp:0) }')
  echo -e "${S}\t${ROLE[$S]}\t${breadth}\t${meandepth}\t${pctunm}\t${nz}\t${totz}" >> "$SUMMARY"

  # extraire les reads non mappés pour assemblage (contenu propre-en-plus)
  samtools fastq -f 4 -1 "$OUT/${S}_unmapCP_R1.fq" -2 "$OUT/${S}_unmapCP_R2.fq" \
    -0 /dev/null -s /dev/null -n "$BAM" 2>/dev/null || true
done

echo "=== SUMMARY ==="
cat "$SUMMARY"
