#!/usr/bin/env python3
"""Profil de résistance déterministe d'une souche MTBC (baseline catalogue réconcilié).

Outil d'interrogation opérationnel du volet « prédiction » : on lui donne les variants d'une
souche (ou d'une cohorte), il rend, par médicament, un verdict « R » (≥1 déterminant catalogué
R-associé porté) ou « non expliqué par le catalogue », avec les déterminants touchés (gène,
SPDI, grade, source). C'est l'étage DÉTERMINISTE du prédicteur (le ML résiduel reste dans
`phase10_predict.py` du projet) ; sur la plupart des médicaments, à spécificité contrôlée,
c'est l'essentiel du signal.

Entrées — souche unique (sortie détaillée) :
  --spdi FILE      liste de SPDI 0-based (un par ligne ou séparés par des espaces)
  --vcf FILE       VCF H37Rv ; CHROM=NC_000962.3, converti en SPDI 0-based (POS-1)
  --variant HGVS   une mutation unique (ex. katG_p.Ser315Thr), résolue via hgvs_to_spdi

Entrées — cohorte (sortie tableau souche × médicament + résumé) :
  --spdi-dir DIR   un fichier SPDI par souche (nom de fichier = identifiant de la souche)
  --strains FILE   une liste d'identifiants ; SPDI résolus SANS réseau via bdd/actuelle,
                   puis le pangénome local si --pangenome (pan_strains.pkl, volumineux)

Le matching est RÉCONCILIÉ via `variant_match` (SNP exact + décomposition des MNV en SNP
composants + indel exact) : il capte les angles morts de représentation corrigés (le MNV de
la gyrA pour les fluoroquinolones surtout), contrairement à un matching SPDI brut.

Chemins : variable d'environnement RESISTANCE_PROJECT (défaut ~/docs/codes/mtbc/Resistance_antibio).

AVERTISSEMENT : outil de RECHERCHE, pas de diagnostic clinique. Sur des souches réelles,
faire précéder d'un sas qualité (species-id pour écarter un M. kansasii mal étiqueté,
strain-qc). Le catalogue ne couvre que la résistance attribuable à une mutation cible connue.
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from variant_match import parse_spdi, decompose

_PROJECT = Path(os.environ.get("RESISTANCE_PROJECT",
                               Path.home() / "docs/codes/mtbc/Resistance_antibio"))
CATALOGUE_TSV = _PROJECT / "catalogue" / "catalogue_consolide.tsv"
PAN_STRAINS = _PROJECT / "data" / "pangenome" / "pan_strains.pkl"
BDD_ACTUELLE = _PROJECT.parent / "bdd" / "actuelle"

# Ordre d'affichage : 1re ligne, puis fluoroquinolones, injectables, 2e ligne, nouveaux.
DRUG_ORDER = ["isoniazid", "rifampicin", "ethambutol", "pyrazinamide", "streptomycin",
              "moxifloxacin", "levofloxacin", "amikacin", "kanamycin", "capreomycin",
              "ethionamide", "bedaquiline", "clofazimine", "linezolid", "delamanid"]


def _is_snp(spdi):
    _, ref, alt = parse_spdi(spdi)
    return len(ref) == 1 and len(alt) == 1


def load_catalogue(path=None):
    p = Path(path) if path else CATALOGUE_TSV
    if not p.exists():
        sys.exit(f"[resistance_profile] catalogue introuvable : {p}\n"
                 f"  préciser --catalogue, ou définir RESISTANCE_PROJECT.")
    return pd.read_csv(p, sep="\t", dtype=str).fillna("")


def read_spdi_file(path):
    return {s for s in Path(path).read_text().split() if s.startswith("NC_000962.3:")}


def read_vcf(path):
    """VCF H37Rv -> SPDI 0-based. POS 1-based -> position-1 (convention projet).

    Limite : la normalisation des indels du VCF peut différer de celle du catalogue ; le
    match indel est exact, donc un indel à normalisation divergente sera manqué (angle mort
    résiduel documenté). SNP et MNV sont robustes."""
    spdis = set()
    for line in Path(path).read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        f = line.split("\t")
        if len(f) < 5:
            continue
        pos, ref, alt = f[1], f[3], f[4]
        for a in alt.split(","):
            if a in (".", "<NON_REF>", "*"):
                continue
            try:
                spdis.add(f"NC_000962.3:{int(pos) - 1}:{ref}:{a}")
            except ValueError:
                continue
    return spdis


# --- Cœur du matching ------------------------------------------------------

def matched_determinants(strain_spdis, det, snp_det=None):
    """{SPDI déterminant catalogué touché -> mode}, réconcilié (SNP/MNV/indel).

    `mode` = 'exact' ou 'MNV' (déterminant atteint via décomposition d'un variant
    multi-nucléotidique observé). `snp_det` peut être pré-calculé (mode batch)."""
    if snp_det is None:
        snp_det = {s for s in det if _is_snp(s)}
    matched = {}
    for s in strain_spdis:
        try:
            _, ref, alt = parse_spdi(s)
        except Exception:
            continue
        if len(ref) == len(alt):                       # SNP ou MNV substitution
            if s in det:
                matched[s] = "exact"
            multibase = len(ref) > 1
            for comp in decompose(s):
                if comp in snp_det:
                    matched.setdefault(comp, "MNV" if multibase else "exact")
        else:                                          # indel
            if s in det:
                matched[s] = "exact"
    return matched


def build_det_index(cat):
    """Pré-calcul partagé pour le batch : (det, snp_det, spdi->{drugs}, drugs ordonnés)."""
    rdf = cat[(cat["call"] == "R-associated") & (cat["spdi"] != "")]
    det = set(rdf["spdi"])
    snp_det = {s for s in det if _is_snp(s)}
    spdi2drugs = defaultdict(set)
    for spdi, drug in zip(rdf["spdi"], rdf["drug"]):
        spdi2drugs[spdi].add(drug)
    drugs = sorted(rdf["drug"].unique())
    ordered = [d for d in DRUG_ORDER if d in drugs] + [d for d in drugs if d not in DRUG_ORDER]
    return det, snp_det, spdi2drugs, ordered


def profile(strain_spdis, cat):
    """Souche unique -> {drug -> {verdict, determinants:[{gene,variant,spdi,grade,source,match}]}}."""
    rdf = cat[(cat["call"] == "R-associated") & (cat["spdi"] != "")]
    det = set(rdf["spdi"])
    matched = matched_determinants(strain_spdis, det)
    hit_rows = rdf[rdf["spdi"].isin(matched.keys())]
    out = {}
    for drug in sorted(rdf["drug"].unique()):
        drows = hit_rows[hit_rows["drug"] == drug].drop_duplicates("spdi")
        dets = [{"gene": r.gene, "variant": r.variant, "spdi": r.spdi,
                 "grade": r.source_grade, "source": r.source, "match": matched[r.spdi]}
                for r in drows.itertuples()]
        out[drug] = {"verdict": "R" if dets else "non expliqué",
                     "determinants": sorted(dets, key=lambda d: d["spdi"])}
    return out


# --- Cohorte (batch) -------------------------------------------------------

def load_spdi_dir(d):
    out = {}
    for f in sorted(Path(d).iterdir()):
        if f.is_file():
            sp = read_spdi_file(f)
            if sp:
                out[f.stem] = sp
    return out, []


def resolve_strains(ids, use_pangenome=False):
    """Cascade SANS réseau : pangénome local (si --pangenome) puis bdd/actuelle/.../spdi.txt."""
    pan = None
    if use_pangenome and PAN_STRAINS.exists():
        import pickle
        with open(PAN_STRAINS, "rb") as fh:
            pan = pickle.load(fh)
    out, missing = {}, []
    for sid in ids:
        if pan is not None and sid in pan:
            out[sid] = set(pan[sid])
            continue
        hits = list(BDD_ACTUELLE.glob(f"*/{sid}/NC_000962.3/spdi.txt"))
        if hits:
            out[sid] = read_spdi_file(hits[0])
        else:
            missing.append(sid)
    return out, missing


def batch_table(strain_map, cat):
    """{strain_id -> set(SPDI)} -> (DataFrame souche×médicament 'R'/'.', drugs ordonnés)."""
    det, snp_det, spdi2drugs, drugs = build_det_index(cat)
    records = {}
    for sid, sp in strain_map.items():
        matched = matched_determinants(sp, det, snp_det)
        rdrugs = set()
        for s in matched:
            rdrugs |= spdi2drugs.get(s, set())
        records[sid] = {d: ("R" if d in rdrugs else ".") for d in drugs}
    df = pd.DataFrame.from_dict(records, orient="index", columns=drugs)
    df.index.name = "strain_id"
    return df, drugs


def batch_summary(df, missing):
    n = len(df)
    lines = [f"# Profil de résistance — cohorte ({n} souches profilées"
             + (f", {len(missing)} non résolues" if missing else "") + ")",
             "# Verdict 'R' = ≥1 déterminant catalogué R-associé (réconcilié). "
             "'.' = non expliqué par le catalogue.",
             "# AVERTISSEMENT : recherche, pas de diagnostic clinique.", ""]
    if n:
        rate = (df == "R").mean().sort_values(ascending=False)
        lines.append("Taux de résistance prédite par médicament :")
        for d, r in rate.items():
            if r > 0:
                lines.append(f"  {d:16s} {100 * r:5.1f}%  ({int((df[d] == 'R').sum())}/{n})")
        has = lambda d: d in df.columns
        mdr = ((df.get("isoniazid") == "R") & (df.get("rifampicin") == "R")) \
            if has("isoniazid") and has("rifampicin") else None
        if mdr is not None:
            fq = pd.Series(False, index=df.index)
            for d in ("moxifloxacin", "levofloxacin"):
                if has(d):
                    fq = fq | (df[d] == "R")
            prexdr = mdr & fq
            lines += ["", f"MDR (INH + RIF)          : {int(mdr.sum())} ({100*mdr.mean():.1f}%)",
                      f"pré-XDR (MDR + FQ)       : {int(prexdr.sum())} ({100*prexdr.mean():.1f}%)"]
    if missing:
        lines += ["", f"Non résolues ({len(missing)}) : "
                  + ", ".join(missing[:10]) + (" ..." if len(missing) > 10 else "")]
    return "\n".join(lines)


# --- Rendu souche unique ---------------------------------------------------

def render_text(prof, n_in):
    lines = ["# Profil de résistance — baseline catalogue réconcilié (variant_match)",
             f"# Entrée : {n_in} variants (SPDI)",
             "# AVERTISSEMENT : outil de recherche, pas de diagnostic clinique.", ""]
    res = {d: v for d, v in prof.items() if v["verdict"] == "R"}
    sen = sorted(d for d, v in prof.items() if v["verdict"] != "R")
    lines.append(f"RÉSISTANCES PRÉDITES ({len(res)} médicaments) :")
    if not res:
        lines.append("  (aucune — aucun déterminant catalogué R porté)")
    for drug in sorted(res):
        for i, d in enumerate(res[drug]["determinants"]):
            tag = "  [via MNV décomposé]" if d["match"] == "MNV" else ""
            head = f"{drug:16s}" if i == 0 else " " * 16
            grade = f"{d['source']}:{d['grade']}".strip(":")
            lines.append(f"  {head}{d['gene']} {d['variant']}  {d['spdi']}  [{grade}]{tag}")
    lines.append("")
    lines.append(f"NON EXPLIQUÉ PAR LE CATALOGUE ({len(sen)} médicaments) :")
    lines.append("  " + ", ".join(sen))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--spdi", help="souche unique : fichier de SPDI")
    g.add_argument("--vcf", help="souche unique : VCF H37Rv")
    g.add_argument("--variant", help="souche unique : une mutation HGVS")
    g.add_argument("--spdi-dir", dest="spdi_dir", help="cohorte : répertoire de fichiers SPDI")
    g.add_argument("--strains", help="cohorte : liste d'identifiants de souches")
    ap.add_argument("--pangenome", action="store_true",
                    help="(--strains) résoudre aussi via le pangénome local (volumineux)")
    ap.add_argument("--out", help="(cohorte) écrire le tableau TSV ici")
    ap.add_argument("--catalogue", help="catalogue_consolide.tsv (sinon défaut RESISTANCE_PROJECT)")
    ap.add_argument("--json", action="store_true", help="sortie JSON structurée")
    a = ap.parse_args()
    cat = load_catalogue(a.catalogue)

    # --- cohorte ---
    if a.spdi_dir or a.strains:
        if a.spdi_dir:
            strain_map, missing = load_spdi_dir(a.spdi_dir)
        else:
            ids = [x for x in Path(a.strains).read_text().split() if x]
            strain_map, missing = resolve_strains(ids, a.pangenome)
        if not strain_map:
            sys.exit("[resistance_profile] aucune souche résolue.")
        df, drugs = batch_table(strain_map, cat)
        if a.json:
            print(json.dumps({"n_strains": len(df), "missing": missing,
                              "table": df.reset_index().to_dict(orient="records")},
                             ensure_ascii=False, indent=2))
        else:
            print(batch_summary(df, missing))
            if a.out:
                df.to_csv(a.out, sep="\t")
                print(f"\nTableau complet écrit : {a.out}")
            else:
                print("\n" + df.reset_index().to_string(index=False))
        return

    # --- souche unique ---
    if a.spdi:
        strain = read_spdi_file(a.spdi)
    elif a.vcf:
        strain = read_vcf(a.vcf)
    else:
        # mutation unique : représentation canonique mono-base (resolve), pour ne pas faire
        # apparaître des codons voisins via les formes MNV de resolve_all. Fallback
        # toutes-représentations seulement si non résolu en mono-base (indels).
        from hgvs_to_spdi import resolve, resolve_all
        s = resolve(a.variant)
        strain = {s} if s else set(resolve_all(a.variant))
        if not strain:
            sys.exit(f"[resistance_profile] variant non résolu en SPDI : {a.variant}")

    prof = profile(strain, cat)
    if a.json:
        print(json.dumps({"n_input": len(strain), "profile": prof},
                         ensure_ascii=False, indent=2))
    else:
        print(render_text(prof, len(strain)))
        if a.variant:
            print(f"\n# Explication mécanistique (resistance-catalogue, mode 4) : explain_mutation.py "
                  f"--variant {a.variant}")


if __name__ == "__main__":
    main()
