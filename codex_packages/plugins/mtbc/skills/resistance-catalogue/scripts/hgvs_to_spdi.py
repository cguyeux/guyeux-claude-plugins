#!/usr/bin/env python3
"""Résolveur HGVS -> SPDI (0-based), basé sur les coordonnées génomiques officielles OMS.

Le catalogue OMS 2e éd. fournit `WHO-UCN-TB-2023.7-eng_genomic_coordinates.txt` :
    variant  chromosome  position  reference_nucleotide  alternative_nucleotide
qui mappe chaque variant HGVS (`rrs_n.1401A>G`, `katG_p.Ser315Thr`) à sa/ses coordonnée(s)
génomique(s) H37Rv (NC_000962.3) en convention **1-based** (VCF).

Le pangénome du groupe Guyeux est en SPDI **0-based** (`NC_000962.3:position:ref:alt`,
position = position_VCF - 1 ; vérifié contre pan_spdi.pkl). On applique donc -1.
La notation `variant` OMS == `f"{Gene}_{Mutation}"` de tb-profiler : un seul résolveur
sert les deux sources.

Autonome : si le fichier de coordonnées est absent, il est téléchargé depuis le dépôt
officiel GTB-tbsequencing/mutation-catalogue-2023 et mis en cache.

`resolve()` privilégie la représentation mono-base (SNV) ; `resolve_all()` rend TOUTES les
représentations courtes (SNV + indels/MNV), couvrant le 4e angle mort de représentation
(indels pncA…). Chemins : variable d'environnement RESISTANCE_PROJECT.

Usage :
    python hgvs_to_spdi.py katG_p.Ser315Thr
    python hgvs_to_spdi.py --report
    from hgvs_to_spdi import resolve, resolve_all
"""
import argparse
import os
import sys
import urllib.request
from functools import lru_cache
from pathlib import Path

COORDS_URL = ("https://raw.githubusercontent.com/GTB-tbsequencing/"
              "mutation-catalogue-2023/main/Final%20Result%20Files/"
              "WHO-UCN-TB-2023.7-eng_genomic_coordinates.txt")

# emplacements candidats (projet Guyeux d'abord, puis cache)
_PROJECT = Path(os.environ.get("RESISTANCE_PROJECT",
                               Path.home() / "docs/codes/mtbc/en_cours/Resistance_antibio"))
_CANDIDATES = [
    _PROJECT / "data/sources/who_catalogue/WHO-UCN-TB-2023.7-eng_genomic_coordinates.txt",
    Path.home() / ".cache/mtbc/WHO-UCN-TB-2023.7-eng_genomic_coordinates.txt",
]


def _coords_file() -> Path:
    for p in _CANDIDATES:
        if p.exists():
            return p
    dest = _CANDIDATES[-1]
    dest.parent.mkdir(parents=True, exist_ok=True)
    sys.stderr.write(f"[hgvs_to_spdi] téléchargement des coordonnées OMS -> {dest}\n")
    urllib.request.urlretrieve(COORDS_URL, dest)
    return dest


@lru_cache(maxsize=1)
def _index():
    """variant -> (snv: SPDI mono-base préféré, allmap: variant -> {toutes représentations})."""
    import csv
    from collections import defaultdict
    snv, allmap = {}, defaultdict(set)
    with open(_coords_file()) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            v = row.get("variant")
            ref = row.get("reference_nucleotide")
            alt = row.get("alternative_nucleotide")
            pos = row.get("position")
            if not v or not ref or not alt or not pos:
                continue
            # convention projet : position 0-based = position VCF (1-based) - 1
            spdi = f"NC_000962.3:{int(pos) - 1}:{ref}:{alt}"
            allmap[v].add(spdi)
            if len(ref) == 1 and len(alt) == 1:
                snv.setdefault(v, spdi)
    return snv, allmap


def resolve(variant: str):
    """SPDI 0-based d'un variant HGVS (mono-base préféré, sinon plus court indel/MNV), ou None."""
    snv, allmap = _index()
    if variant in snv:
        return snv[variant]
    cands = allmap.get(variant)
    return min(cands, key=len) if cands else None


def resolve_all(variant: str, max_len: int = 24):
    """Toutes les représentations SPDI courtes d'un variant (SNV + indels/MNV).

    Filtre ref/alt > max_len bases (grosses délétions LoF). Capture les frameshifts/indels
    courts (ex. pncA `T:TC`) — correction du 4e angle mort de représentation (indels)."""
    _, allmap = _index()
    out = []
    for s in allmap.get(variant, ()):
        _, _, ref, alt = s.split(":")
        if len(ref) <= max_len and len(alt) <= max_len:
            out.append(s)
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variant", nargs="?", help="ex. katG_p.Ser315Thr")
    ap.add_argument("--report", action="store_true", help="couverture + exemples")
    a = ap.parse_args()
    if a.report:
        snv, allmap = _index()
        indels = sum(1 for v in allmap if v not in snv and resolve_all(v))
        print(f"variants ponctuels (SNV) résolus : {len(snv)} | "
              f"non-SNV avec ≥1 indel/MNV court : {indels}")
        for v in ("rrs_n.1401A>G", "katG_p.Ser315Thr", "rpoB_p.Ser450Leu", "pncA_p.Glu173fs"):
            print(f"  {v} -> resolve={resolve(v)} | all={resolve_all(v)[:3]}")
    elif a.variant:
        print(resolve(a.variant) or "None")
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
