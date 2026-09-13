#!/usr/bin/env python3
"""Retrouve le PDF auteur d'un manuscrit, pour la pièce jointe du ticket Publiweb.

Publiweb attend deux fichiers : le PDF « auteur » (manuscrit accepté, mise en
page maison, celui qui part sur HAL) et le PDF éditeur. Le premier est le
`main.pdf` du dépôt de l'article, mais ce dépôt peut vivre à plusieurs endroits
et porter plusieurs PDF de générations différentes. Ce script les rassemble et
les classe, il ne choisit pas à la place de l'auteur.

Cherche dans, par ordre de vraisemblance :
  ~/docs/publis/<titre>/            et son sous-dossier article/
  ~/docs/codes/<projet>/article/    (projets initialisés par /init-project)

Le score d'appariement compte les mots significatifs du titre retrouvés dans le
nom du dossier, puis dans le `\\title{}` du LaTeX, qui départage les dossiers au
nom abrégé.

Usage :
    python3 find_manuscript.py "Titre exact ou approché de l'article"
    python3 find_manuscript.py "titre" --all      # tous les candidats, pas les 5 premiers
"""

from __future__ import annotations

import argparse
import re
import subprocess
import unicodedata
from datetime import datetime
from pathlib import Path

ROOTS = [Path.home() / "docs" / "publis", Path.home() / "docs" / "codes"]

# Mots trop fréquents dans les titres pour discriminer quoi que ce soit.
STOPWORDS = {
    "a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "of", "on",
    "or", "the", "to", "with", "using", "based", "towards", "toward", "via",
    "un", "une", "des", "de", "du", "la", "le", "les", "et", "pour", "par",
    "dans", "sur", "aux", "au",
}


def words(text: str) -> set[str]:
    text = "".join(c for c in unicodedata.normalize("NFD", text)
                   if unicodedata.category(c) != "Mn").lower()
    return {w for w in re.findall(r"[a-z0-9]+", text)
            if len(w) > 2 and w not in STOPWORDS}


def latex_title(directory: Path) -> str:
    """Titre déclaré dans le premier .tex du dossier qui en porte un."""
    for name in ("main.tex", "sn-article.tex", "article.tex", "paper.tex"):
        path = directory / name
        if path.exists():
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            match = re.search(r"\\title(?:\[[^\]]*\])?\s*\{", text)
            if not match:
                continue
            start, depth, pos = match.end(), 1, match.end()
            while pos < len(text) and depth:
                if text[pos] == "{":
                    depth += 1
                elif text[pos] == "}":
                    depth -= 1
                pos += 1
            title = re.sub(r"\\[a-zA-Z]+\s*", " ", text[start:pos - 1])
            return re.sub(r"\s+", " ", title.replace("{", "").replace("}", "")).strip()
    return ""


def candidate_units() -> list[tuple[Path, list[Path]]]:
    """(racine du manuscrit, dossiers où chercher ses PDF).

    Un manuscrit de `publis/` porte souvent ses sources dans un sous-dossier
    `article/` : les deux forment une seule unité, sans quoi le dossier au bon
    nom et le dossier au bon contenu sortiraient comme deux candidats rivaux.
    """
    units: list[tuple[Path, list[Path]]] = []
    publis = ROOTS[0]
    if publis.is_dir():
        for child in sorted(publis.iterdir()):
            if not child.is_dir():
                continue
            places = [child]
            for sub in ("article", "manuscript", "paper"):
                if (child / sub).is_dir():
                    places.append(child / sub)
            units.append((child, places))
    codes = ROOTS[1]
    if codes.is_dir():
        for child in sorted(codes.iterdir()):
            article = child / "article"
            if article.is_dir():
                units.append((child, [article]))
    return units


def git_remote(directory: Path) -> str:
    for level in (directory, directory.parent):
        if (level / ".git").exists():
            try:
                out = subprocess.run(
                    ["git", "-C", str(level), "remote", "get-url", "origin"],
                    capture_output=True, text=True, timeout=10)
            except (OSError, subprocess.SubprocessError):
                return ""
            if out.returncode == 0:
                url = out.stdout.strip()
                if "overleaf" in url:
                    return f"Overleaf : {url}"
                return url
    return ""


def _hint(pdf: Path, target: set[str]) -> str:
    """Étiquette ce que le nom du fichier laisse deviner de la version."""
    lowered = pdf.name.lower()
    if any(k in lowered for k in ("anonym", "blind", "double-blind")):
        return "  <- version anonymisée, ne va pas sur HAL"
    if any(k in lowered for k in ("proof", "published", "editor", "reprint")):
        return "  <- ressemble à une version éditeur"
    if pdf.stem.lower() in ("main", "article", "paper"):
        return "  <- candidat PDF auteur"
    if len(target & words(pdf.stem)) / len(target) >= 0.6:
        return "  <- candidat PDF auteur (nommé d'après le titre)"
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("title")
    parser.add_argument("--all", action="store_true",
                        help="afficher tous les candidats plutôt que les 5 meilleurs")
    args = parser.parse_args()

    target = words(args.title)
    if not target:
        print("Titre trop court pour chercher quoi que ce soit.")
        return 1

    scored: list[tuple[float, Path, list[Path], str]] = []
    for root, places in candidate_units():
        score = len(target & words(root.name)) / len(target)
        best_title = ""
        for place in places:
            tex = latex_title(place)
            if tex:
                tex_score = len(target & words(tex)) / len(target)
                if tex_score > score or not best_title:
                    best_title = tex
                score = max(score, tex_score)
        if score >= 0.3:
            scored.append((score, root, places, best_title))
    scored.sort(key=lambda row: -row[0])

    if not scored:
        # Un titre long ne recoupe qu'une fraction d'un dossier au nom court
        # (« Curriculum Learning versus LLM [ICAART extension] » face au titre
        # complet de l'article) : on redescend le seuil plutôt que de conclure
        # à tort à l'absence.
        for root, places in candidate_units():
            score = len(target & words(root.name)) / len(target)
            for place in places:
                tex = latex_title(place)
                if tex:
                    score = max(score, len(target & words(tex)) / len(target))
            if score >= 0.15:
                scored.append((score, root, places, ""))
        scored.sort(key=lambda row: -row[0])
        if scored:
            print("Aucun appariement franc. Candidats faibles, à vérifier "
                  "avant de joindre quoi que ce soit :\n")
        else:
            print("Aucun dossier de manuscrit ne correspond.")
            print("Restent : les pièces jointes de mails (chercher l'accusé "
                  "d'acceptation), ou le projet Overleaf s'il n'a jamais été "
                  "cloné.")
            print("Réessayer avec le nom court du travail plutôt que le titre "
                  "complet : les dossiers sont souvent nommés en raccourci.")
            return 1

    for score, root, places, tex in (scored if args.all else scored[:5]):
        print(f"\n{'=' * 70}\n{root}   (appariement {score:.0%})")
        if tex:
            print(f"  \\title : {tex[:100]}")
        remote = git_remote(root if (root / '.git').exists() else places[-1])
        if remote:
            print(f"  git    : {remote}")
        pdfs: list[Path] = []
        for place in places:
            pdfs.extend(place.glob("*.pdf"))
        pdfs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        if not pdfs:
            print("  aucun PDF compilé — recompiler le dépôt pour obtenir "
                  "le PDF auteur")
            continue
        hints = [_hint(pdf, target) for pdf in pdfs[:8]]
        if not any(h.startswith("  <- candidat") for h in hints):
            # Aucun nom ne trahit sa nature : le plus récent est le point de
            # départ le plus raisonnable, à confirmer en l'ouvrant.
            hints[0] += "  <- le plus récent, à ouvrir pour confirmer"
        print("  PDF, du plus récent au plus ancien :")
        for pdf, hint in zip(pdfs[:8], hints):
            stat = pdf.stat()
            date = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            print(f"    {date}  {stat.st_size // 1024:>6} kio  "
                  f"{pdf.relative_to(root)}{hint}")

    print(f"\n{'=' * 70}")
    print("Le PDF auteur est le manuscrit accepté compilé maison, auteurs "
          "visibles, sans la mise en page de l'éditeur. Vérifier la date : un "
          "main.pdf plus vieux que la dernière révision n'est pas la version "
          "acceptée, il faut recompiler le dépôt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
