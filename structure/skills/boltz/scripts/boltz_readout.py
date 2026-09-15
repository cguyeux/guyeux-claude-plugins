#!/usr/bin/env python3
"""
Objet: lecture normalisee d'un lot de predictions Boltz-2 de COMPLEXE, appliquant
    mecaniquement les mesures que le garde-fou n0 du skill `boltz` prescrit et
    qu'un coup d'oeil au JSON de confiance ne donne pas : profondeur du MSA
    APPARIE par paire, dispersion des scores entre echantillons de diffusion,
    ptm PROPRE et PAE INTRA-chaine de chaque partenaire, localisation de
    l'interface predite, et alerte automatique quand deux jobs qu'on s'apprete a
    classer n'ont pas des MSA apparies comparables.
Entrees: un ou plusieurs repertoires de sortie Boltz (`boltz_results_<job>` ou
    `out_<job>`, ou un parent qui en contient plusieurs). Aucune dependance hors
    numpy.
Sorties: TSV sur stdout (une ligne par job) et, avec --markdown, un tableau
    Markdown pret a coller dans un registre de projet.
Reutilisable: OUI, generique -- tout criblage d'interaction par co-repliement du
    depot. Ne rien y coder de specifique a un projet.
Projet: skill bio_pathogens:boltz (ne pour mtbc/Rv0007 P5.2, 2026-09-03)
Date: 2026-09-03

POURQUOI CE SCRIPT EXISTE
--------------------------
Un manuscrit entier a ete redige dans `mtbc/Rv0007` sur un classement de
partenaires produit a --diffusion_samples 1, sans que personne mesure que les
deux paires comparees avaient des MSA apparies de 12 et 714 lignes. Les trois
mesures qui auraient arrete cela (profondeur appariee, dispersion entre
echantillons, ptm propre du partenaire) existaient toutes dans les fichiers de
sortie ; aucune n'etait lue. Ce script les lit toutes, systematiquement.

LE PIEGE DU COMPTAGE DE PROFONDEUR (mesure a la main le 2026-09-03)
--------------------------------------------------------------------
`pair.a3m` n'est PAS un FASTA ordinaire et `grep -c '^>'` y donne un faux compte,
pour deux raisons cumulees :
  1. le fichier concatene UN BLOC PAR CHAINE, separes par un octet NUL ; le total
     des en-tetes melange donc les deux chaines et les deux requetes ;
  2. cet octet NUL fait basculer grep en mode binaire, ou son comptage de lignes
     differe (mesure : 1430 en mode binaire contre 1429 avec -a, sur un fichier
     dont le vrai nombre d'en-tetes est 1430).
La profondeur APPARIEE d'une paire est le nombre de lignes appariees, c'est-a-dire
`en-tetes du bloc - 1` (la requete), et elle est IDENTIQUE pour les deux blocs par
construction de l'appariement. C'est ce nombre, et lui seul, qui mesure la
contrainte de coevolution disponible pour l'interface.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

MSA_RATIO_ALERT = 3.0  # facteur au-dela duquel un classement n'est plus lisible


# --------------------------------------------------------------------------- #
# Reperage des sorties
# --------------------------------------------------------------------------- #
def find_jobs(roots: list[str]) -> dict[str, str]:
    """job -> repertoire `predictions/<job>`. Tolere les dispositions locale
    (`boltz_results_<job>/predictions/<job>`) et Slurm (`out_<job>/boltz_results_
    <job>/predictions/<job>`), et un parent qui contient plusieurs jobs."""
    found: dict[str, str] = {}
    for root in roots:
        for dirpath, dirnames, _ in os.walk(root):
            if os.path.basename(dirpath) != "predictions":
                continue
            for job in dirnames:
                d = os.path.join(dirpath, job)
                if any(f.startswith("confidence_") for f in os.listdir(d)):
                    found[job] = d
    return dict(sorted(found.items()))


def msa_dir_of(pred_dir: str) -> str | None:
    """Le repertoire msa/ est frere de predictions/, sous boltz_results_<job>."""
    cand = os.path.join(os.path.dirname(os.path.dirname(pred_dir)), "msa")
    return cand if os.path.isdir(cand) else None


# --------------------------------------------------------------------------- #
# Profondeur des MSA
# --------------------------------------------------------------------------- #
def paired_depth(msa_dir: str | None) -> tuple[int | None, list[int]]:
    """(profondeur appariee, en-tetes par bloc). Voir l'en-tete du module : on
    decoupe sur l'octet NUL, un bloc par chaine, et on retranche la requete."""
    if not msa_dir:
        return None, []
    pair = None
    for dp, _, fn in os.walk(msa_dir):
        if "pair.a3m" in fn:
            pair = os.path.join(dp, "pair.a3m")
            break
    if pair is None:
        return None, []
    raw = open(pair, "rb").read()
    per_block = []
    for blk in raw.split(b"\x00"):
        n = sum(1 for line in blk.decode("utf-8", "replace").split("\n")
                if line.startswith(">"))
        if n:
            per_block.append(n)
    if not per_block:
        return 0, []
    # identique par construction ; on prend le minimum, qui est la contrainte reelle
    return min(per_block) - 1, per_block


def unpaired_depths(msa_dir: str | None) -> list[int]:
    """Profondeur du MSA NON apparie de chaque chaine (contexte : une chaine peut
    etre bien couverte seule et n'avoir presque aucun partenaire appariable)."""
    if not msa_dir:
        return []
    out = []
    for name in sorted(os.listdir(msa_dir)):
        if not name.endswith(".csv"):
            continue
        with open(os.path.join(msa_dir, name)) as fh:
            out.append(max(0, sum(1 for _ in fh) - 1))  # -1 = en-tete CSV
    return out


# --------------------------------------------------------------------------- #
# Longueurs de chaine, depuis la structure (aucune dependance a l'entree YAML)
# --------------------------------------------------------------------------- #
def _atom_site(path: str):
    """Rend (colonnes, lignes) de la boucle _atom_site d'un mmCIF Boltz."""
    cols: dict[str, int] = {}
    rows: list[list[str]] = []
    in_loop = False
    with open(path) as fh:
        for line in fh:
            s = line.strip()
            if s.startswith("_atom_site."):
                cols[s.split(".", 1)[1]] = len(cols)
                in_loop = True
                continue
            if in_loop:
                if s.startswith("#") or not s:
                    break
                f = s.split()
                if len(f) >= len(cols):
                    rows.append(f)
    return cols, rows


def chain_lengths_from_cif(path: str) -> list[int]:
    cols, rows = _atom_site(path)
    ch_i = cols.get("label_asym_id", 6)
    sq_i = cols.get("label_seq_id", 8)
    lengths: dict[str, set] = {}
    for f in rows:
        lengths.setdefault(f[ch_i], set()).add(f[sq_i])
    return [len(lengths[c]) for c in sorted(lengths)]


def interface_residues(path: str, cutoff: float = 8.0) -> dict[str, set[int]]:
    """Residus au contact entre les DEUX premieres chaines (tout atome a moins de
    `cutoff` A). Implemente le corollaire 3 du garde-fou n0 : deux bras qui docquent
    sur le MEME site n'ont aucune specificite, quel que soit leur score."""
    cols, rows = _atom_site(path)
    ch_i, sq_i = cols.get("label_asym_id", 6), cols.get("label_seq_id", 8)
    x_i = cols.get("Cartn_x", 10)
    coords: dict[str, list[tuple[int, float, float, float]]] = {}
    for f in rows:
        try:
            coords.setdefault(f[ch_i], []).append(
                (int(f[sq_i]), float(f[x_i]), float(f[x_i + 1]), float(f[x_i + 2])))
        except (ValueError, IndexError):
            continue
    chains = sorted(coords)
    if len(chains) < 2:
        return {}
    a = np.array([[x, y, z] for _, x, y, z in coords[chains[0]]])
    b = np.array([[x, y, z] for _, x, y, z in coords[chains[1]]])
    ra = np.array([r for r, *_ in coords[chains[0]]])
    rb = np.array([r for r, *_ in coords[chains[1]]])
    d = np.linalg.norm(a[:, None, :] - b[None, :, :], axis=-1)
    hit = d < cutoff
    return {"A": set(int(v) for v in np.unique(ra[hit.any(axis=1)])),
            "B": set(int(v) for v in np.unique(rb[hit.any(axis=0)]))}


# --------------------------------------------------------------------------- #
# PAE
# --------------------------------------------------------------------------- #
def pae_stats(npz_path: str, la: int, lb: int) -> dict | None:
    d = np.load(npz_path)
    pae = d[list(d.keys())[0]]
    if pae.ndim == 3:
        pae = pae[0]
    if la + lb != pae.shape[0]:
        return None  # jamais rendre un chiffre faux : cf. skill, section tokenisation
    ab, ba = pae[:la, la:], pae[la:, :la]
    inter_min = float(min(ab.min(), ba.min()))
    i, j = np.unravel_index(int(np.argmin(ab)), ab.shape)
    return {
        "pae_inter_min": inter_min,
        "pae_inter_mean": float((ab.mean() + ba.mean()) / 2),
        "pae_intra_a": float(pae[:la, :la].mean()),
        "pae_intra_b": float(pae[la:, la:].mean()),
        "argmin_res_a": int(i) + 1,
        "argmin_res_b": int(j) + 1,
        "n_cells": int(ab.size + ba.size),
    }


def mean_sd(xs: list[float]) -> tuple[float, float]:
    if not xs:
        return math.nan, math.nan
    m = sum(xs) / len(xs)
    if len(xs) == 1:
        return m, 0.0
    return m, math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


# --------------------------------------------------------------------------- #
def read_job(job: str, pred_dir: str) -> dict:
    models = sorted(f for f in os.listdir(pred_dir) if f.startswith("confidence_"))
    cifs = sorted(f for f in os.listdir(pred_dir) if f.endswith(".cif"))
    lens = chain_lengths_from_cif(os.path.join(pred_dir, cifs[0])) if cifs else []
    la, lb = (lens + [0, 0])[:2]

    per_model = []
    for m in models:
        conf = json.load(open(os.path.join(pred_dir, m)))
        tag = m[len("confidence_"):-len(".json")]
        npz = os.path.join(pred_dir, f"pae_{tag}.npz")
        row = {
            "iptm": conf.get("iptm"),
            "ptm": conf.get("ptm"),
            "complex_plddt": conf.get("complex_plddt"),
            "chain_ptm_a": (conf.get("chains_ptm") or {}).get("0"),
            "chain_ptm_b": (conf.get("chains_ptm") or {}).get("1"),
        }
        if os.path.exists(npz):
            st = pae_stats(npz, la, lb)
            if st:
                row.update(st)
        per_model.append(row)

    msa_dir = msa_dir_of(pred_dir)
    depth, blocks = paired_depth(msa_dir)
    out = {"job": job, "n_models": len(per_model), "len_a": la, "len_b": lb,
           "msa_paired": depth, "msa_blocks": blocks,
           "msa_unpaired": unpaired_depths(msa_dir)}
    for key in ("iptm", "complex_plddt", "pae_inter_min", "pae_inter_mean",
                "pae_intra_a", "pae_intra_b", "chain_ptm_a", "chain_ptm_b"):
        vals = [r[key] for r in per_model if r.get(key) is not None]
        m, sd = mean_sd(vals)
        out[key] = m
        out[key + "_sd"] = sd
        if key in ("iptm", "pae_inter_min"):
            out[key + "_min"] = min(vals) if vals else math.nan
            out[key + "_max"] = max(vals) if vals else math.nan
    best = min((r for r in per_model if "argmin_res_a" in r),
               key=lambda r: r["pae_inter_min"], default=None)
    out["interface_argmin"] = (f"A{best['argmin_res_a']}-B{best['argmin_res_b']}"
                               if best else "")
    out["pae_n_cells"] = best["n_cells"] if best else 0

    # Corollaire 3 : le CŒUR de l'interface, seul comparable entre deux jobs. Un
    # simple union a 8 A sur des modeles peu confiants renvoie la chaine entiere et
    # ne discrimine rien ; on retient les residus a moins de 5 A dans la MAJORITE
    # des echantillons de diffusion, ce qui exige en plus que le site soit stable.
    counts = {"A": {}, "B": {}}
    for c in cifs:
        for k, v in interface_residues(os.path.join(pred_dir, c), cutoff=5.0).items():
            for r in v:
                counts[k][r] = counts[k].get(r, 0) + 1
    need = max(1, len(cifs) // 2 + 1)
    for k in ("A", "B"):
        core = sorted(r for r, n in counts[k].items() if n >= need)
        out[f"iface_{k.lower()}"] = core
        out[f"iface_{k.lower()}_span"] = f"{min(core)}-{max(core)}" if core else ""
        out[f"iface_{k.lower()}_n"] = len(core)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="lecture normalisee d'un lot de "
                                             "predictions Boltz-2 de complexe")
    ap.add_argument("dirs", nargs="+", help="repertoires de sortie Boltz (ou leur parent)")
    ap.add_argument("--markdown", action="store_true", help="tableau Markdown au lieu du TSV")
    ap.add_argument("--msa-ratio-alert", type=float, default=MSA_RATIO_ALERT)
    args = ap.parse_args()

    jobs = find_jobs(args.dirs)
    if not jobs:
        sys.exit("aucune prediction Boltz trouvee sous " + " ".join(args.dirs))
    rows = [read_job(j, d) for j, d in jobs.items()]

    cols = ["job", "n_models", "len_a", "len_b", "msa_paired", "iptm", "iptm_sd",
            "pae_inter_min", "pae_inter_min_sd", "pae_inter_min_min",
            "pae_inter_min_max", "pae_inter_mean", "pae_inter_mean_sd",
            "complex_plddt", "chain_ptm_a", "chain_ptm_b", "pae_intra_a",
            "pae_intra_b", "interface_argmin", "iface_a_span", "iface_b_span"]

    def fmt(v):
        if isinstance(v, float):
            return "" if math.isnan(v) else f"{v:.3f}"
        return "" if v is None else str(v)

    if args.markdown:
        print("| " + " | ".join(cols) + " |")
        print("|" + "---|" * len(cols))
        for r in rows:
            print("| " + " | ".join(fmt(r.get(c)) for c in cols) + " |")
    else:
        print("\t".join(cols))
        for r in rows:
            print("\t".join(fmt(r.get(c)) for c in cols))

    depths = [r["msa_paired"] for r in rows if r["msa_paired"]]
    print(file=sys.stderr)
    if len(depths) >= 2 and max(depths) / max(1, min(depths)) > args.msa_ratio_alert:
        print(f"ALERTE garde-fou n0 : profondeurs de MSA APPARIE de {min(depths)} a "
              f"{max(depths)} lignes (facteur {max(depths)/max(1,min(depths)):.1f} > "
              f"{args.msa_ratio_alert}). Le classement de ces jobs n'est PAS "
              f"interpretable tel quel : sous-echantillonner le plus profond a la "
              f"profondeur du plus pauvre et rejouer.", file=sys.stderr)
    if any(r["n_models"] < 3 for r in rows):
        print("ALERTE : moins de 3 echantillons de diffusion sur au moins un job. "
              "Le PAE inter-chaines MINIMUM est une statistique d'extreme (une "
              "cellule parmi des milliers) : sans dispersion, il ne departage rien.",
              file=sys.stderr)


if __name__ == "__main__":
    main()
