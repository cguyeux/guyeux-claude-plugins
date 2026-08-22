#!/usr/bin/env python3
"""
scout_bioprojects.py — Découverte de BioProjects NCBI récents (ou à runs récents) pour le MTBC.

Angle principal : runs SRA déposés depuis --since pour l'organisme donné, agrégés par BioProject.
Réutilise le gazetteer pays et l'efetch BioProject de sweep_bioprojects.py (global_supplementary/
bioproject_geo/) — aucune duplication de la logique pays ni des règles isolement/séquençage.

USAGE :
  python3 scout_bioprojects.py --organism "Mycobacterium africanum" --since 2025-01-01 \
      [--country Nigeria] [--resistance "MDR,rifampicin,multidrug,XDR"] [--min-runs 1] \
      [--out candidates.tsv]

Avant une campagne large, valider sur un cas connu (cf. SKILL.md § Étape 0) : ce script s'appuie
sur des regex sur le XML brut NCBI, pas un client Entrez dédié, même style que sweep_bioprojects.py.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from xml.etree import ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BIOPROJECT_GEO = os.path.normpath(
    os.path.join(HERE, "..", "..", "..", "..", "..", "mtbc", "global_supplementary", "bioproject_geo")
)
sys.path.insert(0, os.environ.get("BIOPROJECT_GEO_DIR", DEFAULT_BIOPROJECT_GEO))
try:
    from sweep_bioprojects import efetch_bioproject, parse_country  # réutilisation, pas de duplication
except ImportError:
    efetch_bioproject = None
    parse_country = None
    print(
        "AVERTISSEMENT: sweep_bioprojects.py introuvable (BIOPROJECT_GEO_DIR mal résolu) — "
        "pays/titre/résistance resteront vides, seuls les comptes de runs seront produits.",
        file=sys.stderr,
    )

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def fetch(url, retries=3):
    for _ in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            time.sleep(1.0)
    return ""


def esearch(db, term, retmax=5000):
    url = f"{EUTILS}/esearch.fcgi?db={db}&term={urllib.parse.quote(term)}&retmax={retmax}&retmode=json"
    data = fetch(url)
    time.sleep(0.34)
    try:
        return json.loads(data)["esearchresult"]["idlist"]
    except Exception:
        return []


def esummary_sra(uids):
    """UIDs SRA -> liste de dicts {bioproject, organism, run, create_date}."""
    out = []
    for i in range(0, len(uids), 200):
        chunk = uids[i : i + 200]
        url = f"{EUTILS}/esummary.fcgi?db=sra&id={','.join(chunk)}&retmode=xml"
        xml = fetch(url)
        time.sleep(0.34)
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            continue
        for docsum in root.findall(".//DocSum"):
            item = {it.get("Name"): (it.text or "") for it in docsum.findall("Item")}
            exp_xml = item.get("ExpXml", "")
            bioproject = re.search(r"<Bioproject>([^<]+)</Bioproject>", exp_xml)
            organism = re.search(r'Organism ScientificName="([^"]+)"', exp_xml)
            run = re.search(r'acc="([A-Z]{2,4}\d+)"', item.get("Runs", ""))
            out.append(
                {
                    "bioproject": bioproject.group(1) if bioproject else "",
                    "organism": organism.group(1) if organism else "",
                    "run": run.group(1) if run else "",
                    "create_date": item.get("CreateDate", ""),
                }
            )
    return out


def parse_resistance(text, keywords):
    t = text.lower()
    hits = [k for k in keywords if k.lower() in t]
    return "|".join(hits)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--organism", required=True, help='ex: "Mycobacterium africanum"')
    ap.add_argument("--since", required=True, help="YYYY-MM-DD, date de dépôt SRA minimale (PDAT)")
    ap.add_argument("--country", default=None, help="mot-clé ajouté à la recherche SRA (AND, tous champs)")
    ap.add_argument(
        "--resistance",
        default="",
        help="mots-clés séparés par des virgules, recherchés dans titre/description du BioProject",
    )
    ap.add_argument("--min-runs", type=int, default=1, help="n_runs_recent minimum pour retenir un BioProject")
    ap.add_argument("--out", default="candidates.tsv")
    args = ap.parse_args()

    term = f'"{args.organism}"[Organism] AND ("{args.since}"[PDAT] : "3000"[PDAT])'
    if args.country:
        term += f" AND {args.country}[All Fields]"
    print(f"esearch db=sra: {term}", file=sys.stderr)
    uids = esearch("sra", term)
    print(f"{len(uids)} runs SRA trouvés depuis {args.since}", file=sys.stderr)

    header = (
        "bioproject\tn_runs_recent\tdate_min\tdate_max\torganism_declared\ttitle\t"
        "country_guess\tcountry_confidence\tresistance_hit\n"
    )
    if not uids:
        open(args.out, "w").write(header)
        print(f"0 BioProject -> {args.out}", file=sys.stderr)
        return

    records = esummary_sra(uids)
    by_bp = {}
    for r in records:
        bp = r["bioproject"]
        if not bp:
            continue
        e = by_bp.setdefault(bp, {"n": 0, "organisms": set(), "dates": []})
        e["n"] += 1
        if r["organism"]:
            e["organisms"].add(r["organism"])
        if r["create_date"]:
            e["dates"].append(r["create_date"])

    resistance_kw = [k.strip() for k in args.resistance.split(",") if k.strip()]
    rows = []
    for bp, e in sorted(by_bp.items(), key=lambda kv: -kv[1]["n"]):
        if e["n"] < args.min_runs:
            continue
        title, country, conf, res_hit = "", "", 0, ""
        if efetch_bioproject:
            d = efetch_bioproject(bp)
            title = d.get("title", "")
            blob = " ".join([d.get("title", ""), d.get("desc", ""), d.get("name", "")])  # org EXCLU
            countries = parse_country(blob) if parse_country else []
            conf = 3 if len(countries) == 1 else (2 if len(countries) > 1 else 0)
            country = countries[0] if len(countries) == 1 else "|".join(countries)
            res_hit = parse_resistance(blob, resistance_kw) if resistance_kw else ""
        rows.append(
            [
                bp,
                e["n"],
                min(e["dates"]) if e["dates"] else "",
                max(e["dates"]) if e["dates"] else "",
                "|".join(sorted(e["organisms"])),
                title,
                country,
                conf,
                res_hit,
            ]
        )

    with open(args.out, "w") as out:
        out.write(header)
        for row in rows:
            out.write("\t".join(str(x) for x in row) + "\n")
    print(f"{len(rows)} BioProjects (>= {args.min_runs} runs) -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
