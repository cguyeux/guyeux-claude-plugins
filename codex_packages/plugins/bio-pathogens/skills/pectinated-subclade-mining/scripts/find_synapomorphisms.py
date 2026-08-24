#!/usr/bin/env python3
"""
find_synapomorphisms.py — extraction des SPDI synapomorphiques d'un sous-clade
candidat avec filtre PER-POOL strict.

Usage :
    python3 find_synapomorphisms.py \
        --candidates /tmp/cand_X.txt \
        --candidate-current-dir Bovis1.2.2 \
        --bdd /home/christophe/docs/codes/mtbc/bdd/actuelle \
        --exclude-clades "Bovis1.1,Bovis1.2.1.BCG,Bovis2.s2.1" \
        --exclude-sample-size 12 \
        --t-in 0.95 \
        --t-out 0.05 \
        --out /tmp/synapo_X.txt

Le candidat est une liste de SRA (un par ligne) actuellement dans le repertoire
--candidate-current-dir. Le script charge leurs SPDI directement depuis les
fichiers `<bdd>/<current_dir>/<SRA>/NC_000962.3/spdi.txt`.

Les sous-clades a exclure sont passes via --exclude-clades (CSV). Pour chacun
un echantillon aleatoire de N souches est charge (defaut 12).

Filtre PER-POOL : un SPDI candidat doit etre present a >= t_in dans le candidat
ET a <= t_out dans CHAQUE pool exclude (jamais global).

Sortie : un SPDI par ligne dans --out.
"""
import argparse
import os
import random
import sys
from collections import Counter


def load_spdi(bdd, clade_dir, sra):
    fp = os.path.join(bdd, clade_dir, sra, 'NC_000962.3', 'spdi.txt')
    try:
        with open(fp) as f:
            return set(l.strip() for l in f if l.strip())
    except FileNotFoundError:
        return None


def sample_pool(bdd, clade_dir, n, seed=42):
    d = os.path.join(bdd, clade_dir)
    if not os.path.isdir(d):
        return []
    random.seed(seed)
    sras = [s for s in os.listdir(d) if os.path.isdir(os.path.join(d, s))]
    pick = random.sample(sras, min(n, len(sras)))
    pool = []
    for s in pick:
        sp = load_spdi(bdd, clade_dir, s)
        if sp and len(sp) > 100:
            pool.append(sp)
    return pool


def find_synapomorphisms(target_sets, exclude_pools_dict, t_in, t_out):
    """Filtre PER-POOL : chaque pool individuellement <t_out."""
    cnt = Counter()
    for sp in target_sets.values():
        cnt.update(sp)
    core = {sp for sp, n in cnt.items() if n >= t_in * len(target_sets)}
    final = set()
    diagnostics = {pname: [] for pname in exclude_pools_dict}
    for sp in core:
        valid = True
        for pname, pool in exclude_pools_dict.items():
            if not pool:
                continue
            present = sum(1 for ref in pool if sp in ref)
            frac = present / len(pool) if pool else 0
            if frac > t_out:
                valid = False
                diagnostics[pname].append((sp, frac))
                break
        if valid:
            final.add(sp)
    return final, diagnostics, len(core)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--candidates', required=True, help='Fichier SRA candidats (un par ligne)')
    p.add_argument('--candidate-current-dir', required=True,
                   help='Repertoire actuel des candidats (relatif a --bdd)')
    p.add_argument('--bdd', required=True, help='Racine bdd/actuelle/')
    p.add_argument('--exclude-clades', required=True,
                   help='Liste CSV des clades a exclure (chacun en pool separe)')
    p.add_argument('--exclude-sample-size', type=int, default=12,
                   help='Echantillon par clade exclu (defaut 12)')
    p.add_argument('--t-in', type=float, default=0.95,
                   help='Seuil de presence dans le candidat (defaut 0.95)')
    p.add_argument('--t-out', type=float, default=0.05,
                   help='Seuil de presence dans chaque pool exclu (defaut 0.05)')
    p.add_argument('--out', required=True, help='Fichier sortie markers')
    p.add_argument('--seed', type=int, default=42)
    args = p.parse_args()

    # Charger candidats
    with open(args.candidates) as f:
        cand_sras = [l.strip() for l in f if l.strip()]
    cand_sets = {}
    for s in cand_sras:
        sp = load_spdi(args.bdd, args.candidate_current_dir, s)
        if sp and len(sp) > 100:
            cand_sets[s] = sp
    print(f'Candidates loaded: {len(cand_sets)}/{len(cand_sras)} from {args.candidate_current_dir}',
          file=sys.stderr)

    if len(cand_sets) < 2:
        print('Pas assez de candidats avec SPDI valides', file=sys.stderr)
        sys.exit(1)

    # Charger pools d'exclusion
    exclude_pools = {}
    for c in args.exclude_clades.split(','):
        c = c.strip()
        if not c:
            continue
        pool = sample_pool(args.bdd, c, args.exclude_sample_size, args.seed)
        exclude_pools[c] = pool
        print(f'Exclude pool {c}: {len(pool)}', file=sys.stderr)

    # Ajouter aussi le reste du clade parent (les souches non-candidates)
    rest_pool = []
    d = os.path.join(args.bdd, args.candidate_current_dir)
    cand_set = set(cand_sras)
    for s in os.listdir(d):
        if s in cand_set:
            continue
        sp = load_spdi(args.bdd, args.candidate_current_dir, s)
        if sp and len(sp) > 100:
            rest_pool.append(sp)
    if rest_pool:
        exclude_pools[f'_rest_{args.candidate_current_dir}'] = rest_pool
        print(f'Rest of {args.candidate_current_dir}: {len(rest_pool)}', file=sys.stderr)

    # Find synapo
    syn, diag, n_core = find_synapomorphisms(cand_sets, exclude_pools, args.t_in, args.t_out)
    print(f'\nCore (>={args.t_in*100:.0f}% in candidates): {n_core}', file=sys.stderr)
    print(f'Synapomorphisms (per-pool filter <={args.t_out*100:.0f}%): {len(syn)}', file=sys.stderr)

    # Top rejection reasons
    if any(diag.values()):
        print('\nMarkers rejetes par pool :', file=sys.stderr)
        for pname, rejects in diag.items():
            if rejects:
                print(f'  {pname}: {len(rejects)} markers (max frac dans le pool: {max(r[1] for r in rejects):.2f})', file=sys.stderr)

    # Save
    with open(args.out, 'w') as f:
        for sp in sorted(syn):
            f.write(sp + '\n')
    print(f'\nMarkers ecrits dans {args.out}', file=sys.stderr)


if __name__ == '__main__':
    main()
