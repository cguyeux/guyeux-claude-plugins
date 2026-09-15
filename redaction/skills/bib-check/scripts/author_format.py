#!/usr/bin/env python3
"""Format du champ `author` : une entree sans virgule fait echanger nom et prenom par BibTeX.

Pourquoi cet outil existe. Le 2026-08-03 (Rv2438A), une entree moissonnee depuis NCBI
E-utilities portait :

    author  = {Choe D and Kim U and Hwang S and ...}

Sans virgule entre le nom et les initiales, BibTeX applique la regle « First von Last » et
prend le DERNIER mot comme nom de famille : pour `Choe D`, cela donne prenom = Choe, nom = D.
Le defaut est INVISIBLE dans la bibliographie complete, parce que le style d'impression le
plus courant (`unsrtnat`, et d'autres) imprime les auteurs dans l'ordre « prenom nom », ce qui
reconstitue par coincidence le texte tel qu'il a ete tape. Il n'apparait QUE quand `\\citet` ou
`\\citeauthor` extrait explicitement le champ « nom de famille » pour composer « Nom et al. »,
qui affiche alors « D et al. » au lieu de « Choe et al. ». Une entree peut donc porter ce
defaut pendant des mois sans qu'aucune compilation ne le revele, jusqu'a l'ajout d'une
citation nommee.

Ce script attrape la classe d'erreur sans reseau, en lisant directement le champ `author` :
tout auteur au format `Mot MAJ` ou `Mot MAJ suffixe` (1 a 4 lettres majuscules, sans point ni
virgule) est un nom de famille suivi de ses initiales, jamais correctement parse par BibTeX
tant qu'aucune virgule ne separe les deux.

Usage :
    python3 author_format.py references.bib
    python3 author_format.py references.bib --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SUFFIXES = {"2nd", "3rd", "4th", "Jr", "Jr.", "Sr", "Sr."}

ENTRY = re.compile(r"@(\w+)\s*\{\s*([^,]+),(.*?)\}\s*(?=\s*(?:%[^\n]*(?:\n\s*)?)*(?:@|\Z))", re.S)
INITIALS = re.compile(r"^[A-Z]{1,4}$")


def field(body: str, name: str) -> str | None:
    """Extrait un champ .bib en respectant les accolades IMBRIQUÉES.

    Un `author` accentué protège chaque lettre diacritique dans ses propres accolades
    (`Ja{\\"i}s`, `Guerra-Assun{\\c{c}}{\\~a}o`) : `[^}]*` s'arrête à la PREMIÈRE fermante
    rencontrée, donc tronque le champ dès la première lettre accentuée au lieu de la fin
    réelle du champ. Bug réel constaté le 2026-08-03 : 5/26 champs `author` d'un manuscrit
    réel tronqués, dont un dès le 2e caractère (`torok2008` -> `T{\\"o` puis coupure) — la
    détection de séparation nom/prénom tournait alors sur une chaîne quasi vide pour ces
    entrées, sans qu'aucun avertissement ne le signale. Un compteur de profondeur d'accolades
    est nécessaire dès qu'un champ peut contenir des accents BibTeX ou un autre champ imbriqué.
    """
    m = re.search(rf"\b{name}\s*=\s*\{{", body, re.I)
    if not m:
        return None
    start, depth, i = m.end(), 1, m.end()
    while depth > 0 and i < len(body):
        if body[i] == "{":
            depth += 1
        elif body[i] == "}":
            depth -= 1
        i += 1
    return body[start:i - 1].strip()


def suspect_tokens(author_field: str) -> list[str]:
    """Retourne les auteurs de la forme `Nom INITIALES` sans virgule (parsing BibTeX cassé)."""
    suspects = []
    for token in author_field.split(" and "):
        token = token.strip()
        if not token or "," in token:
            continue  # deja au format Last, First : rien a signaler
        words = token.split()
        if len(words) < 2:
            continue
        if words[-1] in SUFFIXES:
            if len(words) < 3 or not INITIALS.match(words[-2]):
                continue
        elif not INITIALS.match(words[-1]):
            continue
        suspects.append(token)
    return suspects


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bib")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    text = Path(a.bib).read_text(encoding="utf-8")
    findings, checked = [], 0

    for m in ENTRY.finditer(text):
        key, body = m.group(2).strip(), m.group(3)
        author = field(body, "author")
        if not author:
            continue
        checked += 1
        suspects = suspect_tokens(author)
        if suspects:
            findings.append({"key": key, "author": author, "suspects": suspects})

    if a.json:
        print(json.dumps({"checked": checked, "findings": findings}, indent=2, ensure_ascii=False))
        return 1 if findings else 0

    print(f"Format du champ author : {checked} entree(s) avec un champ author, "
          f"{len(findings)} avec au moins un auteur mal separe\n")
    for f in findings:
        print(f"  SUSPECT  @{f['key']}")
        print(f"     author   : {f['author']}")
        print(f"     auteur(s) a risque : {', '.join(f['suspects'])}")
        print("     => sans virgule, BibTeX prend le DERNIER mot pour nom de famille : "
              "invisible sauf sous \\citet/\\citeauthor, qui afficherait les initiales "
              "au lieu du nom. Corriger en 'Nom, I.' (ou 'Nom, suffixe, I.' avec suffixe "
              "generationnel).\n")
    if not findings:
        print("  Aucun auteur mal separe detecte.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
