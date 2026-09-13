#!/usr/bin/env bash
# Build durci de fpocket (Le Guilloux 2009) pour GCC 14+ (avertissements
# -Wincompatible-pointer-types / -Wimplicit-function-declaration /
# -Wint-conversion / -Wimplicit-int promus en erreurs dures depuis GCC 14,
# ce qui casse `make` tel quel sur fpocket 4.2.2/master).
#
# Piste tracée : Rv1025 pistes/P5.md P5.3 (dette d'outillage, durcie 2026-08-24).
# Recette d'origine : Rv1025 P5.1 (2026-07-30), consignée en prose dans
# SKILL.md et ~/.claude/knowledge/tuberculosis.md avant ce script.
#
# Usage :
#   ./build_fpocket.sh [répertoire_cache]
#
# Sans argument, construit dans ~/.cache/fpocket_build/ (hors scratchpad,
# survit aux sessions) et installe le binaire dans ~/.local/bin/fpocket.
# Idempotent : si le binaire cible existe déjà et fonctionne, ne reconstruit
# pas (utiliser --force pour forcer).
set -euo pipefail

FPOCKET_COMMIT="4bb0d8447f62fee77e2c3c29f54b5fcaf5e2c066"
FPOCKET_REPO="https://github.com/Discngine/fpocket.git"

FORCE=0
CACHE_DIR="${HOME}/.cache/fpocket_build"
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    *) CACHE_DIR="$arg" ;;
  esac
done

INSTALL_DIR="${HOME}/.local/bin"
INSTALL_BIN="${INSTALL_DIR}/fpocket"

if [[ "$FORCE" -eq 0 && -x "$INSTALL_BIN" ]]; then
  if "$INSTALL_BIN" 2>&1 | grep -qi "usage\|fpocket"; then
    echo "fpocket déjà installé et fonctionnel : $INSTALL_BIN (--force pour reconstruire)"
    exit 0
  fi
fi

command -v git >/dev/null || { echo "git introuvable" >&2; exit 1; }
command -v gcc >/dev/null || { echo "gcc introuvable" >&2; exit 1; }

GCC_MAJOR="$(gcc -dumpversion | cut -d. -f1)"
echo "GCC détecté : $(gcc --version | head -1) (majeur $GCC_MAJOR)"

mkdir -p "$CACHE_DIR"
SRC_DIR="${CACHE_DIR}/fpocket"

if [[ -d "$SRC_DIR/.git" ]]; then
  echo "Source déjà clonée dans $SRC_DIR, réutilisée."
else
  rm -rf "$SRC_DIR"
  git clone --quiet "$FPOCKET_REPO" "$SRC_DIR"
fi

git -C "$SRC_DIR" checkout --quiet "$FPOCKET_COMMIT"

pushd "$SRC_DIR" >/dev/null
make clean >/dev/null 2>&1 || true

if [[ "$GCC_MAJOR" -ge 14 ]]; then
  echo "GCC >= 14 : application du contournement (avertissements repromus en non-erreurs, Makefile non modifié)."
  make CC="gcc -Wno-error=incompatible-pointer-types -Wno-error=implicit-function-declaration -Wno-error=int-conversion -Wno-error=implicit-int"
else
  make
fi
popd >/dev/null

BUILT_BIN="${SRC_DIR}/bin/fpocket"
if [[ ! -x "$BUILT_BIN" ]]; then
  echo "ÉCHEC : $BUILT_BIN absent après make." >&2
  exit 1
fi

# Vérification fonctionnelle minimale avant d'installer (pas juste "le fichier existe").
if ! "$BUILT_BIN" 2>&1 | grep -qi "usage\|fpocket"; then
  echo "ÉCHEC : $BUILT_BIN construit mais ne répond pas comme fpocket attendu." >&2
  exit 1
fi

mkdir -p "$INSTALL_DIR"
cp "$BUILT_BIN" "$INSTALL_BIN"
chmod +x "$INSTALL_BIN"

echo "OK — fpocket installé : $INSTALL_BIN"
echo "Source mise en cache (~360 Mo, réutilisable) : $SRC_DIR"
echo "Ajouter au PATH si besoin : export PATH=\"\$HOME/.local/bin:\$PATH\""
