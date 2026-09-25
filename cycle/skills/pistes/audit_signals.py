#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_signals.py — rend MÉCANIQUE le passage de l'audit de registre.

Pourquoi ce script existe (P70.6 de `predictops`, 2026-09-08). `status.py --audit`
portait déjà tous les contrôles, et `SKILL.md` prescrivait de le lancer à chaque
`/pistes read`. Mais une consigne n'est pas un mécanisme : pendant les deux jours
où personne ne l'a lancé, l'en-tête de `P67` a continué d'annoncer « CORRECTIF
PRÊT, NON DÉPLOYÉ » alors que le corps de la piste consignait le déploiement de la
veille, et un faux feu vert de déploiement en PRODUCTION a été demandé à
l'utilisateur sur cette base. Le défaut n'était pas l'absence d'outil, c'était
l'absence de déclenchement.

Deux modes, tous deux destinés aux hooks et silencieux quand tout va bien :

  --quiet     état COURANT du registre, une ligne par contrôle non nul.
              Hook SessionStart : dire le défaut AVANT qu'on s'appuie dessus.
  --diff SNAP état DIFFÉRENTIEL contre un instantané pris en début de session.
              Hook Stop : ne signaler que ce que la session vient de dégrader,
              jamais le stock — un contrôle qui reproche à chaque fin de session
              un défaut ancien et connu cesse d'être lu au bout de deux jours.

La distinction stock / dégradation est le cœur du dispositif. Le stock est
informatif et se traite quand on décide de le traiter ; la dégradation est
imputable à la session en cours, donc corrigeable immédiatement et à moindre
coût. Les mélanger produirait exactement le bruit permanent qui a déjà rendu
`completude_cahier` illisible avant son crible (60 % de faux positifs mesurés le
2026-09-07 sur `annotation_mtbc`).

Usage :
    python3 audit_signals.py [projet]                  # résumé lisible
    python3 audit_signals.py [projet] --quiet          # rien si registre sain
    python3 audit_signals.py [projet] --json
    python3 audit_signals.py [projet] --snapshot FIC   # écrit les compteurs
    python3 audit_signals.py [projet] --diff FIC       # signale les HAUSSES
    python3 audit_signals.py [projet] --pistes-ouvertes  # bloc pour SessionStart

Lecture seule sur le projet (hors `--snapshot`, qui n'écrit que son instantané).
Ne plante jamais : tout échec dégrade en sortie vide et code 0.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import status  # noqa: E402  (le module canonique porte TOUS les contrôles)

# Au-delà, on n'énumère plus : on compte. Une sonde de démarrage qui déroule
# quarante identifiants n'est plus lue, et le détail est à un `--audit` de là.
MAX_ITEMS = 4


def compteurs(root):
    """{clé: n} pour les dix contrôles, plus le contexte non compté."""
    col = status.collecte_audit(root)
    return ({cle: col[cle]["n"] for cle, _, _ in status.SECTIONS_AUDIT}, col)


# Contrôles NON `zero_attendu` mais suivis malgré tout : ceux dont une hausse signale un
# geste INCORRECT et RÉPARABLE, qui redescend dès qu'on le corrige. C'est le critère qui
# les sépare de `cahier_absents`, exclu du `--diff` le 2026-09-08 : celui-là monte par un
# geste PRESCRIT (documenter un travail inter-projets dans un cahier append-only) et ne
# redescend jamais, donc le suivre punit le bon geste. Étiqueter une feuille, à l'inverse,
# est un geste correct qui fait baisser le compteur.
#
# Ajouté le 2026-09-22 après un cas mesuré : une feuille créée en séance
# (`yersinia_pseudotuberculosis_virulence`, P1.3.f) est restée sans étiquette modèle/effort
# sans qu'aucun signal ne parte, ni au démarrage ni à la fin. Cause : `sans_etiquette` est
# `zero_attendu=False`, donc absent du `--diff` ; et `rendu_courant` rendait `[]` dès qu'il
# n'y avait aucun contrôle DUR en défaut, si bien que les contrôles mous n'étaient jamais
# affichés seuls. Un projet sain par ailleurs ne recevait donc jamais ce rappel — exactement
# le cas d'un projet jeune et bien tenu.
REPARABLES = {"sans_etiquette"}


def _phrase(col, cles):
    return " ; ".join(f"{col[c]['n']} {col[c]['libelle']}" for c in cles)


def rendu_courant(col):
    """Lignes à afficher pour l'état COURANT, ou [] si le registre est sain.

    Deux registres de gravité, et la distinction n'est pas cosmétique : les
    contrôles `zero_attendu` décrivent un registre en défaut, réparable et qui
    DOIT revenir à zéro ; les autres portent un bruit structurel déjà instruit
    (le cahier append-only nomme des identifiants qui n'ont jamais été des
    pistes — un script, une piste d'un autre projet, une version d'artefact —
    et six des huit cas de `predictops` ne sont pas filtrables mécaniquement).
    Les confondre ferait crier la sonde en permanence sur un défaut que personne
    ne peut fermer."""
    durs = [c for c, _, zero in status.SECTIONS_AUDIT if zero and col[c]["n"]]
    mous = [c for c, _, zero in status.SECTIONS_AUDIT if not zero and col[c]["n"]]
    if not durs:
        # Pas de défaut dur, mais un compteur RÉPARABLE non nul mérite un rappel : sans
        # lui, un projet sain par ailleurs n'entend jamais parler de ses feuilles non
        # étiquetées. Rappel explicitement non bloquant, et restreint aux réparables pour
        # ne pas ressortir à chaque démarrage le bruit structurel déjà instruit.
        rep = [c for c in mous if c in REPARABLES]
        if not rep:
            return []
        out = [f"Registre de pistes, rappel non bloquant — {_phrase(col, rep)}."]
        for cle in rep:
            items = col[cle]["items"][:MAX_ITEMS]
            # `items` porte des tuples pour certains contrôles et de simples
            # identifiants pour d'autres (`sans_etiquette`) : accepter les deux, sinon
            # le rappel annonce un effectif sans jamais dire QUELLES pistes, ce qui
            # oblige à relancer l'audit et vide le rappel de son intérêt.
            ids = [it[0] if isinstance(it, (list, tuple)) else it
                   for it in items if it]
            if ids:
                suite = ", …" if col[cle]["n"] > MAX_ITEMS else ""
                out.append(f"  · {col[cle]['libelle']} : {', '.join(map(str, ids))}{suite}")
        out.append("  Contrôle TOLÉRANT : étiqueter à la réouverture d'un projet ou à la "
                   "création d'une feuille, jamais en masse. Propositions : `python3 "
                   "${CLAUDE_PLUGIN_ROOT}/skills/routage/scripts/routage.py etiqueter <projet>`.")
        return out
    out = [f"Registre de pistes — {_phrase(col, durs)}."]
    for cle in durs:
        items = col[cle]["items"][:MAX_ITEMS]
        ids = [it[0] for it in items if isinstance(it, (list, tuple)) and it]
        if ids:
            suite = ", …" if col[cle]["n"] > MAX_ITEMS else ""
            out.append(f"  · {col[cle]['libelle']} : {', '.join(map(str, ids))}{suite}")
    if mous:
        out.append(f"  (aussi {_phrase(col, mous)} — bruit structurel connu, "
                   f"cf. P70.5 : instruire, ne pas compter comme perte.)")
    out.append("  Détail : `python3 ${CLAUDE_PLUGIN_ROOT}/skills/pistes/status.py <projet> --audit`.")
    return out


def rendu_diff(col, snap):
    """Lignes pour les seules HAUSSES depuis l'instantané, ou [] si rien n'a empiré.

    Restreint aux contrôles `zero_attendu` — correctif du 2026-09-08, le jour même de
    l'installation, après que ce hook eut bloqué sa PREMIÈRE fin de session réelle. Le
    motif était `cahier_absents` passé de 8 à 9, le nouveau venu étant `P16.19b`, une
    sous-piste d'un AUTRE projet citée en renvoi dans l'entrée de cahier qui documentait
    la séance. Or c'est un geste normal et même prescrit, et le cahier étant append-only
    l'identifiant ne s'en retire pas : le compteur ne redescendra jamais.

    Autrement dit, le hook aurait bloqué CHAQUE session documentant un travail
    inter-projets, c'est-à-dire précisément les mieux tenues. Un garde-fou qui punit le
    geste correct est désarmé en deux jours — le mode d'échec contre lequel tout ce
    dispositif est construit. Le `--diff` hérite donc de la distinction que porte déjà
    `SECTIONS_AUDIT` : les compteurs au bruit structurel instruit (cf. P70.5) montent
    légitimement, seuls ceux dont zéro est la valeur attendue constituent une
    dégradation.

    À noter pour qui touchera à ce hook : six cas de test synthétiques l'avaient validé,
    et c'est la première mise en situation RÉELLE qui a trouvé le défaut — parce qu'elle
    seule rejouait le geste ordinaire de fin de séance, écrire au cahier."""
    hausses = []
    for cle, lib, zero in status.SECTIONS_AUDIT:
        if not zero and cle not in REPARABLES:
            continue
        avant, apres = snap.get(cle), col[cle]["n"]
        if avant is None or apres <= avant:
            continue
        hausses.append((cle, lib, avant, apres))
    if not hausses:
        return []
    out = ["Le registre de pistes a été DÉGRADÉ pendant cette session :"]
    for cle, lib, avant, apres in hausses:
        out.append(f"  · {lib} : {avant} → {apres}")
        items = col[cle]["items"][-MAX_ITEMS:]
        ids = [it[0] if isinstance(it, (list, tuple)) else it
               for it in items if it]
        if ids:
            out.append(f"    (dernier(s) : {', '.join(map(str, ids))})")
    out.append("Corriger avant de terminer — ou consigner pourquoi c'est assumé. "
               "Détail : `status.py <projet> --audit`.")
    return out


def rendu_pistes_ouvertes(root, limite=14):
    """Le bloc de pistes ouvertes du SessionStart, calculé par l'OUTIL canonique.

    Remplace un `grep -E '\\[(en cours|à faire)\\]'` sur `pistes.md` qui a rendu
    3 pistes là où le registre en portait 12 (mesuré sur `predictops` le
    2026-09-08). Deux causes, mécaniques et invisibles : l'expression exigeait le
    crochet FERMANT juste après l'état, donc toute étiquette qualifiée
    (« [en cours, backend livré] ») échappait ; et elle était sensible à la
    casse, donc « [EN COURS] » aussi. L'assainissement de P70.4 — poser l'état en
    tête et garder le qualificatif à côté — a mécaniquement aggravé ce trou, le
    hook n'étant pas passé par `status.py`. C'est P70.1 à la lettre : le réflexe
    `grep` sur `pistes.md` ne remplace pas l'outil du skill."""
    states = status.lire_registre(root)[0]

    def ouvert(etat):
        return etat.endswith(("à faire", "en cours")) or etat == "état non déclaré"

    ouvertes = {}
    for pid, (etat, _src, _lib) in states.items():
        if ouvert(etat):
            ouvertes.setdefault(status.racine(pid), []).append(pid)

    majeures, orphelines, muettes = [], 0, 0
    for rac in sorted(ouvertes, key=status.sort_key):
        sous = [p for p in ouvertes[rac] if p != rac]
        # Une racine dont la piste MAJEURE est close mais qui garde des sous-pistes
        # ouvertes n'est pas une piste ouverte : l'annoncer comme telle rendrait la
        # liste fausse par excès, le défaut même que P70 traite. Elle n'est pas non
        # plus rien : ces sous-pistes sont soit un reliquat réel (cas P52, en-tête
        # `réalisé` sur une sous-piste « en attente »), soit — bien plus souvent —
        # une sous-piste que personne n'a jamais étiquetée et que `--open` retient
        # par prudence. Indécidable mécaniquement, donc AGRÉGÉ en une ligne : les
        # détailler noierait les pistes réellement ouvertes, mesuré sur `predictops`
        # (22 racines closes contre 12 pistes ouvertes).
        if rac in states and ouvert(states[rac][0]):
            etat, _s, lib = states[rac]
            majeures.append(f"{rac} [{status.mot_etat(etat)}] {lib[:78]}"
                            + (f"  (+{len(sous)} sous-piste(s) ouverte(s))" if sous else ""))
        elif sous:
            orphelines += len(sous)
            muettes += sum(1 for p in sous if states[p][0] == "état non déclaré")

    if not majeures and not orphelines:
        return []
    entete = (f"{len(majeures)} piste(s) majeure(s) ouverte(s) sur "
              f"{len({status.racine(p) for p in states})} — source `status.py --open`, "
              f"PAS un grep sur pistes.md")
    reste = len(majeures) - limite
    out = [entete] + majeures[:limite]
    if reste > 0:
        out.append(f"… et {reste} autre(s) : `status.py <projet> --open`.")
    if orphelines:
        out.append(f"(+ {orphelines} sous-piste(s) formellement ouverte(s) sous une piste "
                   f"majeure CLOSE, dont {muettes} sans état déclaré — reliquat d'étiquetage "
                   f"probable, pas du travail en cours.)")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--quiet", action="store_true",
                    help="ne rien écrire si le registre est sain (hook SessionStart)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--snapshot", metavar="FIC", help="écrire les compteurs courants")
    ap.add_argument("--diff", metavar="FIC", help="signaler les hausses depuis FIC")
    ap.add_argument("--pistes-ouvertes", action="store_true",
                    help="bloc des pistes ouvertes, calculé par status.py")
    args = ap.parse_args()

    root = status.project_root(args.path)
    if not root:
        if not (args.quiet or args.diff):
            print("Aucun projet structuré trouvé (pas de cahier_de_labo.md en remontant).",
                  file=sys.stderr)
        return 0

    if args.pistes_ouvertes:
        print("\n".join(rendu_pistes_ouvertes(root)))
        return 0

    n, col = compteurs(root)

    if args.snapshot:
        os.makedirs(os.path.dirname(os.path.abspath(args.snapshot)), exist_ok=True)
        with open(args.snapshot, "w", encoding="utf-8") as fh:
            json.dump({"racine": root, "compteurs": n}, fh, ensure_ascii=False)
        # Écrire l'instantané est un geste de hook : muet s'il n'est pas accompagné
        # d'un mode d'affichage (`--quiet` au SessionStart, qui veut les deux).
        if not (args.quiet or args.json or args.diff):
            return 0

    if args.diff:
        try:
            with open(args.diff, encoding="utf-8") as fh:
                snap = json.load(fh)
        except (OSError, ValueError):
            return 0            # pas d'instantané : rien à comparer, jamais d'alerte
        # Un instantané pris sur un AUTRE projet ne dit rien de celui-ci : sans ce
        # test, un `cd` en cours de session ferait comparer deux registres étrangers.
        if snap.get("racine") != root:
            return 0
        lignes = rendu_diff(col, snap.get("compteurs", {}))
        if lignes:
            print("\n".join(lignes))
            return 1            # l'appelant décide s'il bloque
        return 0

    if args.json:
        print(json.dumps({"racine": root, "compteurs": n}, ensure_ascii=False, indent=2))
        return 0

    lignes = rendu_courant(col)
    if lignes:
        print("\n".join(lignes))
    elif not args.quiet:
        print(f"Registre de pistes sain sur {os.path.basename(root)} : "
              f"les {sum(1 for _, _, z in status.SECTIONS_AUDIT if z)} contrôles à zéro "
              f"attendu sont à zéro.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Ne JAMAIS casser une session pour un signal — mais imprimer la TRACE,
        # pas seulement le message (leçon du 2026-08-12 sur `recadrage_signals`).
        import traceback
        print("[audit_signals] échec non bloquant :", file=sys.stderr)
        traceback.print_exc()
        sys.exit(0)
