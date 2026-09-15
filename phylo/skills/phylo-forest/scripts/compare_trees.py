#!/usr/bin/env python3
"""
Objet    : comparer deux arbres RAxML-NG (avec supports bootstrap) inferes sur le meme jeu de
           taxons, l'un avec toutes les positions, l'autre avec les positions PE/PPE masquees,
           et dire non seulement COMBIEN de bipartitions different mais si celles qui bougent
           sont SOUTENUES (un desaccord entre deux noeuds a 40 % de bootstrap n'est pas un
           desaccord, c'est du bruit dans les deux arbres).
Entrees  : deux fichiers Newick .raxml.support (meme ensemble de feuilles).
Sorties  : stdout — RF brute et normalisee, bipartitions propres a chaque arbre avec leur
           support, et le decompte de celles qui sont soutenues (>= seuil).
Reutilisable : oui, tout couple d'arbres sur le meme jeu de taxons (effet d'un masque, d'un
           modele, d'un outil). Parametre --seuil.
Projet   : mtbc / P72.4 (effet du masque PE/PPE de TB-Annotator sur la topologie)
Date     : 2026-09-10
"""
import sys, argparse
from ete3 import Tree

def bipartitions(t, leaves):
    """Ensemble des bipartitions non triviales, chacune normalisee par le cote ne contenant
    pas un taxon de reference fixe, avec le support du noeud qui la porte."""
    ref = min(leaves)
    out = {}
    for node in t.traverse("postorder"):
        if node.is_leaf() or node.is_root():
            continue
        side = frozenset(node.get_leaf_names())
        if len(side) < 2 or len(side) > len(leaves) - 2:
            continue
        key = side if ref not in side else frozenset(leaves - side)
        out[key] = node.support
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tree_a"); ap.add_argument("tree_b")
    ap.add_argument("--nom-a", default="A"); ap.add_argument("--nom-b", default="B")
    ap.add_argument("--seuil", type=float, default=70.0,
                    help="support bootstrap au-dela duquel une bipartition compte comme soutenue")
    a = ap.parse_args()

    ta = Tree(a.tree_a); tb = Tree(a.tree_b)
    la = set(ta.get_leaf_names()); lb = set(tb.get_leaf_names())
    if la != lb:
        sys.exit(f"jeux de feuilles differents : {len(la)} vs {len(lb)}, "
                 f"{len(la ^ lb)} en difference symetrique")
    ta.unroot(); tb.unroot()
    ba = bipartitions(ta, la); bb = bipartitions(tb, lb)

    only_a = set(ba) - set(bb); only_b = set(bb) - set(ba); common = set(ba) & set(bb)
    rf = len(only_a) + len(only_b)
    denom = len(ba) + len(bb)
    print(f"taxons : {len(la)}")
    print(f"bipartitions internes : {a.nom_a} {len(ba)}, {a.nom_b} {len(bb)}, communes {len(common)}")
    print(f"Robinson-Foulds : {rf} / {denom} = {100*rf/denom:.2f} % (normalisee)")
    print()
    sa = [ba[k] for k in only_a]; sb = [bb[k] for k in only_b]
    fa = [s for s in sa if s >= a.seuil]; fb = [s for s in sb if s >= a.seuil]
    print(f"bipartitions propres a {a.nom_a} : {len(only_a)}, dont {len(fa)} soutenues (>= {a.seuil:g} %)")
    if sa: print(f"   supports : min {min(sa):.0f}, median {sorted(sa)[len(sa)//2]:.0f}, max {max(sa):.0f}")
    print(f"bipartitions propres a {a.nom_b} : {len(only_b)}, dont {len(fb)} soutenues (>= {a.seuil:g} %)")
    if sb: print(f"   supports : min {min(sb):.0f}, median {sorted(sb)[len(sb)//2]:.0f}, max {max(sb):.0f}")
    print()
    sc_a = [ba[k] for k in common]; sc_b = [bb[k] for k in common]
    if common:
        print(f"sur les {len(common)} bipartitions COMMUNES, support median "
              f"{sorted(sc_a)[len(sc_a)//2]:.0f} % ({a.nom_a}) vs "
              f"{sorted(sc_b)[len(sc_b)//2]:.0f} % ({a.nom_b})")
        gain = sum(1 for k in common if bb[k] > ba[k]); perte = sum(1 for k in common if bb[k] < ba[k])
        print(f"   support en hausse chez {a.nom_b} : {gain} ; en baisse : {perte} ; "
              f"inchange : {len(common)-gain-perte}")
    print()
    if fa or fb:
        print(f"VERDICT : {len(fa)+len(fb)} bipartition(s) SOUTENUE(S) en desaccord — "
              f"le masque change une conclusion, pas seulement du bruit.")
    elif rf:
        print("VERDICT : les bipartitions en desaccord sont toutes faiblement soutenues — "
              "le masque deplace du bruit, pas des noeuds sur lesquels on conclurait.")
    else:
        print("VERDICT : topologies identiques.")

if __name__ == "__main__":
    main()
