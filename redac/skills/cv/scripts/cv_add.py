#!/usr/bin/env python3
"""Ajoute une publication aux BibTeX du CV, sans jamais inventer un champ.

Le script fait la partie mécanique et vérifiable : interroger Crossref, décider
du fichier de destination, forger la clé maison, détecter les doublons, ajouter
les auteurs à `affiliations.txt`, écrire l'entrée. Il ne fait PAS la partie
enquête (lire les mails, retrouver le manuscrit, deviner l'acronyme d'une
conférence) : c'est l'agent qui la mène, puis passe le résultat ici.

Toute information absente reste un champ vide signalé en fin de rapport, jamais
une valeur plausible inventée.

Entrées possibles, exclusives :

    --doi 10.1016/j.jbi.2026.104xxx      métadonnées Crossref
    --title "Titre exact"                recherche Crossref par titre
    --json meta.json                     métadonnées déjà rassemblées (mail, PDF, éditeur)

Options :

    --kind article|inproceedings         force la destination (sinon déduite)
    --set champ=valeur                   complète ou corrige un champ, répétable
    --write                              écrit vraiment (sinon, aperçu seul)
    --add-affiliations "Nom, Prénom=Institution|Pays"   répétable

Le JSON accepte directement les noms de champs BibTeX du dépôt, plus une clé
`authors` qui peut être une liste de `"Nom, Prénom"`.

Exemples :

    python3 cv_add.py --doi 10.3390/ai6100253
    python3 cv_add.py --json /tmp/papier.json --kind inproceedings --write
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import bibtools as bt

CROSSREF = "https://api.crossref.org/works"
MAILTO = "guyeux@gmail.com"          # « polite pool » Crossref, identifie l'appelant

CROSSREF_TYPE_TO_KIND = {
    "journal-article": "article",
    "proceedings-article": "inproceedings",
    "book-chapter": "article",       # à rebasculer à la main, le CV les traite ailleurs
    "posted-content": "article",     # préprint
}


# --------------------------------------------------------------------------- #
# Crossref
# --------------------------------------------------------------------------- #

def crossref_by_doi(doi: str) -> dict:
    url = f"{CROSSREF}/{urllib.parse.quote(bt.normalize_doi(doi))}?mailto={MAILTO}"
    return _fetch(url)["message"]


def crossref_by_title(title: str) -> dict | None:
    query = urllib.parse.urlencode({"query.bibliographic": title, "rows": 5,
                                    "mailto": MAILTO})
    items = _fetch(f"{CROSSREF}?{query}")["message"]["items"]
    target = bt.normalize_title(title)
    for item in items:
        candidate = item.get("title", [""])[0]
        if bt.normalize_title(candidate) == target:
            return item
    if items:
        print("Aucune correspondance exacte sur le titre. Candidats Crossref :")
        for item in items[:5]:
            print(f"  {item.get('DOI')} — {item.get('title', [''])[0][:80]}")
        print("Relancer avec --doi sur le bon, ou passer par --json.")
    return None


def _fetch(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent":
                                                   f"cv-skill (mailto:{MAILTO})"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def from_crossref(item: dict, kind: str | None) -> tuple[str, dict]:
    """Traduit une réponse Crossref en champs BibTeX du dépôt."""
    kind = kind or CROSSREF_TYPE_TO_KIND.get(item.get("type", ""), "article")

    authors = []
    for person in item.get("author", []):
        family = person.get("family", "").strip()
        given = person.get("given", "").strip()
        if family and given:
            authors.append(f"{family}, {given}")
        elif family:
            authors.append(family)

    parts = (item.get("published-print") or item.get("published-online")
             or item.get("issued") or {}).get("date-parts", [[]])[0]
    year = str(parts[0]) if parts else ""
    month = bt.MONTHS_EN[parts[1] - 1] if len(parts) > 1 and 1 <= parts[1] <= 12 else ""
    day = str(parts[2]) if len(parts) > 2 else ""

    container = (item.get("container-title") or [""])[0]
    fields = {
        "title": (item.get("title") or [""])[0].strip(),
        "author": " and ".join(authors),
        "year": year,
        "month": month,
        "doi": bt.normalize_doi(item.get("DOI", "")),
        "publisher": item.get("publisher", "").strip(),
        "abstract": _clean_abstract(item.get("abstract", "")),
        "volume": item.get("volume", ""),
        "url": item.get("URL", ""),
    }
    if kind == "article":
        fields["journal"] = container
        fields["number"] = item.get("issue", "")
        fields["page"] = item.get("page", "")
    else:
        fields["booktitle"] = container
        fields["pages"] = item.get("page", "")
        fields["day"] = day
    if item.get("subject"):
        fields["keywords"] = ", ".join(item["subject"])
    return kind, {k: v for k, v in fields.items() if v}


def _clean_abstract(text: str) -> str:
    """Crossref rend l'abstract en JATS : on retire le balisage."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = re.sub(r"^\s*Abstract\s*", "", text)
    return re.sub(r"\s+", " ", text).strip()


# --------------------------------------------------------------------------- #
# Programme
# --------------------------------------------------------------------------- #

def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--doi")
    source.add_argument("--title")
    source.add_argument("--json", type=Path)
    parser.add_argument("--kind", choices=["article", "inproceedings"])
    parser.add_argument("--set", action="append", default=[], metavar="CHAMP=VALEUR")
    parser.add_argument("--add-affiliations", action="append", default=[],
                        metavar="NOM=INSTITUTION|PAYS")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    # 1. métadonnées
    if args.doi:
        print(f"Crossref : {bt.normalize_doi(args.doi)}")
        kind, fields = from_crossref(crossref_by_doi(args.doi), args.kind)
    elif args.title:
        item = crossref_by_title(args.title)
        if item is None:
            return 1
        print(f"Crossref : {item.get('DOI')}")
        kind, fields = from_crossref(item, args.kind)
    else:
        data = json.loads(args.json.read_text(encoding="utf-8"))
        if isinstance(data.get("authors"), list):
            data["author"] = " and ".join(data.pop("authors"))
        kind = args.kind or data.pop("kind", None) or (
            "article" if data.get("journal") else "inproceedings")
        fields = {k: str(v) for k, v in data.items() if v not in (None, "")}

    for assignment in args.set:
        name, _, value = assignment.partition("=")
        fields[name.strip()] = value.strip()

    if not fields.get("title"):
        print("ERREUR : pas de titre, rien à ajouter.")
        return 1

    # 2. doublon
    existing = bt.load_all()
    duplicates = bt.find_duplicates(existing, fields["title"], fields.get("doi", ""))
    if duplicates:
        print("\nDéjà présent dans le CV :")
        for entry in duplicates:
            print(f"  {entry.key}  ({entry.source.name})  publiweb = "
                  f"{{{entry.publiweb}}}")
            print(f"    {entry.get('title')[:80]}")
        print("Une version conférence puis une version revue du même travail sont "
              "deux entrées légitimes ; sinon, éditer l'entrée existante plutôt "
              "que d'en ajouter une seconde.")
        if args.write:
            print("\nÉcriture refusée. Forcer en changeant le titre ou le DOI, ou "
                  "éditer l'entrée existante à la main.")
            return 1

    # 3. construction de l'entrée
    entry = bt.blank_entry(kind)
    entry.fields.update({k: v for k, v in fields.items() if k in entry.fields})
    unknown = {k: v for k, v in fields.items() if k not in entry.fields}
    bt.escape_entry(entry)
    entry.key = bt.make_key(entry.authors, entry.get("year") or "0000", kind,
                            {e.key for e in existing})

    # 4. affiliations
    for assignment in args.add_affiliations:
        name, _, rest = assignment.partition("=")
        institution, _, country = rest.partition("|")
        if bt.add_affiliation(name.strip(), institution.strip(), country.strip()):
            print(f"affiliations.txt : + {name.strip()}")
        else:
            print(f"affiliations.txt : {name.strip()} y était déjà")
    affiliations = bt.load_affiliations()
    missing = [a for a in entry.authors if a not in affiliations]

    # 5. rapport
    print(f"\nDestination : {(bt.JOURNALS_BIB if kind == 'article' else bt.CONFERENCES_BIB).name}")
    print(f"Clé         : {entry.key}\n")
    print(entry.to_bibtex())

    required = bt.REQUIRED_FOR_PUBLIWEB[kind]
    empty_required = [f for f in required if not entry.get(f).strip()]
    empty_other = [f for f in entry.fields
                   if not entry.get(f).strip() and f not in required]

    print()
    if unknown:
        print(f"Champs ignorés (hors modèle {kind}) : {', '.join(sorted(unknown))}")
    if empty_required:
        print("À COMPLÉTER avant le ticket Publiweb (le canevas de all.py les "
              f"attend) :\n  {', '.join(empty_required)}")
    if empty_other:
        print(f"Vides mais facultatifs : {', '.join(sorted(empty_other))}")
    if missing:
        print("\nAuteurs absents de affiliations.txt — all.py s'arrêtera dessus :")
        for author in missing:
            print(f"  {author}")
        print("  Les ajouter avec --add-affiliations \"Nom, Prénom=Institution|Pays\"")

    # 6. écriture
    if not args.write:
        print("\n(aperçu seul ; ajouter --write pour écrire)")
        return 0
    if missing:
        print("\nÉcriture refusée tant que des auteurs manquent dans "
              "affiliations.txt : all.py planterait au prochain passage.")
        return 1
    path = bt.append_entry(entry)
    print(f"\nÉcrit dans {path}")
    print("Suite : python3 cv_check.py, puis cv_build.sh, puis le ticket Publiweb "
          "(skill femto-tickets) avec le canevas imprimé par all.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
