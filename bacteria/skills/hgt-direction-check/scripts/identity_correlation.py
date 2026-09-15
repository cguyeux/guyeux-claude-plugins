#!/usr/bin/env python3
"""
Objet: le PRÉ-TEST qui disqualifie un argument de sens de transfert fondé sur une identité de
    séquence, en deux minutes et sans arbre. Pour chaque membre du panel de famille, mesure
    l'identité à la cible supposée DONNEUSE (gène viral, plasmidique) et l'identité à un
    homologue CELLULAIRE de référence, puis leur corrélation de Spearman.
Entrées: --panel (FASTA protéique des références de la famille), --cible (FASTA d'une séquence,
    le gène du donneur candidat), --reference (FASTA d'une séquence, homologue cellulaire de
    référence choisi AVANT de voir le résultat).
Sorties: TSV sur stdout (nom, identité à la cible, identité à la référence) et la corrélation
    sur stderr ; --out écrit le TSV dans un fichier.
Réutilisable: oui, c'est l'étape 0 du skill hgt-direction-check.
Projet: généralisé depuis SpacerEgalVirus/analyses/phase58_p14_1_ismlu3_isbli2.py (P14.1).
Date: 2026-09-12.

Pourquoi ce test vient AVANT tout arbre. Sur le cas fondateur, l'identité au gène 30 du
corynébactériophage Poushou était prédite à rho = 0,913 (p = 1,0e-94, n = 240) par la seule
identité à ISMlu3, une séquence d'insertion CELLULAIRE de *Micrococcus luteus*. « Être proche
du gène phagique » n'était donc pas une propriété phagique mais une position dans la structure
de la famille IS256 — et un manuscrit avait été écrit sur la lecture inverse.

Un rho élevé tue l'argument d'identité : soit on l'abandonne, soit on passe à la topologie, qui
est la seule à pouvoir trancher un sens. Un rho faible ne prouve rien de positif, il rend
seulement la suite intéressante.

Garde-fou : choisir l'homologue cellulaire de référence AVANT de voir le résultat, et pour une
raison indépendante (le plus proche par identité dans un balayage préalable, ou le prototype
nommé de la famille), jamais parce qu'il donne le rho souhaité.
"""

import argparse
import sys
from pathlib import Path

from Bio import Align, SeqIO
from Bio.Align import substitution_matrices


def aligneur_global():
    a = Align.PairwiseAligner()
    a.substitution_matrix = substitution_matrices.load("BLOSUM62")
    a.open_gap_score = -11
    a.extend_gap_score = -1
    a.mode = "global"
    return a


def pident(aligneur, s1, s2, denominateur="full"):
    """Identité en pourcentage sur l'alignement global.

    Deux définitions circulent et elles ne donnent PAS le même chiffre, ce qui a été mesuré :
    sur le panel IS256 du cas fondateur, la corrélation vaut rho = 0,913 avec `full` et
    rho = 0,715 avec `aligned`. La conclusion qualitative est la même, mais un skill qui
    annoncerait l'un en calculant l'autre contredirait silencieusement le registre du projet.

    - `full`    : dénominateur = longueur TOTALE de l'alignement, gaps compris. C'est la
                  définition des scripts d'origine (P7.5.2, P14.1), donc celle qui reproduit
                  les chiffres consignés. Plus conservatrice, elle pénalise les séquences de
                  longueurs inégales.
    - `aligned` : dénominateur = colonnes appariées seulement, gaps exclus. C'est la définition
                  usuelle de BLAST.
    """
    aln = aligneur.align(s1, s2)[0]
    a, b = str(aln[0]), str(aln[1])
    if denominateur == "aligned":
        apparies = [(x, y) for x, y in zip(a, b) if x != "-" and y != "-"]
        if not apparies:
            return 0.0
        return 100.0 * sum(1 for x, y in apparies if x == y) / len(apparies)
    if not a:
        return 0.0
    return 100.0 * sum(1 for x, y in zip(a, b) if x == y and x != "-") / len(a)


def une_sequence(chemin):
    rec = next(SeqIO.parse(chemin, "fasta"))
    return rec.id, str(rec.seq).upper().rstrip("*")


def spearman(xs, ys):
    """Spearman sans scipy : rangs moyens sur les ex aequo, puis Pearson sur les rangs.
    La p-valeur est approchée par la statistique t, valable pour n >= 10."""
    def rangs(v):
        ordre = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(ordre):
            j = i
            while j + 1 < len(ordre) and v[ordre[j + 1]] == v[ordre[i]]:
                j += 1
            moyen = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[ordre[k]] = moyen
            i = j + 1
        return r

    rx, ry = rangs(xs), rangs(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    if den == 0:
        return 0.0, 1.0, n
    rho = num / den
    if n <= 2 or abs(rho) >= 1:
        return rho, 0.0, n
    t = rho * ((n - 2) / (1 - rho * rho)) ** 0.5
    # Approximation normale de la loi de Student, suffisante pour dire « écrasant » ou « nul ».
    import math
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(t) / 2 ** 0.5)))
    return rho, p, n


def main():
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[1])
    ap.add_argument("--panel", required=True, help="FASTA protéique des références de la famille")
    ap.add_argument("--cible", required=True, help="FASTA du gène du donneur candidat")
    ap.add_argument("--reference", required=True,
                    help="FASTA de l'homologue CELLULAIRE de référence, choisi d'avance")
    ap.add_argument("--min-aa", type=int, default=120, help="longueur minimale retenue")
    ap.add_argument("--identity", choices=("full", "aligned"), default="full",
                    help="dénominateur de l'identité : 'full' compte les gaps (défaut, "
                         "définition des scripts d'origine, reproduit les chiffres consignés) ; "
                         "'aligned' ne compte que les colonnes appariées (définition BLAST)")
    ap.add_argument("--out", help="fichier TSV de sortie")
    a = ap.parse_args()

    aligneur = aligneur_global()
    nom_cible, seq_cible = une_sequence(a.cible)
    nom_ref, seq_ref = une_sequence(a.reference)

    resultats = []
    for rec in SeqIO.parse(a.panel, "fasta"):
        seq = str(rec.seq).upper().rstrip("*")
        if len(seq) < a.min_aa:
            continue
        nom = rec.id
        if nom in (nom_cible, nom_ref):
            continue
        resultats.append((nom, pident(aligneur, seq, seq_cible, a.identity),
                          pident(aligneur, seq, seq_ref, a.identity)))

    if len(resultats) < 10:
        sys.exit(f"panel trop petit après filtrage ({len(resultats)} séquences) : "
                 "la corrélation ne serait pas interprétable")

    resultats.sort(key=lambda r: -r[1])
    entete = f"#nom\tidentite_vs_{nom_cible}\tidentite_vs_{nom_ref}"
    corps = "\n".join(f"{n}\t{x:.2f}\t{y:.2f}" for n, x, y in resultats)
    print(entete)
    print(corps)
    if a.out:
        Path(a.out).write_text(entete + "\n" + corps + "\n", encoding="utf-8")

    rho, p, n = spearman([r[1] for r in resultats], [r[2] for r in resultats])
    print("", file=sys.stderr)
    print(f"Spearman rho = {rho:.3f}  (p ~ {p:.2e}, n = {n})"
          f"   [identité : {a.identity}]", file=sys.stderr)
    print(f"cible donneuse  : {nom_cible}", file=sys.stderr)
    print(f"reference cellulaire : {nom_ref}", file=sys.stderr)
    print("", file=sys.stderr)
    if abs(rho) >= 0.7:
        print("LECTURE : rho élevé. L'identité à la cible est prédite par la seule position dans",
              file=sys.stderr)
        print("la famille : l'argument d'identité ne porte AUCUNE information de sens de",
              file=sys.stderr)
        print("transfert. L'abandonner, ou passer à la topologie (read_direction.py), qui est la",
              file=sys.stderr)
        print("seule à pouvoir trancher.", file=sys.stderr)
    else:
        print("LECTURE : rho faible. Cela ne prouve RIEN de positif sur le sens du transfert,",
              file=sys.stderr)
        print("cela rend seulement la suite intéressante : construire les deux arbres et lire",
              file=sys.stderr)
        print("le nichage (read_direction.py).", file=sys.stderr)
    # Trois premiers du panel : utile pour voir tout de suite si des non-cibles dominent.
    print("", file=sys.stderr)
    print("Trois plus proches de la cible (à comparer à ce que le manuscrit met en avant) :",
          file=sys.stderr)
    for n_, x, y in resultats[:3]:
        print(f"  {n_:<20} {x:6.2f} % vs cible   {y:6.2f} % vs référence cellulaire",
              file=sys.stderr)


if __name__ == "__main__":
    main()
