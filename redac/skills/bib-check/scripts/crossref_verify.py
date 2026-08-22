#!/usr/bin/env python3
r"""Vérification en ligne des entrées .bib à DOI, contre les métadonnées officielles CrossRef.

Pourquoi cet outil existe. La Phase 3 du skill /bib-check décrit une vérification en ligne
entrée par entrée (WebSearch/WebFetch), coûteuse en tours d'agent et sujette à la variabilité
d'un rapport de recherche. Pour toute entrée qui porte déjà un DOI, CrossRef expose les
métadonnées officielles de l'éditeur en un seul appel HTTP, sans clé API. Ce script fait le
travail mécanique (titre/année/revue), et laisse à l'agent la décision finale (corriger ou
signaler) plutôt que la recherche répétitive.

Née d'un besoin réel (tissue_tropism_mtbc, 2026-08-03) : vérifier 26 références en une passe.
Deux pièges rencontrés et corrigés ici :

1. **Extraction de champ .bib par accolades imbriquées.** Un titre protège ses mots à casse
   fixe (`{Mycobacterium}`, `{HIV}`) dans leurs propres accolades : un `[^}]*` naïf tronque le
   champ au premier mot protégé. Un compteur de profondeur d'accolades est nécessaire (même
   correctif que `doi_coherence.py`/`author_format.py`, câblé indépendamment ici pour que ce
   script reste autonome).
2. **Balises HTML de CrossRef collées sans espace.** CrossRef rend parfois `<i>Genus
   species</i>Verb` sans espace autour de la balise (« …tuberculosis</i>Invasion… »). Un simple
   retrait des balises produit alors un mot fantôme (« tuberculosisinvasion ») qui ne correspond
   à rien dans le `.bib` et déclenche un faux écart. Insérer une espace à chaque frontière de
   balise avant de comparer.
3. **`--mark-verified` recollait les entrées entre elles.** La regex `ENTRY` consommait, dans le
   match lui-même, le `\s*` séparant la `}` fermante de l'entrée suivante (nécessaire pour que le
   lookahead saute par-dessus les commentaires `%...`) ; `add_verified` faisait ensuite
   `block.rstrip()` avant de reconstruire l'entrée, ce qui supprimait la ligne vide séparatrice
   sans la restituer — chaque entrée réécrite se retrouvait collée à la suivante (`}@article{...`
   sur une seule ligne). Corrigé (Rv0810c, 2026-08-17) en déplaçant ce `\s*` dans le lookahead
   (zéro-largeur, donc non consommé par le match).

Usage :
    python3 crossref_verify.py references.bib
    python3 crossref_verify.py references.bib --mark-verified   # ajoute verified={date} au .bib
    python3 crossref_verify.py references.bib --json

Limites assumées : n'interroge que les entrées portant un `doi`. Les thèses, rapports et
préprints non résolus par CrossRef restent à vérifier par une autre voie (page de titre du PDF,
WebSearch) — ce script le signale (statut NO_DOI) sans jamais improviser une comparaison.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ENTRY = re.compile(r"@(\w+)\s*\{\s*([^,]+),(.*?)\}(?=\s*(?:%[^\n]*(?:\n\s*)?)*(?:@|\Z))", re.S)
HYPHENS = re.compile(r"[‐‑‒–—]")
QUOTES = re.compile(r"[‘’]")


def field(body: str, name: str) -> str | None:
    """Extrait un champ .bib délimité par {} en respectant les accolades imbriquées."""
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
    return re.sub(r"\s+", " ", body[start:i - 1]).strip()


def norm_title(t: str | None) -> str:
    """Normalise un titre pour comparaison : balises HTML (avec ré-espacement aux frontières),
    accolades/commandes LaTeX, apostrophes et tirets Unicode, casse."""
    if not t:
        return ""
    t = html.unescape(t)
    t = re.sub(r"<[^>]+>", " ", t)     # re-espacer, jamais coller (piège CrossRef ci-dessus)
    t = re.sub(r"[{}\\]", "", t)
    t = QUOTES.sub("'", t)
    t = HYPHENS.sub("-", t)
    t = re.sub(r"-{2,}", "-", t)  # convention LaTeX "--" (tiret demi-cadratin) vs "-" Unicode CrossRef
    t = re.sub(r"\s+", " ", t).strip().lower()
    # le re-espacement aux frontieres de balise (ligne precedente) introduit une espace
    # parasite quand l'italique touche une ponctuation ("<i>pestis</i>, the" -> "pestis , the") :
    # la retirer pour ne pas fabriquer un faux DIFF sur un titre par ailleurs identique.
    return re.sub(r"\s+([,.;:)])", r"\1", t)


def crossref_lookup(doi: str) -> dict | None:
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    req = urllib.request.Request(
        url, headers={"User-Agent": "bib-check/1.0 (mailto:bib-check@localhost)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)["message"]
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return None


def crossref_years(d: dict) -> set[str]:
    """Toutes les annees candidates (issued/print/online) : un .bib qui cite l'annee
    d'edition imprimee (convention bibliographique standard) ne doit pas etre signale
    DIFF juste parce que `issued` pointe la mise en ligne anticipee, plus ancienne."""
    years = set()
    for k in ("issued", "published-print", "published-online"):
        parts = d.get(k, {}).get("date-parts")
        if parts and parts[0] and parts[0][0]:
            years.add(str(parts[0][0]))
    return years


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bib")
    ap.add_argument("--mark-verified", action="store_true",
                    help="ajoute verified={date} aux entrées OK (ne touche pas les DIFF/NO_DOI)")
    ap.add_argument("--sleep", type=float, default=0.4, help="délai entre requêtes CrossRef")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    path = Path(a.bib)
    text = path.read_text(encoding="utf-8")
    results = []

    for m in ENTRY.finditer(text):
        key, body = m.group(2).strip(), m.group(3)
        if re.search(r"\bverified\s*=", body, re.I):
            results.append({"key": key, "status": "SKIP_ALREADY_VERIFIED"})
            continue
        doi = field(body, "doi")
        if not doi:
            results.append({"key": key, "status": "NO_DOI"})
            continue
        d = crossref_lookup(doi)
        time.sleep(a.sleep)
        if d is None:
            results.append({"key": key, "status": "UNRESOLVED", "doi": doi})
            continue
        bib_title = field(body, "title")
        bib_year = field(body, "year")
        bib_journal = field(body, "journal") or field(body, "booktitle")
        xr_title = (d.get("title") or [""])[0]
        xr_years = crossref_years(d)
        xr_journal = (d.get("container-title") or [""])[0]

        title_ok = norm_title(bib_title) == norm_title(xr_title)
        year_ok = bib_year in xr_years if xr_years else True
        journal_ok = (norm_title(bib_journal) == norm_title(xr_journal)) if bib_journal else True
        ok = title_ok and year_ok and journal_ok
        results.append({
            "key": key, "status": "OK" if ok else "DIFF", "doi": doi,
            "bib_title": bib_title, "xr_title": xr_title, "title_ok": title_ok,
            "bib_year": bib_year, "xr_year": "/".join(sorted(xr_years)), "year_ok": year_ok,
            "bib_journal": bib_journal, "xr_journal": xr_journal, "journal_ok": journal_ok,
        })

    if a.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0 if all(r["status"] in ("OK", "NO_DOI", "SKIP_ALREADY_VERIFIED") for r in results) else 1

    n_ok = n_diff = n_nodoi = n_unresolved = n_skip = 0
    for r in results:
        s = r["status"]
        if s == "OK":
            n_ok += 1
            print(f"  OK      {r['key']}")
        elif s == "DIFF":
            n_diff += 1
            print(f"  DIFF    {r['key']}  (doi={r['doi']})")
            if not r["title_ok"]:
                print(f"          titre .bib   : {r['bib_title']}")
                print(f"          titre CrossRef: {r['xr_title']}")
            if not r["year_ok"]:
                print(f"          année .bib={r['bib_year']}  CrossRef={r['xr_year']}")
            if not r["journal_ok"]:
                print(f"          revue .bib   : {r['bib_journal']}")
                print(f"          revue CrossRef: {r['xr_journal']}")
        elif s == "NO_DOI":
            n_nodoi += 1
            print(f"  NO_DOI  {r['key']}  (vérifier autrement : PDF, WebSearch)")
        elif s == "UNRESOLVED":
            n_unresolved += 1
            print(f"  ERREUR  {r['key']}  DOI={r['doi']} ne résout pas (réseau ? DOI invalide ?)")
        else:
            n_skip += 1

    print(f"\n{n_ok} OK, {n_diff} écart(s), {n_nodoi} sans DOI, {n_unresolved} non résolus, "
          f"{n_skip} déjà vérifiés")

    if a.mark_verified and n_ok:
        today = date.today().isoformat()
        ok_keys = {r["key"] for r in results if r["status"] == "OK"}

        def add_verified(m: re.Match) -> str:
            key = m.group(2).strip()
            block = m.group(0)
            if key in ok_keys and not re.search(r"\bverified\s*=", block, re.I):
                return block.rstrip()[:-1].rstrip().rstrip(",") + f",\n  verified = {{{today}}}\n}}"
            return block

        path.write_text(ENTRY.sub(add_verified, text), encoding="utf-8")
        print(f"{len(ok_keys)} entrée(s) marquée(s) verified={{{today}}}")

    return 1 if (n_diff or n_unresolved) else 0


if __name__ == "__main__":
    sys.exit(main())
