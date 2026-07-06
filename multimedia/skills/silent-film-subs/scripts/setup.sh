#!/usr/bin/env bash
# Installe les dépendances locales pour le skill silent-film-subs.
# Usage : bash setup.sh [--lang rus|deu|ita|...]
set -euo pipefail

LANG_CODE="${2:-rus}"
[[ "${1:-}" == "--lang" ]] && LANG_CODE="$2"

DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$DIR/tessdata"

# 1) Vérification des binaires système
for bin in ffmpeg ffprobe tesseract mkvmerge python3 curl; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "ERREUR : $bin manquant. Installer via le gestionnaire de paquets." >&2
    exit 1
  fi
done

# 2) Tesseract traineddata (téléchargement local, pas de sudo)
if [[ ! -f "$DIR/tessdata/${LANG_CODE}.traineddata" ]]; then
  echo "Téléchargement tessdata/${LANG_CODE}.traineddata..."
  curl -fsSL -o "$DIR/tessdata/${LANG_CODE}.traineddata" \
    "https://github.com/tesseract-ocr/tessdata_best/raw/main/${LANG_CODE}.traineddata"
fi

# 3) Venv Python
if [[ ! -d "$DIR/.venv" ]]; then
  python3 -m venv "$DIR/.venv"
fi
"$DIR/.venv/bin/pip" install --quiet --upgrade pip
"$DIR/.venv/bin/pip" install --quiet opencv-python-headless numpy

echo "Setup OK."
echo "  Tessdata : $DIR/tessdata/"
echo "  Python   : $DIR/.venv/bin/python"
