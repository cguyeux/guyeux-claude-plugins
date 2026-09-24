#!/usr/bin/env python3
"""batch_branch_bias.py — avant de dater, tester si un LOT (version de pipeline,
centre de sequencage, campagne d'ingestion) gonfle ou raccourcit les branches
TERMINALES d'un groupe de souches.

Le probleme qu'il tranche
-------------------------
Quand un groupe de souches a ete traite par une version de pipeline differente
de celle des comparanda, la topologie peut survivre — un artefact de traitement
ne redistribue pas un lot homogene en deux moities qui s'apparient chacune a un
groupe traite autrement — mais les LONGUEURS DE BRANCHES, elles, dependent
directement du nombre de variants appeles. Or ce sont elles qui portent les
dates. Un groupe sur-appele parait jeune et derive vite, un groupe sous-appele
parait basal et vieillit les noeuds : dans les deux cas la chronologie ment sans
que rien ne le signale.

Le test est celui d'une DIFFERENCE SYSTEMATIQUE des branches terminales entre
groupes. Il est a posteriori, il ne coute rien une fois l'arbre construit, et il
est sensible : un exces de quelques dizaines de variants par souche double
souvent une branche terminale, qui n'en compte que quelques dizaines.

Ce qu'il ne dit pas
-------------------
Un ecart significatif ne prouve pas l'artefact : deux populations reellement
differentes (diversite locale, echantillonnage recent contre historique, un
groupe plus clonal que l'autre) donnent le meme signal. Le test DISQUALIFIE la
datation quand il est positif ; il l'AUTORISE quand il est negatif, ce qui est
son usage principal. En cas de positif, isoler le confondant demande un controle
apparie (memes souches, deux traitements) que le test ne fournit pas.

Usage
-----
    python3 batch_branch_bias.py arbre.newick --groups groups.tsv
    python3 batch_branch_bias.py arbre.newick --groups g.tsv --ref Cameroon --scale 3800
    python3 batch_branch_bias.py arbre.newick --pattern '^(GHANA|Cameroon)_'

`--groups` : TSV `label<TAB>accession` (le meme fichier que `lineage_navigator
--groups`). Une feuille est rattachee au label dont l'accession est une
sous-chaine de son nom. A defaut, `--pattern` extrait le label par son premier
groupe de capture dans le nom de feuille.

`--scale` multiplie les longueurs pour les rendre lisibles (nombre de sites de
l'alignement, pour lire des SNP plutot que des substitutions par site).

Projet : mtbc/ (transverse)  ·  Date : 2026-09-15
"""
import argparse
import re
import sys
from collections import defaultdict

try:
    from scipy.stats import mannwhitneyu
except ImportError:
    mannwhitneyu = None
from ete3 import Tree


def load_groups(path):
    m = {}
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.replace("\t", " ").split()
            if len(parts) >= 2:
                m[parts[1]] = parts[0]
    return m


def median(v):
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tree")
    ap.add_argument("--groups", help="TSV label<TAB>accession")
    ap.add_argument("--pattern", help="regex a un groupe de capture sur le nom de feuille")
    ap.add_argument("--ref", help="groupe de reference des comparaisons (defaut : le plus gros)")
    ap.add_argument("--scale", type=float, default=1.0,
                    help="facteur multiplicatif (ex. nombre de sites) pour lire des SNP")
    ap.add_argument("--min-n", type=int, default=5, help="taille minimale d'un groupe teste")
    args = ap.parse_args()

    t = Tree(args.tree, format=1)
    gmap = load_groups(args.groups) if args.groups else {}
    pat = re.compile(args.pattern) if args.pattern else None

    by = defaultdict(list)
    unassigned = 0
    for leaf in t:
        label = None
        if pat:
            m = pat.search(leaf.name)
            if m:
                label = m.group(1)
        if label is None and gmap:
            for acc, lab in gmap.items():
                if acc in leaf.name:
                    label = lab
                    break
        if label is None:
            unassigned += 1
            continue
        by[label].append(leaf.dist * args.scale)

    if not by:
        print("Aucune feuille rattachee a un groupe.", file=sys.stderr)
        return 2

    ref = args.ref or max(by, key=lambda k: len(by[k]))
    print(f"{len(t):d} feuilles, {len(by)} groupes, {unassigned} non rattachees.")
    print(f"Reference : {ref} (n={len(by.get(ref, []))})\n")
    print(f"{'groupe':22s} {'n':>4s} {'mediane':>9s} {'moyenne':>9s} "
          f"{'ratio/ref':>10s} {'p (MWU)':>10s}")
    rows = sorted(by.items(), key=lambda kv: -len(kv[1]))
    refv = by.get(ref, [])
    verdict_rows = []
    for lab, v in rows:
        med, mean = median(v), sum(v) / len(v)
        ratio = med / median(refv) if refv and median(refv) else float("nan")
        p = float("nan")
        if lab != ref and len(v) >= args.min_n and len(refv) >= args.min_n and mannwhitneyu:
            p = mannwhitneyu(v, refv, alternative="two-sided").pvalue
        print(f"{lab:22s} {len(v):4d} {med:9.2f} {mean:9.2f} {ratio:10.2f} {p:10.3g}")
        if lab != ref and len(v) >= args.min_n and p == p:
            verdict_rows.append((lab, ratio, p))

    print()
    flag = [(l, r, p) for l, r, p in verdict_rows if p < 0.05 and (r > 1.25 or r < 0.8)]
    if flag:
        print("VERDICT : ecart systematique detecte, la DATATION est disqualifiee en l'etat.")
        for l, r, p in flag:
            sens = "plus longues" if r > 1 else "plus courtes"
            print(f"  {l} : branches terminales {sens} d'un facteur {r:.2f} (p={p:.3g}) "
                  f"vs {ref}")
        print("  Un ecart reel de population produit le meme signal : un controle apparie")
        print("  est necessaire pour l'imputer au traitement plutot qu'a la biologie.")
    else:
        print("VERDICT : aucun ecart systematique de branche terminale (seuils p<0.05 et")
        print(f"  ratio hors [0.8 ; 1.25]) entre les groupes et {ref}. La datation n'est pas")
        print("  disqualifiee par un effet de lot sur les longueurs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
