#!/usr/bin/env python3
"""
Objet: mesurer les deux artefacts qui fabriquent un faux transfert INTER-DOMAINE, et qu'aucun
    contrôle du skill hgt-direction-check ne couvre : l'HÉTÉROGÉNÉITÉ DE COMPOSITION en acides
    aminés entre lignées, et la SATURATION des substitutions à la distance qui sépare une
    bactérie d'un eucaryote. Les deux regroupent les séquences par composition ou par hasard
    plutôt que par ascendance, et produisent un nichage qui ressemble trait pour trait à une
    capture récente.
Entrées: --alignment (FASTA aligné, protéique), --focus (étiquettes des séquences dont le sort
    décide de la lecture : la requête et les donneurs candidats), --tree (facultatif : les
    distances patristiques d'un arbre déjà inféré rendent le test de saturation plus juste).
Sorties: rapport sur stdout et --out ; --out-recoded écrit l'alignement RECODÉ (Dayhoff-6 ou
    SR-4) prêt à ré-inférer ; dernière ligne machine-lisible
    `VERDICT_COMPOSITION: HOMOGENE|HETEROGENE|SATURE|HETEROGENE_ET_SATURE`.
Réutilisable: oui, c'est l'étape 2 du skill hgt-interdomain-check.
Projet: écrit pour environnement/pistes.md AG2 (manque (2) du constat du 2026-09-22).
Date: 2026-09-22.

Pourquoi cette étape n'existe pas dans le skill frère. Le contrôle d'attraction des longues
branches de `hgt-direction-check` (un arbre inféré sans les donneurs) teste une chose et une
seule : le clade d'accueil a-t-il été FABRIQUÉ par la présence des donneurs. Entre une IS
bactérienne et une IS portée par un phage de la même bactérie, la divergence est modérée et la
composition comparable, donc ce contrôle suffit. Entre une protéine de *Leptospira* et une
histone-méthyltransférase de plante, ni l'un ni l'autre n'est vrai : le signal phylogénétique
peut être épuisé, et deux lignées à composition proche s'attirent sans lien de parenté.

Les deux mesures ne PROUVENT rien ; elles disent si l'arbre qu'on s'apprête à lire a le droit
d'être lu avec un modèle homogène, ou s'il faut passer aux modèles à profils hétérogènes
(C20/C60, PMSF) et au recodage. Un résultat de transfert qui ne survit pas au recodage n'est
pas un résultat.
"""

import argparse
import sys
from pathlib import Path

import numpy as np

AA = "ACDEFGHIKLMNPQRSTVWY"

RECODAGES = {
    # Dayhoff-6 : les six classes de substitution de Dayhoff, le recodage le plus utilisé
    # contre l'hétérogénéité de composition.
    "dayhoff6": {"AGPST": "0", "C": "1", "DENQ": "2", "HKR": "3", "ILMV": "4", "FWY": "5"},
    # SR-4 (Susko & Roger 2007), plus agressif : quatre états, conçu pour les jeux saturés
    # entre domaines du vivant.
    "sr4": {"AGNPST": "0", "CHWY": "1", "DEKQR": "2", "FILMV": "3"},
}


def lit_alignement(chemin):
    noms, seqs, nom, buf = [], [], None, []
    for brut in Path(chemin).read_text(encoding="utf-8").splitlines():
        if brut.startswith(">"):
            if nom is not None:
                noms.append(nom)
                seqs.append("".join(buf))
            nom, buf = brut[1:].split()[0], []
        elif nom is not None:
            buf.append(brut.strip())
    if nom is not None:
        noms.append(nom)
        seqs.append("".join(buf))
    if not seqs:
        raise SystemExit(f"aucune séquence lue dans {chemin}")
    L = {len(s) for s in seqs}
    if len(L) != 1:
        raise SystemExit(f"{chemin} n'est pas aligné : longueurs {sorted(L)[:5]}...")
    return noms, np.array([list(s.upper()) for s in seqs], dtype="<U1")


def chi2_sf(x, df):
    """Survie du chi2. scipy si présent, sinon on rend None et on compare à la valeur critique
    tabulée : le verdict ne doit pas dépendre de la présence d'une bibliothèque."""
    try:
        from scipy.stats import chi2
        return float(chi2.sf(x, df))
    except Exception:
        return None


def critique_05(df):
    """Valeur critique du chi2 à 5 %, approximation de Wilson-Hilferty. Elle n'est utilisée que
    si scipy manque, et vaut 30,1 pour df = 19 (valeur exacte 30,14)."""
    import math
    t = 2.0 / (9.0 * df)
    return df * (1.0 - t + 1.6448536 * math.sqrt(t)) ** 3


def composition(noms, mat, etats):
    """Test d'homogénéité de composition, séquence par séquence, contre la composition moyenne
    de l'alignement — le même test que celui qu'IQ-TREE imprime en tête de sortie.

    Les états ABSENTS du jeu entier sont retirés : leur effectif attendu est nul, la division
    rendrait `nan`, et une seule case suffisait à rendre `nan` la statistique de TOUTES les
    séquences — donc zéro composition déviante détectée, en silence. Les degrés de liberté
    suivent le nombre d'états réellement observés."""
    valides = np.isin(mat, list(etats))
    total = np.array([(mat[valides] == e).sum() for e in etats], dtype=float)
    presents = total > 0
    if presents.sum() < 2:
        raise SystemExit("moins de deux acides aminés distincts dans l'alignement")
    total, etats = total[presents], [e for e, ok in zip(etats, presents) if ok]
    freq = total / total.sum()
    df = len(etats) - 1
    resultats = []
    for i, nom in enumerate(noms):
        obs = np.array([(mat[i] == e).sum() for e in etats], dtype=float)
        n = obs.sum()
        if n < 20:
            resultats.append((nom, float("nan"), None, int(n)))
            continue
        att = freq * n
        stat = float((((obs - att) ** 2) / att).sum())
        resultats.append((nom, stat, chi2_sf(stat, df), int(n)))
    return resultats, df


def p_distances(mat):
    """p-distances par paire sur les colonnes où les DEUX séquences portent un résidu."""
    n = mat.shape[0]
    gap = np.isin(mat, ["-", "?", "X", "."])
    D = np.full((n, n), np.nan)
    couvert = np.full((n, n), 0)
    for i in range(n):
        paire = (~gap[i]) & (~gap)
        diff = (mat[i] != mat) & paire
        cnt = paire.sum(axis=1)
        with np.errstate(invalid="ignore", divide="ignore"):
            D[i] = np.where(cnt > 0, diff.sum(axis=1) / np.maximum(cnt, 1), np.nan)
        couvert[i] = cnt
    return D, couvert


def distances_patristiques(chemin, noms, max_paires, graine=20260922):
    """Distances patristiques par paire. `Phylo.distance` coûte cher et le nombre de paires
    croît en n^2 (246 feuilles = 30 000 appels, une demi-minute) : au-delà de --max-pairs on
    tire un ÉCHANTILLON de paires à graine fixe, ce qui suffit à estimer une pente et rend le
    résultat reproductible."""
    import random
    from Bio import Phylo
    arbre = Phylo.read(chemin, "newick")
    presents = {t.name: t for t in arbre.get_terminals()}
    idx = [i for i, nm in enumerate(noms) if nm in presents]
    n = len(noms)
    P = np.full((n, n), np.nan)
    paires = [(idx[a], idx[b]) for a in range(len(idx)) for b in range(a + 1, len(idx))]
    echantillonne = len(paires) > max_paires
    if echantillonne:
        paires = random.Random(graine).sample(paires, max_paires)
    for i, j in paires:
        d = arbre.distance(presents[noms[i]], presents[noms[j]])
        P[i, j] = P[j, i] = d
    return P, len(idx), echantillonne


def main():
    p = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[1])
    p.add_argument("--alignment", required=True)
    p.add_argument("--focus", nargs="*", default=[],
                   help="étiquettes dont le sort décide de la lecture (requête, donneurs)")
    p.add_argument("--tree", help="arbre déjà inféré, pour les distances patristiques")
    p.add_argument("--recode", choices=sorted(RECODAGES), default="dayhoff6")
    p.add_argument("--out-recoded", help="écrit l'alignement recodé, prêt à ré-inférer")
    p.add_argument("--max-pairs", type=int, default=5000,
                   help="paires tirées au sort pour la pente patristique (graine fixe)")
    p.add_argument("--p-sature", type=float, default=0.85,
                   help="p-distance au-delà de laquelle une paire n'informe plus (défaut 0,85)")
    p.add_argument("--out")
    a = p.parse_args()

    noms, mat = lit_alignement(a.alignment)
    inconnues = [f for f in a.focus if f not in noms]
    if inconnues:
        raise SystemExit("étiquettes --focus absentes de l'alignement : " + ", ".join(inconnues)
                         + "\n(ne JAMAIS repérer une séquence par son contenu quand un "
                           "identifiant existe : corriger l'étiquette, pas le script)")

    L = ["COMPOSITION ET SATURATION — le droit de lire l'arbre", "=" * 78, "",
         f"alignement : {len(noms)} séquences x {mat.shape[1]} colonnes"]

    # --- composition ---------------------------------------------------------------------
    res, df = composition(noms, mat, AA)
    echecs = [(nm, st, pv) for nm, st, pv, _eff in res
              if st == st and ((pv is not None and pv < 0.05)
                               or (pv is None and st > critique_05(df)))]
    frac = len(echecs) / len(res)
    focus_echec = [nm for nm, _s, _p in echecs if nm in a.focus]
    L += ["", f"-- composition en acides aminés (chi2 contre la moyenne du jeu, df = {df})",
          f"   séquences à composition déviante : {len(echecs)}/{len(res)} ({frac:.0%})"]
    if echecs:
        L.append("   les plus déviantes : " + ", ".join(
            f"{nm} (chi2 = {st:.0f})" for nm, st, _p in sorted(echecs, key=lambda x: -x[1])[:6]))
    if a.focus:
        L.append("   parmi les séquences décisives : "
                 + (", ".join(focus_echec) if focus_echec else "aucune"))
    heterogene = frac > 0.10 or bool(focus_echec)

    # --- saturation ----------------------------------------------------------------------
    D, couvert = p_distances(mat)
    triu = np.triu_indices(len(noms), 1)
    pd_ = D[triu]
    recouvrement = couvert[triu]
    fini = pd_[~np.isnan(pd_)]
    frac_sat = float((fini > a.p_sature).mean()) if fini.size else float("nan")
    L += ["", "-- saturation",
          f"   p-distances : médiane {np.median(fini):.2f}, maximum {fini.max():.2f}"
          if fini.size else "   p-distances : non calculables",
          f"   paires au-delà de {a.p_sature:.2f} (information quasi nulle) : {frac_sat:.0%}",
          f"   paires alignées sur moins de 50 colonnes communes : "
          f"{float((recouvrement < 50).mean()):.0%} (leur p-distance n'est pas fiable)"]

    pente = float("nan")
    if a.tree:
        P, n_feuilles, echantillonne = distances_patristiques(a.tree, noms, a.max_pairs)
        x, y = P[triu], pd_
        ok = (~np.isnan(x)) & (~np.isnan(y)) & (x > 0)
        if ok.sum() >= 30:
            # Régression à l'origine : la pente d'une p-distance contre la distance inférée
            # tombe vers 0 quand les substitutions se recouvrent. C'est le graphe de saturation
            # classique, réduit à son unique nombre.
            pente = float((x[ok] * y[ok]).sum() / (x[ok] ** 2).sum())
            L.append(f"   arbre lu : {n_feuilles} feuilles appariées ; pente p-distance contre "
                     f"distance patristique = {pente:.3f}"
                     + (f" (sur {a.max_pairs} paires tirées au sort, graine fixe)"
                        if echantillonne else f" (sur {int(ok.sum())} paires)"))
            L.append("   (une pente nettement inférieure à 1 signe des substitutions multiples "
                     "déjà recouvertes)")
    else:
        L.append("   --tree non fourni : la pente de saturation n'est pas mesurée, seule la "
                 "fraction de paires épuisées l'est")

    sature = (frac_sat == frac_sat and frac_sat > 0.20) or (pente == pente and pente < 0.5)

    # --- recodage ------------------------------------------------------------------------
    if a.out_recoded:
        table = {}
        for classe, code in RECODAGES[a.recode].items():
            for lettre in classe:
                table[lettre] = code
        with open(a.out_recoded, "w", encoding="utf-8") as fh:
            for i, nom in enumerate(noms):
                s = "".join(table.get(c, "-" if c in "-?X." else "-") for c in mat[i])
                fh.write(f">{nom}\n" + "\n".join(s[k:k + 60] for k in range(0, len(s), 60)) + "\n")
        L += ["", f"-- recodage {a.recode} écrit dans {a.out_recoded}",
              "   ré-inférer l'arbre dessus (modèle GTR/MK à états réduits) : un transfert qui",
              "   disparaît au recodage était une affaire de composition, pas d'ascendance."]

    # --- verdict --------------------------------------------------------------------------
    verdict = {(False, False): "HOMOGENE", (True, False): "HETEROGENE",
               (False, True): "SATURE", (True, True): "HETEROGENE_ET_SATURE"}[
        (bool(heterogene), bool(sature))]
    conseil = {
        "HOMOGENE": ["Un modèle homogène (LG+G, ou le meilleur selon ModelFinder) est licite.",
                     "Le recodage reste un contrôle utile mais n'est pas obligatoire ici."],
        "HETEROGENE": ["Composition hétérogène : inférer sous modèle à profils hétérogènes",
                       "(LG+C60+F+G, ou PMSF si le jeu est gros) ET vérifier que la topologie",
                       "décisive survit au recodage. Un modèle homogène rapprocherait ici des",
                       "lignées par leur composition seule."],
        "SATURE": ["Signal épuisé à cette distance : la topologie profonde n'est pas fiable.",
                   "Recoder, et surtout renoncer à lire un nichage profond comme une date ou",
                   "comme un transfert récent."],
        "HETEROGENE_ET_SATURE": [
            "Les deux artefacts sont présents : c'est la configuration où un faux transfert",
            "inter-domaine se fabrique tout seul. Profils hétérogènes ET recodage ET test",
            "topologique explicite sont requis ; un nichage lu sur un arbre homogène ne vaut",
            "rien dans cet état."],
    }[verdict]
    if focus_echec:
        conseil = conseil + ["", "Aggravant : la composition déviante touche des séquences "
                                 "DÉCISIVES (" + ", ".join(focus_echec) + "),",
                             "c'est-à-dire précisément celles dont le placement porte la "
                             "conclusion."]

    L += ["", "-- VERDICT " + "-" * 67] + conseil + ["", f"VERDICT_COMPOSITION: {verdict}"]
    texte = "\n".join(L)
    print(texte)
    if a.out:
        Path(a.out).write_text(texte + "\n", encoding="utf-8")
        print(f"\n[écrit dans {a.out}]", file=sys.stderr)


if __name__ == "__main__":
    main()
