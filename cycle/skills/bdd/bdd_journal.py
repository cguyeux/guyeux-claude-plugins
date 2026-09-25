#!/usr/bin/env python3
"""Bibliotheque d'ecriture pour les scripts qui modifient un store `bdd/registre.json`.

Import par chemin fixe (`${CLAUDE_PLUGIN_ROOT}/skills/bdd/bdd_journal.py`) : les skills de genre qui
l'utilisent doivent degrader silencieusement si le skill `bdd` n'est pas installe sur la
machine (`mp`, `mh`) — `stamp()` rend alors `@non-versionnee` plutot que de lever, et
`ecriture()` devient un context manager transparent (aucun journal, aucun refus de derive).
"""
from __future__ import annotations

import importlib.util
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

_BDD_PY = Path(__file__).resolve().parent / "bdd.py"


def _charger_bdd():
    if not _BDD_PY.is_file():
        return None
    spec = importlib.util.spec_from_file_location("bdd", _BDD_PY)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("bdd", module)
    spec.loader.exec_module(module)
    return module


_bdd = _charger_bdd()


def disponible() -> bool:
    return _bdd is not None


class ErreurDerive(RuntimeError):
    pass


def stamp(store_id: str) -> str:
    if _bdd is None:
        return f"{store_id}@non-versionnee"
    try:
        registre, bases = _bdd.charger_registre()
        store = _bdd.obtenir_store(registre, store_id)
    except _bdd.BddError:
        return f"{store_id}@non-versionnee"
    if store.get("etat") == "à créer":
        return f"{store_id}@non-versionnee"
    if store["type"] == "git":
        racine = _bdd.resoudre_racine(store, bases)
        resultat = _bdd.scanner_git(racine, store)
        return f"{store_id}@{resultat['version']}"
    meta = _bdd.resoudre_meta(store_id, store, bases)
    doc = _bdd.lire_version_json(meta)
    if doc is None:
        return f"{store_id}@non-versionnee"
    return f"{store_id}@{doc['version']}"


def stamp_json(store_id: str) -> dict:
    return {"store": store_id, "citation": stamp(store_id)}


def meta_dir(store_id: str) -> Path | None:
    """Repertoire `.bdd/<store_id>` du store (jamais a l'interieur de sa racine, cf.
    resoudre_meta) : sous-repertoire `sauvegardes/` a utiliser par les scripts d'ecriture
    pour y deposer leurs copies de securite AVANT overwrite, au lieu de les semer a cote
    du fichier suivi (piste AA3 : `barcode_complete.tsv.avant_*` polluait le scan
    `jeu_fichiers` et forcait des exclusions glob a maintenir a la main). `None` si le
    skill `bdd` est absent ou le store non resolvable — l'appelant doit alors degrader
    vers son ancien comportement, jamais lever."""
    if _bdd is None:
        return None
    try:
        registre, bases = _bdd.charger_registre()
        store = _bdd.obtenir_store(registre, store_id)
        return _bdd.resoudre_meta(store_id, store, bases)
    except Exception:
        return None


def store_for_path(chemin: str) -> str | None:
    """Store dont la racine (resolue registre) contient `chemin`, ou None si aucun ne
    correspond (chemin hors bdd/, `--dest` arbitraire type /tmp, skill absent...).

    Sert aux scripts dont la destination d'ecriture est un PARAMETRE (ex.
    `fetch_reports_http.py --dest`, piste AA3) : la destination reelle n'est connue qu'a
    l'execution, contrairement aux scripts qui codent leur racine en dur. Le store le plus
    SPECIFIQUE (racine la plus longue) gagne si plusieurs racines sont prefixes l'une de
    l'autre — aucun cas de ce genre au 2026-09-21, mais le registre n'exclut pas d'en ajouter."""
    if _bdd is None:
        return None
    try:
        registre, bases = _bdd.charger_registre()
        cible = Path(chemin).resolve()
    except Exception:
        return None
    meilleur, meilleure_longueur = None, -1
    for store_id, store in registre.get("stores", {}).items():
        if store.get("type") not in ("arbre_souches", "jeu_fichiers", "fichier"):
            continue
        try:
            racine = _bdd.resoudre_racine(store, bases).resolve()
        except Exception:
            continue
        if cible == racine or racine in cible.parents:
            longueur = len(str(racine))
            if longueur > meilleure_longueur:
                meilleur, meilleure_longueur = store_id, longueur
    return meilleur


@contextmanager
def ecriture(
    store_id: str,
    *,
    outil: str,
    motif: str,
    piste: str | None = None,
    projet: str | None = None,
    undo_log: str | None = None,
    sauvegarde: str | None = None,
    sans_undo: bool = False,
    malgre_derive: bool = False,
) -> Generator[dict | None]:
    if _bdd is None:
        yield None
        return

    registre, bases = _bdd.charger_registre()
    store = _bdd.obtenir_store(registre, store_id)
    racine = _bdd.resoudre_racine(store, bases)
    meta = _bdd.resoudre_meta(store_id, store, bases)
    doc = _bdd.lire_version_json(meta)

    if doc is not None and not malgre_derive:
        live = _bdd.calculer_sentinelle(_bdd._racine_sentinelle(store, racine))
        ref = doc.get("sentinelle") or {}
        if live.get("sha_entrees") != ref.get("sha_entrees"):
            raise ErreurDerive(
                f"{store_id} est +dirty (derive depuis r{doc['revision']}) : "
                "lancer 'bdd check' avant d'ecrire, ou passer malgre_derive=True en connaissance de cause."
            )

    try:
        yield doc
    except Exception:
        if doc is not None:
            _bdd.journal_ajouter(meta, {
                "id": f"apres_r{doc['revision']}", "ts": _bdd._maintenant_iso(), "store": store_id,
                "type": "ecriture_interrompue", "outil": outil, "motif": motif, "piste": piste,
                "projet": projet, "operateur": _bdd._detecter_operateur(),
            })
        raise

    resultat = _bdd.SCANNERS[store["type"]](racine, store)
    anciennes = [] if doc is None else _bdd.lire_manifeste(meta, doc["revision"])[1]
    delta, vide = _bdd._calculer_delta(store["type"], anciennes, resultat["lignes"])
    if vide:
        return

    version = _bdd.construire_version(store["type"], resultat)
    nouvelle_revision = 0 if doc is None else doc["revision"] + 1
    sentinelle = _bdd.calculer_sentinelle(_bdd._racine_sentinelle(store, racine))
    _bdd.ecrire_version_json(meta, store_id, store, resultat, version, revision=nouvelle_revision,
                               sentinelle=sentinelle, duree_s=resultat.get("duree_s", 0))
    _bdd.ecrire_manifeste(meta, nouvelle_revision, resultat)
    _bdd.ecrire_sentinelle_cache(meta, sentinelle)
    _bdd.journal_ajouter(meta, {
        "id": f"r{nouvelle_revision}", "ts": _bdd._maintenant_iso(), "store": store_id, "type": "ecriture",
        "outil": outil, "motif": motif, "piste": piste, "projet": projet,
        "operateur": _bdd._detecter_operateur(), "session": _bdd._detecter_session(),
        "delta": delta,
        "undo": None if sans_undo else ({"type": "undo_log", "chemin": undo_log} if undo_log else None),
        "sauvegarde": sauvegarde,
    })
    _bdd.miroir_copier(store_id, meta)
