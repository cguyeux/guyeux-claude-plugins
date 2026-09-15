#!/usr/bin/env python3
"""crispr-spacer-null — un espaceur CRISPR ressemble-t-il a sa cible plus que
le hasard, sur des sequences courtes (30-50 nt) et divergees ?

Extrait et generalise le harnais developpe dans `SpacerEgalVirus` (2026,
origine phagique des espaceurs du locus DR du MTBC) pour repondre a une
question qui revient dans plusieurs projets MTBC : un appariement BLAST a
e = 1e-3 - 10 sur 35-41 nt ne veut RIEN dire seul, il doit toujours etre lu
contre un modele nul explicite (cf. garde-fou 9 de `../archeo_crispr/` :
« un test de protospacer n'a de sens que comparatif »).

QUATRE outils, composables :

  null       -- genere des permutations d'ordre k (mono/di/tri/tetra-
                nucleotidique, marche eulerienne d'Altschul-Erickson
                generalisee) preservant EXACTEMENT le contenu en k-mers de
                chaque sequence, plus un diagnostic de DEGENERESCENCE (theoreme
                BEST, De Bruijn-van Aardenne-Ehrenfest-Smith-Tutte) : sur un
                fragment court, un nul d'ordre eleve peut n'avoir presque
                aucune sequence admissible, auquel cas un ratio de 1,00 ne
                prouve rien (piege documente : k=4 sur 35-41 nt est
                indecidable, mediane de 16 sequences possibles).

  controls   -- genere des temoins GENOMIQUES apparies en longueur et en GC,
                tires HORS d'un locus a exclure (+- flanc), dans un genome de
                reference. Sert a demasquer un effet de genome entier qu'une
                permutation ne peut pas detecter (P2.12 : les temoins
                decrochent des espaceurs des qu'on resserre le seuil, alors
                que la force d'appariement seule ne les distinguait pas).

  blast-test -- lance BLASTN (observe + nul) contre une base ou un FASTA
                cible, puis calcule deux tests, a un balayage de seuils
                d'e-value :
                  test A (force) : la meilleure e-value REELLE d'une requete
                  bat-elle celle de ses N permutations ?
                  test B (specificite) : la PROPORTION de hits tombant sur un
                  sous-ensemble cible (mot-cle(s) dans le nom du sujet) est-
                  elle plus elevee pour l'observe que pour le nul ?

  kmer-partial -- pour les sequences trop divergees pour aligner (approche
                Shmakov et al. 2017/2020) : compte les k-mers COURTS (16-20 nt)
                retrouves EXACTEMENT dans une cible, observe contre nul,
                avec un corpus temoin comme juge (un ratio eleve sur les DEUX
                corpus signale un artefact de composition).

Aucune etape ne se lit seule : un ratio observe/nul sans p empirique, ou un
nul dont la degenerescence n'a pas ete verifiee, ne prouve rien. Toujours
rapporter le ratio ET le p ET (pour k>=3) le diagnostic de degenerescence.

Usage :
    python3 crispr_spacer_null.py null --fasta spacers.fa --k 2 --n-perm 100 --out perms.fa
    python3 crispr_spacer_null.py null --fasta spacers.fa --k 4 --diagnostic-only
    python3 crispr_spacer_null.py controls --genome ref.fasta --fasta spacers.fa \\
        --exclude-start 3113658 --exclude-end 3132714 --flank 5000 --n 300 --out temoins.fa
    python3 crispr_spacer_null.py blast-test --observe spacers.fa --null perms.fa \\
        --db data/blast_db/mabase --target-keyword Mycobacterium --evalues 10 1 0.1 0.01
    python3 crispr_spacer_null.py kmer-partial --observe spacers.fa --null perms.fa \\
        --target cibles.fa --control temoins_composition.fa --k 16 18 20
"""

import argparse
import math
import random
import subprocess
import sys
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from statistics import mean, median

SEED_DEFAULT = 20260803  # convention du projet d'origine (SpacerEgalVirus, P2.1)


# ---------------------------------------------------------------------------
# FASTA I/O
# ---------------------------------------------------------------------------

def read_fasta(path):
    """-> dict {nom: sequence}, ordre d'insertion préservé."""
    seqs = {}
    name, chunks = None, []
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith(">"):
                if name is not None:
                    seqs[name] = "".join(chunks).upper()
                name, chunks = line[1:].strip(), []
            else:
                chunks.append(line.strip())
    if name is not None:
        seqs[name] = "".join(chunks).upper()
    return seqs


def write_fasta(seqs, path):
    with open(path, "w") as f:
        for name, seq in seqs.items():
            f.write(f">{name}\n{seq}\n")


def rc(s):
    return s.translate(str.maketrans("ACGTN", "TGCAN"))[::-1]


# ---------------------------------------------------------------------------
# 1. Permutation d'ordre k (Altschul-Erickson generalisee) + degenerescence
#    (theoreme BEST). Genere ce module a partir de
#    analyses/phase1_test_nul_permutation.py et
#    analyses/phase19_nul_ordre_superieur.py de SpacerEgalVirus (2026-08).
# ---------------------------------------------------------------------------

def klet_graph(seq, k):
    """Multigraphe oriente sur les (k-1)-mers de `seq` ; k=2 -> sommets = bases."""
    m = k - 1
    if m == 0:
        # k=1 : permutation simple de la composition, pas de graphe a proprement
        # parler -- traite a part dans klet_shuffle.
        return None, None, None
    verts = [seq[i:i + m] for i in range(len(seq) - m + 1)]
    edges = defaultdict(list)
    for a, b in zip(verts[:-1], verts[1:]):
        edges[a].append(b)
    return edges, verts[0], verts[-1]


def klet_shuffle(seq, k, rng, tries=200):
    """Permutation conservant EXACTEMENT le contenu en k-mers de `seq`.

    -> (sequence, ok). ok=False si le tirage d'arborescence echoue (sequence
    trop courte / trop degeneree) : on renvoie alors la sequence INCHANGEE
    plutot qu'une permutation d'ordre inferieur, pour ne jamais fabriquer
    silencieusement un nul plus faible que celui demande.
    """
    if k == 1:
        lst = list(seq)
        rng.shuffle(lst)
        return "".join(lst), True
    if len(seq) < 2 * k:
        return seq, False
    edges, first, last = klet_graph(seq, k)
    verts = list(edges.keys())

    tree = None
    for _ in range(tries):
        cand = {v: rng.choice(edges[v]) for v in verts if v != last}
        ok = True
        for v in verts:
            if v == last:
                continue
            seen, cur = set(), v
            while cur != last:
                if cur in seen or cur not in cand:
                    ok = False
                    break
                seen.add(cur)
                cur = cand[cur]
            if not ok:
                break
        if ok:
            tree = cand
            break
    if tree is None:
        return seq, False

    new_edges = {}
    for v in verts:
        lst = list(edges[v])
        if v != last:
            lst.remove(tree[v])
        rng.shuffle(lst)
        if v != last:
            lst.append(tree[v])
        new_edges[v] = lst

    m = k - 1
    out, idx, cur = [first], defaultdict(int), first
    n_edges = len(seq) - m
    for _ in range(n_edges):
        nxt = new_edges[cur][idx[cur]]
        idx[cur] += 1
        out.append(nxt[-1] if m else nxt)
        cur = nxt
    return "".join(out), True


def kmer_counts(s, k):
    c = defaultdict(int)
    for i in range(len(s) - k + 1):
        c[s[i:i + k]] += 1
    return dict(c)


def det_bareiss(mat):
    """Determinant entier exact (Bareiss)."""
    n = len(mat)
    if n == 0:
        return 1
    a = [[Fraction(x) for x in row] for row in mat]
    sign, prev = 1, Fraction(1)
    for i in range(n - 1):
        if a[i][i] == 0:
            for r in range(i + 1, n):
                if a[r][i] != 0:
                    a[i], a[r] = a[r], a[i]
                    sign = -sign
                    break
            else:
                return 0
        for r in range(i + 1, n):
            for c in range(i + 1, n):
                a[r][c] = (a[r][c] * a[i][i] - a[r][i] * a[i][c]) / prev
            a[r][i] = Fraction(0)
        prev = a[i][i]
    return int(sign * a[n - 1][n - 1])


def n_arborescences(edges, verts, root):
    idx = {v: i for i, v in enumerate(verts)}
    n = len(verts)
    lap = [[0] * n for _ in range(n)]
    for u in verts:
        for v in edges[u]:
            if u == v:
                continue
            lap[idx[u]][idx[u]] += 1
            lap[idx[u]][idx[v]] -= 1
    r = idx[root]
    minor = [[lap[i][j] for j in range(n) if j != r] for i in range(n) if i != r]
    return det_bareiss(minor)


def n_klet_sequences(seq, k):
    """Nombre EXACT de sequences de meme contenu en k-mers que `seq` (elle incluse).

    Sert de diagnostic de degenerescence : si ce nombre est petit (quelques
    dizaines), le nul d'ordre k n'a quasiment aucune liberte sur cette
    sequence et un ratio observe/nul proche de 1 est INDECIDABLE, pas un
    verdict de "pas de signal". Cf. SpacerEgalVirus P2.11 : k=4 sur des
    espaceurs de 35-41 nt donne une mediane de 16 sequences admissibles.
    """
    if k <= 1 or len(seq) < 2 * k:
        return None  # non applicable / trivial
    edges, first, last = klet_graph(seq, k)
    closed = {u: list(v) for u, v in edges.items()}
    closed.setdefault(last, [])
    closed[last] = closed[last] + [first]
    closed.setdefault(first, [])
    verts = sorted(closed.keys())
    n_paths = n_arborescences(closed, verts, first)
    for v in verts:
        n_paths *= math.factorial(len(closed[v]) - 1)
    for m in kmer_counts(seq, k).values():
        n_paths //= math.factorial(m)
    return n_paths


def write_perms(spacers, k, n_perm, path, seed=SEED_DEFAULT):
    rng = random.Random(seed)
    diag = {}
    with open(path, "w") as f:
        for name, seq in spacers.items():
            n_adm = n_klet_sequences(seq, k) if k >= 2 else None
            diag[name] = n_adm
            for i in range(n_perm):
                sh, ok = klet_shuffle(seq, k, rng)
                f.write(f">{name}|p{i}\n{sh}\n")
    return diag


def cmd_null(args):
    spacers = read_fasta(args.fasta)
    rng = random.Random(args.seed)
    # auto-test : verifie que le shuffle conserve bien les k-mers avant de
    # produire quoi que ce soit -- un nul non verifie ne vaut rien.
    for name, seq in list(spacers.items())[:min(20, len(spacers))]:
        sh, ok = klet_shuffle(seq, args.k, rng)
        if ok:
            assert sorted(sh) == sorted(seq), f"{name}: composition alteree"
            if args.k >= 2:
                assert kmer_counts(sh, args.k) == kmer_counts(seq, args.k), \
                    f"{name}: {args.k}-mers alteres"
    print(f"[auto-test] shuffle d'ordre {args.k} verifie sur "
          f"{min(20, len(spacers))} sequences.", file=sys.stderr)

    if args.diagnostic_only:
        rows = ["nom,longueur,n_sequences_admissibles_ordre_k"]
        vals = []
        for name, seq in spacers.items():
            n_adm = n_klet_sequences(seq, args.k)
            rows.append(f"{name},{len(seq)},{n_adm}")
            if n_adm is not None:
                vals.append(n_adm)
        print("\n".join(rows))
        if vals:
            print(f"\n# mediane={median(vals):.0f}  min={min(vals)}  "
                  f"n<100={sum(1 for v in vals if v < 100)}/{len(vals)}"
                  f"  (< 100 sequences admissibles = nul quasi degenere sur"
                  f" cette requete a cet ordre)", file=sys.stderr)
        return

    diag = write_perms(spacers, args.k, args.n_perm, args.out, args.seed)
    print(f"[ok] {len(spacers)} sequences x {args.n_perm} permutations d'ordre "
          f"{args.k} -> {args.out}", file=sys.stderr)
    if args.k >= 2:
        vals = [v for v in diag.values() if v is not None]
        if vals:
            n_low = sum(1 for v in vals if v < 100)
            print(f"[diagnostic] sequences admissibles par requete : "
                  f"mediane={median(vals):.0f}, min={min(vals)}, "
                  f"{n_low}/{len(vals)} sous 100 (nul quasi degenere pour ces"
                  f"-la : un ratio ~1 n'y prouve rien).", file=sys.stderr)


# ---------------------------------------------------------------------------
# 2. Temoins genomiques GC-apparies, hors locus
#    (analyses/phase17_specificite_temoins.py, phase22)
# ---------------------------------------------------------------------------

def gc_content(s):
    s = s.upper()
    return (s.count("G") + s.count("C")) / len(s) if s else 0.0


def genomic_controls(genome_seq, query_lens_gcs, exclude, n_controls, seed, gc_tol=0.02):
    """`exclude` = (start, end, flank) en coordonnees 0-based du genome a eviter.

    Tire des fenetres de meme longueur ET de GC apparie (+- gc_tol) que les
    requetes fournies (`query_lens_gcs` = liste de (longueur, gc_cible)),
    hors de [start-flank, end+flank[. Reproductible via `seed`.
    """
    rng = random.Random(seed)
    start, end, flank = exclude
    lo, hi = start - flank, end + flank
    h = genome_seq
    out = []
    tries = 0
    max_tries = n_controls * 20000
    while len(out) < n_controls and tries < max_tries:
        tries += 1
        L, cible = query_lens_gcs[rng.randrange(len(query_lens_gcs))]
        i = rng.randrange(0, len(h) - L)
        if lo < i < hi:
            continue
        s = h[i:i + L]
        if "N" in s or abs(gc_content(s) - cible) > gc_tol:
            continue
        out.append((f"temoin_{i}_{L}", s))
    if len(out) < n_controls:
        print(f"[avertissement] seulement {len(out)}/{n_controls} temoins "
              f"trouves apres {tries} tirages (tolerance GC ou longueur trop "
              f"stricte, ou genome trop court hors exclusion)", file=sys.stderr)
    return out


def cmd_controls(args):
    genome = read_fasta(args.genome)
    gseq = next(iter(genome.values()))
    queries = read_fasta(args.fasta)
    qlg = [(len(s), gc_content(s)) for s in queries.values()]
    ctrls = genomic_controls(
        gseq, qlg, (args.exclude_start, args.exclude_end, args.flank),
        args.n, args.seed, args.gc_tol)
    write_fasta(dict(ctrls), args.out)
    print(f"[ok] {len(ctrls)} temoins GC-apparies (tolerance ±{args.gc_tol}) "
          f"ecrits dans {args.out}", file=sys.stderr)


# ---------------------------------------------------------------------------
# 3. BLAST observe/nul + test A (force) + test B (specificite)
#    (analyses/phase1_test_nul_permutation.py)
# ---------------------------------------------------------------------------

def run_blast(fasta, db, evalue, out, threads=8):
    cmd = ["blastn", "-query", str(fasta), "-task", "blastn", "-db", str(db),
           "-evalue", str(evalue), "-num_threads", str(threads),
           "-outfmt", "10 qseqid sseqid stitle evalue", "-out", str(out)]
    subprocess.run(cmd, check=True)


def parse_hits(path):
    """-> {qseqid: [(stitle, evalue), ...]}."""
    hits = defaultdict(list)
    with open(path) as f:
        for line in f:
            parts = line.rstrip("\n").split(",")
            if len(parts) < 4:
                continue
            q, ev = parts[0], parts[-1]
            stitle = ",".join(parts[2:-1])
            try:
                hits[q].append((stitle, float(ev)))
            except ValueError:
                continue
    return hits


def matches_keyword(stitle, keywords):
    return any(kw.lower() in stitle.lower() for kw in keywords)


def test_A(obs_hits, null_hits, names, n_perm, thr):
    signif, testable, rows = 0, 0, []
    for name in names:
        obs = min((e for _, e in obs_hits.get(name, []) if e <= thr), default=None)
        best_null = []
        for k in range(n_perm):
            h = [e for _, e in null_hits.get(f"{name}|p{k}", []) if e <= thr]
            best_null.append(min(h, default=float("inf")))
        if obs is None:
            rows.append((name, None, None, None))
            continue
        testable += 1
        better = sum(1 for b in best_null if b <= obs)
        p = (better + 1) / (n_perm + 1)
        if p < 0.05:
            signif += 1
        rows.append((name, obs, better, p))
    attendu = 0.05 * testable
    return {"seuil": thr, "testables": testable, "signif": signif,
            "attendu": attendu, "ratio": signif / attendu if attendu else None,
            "rows": rows}


def test_B(obs_hits, null_hits, names, n_perm, keywords, thr):
    obs_tot = obs_in = 0
    for name in names:
        for s, e in obs_hits.get(name, []):
            if e > thr:
                continue
            obs_tot += 1
            if matches_keyword(s, keywords):
                obs_in += 1
    obs_prop = obs_in / obs_tot if obs_tot else 0.0

    props = []
    for k in range(n_perm):
        tot = inn = 0
        for name in names:
            for s, e in null_hits.get(f"{name}|p{k}", []):
                if e > thr:
                    continue
                tot += 1
                if matches_keyword(s, keywords):
                    inn += 1
        props.append(inn / tot if tot else 0.0)
    moy = mean(props) if props else 0.0
    ge = sum(1 for p in props if p >= obs_prop)
    p_emp = (ge + 1) / (n_perm + 1)
    return {"seuil": thr, "obs_in": obs_in, "obs_tot": obs_tot, "obs_prop": obs_prop,
            "nul_moyen": moy, "ratio": obs_prop / moy if moy else None, "p": p_emp}


def cmd_blast_test(args):
    observe = read_fasta(args.observe)
    OUT = Path(args.out_dir)
    OUT.mkdir(parents=True, exist_ok=True)

    obs_csv = OUT / "obs.csv"
    run_blast(args.observe, args.db, max(args.evalues), obs_csv, args.threads)
    obs_hits = parse_hits(obs_csv)

    null_hits = {}
    if args.null:
        null_csv = OUT / "null.csv"
        run_blast(args.null, args.db, max(args.evalues), null_csv, args.threads)
        null_hits = parse_hits(null_csv)
        n_perm = args.n_perm or (
            len(read_fasta(args.null)) // max(1, len(observe)))
    else:
        n_perm = 0

    names = sorted(observe)
    report = []
    for thr in sorted(args.evalues, reverse=True):
        if null_hits:
            a = test_A(obs_hits, null_hits, names, n_perm, thr)
            report.append(f"[A] e<={thr:<6g} testables={a['testables']:4d} "
                          f"signif={a['signif']:4d} attendu={a['attendu']:6.1f} "
                          f"ratio={a['ratio']}")
        if null_hits and args.target_keyword:
            b = test_B(obs_hits, null_hits, names, n_perm, args.target_keyword, thr)
            report.append(f"[B] e<={thr:<6g} observe={b['obs_in']}/{b['obs_tot']}="
                          f"{b['obs_prop']*100:.2f}% nul={b['nul_moyen']*100:.2f}% "
                          f"ratio={b['ratio']} p={b['p']:.4f}")
        if not null_hits:
            n = sum(1 for name in names if any(e <= thr for _, e in obs_hits.get(name, [])))
            report.append(f"[observe seul, pas de nul fourni] e<={thr:<6g} : "
                          f"{n}/{len(names)} requetes avec >=1 hit")
    txt = "\n".join(report)
    print(txt)
    (OUT / "rapport.txt").write_text(txt + "\n")


# ---------------------------------------------------------------------------
# 4. Correspondances partielles en k-mers courts (Shmakov 2017/2020)
#    (analyses/phase25_kmers_partiels.py)
# ---------------------------------------------------------------------------

def kmers_of(seq, k):
    return {seq[i:i + k] for i in range(len(seq) - k + 1) if "N" not in seq[i:i + k]}


def scan_corpus(sequences, wanted, k):
    """k-mers de `wanted` reellement presents dans `sequences` (un seul passage)."""
    found = set()
    for s in sequences:
        for i in range(len(s) - k + 1):
            m = s[i:i + k]
            if m in wanted:
                found.add(m)
    return found


def count_per_query(seqs, found, k):
    out = {}
    for name, seq in seqs.items():
        ks = kmers_of(seq, k)
        out[name] = sum(1 for m in ks if m in found or rc(m) in found)
    return out


def cmd_kmer_partial(args):
    observe = read_fasta(args.observe)
    null = read_fasta(args.null) if args.null else {}
    target_seqs = list(read_fasta(args.target).values())
    control_seqs = list(read_fasta(args.control).values()) if args.control else []
    n_perm = args.n_perm or (len(null) // max(1, len(observe)) if null else 0)

    for k in args.k:
        wanted = set()
        for d in (observe, null):
            for s in d.values():
                for m in kmers_of(s, k):
                    wanted.add(m)
                    wanted.add(rc(m))
        for corpus_name, corpus in (("cible", target_seqs), ("temoin", control_seqs)):
            if not corpus:
                continue
            found = scan_corpus(corpus, wanted, k)
            obs_counts = count_per_query(observe, found, k)
            obs_tot = sum(obs_counts.values())
            obs_touch = sum(1 for v in obs_counts.values() if v > 0)
            line = (f"k={k} corpus={corpus_name:<8s} observe: "
                    f"{obs_tot} k-mers retrouves, {obs_touch}/{len(observe)} "
                    f"requetes touchees")
            if null and n_perm:
                null_counts = count_per_query(null, found, k)
                tot_perm, touch_perm = [], []
                for i in range(n_perm):
                    c = [null_counts.get(f"{n}|p{i}", 0) for n in observe]
                    tot_perm.append(sum(c))
                    touch_perm.append(sum(1 for x in c if x > 0))
                mt = mean(tot_perm) if tot_perm else 0
                p_tot = (sum(1 for x in tot_perm if x >= obs_tot) + 1) / (n_perm + 1)
                line += (f" | nul={mt:.1f} ratio={obs_tot/mt if mt else float('nan'):.2f}x"
                        f" p={p_tot:.4f}")
            print(line)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("null", help="permutations d'ordre k + diagnostic de degenerescence")
    p.add_argument("--fasta", required=True)
    p.add_argument("--k", type=int, default=2, help="1=mono, 2=di, 3=tri, 4=tetra...")
    p.add_argument("--n-perm", type=int, default=100)
    p.add_argument("--seed", type=int, default=SEED_DEFAULT)
    p.add_argument("--out", default="null.fasta")
    p.add_argument("--diagnostic-only", action="store_true",
                   help="n'ecrit rien, rend juste le nombre de sequences admissibles par requete")
    p.set_defaults(func=cmd_null)

    p = sub.add_parser("controls", help="temoins genomiques GC-apparies hors locus")
    p.add_argument("--genome", required=True, help="FASTA du genome de reference (1 sequence)")
    p.add_argument("--fasta", required=True, help="requetes dont on reprend longueur+GC")
    p.add_argument("--exclude-start", type=int, required=True)
    p.add_argument("--exclude-end", type=int, required=True)
    p.add_argument("--flank", type=int, default=5000)
    p.add_argument("--n", type=int, default=300)
    p.add_argument("--gc-tol", type=float, default=0.02)
    p.add_argument("--seed", type=int, default=SEED_DEFAULT)
    p.add_argument("--out", default="controls.fasta")
    p.set_defaults(func=cmd_controls)

    p = sub.add_parser("blast-test", help="test A (force) + test B (specificite) observe vs nul")
    p.add_argument("--observe", required=True)
    p.add_argument("--null", help="FASTA des permutations (sortie de `null`) ; omis = observe seul")
    p.add_argument("--n-perm", type=int, default=0, help="0 = deduit de la taille du fichier null")
    p.add_argument("--db", required=True, help="base BLAST (prefixe makeblastdb)")
    p.add_argument("--evalues", type=float, nargs="+", default=[10, 1, 0.1, 0.01])
    p.add_argument("--target-keyword", nargs="+",
                   help="mot(s)-cle(s) dans le nom du sujet pour le test B (ex: Mycobacterium)")
    p.add_argument("--threads", type=int, default=8)
    p.add_argument("--out-dir", default="crispr_spacer_null_out")
    p.set_defaults(func=cmd_blast_test)

    p = sub.add_parser("kmer-partial", help="k-mers courts exacts (Shmakov), pour sequences trop divergees")
    p.add_argument("--observe", required=True)
    p.add_argument("--null")
    p.add_argument("--n-perm", type=int, default=0)
    p.add_argument("--target", required=True, help="FASTA du corpus cible")
    p.add_argument("--control", help="FASTA du corpus temoin (composition), juge du test")
    p.add_argument("--k", type=int, nargs="+", default=[16, 18, 20])
    p.set_defaults(func=cmd_kmer_partial)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
