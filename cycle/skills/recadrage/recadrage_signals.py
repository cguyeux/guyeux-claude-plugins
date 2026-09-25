#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""recadrage_signals.py — mesure les signaux qui déclenchent un recadrage de projet.

Lecture seule, stdlib uniquement, ne plante jamais (tout échec dégrade en None).
Rend des MÉTRIQUES, jamais un verdict sémantique : le verdict (POURSUIVRE /
RECADRER / ESSAIMER / SCINDER) est rendu par le skill `recadrage`, qui lit
les fichiers. Ce script existe pour que le DÉCLENCHEMENT soit déterministe et
bon marché plutôt que laissé au flair.

Usage :
    python3 recadrage_signals.py [projet]            # résumé lisible
    python3 recadrage_signals.py [projet] --json     # JSON complet
    python3 recadrage_signals.py [projet] --quiet    # une ligne SI recadrage dû, sinon rien
                                                     # (destiné au hook SessionStart)

`projet` : chemin absolu, ou nom relatif à $CYCLE_PROJECT_SHORTCUT_ROOT (défaut
~/docs/codes/mtbc), ou défaut = cwd (en remontant jusqu'au premier ancêtre
STRICT portant cahier_de_labo.md).
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

# ── Seuils de déclenchement ──────────────────────────────────────────────────
# Choisis pour qu'un projet actif soit recadré ~1 fois par mois, jamais à chaque
# session. Un recadrage trop fréquent devient un rituel qu'on expédie.
JOURS_AVANT_RECADRAGE = 30          # ancienneté du dernier recadrage
ENTREES_CAHIER_AVANT_RECADRAGE = 15  # ou : volume de séances depuis
PART_HORS_ARTICLE_ALERTE = 0.40      # part d'acquis destination B/C qui alerte
SECTIONS_MANUSCRIT_ALERTE = 9        # \section dans main.tex
FIGURES_MANUSCRIT_ALERTE = 8         # \includegraphics distincts
LIGNES_MANUSCRIT_ALERTE = 1400       # lignes de main.tex (corps + préambule)
PISTES_OUVERTES_ALERTE = 12          # pistes MAJEURES encore ouvertes

# Raccourci de nommage : défaut = l'environnement pour lequel ce skill a été
# conçu (le plugin `cycle` est domain-agnostic, ce raccourci ne l'est pas) ;
# surchargeable pour un autre genre ou un autre clone du dépôt public. À garder
# aligné avec la même constante dans `cycle-projet/cycle_status.py` (même
# mécanique de résolution).
MTBC_ROOT = Path(os.environ.get("CYCLE_PROJECT_SHORTCUT_ROOT",
                                 str(Path.home() / "docs" / "codes" / "mtbc"))).expanduser()

# C1 (projet vivant destinataire) et C2 (registre du parent) éclatent l'ancienne
# C depuis l'arbitrage du 2026-08-26 ; E est la réponse à la question ouverte d'un
# autre projet. « C » nu reste accepté : les états écrits avant cette date le
# portent, et les relire comme « sans destination » déclencherait un recadrage en
# boucle sur des projets déjà triés.
DESTINATIONS = ("A", "B", "C", "C1", "C2", "D", "E")
DEST_LABELS = {
    "A": "article en cours",
    "B": "second papier du même projet",
    "C": "essaimage hors projet",
    "D": "classé sans suite",
}


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
            # Un chemin relatif RÉEL (« . », « .. », « ./x ») doit primer sur le
            # raccourci par nom de projet MTBC, sinon « . »/« .. » se résout en
            # MTBC_ROOT/"." ou MTBC_ROOT/".." — ce candidat est TOUJOURS un
            # répertoire valide (l'ajout de "." ou ".." ne change rien filesystem-
            # wise), donc il gagne systématiquement, quel que soit le cwd réel, pour
            # tout projet situé hors MTBC_ROOT. Même correctif que `cycle_status.py`
            # (`resoudre()`), à garder aligné entre les deux scripts. Bug vécu sur
            # AAP_generique_tub (2026-08-18, hors MTBC_ROOT) : `resoudre(".")`
            # renvoyait silencieusement mtbc/ au lieu du projet courant.
            local = (Path.cwd() / arg).resolve()
            cand = MTBC_ROOT / arg
            p = local if (arg.startswith((".", "/")) or local.is_dir()) else cand
        if not p.is_dir():
            return None
        # Un répertoire quelconque n'est pas un projet : exiger le cahier, sinon
        # remonter (gère aussi le cas où arg pointe vers un sous-répertoire du
        # projet, pas seulement sa racine).
        return trouver_racine(p.resolve())
    return trouver_racine(Path.cwd())


# ── État des découvertes ─────────────────────────────────────────────────────

RE_RECADRAGE = re.compile(
    r"\*\*Dernier recadrage\s*:\*\*\s*(\d{4}-\d{2}-\d{2})(?:\s*\(([^)]*)\))?"
)
RE_ITERATION = re.compile(r"\*\*Itération\s*:\*\*\s*(\d+)")
RE_REECRIT = re.compile(r"\*\*Réécrit le\s*:\*\*\s*(\d{4}-\d{2}-\d{2})")
RE_DEST = re.compile(r"destination\s*:\s*(C[12]|[ABCDE])(?![\w])", re.IGNORECASE)


def section(txt: str, n: int) -> str:
    """Corps de la section '## <n>.' du squelette /etat (8 sections + §9)."""
    m = re.search(rf"^##\s*{n}\.\s.*$", txt, re.MULTILINE)
    if not m:
        return ""
    start = m.end()
    m2 = re.search(r"^##\s*\d+\.\s", txt[start:], re.MULTILINE)
    return txt[start: start + m2.start()] if m2 else txt[start:]


def analyser_etat(root: Path) -> dict:
    f = root / "etat_des_decouvertes.md"
    out: dict = {
        "existe": f.is_file(),
        "iteration": None,
        "reecrit_le": None,
        "dernier_recadrage": None,
        "dernier_verdict": None,
        "acquis_total": 0,
        "acquis_sans_destination": 0,
        "destinations": {d: 0 for d in DESTINATIONS},
        "part_hors_article": None,
        "section9_presente": False,
        "miu_projet": None,
    }
    if not out["existe"]:
        return out
    txt = _read(f)
    if (m := RE_MIU_PROJET.search(txt)):
        out["miu_projet"] = {"M": int(m.group(1)), "I": int(m.group(2)), "U": int(m.group(3))}
    if (m := RE_ITERATION.search(txt)):
        out["iteration"] = int(m.group(1))
    if (m := RE_REECRIT.search(txt)):
        out["reecrit_le"] = m.group(1)
    if (m := RE_RECADRAGE.search(txt)):
        out["dernier_recadrage"] = m.group(1)
        out["dernier_verdict"] = (m.group(2) or "").strip() or None
    out["section9_presente"] = bool(re.search(r"^##\s*9\.\s", txt, re.MULTILINE))

    # §2 : un acquis = une puce de premier niveau ('- ' en colonne 0).
    corps2 = section(txt, 2)
    for bloc in re.split(r"\n(?=- )", corps2):
        if not bloc.strip().startswith("- "):
            continue
        out["acquis_total"] += 1
        if (m := RE_DEST.search(bloc)):
            out["destinations"][m.group(1).upper()] += 1
        else:
            out["acquis_sans_destination"] += 1

    tagues = sum(out["destinations"].values())
    if tagues:
        # E ne compte PAS comme hors article : l'acquis reste ici (il est souvent
        # A par ailleurs), seule une copie part répondre à la question d'un autre.
        hors = (out["destinations"]["B"] + out["destinations"]["C"]
                + out["destinations"]["C1"] + out["destinations"]["C2"])
        out["part_hors_article"] = round(hors / tagues, 3)
    return out


# ── Cahier de labo ───────────────────────────────────────────────────────────

RE_ENTREE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})", re.MULTILINE)


def analyser_cahier(root: Path, depuis: str | None) -> dict:
    f = root / "cahier_de_labo.md"
    dates = RE_ENTREE.findall(_read(f)) if f.is_file() else []
    out = {
        "existe": f.is_file(),
        "entrees_total": len(dates),
        "derniere_entree": max(dates) if dates else None,
        "entrees_depuis_recadrage": None,
    }
    if depuis and dates:
        out["entrees_depuis_recadrage"] = sum(1 for d in dates if d > depuis)
    elif dates:
        out["entrees_depuis_recadrage"] = len(dates)
    return out


# ── Pistes ───────────────────────────────────────────────────────────────────

# Le titre — et le corps du tag d'état lui-même — peuvent porter des crochets
# imbriqués : tags de titre ([OUTILLAGE], [SÉRENDIPITÉ ← X]), ou une citation
# littérale d'un ancien tag dans le récit de clôture (ex. l'en-tête P20 dit
# « P20.4 ... portait `[à faire]` sans bloc de résultat ... » DANS son propre
# tag d'état `[**CLOS EN INTÉGRALITÉ** ... ]`). Un simple `\[([^\[\]]*)\]`
# glouton s'arrête au premier `]` rencontré en remontant depuis la fin, donc
# tombe sur ce crochet cité plutôt que sur le vrai crochet englobant — état
# lu à tort comme « à faire » alors que la piste est close. `_dernier_crochet`
# fait un scan à profondeur de crochets pour prendre le DERNIER groupe de
# PREMIER NIVEAU de la ligne, imbrication comprise.
# Par ailleurs, pas d'ancrage de fin de ligne après le crochet : la convention
# pistes.md autorise une annotation `maj : ... (...)` APRÈS le tag d'état sur
# la même ligne d'en-tête (ex. « ## P16. ... [en cours] maj : 2026-08-18 (...) »).
# Avec un ancrage de fin de ligne, ces pistes — pourtant valides — ne
# matchaient jamais et disparaissaient silencieusement du décompte ET du
# classement MIU.
#
# La lettre de racine (« P » historique) était hardcodée ici, exactement comme dans
# `status.py` (skill `pistes`) : un projet numérotant ses pistes autrement (`A1`-`A7`
# sur `archeo_crispr`) rendait ce script muet, « 0 pistes ouvertes », silencieusement.
# Correctif identique : DÉTECTER la ou les lettres réellement employées par CE
# registre (`_lettres_racine`) plutôt que d'accepter n'importe quelle lettre majuscule
# — un cahier MTBC regorge de codes de lignée (`L4`, `L6.5`...) qui ne sont PAS des
# identifiants de piste, et une classe `[A-Z]` non filtrée les confondrait en masse.
# Détection des préfixes DÉLÉGUÉE à `status.py` du skill `pistes` (2026-09-21, piste AE
# de `environnement`). L'implémentation locale précédente exigeait un CHIFFRE collé à la
# lettre de racine, des deux côtés (titres `^##\s+([A-Z])[0-9]`, noms de fichiers
# `^([A-Z])[0-9]`) : une piste majeure titrée `## S.` ou `## AA.` — dont la numérotation
# n'apparaît que sur les SOUS-pistes (`S1`, `AA1`...) — n'était donc reconnue par aucune
# des deux sources. Mesuré sur `environnement` : `trouve` restait `{'P'}` et le classement
# ACTION/PROMESSE ignorait EN SILENCE 6 des 7 pistes majeures ouvertes (S, V, Y, Z, AA, AB),
# sans message ni compteur. Même famille de défaut que les pistes AC (`status.py`) et AD
# (`impact_done.py`, `carrefour.py`) du même dépôt : un script qui réimplémente sa propre
# détection de préfixes en diverge au premier cas non prévu. `detecter_prefixes` est
# désormais la source unique — déjà durcie et mesurée sur 197 projets (cf. sa docstring et
# le faux positif `droit-shs/rohonczi` qu'elle documente), donc à ne surtout PAS recopier ici.
def _prefixes_status(root: Path) -> set[str] | None:
    """Préfixes rendus par `status.detecter_prefixes`, ou None si le skill `pistes`
    n'est pas installé à côté (les deux skills peuvent être déployés séparément)."""
    import importlib.util
    _voisin = Path(__file__).resolve().parent.parent / "pistes" / "status.py"
    spath = _voisin if _voisin.is_file() else Path.home() / ".claude" / "skills" / "pistes" / "status.py"
    if not spath.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location("_pistes_status", spath)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return set(mod.detecter_prefixes(str(root))) or None
    except Exception:
        return None


def _lettres_racine(f: Path) -> str:
    """Fragment de regex pour la ou les lettres/préfixes de racine réellement vus dans CE
    `pistes.md`/`pistes/*.md` : `P` seule si un seul préfixe d'une lettre (comportement
    historique, chaîne identique à l'ancien littéral), classe `[AP]` si plusieurs d'une
    lettre, alternance `(?:AA|AB|P)` dès qu'un préfixe en compte plusieurs (une classe de
    caractères ne peut pas représenter une PAIRE). Retombe sur `P` si rien n'est trouvé."""
    trouve = _prefixes_status(f.parent)
    if trouve is None:                       # repli : skill `pistes` absent
        trouve = set()
        if f.is_file():
            for m in re.finditer(r"^##\s+\*{0,2}([A-Z])[0-9]", _read(f), re.MULTILINE):
                trouve.add(m.group(1))
        ddir = f.parent / "pistes"
        if ddir.is_dir():
            for p in ddir.iterdir():
                m = re.match(r"^([A-Z]{1,3})(?:[0-9]+)?\.md$", p.name)
                if m:
                    trouve.add(m.group(1))
    if any(len(p) > 1 for p in trouve):
        return "(?:" + "|".join(sorted(trouve, key=len, reverse=True)) + ")"
    s = "".join(sorted(trouve)) or "P"
    return s if len(s) == 1 else "[" + s + "]"


# `\d*` et non `\d+` (2026-09-21, piste AE) : une piste MAJEURE peut n'être qu'une lettre
# de racine, sa numérotation ne commençant qu'aux sous-pistes (`## S.` + `- S1`, `## AA.` +
# `- AA1`). Le point qui suit reste OBLIGATOIRE, et la lettre est prise dans les seuls
# préfixes réellement vus dans ce registre : un titre de prose ne peut donc pas être pris
# pour une piste, sauf à commencer exactement par un préfixe du projet suivi d'un point.
def _re_piste_ligne(lettre: str) -> re.Pattern:
    return re.compile(r"^##\s+(" + lettre + r"\d*)\.\s+(.*)$", re.MULTILINE)


def _dernier_crochet(ligne: str) -> tuple[str, str] | None:
    """(titre, état) à partir du DERNIER groupe `[...]` de premier niveau de
    `ligne`, en respectant l'imbrication (cf. commentaire de RE_PISTE_LIGNE).
    None si la ligne ne porte aucun crochet complet (piste mal formée)."""
    spans = []
    profondeur = 0
    debut = None
    for i, ch in enumerate(ligne):
        if ch == "[":
            if profondeur == 0:
                debut = i
            profondeur += 1
        elif ch == "]":
            if profondeur > 0:
                profondeur -= 1
                if profondeur == 0 and debut is not None:
                    spans.append((debut, i))
    if not spans:
        return None
    s, e = spans[-1]
    return ligne[:s], ligne[s + 1:e]
# `[^\]]+` et non `[^\]\s]+` : un nom de projet peut contenir des espaces
# (« Still unknown gene function »), et s'arrêter au premier blanc le tronquait.
RE_SERENDIP = re.compile(r"SÉRENDIPITÉ\s*←\s*([^\]]+)", re.IGNORECASE)
# MIU : Maturité / Importance / Urgence, 0-3 chacune (cf. SKILL.md, section MIU).
RE_MIU = re.compile(r"MIU\s*:\s*M\s*([0-3])\s*I\s*([0-3])\s*U\s*([0-3])")
RE_MIU_PROJET = re.compile(r"\*\*MIU projet\s*:\*\*\s*M\s*([0-3])\s*I\s*([0-3])\s*U\s*([0-3])")
RE_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")

OUVERT = ("à faire", "a faire", "en cours")


def _est_ouvert(etat: str) -> bool:
    """Un état ouvert, même suivi d'un commentaire dans le MÊME crochet.

    Deux habitudes d'écriture cassaient une égalité stricte (`etat in OUVERT`),
    qui classait alors la piste ni ouverte ni close, sans rien signaler :
    la GLOSE dans le même crochet (« [en cours - resoumis a MMI le 2026-08-31] »)
    et l'EMPHASE markdown en tete (« [**en cours** - ...] », « [**realise** ...] »).
    Sur annotation_mtbc, `--priorites` annoncait « 0 pistes ouvertes » sur un projet
    qui en avait deux, puis ratait encore P37 apres le premier correctif.
    Trouve par l'audit `/pistes read` du 2026-09-05.
    """
    return etat.lstrip("*_ ").startswith(OUVERT)


def registre_parent(root: Path) -> Path:
    """Premier `pistes.md` ANCESTRAL au-dessus du projet.

    Pas simplement `root.parent / "pistes.md"` : un projet déplacé dans un
    répertoire d'archivage (`clos_soumis/`, `clos_abandonne/`) aurait alors pour
    registre celui du cimetière, que personne ne relit — exactement l'inverse du
    but. On remonte donc jusqu'au premier registre qui existe VRAIMENT. Si aucun
    n'existe, on rend le parent direct, à créer.
    """
    d = root.parent
    for _ in range(5):
        if (d / "pistes.md").is_file():
            return d / "pistes.md"
        if d.parent == d:
            break
        d = d.parent
    return root.parent / "pistes.md"


def _bloc_piste(txt: str, debut: int) -> str:
    """Corps d'une piste majeure : de son en-tête au prochain `## `."""
    m = re.search(r"^##\s", txt[debut:], re.MULTILINE)
    return txt[debut: debut + m.start()] if m else txt[debut:]


# Architecture index + détail (2026-08-20, cf. skill /pistes) : pistes.md ne
# garde qu'un pointeur `-> détail : pistes/Px.md`, le corps réel (sous-pistes
# incluses) vit dans ce fichier. Sans ce rouvre, `sous_pistes` tomberait
# toujours à 0 et la zone MIU (I_justifiee/U_datee) ne verrait plus jamais la
# clause de justification, qui a suivi le corps vers le fichier de détail.
def _re_detail(lettre: str) -> re.Pattern:
    # `\d*` : symétrique de `_re_piste_ligne` — `pistes/S.md`, `pistes/AA.md` (piste AE).
    return re.compile(r"->\s*détail\s*:\s*(pistes/" + lettre + r"\d*\.md)")


def _corps_effectif(corps: str, f: Path, lettre: str) -> str:
    m = _re_detail(lettre).search(corps)
    if not m:
        return corps
    detail_path = f.parent / m.group(1)
    if not detail_path.is_file():
        return corps
    detail_txt = _read(detail_path)
    # Le fichier de détail répète son propre en-tête ('## Px. ...') -- on ne
    # veut que ce qui suit, pour rester cohérent avec _bloc_piste ci-dessus.
    hdr = re.search(r"^##\s", detail_txt, re.MULTILINE)
    fin_hdr = detail_txt.find("\n", hdr.end()) if hdr else -1
    return detail_txt[fin_hdr + 1:] if fin_hdr != -1 else detail_txt


def analyser_pistes(f: Path) -> dict:
    out = {
        "chemin": str(f),
        "existe": f.is_file(),
        "majeures": 0,
        "ouvertes": 0,
        "etats": {},
        "serendipites": 0,
        "serendipites_par_projet": {},
        "pistes": [],              # détail, pour le classement de priorité
        "ouvertes_sans_miu": 0,
    }
    if not f.is_file():
        return out
    txt = _read(f)
    lettre = _lettres_racine(f)
    for m in _re_piste_ligne(lettre).finditer(txt):
        num = m.group(1)
        trouve = _dernier_crochet(m.group(2))
        if trouve is None:
            continue
        titre, etat = trouve
        etat = etat.strip().lower()
        out["majeures"] += 1
        out["etats"][etat] = out["etats"].get(etat, 0) + 1
        ouverte = _est_ouvert(etat)
        if ouverte:
            out["ouvertes"] += 1
        serendip = RE_SERENDIP.search(titre)
        if serendip:
            out["serendipites"] += 1
            k = serendip.group(1).strip()
            out["serendipites_par_projet"][k] = out["serendipites_par_projet"].get(k, 0) + 1

        corps = _corps_effectif(_bloc_piste(txt, m.end()), f, lettre)
        miu = RE_MIU.search(corps)
        p = {
            "num": num,
            "titre": ' '.join(titre.split())[:100],
            "etat": etat,
            "ouverte": ouverte,
            "serendipite": bool(serendip),
            "M": None, "I": None, "U": None,
            "I_justifiee": None, "U_datee": None,
            "sous_pistes": len(re.findall(r"^\s+-\s+" + lettre + r"\d+\.\d+", corps, re.MULTILINE)),
        }
        if miu:
            p["M"], p["I"], p["U"] = (int(miu.group(i)) for i in (1, 2, 3))
            # Garde-fous anti-inflation : une I forte doit être justifiée, une U
            # maximale doit porter une date. Mesuré sur la ligne MIU et la suivante.
            fin = corps.find('\n', miu.end())
            fin2 = corps.find('\n', fin + 1) if fin != -1 else -1
            zone = corps[miu.start(): fin2 if fin2 != -1 else len(corps)]
            p["I_justifiee"] = bool(re.search(r"\bI\s*:", zone))
            p["U_datee"] = bool(RE_DATE.search(zone))
        elif ouverte:
            out["ouvertes_sans_miu"] += 1
        out["pistes"].append(p)
    return out


def classer(pistes: list[dict]) -> dict:
    """Deux lectures explicites plutôt qu'un score unique qui masquerait le raisonnement.

    ACTION  : ce qu'il faut faire maintenant — l'urgent d'abord, puis ce qui est à
              la fois important et MÛR (finir ce qui est presque fini, principe qui
              évite l'accumulation de chantiers ouverts).
    PROMESSE: fort potentiel jamais amorcé — importance élevée, maturité faible.
              Volontairement DISJOINT du classement d'action : ce sont deux
              questions différentes, les confondre est ce qui fait qu'on ne lance
              jamais les paris (toujours moins « prioritaires » qu'un chantier ouvert).
    """
    notes = [p for p in pistes if p["ouverte"] and p["M"] is not None]
    action = sorted(notes, key=lambda p: (p["U"], p["I"] + p["M"], p["I"]), reverse=True)
    promesse = sorted(
        [p for p in notes if p["I"] >= 2 and p["M"] <= 1],
        key=lambda p: (p["I"], -p["M"]), reverse=True,
    )
    return {
        "action": action,
        "promesse": promesse,
        "suspectes": [p for p in notes
                      if (p["I"] >= 2 and not p["I_justifiee"]) or (p["U"] == 3 and not p["U_datee"])],
    }


# ── Manuscrit ────────────────────────────────────────────────────────────────

RE_INPUT = re.compile(r"^[^%\n]*\\(?:input|include)\{([^}]+)\}", re.MULTILINE)


def _texte_manuscrit(f: Path, vus: set[str] | None = None) -> str:
    """Texte du manuscrit, \\input et \\include résolus (1 niveau de récursion suffit).

    Un manuscrit modulaire (main.tex qui n'est qu'une table des matières) mesurait
    sinon 180 lignes et 0 figure, et aucun signal de scission ne se déclenchait
    jamais sur les projets qui en ont le plus besoin.
    """
    vus = vus if vus is not None else set()
    key = str(f.resolve())
    if key in vus or not f.is_file():
        return ""
    vus.add(key)
    txt = _read(f)
    for rel in RE_INPUT.findall(txt):
        rel = rel.strip()
        cible = f.parent / (rel if rel.endswith(".tex") else rel + ".tex")
        txt += "\n" + _texte_manuscrit(cible, vus)
    return txt


def analyser_manuscrit(root: Path) -> dict:
    out = {"existe": False, "chemin": None, "lignes": 0, "sections": 0,
           "figures": 0, "fichiers": 0}
    for rel in ("article/main.tex", "main.tex", "article/manuscript.tex"):
        f = root / rel
        if f.is_file():
            vus: set[str] = set()
            txt = _texte_manuscrit(f, vus)
            out.update(
                existe=True,
                chemin=str(f),
                lignes=txt.count("\n") + 1,
                sections=len(re.findall(r"^\s*\\section\{", txt, re.MULTILINE)),
                figures=len(set(re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", txt))),
                fichiers=len(vus),
            )
            break
    return out


# ── Assemblage ───────────────────────────────────────────────────────────────

def jours_depuis(d: str | None) -> int | None:
    if not d:
        return None
    try:
        return (date.today() - datetime.strptime(d, "%Y-%m-%d").date()).days
    except Exception:
        return None


def collecter(root: Path) -> dict:
    etat = analyser_etat(root)
    cahier = analyser_cahier(root, etat["dernier_recadrage"])
    pistes = analyser_pistes(root / "pistes.md")
    parent = analyser_pistes(registre_parent(root))
    manus = analyser_manuscrit(root)

    anciennete = jours_depuis(etat["dernier_recadrage"])
    jamais = etat["dernier_recadrage"] is None

    # Déclenchement : un seul motif suffit. Volontairement OU, pas ET —
    # un projet qui n'a jamais été recadré est le cas le plus à risque.
    motifs = []
    if jamais:
        motifs.append("aucun recadrage jamais enregistré")
    else:
        if anciennete is not None and anciennete >= JOURS_AVANT_RECADRAGE:
            motifs.append(f"dernier recadrage il y a {anciennete} j (seuil {JOURS_AVANT_RECADRAGE})")
        n = cahier["entrees_depuis_recadrage"] or 0
        if n >= ENTREES_CAHIER_AVANT_RECADRAGE:
            motifs.append(f"{n} entrées de cahier depuis (seuil {ENTREES_CAHIER_AVANT_RECADRAGE})")
    if etat["acquis_sans_destination"]:
        motifs.append(
            f"{etat['acquis_sans_destination']}/{etat['acquis_total']} acquis sans destination"
        )

    # Signaux de SCISSION : matière factuelle, pas verdict. Le skill tranche
    # en y ajoutant les deux critères non mesurables (questions indépendantes,
    # publics/journaux distincts).
    scission = []
    p = etat["part_hors_article"]
    if p is not None and p >= PART_HORS_ARTICLE_ALERTE:
        scission.append(f"{int(p * 100)} % des acquis tagués sont hors de l'article courant")
    if manus["sections"] >= SECTIONS_MANUSCRIT_ALERTE:
        scission.append(f"{manus['sections']} sections dans le manuscrit")
    if manus["figures"] >= FIGURES_MANUSCRIT_ALERTE:
        scission.append(f"{manus['figures']} figures dans le manuscrit")
    if manus["lignes"] >= LIGNES_MANUSCRIT_ALERTE:
        scission.append(f"{manus['lignes']} lignes de main.tex")
    if pistes["ouvertes"] >= PISTES_OUVERTES_ALERTE:
        scission.append(f"{pistes['ouvertes']} pistes majeures encore ouvertes")

    return {
        "projet": root.name,
        "racine": str(root),
        "date": date.today().isoformat(),
        "etat": etat,
        "cahier": cahier,
        "pistes_projet": pistes,
        "registre_parent": parent,
        "manuscrit": manus,
        "anciennete_recadrage_j": anciennete,
        "recadrage_du": bool(motifs),
        "motifs": motifs,
        "signaux_scission": scission,
        "seuils": {
            "jours": JOURS_AVANT_RECADRAGE,
            "entrees_cahier": ENTREES_CAHIER_AVANT_RECADRAGE,
            "part_hors_article": PART_HORS_ARTICLE_ALERTE,
            "sections": SECTIONS_MANUSCRIT_ALERTE,
            "figures": FIGURES_MANUSCRIT_ALERTE,
            "lignes_manuscrit": LIGNES_MANUSCRIT_ALERTE,
            "pistes_ouvertes": PISTES_OUVERTES_ALERTE,
        },
    }


def rendu_priorites(d: dict) -> str:
    """Classement des pistes ouvertes par MIU — projet ET registre parent."""
    L = [f"=== Priorités — {d['projet']} ({d['date']}) ==="]
    for label, bloc in (("projet", d["pistes_projet"]), ("registre parent", d["registre_parent"])):
        pistes = bloc.get("pistes", [])
        if label == "registre parent":
            # N'afficher du registre que ce qui vient de CE projet : le reste
            # appartient aux autres, l'y mélanger rendrait le classement illisible.
            pistes = [p for p in pistes if p["serendipite"] and d["projet"] in p["titre"]]
        c = classer(pistes)
        notees = sum(1 for p in pistes if p["ouverte"] and p["M"] is not None)
        ouvertes = sum(1 for p in pistes if p["ouverte"])
        L.append("")
        suffixe = " issues de ce projet" if label == "registre parent" else ""
        L.append(f"── {label} : {ouvertes} pistes ouvertes{suffixe}, {notees} notées MIU")
        if not notees:
            if ouvertes:
                L.append("   (aucune notée — ajouter `MIU : M<0-3> I<0-3> U<0-3>` sur la ligne origine/maj)")
            continue
        L.append("   ACTION (urgent d'abord, puis important ET mûr) :")
        for p in c["action"][:6]:
            L.append(f"     M{p['M']} I{p['I']} U{p['U']}  {p['num']:>4}  {p['titre'][:78]}")
        if c["promesse"]:
            L.append("   PROMESSES (important, jamais amorcé) :")
            for p in c["promesse"][:6]:
                L.append(f"     M{p['M']} I{p['I']} U{p['U']}  {p['num']:>4}  {p['titre'][:78]}")
        if c["suspectes"]:
            L.append("   NOTES À JUSTIFIER (I≥2 sans clause `I:`, ou U=3 sans date) :")
            for p in c["suspectes"][:6]:
                L.append(f"     M{p['M']} I{p['I']} U{p['U']}  {p['num']:>4}  {p['titre'][:78]}")
    return "\n".join(L)


def rendu_portfolio(racine: Path) -> str:
    """Compare les projets frères entre eux par leur MIU projet.

    Répond à « lequel finir en premier ? », que le MIU par piste ne dit pas :
    une piste M3I3 dans un projet mort ne vaut pas une piste M2I2 dans un projet
    à deux semaines de la soumission.
    """
    # Un niveau de récursion : les projets archivés (`clos_soumis/`, `clos_abandonne/`)
    # doivent apparaître. Un projet soumis peut porter du matériel de révision urgent,
    # et l'ignorer parce qu'il a été rangé est exactement l'angle mort à éviter.
    candidats = []
    for d in sorted(p for p in racine.iterdir() if p.is_dir() and not p.name.startswith('.')):
        if (d / "cahier_de_labo.md").is_file():
            candidats.append(d)
        else:
            candidats += sorted(s for s in d.iterdir()
                                if s.is_dir() and (s / "cahier_de_labo.md").is_file())

    lignes, sans = [], []
    for d in candidats:
        e = analyser_etat(d)
        if not e["existe"]:
            continue
        nom = str(d.relative_to(racine))
        if e["miu_projet"]:
            m = e["miu_projet"]
            lignes.append((m["U"], m["I"] + m["M"], m["I"], nom, m, e))
        else:
            sans.append(nom)
    L = [f"=== Portfolio — {racine} ({date.today().isoformat()}) ==="]
    if lignes:
        L.append("  Classement d'action (U, puis I+M) :")
        for _, _, _, nom, m, e in sorted(lignes, reverse=True):
            rec = e["dernier_recadrage"] or "jamais"
            L.append(f"    M{m['M']} I{m['I']} U{m['U']}  {nom:<24} recadrage: {rec}")
    if sans:
        L.append(f"  Sans MIU projet ({len(sans)}) : {', '.join(sans[:14])}"
                 + (" …" if len(sans) > 14 else ""))
        L.append("    (ajouter `**MIU projet :** M<0-3> I<0-3> U<0-3>` dans l'en-tête de "
                 "etat_des_decouvertes.md)")
    return "\n".join(L)


def rendu_lisible(d: dict) -> str:
    e, c, p, par, m = (
        d["etat"], d["cahier"], d["pistes_projet"], d["registre_parent"], d["manuscrit"],
    )
    L = [f"=== Signaux de recadrage — {d['projet']} ({d['date']}) ==="]
    if e["existe"]:
        dr = e["dernier_recadrage"] or "JAMAIS"
        anc = f" (il y a {d['anciennete_recadrage_j']} j)" if d["anciennete_recadrage_j"] is not None else ""
        verd = f" — verdict : {e['dernier_verdict']}" if e["dernier_verdict"] else ""
        L.append(f"  État        : itération {e['iteration']}, réécrit {e['reecrit_le']}")
        L.append(f"  Recadrage   : {dr}{anc}{verd}")
        rep = ", ".join(f"{k}={e['destinations'][k]}" for k in DESTINATIONS)
        L.append(
            f"  Acquis §2   : {e['acquis_total']} dont {e['acquis_sans_destination']} "
            f"sans destination  [{rep}]"
        )
        if e["part_hors_article"] is not None:
            L.append(f"  Hors article: {int(e['part_hors_article'] * 100)} % "
                     f"des acquis tagués (B+C+C1+C2, E exclu)")
    else:
        L.append("  État        : etat_des_decouvertes.md ABSENT (/etat update pour le créer)")
    L.append(
        f"  Cahier      : {c['entrees_total']} entrées, dernière {c['derniere_entree']}, "
        f"{c['entrees_depuis_recadrage']} depuis le recadrage"
    )
    L.append(
        f"  Pistes      : {p['majeures']} majeures dont {p['ouvertes']} ouvertes"
        + (f" ({p['ouvertes_sans_miu']} sans MIU)" if p["ouvertes_sans_miu"] else "")
        + (f", {p['serendipites']} sérendipités" if p["serendipites"] else "")
    )
    if e["miu_projet"]:
        mp = e["miu_projet"]   # PAS `m` : `m` porte déjà le manuscrit dans cette fonction
        L.append(f"  MIU projet  : M{mp['M']} I{mp['I']} U{mp['U']}")
    if par["existe"]:
        L.append(
            f"  Registre ↑  : {par['chemin']} — {par['majeures']} pistes, "
            f"{par['serendipites']} sérendipités"
            + (f" {par['serendipites_par_projet']}" if par["serendipites_par_projet"] else "")
        )
    else:
        L.append(f"  Registre ↑  : ABSENT ({par['chemin']}) — à créer pour accueillir l'essaimage")
    if m["existe"]:
        multi = f" ({m['fichiers']} fichiers .tex)" if m["fichiers"] > 1 else ""
        L.append(
            f"  Manuscrit   : {m['lignes']} lignes, {m['sections']} sections, "
            f"{m['figures']} figures{multi}"
        )
    L.append("")
    L.append("  RECADRAGE DÛ : " + ("OUI" if d["recadrage_du"] else "non"))
    for x in d["motifs"]:
        L.append(f"    · {x}")
    if d["signaux_scission"]:
        L.append(f"  Signaux de SCISSION ({len(d['signaux_scission'])}) :")
        for x in d["signaux_scission"]:
            L.append(f"    · {x}")
    return "\n".join(L)


def main() -> int:
    args = [a for a in sys.argv[1:]]
    as_json = "--json" in args
    quiet = "--quiet" in args
    priorites = "--priorites" in args
    pos = [a for a in args if not a.startswith("--")]

    if "--portfolio" in args:
        racine = Path(pos[0]).expanduser().resolve() if pos else MTBC_ROOT
        print(rendu_portfolio(racine))
        return 0

    root = resoudre(pos[0] if pos else None)
    if root is None:
        if quiet:
            return 0
        print("Aucun projet structuré trouvé (pas de cahier_de_labo.md dans les ancêtres).",
              file=sys.stderr)
        return 1

    d = collecter(root)

    if quiet:
        # Sortie SILENCIEUSE sauf si le recadrage est dû : ce mode alimente le
        # hook SessionStart, qui ne doit rien coûter quand tout va bien.
        if d["recadrage_du"]:
            motifs = " ; ".join(d["motifs"])
            print(f"Recadrage dû sur {d['projet']} — {motifs}. Lancer /recadrage.")
            if d["signaux_scission"]:
                print(f"  Signaux de scission : {' ; '.join(d['signaux_scission'])}")
        return 0

    if as_json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
    elif priorites:
        print(rendu_priorites(d))
    else:
        print(rendu_lisible(d))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Ne JAMAIS casser une session pour un signal — mais imprimer la TRACE,
        # pas seulement le message : un garde-fou qui avale l'exception protège la
        # session au prix du diagnostic (vécu le 2026-08-12, un KeyError d'une
        # ligne rendu illisible par un `except` qui n'affichait que « 'existe' »).
        import traceback
        print("[recadrage_signals] échec non bloquant :", file=sys.stderr)
        traceback.print_exc()
        sys.exit(0)
