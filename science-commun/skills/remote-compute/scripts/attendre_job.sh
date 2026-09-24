#!/usr/bin/env bash
# attendre_job.sh -- veille sur un job Slurm distant, SANS jamais confondre
# « je n'ai rien vu » avec « je n'arrive plus à regarder ».
#
# POURQUOI (2026-09-23, deux incidents le même jour sur le job AG2 270281 de `mh`).
#   1. Une veille écrite à la va-vite testait `until ! ssh ... squeue ... | grep -q .` : une
#      sortie vide par ÉCHEC SSH est indiscernable d'une file réellement vide, et le job a été
#      déclaré terminé alors qu'il lui restait des heures.
#   2. Sa remplaçante testait bien le code de retour, mais se contentait de journaliser chaque
#      échec et n'a rendu la main qu'au bout de trois heures -- or le VPN était tombé six
#      minutes après son lancement et elle n'a JAMAIS réussi une seule observation. Une veille
#      qui échoue en silence est à peine mieux qu'une veille absente.
#
# D'où trois sorties distinctes, qui sont tout l'intérêt du script :
#   0 -- condition de fin atteinte (le fichier témoin existe et n'est pas vide) ;
#   1 -- le job n'est plus RUNNING alors que le témoin n'existe pas : échec ou annulation ;
#   3 -- PERTE DE CONTACT : N échecs SSH consécutifs, on alerte tôt au lieu d'attendre ;
#   2 -- expiration du délai maximal, le job tournant toujours.
#
# Le témoin doit être un fichier que l'outil n'écrit QU'EN FIN d'analyse : pour IQ-TREE, c'est
# `<prefixe>.iqtree` (le rapport), et surtout pas `<prefixe>.treefile`, réécrit en cours de route.
#
# Usage :
#   attendre_job.sh --job 270281 --temoin /Work/Users/cguyeux/ag2_set/ML_libre.iqtree \
#                   [--hote mh] [--intervalle 300] [--echecs 3] [--max-heures 12]

set -uo pipefail

HOTE=mh; JOB=""; TEMOIN=""; INTERVALLE=300; MAX_ECHECS=3; MAX_HEURES=12

while [ $# -gt 0 ]; do
  case "$1" in
    --hote) HOTE="$2"; shift 2 ;;
    --job) JOB="$2"; shift 2 ;;
    --temoin) TEMOIN="$2"; shift 2 ;;
    --intervalle) INTERVALLE="$2"; shift 2 ;;
    --echecs) MAX_ECHECS="$2"; shift 2 ;;
    --max-heures) MAX_HEURES="$2"; shift 2 ;;
    *) echo "argument inconnu : $1" >&2; exit 64 ;;
  esac
done
[ -n "$JOB" ] && [ -n "$TEMOIN" ] || { echo "--job et --temoin sont obligatoires" >&2; exit 64; }

fin=$((SECONDS + MAX_HEURES * 3600))
echecs=0

while [ $SECONDS -lt $fin ]; do
  sortie=$(ssh -o ConnectTimeout=15 -o BatchMode=yes "$HOTE" \
    "test -s '$TEMOIN' && echo TEMOIN_PRESENT; sacct -n --jobs=$JOB --format=State | head -1" 2>/dev/null)
  rc=$?

  if [ $rc -ne 0 ]; then
    echecs=$((echecs + 1))
    echo "$(date '+%F %H:%M') contact perdu avec $HOTE (rc=$rc), échec $echecs/$MAX_ECHECS"
    if [ "$echecs" -ge "$MAX_ECHECS" ]; then
      echo "PERTE DE CONTACT : $echecs échecs consécutifs. Le job n'est PAS présumé mort --"
      echo "Slurm ne dépend pas de cette connexion. Vérifier le VPN (sudo vpn up) puis relancer."
      exit 3
    fi
    sleep "$INTERVALLE"
    continue
  fi

  echecs=0
  etat=$(printf '%s' "$sortie" | tr -d ' ' | tail -1)
  if printf '%s' "$sortie" | grep -q TEMOIN_PRESENT; then
    echo "$(date '+%F %H:%M') TERMINÉ : $TEMOIN est écrit (état du job $JOB : ${etat:-inconnu})"
    exit 0
  fi
  case "$etat" in
    RUNNING|PENDING|REQUEUED|RESIZING|SUSPENDED) : ;;
    "") echo "$(date '+%F %H:%M') sacct ne rend aucun état pour $JOB -- à examiner"; exit 1 ;;
    *)  echo "$(date '+%F %H:%M') job $JOB n'est plus actif (état=$etat) SANS que $TEMOIN existe"
        exit 1 ;;
  esac
  sleep "$INTERVALLE"
done

echo "$(date '+%F %H:%M') délai de $MAX_HEURES h écoulé, job $JOB toujours actif"
exit 2
