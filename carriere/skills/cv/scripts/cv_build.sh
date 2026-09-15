#!/usr/bin/env bash
# Régénère et recompile le CV, puis vérifie que le résultat tient debout.
#
# Séquence : contrôle d'intégrité, all.py (BibTeX -> .tex), pdflatex deux fois
# (la seconde résout les références croisées et les compteurs de publications),
# puis lecture du log. Un pdflatex qui « passe » n'est pas une preuve : le CV
# compile même avec des références manquantes, la seule vérification qui compte
# est la lecture du log et du nombre de pages.
#
# Usage :
#   cv_build.sh                 # contrôle + régénération + compilation
#   cv_build.sh --no-check      # sauter cv_check.py
#   cv_build.sh --variant iuf   # compiler une variante (délègue à cv_variant.py)
#
# Sortie non nulle si pdflatex a échoué ou si le PDF n'a pas été régénéré.

set -uo pipefail

CV_DIR="${CV_DIR:-$HOME/docs/cv}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_CHECK=1

while [ $# -gt 0 ]; do
  case "$1" in
    --no-check) RUN_CHECK=0; shift ;;
    --variant)  exec python3 "$SCRIPT_DIR/cv_variant.py" --name "$2" ;;
    -h|--help)  sed -n '2,18p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "option inconnue : $1" >&2; exit 2 ;;
  esac
done

cd "$CV_DIR" || { echo "introuvable : $CV_DIR" >&2; exit 1; }

if [ "$RUN_CHECK" -eq 1 ]; then
  echo "== Contrôle d'intégrité des BibTeX =="
  if ! python3 "$SCRIPT_DIR/cv_check.py"; then
    echo
    echo "Contrôle en échec. Corriger avant de régénérer : all.py s'arrêterait"
    echo "en cours de route, en laissant des .tex à moitié écrits."
    exit 1
  fi
  echo
fi

echo "== all.py : BibTeX -> references/*.tex =="
# MPLBACKEND=Agg : all.py importe pylab pour les histogrammes de publications
# par année et cherche sinon un affichage graphique.
if ! MPLBACKEND=Agg python3 all.py > /tmp/cv_all_py.log 2>&1; then
  echo "all.py a échoué :"
  tail -20 /tmp/cv_all_py.log
  exit 1
fi
echo "ok ($(grep -c . /tmp/cv_all_py.log) lignes de sortie)"

echo
echo "== pdflatex (2 passes) =="
BEFORE=""
[ -f main.pdf ] && BEFORE=$(stat -c %Y main.pdf)

for pass in 1 2; do
  if ! pdflatex -interaction=nonstopmode -halt-on-error main.tex \
       > /tmp/cv_pdflatex_$pass.log 2>&1; then
    echo "pdflatex a échoué à la passe $pass :"
    grep -A5 "^!" /tmp/cv_pdflatex_$pass.log | head -30
    exit 1
  fi
  echo "passe $pass : ok"
done

if [ ! -f main.pdf ]; then
  echo "main.pdf absent après compilation." >&2
  exit 1
fi
AFTER=$(stat -c %Y main.pdf)
if [ -n "$BEFORE" ] && [ "$BEFORE" = "$AFTER" ]; then
  echo "ATTENTION : main.pdf n'a pas été réécrit." >&2
fi

echo
echo "== Vérification du log =="
LOG=main.log
PAGES=$(pdfinfo main.pdf 2>/dev/null | awk '/^Pages:/{print $2}')
echo "main.pdf : ${PAGES:-?} pages, $(( $(stat -c %s main.pdf) / 1024 )) kio"

# grep -c imprime déjà 0 quand il ne trouve rien : un « || echo 0 » ajouterait
# une seconde ligne et casserait les tests numériques qui suivent.
undefined=$(grep -c "Undefined control sequence" "$LOG" 2>/dev/null)
refs=$(grep -c "LaTeX Warning: Reference .* undefined" "$LOG" 2>/dev/null)
cites=$(grep -c "Citation .* undefined" "$LOG" 2>/dev/null)
overfull=$(grep -c "Overfull \\\\hbox" "$LOG" 2>/dev/null)

[ "$undefined" -gt 0 ] && { echo "ERREUR   $undefined séquence(s) de contrôle indéfinie(s) :";
  grep -B2 "Undefined control sequence" "$LOG" | head -12; }
[ "$refs" -gt 0 ] && { echo "ATTENTION $refs référence(s) non résolue(s) :";
  grep "LaTeX Warning: Reference .* undefined" "$LOG" | head -5; }
[ "$cites" -gt 0 ] && echo "ATTENTION $cites citation(s) non résolue(s)"
# Les débordements de marge sont la panne visuelle typique d'un titre ou d'un
# DOI long ajouté sans césure possible : on ne signale que les francs.
big=$(grep "Overfull \\\\hbox" "$LOG" | awk -F'[( ]' '$2+0 > 20' | wc -l)
[ "$big" -gt 0 ] && { echo "ATTENTION $big débordement(s) de marge > 20 pt (sur $overfull) :";
  grep "Overfull \\\\hbox" "$LOG" | awk -F'[( ]' '$2+0 > 20' | head -5; }

if [ "$undefined" -eq 0 ] && [ "$refs" -eq 0 ]; then
  echo "Rien de bloquant dans le log."
fi

echo
echo "== Publications encore à déclarer dans Publiweb =="
if grep -q "^Titre" /tmp/cv_all_py.log; then
  sed -n '/Informations manquantes dans Publiweb/,/^Rappel:/p' /tmp/cv_all_py.log \
    | sed '$d'
  echo "Canevas ci-dessus : à coller dans le ticket Publiweb (skill femto-tickets)."
else
  echo "Aucune : toutes les entrées sont à publiweb = {True} ou {En cours}."
fi
