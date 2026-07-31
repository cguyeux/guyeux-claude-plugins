#!/usr/bin/env python3
"""Explication mécanistique d'une mutation de résistance — partie locale (dossier).

Pour un variant (HGVS `gene_p.X` ou SPDI), rassemble les éléments locaux d'explication :
  - identité : SPDI, variant, gène, codon, changement d'acide aminé ;
  - verdict CATALOGUE (resistance-catalogue) : par médicament, grade WHO/tb-profiler, source, n_R/n_S ;
  - ASSOCIATION EMPIRIQUE observée dans le dataset du projet : portage et taux R/S par
    médicament parmi les souches porteuses (odds-ratio brut) — preuve directe ;
  - et imprime les commandes pour compléter par la littérature (tbmonitor-papers),
    l'impact protéique (mtbc-mutation-impact, LLR Meier), et la structure 3D (esm-atlas-cli).

Hiérarchie de preuve (à respecter dans la synthèse) : catalogue + littérature + association
empirique = preuve forte ; LLR ESM = appui calibré ; SAE deltas / 3D = contexte mécanistique
exploratoire (ne PAS sur-interpréter, cf. garde-fou mtbc-mutation-impact).

Usage : explain_mutation.py --variant rpoB_p.Ser450Leu [--spdi NC_000962.3:...]
"""
import argparse
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import paths

MODELDIR = paths.RESULTATS / "model"


def annotate(spdi):
    """(gene, codon, aa_pos, base_in_codon) pour un SPDI ponctuel via les CDS H37Rv."""
    txt = (paths.FASTAS / "NC_000962.3_CDS.fasta").read_text()
    p0 = int(spdi.split(":")[1]); p1 = p0 + 1
    for line in txt.splitlines():
        if not line.startswith(">"):
            continue
        loc = re.search(r"\[location=([^\]]+)\]", line)
        if not loc:
            continue
        nums = re.findall(r"\d+", loc.group(1))
        if not nums:
            continue
        deb, fin = int(nums[0]), int(nums[-1])
        if deb <= p1 <= fin:
            g = re.search(r"\[gene=([^\]]+)\]", line)
            rev = "complement" in loc.group(1)
            off = (fin - p1) if rev else (p1 - deb)
            return (g.group(1) if g else "?", off // 3 + 1, off % 3 + 1)
    return ("intergenic", None, None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant"); ap.add_argument("--spdi")
    a = ap.parse_args()
    cat = pd.read_csv(paths.CATALOGUE_TSV, sep="\t").fillna("")

    spdi = a.spdi
    if not spdi and a.variant:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from hgvs_to_spdi import resolve
        spdi = resolve(a.variant)
    if not spdi:
        # retrouver le spdi depuis le catalogue par variant
        m = cat[cat.variant == a.variant]
        spdi = m.spdi.iloc[0] if len(m) and m.spdi.iloc[0] else None
    print(f"# Explication mécanistique : {a.variant or ''}  {spdi or '(SPDI non résolu)'}\n")

    if spdi:
        gene, codon, basep = annotate(spdi)
        print(f"Localisation : gène {gene}" + (f", codon {codon} (base {basep})" if codon else ""))

    # 1. CATALOGUE
    sub = cat[(cat.spdi == spdi) | (cat.variant == a.variant)] if spdi else cat[cat.variant == a.variant]
    print("\n## Verdict catalogue")
    if len(sub):
        print(sub[["drug", "call", "source", "source_grade", "n_R", "n_S"]]
              .drop_duplicates().to_string(index=False))
    else:
        print("  absent du catalogue → candidat hors-catalogue")

    # 2. ASSOCIATION EMPIRIQUE (dataset projet)
    print("\n## Association empirique observée (souches du projet)")
    if spdi and (MODELDIR / "X.npz").exists():
        feats = (MODELDIR / "features.txt").read_text().splitlines()
        fidx = {s: j for j, s in enumerate(feats)}
        if spdi in fidx:
            X = sparse.load_npz(MODELDIR / "X.npz").tocsc()
            rows = pd.read_csv(MODELDIR / "rows.tsv", sep="\t", keep_default_na=False)
            carr = np.asarray(X[:, fidx[spdi]].todense()).ravel() > 0
            print(f"  porté par {int(carr.sum())} souches du dataset")
            drugcols = [c for c in rows.columns if c not in
                        ("strain_id", "lineage_level_1", "lineage_code")]
            for d in drugcols:
                ph = rows[d]
                cr = ph[carr & ph.isin(["R", "S"])]
                if len(cr) >= 10:
                    nr = (cr == "R").sum(); pct = 100 * nr / len(cr)
                    if pct >= 20:
                        print(f"    {d:14s}: {nr}/{len(cr)} R parmi porteurs ({pct:.0f}%)")
        else:
            print("  SPDI absent de la matrice de features (rare ou indel non retenu)")
    else:
        print("  (matrice indisponible)")

    # 3. hooks
    g = (annotate(spdi)[0] if spdi else None) or (a.variant or "").split("_")[0]
    mut = (a.variant or "").split("_p.")[-1] if "_p." in (a.variant or "") else ""
    print("\n## Compléter l'explication (skills à enchaîner)")
    print(f"  littérature : tbmonitor-papers  (chercher '{g}' + nom du médicament dans titre/abstract)")
    if g and mut:
        print(f"  impact protéique (LLR Meier) : /mtbc-mutation-impact {g} {mut}")
    print(f"  fonction du gène : /mtbc-gene-function {g}")
    print(f"  structure 3D : esm-atlas-cli (ESMFold de {g}, position du résidu)")
    print("\nSynthèse à rédiger : hiérarchiser catalogue + littérature + association empirique "
          "(preuve forte), LLR ESM (appui calibré), 3D/SAE (contexte exploratoire).")


if __name__ == "__main__":
    main()
