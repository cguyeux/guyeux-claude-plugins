#!/usr/bin/env python3
"""Banc de validation de crisprbuilder2 contre CRISPRCasdb (verite independante).

Pourquoi un banc. Les trois defauts connus de l'outil (DR sur-etendu sur les
petits arrays, cout du comptage de k-mers, absence de garde-fou contamination)
se corrigent dans la meme fonction ou juste a cote. Sans mesure AVANT/APRES sur
un jeu fixe, une correction qui repare un cas peut en casser un autre sans que
rien ne le signale — c'est exactement ce qui est arrive au lot v1 du projet
SpacerEgalVirus (skip silencieux pris pour une reussite).

Verite de reference : les DR consensus rendus par CRISPRCasFinder au niveau
evidence 4 dans CRISPRCasdb, releves sur les genomes complets ci-dessous.

Le DR est compare dans LES DEUX SENS : l'outil rend le motif dans le sens du
brin ou il l'a vu, qui n'est pas celui de la nomenclature publiee.

Usage :
    python3 valider.py --data <repertoire des fasta> [--kmer 21] [--json out.json]
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crisprbuilder2 as cb          # noqa: E402

# (fichier, systeme attendu, DR attendu (evidence 4, CRISPRCasdb))
CAS = [
    ("NC_000962.3.fasta", "III-A", "GTTTCCGTCCCCTCTCGGGGTTTTGGGTCTGACGAC"),
    ("NC_015848_M_canettii.fasta", "III-A", "GTTTCCGTCCCCTCTCGGGGTTTTGGGTCTGACGAC"),
    ("canettii_140070005_IE.fasta", "I-E", "GTGCTCCCCGCAAACGCGGGGGTGATCC"),
    ("canettii_140070008_IG.fasta", "I-G", "CCCTCAATGGTGTCCGGCCAAAATGACCGGATTAAT"),
    ("canettii_140070017_IG.fasta", "I-G", "CCCTCAATGGTGTCCGGCCAAAATGACCGGATTAAT"),
    ("canettii_140070010_ICG.fasta", "I-C/G", "GTTCCGATCCTCAGCGGCGGGCAAGGCCCGCCGCTGC"),
]


def verdict(rendu, attendu, tol=2):
    """exact / quasi-exact / sur-etendu / tronque / faux, sur les deux brins.

    La classe « quasi-exact » n'est pas une indulgence : le DR de reference est
    un CONSENSUS, calcule par CRISPRCasFinder sur les copies d'UNE souche, et
    deux souches d'un meme systeme peuvent legitimement differer d'un
    nucleotide. Cas mesure : CIPT 140070017 rend
    `GCCTCAATGGTGTCCGGCCAAAATGACCGGATTAAT` la ou la table de reference, etablie
    sur CIPT 140070008, porte un C initial — meme longueur, une seule
    difference, et une conservation de 99,8 % sur les copies de CETTE souche,
    ce qui dit que le G y est bien majoritaire. Compter cela comme un echec de
    detection ferait porter a l'outil une imprecision de la reference.
    """
    if not rendu:
        return "aucun"
    for r in (rendu, cb.rc(rendu)):
        if r == attendu:
            return "exact"
    for r in (rendu, cb.rc(rendu)):
        if len(r) == len(attendu):
            mm = sum(1 for a, b in zip(r, attendu) if a != b)
            if mm <= tol:
                return f"quasi-exact ({mm} mismatch)"
    for r in (rendu, cb.rc(rendu)):
        if attendu in r:
            return f"sur-etendu (+{len(r) - len(attendu)} nt)"
        if r in attendu:
            return f"tronque (-{len(attendu) - len(r)} nt)"
    return "faux"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--kmer", type=int, default=21)
    ap.add_argument("--json")
    a = ap.parse_args()
    data = Path(a.data)

    res, exacts, total_t = [], 0, 0.0
    print(f"{'genome':<32}{'attendu':<8}{'t (s)':>8}{'spacers':>9}"
          f"{'cons.':>8}  verdict")
    for fichier, systeme, dr_att in CAS:
        chemin = data / fichier
        if not chemin.exists():
            print(f"{fichier:<32}{systeme:<8}{'absent':>8}")
            continue
        t0 = time.time()
        r = cb.analyse(chemin, kmer=a.kmer)
        dt = time.time() - t0
        total_t += dt
        v = verdict(r.get("dr"), dr_att)
        exacts += v.startswith(("exact", "quasi-exact"))
        print(f"{fichier:<32}{systeme:<8}{dt:>8.1f}{r.get('n_spacers_total', 0):>9}"
              f"{r.get('dr_conservation', 0):>7} %  {v}")
        res.append({"genome": fichier, "systeme": systeme, "dr_attendu": dr_att,
                    "dr_rendu": r.get("dr"), "verdict": v, "secondes": round(dt, 2),
                    "n_spacers": r.get("n_spacers_total"),
                    "dr_conservation": r.get("dr_conservation"),
                    "candidats": [c.get("dr") for c in r.get("dr_candidates", [])[:3]]})
    n = len(res)
    print(f"\n{exacts}/{n} en detection aveugle exacte ; {total_t:.1f} s au total"
          f" ({total_t / n:.1f} s par genome)" if n else "")
    if a.json:
        Path(a.json).write_text(json.dumps(
            {"exacts": exacts, "n": n, "secondes_total": round(total_t, 1),
             "cas": res}, indent=1))


if __name__ == "__main__":
    main()
