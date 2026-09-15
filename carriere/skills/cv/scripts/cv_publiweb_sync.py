#!/usr/bin/env python3
"""Réconcilie le champ `publiweb` des BibTeX avec ce que FEMTO-ST publie vraiment.

Le champ `publiweb` d'une entrée est censé dire où en est sa déclaration :
`{False}` à déclarer, `{En cours}` ticket déposé, `{True}` archivée. En pratique
la bascule finale `En cours` -> `True` s'oublie, et le champ dérive : 130 entrées
étaient à `{En cours}` en septembre 2026, ce qui ne veut plus rien dire.

La page personnelle publique **est** la preuve d'ingestion : une publication n'y
figure que lorsque l'équipe Publiweb l'a définitivement traitée.

    https://www.femto-st.fr/fr/personnel-femto/cguyeux

Elle s'ouvre sans VPN. Ce script la récupère, apparie chaque publication avec les
entrées des deux `.bib` par DOI puis par titre normalisé, et rend quatre listes :

  1. À BASCULER      présentes sur la page, encore `{False}` ou `{En cours}`
                     dans le .bib  ->  passer à `{True}`
  2. SANS TRACE      `{En cours}` mais absentes de la page : le ticket n'a jamais
                     abouti, ou n'est pas encore traité. À vérifier, éventuellement
                     à repasser en `{False}` pour que le canevas ressorte
  3. À DÉCLARER      `{False}` et absentes de la page : état cohérent, rien à faire
                     ici, elles attendent leur ticket
  4. HORS CV         sur la page mais dans aucun `.bib` : publication déclarée à
                     FEMTO-ST et absente du CV, ou entrée de famille 2 (workshop,
                     ouvrage, logiciel), qui ne passe pas par les `.bib`

Usage :
    python3 cv_publiweb_sync.py                 # rapport seul
    python3 cv_publiweb_sync.py --apply         # écrit les bascules de la liste 1
    python3 cv_publiweb_sync.py --stale-to-false  # + repasse la liste 2 en {False}
    python3 cv_publiweb_sync.py --cache /tmp/p.html  # travailler hors ligne

`--apply` ne touche QUE le champ `publiweb` des entrées de la liste 1, par
réécriture ligne à ligne : aucun autre caractère des `.bib` n'est modifié.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

import bibtools as bt

PAGE_URL = "https://www.femto-st.fr/fr/personnel-femto/cguyeux"

# Types de la page qui correspondent aux deux .bib du CV. Les autres (misc,
# incollection, book, techreport) relèvent des sections écrites à la main.
BIB_TYPES = {"article": "article", "inproceedings": "inproceedings"}


# --------------------------------------------------------------------------- #
# Page personnelle
# --------------------------------------------------------------------------- #

def fetch_page(cache: Path | None) -> str:
    if cache and cache.exists():
        print(f"Page lue depuis le cache : {cache}")
        return cache.read_text(encoding="utf-8", errors="ignore")
    request = urllib.request.Request(
        PAGE_URL, headers={"User-Agent": "Mozilla/5.0 (cv-skill)"})
    with urllib.request.urlopen(request, timeout=60) as response:
        text = response.read().decode("utf-8", errors="ignore")
    if cache:
        cache.write_text(text, encoding="utf-8")
        print(f"Page enregistrée dans {cache}")
    return text


def parse_page(text: str) -> list[dict]:
    """Une entrée par `<li class="<type> y-<année>">` de la page."""
    publications = []
    for match in re.finditer(r'<li class="(\w+) y-(\d{4})">', text):
        kind, year = match.group(1), match.group(2)
        end = text.find("</li>", match.end())
        block = text[match.end():end if end > 0 else match.end() + 4000]

        title_match = re.search(r"<strong[^>]*>(.*?)</strong>", block, re.S)
        if not title_match:
            continue
        title = html.unescape(re.sub(r"<[^>]+>", "", title_match.group(1))).strip()

        doi = ""
        doi_match = re.search(r'href="[^"]*?(10\.\d{4,9}/[^"#&\s]+)', block)
        if doi_match:
            doi = html.unescape(doi_match.group(1))

        entry_match = re.search(r"publiweb\.femto-st\.fr/tntnet/entries/(\d+)", block)
        publications.append({
            "kind": kind, "year": year, "title": title, "doi": doi,
            "publiweb_id": entry_match.group(1) if entry_match else "",
        })
    return publications


# --------------------------------------------------------------------------- #
# Appariement
# --------------------------------------------------------------------------- #

def match_entries(entries: list[bt.Entry], published: list[dict]):
    """Apparie par DOI, puis par titre en préférant le même type.

    Un même travail existe souvent en version conférence ET en version revue,
    sous le même titre : apparier sur le titre seul ferait passer l'une pour
    l'autre. Le DOI tranche quand il existe, le type tranche ensuite.
    """
    by_doi: dict[str, list[dict]] = {}
    by_title: dict[str, list[dict]] = {}
    for item in published:
        if item["doi"]:
            by_doi.setdefault(bt.normalize_doi(item["doi"]), []).append(item)
        by_title.setdefault(bt.normalize_title(item["title"]), []).append(item)

    def pick(candidates: list[dict], kind: str) -> dict | None:
        if not candidates:
            return None
        same = [c for c in candidates if BIB_TYPES.get(c["kind"]) == kind]
        return same[0] if same else candidates[0]

    paired: dict[str, dict] = {}
    for entry in entries:
        doi = bt.normalize_doi(entry.get("doi"))
        hit = pick(by_doi.get(doi, []), entry.kind) if doi else None
        if hit is None:
            hit = pick(by_title.get(bt.normalize_title(entry.get("title")), []),
                       entry.kind)
        if hit is not None:
            paired[entry.key] = hit
    return paired


def near_matches(unpaired: list[bt.Entry], orphans: list[dict],
                 threshold: float = 0.55) -> list[tuple[bt.Entry, dict, float]]:
    """Rapprochements probables mais non certains, par recouvrement de mots.

    Sert à repérer les titres qui ont DIVERGÉ : un article dont le titre a changé
    en révision garde son ancien titre dans le .bib et ne s'apparie plus, alors
    que la publication est bel et bien ingérée. Ces cas se corrigent à la main,
    jamais automatiquement : deux articles voisins du même groupe partagent
    facilement 60 % de leur vocabulaire.
    """
    found = []
    for entry in unpaired:
        words = set(bt.normalize_title(entry.get("title")).split())
        if not words:
            continue
        best, score = None, 0.0
        for item in orphans:
            other = set(bt.normalize_title(item["title"]).split())
            if not other:
                continue
            jaccard = len(words & other) / len(words | other)
            if jaccard > score:
                best, score = item, jaccard
        if best is not None and score >= threshold:
            found.append((entry, best, score))
    return sorted(found, key=lambda row: -row[2])


# --------------------------------------------------------------------------- #
# Écriture
# --------------------------------------------------------------------------- #

def set_publiweb(entries: list[bt.Entry], keys: dict[str, str]) -> int:
    """Réécrit le seul champ `publiweb` des entrées nommées. `keys` : clé -> valeur."""
    changed = 0
    for path in (bt.JOURNALS_BIB, bt.CONFERENCES_BIB):
        lines = path.read_text(encoding="utf-8").splitlines()
        current = None
        for index, line in enumerate(lines):
            start = re.match(r"^@\w+\{([^,]+),", line)
            if start:
                current = start.group(1).strip()
                continue
            if current in keys and re.match(r"^\s*publiweb\s*=\s*\{", line):
                lines[index] = f"  publiweb = {{{keys[current]}}},"
                changed += 1
                current = None
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed


# --------------------------------------------------------------------------- #
# Étape oubliée : l'affichage web
# --------------------------------------------------------------------------- #

def _show_pending_display(registry: Path, published: list[dict], show) -> None:
    """Publications archivées par le service mais jamais affichées.

    C'est l'angle mort du dispositif. Karine DIEZ archive la publication et donne
    sa référence `ACTI-2026-000xx` dans le ticket, en précisant que « la demande
    d'affichage Web peut être faite » ; le ticket se ferme tout seul quinze jours
    plus tard, remarque ou pas. Si le mail de suivi n'a pas été transféré à
    Pierre-Alain Masson entre-temps, la publication reste archivée et invisible :
    ni sur la page personnelle, ni dans aucun signal du CV. Un ticket clos ne veut
    donc pas dire une publication en ligne.
    """
    if not registry.exists():
        return
    try:
        data = json.loads(registry.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"\n{registry} illisible, suivi des tickets ignoré.")
        return

    on_page = {bt.normalize_title(p["title"]) for p in published}
    pending = []
    for row in data.get("tickets", []):
        if row.get("affichage_demande"):
            continue
        if bt.normalize_title(row.get("titre", "")) in on_page:
            continue
        label = f"{row.get('ref') or 'réf. inconnue'}  ticket {row.get('ticket')}"
        detail = row.get("en_attente", "")
        pending.append(f"{label}\n      {row.get('titre', '')[:66]}"
                       + (f"\n      en attente : {detail}" if detail else ""))

    show("6. ARCHIVÉES mais PAS AFFICHÉES", pending,
         "Référence d'archivage attribuée, affichage web jamais demandé : elles\n"
         "restent invisibles. Transférer le mail de suivi du ticket à\n"
         "pierre-alain.masson@femto-st.fr, qui coche l'affichage. Groupable :\n"
         "il traite plusieurs publications d'un coup.")


# --------------------------------------------------------------------------- #

def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true",
                        help="basculer en {True} les entrées présentes sur la page")
    parser.add_argument("--stale-to-false", action="store_true",
                        help="repasser en {False} les {En cours} sans trace sur la page")
    parser.add_argument("--cache", type=Path,
                        help="fichier HTML de cache, pour travailler hors ligne")
    parser.add_argument("--tickets", type=Path,
                        default=bt.CV_DIR / "publiweb_suivi.json",
                        help="registre de suivi des tickets (défaut : "
                             "~/docs/cv/publiweb_suivi.json)")
    parser.add_argument("--limit", type=int, default=15,
                        help="entrées listées par rubrique (défaut 15)")
    args = parser.parse_args()

    published = parse_page(fetch_page(args.cache))
    if not published:
        print("Aucune publication lue sur la page : structure changée ou accès "
              "bloqué. Vérifier l'URL à la main avant de conclure quoi que ce soit.")
        return 1
    relevant = [p for p in published if p["kind"] in BIB_TYPES]
    print(f"{len(published)} publications sur la page personnelle, dont "
          f"{len(relevant)} de type revue ou conférence "
          f"({len(published) - len(relevant)} ouvrages, chapitres, rapports et "
          "divers, qui ne passent pas par les .bib).\n")

    entries = bt.load_all()
    paired = match_entries(entries, published)

    to_flip: dict[str, str] = {}
    stale: list[bt.Entry] = []
    waiting: list[bt.Entry] = []
    for entry in entries:
        on_page = entry.key in paired
        state = entry.publiweb
        if on_page and state != "True":
            to_flip[entry.key] = "True"
        elif not on_page and state == "En cours":
            stale.append(entry)
        elif not on_page and state == "False":
            waiting.append(entry)

    matched_items = {id(item) for item in paired.values()}
    orphans = [p for p in relevant if id(p) not in matched_items]

    def show(title: str, rows: list[str], note: str = "") -> None:
        print(f"\n{'=' * 70}\n{title} : {len(rows)}")
        if note:
            print(f"{note}")
        for row in rows[:args.limit]:
            print(f"  {row}")
        if len(rows) > args.limit:
            print(f"  … et {len(rows) - args.limit} autres")

    by_key = {e.key: e for e in entries}
    show("1. À BASCULER en {True}",
         [f"{k}  [{by_key[k].publiweb or 'vide'}]  {by_key[k].get('title')[:60]}"
          for k in to_flip],
         "Présentes sur la page, donc définitivement ingérées par l'équipe Publiweb.")

    show("2. SANS TRACE sur la page, alors que marquées {En cours}",
         [f"{e.key}  {e.get('year')}  {e.get('title')[:60]}" for e in stale],
         "Ticket jamais abouti, encore en traitement, ou publication trop récente.\n"
         "Au-delà de quelques mois, considérer que la déclaration n'a pas eu lieu.")

    show("3. À DÉCLARER, état cohérent ({False}, absente de la page)",
         [f"{e.key}  {e.get('year')}  {e.get('title')[:60]}" for e in waiting],
         "Rien à corriger ici : leur canevas sort déjà dans all.py.")

    unpaired = [e for e in entries if e.key not in paired]
    near = near_matches(unpaired, orphans)
    near_titles = {id(item) for _, item, _ in near}
    show("4. SUR LA PAGE mais dans aucun .bib",
         [f"{p['year']}  {p['kind']:<14}  {p['title'][:60]}"
          for p in orphans if id(p) not in near_titles],
         "Soit une publication déclarée à FEMTO-ST et absente du CV, soit une\n"
         "entrée de famille 2 (workshop, poster) qui ne passe pas par les .bib.")

    show("5. TITRES DIVERGENTS, même travail des deux côtés",
         [f"{e.key} ({score:.0%})\n      .bib  : {e.get('title')[:66]}"
          f"\n      page  : {item['title'][:66]}" for e, item, score in near],
         "Le titre a changé après le dépôt au CV, typiquement en révision. La\n"
         "publication est ingérée : corriger le titre dans le .bib, puis relancer\n"
         "avec --apply. Vérifier chaque cas, un fort recouvrement ne prouve rien.")

    _show_pending_display(args.tickets, published, show)

    print(f"\n{'=' * 70}")
    if not args.apply and not args.stale_to_false:
        print(f"Rapport seul. `--apply` bascule les {len(to_flip)} entrées de la "
              "liste 1 en {True}.")
        if stale:
            print("`--stale-to-false` repasse en plus la liste 2 en {False}, pour "
                  "que leur canevas ressorte et qu'on puisse les redéclarer.")
        return 0

    changes = dict(to_flip) if args.apply else {}
    if args.stale_to_false:
        changes.update({e.key: "False" for e in stale})
    written = set_publiweb(entries, changes)
    print(f"{written} champ(s) publiweb réécrit(s) sur {len(changes)} demandé(s).")
    if written != len(changes):
        print("Écart : une entrée visée n'avait pas de ligne `publiweb`. "
              "Passer cv_check.py.")
    print("Suite : ./cv_build.sh pour régénérer et voir le canevas à jour.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
