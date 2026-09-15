#!/usr/bin/env python3
"""
Objet    : mesurer l'homoplasie site par site (parcimonie de Fitch) sur un arbre donne, et
           comparer deux categories de positions. Tranche entre « signal phylogenetique reel »
           et « signal structure mais incompatible avec l'arbre » (artefact de mapping), ce
           qu'un simple comptage de sites informatifs ne peut pas faire.
Entrees  : arbre Newick, alignement PHYLIP binaire (0/1/?), liste de positions d'une categorie.
Sorties  : stdout — pas de Fitch et indice de coherence par categorie, test de Mann-Whitney.
Reutilisable : oui, toute comparaison de deux jeux de marqueurs sur un meme arbre.
Projet   : mtbc / P72.4
Date     : 2026-09-10
Note     : l'arbre doit avoir ete construit SUR LES DEUX categories, sans quoi la categorie
           ayant servi a l'inference est avantagee et la comparaison ne veut rien dire.
"""
import sys
from ete3 import Tree

def fitch(tree, states):
    """petite parcimonie binaire ; states: dict feuille -> '0'/'1'/'?' ; rend le nb de pas"""
    steps = 0
    sets = {}
    for node in tree.traverse("postorder"):
        if node.is_leaf():
            c = states.get(node.name, '?')
            sets[node] = {'0','1'} if c == '?' else {c}
        else:
            ch = [sets[k] for k in node.children]
            inter = set.intersection(*ch)
            if inter:
                sets[node] = inter
            else:
                sets[node] = set.union(*ch)
                steps += 1
    return steps

def main():
    tree_f, phy_f, pos_f, cat_f = sys.argv[1:5]
    t = Tree(tree_f)
    lines = [l.rstrip("\n") for l in open(phy_f) if l.strip()]
    n, L = map(int, lines[0].split())
    names, seqs = [], []
    for l in lines[1:1+n]:
        p = l.split(); names.append(p[0]); seqs.append(p[1])
    pos = [l.split(":")[1] for l in open(pos_f) if l.strip()]
    cat = set(l.strip() for l in open(cat_f) if l.strip())

    res = {'cat': [], 'autre': []}
    for i in range(L):
        col = {names[j]: seqs[j][i] for j in range(n)}
        obs = {c for c in col.values() if c != '?'}
        if len(obs) < 2:
            continue                      # site invariant : pas d'homoplasie definissable
        s = fitch(t, col)
        (res['cat'] if pos[i] in cat else res['autre']).append(s)

    for k, v in res.items():
        if not v: continue
        v_sorted = sorted(v)
        mean = sum(v)/len(v)
        ci = sum(1.0/s for s in v)/len(v)   # indice de coherence moyen (min 1 pas par site)
        homo = sum(1 for s in v if s > 1)
        lab = "PE/PPE" if k == 'cat' else "hors masque"
        print(f"{lab:14s} n={len(v):5d} | pas de Fitch : moyenne {mean:.3f}, mediane {v_sorted[len(v)//2]} | "
              f"CI moyen {ci:.3f} | sites homoplasiques (>1 pas) {homo:5d} ({100*homo/len(v):.1f} %)")
    try:
        from scipy.stats import mannwhitneyu, fisher_exact
        u, p = mannwhitneyu(res['cat'], res['autre'], alternative='greater')
        print(f"\nMann-Whitney (PE/PPE ont-ils PLUS de pas ?) : U={u:.0f}, p={p:.3g}")
        hc = sum(1 for s in res['cat'] if s > 1); ha = sum(1 for s in res['autre'] if s > 1)
        odds, pf = fisher_exact([[hc, len(res['cat'])-hc], [ha, len(res['autre'])-ha]])
        print(f"Fisher sur la PROPORTION de sites homoplasiques : OR={odds:.2f}, p={pf:.3g}")
    except ImportError:
        print("scipy absent")

if __name__ == "__main__":
    main()
