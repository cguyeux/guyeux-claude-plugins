#!/usr/bin/env python3
"""
binary_fitch.py — Score de parcimonie (Fitch) d'un arbre donné sur une matrice binaire, avec
décomposition par sous-ensembles de sites et de tips, pour diagnostiquer d'où vient l'homoplasie
d'un mutation-annotated tree avant de lui faire confiance pour du placement.

Usage :
  binary_fitch.py --tree T.nwk --phy M.phy [--positions M.positions.txt --mask mask.txt ...]
                  [--drop-tips tips.txt] [--per-site out.tsv]

Rend le score total, le plancher tree-like (nombre de sites variables retenus), le ratio, et si
--mask / --drop-tips sont donnés, le score sur chaque combinaison (tous / hors masque / hors tips
/ hors masque et hors tips), toujours sur le MÊME arbre (élagué des tips retirés, sans
ré-inférence). --per-site écrit le nombre de changements par site sur l'arbre complet.

Fitch binaire vectorisé numpy : état d'un nœud = masque 2 bits (1=état 0 possible, 2=état 1
possible) ; intersection si non vide sinon union + 1 changement. Les '?' / '-' / '.' de la
matrice comptent comme 3 (les deux états possibles), donc n'ajoutent jamais de changement.
Écrit pour Bovis_full P10.6 (2026-09-20) ; générique pour toute matrice 0/1 (SPDI, RD, IS).
"""
import argparse, sys
import numpy as np

try:
    from ete3 import Tree
except ImportError:
    sys.exit("ete3 requis")


def read_phy(path):
    names, rows = [], []
    with open(path) as f:
        n, m = map(int, next(f).split())
        for l in f:
            if not l.strip():
                continue
            s, q = l.split()
            names.append(s)
            a = np.frombuffer(q.encode(), dtype=np.uint8)
            st = np.where(a == ord("0"), 1, np.where(a == ord("1"), 2, 3)).astype(np.uint8)
            rows.append(st)
    X = np.vstack(rows)
    assert X.shape == (n, m), f"PHYLIP annonce {n}x{m}, lu {X.shape}"
    return names, X


def read_positions(path):
    out = []
    for l in open(path):
        l = l.strip()
        if not l or l.startswith("#"):
            continue
        out.append(int(l.split(":")[1]) if ":" in l else int(l))
    return out


def fitch(tree, states, idx):
    """states : dict tip -> uint8 array (1/2/3). Retourne (score total, changements par site)."""
    changes = np.zeros(next(iter(states.values())).shape[0], dtype=np.int32)
    node_state = {}
    for node in tree.traverse("postorder"):
        if node.is_leaf():
            node_state[node] = states[idx[node.name]]
            continue
        acc = None
        for ch in node.children:
            s = node_state.pop(ch)
            if acc is None:
                acc = s
                continue
            inter = acc & s
            empty = inter == 0
            acc = np.where(empty, acc | s, inter).astype(np.uint8)
            changes = changes + empty
        node_state[node] = acc
    return int(changes.sum()), changes


def score_subset(tree, X, names, keep_sites, drop_tips):
    t = tree.copy("newick")
    if drop_tips:
        keep = [n for n in names if n not in drop_tips]
        t.prune(keep, preserve_branch_length=False)
    idx = {n: i for i, n in enumerate(names)}
    sub = X[:, keep_sites]
    # sites variables parmi les tips retenus (plancher tree-like = 1 changement chacun)
    tip_rows = np.array([idx[l.name] for l in t.iter_leaves()])
    v = sub[tip_rows]
    variable = ((v == 1).any(0) & (v == 2).any(0)).sum()
    states = {i: sub[i] for i in range(len(names))}
    score, per_site = fitch(t, states, idx)
    return score, int(variable), per_site


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tree", required=True)
    ap.add_argument("--phy", required=True)
    ap.add_argument("--positions", help="positions des colonnes (SPDI ou nues), requis avec --mask")
    ap.add_argument("--mask", action="append", default=[], help="fichier(s) de positions à exclure")
    ap.add_argument("--drop-tips", help="fichier : un tip par ligne à retirer")
    ap.add_argument("--per-site", help="TSV position\\tchangements sur l'arbre complet")
    a = ap.parse_args()

    tree = Tree(a.tree, format=1)
    names, X = read_phy(a.phy)
    leaves = set(l.name for l in tree.iter_leaves())
    missing = [n for n in names if n not in leaves]
    if missing:
        print(f"[fitch] {len(missing)} lignes de la matrice absentes de l'arbre, ignorées", file=sys.stderr)
        keep = [i for i, n in enumerate(names) if n in leaves]
        names = [names[i] for i in keep]; X = X[keep]
    extra = leaves - set(names)
    if extra:
        sys.exit(f"tips de l'arbre absents de la matrice : {list(extra)[:5]}")

    all_sites = np.arange(X.shape[1])
    unmasked = all_sites
    combos = {"tous sites / tous tips": (all_sites, set())}
    if a.mask:
        if not a.positions:
            sys.exit("--mask exige --positions")
        pos = read_positions(a.positions)
        assert len(pos) == X.shape[1], "positions et colonnes ne correspondent pas"
        m = set()
        for f in a.mask:
            m |= set(read_positions(f))
        unmasked = np.array([i for i, p in enumerate(pos) if p not in m])
        combos["hors masque / tous tips"] = (unmasked, set())
    if a.drop_tips:
        drop = set(l.strip() for l in open(a.drop_tips) if l.strip())
        combos["tous sites / hors tips retirés"] = (all_sites, drop)
        if a.mask:
            combos["hors masque / hors tips retirés"] = (unmasked, drop)

    print("combinaison\tsites\tscore\tplancher_sites_variables\tratio")
    per_site_full = None
    for label, (sites, drop) in combos.items():
        score, variable, per_site = score_subset(tree, X, names, sites, drop)
        if label.startswith("tous sites / tous"):
            per_site_full = per_site
        print(f"{label}\t{len(sites)}\t{score}\t{variable}\t{score/max(variable,1):.2f}")
    if a.per_site and per_site_full is not None:
        pos = read_positions(a.positions) if a.positions else list(range(X.shape[1]))
        with open(a.per_site, "w") as f:
            f.write("position\tchanges\n")
            for p, c in zip(pos, per_site_full):
                f.write(f"{p}\t{int(c)}\n")


if __name__ == "__main__":
    main()
