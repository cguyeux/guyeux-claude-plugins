#!/usr/bin/env python3
"""Informations administratives recurrentes des dossiers de financement.

Donnees : $AAP_KB/admin_profile.json (defaut ~/.agents/knowledge/funding/).

Ce fichier existe pour une seule raison : ces champs sont redemandes par CHAQUE
formulaire, et les rechercher a chaque dossier coute plus cher que de les tenir a jour
une fois. Ce qui n'a pas ete lu dans un document vaut 'unknown' : un SIRET plausible
est un SIRET faux.

Sous-commandes
    show     affiche le dossier, ou une section
    missing  liste tout ce qui vaut encore unknown, avec ou l'obtenir
    get      valeur d'un champ, pour collage direct dans un formulaire
"""

from __future__ import annotations

import argparse
import json
import sys

from _kb import kb_dir

WHERE = {
    "hosting_institution.pic_number":
        "cellule Europe de l'UMLP : indispensable a tout depot Horizon, le PIC identifie "
        "l'etablissement dans le portail Funding and Tenders.",
    "hosting_institution.vat_number":
        "agence comptable de l'UMLP.",
    "hosting_institution.ape_code":
        "fiche INSEE de l'etablissement.",
    "costs.doctorant": "grille de couts environnes de la DRH ou du service valorisation.",
    "costs.postdoc": "grille de couts environnes de la DRH ou du service valorisation.",
    "costs.ingenieur_etude": "grille de couts environnes de la DRH.",
    "costs.ingenieur_recherche": "grille de couts environnes de la DRH.",
    "costs.overhead_umlp": "service valorisation : le taux varie selon le financeur.",
    "internal_circuit.umlp_dreif": "annuaire UMLP, direction de la recherche.",
    "internal_circuit.valorisation": "annuaire UMLP.",
    "internal_circuit.disc_gestion": "gestionnaire du departement DISC.",
    "internal_circuit.cnrs_delegation": "delegation regionale CNRS de rattachement de FEMTO-ST.",
    "identity.section_cnu": "arrete de nomination.",
    "identity.idhal": "profil HAL.",
    "identity.phone": "signature institutionnelle.",
    "reusable_texts.bio_fr_10_lignes": "a rediger une fois, puis reutiliser. Skill /cv.",
    "reusable_texts.bio_en_10_lignes": "a rediger une fois, puis reutiliser. Skill /cv.",
    "reusable_texts.five_key_publications":
        "skill /cv : la plupart des dossiers en demandent cinq au maximum.",
}


def _load() -> dict:
    p = kb_dir() / "admin_profile.json"
    if not p.exists():
        sys.exit(f"introuvable : {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _walk(d, prefix=""):
    for k, v in d.items():
        if k.startswith("_"):
            continue
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            yield from _walk(v, path)
        else:
            yield path, v


def cmd_show(a) -> int:
    d = _load()
    if a.section:
        if a.section not in d:
            sys.exit(f"section inconnue : {a.section}\n"
                     f"sections : {', '.join(k for k in d if not k.startswith('_'))}")
        d = {a.section: d[a.section]}
    for sec, body in d.items():
        if sec.startswith("_") or not isinstance(body, dict):
            continue
        print(f"\n[{sec}]")
        for k, v in body.items():
            if k.startswith("_source"):
                print(f"    source : {v}")
            elif k.startswith("_"):
                continue
            else:
                print(f"    {k:28} {v}")
    return 0


def cmd_missing(a) -> int:
    d = _load()
    n = 0
    for path, v in _walk(d):
        if v == "unknown":
            n += 1
            print(f"{path}")
            if path in WHERE:
                print(f"    ou l'obtenir : {WHERE[path]}")
    print(f"\n{n} champ(s) a renseigner. Un 'unknown' n'est pas une donnee, "
          f"c'est une verification a faire.")
    return 0


def cmd_get(a) -> int:
    d = _load()
    for path, v in _walk(d):
        if path == a.path or path.endswith("." + a.path):
            print(v)
            return 0
    sys.exit(f"champ inconnu : {a.path}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    q = s.add_parser("show"); q.add_argument("section", nargs="?"); q.set_defaults(func=cmd_show)
    q = s.add_parser("missing"); q.set_defaults(func=cmd_missing)
    q = s.add_parser("get"); q.add_argument("path"); q.set_defaults(func=cmd_get)
    a = p.parse_args()
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
