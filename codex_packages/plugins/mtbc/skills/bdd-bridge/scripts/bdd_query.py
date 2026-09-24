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
    polarize <SPDI>        Distribution d'UN SPDI par clade en 3 états ON/OFF/UNKNOWN,
                           polarisation par l'outgroup, et dose-réponse couverture x
                           non-portage (le test qui sépare un non-appel d'un vrai
                           allèle de référence)
    denominator <clade>    Effectif local EXPLOITABLE vs effectif TBannotator, avec
                           les avertissements qui empêchent de confondre l'échantillon
                           étudié et la population (garde de dénominateur, P63.3)
"""
import os, sys, json, argparse, re, csv, pathlib
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

# --- Contenu réel d'un répertoire de souche (P63.7, 2026-09-06) -------------
# Un répertoire d'accession NE GARANTIT PAS une souche exploitable : le balayage
# exhaustif du 2026-09-06 a trouvé 1 025 répertoires sans aucune donnée génomique
# sur 168 155, dont 943 dans la seule lignée L4.7 (41,4 % de ses répertoires :
# 548 entièrement vides créés en un lot le 2026-03-17, 395 ne portant qu'un
# crispr_reads_report.json). Compter des répertoires y surestime de 70 %.
CONTENT_REPORT = "report"    # report.json présent : souche complète
CONTENT_SPDI = "spdi"        # spdi.txt seul : format ancien, exploitable
CONTENT_CRISPR = "crispr"    # crispr_reads_report.json seul : PAS de génomique
CONTENT_EMPTY = "vide"       # NC_000962.3 vide : rien du tout
CONTENT_OTHER = "autre"      # ni spdi ni report
USABLE = (CONTENT_REPORT, CONTENT_SPDI)


def strain_content(path):
    """Classe le contenu réel de <path>/NC_000962.3. Voir CONTENT_* ci-dessus."""
    d = os.path.join(path, REF)
    try:
        files = set(os.listdir(d))
    except OSError:
        return CONTENT_EMPTY
    if not files:
        return CONTENT_EMPTY
    if "report.json" in files:
        return CONTENT_REPORT
    if "spdi.txt" in files:
        return CONTENT_SPDI
    if files == {"crispr_reads_report.json"}:
        return CONTENT_CRISPR
    return CONTENT_OTHER


def is_usable_strain_dir(p):
    """Vrai si le répertoire porte une donnée génomique exploitable."""
    return is_strain_dir(p) and strain_content(p) in USABLE

def list_clades(bdd):
    root = actuelle(bdd)
    out = []
    for name in sorted(os.listdir(root)):
        d = os.path.join(root, name)
        if not os.path.isdir(d):
            continue  # ignore _flatten_*_undo_log.tsv etc.
        strains = [s for s in os.listdir(d) if is_strain_dir(os.path.join(d, s))]
        kinds = Counter(strain_content(os.path.join(d, s)) for s in strains)
        usable = sum(kinds[k] for k in USABLE)
        out.append({"clade": name, "n_strains": len(strains),
                    "n_exploitables": usable,
                    "n_sans_donnee": len(strains) - usable,
                    "contenu": dict(kinds)})
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
    """Ensemble de positions génomiques à exclure, une par ligne.

    Accepte DEUX écritures, délibérément, parce que `align` écrit lui-même son
    `.positions.txt` en SPDI et qu'un masque dérivé de sa propre sortie doit
    pouvoir lui être redonné sans conversion (le refuser obligeait à un `awk`
    jetable à chaque usage — corrigé le 2026-09-10, P72.4) :
      - position nue            : `103835`
      - SPDI complet            : `NC_000962.3:103835:G:T`  (2e champ = position)
    Les lignes vides et les commentaires `#` sont ignorés ; une ligne
    inexploitable est signalée plutôt que silencieusement perdue.
    Ex. global_supplementary/traces_mask/traces_mask_positions.txt (PE/PPE +
    répétitions + résistance)."""
    if not path or not os.path.exists(path):
        return set()
    out, bad = set(), []
    with open(path) as f:
        for lineno, raw in enumerate(f, 1):
            l = raw.strip()
            if not l or l.startswith("#"):
                continue
            tok = l.split()[0]
            field = tok.split(":")[1] if ":" in tok else tok
            try:
                out.add(int(field))
            except ValueError:
                bad.append((lineno, l[:60]))
    if bad:
        head = "; ".join(f"l.{n}: {t}" for n, t in bad[:3])
        print(f"# masque {path} : {len(bad)} ligne(s) illisible(s) ignorée(s) ({head})",
              file=sys.stderr)
    return out

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
    usable = sum(d["n_exploitables"] for d in data)
    if args.json:
        return {"bdd": bdd, "n_clades": len(data), "n_strains_total": total,
                "n_exploitables_total": usable,
                "n_sans_donnee_total": total - usable, "clades": data}
    lines = [f"{d['clade']}\t{d['n_strains']}\t{d['n_exploitables']}" for d in data]
    hdr = "# clade\trepertoires\texploitables"
    foot = (f"# {len(data)} clades, {total} repertoires, {usable} exploitables, "
            f"{total - usable} sans donnee genomique")
    return hdr + "\n" + "\n".join(lines) + "\n" + foot

# --- Garde de dénominateur (P63.3, 2026-09-06) ------------------------------
# `bdd/` est le sous-ensemble CURÉ de ce qui a été ÉTUDIÉ (politique CG,
# 2026-09-06), pas un miroir de TBannotator : 105 929 souches de la base n'y ont
# aucun répertoire. Un effectif local décrit donc l'ÉCHANTILLON TRAVAILLÉ, jamais
# la population. Cette commande met les deux comptes côte à côte pour qu'aucun
# manuscrit n'annonce l'un en croyant dire l'autre.
TBA_URL_DEFAUT = "https://tblearn.tbannotator.ideev.universite-paris-saclay.fr/mcp"
TBA_GEL = ("La base publique est un INSTANTANÉ FIGÉ à 2026-02 (reprise de TBannotator "
           "par C. Lecarpentier, déploiement IDEEV/Paris-Saclay). Le pipeline `mp` a "
           "continué de produire depuis : 17 846 souches calculées n'y sont pas encore "
           "ingérées. Le compte distant est donc un plancher.")


def _tba_query(sql, timeout=60):
    """Interroge le MCP TBannotator en JSON-RPC (stdlib uniquement)."""
    import urllib.request
    url = os.environ.get("TBANNOTATOR_MCP_URL", TBA_URL_DEFAUT).rstrip("/")

    def post(payload, sid=None):
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json, text/event-stream")
        if sid:
            req.add_header("mcp-session-id", sid)
        r = urllib.request.urlopen(req, timeout=timeout)
        out = None
        for line in r.read().decode().splitlines():
            if line.startswith("data:"):
                out = json.loads(line[5:].strip())
        return out, r.headers.get("mcp-session-id", sid)

    _, sid = post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                   "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                              "clientInfo": {"name": "bdd-bridge", "version": "1"}}})
    post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, sid)
    res, _ = post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                   "params": {"name": "tool_query_postgres",
                              "arguments": {"query": sql, "max_rows": 50,
                                            "compress": False,
                                            "timeout_seconds": timeout}}}, sid)
    txt = [c["text"] for c in res.get("result", {}).get("content", [])
           if c.get("type") == "text"][0]
    try:
        d = json.loads(txt)
    except Exception:
        import ast
        d = ast.literal_eval(txt)
    if not d.get("success"):
        raise RuntimeError(str(d.get("error"))[:200])
    return list(csv.reader(io_StringIO(d["data"]["csv"])))


def io_StringIO(txt):
    import io as _io
    return _io.StringIO(txt)


def clade_to_lineage_code(clade):
    """Traduit un nom de répertoire local en code de lignée TBannotator.

    Les codes du système `guyeux` sont sans préfixe « L » (`4.15`, `Bovis La1`).
    Renvoie None si la traduction n'est pas sûre : mieux vaut ne rien affirmer que
    comparer deux choses différentes.
    """
    c = clade.strip()
    if re.match(r"^L\d+(\.\d+)*$", c):
        return c[1:]
    if re.match(r"^\d+(\.\d+)*$", c):
        return c
    if c.lower().startswith(("bovis", "caprae", "orygis", "bcg", "canettii", "pinipedii")):
        return c
    return None


def cmd_denominator(bdd, args):
    clade = args.clade
    d = os.path.join(actuelle(bdd), clade)
    if not os.path.isdir(d):
        raise SystemExit(f"clade introuvable sur disque : {clade}")
    kinds = Counter()
    for s in os.listdir(d):
        p = os.path.join(d, s)
        if is_strain_dir(p):
            kinds[strain_content(p)] += 1
    n_dirs = sum(kinds.values())
    n_usable = sum(kinds[k] for k in USABLE)
    code = clade_to_lineage_code(clade)
    remote = {"systeme": args.system, "code": code, "n": None, "erreur": None}
    if args.local_only:
        remote["erreur"] = "--local-only : base non interrogée"
    elif code is None:
        remote["erreur"] = ("nom de répertoire non traduisible en code de lignée ; "
                            "comparer à la main plutôt que de deviner")
    else:
        sql = ("SELECT count(DISTINCT strain_name) AS n FROM mv_strain_classification "
               f"WHERE system_name = '{args.system}' AND lineage_code = '{code}'")
        try:
            rows = _tba_query(sql)
            remote["n"] = int(rows[1][0]) if len(rows) > 1 else 0
        except Exception as exc:                      # serveur injoignable, etc.
            remote["erreur"] = str(exc)[:200]
    out = {"clade": clade, "bdd": bdd,
           "local": {"repertoires": n_dirs, "exploitables": n_usable,
                     "sans_donnee": n_dirs - n_usable, "contenu": dict(kinds)},
           "tbannotator": remote,
           "avertissements": [
               "Un effectif bdd/ décrit l'ÉCHANTILLON ÉTUDIÉ, pas la population.",
               TBA_GEL,
           ]}
    if n_dirs != n_usable:
        out["avertissements"].insert(0, (
            f"{n_dirs - n_usable} des {n_dirs} répertoires de {clade} ne portent AUCUNE "
            f"donnée génomique : compter les répertoires surestime de "
            f"{100.0 * (n_dirs - n_usable) / max(n_usable, 1):.0f} %."))
    if remote["n"] is not None and remote["n"] != n_usable:
        out["avertissements"].append(
            "Le placement local fait autorité et peut diverger de la classification "
            "de la base : ces deux nombres ne sont pas deux mesures de la même chose.")
    if args.json:
        return out
    lines = [f"clade {clade}",
             f"  bdd/ répertoires          : {n_dirs}",
             f"  bdd/ EXPLOITABLES         : {n_usable}",
             f"  bdd/ sans donnée          : {n_dirs - n_usable}  {dict(kinds)}"]
    if remote["n"] is not None:
        lines.append(f"  TBannotator ({args.system}, code {code}) : {remote['n']}")
    else:
        lines.append(f"  TBannotator               : non comparé — {remote['erreur']}")
    lines.append("")
    for w in out["avertissements"]:
        lines.append(f"  ! {w}")
    return "\n".join(lines)


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


# --- polarize : distribution d'UN SPDI par clade, en 3 états ON/OFF/UNKNOWN ---
# Forgé le 2026-09-08 (projet Rv2566, piste P13) après que le MÊME scanner par-souche eut été
# réécrit six fois dans un seul projet. La valeur ajoutée n'est pas le comptage, que trois lignes
# de `grep` rendent, c'est la distinction ABSENT / NON COUVERT : sans elle, une fréquence de
# 98,6 % ne se distingue pas d'une fixation totale entachée de 1,4 % de non-appels, et deux
# lectures opposées du même chiffre restent également défendables.
#
# LEÇON INTÉGRÉE, ET ELLE DÉPASSE LA SPÉCIFICATION D'ORIGINE. Le codage 3 états au seuil de
# COUVERTURE DU GÈNE ne suffit pas et peut rendre le verdict INVERSE du bon : sur l'indel de 2 pb
# de Rv2566 chez M. bovis, il classait 176 des 177 non-porteurs en « vrais sauvages » alors que la
# fixation est en réalité totale. Un seuil de gène (plusieurs kb) est bien trop permissif pour un
# indel, dont l'appel dépend de la profondeur LOCALE. Le test qui tranche est la DOSE-RÉPONSE
# (--dose-response) : si le non-portage décroît vers zéro quand la couverture monte, ce sont des
# non-appels ; s'il atteint un PLATEAU non nul, ce sont de vrais allèles de référence. Livrer la
# seule spécification d'origine aurait donc livré un outil qui se trompe sur le cas qui l'a motivé.

_COV_BINS = [(0, 10), (10, 20), (20, 30), (30, 50), (50, 80), (80, 120), (120, 200),
             (200, float("inf"))]


def read_gene_coverage(bdd, clade, sra, gene):
    """Couverture d'un gène + profondeur génome, depuis report.json.

    PIÈGE, coût d'un passage entier perdu avant d'être compris (2026-09-07) : les report.json de
    la BDD existent sous DEUX formats mêlés dans un même clade, pretty-printé et COMPACT (une
    seule ligne, ~75 % des fichiers). Un motif calé sur l'indentation ne voit que le quart
    pretty-printé et rend silencieusement une couverture manquante pour le reste, ce qui bascule à
    tort les souches concernées en UNKNOWN. D'où les `\\s*` partout et le mode DOTALL.
    """
    fp = os.path.join(actuelle(bdd), clade, sra, REF, "report.json")
    if not os.path.exists(fp):
        return None
    try:
        txt = open(fp, encoding="utf-8", errors="replace").read()
    except OSError:
        return None
    num = r"[-0-9.eE+]+"
    m = re.search(rf'"locus_tag":\s*"{re.escape(gene)}",\s*"mean_coverage":\s*({num}),'
                  rf'\s*"median_coverage":\s*({num}),\s*"percent_missing":\s*({num})', txt)
    if not m:
        return None
    out = {"mean": float(m.group(1)), "median": float(m.group(2)),
           "pct_missing": float(m.group(3)), "genome_depth": None}
    d = re.search(r'"mapping_stats":\s*\{[^}]*?"mean_depth":\s*([-0-9.eE+]+)', txt, re.S)
    if d:
        out["genome_depth"] = float(d.group(1))
    return out


def gene_of_spdi(bdd, clade, sra, spdi):
    """Locus tag du gène portant ce SPDI, lu dans l'annotation que le pipeline produit déjà."""
    fp = os.path.join(actuelle(bdd), clade, sra, REF, "report.json")
    if not os.path.exists(fp):
        return None
    try:
        d = json.load(open(fp, encoding="utf-8", errors="replace"))
    except Exception:
        return None
    for s in d.get("snp", []):
        if s.get("spdi") != spdi:
            continue
        for a in (s.get("annotations") or []):
            tag = (a.get("gene_locus_tag") or "").replace("gene-", "")
            if tag and tag != "null" and not tag.startswith("Rv0215c"):
                return tag
    return None


def call_state(has, cov, thr):
    if has:
        return "ON"
    if not cov or cov.get("median") is None:
        return "UNKNOWN"
    ratio = (cov["mean"] / cov["genome_depth"]) if (cov.get("genome_depth") and cov.get("mean")) else None
    if (cov["median"] < thr["min_median_cov"] or cov["pct_missing"] > thr["max_pct_missing"]
            or (ratio is not None and ratio < thr["min_mean_ratio"])):
        return "UNKNOWN"
    return "OFF"


def lire_liste_souches(chemin):
    """Lit une liste explicite de souches, une par ligne, au format `<clade>/<sra>`.

    Tolère un TSV dont la PREMIÈRE colonne porte le chemin (les colonnes suivantes sont
    ignorées), une ligne d'en-tête, les commentaires `#`, un préfixe `./`, et un suffixe
    `/NC_000962.3[/spdi.txt]` -- c'est-à-dire, telles quelles, les sorties de `rg -l` et les
    tables produites par les scripts d'analyse.

    RAISON D'ÊTRE (2026-09-08, projet Rv2566). Un clade RÉEL n'a pas toujours de nom : le
    sous-clade L1 portant un frameshift fixé de Rv2566 est réparti par la taxonomie de
    répertoires entre un conteneur NU `L1` de 21 163 souches, `L_1.A.2` et `L_1.A.2.1`. Aucun
    préfixe ne le désigne, si bien que `--clades` ne pouvait pas l'atteindre et qu'il a fallu
    écrire un scanner local. C'est exactement le motif que cette sous-commande existe pour
    supprimer.
    """
    pairs = []
    for ligne in pathlib.Path(chemin).read_text().splitlines():
        t = ligne.strip()
        if not t or t.startswith("#"):
            continue
        t = t.split("\t")[0].strip().lstrip("./")
        for suffixe in ("/NC_000962.3/spdi.txt", "/NC_000962.3/report.json", "/NC_000962.3"):
            if t.endswith(suffixe):
                t = t[: -len(suffixe)]
                break
        parts = [x for x in t.split("/") if x]
        if len(parts) < 2:
            continue                      # en-tête ou ligne libre : ignorée en silence
        clade, sra = parts[0], parts[-1]
        pairs.append((clade, sra))
    # dédoublonnage : certains chemins DOUBLENT l'accession (`<clade>/ERRxxx/ERRxxx/...`),
    # et compter des FICHIERS pour des SOUCHES gonfle les effectifs (vécu, Caprae 286 vs 278).
    vus, res = set(), []
    for c, s in pairs:
        if (c, s) in vus:
            continue
        vus.add((c, s))
        res.append((c, s))
    return res


def cmd_polarize(bdd, args):
    spdi = args.spdi
    thr = {"min_median_cov": args.min_median_cov, "max_pct_missing": args.max_pct_missing,
           "min_mean_ratio": args.min_mean_ratio}
    liste = getattr(args, "strains", None)
    prefixes = args.clades or ([] if liste else [c for c in list_clades(bdd)])
    if args.outgroup and args.outgroup not in prefixes:
        prefixes = list(prefixes) + [args.outgroup]

    pairs = []
    seen = set()
    for pref in prefixes:
        for clade, sra in list_strains_recursive(bdd, pref):
            if (clade, sra) in seen:
                continue
            seen.add((clade, sra))
            pairs.append((pref, clade, sra))
    if liste:
        nom = args.strains_name or pathlib.Path(liste).stem
        for clade, sra in lire_liste_souches(liste):
            if (clade, sra) in seen:
                continue
            seen.add((clade, sra))
            pairs.append((nom, clade, sra))

    gene = args.gene
    rows = []
    for pref, clade, sra in pairs:
        has = spdi in set(read_spdi(bdd, clade, sra))
        if gene is None and has:
            gene = gene_of_spdi(bdd, clade, sra, spdi)
        rows.append({"groupe": pref, "clade": clade, "sra": sra, "on": has})
    if gene is None:
        return {"erreur": "gène indéterminable : aucun porteur trouvé pour déduire le locus_tag ; "
                          "relancer avec --gene <locus_tag>", "spdi": spdi,
                "n_souches": len(rows)}

    # report.json lu pour les non-porteurs (obligatoire) et pour tous si --dose-response
    for r in rows:
        need = (not r["on"]) or args.dose_response
        cov = read_gene_coverage(bdd, r["clade"], r["sra"], gene) if need else None
        r["cov"] = cov
        r["etat"] = call_state(r["on"], cov, thr)

    par_groupe = {}
    for r in rows:
        g = par_groupe.setdefault(r["groupe"], {"n": 0, "ON": 0, "OFF": 0, "UNKNOWN": 0})
        g["n"] += 1
        g[r["etat"]] += 1
    for g in par_groupe.values():
        den = g["ON"] + g["OFF"]
        g["freq_naive"] = round(g["ON"] / g["n"], 4) if g["n"] else None
        g["freq_corrigee"] = round(g["ON"] / den, 4) if den else None

    out = {"spdi": spdi, "gene": gene, "seuils": thr, "n_souches": len(rows),
           "par_groupe": par_groupe}
    if args.outgroup and args.outgroup in par_groupe:
        o = par_groupe[args.outgroup]
        out["polarisation"] = {
            "outgroup": args.outgroup, "n": o["n"], "ON": o["ON"],
            "lecture": ("état DÉRIVÉ : absent de l'outgroup" if o["ON"] == 0 else
                        "état présent chez l'outgroup : NE PAS revendiquer une acquisition "
                        "spécifique de lignée sans réexaminer la polarité")}
    if args.dose_response:
        # BUG CORRIGÉ LE JOUR MÊME DE LA FORGE, et il vaut d'être consigné : agréger toutes les
        # souches dans une seule courbe mélange les clades CIBLES avec l'OUTGROUP, qui est par
        # construction non porteur du site. Sur le test de non-régression (site Bovis, outgroup
        # Canettii), les 149 Canettii se répartissaient dans les tranches comme autant de faux
        # non-porteurs et faisaient remonter la tranche [120,200) de 0,00 % à 2,10 % — c'est-à-dire
        # qu'ils fabriquaient un PLATEAU là où il n'y en a pas, donc le verdict exactement inverse
        # du bon. La dose-réponse est donc rendue PAR GROUPE, jamais agrégée.
        dr = {}
        for grp in sorted(par_groupe):
            sub_g = [r for r in rows if r["groupe"] == grp]
            bins = []
            for lo, hi in _COV_BINS:
                sub = [r for r in sub_g if r["cov"] and r["cov"].get("median") is not None
                       and lo <= r["cov"]["median"] < hi]
                non = sum(1 for r in sub if not r["on"])
                bins.append({"couverture_mediane_gene": (f"[{lo},{hi})" if hi != float("inf")
                                                        else f">={lo}"),
                             "n": len(sub), "n_non_porteurs": non,
                             "pct_non_porteurs": round(100.0 * non / len(sub), 3) if sub else None})
            dr[grp] = bins
        out["dose_reponse"] = dr
        out["lecture_dose_reponse"] = (
            "décroissance vers zéro sans plateau = NON-APPELS (le site est en réalité fixé) ; "
            "plateau non nul = vrais allèles de référence. C'est ce test, et non le seuil 3 états, "
            "qui tranche pour un INDEL ou un microsatellite.")
    if args.json:
        return out

    lines = [f"SPDI {spdi}   gène {gene}   {len(rows)} souches",
             f"seuils : median>={thr['min_median_cov']}  pct_missing<={thr['max_pct_missing']}  "
             f"mean_ratio>={thr['min_mean_ratio']}", ""]
    lines.append(f"{'groupe':22s} {'n':>7s} {'ON':>7s} {'OFF':>6s} {'UNK':>6s} "
                 f"{'f_naive':>9s} {'f_corr':>8s}")
    for g, v in sorted(par_groupe.items(), key=lambda x: -x[1]["n"]):
        fn = "-" if v["freq_naive"] is None else f"{100*v['freq_naive']:.2f}"
        fc = "-" if v["freq_corrigee"] is None else f"{100*v['freq_corrigee']:.2f}"
        lines.append(f"{g:22s} {v['n']:7d} {v['ON']:7d} {v['OFF']:6d} {v['UNKNOWN']:6d} "
                     f"{fn:>9s} {fc:>8s}")
    if "polarisation" in out:
        lines += ["", f"polarisation ({out['polarisation']['outgroup']}) : "
                      f"{out['polarisation']['ON']}/{out['polarisation']['n']} — "
                      f"{out['polarisation']['lecture']}"]
    if args.dose_response:
        for grp, bins in out["dose_reponse"].items():
            lines += ["", f"dose-réponse — {grp} (couverture du gène x non-portage) :"]
            for b in bins:
                pc = "-" if b["pct_non_porteurs"] is None else f"{b['pct_non_porteurs']:.2f}"
                lines.append(f"  {b['couverture_mediane_gene']:>12s}  n={b['n']:6d}  "
                             f"non-porteurs={b['n_non_porteurs']:5d}  {pc:>7s} %")
        lines += ["", "  " + out["lecture_dose_reponse"]]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Pont lecture read-only bdd/actuelle MTBC")
    ap.add_argument("--bdd", help="chemin racine bdd/ (défaut: $TBANNOTATOR_BDD ou ../bdd)")
    ap.add_argument("--json", action="store_true", help="sortie JSON")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("clades")
    p = sub.add_parser("strains"); p.add_argument("clade")
    p.add_argument("--recursive", action="store_true", help="agréger clade + tout son sous-arbre clade.*")
    p = sub.add_parser("denominator", help="effectif local EXPLOITABLE vs effectif TBannotator (garde de dénominateur)")
    p.add_argument("clade")
    p.add_argument("--system", default="guyeux", help="système de classification distant (défaut: guyeux)")
    p.add_argument("--local-only", action="store_true", dest="local_only", help="ne pas interroger la base")
    p = sub.add_parser("strain"); p.add_argument("clade"); p.add_argument("sra")
    p = sub.add_parser("matrix"); p.add_argument("clade"); p.add_argument("--min-frac", type=float, default=0.0, dest="min_frac")
    p.add_argument("--recursive", action="store_true", help="agréger clade + tout son sous-arbre clade.*")
    p = sub.add_parser("synapo"); p.add_argument("clade"); p.add_argument("--min-frac", type=float, default=0.0, dest="min_frac")
    p.add_argument("--recursive", action="store_true", help="agréger clade + tout son sous-arbre clade.*")
    p = sub.add_parser("polarize", help="distribution d'UN SPDI par clade en 3 états ON/OFF/UNKNOWN "
                       "(+ polarisation par l'outgroup, + dose-réponse couverture x non-portage)")
    p.add_argument("spdi", help="ex. NC_000962.3:2887961:GGC:G")
    p.add_argument("--clades", nargs="+", help="préfixes de clades (défaut : tous, sauf si --strains)")
    p.add_argument("--strains", help="fichier de souches `<clade>/<sra>` (une par ligne, TSV "
                                     "toléré) formant un GROUPE nommé : sert quand le clade réel "
                                     "n'a pas de nom dans la taxonomie de répertoires")
    p.add_argument("--strains-name", dest="strains_name", default=None,
                   help="nom du groupe défini par --strains (défaut : nom du fichier)")
    p.add_argument("--outgroup", default=None, help="clade servant de groupe externe (ex. Canettii)")
    p.add_argument("--gene", default=None, help="locus_tag portant le site ; déduit du 1er porteur si omis")
    p.add_argument("--min-median-cov", type=float, default=10.0, dest="min_median_cov")
    p.add_argument("--max-pct-missing", type=float, default=0.10, dest="max_pct_missing")
    p.add_argument("--min-mean-ratio", type=float, default=0.10, dest="min_mean_ratio")
    p.add_argument("--dose-response", action="store_true", dest="dose_response",
                   help="lit report.json pour TOUTES les souches (coûteux) et rend la courbe "
                        "non-portage x couverture — LE test qui tranche pour un indel")
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
          "matrix": cmd_matrix, "synapo": cmd_synapo, "align": cmd_align,
          "denominator": cmd_denominator, "polarize": cmd_polarize}[args.cmd]
    res = fn(bdd, args)
    if isinstance(res, (dict, list)) or args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(res)

if __name__ == "__main__":
    main()
