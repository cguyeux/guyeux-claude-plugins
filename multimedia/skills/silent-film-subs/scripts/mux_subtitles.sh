#!/usr/bin/env bash
# Ajoute une piste de sous-titres à un .mkv sans réencoder.
# Usage : bash mux_subtitles.sh <film.mkv> <subs.srt> [lang_code] [track_name]
set -euo pipefail

VIDEO="$1"
SUBS="$2"
LANG="${3:-fre}"
NAME="${4:-Sous-titres ${LANG}}"

if [[ ! -f "$VIDEO" ]]; then
  echo "Vidéo introuvable : $VIDEO" >&2; exit 1
fi
if [[ ! -f "$SUBS" ]]; then
  echo "Sous-titres introuvables : $SUBS" >&2; exit 1
fi

# Vérifier UTF-8
if ! file "$SUBS" | grep -q UTF-8; then
  echo "ATTENTION : $SUBS ne semble pas être en UTF-8 (VLC peut planter)." >&2
  echo "  Convertir avec : iconv -f ISO-8859-1 -t UTF-8 in.srt > out.srt" >&2
fi

OUT="${VIDEO%.*}.muxed.mkv"

# mkvmerge crashe avec "locale::facet::_S_create_c_locale" si LC_ALL est mal réglé.
LC_ALL=C.UTF-8 LANG=C.UTF-8 mkvmerge -o "$OUT" \
  "$VIDEO" \
  --language "0:${LANG}" --track-name "0:${NAME}" \
  --default-track-flag "0:yes" \
  "$SUBS"

echo "Produit : $OUT"
