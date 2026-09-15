#!/usr/bin/env python3
"""Sélectionne les publications d'un thème, pour un dossier ciblé.

Un CV complet fait 39 pages et ~290 références : un dossier ANR, une audition ou
une lettre n'en veut qu'une poignée, choisies pour le thème du dossier. Ce script
fait la sélection sur titre, mots-clés et résumé, et la rend au format voulu.

Le rappel prime sur la précision : un seul motif rate toujours des synonymes
(chercher `firefight` rate les entrées qui n'écrivent que `firemen`). Passer
plusieurs motifs séparés par `|`, puis relire la sortie : le script compte les
occurrences par motif pour montrer lequel n'a rien ramené.

Usage :
    python3 cv_select.py --focus "tubercul|mycobact|genom"
    python3 cv_select.py --focus "wildfire|forest fire|firemen" --top 8 --format tex
    python3 cv_select.py --focus "..." --kind article --since 2020 --format bib

Formats : `list` (par défaut, lisible), `tex` (items `\\item` prêts à coller dans
une variante), `bib` (clés seules), `count` (dénombrement par motif).
"""

from __future__ import annotations

import argparse
import re
import sys

import bibtools as bt


def prenoms(full: str) -> str:
    """« Guyeux, Christophe » -> « C. Guyeux », comme le rendu du CV."""
    family, _, given = full.partition(",")
    initials = ".".join(p[0] for p in re.split(r"[\s-]+", given.strip()) if p)
    return f"{initials}. {family.strip()}" if initials else family.strip()


def citation(entry: bt.Entry) -> str:
    authors = ", ".join(prenoms(a) for a in entry.authors)
    title = entry.get("title").replace("\\&", "&").replace("\\%", "%")
    if entry.kind == "article":
        venue = entry.get("journal")
        detail = ", ".join(x for x in (entry.get("volume"), entry.get("page")) if x)
    else:
        venue = entry.get("acronym") or entry.get("booktitle")
        detail = ", ".join(x for x in (entry.get("city"), entry.get("country")) if x)
    parts = [authors, title, venue, detail, entry.get("year")]
    return ". ".join(p for p in parts if p) + "."


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--focus", required=True,
                        help="motifs séparés par | , insensibles à la casse")
    parser.add_argument("--kind", choices=["article", "inproceedings"])
    parser.add_argument("--since", type=int, help="année minimale")
    parser.add_argument("--top", type=int, help="ne garder que les N plus récentes")
    parser.add_argument("--format", choices=["list", "tex", "bib", "count"],
                        default="list")
    parser.add_argument("--fields", default="title,keywords,abstract",
                        help="champs fouillés (défaut : titre, mots-clés, résumé)")
    args = parser.parse_args()

    fields = [f.strip() for f in args.fields.split(",")]
    patterns = [p.strip() for p in args.focus.split("|") if p.strip()]
    entries = bt.load_all()

    if args.kind:
        entries = [e for e in entries if e.kind == args.kind]
    if args.since:
        entries = [e for e in entries
                   if e.get("year").isdigit() and int(e.get("year")) >= args.since]

    per_pattern: dict[str, list[bt.Entry]] = {p: [] for p in patterns}
    selected: list[bt.Entry] = []
    for entry in entries:
        haystack = " ".join(entry.get(f) for f in fields).lower()
        hit = False
        for pattern in patterns:
            if re.search(pattern.lower(), haystack):
                per_pattern[pattern].append(entry)
                hit = True
        if hit:
            selected.append(entry)

    selected.sort(key=lambda e: (e.get("year"), e.get("month")), reverse=True)
    if args.top:
        selected = selected[:args.top]

    if args.format == "count":
        for pattern in patterns:
            count = len(per_pattern[pattern])
            flag = "   <- aucun résultat, motif inutile ou mal orthographié" if not count else ""
            print(f"{count:>4}  {pattern}{flag}")
        print(f"{len(selected):>4}  TOTAL (dédoublonné)")
        return 0

    if not selected:
        print("Aucune publication ne correspond. Élargir les motifs : un thème "
              "s'écrit rarement d'une seule façon dans 290 titres.", file=sys.stderr)
        return 1

    if args.format == "bib":
        for entry in selected:
            print(entry.key)
        return 0

    if args.format == "tex":
        print("% Sélection produite par cv_select.py --focus "
              f"\"{args.focus}\" ({len(selected)} entrées)")
        print("\\begin{etaremune}")
        for entry in selected:
            print(f"  \\item {citation(entry)}")
        print("\\end{etaremune}")
        return 0

    journals = sum(1 for e in selected if e.kind == "article")
    print(f"{len(selected)} publications ({journals} revues, "
          f"{len(selected) - journals} conférences)\n")
    for entry in selected:
        tag = "[J]" if entry.kind == "article" else "[C]"
        print(f"{tag} {entry.get('year')}  {entry.key}")
        print(f"     {citation(entry)}")
    print("\nRelire avant de coller : un motif attrape aussi les faux amis "
          "(« emergence » évolutive pour « emergency », « high-risk clone » "
          "bactérien pour « risk »).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
