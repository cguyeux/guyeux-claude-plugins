#!/usr/bin/env python3
"""
Objet: Caracteriser le CONTEXTE SEQUENCE d'un indel appele (homopolymere, repetition
       en tandem de periode 1-12, %GC, ambiguite de placement apres normalisation),
       et le situer contre un MODELE NUL genomique (percentiles sur tout le
       chromosome), pour juger si l'appel est plausiblement un artefact de
       glissement de polymerase / de sequencage plutot qu'un evenement reel.
       Ne rend PAS de verdict : rend une mesure et son percentile. Le verdict
       exige les reads (cf. P2.2).
Entrees: FASTA de reference (defaut NC_000962.3), variants en SPDI 0-based
       `pos:ref:alt` passes en argument, CDS optionnelle `debut-fin:brin` (1-based
       GFF inclusif) pour l'effet sur le cadre de lecture.
Sorties: JSON + rapport texte dans `résultats/` (chemins passes en option).
Réutilisable: oui - CLI entierement parametree, aucune constante propre au projet.
       Candidat a l'essaimage en skill MTBC partage (4 projets du depot ont deja
       eu besoin de cette mesure : gene_decay_census, lineage_navigator, Rv0810c,
       Rv2699c). Reprend et generalise `homopolymer_context` de
       `fini/Rv0810c/analyses/phase6_p4_3_disruption.py`.
Projet: forge dans mtbc/Rv3896c-Rv3898c (P2.1), generalise en skill
Date: 2026-09-10
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from Bio import SeqIO
from Bio.Seq import Seq

COMP = str.maketrans("ACGTacgt", "TGCAtgca")


# --------------------------------------------------------------------------- #
# Coordonnees
# --------------------------------------------------------------------------- #
def spdi_to_1based(pos0: int) -> int:
    """SPDI est 0-based (norme NCBI) : la premiere base affectee est a pos0+1."""
    return pos0 + 1


def parse_spdi(s: str) -> tuple[int, str, str]:
    """`4383143:C:CCGGGG` ou `NC_000962.3:4383143:C:CCGGGG` -> (pos0, ref, alt)."""
    parts = s.split(":")
    if len(parts) == 4:
        parts = parts[1:]
    if len(parts) != 3:
        raise ValueError(f"SPDI mal forme : {s}")
    return int(parts[0]), parts[1].upper(), parts[2].upper()


def check_convention(genome: str, spdis: list[str]) -> dict:
    """Verifie que les SPDI fournis sont bien 0-based, et pas 1-based.

    Un SPDI dont l'allele de reference ne se retrouve pas sur le genome a la
    position annoncee est une erreur de convention (le piege classique : lire
    un SPDI comme du VCF). On teste les deux hypotheses et on rend celle qui
    colle, sans la supposer.
    """
    res = {"0based_ok": 0, "1based_ok": 0, "detail": []}
    for s in spdis:
        pos0, ref, _ = parse_spdi(s)
        as0 = genome[pos0 : pos0 + len(ref)]          # hypothese 0-based
        as1 = genome[pos0 - 1 : pos0 - 1 + len(ref)]  # hypothese 1-based
        res["0based_ok"] += as0 == ref
        res["1based_ok"] += as1 == ref
        res["detail"].append(
            {"spdi": s, "ref_attendue": ref, "lu_si_0based": as0, "lu_si_1based": as1}
        )
    res["verdict"] = (
        "0-based" if res["0based_ok"] > res["1based_ok"]
        else "1-based" if res["1based_ok"] > res["0based_ok"]
        else "indecidable"
    )
    return res


# --------------------------------------------------------------------------- #
# Contexte repete local
# --------------------------------------------------------------------------- #
def homopolymer_at(seq: str, i: int) -> dict:
    """Homopolymere (0-based, indice i) contenant la position i."""
    b = seq[i]
    lo = i
    while lo > 0 and seq[lo - 1] == b:
        lo -= 1
    hi = i
    while hi < len(seq) - 1 and seq[hi + 1] == b:
        hi += 1
    return {"base": b, "debut0": lo, "fin0": hi, "longueur": hi - lo + 1}


def tandem_repeats_overlapping(seq: str, lo: int, hi: int, pmax: int = 12,
                               min_units: float = 2.0) -> list[dict]:
    """Repetitions en tandem EXACTES chevauchant l'intervalle 0-based [lo, hi].

    Pour chaque periode p, on cherche la repetition maximale : le plus long
    segment tel que seq[k] == seq[k-p] partout. On ne garde que les segments
    d'au moins `min_units` unites, et on retire ceux qui ne sont que la
    re-decouverte d'une periode plus courte (p multiple d'une periode retenue
    couvrant le meme segment).
    """
    out: list[dict] = []
    n = len(seq)
    for p in range(1, pmax + 1):
        k = p
        while k < n:
            if seq[k] != seq[k - p]:
                k += 1
                continue
            start = k - p
            end = k
            while end + 1 < n and seq[end + 1] == seq[end + 1 - p]:
                end += 1
            length = end - start + 1
            if length >= min_units * p and not (end < lo or start > hi):
                out.append(
                    {
                        "periode": p,
                        "unite": seq[start : start + p],
                        "debut0": start,
                        "fin0": end,
                        "longueur_pb": length,
                        "n_unites": round(length / p, 2),
                    }
                )
            k = end + 1
    # dedupliquer : garder la plus petite periode pour un segment donne
    out.sort(key=lambda d: (d["debut0"], d["periode"]))
    kept: list[dict] = []
    for r in out:
        redundant = any(
            k["debut0"] <= r["debut0"] and k["fin0"] >= r["fin0"]
            and r["periode"] % k["periode"] == 0
            for k in kept
        )
        if not redundant:
            kept.append(r)
    return sorted(kept, key=lambda d: -d["longueur_pb"])


def gc_fraction(s: str) -> float:
    s = s.upper()
    return (s.count("G") + s.count("C")) / len(s) if s else float("nan")


# --------------------------------------------------------------------------- #
# Normalisation d'un indel : de combien peut-il glisser ?
# --------------------------------------------------------------------------- #
def indel_placement_ambiguity(genome: str, pos0: int, ref: str, alt: str) -> dict:
    """Nombre de placements EQUIVALENTS de l'indel (ambiguite de normalisation).

    Un indel dans une repetition peut souvent etre ecrit a plusieurs positions
    sans changer la sequence produite. Le nombre de decalages possibles est une
    mesure DIRECTE de la repetitivite locale vue par l'indel lui-meme : 0 =
    contexte unique, grand = microsatellite.
    """
    if len(ref) == len(alt):
        return {"applicable": False}
    inserted = len(alt) > len(ref)
    unit = alt[len(ref):] if inserted else ref[len(alt):]
    anchor = pos0 + len(alt) - 1 if inserted else pos0 + len(alt) - 1

    left = 0
    u = unit
    a = anchor
    while a >= 0 and u[-1] == genome[a]:
        u = u[-1] + u[:-1]
        a -= 1
        left += 1
    right = 0
    u = unit
    b = anchor + 1 + (0 if inserted else len(unit))
    while b < len(genome) and u[0] == genome[b]:
        u = u[1:] + u[0]
        b += 1
        right += 1
    return {
        "applicable": True,
        "type": "insertion" if inserted else "deletion",
        "unite": unit,
        "decalages_gauche": left,
        "decalages_droite": right,
        "placements_equivalents": left + right + 1,
    }


# --------------------------------------------------------------------------- #
# Modele nul genomique
# --------------------------------------------------------------------------- #
def genome_null_model(genome: str, win: int = 100, n_sample: int = 20000,
                      flank: int = 30, pmax: int = 12, seed: int = 20260910) -> dict:
    """Distribution NULLE, mesuree EXACTEMENT comme au site du variant.

    Piege evite : comparer "le plus long tandem chevauchant le site" a "le plus
    long tandem n'importe ou dans une fenetre de 100 pb" n'est pas comparer deux
    fois la meme chose, et gonfle artificiellement la rarete du site. On tire
    donc `n_sample` positions au hasard sur le chromosome et on leur applique la
    MEME fonction qu'au site : homopolymere contenant la position, plus long
    tandem la chevauchant, %GC de la fenetre centree.
    """
    rng = np.random.default_rng(seed)
    arr = np.frombuffer(genome.upper().encode(), dtype=np.uint8)
    n = arr.size
    is_gc = (arr == ord("G")) | (arr == ord("C"))

    # %GC en fenetre glissante centree, exact et vectorise
    cs = np.concatenate([[0], np.cumsum(is_gc)])
    half = win // 2
    starts = np.arange(half, n - half)
    gc_pos = (cs[starts + half] - cs[starts - half]) / win

    pos = rng.integers(flank + 1, n - flank - 1, size=n_sample)
    hp = np.empty(n_sample, dtype=np.int32)
    tr = np.empty(n_sample, dtype=np.int32)
    for k, i in enumerate(pos):
        hp[k] = homopolymer_at(genome, int(i))["longueur"]
        w = genome[int(i) - flank : int(i) + flank + 1]
        reps = tandem_repeats_overlapping(w, flank, flank, pmax=pmax)
        tr[k] = reps[0]["longueur_pb"] if reps else 0
    return {
        "fenetre_gc_pb": win,
        "n_sample": int(n_sample),
        "flank": flank,
        "gc": gc_pos,
        "homopolymere_au_site": hp,
        "tandem_au_site": tr,
        "gc_genome": float(is_gc.mean()),
    }


def percentile_of(dist: np.ndarray, value: float) -> float:
    return float((dist <= value).mean() * 100)


# --------------------------------------------------------------------------- #
# Effet sur le cadre de lecture
# --------------------------------------------------------------------------- #
def translate_to_stop(genome: str, start1: int, end1: int, strand: str,
                     extension: int = 3000) -> tuple[str, int | None]:
    """Traduit depuis le codon start annote JUSQU'AU PREMIER STOP REEL.

    Piege evite : traduire seulement la CDS annotee et lire "N aa jusqu'au
    premier stop" alors qu'aucun stop n'a ete rencontre et qu'on a simplement
    bute sur la borne annotee. Apres un frameshift ou un stop_lost, le stop
    reel est en general HORS de la CDS de reference : c'est tout l'objet.
    Rend (proteine sans le stop, position 1-based de la premiere base du codon
    stop sur le brin +, ou None si aucun stop dans `extension` nt).
    """
    if strand == "-":
        lo = max(1, start1 - extension)
        seg = genome[lo - 1 : end1]
        read = str(Seq(seg).reverse_complement())
    else:
        hi = min(len(genome), end1 + extension)
        seg = genome[start1 - 1 : hi]
        read = seg
    ncod = len(read) // 3
    aa = str(Seq(read[: ncod * 3]).translate(table=11))
    if "*" not in aa:
        return aa, None
    k = aa.index("*")
    stop_off = k * 3
    if strand == "-":
        stop_pos1 = end1 - stop_off - 2
    else:
        stop_pos1 = start1 + stop_off
    return aa[:k], stop_pos1


def cds_effect(genome: str, cds: tuple[int, int, str], pos0: int,
               ref: str, alt: str, extension: int = 3000) -> dict:
    """Effet d'un variant sur une CDS (bornes 1-based GFF inclusives).

    La traduction va toujours jusqu'au premier stop REEL, pas jusqu'a la borne
    annotee, pour l'allele de reference comme pour l'allele alternatif.
    """
    start1, end1, strand = cds
    p1 = spdi_to_1based(pos0)
    last1 = p1 + len(ref) - 1
    inside = not (last1 < start1 or p1 > end1)
    out = {
        "cds_1based": [start1, end1, strand],
        "premiere_base_1based": p1,
        "dans_la_cds": inside,
    }
    if not inside:
        return out
    offset = (end1 - p1) if strand == "-" else (p1 - start1)
    out["offset_dans_la_cds_0based"] = offset
    out["codon_1based"] = offset // 3 + 1
    out["position_dans_le_codon"] = offset % 3 + 1

    d = len(alt) - len(ref)
    out["decalage_nt"] = d
    out["frameshift"] = d % 3 != 0

    mut_genome = genome[: p1 - 1] + alt + genome[last1:]
    ms, me = (start1, end1 + d) if strand == "-" else (start1, end1 + d)

    wt_aa, wt_stop = translate_to_stop(genome, start1, end1, strand, extension)
    mut_aa, mut_stop = translate_to_stop(mut_genome, ms, me, strand, extension)

    out["proteine_wt_len"] = len(wt_aa)
    out["proteine_mut_len"] = len(mut_aa)
    out["stop_wt_atteint"] = wt_stop is not None
    out["stop_mut_atteint"] = mut_stop is not None
    out["stop_wt_pos1_genome_ref"] = wt_stop
    out["stop_mut_pos1_genome_mute"] = mut_stop
    out["longueur_cds_annotee_aa"] = (end1 - start1 + 1) // 3 - 1
    out["wt_stop_est_celui_de_l_annotation"] = (
        wt_stop is not None
        and ((strand == "-" and wt_stop == start1) or (strand == "+" and wt_stop == end1 - 2))
    )

    first_diff = next((k for k, (x, y) in enumerate(zip(wt_aa, mut_aa)) if x != y), None)
    if first_diff is None and len(wt_aa) != len(mut_aa):
        first_diff = min(len(wt_aa), len(mut_aa))
    out["premier_residu_divergent"] = None if first_diff is None else first_diff + 1
    out["n_residus_identiques_en_tete"] = len(wt_aa) if first_diff is None else first_diff
    out["proteine_wt"] = wt_aa
    out["proteine_mut"] = mut_aa
    out["queue_wt_depuis_divergence"] = "" if first_diff is None else wt_aa[first_diff:]
    out["queue_mut_depuis_divergence"] = "" if first_diff is None else mut_aa[first_diff:]
    return out


def kmer_uniqueness(genome: str, i0: int, span: int, k: int = 31) -> dict:
    """Les k-mers couvrant le site sont-ils UNIQUES dans le chromosome ?

    Second mecanisme d'artefact, distinct du glissement : si la region a un
    paralogue, les reads d'ailleurs viennent s'y mapper et fabriquent de faux
    appels (le ~10 % non uniquement mappable du MTBC : PE/PPE, esx, pks/pps).
    On compte les occurrences exactes, sur les deux brins, de chaque k-mer
    chevauchant le site.
    """
    rc = genome.translate(COMP)[::-1]
    lo = max(0, i0 - k + 1)
    hi = min(len(genome) - k, i0 + span)
    total, non_uniques, worst = 0, 0, 0
    for st in range(lo, hi + 1):
        km = genome[st : st + k]
        if len(km) < k:
            continue
        n = genome.count(km) + rc.count(km)
        total += 1
        worst = max(worst, n)
        if n > 1:
            non_uniques += 1
    return {
        "k": k,
        "n_kmers_testes": total,
        "n_kmers_non_uniques": non_uniques,
        "occurrences_max": worst,
        "region_uniquement_mappable": non_uniques == 0,
    }


# --------------------------------------------------------------------------- #
def analyse_variant(genome: str, spdi: str, null: dict, flank: int,
                    cds: tuple[int, int, str] | None) -> dict:
    pos0, ref, alt = parse_spdi(spdi)
    p1 = spdi_to_1based(pos0)
    i0 = p1 - 1  # index 0-based dans genome

    observed = genome[i0 : i0 + len(ref)]
    rep: dict = {
        "spdi": spdi,
        "pos0_spdi": pos0,
        "premiere_base_1based": p1,
        "ref_annoncee": ref,
        "ref_lue_sur_le_genome": observed,
        "ref_verifiee": observed == ref,
        "type": ("insertion" if len(alt) > len(ref)
                 else "deletion" if len(alt) < len(ref) else "substitution"),
        "taille_indel_pb": len(alt) - len(ref),
    }
    if not rep["ref_verifiee"]:
        rep["ERREUR"] = "allele de reference non retrouve : convention ou variant faux"
        return rep

    # --- sequences
    lo, hi = i0 - flank, i0 + len(ref) + flank
    win_ref = genome[lo:hi]
    site_in_win = i0 - lo
    mut_genome_local = genome[lo : i0 + len(ref)] + alt[len(ref):] + genome[i0 + len(ref) : hi] \
        if len(alt) > len(ref) else genome[lo:i0] + alt + genome[i0 + len(ref) : hi]
    rep["contexte_brin_plus_ref"] = win_ref
    rep["contexte_brin_plus_alt"] = mut_genome_local
    rep["contexte_brin_moins_ref"] = win_ref.translate(COMP)[::-1]
    rep["contexte_brin_moins_alt"] = mut_genome_local.translate(COMP)[::-1]
    rep["sequence_inseree_ou_deletee"] = (alt[len(ref):] if len(alt) > len(ref)
                                          else ref[len(alt):])

    # --- homopolymere
    hp = homopolymer_at(genome, i0)
    rep["homopolymere_ref"] = {
        "base": hp["base"], "longueur": hp["longueur"],
        "1based": [hp["debut0"] + 1, hp["fin0"] + 1],
    }
    # homopolymere maximal cree dans la fenetre mutee, au site
    site_alt = site_in_win
    hp_alt = homopolymer_at(mut_genome_local, site_alt)
    rep["homopolymere_alt_au_site"] = {"base": hp_alt["base"], "longueur": hp_alt["longueur"]}
    rep["homopolymere_max_fenetre_alt"] = max(
        homopolymer_at(mut_genome_local, k)["longueur"] for k in range(len(mut_genome_local))
    )

    # --- repetitions en tandem
    span_lo, span_hi = site_in_win, site_in_win + max(len(ref), 1) - 1
    rep["tandem_ref"] = tandem_repeats_overlapping(win_ref, span_lo, span_hi)[:6]
    rep["tandem_alt"] = tandem_repeats_overlapping(
        mut_genome_local, span_lo, span_lo + abs(len(alt) - len(ref))
    )[:6]

    # --- ambiguite de placement
    rep["ambiguite_placement"] = indel_placement_ambiguity(genome, pos0, ref, alt)

    # --- unicite des k-mers (cross-mapping)
    rep["unicite_kmers"] = kmer_uniqueness(genome, i0, max(len(ref), len(alt)))

    # --- GC local et percentiles
    rep["gc"] = {}
    for w in (20, 50, 100, 200):
        seg = genome[i0 - w // 2 : i0 + w // 2]
        rep["gc"][f"fenetre_{w}pb"] = round(gc_fraction(seg), 4)
    rep["gc"]["genome_entier"] = round(null["gc_genome"], 4)
    rep["percentiles_vs_genome"] = {
        "gc_100pb": round(percentile_of(null["gc"], rep["gc"]["fenetre_100pb"]), 2),
        "homopolymere_ref": round(percentile_of(null["homopolymere_au_site"],
                                                rep["homopolymere_ref"]["longueur"]), 2),
        "tandem_au_site_ref": round(
            percentile_of(null["tandem_au_site"],
                          rep["tandem_ref"][0]["longueur_pb"] if rep["tandem_ref"] else 0), 2),
    }

    if cds:
        rep["effet_cds"] = cds_effect(genome, cds, pos0, ref, alt)
    return rep


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--genome", required=True,
                    help="FASTA du genome de reference (un seul enregistrement)")
    ap.add_argument("--spdi", nargs="+", required=True,
                    help="variants SPDI 0-based, ex. 4383143:C:CCGGGG")
    ap.add_argument("--cds", default=None,
                    help="CDS du variant principal, 1-based GFF : debut-fin:brin")
    ap.add_argument("--flank", type=int, default=60)
    ap.add_argument("--out-json", default=None)
    ap.add_argument("--out-txt", default=None)
    a = ap.parse_args()

    genome = str(next(SeqIO.parse(a.genome, "fasta")).seq).upper()
    conv = check_convention(genome, a.spdi)

    cds = None
    if a.cds:
        span, strand = a.cds.split(":")
        s, e = span.split("-")
        cds = (int(s), int(e), strand)

    null = genome_null_model(genome)
    report = {
        "genome": a.genome,
        "longueur_genome": len(genome),
        "convention_coordonnees": conv,
        "modele_nul": {
            "methode": ("positions tirees au hasard sur le chromosome, mesurees "
                        "exactement comme le site du variant"),
            "n_positions_tirees": null["n_sample"],
            "fenetre_gc_pb": null["fenetre_gc_pb"],
            "gc_genome": round(null["gc_genome"], 4),
            "gc_median": round(float(np.median(null["gc"])), 4),
            "homopolymere_median": int(np.median(null["homopolymere_au_site"])),
            "homopolymere_p95": int(np.percentile(null["homopolymere_au_site"], 95)),
            "homopolymere_p99": int(np.percentile(null["homopolymere_au_site"], 99)),
            "homopolymere_max_tire": int(null["homopolymere_au_site"].max()),
            "tandem_median": int(np.median(null["tandem_au_site"])),
            "tandem_p95": int(np.percentile(null["tandem_au_site"], 95)),
            "tandem_p99": int(np.percentile(null["tandem_au_site"], 99)),
            "tandem_max_tire": int(null["tandem_au_site"].max()),
        },
        "variants": [analyse_variant(genome, s, null, a.flank,
                                     cds if i == 0 else None)
                     for i, s in enumerate(a.spdi)],
    }

    if a.out_json:
        Path(a.out_json).write_text(json.dumps(report, indent=2, ensure_ascii=False))
    txt = render(report)
    if a.out_txt:
        Path(a.out_txt).write_text(txt)
    print(txt)


def render(r: dict) -> str:
    L = []
    A = L.append
    A("=" * 78)
    A("CONTEXTE SEQUENCE D'UN INDEL APPELE — mesure, pas verdict")
    A("=" * 78)
    c = r["convention_coordonnees"]
    A(f"\nConvention des SPDI fournis : {c['verdict']} "
      f"({c['0based_ok']} verifies en 0-based, {c['1based_ok']} en 1-based)")
    m = r["modele_nul"]
    A(f"\nMODELE NUL — {m['n_positions_tirees']} positions tirees au hasard sur "
      f"{r['longueur_genome']} pb, mesurees comme le site")
    A(f"  GC genome {m['gc_genome']:.3f} | mediane fenetre {m['fenetre_gc_pb']} pb "
      f"{m['gc_median']:.3f}")
    A(f"  homopolymere CONTENANT la position : mediane {m['homopolymere_median']}, "
      f"p95 {m['homopolymere_p95']}, p99 {m['homopolymere_p99']}, "
      f"max tire {m['homopolymere_max_tire']}")
    A(f"  plus long tandem CHEVAUCHANT la position (periode<=12) : "
      f"mediane {m['tandem_median']}, p95 {m['tandem_p95']}, p99 {m['tandem_p99']}, "
      f"max tire {m['tandem_max_tire']}")

    for v in r["variants"]:
        A("\n" + "-" * 78)
        A(f"VARIANT {v['spdi']}   ({v['type']}, {v['taille_indel_pb']:+d} pb)")
        A("-" * 78)
        if not v.get("ref_verifiee"):
            A(f"  !! {v.get('ERREUR', 'ref non verifiee')} "
              f"(annoncee {v['ref_annoncee']}, lue {v['ref_lue_sur_le_genome']})")
            continue
        A(f"  position 1-based : {v['premiere_base_1based']}   "
          f"ref verifiee : {v['ref_lue_sur_le_genome']}")
        A(f"  sequence inseree/deletee : {v['sequence_inseree_ou_deletee']!r}")
        hp = v["homopolymere_ref"]
        A(f"\n  HOMOPOLYMERE au site (ref) : {hp['base']}x{hp['longueur']} "
          f"[{hp['1based'][0]}-{hp['1based'][1]}]  "
          f"-> percentile {v['percentiles_vs_genome']['homopolymere_ref']:.1f} du genome")
        A(f"  homopolymere au site apres mutation : "
          f"{v['homopolymere_alt_au_site']['base']}x{v['homopolymere_alt_au_site']['longueur']} "
          f"(max de la fenetre mutee : {v['homopolymere_max_fenetre_alt']})")
        A("\n  REPETITIONS EN TANDEM chevauchant le site (reference) :")
        if not v["tandem_ref"]:
            A("    aucune (>= 2 unites, periode <= 12)")
        for t in v["tandem_ref"]:
            A(f"    periode {t['periode']:2d} | unite {t['unite']!r:12s} | "
              f"{t['longueur_pb']:3d} pb = {t['n_unites']} unites")
        A(f"    -> percentile du plus long tandem au site : "
          f"{v['percentiles_vs_genome']['tandem_au_site_ref']:.1f} "
          f"(0 = plus court qu'a toute position tiree)")
        amb = v["ambiguite_placement"]
        if amb.get("applicable"):
            A(f"\n  AMBIGUITE DE PLACEMENT : {amb['placements_equivalents']} "
              f"placement(s) equivalent(s) "
              f"({amb['decalages_gauche']} a gauche, {amb['decalages_droite']} a droite)")
        u = v["unicite_kmers"]
        A(f"\n  UNICITE DES {u['k']}-MERS couvrant le site : "
          f"{u['n_kmers_testes'] - u['n_kmers_non_uniques']}/{u['n_kmers_testes']} uniques "
          f"(occurrences max {u['occurrences_max']}) -> "
          f"region uniquement mappable : {u['region_uniquement_mappable']}")
        g = v["gc"]
        A(f"\n  GC : 20pb {g['fenetre_20pb']:.3f} | 50pb {g['fenetre_50pb']:.3f} | "
          f"100pb {g['fenetre_100pb']:.3f} | 200pb {g['fenetre_200pb']:.3f} | "
          f"genome {g['genome_entier']:.3f}")
        A(f"    -> percentile GC (100 pb) : {v['percentiles_vs_genome']['gc_100pb']:.1f}")
        A(f"\n  contexte brin + (ref) : ...{v['contexte_brin_plus_ref']}...")
        A(f"  contexte brin + (alt) : ...{v['contexte_brin_plus_alt']}...")
        A(f"  contexte brin - (ref) : ...{v['contexte_brin_moins_ref']}...")
        A(f"  contexte brin - (alt) : ...{v['contexte_brin_moins_alt']}...")
        if "effet_cds" in v:
            e = v["effet_cds"]
            A(f"\n  CDS {e['cds_1based']} : dans la CDS = {e['dans_la_cds']}")
            if e["dans_la_cds"]:
                A(f"    codon {e['codon_1based']} (position {e['position_dans_le_codon']} "
                  f"du codon), decalage {e['decalage_nt']:+d} nt, "
                  f"frameshift = {e['frameshift']}")
                A(f"    CDS annotee : {e['longueur_cds_annotee_aa']} aa")
                A(f"    proteine REF jusqu'au 1er stop REEL : {e['proteine_wt_len']} aa "
                  f"(stop atteint : {e['stop_wt_atteint']}, pos {e['stop_wt_pos1_genome_ref']}, "
                  f"= stop de l'annotation : {e['wt_stop_est_celui_de_l_annotation']})")
                A(f"    proteine ALT jusqu'au 1er stop REEL : {e['proteine_mut_len']} aa "
                  f"(stop atteint : {e['stop_mut_atteint']})")
                A(f"    premier residu divergent : {e['premier_residu_divergent']} "
                  f"({e['n_residus_identiques_en_tete']} aa identiques en tete)")
                A(f"    queue WT  : {e['queue_wt_depuis_divergence']}")
                A(f"    queue MUT : {e['queue_mut_depuis_divergence']}")
    A("\n" + "=" * 78)
    A("Rappel : une mesure de contexte NE TRANCHE PAS un artefact. Elle dit si le")
    A("site est le genre d'endroit ou les appeurs se trompent. Le verdict exige")
    A("les reads (pileup) sur plusieurs souches de clades differents.")
    return "\n".join(L)


if __name__ == "__main__":
    main()
