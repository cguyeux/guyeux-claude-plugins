#!/usr/bin/env python3
"""
bdd_query.py — Pont de lecture read-only sur bdd/actuelle/ (base MTBC locale).

Conçu pour être appelable à l'identique depuis Claude Code (shell-out) et depuis
Claude Science. Stdlib pure, aucune dépendance. Sortie --json partout.

Structure attendue de la BDD :
    <bdd>/actuelle/<clade>/<SRA>/NC_000962.3/{spdi.txt, report.json}

Localisation de la BDD (par priorité) :
    --bdd <chemin>  |  $TBANNOTATOR_BDD  |  ../bdd (relatif au dépôt mtbc)

Sous-commandes :
    clades                 Liste des clades + effectif (souches)
    strains <clade>        Liste des souches d'un clade
    strain  <clade> <SRA>  Détail d'une souche (QC + nb SNP)
    matrix  <clade>        Matrice SNP binaire (présence/absence) du clade -> TSV/JSON
    synapo  <clade>        Positions SPDI partagées par (presque) toutes les souches du clade
"""
import os, sys, json, argparse, re, csv
from collections import Counter

GENOME_LEN_H37RV = 4411532  # NC_000962.3

REF = "NC_000962.3"

def find_bdd(cli_path):
    if cli_path:
        return os.path.abspath(cli_path)
    env = os.environ.get("TBANNOTATOR_BDD")
    if env and os.path.isdir(env):
        return os.path.abspath(env)
    here = os.path.dirname(os.path.abspath(__file__))
    for up in range(6):
        cand = os.path.join(here, *([".."]*up), "bdd")
        if os.path.isdir(os.path.join(cand, "actuelle")):
            return os.path.abspath(cand)
    return os.path.abspath(os.path.join(here, "..", "bdd"))

def actuelle(bdd):
    return os.path.join(bdd, "actuelle")

def is_strain_dir(p):
    return os.path.isdir(os.path.join(p, REF))

def list_clades(bdd):
    root = actuelle(bdd)
    out = []
    for name in sorted(os.listdir(root)):
        d = os.path.join(root, name)
        if not os.path.isdir(d):
            continue  # ignore _flatten_*_undo_log.tsv etc.
        strains = [s for s in os.listdir(d) if is_strain_dir(os.path.join(d, s))]
        out.append({"clade": name, "n_strains": len(strains)})
    return out

def list_strains(bdd, clade):
    d = os.path.join(actuelle(bdd), clade)
    if not os.path.isdir(d):
        raise SystemExit(f"clade introuvable : {clade}")
    return sorted(s for s in os.listdir(d) if is_strain_dir(os.path.join(d, s)))

def subtree_clades(bdd, prefix):
    """Conteneurs 'prefix' + tous ses descendants 'prefix.*' (ex. L5.2.1 ->
    L5.2.1, L5.2.1.1, L5.2.1.1.1.1, ...). Une lignée matérialisée en
    sous-conteneurs géographiques/phylogénétiques n'est PAS un seul dossier ;
    comparer un clade entier à un marqueur publié exige d'agréger tout le
    sous-arbre, pas seulement le conteneur racine."""
    root = actuelle(bdd)
    return sorted(d for d in os.listdir(root)
                  if os.path.isdir(os.path.join(root, d))
                  and (d == prefix or d.startswith(prefix + ".")))

def list_strains_recursive(bdd, prefix):
    """[(clade_dir, sra), ...] pour tout le sous-arbre de `prefix`."""
    pairs = []
    for d in subtree_clades(bdd, prefix):
        for s in list_strains(bdd, d):
            pairs.append((d, s))
    return pairs

def read_spdi(bdd, clade, sra):
    fp = os.path.join(actuelle(bdd), clade, sra, REF, "spdi.txt")
    if not os.path.exists(fp):
        return []
    with open(fp) as f:
        return [ln.strip() for ln in f if ln.strip()]

def strain_detail(bdd, clade, sra):
    spdi = read_spdi(bdd, clade, sra)
    rj = os.path.join(actuelle(bdd), clade, sra, REF, "report.json")
    qc = {}
    if os.path.exists(rj):
        try:
            d = json.load(open(rj))
            ms = d.get("mapping_stats", {})
            qc = {
                "covered_bases_percent": ms.get("covered_bases_percent"),
                "mean_depth": ms.get("mean_depth"),
                "mean_mapq": ms.get("mean_mapq"),
                "gc_content": d.get("quality", {}).get("after_filtering", {}).get("gc_content"),
            }
        except Exception as e:
            qc = {"error": str(e)}
    return {"clade": clade, "strain": sra, "n_snp": len(spdi), "qc": qc}

def spdi_pos(spdi):
    """Position génomique d'un SPDI 'NC_000962.3:pos:ref:alt'."""
    return int(spdi.split(":")[1])

_TRANSITIONS = {("C", "T"), ("T", "C"), ("G", "A"), ("A", "G")}

def is_transition(spdi):
    """Vrai si le SPDI est une transition (C↔T ou G↔A). Les dommages de
    l'ADN ancien (désamination) produisent presque exclusivement des
    transitions C→T / G→A, créant de faux SNP singletons qui gonflent la
    branche terminale des génomes anciens. Filtrer les transitions sur les
    seules souches aDNA supprime cet artefact ; on garde les transversions,
    non affectées par la désamination."""
    parts = spdi.split(":")
    if len(parts) < 4:
        return False
    ref, alt = parts[2].upper(), parts[3].upper()
    return (ref, alt) in _TRANSITIONS

def load_mask(path):
    """Ensemble de positions génomiques à exclure (une position par ligne).
    Ex. global_supplementary/traces_mask/traces_mask_positions.txt (PE/PPE +
    répétitions + résistance)."""
    if not path or not os.path.exists(path):
        return set()
    with open(path) as f:
        return {int(l) for l in f if l.strip() and not l.startswith("#")}

_CUS = re.compile(r"CUS_GS_(\d+)_(\d+)")

def strain_deletions(bdd, clade, sra, rd_table=None):
    """Intervalles (start, stop) supprimés chez une souche, depuis
    report.json['missing_rd']. Les CUS_GS portent leurs coordonnées dans le
    nom (auto-suffisants). Les RD nommés ne sont résolus que si rd_table
    (dict nom->(start,stop)) est fourni ; sinon ignorés (les CUS_GS couvrent
    en pratique les mêmes délétions, cf. rd_materialize.py)."""
    rj = os.path.join(actuelle(bdd), clade, sra, REF, "report.json")
    if not os.path.exists(rj):
        return []
    try:
        mr = json.load(open(rj)).get("missing_rd") or []
    except Exception:
        return []
    items = mr.keys() if isinstance(mr, dict) else mr
    ranges = []
    for tag in items:
        tag = str(tag)
        m = _CUS.match(tag)
        if m:
            ranges.append((int(m.group(1)), int(m.group(2))))
        elif rd_table and tag.rstrip("*?") in rd_table:
            ranges.append(rd_table[tag.rstrip("*?")])
    return ranges

def load_rd_table(path):
    """Table RD nommés -> (start, stop). Lit bespiatykh_canonical_rd.csv
    (colonnes rd_name,start,length,end,...) ; résout via end, sinon
    start+length, sinon le synonyme CUS_GS."""
    table = {}
    if not path or not os.path.exists(path):
        return table
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("rd_name") or "").strip().rstrip("*?")
            if not name:
                continue
            s = (row.get("start") or "").strip()
            e = (row.get("end") or "").strip()
            ln = (row.get("length") or "").strip()
            if s and e:
                table[name] = (int(s), int(e))
            elif s and ln:
                table[name] = (int(s), int(s) + int(ln) - 1)
            else:
                m = _CUS.match((row.get("sola_matched_cusgs") or ""))
                if m:
                    table[name] = (int(m.group(1)), int(m.group(2)))
    return table

def in_ranges(pos, ranges):
    return any(a <= pos <= b for a, b in ranges)

def build_alignment(bdd, clades, mask=None, min_frac=0.0, code_rd=True,
                    rd_table=None, adna_strains=None, adna_transversions=False):
    """Alignement binaire multi-clades avec masque de positions et codage
    des délétions RD en données manquantes.

    adna_strains / adna_transversions : si adna_transversions est vrai, pour
    chaque souche listée dans adna_strains, les SNP de type transition (C↔T,
    G↔A) sont codés '?' (données manquantes) au lieu de '1'. Corrige
    l'inflation de branche des génomes anciens due à la désamination.

    Retourne (strains, cols, char_matrix, stats) où char_matrix[s] est une
    chaîne '0'/'1'/'?' alignée sur cols (positions génomiques triées)."""
    mask = mask or set()
    adna_strains = set(adna_strains or [])
    # collecte par souche : SPDI présents + intervalles délétés
    per_strain, per_del, order = {}, {}, []
    for clade in clades:
        for s in list_strains(bdd, clade):
            key = s  # SRA unique
            per_strain[key] = set(read_spdi(bdd, clade, s))
            per_del[key] = strain_deletions(bdd, clade, s, rd_table) if code_rd else []
            order.append(key)
    n = len(order)
    # panel = union des SPDI, position non masquée
    freq = Counter()
    for s in order:
        freq.update(per_strain[s])
    cols = [p for p in sorted(freq, key=spdi_pos)
            if spdi_pos(p) not in mask and (not n or freq[p] / n >= min_frac)]
    n_masked_cols = sum(1 for p in freq if spdi_pos(p) in mask)
    # matrice de caractères
    char = {}
    n_missing = 0
    n_adna_ts_masked = 0
    for s in order:
        row = []
        present = per_strain[s]
        dels = per_del[s]
        filter_ts = adna_transversions and s in adna_strains
        for p in cols:
            gp = spdi_pos(p)
            if p in present:
                if filter_ts and is_transition(p):
                    row.append("?"); n_missing += 1; n_adna_ts_masked += 1
                else:
                    row.append("1")
            elif dels and in_ranges(gp, dels):
                row.append("?"); n_missing += 1
            else:
                row.append("0")
        char[s] = "".join(row)
    stats = {"n_strains": n, "n_cols": len(cols), "n_masked_cols": n_masked_cols,
             "n_missing_cells": n_missing, "n_adna_ts_masked": n_adna_ts_masked,
             "pct_missing": round(100 * n_missing / (n * len(cols)), 3) if n and cols else 0.0}
    return order, cols, char, stats

def build_matrix(bdd, clade, min_frac=0.0, recursive=False):
    """Matrice binaire souches x positions SPDI (1 = variant présent).
    recursive=True agrège `clade` + tout son sous-arbre `clade.*`."""
    if recursive:
        pairs = list_strains_recursive(bdd, clade)
        strains = [s for _, s in pairs]
        per_strain = {s: set(read_spdi(bdd, d, s)) for d, s in pairs}
    else:
        strains = list_strains(bdd, clade)
        per_strain = {s: set(read_spdi(bdd, clade, s)) for s in strains}
    freq = Counter()
    for s in strains:
        freq.update(per_strain[s])
    n = len(strains)
    cols = sorted(p for p, c in freq.items() if c / n >= min_frac) if n else []
    return strains, cols, per_strain, freq, n

def cmd_clades(bdd, args):
    data = list_clades(bdd)
    total = sum(d["n_strains"] for d in data)
    if args.json:
        return {"bdd": bdd, "n_clades": len(data), "n_strains_total": total, "clades": data}
    lines = [f"{d['clade']}\t{d['n_strains']}" for d in data]
    return "\n".join(lines) + f"\n# {len(data)} clades, {total} souches"

def cmd_strains(bdd, args):
    if getattr(args, "recursive", False):
        pairs = list_strains_recursive(bdd, args.clade)
        if args.json:
            return {"clade": args.clade, "recursive": True, "n_strains": len(pairs),
                    "strains": [{"dir": d, "sra": s} for d, s in pairs]}
        lines = [f"{d}/{s}" for d, s in pairs]
        return "\n".join(lines) + f"\n# {len(pairs)} souches (sous-arbre {args.clade}.*)"
    s = list_strains(bdd, args.clade)
    if args.json:
        return {"clade": args.clade, "n_strains": len(s), "strains": s}
    return "\n".join(s) + f"\n# {len(s)} souches"

def cmd_strain(bdd, args):
    return strain_detail(bdd, args.clade, args.sra)

def cmd_matrix(bdd, args):
    strains, cols, per_strain, freq, n = build_matrix(
        bdd, args.clade, args.min_frac, recursive=getattr(args, "recursive", False))
    if args.json:
        rows = {s: [1 if c in per_strain[s] else 0 for c in cols] for s in strains}
        return {"clade": args.clade, "n_strains": n, "n_positions": len(cols),
                "positions": cols, "matrix": rows}
    out = ["strain\t" + "\t".join(cols)]
    for s in strains:
        out.append(s + "\t" + "\t".join("1" if c in per_strain[s] else "0" for c in cols))
    hdr = f"# clade={args.clade} n_strains={n} n_positions={len(cols)} min_frac={args.min_frac}"
    return hdr + "\n" + "\n".join(out)

def cmd_align(bdd, args):
    clades = args.clades
    mask = load_mask(args.mask)
    rd_table = load_rd_table(args.rd_table) if args.rd_table else None
    adna = set()
    if getattr(args, "adna", None):
        for tok in args.adna:
            adna.update(t for t in tok.split(",") if t)
    order, cols, char, stats = build_alignment(
        bdd, clades, mask=mask, min_frac=args.min_frac,
        code_rd=not args.no_rd, rd_table=rd_table,
        adna_strains=adna, adna_transversions=getattr(args, "adna_transversions", False))
    # genome-len appelable = génome de référence - positions masquées
    genome_len = args.genome_len - len(mask)
    stats["mask_positions"] = len(mask)
    stats["genome_len_callable"] = genome_len
    stats["clades"] = clades

    # écriture PHYLIP relaxé (binaire, '?' = manquant)
    if args.out:
        with open(args.out, "w") as f:
            f.write(f" {stats['n_strains']} {stats['n_cols']}\n")
            for s in order:
                f.write(f"{s}  {char[s]}\n")
        # positions génomiques (1 par colonne, ordre de l'alignement)
        posf = os.path.splitext(args.out)[0] + ".positions.txt"
        with open(posf, "w") as f:
            f.write("\n".join(cols) + "\n")
        stats["alignment"] = args.out
        stats["positions_file"] = posf
    if args.json:
        return stats
    lines = [f"# alignement {'+'.join(clades)}",
             f"# {stats['n_strains']} souches x {stats['n_cols']} sites"
             f" ({stats['n_masked_cols']} colonnes masquées écartées)",
             f"# cellules manquantes (RD->?): {stats['n_missing_cells']}"
             f" ({stats['pct_missing']}%)",
             f"# transitions aDNA masquées: {stats.get('n_adna_ts_masked', 0)}"
             + (f" (souches: {','.join(sorted(adna))})" if adna else ""),
             f"# genome-len appelable pour ascertainment: {genome_len}"
             f"  (= {args.genome_len} - {len(mask)} masquées)"]
    if args.out:
        lines.append(f"# écrit: {stats['alignment']} + {stats['positions_file']}")
        lines.append(f"# -> beast2_binary.py --phylip {stats['alignment']}"
                     f" --dates DATES.tsv --out run.xml --ascertainment"
                     f" --genome-len {genome_len}")
    return "\n".join(lines)

def cmd_synapo(bdd, args):
    recursive = getattr(args, "recursive", False)
    strains, cols, per_strain, freq, n = build_matrix(bdd, args.clade, 0.0, recursive=recursive)
    thr = args.min_frac if args.min_frac > 0 else 0.95
    synapo = [{"spdi": p, "n": freq[p], "frac": round(freq[p]/n, 4)}
              for p in cols if n and freq[p]/n >= thr]
    synapo.sort(key=lambda x: (-x["frac"], x["spdi"]))
    if args.json:
        return {"clade": args.clade, "recursive": recursive, "n_strains": n, "threshold": thr,
                "n_synapo": len(synapo), "synapomorphies": synapo}
    out = [f"# clade={args.clade} n_strains={n} seuil={thr} recursive={recursive} -> {len(synapo)} synapomorphies"]
    out += [f"{d['spdi']}\t{d['n']}/{n}\t{d['frac']}" for d in synapo]
    return "\n".join(out)

def main():
    ap = argparse.ArgumentParser(description="Pont lecture read-only bdd/actuelle MTBC")
    ap.add_argument("--bdd", help="chemin racine bdd/ (défaut: $TBANNOTATOR_BDD ou ../bdd)")
    ap.add_argument("--json", action="store_true", help="sortie JSON")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("clades")
    p = sub.add_parser("strains"); p.add_argument("clade")
    p.add_argument("--recursive", action="store_true", help="agréger clade + tout son sous-arbre clade.*")
    p = sub.add_parser("strain"); p.add_argument("clade"); p.add_argument("sra")
    p = sub.add_parser("matrix"); p.add_argument("clade"); p.add_argument("--min-frac", type=float, default=0.0, dest="min_frac")
    p.add_argument("--recursive", action="store_true", help="agréger clade + tout son sous-arbre clade.*")
    p = sub.add_parser("synapo"); p.add_argument("clade"); p.add_argument("--min-frac", type=float, default=0.0, dest="min_frac")
    p.add_argument("--recursive", action="store_true", help="agréger clade + tout son sous-arbre clade.*")
    p = sub.add_parser("align", help="alignement binaire masqué + RD->? prêt pour BEAST2")
    p.add_argument("clades", nargs="+", help="un ou plusieurs clades")
    p.add_argument("--mask", help="fichier positions à masquer (ex. traces_mask_positions.txt)")
    p.add_argument("--rd-table", dest="rd_table", help="table RD nommés (bespiatykh_canonical_rd.csv) ; sinon seuls les CUS_GS sont codés")
    p.add_argument("--no-rd", action="store_true", help="ne PAS coder les délétions RD en '?'")
    p.add_argument("--adna", action="append", help="souche(s) aDNA (répétable ou liste séparée par virgules) ; cible du filtrage transitions")
    p.add_argument("--adna-transversions", action="store_true", dest="adna_transversions",
                   help="pour les souches --adna, coder les transitions (C<->T, G<->A) en '?' — corrige l'inflation de branche par désamination")
    p.add_argument("--min-frac", type=float, default=0.0, dest="min_frac")
    p.add_argument("--genome-len", type=int, default=GENOME_LEN_H37RV, dest="genome_len")
    p.add_argument("--out", help="fichier PHYLIP de sortie (+ .positions.txt)")
    args = ap.parse_args()

    bdd = find_bdd(args.bdd)
    if not os.path.isdir(actuelle(bdd)):
        raise SystemExit(f"bdd/actuelle introuvable sous : {bdd}")

    fn = {"clades": cmd_clades, "strains": cmd_strains, "strain": cmd_strain,
          "matrix": cmd_matrix, "synapo": cmd_synapo, "align": cmd_align}[args.cmd]
    res = fn(bdd, args)
    if isinstance(res, (dict, list)) or args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(res)

if __name__ == "__main__":
    main()
