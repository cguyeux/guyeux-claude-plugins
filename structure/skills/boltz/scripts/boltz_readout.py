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
    # LIMITE CONNUE, NON CORRIGEE (2026-09-19, mtbc/Rv3896c-Rv3898c, P4.8) : pour un ligand
    # petite molecule, `label_seq_id` vaut "." pour TOUS ses atomes -> le set() par chaine
    # les collapse a une seule valeur, rendant une longueur de 1 quel que soit le nombre
    # reel d'atomes lourds du ligand. Or le skill tokenise 1 token par atome de ligand (cf.
    # section "Lire les sorties" du skill) : la+lb ne correspond donc jamais a pae.shape[0]
    # pour un ligand multi-atomes, et `pae_stats()` (garde-fou "jamais un chiffre faux")
    # rend systematiquement None -> colonnes pae_inter_* vides en sortie pour ce cas. Verifie
    # sur rv3896c_glcnacmurnac (302 aa + ligand 34 atomes lourds, tokens reels 336) : lb rendu
    # ici vaut 1 au lieu de 34. Calcul manuel (script ponctuel, cf. cahier du projet cite
    # ci-dessus) reste necessaire pour le PAE inter-chaines tant que ceci n'est pas corrige.
    # Piste de correctif, non appliquee : distinguer chaine polymere (compter les label_seq_id
    # numeriques distincts, comportement actuel) de chaine ligand (compter les ATOMES, via
    # `id`/`label_atom_id` plutot que `label_seq_id`), a partir du mol_type/entity_id lu dans
    # `processed/records/<job>.json` plutot que du seul mmCIF.
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
        # label_seq_id vaut "." pour un ligand petite molecule (non-polymere, pas de numero de
        # residu) : int(f[sq_i]) leve alors une ValueError. BUG CORRIGE 2026-09-19 (mtbc/
        # Rv3896c-Rv3898c, P4.8) : l'ancienne version faisait `coords.setdefault(chain, [])
        # .append((int(f[sq_i]), ...))` -- `setdefault` cree la cle AVANT que `int()` echoue,
        # laissant la chaine ligand a une liste VIDE pour de bon (l'exception saute l'ajout mais
        # pas la creation de la cle). `chains = sorted(coords)` incluait alors la chaine ligand
        # avec zero coordonnee, et `np.array([])` sur une liste vide est 1-D (pas (0,3)),
        # plantant plus loin sur `b[None, :, :]`. Repli : residu 1 pour tout atome non numerote
        # (correct pour un ligand a une seule unite ; les coordonnees, elles, sont toujours
        # necessaires au calcul de distance meme quand le numero de residu n'a pas de sens).
        try:
            x, y, z = float(f[x_i]), float(f[x_i + 1]), float(f[x_i + 2])
        except (ValueError, IndexError):
            continue
        try:
            seqid = int(f[sq_i])
        except (ValueError, IndexError):
            seqid = 1
        coords.setdefault(f[ch_i], []).append((seqid, x, y, z))
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
def pae_stats(npz_path: str, lens: list[int]) -> dict | None:
    """Generalise a N >= 2 chaines (corrige le 2026-09-20, mtbc/Rv2892c P3.7/P3.9 :
    avant cette date, la version 2-chaines de cette fonction rendait None des qu'un
    complexe portait une 3e chaine (la+lb != pae.shape[0]) -- jamais un chiffre FAUX,
    mais un manque qui forcait un script ponctuel a chaque docking ternaire/quaternaire.

    GARDE-FOU (verifie contre un complexe ternaire resolu, PE25-PPE41-EspG5 pris comme
    positif calibre, Table S8 de mtbc/Rv2892c/article/supplementary.tex) : la moyenne
    PAE inter-chaines n'est PAS le flatten brut de tous les blocs hors-diagonale. Un
    flatten sur-pondere la paire impliquant la plus grande chaine (7,54-8,43 A mesure au
    lieu des 7,28-8,15 A publies). La definition correcte est la moyenne NON ponderee des
    moyennes de CHAQUE PAIRE de chaines (chaque paire compte pour 1/N_pairs, quelle que
    soit sa taille) -- c'est ce que cette fonction calcule, et elle est identique a
    l'ancienne implementation dans le cas particulier a 2 chaines (une seule paire)."""
    d = np.load(npz_path)
    pae = d[list(d.keys())[0]]
    if pae.ndim == 3:
        pae = pae[0]
    if sum(lens) != pae.shape[0] or len(lens) < 2:
        return None  # jamais rendre un chiffre faux : cf. skill, section tokenisation
    bounds = [0]
    for n in lens:
        bounds.append(bounds[-1] + n)
    pair_means, pair_mins, pair_argmins = [], [], []
    for i in range(len(lens)):
        for j in range(i + 1, len(lens)):
            b1 = pae[bounds[i]:bounds[i + 1], bounds[j]:bounds[j + 1]]
            b2 = pae[bounds[j]:bounds[j + 1], bounds[i]:bounds[i + 1]]
            pair_means.append((float(b1.mean()) + float(b2.mean())) / 2)
            m1, m2 = float(b1.min()), float(b2.min())
            pair_mins.append(min(m1, m2))
            if m1 <= m2:
                ii, jj = np.unravel_index(int(np.argmin(b1)), b1.shape)
            else:
                jj, ii = np.unravel_index(int(np.argmin(b2)), b2.shape)
            pair_argmins.append((i, int(ii) + 1, j, int(jj) + 1))
    best_pair = int(np.argmin(pair_mins))
    ci, ri, cj, rj = pair_argmins[best_pair]
    out = {
        "pae_inter_min": float(min(pair_mins)),
        "pae_inter_mean": float(np.mean(pair_means)),
        "argmin_res_a": ri,
        "argmin_res_b": rj,
        "argmin_pair": f"{ci}-{cj}",  # indices de chaine du couple le plus proche (N>2 chaines)
        "n_cells": int(sum((bounds[i + 1] - bounds[i]) * (bounds[j + 1] - bounds[j]) * 2
                           for i in range(len(lens)) for j in range(i + 1, len(lens)))),
        "n_chains": len(lens),
    }
    for k in range(len(lens)):
        out[f"pae_intra_chain{k}"] = float(pae[bounds[k]:bounds[k + 1],
                                                 bounds[k]:bounds[k + 1]].mean())
    # Colonnes historiques (2 chaines), conservees pour compatibilite descendante des
    # TSV/scripts existants : identiques a la sortie d'avant le 2026-09-20 quand N=2.
    if len(lens) == 2:
        out["pae_intra_a"] = out["pae_intra_chain0"]
        out["pae_intra_b"] = out["pae_intra_chain1"]
    else:
        out["pae_pairs"] = ";".join(
            f"{i}-{j}:{m:.2f}" for (i, j), m in
            zip(((i, j) for i in range(len(lens)) for j in range(i + 1, len(lens))),
                pair_means))
    return out


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
    la, lb = (lens + [0, 0])[:2]  # colonnes historiques len_a/len_b (2 premieres chaines)

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
        if os.path.exists(npz) and lens:
            st = pae_stats(npz, lens)  # toutes les chaines, plus seulement les 2 premieres
            if st:
                row.update(st)
        per_model.append(row)

    msa_dir = msa_dir_of(pred_dir)
    depth, blocks = paired_depth(msa_dir)
    out = {"job": job, "n_models": len(per_model), "len_a": la, "len_b": lb,
           "n_chains": len(lens), "len_chains": ",".join(str(n) for n in lens),
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

    cols = ["job", "n_models", "len_a", "len_b", "n_chains", "len_chains",
            "msa_paired", "iptm", "iptm_sd",
            "pae_inter_min", "pae_inter_min_sd", "pae_inter_min_min",
            "pae_inter_min_max", "pae_inter_mean", "pae_inter_mean_sd",
            "complex_plddt", "chain_ptm_a", "chain_ptm_b", "pae_intra_a",
            "pae_intra_b", "interface_argmin", "iface_a_span", "iface_b_span"]
    # n_chains/len_chains sont nouveaux (2026-09-20) : un TSV deja parse par un script
    # existant qui indexe par POSITION plutot que par en-tete verrait ses colonnes
    # decalees. Prevenir plutot que casser silencieusement :
    if any(r.get("n_chains", 2) > 2 for r in rows):
        print("NOTE : au moins un job a plus de 2 chaines -- colonnes n_chains/len_chains "
              "ajoutees (2026-09-20), pae_inter_mean/min desormais calcules correctement "
              "sur toutes les paires (voir pae_stats()) plutot que None. Le detail par "
              "paire n'est pas dans ce TSV : relire pae_stats() sur les fichiers bruts si "
              "le breakdown par paire est necessaire.", file=sys.stderr)

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
