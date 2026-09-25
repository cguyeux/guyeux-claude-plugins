#!/usr/bin/env python3
"""Bloc `[DONNÉES — …]` pour le hook `SessionStart` (`session_context.sh`, piste AA2).

Compare la citation `données :`/`**Données :**` la plus récente d'un projet (état des
découvertes en priorité, sinon la dernière entrée du cahier) à l'état COURANT des
stores cités (skill `bdd`), et signale une dérive : la base a bougé depuis que le
projet l'a citée en dernier. Silencieux — aucune sortie, code 0 — si le projet ne cite
aucun store versionné, si le skill `bdd` est absent (mp, mh), ou en cas d'erreur : ce
script alimente un hook qui tourne à chaque démarrage de session, potentiellement des
dizaines de fois en parallèle sur cette machine, et ne doit jamais bloquer ni faire de
bruit hors-sujet (même doctrine que les blocs ENVIRONNEMENT/VERSION voisins).

Usage : session_donnees.py <racine_projet>
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

_BDD_PY = Path(__file__).resolve().parent / "bdd.py"

_CITATION_RE = re.compile(r"([a-zA-Z0-9_-]+)@([^\s;,]+)")


def _charger_bdd():
    if not _BDD_PY.is_file():
        return None
    spec = importlib.util.spec_from_file_location("bdd", _BDD_PY)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None
    return module


def derniere_citation(root: Path):
    """(date_iso, ligne_citation) la plus récente. L'état fait foi s'il porte une
    ligne `**Données :**` exploitable (réécrite en entier à chaque `/etat update`,
    donc toujours à jour) ; à défaut, la dernière ligne `données :` du cahier
    (append-only : on ne veut que la plus récente, pas tout l'historique)."""
    etat = root / "etat_des_decouvertes.md"
    if etat.is_file():
        try:
            texte = etat.read_text(encoding="utf-8", errors="replace")
        except OSError:
            texte = ""
        m_ligne = re.search(r"^\*\*Données\s*:\*\*\s*(.+)$", texte, re.MULTILINE)
        m_date = re.search(r"\*\*Réécrit le\s*:\*\*\s*(\d{4}-\d{2}-\d{2})", texte)
        if m_ligne and m_date and "@" in m_ligne.group(1):
            return m_date.group(1), m_ligne.group(1).strip()

    cahier = root / "cahier_de_labo.md"
    if cahier.is_file():
        try:
            lignes = cahier.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            lignes = []
        date_courante = None
        derniere = None
        for ligne in lignes:
            m_entete = re.match(r"^## (\d{4}-\d{2}-\d{2}) \d{2}:\d{2}", ligne)
            if m_entete:
                date_courante = m_entete.group(1)
                continue
            m_don = re.match(r"^donn[ée]es\s*:\s*(.+)$", ligne.strip(), re.IGNORECASE)
            if m_don and date_courante and "@" in m_don.group(1):
                derniere = (date_courante, m_don.group(1).strip())
        if derniere:
            return derniere
    return None, None


def _stamp(bdd, store_id, store, bases):
    if store["type"] == "git":
        racine = bdd.resoudre_racine(store, bases)
        resultat = bdd.scanner_git(racine, store)
        return resultat["version"]
    meta = bdd.resoudre_meta(store_id, store, bases)
    doc = bdd.lire_version_json(meta)
    if doc is None:
        return None
    return doc["version"]


def _ecritures_depuis(bdd, store_id, store, bases, date_citation):
    """Nombre d'événements `ecriture` journalisés strictement après le JOUR de la
    citation (granularité jour, pas d'horodatage précis : un rappel informatif, pas
    une preuve de reproductibilité — celle-ci vient de la comparaison des stamps)."""
    if not date_citation or store["type"] == "git":
        return 0
    meta = bdd.resoudre_meta(store_id, store, bases)
    journal = meta / "journal.jsonl"
    if not journal.is_file():
        return 0
    n = 0
    try:
        with open(journal, encoding="utf-8") as f:
            for ligne in f:
                try:
                    ev = json.loads(ligne)
                except Exception:
                    continue
                if ev.get("type") != "ecriture":
                    continue
                if ev.get("ts", "")[:10] > date_citation:
                    n += 1
    except OSError:
        return 0
    return n


def main() -> None:
    if len(sys.argv) < 2:
        return
    root = Path(sys.argv[1])
    date_citation, ligne = derniere_citation(root)
    if not ligne:
        return

    bdd = _charger_bdd()
    if bdd is None:
        return
    try:
        registre, bases = bdd.charger_registre()
    except Exception:
        return

    derives = []
    for store_id, version_cite in _CITATION_RE.findall(ligne):
        if store_id not in registre.get("stores", {}):
            continue
        try:
            store = bdd.obtenir_store(registre, store_id)
            if store.get("etat") == "à créer":
                continue
            actuelle = _stamp(bdd, store_id, store, bases)
        except Exception:
            continue
        if actuelle is None or actuelle == version_cite:
            continue
        n = _ecritures_depuis(bdd, store_id, store, bases, date_citation)
        derives.append((store_id, version_cite, actuelle, n))

    if not derives:
        return

    parts = []
    for store_id, cite, actuelle, n in derives:
        suffixe = f" : {n} écriture(s) journalisée(s) depuis" if n else ""
        parts.append(f"{store_id}@{cite} du {date_citation} ; courante {store_id}@{actuelle}{suffixe}")
    print("[DONNÉES — état fondé sur " + " ; ".join(parts) + "]")


if __name__ == "__main__":
    main()
