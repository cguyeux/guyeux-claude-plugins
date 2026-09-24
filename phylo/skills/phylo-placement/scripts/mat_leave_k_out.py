#!/usr/bin/env python3
"""
mat_leave_k_out.py — Validation d'un mutation-annotated tree (UShER) par retrait-réinsertion.

Généralise le test manuel leave-2-out de Bovis_full P10.2.c (2026-09-20) à k souches tirées
au hasard, pour mesurer à l'échelle d'un clade réel (centaines à milliers de tips) si le
placement incrémental d'UShER retombe sur la position de l'arbre ML d'origine, et avec
quelle ambiguïté (nombre de placements parcimonieusement équivalents).

Deux phases, parce qu'`usher` tourne en général sur la machine de calcul (mp) alors que
l'élagage et la comparaison d'arbres se font en local avec ete3 :

  prepare   --tree T.nwk --vcf all.vcf --k 20 --out DIR [--seed 42]
            tire k tips, écrit DIR/ref.nwk (arbre élagué, longueurs conservées),
            DIR/ref.vcf (colonnes des tips conservés), DIR/heldout.vcf (colonnes des k tips),
            DIR/heldout.txt (liste). Puis, sur la machine à usher :
              usher --tree ref.nwk --vcf ref.vcf --save-mutation-annotated-tree ref.pb -d u_ref
              usher --load-mutation-annotated-tree ref.pb --vcf heldout.vcf \\
                    --save-mutation-annotated-tree placed.pb -d u_placed 2>&1 | tee placed.log
            (le fichier u_placed/final-tree.nh est l'arbre replacé.)

  evaluate  --tree T.nwk --placed u_placed/final-tree.nh --heldout heldout.txt [--log placed.log]
            pour chaque tip retiré : (a) la feuille-sœur ou le groupe-sœur (leaf set du sous-arbre
            frère, hors autres tips retirés) est-il identique entre l'arbre d'origine et l'arbre
            replacé ? (b) l'ensemble des plus proches voisins (distance patristique minimale,
            hors tips retirés) est-il identique ? (c) DÉPLACEMENT : distance patristique, dans
            l'arbre d'origine, entre la branche d'attache d'origine et celle impliquée par le
            placement (en SNP avec --sites <longueur de l'alignement ML>), et « même polytomie »
            si ce chemin ne traverse que des branches quasi nulles (--eps, 0,5 SNP par défaut) ;
            (d) si --log : score de parcimonie et nombre de placements optimaux rapportés par
            usher ; (e) si --clades-true/--clades-placed : le CLADE NOMMÉ assigné par placement
            est-il identique au clade vrai (registre de nomenclature, ex. bdd/actuelle) ? C'est le
            seul critère qui réponde à la question de P10 (Bovis_full P10.6.d, 2026-09-21) — « peut-
            on classer sans refaire RAxML » — sur un sous-arbre couvrant PLUSIEURS clades nommés ;
            (a)-(c) mesurent la reproductibilité du bruit dans un clone quand le sous-arbre testé
            est un clade terminal dense (P10.6.b), pas l'exactitude taxonomique. Workflow : annoter
            le MAT de référence AVANT placement (`matUtils annotate -i ref.pb -c clades-true.tsv
            -o ref_annotated.pb`), placer les retirés dessus, puis lire le MAT placé
            (`matUtils summary -i placed.pb -C clades-placed.tsv`). Sortie TSV sur stdout + résumé
            stderr.

Stdlib + ete3. Aucune dépendance à la base : ne lit que Newick, VCF et le log usher.

Piège connu : dans une expansion clonale dense, beaucoup de tips sont à distance 0 les uns
des autres et RAxML rend des branches de longueur nulle — la « feuille sœur » est alors un
choix arbitraire de l'arbre binaire. Le critère (b), plus proches voisins, est celui qui
compte dans ce régime ; (a) est le critère strict qui valait pour P10.2.c (15 souches).
"""
import argparse, os, random, re, sys

try:
    from ete3 import Tree
except ImportError:  # message clair plutôt qu'une trace
    sys.exit("ete3 requis (pip install ete3) — élagage et comparaison d'arbres")


# ----------------------------------------------------------------------------- VCF utils
def read_vcf(path):
    header, cols, rows = [], None, []
    with open(path) as f:
        for line in f:
            if line.startswith("##"):
                header.append(line)
            elif line.startswith("#CHROM"):
                cols = line.rstrip("\n").split("\t")
            else:
                rows.append(line.rstrip("\n").split("\t"))
    if cols is None:
        sys.exit(f"VCF sans ligne #CHROM : {path}")
    return header, cols, rows


def write_vcf_subset(path, header, cols, rows, keep_samples):
    fixed = cols[:9]
    idx = [i for i, c in enumerate(cols) if i >= 9 and c in keep_samples]
    with open(path, "w") as f:
        f.writelines(header)
        f.write("\t".join(fixed + [cols[i] for i in idx]) + "\n")
        n_kept = 0
        for r in rows:
            gts = [r[i] for i in idx]
            # une ligne où plus aucun échantillon retenu ne porte l'allèle alternatif est inutile
            # au MAT de référence, mais elle reste NÉCESSAIRE au VCF des retirés (usher exige que
            # les positions des retirés existent) — on garde donc toutes les lignes, sans filtrer.
            f.write("\t".join(r[:9] + gts) + "\n")
            n_kept += 1
    return n_kept


# ----------------------------------------------------------------------------- tree utils
def leaf_names(t):
    return [l.name for l in t.iter_leaves()]


def sister_set(tree, name, exclude):
    """Leaf set du sous-arbre frère du tip `name` (hors `exclude`). Si le frère immédiat ne
    contient que des exclus, remonte jusqu'à trouver un frère non vide."""
    node = tree & name
    while node.up is not None:
        sibs = set()
        for s in node.up.children:
            if s is node:
                continue
            sibs |= {l.name for l in s.iter_leaves()}
        sibs -= exclude
        if sibs:
            return frozenset(sibs)
        node = node.up
    return frozenset()


def nearest_set(tree, name, exclude, tol=1e-9):
    """Ensemble des feuilles à distance patristique minimale de `name` (hors exclus)."""
    node = tree & name
    best, best_set = None, set()
    for l in tree.iter_leaves():
        if l.name == name or l.name in exclude:
            continue
        d = tree.get_distance(node, l)
        if best is None or d < best - tol:
            best, best_set = d, {l.name}
        elif abs(d - best) <= tol:
            best_set.add(l.name)
    return best, frozenset(best_set)


# ----------------------------------------------------------------------------- prepare
def cmd_prepare(a):
    os.makedirs(a.out, exist_ok=True)
    t = Tree(a.tree, format=1)
    leaves = leaf_names(t)
    header, cols, rows = read_vcf(a.vcf)
    samples = set(cols[9:])
    common = [l for l in leaves if l in samples]
    if len(common) < len(leaves):
        print(f"[prepare] {len(leaves)-len(common)} tips de l'arbre absents du VCF (ignorés du tirage)",
              file=sys.stderr)
    rng = random.Random(a.seed)
    held = sorted(rng.sample(common, a.k))
    held_set = set(held)
    keep = [l for l in leaves if l not in held_set]
    t.prune(keep, preserve_branch_length=True)
    t.write(outfile=os.path.join(a.out, "ref.nwk"), format=1)
    write_vcf_subset(os.path.join(a.out, "ref.vcf"), header, cols, rows, set(keep))
    write_vcf_subset(os.path.join(a.out, "heldout.vcf"), header, cols, rows, held_set)
    with open(os.path.join(a.out, "heldout.txt"), "w") as f:
        f.write("\n".join(held) + "\n")
    print(f"[prepare] {len(leaves)} tips, {a.k} retirés (seed {a.seed}), arbre élagué à "
          f"{len(keep)} tips → {a.out}/{{ref.nwk,ref.vcf,heldout.vcf,heldout.txt}}", file=sys.stderr)


# ----------------------------------------------------------------------------- evaluate
USHER_RE = re.compile(r"Sample name:\s*(\S+)\s*Parsimony score:\s*(\d+)\s*Number of parsimony-optimal placements:\s*(\d+)")


def parse_usher_log(path):
    stats = {}
    if not path or not os.path.exists(path):
        return stats
    txt = open(path, errors="replace").read()
    for m in USHER_RE.finditer(txt):
        stats[m.group(1)] = (int(m.group(2)), int(m.group(3)))
    return stats


def attach_branch_root(tree, leaf_set):
    """Racine, dans `tree`, du sous-arbre frère désigné par `leaf_set` : la branche d'attache
    implicite d'un placement est la branche qui porte ce nœud."""
    leaves = [tree & n for n in leaf_set]
    return leaves[0] if len(leaves) == 1 else tree.get_common_ancestor(leaves)


def displacement(tree, s_o, s_p, eps_bl):
    """Distance patristique dans l'arbre d'ORIGINE entre la racine du frère d'origine et celle
    du frère replacé, et nombre de branches non quasi nulles (> eps_bl) sur ce chemin. 0 branche
    non nulle = même polytomie : le placement est indiscernable de l'origine au sens de l'arbre
    ML lui-même, même si la feuille sœur nominale diffère."""
    if not s_o or not s_p:
        return float("nan"), -1
    a, b = attach_branch_root(tree, s_o), attach_branch_root(tree, s_p)
    if a is b:
        return 0.0, 0
    anc = tree.get_common_ancestor(a, b)
    d, n_long = 0.0, 0
    for x in (a, b):
        while x is not anc:
            d += x.dist
            n_long += x.dist > eps_bl
            x = x.up
    return d, n_long


def read_resolved_clades(path):
    """Lit un log `matUtils annotate` (stdout/stderr) et rend l'ensemble des clades pour
    lesquels une ligne "Assigning <clade> to node <n>" a été émise — c'est-à-dire les clades
    que l'algorithme a réussi à rattacher à UN nœud du MAT (au moins --set-overlap, 0.6 par
    défaut, de leurs souches de référence en descendent).

    Piège vérifié empiriquement (Bovis_full P10.6.d, 2026-09-21, arbre réutilisé de juin sur
    une nomenclature de septembre) : un clade nommé peut être ABSENT de ces lignes — aucun
    nœud, même à 60 % de recouvrement, ne le rassemble dans CETTE topologie — sans qu'aucune
    erreur ne soit levée ; matUtils passe silencieusement au clade suivant. Une souche retirée
    dont le vrai clade n'a jamais été assigné n'a, par construction, AUCUNE étiquette correcte
    à retrouver : compter son placement comme un échec du MAT confondrait un défaut de la
    TOPOLOGIE RÉUTILISÉE (ou une nomenclature qui a bougé depuis sa construction — le "piège de
    la date" du skill `phylo-forest`) avec un défaut du PLACEMENT lui-même. Sur ce cas réel :
    10/59 clades jamais assignés, concentrant 10 des 11 échecs bruts (72,5 % de succès brut,
    96,7 % une fois restreint aux clades réellement résolubles dans l'arbre)."""
    resolved = set()
    if not path or not os.path.exists(path):
        return resolved
    for line in open(path, errors="replace"):
        if line.startswith("Assigning "):
            parts = line.split()
            if len(parts) >= 2:
                resolved.add(parts[1])
    return resolved


def read_clade_tsv(path):
    """Lit un tsv sample<TAB>clade. Tolère l'en-tête produit par `matUtils summary -C`
    (première ligne "sample\\tclade" ou similaire) : une ligne dont le 1er champ ne
    correspond à aucun nom d'échantillon plausible n'est de toute façon jamais consultée
    par construction (on ne cherche que les noms passés par l'appelant), donc pas besoin
    de la détecter explicitement. Ne garde que la DERNIÈRE colonne comme clade : si le MAT
    porte plusieurs systèmes d'annotation simultanés, matUtils ajoute une colonne par
    système et le système d'intérêt est celui posé en dernier par `annotate -c`."""
    out = {}
    with open(path) as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            out[parts[0]] = parts[-1]
    return out


def cmd_evaluate(a):
    orig = Tree(a.tree, format=1)
    placed = Tree(a.placed, format=1)
    held = [l.strip() for l in open(a.heldout) if l.strip()]
    held_set = set(held)
    placed_leaves = set(leaf_names(placed))
    missing = [h for h in held if h not in placed_leaves]
    if missing:
        print(f"[evaluate] {len(missing)} tips retirés absents de l'arbre replacé : {missing[:5]}…",
              file=sys.stderr)
    stats = parse_usher_log(a.log)
    scale = a.sites if a.sites else 1.0
    eps_bl = a.eps / scale

    clade_check = bool(a.clades_true and a.clades_placed)
    clades_true = read_clade_tsv(a.clades_true) if clade_check else {}
    clades_placed = read_clade_tsv(a.clades_placed) if clade_check else {}
    resolved_clades = read_resolved_clades(a.annotate_log) if clade_check else set()
    if clade_check:
        absent = [h for h in held if h not in clades_true]
        if absent:
            print(f"[evaluate] {len(absent)} tips retirés sans clade vrai connu (--clades-true) : "
                  f"{absent[:5]}…", file=sys.stderr)
        if not a.annotate_log:
            print("[evaluate] --annotate-log absent : impossible de distinguer un vrai échec de "
                  "placement d'un clade jamais résolu dans ce MAT (cf. docstring de "
                  "read_resolved_clades) — le taux ci-dessous mélange les deux.", file=sys.stderr)

    cols = ["sample", "sister_match", "nn_match", "same_polytomy", "displacement",
            "n_long_branches", "sister_orig_n", "sister_placed_n",
            "nn_dist_orig", "nn_dist_placed", "nn_orig_n", "nn_placed_n",
            "parsimony_score", "n_optimal_placements"]
    if clade_check:
        cols += ["clade_true", "clade_placed", "clade_resolvable", "clade_match"]
    print("\t".join(cols))
    n_s = n_n = n_uniq = n_poly = n_clade = n_clade_k = n_unresolved = 0
    disps = []
    for h in held:
        if h in missing:
            continue
        s_o = sister_set(orig, h, held_set)
        s_p = sister_set(placed, h, held_set)
        d_o, n_o = nearest_set(orig, h, held_set)
        d_p, n_p = nearest_set(placed, h, held_set)
        sm, nm = (s_o == s_p), (n_o == n_p)
        dsp, n_long = displacement(orig, s_o, s_p, eps_bl)
        dsp *= scale
        poly = n_long == 0
        n_s += sm; n_n += nm; n_poly += poly
        if dsp == dsp:
            disps.append(dsp)
        ps, nopt = stats.get(h, ("", ""))
        if nopt == 1:
            n_uniq += 1
        row = [h, int(sm), int(nm), int(poly), f"{dsp:.3g}", n_long,
               len(s_o), len(s_p), f"{d_o:.6g}", f"{d_p:.6g}", len(n_o), len(n_p), ps, nopt]
        if clade_check:
            c_t, c_p = clades_true.get(h, ""), clades_placed.get(h, "")
            resolvable = (not a.annotate_log) or (c_t in resolved_clades)
            cm = bool(c_t) and (c_t == c_p)
            if c_t and resolvable:
                n_clade_k += 1
                n_clade += cm
            elif c_t:
                n_unresolved += 1
            row += [c_t, c_p, int(resolvable), int(cm)]
        print("\t".join(map(str, row)))
    k = len(held) - len(missing)
    disps.sort()
    med = disps[len(disps) // 2] if disps else float("nan")
    unit = "SNP" if a.sites else "u. de branche"
    print(f"[evaluate] k={k} : frère identique {n_s}/{k} ; plus proches voisins identiques {n_n}/{k}"
          f" ; même polytomie (eps {a.eps:g} {unit}) {n_poly}/{k}"
          f" ; déplacement médian {med:.3g} {unit}, max {max(disps) if disps else float('nan'):.3g}"
          + (f" ; placement unique {n_uniq}/{k}" if stats else " ; (pas de log usher : ambiguïté non mesurée)")
          + (f" ; clade nommé identique {n_clade}/{n_clade_k}"
             + (f" ({n_unresolved} exclus, vrai clade jamais résolu dans ce MAT)" if n_unresolved else "")
             if clade_check else ""),
          file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--tree", required=True); p.add_argument("--vcf", required=True)
    p.add_argument("--k", type=int, default=20); p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_prepare)
    e = sub.add_parser("evaluate")
    e.add_argument("--tree", required=True, help="arbre ML d'origine (tous les tips)")
    e.add_argument("--placed", required=True, help="final-tree.nh produit par usher après placement")
    e.add_argument("--heldout", required=True); e.add_argument("--log", default=None)
    e.add_argument("--sites", type=float, default=None,
                   help="longueur de l'alignement ML : convertit les longueurs de branche en SNP")
    e.add_argument("--eps", type=float, default=0.5,
                   help="branche considérée nulle en deçà (en SNP si --sites, sinon en u. de branche)")
    e.add_argument("--clades-true", default=None,
                   help="tsv sample<TAB>clade (vérité terrain, ex. scan bdd/actuelle) : active le "
                        "critère « clade nommé identique », le seul qui réponde à la question de "
                        "P10 (« classer sans refaire RAxML ») plutôt qu'à la reproductibilité du "
                        "bruit dans un clone (frère/plus proche voisin)")
    e.add_argument("--clades-placed", default=None,
                   help="tsv produit par `matUtils summary -i placed.pb -C <fichier>` sur le MAT "
                        "après placement des retirés (annoté au préalable via "
                        "`matUtils annotate -c <clades-true> -o ref_annotated.pb` avant le "
                        "placement usher) ; requiert --clades-true")
    e.add_argument("--annotate-log", default=None,
                   help="stdout/stderr capturé de `matUtils annotate` (voir --clades-true) : "
                        "exclut du critère « clade nommé identique » les souches dont le vrai "
                        "clade n'a jamais été assigné à un nœud dans CE MAT (topologie réutilisée "
                        "trop ancienne pour cette nomenclature, ou clade non monophylétique) — "
                        "sans ce log, un clade non résoluble compte à tort comme un échec de "
                        "placement (cf. docstring de read_resolved_clades)")
    e.set_defaults(fn=cmd_evaluate)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
