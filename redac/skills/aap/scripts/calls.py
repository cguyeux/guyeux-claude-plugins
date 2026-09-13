#!/usr/bin/env python3
"""Base des dispositifs de financement : consultation, ajout, mise a jour.

Donnees : $AAP_KB/calls.tsv (defaut ~/.agents/knowledge/funding/).

Sous-commandes
    list       liste les dispositifs, filtrable
    show       fiche complete d'un dispositif, blockers en evidence
    set        met a jour des champs et redate la verification
    add        cree une ligne pour un dispositif nouvellement rencontre
    due        dispositifs dont la cloture approche
    stale      fiches dont la verification date de plus de N jours
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime

from _kb import kb_dir, load, save, wrap

FILE = "calls.tsv"


def _days_until(iso: str) -> int | None:
    try:
        return (datetime.strptime(iso.strip()[:10], "%Y-%m-%d").date() - date.today()).days
    except (ValueError, AttributeError):
        return None


def cmd_list(a) -> int:
    cols, rows = load(FILE)
    for r in rows:
        if a.funder and a.funder.lower() not in r["funder"].lower():
            continue
        if a.instructed and r["source"] == "unknown":
            continue
        print(f"{r['key']:22} {r['funder'][:28]:28} cloture {r['close_date']:12} "
              f"plafond {r['ceiling'][:28]:28} [{r['source']}]")
    return 0


def cmd_show(a) -> int:
    cols, rows = load(FILE)
    hit = [r for r in rows if r["key"] == a.key]
    if not hit:
        sys.exit(f"dispositif inconnu : {a.key}")
    r = hit[0]
    print(f"\n{r['name']}  ({r['key']})")
    print(f"Financeur : {r['funder']}")
    print(f"\n{r['scope_short']}\n")
    print(f"Periodicite {r['periodicity']} | ouverture {r['open_date']} | "
          f"cloture {r['close_date']} | etape 2 {r['close_date_step2']} | "
          f"resultats {r['results_date']}")
    print(f"Plafond {r['ceiling']} | taux {r['funding_rate']} | duree {r['duration']}")
    print("\nQUI PEUT PORTER")
    print(wrap(r["who_can_apply"]))
    print("\nCE QUI REND INELIGIBLE OU COMPLIQUE")
    print(wrap(r["blockers"]))
    print("\nFORMAT")
    print(wrap(r["format"]))
    print("\nPIECES OBLIGATOIRES")
    print(wrap(r["required_docs"]))
    print(f"\nDepot : {r['portal']}")
    print(f"Contact interne : {r['internal_contact']}")
    print(f"Contact financeur : {r['funder_contact']}")
    if r["detail_file"] not in ("none", "unknown", ""):
        print(f"\nFiche detaillee : {kb_dir() / r['detail_file']}")
    print(f"\nVerifie le {r['verified_on']}, source {r['source']}")
    if r["source"] == "unknown":
        print("ATTENTION : aucune donnee verifiee. Instruire le reglement avant de decider.")
    return 0


def cmd_set(a) -> int:
    cols, rows = load(FILE)
    hit = [r for r in rows if r["key"] == a.key]
    if not hit:
        sys.exit(f"dispositif inconnu : {a.key}")
    r = hit[0]
    for pair in a.field:
        if "=" not in pair:
            sys.exit(f"attendu champ=valeur, recu : {pair}")
        k, v = pair.split("=", 1)
        if k not in cols:
            sys.exit(f"colonne inconnue : {k}\ncolonnes : {', '.join(cols)}")
        r[k] = v
    if not a.keep_date:
        r["verified_on"] = date.today().isoformat()
    save(FILE, cols, rows)
    print(f"{a.key} mis a jour ({len(a.field)} champ(s)), verified_on={r['verified_on']}")
    return 0


def cmd_add(a) -> int:
    cols, rows = load(FILE)
    if any(r["key"] == a.key for r in rows):
        sys.exit(f"{a.key} existe deja, utiliser set")
    new = {c: "unknown" for c in cols}
    new.update(key=a.key, name=a.name, funder=a.funder,
               verified_on=date.today().isoformat(), source=a.source,
               detail_file="none")
    rows.append(new)
    save(FILE, cols, rows)
    print(f"{a.key} cree. Renseigner ensuite who_can_apply et blockers : "
          f"ce sont les deux colonnes qui tuent un dossier quand on les lit trop tard.")
    return 0


def cmd_due(a) -> int:
    cols, rows = load(FILE)
    out = []
    for r in rows:
        for field, label in (("close_date", ""), ("close_date_step2", " (etape 2)")):
            d = _days_until(r.get(field, ""))
            if d is not None and -7 <= d <= a.days:
                out.append((d, r, field, label))
    if not out:
        print(f"aucune cloture connue dans les {a.days} prochains jours.")
        print("Rappel : une date 'unknown' n'est pas une absence d'echeance, "
              "c'est une verification a faire.")
        return 0
    for d, r, field, label in sorted(out, key=lambda t: (t[0], t[1]["key"])):
        mark = "DEPASSEE" if d < 0 else f"J-{d}"
        print(f"{mark:10} {r[field]}  {r['key']:22} {r['name'][:44]}{label}")
    return 0


def cmd_stale(a) -> int:
    cols, rows = load(FILE)
    for r in rows:
        d = _days_until(r["verified_on"])
        if d is None:
            print(f"{'jamais':>10}  {r['key']:22} {r['name'][:50]}")
        elif -d > a.days:
            print(f"{-d:>7} j   {r['key']:22} {r['name'][:50]}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)

    q = s.add_parser("list"); q.add_argument("--funder")
    q.add_argument("--instructed", action="store_true",
                   help="masquer les dispositifs non encore instruits")
    q.set_defaults(func=cmd_list)

    q = s.add_parser("show"); q.add_argument("key"); q.set_defaults(func=cmd_show)

    q = s.add_parser("set"); q.add_argument("key")
    q.add_argument("field", nargs="+", metavar="champ=valeur")
    q.add_argument("--keep-date", action="store_true")
    q.set_defaults(func=cmd_set)

    q = s.add_parser("add"); q.add_argument("key")
    q.add_argument("--name", required=True); q.add_argument("--funder", required=True)
    q.add_argument("--source", default="page-appel")
    q.set_defaults(func=cmd_add)

    q = s.add_parser("due"); q.add_argument("--days", type=int, default=90)
    q.set_defaults(func=cmd_due)

    q = s.add_parser("stale"); q.add_argument("--days", type=int, default=365)
    q.set_defaults(func=cmd_stale)

    a = p.parse_args()
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
