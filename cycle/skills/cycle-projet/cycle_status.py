#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cycle_status.py — situe un projet de recherche dans son cycle de vie.

Lecture seule, stdlib uniquement, ne plante jamais (tout échec dégrade en None).
Rend des MÉTRIQUES et une phase OBSERVÉE, jamais un verdict de porte : le
franchissement d'une porte (point fixe) est instruit par le skill `cycle-projet`,
qui lit les fichiers. Ce script existe pour que le désaccord entre la phase
DÉCLARÉE (en-tête de etat_des_decouvertes.md) et ce que les artefacts MONTRENT
soit détecté sans flair.

Usage :
    python3 cycle_status.py [projet]            # résumé lisible
    python3 cycle_status.py [projet] --json     # JSON complet
    python3 cycle_status.py [projet] --quiet    # une ligne SI désaccord, sinon rien
                                                # (destiné au hook SessionStart)

`projet` : chemin absolu, ou nom relatif à ~/docs/codes/mtbc/, ou défaut = cwd
(en remontant jusqu'au premier ancêtre STRICT portant cahier_de_labo.md).
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

import os

# Raccourci de nommage : un nom de projet relatif nu (pas "." ni "/") se résout
# d'abord ici avant d'être cherché depuis le cwd. Défaut = l'environnement pour
# lequel ce skill a été conçu (le plugin `cycle` est domain-agnostic, ce
# raccourci ne l'est pas) ; surchargeable pour un autre genre ou un autre
# clone du dépôt public. À garder aligné avec la même constante dans
# `recadrage/recadrage_signals.py` (même mécanique de résolution).
MTBC_ROOT = Path(os.environ.get("CYCLE_PROJECT_SHORTCUT_ROOT",
                                 str(Path.home() / "docs" / "codes" / "mtbc"))).expanduser()

PHASES = {
    1: "analyse primaire",
    2: "valorisation et squelette",
    3: "itération draft",
    4: "finalisation et soumission",
    5: "clôture",
}

# Registres du pipeline qualité (phase 3) et le skill qui les maintient.
REGISTRES_QUALITE = {
    "claim_check.md": "/claim-check",
    "fig_check.md": "/fig-check",
    "review/INDEX.md": "/manuscript-review",
}

# Un manuscrit sous ce seuil de lignes n'est pas un draft : c'est un squelette.
LIGNES_DRAFT_MINI = 250
# En dessous, le main.tex n'est même pas un squelette délibéré : c'est encore le
# gabarit posé par /init-project (~93 lignes, sections vides). Sans ce seuil, tout
# projet fraîchement scaffoldé serait annoncé en phase 2.
LIGNES_SQUELETTE_MINI = 130

# Puces de gabarit à ne pas compter comme des acquis en §2.
PLACEHOLDERS = ("[à renseigner]", "(rien encore)", "[À REGÉNÉRER", "néant")


def _index_a_des_entrees(txt: str) -> bool:
    """Une table Markdown '| Date | ... |' a-t-elle au moins une ligne de DONNÉE
    sous son séparateur '|---|---|' ?

    `/init-project` crée `review/INDEX.md` avec l'en-tête de table mais aucune
    ligne : sa seule PRÉSENCE ne prouve donc rien. Défaut vécu (SpacerEgalVirus,
    2026-08-26) : `review✓` affiché alors qu'aucun `/manuscript-review` n'avait
    jamais tourné, parce que le fichier gabarit existait déjà. Un registre
    (`review/INDEX.md`) qui certifie une porte doit être lu pour son CONTENU, pas
    pour sa présence.
    """
    lignes = txt.splitlines()
    for i, l in enumerate(lignes):
        if re.match(r"^\s*\|[\s:|-]+\|\s*$", l):
            return any(x.strip().startswith("|") for x in lignes[i + 1:])
    return False


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def trouver_racine(depart: Path) -> Path | None:
    """Premier ancêtre STRICT (cwd inclus) portant cahier_de_labo.md, 6 niveaux max.

    Jamais un répertoire frère : c'est le faux positif historique du hook Stop.
    """
    d = depart.resolve()
    for _ in range(6):
        if (d / "cahier_de_labo.md").is_file():
            return d
        if d.parent == d:
            break
        d = d.parent
    return None


def resoudre(arg: str | None) -> Path | None:
    if arg:
        p = Path(arg).expanduser()
        if not p.is_absolute():
            # Un chemin relatif RÉEL (« .. », « ./x ») doit primer sur le raccourci
            # par nom de projet MTBC, sinon « .. » se résout en MTBC_ROOT/".."
            local = (Path.cwd() / arg).resolve()
            cand = MTBC_ROOT / arg
            p = local if (arg.startswith((".", "/")) or local.is_dir()) else cand
        if not p.is_dir():
            return None
        # Un répertoire quelconque n'est pas un projet : exiger le cahier, sinon
        # remonter. Sans ce contrôle, on rend des métriques vides et crédibles.
        return trouver_racine(p.resolve())
    return trouver_racine(Path.cwd())


# ── État des découvertes ─────────────────────────────────────────────────────

# Deux libellés coexistent dans les états déjà écrits — `**Phase :** 4/5` (forme
# canonique du skill) et `**Phase du cycle de vie :** 4 — ...` (forme produite par
# /etat sur plusieurs projets), avec ou sans le `/5`. N'en reconnaître qu'un seul
# faisait annoncer « PHASE NON DÉCLARÉE » sur des projets qui la déclarent bel et
# bien, et le hook SessionStart répercutait ce faux négatif à chaque ouverture.
RE_PHASE = re.compile(r"\*\*Phase(?:\s+du\s+cycle\s+de\s+vie)?\s*:\*\*\s*([1-5])"
                      r"(?:\s*/\s*5)?")
# Repli : sur au moins un projet clos (SpacerEgalVirus), la phase est imbriquée
# dans le texte du champ **Voie :** (« **Voie : article. Phase 4/5 (…)** »),
# le gras couvrant toute la phrase et non le seul « Voie : » — RE_VOIE ne
# matche donc même pas. N'est cherché QUE dans le PREMIER bloc du fichier
# (avant la première section « ## »), jamais dans le corps, pour ne pas
# attraper une mention de phase hors de tout contexte de déclaration.
RE_PHASE_DANS_ENTETE = re.compile(r"[Pp]hase\s+([1-5])\s*/\s*5")
RE_ITERATION = re.compile(r"\*\*Itération\s*:\*\*\s*(\d+)")
# La VOIE du projet (arbitrage CG 2026-09-11). Les cinq phases et les sept portes
# ne valent que pour la voie ARTICLE : un projet dont le livrable est un mail de
# réponse à un collègue ou un skill reforgé n'a pas de phase, et lui en réclamer
# une produit un faux « PHASE NON DÉCLARÉE » à chaque ouverture de session.
# Absence de la ligne = « article », par compatibilité avec les états déjà écrits.
RE_VOIE = re.compile(r"\*\*Voie\s*:\*\*\s*([^*\n]+)")
VOIES_SANS_PHASE = ("réponse", "reponse", "réoutillage", "reoutillage", "outillage")
RE_REECRIT = re.compile(r"\*\*Réécrit le\s*:\*\*\s*(\d{4}-\d{2}-\d{2})")
# C1/C2 (essaimage vers un projet vivant / vers le registre parent) doivent être
# reconnus AVANT le C nu, sinon « C1 » ne matche pas du tout (le \b échoue entre
# « C » et « 1 ») et l'acquis est compté sans destination — même alternative que
# recadrage_signals.py, dont ce regex avait divergé.
RE_DEST = re.compile(r"destination\s*:\s*\**(C[12]|[ABCDE])(?![\w])", re.IGNORECASE)
# Un acquis de §2 est une puce de premier niveau.
RE_ACQUIS = re.compile(r"^-\s+\S", re.MULTILINE)


def section(txt: str, n: int) -> str:
    """Corps de la section '## <n>.' du squelette /etat (8 sections + §9)."""
    m = re.search(rf"^##\s*{n}\.\s.*$", txt, re.MULTILINE)
    if not m:
        return ""
    debut = m.end()
    suite = re.search(r"^##\s", txt[debut:], re.MULTILINE)
    return txt[debut: debut + suite.start()] if suite else txt[debut:]


def lire_etat(root: Path) -> dict:
    p = root / "etat_des_decouvertes.md"
    if not p.is_file():
        return {"present": False}
    txt = _read(p)
    m_phase = RE_PHASE.search(txt)
    m_iter = RE_ITERATION.search(txt)
    m_reec = RE_REECRIT.search(txt)
    m_voie = RE_VOIE.search(txt)
    voie = m_voie.group(1).strip() if m_voie else None
    # « article + réoutillage » garde sa phase : dès qu'une voie article est
    # déclarée, le rail s'applique. Seule une voie EXCLUSIVEMENT (b) et/ou (c)
    # dispense de phase.
    voie_l = (voie or "").lower()
    hors_rail = bool(voie) and "article" not in voie_l and any(
        v in voie_l for v in VOIES_SANS_PHASE)

    phase_declaree = int(m_phase.group(1)) if m_phase else None
    if phase_declaree is None:
        entete = txt.split("\n##", 1)[0]
        m_phase_entete = RE_PHASE_DANS_ENTETE.search(entete)
        if m_phase_entete:
            phase_declaree = int(m_phase_entete.group(1))

    corps2 = section(txt, 2)
    acquis = [l for l in corps2.splitlines()
              if RE_ACQUIS.match(l) and not any(ph in l for ph in PLACEHOLDERS)]
    dests = RE_DEST.findall(corps2)
    return {
        "present": True,
        "phase_declaree": phase_declaree,
        "voie": voie,
        "hors_rail": hors_rail,
        "iteration": int(m_iter.group(1)) if m_iter else None,
        "reecrit_le": m_reec.group(1) if m_reec else None,
        "n_acquis": len(acquis),
        "n_tagues": len(dests),
        "sans_destination": max(0, len(acquis) - len(dests)),
    }


# ── Plan narratif (porte 2) ──────────────────────────────────────────────────

RE_PN_ROW_M = re.compile(r"^\s*\|\s*M\d+\s*\|", re.MULTILINE)
RE_PN_ROW_B = re.compile(r"^\s*\|\s*B\d+\s*\|", re.MULTILINE)
RE_PN_RANG = re.compile(r"\|\s*(PORTEUR|BASCULE|MENTION|SUPPL[EÉ]MENTAIRE|S[EÉ]RENDIPIT[EÉ])\s*\|")
RE_PN_MAJ = re.compile(r"\*\*Mis à jour le :\*\*\s*(\d{4}-\d{2}-\d{2})")


def lire_plan_narratif(root: Path) -> dict:
    """Présence et complétude de `plan_narratif.md` (porte 2, skill /narratif).

    On ne juge pas la qualité du narratif — cela ne se mesure pas. On rend les
    trois chiffres qui disent si l'étape a été FAITE : combien de maillons, combien
    de bascules, et combien d'acquis ont reçu un rang. Un plan à zéro rang est un
    gabarit posé, pas une étape franchie.
    """
    p = root / "plan_narratif.md"
    if not p.is_file():
        return {"present": False}
    txt = _read(p)
    m = RE_PN_MAJ.search(txt)
    return {
        "present": True,
        "maj": m.group(1) if m else None,
        "maillons": len(RE_PN_ROW_M.findall(txt)),
        "bascules": len(RE_PN_ROW_B.findall(txt)),
        "rangs": len(RE_PN_RANG.findall(txt)),
    }


# ── Pistes ───────────────────────────────────────────────────────────────────

RE_PISTE_MAJEURE = re.compile(r"^##\s+P\d+\..*?\[(à faire|en cours|réalisé|abandonné)\]",
                              re.MULTILINE)
RE_SOUS_PISTE = re.compile(r"^\s+-\s+P[\d.]+.*?\[(à faire|en cours)\]", re.MULTILINE)


def lire_pistes(root: Path) -> dict:
    p = root / "pistes.md"
    if not p.is_file():
        return {"present": False}
    txt = _read(p)
    majeures = RE_PISTE_MAJEURE.findall(txt)
    ouvertes = [e for e in majeures if e in ("à faire", "en cours")]
    # Architecture index + détail (2026-08-20, cf. skill /pistes) : pistes.md
    # ne garde plus les sous-pistes en clair, elles vivent dans pistes/Px.md.
    # Sans ce fallback, sous_pistes_ouvertes tomberait toujours à 0 sur un
    # projet restructuré.
    sous_pistes = len(RE_SOUS_PISTE.findall(txt))
    detail_dir = root / "pistes"
    if detail_dir.is_dir():
        for f in detail_dir.glob("P*.md"):
            sous_pistes += len(RE_SOUS_PISTE.findall(_read(f)))
    return {
        "present": True,
        "majeures": len(majeures),
        "ouvertes": len(ouvertes),
        "sous_pistes_ouvertes": sous_pistes,
    }


# ── Littérature ──────────────────────────────────────────────────────────────

def lire_litterature(root: Path) -> dict:
    d = root / "litterature_review"
    idx = d / "index.md"
    bib = d / "references.bib"
    txt = _read(idx)
    # Un index de scaffold non renseigné fait ~20 lignes de gabarit.
    lignes = len([l for l in txt.splitlines() if l.strip()])
    n_refs = _read(bib).count("@")
    return {
        "present": d.is_dir(),
        "index_lignes": lignes,
        "refs_bib": n_refs,
        "renseignee": lignes > 25 or n_refs > 0,
    }


# ── Manuscrit et registres qualité ───────────────────────────────────────────

def _lire_un_manuscrit(root: Path, art: Path) -> dict:
    main = art / "main.tex"
    txt = _read(main)
    lignes = len(txt.splitlines())
    registres = {}
    for rel, skill in REGISTRES_QUALITE.items():
        # Selon les projets, les registres vivent à la racine OU dans article*/ :
        # chercher aux deux endroits, sinon un registre existant passe pour absent.
        # Un second manuscrit (article2/, articleB/...) porte souvent son propre
        # registre suffixé (claim_check_article2.md) : le chercher aussi à la
        # racine sous ce nom, sinon il passe pour absent alors qu'il existe.
        stem, ext = rel.rsplit(".", 1) if "." in rel else (rel, "")
        suffixe = f"{stem}_{art.name}.{ext}" if ext else f"{stem}_{art.name}"
        candidats = (art / rel, root / rel, root / suffixe)
        f = next((c for c in candidats if c.is_file()), None)
        if f is not None:
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime).date().isoformat()
            except Exception:
                mtime = None
            # review/INDEX.md est une TABLE : sa présence seule ne prouve rien,
            # un projet fraîchement scaffoldé en a une vide. Les autres registres
            # (claim_check.md, fig_check.md) sont rédigés en prose dès leur
            # création par le skill correspondant, la présence y reste un proxy
            # valable.
            vide = rel == "review/INDEX.md" and not _index_a_des_entrees(_read(f))
            registres[rel] = {"present": not vide, "skill": skill, "maj": mtime,
                              "chemin": str(f.relative_to(root)), "vide": vide}
        else:
            registres[rel] = {"present": False, "skill": skill, "maj": None,
                              "chemin": None, "vide": False}
    return {
        "present": True,
        "repertoire": art.name,
        "lignes": lignes,
        "sections": len(re.findall(r"^\\section\{", txt, re.MULTILINE)),
        "figures": len(set(re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", txt))),
        "est_draft": lignes >= LIGNES_DRAFT_MINI,
        "version_fr": (art / "main_fr.tex").is_file(),
        "declaration_ia": bool(
            re.search(r"generative AI|artificial intelligence|assistance IA|agent IA|Codex|Claude", txt, re.IGNORECASE)
        ),
        "registres": registres,
    }


def lire_manuscrits(root: Path) -> list[dict]:
    """Un projet peut porter plusieurs manuscrits (article/, article2/...).

    Chercher TOUS les `article*/main.tex`, pas seulement `article/` : un second
    manuscrit invisible à ce script passait pour un projet fini alors que son
    propre pipeline qualité n'avait jamais été instruit (cf. incident
    SpacerEgalVirus 2026-08-26, où seul `article/` était vu).
    """
    dirs = sorted(
        p.parent for p in root.glob("article*/main.tex")
    )
    return [_lire_un_manuscrit(root, d) for d in dirs]


def lire_manuscrit(root: Path) -> dict:
    """Rétrocompatibilité : le premier manuscrit trouvé (`article/` si présent)."""
    manus = lire_manuscrits(root)
    if not manus:
        return {"present": False}
    principal = next((m for m in manus if m["repertoire"] == "article"), manus[0])
    return principal


# ── Cahier ───────────────────────────────────────────────────────────────────

def lire_cahier(root: Path) -> dict:
    txt = _read(root / "cahier_de_labo.md")
    entrees = re.findall(r"^##\s+(\d{4}-\d{2}-\d{2})", txt, re.MULTILINE)
    return {"entrees": len(entrees), "derniere": entrees[-1] if entrees else None}


# ── Porte 1 : rétablissement après un reboot hard (skill `reboot`, AB5) ──────

RE_AFF_COMPTEURS = re.compile(
    r"compteurs:\s*\n\s*non_testee:\s*(\d+)\s*\n\s*en_test:\s*(\d+)\s*\n"
    r"\s*prouvee:\s*(\d+)\s*\n\s*refutee:\s*(\d+)\s*\n\s*abandonnee:\s*(\d+)"
)
# `| A1 | P1 | énoncé | … | statut | … |` : colonne 1 l'identifiant, 2 la
# priorité, 7 le statut. Lu par position, jamais par en-tête traduit.
RE_AFF_LIGNE = re.compile(r"^\|\s*(A\d+)\s*\|\s*(P[123])\s*\|(.*)$", re.MULTILINE)


def lire_affirmations(root: Path) -> dict:
    """`affirmations.md` : l'acquis legacy en transit après un reboot `hard`.

    La rédaction est bloquée (porte 1) tant qu'une affirmation STRUCTURANTE (P1)
    reste `non testée` ou `en test` : un manuscrit bâti sur un acquis hérité mais
    non re-prouvé est exactement ce que le reboot existe pour empêcher. C'est un
    artefact TRANSITOIRE — absent chez l'immense majorité des projets, gelé dans
    l'archive au `clore` — donc son absence n'est jamais un défaut.

    Lecture directe du fichier plutôt qu'import de `reboot.py` : ce dernier
    importe déjà `cycle_status` pour lire la phase, et l'inverse ferait une
    boucle.
    """
    fichier = root / "affirmations.md"
    if not fichier.is_file():
        return {"present": False}
    txt = _read(fichier)
    m = RE_AFF_COMPTEURS.search(txt)
    compteurs = {}
    if m:
        compteurs = dict(zip(("non_testee", "en_test", "prouvee", "refutee", "abandonnee"),
                             (int(g) for g in m.groups())))
    p1_non_tranchees = [
        ident for ident, _p, reste in RE_AFF_LIGNE.findall(txt)
        if _p == "P1" and ("non testée" in reste or "en test" in reste)
    ]
    return {
        "present": True,
        "compteurs": compteurs,
        "p1_non_tranchees": p1_non_tranchees,
        "redaction_bloquee": bool(p1_non_tranchees),
    }


# ── Porte 1 : reboot HARD clos, traces post-clôture (AO1/AO2) ────────────────

RE_REBOOT_CLOS = re.compile(r"-\s+\*\*Clos le\s+(\d{4}-\d{2}-\d{2})\s*:\*\*")
# Les deux libellés fixés par `reboot.py cmd_clore` (AO1) ; le texte qui suit
# « : » varie en prose (parenthèse cahier, renvoi), donc non ancré en fin de
# ligne — seul « à faire » / « fait le AAAA-MM-JJ » compte.
RE_TRACE_REBOOT = re.compile(
    r"^\s*-\s+(recadrage post-clôture|revue de littérature ciblée post-clôture)"
    r"[^\n:]*:\s*(?:à faire|fait le\s+(\d{4}-\d{2}-\d{2}))",
    re.MULTILINE)


def _bloc_reboot(txt: str) -> str:
    m = re.search(r"^##\s+Reboot\s*$", txt, re.MULTILINE)
    if not m:
        return ""
    debut = m.end()
    suite = re.search(r"^##\s", txt[debut:], re.MULTILINE)
    return txt[debut: debut + suite.start()] if suite else txt[debut:]


def lire_reboot(root: Path) -> dict:
    """Bloc `## Reboot` du `CLAUDE.md` du projet : une clôture de reboot HARD
    ROUVRE la porte 1 (arbitrage CG 2026-09-25, cas La4 ; skill `cycle-projet`,
    encadré Porte 1 ; `/reboot` étape 4), même si P1/P3/P4 sont soldés. Elle ne
    se referme qu'une fois les DEUX traces post-clôture — recadrage, revue de
    littérature ciblée — passées de « à faire » à « fait le AAAA-MM-JJ » à une
    date au moins égale à celle de la clôture. Traces satisfaites ne veut pas
    dire porte 1 FRANCHIE : elles ne font que rendre applicables les critères
    ORDINAIRES de la porte 1 (pistes ouvertes, deux tours à vide) — mesurés par
    ailleurs (`lire_pistes`). Mesure seulement ; `gate` tranche.
    """
    p = root / "CLAUDE.md"
    if not p.is_file():
        return {"present": False}
    bloc = _bloc_reboot(_read(p))
    if not bloc:
        return {"present": False}
    m_clos = RE_REBOOT_CLOS.search(bloc)
    if not m_clos:
        return {"present": True, "clos_le": None}
    clos_le = m_clos.group(1)

    traces = {label: (fait_le or None) for label, fait_le in RE_TRACE_REBOOT.findall(bloc)}

    def _fait_apres_clos(cle: str) -> bool:
        fait_le = traces.get(cle)
        return bool(fait_le and fait_le >= clos_le)

    recadrage_ok = _fait_apres_clos("recadrage post-clôture")
    revue_ok = _fait_apres_clos("revue de littérature ciblée post-clôture")
    return {
        "present": True,
        "clos_le": clos_le,
        "traces": traces,
        "recadrage_ok": recadrage_ok,
        "revue_ok": revue_ok,
        "porte1_bloquee": not (recadrage_ok and revue_ok),
    }


# ── Portes 1bis et 3bis : les deux verdicts ──────────────────────────────────

VERDICTS_CONNUS = ("SOUMETTRE", "DIFFUSER-SANS-COMITE", "NE-PAS-DIFFUSER", "ROUVRIR")
VERDICTS_AMONT = ("REDIGER", "RÉDIGER", "RECADRER", "ELARGIR", "ÉLARGIR", "CLASSER")


def _blocs_verdict(txt: str) -> list[str]:
    """Découpe le registre en blocs, un par verdict, du plus récent au plus ancien."""
    parts = re.split(r"^##\s+Verdict", txt, flags=re.M)
    return parts[1:] if len(parts) > 1 else ([txt] if txt.strip() else [])


def lire_verdict(root: Path, porte: str = "3bis") -> dict:
    """Lit le verdict COURANT d'une des deux portes, s'il existe.

    Les verdicts des DEUX portes sont empilés dans le même `verdict_diffusion.md`,
    du plus récent au plus ancien, et se distinguent par la clé `porte : 1bis`
    (absente pour la 3bis, qui est le défaut historique). Prendre la première
    occurrence de `verdict :` sans regarder cette clé lirait un verdict amont comme
    un verdict de diffusion, ce qui est faux dès qu'un projet a franchi les deux
    portes — corrigé le 2026-09-04, à la création de la porte 1bis.
    Mesure seulement, ne tranche rien, comme tout le reste de ce script.
    """
    txt = _read(root / "verdict_diffusion.md")
    if not txt:
        return {"present": False, "verdict": None, "rendu_le": None}
    attendus = VERDICTS_AMONT if porte == "1bis" else VERDICTS_CONNUS
    for bloc in _blocs_verdict(txt):
        est_amont = bool(re.search(r"^\s*porte\s*:\s*1bis\s*$", bloc, flags=re.M))
        if est_amont != (porte == "1bis"):
            continue
        mv = re.search(r"^\s*verdict\s*:\s*([A-ZÉÈ-]+)\s*$", bloc, flags=re.M)
        md = re.search(r"^\s*rendu le\s*:\s*(\d{4}-\d{2}-\d{2})\s*$", bloc, flags=re.M)
        verdict = mv.group(1) if mv else None
        return {
            "present": True,
            "verdict": verdict if verdict in attendus else None,
            "brut": verdict,
            "rendu_le": md.group(1) if md else None,
        }
    return {"present": False, "verdict": None, "rendu_le": None}


# ── Phase observée ───────────────────────────────────────────────────────────

def _phase_un_manuscrit(manu: dict) -> tuple[int, str]:
    if manu.get("present"):
        if manu.get("version_fr"):
            return 4, "une version française du manuscrit existe"
        if manu.get("est_draft"):
            nb_reg = sum(1 for r in manu["registres"].values() if r["present"])
            if nb_reg:
                return 3, f"manuscrit au stade draft, {nb_reg} registre(s) qualité présent(s)"
            return 3, "manuscrit au stade draft"
        if manu.get("sections", 0) >= 2 and manu.get("lignes", 0) >= LIGNES_SQUELETTE_MINI:
            return 2, "manuscrit à l'état de squelette (sections posées, corps non rédigé)"
    return 1, "aucun manuscrit rédigé au-delà du gabarit de scaffold"


def phase_observee(manus: list[dict], root: Path) -> tuple[int, str]:
    """Phase déduite des ARTEFACTS seuls, indépendamment de ce qui est déclaré.

    Volontairement conservatrice : elle ne certifie aucune porte, elle constate
    le stade le plus avancé dont il existe une trace matérielle. Un projet à
    plusieurs manuscrits n'est pas plus avancé que le MOINS avancé d'entre eux :
    la porte se franchit pour chaque article, pas pour le projet en bloc.
    """
    # Phase 5 : le projet vit déjà dans un répertoire de clôture. Les quatre noms
    # sont ceux de la règle des cinq statuts gravée le 2026-09-16 (`mtbc/CLAUDE.md`,
    # `codes/CLAUDE.md`) ; `en_cours/`, le cinquième, ne dit rien de la phase.
    if root.parent.name in ("clos_soumis", "clos_accepte", "clos", "clos_abandonne"):
        return 5, "le projet est dans un répertoire de clôture"

    if not manus:
        return 1, "aucun manuscrit rédigé au-delà du gabarit de scaffold"

    phases = [_phase_un_manuscrit(m) for m in manus]
    pire = min(phases, key=lambda pm: pm[0])
    if len(manus) == 1:
        return pire
    detail = ", ".join(f"{m['repertoire']}={p}" for m, (p, _) in zip(manus, phases))
    return pire[0], f"le moins avancé des {len(manus)} manuscrits ({detail})"


def collecte(root: Path) -> dict:
    etat = lire_etat(root)
    pistes = lire_pistes(root)
    manus = lire_manuscrits(root)
    litt = lire_litterature(root)
    cahier = lire_cahier(root)
    obs, motif = phase_observee(manus, root)
    decl = etat.get("phase_declaree")
    return {
        "projet": root.name,
        "chemin": str(root),
        "date": date.today().isoformat(),
        "phase_declaree": decl,
        "voie": etat.get("voie"),
        "hors_rail": bool(etat.get("hors_rail")),
        "phase_observee": obs,
        "phase_observee_motif": motif,
        # Hors rail (voie réponse et/ou réoutillage sans article), il n'y a ni
        # phase à déclarer ni phase à observer : ni désaccord ni absence.
        "desaccord": bool(decl and decl != obs) and not etat.get("hors_rail"),
        "phase_absente": bool(etat.get("present") and decl is None
                              and not etat.get("hors_rail")),
        "etat": etat,
        "pistes": pistes,
        "manuscrits": manus,
        "litterature": litt,
        "cahier": cahier,
        "affirmations": lire_affirmations(root),
        "reboot": lire_reboot(root),
        "verdict": lire_verdict(root),
        "verdict_amont": lire_verdict(root, porte="1bis"),
        "plan_narratif": lire_plan_narratif(root),
        "profil_plugins": lire_profil_plugins(root),
    }


# ── Profil d'activation des plugins (P5.5) ───────────────────────────────────

PROFIL_PLUGINS = (Path.home() / "docs" / "environnement" / "outils"
                  / "profil_plugins.py")


def lire_profil_plugins(root: Path) -> dict:
    """Le profil que la phase courante APPELLE, comparé à celui qui est écrit.

    Le profil d'un projet (quels plugins sa famille et sa phase lui donnent) est
    calculé par `~/docs/environnement/outils/profil_plugins.py` depuis
    `profils/profils.json`. On ne le recopie pas ici : on l'interroge, pour que la
    porte signale un profil périmé — cas le plus fréquent, une phase qui vient
    d'avancer sans que le settings du projet ait suivi.

    L'import est PARESSEUX et sous un nom de module distinct : `profil_plugins`
    importe lui-même ce fichier pour lire la phase, et un import au niveau module
    ferait une boucle.
    """
    if not PROFIL_PLUGINS.is_file():
        return {"disponible": False}
    try:
        spec = importlib.util.spec_from_file_location("profil_plugins_cs", PROFIL_PLUGINS)
        if spec is None or spec.loader is None:
            return {"disponible": False}
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        conf = mod.charger()
        prof = mod.appliquer(root, conf, write=False)
    except Exception as e:                              # noqa: BLE001 — jamais bloquant
        return {"disponible": False, "erreur": e.__class__.__name__}
    return {
        "disponible": True, "conforme": not prof["change"],
        "blocs": prof["blocs"], "famille": prof["famille"],
        "attendus": [k.split("@")[0] for k in prof["actives_apres"]],
        "actuels": [k.split("@")[0] for k in prof["actives_avant"]],
    }


# ── Rendu ────────────────────────────────────────────────────────────────────

def rendre(d: dict) -> str:
    L = []
    decl = d["phase_declaree"]
    obs = d["phase_observee"]
    decl_s = f"{decl}/5 — {PHASES[decl]}" if decl else "NON DÉCLARÉE"
    L.append(f"=== Cycle de vie — {d['projet']} ({d['date']}) ===")
    if d.get("voie"):
        L.append(f"  Voie déclarée  : {d['voie']}")
    if d.get("hors_rail"):
        # Les cinq phases ne décrivent que la voie ARTICLE : sur une voie réponse
        # ou réoutillage, annoncer une phase observée serait un contresens.
        L.append("  Phase          : sans objet sur cette voie (le rail des cinq "
                 "phases ne vaut que pour la voie article)")
        L.append("  → le projet est fini quand la réponse est partie, ou quand "
                 "l'outil est reforgé ; cahier, pistes et KB restent dus.")
    else:
        L.append(f"  Phase déclarée : {decl_s}")
        L.append(f"  Phase observée : {obs}/5 — {PHASES[obs]}  ({d['phase_observee_motif']})")

    pp = d.get("profil_plugins") or {}
    if pp.get("disponible"):
        if pp["conforme"]:
            L.append(f"  Plugins        : profil conforme ({pp['famille']}) — "
                     f"{', '.join(pp['blocs'])}")
        else:
            manquants = sorted(set(pp["attendus"]) - set(pp["actuels"]))
            surnuméraires = sorted(set(pp["actuels"]) - set(pp["attendus"]))
            L.append(f"  Plugins        : profil À RÉÉCRIRE ({pp['famille']})"
                     + (f" — manquent {manquants}" if manquants else "")
                     + (f" — en trop {surnuméraires}" if surnuméraires else ""))
            L.append("    python3 ~/docs/environnement/outils/profil_plugins.py "
                     "--apply . --write   (puis redémarrer la session)")

    e = d["etat"]
    if e.get("present"):
        L.append(f"  État        : itération {e.get('iteration')}, réécrit {e.get('reecrit_le')}"
                 f" — {e['n_acquis']} acquis dont {e['sans_destination']} sans destination")
    else:
        L.append("  État        : etat_des_decouvertes.md ABSENT")

    p = d["pistes"]
    if p.get("present"):
        L.append(f"  Pistes      : {p['majeures']} majeures dont {p['ouvertes']} ouvertes, "
                 f"{p['sous_pistes_ouvertes']} sous-pistes ouvertes")
    else:
        L.append("  Pistes      : pistes.md ABSENT")

    lt = d["litterature"]
    L.append(f"  Littérature : {'renseignée' if lt['renseignee'] else 'NON RENSEIGNÉE'}"
             f" ({lt['refs_bib']} réfs, index {lt['index_lignes']} lignes)")

    manus = d["manuscrits"]
    if manus:
        for m in manus:
            prefixe = f"[{m['repertoire']}] " if len(manus) > 1 else ""
            L.append(f"  Manuscrit   : {prefixe}{m['lignes']} lignes, {m['sections']} sections, "
                     f"{m['figures']} figures — {'draft' if m['est_draft'] else 'squelette'}")
            reg = ", ".join(
                f"{k.split('/')[0]}{'⚠(vide)' if v.get('vide') else ('✓' if v['present'] else '✗')}"
                for k, v in m["registres"].items())
            L.append(f"  Qualité     : {prefixe}{reg}")
            L.append(f"  Finalisation: {prefixe}version FR {'✓' if m['version_fr'] else '✗'}, "
                     f"déclaration IA {'✓' if m['declaration_ia'] else '✗'}")
    else:
        L.append("  Manuscrit   : article*/main.tex ABSENT")

    aff = d.get("affirmations") or {}
    if aff.get("present"):
        cpt = aff.get("compteurs") or {}
        L.append(f"  Porte 1     : reboot en rétablissement — "
                 f"{cpt.get('non_testee', '?')} non testée(s), {cpt.get('en_test', '?')} en test, "
                 f"{cpt.get('prouvee', '?')} prouvée(s), {cpt.get('refutee', '?')} réfutée(s)")
        if aff.get("redaction_bloquee"):
            ids = ", ".join(aff["p1_non_tranchees"][:6])
            suite = ", …" if len(aff["p1_non_tranchees"]) > 6 else ""
            L.append(f"                RÉDACTION BLOQUÉE : {len(aff['p1_non_tranchees'])} "
                     f"affirmation(s) P1 non tranchée(s) ({ids}{suite}) — "
                     f"/reboot affirmation <id> --statut …")

    rb = d.get("reboot") or {}
    if rb.get("present") and rb.get("clos_le"):
        if rb["porte1_bloquee"]:
            manquantes = ", ".join(
                lbl for lbl, ok in (("recadrage post-clôture", rb["recadrage_ok"]),
                                    ("revue de littérature ciblée post-clôture", rb["revue_ok"]))
                if not ok)
            L.append(f"  Porte 1 (reboot) : REFUSÉE — clôture du {rb['clos_le']}, trace(s) "
                     f"manquante(s) ou antérieure(s) à la clôture : {manquantes}.")
            L.append("                     /recadrage sur l'état post-reboot puis /lit-review "
                     "ciblée, datées ≥ la clôture, avant tout dégel du manuscrit "
                     "(/reboot, étape 4).")
        else:
            po = p.get("ouvertes", 0) if p.get("present") else None
            spo = p.get("sous_pistes_ouvertes", 0) if p.get("present") else None
            if po or spo:
                L.append(f"  Porte 1 (reboot) : traces post-clôture satisfaites (clôture du "
                         f"{rb['clos_le']}) — porte 1 ORDINAIRE encore NON FRANCHIE : "
                         f"{po} piste(s) majeure(s) et {spo} sous-piste(s) encore ouverte(s).")
            else:
                L.append(f"  Porte 1 (reboot) : traces post-clôture satisfaites (clôture du "
                         f"{rb['clos_le']}) — aucune piste ouverte : instruire la porte 1 "
                         "ordinaire (deux tours à vide) avant 1bis.")

    a = d.get("verdict_amont") or {}
    if a.get("verdict"):
        L.append(f"  Porte 1bis  : {a['verdict']} (rendu le {a['rendu_le'] or 'sans date'})")
    elif 2 <= obs <= 4:
        # Signal, jamais blocage : la règle du doute de la porte 1bis est « dans le
        # doute, on rédige », donc l'absence de verdict amont se signale sans
        # condamner un projet déjà lancé (les projets antérieurs au 2026-09-04 n'en
        # ont aucun, et c'est normal). Borné à 4 : sur un projet en phase 5, déjà
        # clos ou archivé, le rappel est un reproche rétroactif sans action possible,
        # et il s'afficherait sur des dizaines de projets de `fini/`.
        L.append("  Porte 1bis  : aucun verdict de sujet rendu avant la rédaction "
                 "(/verdict-diffusion amont)")

    pn = d.get("plan_narratif") or {}
    if pn.get("present"):
        L.append(f"  Porte 2     : plan narratif {pn['maillons']} maillon(s), "
                 f"{pn['bascules']} bascule(s), {pn['rangs']} acquis rangé(s) "
                 f"(maj {pn['maj'] or 'sans date'})")
        if pn["rangs"] == 0:
            L.append("                gabarit posé mais AUCUN rang : l'étape n'est "
                     "pas faite (/narratif tri)")
    elif 2 <= obs <= 3:
        # Même logique qu'à la porte 1bis : signal, jamais blocage. Les projets
        # antérieurs au 2026-09-09 n'ont aucun plan narratif, et c'est normal.
        L.append("  Porte 2     : aucun plan narratif — le squelette a été écrit "
                 "sans étape de conception (/narratif)")

    v = d["verdict"]
    if v.get("verdict"):
        L.append(f"  Porte 3bis  : {v['verdict']} (rendu le {v['rendu_le'] or 'sans date'})")
    elif v.get("present"):
        L.append("  Porte 3bis  : verdict_diffusion.md présent mais ILLISIBLE "
                 f"(attendu 'verdict : <{'|'.join(VERDICTS_CONNUS)}>')")
    else:
        L.append("  Porte 3bis  : aucun verdict de diffusion rendu (/verdict-diffusion)")

    c = d["cahier"]
    L.append(f"  Cahier      : {c['entrees']} entrées, dernière {c['derniere']}")

    L.append("")
    if d["phase_absente"]:
        L.append("  ⚠ PHASE NON DÉCLARÉE dans l'en-tête de etat_des_decouvertes.md.")
        L.append(f"    Ajouter : **Phase :** {obs}/5 — {PHASES[obs]}")
    elif d["desaccord"] and d["verdict"].get("verdict") == "ROUVRIR" and decl < obs:
        # Écart VOULU : la porte 3bis a renvoyé une question précise en phase 1 tandis
        # que le manuscrit reste matériellement au stade qu'il avait atteint. L'annoncer
        # comme une phase sautée serait un contresens sur le seul retour en arrière que
        # le cycle autorise.
        L.append(f"  Écart déclarée {decl} / observée {obs} ATTENDU : verdict ROUVRIR du "
                 f"{d['verdict']['rendu_le'] or 'sans date'}.")
        L.append("    Les questions rouvertes sont instruites en discipline de phase 1 ;")
        L.append("    le manuscrit reste gelé à la porte 3bis, rien n'est perdu.")
        L.append("    Rejouer `/verdict-diffusion` une fois ces questions closes.")
    elif d["desaccord"]:
        L.append(f"  ⚠ DÉSACCORD : déclarée {decl}, observée {obs}.")
        L.append("    Soit la phase déclarée est périmée, soit une phase a été sautée.")
        L.append("    Instruire la porte avec `/cycle-projet gate` avant de continuer.")
    else:
        L.append("  Phase déclarée et artefacts cohérents.")
    # Uniquement en phase 4 : un projet déjà archivé (5) relève de règles
    # antérieures à cette porte, le signaler serait du bruit rétroactif.
    if obs == 4 and not d["verdict"].get("verdict"):
        L.append("  ⚠ PORTE 3bis NON FRANCHIE : le manuscrit est finalisé sans qu'aucun")
        L.append("    verdict de diffusion n'ait été rendu. `/verdict-diffusion` tranche")
        L.append("    s'il mérite un comité, un préprint, rien, ou un retour en phase 1.")
    return "\n".join(L)


def main() -> int:
    args = [a for a in sys.argv[1:]]
    as_json = "--json" in args
    quiet = "--quiet" in args
    pos = [a for a in args if not a.startswith("--")]

    root = resoudre(pos[0] if pos else None)
    if root is None:
        if not quiet:
            print("Aucun projet structuré trouvé (pas de cahier_de_labo.md en remontant).")
        return 1

    d = collecte(root)

    if quiet:
        if d["phase_absente"]:
            print(f"[cycle] {d['projet']} : phase de cycle non déclarée "
                  f"(observée {d['phase_observee']}/5 — {PHASES[d['phase_observee']]}).")
        elif d["desaccord"]:
            print(f"[cycle] {d['projet']} : phase déclarée {d['phase_declaree']}/5 mais "
                  f"artefacts en phase {d['phase_observee']}/5 — instruire `/cycle-projet gate`.")
        return 0

    print(json.dumps(d, ensure_ascii=False, indent=2) if as_json else rendre(d))
    return 0


if __name__ == "__main__":
    sys.exit(main())
