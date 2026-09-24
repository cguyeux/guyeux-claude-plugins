#!/usr/bin/env python3
"""Agrege les sorties mosdepth de mosdepth_rd_batch.sh en appels presence/absence.

Usage:
    python3 mosdepth_rd_aggregate.py <depths_dir> <baseline_name> <marker1> [marker2 ...] \
        [--threshold 0.05] [--out rd_calls.tsv]

<depths_dir>     repertoire contenant les <acc>.regions.bed.gz produits par mosdepth_rd_batch.sh
<baseline_name>  nom de la region "genome entier" dans le RD.bed utilise (ex: H37Rv)
<markerN>        noms des RD a rapporter (doivent exister comme colonne "name" du RD.bed)

Formule RDscan (RDscan/workflow/scripts/makeTables.R) : delete ssi
    depth_mediane(region) / depth_mediane(genome) <= threshold (0.05 par defaut).
"""
import argparse
import csv
import glob
import gzip
import os
import sys


def read_regions(path):
    d = {}
    with gzip.open(path, "rt") as f:
        for line in f:
            _, _, _, name, depth = line.rstrip("\n").split("\t")
            d[name] = float(depth)
    return d


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("depths_dir")
    ap.add_argument("baseline_name")
    ap.add_argument("markers", nargs="+")
    ap.add_argument("--threshold", type=float, default=0.05)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.depths_dir, "*.regions.bed.gz")))
    print(f"n_files {len(files)}", file=sys.stderr)

    rows = []
    for f in files:
        acc = os.path.basename(f).split(".regions.bed.gz")[0]
        d = read_regions(f)
        baseline = d.get(args.baseline_name)
        if not baseline:
            continue
        row = {"acc": acc}
        for m in args.markers:
            if m in d:
                ratio = d[m] / baseline
                row[m] = 1 if ratio <= args.threshold else 0
                row[m + "_ratio"] = round(ratio, 4)
        rows.append(row)

    print(f"n_strains_with_baseline {len(rows)}")
    for m in args.markers:
        present = [r for r in rows if m in r]
        deleted = [r for r in present if r[m] == 1]
        if present:
            print(f"{m}: deleted {len(deleted)}/{len(present)} ({100*len(deleted)/len(present):.1f}%)")
        else:
            print(f"{m}: no data")

    if args.out:
        fieldnames = ["acc"] + args.markers + [m + "_ratio" for m in args.markers]
        with open(args.out, "w", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        print(f"written {args.out}")


if __name__ == "__main__":
    main()
