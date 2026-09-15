#!/usr/bin/env python3
"""Crée et compile une variante du CV : format court, langue, dossier ciblé.

Le CV complet fait 39 pages. Un dossier ANR, une audition, une invitation ou une
fiche partenaire en veulent une ou deux. Une variante est un fichier `.tex` à la
racine de `~/docs/cv/` qui réassemble les mêmes blocs `cvDoc/` autrement — c'est
déjà le montage de `iuf.tex`, `deleg.tex`, `erc.tex`, `anr-h14.tex`.

Ce script fait trois choses :

    list                    inventorier les variantes et ce qu'elles importent
    new                     écrire le squelette d'une nouvelle variante
    build                   compiler une variante SANS toucher main.tex

Le point délicat est `build`. Le montage historique demandait de commenter la
ligne `\\input{cv}` de `main.tex`, compiler, puis restaurer : une interruption au
milieu laissait le dépôt dans un état faux et `main.pdf` n'était plus le CV par
défaut. Ici on dérive un fichier maître jetable `_variant_<nom>.tex`, on le
compile, on récupère le PDF et on jette les auxiliaires. `main.tex` n'est jamais
modifié.

Usage :
    python3 cv_variant.py list
    python3 cv_variant.py new --name anr-sadiand --preset 2pages --lang fr \\
                              --focus "tubercul|genom" --for "ANR AAPG 2027"
    python3 cv_variant.py build --name anr-sadiand --lang fr --out ~/Bureau/cv.pdf

Presets de `new`, vérifiés à la compilation :
    1page    identité et métriques — tient en une page
    2pages   idem + domaines de recherche et distinctions — tient en deux pages
    complet  la structure de `cv.tex`, à élaguer à la main

Les blocs longs (financements, encadrements, vulgarisation) ne sont dans aucun
preset court : les ajouter à la main quand le dossier les réclame, en sachant ce
qu'ils coûtent.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

CV_DIR = Path.home() / "docs" / "cv"
SCRIPTS = Path(__file__).resolve().parent

# Fichiers de la racine qui ne sont pas des variantes de CV.
NOT_A_VARIANT = {"main", "cv"}


# --------------------------------------------------------------------------- #
# list
# --------------------------------------------------------------------------- #

def cmd_list(_: argparse.Namespace) -> int:
    active = _active_inputs(CV_DIR / "main.tex")
    print(f"Variante active dans main.tex : {', '.join(active) or 'aucune'}\n")
    rows = []
    for path in sorted(CV_DIR.glob("*.tex")):
        if path.stem in NOT_A_VARIANT:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        blocks = re.findall(r"^\s*\\(?:input|import)\{[^}]*?([\w./]+)\.tex\}",
                            text, re.MULTILINE)
        blocks += re.findall(r"^\s*\\import\{cvDoc/\}\{([\w]+)\.tex\}",
                             text, re.MULTILINE)
        pdf = path.with_suffix(".pdf")
        rows.append((path.stem, len(text.splitlines()),
                     sorted(set(b.split("/")[-1] for b in blocks)),
                     pdf.exists()))
    for name, lines, blocks, has_pdf in rows:
        mark = " (actif)" if name in active else ""
        print(f"{name}{mark}  —  {lines} lignes"
              f"{', PDF présent' if has_pdf else ''}")
        if blocks:
            print(f"    blocs : {', '.join(blocks[:12])}"
                  f"{'…' if len(blocks) > 12 else ''}")
    return 0


def _active_inputs(main: Path) -> list[str]:
    """`\\input{X}` non commentés du corps de main.tex."""
    names = []
    for line in main.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("%"):
            continue
        match = re.match(r"\\input\{([\w./-]+?)(?:\.tex)?\}", stripped)
        if match:
            names.append(match.group(1))
    return names


# --------------------------------------------------------------------------- #
# new
# --------------------------------------------------------------------------- #

# Presets mesurés, pas espérés : « 1page » et « 2pages » tiennent réellement dans
# leur format une fois compilés. Les blocs longs (researchFundings ~2 pages,
# supervisionPhD ~2 pages, researchComm ~3 pages) ne sont dans aucun preset court :
# les ajouter à la main quand le dossier les réclame, en acceptant le dépassement.
PRESETS = {
    "1page": ["titre", "debut", "researchPublicationsSummary"],
    "2pages": ["titre", "debut", "researchArea", "researchPublicationsSummary",
               "researchAwards"],
    "complet": ["titre", "debut", "teaching", "research", "publications"],
}

# Ce que coûte chaque bloc, mesuré à la compilation. Affiché par `new` pour
# guider l'élagage.
BLOCK_COST = {
    "researchComm": "~3 pages",
    "researchFundings": "~2 pages",
    "supervisionPhD": "~2 pages",
    "teachingDetails": "~1,5 page",
    "publications": "~25 pages",
    "research": "~10 pages",
}


def cmd_new(args: argparse.Namespace) -> int:
    path = CV_DIR / f"{args.name}.tex"
    if path.exists() and not args.force:
        print(f"{path} existe déjà. --force pour l'écraser.")
        return 1

    blocks = PRESETS[args.preset]
    lines = [
        f"% Variante « {args.name} » — {args.preset}, "
        f"{'français' if args.lang == 'fr' else 'anglais'}",
        f"% Destinataire : {args.for_ or 'à préciser'}",
        f"% Créée le {date.today().isoformat()} par cv_variant.py.",
        "%",
        "% Compiler sans toucher main.tex :",
        f"%   python3 cv_variant.py build --name {args.name} --lang {args.lang}",
        "%",
        "% Les blocs viennent de cvDoc/ et sont partagés avec le CV complet :",
        "% ne jamais les éditer pour un besoin propre à ce dossier, écrire le",
        "% texte spécifique directement ici.",
        "",
    ]
    for block in blocks:
        lines.append(f"\\import{{cvDoc/}}{{{block}.tex}}")
        lines.append("")

    if args.focus:
        selection = _selection_tex(args.focus, args.top)
        lines += [
            "%" + "-" * 68,
            f"% Publications représentatives du thème « {args.focus} ».",
            "% Sélection produite par cv_select.py, À RELIRE : le filtre attrape",
            "% des faux amis et ne connaît pas l'importance relative des travaux.",
            "%" + "-" * 68,
            "\\begin{anglais}",
            "\t\\NewSubSubPart{Selected publications}{}",
            "\\end{anglais}",
            "\\begin{francais}",
            "\t\\NewSubSubPart{Publications représentatives}{}",
            "\\end{francais}",
            "\\sectiongap",
            "",
            selection,
            "",
            "\\begin{anglais}",
            "\tFull list: \\href{https://scholar.google.com/citations?user=ebdFNfYAAAAJ&hl=en}{[Google Scholar]}, "
            "\\href{http://dblp.uni-trier.de/pers/hd/g/Guyeux:Christophe}{[dblp]}",
            "\\end{anglais}",
            "\\begin{francais}",
            "\tListe complète : \\href{https://scholar.google.com/citations?user=ebdFNfYAAAAJ&hl=en}{[Google Scholar]}, "
            "\\href{http://dblp.uni-trier.de/pers/hd/g/Guyeux:Christophe}{[dblp]}",
            "\\end{francais}",
            "",
        ]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Écrit : {path}")
    print(f"Blocs importés : {', '.join(blocks)}")
    heavy = [f"{b} ({BLOCK_COST[b]})" for b in blocks if b in BLOCK_COST]
    if heavy:
        print(f"Blocs volumineux inclus : {', '.join(heavy)}")
    print("Blocs disponibles non inclus, à ajouter si le dossier les demande : "
          + ", ".join(f"{b} ({c})" for b, c in BLOCK_COST.items()
                      if b not in blocks))
    print("\nÀ faire à la main avant compilation :")
    print("  - relire la sélection de publications si --focus a été utilisé ;")
    print("  - retirer les blocs hors sujet pour ce dossier précis "
          "(researchComm pèse 3 pages à lui seul) ;")
    print("  - ajouter le texte propre au dossier, ici et pas dans cvDoc/.")
    print(f"\nCompiler : python3 cv_variant.py build --name {args.name} "
          f"--lang {args.lang}")
    return 0


def _selection_tex(focus: str, top: int) -> str:
    out = subprocess.run(
        [sys.executable, str(SCRIPTS / "cv_select.py"), "--focus", focus,
         "--top", str(top), "--format", "tex"],
        capture_output=True, text=True)
    if out.returncode != 0:
        return f"% cv_select.py n'a rien trouvé pour « {focus} »"
    return out.stdout.strip()


# --------------------------------------------------------------------------- #
# build
# --------------------------------------------------------------------------- #

def cmd_build(args: argparse.Namespace) -> int:
    variant = CV_DIR / f"{args.name}.tex"
    if not variant.exists():
        print(f"{variant} n'existe pas. `list` pour l'inventaire, "
              "`new` pour en créer une.")
        return 1

    master = _derive_master(args.name, args.lang)
    print(f"Fichier maître jetable : {master.name} (main.tex non modifié)")

    for step in (1, 2):
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", master.name],
            cwd=CV_DIR, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"pdflatex a échoué à la passe {step} :")
            for line in result.stdout.splitlines():
                if line.startswith("!") or "Error" in line:
                    print(f"  {line}")
            print(f"\nLe fichier maître est conservé pour diagnostic : {master}")
            return 1
        print(f"passe {step} : ok")

    produced = master.with_suffix(".pdf")
    destination = Path(args.out).expanduser() if args.out else \
        CV_DIR / f"{args.name}.pdf"
    shutil.copy2(produced, destination)
    pages = _page_count(destination)
    print(f"\n{destination}  —  {pages} page(s), "
          f"{destination.stat().st_size // 1024} kio")
    if args.preset_pages and pages > args.preset_pages:
        print(f"ATTENTION : {pages} pages pour une cible de "
              f"{args.preset_pages}. Retirer un bloc, pas réduire la police.")

    _discard([master, produced] + [master.with_suffix(s)
                                   for s in (".aux", ".log", ".out", ".toc")])
    return 0


def _derive_master(name: str, lang: str) -> Path:
    """main.tex avec son préambule intact, mais un seul \\input : la variante."""
    text = (CV_DIR / "main.tex").read_text(encoding="utf-8")
    out_lines, replaced = [], False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(r"\includeversion") or stripped.startswith(r"\excludeversion"):
            continue
        if re.match(r"^\\input\{[\w./-]+\}$", stripped):
            if not replaced:
                out_lines.append(f"\\input{{{name}}}")
                replaced = True
            continue
        if stripped == r"\begin{document}":
            out_lines.append(line)
            if lang == "fr":
                out_lines += [r"\excludeversion{anglais}", r"\includeversion{francais}"]
            else:
                out_lines += [r"\excludeversion{francais}", r"\includeversion{anglais}"]
            continue
        out_lines.append(line)
    if not replaced:
        # main.tex n'avait aucun \input actif : insérer avant \end{document}
        index = out_lines.index(r"\end{document}")
        out_lines.insert(index, f"\\input{{{name}}}")
    master = CV_DIR / f"_variant_{name}.tex"
    master.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return master


def _page_count(pdf: Path) -> int:
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True)
    for line in out.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split()[1])
    return 0


def _discard(paths: list[Path]) -> None:
    """Jette les fichiers de travail à la corbeille, jamais `rm`."""
    existing = [str(p) for p in paths if p.exists()]
    if not existing:
        return
    result = subprocess.run(["gio", "trash", *existing],
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"(fichiers de travail conservés, gio trash indisponible : "
              f"{', '.join(Path(p).name for p in existing)})")


# --------------------------------------------------------------------------- #

def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="inventaire des variantes").set_defaults(func=cmd_list)

    new = sub.add_parser("new", help="créer une variante")
    new.add_argument("--name", required=True)
    new.add_argument("--preset", choices=list(PRESETS), default="2pages")
    new.add_argument("--lang", choices=["fr", "en"], default="fr")
    new.add_argument("--focus", help="motifs de sélection des publications")
    new.add_argument("--top", type=int, default=8)
    new.add_argument("--for", dest="for_", help="destinataire, pour l'en-tête")
    new.add_argument("--force", action="store_true")
    new.set_defaults(func=cmd_new)

    build = sub.add_parser("build", help="compiler une variante")
    build.add_argument("--name", required=True)
    build.add_argument("--lang", choices=["fr", "en"], default="fr")
    build.add_argument("--out", help="chemin du PDF produit")
    build.add_argument("--preset-pages", type=int,
                       help="nombre de pages visé, pour avertir si dépassement")
    build.set_defaults(func=cmd_build)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
