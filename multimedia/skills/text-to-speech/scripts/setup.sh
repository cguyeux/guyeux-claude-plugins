#!/usr/bin/env bash
set -euo pipefail

# Installation du skill text-to-speech.
# Trois backends :
#   - mistral (PAR DÉFAUT, recommandé livre audio FR) : nécessite MISTRAL_API_KEY
#       Voxtral (voxtral-mini-tts), voix préréglées dont 6 FR (« Marie »).
#   - openai (narration FR expressive, instructions de prosodie) : OPENAI_API_KEY
#   - kokoro (offline, gratuit, qualité moindre en français)
#
# Usage :
#   bash setup.sh              # installe mistral + openai (backends cloud légers)
#   bash setup.sh --mistral    # Mistral uniquement (défaut du skill)
#   bash setup.sh --openai     # OpenAI uniquement
#   bash setup.sh --kokoro     # Kokoro uniquement
#   bash setup.sh --analyse    # outil d'analyse de voix (parselmouth) pour la galerie
#   bash setup.sh --all        # tout (kokoro tire torch, plus lourd)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

WANT_MISTRAL=0
WANT_OPENAI=0
WANT_KOKORO=0
WANT_ANALYSE=0
case "${1:-}" in
  --mistral) WANT_MISTRAL=1 ;;
  --openai)  WANT_OPENAI=1 ;;
  --kokoro)  WANT_KOKORO=1 ;;
  --analyse) WANT_ANALYSE=1 ;;
  --all)     WANT_MISTRAL=1; WANT_OPENAI=1; WANT_KOKORO=1; WANT_ANALYSE=1 ;;
  "")        WANT_MISTRAL=1; WANT_OPENAI=1 ;;   # défaut : les deux backends cloud
  *) echo "Option inconnue : $1 (--mistral | --openai | --kokoro | --analyse | --all)" >&2; exit 1 ;;
esac

# Choix d'un interpréteur Python compatible.
# Python 3.14 (trop récent) casse l'installation de mistralai/pydantic ;
# on préfère 3.13 ou 3.12 s'ils sont présents.
PYBIN=""
for cand in python3.13 python3.12 python3; do
  if command -v "$cand" >/dev/null 2>&1; then PYBIN="$cand"; break; fi
done
if [[ -z "$PYBIN" ]]; then
  echo "[setup] Aucun python3 trouvé." >&2; exit 1
fi
PYMINOR="$("$PYBIN" -c 'import sys; print(sys.version_info[1])')"
echo "[setup] Interpréteur : $PYBIN ($("$PYBIN" --version 2>&1))"
if (( PYMINOR >= 14 )); then
  echo "[setup] ATTENTION : Python 3.$PYMINOR peut casser l'install de mistralai." >&2
  echo "[setup] Installez python3.12 ou python3.13 si l'installation échoue." >&2
fi

echo "[setup] Vérification des dépendances système..."
missing=()
need=(ffmpeg)
(( WANT_KOKORO )) && need+=(espeak-ng)
for cmd in "${need[@]}"; do
  command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
done
if (( ${#missing[@]} > 0 )); then
  echo "[setup] MANQUANT : ${missing[*]}" >&2
  echo "Sur Arch : sudo pacman -S ${missing[*]}" >&2
  echo "Sur Debian/Ubuntu : sudo apt install ${missing[*]}" >&2
  exit 1
fi

# Venv local
if [[ ! -d .venv ]]; then
  echo "[setup] Création du venv .venv/ avec $PYBIN"
  "$PYBIN" -m venv .venv
fi
.venv/bin/pip install --quiet --upgrade pip

# audioop retiré de la stdlib en Python 3.13+ ; pydub a alors besoin d'audioop-lts.
AUDIOOP=()
if (( PYMINOR >= 13 )); then
  AUDIOOP=(audioop-lts)
fi

if (( WANT_MISTRAL )); then
  echo "[setup] Backend Mistral/Voxtral (mistralai, pydub, tqdm)..."
  .venv/bin/pip install --quiet mistralai pydub tqdm "${AUDIOOP[@]}"
fi
if (( WANT_OPENAI )); then
  echo "[setup] Backend OpenAI (openai, pydub, tqdm)..."
  .venv/bin/pip install --quiet openai pydub tqdm "${AUDIOOP[@]}"
fi
if (( WANT_KOKORO )); then
  echo "[setup] Backend Kokoro (kokoro, soundfile, numpy)..."
  .venv/bin/pip install --quiet 'kokoro>=0.9.4' soundfile numpy
fi
if (( WANT_ANALYSE )); then
  echo "[setup] Outil d'analyse de voix (praat-parselmouth, numpy)..."
  .venv/bin/pip install --quiet praat-parselmouth numpy
fi

echo ""
echo "[setup] OK."
echo ""
if (( WANT_MISTRAL )); then
  echo "Backend Mistral/Voxtral (défaut, livre audio FR) :"
  echo "  export MISTRAL_API_KEY=...   # déjà dans ~/.bashrc"
  echo "  .venv/bin/python ${SCRIPT_DIR}/tts_mistral.py texte.txt -o sortie.mp3"
  echo "  .venv/bin/python ${SCRIPT_DIR}/tts_mistral.py texte.txt -o sortie.mp3 --voice fr_marie_curious"
  echo "  .venv/bin/python ${SCRIPT_DIR}/tts_mistral.py --list-voices --lang fr"
  echo ""
fi
if (( WANT_OPENAI )); then
  echo "Backend OpenAI (narration expressive, instructions de prosodie) :"
  echo "  export OPENAI_API_KEY=sk-..."
  echo "  .venv/bin/python ${SCRIPT_DIR}/tts_openai.py texte.txt -o sortie.mp3 --voice onyx --instructions polar.txt"
  echo ""
fi
if (( WANT_KOKORO )); then
  echo "Backend Kokoro (offline, gratuit) :"
  echo "  .venv/bin/python ${SCRIPT_DIR}/tts_kokoro.py texte.txt -o sortie.mp3 --lang f"
  echo ""
fi
if (( WANT_ANALYSE )); then
  echo "Analyse de voix (sexe, registre, style) pour documenter la galerie :"
  echo "  .venv/bin/python ${SCRIPT_DIR}/analyse_voix.py enregistrement.mp3 --start 90 --dur 30"
  echo ""
fi
