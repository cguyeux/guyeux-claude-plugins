#!/usr/bin/env python3
"""
RD crosscheck : notre chaine (TBannotator) contre RDscan, souche par souche

Format RDscan verifie sur le SOURCE du depot (dbespiatykh/RDscan, commit f7e2d91, 2026-08-17 --
workflow/scripts/makeTables.R, proportions.py, concatenate_bed.py, resources/RD.bed), pas suppose :
RDscan ne produit PAS une table longue par RD, mais deux matrices LARGES cohort-wide.

  RD connues (mode "known") : RD_known.bin.tsv -- une ligne par ECHANTILLON (colonne Sample),
      une colonne par nom de RD (RD9, RD105, RD750, ... les noms de resources/RD.bed), valeur
      0/1 (1 = profondeur relative <= seuil = deletion appelee). Pas de coordonnees dans ce
      fichier : les bornes des RD connues sont fixes, definies une fois pour toutes dans RD.bed,
      donc AUCUNE comparaison de bornes n'est possible ni pertinente dans ce mode.

  RD candidates (mode "putative") : RD_putative.tsv -- une ligne par deletion candidate detectee
      dans la cohorte (CHROM, START, END, SIZE, RD, TYPE), puis une colonne par echantillon dont
      la valeur est la taille de deletion chez cet echantillon (vide si absente). C'est le
      pendant de nos CUS_GS_<start>_<end> : la comparaison de bornes s'applique ici.

Le protocole SKILL.md est un recoupement souche par souche sur un jeu temoin, pas un batch aveugle
sur toute la cohorte : --sample selectionne une souche a la fois dans les deux tables.

Usage:
    # RD connues (RD9, RD105, RD750...) sur le jeu temoin
    python3 crosscheck_rdscan.py known coverage_report_rd.bed.tsv RD_known.bin.tsv \\
        --sample SRR12345678 --witness RD9,RD105,RD750

    # RD candidates (CUS) contre RD_putative.tsv
    python3 crosscheck_rdscan.py putative coverage_report_dynamic_rd.bed.tsv RD_putative.tsv \\
        --sample SRR12345678 --margin 100

CALCUL DE L'APPEL COTE "OURS" : coverage_report_{rd,dynamic_rd}.bed.tsv NE PORTE PAS de colonne
booleenne presence/absence -- seulement les mesures brutes (quality, low_coverage, mean_ratio,
other...). L'appel binaire est un OU de conditions, verifie en lisant `scripts/json_report.py` du
pipeline sur mp:/data/current/run/ le 2026-08-17 (pas suppose) :
  - RD connues   : quality > 0.8  OU  low_coverage > 0.95  OU  mean_ratio < 0.1
  - RD candidates (CUS/dynamic) : quality > 0.8 UNIQUEMENT (pas de repli couverture, plus exigeant)
Ce script calcule cet appel lui-meme par defaut (--rd-type known|dynamic) ; ne pas lui donner une
colonne "call" qui n'existe pas dans le fichier reel.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

OURS_COL_CANDIDATES = {
    "name": ["rd_name", "rd", "name", "id"],
    "start": ["start", "begin"],
    "end": ["end", "stop"],
    "quality": ["quality"],
    "low_coverage": ["low_coverage"],
    "mean_ratio": ["mean_ratio"],
}

RD_TYPE_THRESHOLDS = {
    "known": lambda q, lc, mr: (q > 0.8) | (lc > 0.95) | (mr < 0.1),
    "dynamic": lambda q, lc, mr: q > 0.8,
}


def parse_col_override(spec):
    """--ours-cols name=RD_name,call=Deleted -> dict"""
    out = {}
    if not spec:
        return out
    for pair in spec.split(","):
        key, _, val = pair.partition("=")
        if not val:
            raise ValueError(f"override mal forme (attendu cle=valeur) : {pair!r}")
        out[key.strip()] = val.strip()
    return out


def resolve_columns(df, candidates, overrides, required):
    resolved = {}
    lower_map = {c.lower(): c for c in df.columns}
    for field in required:
        if field in overrides:
            if overrides[field] not in df.columns:
                raise ValueError(
                    f"colonne '{overrides[field]}' (override pour '{field}') absente : {list(df.columns)}"
                )
            resolved[field] = overrides[field]
            continue
        for cand in candidates.get(field, []):
            if cand in df.columns:
                resolved[field] = cand
                break
            if cand.lower() in lower_map:
                resolved[field] = lower_map[cand.lower()]
                break
        if field not in resolved:
            raise ValueError(
                f"impossible de deviner la colonne '{field}' parmi {list(df.columns)} ; "
                f"utiliser --ours-cols pour la preciser"
            )
    return resolved


def truthy_call(value):
    """Normalise une colonne 'call' heterogene (bool, 0/1, present/absent, deleted/intact...) en bool."""
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    s = str(value).strip().lower()
    return s in {"1", "true", "yes", "present", "deleted", "deletion", "absent_ref", "rd"}


def load_ours(path, need_coords, rd_type, overrides):
    df = pd.read_csv(path, sep=None, engine="python")
    required = ["name", "quality", "low_coverage", "mean_ratio"] + (["start", "end"] if need_coords else [])
    cols = resolve_columns(df, OURS_COL_CANDIDATES, overrides, required)
    quality = pd.to_numeric(df[cols["quality"]], errors="coerce")
    low_coverage = pd.to_numeric(df[cols["low_coverage"]], errors="coerce")
    mean_ratio = pd.to_numeric(df[cols["mean_ratio"]], errors="coerce")
    out = {
        "name": df[cols["name"]].astype(str),
        "call": RD_TYPE_THRESHOLDS[rd_type](quality, low_coverage, mean_ratio).fillna(False),
    }
    if need_coords:
        out["start"] = pd.to_numeric(df[cols["start"]], errors="coerce")
        out["end"] = pd.to_numeric(df[cols["end"]], errors="coerce")
    return pd.DataFrame(out)


def find_sample_column(df, hint=None):
    for cand in (["Sample", "sample", "sample_id", "SRA", "strain"] if not hint else [hint]):
        if cand in df.columns:
            return cand
    raise ValueError(f"colonne Sample introuvable parmi {list(df.columns)} (essayer --sample-col)")


def run_known(args):
    ours = load_ours(args.ours, need_coords=False, rd_type=args.rd_type, overrides=parse_col_override(args.ours_cols))
    wide = pd.read_csv(args.rdscan, sep="\t")
    sample_col = find_sample_column(wide, args.sample_col)
    row = wide[wide[sample_col].astype(str) == args.sample]
    if row.empty:
        sys.exit(
            f"echantillon '{args.sample}' absent de {args.rdscan} (colonne {sample_col!r}) ; "
            f"valeurs disponibles : {sorted(wide[sample_col].astype(str).unique())[:10]}..."
        )
    row = row.iloc[0]
    rd_columns = [c for c in wide.columns if c != sample_col]
    rdscan_calls = {rd: truthy_call(row[rd]) for rd in rd_columns}

    rows = []
    for _, o in ours.iterrows():
        if o["name"] in rdscan_calls:
            rd_call = rdscan_calls.pop(o["name"])
            verdict = "concordant" if o["call"] == rd_call else "desaccord_call"
            rows.append(dict(rd=o["name"], our_call=o["call"], rdscan_call=rd_call, verdict=verdict))
        else:
            rows.append(dict(rd=o["name"], our_call=o["call"], rdscan_call=None, verdict="nous_seuls"))
    for rd, rd_call in rdscan_calls.items():
        rows.append(dict(rd=rd, our_call=None, rdscan_call=rd_call, verdict="rdscan_seul_hors_notre_liste"))

    result = pd.DataFrame(rows)
    print(f"\n=== Souche {args.sample} : accord chiffre sur les RD connues ===")
    concordant = (result["verdict"] == "concordant").sum()
    testable = result["verdict"].isin(["concordant", "desaccord_call"]).sum()
    print(f"{concordant}/{testable} concordantes (sur les RD que les deux methodes evaluent)")
    print(result["verdict"].value_counts().to_string())

    extra = result[result["verdict"] == "rdscan_seul_hors_notre_liste"]
    if len(extra):
        print(
            f"\n[info] {len(extra)} RD de resources/RD.bed evaluees par RDscan et absentes de notre "
            f"table (RD non testees par notre chaine, pas un desaccord) : {extra['rd'].tolist()}"
        )

    disagree = result[result["verdict"] == "desaccord_call"]
    if len(disagree):
        print(f"\n[attention] {len(disagree)} desaccords d'appel a documenter au cahier de labo :")
        print(disagree[["rd", "our_call", "rdscan_call"]].to_string(index=False))

    if args.witness:
        wanted = set(w.strip() for w in args.witness.split(","))
        missing = wanted - set(result["rd"])
        print(f"\n=== Jeu temoin ({len(wanted)} RD attendues) ===")
        if missing:
            print(f"[avertissement] absentes du recoupement : {sorted(missing)}")
        else:
            print("toutes les RD temoins sont presentes dans le recoupement")

    if args.output:
        result.to_csv(args.output, sep="\t", index=False)
        print(f"\nTableau detaille ecrit dans {args.output}")


def run_putative(args):
    ours = load_ours(args.ours, need_coords=True, rd_type=args.rd_type, overrides=parse_col_override(args.ours_cols))
    ours = ours[ours["call"]]

    wide = pd.read_csv(args.rdscan, sep="\t")
    for col in ("CHROM", "START", "END"):
        if col not in wide.columns:
            raise ValueError(f"colonne '{col}' absente de {args.rdscan} : {list(wide.columns)}")
    if args.sample not in wide.columns:
        candidates = [c for c in wide.columns if c not in ("CHROM", "START", "END", "SIZE", "RD", "TYPE")]
        sys.exit(f"echantillon '{args.sample}' absent des colonnes de {args.rdscan} ; disponibles : {candidates[:10]}...")

    detected = wide[wide[args.sample].notna()].copy()
    detected["name"] = detected.get("RD", pd.Series(dtype=str)).fillna("").astype(str)
    detected.loc[detected["name"] == "", "name"] = (
        "putative_" + detected["START"].astype(str) + "_" + detected["END"].astype(str)
    )
    theirs = pd.DataFrame(
        {
            "name": detected["name"],
            "start": pd.to_numeric(detected["START"], errors="coerce"),
            "end": pd.to_numeric(detected["END"], errors="coerce"),
        }
    )

    matched_theirs_idx = set()
    rows = []
    for _, o in ours.iterrows():
        overlap = theirs[(theirs["start"] <= o["end"] + args.margin) & (theirs["end"] >= o["start"] - args.margin)]
        overlap = overlap[~overlap.index.isin(matched_theirs_idx)]
        if len(overlap):
            best = overlap.iloc[(overlap["start"] - o["start"]).abs().argsort().iloc[0]]
            matched_theirs_idx.add(best.name)
            border_delta = max(abs(o["start"] - best["start"]), abs(o["end"] - best["end"]))
            verdict = "concordant" if border_delta <= args.margin else "concordant_bornes_divergentes"
            rows.append(dict(rd=o["name"], rdscan_rd=best["name"], border_delta=border_delta, verdict=verdict))
        else:
            rows.append(dict(rd=o["name"], rdscan_rd=None, border_delta=None, verdict="nous_seuls"))
    for idx, t in theirs.iterrows():
        if idx not in matched_theirs_idx:
            rows.append(dict(rd=None, rdscan_rd=t["name"], border_delta=None, verdict="rdscan_seul"))

    result = pd.DataFrame(rows)
    print(f"\n=== Souche {args.sample} : accord chiffre sur les RD candidates (CUS vs putatives) ===")
    print(result["verdict"].value_counts().to_string())
    only_rdscan = result[result["verdict"] == "rdscan_seul"]
    if len(only_rdscan):
        print(
            f"\n[attention] {len(only_rdscan)} deletions candidates vues par RDscan et absentes de nos "
            f"CUS (defaut de sensibilite possible) : {only_rdscan['rdscan_rd'].tolist()}"
        )

    if args.output:
        result.to_csv(args.output, sep="\t", index=False)
        print(f"\nTableau detaille ecrit dans {args.output}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="mode", required=True)

    known = sub.add_parser("known", help="RD connues : coverage_report_rd.bed.tsv vs RD_known.bin.tsv")
    known.add_argument("ours", type=Path)
    known.add_argument("rdscan", type=Path)
    known.add_argument("--sample", required=True, help="identifiant d'echantillon (colonne Sample de RDscan)")
    known.add_argument("--sample-col", help="nom de la colonne Sample si different du defaut")
    known.add_argument("--witness", help="RD temoins attendues, separees par des virgules")
    known.add_argument("--rd-type", choices=["known", "dynamic"], default="known",
                        help="formule de seuil pour l'appel (defaut: known = OU quality/low_coverage/mean_ratio)")
    known.add_argument("--ours-cols", help="override colonnes ours, ex: name=RD_name,quality=Q,low_coverage=LC,mean_ratio=MR")
    known.add_argument("-o", "--output", type=Path)
    known.set_defaults(func=run_known)

    putative = sub.add_parser("putative", help="RD candidates : CUS vs RD_putative.tsv")
    putative.add_argument("ours", type=Path)
    putative.add_argument("rdscan", type=Path)
    putative.add_argument("--sample", required=True, help="nom de colonne echantillon dans RD_putative.tsv")
    putative.add_argument("--margin", type=int, default=100, help="marge de bornes en pb (defaut 100)")
    putative.add_argument("--rd-type", choices=["known", "dynamic"], default="dynamic",
                           help="formule de seuil pour l'appel (defaut: dynamic = quality > 0.8 seul, cf CUS)")
    putative.add_argument("--ours-cols", help="override colonnes ours, ex: name=CUS,start=Start,end=End,quality=Q,low_coverage=LC,mean_ratio=MR")
    putative.add_argument("-o", "--output", type=Path)
    putative.set_defaults(func=run_putative)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
