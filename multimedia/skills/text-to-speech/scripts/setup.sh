#!/usr/bin/env bash
set -euo pipefail

# Installation du skill text-to-speech.
# Deux backends :
#   - openai (recommandé pour livre audio FR) : nécessite OPENAI_API_KEY
#   - kokoro (offline, gratuit, qualité moindre en français)
#
# Usage :
#   bash setup.sh              # installe tout
#   bash setup.sh --openai     # OpenAI uniquement
#   bash setup.sh --kokoro     # Kokoro uniquement

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

WANT_OPENAI=1
WANT_KOKORO=1
case "${1:-}" in
  --openai) WANT_KOKORO=0 ;;
  --kokoro) WANT_OPENAI=0 ;;
  "") ;;
  *) echo "Option inconnue : $1 (utiliser --openai ou --kokoro)" >&2; exit 1 ;;
esac

echo "[setup] Vérification des dépendances système..."
missing=()
need=(ffmpeg python3)
(( WANT_KOKORO )) && need+=(espeak-ng)

for cmd in "${need[@]}"; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    missing+=("$cmd")
  fi
done

if (( ${#missing[@]} > 0 )); then
  echo "[setup] MANQUANT : ${missing[*]}" >&2
  echo "Sur Arch : sudo pacman -S ${missing[*]/python3/python}" >&2
  echo "Sur Debian/Ubuntu : sudo apt install ${missing[*]}" >&2
  exit 1
fi

# Venv local
if [[ ! -d .venv ]]; then
  echo "[setup] Création du venv .venv/"
  python3 -m venv .venv
fi
.venv/bin/pip install --quiet --upgrade pip

if (( WANT_OPENAI )); then
  echo "[setup] Installation backend OpenAI (openai, pydub, tqdm)..."
  # audioop-lts : remplaçant du module audioop retiré de la stdlib en Python 3.13+,
  # nécessaire pour que pydub fonctionne sur ces versions.
  .venv/bin/pip install --quiet openai pydub tqdm audioop-lts
fi

if (( WANT_KOKORO )); then
  echo "[setup] Installation backend Kokoro (kokoro, soundfile, numpy)..."
  .venv/bin/pip install --quiet 'kokoro>=0.9.4' soundfile numpy
fi

echo ""
echo "[setup] OK."
echo ""
if (( WANT_OPENAI )); then
  echo "Backend OpenAI (recommandé pour livre audio FR) :"
  echo "  export OPENAI_API_KEY=sk-..."
  echo "  .venv/bin/python ${SCRIPT_DIR}/tts_openai.py texte.txt -o sortie.mp3"
  echo "  .venv/bin/python ${SCRIPT_DIR}/tts_openai.py texte.txt -o sortie.mp3 --voice onyx --instructions polar.txt"
  echo ""
fi
if (( WANT_KOKORO )); then
  echo "Backend Kokoro (offline, gratuit) :"
  echo "  .venv/bin/python ${SCRIPT_DIR}/tts_kokoro.py texte.txt -o sortie.mp3 --lang f"
  echo ""
fi
