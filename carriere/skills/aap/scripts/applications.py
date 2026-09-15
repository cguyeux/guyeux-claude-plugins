#!/usr/bin/env python3
"""Registre CENTRAL des candidatures a des appels a projets.

Donnees : $AAP_KB/applications.tsv (defaut ~/.agents/knowledge/funding/).

Central et jamais par dossier : c'est la seule structure qui montre qu'on a deux
dossiers chez le meme financeur le meme millesime, ou qu'un mandat en cours interdit
un depot. Un dossier isole ne peut pas le voir, et c'est precisement la contrainte
qui rend un projet ineligible apres coup.

Sous-commandes
    list          etat du registre, filtrable
    show          detail d'une candidature
    add           enregistre une candidature (des le stade idee)
    set           met a jour des champs, redate la ligne
    eligibility   AVANT de monter un dossier : ce qui bloque, mesure sur le registre
    decide        enregistre une decision et rappelle d'ecrire l'enseignement
    open          ce qui est en cours et n'a pas bouge
    merge         fusionne une ligne dans une autre (doublon, ou dossier devenu un depot)
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime

from _kb import kb_dir, load, save, wrap

FILE = "applications.tsv"
CALLS = "calls.tsv"
ACTIVE = {"idee", "go-no-go", "redaction", "depose", "audition"}
STATUS = ["idee", "go-no-go", "redaction", "depose", "audition",
          "accepte", "refuse", "abandonne", "unknown"]


def _age(iso: str) -> int | None:
    try:
        return (date.today() - datetime.strptime(iso.strip()[:10], "%Y-%m-%d").date()).days
    except (ValueError, AttributeError):
        return None


def _call(key: str) -> dict | None:
    _, rows = load(CALLS)
    for r in rows:
        if r["key"] == key:
            return r
    return None


def cmd_list(a) -> int:
    cols, rows = load(FILE)
    for r in rows:
        if a.call and r["call_key"] != a.call:
            continue
        if a.open and r["status"] not in ACTIVE:
            continue
        if a.status and r["status"] != a.status:
            continue
        print(f"{r['status']:10} {r['key']:26} {r['call_key']:20} {r['year']:6} "
              f"{r['role']:18} {r['acronym']}")
    return 0


def cmd_show(a) -> int:
    cols, rows = load(FILE)
    hit = [r for r in rows if r["key"] == a.key]
    if not hit:
        sys.exit(f"candidature inconnue : {a.key}")
    r = hit[0]
    print(f"\n{r['acronym']}  ({r['key']})")
    print(f"Dispositif {r['call_key']} | millesime {r['year']} | role {r['role']}")
    print(f"Coordinateur : {r['coordinator']}")
    print(f"Statut {r['status']} | demande {r['amount_requested']} | "
          f"obtenu {r['amount_granted']}")
    print(f"Depose le {r['submitted_on']} | decide le {r['decision_on']}")
    print(f"Dossier : {r['dossier_path']}")
    print("\nNOTES")
    print(wrap(r["notes"]))
    print(f"\nLigne mise a jour le {r['updated_on']}")
    return 0


def cmd_add(a) -> int:
    cols, rows = load(FILE)
    if any(r["key"] == a.key for r in rows):
        sys.exit(f"{a.key} existe deja, utiliser set")
    if _call(a.call) is None:
        sys.exit(f"dispositif inconnu dans calls.tsv : {a.call}\n"
                 f"le creer d'abord avec calls.py add")
    new = {c: "unknown" for c in cols}
    new.update(key=a.key, acronym=a.acronym, call_key=a.call, year=a.year,
               role=a.role, status=a.status, amount_granted="n/a",
               submitted_on="n/a", decision_on="n/a",
               dossier_path=a.dossier or "unknown", notes=a.notes or "unknown",
               updated_on=date.today().isoformat())
    rows.append(new)
    save(FILE, cols, rows)
    print(f"{a.key} enregistre au statut {a.status}.")
    print("Enchainer sur : applications.py eligibility " + a.call +
          " --year " + a.year)
    return 0


def cmd_set(a) -> int:
    cols, rows = load(FILE)
    hit = [r for r in rows if r["key"] == a.key]
    if not hit:
        sys.exit(f"candidature inconnue : {a.key}")
    r = hit[0]
    for pair in a.field:
        if "=" not in pair:
            sys.exit(f"attendu champ=valeur, recu : {pair}")
        k, v = pair.split("=", 1)
        if k not in cols:
            sys.exit(f"colonne inconnue : {k}\ncolonnes : {', '.join(cols)}")
        if k == "status" and v not in STATUS:
            sys.exit(f"statut invalide : {v}\nvaleurs : {', '.join(STATUS)}")
        r[k] = v
    r["updated_on"] = date.today().isoformat()
    save(FILE, cols, rows)
    print(f"{a.key} mis a jour.")
    return 0


def cmd_eligibility(a) -> int:
    call = _call(a.call)
    if call is None:
        sys.exit(f"dispositif inconnu : {a.call}")
    _, rows = load(FILE)
    print(f"\n=== {call['name']} — millesime {a.year} ===\n")

    if call["source"] == "unknown":
        print("AUCUNE DONNEE VERIFIEE pour ce dispositif. Lire le reglement et "
              "renseigner who_can_apply et blockers AVANT de monter quoi que ce soit.\n")

    print("QUI PEUT PORTER")
    print(wrap(call["who_can_apply"]))
    print("\nCE QUE LE REGLEMENT INTERDIT")
    print(wrap(call["blockers"]))

    same = [r for r in rows if r["call_key"] == a.call and r["year"] == a.year]
    active = [r for r in same if r["status"] in ACTIVE]
    print(f"\nDEJA AU REGISTRE POUR CE DISPOSITIF ET CE MILLESIME : "
          f"{len(same)} ligne(s), dont {len(active)} active(s)")
    for r in same:
        print(f"    {r['status']:10} {r['role']:18} {r['acronym']:14} {r['key']}")

    if a.call == "anr-aapg":
        coord = [r for r in active if r["role"] in ("porteur", "co-porteur")]
        impl = [r for r in active if r["role"] != "n/a"]
        try:
            cap = 2 if int(a.year) >= 2027 else 3
        except ValueError:
            cap = 3
        print("\nLIMITES ANR, mesurees sur le registre")
        print(f"    coordinations : {len(coord)} / 1 autorisee")
        print(f"    implications  : {len(impl)} / {cap} autorisees, les deux etapes cumulees")
        if cap == 2:
            print("    (plafond ramene de 3 a 2 a partir de l'AAPG 2027)")
        if len(coord) > 1:
            print("    DEPASSEMENT de la limite de coordination : ineligibilite.")
        if len(impl) >= cap:
            print("    Plafond d'implication atteint : un dossier de plus rend ineligible.")
        won = [r for r in rows if r["call_key"] == a.call and r["status"] == "accepte"
               and r["role"] in ("porteur", "co-porteur")]
        if won and cap == 2:
            print("\n    CARENCE A VERIFIER : le delai pour les coordinateurs de projets")
            print("    OBTENUS passe a 2 ans a l'AAPG 2027. Projets obtenus au registre :")
            for w in won:
                print(f"        {w['acronym']} ({w['year']}), decide le {w['decision_on']}")
        mandates = [r for r in rows if r["call_key"] == a.call and r["role"] == "n/a"]
        for m in mandates:
            print(f"\n    MANDAT A VERIFIER : {m['key']} (statut {m['status']})")
            print(wrap(m["notes"], indent="        "))

    others = [r for r in rows if r["status"] in ACTIVE and r["call_key"] != a.call]
    if others:
        print("\nAUTRES CANDIDATURES ACTIVES, a confronter aux clauses de non-cumul")
        for r in others:
            print(f"    {r['status']:10} {r['call_key']:20} {r['acronym']:14} {r['key']}")
        print("    Le non-cumul se juge sur l'OBJET et l'INSTRUMENT, ce qu'aucun script")
        print("    ne peut trancher : le lire soi-meme dans le reglement.")

    print("\nCe verdict porte sur l'eligibilite, pas sur l'opportunite.")
    print("Pour l'opportunite, references/go_no_go.md.")
    return 0


def cmd_decide(a) -> int:
    cols, rows = load(FILE)
    hit = [r for r in rows if r["key"] == a.key]
    if not hit:
        sys.exit(f"candidature inconnue : {a.key}")
    r = hit[0]
    if a.outcome not in ("accepte", "refuse", "abandonne"):
        sys.exit("outcome attendu : accepte, refuse ou abandonne")
    r["status"] = a.outcome
    r["decision_on"] = a.on or date.today().isoformat()
    if a.amount:
        r["amount_granted"] = a.amount
    r["updated_on"] = date.today().isoformat()
    save(FILE, cols, rows)
    print(f"{a.key} : {a.outcome} le {r['decision_on']}.")
    print()
    if a.outcome == "refuse":
        print("MAINTENANT, et pas plus tard : ouvrir " + str(kb_dir() / "rejections.md"))
        print("et y verser le VERBATIM des motifs, jamais leur paraphrase adoucie.")
        print("Un motif non ecrit le jour meme ne sera jamais retrouve, et le meme")
        print("reproche reviendra chez le financeur suivant.")
    else:
        print("Verser dans " + str(kb_dir() / "rejections.md") + " ce que cette")
        print("decision apprend : sur quel argument le dossier a porte.")
    return 0


def cmd_merge(a) -> int:
    """Fusionne une ligne dans une autre : le doublon disparait, sa trace reste."""
    cols, rows = load(FILE)
    src = [r for r in rows if r["key"] == a.key]
    dst = [r for r in rows if r["key"] == a.into]
    if not src:
        sys.exit(f"candidature inconnue : {a.key}")
    if not dst:
        sys.exit(f"cible inconnue : {a.into}")
    src, dst = src[0], dst[0]
    if not a.yes:
        print(f"Fusionnerait {src['key']} ({src['acronym']}, {src['status']})")
        print(f"         dans {dst['key']} ({dst['acronym']}, {dst['status']}).")
        print(f"\nNotes de la ligne absorbee, a reprendre a la main si utile :")
        print(wrap(src["notes"]))
        print("\nRelancer avec --yes pour appliquer.")
        return 0
    if src.get("dossier_path", "unknown") not in ("unknown", "", "n/a") \
            and dst.get("dossier_path", "unknown") in ("unknown", "", "n/a"):
        dst["dossier_path"] = src["dossier_path"]
    dst["updated_on"] = date.today().isoformat()
    rows = [r for r in rows if r["key"] != a.key]
    save(FILE, cols, rows)
    print(f"{a.key} fusionne dans {a.into}. Verifier que les notes de {a.into}")
    print("portent bien ce que la ligne absorbee disait, la fusion ne les concatene pas.")
    return 0


def cmd_open(a) -> int:
    cols, rows = load(FILE)
    for r in rows:
        if r["status"] not in ACTIVE:
            continue
        d = _age(r["updated_on"])
        flag = "" if d is None or d <= a.days else f"  (rien depuis {d} j)"
        print(f"{r['status']:10} {r['key']:26} {r['call_key']:20} {r['acronym']}{flag}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)

    q = s.add_parser("list"); q.add_argument("--call"); q.add_argument("--status")
    q.add_argument("--open", action="store_true"); q.set_defaults(func=cmd_list)

    q = s.add_parser("show"); q.add_argument("key"); q.set_defaults(func=cmd_show)

    q = s.add_parser("add"); q.add_argument("key")
    q.add_argument("--acronym", required=True); q.add_argument("--call", required=True)
    q.add_argument("--year", required=True)
    q.add_argument("--role", default="porteur")
    q.add_argument("--status", default="idee", choices=STATUS)
    q.add_argument("--dossier"); q.add_argument("--notes")
    q.set_defaults(func=cmd_add)

    q = s.add_parser("set"); q.add_argument("key")
    q.add_argument("field", nargs="+", metavar="champ=valeur")
    q.set_defaults(func=cmd_set)

    q = s.add_parser("eligibility"); q.add_argument("call")
    q.add_argument("--year", required=True); q.set_defaults(func=cmd_eligibility)

    q = s.add_parser("decide"); q.add_argument("key"); q.add_argument("outcome")
    q.add_argument("--amount"); q.add_argument("--on")
    q.set_defaults(func=cmd_decide)

    q = s.add_parser("merge"); q.add_argument("key")
    q.add_argument("--into", required=True)
    q.add_argument("--yes", action="store_true")
    q.set_defaults(func=cmd_merge)

    q = s.add_parser("open"); q.add_argument("--days", type=int, default=60)
    q.set_defaults(func=cmd_open)

    a = p.parse_args()
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
