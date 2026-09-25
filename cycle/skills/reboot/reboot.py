#!/usr/bin/env python3
"""`/reboot` — diagnostic et cycle de reboot d'un projet (pistes AB1-AB4).

Sous-commandes en LECTURE SEULE : `diagnostic` (verdict HARD/SOFT/AUCUN, règles
1-5 du plan `audit/2026-09-21/plan_reboot_versionnage.md` § AB.3), `status`
(état dérivé du reboot en cours), `signals --quiet` (bloc pour
`session_context.sh`), `affirmations` (prévisualisation de `affirmations.md` et
du nouveau `pistes.md`, § AB.5 — écrit seulement avec `--ecrire`/`--pistes-ecrire`),
`lire-archive` (lecture d'une archive de reboot déjà produite par `hard`).
`affirmation <id>`, `hard`, `annuler` (pistes AB2-AB3), `soft`, `recycler`,
`clore` (piste AB4) ÉCRIVENT.

Usage :
    python3 reboot.py diagnostic [<projet>] [--json]
    python3 reboot.py status [<projet>] [--legacy] [--json]
    python3 reboot.py signals [<projet>] --quiet
    python3 reboot.py affirmations [<projet>] [--ecrire F] [--pistes-ecrire F] [--json]
                                    [--migrate] [--carrefour-match]
    python3 reboot.py affirmation <id> [<projet>] [--statut ...] [--preuve ...] [--notes ...] [--apply]
    python3 reboot.py hard [<projet>] [--apply] [--garder-article] [--commit-article]
                            [--kb-renvoi] [--suffixe S]
    python3 reboot.py annuler <date> [<projet>] [--suffixe S] [--apply]
    python3 reboot.py soft [<projet>] [--apply]
    python3 reboot.py recycler <chemin> [<projet>] [--vers DEST] [--verdict recyclé|réécrit|rejeté]
                               [--lien] [--apply]
    python3 reboot.py lire-archive [fichier] [<projet>] [--grep MOTIF] [--json]
    python3 reboot.py clore [<projet>] [--apply]

Sans argument positionnel, la racine est localisée en remontant depuis le
répertoire courant (5 niveaux max, comme le skill `pistes`) jusqu'au premier
répertoire portant `cahier_de_labo.md`.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

HOME = Path.home()
SKILL_DIR = Path(__file__).resolve().parent


def _skill_voisin(nom: str) -> Path:
    """Chemin d'un skill co-localise dans le meme plugin (`bdd`, `pistes`, `cycle-projet`,
    `init-project` en font tous partie) : chemin relatif d'abord, portable apres
    clonage/installation ; repli sur le skill personnel pour qui n'a que celui-ci."""
    candidat = SKILL_DIR.parent / nom
    return candidat if candidat.is_dir() else HOME / ".claude" / "skills" / nom


ENV_VERSION_PY = HOME / "docs" / "environnement" / "outils" / "env_version.py"
BDD_PY = _skill_voisin("bdd") / "bdd.py"
BDD_REGISTRE = HOME / "docs" / "environnement" / "bdd" / "registre.json"
CARREFOUR_PY = _skill_voisin("pistes") / "carrefour.py"
CYCLE_STATUS_DIR = _skill_voisin("cycle-projet")
INIT_PROJECT_DIR = _skill_voisin("init-project")
OUTILS_ENVIRONNEMENT_DIR = HOME / "docs" / "environnement" / "outils"
PROFIL_PLUGINS_PY = OUTILS_ENVIRONNEMENT_DIR / "profil_plugins.py"


def _home_donnees() -> Path:
    """`REBOOT_HOME` (piste AB6) : surcharge UNIQUEMENT les répertoires que `hard
    --kb-renvoi` et l'archivage de mémoire native peuvent ÉCRIRE hors du projet cible —
    jamais les scripts partagés ci-dessus (`ENV_VERSION_PY`, `BDD_PY`...), lus en lecture
    seule et déjà exercés contre leurs propres fixtures (`test_env_version.py`,
    `test_bdd_*.py`) : un test de `/reboot` les appelle réellement plutôt que de les
    simuler. Fonction (pas une constante figée à l'import) pour que la variable
    d'environnement puisse être posée PAR test, après l'import du module."""
    return Path(os.environ["REBOOT_HOME"]) if os.environ.get("REBOOT_HOME") else HOME


def _knowledge_dir() -> Path:
    return _home_donnees() / ".agents" / "knowledge"

STATUTS_AFFIRMATION = ("non testée", "en test", "prouvée", "réfutée", "abandonnée")

REPERTOIRES_CLOTURE = ("clos_soumis", "clos_accepte", "clos", "clos_abandonne")

RE_ENV_PROJET = re.compile(r"\*\*Environnement\s*:\*\*\s*v(\d+\.\d+\.\d+)")
RE_REECRIT = re.compile(r"\*\*R[ée]écrit le\s*:\*\*\s*(\d{4}-\d{2}-\d{2})")
RE_CAHIER_DATE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})", re.MULTILINE)
RE_CITATION_STORE = re.compile(r"\b([a-z][a-z0-9_-]*)@([A-Za-z0-9_.+-]+)\b")

# --------------------------------------------------------------------------
# Liste blanche et catégories du reboot `hard` (AB.4 du plan)
# --------------------------------------------------------------------------

LISTE_BLANCHE_RACINE = {
    "CLAUDE.md", "cahier_de_labo.md", "etat_des_decouvertes.md", "pistes.md",
    "article", ".claude", "litterature_review", "archives", ".gitignore",
    "README.md", ".git",
}
DIRS_NOMMEES_ARCHIVE = ("analyses", "résultats", "resultats", "experiments", "data", "bilans")
FICHIERS_REGISTRES_RACINE = (
    "claim_check.md", "fig_check.md", "tab_check.md",
    "plan_narratif.md", "verdict_diffusion.md", "cadrage_editorial.md",
    "DERNIERE_SESSION.md", "JOURNAL.md", "reanalysis_registry.md",
)

try:
    if str(CYCLE_STATUS_DIR) not in sys.path:
        sys.path.insert(0, str(CYCLE_STATUS_DIR))
    import cycle_status  # type: ignore
except Exception:
    cycle_status = None  # repli : phase déclarée/observée indisponible

try:
    if str(SKILL_DIR) not in sys.path:
        sys.path.insert(0, str(SKILL_DIR))
    import affirmations as affirmations_mod  # type: ignore
except Exception:
    affirmations_mod = None  # repli : sous-commandes `affirmations`/`affirmation`/`hard` indisponibles

try:
    if str(INIT_PROJECT_DIR) not in sys.path:
        sys.path.insert(0, str(INIT_PROJECT_DIR))
    import init_project as _init_mod  # type: ignore
except Exception:
    _init_mod = None  # repli : `hard` (gabarits des nouveaux artefacts) indisponible

try:
    if str(OUTILS_ENVIRONNEMENT_DIR) not in sys.path:
        sys.path.insert(0, str(OUTILS_ENVIRONNEMENT_DIR))
    import deplacer_projet as _deplacer_projet_mod  # type: ignore
except Exception:
    _deplacer_projet_mod = None  # repli : archivage de la mémoire native sauté


def _section_repli(txt: str, n: int) -> str:
    """Repli de `cycle_status.section` si le module est indisponible."""
    m = re.search(rf"^##\s*{n}\.\s.*$", txt, re.MULTILINE)
    if not m:
        return ""
    debut = m.end()
    suite = re.search(r"^##\s", txt[debut:], re.MULTILINE)
    return txt[debut: debut + suite.start()] if suite else txt[debut:]


# --------------------------------------------------------------------------
# Localisation de la racine (même convention que le skill `pistes`)
# --------------------------------------------------------------------------

def trouver_racine(depart: Path, max_niveaux: int = 5) -> Path | None:
    p = depart.resolve()
    for _ in range(max_niveaux + 1):
        if (p / "cahier_de_labo.md").is_file():
            return p
        if p.parent == p:
            break
        p = p.parent
    return None


def resoudre_racine(arg: str | None) -> Path:
    depart = Path(arg).resolve() if arg else Path.cwd()
    if arg and not depart.is_dir():
        # Un chemin inexistant (faute de frappe, mauvais cwd) ne doit jamais remonter
        # silencieusement vers un ancêtre réel sans rapport — mesuré le 2026-09-21 :
        # un chemin relatif fautif a fait retomber le diagnostic sur `environnement`
        # lui-même au lieu de refuser franchement.
        print(f"REFUS : {depart} n'est pas un répertoire existant.", file=sys.stderr)
        raise SystemExit(1)
    racine = trouver_racine(depart)
    if racine is None:
        print(f"Aucun projet structuré trouvé (pas de cahier_de_labo.md en remontant depuis {depart}).",
              file=sys.stderr)
        raise SystemExit(1)
    return racine


# --------------------------------------------------------------------------
# Adaptateurs env_version / bdd / carrefour, avec repli
# --------------------------------------------------------------------------

def adaptateur_env_version(projet: Path) -> dict:
    """Repli explicite : versionnage non déployé, script absent ou sortie illisible."""
    if not ENV_VERSION_PY.is_file():
        return {"disponible": False, "motif": "outils/env_version.py introuvable — versionnage non déployé"}
    try:
        r = subprocess.run(
            [sys.executable, str(ENV_VERSION_PY), "verdict", str(projet), "--json"],
            capture_output=True, text=True, timeout=20,
        )
    except Exception as exc:  # binaire absent, timeout...
        return {"disponible": False, "motif": f"échec d'appel à env_version.py : {exc}"}
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        message = (r.stderr or r.stdout or "sortie illisible").strip()[:200]
        return {"disponible": False, "motif": message or "sortie illisible"}
    data["disponible"] = True
    return data


def _charger_stores_connus() -> set[str]:
    if not BDD_REGISTRE.is_file():
        return set()
    try:
        registre = json.loads(BDD_REGISTRE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    return set(registre.get("stores", {}).keys())


def adaptateur_bdd_check(store: str) -> dict:
    if not BDD_PY.is_file():
        return {"disponible": False, "motif": "skill bdd introuvable — versionnage des données non déployé"}
    try:
        r = subprocess.run(
            [sys.executable, str(BDD_PY), "check", store, "--json"],
            capture_output=True, text=True, timeout=60,
        )
    except Exception as exc:
        return {"disponible": False, "motif": f"échec d'appel à bdd.py : {exc}"}
    for ligne in r.stdout.splitlines():
        ligne = ligne.strip()
        if ligne.startswith("{"):
            try:
                data = json.loads(ligne)
            except json.JSONDecodeError:
                continue
            data["disponible"] = True
            return data
    message = (r.stdout or r.stderr or "store non initialisé ou sortie sans JSON").strip()[:200]
    return {"disponible": False, "motif": message}


def citations_stores(root: Path) -> list[tuple[str, str]]:
    """`<store>@<version>` cités dans l'état et les `claim_check.md` du projet."""
    connus = _charger_stores_connus()
    if not connus:
        return []
    fichiers = [root / "etat_des_decouvertes.md", root / "claim_check.md"]
    fichiers += sorted(root.glob("article*/claim_check.md"))
    trouve: dict[str, str] = {}
    for f in fichiers:
        if not f.is_file():
            continue
        try:
            texte = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for store, version in RE_CITATION_STORE.findall(texte):
            if store in connus:
                trouve.setdefault(store, version)
    return sorted(trouve.items())


def adaptateur_overlap(root: Path) -> dict:
    if not CARREFOUR_PY.is_file():
        return {"disponible": False, "motif": "carrefour.py introuvable"}
    try:
        r = subprocess.run(
            [sys.executable, str(CARREFOUR_PY), "overlap", "-k", "60"],
            capture_output=True, text=True, timeout=60, cwd=str(root),
        )
    except Exception as exc:
        return {"disponible": False, "motif": f"échec d'appel à carrefour.py : {exc}"}
    lignes = [l for l in r.stdout.splitlines() if root.name in l]
    return {"disponible": True, "lignes": lignes[:5]}


RE_LIGNE_MATCH = re.compile(
    r"^(\d\.\d\d) (.) (.{30}) (.{10}) (.{8}) (.{78}) \| (.*)$")


def adaptateur_match(root: Path, enonce: str, k: int = 3) -> dict:
    """`carrefour.py match` sur un énoncé isolé (AB8a : lot sur les P1). Pas de sortie
    JSON côté `carrefour.py` — parsée en texte fixe, comme `adaptateur_overlap` le fait
    déjà pour `overlap` ; c'est la convention déjà en usage dans ce fichier pour ce script."""
    if not CARREFOUR_PY.is_file():
        return {"disponible": False, "motif": "carrefour.py introuvable"}
    try:
        r = subprocess.run(
            [sys.executable, str(CARREFOUR_PY), "match", enonce, "-k", str(k)],
            capture_output=True, text=True, timeout=30, cwd=str(root),
        )
    except Exception as exc:
        return {"disponible": False, "motif": f"échec d'appel à carrefour.py : {exc}"}
    candidats = []
    for ligne in r.stdout.splitlines():
        m = RE_LIGNE_MATCH.match(ligne)
        if m:
            score, marque, projet, _type, _ref, texte, _pourquoi = m.groups()
            candidats.append({"score": float(score), "vivant": marque.strip() == "",
                               "projet": projet.strip(), "texte": texte.strip()})
    return {"disponible": True, "candidats": candidats[:k]}


def annoter_carrefour_voisins(root: Path, affirmations: list[dict]) -> int:
    """Annote chaque affirmation `[non testée]`/`[en test]` (les P1, cf. AB8b) du meilleur
    voisin VIVANT trouvé par `carrefour.py match` (AB8a). N'écrit rien sur disque — mute la
    `notes` de chaque dict en mémoire, à générer ensuite comme les autres champs. Rend le
    nombre d'affirmations annotées (0 si `carrefour.py` est indisponible : dégradation
    silencieuse assumée, comme les autres adaptateurs de ce fichier)."""
    n = 0
    for a in affirmations:
        if a["statut"] not in ("non testée", "en test"):
            continue
        resultat = adaptateur_match(root, a["enonce"])
        if not resultat["disponible"]:
            continue
        vivants = [c for c in resultat["candidats"] if c["vivant"]]
        if not vivants:
            continue
        top = vivants[0]
        note = f"voisin carrefour : {top['projet']} ({top['score']:.2f}) — {top['texte']}"
        a["notes"] = (a["notes"] + " ; " if a["notes"] else "") + note
        n += 1
    return n


# --------------------------------------------------------------------------
# Mesures (AB.3)
# --------------------------------------------------------------------------

def _age_jours(date_iso: str | None) -> int | None:
    if not date_iso:
        return None
    try:
        d = _dt.date.fromisoformat(date_iso)
    except ValueError:
        return None
    return (_dt.date.today() - d).days


def _derniere_date_cahier(root: Path) -> str | None:
    chemin = root / "cahier_de_labo.md"
    if not chemin.is_file():
        return None
    dates = RE_CAHIER_DATE.findall(chemin.read_text(encoding="utf-8", errors="replace"))
    return max(dates) if dates else None


def _manuscrit_mur(root: Path, manuscrits: list[dict]) -> bool:
    if any(m.get("version_fr") for m in manuscrits):
        return True
    if any(root.glob("*_submission")):
        return True
    return False


def collecter_mesures(root: Path) -> dict:
    etat_path = root / "etat_des_decouvertes.md"
    etat_txt = etat_path.read_text(encoding="utf-8", errors="replace") if etat_path.is_file() else ""

    m_env = RE_ENV_PROJET.search(etat_txt)
    env_projet = m_env.group(1) if m_env else None
    rattache = env_projet is not None

    m_reecrit = RE_REECRIT.search(etat_txt)
    age_etat = _age_jours(m_reecrit.group(1)) if m_reecrit else None

    derniere_cahier = _derniere_date_cahier(root)
    age = _age_jours(derniere_cahier)
    cahier_entrees = len(RE_CAHIER_DATE.findall(
        (root / "cahier_de_labo.md").read_text(encoding="utf-8", errors="replace")
    )) if (root / "cahier_de_labo.md").is_file() else 0

    squelette = "SQUELETTE NON RENSEIGN" in etat_txt

    statut = root.parent.name if root.parent.name in REPERTOIRES_CLOTURE else "en_cours"

    infos_cycle: dict = {}
    if cycle_status is not None:
        try:
            infos_cycle = cycle_status.collecte(root)
        except Exception as exc:  # ne bloque jamais le diagnostic
            infos_cycle = {"erreur": str(exc)}
    phase_declaree = infos_cycle.get("phase_declaree")
    phase_observee = infos_cycle.get("phase_observee")
    phase = phase_declaree if phase_declaree is not None else phase_observee
    manuscrits: list[dict] = infos_cycle.get("manuscrits") or []
    manuscrit_mur = _manuscrit_mur(root, manuscrits)

    env = adaptateur_env_version(root)
    delta = env.get("consequence") if (env.get("disponible") and rattache) else None
    env_courant = env.get("courante")

    donnees = []
    for store, version_citee in citations_stores(root):
        chk = adaptateur_bdd_check(store)
        donnees.append({
            "store": store, "version_citee": version_citee,
            "disponible": chk.get("disponible", False),
            "statut": chk.get("statut"), "motif": chk.get("motif"),
        })
    donnees_derive = any(d.get("statut") == "derive" for d in donnees)

    return {
        "statut": statut,
        "env_projet": env_projet, "env_courant": env_courant, "rattache": rattache,
        "delta": delta, "env_disponible": env.get("disponible", False), "env_motif": env.get("motif"),
        "age": age, "derniere_entree_cahier": derniere_cahier, "cahier_entrees": cahier_entrees,
        "age_etat": age_etat, "reecrit_le": m_reecrit.group(1) if m_reecrit else None,
        "squelette": squelette,
        "phase_declaree": phase_declaree, "phase_observee": phase_observee, "phase": phase,
        "manuscrit_mur": manuscrit_mur,
        "donnees": donnees, "donnees_derive": donnees_derive,
        "article_non_commite": _article_non_commite(root, manuscrits),
        "hors_format_init_project": not etat_path.is_file() or not (root / "pistes.md").is_file(),
    }


def _article_non_commite(root: Path, manuscrits: list[dict]) -> bool:
    for m in manuscrits:
        chemin_article = root / m["repertoire"]
        if not (chemin_article / ".git").is_dir():
            continue
        try:
            r = subprocess.run(["git", "status", "--porcelain"], cwd=str(chemin_article),
                                capture_output=True, text=True, timeout=10)
        except Exception:
            continue
        if r.stdout.strip():
            return True
    return False


# --------------------------------------------------------------------------
# Règles 1-5 (AB.3)
# --------------------------------------------------------------------------

def evaluer_regles(mesures: dict) -> tuple[str, list[str], list[str]]:
    reserves = []
    if mesures["manuscrit_mur"]:
        reserves.append("manuscrit mûr (main_fr.tex et/ou répertoire de soumission présents) "
                         "→ envisager `hard --garder-article`")
    if mesures["article_non_commite"]:
        reserves.append("article/ porte des modifications non committées")
    if mesures["hors_format_init_project"]:
        reserves.append("projet hors format init-project (état ou pistes.md absent)")

    # Règle 1 : répertoire de clôture.
    if mesures["statut"] in REPERTOIRES_CLOTURE:
        return "AUCUN", [f"projet sous {mesures['statut']}/ — ramener en en_cours/ "
                          f"(deplacer_projet.py) avant tout reboot"], reserves

    age, age_etat = mesures["age"], mesures["age_etat"]
    rattache, delta = mesures["rattache"], mesures["delta"]

    # Règle 2 : projet actif et récent.
    if (age is not None and age < 30 and age_etat is not None and age_etat < 30
            and delta in (None, "aucune", "soft")):
        motifs = [f"projet actif et récent (âge {age} j, état {age_etat} j), sans dérive majeure"]
        if not rattache:
            reserves.append("poser **Environnement :** dans l'état (projet jamais rattaché)")
        return "AUCUN", motifs, reserves

    phase = mesures["phase"]
    donnees_derive = mesures["donnees_derive"]

    # Règle 3 : HARD.
    motifs_hard = []
    if delta == "hard":
        motifs_hard.append(f"delta d'environnement MAJEUR ({mesures['env_projet']} → v{mesures['env_courant']})")
    if not rattache and (age is None or age >= 90):
        motifs_hard.append("estampille d'environnement absente et "
                            + (f"dernière entrée de cahier il y a {age} j (≥ 90)" if age is not None
                               else "aucune entrée de cahier datée"))
    # Le squelette ne compte que s'il est LUI-MÊME ancien. Un squelette fraîchement posé
    # signale une migration `init-project --migrate`, pas un abandon : mesuré le 2026-09-22
    # (AB7), la migration du 2026-09-16 a posé 54 squelettes d'un coup sur les 141 projets
    # de `en_cours/`, dont 32 sur un cahier ≥ 5 entrées. Sans cette condition, le critère
    # n'ajoutait que 2 verdicts HARD réels sur tout le dépôt (les 18 autres l'étaient déjà
    # par l'âge du cahier), et ces 2 étaient des SOFT sur-classés sur la foi d'un artefact
    # vieux de six jours. Un critère presque toujours redondant et parfois faux se corrige
    # plutôt que de s'entretenir.
    if (mesures["squelette"] and mesures["cahier_entrees"] >= 5
            and (age_etat is None or age_etat >= 90)):
        motifs_hard.append(f"squelette non renseigné sur un cahier à {mesures['cahier_entrees']} "
                            f"entrées, et l'état lui-même n'a pas été réécrit depuis "
                            + (f"{age_etat} j" if age_etat is not None else "jamais"))
    if donnees_derive and phase is not None and phase <= 3:
        motifs_hard.append(f"dérive de données citées, phase {phase} ≤ 3")
    if motifs_hard:
        return "HARD", motifs_hard, reserves

    # Règle 4 : SOFT.
    motifs_soft = []
    if delta == "soft":
        motifs_soft.append(f"delta d'environnement MINEUR ({mesures['env_projet']} → v{mesures['env_courant']})")
    if not rattache and age is not None and 30 <= age < 90:
        motifs_soft.append(f"estampille absente, dernière entrée de cahier il y a {age} j (30-90)")
    if donnees_derive and phase is not None and phase >= 4:
        motifs_soft.append(f"dérive de données citées, phase {phase} ≥ 4")
    if motifs_soft:
        return "SOFT", motifs_soft, reserves

    # Règle 5 : par défaut.
    return "AUCUN", ["aucune règle HARD/SOFT déclenchée"], reserves


# --------------------------------------------------------------------------
# Sous-commande `diagnostic`
# --------------------------------------------------------------------------

def cmd_diagnostic(root: Path, as_json: bool) -> int:
    mesures = collecter_mesures(root)
    verdict, motifs, reserves = evaluer_regles(mesures)
    resultat = {
        "projet": root.name, "chemin": str(root), "date": _dt.date.today().isoformat(),
        "verdict": verdict, "motifs": motifs, "reserves": reserves, "mesures": mesures,
    }
    if as_json:
        print(json.dumps(resultat, ensure_ascii=False, indent=2))
        return 0
    print(f"{root.name} — verdict {verdict}")
    for m in motifs:
        print(f"  - {m}")
    if reserves:
        print("  réserves :")
        for rv in reserves:
            print(f"    · {rv}")
    print(f"  mesures : statut={mesures['statut']} rattaché={mesures['rattache']} "
          f"env={mesures['env_projet']}→v{mesures['env_courant']} delta={mesures['delta']} "
          f"âge={mesures['age']}j âge_état={mesures['age_etat']}j squelette={mesures['squelette']} "
          f"cahier_entrées={mesures['cahier_entrees']} phase={mesures['phase']} "
          f"manuscrit_mûr={mesures['manuscrit_mur']}")
    if not mesures["env_disponible"]:
        print(f"  [env_version indisponible : {mesures['env_motif']}]")
    return 0


# --------------------------------------------------------------------------
# Sous-commande `status`
# --------------------------------------------------------------------------

RE_PISTE_MIGRATION = re.compile(
    r"^##\s+P\d+\.\s*Migration d'environnement.*?\[(à faire|en cours|réalisé|abandonné)\]",
    re.MULTILINE,
)

LEGACY_FICHIERS = ("reboot_state.md", "reanalysis_registry.md")


def _est_archive_de_ce_skill(archive: Path) -> bool:
    """Une archive de CE skill porte un `MANIFEST.json` ; celles de `mtbc-reboot`, non.

    Les deux outils partagent la convention de nom `archives/<date>_reboot/`, si bien qu'un
    glob seul confond un reboot conduit ici avec un reboot d'avril 2026. Mesuré le 2026-09-22
    (AB7) : `status` rendait « ARCHIVÉ — rétablissement non encore lancé » sur les six projets
    vestiges (L4.14, L4.11, L4.15…), et comme `signals` en dérive le bloc de démarrage, chaque
    session ouverte sur l'un d'eux aurait vu un rétablissement en attente qui n'existe pas.
    Le `MANIFEST.json` est le discriminant sûr : il est écrit par `cmd_hard` et n'a jamais
    existé dans l'ancien format, dont les archives portent plutôt `knowledge_entries_removed.md`.
    """
    return (archive / "MANIFEST.json").is_file()


def _etat_derive(root: Path) -> tuple[str, list[str]]:
    notes = []
    toutes = sorted(root.glob("archives/*_reboot"))
    archives = [a for a in toutes if _est_archive_de_ce_skill(a)]
    legacy_seules = [a for a in toutes if a not in archives]
    if legacy_seules and not archives:
        notes.append(f"{len(legacy_seules)} archive(s) d'un reboot ANTÉRIEUR à ce skill "
                     f"(pas de MANIFEST.json ; la plus récente : "
                     f"{legacy_seules[-1].relative_to(root)}) — les lire avec `status --legacy`, "
                     f"elles ne valent pas reboot courant")
    if archives:
        derniere_archive = archives[-1]
        notes.append(f"archive la plus récente : {derniere_archive.relative_to(root)}")
        affirmations = root / "affirmations.md"
        affirmations_gelees = derniere_archive / "affirmations.md"
        if affirmations_gelees.is_file():
            return "CLOS", notes + [f"affirmations.md gelé dans "
                                    f"{affirmations_gelees.relative_to(root)} — clos par `/reboot clore`"]
        if not affirmations.is_file():
            return "ARCHIVÉ", notes + ["affirmations.md absent — rétablissement (piste AB2) non encore lancé"]
        return "RÉTABLISSEMENT_EN_COURS", notes + ["affirmations.md présent — lire son frontmatter "
                                                    "(`status --legacy` non concerné)"]

    pistes_md = root / "pistes.md"
    if pistes_md.is_file():
        m = RE_PISTE_MIGRATION.search(pistes_md.read_text(encoding="utf-8", errors="replace"))
        if m:
            etat = m.group(1)
            if etat == "réalisé":
                return "MIGRATION_CLOSE", notes
            if etat == "en cours":
                return "MIGRATION_OUVERTE", notes

    return "AUCUN_REBOOT", notes


def cmd_status(root: Path, legacy: bool, as_json: bool) -> int:
    etat, notes = _etat_derive(root)
    resultat = {"projet": root.name, "chemin": str(root), "etat": etat, "notes": notes}
    if legacy:
        legacy_trouves = {}
        for nom in LEGACY_FICHIERS:
            f = root / nom
            if f.is_file():
                extrait = f.read_text(encoding="utf-8", errors="replace").splitlines()[:5]
                legacy_trouves[nom] = extrait
        resultat["legacy"] = legacy_trouves
    if as_json:
        print(json.dumps(resultat, ensure_ascii=False, indent=2))
        return 0
    print(f"{root.name} — état {etat}")
    for n in notes:
        print(f"  - {n}")
    if legacy and resultat.get("legacy"):
        for nom, extrait in resultat["legacy"].items():
            print(f"  legacy {nom} : {' / '.join(extrait)}")
    elif legacy:
        print("  legacy : aucun fichier reboot_state.md / reanalysis_registry.md")
    return 0


# --------------------------------------------------------------------------
# Sous-commande `signals`
# --------------------------------------------------------------------------

def cmd_signals(root: Path, quiet: bool) -> int:
    lignes = []
    etat, _ = _etat_derive(root)
    if etat == "AUCUN_REBOOT":
        mesures = collecter_mesures(root)
        verdict, motifs, _ = evaluer_regles(mesures)
        if verdict != "AUCUN":
            motif = motifs[0] if motifs else verdict
            lignes.append(f"[REBOOT — diagnostic dû ({verdict}) : {motif} ; lancer /reboot diagnostic]")

    fichier_affirmations = root / "affirmations.md"
    if fichier_affirmations.is_file():
        try:
            txt = fichier_affirmations.read_text(encoding="utf-8", errors="replace")
        except OSError:
            txt = ""
        m = re.search(
            r"compteurs:\s*\n\s*non_testee:\s*(\d+)\s*\n\s*en_test:\s*(\d+)\s*\n"
            r"\s*prouvee:\s*(\d+)\s*\n\s*refutee:\s*(\d+)\s*\n\s*abandonnee:\s*(\d+)",
            txt,
        )
        if m:
            non_testee, en_test, prouvee, refutee, _abandonnee = (int(x) for x in m.groups())
            if non_testee or en_test:
                lignes.append(f"[AFFIRMATIONS — {non_testee} non testées / {en_test} en test / "
                               f"{prouvee} prouvées / {refutee} réfutées — rédaction bloquée "
                               f"(P1 : {non_testee + en_test} non tranchées)]")

    for l in lignes:
        print(l)
    if not lignes and not quiet:
        print(f"{root.name} : rien à signaler.")
    return 0


# --------------------------------------------------------------------------
# Sous-commande `affirmations` (prévisualisation — AB2)
# --------------------------------------------------------------------------

def cmd_affirmations(root: Path, ecrire: str | None, pistes_ecrire: str | None, as_json: bool,
                      migrer: bool = False, carrefour_match: bool = False) -> int:
    if affirmations_mod is None:
        print("REFUS : module affirmations.py introuvable à côté de reboot.py", file=sys.stderr)
        return 1
    section_fn = cycle_status.section if cycle_status is not None else _section_repli
    mesures = collecter_mesures(root)
    migrer_effectif = migrer and mesures["squelette"]
    if migrer and not migrer_effectif:
        print("--migrate ignoré : l'état legacy n'est pas un squelette, rien à en tirer "
              "(cf. AB8a — le dépouillement du cahier ne vaut que pour un état vide)",
              file=sys.stderr)
    aff = affirmations_mod.assembler_affirmations(root, section_fn, migrer=migrer_effectif)
    affirmations_mod.assigner_pistes(aff)  # AB8b : avant toute génération, cf. sa docstring
    if carrefour_match:
        n = annoter_carrefour_voisins(root, aff)
        print(f"carrefour : {n} affirmation(s) à rétablir annotée(s) d'un voisin vivant", file=sys.stderr)
    compteurs = affirmations_mod.compter_statuts(aff)

    if as_json:
        print(json.dumps({"projet": root.name, "compteurs": compteurs, "affirmations": aff},
                          ensure_ascii=False, indent=2))
    else:
        print(affirmations_mod.generer_affirmations_md(root, aff, mesures))

    if ecrire:
        chemin = Path(ecrire)
        chemin.write_text(affirmations_mod.generer_affirmations_md(root, aff, mesures), encoding="utf-8")
        print(f"écrit : {chemin}", file=sys.stderr)
    if pistes_ecrire:
        chemin = Path(pistes_ecrire)
        chemin.write_text(affirmations_mod.generer_pistes_reboot_md(root, aff), encoding="utf-8")
        print(f"écrit : {chemin}", file=sys.stderr)
    return 0


# --------------------------------------------------------------------------
# Sous-commande `affirmation <id>` (met à jour une ligne — ÉCRIT)
# --------------------------------------------------------------------------

RE_LIGNE_AFFIRMATION = re.compile(r"^\|\s*(A\d+)\s*\|")


def _recompter_compteurs_frontmatter(lignes: list[str]) -> list[str]:
    compte = {"non_testee": 0, "en_test": 0, "prouvee": 0, "refutee": 0, "abandonnee": 0}
    cle_par_statut = {"non testée": "non_testee", "en test": "en_test", "prouvée": "prouvee",
                       "réfutée": "refutee", "abandonnée": "abandonnee"}
    for l in lignes:
        m = RE_LIGNE_AFFIRMATION.match(l)
        if not m:
            continue
        cols = [c.strip() for c in l.strip().strip("|").split("|")]
        if len(cols) != 10:
            continue
        for libelle, cle in cle_par_statut.items():
            if cols[6].startswith(libelle):
                compte[cle] += 1
                break
    dans_bloc = False
    for i, l in enumerate(lignes):
        if l.strip() == "compteurs:":
            dans_bloc = True
            continue
        if dans_bloc:
            m2 = re.match(r"^(\s*)(non_testee|en_test|prouvee|refutee|abandonnee):\s*\d+\s*$", l)
            if m2:
                lignes[i] = f"{m2.group(1)}{m2.group(2)}: {compte[m2.group(2)]}"
            elif l.strip() == "---":
                dans_bloc = False
    return lignes


def cmd_affirmation(root: Path, id_: str, statut: str | None, preuve: str | None,
                     notes: str | None, apply: bool) -> int:
    chemin = root / "affirmations.md"
    if not chemin.is_file():
        print(f"REFUS : {chemin} introuvable — lancer d'abord "
              f"`reboot.py affirmations --ecrire {chemin}`", file=sys.stderr)
        return 1
    if statut is not None and statut not in STATUTS_AFFIRMATION:
        print(f"REFUS : statut '{statut}' hors nomenclature {STATUTS_AFFIRMATION}", file=sys.stderr)
        return 1

    lignes = chemin.read_text(encoding="utf-8").splitlines()
    idx = None
    for i, l in enumerate(lignes):
        m = RE_LIGNE_AFFIRMATION.match(l)
        if m and m.group(1) == id_:
            idx = i
            break
    if idx is None:
        print(f"REFUS : id {id_} introuvable dans {chemin}", file=sys.stderr)
        return 1
    cols = [c.strip() for c in lignes[idx].strip().strip("|").split("|")]
    if len(cols) != 10:
        print(f"REFUS : ligne {id_} n'a pas les 10 colonnes attendues (format inattendu)", file=sys.stderr)
        return 1

    avant = lignes[idx]
    if statut is not None:
        horodate = f" <{_dt.date.today().isoformat()}>" if statut in ("prouvée", "réfutée", "abandonnée") else ""
        cols[6] = statut + horodate
    if preuve is not None:
        cols[8] = preuve
    if notes is not None:
        cols[9] = notes
    apres = "| " + " | ".join(c.replace("|", "/") for c in cols) + " |"

    if not apply:
        print(f"simulé (--apply pour écrire) :\n  avant : {avant}\n  après : {apres}")
        return 0

    lignes[idx] = apres
    lignes = _recompter_compteurs_frontmatter(lignes)
    chemin.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    print(f"écrit : {chemin} ({id_} → {statut or '(statut inchangé)'})")
    piste = cols[7]
    if piste not in ("", "—") and statut in ("prouvée", "réfutée", "abandonnée"):
        print(f"  piste associée {piste} : clore manuellement (`/pistes done {piste}` puis "
              f"`impact_done.py {piste}`) — non automatisé par cette sous-commande")
    return 0


# --------------------------------------------------------------------------
# Utilitaires d'écriture — chaque opération est ENREGISTRÉE (pour MANIFEST.json
# et `annuler`) que l'on soit en dry-run ou en `--apply` ; seule l'exécution
# réelle est conditionnée par `apply`, ce qui garantit qu'un dry-run n'écrit
# jamais rien (test AB3 : « dry-run à empreinte identique »).
# --------------------------------------------------------------------------

def _deplacer(ops: list[dict], apply: bool, src: Path, dst: Path) -> None:
    ops.append({"type": "move", "src": str(src), "dst": str(dst)})
    if apply:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))


def _copier(ops: list[dict], apply: bool, src: Path, dst: Path) -> None:
    ops.append({"type": "copy", "src": str(src), "dst": str(dst)})
    if apply:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)


def _ecrire(ops: list[dict], apply: bool, dst: Path, contenu: str) -> None:
    ops.append({"type": "create", "dst": str(dst)})
    if apply:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(contenu, encoding="utf-8")


def _mkdir(ops: list[dict], apply: bool, dst: Path) -> None:
    ops.append({"type": "mkdir", "dst": str(dst)})
    if apply:
        dst.mkdir(parents=True, exist_ok=True)


def _gio_trash(path: Path) -> tuple[bool, str]:
    if shutil.which("gio") is None:
        return False, "commande gio introuvable — laissé en place (règle : jamais rm)"
    try:
        r = subprocess.run(["gio", "trash", str(path)], capture_output=True, text=True, timeout=30)
    except Exception as exc:
        return False, f"échec gio trash : {exc}"
    if r.returncode != 0:
        return False, (r.stderr or r.stdout or "échec gio trash").strip()[:200]
    return True, "déplacé vers la corbeille"


def _appeler_best_effort(cmd: list[str], label: str) -> None:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            print(f"  ⚠ {label} : code {r.returncode} — {(r.stderr or r.stdout).strip()[:200]}",
                  file=sys.stderr)
        else:
            print(f"  ✔ {label}")
    except Exception as exc:
        print(f"  ⚠ {label} : {exc}", file=sys.stderr)


def _git(repo: Path, *args: str, timeout: int = 30):
    try:
        return subprocess.run(["git", *args], cwd=str(repo), capture_output=True,
                              text=True, timeout=timeout)
    except Exception as exc:
        class _R:
            returncode = 1
            stdout = ""
            stderr = str(exc)
        return _R()


def _git_sale(repo: Path) -> bool:
    r = _git(repo, "status", "--porcelain")
    return bool(r.stdout.strip()) if r.returncode == 0 else False


def _manuscrits(root: Path) -> list[dict]:
    if cycle_status is not None:
        try:
            return cycle_status.lire_manuscrits(root)
        except Exception:
            pass
    if (root / "article" / "main.tex").is_file():
        return [{"repertoire": "article"}]
    return []


# --------------------------------------------------------------------------
# Sous-commande `hard` (ÉCRIT — AB3)
# --------------------------------------------------------------------------

def _scaffold_article(root: Path, ops: list[dict], apply: bool, title: str, domain: str) -> None:
    if _init_mod is None:
        return
    art = root / "article"
    _ecrire(ops, apply, art / "main.tex", _init_mod.main_tex_template(root.name, title, domain))
    _ecrire(ops, apply, art / "references.bib", _init_mod.REFERENCES_BIB)
    _ecrire(ops, apply, art / "Makefile", _init_mod.MAKEFILE)
    _ecrire(ops, apply, art / ".gitignore", _init_mod.ARTICLE_GITIGNORE)
    _ecrire(ops, apply, art / "review" / "INDEX.md", _init_mod.review_index_template())
    _mkdir(ops, apply, art / "figures")
    _mkdir(ops, apply, art / "supplementary_materials")
    ops.append({"type": "git_init_article", "dst": str(art)})
    if apply:
        ok, msg = _init_mod.init_article_git_repo(art)
        prefixe = "  ✔" if ok else "  ⚠"
        print(f"{prefixe} article/ : {msg}")


def _bloc_reboot(mesures: dict, tags: dict, nom_archive: str, garder_article: bool,
                 n_aff: int, recadrage_txt: str, today: str) -> str:
    donnees = mesures.get("donnees") or []
    donnees_txt = ", ".join(f"{d['store']}@{d['version_citee']}" for d in donnees) or \
        "aucune citée avant reboot"
    env_legacy = mesures.get("env_projet")
    env_courant = mesures.get("env_courant")
    env_txt = (f"v{env_legacy}" if env_legacy else "non estampillé") + \
        (f" → v{env_courant}" if env_courant else " → (env_version.py indisponible)")
    tag_txt = ", ".join(f"{r}:{t}" for r, t in tags.items()) or "aucun manuscrit git"
    if garder_article:
        article_txt = (f"conservé (`--garder-article`), tag {tag_txt}, bandeau de gel posé sur "
                       f"main.tex/main_fr.tex — rédaction gelée.")
    else:
        article_txt = (f"feuille blanche, manuscrit legacy archivé et tagué ({tag_txt}), rédaction bloquée "
                       f"par P1, puis par la porte 1 que la clôture rouvre (étape 4).")
    recadrage_ligne = (f"verdict archivé dans `archives/{nom_archive}/RECADRAGE.md`, décisions en P2"
                       if recadrage_txt else
                       "`/recadrage` non exécuté avant ce hard — à faire a posteriori, décisions en P2 le cas échéant")
    return dedent(f"""
        ## Reboot

        - **Mode :** hard    **Date :** {today}
        - **Environnement :** {env_txt}
        - **Données citées avant reboot :** {donnees_txt}
        - **Archive :** `archives/{nom_archive}/` — lecture seule, rien ne s'y exécute ni ne s'y
          importe directement ; passer par `/reboot recycler <chemin>` pour en reprendre un élément.
        - **Affirmations :** {n_aff} énoncé(s) à rétablir, voir `affirmations.md` et la piste P1.
        - **Article :** {article_txt}
        - **Recadrage :** {recadrage_ligne}
        """)


def _archiver_memoire_native(root: Path, archive: Path, ops: list[dict], apply: bool) -> None:
    if _deplacer_projet_mod is None:
        return
    try:
        racine_mem = _deplacer_projet_mod.racine_memoire(root)
    except Exception:
        racine_mem = None
    if racine_mem is None:
        return
    mem_dir = _home_donnees() / ".claude" / "projects" / _deplacer_projet_mod.slug(racine_mem) / "memory"
    if not mem_dir.is_dir():
        return
    # `racine_memoire` remonte au premier ancêtre portant un `.git` : dans un monorepo
    # (ex. tous les projets `~/docs/codes/mtbc/*` à plat sous un seul dépôt racine
    # `~/docs/codes`), ce n'est presque jamais `root` lui-même, et `mem_dir` est alors
    # PARTAGÉ par des centaines de projets sans rapport. N'y toucher qu'aux mémoires qui
    # mentionnent réellement ce projet — jamais à l'aveugle sur tout le magasin partagé.
    scope_partage = racine_mem.resolve() != root.resolve()
    motif_projet = re.compile(rf"\b{re.escape(root.name)}\b") if scope_partage else None
    memory_md = mem_dir / "MEMORY.md"
    retires: list[str] = []
    for f in sorted(mem_dir.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        est_projet = f.name.startswith("project_")
        try:
            txt = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            txt = ""
        if not est_projet:
            m = re.search(r"^metadata:\s*\n(?:\s+\S+:.*\n)*?\s*type:\s*(\w+)", txt, re.MULTILINE)
            est_projet = bool(m and m.group(1) == "project")
        if not est_projet:
            continue
        if motif_projet is not None and not motif_projet.search(txt):
            continue
        dst = archive / "memoire_native" / f.name
        _copier(ops, apply, f, dst)
        ops.append({"type": "memoire_trash", "original": str(f), "copie": str(dst)})
        if apply:
            ok, msg = _gio_trash(f)
            if not ok:
                print(f"  ⚠ mémoire native {f.name} non retirée : {msg}", file=sys.stderr)
        retires.append(f.name)
    if retires and memory_md.is_file() and apply:
        txt = memory_md.read_text(encoding="utf-8")
        lignes = txt.splitlines()
        nouvelles = [l for l in lignes if not any(f"]({nom})" in l for nom in retires)]
        if len(nouvelles) != len(lignes):
            memory_md.write_text("\n".join(nouvelles) + "\n", encoding="utf-8")
            ops.append({"type": "memory_md_retire", "fichier": str(memory_md), "entrees": retires})


def _inventaire_kb(root: Path, archive: Path, ops: list[dict], apply: bool,
                   kb_renvoi: bool, today: str) -> None:
    knowledge_dir = _knowledge_dir()
    if not knowledge_dir.is_dir():
        return
    motif = re.compile(rf"\b{re.escape(root.name)}\b")
    trouvailles: dict[str, list[tuple[int, str]]] = {}
    for f in sorted(knowledge_dir.rglob("*.md")):
        try:
            lignes = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        hits = [(i + 1, l.strip()) for i, l in enumerate(lignes) if motif.search(l)]
        if hits:
            trouvailles[str(f.relative_to(knowledge_dir))] = hits
    if not trouvailles:
        return

    corps = [f"# Entrées KB citant {root.name} (reboot hard {today})",
             "",
             "Jamais retirées automatiquement (doctrine : renvoi de péremption seulement)."]
    for chemin, hits in trouvailles.items():
        corps.append(f"\n## {chemin}\n")
        for numero, ligne in hits[:20]:
            corps.append(f"- L{numero} : {ligne}")
    _ecrire(ops, apply, archive / "kb_entrees_citant_le_projet.md", "\n".join(corps) + "\n")

    if not kb_renvoi:
        return
    marqueur = f"<!-- renvoi-peremption reboot-hard {root.name} {today} -->"
    ligne_renvoi = (f"> ⚠ Renvoi de péremption (reboot hard {today}, motif "
                    f"registres-sans-referent) : le projet `{root.name}` a été rebooté ; cette "
                    f"entrée peut citer un état antérieur au reboot. {marqueur}")
    for chemin_rel in trouvailles:
        f = knowledge_dir / chemin_rel
        ops.append({"type": "kb_renvoi", "fichier": str(f), "marqueur": marqueur})
        if not apply:
            continue
        txt = f.read_text(encoding="utf-8")
        if marqueur in txt:
            continue
        lignes = txt.splitlines()
        idx = 0
        if lignes and lignes[0].startswith("#"):
            idx = 1
            while idx < len(lignes) and not lignes[idx].strip():
                idx += 1
        lignes[idx:idx] = [ligne_renvoi, ""]
        f.write_text("\n".join(lignes) + "\n", encoding="utf-8")


def _rapport_hard(root: Path, archive: Path, ops: list[dict], apply: bool, n_aff: int) -> None:
    mode = "APPLIQUÉ" if apply else "dry-run (--apply pour écrire)"
    print(f"{root.name} — reboot hard {mode}")
    print(f"  archive : {archive}")
    n_move = sum(1 for o in ops if o["type"] == "move")
    n_create = sum(1 for o in ops if o["type"] == "create")
    n_copy = sum(1 for o in ops if o["type"] == "copy")
    print(f"  {n_move} déplacement(s), {n_create} création(s), {n_copy} copie(s)")
    print(f"  {n_aff} affirmation(s) à rétablir")
    if not apply:
        for o in ops:
            if o["type"] == "move":
                print(f"    déplacerait  {o['src']} → {o['dst']}")
            elif o["type"] == "copy":
                print(f"    copierait    {o['src']} → {o['dst']}")
            elif o["type"] == "create":
                print(f"    créerait     {o['dst']}")


def cmd_hard(root: Path, apply: bool, garder_article: bool, commit_article: bool,
             kb_renvoi: bool, suffixe: str | None) -> int:
    if _init_mod is None:
        print("REFUS : module init_project.py introuvable (${CLAUDE_PLUGIN_ROOT}/skills/init-project/) "
              "— hard a besoin de ses gabarits.", file=sys.stderr)
        return 1
    if affirmations_mod is None:
        print("REFUS : module affirmations.py introuvable à côté de reboot.py.", file=sys.stderr)
        return 1
    if root.parent.name in REPERTOIRES_CLOTURE:
        print(f"REFUS : {root} est sous {root.parent.name}/ — ramener en en_cours/ "
              f"(deplacer_projet.py) avant tout reboot hard.", file=sys.stderr)
        return 1

    today = _dt.date.today().isoformat()
    nom_archive = f"{today}_reboot" + (f"-{suffixe}" if suffixe else "")
    archive = root / "archives" / nom_archive

    if archive.exists():
        message = (f"{archive} existe déjà — un reboot hard a déjà eu lieu ce jour "
                   f"(--suffixe pour un second reboot volontaire le même jour).")
        if apply:
            print(f"REFUS : {message}", file=sys.stderr)
            return 1
        print(f"[dry-run] {message} (--apply refuserait sans --suffixe)")

    mesures = collecter_mesures(root)
    manuscrits = _manuscrits(root)

    sales = [m["repertoire"] for m in manuscrits
             if (root / m["repertoire"] / ".git").is_dir() and _git_sale(root / m["repertoire"])]
    if sales and not commit_article:
        message = (f"{', '.join(sales)} porte des modifications non committées — relancer avec "
                   f"--commit-article pour geler l'état avant archivage, ou committer/stash "
                   f"manuellement.")
        if apply:
            print(f"REFUS : {message}", file=sys.stderr)
            return 1
        print(f"[dry-run] {message} (--apply refuserait sans --commit-article)")

    legacy_claude_txt = (root / "CLAUDE.md").read_text(encoding="utf-8", errors="replace") \
        if (root / "CLAUDE.md").is_file() else ""
    etat_txt_legacy = (root / "etat_des_decouvertes.md").read_text(encoding="utf-8", errors="replace") \
        if (root / "etat_des_decouvertes.md").is_file() else ""
    recadrage_txt = (root / "RECADRAGE.md").read_text(encoding="utf-8", errors="replace") \
        if (root / "RECADRAGE.md").is_file() else ""

    section_fn = cycle_status.section if cycle_status is not None else _section_repli
    section9 = section_fn(etat_txt_legacy, 9).strip() if etat_txt_legacy else ""

    aff = affirmations_mod.assembler_affirmations(root, section_fn)
    affirmations_mod.assigner_pistes(aff)  # AB8b : avant toute génération, cf. sa docstring
    # Nommer l'archive dans le frontmatter : sans cet argument, `affirmations.md` produit par un
    # `hard --apply` réel annonçait « non archivé (généré en prévisualisation AB2) », c'est-à-dire
    # que le seul artefact censé pointer vers l'archive ne la nommait pas (relevé le 2026-09-22).
    affirmations_contenu = affirmations_mod.generer_affirmations_md(
        root, aff, mesures, archive=str(archive.relative_to(root)))
    pistes_reboot_contenu = affirmations_mod.generer_pistes_reboot_md(root, aff)

    ops: list[dict] = []

    # --- cahier, état, pistes, CLAUDE.md legacy : verbatim ---
    for nom in ("cahier_de_labo.md", "cahier_de_labo_archive.md"):
        f = root / nom
        if f.is_file():
            _deplacer(ops, apply, f, archive / nom)
    for f in sorted(root.glob("cahier_de_labo.md.bak_*")):
        _deplacer(ops, apply, f, archive / f.name)

    if etat_txt_legacy:
        _deplacer(ops, apply, root / "etat_des_decouvertes.md", archive / "etat_legacy.md")

    for nom in ("pistes.md", "pistes_archive.md"):
        f = root / nom
        if f.is_file():
            _deplacer(ops, apply, f, archive / nom)
    for f in sorted(root.glob("pistes.md.bak_*")):
        _deplacer(ops, apply, f, archive / f.name)
    if (root / "pistes").is_dir():
        _deplacer(ops, apply, root / "pistes", archive / "pistes")

    if legacy_claude_txt:
        _deplacer(ops, apply, root / "CLAUDE.md", archive / "CLAUDE_legacy.md")

    # --- répertoires nommés ---
    for nom in DIRS_NOMMEES_ARCHIVE:
        d = root / nom
        if d.is_dir():
            _deplacer(ops, apply, d, archive / nom)

    # --- registres à la racine ---
    for nom in FICHIERS_REGISTRES_RACINE:
        f = root / nom
        if f.is_file():
            _deplacer(ops, apply, f, archive / "registres" / nom)
    if recadrage_txt:
        _deplacer(ops, apply, root / "RECADRAGE.md", archive / "RECADRAGE.md")

    # --- manuscrit(s) : commit, tag, registres, déplacement/copie ---
    tags: dict[str, str] = {}
    for m in manuscrits:
        rep = m["repertoire"]
        chemin = root / rep
        if not chemin.is_dir():
            continue
        est_git = (chemin / ".git").is_dir()
        if est_git and commit_article and _git_sale(chemin):
            ops.append({"type": "commit", "repo": str(chemin)})
            if apply:
                _git(chemin, "add", "-A")
                _git(chemin, "commit", "-q", "-m", f"reboot hard : gel avant archivage ({today})")
        if est_git:
            tag = (f"avant-reboot-{today}" + (f"-{suffixe}" if suffixe else "")
                   + (f"-{rep}" if rep != "article" else ""))
            deja = apply and bool(_git(chemin, "tag", "-l", tag).stdout.strip())
            ops.append({"type": "tag", "repo": str(chemin), "tag": tag})
            if apply and not deja:
                _git(chemin, "tag", tag)
            tags[rep] = tag
        for nom in ("claim_check.md", "fig_check.md", "tab_check.md",
                   "plan_narratif.md", "verdict_diffusion.md", "cadrage_editorial.md"):
            f = chemin / nom
            if f.is_file():
                _deplacer(ops, apply, f, archive / "registres" / rep / nom)
        for base in ("claim_check", "fig_check", "tab_check"):
            f = root / f"{base}_{rep}.md"
            if f.is_file():
                _deplacer(ops, apply, f, archive / "registres" / f"{base}_{rep}.md")

        if garder_article:
            _copier(ops, apply, chemin, archive / f"{rep}_copie")
            if apply:
                bandeau = (f"%% MANUSCRIT LEGACY — reboot hard du {today} — rédaction gelée, "
                          f"voir archives/{nom_archive}/\n")
                for nom_tex in ("main.tex", "main_fr.tex"):
                    ftex = chemin / nom_tex
                    if ftex.is_file():
                        contenu = ftex.read_text(encoding="utf-8", errors="replace")
                        if not contenu.startswith("%% MANUSCRIT LEGACY"):
                            ftex.write_text(bandeau + contenu, encoding="utf-8")
        else:
            _deplacer(ops, apply, chemin, archive / rep)

    m_titre = re.search(r"^#\s*CLAUDE\.md\s*—\s*(.+)$", legacy_claude_txt, re.MULTILINE)
    title = m_titre.group(1).strip() if m_titre else root.name
    famille = None
    try:
        famille = _init_mod.deviner_famille(root.parent)
    except Exception:
        famille = None
    m_voies = re.search(r"\*\*Voie\s*:\*\*\s*([a-zA-ZÀ-ÿ+ ]+)", legacy_claude_txt)
    voies = tuple(v.strip() for v in m_voies.group(1).split("+")) if m_voies else ("article",)
    domain = "mtbc" if famille == "mtbc" else "generic"

    if not garder_article and any(m["repertoire"] == "article" for m in manuscrits):
        _scaffold_article(root, ops, apply, title, domain)

    # --- vrac : reste de la racine hors liste blanche et hors éléments déjà traités ---
    traites = {"cahier_de_labo.md", "cahier_de_labo_archive.md", "etat_des_decouvertes.md",
              "pistes.md", "pistes_archive.md", "pistes", "CLAUDE.md", "RECADRAGE.md",
              *DIRS_NOMMEES_ARCHIVE, *FICHIERS_REGISTRES_RACINE,
              *(m["repertoire"] for m in manuscrits)}
    for entree in sorted(root.iterdir()):
        nom = entree.name
        if nom in LISTE_BLANCHE_RACINE or nom in traites:
            continue
        if nom.startswith(".") or nom.startswith("cahier_de_labo.md.bak_") or nom.startswith("pistes.md.bak_"):
            continue
        _deplacer(ops, apply, entree, archive / "racine_legacy" / nom)

    # --- nouveaux artefacts ---
    contenu_claude = _init_mod.claude_md_template(root.name, title, domain, voies, famille)
    contenu_claude = contenu_claude.replace(
        "[Décrire ici la question de recherche, l'échantillon ou les données, ce qui est "
        "attendu, et ce qui distingue ce projet de ses voisins.]",
        (f"À reprendre depuis `archives/{nom_archive}/CLAUDE_legacy.md` : identité de l'objet, "
         f"collaborateurs, pièges méthodologiques propres à ce projet. Tout chiffre repris de "
         f"l'archive est legacy, à re-vérifier (`affirmations.md`) avant citation."),
    )
    contenu_claude += _bloc_reboot(mesures, tags, nom_archive, garder_article, len(aff),
                                   recadrage_txt, today)
    _ecrire(ops, apply, root / "CLAUDE.md", contenu_claude)

    contenu_cahier = _init_mod.cahier_de_labo_template(root.name, title, root)
    contenu_cahier += (f"## {today} — Reboot hard : archivage\n\n"
                       f"Reboot hard exécuté ; historique antérieur déplacé verbatim dans "
                       f"`archives/{nom_archive}/`. {len(aff)} affirmation(s) à rétablir "
                       f"(`affirmations.md`, piste P1).\n\n")
    _ecrire(ops, apply, root / "cahier_de_labo.md", contenu_cahier)

    contenu_etat = _init_mod.etat_des_decouvertes_template(
        root.name, n_entrees=mesures.get("cahier_entrees") or 1, voies=voies)
    if section9:
        contenu_etat = contenu_etat.replace(
            "## 9. Hors périmètre — essaimé / classé\n- néant à ce jour",
            "## 9. Hors périmètre — essaimé / classé\n" + section9,
        )
    if recadrage_txt:
        contenu_etat = contenu_etat.replace(
            "## 1. Question de recherche et objectifs (évolutifs)",
            (f"## 1. Question de recherche et objectifs (évolutifs)\n\n"
             f"Cadrage issu de `/recadrage` avant ce reboot "
             f"(voir `archives/{nom_archive}/RECADRAGE.md`) :\n\n> "
             + recadrage_txt.strip().replace("\n", "\n> ") + "\n"),
        )
    _ecrire(ops, apply, root / "etat_des_decouvertes.md", contenu_etat)
    _ecrire(ops, apply, root / "pistes.md", pistes_reboot_contenu)
    _ecrire(ops, apply, root / "affirmations.md", affirmations_contenu)

    _archiver_memoire_native(root, archive, ops, apply)
    _inventaire_kb(root, archive, ops, apply, kb_renvoi, today)

    if apply:
        if PROFIL_PLUGINS_PY.is_file():
            _appeler_best_effort([sys.executable, str(PROFIL_PLUGINS_PY), "--apply", str(root), "--write"],
                                 "profil_plugins.py --apply --write")
            ops.append({"type": "profil_plugins"})
        if CARREFOUR_PY.is_file():
            _appeler_best_effort([sys.executable, str(CARREFOUR_PY), "reindex", "--root", str(root)],
                                 "carrefour.py reindex")
            ops.append({"type": "carrefour_reindex"})

    manifest = {
        "reboot": "hard", "date": today, "suffixe": suffixe, "projet": root.name,
        "racine": str(root), "garder_article": garder_article, "commit_article": commit_article,
        "kb_renvoi": kb_renvoi, "affirmations": len(aff), "operations": ops,
    }
    if apply:
        archive.mkdir(parents=True, exist_ok=True)
        (archive / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                                encoding="utf-8")

    _rapport_hard(root, archive, ops, apply, len(aff))
    return 0


# --------------------------------------------------------------------------
# Sous-commande `annuler` (ÉCRIT — AB3)
# --------------------------------------------------------------------------

def cmd_annuler(root: Path, date_arg: str, suffixe: str | None, apply: bool) -> int:
    nom_archive = f"{date_arg}_reboot" + (f"-{suffixe}" if suffixe else "")
    archive = root / "archives" / nom_archive
    manifest_path = archive / "MANIFEST.json"
    if not manifest_path.is_file():
        print(f"REFUS : {manifest_path} introuvable — rien à annuler pour {nom_archive} "
              f"(déjà annulé, ou jamais appliqué).", file=sys.stderr)
        return 1
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"REFUS : MANIFEST.json illisible : {exc}", file=sys.stderr)
        return 1

    ops = manifest.get("operations", [])
    non_reversibles: set[str] = set()
    n_create = n_move = 0
    for op in reversed(ops):
        typ = op["type"]
        if typ == "create":
            n_create += 1
            dst = Path(op["dst"])
            if apply and dst.exists():
                ok, msg = _gio_trash(dst)
                if not ok:
                    print(f"  ⚠ {dst} non retiré : {msg}", file=sys.stderr)
        elif typ == "move":
            n_move += 1
            src, dst = Path(op["src"]), Path(op["dst"])
            if apply and dst.exists():
                if src.exists():
                    # `src` ne peut être occupé que par un reliquat plus tardif du même
                    # `hard` (create/mkdir/git_init_article) : le manifeste garantit que
                    # `hard` a vidé `src` avant d'y écrire quoi que ce soit de neuf. Sûr à
                    # retirer avant de restaurer l'archivé — mesuré le 2026-09-21 : sans ce
                    # nettoyage, `figures/`, `supplementary_materials/` et `.git/` (jamais
                    # suivis comme « create ») laissaient `article/` non vide et bloquaient
                    # indéfiniment la restauration de l'archive.
                    ok, msg = _gio_trash(src)
                    if not ok:
                        print(f"  ⚠ {src} occupé par un reliquat non retirable ({msg}) — "
                              f"restauration sautée, fusionner manuellement depuis {dst}.",
                              file=sys.stderr)
                if not src.exists():
                    src.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(dst), str(src))
        elif typ == "kb_renvoi":
            if apply:
                f, marqueur = Path(op["fichier"]), op["marqueur"]
                if f.is_file():
                    txt = f.read_text(encoding="utf-8")
                    if marqueur in txt:
                        lignes = [l for l in txt.splitlines() if marqueur not in l]
                        f.write_text("\n".join(lignes) + "\n", encoding="utf-8")
        else:
            non_reversibles.add(typ)

    if apply:
        ok, msg = _gio_trash(archive)
        if not ok:
            print(f"  ⚠ archive {archive} non retirée : {msg}", file=sys.stderr)

    mode = "APPLIQUÉ" if apply else "dry-run (--apply pour écrire)"
    print(f"{root.name} — annulation {nom_archive} {mode}")
    print(f"  {n_move} déplacement(s) restauré(s), {n_create} création(s) retirée(s)")
    if non_reversibles:
        print(f"  non ré-appliqués automatiquement : {', '.join(sorted(non_reversibles))} "
              f"(tags git laissés en place ; mémoire native et copies --garder-article à "
              f"recopier manuellement depuis l'archive avant sa suppression).")
    return 0


# --------------------------------------------------------------------------
# Sous-commande `soft` (ÉCRIT — AB4)
# --------------------------------------------------------------------------

RE_PISTE_MAJEURE_TETE = re.compile(r"^##\s+([A-Za-z]{1,3})(\d{0,3})\.\s", re.MULTILINE)

SOUS_PISTES_SOFT = (
    ("Impact sur l'article : relire `main.tex` (et `main_fr.tex`) contre les règles "
     "nouvelles de l'environnement", "Opus:high"),
    ("Données à re-citer : `bdd check` puis `bdd stamp`, recomptes", "Sonnet:high"),
    ("Scripts à re-valider : réexécution témoin de chaque script cité dans l'état", "Sonnet:xhigh"),
    ("Registres à estampiller : renvoi de péremption en tête de `claim_check.md`, "
     "`fig_check.md`, `verdict_diffusion.md`, `plan_narratif.md`", "Sonnet:high"),
    ("En-tête de l'état (`**Environnement :**`), `/etat update`, clôture de la piste", "Sonnet:high"),
)


def _lettre_suivante(lettre: str) -> str:
    """Incrément façon colonnes de tableur : Z -> AA -> AB ..."""
    lettres = list(lettre.upper())
    i = len(lettres) - 1
    while i >= 0:
        if lettres[i] != "Z":
            lettres[i] = chr(ord(lettres[i]) + 1)
            return "".join(lettres)
        lettres[i] = "A"
        i -= 1
    return "A" + "".join(lettres)


def _prochain_id_piste(pistes_txt: str) -> str:
    """Prochain identifiant de piste MAJEURE. Convention très majoritaire des projets
    scaffoldés par `init-project` : `P<n>` numéroté. Repli sur l'incrément de lettre
    pure (`Z` -> `AA`) pour un projet qui, comme `environnement` lui-même, numérote
    ses pistes majeures par lettres sans chiffre."""
    matches = RE_PISTE_MAJEURE_TETE.findall(pistes_txt)
    if not matches:
        return "P1"
    numerotes = [(l, int(c)) for l, c in matches if c]
    if numerotes:
        compte: dict[str, int] = {}
        for l, _ in numerotes:
            compte[l] = compte.get(l, 0) + 1
        lettre_dominante = max(compte, key=lambda l: compte[l])
        max_n = max(n for l, n in numerotes if l == lettre_dominante)
        return f"{lettre_dominante}{max_n + 1}"
    non_numerotes = sorted({l for l, _ in matches}, key=lambda l: (len(l), l))
    return _lettre_suivante(non_numerotes[-1])


def _delta_soft(mesures: dict) -> dict:
    """vA_fmt/vB_fmt (déjà formatés : `v1.2.3`, ou libellé de repli) du couple de
    migration. Repli explicite si `env_version.py` est indisponible ou si le projet
    n'a jamais été rattaché (§ AB.6 : « delta estimé par la date »)."""
    env_projet, env_courant = mesures.get("env_projet"), mesures.get("env_courant")
    vA_fmt = f"v{env_projet}" if env_projet else "non estampillé"
    if mesures.get("env_disponible") and env_courant:
        vB_fmt = f"v{env_courant}"
        return {"vA_fmt": vA_fmt, "vB_fmt": vB_fmt, "repli": False, "texte": f"{vA_fmt} → {vB_fmt}"}
    age = mesures.get("age")
    motif = mesures.get("env_motif") or "env_version.py indisponible"
    texte = (f"delta non calculable automatiquement ({motif}) — dernière entrée de cahier "
             f"il y a {age} j : consulter `~/docs/environnement/cahier_de_labo.md` autour de "
             f"cette période pour ce qui a changé côté outillage" if age is not None else
             f"delta non calculable automatiquement ({motif}, aucune entrée de cahier datée)")
    return {"vA_fmt": vA_fmt, "vB_fmt": "v?", "repli": True, "texte": texte}


def _piste_migration_existe(pistes_txt: str, delta: dict) -> bool:
    motif = re.escape(delta["vA_fmt"]) + r".{0,20}" + re.escape(delta["vB_fmt"])
    return bool(re.search(r"Migration d'environnement.{0,10}" + motif, pistes_txt))


def _bloc_piste_soft(piste_id: str, delta: dict, today: str) -> str:
    lignes = [f"## {piste_id}. Migration d'environnement {delta['vA_fmt']}→{delta['vB_fmt']} "
              f"(reboot soft {today}) [en cours]",
              f"  origine : reboot soft {today}    maj : {today}"]
    if delta["repli"]:
        lignes.append(f"  {delta['texte']}")
    for k, (libelle, tag) in enumerate(SOUS_PISTES_SOFT, start=1):
        lignes.append(f"  - {piste_id}.{k}  {libelle} [à faire] [{tag}]")
    return "\n".join(lignes) + "\n"


def _bloc_claude_soft(piste_id: str, delta: dict, today: str) -> str:
    return dedent(f"""
        ## Migration d'environnement (soft, {today})

        - **Delta :** {delta['texte']}
        - **Piste :** {piste_id} — voir `pistes.md`
        - **Statut :** en cours ; cinq sous-pistes (article, données, scripts, registres, état).
        """)


def _ligne_environnement_soft(etat_txt: str, piste_id: str, delta: dict, today: str) -> tuple[str, bool]:
    """Retourne (nouveau_texte, changé). AB.4 : sous `soft`, l'état reste intact hormis
    cette ligne, réécrite en place (ou insérée si le projet n'était jamais rattaché)."""
    if delta["repli"]:
        nouvelle = f"**Environnement :** {delta['texte']} (piste {piste_id})"
    else:
        nouvelle = (f"**Environnement :** {delta['vB_fmt']} (migration soft depuis "
                    f"{delta['vA_fmt']}, {today}, piste {piste_id})")
    if RE_ENV_PROJET.search(etat_txt):
        nouveau_txt = re.sub(r"^\*\*Environnement\s*:\*\*.*$", nouvelle, etat_txt,
                             count=1, flags=re.MULTILINE)
        return nouveau_txt, True
    if not etat_txt:
        return etat_txt, False
    m_reecrit = RE_REECRIT.search(etat_txt)
    if m_reecrit:
        fin_ligne = etat_txt.index("\n", m_reecrit.start())
        return etat_txt[:fin_ligne + 1] + nouvelle + "\n" + etat_txt[fin_ligne + 1:], True
    m_titre = re.search(r"^#\s.*$", etat_txt, re.MULTILINE)
    if m_titre:
        fin_ligne = etat_txt.index("\n", m_titre.start())
        return etat_txt[:fin_ligne + 1] + "\n" + nouvelle + "\n" + etat_txt[fin_ligne + 1:], True
    return nouvelle + "\n\n" + etat_txt, True


def cmd_soft(root: Path, apply: bool) -> int:
    pistes_path = root / "pistes.md"
    if not pistes_path.is_file():
        print(f"REFUS : {pistes_path} introuvable — projet hors format init-project, "
              f"`soft` a besoin d'un pistes.md existant.", file=sys.stderr)
        return 1

    mesures = collecter_mesures(root)
    delta = _delta_soft(mesures)
    if not delta["repli"] and delta["vA_fmt"] == delta["vB_fmt"]:
        print(f"REFUS : {delta['vA_fmt']} = {delta['vB_fmt']} — projet déjà à jour, rien à migrer "
              f"(l'état a peut-être déjà été mis à jour par un `soft` précédent).", file=sys.stderr)
        return 1
    pistes_txt = pistes_path.read_text(encoding="utf-8", errors="replace")
    if _piste_migration_existe(pistes_txt, delta):
        print(f"REFUS : une piste « Migration d'environnement » pour le couple "
              f"{delta['vA_fmt']}→{delta['vB_fmt']} existe déjà dans {pistes_path}.", file=sys.stderr)
        return 1

    today = _dt.date.today().isoformat()
    piste_id = _prochain_id_piste(pistes_txt)
    bloc_piste = _bloc_piste_soft(piste_id, delta, today)
    nouveau_pistes_txt = pistes_txt.rstrip("\n") + "\n\n" + bloc_piste

    etat_path = root / "etat_des_decouvertes.md"
    etat_txt = etat_path.read_text(encoding="utf-8", errors="replace") if etat_path.is_file() else ""
    nouveau_etat_txt, etat_change = _ligne_environnement_soft(etat_txt, piste_id, delta, today)

    claude_path = root / "CLAUDE.md"
    claude_txt = claude_path.read_text(encoding="utf-8", errors="replace") if claude_path.is_file() else ""
    bloc_claude = _bloc_claude_soft(piste_id, delta, today)
    nouveau_claude_txt = claude_txt.rstrip("\n") + "\n" + bloc_claude if claude_txt else bloc_claude

    mode = "APPLIQUÉ" if apply else "dry-run (--apply pour écrire)"
    print(f"{root.name} — reboot soft {mode}")
    print(f"  delta : {delta['texte']}")
    print(f"  piste créée : {piste_id} (Migration d'environnement) — {pistes_path}")
    if etat_change:
        print(f"  ligne **Environnement :** posée dans {etat_path}")
    else:
        print(f"  {etat_path} absent ou vide — ligne **Environnement :** non posée")
    if claude_path.is_file():
        print(f"  bloc « Migration d'environnement » ajouté à {claude_path}")
    else:
        print(f"  {claude_path} absent — bloc non écrit")

    if not apply:
        return 0

    pistes_path.write_text(nouveau_pistes_txt, encoding="utf-8")
    if etat_change:
        etat_path.write_text(nouveau_etat_txt, encoding="utf-8")
    if claude_path.is_file():
        claude_path.write_text(nouveau_claude_txt, encoding="utf-8")
    print(f"écrit : {pistes_path}" + (f", {etat_path}" if etat_change else "")
          + (f", {claude_path}" if claude_path.is_file() else ""))
    return 0


# --------------------------------------------------------------------------
# Sous-commande `recycler` (ÉCRIT — AB4)
# --------------------------------------------------------------------------

PREFIXES_CHEMIN_SUSPECT = ("/home/", "/Users/", "/mnt/", "/data/", "/tmp/", "/srv/")
RE_CHEMIN_ABSOLU = re.compile(
    r"(?<![\w/])(" + "|".join(re.escape(p) for p in PREFIXES_CHEMIN_SUSPECT)
    + r")[^\s'\"(),;]*"
)
RE_DATE_ISO = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
# Signatures de stores de données propres à VOTRE projet, dont la présence dans un
# fichier archivé signale un contrôle mécanique (pas une lecture humaine) : liste vide
# par défaut, à peupler via `CYCLE_MOTIFS_MECANIQUES` (motifs séparés par des virgules,
# ex. "mon-corpus/actuelle,mes-barcodes,mes-lignees.py") pour ne pas imposer les
# conventions de nommage d'un projet particulier à un autre.
_MOTIFS_ENV = os.environ.get("CYCLE_MOTIFS_MECANIQUES", "")
MOTIFS_MECANIQUES = {m.strip(): m.strip() for m in _MOTIFS_ENV.split(",") if m.strip()}
RE_MCP = re.compile(r"\bmcp__[A-Za-z0-9_]+\b")
RE_FIGURE = re.compile(r"savefig\(|ggsave\(|plt\.show\(")

RECYCLAGE_COLONNES_NOMS = ("chemin legacy", "type", "demandé le", "lecture intégrale (déclarée)",
                           "bugs KB", "chemins en dur", "données citées vs courantes",
                           "réexécution témoin (déclarée)", "verdict", "destination", "affirmation")
RECYCLAGE_COLONNES = len(RECYCLAGE_COLONNES_NOMS)
RECYCLAGE_ENTETE = "| " + " | ".join(RECYCLAGE_COLONNES_NOMS) + " |"
RECYCLAGE_SEPARATEUR = "|" + "|".join(["---"] * RECYCLAGE_COLONNES) + "|"
VERDICTS_RECYCLAGE = ("recyclé", "réécrit", "rejeté")


def _archive_reboot_de(root: Path, chemin: Path) -> Path | None:
    """Archive `archives/<date>_reboot[-suffixe]/` de `root` qui contient `chemin`, ou
    None si `chemin` n'est sous aucune archive de reboot de ce projet."""
    root_resolu = root.resolve()
    for p in chemin.resolve().parents:
        if (p.parent == root_resolu / "archives"
                and re.match(r"^\d{4}-\d{2}-\d{2}_reboot(-.+)?$", p.name)):
            return p
    return None


def _type_recyclage(chemin: Path) -> str:
    suf = chemin.suffix.lower()
    if chemin.is_dir():
        return "répertoire"
    if suf in (".py", ".r", ".sh", ".pl"):
        return "script"
    if suf in (".md", ".tex", ".txt", ".rst"):
        return "doc"
    if suf in (".csv", ".tsv", ".json", ".xlsx", ".parquet", ".tab"):
        return "données"
    if suf in (".png", ".pdf", ".svg", ".jpg", ".jpeg"):
        return "figure"
    return "autre"


def _controles_mecaniques(chemin: Path, archive: Path) -> dict:
    resultat: dict = {"chemins_en_dur": [], "motifs": [], "mcp": [], "figure": False, "date_entete": None}
    if chemin.is_dir():
        return resultat
    try:
        texte = chemin.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return resultat
    lignes_non_shebang = [l for l in texte.splitlines() if not l.startswith("#!")]
    corps = "\n".join(lignes_non_shebang)
    resultat["chemins_en_dur"] = sorted({m.group(0) for m in RE_CHEMIN_ABSOLU.finditer(corps)})
    resultat["motifs"] = [nom for nom, motif in MOTIFS_MECANIQUES.items() if motif in texte]
    resultat["mcp"] = sorted(set(RE_MCP.findall(texte)))
    resultat["figure"] = bool(RE_FIGURE.search(texte))
    m_date = RE_DATE_ISO.search("\n".join(texte.splitlines()[:40]))
    resultat["date_entete"] = m_date.group(1) if m_date else None
    m_date_archive = re.match(r"^(\d{4}-\d{2}-\d{2})_reboot", archive.name)
    resultat["date_archive"] = m_date_archive.group(1) if m_date_archive else None
    return resultat


def _ligne_recyclage(cols: list[str]) -> str:
    return "| " + " | ".join(c.replace("|", "/") or "—" for c in cols) + " |"


def _lire_table_recyclage(txt: str) -> tuple[list[str], list[list[str]]]:
    lignes = [l for l in txt.splitlines() if l.strip().startswith("|")]
    if len(lignes) < 2:
        return [], []
    rangs = []
    for l in lignes[2:]:
        cols = [c.strip() for c in l.strip().strip("|").split("|")]
        if len(cols) == RECYCLAGE_COLONNES:
            rangs.append(cols)
    return lignes[:2], rangs


def cmd_recycler(root: Path, chemin_arg: str, vers: str | None, verdict: str | None,
                  lien: bool, apply: bool) -> int:
    chemin = Path(chemin_arg)
    chemin = chemin if chemin.is_absolute() else (root / chemin_arg)
    if not chemin.exists():
        print(f"REFUS : {chemin} introuvable.", file=sys.stderr)
        return 1
    archive = _archive_reboot_de(root, chemin)
    if archive is None:
        print(f"REFUS : {chemin} n'est pas sous une archive archives/<date>_reboot/ de {root}.",
              file=sys.stderr)
        return 1
    if verdict is not None and verdict not in VERDICTS_RECYCLAGE:
        print(f"REFUS : verdict '{verdict}' hors nomenclature {VERDICTS_RECYCLAGE}.", file=sys.stderr)
        return 1
    if verdict in ("recyclé", "réécrit") and not vers:
        print("REFUS : --vers requis avec --verdict recyclé|réécrit.", file=sys.stderr)
        return 1

    chemin_relatif = str(chemin.resolve().relative_to(archive.resolve()))
    controles = _controles_mecaniques(chemin, archive)
    type_ = _type_recyclage(chemin)
    today = _dt.date.today().isoformat()

    print(f"{chemin_relatif} — type {type_}")
    if controles["chemins_en_dur"]:
        print(f"  chemins en dur : {', '.join(controles['chemins_en_dur'])}")
    if controles["motifs"]:
        print(f"  motifs mécaniques : {', '.join(controles['motifs'])}")
    if controles["mcp"]:
        print(f"  outils MCP cités (à vérifier vivants) : {', '.join(controles['mcp'])}")
    if controles["figure"]:
        print("  script producteur de figure détecté (savefig/ggsave)")
    if controles["date_entete"] and controles.get("date_archive") and \
            controles["date_entete"] != controles["date_archive"]:
        print(f"  date d'en-tête {controles['date_entete']} != date de l'archive "
              f"{controles['date_archive']}")

    recyclage_path = archive / "RECYCLAGE.md"
    txt = recyclage_path.read_text(encoding="utf-8") if recyclage_path.is_file() else \
        f"# Recyclage — {archive.name}\n\n{RECYCLAGE_ENTETE}\n{RECYCLAGE_SEPARATEUR}\n"
    entete_lignes, rangs = _lire_table_recyclage(txt)

    bugs_kb = ", ".join(controles["mcp"]) or "—"
    chemins_en_dur_txt = ", ".join(controles["chemins_en_dur"]) or "aucun"
    idx_existant = next((i for i, r in enumerate(rangs) if r[0] == chemin_relatif), None)
    # AB8c : « déclarée », jamais « faite » — ces deux colonnes ne reflètent que la présence
    # d'un --verdict, aucun contrôle réel du script ni de la lecture (cf. references/recyclage.md).
    lecture_integrale = "déclarée (verdict posé)" if verdict else "non déclarée"
    reexecution = "déclarée (verdict posé)" if verdict else "non déclarée"
    verdict_txt = verdict or (rangs[idx_existant][8] if idx_existant is not None else "—")
    destination_txt = vers or (rangs[idx_existant][9] if idx_existant is not None else "—")
    affirmation_txt = rangs[idx_existant][10] if idx_existant is not None else "—"
    demande_le = rangs[idx_existant][2] if idx_existant is not None else today

    nouveau_rang = [chemin_relatif, type_, demande_le, lecture_integrale, bugs_kb,
                    chemins_en_dur_txt, "non vérifié automatiquement", reexecution,
                    verdict_txt, destination_txt, affirmation_txt]
    if idx_existant is not None:
        rangs[idx_existant] = nouveau_rang
    else:
        rangs.append(nouveau_rang)

    prefixe = txt.split("\n" + entete_lignes[0], 1)[0] if entete_lignes else f"# Recyclage — {archive.name}\n"
    corps = [prefixe.rstrip("\n"), "", RECYCLAGE_ENTETE, RECYCLAGE_SEPARATEUR]
    corps += [_ligne_recyclage(r) for r in rangs]
    nouveau_txt = "\n".join(corps) + "\n"

    faire_lien = False
    dest_finale = None
    if verdict in ("recyclé", "réécrit") and vers:
        dest_finale = Path(vers) if Path(vers).is_absolute() else root / vers
        taille = chemin.stat().st_size if chemin.is_file() else 0
        faire_lien = lien or taille > 100 * 1024 * 1024

    mode = "APPLIQUÉ" if apply else "dry-run (--apply pour écrire)"
    print(f"  RECYCLAGE.md ({archive.name}) : ligne {'mise à jour' if idx_existant is not None else 'créée'} — {mode}")
    if dest_finale is not None:
        action = "lien symbolique" if faire_lien else "copie"
        print(f"  {action} prévue : {chemin} -> {dest_finale} (archive intacte)")

    if not apply:
        return 0

    recyclage_path.write_text(nouveau_txt, encoding="utf-8")
    if dest_finale is not None:
        dest_finale.parent.mkdir(parents=True, exist_ok=True)
        if faire_lien:
            if dest_finale.exists() or dest_finale.is_symlink():
                _gio_trash(dest_finale)
            dest_finale.symlink_to(chemin.resolve())
        elif chemin.is_dir():
            shutil.copytree(chemin, dest_finale, dirs_exist_ok=True)
        else:
            shutil.copy2(chemin, dest_finale)
    print(f"écrit : {recyclage_path}" + (f", {dest_finale}" if dest_finale is not None else ""))
    return 0


# --------------------------------------------------------------------------
# Sous-commande `lire-archive` (LECTURE SEULE — AB4)
# --------------------------------------------------------------------------

def cmd_lire_archive(root: Path, fichier: str | None, grep: str | None, as_json: bool) -> int:
    archives = sorted(root.glob("archives/*_reboot"))
    if not archives:
        print(f"REFUS : aucune archive de reboot sous {root / 'archives'}/.", file=sys.stderr)
        return 1
    archive = archives[-1]

    if grep is not None:
        try:
            motif = re.compile(grep)
        except re.error as exc:
            print(f"REFUS : motif invalide : {exc}", file=sys.stderr)
            return 1
        base = (archive / fichier) if fichier else archive
        if not base.exists():
            print(f"REFUS : {base} introuvable.", file=sys.stderr)
            return 1
        cibles = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file())
        trouvailles = []
        for f in cibles:
            try:
                texte = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for i, ligne in enumerate(texte.splitlines(), start=1):
                if motif.search(ligne):
                    trouvailles.append({"fichier": str(f.relative_to(archive)), "ligne": i, "texte": ligne})
        if as_json:
            print(json.dumps({"archive": archive.name, "resultats": trouvailles}, ensure_ascii=False, indent=2))
        else:
            for t in trouvailles:
                print(f"{t['fichier']}:{t['ligne']}: {t['texte']}")
            if not trouvailles:
                print(f"aucune occurrence de {grep!r} sous {archive.name}")
        return 0

    if fichier is None:
        contenu = sorted(str(p.relative_to(archive)) for p in archive.rglob("*") if p.is_file())
        if as_json:
            print(json.dumps({"archive": archive.name, "fichiers": contenu}, ensure_ascii=False, indent=2))
        else:
            print(f"{archive.name} :")
            for c in contenu:
                print(f"  {c}")
        return 0

    cible = archive / fichier
    if not cible.is_file():
        print(f"REFUS : {cible} introuvable sous {archive.name}.", file=sys.stderr)
        return 1
    try:
        texte = cible.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"REFUS : lecture impossible : {exc}", file=sys.stderr)
        return 1
    tronque = len(texte) > 20000
    if as_json:
        print(json.dumps({"archive": archive.name, "fichier": fichier,
                          "contenu": texte[:20000], "tronque": tronque}, ensure_ascii=False, indent=2))
    else:
        print(texte[:20000])
        if tronque:
            print(f"\n[... tronqué à 20000 caractères — {cible} fait {len(texte)} caractères]")
    return 0


# --------------------------------------------------------------------------
# Sous-commande `clore` (ÉCRIT — AB4)
# --------------------------------------------------------------------------

RE_COMPTEURS_FRONTMATTER = re.compile(
    r"compteurs:\s*\n\s*non_testee:\s*(\d+)\s*\n\s*en_test:\s*(\d+)\s*\n"
    r"\s*prouvee:\s*(\d+)\s*\n\s*refutee:\s*(\d+)\s*\n\s*abandonnee:\s*(\d+)"
)


def cmd_clore(root: Path, apply: bool) -> int:
    fichier = root / "affirmations.md"
    if not fichier.is_file():
        print(f"REFUS : {fichier} introuvable — rien à clore (pas de reboot hard en cours, "
              f"ou déjà clos).", file=sys.stderr)
        return 1
    txt = fichier.read_text(encoding="utf-8")
    m = RE_COMPTEURS_FRONTMATTER.search(txt)
    if not m:
        print(f"REFUS : frontmatter de {fichier} illisible (compteurs introuvables).", file=sys.stderr)
        return 1
    non_testee, en_test, prouvee, refutee, abandonnee = (int(x) for x in m.groups())
    if non_testee or en_test:
        print(f"REFUS : {non_testee + en_test} affirmation(s) non tranchée(s) "
              f"({non_testee} non testée(s), {en_test} en test) — clore refusé tant qu'il en reste.",
              file=sys.stderr)
        return 1

    archives = sorted(root.glob("archives/*_reboot"))
    if not archives:
        print("REFUS : aucune archive de reboot — clore ne s'applique qu'après un `hard`.",
              file=sys.stderr)
        return 1
    archive = archives[-1]
    dst = archive / "affirmations.md"
    if dst.exists():
        print(f"REFUS : {dst} existe déjà — reboot déjà clos.", file=sys.stderr)
        return 1

    today = _dt.date.today().isoformat()
    claude_path = root / "CLAUDE.md"
    claude_txt = claude_path.read_text(encoding="utf-8", errors="replace") if claude_path.is_file() else ""
    nouveau_bloc = (f"## Reboot\n\n"
                     f"- **Clos le {today} :** reboot `{archive.name}` clos, `affirmations.md` gelé "
                     f"dans `archives/{archive.name}/` ({prouvee} prouvée(s), {refutee} réfutée(s), "
                     f"{abandonnee} abandonnée(s)).\n"
                     f"- **Porte 1 rouverte par la clôture** (`/reboot`, étape 4) : ni la clôture ni P1 "
                     f"soldé ne franchissent la porte 1 ni ne dégèlent le manuscrit ; tout verdict "
                     f"1bis/3bis antérieur est périmé.\n"
                     f"  - recadrage post-clôture (`/recadrage` sur l'état post-reboot) : à faire\n"
                     f"  - revue de littérature ciblée post-clôture (`/lit-review`) : à faire\n")
    if "## Reboot" in claude_txt:
        nouveau_claude_txt = re.sub(r"## Reboot\n.*\Z", nouveau_bloc, claude_txt, flags=re.DOTALL)
    else:
        nouveau_claude_txt = claude_txt.rstrip("\n") + "\n\n" + nouveau_bloc if claude_txt else nouveau_bloc

    mode = "APPLIQUÉ" if apply else "dry-run (--apply pour écrire)"
    print(f"{root.name} — clore {mode}")
    print(f"  {fichier} -> {dst} (gelé)")
    print(f"  bloc Reboot de {claude_path} allégé à la clôture et à la trace de la porte 1 rouverte")
    if not apply:
        return 0

    shutil.move(str(fichier), str(dst))
    if claude_path.is_file():
        claude_path.write_text(nouveau_claude_txt, encoding="utf-8")
    print(f"écrit : {dst}" + (f", {claude_path}" if claude_path.is_file() else ""))
    print("SUITE OBLIGATOIRE : la clôture rouvre la porte 1, elle ne la franchit pas. "
          "`/recadrage` sur l'état post-reboot, puis `/lit-review` ciblée, puis porte 1 "
          "re-prouvée et 1bis re-rendue avant tout dégel du manuscrit (`/reboot`, étape 4).")
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = p.add_subparsers(dest="commande", required=True)

    p_diag = sub.add_parser("diagnostic")
    p_diag.add_argument("projet", nargs="?", default=None)
    p_diag.add_argument("--json", action="store_true")

    p_status = sub.add_parser("status")
    p_status.add_argument("projet", nargs="?", default=None)
    p_status.add_argument("--legacy", action="store_true")
    p_status.add_argument("--json", action="store_true")

    p_signals = sub.add_parser("signals")
    p_signals.add_argument("projet", nargs="?", default=None)
    p_signals.add_argument("--quiet", action="store_true")

    p_aff = sub.add_parser("affirmations")
    p_aff.add_argument("projet", nargs="?", default=None)
    p_aff.add_argument("--ecrire", default=None, help="chemin où écrire affirmations.md (sinon prévisualisation seule)")
    p_aff.add_argument("--pistes-ecrire", default=None, help="chemin où écrire le nouveau pistes.md de reboot")
    p_aff.add_argument("--json", action="store_true")
    p_aff.add_argument("--migrate", action="store_true",
                       help="état legacy squelette : dépouillement mécanique du cahier (AB8a, candidats bruts P2)")
    p_aff.add_argument("--carrefour-match", action="store_true",
                       help="annote chaque affirmation à rétablir du meilleur voisin vivant (AB8a)")

    p_aff1 = sub.add_parser("affirmation")
    p_aff1.add_argument("id")
    p_aff1.add_argument("projet", nargs="?", default=None)
    p_aff1.add_argument("--statut", choices=STATUTS_AFFIRMATION, default=None)
    p_aff1.add_argument("--preuve", default=None)
    p_aff1.add_argument("--notes", default=None)
    p_aff1.add_argument("--apply", action="store_true")

    p_hard = sub.add_parser("hard")
    p_hard.add_argument("projet", nargs="?", default=None)
    p_hard.add_argument("--apply", action="store_true")
    p_hard.add_argument("--garder-article", action="store_true")
    p_hard.add_argument("--commit-article", action="store_true")
    p_hard.add_argument("--kb-renvoi", action="store_true")
    p_hard.add_argument("--suffixe", default=None)

    p_annuler = sub.add_parser("annuler")
    p_annuler.add_argument("date")
    p_annuler.add_argument("projet", nargs="?", default=None)
    p_annuler.add_argument("--suffixe", default=None)
    p_annuler.add_argument("--apply", action="store_true")

    p_soft = sub.add_parser("soft")
    p_soft.add_argument("projet", nargs="?", default=None)
    p_soft.add_argument("--apply", action="store_true")

    p_recycler = sub.add_parser("recycler")
    p_recycler.add_argument("chemin")
    p_recycler.add_argument("projet", nargs="?", default=None)
    p_recycler.add_argument("--vers", default=None)
    p_recycler.add_argument("--verdict", choices=VERDICTS_RECYCLAGE, default=None)
    p_recycler.add_argument("--lien", action="store_true")
    p_recycler.add_argument("--apply", action="store_true")

    p_lire = sub.add_parser("lire-archive")
    p_lire.add_argument("fichier", nargs="?", default=None)
    p_lire.add_argument("projet", nargs="?", default=None)
    p_lire.add_argument("--grep", default=None)
    p_lire.add_argument("--json", action="store_true")
    p_lire.add_argument("--racine", default=None,
                        help="lève l'ambiguïté fichier/projet quand les deux positionnels "
                             "sont nécessaires (le premier positionnel reste alors `fichier`)")

    p_clore = sub.add_parser("clore")
    p_clore.add_argument("projet", nargs="?", default=None)
    p_clore.add_argument("--apply", action="store_true")

    args = p.parse_args(argv)
    projet_arg = getattr(args, "racine", None) or args.projet
    root = resoudre_racine(projet_arg)

    if args.commande == "diagnostic":
        return cmd_diagnostic(root, args.json)
    if args.commande == "status":
        return cmd_status(root, args.legacy, args.json)
    if args.commande == "signals":
        return cmd_signals(root, args.quiet)
    if args.commande == "affirmations":
        return cmd_affirmations(root, args.ecrire, args.pistes_ecrire, args.json,
                                args.migrate, args.carrefour_match)
    if args.commande == "affirmation":
        return cmd_affirmation(root, args.id, args.statut, args.preuve, args.notes, args.apply)
    if args.commande == "hard":
        return cmd_hard(root, args.apply, args.garder_article, args.commit_article,
                        args.kb_renvoi, args.suffixe)
    if args.commande == "annuler":
        return cmd_annuler(root, args.date, args.suffixe, args.apply)
    if args.commande == "soft":
        return cmd_soft(root, args.apply)
    if args.commande == "recycler":
        return cmd_recycler(root, args.chemin, args.vers, args.verdict, args.lien, args.apply)
    if args.commande == "lire-archive":
        return cmd_lire_archive(root, args.fichier, args.grep, args.json)
    if args.commande == "clore":
        return cmd_clore(root, args.apply)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
