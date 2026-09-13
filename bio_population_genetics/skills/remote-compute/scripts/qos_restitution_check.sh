#!/usr/bin/env bash
# Les QOS `3gpu` et `cpu-96` d'Helios sont PRETEES au cas par cas (attachees le 2026-09-07).
# Le mesocentre demande a etre prevenu en fin de travaux pour les retirer, et c'est
# exactement le genre d'engagement qui s'oublie. Ce script repond a une seule question :
# la campagne est-elle terminee, donc est-il temps de rendre les QOS ?
#
# Critere mecanique, pas une impression : aucun job soumis sous une QOS pretee depuis
# N jours (defaut 14), ET aucun job en file. Tant qu'un job tourne, il n'y a rien a faire.
#
# USAGE
#   bash qos_restitution_check.sh [jours_d_inactivite]
#
# CODES DE SORTIE
#   0 = campagne encore active, ou indeterminee (ne rien faire)
#   1 = campagne terminee selon le critere : rendre les QOS
#   2 = cluster injoignable (VPN a terre ?), rien n'est conclu

set -uo pipefail
JOURS="${1:-14}"
QOS_PRETEES="3gpu|cpu-96"

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$DIR/vpn_ensure.sh" mh >/dev/null 2>&1 || { echo "mh injoignable (VPN ?), rien conclu."; exit 2; }

SORTIE=$(ssh -o ConnectTimeout=15 mh "
  sacct -u \$USER -X -S now-${JOURS}days --format=JobID,QOS%12,State%12,End%20 -n 2>/dev/null | grep -E '${QOS_PRETEES}' | wc -l
  squeue -u \$USER -h 2>/dev/null | wc -l
  sacct -u \$USER -X -S now-180days --format=End%20,QOS%12 -n 2>/dev/null | grep -E '${QOS_PRETEES}' | sort | tail -1
" 2>/dev/null) || { echo "SSH vers mh en echec, rien conclu."; exit 2; }

RECENTS=$(echo "$SORTIE" | sed -n 1p | tr -d ' ')
EN_FILE=$(echo "$SORTIE" | sed -n 2p | tr -d ' ')
DERNIER=$(echo "$SORTIE" | sed -n 3p | xargs)

if [ "${RECENTS:-0}" -gt 0 ] || [ "${EN_FILE:-0}" -gt 0 ]; then
  echo "Campagne ACTIVE : ${RECENTS} job(s) sous QOS pretee sur ${JOURS} j, ${EN_FILE} en file."
  echo "Ne pas rendre les QOS."
  exit 0
fi

echo "Campagne TERMINEE selon le critere : aucun job sous QOS pretee depuis ${JOURS} jours,"
echo "aucun job en file. Dernier job connu sous QOS pretee : ${DERNIER:-aucun trace}."
echo
echo "=> Rendre les QOS : le brouillon de restitution est pret dans Superhuman"
echo "   (objet 'Re: Demande de QOS sur Helios (compte cguyeux) - fin de campagne, QOS a retirer',"
echo "   destinataire meso-admins@univ-fcomte.fr, Kamel Mazouzi en copie)."
echo "   Le relire, y porter le gain reel de la campagne, puis l'envoyer."
exit 1
