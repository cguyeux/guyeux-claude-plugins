#!/usr/bin/env python3
"""
Objet: construire les DEUX jeux de séquences que réclame un test de sens de transfert : le
    panel complet (références cellulaires de la famille plus les séquences portées par les
    donneurs candidats) et le panel cellulaire SEUL, qui servira à inférer l'arbre de contrôle.
Entrées: --family-faa (FASTA protéique des références de la famille), --hits (TSV de type
    sortie BLAST tabulaire avec au minimum subject, sstart, send) et --genomes (FASTA des
    génomes donneurs, un enregistrement par génome, identifiants identiques à la colonne
    subject des hits). Optionnel : --family-names pour restreindre le FASTA de famille à une
    liste de noms.
Sorties: <out>/panel.faa, <out>/panel_sans_donneurs.faa, <out>/hosts.tsv (gabarit à compléter),
    <out>/rapport.txt.
Réutilisable: oui, c'est l'étape 1 du skill hgt-direction-check.
Projet: généralisé depuis SpacerEgalVirus/analyses/phase61_p68_2_phylogenie_is256.py (P68.2).
Date: 2026-09-12.

Trois exigences, dont deux ont chacune failli fausser le cas fondateur.

1. Le panel cellulaire doit être EXHAUSTIF pour la famille, pas un trio choisi. Passer d'une
   seule référence aux 241 références IS256 d'ISfinder a suffi à faire apparaître les deux
   éléments qui retournaient la lecture du manuscrit.
2. Plusieurs taxons d'hôtes chez les donneurs, si la nature le permet : c'est ce qui transforme
   un cas unique en résultat répété, et donc un soupçon en démonstration.
3. Dédupliquer par SÉQUENCE et non par nom : quatre génomes portant la même protéine ne sont
   pas quatre observations. Sur le cas fondateur, quatre corynéphages du même cluster portaient
   une protéine strictement identique.

Note d'outillage : une base BLAST construite sans `-parse_seqids` répond « DB contains no
accession info » à tout `blastdbcmd -entry`, quelle que soit la forme de l'identifiant. D'où
l'extraction depuis les FASTA sources plutôt que depuis la base.
"""

import argparse
import csv
import sys
from pathlib import Path

from Bio import SeqIO
from Bio.Seq import Seq


def charge_famille(chemin, noms_retenus=None, min_aa=120, nettoyeur=None):
    """Références de la famille. `nettoyeur` permet de normaliser un identifiant FASTA exotique
    (ex. le mirroir ISfinder porte `nom~~~...`), passé en chaîne de séparateurs."""
    panel = {}
    for rec in SeqIO.parse(chemin, "fasta"):
        nom = rec.id
        if nettoyeur:
            for sep in nettoyeur:
                nom = nom.split(sep)[0]
        nom = nom.strip()
        if noms_retenus is not None and nom not in noms_retenus:
            continue
        seq = str(rec.seq).upper().rstrip("*")
        if len(seq) >= min_aa:
            panel[nom] = seq
    return panel


def regions_hits(chemin, col_subject="subject", col_debut="sstart", col_fin="send",
                 col_score="bitscore"):
    """Régions des génomes donneurs portant un homologue, dédupliquées par intervalle
    approximatif (arrondi à 500 nt) en gardant le meilleur score."""
    regions = {}
    with open(chemin) as f:
        texte = f.read()
    delim = "\t" if "\t" in texte.split("\n")[0] else ","
    for row in csv.DictReader(texte.splitlines(), delimiter=delim):
        if col_subject not in row:
            sys.exit(f"colonne '{col_subject}' absente de {chemin} ; colonnes : {list(row)}")
        s, e = int(row[col_debut]), int(row[col_fin])
        deb, fin = min(s, e), max(s, e)
        brin = 1 if s <= e else -1
        cle = (row[col_subject], round(deb / 500), round(fin / 500), brin)
        score = float(row.get(col_score, 0) or 0)
        if cle not in regions or score > regions[cle][0]:
            regions[cle] = (score, row[col_subject], deb, fin, brin)
    return list(regions.values())


def index_genomes(chemin):
    return {rec.id: str(rec.seq).upper() for rec in SeqIO.parse(chemin, "fasta")}


def traduit(genome, deb, fin, brin, marge, min_aa):
    """Plus longue traduction sans codon stop interne, dans le cadre imposé par le brin."""
    deb = max(1, deb - marge)
    fin = min(len(genome), fin + marge)
    s = Seq(genome[deb - 1:fin])
    if brin == -1:
        s = s.reverse_complement()
    meilleur = ""
    for cadre in range(3):
        aa = str(s[cadre:len(s) - (len(s) - cadre) % 3].translate())
        for bout in aa.split("*"):
            if len(bout) > len(meilleur):
                meilleur = bout
    return meilleur if len(meilleur) >= min_aa else None


def nom_court(sujet, retirer):
    brut = sujet.split("|")[-1] if "|" in sujet else sujet
    brut = brut.split(",")[0]
    for r in retirer:
        brut = brut.replace(r, "")
    return brut.strip("_ ").replace(" ", "_") or sujet


def main():
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[1])
    ap.add_argument("--family-faa", required=True)
    ap.add_argument("--family-names", help="fichier d'un nom par ligne, pour restreindre")
    ap.add_argument("--family-id-sep", default="",
                    help="séparateurs à couper dans l'identifiant FASTA (ex. '~~~')")
    ap.add_argument("--hits", required=True, help="TSV BLAST tabulaire (subject/sstart/send)")
    ap.add_argument("--genomes", required=True, help="FASTA des génomes donneurs")
    ap.add_argument("--donor-prefix", default="DONOR_")
    ap.add_argument("--strip", default="", help="fragments à retirer des noms de génomes, "
                                               "séparés par des virgules")
    ap.add_argument("--margin", type=int, default=150, help="marge nt autour du hit")
    ap.add_argument("--min-aa", type=int, default=120)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    noms = None
    if a.family_names:
        noms = {l.strip() for l in Path(a.family_names).read_text().splitlines() if l.strip()}
    seps = [a.family_id_sep] if a.family_id_sep else None
    panel = charge_famille(a.family_faa, noms, a.min_aa, seps)
    if not panel:
        sys.exit("panel cellulaire vide : vérifier --family-faa, --family-names et --family-id-sep")

    genomes = index_genomes(a.genomes)
    retirer = [x for x in a.strip.split(",") if x]

    brutes, echecs, absents = {}, [], []
    for _score, sujet, deb, fin, brin in regions_hits(a.hits):
        genome = genomes.get(sujet)
        if genome is None:
            absents.append(sujet)
            continue
        aa = traduit(genome, deb, fin, brin, a.margin, a.min_aa)
        if aa is None:
            echecs.append((sujet, deb, fin))
            continue
        base = f"{a.donor_prefix}{nom_court(sujet, retirer)}"
        etiquette, n = base, 2
        while etiquette in brutes and brutes[etiquette] != aa:
            etiquette, n = f"{base}_{n}", n + 1
        brutes[etiquette] = aa

    # Déduplication par SÉQUENCE : plusieurs génomes portant la même protéine ne sont pas
    # plusieurs observations.
    vues, donneurs, redondants = {}, {}, []
    for nm, aa in sorted(brutes.items()):
        if aa in vues:
            redondants.append((nm, vues[aa]))
        else:
            vues[aa] = nm
            donneurs[nm] = aa

    with open(out / "panel.faa", "w") as f:
        for nm, aa in sorted(panel.items()):
            f.write(f">{nm}\n{aa}\n")
        for nm, aa in sorted(donneurs.items()):
            f.write(f">{nm}\n{aa}\n")
    with open(out / "panel_sans_donneurs.faa", "w") as f:
        for nm, aa in sorted(panel.items()):
            f.write(f">{nm}\n{aa}\n")

    # Gabarit d'hôtes : à COMPLÉTER à la main, le taxon de l'hôte d'un donneur ne se déduit pas
    # de son nom de façon fiable, et c'est lui qui porte le test de concordance.
    with open(out / "hosts.tsv", "w") as f:
        f.write("#etiquette\ttaxon_hote\tgroupe_taxonomique\n")
        for nm in sorted(donneurs):
            f.write(f"{nm}\t\t\n")

    lignes = [
        "PANEL POUR UN TEST DE SENS DE TRANSFERT (hgt-direction-check, étape 1)",
        "=" * 78,
        "",
        f"références cellulaires de la famille : {len(panel)}",
        f"séquences portées par des donneurs   : {len(donneurs)}"
        f" (après déduplication de {len(brutes)} extractions)",
        "",
        "-- séquences donneuses retenues --------------------------------------------",
    ]
    for nm, aa in sorted(donneurs.items()):
        lignes.append(f"  {nm:<38} {len(aa):>4} aa")
    if redondants:
        lignes += ["", "-- écartées car STRICTEMENT identiques à une retenue ----------------------"]
        lignes += [f"  {nm:<38} = {g}" for nm, g in redondants]
    if echecs:
        lignes += ["", "-- extractions échouées (aucune traduction assez longue) ------------------"]
        lignes += [f"  {s} {d}-{f}" for s, d, f in echecs]
    if absents:
        lignes += ["", "-- sujets des hits ABSENTS du FASTA de génomes ----------------------------"]
        lignes += [f"  {s}" for s in sorted(set(absents))[:20]]
        lignes += ["  (identifiants incohérents entre --hits et --genomes : à corriger, sinon des",
                   "   donneurs manquent au panel sans que rien ne le signale)"]
    lignes += [
        "",
        "-- à faire avant l'étape 2 -------------------------------------------------",
        f"1. COMPLÉTER {out / 'hosts.tsv'} : taxon de l'hôte et groupe taxonomique de chaque",
        "   séquence donneuse. C'est ce fichier qui porte le test de concordance, et il ne se",
        "   déduit pas des noms de façon fiable.",
        "2. Vérifier que plusieurs GROUPES d'hôtes sont représentés : un seul groupe donne un",
        "   cas unique, plusieurs donnent un résultat répété et indépendant.",
        "3. Inférer les DEUX arbres (panel.faa et panel_sans_donneurs.faa), le second",
        "   INDÉPENDAMMENT et jamais par élagage du premier.",
        "",
    ]
    texte = "\n".join(lignes)
    (out / "rapport.txt").write_text(texte, encoding="utf-8")
    print(texte)


if __name__ == "__main__":
    main()
