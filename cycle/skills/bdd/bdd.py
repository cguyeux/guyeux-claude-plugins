#!/usr/bin/env python3
"""Versionnage des bases internes declarees dans `bdd/registre.json` (piste AA).

Quatre types de store : `arbre_souches`, `jeu_fichiers`, `fichier`, `git`. Sous-commandes :
init, stamp, check, bump, log, diff, miroir. Spec complete :
`~/docs/environnement/audit/2026-09-21/plan_reboot_versionnage.md` § Chantier AA.
Stdlib uniquement (le skill doit rester importable sans dependance externe).
"""
from __future__ import annotations

import argparse
import csv
import fnmatch
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from pathlib import Path

NOM_META = ".bdd"
SEUIL_COORD = 50_000
REGISTRE_DEFAUT = Path.home() / "docs" / "environnement" / "bdd" / "registre.json"
MIROIR_RACINE = Path.home() / "docs" / "environnement" / "bdd" / "journaux"
ENV_RACINE = Path.home() / "docs" / "environnement"

FICHIERS_SOUCHE = ("spdi.txt", "report.json", "crispr_reads_report.json")


class BddError(Exception):
    pass


# --------------------------------------------------------------------------- registre

def charger_registre(chemin: str | None = None) -> tuple[dict, dict]:
    chemin_reel = Path(chemin or os.environ.get("BDD_REGISTRE") or REGISTRE_DEFAUT).expanduser()
    if not chemin_reel.is_file():
        raise BddError(f"registre introuvable : {chemin_reel}")
    registre = json.loads(chemin_reel.read_text(encoding="utf-8"))
    return registre, registre.get("bases", {})


def obtenir_store(registre: dict, store_id: str) -> dict:
    stores = registre.get("stores", {})
    if store_id not in stores:
        raise BddError(f"store inconnu : {store_id} (connus : {', '.join(sorted(stores))})")
    return stores[store_id]


def resoudre_racine(store: dict, bases: dict) -> Path:
    racine = store.get("racine")
    if racine is None:
        raise BddError("store sans racine (etat 'a creer' ?)")
    chemin = Path(racine).expanduser()
    if not chemin.is_absolute():
        base = store.get("base")
        if base is not None:
            chemin = Path(bases[base]).expanduser() / racine
    return Path(chemin).resolve()


def resoudre_meta(store_id: str, store: dict, bases: dict) -> Path:
    """`.bdd/` n'est JAMAIS a l'interieur de la racine d'un `arbre_souches` (clade fantome) :
    a defaut de `meta` explicite dans le registre, on se rabat sur le parent de la racine."""
    if "meta" in store:
        return Path(store["meta"]).expanduser().resolve()
    racine = resoudre_racine(store, bases)
    base_dir = racine.parent if store["type"] in ("fichier", "arbre_souches") else racine
    return base_dir / NOM_META / store_id


# --------------------------------------------------------------------------- utilitaires

def _aujourdhui() -> str:
    return date.today().isoformat()


def _maintenant_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _maintenant_lisible() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _detecter_operateur() -> str:
    override = os.environ.get("BDD_OPERATEUR")
    if override:
        return override
    if os.environ.get("CLAUDECODE") or os.environ.get("CLAUDE_CODE"):
        return "claude-code"
    if os.environ.get("CODEX_SANDBOX") or os.environ.get("CODEX_HOME"):
        return "codex"
    return "cg"


def _detecter_session() -> dict:
    return {
        "agentctl_pid": os.getppid(),
        "claude_session": os.environ.get("CLAUDE_SESSION_ID") or os.environ.get("CLAUDECODE_SESSION_ID"),
    }


def _sha256_fichier(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def _match_glob_any(nom: str, motifs: list[str], pour_dossier: bool = False) -> str | None:
    for m in motifs:
        if m.endswith("/") != pour_dossier:
            continue
        cible = m.rstrip("/") if pour_dossier else m
        if fnmatch.fnmatch(nom, cible):
            return m
    return None


# --------------------------------------------------------------------------- sentinelle

def calculer_sentinelle(racine: Path) -> dict:
    """Exclut toujours `NOM_META` : `.bdd/` peut se retrouver dans le repertoire sentinelle
    (type `fichier`, ou `arbre_souches` sans `meta` explicite dans le registre) et sa propre
    creation ne doit pas se signaler elle-meme comme une derive du store."""
    try:
        entrees = sorted(
            (e.name, e.stat(follow_symlinks=False).st_mtime)
            for e in os.scandir(racine)
            if e.name != NOM_META
        )
        mtime_racine = racine.stat().st_mtime
    except OSError:
        return {"mtime_racine": None, "n_entrees": 0, "sha_entrees": None}
    src = "\n".join(f"{n}\t{m!r}" for n, m in entrees)
    sha = hashlib.sha256(src.encode("utf-8", "surrogateescape")).hexdigest()
    return {"mtime_racine": mtime_racine, "n_entrees": len(entrees), "sha_entrees": sha}


def _racine_sentinelle(store: dict, racine: Path) -> Path:
    return racine.parent if store["type"] == "fichier" else racine


# --------------------------------------------------------------------------- scan : arbre_souches

def _iter_souches(racine: Path, plate: bool):
    if plate:
        try:
            entrees = list(os.scandir(racine))
        except OSError:
            return
        for e in entrees:
            if e.name == NOM_META:
                continue
            if e.is_dir(follow_symlinks=False) or e.is_symlink():
                yield "", e.name, Path(e.path)
        return
    try:
        clades = list(os.scandir(racine))
    except OSError:
        return
    for ce in clades:
        if ce.name == NOM_META or not (ce.is_dir(follow_symlinks=False) or ce.is_symlink()):
            continue
        try:
            sras = list(os.scandir(ce.path))
        except OSError:
            sras = []
        for se in sras:
            if se.is_dir(follow_symlinks=False) or se.is_symlink():
                yield ce.name, se.name, Path(se.path)


def _classer_souche(sra_path: Path):
    if os.path.islink(sra_path):
        return "lien", None, None
    sous_dirs = []
    try:
        for e in os.scandir(sra_path):
            if e.is_dir(follow_symlinks=False):
                sous_dirs.append(Path(e.path))
    except (OSError, NotADirectoryError):
        return "vide", None, None
    candidats = sous_dirs if sous_dirs else [sra_path]
    for c in candidats:
        spdi, report, crispr = c / FICHIERS_SOUCHE[0], c / FICHIERS_SOUCHE[1], c / FICHIERS_SOUCHE[2]
        spdi_ok, report_ok, crispr_ok = spdi.is_file(), report.is_file(), crispr.is_file()
        if spdi_ok or report_ok or crispr_ok:
            if spdi_ok and report_ok:
                cat = "complet"
            elif spdi_ok:
                cat = "spdi_seul"
            elif report_ok:
                cat = "report_seul"
            else:
                cat = "crispr_seul"
            return cat, (spdi.stat() if spdi_ok else None), (report.stat() if report_ok else None)
    return "vide", None, None


def scanner_arbre_souches(racine: Path, store: dict) -> dict:
    debut = time.monotonic()
    plate = bool(store.get("plate"))
    paires = list(_iter_souches(racine, plate))
    lignes: list[tuple] = [None] * len(paires)  # type: ignore[list-item]

    def _traiter(item):
        i, (clade, sra, chemin) = item
        cat, st_spdi, st_report = _classer_souche(chemin)
        return i, (
            clade, sra, cat,
            str(st_spdi.st_size) if st_spdi else "-",
            str(int(st_spdi.st_mtime)) if st_spdi else "-",
            str(st_report.st_size) if st_report else "-",
            str(int(st_report.st_mtime)) if st_report else "-",
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, ligne in pool.map(_traiter, enumerate(paires)):
            lignes[i] = ligne

    lignes.sort(key=lambda r: (r[0], r[1]))
    clades = {r[0] for r in lignes}
    n_exploitables = sum(1 for r in lignes if r[2] in ("complet", "spdi_seul"))
    n_vides = sum(1 for r in lignes if r[2] == "vide")
    n_partiels = len(lignes) - n_exploitables - n_vides
    placement_src = "\n".join(f"{r[0]}\t{r[1]}" for r in lignes)
    lignes_contenu = sorted(lignes, key=lambda r: r[1])
    contenu_src = "\n".join(f"{r[1]}\t{r[3]}\t{r[4]}\t{r[5]}\t{r[6]}" for r in lignes_contenu)
    return {
        "header": ["clade", "sra", "categorie", "taille_spdi", "mtime_spdi", "taille_report", "mtime_report"],
        "lignes": lignes,
        "compte": {
            "clades": len(clades), "souches": len(lignes),
            "exploitables": n_exploitables, "vides": n_vides, "partiels": n_partiels,
        },
        "condensats": {
            "placement": hashlib.sha256(placement_src.encode("utf-8", "surrogateescape")).hexdigest()[:6],
            "contenu": hashlib.sha256(contenu_src.encode("utf-8", "surrogateescape")).hexdigest()[:6],
        },
        "duree_s": time.monotonic() - debut,
    }


def calculer_delta_arbre(anciennes: list[tuple], nouvelles: list[tuple]) -> dict:
    anc_par_sra: dict[str, list[tuple]] = {}
    for r in anciennes:
        anc_par_sra.setdefault(r[1], []).append(r)
    nouv_par_sra: dict[str, list[tuple]] = {}
    for r in nouvelles:
        nouv_par_sra.setdefault(r[1], []).append(r)

    sras_anc, sras_nouv = set(anc_par_sra), set(nouv_par_sra)
    ajouts = [r for sra in sorted(sras_nouv - sras_anc) for r in nouv_par_sra[sra]]
    suppressions = [r for sra in sorted(sras_anc - sras_nouv) for r in anc_par_sra[sra]]
    deplacements, modifies, doublons, doublons_nouveaux = [], [], [], []

    for sra in sorted(sras_anc & sras_nouv):
        anc_rows, nouv_rows = anc_par_sra[sra], nouv_par_sra[sra]
        if len(nouv_rows) > 1:
            clades_doublon = sorted(r[0] for r in nouv_rows)
            doublons.append((sra, clades_doublon))
            # un doublon deja present a l'ancienne revision, inchange, n'est pas une DERIVE
            # depuis cette revision : seul un doublon NOUVEAU (ou dont les clades ont change)
            # compte dans `delta_est_vide`.
            if len(anc_rows) <= 1 or sorted(r[0] for r in anc_rows) != clades_doublon:
                doublons_nouveaux.append((sra, clades_doublon))
        anc_clades, nouv_clades = {r[0] for r in anc_rows}, {r[0] for r in nouv_rows}
        if anc_clades != nouv_clades and len(anc_rows) == 1 and len(nouv_rows) == 1:
            deplacements.append((sra, anc_rows[0][0], nouv_rows[0][0]))
        else:
            for ar in anc_rows:
                for nr in nouv_rows:
                    if ar[0] == nr[0] and tuple(ar[2:]) != tuple(nr[2:]):
                        modifies.append((ar[0], sra))

    clades_anc, clades_nouv = {r[0] for r in anciennes}, {r[0] for r in nouvelles}
    return {
        "ajouts": ajouts, "suppressions": suppressions, "deplacements": deplacements,
        "modifies": modifies, "doublons": doublons, "doublons_nouveaux": doublons_nouveaux,
        "clades_crees": sorted(clades_nouv - clades_anc),
        "clades_supprimes": sorted(clades_anc - clades_nouv),
        "vides_avant": sum(1 for r in anciennes if r[2] == "vide"),
        "vides_apres": sum(1 for r in nouvelles if r[2] == "vide"),
    }


def delta_est_vide(delta: dict) -> bool:
    return not (
        delta["ajouts"] or delta["suppressions"] or delta["deplacements"] or delta["modifies"]
        or delta["doublons_nouveaux"] or delta["clades_crees"] or delta["clades_supprimes"]
    )


# --------------------------------------------------------------------------- scan : jeu_fichiers / fichier

def scanner_jeu_fichiers(racine: Path, store: dict) -> dict:
    debut = time.monotonic()
    fichiers = store.get("fichiers") or []
    lignes = []
    for rel in fichiers:
        chemin = racine / rel
        if chemin.is_file():
            st = chemin.stat()
            lignes.append((rel, _sha256_fichier(chemin), str(st.st_size), str(int(st.st_mtime)), "present"))
        else:
            lignes.append((rel, "-", "-", "-", "absent"))
    lignes.sort(key=lambda r: r[0])
    src = "\n".join(f"{r[0]}\t{r[1]}" for r in lignes if r[4] == "present")
    return {
        "header": ["chemin", "sha256", "taille", "mtime", "etat"],
        "lignes": lignes,
        "compte": {"fichiers": len(fichiers), "absents": sum(1 for r in lignes if r[4] == "absent")},
        "condensats": {"contenu": hashlib.sha256(src.encode("utf-8", "surrogateescape")).hexdigest()[:12]},
        "duree_s": time.monotonic() - debut,
    }


def scanner_fichier(racine: Path, store: dict) -> dict:
    debut = time.monotonic()
    if not racine.is_file():
        return {
            "header": ["chemin", "sha256", "taille", "mtime", "etat"],
            "lignes": [(racine.name, "-", "-", "-", "absent")],
            "compte": {"absent": True},
            "condensats": {"contenu": "0" * 12},
            "duree_s": 0.0,
        }
    st = racine.stat()
    sha = _sha256_fichier(racine)
    return {
        "header": ["chemin", "sha256", "taille", "mtime", "etat"],
        "lignes": [(racine.name, sha, str(st.st_size), str(int(st.st_mtime)), "present")],
        "compte": {"taille": st.st_size},
        "condensats": {"contenu": sha[:12]},
        "duree_s": time.monotonic() - debut,
    }


def calculer_delta_fichiers(anciennes: list[tuple], nouvelles: list[tuple]) -> dict:
    anc = {r[0]: r for r in anciennes}
    nouv = {r[0]: r for r in nouvelles}
    modifies = sorted(c for c in (set(anc) & set(nouv)) if anc[c][1] != nouv[c][1])
    return {
        "ajouts": sorted(set(nouv) - set(anc)),
        "suppressions": sorted(set(anc) - set(nouv)),
        "modifies": modifies,
    }


def delta_fichiers_est_vide(delta: dict) -> bool:
    return not (delta["ajouts"] or delta["suppressions"] or delta["modifies"])


# --------------------------------------------------------------------------- scan : git

def scanner_git(racine: Path, store: dict) -> dict:
    sous_arbre = store.get("sous_arbre")
    tete = subprocess.run(
        ["git", "-C", str(racine), "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    cible = ["--", sous_arbre] if sous_arbre else []
    statut = subprocess.run(
        ["git", "-C", str(racine), "status", "--porcelain", *cible],
        capture_output=True, text=True, check=True,
    ).stdout
    dirty = bool(statut.strip())

    n_version = None
    changelog_rel = store.get("changelog")
    if changelog_rel:
        chemin_changelog = racine / changelog_rel
        if chemin_changelog.is_file():
            for ligne in chemin_changelog.read_text(encoding="utf-8", errors="replace").splitlines():
                m = re.match(r"^##\s+v(\d+)", ligne.strip())
                if m:
                    n_version = int(m.group(1))
                    break

    version = f"v{n_version}-g{tete}" if n_version is not None else f"g{tete}"
    if dirty:
        version += "+dirty"
    return {"version": version, "head": tete, "dirty": dirty, "n_version": n_version}


SCANNERS = {
    "arbre_souches": scanner_arbre_souches,
    "jeu_fichiers": scanner_jeu_fichiers,
    "fichier": scanner_fichier,
}


def construire_version(type_store: str, resultat: dict) -> str:
    if type_store == "arbre_souches":
        c, cond = resultat["compte"], resultat["condensats"]
        return f"{_aujourdhui()}-{c['clades']}c-{c['exploitables']}s-{cond['placement']}{cond['contenu']}"
    if type_store == "jeu_fichiers":
        c = resultat["compte"]
        return f"{_aujourdhui()}-{c['fichiers']}f-{resultat['condensats']['contenu']}"
    if type_store == "fichier":
        return f"{_aujourdhui()}-{resultat['condensats']['contenu']}"
    if type_store == "git":
        return resultat["version"]
    raise BddError(f"type inconnu : {type_store}")


# --------------------------------------------------------------------------- persistance : version / manifeste / journal

def lire_version_json(meta: Path) -> dict | None:
    chemin = meta / "version.json"
    if not chemin.is_file():
        return None
    return json.loads(chemin.read_text(encoding="utf-8"))


def ecrire_version_json(meta: Path, store_id: str, store: dict, resultat: dict, version: str,
                          *, revision: int, sentinelle: dict, duree_s: float) -> dict:
    doc = {
        "schema": 1, "store": store_id, "type": store["type"],
        "revision": revision, "version": version, "date": _aujourdhui(),
        "compte": resultat.get("compte", {}), "condensats": resultat.get("condensats", {}),
        "ecrit_le": _maintenant_iso(), "duree_scan_s": round(duree_s, 3),
        "sentinelle": sentinelle,
    }
    if "ref" in store:
        doc["ref"] = store["ref"]
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "version.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return doc


def ecrire_manifeste(meta: Path, revision: int, resultat: dict) -> None:
    dossier = meta / "manifests"
    dossier.mkdir(parents=True, exist_ok=True)
    with gzip.open(dossier / f"r{revision}.tsv.gz", "wt", encoding="utf-8", newline="") as f:
        ecrivain = csv.writer(f, delimiter="\t")
        ecrivain.writerow(resultat["header"])
        ecrivain.writerows(resultat["lignes"])


def lire_manifeste(meta: Path, revision: int) -> tuple[list[str], list[tuple]]:
    chemin = meta / "manifests" / f"r{revision}.tsv.gz"
    if not chemin.is_file():
        raise BddError(f"manifeste introuvable : {chemin}")
    with gzip.open(chemin, "rt", encoding="utf-8", newline="") as f:
        lecteur = csv.reader(f, delimiter="\t")
        header = next(lecteur)
        lignes = [tuple(r) for r in lecteur]
    return header, lignes


def ecrire_sentinelle_cache(meta: Path, sentinelle: dict) -> None:
    dossier = meta / "cache"
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / "sentinelle.json").write_text(json.dumps(sentinelle, ensure_ascii=False), encoding="utf-8")


def journal_ajouter(meta: Path, entree: dict) -> None:
    meta.mkdir(parents=True, exist_ok=True)
    with (meta / "journal.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(entree, ensure_ascii=False) + "\n")


def journal_lire(meta: Path) -> list[dict]:
    chemin = meta / "journal.jsonl"
    if not chemin.is_file():
        return []
    return [json.loads(l) for l in chemin.read_text(encoding="utf-8").splitlines() if l.strip()]


def _dernier_evenement_apres(meta: Path, apres_ts: str) -> dict | None:
    dernier = None
    for entree in journal_lire(meta):
        if entree.get("ts", "") > apres_ts:
            dernier = entree
    return dernier


# --------------------------------------------------------------------------- retro-compatibilite (AA.6)

def indexer_anterieures(racine: Path, store: dict) -> list[dict]:
    """Sauvegardes suffixees anterieures au skill (>60 conventions differentes) : jamais touchees,
    indexees une fois a l'`init` pour que le journal en garde la memoire (AA.6)."""
    motifs = list(store.get("exclusions") or [])
    if store["type"] == "fichier":
        base_scan = racine.parent
        motifs = motifs or [racine.name + ".*", racine.name + "_bak*"]
    else:
        base_scan = racine
    if not motifs:
        return []
    resultats = []
    try:
        entrees = list(os.scandir(base_scan))
    except OSError:
        return []
    for e in entrees:
        if e.name == NOM_META:
            continue
        if e.is_dir(follow_symlinks=False):
            motif = _match_glob_any(e.name, motifs, pour_dossier=True)
            if motif:
                n, taille = 0, 0
                for _r, _d, fs in os.walk(e.path):
                    for fn in fs:
                        n += 1
                        try:
                            taille += os.path.getsize(os.path.join(_r, fn))
                        except OSError:
                            pass
                resultats.append({"dossier": e.name, "n_fichiers": n, "taille_totale": taille, "convention": motif})
            continue
        if store["type"] == "fichier" and e.name == racine.name:
            continue
        motif = _match_glob_any(e.name, motifs)
        if motif and e.is_file():
            st = e.stat()
            resultats.append({
                "fichier": e.name, "taille": st.st_size, "mtime": int(st.st_mtime),
                "sha12": _sha256_fichier(Path(e.path))[:12], "convention": motif,
            })
    return resultats


def proposer_reconstitution(racine: Path, store: dict) -> list[str]:
    motifs = ["_flatten_*_undo_log.tsv", "*.bak_*", "*.pkl.bak_*"]
    trouves = []
    try:
        for e in os.scandir(racine):
            if e.is_file() and any(fnmatch.fnmatch(e.name, m) for m in motifs):
                trouves.append((e.stat().st_mtime, e.path))
    except OSError:
        pass
    trouves.sort(reverse=True)
    return [f"{p} (mtime {datetime.fromtimestamp(m):%Y-%m-%d %H:%M})" for m, p in trouves[:5]]


# --------------------------------------------------------------------------- coordination (agentctl / runsafe)

def estimer_taille(store: dict, racine: Path, meta: Path | None) -> int:
    if store["type"] in ("jeu_fichiers", "fichier", "git"):
        return len(store.get("fichiers", [1])) or 1
    if meta is not None and (meta / "version.json").is_file():
        try:
            doc = json.loads((meta / "version.json").read_text(encoding="utf-8"))
            return int(doc.get("compte", {}).get("souches", 0)) or 1
        except (OSError, ValueError):
            pass
    plate = bool(store.get("plate"))
    try:
        top = list(os.scandir(racine))
    except OSError:
        return 0
    if plate:
        return len(top)
    dirs = [e for e in top if e.is_dir(follow_symlinks=False) and e.name != NOM_META]
    if not dirs:
        return 0
    echantillon = dirs[:: max(len(dirs) // 5, 1)][:5]  # jusqu'a 5 clades repartis, pas seulement le premier
    tailles = []
    for d in echantillon:
        try:
            tailles.append(len(list(os.scandir(d.path))))
        except OSError:
            pass
    n_echantillon = round(sum(tailles) / len(tailles)) if tailles else 1
    return len(dirs) * max(n_echantillon, 1)


def coordonner(store_id: str, verbe: str, estimation: int, sans_coord: bool) -> str | None:
    if sans_coord or estimation < SEUIL_COORD:
        return None
    try:
        res = subprocess.run(
            ["agentctl", "task", "start", "--title", f"bdd {verbe} {store_id}", "--ram-gb", "2", "--cpu", "4"],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        print("agentctl indisponible : scan lance sans coordination.", file=sys.stderr)
        return None
    m = re.search(r"tache (\S+) enregistree", res.stdout)
    if not m:
        print(res.stdout.strip(), file=sys.stderr)
        raise BddError(
            "garde-fou ressources partagees : tache non enregistree (machine chargee) — "
            "relancer plus tard, ou --sans-coord en connaissance de cause."
        )
    return m.group(1)


def cloturer_coordination(tid: str | None, ok: bool, note: str = "") -> None:
    if tid is None:
        return
    args = ["agentctl", "task", "done" if ok else "fail", tid]
    if note:
        args += ["--note", note]
    try:
        subprocess.run(args, capture_output=True, text=True)
    except FileNotFoundError:
        pass


def _sous_runsafe_si_necessaire(args: argparse.Namespace, store_id: str, estimation: int) -> bool:
    if getattr(args, "interne_runsafe", False):
        return True
    if args.sans_coord or estimation < SEUIL_COORD:
        return False
    cmd = [
        "runsafe", "--cpu", "4", "--ram-gb", "2", "--name", f"bdd-{store_id}", "--",
        sys.executable, str(Path(__file__).resolve()), *sys.argv[1:], "--interne-runsafe",
    ]
    try:
        resultat = subprocess.run(cmd)
    except FileNotFoundError:
        print("runsafe indisponible : scan lance hors cgroup.", file=sys.stderr)
        return False
    sys.exit(resultat.returncode)


# --------------------------------------------------------------------------- abonnes (piste AA / P1.88)


def derniere_citation_projet(root: Path) -> tuple[str | None, str | None]:
    """(date_iso, ligne_citation) la plus recente d'un projet consommateur : l'etat des
    decouvertes fait foi s'il porte une ligne `**Donnees :**` exploitable (reecrite en
    entier a chaque `/etat update`, donc toujours a jour) ; a defaut, la derniere ligne
    `donnees :` du cahier (append-only : on ne veut que la plus recente).

    Implementation canonique — dupliquee (et non importee) dans `session_donnees.py` qui
    tourne au hook SessionStart de toute session sur la machine : un import croise aurait
    fait dependre un chemin chaud et a fort rayon d'impact d'une commande ajoutee ici pour
    `bdd abonnes` (piste P1.88, `lineage_navigator`). Garder les deux copies synchronisees
    si l'une change."""
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


def version_actuelle_store(store_id: str, store: dict, bases: dict) -> str | None:
    """Version REFERENCE d'un store (dernier `bump`/`init`, ou scan direct pour `git`) —
    pas un live-scan avec detection `+dirty` (c'est le role de `stamp`/`check`) : suffit a
    comparer a une citation figee par un consommateur."""
    if store["type"] == "git":
        racine = resoudre_racine(store, bases)
        return scanner_git(racine, store)["version"]
    meta = resoudre_meta(store_id, store, bases)
    doc = lire_version_json(meta)
    return doc["version"] if doc else None


def ecritures_journal_depuis(store_id: str, store: dict, bases: dict, date_citation: str | None) -> int:
    """Nombre d'evenements `ecriture` journalises strictement apres le JOUR de la citation
    (granularite jour) : un rappel informatif, pas une preuve de reproductibilite."""
    if not date_citation or store["type"] == "git":
        return 0
    meta = resoudre_meta(store_id, store, bases)
    n = 0
    for entree in journal_lire(meta):
        if entree.get("type") != "ecriture":
            continue
        if entree.get("ts", "")[:10] > date_citation:
            n += 1
    return n


def cmd_abonnes(args: argparse.Namespace) -> int:
    registre, bases = charger_registre(args.registre)
    store = obtenir_store(registre, args.store)
    abonnes = store.get("abonnes") or []
    if not abonnes:
        print(f"{args.store} : aucun abonne declare dans le registre.")
        return 0

    version_ref = None if store.get("etat") == "à créer" else version_actuelle_store(args.store, store, bases)
    resultats = []
    anomalies = 0
    for ab in abonnes:
        projet = ab.get("projet", "?")
        racine_projet = Path(ab.get("racine", "")).expanduser()
        date_citation, ligne = derniere_citation_projet(racine_projet) if racine_projet.is_dir() else (None, None)
        cite = None
        if ligne:
            m = re.search(rf"{re.escape(args.store)}@([^\s;,]+)", ligne)
            cite = m.group(1) if m else None
        n_ecritures = 0
        if cite is None:
            statut = "aucune_citation"
            anomalies += 1
        elif version_ref is not None and cite != version_ref:
            n_ecritures = ecritures_journal_depuis(args.store, store, bases, date_citation)
            statut = "derive"
            anomalies += 1
        else:
            statut = "a_jour"
        resultats.append({
            "projet": projet, "racine": str(racine_projet), "statut": statut,
            "citation": cite, "date_citation": date_citation, "ecritures_depuis": n_ecritures,
        })

    if args.json:
        print(json.dumps({
            "store": args.store, "version_reference": version_ref, "abonnes": resultats,
        }, ensure_ascii=False))
    else:
        print(f"{args.store} (reference {version_ref}) : {len(abonnes)} abonne(s)")
        for r in resultats:
            if r["statut"] == "a_jour":
                print(f"  {r['projet']:<20} A JOUR ({r['citation']})")
            elif r["statut"] == "aucune_citation":
                print(f"  {r['projet']:<20} AUCUNE CITATION (jamais cite dans etat/cahier)")
            else:
                suffixe = f" : {r['ecritures_depuis']} ecriture(s) journalisee(s) depuis" if r["ecritures_depuis"] else ""
                print(f"  {r['projet']:<20} DERIVE (cite {r['citation']} du {r['date_citation']} ; "
                      f"reference {version_ref}{suffixe})")
    return 1 if anomalies else 0


# --------------------------------------------------------------------------- miroir

def miroir_copier(store_id: str, meta: Path) -> Path:
    cible = MIROIR_RACINE / store_id
    cible.mkdir(parents=True, exist_ok=True)
    for nom in ("version.json", "journal.jsonl"):
        src = meta / nom
        if src.is_file():
            shutil.copy2(src, cible / nom)
    return cible


# --------------------------------------------------------------------------- affichage

def afficher_delta(delta: dict, type_store: str) -> None:
    if type_store == "arbre_souches":
        if delta["ajouts"]:
            print(f"  ajouts : {len(delta['ajouts'])}")
        if delta["suppressions"]:
            print(f"  suppressions : {len(delta['suppressions'])}")
        if delta["deplacements"]:
            groupes: dict[tuple, int] = {}
            for sra, ac, nc in delta["deplacements"]:
                groupes[(ac, nc)] = groupes.get((ac, nc), 0) + 1
            for (ac, nc), n in sorted(groupes.items()):
                print(f"  deplacement : {ac} -> {nc} ({n})")
        if delta["modifies"]:
            print(f"  modifies : {len(delta['modifies'])}")
        if delta["doublons"]:
            print(f"  doublons : {len(delta['doublons'])}")
        if delta["clades_crees"]:
            print(f"  clades crees : {', '.join(delta['clades_crees'])}")
        if delta["clades_supprimes"]:
            print(f"  clades supprimes : {', '.join(delta['clades_supprimes'])}")
        if delta["vides_avant"] != delta["vides_apres"]:
            print(f"  vides : {delta['vides_avant']} -> {delta['vides_apres']}")
    else:
        if delta["ajouts"]:
            print(f"  ajouts : {', '.join(delta['ajouts'])}")
        if delta["suppressions"]:
            print(f"  suppressions : {', '.join(delta['suppressions'])}")
        if delta["modifies"]:
            print(f"  modifies : {', '.join(delta['modifies'])}")


def _delta_json(delta: dict) -> dict:
    return delta


def _calculer_delta(type_store: str, anciennes: list[tuple], nouvelles: list[tuple]) -> tuple[dict, bool]:
    if type_store == "arbre_souches":
        delta = calculer_delta_arbre(anciennes, nouvelles)
        return delta, delta_est_vide(delta)
    delta = calculer_delta_fichiers(anciennes, nouvelles)
    return delta, delta_fichiers_est_vide(delta)


def _scanner_avec_coordination(args: argparse.Namespace, store_id: str, store: dict, racine: Path,
                                 meta: Path | None, verbe: str) -> dict:
    estimation = estimer_taille(store, racine, meta)
    if _sous_runsafe_si_necessaire(args, store_id, estimation):
        sys.exit(0)  # pragma: no cover — le sous-processus runsafe a deja tout fait
    tid = coordonner(store_id, verbe, estimation, args.sans_coord)
    try:
        resultat = SCANNERS[store["type"]](racine, store)
    except Exception:
        cloturer_coordination(tid, ok=False, note="exception pendant le scan")
        raise
    cloturer_coordination(tid, ok=True, note=f"{resultat.get('duree_s', 0):.1f}s")
    return resultat


# --------------------------------------------------------------------------- commandes CLI

def cmd_init(args: argparse.Namespace) -> int:
    registre, bases = charger_registre(args.registre)
    store = obtenir_store(registre, args.store)
    if store.get("etat") == "à créer":
        print(f"{args.store} : etat 'a creer', rien a initialiser.")
        return 0
    if store["type"] == "git":
        print(f"{args.store} : type git, delegue a git — 'bdd stamp {args.store}' suffit.")
        return 0

    racine = resoudre_racine(store, bases)
    meta = resoudre_meta(args.store, store, bases)
    if (meta / "version.json").is_file():
        doc = lire_version_json(meta)
        assert doc is not None
        print(f"{args.store} : deja initialise ({doc['version']}). Utiliser 'bdd bump'.")
        return 1

    resultat = _scanner_avec_coordination(args, args.store, store, racine, None, "init")
    version = construire_version(store["type"], resultat)
    anterieures = indexer_anterieures(racine, store)

    if not args.write:
        print(f"{args.store} : init (dry-run) -> r0 {version} ({resultat.get('duree_s', 0):.2f}s scan)")
        if anterieures:
            print(f"  {len(anterieures)} version(s) anterieure(s) non numerotee(s) trouvee(s) (--write pour indexer).")
        return 0

    sentinelle = calculer_sentinelle(_racine_sentinelle(store, racine))
    doc = ecrire_version_json(meta, args.store, store, resultat, version, revision=0,
                                sentinelle=sentinelle, duree_s=resultat.get("duree_s", 0))
    ecrire_manifeste(meta, 0, resultat)
    ecrire_sentinelle_cache(meta, sentinelle)
    entree = {
        "id": "r0", "ts": _maintenant_iso(), "store": args.store, "type": "init",
        "outil": "bdd.py", "argv": sys.argv, "motif": f"etat constate le {_aujourdhui()}, aucun historique revendique",
        "operateur": _detecter_operateur(), "session": _detecter_session(),
        "apres": {"version": version, "compte": resultat.get("compte", {})},
        "anterieures": anterieures,
    }
    journal_ajouter(meta, entree)
    miroir_copier(args.store, meta)

    if args.json:
        print(json.dumps(doc, ensure_ascii=False))
    else:
        print(f"{args.store} : initialise r0 {version} ({resultat.get('duree_s', 0):.2f}s scan)")
        if anterieures:
            print(f"  {len(anterieures)} version(s) anterieure(s) non numerotee(s) indexee(s).")
    return 0


def cmd_stamp(args: argparse.Namespace) -> int:
    registre, bases = charger_registre(args.registre)
    store = obtenir_store(registre, args.store)
    if store.get("etat") == "à créer":
        print(f"{args.store}@non-versionnee")
        return 0

    racine = resoudre_racine(store, bases)
    if store["type"] == "git":
        resultat = scanner_git(racine, store)
        print(f"{args.store}@{resultat['version']} (acces {_maintenant_lisible()})")
        if args.json:
            print(json.dumps({"store": args.store, **resultat}, ensure_ascii=False))
        return 0

    meta = resoudre_meta(args.store, store, bases)
    if args.verifier:
        return cmd_check(args)

    doc = lire_version_json(meta)
    if doc is None:
        print(f"{args.store}@non-versionnee")
        return 0

    sentinelle_live = calculer_sentinelle(_racine_sentinelle(store, racine))
    sentinelle_ref = doc.get("sentinelle") or {}
    propre = sentinelle_live.get("sha_entrees") == sentinelle_ref.get("sha_entrees")
    ts = _maintenant_lisible()
    if propre:
        citation = f"{args.store}@{doc['version']} (acces {ts})"
    else:
        citation = (f"{args.store}@{doc['version']}+dirty (acces {ts} ; "
                    f"DERIVE depuis le check du {doc.get('date')}, lancer bdd check)")
    print(citation)
    if args.json:
        print(json.dumps({
            "store": args.store, "version": doc["version"], "propre": propre,
            "revision": doc["revision"], "acces": ts,
        }, ensure_ascii=False))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    registre, bases = charger_registre(args.registre)
    store = obtenir_store(registre, args.store)
    if store["type"] == "git":
        print(f"{args.store} : type git (delegation) — 'bdd stamp' suffit, rien a verifier.")
        return 0

    racine = resoudre_racine(store, bases)
    meta = resoudre_meta(args.store, store, bases)
    doc = lire_version_json(meta)
    if doc is None:
        print(f"{args.store} : non initialise. Lancer 'bdd init {args.store} --write' d'abord.")
        return 1

    resultat = _scanner_avec_coordination(args, args.store, store, racine, meta, "check")
    _, anciennes = lire_manifeste(meta, doc["revision"])
    delta, vide = _calculer_delta(store["type"], anciennes, resultat["lignes"])
    version_actuelle = construire_version(store["type"], resultat)

    if vide:
        print(f"{args.store} : A JOUR (r{doc['revision']}, {doc['version']})")
        statut = "a_jour"
    else:
        print(f"{args.store} : DERIVE depuis r{doc['revision']} ({doc['version']})")
        afficher_delta(delta, store["type"])
        evenement = _dernier_evenement_apres(meta, doc.get("ecrit_le", ""))
        if evenement:
            print(f"  journalise ? OUI ({evenement.get('type')} par {evenement.get('outil', '?')} "
                  f"le {str(evenement.get('ts', '?'))[:10]})")
        else:
            print("  journalise ? NON")
            for suggestion in proposer_reconstitution(racine, store):
                print(f"  reconstitution proposee : {suggestion}")
        statut = "derive"

    if args.json:
        print(json.dumps({
            "store": args.store, "statut": statut, "revision_reference": doc["revision"],
            "version_reference": doc["version"], "version_actuelle": version_actuelle,
            "delta": _delta_json(delta),
        }, ensure_ascii=False))

    if getattr(args, "regulariser", False) and not vide:
        if not args.write:
            print("  (dry-run --regulariser : ajouter --write pour creer la revision)")
            return 2
        nouvelle_revision = doc["revision"] + 1
        sentinelle = calculer_sentinelle(_racine_sentinelle(store, racine))
        ecrire_version_json(meta, args.store, store, resultat, version_actuelle, revision=nouvelle_revision,
                              sentinelle=sentinelle, duree_s=resultat.get("duree_s", 0))
        ecrire_manifeste(meta, nouvelle_revision, resultat)
        ecrire_sentinelle_cache(meta, sentinelle)
        journal_ajouter(meta, {
            "id": f"r{nouvelle_revision}", "ts": _maintenant_iso(), "store": args.store, "type": "regularisation",
            "outil": args.outil or "bdd.py", "motif": args.motif,
            "undo": {"type": "undo_log", "chemin": args.undo_log} if args.undo_log else None,
            "operateur": _detecter_operateur(), "attribution": {"presumee": True},
            "delta": _delta_json(delta),
        })
        miroir_copier(args.store, meta)
        print(f"  regularise en r{nouvelle_revision} ({version_actuelle})")
        return 0

    return 0 if vide else 2


def cmd_bump(args: argparse.Namespace) -> int:
    registre, bases = charger_registre(args.registre)
    store = obtenir_store(registre, args.store)
    if store["type"] == "git":
        print(f"{args.store} : type git (delegation), rien a bumper — c'est 'git commit' qui fait foi.")
        return 0
    if store["type"] == "arbre_souches" and not args.sans_undo and not args.undo_log:
        print("bump sur arbre_souches exige --undo-log <fichier> (ou --sans-undo avec --motif explicite).")
        return 1

    racine = resoudre_racine(store, bases)
    meta = resoudre_meta(args.store, store, bases)
    doc = lire_version_json(meta)
    if doc is None:
        print(f"{args.store} : non initialise. Lancer 'bdd init {args.store} --write' d'abord.")
        return 1

    resultat = _scanner_avec_coordination(args, args.store, store, racine, meta, "bump")
    _, anciennes = lire_manifeste(meta, doc["revision"])
    delta, vide = _calculer_delta(store["type"], anciennes, resultat["lignes"])

    if vide:
        print(f"{args.store} : aucun changement detecte, bump refuse (code 3).")
        return 3

    version = construire_version(store["type"], resultat)
    if not args.write:
        print(f"{args.store} : bump propose r{doc['revision']} -> r{doc['revision'] + 1} ({version})")
        afficher_delta(delta, store["type"])
        print("  (dry-run : ajouter --write pour ecrire)")
        return 0

    nouvelle_revision = doc["revision"] + 1
    sentinelle = calculer_sentinelle(_racine_sentinelle(store, racine))
    ecrire_version_json(meta, args.store, store, resultat, version, revision=nouvelle_revision,
                          sentinelle=sentinelle, duree_s=resultat.get("duree_s", 0))
    ecrire_manifeste(meta, nouvelle_revision, resultat)
    ecrire_sentinelle_cache(meta, sentinelle)
    journal_ajouter(meta, {
        "id": f"r{nouvelle_revision}", "ts": _maintenant_iso(), "store": args.store, "type": "ecriture",
        "outil": args.outil, "argv": sys.argv, "motif": args.motif, "piste": args.piste,
        "operateur": _detecter_operateur(), "session": _detecter_session(),
        "delta": _delta_json(delta),
        "undo": {"type": "undo_log", "chemin": args.undo_log} if args.undo_log else None,
        "sauvegarde": args.sauvegarde,
    })
    miroir_copier(args.store, meta)
    print(f"{args.store} : bump r{nouvelle_revision} ({version})")
    n_abonnes = len(store.get("abonnes") or [])
    if n_abonnes:
        print(f"  {n_abonnes} abonne(s) declare(s) pour {args.store} : verifier avec 'bdd abonnes {args.store}'.")
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    registre, bases = charger_registre(args.registre)
    store = obtenir_store(registre, args.store)
    if store["type"] == "git":
        print(f"{args.store} : type git (delegation) — voir 'git log' dans le depot.")
        return 0
    meta = resoudre_meta(args.store, store, bases)
    entrees = journal_lire(meta)
    if not entrees:
        print(f"{args.store} : aucun journal (pas encore initialise).")
        return 0
    if args.n:
        entrees = entrees[-args.n:]
    if args.json:
        print(json.dumps(entrees, ensure_ascii=False))
        return 0
    for e in entrees:
        print(f"{e.get('id', '?'):>6}  {str(e.get('ts', '?'))[:19]}  {e.get('type', '?'):<20} "
              f"{e.get('outil', '-') or '-':<28} {e.get('motif', '-') or '-'}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    registre, bases = charger_registre(args.registre)
    store = obtenir_store(registre, args.store)
    meta = resoudre_meta(args.store, store, bases)
    ra = int(str(args.rev_a).lstrip("r"))
    _, lignes_a = lire_manifeste(meta, ra)
    if args.rev_b == "actuel":
        racine = resoudre_racine(store, bases)
        lignes_b = SCANNERS[store["type"]](racine, store)["lignes"]
        label_b = "actuel"
    else:
        rb = int(str(args.rev_b).lstrip("r"))
        _, lignes_b = lire_manifeste(meta, rb)
        label_b = f"r{rb}"
    delta, _ = _calculer_delta(store["type"], lignes_a, lignes_b)
    if args.json:
        print(json.dumps(_delta_json(delta), ensure_ascii=False))
    else:
        print(f"{args.store} : r{ra} -> {label_b}")
        afficher_delta(delta, store["type"])
    return 0


def cmd_miroir(args: argparse.Namespace) -> int:
    registre, bases = charger_registre(args.registre)
    store = obtenir_store(registre, args.store)
    if store["type"] == "git":
        print(f"{args.store} : type git (delegation), rien a miroiter.")
        return 0
    meta = resoudre_meta(args.store, store, bases)
    cible = miroir_copier(args.store, meta)
    print(f"{args.store} : miroite vers {cible}")
    if args.commit:
        rels = [str((cible / n).relative_to(ENV_RACINE)) for n in ("version.json", "journal.jsonl")
                if (cible / n).is_file()]
        subprocess.run(["git", "-C", str(ENV_RACINE), "add", *rels], check=True)
        doc = lire_version_json(meta) or {}
        msg = f"bdd miroir {args.store} r{doc.get('revision', '?')} {doc.get('version', '')}"
        res = subprocess.run(["git", "-C", str(ENV_RACINE), "commit", "-m", msg])
        if res.returncode != 0:
            print("  rien a commiter (miroir deja a jour).")
    return 0


# --------------------------------------------------------------------------- CLI

def construire_parseur() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bdd", description="Versionnage des bases internes (registre AA0).")
    p.add_argument("--registre", default=None)
    sous = p.add_subparsers(dest="commande", required=True)

    def _commun(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("store")
        sp.add_argument("--json", action="store_true")

    def _options_scan(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--sans-coord", action="store_true")
        sp.add_argument("--interne-runsafe", action="store_true", help=argparse.SUPPRESS)

    sp = sous.add_parser("init")
    _commun(sp)
    sp.add_argument("--write", action="store_true")
    _options_scan(sp)
    sp.set_defaults(func=cmd_init)

    sp = sous.add_parser("stamp")
    _commun(sp)
    sp.add_argument("--verifier", action="store_true")
    _options_scan(sp)
    sp.set_defaults(func=cmd_stamp)

    sp = sous.add_parser("check")
    _commun(sp)
    sp.add_argument("--regulariser", action="store_true")
    sp.add_argument("--motif")
    sp.add_argument("--outil")
    sp.add_argument("--undo-log")
    sp.add_argument("--write", action="store_true")
    _options_scan(sp)
    sp.set_defaults(func=cmd_check)

    sp = sous.add_parser("bump")
    _commun(sp)
    sp.add_argument("--outil", required=True)
    sp.add_argument("--motif", required=True)
    sp.add_argument("--piste")
    sp.add_argument("--undo-log")
    sp.add_argument("--sauvegarde")
    sp.add_argument("--sans-undo", action="store_true")
    sp.add_argument("--write", action="store_true")
    _options_scan(sp)
    sp.set_defaults(func=cmd_bump)

    sp = sous.add_parser("log")
    _commun(sp)
    sp.add_argument("-n", type=int, default=None)
    sp.set_defaults(func=cmd_log)

    sp = sous.add_parser("diff")
    _commun(sp)
    sp.add_argument("rev_a")
    sp.add_argument("rev_b", nargs="?", default="actuel")
    sp.set_defaults(func=cmd_diff)

    sp = sous.add_parser("miroir")
    _commun(sp)
    sp.add_argument("--commit", action="store_true")
    sp.set_defaults(func=cmd_miroir)

    sp = sous.add_parser("abonnes", help="verifie la fraicheur de citation des projets abonnes a ce store")
    _commun(sp)
    sp.set_defaults(func=cmd_abonnes)

    return p


def main(argv: list[str] | None = None) -> int:
    args = construire_parseur().parse_args(argv)
    try:
        return args.func(args) or 0
    except BddError as exc:
        print(f"erreur : {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
