#!/usr/bin/env python3
"""p164_bandeaux_nomenclature.py — poser un renvoi de peremption en tete des entrees qui
nomment des clades Bovis sans referent (P16.4).

Objet     : la nomenclature Bovis a change deux fois (trichotomie du 2026-06-22, decalage de
            niveau du 2026-07-20) et des entrees ecrites AVANT continuent de nommer des clades
            qui n'existent plus. Le foyer principal est `~/.agents/knowledge/tuberculosis.md`,
            que lisent TOUS les autres projets sans connaitre cette histoire. Le geste de P16.4
            n'est PAS de reecrire ces entrees (elles decrivent des faits dates, souvent encore
            vrais en tant que faits) mais de poser en TETE DE CHAQUE ENTREE concernee un renvoi
            qui dit que les noms cites n'ont plus de referent, et ou retrouver la traduction.
            Applique ainsi la regle posee par CG le 2026-09-11 : toute entree KB anterieure a la
            consolidation taxonomique de l'ete 2026 et qui NOMME des clades est suspecte par
            construction.

            Reutilise les regles de detection de `audit_connaissances_2026_09.py` (meme regex de
            label, meme autorite disque + registre, meme regex de marqueur de peremption), de
            sorte que ce que ce script marque est exactement ce que l'audit compte.

Entrées   : bdd/actuelle, registre_noeuds.tsv, et les cibles de l'audit (KB inter-projets,
            pistes/, cahier, CLAUDE.md, skills mtbc-lineages).
Sorties   : les fichiers cibles, modifies en place (sauvegarde `<nom>.bak_p164_<date>`), et un
            rapport `résultats/p164_bandeaux/RAPPORT.tsv`.
Réutilisable : oui — tout depot dont la nomenclature a bouge a le meme probleme. Candidat au
            skill `registres-sans-referent` avec le script d'audit (cf. P16.8).
Projet    : Bovis_full (P16.4)
Date      : 2026-09-12
"""
from __future__ import annotations

import argparse
import collections
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path

# === A ADAPTER AU DEPOT (skill `registres-sans-referent`) ===
# Ces chemins sont derives de l'emplacement du script, ce qui est correct quand il vit dans le
# `analyses/` d'un projet et faux quand il est appele depuis le skill. Fixer le projet cible par
# la variable d'environnement RSR_PROJET, ou editer PROJ ci-dessous.
#   RSR_PROJET=/chemin/vers/le/projet python audit_enonces.py
HERE = Path(__file__).resolve().parent
PROJ = Path(os.environ["RSR_PROJET"]).resolve() if os.environ.get("RSR_PROJET") else HERE.parent
sys.path.insert(0, str(HERE))
import audit_connaissances_2026_09 as A  # noqa: E402

OUT = PROJ / "résultats" / "p164_bandeaux"
STAMP = date.today().isoformat().replace("-", "")

# marqueur d'idempotence : un bandeau deja pose ne se repose pas
SENTINELLE = "NOMENCLATURE BOVIS PÉRIMÉE"
RX_PERIME_CI = re.compile(A.RX_PERIME.pattern, re.IGNORECASE)

# labels que le regex capte mais qui ne sont pas des noms de clade de la base :
#  - composites d'un autre systeme (`Bovis.2.2.1_Af1`, `Bovis.2.1.8_Af2`, `Bovis.1_proto`) ;
#  - labels d'EXEMPLE forges pour illustrer un piege de glob (`Bovis.2.10`, `...1.30`).
# Ils sont sortis du compte, pas du texte : l'entree qui les porte peut rester sans bandeau si
# elle ne porte que ceux-la.
RX_FAUX_POSITIF = re.compile(r"_(?:Af\d|proto|La\d|crown)\b")
# Un label force a deux chiffres (`Bovis.2.10`, `...1.30`) n'est un faux positif QUE si la ligne
# l'a forge pour illustrer un piege de nommage. Le filtre est donc CONTEXTUEL : morphologique, il
# jetait `Bovis.12`, qui est un vrai label de l'ancienne racine (elle allait jusqu'a `Bovis.53`).
RX_CONTEXTE_EXEMPLE = re.compile(r"fnmatch|glob|capterait|piège de nommage|startswith|"
                                 r"ne matche pas|NE capture PAS", re.IGNORECASE)


def verdict(lab: str, disque: dict, reg: set, prefixes: set) -> str:
    if A.RX_NOTATION.search(lab) or lab.startswith("Bovis_"):
        return "NOTATION"
    if lab in disque:
        return "EXISTE"
    if lab in reg or lab in prefixes:
        return "NOEUD_INTERNE"
    return "INCONNU"


# Un ajout horodate empile sous une entree sans rapport (`**[2026-07-20] ...`) est une entree a
# part entiere sans titre : la KB en compte plusieurs, et un bandeau pose en tete de l'entree qui
# les heberge annoncerait des clades absents de son debut.
RX_AJOUT = re.compile(r"^\*\*\[\d{4}-\d{2}-\d{2}\]")


def ancrages_hors_code(lignes: list[str]) -> list[int]:
    """index 0-based des points d'ancrage : titres markdown et ajouts horodates, hors blocs ```."""
    out, dans_code = [], False
    for i, l in enumerate(lignes):
        if l.lstrip().startswith("```"):
            dans_code = not dans_code
            continue
        if dans_code:
            continue
        if re.match(r"^#{1,6} ", l) or RX_AJOUT.match(l.lstrip()):
            out.append(i)
    return out


def point_insertion(lignes: list[str], i_anc: int) -> int:
    """Ou inserer : sous un TITRE (en sautant la ligne vide), AVANT un ajout horodate."""
    if RX_AJOUT.match(lignes[i_anc].lstrip()):
        return i_anc
    j = i_anc + 1
    if j < len(lignes) and lignes[j].strip() == "":
        j += 1
    return j


def deja_marque(lignes: list[str], j: int, avant_ajout: bool = False) -> bool:
    """L'entree porte-t-elle DEJA un avertissement de peremption ?

    Deux formes acceptees : la sentinelle de ce script (idempotence stricte), et tout bloc de
    citation `>` portant un marqueur de peremption en tete d'entree — c'est le cas du skill
    `mtbc-lineages`, dont la section HISTORIQUE est deja bandee a la main et n'a pas besoin d'un
    second avertissement.
    """
    # La fenetre s'arrete au prochain point d'ancrage (titre, ou ajout empile `**[2026-...`) :
    # sinon elle attrape le bandeau de l'entree SUIVANTE quand deux ajouts sont proches, et
    # laisse alors une entree non marquee. Une fenetre simplement plus courte, elle, rate les
    # bandeaux ecrits a la main plus bas et fabrique des doublons.
    if avant_ajout:
        # Bandeau pose AU-DESSUS de l'ajout : c'est la qu'il faut le chercher.
        return any(SENTINELLE in l or (l.lstrip().startswith(">") and RX_PERIME_CI.search(l))
                   for l in lignes[max(0, j - 3):j])
    fenetre = []
    for l in lignes[j:j + 14]:
        if re.match(r"^#{1,6} ", l) or RX_AJOUT.match(l.lstrip()):
            break
        fenetre.append(l)
    if any(SENTINELLE in l for l in fenetre):
        return True
    # insensible a la casse : les bandeaux ecrits a la main crient en majuscules
    # (« TOUT ce qui suit est HISTORIQUE », « N'EXISTE PLUS »), que RX_PERIME ne voit pas telles
    # quelles. Ce meme angle mort fait que l'audit SURESTIME le nombre de citations nues.
    return any(l.lstrip().startswith(">") and RX_PERIME_CI.search(l) for l in fenetre)


# au-dela de cette distance au titre, la citation appartient a un ajout empile sous une entree
# sans rapport (la KB en compte plusieurs) : le bandeau s'ancre alors sur la ligne elle-meme,
# faute de quoi il annoncerait des clades absents du debut de l'entree.
SEUIL_ANCRAGE = 25
# ... sauf dans un fichier de PISTES, ou les sous-pistes sont des items de liste lus par un
# parseur (`~/.claude/skills/pistes/status.py`, RE_ITEM ancre sur `- Pn.x`). Un bloc insere entre
# deux items serait rattache au corps de l'item precedent : un fichier de pistes ne recoit donc
# qu'UN bandeau, en tete, qui couvre tout le registre.
SANS_ANCRAGE_LIGNE = ("piste_", "cahier")


def bandeau(labels: list[str]) -> list[str]:
    liste = ", ".join(f"`{l}`" for l in sorted(labels))
    return [
        f"> ⚠ **{SENTINELLE} — marqué le 2026-09-12 (P16.4).** Les clades nommés ici "
        f"({liste}) n'ont plus de référent dans `bdd/actuelle` : ces noms sont antérieurs à la "
        "trichotomie du 2026-06-22 ou au décalage de niveau du 2026-07-20. Le FAIT consigné dans "
        "l'entrée reste ce qu'il était ; c'est son adressage qui est mort. Avant tout réemploi, "
        "ré-identifier le clade par sa biologie (souches témoins, RD, hôte, pays, effectif) et "
        "non par son nom, puis le relire au registre autoritaire. Voir le bandeau en tête de "
        "fichier.",
        "",
    ]


ENTETE = """> [!IMPORTANT]
> **[2026-09-12] Un nom de clade Bovis n'est pas une donnée stable, et les entrées ci-dessous
> écrites avant l'été 2026 en portent beaucoup qui ne désignent plus rien.** La nomenclature a
> changé deux fois : **trichotomie du 2026-06-22** (backbone ré-encodé, `Bovis_proto` → `Bovis.1`,
> l'ancien crown → `Bovis.2`, donc tout `Bovis.1.*` d'avant est devenu `Bovis.2.1.*`, et
> `Bovis.3` a disparu) puis **décalage de niveau du 2026-07-20** (`Bovis.2.2.*` → `Bovis.2.2.1.*`
> pour loger un clade sœur nouveau). S'y ajoutent les re-peignages de fin juin, qui ont déplacé
> du CONTENU sans passer par un mapping : `Bovis.2.1.2.1` désignait le clade vaccinal le
> 2026-06-22 et ne porte plus que 5 souches sauvages aujourd'hui, le BCG étant
> `Bovis.2.1.2.2.2.1`.
>
> **Règle, portée par CG le 2026-09-11** : toute entrée antérieure à la consolidation
> taxonomique de l'été 2026 et qui NOMME des clades est suspecte par construction. Re-vérifier
> l'existence des répertoires cités dans `bdd/actuelle` AVANT de réutiliser une mesure, et se
> rappeler qu'un clade se ré-identifie par sa biologie (souches témoins, RD, hôte, pays,
> effectif), jamais par son nom. Localiser le clade vaccinal par sa délétion RD1, jamais par son
> label.
>
> **Où lire la vérité du jour** : registre autoritaire
> `mtbc/lineage_navigator/résultats/bovis_validation/registre_noeuds.tsv` (gouvernance de la
> taxonomie Bovis, décision CG du 2026-09-08) ; mappings des deux renommages dans
> `mtbc/Bovis_full/résultats/bovis_rename_2026-06-22/mapping.tsv` et
> `résultats/bovis2_rename_mapping.tsv` ; correspondance des trois racines traduites dans
> `mtbc/Bovis_full/résultats/P12_correspondance/`. Les entrées concernées portent un renvoi
> ⚠ en tête, posé mécaniquement par `Bovis_full/analyses/p164_bandeaux_nomenclature.py`.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="écrire (sinon simulation)")
    args = ap.parse_args()

    disque, reg = A.autorite()
    prefixes = set(A.cumul(disque))
    OUT.mkdir(parents=True, exist_ok=True)

    # Le cahier de labo est APPEND-ONLY : une entree passee ne se retouche pas, meme pour y
    # poser un avertissement. Les deux lignes qu'il porte sont signalees dans l'entree du jour.
    EXCLUS = {"cahier"}

    rapport = []
    for nom, p in A.cibles_completes():
        if nom in EXCLUS:
            continue
        txt = p.read_text(encoding="utf-8")
        lignes = txt.splitlines()
        # 1. reperer les lignes qui citent un label sans referent, sans marqueur de peremption
        nues: dict[int, list[str]] = {}
        for i, ligne in enumerate(lignes):
            if A.RX_PERIME.search(ligne):
                continue
            labs = []
            for lab in sorted(set(A.RX_LABEL.findall(ligne))):
                if lab in ("Bovis_full", "Bovis_emergence", "Bovis_proto",
                           "Bovis_slaughter_bottleneck"):
                    continue
                if RX_FAUX_POSITIF.search(lab):
                    continue
                if re.search(r"[._]\d{2,}$", lab) and RX_CONTEXTE_EXEMPLE.search(ligne):
                    continue
                if verdict(lab, disque, reg, prefixes) == "INCONNU":
                    labs.append(lab)
            if labs:
                nues[i] = labs
        if not nues:
            continue
        # 2. rattacher chaque ligne a son entree (titre reel le plus proche au-dessus)
        ancres = ancrages_hors_code(lignes)
        # Dans un fichier de PISTES, les sous-pistes sont des items de liste lus par un parseur
        # (`~/.claude/skills/pistes/status.py`) : un seul bandeau, en tete de registre.
        if nom.startswith("piste_"):
            ancres = ancres[:1]
        par_entree: dict[int, set[str]] = collections.defaultdict(set)
        for i, labs in nues.items():
            cands = [t for t in ancres if t <= i]
            if not cands:
                continue
            par_entree[max(cands)].update(labs)
        # 3. inserer de bas en haut pour ne pas decaler les index
        n_pose = 0
        for i_anc in sorted(par_entree, reverse=True):
            est_ajout = bool(RX_AJOUT.match(lignes[i_anc].lstrip()))
            j = point_insertion(lignes, i_anc)
            if deja_marque(lignes, j, avant_ajout=est_ajout):
                continue
            labs = sorted(par_entree[i_anc])
            rapport.append((nom, str(p), i_anc + 1, lignes[i_anc].strip()[:110],
                            ";".join(labs), "ajout" if est_ajout else "entrée"))
            if args.apply:
                lignes[j:j] = bandeau(labs)
            n_pose += 1
        if n_pose and args.apply:
            shutil.copy2(p, p.with_name(p.name + f".bak_p164_{STAMP}"))
            corps = "\n".join(lignes) + ("\n" if txt.endswith("\n") else "")
            # 4. entete global, uniquement sur la KB inter-projets
            if nom == "kb_tuberculosis" and "Où lire la vérité du jour" not in corps:
                l2 = corps.splitlines()
                k = 1 if l2 and l2[0].startswith("# ") else 0
                while k < len(l2) and l2[k].strip() == "":
                    k += 1
                l2[k:k] = ENTETE.rstrip("\n").splitlines() + [""]
                corps = "\n".join(l2) + "\n"
            p.write_text(corps, encoding="utf-8")
        print(f"{'POSE' if args.apply else 'SIMU'} {n_pose:3d} bandeau(x)  {nom}")

    with (OUT / "RAPPORT.tsv").open("w", encoding="utf-8") as f:
        f.write("fichier\tchemin\tligne_ancrage\tancre\tlabels_sans_referent\tportee\n")
        for r in rapport:
            f.write("\t".join(str(x) for x in r) + "\n")
    print(f"\ntotal : {len(rapport)} entrées marquées -> {OUT/'RAPPORT.tsv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
