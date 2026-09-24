#!/usr/bin/env python3
"""mtbc-epistasis -- detecteur d'evolution COMPENSATOIRE / d'epistasie de la
resistance MTBC, POLARISE contre les isolats non-resistants de la meme lignee.

Question : une mutation de resistance couteuse (ex. rpoB dans la RRDR, cout de
fitness) co-occurre-t-elle avec une mutation compensatoire candidate (rpoC/rpoA)
PLUS que le hasard ? Le piege (documente, cf. Oman P10.7) : une "compensatoire"
peut n'etre qu'un MARQUEUR de lignee ancestral, present chez tous les membres
d'une sous-lignee independamment de la resistance -> fausse co-occurrence par
structure de population (homoplasie).

Garde-fou : on ne compare JAMAIS globalement. On stratifie PAR LIGNEE et on teste
l'enrichissement de la compensatoire chez les R vs les non-R DANS chaque lignee,
puis on agrege par Mantel-Haenszel (OR ajuste sur la lignee). Une vraie
compensatoire est enrichie chez les R intra-lignee (OR_MH > 1) ; un simple
marqueur de lignee donne un stratum non informatif ou OR_MH ~ 1.

Entrees (au choix) :
  --bdd DIR        arborescence bdd/actuelle : DIR/<lignee>/<SRA>/NC_000962.3/report.json
                   (la lignee est le nom du repertoire parent)
  --manifest TSV   colonnes : strain <tab> lineage <tab> report_path
Sorties :
  TSV par paire (R-gene x compensatoire) : effectifs et OR par lignee + OR_MH,
  p (Cochran-Mantel-Haenszel), verdict. Plus un resume console.

Structure report.json (TBannotator v2) exploitee :
  d["snp"] = [ { "spdi": "NC_000962.3:<pos0>:<ref>:<alt>",
                 "annotations": [ { "gene_name", "gene_locus_tag" (prefixe "gene-"),
                                    "annotation": [effets], "impact", "protein_position",
                                    "hgvs_p", ... } ] }, ... ]
  La position genomique 1-based = pos0 (SPDI, 0-based) + 1.

Dependances : Python >=3.10, scipy (loi du chi2). MH implemente a la main.

Refs compensation : Comas et al. 2012 Nat Genet 44:106 (rpoC/rpoA compensent
rpoB) ; de Vos et al. 2013 AAC 57:827 ; Song et al. 2014. ahpC (promoteur) est un
CO-MARQUEUR de katG S315T (preuve de compensation de fitness plus faible :
Sherman 1996), inclus a titre secondaire et signale comme tel.
"""
import argparse, glob, json, math, os, sys
from collections import defaultdict

# --- Coordonnees H37Rv (NC_000962.3, 1-based) et locus tags (sans le prefixe
# --- "gene-" que porte report.json). Bornes de repli ; l'appariement se fait
# --- d'abord par gene_name, puis locus_tag, puis position. Corriger ici au besoin. ---
GENES = {
    "rpoB": {"locus": "Rv0667",  "start": 759807,  "end": 763325},
    "rpoC": {"locus": "Rv0668",  "start": 763370,  "end": 767320},
    "rpoA": {"locus": "Rv3457c", "start": 3877464, "end": 3878609},
    "katG": {"locus": "Rv1908c", "start": 2153889, "end": 2156111},
    "ahpC": {"locus": "Rv2428",  "start": 2726088, "end": 2726780},
}

# --- Definition de la RESISTANCE (proxy robuste, catalogue-independant) : une
# --- mutation non-synonyme dans la region a cout de fitness connu. ---
R_DEF = {
    "RIF": {"gene": "rpoB", "codons": range(426, 453)},   # RRDR (E. coli 507-533)
    "INH": {"gene": "katG", "codons": range(315, 316)},   # S315
}

# --- Paires resistance -> compensatoires candidates. include_upstream=True capte
# --- les mutations de promoteur (cas ahpC), non-codantes mais pertinentes. ---
PAIRS = [
    {"drug": "RIF", "r_gene": "rpoB", "comp": "rpoC", "include_upstream": False,
     "evidence": "forte (Comas 2012, de Vos 2013)"},
    {"drug": "RIF", "r_gene": "rpoB", "comp": "rpoA", "include_upstream": False,
     "evidence": "forte (Comas 2012)"},
    {"drug": "INH", "r_gene": "katG", "comp": "ahpC", "include_upstream": True,
     "evidence": "faible : co-marqueur, pas compensation de fitness prouvee (Sherman 1996)"},
]

NONSYN_EFFECTS = ("missense", "frameshift", "stop_gained", "stop_lost",
                  "start_lost", "inframe", "disruptive", "initiator")


def _nonsyn(effects, impact):
    """Effet fonctionnel (non-synonyme) ? Exclut synonyme / LOW."""
    if str(impact or "").upper() in ("HIGH", "MODERATE"):
        return True
    e = " ".join(str(x) for x in effects).lower()
    if "synonymous" in e:
        return False
    return any(x in e for x in NONSYN_EFFECTS)


def _upstream(effects):
    return "upstream" in " ".join(str(x) for x in effects).lower()


def _is_gene(gene_name, locus_suffix, pos1, gene):
    """L'annotation touche-t-elle `gene` ? gene_name d'abord, puis locus, puis position."""
    g = GENES[gene]
    if gene_name and str(gene_name).lower() == gene.lower():
        return True
    if locus_suffix and locus_suffix == g["locus"]:
        return True
    if pos1 is not None and g["start"] <= pos1 <= g["end"]:
        return True
    return False


def _iter_annotations(report):
    """Yield (gene_name, locus_suffix, effects, impact, protein_position, pos1)
    pour chaque annotation de chaque SNP du report.json."""
    for s in report.get("snp", []) or []:
        pos1 = None
        spdi = s.get("spdi", "")
        if isinstance(spdi, str):
            parts = spdi.split(":")
            if len(parts) >= 2 and parts[1].lstrip("-").isdigit():
                pos1 = int(parts[1]) + 1  # SPDI 0-based -> 1-based
        for a in s.get("annotations", []) or []:
            gn = a.get("gene_name")
            lt = (a.get("gene_locus_tag") or "").replace("gene-", "")
            eff = a.get("annotation", []) or []
            yield gn, lt, eff, a.get("impact"), a.get("protein_position"), pos1


def classify_strain(report):
    """Renvoie (r_status, comp_status, detail) :
      r_status  : dict drug -> bool
      comp_status : dict comp_gene -> bool
      detail    : dict {"r": {drug: [hgvs_p...]}, "comp": {gene: set(hgvs_p...)}}
                  (les listes servent au mode --describe : soustraction du fond de clade)"""
    r_status = {drug: False for drug in R_DEF}
    comp_status = {p["comp"]: False for p in PAIRS}
    comp_upstream = {p["comp"] for p in PAIRS if p["include_upstream"]}
    detail = {"r": {d: [] for d in R_DEF}, "comp": {c: set() for c in comp_status}}
    for gn, lt, eff, impact, pp, pos1 in _iter_annotations(report):
        for drug, d in R_DEF.items():
            if _is_gene(gn, lt, pos1, d["gene"]) and _nonsyn(eff, impact):
                if isinstance(pp, int) and pp in d["codons"]:
                    r_status[drug] = True
                    detail["r"][drug].append(_label(gn, pp, eff))
        for comp_gene in comp_status:
            if _is_gene(gn, lt, pos1, comp_gene):
                if _nonsyn(eff, impact) or (comp_gene in comp_upstream and _upstream(eff)):
                    comp_status[comp_gene] = True
                    detail["comp"][comp_gene].add(_label(comp_gene, pp, eff))
    return r_status, comp_status, detail


def _label(gene, pp, eff):
    """Étiquette lisible et STABLE d'une mutation (sert de clé de comparaison)."""
    if isinstance(pp, int):
        return f"{gene}:{pp}"
    e = " ".join(str(x) for x in eff).lower()
    return f"{gene}:upstream" if "upstream" in e else f"{gene}:?"


def describe(rows, min_nonR=3):
    """Mode --describe : pour CHAQUE isolat resistant, liste les mutations compensatoires
    qui lui sont PROPRES, c'est-a-dire absentes du fond de sa sous-lignee (= presentes chez
    TOUS les non-resistants de la meme sous-lignee).

    Raison d'etre : une lecture descriptive naive (« cet isolat R porte une mutation rpoC donc
    il est compense ») est un FAUX POSITIF quand la mutation est un marqueur de lignee fixe.
    Le test agrege (Mantel-Haenszel) evite ce piege ; cette fonction l'evite AUSSI pour la
    lecture par isolat, qui autrement echappe au garde-fou. Vecu : rpoC Ala172Val/Pro601Leu
    portees par 37/37 genomes L1 (R et non-R) prises a tort pour des compensations."""
    out = []
    by_lin = defaultdict(list)
    for r in rows:
        by_lin[r[1]].append(r)
    for p in PAIRS:
        drug, cg = p["drug"], p["comp"]
        for lin, strains in sorted(by_lin.items()):
            cases = [s for s in strains if s[2].get(drug)]
            controls = [s for s in strains if not s[2].get(drug)]
            if not cases:
                continue
            # fond de clade = mutations candidates presentes chez TOUS les non-cas
            if controls:
                sets = [s[4]["comp"][cg] for s in controls]
                background = set.intersection(*sets) if len(sets) > 1 else set(sets[0])
            else:
                background = set()
            for case in cases:
                sid, det = case[0], case[4]
                total = det["comp"][cg]
                specific = total - background
                out.append({
                    "strain": sid, "lineage": lin, "drug": drug, "comp": cg,
                    "r_mut": ",".join(sorted(set(det["r"][drug]))) or "-",
                    "n_controls": len(controls),
                    "comp_total": ",".join(sorted(total)) or "-",
                    "comp_specific": ",".join(sorted(specific)) or "-",
                    "verdict": ("candidat compensatoire" if specific
                                else ("NON compense (rien hors fond de clade)" if total
                                      else "aucune mutation candidate")),
                    "caveat": ("" if len(controls) >= min_nonR
                               else f"PEU DE TEMOINS ({len(controls)}) : fond de clade mal estime"),
                })
    return out


def load_strains(args):
    """Yield (strain_id, lineage, report_dict)."""
    if args.manifest:
        with open(args.manifest) as f:
            for i, line in enumerate(f):
                line = line.rstrip("\n")
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if i == 0 and parts[0].lower() in ("strain", "sra", "id"):
                    continue
                if len(parts) < 3:
                    continue
                sid, lin, rp = parts[0], parts[1], parts[2]
                try:
                    with open(rp) as g:
                        yield sid, lin, json.load(g)
                except (OSError, json.JSONDecodeError):
                    continue
    elif args.bdd:
        pat = os.path.join(args.bdd, "*", "*", "NC_000962.3", "report.json")
        for rp in glob.glob(pat):
            parts = rp.split(os.sep)
            lin, sid = parts[-4], parts[-3]  # .../<lineage>/<SRA>/NC_000962.3/report.json
            try:
                with open(rp) as g:
                    yield sid, lin, json.load(g)
            except (OSError, json.JSONDecodeError):
                continue
    else:
        sys.exit("Fournir --bdd DIR ou --manifest TSV.")


def mantel_haenszel(strata):
    """strata : liste de (a,b,c,d) 2x2 [[R&comp+, R&comp-],[nonR&comp+, nonR&comp-]].
    Renvoie (OR_MH, chi2_CMH, p, n_strata_informatifs)."""
    num_or = den_or = 0.0
    num_chi = den_chi = 0.0
    n_info = 0
    for (a, b, c, d) in strata:
        n = a + b + c + d
        if n == 0:
            continue
        r1, r2 = a + b, c + d          # R total, nonR total
        c1, c0 = a + c, b + d          # comp+ total, comp- total
        if r1 == 0 or r2 == 0 or c1 == 0 or c0 == 0:
            continue                    # stratum non informatif (marge nulle)
        n_info += 1
        num_or += a * d / n
        den_or += b * c / n
        e_a = r1 * c1 / n
        var_a = (r1 * r2 * c1 * c0) / (n * n * (n - 1)) if n > 1 else 0.0
        num_chi += (a - e_a)
        den_chi += var_a
    or_mh = (num_or / den_or) if den_or > 0 else (float("inf") if num_or > 0 else float("nan"))
    if den_chi > 0:
        chi2 = (abs(num_chi) - 0.5) ** 2 / den_chi   # correction de continuite
        try:
            from scipy.stats import chi2 as chi2dist
            p = float(chi2dist.sf(chi2, 1))
        except ImportError:
            p = math.erfc(math.sqrt(chi2 / 2))
    else:
        chi2, p = float("nan"), float("nan")
    return or_mh, chi2, p, n_info


def main():
    ap = argparse.ArgumentParser(description="Detecteur de compensation/epistasie MTBC (polarise par lignee).")
    ap.add_argument("--bdd", help="Arborescence bdd/actuelle (<lignee>/<SRA>/NC_000962.3/report.json)")
    ap.add_argument("--manifest", help="TSV : strain<tab>lineage<tab>report_path")
    ap.add_argument("--out", default="epistasis_result.tsv", help="TSV de sortie")
    ap.add_argument("--min-per-stratum", type=int, default=4,
                    help="Effectif R minimal par lignee pour compter le stratum (defaut 4)")
    ap.add_argument("--lineage-major", action="store_true",
                    help="Regrouper les sous-lignees par lignee majeure (L1.2.3 -> L1)")
    ap.add_argument("--describe", action="store_true",
                    help="Lecture PAR ISOLAT resistant : mutations candidates PROPRES a l'isolat "
                         "(fond de sous-lignee soustrait). A utiliser des qu'on veut dire "
                         "'cet isolat est compense' -- ne JAMAIS le lire a la main sans ce filtre.")
    args = ap.parse_args()

    rows = []  # (strain, lineage, r_status, comp_status, detail)
    for sid, lin, rep in load_strains(args):
        if args.lineage_major:
            lin = _major(lin)
        r_status, comp_status, detail = classify_strain(rep)
        rows.append((sid, lin, r_status, comp_status, detail))
    if not rows:
        sys.exit("Aucun report.json exploitable.")
    print(f"[mtbc-epistasis] {len(rows)} souches chargees, "
          f"{len({r[1] for r in rows})} lignees.", file=sys.stderr)

    if args.describe:
        desc = describe(rows)
        dpath = args.out.replace(".tsv", "_describe.tsv")
        cols = ["strain", "lineage", "drug", "r_mut", "comp", "n_controls",
                "comp_total", "comp_specific", "verdict", "caveat"]
        with open(dpath, "w") as f:
            f.write("\t".join(cols) + "\n")
            for d in desc:
                f.write("\t".join(str(d[c]) for c in cols) + "\n")
        print("\n=== Lecture PAR ISOLAT (fond de sous-lignee soustrait) ===")
        if not desc:
            print("  aucun isolat resistant dans ce jeu.")
        for d in desc:
            print(f"  {d['strain']} [{d['lineage']}] {d['drug']} ({d['r_mut']}) -> {d['comp']} : "
                  f"total={d['comp_total']} | PROPRE={d['comp_specific']} | {d['verdict']}"
                  + (f" [{d['caveat']}]" if d["caveat"] else ""))
        print(f"  (detail : {dpath})")
        print("  RAPPEL : une mutation presente aussi chez les non-resistants de la meme "
              "sous-lignee est un MARQUEUR DE CLADE, pas une compensation.")

    out_lines = ["pair\tdrug\tr_gene\tcomp\tevidence\tlineage\tR_comp+\tR_comp-\tnonR_comp+\tnonR_comp-\tOR_stratum"]
    summary = []
    for p in PAIRS:
        drug, rg, cg = p["drug"], p["r_gene"], p["comp"]
        by_lin = defaultdict(lambda: [0, 0, 0, 0])  # a,b,c,d
        for row in rows:
            lin, rs, cs = row[1], row[2], row[3]
            R, C = rs.get(drug, False), cs.get(cg, False)
            cell = by_lin[lin]
            if R and C:        cell[0] += 1
            elif R and not C:  cell[1] += 1
            elif (not R) and C: cell[2] += 1
            else:              cell[3] += 1
        strata = []
        for lin, (a, b, c, d) in sorted(by_lin.items()):
            if (a + b) < args.min_per_stratum:
                continue
            strata.append((a, b, c, d))
            out_lines.append(f"{rg}->{cg}\t{drug}\t{rg}\t{cg}\t{p['evidence']}\t{lin}\t{a}\t{b}\t{c}\t{d}\t{_fmt(_or(a,b,c,d))}")
        or_mh, chi2, pval, n_info = mantel_haenszel(strata)
        n_R = sum(s[0] + s[1] for s in strata)
        summary.append({"pair": f"{rg}->{cg}", "drug": drug, "evidence": p["evidence"],
                        "n_strata": n_info, "n_R": n_R, "OR_MH": or_mh, "chi2": chi2, "p": pval})

    with open(args.out, "w") as f:
        f.write("\n".join(out_lines) + "\n")

    print("\n=== mtbc-epistasis : compensation polarisee par lignee ===")
    print(f"{'paire':12} {'drug':5} {'lignees_info':12} {'n_R':>5} {'OR_MH':>8} {'p_CMH':>10}  verdict")
    for s in summary:
        print(f"{s['pair']:12} {s['drug']:5} {s['n_strata']:>12} {s['n_R']:>5} "
              f"{_fmt(s['OR_MH']):>8} {_fmtp(s['p']):>10}  {_verdict(s)}")
    print(f"\nTSV detaille (2x2 par lignee) : {args.out}")
    print("Rappel : OR_MH > 1 avec p_CMH significatif ET verdict != 'confondu' = "
          "compensation soutenue APRES controle de la structure de population.\n"
          "Sinon la co-occurrence brute etait probablement un marqueur de lignee (homoplasie).")


def _major(lin):
    """L1.2.3 -> L1 ; Bovis.2.1 -> Bovis ; garde le 1er token avant '.'."""
    return lin.split(".")[0] if lin else lin


def _or(a, b, c, d):
    if 0 in (a, b, c, d):                      # correction de Haldane
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    return (a * d) / (b * c) if (b * c) else float("inf")


def _verdict(s):
    orr, p, n = s["OR_MH"], s["p"], s["n_strata"]
    if n == 0 or s["n_R"] < 8:
        return "N insuffisant"
    if p != p:  # NaN
        return "non calculable"
    if p < 0.05 and orr > 1.5:
        return "COMPENSATION soutenue (intra-lignee)"
    if p < 0.05 and orr < 0.67:
        return "anti-association (inattendu)"
    if orr > 1.5 and p >= 0.05:
        return "tendance, non significative"
    return "confondu / pas de signal net"


def _fmt(x):
    if x is None or (isinstance(x, float) and x != x):
        return "NA"
    if x == float("inf"):
        return "inf"
    return f"{x:.2f}"


def _fmtp(x):
    if x is None or (isinstance(x, float) and x != x):
        return "NA"
    return f"{x:.1e}" if x < 1e-3 else f"{x:.3f}"


if __name__ == "__main__":
    main()
