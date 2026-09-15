#!/usr/bin/env python3
"""Garde-fou à passer AVANT `all.py`, qui meurt sans explication utile.

`all.py` appelle `exit()` au premier auteur absent de `affiliations.txt`, après
avoir déjà imprimé une partie de sa sortie : on perd le canevas Publiweb et on
ne sait pas combien d'autres auteurs manquent. Ce script fait le tour complet et
rend tous les problèmes d'un coup.

Contrôles :
  1. auteurs absents de `affiliations.txt` (la cause n° 1 d'arrêt de `all.py`) ;
  2. clés BibTeX dupliquées (`all.py` a une assertion là-dessus) ;
  3. DOI ou titres en double entre entrées, y compris entre les deux fichiers ;
  4. valeur de `publiweb` hors de {True, False, En cours} ;
  5. champs vides indispensables au canevas Publiweb, pour les seules entrées
     encore à déclarer (`publiweb = {False}`).

Sortie : rapport lisible, code de retour 1 si un problème bloquant subsiste.

Usage :
    python3 cv_check.py [--strict]

`--strict` fait aussi échouer sur les avertissements (champs recommandés vides).
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict

import bibtools as bt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true",
                        help="traiter les avertissements comme des erreurs")
    parser.add_argument("--verbose", action="store_true",
                        help="lister aussi les auteurs sans effet sur all.py")
    args = parser.parse_args()

    entries = bt.load_all()
    affiliations = bt.load_affiliations()
    errors: list[str] = []
    warnings: list[str] = []

    print(f"{len(entries)} entrées lues "
          f"({sum(1 for e in entries if e.kind == 'article')} revues, "
          f"{sum(1 for e in entries if e.kind == 'inproceedings')} conférences), "
          f"{len(affiliations)} affiliations.\n")

    # 1. auteurs inconnus d'affiliations.txt
    missing: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        for author in entry.authors:
            if author not in affiliations:
                missing[author].append(entry.key)
    if missing:
        blocking = {a: keys for a, keys in missing.items()
                    if any(not _declared(entries, k) for k in keys)}
        if blocking:
            print("Auteurs absents de affiliations.txt, sur une entrée encore à "
                  "déclarer — all.py s'arrêtera dessus :")
            for author, keys in sorted(blocking.items()):
                print(f"  {author}  ({', '.join(keys[:4])}"
                      f"{'…' if len(keys) > 4 else ''})")
            print("  Format à ajouter : Nom, Prénom $ Affiliation complète $ Pays")
            errors.append(f"{len(blocking)} auteur(s) arrêteront all.py")
        tolerated = len(missing) - len(blocking)
        if tolerated:
            print(f"  ({tolerated} autre(s) auteur(s) sans affiliation, tous sur "
                  "des entrées déjà déclarées : sans effet sur all.py. "
                  "--verbose pour la liste.)")
            if args.verbose:
                for author, keys in sorted(missing.items()):
                    if author not in blocking:
                        print(f"    {author}  ({keys[0]}…)")
        print()

    # 1 bis. accolades parasites qui coupent une entrée en deux
    stray = []
    for path in (bt.JOURNALS_BIB, bt.CONFERENCES_BIB):
        if not path.exists():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("}{"):
                stray.append((path.name, number, line[:70]))
    if stray:
        print("Accolade parasite en début de ligne : elle ferme l'entrée trop tôt, "
              "les champs suivants deviennent invisibles à tout parseur correct.")
        for name, number, text in stray:
            print(f"  {name}:{number}  {text}")
        print("  Correctif : supprimer le } et recaser l'URL dans le champ web.\n")
        errors.append(f"{len(stray)} entrée(s) coupée(s) par une accolade parasite")

    # 2. clés dupliquées
    seen: dict[str, int] = defaultdict(int)
    for entry in entries:
        seen[entry.key] += 1
    duplicates = {k: n for k, n in seen.items() if n > 1}
    if duplicates:
        print("Clés BibTeX dupliquées (assertion fatale dans all.py) :")
        for key, count in sorted(duplicates.items()):
            print(f"  {key} × {count}")
        print()
        errors.append(f"{len(duplicates)} clé(s) dupliquée(s)")

    # 3. DOI et titres en double
    by_doi: dict[str, list[str]] = defaultdict(list)
    by_title: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        doi = bt.normalize_doi(entry.get("doi"))
        if doi:
            by_doi[doi].append(entry.key)
        title = bt.normalize_title(entry.get("title"))
        if title:
            by_title[title].append(entry.key)
    doi_dups = {d: keys for d, keys in by_doi.items() if len(keys) > 1}
    title_dups = {t: keys for t, keys in by_title.items() if len(keys) > 1}
    if doi_dups or title_dups:
        print("Publications en double :")
        for doi, keys in sorted(doi_dups.items()):
            print(f"  même DOI {doi} : {', '.join(keys)}")
        for title, keys in sorted(title_dups.items()):
            if keys not in doi_dups.values():
                print(f"  même titre « {title[:70]}… » : {', '.join(keys)}")
        print("  (une version conférence + une version revue du même travail "
              "est légitime : vérifier avant de supprimer)\n")
        warnings.append(f"{len(doi_dups) + len(title_dups)} doublon(s) potentiel(s)")

    # 4. valeur de publiweb
    bad = [(e.key, e.publiweb) for e in entries
           if e.publiweb not in bt.PUBLIWEB_VALUES]
    if bad:
        print("Champ publiweb hors des valeurs attendues "
              f"({', '.join(sorted(bt.PUBLIWEB_VALUES))}) :")
        for key, value in bad:
            print(f"  {key} : « {value} »")
        print()
        errors.append(f"{len(bad)} champ(s) publiweb invalide(s)")

    # 5. champs manquants sur les entrées encore à déclarer
    to_declare = [e for e in entries if not e.declared_in_publiweb]
    incomplete = []
    for entry in to_declare:
        required = bt.REQUIRED_FOR_PUBLIWEB[entry.kind]
        empty = [f for f in required if not entry.get(f).strip()]
        if empty:
            incomplete.append((entry, empty))
    if to_declare:
        print(f"{len(to_declare)} entrée(s) à déclarer dans Publiweb "
              "(publiweb = {False}) :")
        for entry in to_declare:
            print(f"  {entry.key} — {entry.get('title')[:70]}")
        print()
    if incomplete:
        print("Champs manquants pour le canevas Publiweb :")
        for entry, empty in incomplete:
            print(f"  {entry.key} : {', '.join(empty)}")
        print()
        warnings.append(f"{len(incomplete)} entrée(s) au canevas incomplet")

    # verdict
    print("—" * 60)
    if errors:
        for message in errors:
            print(f"ERREUR   {message}")
    if warnings:
        for message in warnings:
            print(f"ATTENTION {message}")
    if not errors and not warnings:
        print("Rien à signaler, all.py peut tourner.")
    elif not errors:
        print("Aucune erreur bloquante, all.py peut tourner.")

    if errors:
        return 1
    if warnings and args.strict:
        return 1
    return 0


def _declared(entries: list[bt.Entry], key: str) -> bool:
    for entry in entries:
        if entry.key == key:
            return entry.declared_in_publiweb
    return True


if __name__ == "__main__":
    sys.exit(main())
