#!/usr/bin/env python3
"""Parseurs et générateur d'`affirmations.md` (piste AB2, `/reboot`).

Dérive les affirmations candidates d'un projet legacy depuis trois sources —
`etat_des_decouvertes.md` §2/§3/§4, `claim_check.md` (racine et `article*/`),
`reanalysis_registry.md` — les dédoublonne par similarité de Jaccard (annotation,
jamais de fusion silencieuse) et assemble `affirmations.md` (§ AB.5 du plan
`audit/2026-09-21/plan_reboot_versionnage.md`). Bibliothèque pure : aucune
écriture sur disque tant que l'appelant ne le demande pas explicitement.
"""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path

# --------------------------------------------------------------------------
# Découpage en puces et nettoyage
# --------------------------------------------------------------------------

RE_PUCE = re.compile(r"^-\s+\S")
RE_DESTINATION = re.compile(r"destination\s*:\s*\**(C[12]|[ABCDE])\**\s*(\([^)]*\))?", re.IGNORECASE)


def decouper_puces(corps: str) -> list[str]:
    """Puces de premier niveau (`- ...`), chacune avec ses lignes de continuation."""
    puces: list[str] = []
    courante: list[str] = []
    for ligne in corps.splitlines():
        if RE_PUCE.match(ligne):
            if courante:
                puces.append("\n".join(courante))
            courante = [ligne]
        elif courante:
            courante.append(ligne)
    if courante:
        puces.append("\n".join(courante))
    return puces


def nettoyer_enonce(puce: str, max_len: int = 220) -> str:
    texte = re.sub(r"^-\s+", "", puce.strip())
    texte = re.sub(r"\s+", " ", texte)
    texte = RE_DESTINATION.sub("", texte).strip()
    texte = re.sub(r"\s{2,}", " ", texte).strip(" .")
    if len(texte) > max_len:
        texte = texte[: max_len].rstrip() + "…"
    return texte


def extraire_destination(puce: str) -> str | None:
    m = RE_DESTINATION.search(puce)
    return m.group(1).upper() if m else None


# --------------------------------------------------------------------------
# Source 1 : état des découvertes (§2 acquis, §3 réfuté, §4 incertain)
# --------------------------------------------------------------------------

PLACEHOLDERS = ("[à renseigner]", "(rien encore)", "[À REGÉNÉRER", "néant", "[À REGENERER")


def _etat_legacy_le_plus_recent(root: Path) -> Path | None:
    """Archive `hard` la plus récente portant un `etat_legacy.md` (repli, cf. garde-fou ci-dessous)."""
    candidats = sorted(root.glob("archives/*_reboot/etat_legacy.md"))
    return candidats[-1] if candidats else None


def extraire_etat(root: Path, section_fn) -> dict:
    """`section_fn(texte, n)` : `cycle_status.section` ou son repli (jamais réimplémenté deux fois).

    Garde-fou (incident 2026-09-22, L5) : après un `hard --apply`, `<root>/etat_des_decouvertes.md`
    est le squelette NEUF posé par le reboot, pas l'état hérité (déplacé dans
    `archives/<date>_reboot/etat_legacy.md`). Un appel de `affirmations` à ce moment-là lisait donc
    silencieusement un fichier vide et écrasait un `affirmations.md` correct par un fichier à zéro
    ligne, sans erreur. Repli : si le fichier racine ne rend aucune puce dans aucune des trois
    sections, retomber sur l'archive `hard` la plus récente et le dire sur stderr — jamais en
    silence.
    """
    import sys as _sys

    def _extraire(chemin: Path) -> dict:
        txt = chemin.read_text(encoding="utf-8", errors="replace")

        def _items(n: int) -> list[str]:
            corps = section_fn(txt, n)
            return [p for p in decouper_puces(corps) if not any(ph in p for ph in PLACEHOLDERS)]

        acquis = [{"enonce": nettoyer_enonce(p), "destination": extraire_destination(p)}
                  for p in _items(2)]
        refute = [{"enonce": nettoyer_enonce(p)} for p in _items(3)]
        incertain = [{"enonce": nettoyer_enonce(p)} for p in _items(4)]
        return {"acquis": acquis, "refute": refute, "incertain": incertain}

    chemin = root / "etat_des_decouvertes.md"
    resultat = _extraire(chemin) if chemin.is_file() else {"acquis": [], "refute": [], "incertain": []}

    if not (resultat["acquis"] or resultat["refute"] or resultat["incertain"]):
        legacy = _etat_legacy_le_plus_recent(root)
        if legacy is not None:
            print(f"AVERTISSEMENT : {chemin} ne rend aucun acquis (squelette neuf post-hard ?) — "
                  f"repli sur {legacy.relative_to(root) if legacy.is_relative_to(root) else legacy}",
                  file=_sys.stderr)
            resultat = _extraire(legacy)

    return resultat


# --------------------------------------------------------------------------
# Source 2 : claim_check.md (racine et article*/)
# --------------------------------------------------------------------------

RE_SECTION_P_CLAIM = re.compile(r"^###\s+(P\d+)\s*[—-].*$", re.MULTILINE)


def _lignes_table(corps: str) -> list[str]:
    return [l for l in corps.splitlines() if l.strip().startswith("|")]


def _parser_table(corps: str) -> list[dict]:
    """Table markdown générique : entête → clés en minuscules, une ligne = un dict."""
    lignes = _lignes_table(corps)
    if len(lignes) < 2:
        return []
    entetes = [c.strip().lower() for c in lignes[0].strip("|").split("|")]
    lignes_donnees = lignes[2:]  # sauter l'entête et la ligne de séparation ---
    resultat = []
    for ligne in lignes_donnees:
        cols = [c.strip() for c in ligne.strip("|").split("|")]
        if len(cols) != len(entetes):
            continue
        resultat.append(dict(zip(entetes, cols)))
    return resultat


def _item_depuis_ligne_claim(row: dict, p: str) -> dict:
    verifie_le = row.get("vérifié le") or row.get("verifie le")
    notes = row.get("notes", "")
    if verifie_le:
        notes = (notes + " ; " if notes else "") + f"vérifié le {verifie_le}"
    return {
        "p": p,
        "numero": row.get("#"),
        "enonce": row.get("claim (extrait)") or row.get("claim") or "",
        "statut_legacy": row.get("statut", ""),
        "preuve": row.get("source / preuve") or row.get("preuve") or row.get("source/preuve") or "",
        "notes": notes,
    }


def extraire_claim_check(chemin: Path) -> list[dict]:
    """Deux dialectes réels coexistent sur le dépôt (mesuré 2026-09-21) : une section
    `### P<n> — ...` par priorité (ex. L4.13), ou une seule table `## Claims` avec une
    colonne `Priorité` (ex. La4). Le second est tenté seulement si le premier ne rend rien,
    pour ne jamais compter deux fois la même table si un projet mélange les deux un jour."""
    if not chemin.is_file():
        return []
    txt = chemin.read_text(encoding="utf-8", errors="replace")

    matches = list(RE_SECTION_P_CLAIM.finditer(txt))
    items: list[dict] = []
    for i, m in enumerate(matches):
        p = m.group(1)
        debut = m.end()
        fin = matches[i + 1].start() if i + 1 < len(matches) else len(txt)
        items.extend(_item_depuis_ligne_claim(row, p) for row in _parser_table(txt[debut:fin]))
    if items:
        return items

    for row in _parser_table(txt):
        p = (row.get("priorité") or row.get("priorite") or "P2").strip().upper()
        if not re.match(r"^P\d+$", p):
            p = "P2"
        items.append(_item_depuis_ligne_claim(row, p))
    return items


# --------------------------------------------------------------------------
# Source 3 : reanalysis_registry.md (legacy `/mtbc-reboot`)
# --------------------------------------------------------------------------

RE_SECTION_P_REGISTRY = re.compile(r"^##\s+Claims\s+(P\d+)\b.*$", re.MULTILINE)


def extraire_reanalysis_registry(chemin: Path) -> list[dict]:
    if not chemin.is_file():
        return []
    txt = chemin.read_text(encoding="utf-8", errors="replace")
    matches = list(RE_SECTION_P_REGISTRY.finditer(txt))
    items: list[dict] = []
    for i, m in enumerate(matches):
        p = m.group(1)
        debut = m.end()
        fin = matches[i + 1].start() if i + 1 < len(matches) else len(txt)
        for row in _parser_table(txt[debut:fin]):
            items.append({
                "p": p,
                "numero": row.get("#"),
                "enonce": row.get("enonce") or row.get("énoncé") or "",
                "statut_legacy": row.get("statut", ""),
                "preuve": row.get("preuve", ""),
                "notes": row.get("notes", ""),
            })
    return items


# --------------------------------------------------------------------------
# Source 4 (optionnelle, `--migrate`) : dépouillement mécanique du cahier legacy
# --------------------------------------------------------------------------

RE_ENTREE_CAHIER = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})(.*)$", re.MULTILINE)


def extraire_cahier_migrate(root: Path) -> list[dict]:
    """Dépouillement MÉCANIQUE du cahier legacy (AB8a, `--migrate`), à n'invoquer que
    lorsque l'état legacy est un squelette (rien à tirer de §2/§3/§4). Un candidat brut
    par puce de premier niveau sous chaque entrée datée `## AAAA-MM-JJ` — ni jugement, ni
    tri : ce script réduit le coût de REPÉRAGE (un `rg` ciblé fait à la place de
    l'assistant), il ne remplace pas la relecture assistée `[Opus:high]` prévue au plan.
    Limite assumée, dans le même esprit que le reste du module : une entrée de cahier
    rédigée en prose continue, sans puce `- `, n'est pas vue — cf. `decouper_puces`."""
    chemins = [root / "cahier_de_labo.md", root / "cahier_de_labo_archive.md"]
    candidats: list[dict] = []
    for chemin in chemins:
        if not chemin.is_file():
            continue
        txt = chemin.read_text(encoding="utf-8", errors="replace")
        matches = list(RE_ENTREE_CAHIER.finditer(txt))
        for i, m in enumerate(matches):
            date, titre = m.group(1), m.group(2).strip(" —-")
            debut = m.end()
            fin = matches[i + 1].start() if i + 1 < len(matches) else len(txt)
            for puce in decouper_puces(txt[debut:fin]):
                enonce = nettoyer_enonce(puce)
                if enonce:
                    candidats.append({"date": date, "titre": titre, "enonce": enonce,
                                       "fichier": chemin.name})
    return candidats


# --------------------------------------------------------------------------
# Normalisation du statut legacy vers le vocabulaire à cinq états
# --------------------------------------------------------------------------

def _normaliser_cle(s: str) -> str:
    s = re.sub(r"\*+", "", s)
    s = s.lower().strip()
    s = (s.replace("é", "e").replace("è", "e").replace("ê", "e")
           .replace("à", "a").replace("î", "i"))
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# Un statut POSITIF hérité (« vérifié », « confirmé ») ne devient JAMAIS `prouvée` :
# il vaut présomption, pas preuve. La règle cardinale que ce script inscrit lui-même en
# tête de `affirmations.md` est qu'une ligne n'est un acquis que si elle est prouvée
# « dans l'environnement courant avec les données courantes » — or un claim_check vérifié
# sous l'environnement legacy, sur des données que le frontmatter déclare souvent
# `non vérifié`, ne remplit ni l'une ni l'autre condition. Mesuré sur L4.13 le 2026-09-22
# (AB7) : l'ancien mappage rendait 30 des 33 affirmations `prouvée` d'emblée, et la porte 1
# ne bloquait plus que sur 3 lignes — le reboot perdait l'essentiel de son effet sur le
# projet le plus riche du lot. Le sens de l'erreur tranche : un faux « non prouvé » coûte
# une re-vérification, un faux « prouvé » coûte un article faux.
# Les statuts NÉGATIFS restent négatifs (une réfutation legacy reste une réfutation, et la
# sous-piste P1.n existe précisément pour les réexaminer).
_MAP_STATUT_LEGACY = {
    "verifie": "en test", "confirme": "en test", "part confirme": "en test",
    "corrige": "en test",  # dialecte La4 : réputé faux, corrigé et revérifié sous l'ANCIEN env
    "partiellement confirme": "en test",
    "a verifier": "non testée", "ambigu": "en test", "en attente": "non testée",
    "infirme": "réfutée", "incorrect": "réfutée", "incorrect imprecis": "réfutée",
    "non verifiable": "non testée",
}


def normaliser_statut_legacy(s: str | None) -> str:
    if not s:
        return "non testée"
    cle = _normaliser_cle(s)
    if cle in _MAP_STATUT_LEGACY:
        return _MAP_STATUT_LEGACY[cle]
    # repli : préfixe le plus proche (ex. "part confirme reviewer 2" → "part confirme")
    for k, v in _MAP_STATUT_LEGACY.items():
        if cle.startswith(k):
            return v
    return "non testée"


def statut_p_pour_destination(destination: str | None) -> str:
    """Destination A → P1 (structurant) ; sinon P2 par défaut, à revoir à la relecture."""
    return "P1" if destination == "A" else "P2"


# --------------------------------------------------------------------------
# Assemblage de la liste unique d'affirmations candidates
# --------------------------------------------------------------------------

def assembler_affirmations(root: Path, section_fn, migrer: bool = False) -> list[dict]:
    n = 0

    def _id() -> str:
        nonlocal n
        n += 1
        return f"A{n}"

    affirmations: list[dict] = []

    etat = extraire_etat(root, section_fn)
    for a in etat["acquis"]:
        affirmations.append({
            "id": _id(), "p": statut_p_pour_destination(a["destination"]),
            "enonce": a["enonce"], "provenance": "état §2",
            "legacy": "oui", "statut": "non testée", "piste": "", "preuve": "",
            "notes": f"destination legacy : {a['destination']}" if a["destination"] else "",
        })
    for r in etat["refute"]:
        affirmations.append({
            "id": _id(), "p": "P3", "enonce": r["enonce"], "provenance": "état §3",
            "legacy": "oui", "statut": "réfutée", "piste": "", "preuve": "",
            "notes": "réfuté dans l'état legacy — conservé pour mémoire",
        })
    for r in etat["incertain"]:
        affirmations.append({
            "id": _id(), "p": "P3", "enonce": r["enonce"], "provenance": "état §4",
            "legacy": "oui", "statut": "en test", "piste": "", "preuve": "",
            "notes": "incertain dans l'état legacy",
        })

    fichiers_claims = [root / "claim_check.md"] + sorted(root.glob("article*/claim_check.md"))
    for chemin in fichiers_claims:
        for j, c in enumerate(extraire_claim_check(chemin), start=1):
            affirmations.append({
                "id": _id(), "p": c["p"] or "P2", "enonce": c["enonce"],
                "provenance": f"claim_check {chemin.parent.name}/ #{c['numero'] or j}",
                "legacy": "oui", "statut": normaliser_statut_legacy(c["statut_legacy"]),
                "piste": "", "preuve": c["preuve"], "notes": c["notes"],
            })

    for j, r in enumerate(extraire_reanalysis_registry(root / "reanalysis_registry.md"), start=1):
        affirmations.append({
            "id": _id(), "p": r["p"] or "P2", "enonce": nettoyer_enonce("- " + r["enonce"]),
            "provenance": f"registry #{r['numero'] or j}",
            "legacy": "oui", "statut": normaliser_statut_legacy(r["statut_legacy"]),
            "piste": "", "preuve": nettoyer_enonce("- " + r["preuve"]) if r["preuve"] else "",
            "notes": nettoyer_enonce("- " + r["notes"]) if r["notes"] else "",
        })

    if migrer:
        for c in extraire_cahier_migrate(root):
            affirmations.append({
                "id": _id(), "p": "P2", "enonce": c["enonce"],
                "provenance": f"cahier legacy {c['fichier']} — {c['date']} {c['titre']}".strip(),
                "legacy": "oui", "statut": "non testée", "piste": "", "preuve": "",
                "notes": "candidat brut --migrate : extraction mécanique, pas encore relu ni trié",
            })

    marquer_doublons(affirmations)
    return affirmations


# --------------------------------------------------------------------------
# Dédoublonnage par similarité de Jaccard — ANNOTATION, jamais de fusion
# --------------------------------------------------------------------------

def _tokens(enonce: str) -> set[str]:
    return set(re.findall(r"[a-zàâäéèêëïîôöùûüç0-9]{3,}", enonce.lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def marquer_doublons(affirmations: list[dict], seuil: float = 0.6) -> None:
    toks = [_tokens(a["enonce"]) for a in affirmations]
    for i in range(len(affirmations)):
        for j in range(i + 1, len(affirmations)):
            s = _jaccard(toks[i], toks[j])
            if s >= seuil:
                note = f"doublon possible avec {{}} (Jaccard {s:.2f})"
                affirmations[i]["notes"] = (affirmations[i]["notes"] + " ; " if affirmations[i]["notes"] else "") \
                    + note.format(affirmations[j]["id"])
                affirmations[j]["notes"] = (affirmations[j]["notes"] + " ; " if affirmations[j]["notes"] else "") \
                    + note.format(affirmations[i]["id"])


# --------------------------------------------------------------------------
# Génération de `affirmations.md`
# --------------------------------------------------------------------------

def compter_statuts(affirmations: list[dict]) -> dict:
    compteurs = {"non_testee": 0, "en_test": 0, "prouvee": 0, "refutee": 0, "abandonnee": 0}
    cle = {"non testée": "non_testee", "en test": "en_test", "prouvée": "prouvee",
           "réfutée": "refutee", "abandonnée": "abandonnee"}
    for a in affirmations:
        compteurs[cle.get(a["statut"], "non_testee")] += 1
    return compteurs


def generer_affirmations_md(root: Path, affirmations: list[dict], mesures: dict | None = None,
                             archive: str | None = None) -> str:
    compteurs = compter_statuts(affirmations)
    mesures = mesures or {}
    lignes = ["---",
              f"reboot: {_dt.date.today().isoformat()}",
              f"date: {_dt.date.today().isoformat()}",
              f"archive: {archive or 'non archivé (généré en prévisualisation AB2)'}",
              f"env_legacy: {mesures.get('env_projet') or 'non rattaché'}",
              f"env_courant: v{mesures.get('env_courant') or '0.0.0'}",
              "donnees_legacy: " + (", ".join(f"{d['store']}@{d['version_citee']}"
                                               for d in mesures.get("donnees", [])) or "aucune citation trouvée"),
              "donnees_courantes: " + (", ".join(f"{d['store']}={d.get('statut') or '?'}"
                                                  for d in mesures.get("donnees", [])) or "non vérifié"),
              "compteurs:",
              f"  non_testee: {compteurs['non_testee']}",
              f"  en_test: {compteurs['en_test']}",
              f"  prouvee: {compteurs['prouvee']}",
              f"  refutee: {compteurs['refutee']}",
              f"  abandonnee: {compteurs['abandonnee']}",
              "---", "",
              f"# Affirmations — {root.name}", "",
              "Règle : aucune ligne n'est un acquis tant qu'elle n'est pas `[prouvée]` dans "
              "l'environnement courant avec les données courantes.", "",
              "| id | P | énoncé | provenance | dépendances | legacy | statut | piste | preuve | notes |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for a in affirmations:
        cells = [a["id"], a["p"], a["enonce"], a["provenance"], "—", a["legacy"],
                 a["statut"], a["piste"] or "—", a["preuve"] or "—", a["notes"] or "—"]
        lignes.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
    return "\n".join(lignes) + "\n"


# --------------------------------------------------------------------------
# Génération du nouveau `pistes.md` de reboot (squelette P1-P5)
# --------------------------------------------------------------------------

def _affirmations_a_retablir(affirmations: list[dict]) -> list[dict]:
    """Sous-ensemble et ordre partagés entre `assigner_pistes` et
    `generer_pistes_reboot_md` : une seule définition de « P1.k », pour que les deux
    ne puissent pas diverger l'une de l'autre (AB8b)."""
    return [a for a in affirmations if a["statut"] in ("non testée", "en test")]


def assigner_pistes(affirmations: list[dict]) -> None:
    """Fixe `a["piste"]` = "P1.k" pour chaque affirmation à rétablir. À appeler UNE FOIS,
    juste après `assembler_affirmations` et avant toute génération de `affirmations.md`
    ou de `pistes.md` (AB8b) : sans cet appel, la colonne `piste` de `affirmations.md`
    reste vide et le lien `A<k>` ↔ `P1.k` n'existe que dans l'ordre des lignes de la
    liste en mémoire — il casse silencieusement dès qu'une ligne est ajoutée ou retirée
    entre la génération des deux fichiers."""
    for k, a in enumerate(_affirmations_a_retablir(affirmations), start=1):
        a["piste"] = f"P1.{k}"


def generer_pistes_reboot_md(root: Path, affirmations: list[dict]) -> str:
    a_retablir = _affirmations_a_retablir(affirmations)
    a_reexaminer = [a for a in affirmations if a["statut"] in ("réfutée",)]
    lignes = [f"# Pistes — {root.name} (reboot {_dt.date.today().isoformat()})", "",
              "Règle : édité par mutation locale (jamais réécrit en bloc), uniquement via `/pistes`.",
              "États : [à faire] [en cours] [réalisé] [abandonné].", "",
              "## P1. Ré-établir l'acquis legacy dans l'environnement courant [en cours]",
              f"  origine : reboot {_dt.date.today().isoformat()}    maj : {_dt.date.today().isoformat()}"]
    for k, a in enumerate(a_retablir, start=1):
        lignes.append(f"  - P1.{k}  {a['id']} « {a['enonce']} » [à faire]")
    if a_reexaminer:
        lignes.append(f"  - P1.{len(a_retablir) + 1}  Réexaminer les {len(a_reexaminer)} "
                       f"affirmation(s) réfutée(s) legacy [à faire]")
    lignes += ["",
               "## P2. Recadrage post-reboot — question et périmètre [à faire]",
               f"  origine : reboot {_dt.date.today().isoformat()}",
               "  - P2.1 [DÉCISION CG] TRANSFÉRER / FUSIONNER / REDÉCOUPER — jamais exécuté d'office",
               "",
               "## P3. Recyclage des artefacts legacy (archives/…/RECYCLAGE.md) [en cours]",
               f"  origine : reboot {_dt.date.today().isoformat()}",
               "",
               "## P4. Pistes legacy ouvertes au reboot, non re-cadrées [à faire]",
               f"  origine : reboot {_dt.date.today().isoformat()}",
               "",
               "## P5. Manuscrit — feuille blanche, bloqué par P1 puis par la porte 1 rouverte "
               "à la clôture [à faire]",
               f"  origine : reboot {_dt.date.today().isoformat()}",
               "  Ni P1 soldé ni `clore` ne dégèlent P5 : recadrage post-clôture, `/lit-review` "
               "ciblée, porte 1 re-prouvée, puis 1bis (`/reboot`, étape 4).", ""]
    return "\n".join(lignes)
