#!/usr/bin/env bash
# Rafraîchit les chiffres du CV : h-index, i10-index, citations, nombre de
# publications, date de dernière mesure. Puis recompile.
#
# Le travail réel est fait par ~/docs/cv/update_scholar.py, qui interroge Google
# Scholar (profil ebdFNfYAAAAJ), recompte les entrées des deux .bib et réécrit
# cvDoc/researchPublicationsSummary.tex en français et en anglais. Ce wrapper
# ajoute ce qui manquait autour :
#
#   - l'environnement : `scholarly` n'est pas installé et il n'y a pas de
#     pyproject.toml dans ~/docs/cv, donc `make scholar` échoue en
#     ModuleNotFoundError. On passe par `uv run --with scholarly` ;
#   - un garde-fou : Scholar bloque parfois le scraping et rend des zéros. Un
#     h-index qui tombe à 0, ou qui BAISSE, est un échec de récupération, pas un
#     résultat. Le fichier est alors restauré ;
#   - la recompilation, sans laquelle le PDF garde les anciens chiffres.
#
# Usage :
#   cv_metrics.sh              # récupère, vérifie, recompile
#   cv_metrics.sh --dry-run    # récupère et montre le diff, sans recompiler

set -uo pipefail

CV_DIR="${CV_DIR:-$HOME/docs/cv}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEX="cvDoc/researchPublicationsSummary.tex"
DRY_RUN=0

[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

cd "$CV_DIR" || { echo "introuvable : $CV_DIR" >&2; exit 1; }

BACKUP=$(mktemp /tmp/researchPublicationsSummary.XXXXXX.tex)
cp "$TEX" "$BACKUP"
echo "Sauvegarde de l'ancien état : $BACKUP"

echo
echo "== Google Scholar =="
if ! command -v uv > /dev/null; then
  echo "uv est absent. Installer scholarly puis lancer : python3 update_scholar.py" >&2
  exit 1
fi
if ! uv run --with scholarly python3 update_scholar.py; then
  echo
  echo "Récupération en échec (Scholar bloque parfois les requêtes automatiques)."
  echo "Le fichier n'a pas été touché. Réessayer plus tard."
  cp "$BACKUP" "$TEX"
  exit 1
fi

echo
echo "== Contrôle de vraisemblance =="
old_h=$(grep -oP '(?<=^)\d+(?=,$)' "$BACKUP" | head -1)
new_h=$(grep -oP '(?<=^)\d+(?=,$)' "$TEX" | head -1)
echo "h-index : ${old_h:-?} -> ${new_h:-?}"

if [ -z "$new_h" ] || [ "$new_h" = "0" ]; then
  echo "ERREUR : h-index nul ou illisible, c'est un échec de scraping." >&2
  cp "$BACKUP" "$TEX"
  echo "Fichier restauré."
  exit 1
fi
if [ -n "$old_h" ] && [ "$new_h" -lt "$old_h" ]; then
  echo "ERREUR : le h-index a BAISSÉ ($old_h -> $new_h). Un h-index ne décroît" >&2
  echo "pas : Scholar a rendu une page partielle." >&2
  cp "$BACKUP" "$TEX"
  echo "Fichier restauré."
  exit 1
fi

echo
echo "== Ce qui change dans le CV =="
# pipefail ferait passer le code de retour 1 de diff (« fichiers différents »)
# pour un échec : on capture d'abord, on teste ensuite.
CHANGES=$(diff "$BACKUP" "$TEX" | grep -E '^[<>]' | head -20)
if [ -n "$CHANGES" ]; then
  echo "$CHANGES"
else
  echo "(aucune différence : les chiffres n'ont pas bougé depuis la dernière mesure)"
fi

if [ "$DRY_RUN" -eq 1 ]; then
  echo
  echo "--dry-run : le .tex est à jour, le PDF non. Lancer cv_build.sh pour finir."
  exit 0
fi

echo
echo "== Recompilation =="
exec "$SCRIPT_DIR/cv_build.sh" --no-check
