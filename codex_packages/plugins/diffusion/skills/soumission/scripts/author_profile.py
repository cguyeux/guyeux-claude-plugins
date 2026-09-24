#!/usr/bin/env python3
"""Dossier auteur reutilisable et memoire des portails de soumission.

Ce que remplir un formulaire de soumission coute vraiment, ce n'est pas le mot de
passe (Chrome le fournit), ce sont les quarante champs qu'on retape a chaque fois :
affiliation exacte, adresse postale, ORCID, declarations, relecteurs suggeres,
mots-cles. Ce script les memorise une fois pour toutes.

AUCUN SECRET ICI. Ni mot de passe, ni token, ni cle d'API. Les mots de passe
vivent dans le gestionnaire de Chrome, qui les saisit lui-meme ; l'assistant ne
les voit jamais et n'en stocke aucun. Voir references/acces.md.

Donnees :
    $SOUMISSION_KB/author_profile.json   dossier auteur
    $SOUMISSION_KB/portals.tsv           fiche par portail (acces, pieges)

Sous-commandes
    init          cree les fichiers vides commentes
    show          affiche le dossier auteur, pret a remplir un formulaire
    field         extrait une valeur (chemin pointe : affiliation.city)
    set           ecrit une valeur (chemin pointe)
    reviewers     propose des relecteurs, avec les contraintes usuelles
    portals       liste les portails connus
    portal        fiche d'un portail
    portal-set    met a jour une fiche apres une session
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import textwrap
from datetime import date
from pathlib import Path

PORTAL_FIELDS = [
    "portal", "publisher_hint", "url_login", "access_method", "account",
    "account_login", "orcid_sso", "last_success", "twofa", "quirks",
]

ACCESS_METHODS = [
    "session-vivante",      # cookie encore valide, rien a faire
    "orcid-sso",            # bouton "Sign in with ORCID", voie a privilegier
    "chrome-autofill",      # Chrome remplit lui-meme le mot de passe enregistre
    "auteur-requis",        # connexion que seul l'auteur peut faire
    "reset-par-mail",       # plan B : lien de reinitialisation puis Gmail
    "inconnu",
]

TEMPLATE = {
    "_comment": (
        "Dossier auteur pour les formulaires de soumission. Aucun secret ici : "
        "les mots de passe restent dans le gestionnaire de Chrome."
    ),
    "identity": {
        "given_name": "", "family_name": "", "title": "",
        "email_institutional": "", "email_secondary": "",
        "orcid": "", "scopus_id": "", "researcher_id": "", "phone": "",
    },
    "affiliation": {
        "institution": "", "laboratory": "", "department": "",
        "address": "", "postal_code": "", "city": "", "country": "",
        "latex_line": "",
    },
    "declarations": {
        "funding": "", "competing_interests": "", "ethics_approval": "",
        "consent_participate": "", "consent_publication": "",
        "data_availability": "", "code_availability": "",
        "author_contributions": "", "ai_assistance": "",
    },
    "repositories": {
        "github_tb": "", "github_securite_civile": "",
        "preprint_bio": "", "preprint_med": "", "preprint_arxiv": "",
        "zenodo": "",
    },
    "keywords_by_domain": {},
    "reviewers": [],
}


def kb_dir() -> Path:
    return Path(os.environ.get(
        "SOUMISSION_KB", Path.home() / ".agents" / "knowledge" / "journals"))


def profile_path() -> Path:
    return kb_dir() / "author_profile.json"


def portals_path() -> Path:
    return kb_dir() / "portals.tsv"


def load_profile() -> dict:
    p = profile_path()
    if not p.exists():
        print(f"absent : {p}\nlancer d'abord : author_profile.py init", file=sys.stderr)
        sys.exit(1)
    return json.loads(p.read_text(encoding="utf-8"))


def save_profile(data: dict) -> None:
    profile_path().parent.mkdir(parents=True, exist_ok=True)
    profile_path().write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_portals() -> list[dict]:
    p = portals_path()
    if not p.exists():
        return []
    with p.open(encoding="utf-8", newline="") as fh:
        return [dict(r) for r in csv.DictReader(fh, delimiter="\t")]


def save_portals(rows: list[dict]) -> None:
    portals_path().parent.mkdir(parents=True, exist_ok=True)
    with portals_path().open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=PORTAL_FIELDS, delimiter="\t",
                           extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in sorted(rows, key=lambda x: x.get("portal", "")):
            w.writerow({f: (r.get(f) or "").replace("\t", " ").strip()
                        for f in PORTAL_FIELDS})


def dig(data: dict, path: str):
    cur = data
    for part in path.split("."):
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
                continue
            except (ValueError, IndexError):
                return None
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


# --------------------------------------------------------------------------

def cmd_init(args) -> int:
    if profile_path().exists() and not args.force:
        print(f"existe deja : {profile_path()} (--force pour ecraser)", file=sys.stderr)
        return 1
    save_profile(TEMPLATE)
    if not portals_path().exists():
        save_portals([
            {"portal": "editorial-manager", "publisher_hint": "Elsevier, IJAA, Tuberculosis",
             "url_login": "https://www.editorialmanager.com/<code>/",
             "access_method": "inconnu", "orcid_sso": "yes"},
            {"portal": "scholarone", "publisher_hint": "OUP, FEMS, Wiley",
             "url_login": "https://mc.manuscriptcentral.com/<code>",
             "access_method": "inconnu", "orcid_sso": "yes"},
            {"portal": "snapp", "publisher_hint": "Springer Nature",
             "url_login": "https://submission.springernature.com/",
             "access_method": "inconnu", "orcid_sso": "yes"},
            {"portal": "chronoshub", "publisher_hint": "ASM",
             "url_login": "https://asm.chronoshub.io/", "access_method": "inconnu"},
            {"portal": "biorxiv", "publisher_hint": "preprint biologie",
             "url_login": "https://submit.biorxiv.org/", "access_method": "inconnu"},
            {"portal": "arxiv", "publisher_hint": "preprint methodo/calcul",
            "url_login": "https://arxiv.org/login", "access_method": "inconnu",
             "orcid_sso": "no"},
            {"portal": "orcid", "publisher_hint": "identite pivot de tout le reste",
             "url_login": "https://orcid.org/signin", "access_method": "inconnu"},
        ])
    print(f"cree : {profile_path()}\ncree : {portals_path()}\n"
          f"remplir le dossier auteur avec `set`, ou editer le JSON directement.")
    return 0


def cmd_show(args) -> int:
    data = load_profile()
    if args.section:
        sec = dig(data, args.section)
        if sec is None:
            print(f"section inconnue : {args.section}", file=sys.stderr)
            return 1
        print(json.dumps(sec, indent=2, ensure_ascii=False))
        return 0
    missing = []
    for section in ("identity", "affiliation", "declarations", "repositories"):
        block = data.get(section, {})
        print(f"\n[{section}]")
        for k, v in block.items():
            if not v:
                missing.append(f"{section}.{k}")
                print(f"  {k:24s} (vide)")
            else:
                print(f"  {k:24s} " + textwrap.fill(str(v), 96,
                      subsequent_indent=" " * 27))
    revs = data.get("reviewers", [])
    print(f"\n[reviewers] {len(revs)} relecteurs memorises")
    kws = data.get("keywords_by_domain", {})
    if kws:
        print(f"[keywords] {', '.join(kws)}")
    if missing:
        print(f"\n{len(missing)} champs vides, a completer avant la prochaine soumission :")
        for m in missing:
            print(f"  {m}")
    return 0


def cmd_field(args) -> int:
    v = dig(load_profile(), args.path)
    if v is None:
        print(f"chemin absent : {args.path}", file=sys.stderr)
        return 1
    print(v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))
    return 0


def cmd_set(args) -> int:
    data = load_profile()
    parts = args.path.split(".")
    cur = data
    for part in parts[:-1]:
        cur = cur.setdefault(part, {})
        if not isinstance(cur, dict):
            print(f"chemin non navigable : {args.path}", file=sys.stderr)
            return 1
    cur[parts[-1]] = args.value
    save_profile(data)
    print(f"{args.path} = {args.value}")
    return 0


def cmd_reviewers(args) -> int:
    revs = load_profile().get("reviewers", [])
    if not revs:
        print("aucun relecteur memorise. Les portails en demandent souvent 3 a 5, "
              "dont au moins deux d'un pays different de celui des auteurs.\n"
              "En ajouter dans author_profile.json, section \"reviewers\" : "
              "{name, affiliation, country, email, expertise, last_suggested}")
        return 0
    out = revs
    if args.domain:
        out = [r for r in out if args.domain.lower() in
               (r.get("expertise", "") + " " + r.get("affiliation", "")).lower()]
    if args.exclude_country:
        bad = {c.strip().lower() for c in args.exclude_country.split(",")}
        out = [r for r in out if (r.get("country") or "").lower() not in bad]
    if args.exclude:
        bad = {c.strip().lower() for c in args.exclude.split(",")}
        out = [r for r in out if (r.get("name") or "").lower() not in bad]
    out.sort(key=lambda r: r.get("last_suggested", ""))
    countries = set()
    picked = []
    for r in out:
        picked.append(r)
        countries.add(r.get("country", ""))
        if len(picked) >= args.n:
            break
    for r in picked:
        print(f"{r.get('name','?')} — {r.get('affiliation','?')} ({r.get('country','?')})")
        print(f"  {r.get('email','email inconnu')} | {r.get('expertise','')}")
        if r.get("last_suggested"):
            print(f"  deja suggere le {r['last_suggested']}")
    print(f"\n{len(picked)} relecteurs, {len(countries)} pays : {', '.join(sorted(countries))}")
    if len(countries) < 2:
        print("ATTENTION : la plupart des portails exigent au moins deux pays "
              "differents de celui des auteurs.")
    print("Verifier avant de les saisir qu'aucun n'est un co-auteur recent "
          "(conflit d'interet automatique chez la plupart des editeurs).")
    return 0


def cmd_portals(args) -> int:
    rows = load_portals()
    if not rows:
        print("aucun portail memorise (lancer init)")
        return 0
    print(f"{'PORTAIL':18s} {'ACCES':17s} {'ORCID':6s} {'COMPTE':8s} "
          f"{'DERNIERE OK':12s} EDITEURS")
    print("-" * 110)
    for r in rows:
        print(f"{r.get('portal','')[:18]:18s} {r.get('access_method','')[:17]:17s} "
              f"{(r.get('orcid_sso') or '?')[:6]:6s} {(r.get('account') or '?')[:8]:8s} "
              f"{(r.get('last_success') or '-')[:12]:12s} "
              f"{(r.get('publisher_hint') or '')[:44]}")
    return 0


def cmd_portal(args) -> int:
    rows = {r["portal"]: r for r in load_portals()}
    r = rows.get(args.portal)
    if not r:
        print(f"portail inconnu : {args.portal}\nconnus : {', '.join(rows)}",
              file=sys.stderr)
        return 1
    width = max(len(f) for f in PORTAL_FIELDS)
    for f in PORTAL_FIELDS:
        if r.get(f):
            print(f"{f:>{width}} : " + textwrap.fill(r[f], 96,
                  subsequent_indent=" " * (width + 3)))
    if (r.get("orcid_sso") or "") == "yes" and r.get("access_method") != "orcid-sso":
        print("\nCe portail accepte ORCID : essayer d'abord le bouton "
              "\"Sign in with ORCID\" avant toute autre voie.")
    return 0


def cmd_portal_set(args) -> int:
    rows = load_portals()
    idx = {r["portal"]: i for i, r in enumerate(rows)}
    if args.portal not in idx:
        rows.append({f: "" for f in PORTAL_FIELDS} | {"portal": args.portal})
        idx[args.portal] = len(rows) - 1
    r = rows[idx[args.portal]]
    for assign in args.assign:
        if "=" not in assign:
            print(f"attendu champ=valeur : {assign}", file=sys.stderr)
            return 1
        f, v = assign.split("=", 1)
        if f not in PORTAL_FIELDS:
            print(f"champ inconnu : {f}\nchamps : {', '.join(PORTAL_FIELDS)}",
                  file=sys.stderr)
            return 1
        if f == "access_method" and v not in ACCESS_METHODS:
            print(f"methode inconnue : {v}\nmethodes : {', '.join(ACCESS_METHODS)}",
                  file=sys.stderr)
            return 1
        if f == "quirks" and r.get("quirks") and not args.replace:
            v = r["quirks"] + " | " + v
        r[f] = v.replace("\t", " ").strip()
    if args.success:
        r["last_success"] = date.today().isoformat()
    save_portals(rows)
    print(f"{args.portal} : " + ", ".join(args.assign)
          + (f", last_success={r['last_success']}" if args.success else ""))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init", help="cree les fichiers")
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("show", help="affiche le dossier auteur")
    sp.add_argument("section", nargs="?", help="identity, affiliation, declarations...")
    sp.set_defaults(func=cmd_show)

    sp = sub.add_parser("field", help="extrait une valeur")
    sp.add_argument("path", help="chemin pointe, ex: affiliation.city")
    sp.set_defaults(func=cmd_field)

    sp = sub.add_parser("set", help="ecrit une valeur")
    sp.add_argument("path")
    sp.add_argument("value")
    sp.set_defaults(func=cmd_set)

    sp = sub.add_parser("reviewers", help="propose des relecteurs")
    sp.add_argument("--n", type=int, default=5)
    sp.add_argument("--domain")
    sp.add_argument("--exclude-country", default="France",
                    help="pays a eviter, celui des auteurs par defaut")
    sp.add_argument("--exclude", help="noms a exclure (co-auteurs recents)")
    sp.set_defaults(func=cmd_reviewers)

    sub.add_parser("portals", help="liste les portails").set_defaults(func=cmd_portals)

    sp = sub.add_parser("portal", help="fiche d'un portail")
    sp.add_argument("portal")
    sp.set_defaults(func=cmd_portal)

    sp = sub.add_parser("portal-set", help="met a jour une fiche de portail")
    sp.add_argument("portal")
    sp.add_argument("assign", nargs="+", metavar="champ=valeur")
    sp.add_argument("--success", action="store_true",
                    help="date une connexion reussie aujourd'hui")
    sp.add_argument("--replace", action="store_true",
                    help="remplace quirks au lieu d'y ajouter")
    sp.set_defaults(func=cmd_portal_set)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
