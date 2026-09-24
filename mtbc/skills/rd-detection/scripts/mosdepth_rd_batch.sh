#!/bin/bash
# Recoupement RD independant SANS relancer le pipeline Snakemake complet de RDscan.
#
# Contexte : sur des souches DEJA mappees sur H37Rv par notre propre pipeline
# (mp:/data/current/run/results/<SRA>/mapped.cram), la branche mapping de RDscan
# (BWA, wrapper v1.7.1/bio/bwa/mem-samblaster) est redondante, et la branche RD
# CANDIDATES (SURVIVOR + GATK4 + wrappers bcftools/bgzip) n'est pas necessaire
# pour comparer des RD CONNUES (RD9, RD301, RD315, RDoryx_1/4, RD12oryx...).
# La formule de RDscan pour les RD connues (lue au source,
# RDscan/workflow/scripts/makeTables.R) est : delete ssi
#   depth_mediane(region) / depth_mediane(genome_entier) <= threshold (0.05 par defaut)
# Ce script l'applique directement via mosdepth sur les CRAM deja mappes,
# sans BWA, sans Snakemake, sans les wrappers dont la creation d'env avait
# echoue en 2026-08-17 (bcftools/index, bgzip -- inutiles a cette question).
#
# Usage :
#   mosdepth_rd_batch.sh <accessions.txt> <RD.bed> <ref.fa> <resultats_dir> [results_root] [threads]
#
# <accessions.txt>   une accession SRA/ERR par ligne
# <RD.bed>            fichier RD.bed de RDscan (resources/RD.bed), ou tout BED a 4 colonnes
#                      dont la PREMIERE ligne est le genome entier (nom arbitraire, ex "H37Rv")
# <ref.fa>            reference FASTA correspondant aux CRAM (H37Rv NC_000962.3 en general)
# <resultats_dir>     repertoire de sortie, DOIT etre inscriptible par vous (jamais
#                      /data/current/run, proprietaire du pipeline)
# [results_root]      racine des resultats par souche (defaut /data/current/run/results)
# [threads]           parallelisme xargs (defaut 8)
#
# Sortie : <resultats_dir>/batch_status.tsv (acc, OK|FAILED|MISSING_CRAM)
#          <resultats_dir>/depths/<acc>.regions.bed.gz (sortie brute mosdepth --by)
#
# Piege documente (2026-09-20, projet orygis-phylogenie) : certains repertoires
# <results_root>/<acc>/ sont en 0755 (non group/other-writable), ce qui empeche
# d'ecrire le .crai a cote du CRAM original. Ce script contourne SYSTEMATIQUEMENT
# via un lien symbolique dans <resultats_dir>/links/, jamais en copiant le CRAM
# (economie massive d'E/S : un CRAM MTBC pese 80-170 Mo).
#
# Environnement conda recommande sur mp (cree le 2026-09-20, evite les conflits
# de dependances avec l'env "RDscan" existant qui porte deja snakemake-minimal) :
#   conda create -n rdcheck -c bioconda -c conda-forge -y samtools mosdepth

set -uo pipefail

ACCESSIONS="${1:?accessions.txt requis}"
BED="${2:?RD.bed requis}"
REF="${3:?ref.fa requise}"
OUTDIR="${4:?repertoire de sortie inscriptible requis}"
RESULTS_ROOT="${5:-/data/current/run/results}"
THREADS="${6:-8}"

DEPTHS="$OUTDIR/depths"
LINKS="$OUTDIR/links"
mkdir -p "$DEPTHS" "$LINKS"

process_one() {
    acc="$1"
    cram="$RESULTS_ROOT/$acc/mapped.cram"
    if [ ! -f "$cram" ]; then
        echo -e "$acc\tMISSING_CRAM"
        return
    fi
    link="$LINKS/$acc.cram"
    [ -e "$link" ] || ln -s "$cram" "$link"
    if [ ! -f "$link.crai" ]; then
        samtools index "$link" >/dev/null 2>&1
    fi
    if [ ! -f "$DEPTHS/$acc.regions.bed.gz" ]; then
        mosdepth --no-per-base --use-median --fast-mode -t 1 \
          --by "$BED" --fasta "$REF" \
          "$DEPTHS/$acc" "$link" >/dev/null 2>&1
    fi
    if [ -f "$DEPTHS/$acc.regions.bed.gz" ]; then
        echo -e "$acc\tOK"
    else
        echo -e "$acc\tFAILED"
    fi
}
export -f process_one
export RESULTS_ROOT REF BED DEPTHS LINKS

cat "$ACCESSIONS" | xargs -P "$THREADS" -I{} bash -c 'process_one "$@"' _ {} > "$OUTDIR/batch_status.tsv"
echo "done: $(cut -f2 "$OUTDIR/batch_status.tsv" | sort | uniq -c | tr '\n' ' ')"
