#!/usr/bin/env python3
"""Interroge le catalogue consolidé mutation -> résistance (Guyeux group, MTBC).

Le catalogue (`catalogue_consolide.tsv`) croise OMS 2e éd. (2023), tb-profiler et le
signal empirique CRyPTIC en une table longue : une ligne = une assertion (variant,
drogue, verdict, source, grade, comptes), avec SPDI 0-based quand résolu.

Modes :
  --variant katG_p.Ser315Thr        verdicts catalogués pour ce variant (toutes drogues/sources)
  --spdi NC_000962.3:2155167:C:G     idem par SPDI
  --drug isoniazid [--call R-associated]   variants catalogués pour une drogue
  --strain-spdi FILE --drug isoniazid       quels SPDI de la souche sont R-associés (baseline TB-Profiler-like)
  --stats                            résumé du catalogue

Chemin du catalogue : --catalogue, sinon $RESISTANCE_PROJECT/catalogue/, sinon défaut groupe.
Régénération du catalogue : voir le SKILL.md (update_database.py du projet Resistance_antibio).
"""
import argparse
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vocab import canonical_drug

_PROJECT = Path(os.environ.get("RESISTANCE_PROJECT",
                               Path.home() / "docs/codes/mtbc/en_cours/Resistance_antibio"))
_DEFAULT = _PROJECT / "catalogue" / "catalogue_consolide.tsv"


def load(path):
    p = Path(path) if path else _DEFAULT
    if not p.exists():
        sys.exit(f"[query_catalogue] catalogue introuvable : {p}\n"
                 f"  préciser --catalogue, ou régénérer via Resistance_antibio/update_database.py")
    return pd.read_csv(p, sep="\t", dtype=str).fillna("")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogue")
    ap.add_argument("--variant"); ap.add_argument("--spdi")
    ap.add_argument("--drug"); ap.add_argument("--call")
    ap.add_argument("--strain-spdi")
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()
    cat = load(a.catalogue)

    if a.stats:
        print(f"{len(cat)} assertions | {cat['drug'].nunique()} drogues | "
              f"{cat[cat.spdi!=''].spdi.nunique()} SPDI uniques")
        print("sources :", cat["source"].value_counts().to_dict())
        print("verdicts :", cat["call"].value_counts().to_dict())
        print(f"couverture SPDI : {(cat.spdi!='').sum()}/{len(cat)}")
        return

    if a.variant or a.spdi:
        key, col = (a.variant, "variant") if a.variant else (a.spdi, "spdi")
        sub = cat[cat[col] == key]
        if sub.empty:
            print(f"aucune assertion pour {col}={key}")
            return
        cols = ["drug", "call", "source", "source_grade", "spdi", "gene", "n_R", "n_S"]
        print(sub[cols].to_string(index=False))
        return

    if a.drug:
        canon, _ = canonical_drug(a.drug)
        sub = cat[cat["drug"] == canon]
        if a.call:
            sub = sub[sub["call"] == a.call]
        print(f"# {canon} : {len(sub)} assertions"
              + (f" (call={a.call})" if a.call else ""))
        print(sub[["variant", "spdi", "call", "source", "source_grade"]]
              .to_string(index=False))
        return

    if a.strain_spdi and a.drug:
        canon, _ = canonical_drug(a.drug)
        strain = set(Path(a.strain_spdi).read_text().split())
        rset = set(cat[(cat.drug == canon) & (cat.call == "R-associated")
                       & (cat.spdi != "")].spdi)
        hits = strain & rset
        verdict = "R (>=1 marqueur catalogué)" if hits else "non expliqué par le catalogue"
        print(f"{canon} : {verdict}")
        for h in sorted(hits):
            g = cat[cat.spdi == h]["gene"].iloc[0]
            print(f"  {g}\t{h}")
        return

    ap.print_help()


if __name__ == "__main__":
    main()
