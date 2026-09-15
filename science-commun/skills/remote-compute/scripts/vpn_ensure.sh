#!/usr/bin/env bash
# Garantit le VPN UFC avant tout acces distant (mp, mh, ml, ms, bilbo, cluster*,
# tickets.femto-st.fr...). Idempotent : ne fait rien si le tunnel est deja debout.
#
#   vpn_ensure.sh              # garantit le VPN, puis s'arrete
#   vpn_ensure.sh mp           # garantit le VPN puis teste l'acces SSH a mp
#   vpn_ensure.sh --down       # coupe le tunnel
#
# Sortie : une ligne d'etat par verification. Code 0 si tout est joignable.
set -uo pipefail

VPN_BIN=/usr/local/bin/vpn
TIMEOUT_SSH=${TIMEOUT_SSH:-45}   # bilbo depasse regulierement 15 s, cf. SKILL.md

vpn_ip() { ip -o addr show 2>/dev/null | grep -oE '10\.248\.[0-9]+\.[0-9]+' | head -1; }

if [ "${1:-}" = "--down" ]; then
  sudo -n "$VPN_BIN" down >/dev/null 2>&1 && echo "VPN : coupe" || echo "VPN : echec de la coupure"
  exit 0
fi

ip_now=$(vpn_ip)
if [ -n "$ip_now" ]; then
  echo "VPN : deja up ($ip_now)"
else
  if ! sudo -n true 2>/dev/null; then
    echo "VPN : DOWN et sudo non disponible sans mot de passe."
    echo "  -> demander a l'utilisateur :  ! sudo vpn up"
    exit 1
  fi
  echo "VPN : down, montee du tunnel..."
  sudo -n "$VPN_BIN" up >/dev/null 2>&1
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    ip_now=$(vpn_ip); [ -n "$ip_now" ] && break
    sleep 1
  done
  if [ -n "$ip_now" ]; then
    echo "VPN : up ($ip_now)"
  else
    echo "VPN : ECHEC de la montee. Diagnostic : sudo -n $VPN_BIN status"
    exit 1
  fi
fi

# Le VPN debout ne suffit pas : le rebond bilbo peut etre le vrai coupable.
host=${1:-}
[ -z "$host" ] && exit 0

for h in bilbo "$host"; do
  if ssh -o ConnectTimeout="$TIMEOUT_SSH" -o BatchMode=yes "$h" true 2>/dev/null; then
    echo "SSH $h : OK"
  else
    echo "SSH $h : INJOIGNABLE (ConnectTimeout=${TIMEOUT_SSH}s)"
    echo "  Ne PAS conclure qu'un fichier est absent ou qu'un job est mort."
    exit 1
  fi
done
