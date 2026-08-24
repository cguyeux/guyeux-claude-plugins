#!/usr/bin/env python3
"""
host_pathogen_pair.py -- pairing automatique humains anciens (AADR) / pathogens anciens (SPAAM).

Entree :
  - aadr_v66_1240K.anno  (AADR v66, ~14 MB)
  - AncientMetagenomeDir/ancientsinglegenome-hostassociated/samples/*.tsv (SPAAM single-genome)

Sortie :
  - matched_pairs_<query>.tsv : paires hote-pathogene avec distance Haversine et fenetre temporelle
  - Resume console des regroupements par projet / region

Usage :
  python host_pathogen_pair.py --pathogen "Mycobacterium tuberculosis" --max-km 500 --max-years 200
  python host_pathogen_pair.py --pathogen-genus Mycobacterium --period "1500-100 BP" --region Europe
"""

import argparse, csv, math, sys, os
from pathlib import Path
from collections import defaultdict, Counter

HERE = Path(__file__).parent
AADR = HERE / "aadr_v66_1240K.anno"
SPAAM = HERE / "AncientMetagenomeDir" / "ancientsinglegenome-hostassociated" / "samples" / "ancientsinglegenome-hostassociated_samples.tsv"


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def load_spaam(genus_filter="Mycobacterium"):
    rows = []
    with open(SPAAM, newline="", encoding="utf-8") as fh:
        rdr = csv.DictReader(fh, delimiter="\t")
        for r in rdr:
            sp = r.get("singlegenome_species", "")
            if genus_filter and genus_filter.lower() not in sp.lower():
                continue
            try:
                lat = float(r["latitude"]); lon = float(r["longitude"]); age = float(r["sample_age"])
            except (ValueError, KeyError):
                continue
            rows.append({
                "project": r["project_name"], "doi": r.get("publication_doi", ""),
                "site": r["site_name"], "country": r["geo_loc_name"],
                "lat": lat, "lon": lon, "age_bp": age,
                "host": r.get("sample_host", ""), "species": sp,
                "material": r.get("material", ""),
                "accession": r.get("archive_accession", ""),
                "sample_name": r.get("sample_name", ""),
            })
    return rows


def load_aadr():
    rows = []
    with open(AADR, encoding="utf-8") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        idx = {name: i for i, name in enumerate(header)}
        gid_i = 0
        date_i = 10
        group_i = 14
        loc_i = 15
        country_i = 16
        lat_i = 17
        lon_i = 18
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) <= lon_i:
                continue
            try:
                lat = float(parts[lat_i]); lon = float(parts[lon_i]); age = float(parts[date_i])
            except ValueError:
                continue
            if age <= 0:
                continue  # individus presents-day
            rows.append({
                "id": parts[gid_i],
                "group": parts[group_i] if len(parts) > group_i else "",
                "locality": parts[loc_i] if len(parts) > loc_i else "",
                "country": parts[country_i] if len(parts) > country_i else "",
                "lat": lat, "lon": lon, "age_bp": age,
            })
    return rows


def pair(pathogens, humans, max_km=500, max_years=200):
    pairs = []
    for p in pathogens:
        for h in humans:
            d = haversine_km(p["lat"], p["lon"], h["lat"], h["lon"])
            dy = abs(p["age_bp"] - h["age_bp"])
            if d <= max_km and dy <= max_years:
                pairs.append({
                    "pathogen_project": p["project"], "pathogen_species": p["species"],
                    "pathogen_site": p["site"], "pathogen_country": p["country"],
                    "pathogen_age_bp": p["age_bp"], "pathogen_accession": p["accession"],
                    "pathogen_sample": p["sample_name"], "pathogen_material": p["material"],
                    "human_id": h["id"], "human_group": h["group"],
                    "human_locality": h["locality"], "human_country": h["country"],
                    "human_age_bp": h["age_bp"],
                    "distance_km": round(d, 1), "delta_years": round(dy, 1),
                })
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--genus", default="Mycobacterium", help="Filtre genre cote pathogene (def: Mycobacterium)")
    ap.add_argument("--species", default=None, help="Filtre espece exacte (ex: Mycobacterium tuberculosis)")
    ap.add_argument("--max-km", type=float, default=500.0, help="Distance max km (def: 500)")
    ap.add_argument("--max-years", type=float, default=200.0, help="Difference age max BP (def: 200)")
    ap.add_argument("--out", default="matched_pairs.tsv")
    ap.add_argument("--summary-only", action="store_true")
    args = ap.parse_args()

    if not AADR.exists():
        print(f"AADR introuvable: {AADR}", file=sys.stderr); sys.exit(1)
    if not SPAAM.exists():
        print(f"SPAAM introuvable: {SPAAM}", file=sys.stderr); sys.exit(1)

    paths = load_spaam(genus_filter=args.genus)
    if args.species:
        paths = [p for p in paths if args.species.lower() in p["species"].lower()]
    print(f"[SPAAM] {len(paths)} pathogenes anciens (filtre genre={args.genus}, espece={args.species or '*'})", file=sys.stderr)

    humans = load_aadr()
    print(f"[AADR ] {len(humans)} humains anciens (age > 0 BP)", file=sys.stderr)

    pairs = pair(paths, humans, max_km=args.max_km, max_years=args.max_years)
    print(f"[PAIR ] {len(pairs)} paires hote-pathogene avec distance <= {args.max_km} km et delta <= {args.max_years} ans", file=sys.stderr)

    # Resume par projet pathogene
    by_proj = defaultdict(list)
    for p in pairs:
        by_proj[p["pathogen_project"]].append(p)
    print("\n=== Resume par projet pathogene ===", file=sys.stderr)
    for proj, plist in sorted(by_proj.items(), key=lambda x: -len(x[1])):
        sites = Counter((p["pathogen_country"], p["pathogen_site"]) for p in plist)
        humans_top = Counter(p["human_group"] for p in plist).most_common(3)
        print(f"  {proj:25s} {len(plist):4d} paires | sites: {len(sites)} | top groupes humains: {humans_top}", file=sys.stderr)

    if not args.summary_only and pairs:
        with open(args.out, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=pairs[0].keys(), delimiter="\t")
            w.writeheader()
            w.writerows(pairs)
        print(f"\n[OUT  ] {len(pairs)} paires ecrites vers {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
