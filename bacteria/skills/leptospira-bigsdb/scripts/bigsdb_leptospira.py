#!/usr/bin/env python3
"""
Objet : pont de lecture vers BIGSdb Pasteur (bases pubmlst_leptospira_isolates /
  pubmlst_leptospira_seqdef) : filtrer des isolats par métadonnée de provenance, exporter une
  table de métadonnées fidèle, rapporter la complétude réelle par champ, et télécharger les
  génomes assemblés (FASTA) d'un lot filtré.
Entrées : filtres `champ=valeur` (égalité exacte, insensible à la casse, côté serveur) sur les
  champs de provenance déclarés par `/fields` (clade, species, serogroup, serovar, host,
  country, sample_type, ...), ou aucun filtre pour la base entière.
Sorties : table TSV/JSON de métadonnées brutes, fichiers FASTA par isolat + manifeste TSV,
  rapport de complétude par champ (fractions informatif/total).
Réutilisable : oui si un second genre bascule un jour sur BIGSdb Pasteur — cloner en changeant
  DEFAULT_DB ; à ce jour (2026-09-22) seul Leptospira y est hébergé côté Guyeux group.
Projet : environnement, piste AG1. Origine : mail Alexandre Giraud-Gatineau (Institut Pasteur,
  Unité Biologie des Spirochètes) du 2026-09-18. API mesurée en direct le 2026-09-22, mesures
  consolidées dans ~/.agents/knowledge/leptospira.md (ne pas dupliquer ici).
Date : 2026-09-22.

Piège serveur mesuré (a) : GET /db/{db}/isolates ignore SILENCIEUSEMENT un paramètre de requête
  inconnu et renvoie toute la base (1558 isolats) sans erreur ni avertissement — vérifié en
  direct (`?clade=P2` sur ce endpoint renvoie les 1558 isolats). Ne jamais filtrer par ce
  endpoint. Le filtrage réel passe par POST /isolates/search avec un corps JSON
  `{"field.<nom>": "<valeur>"}`, qui répond HTTP 400 sur un nom de champ inconnu et un ensemble
  vide légitime (HTTP 200, records:0) sur une valeur inconnue d'un champ valide — les deux cas
  vérifiés en direct. `validate_fields` revérifie chaque nom de champ contre `/fields` avant
  l'appel, pour un message d'erreur plus lisible que le 400 brut du serveur. La correspondance
  est une ÉGALITÉ STRICTE (insensible à la casse) : `country=Fran` ne retrouve pas la France,
  contrairement à une recherche par sous-chaîne.

Piège serveur mesuré (b) : sans authentification, l'accès est plafonné aux dépôts soumis au
  plus tard le 2024-12-31 (avertissement embarqué dans la réponse de /db/{db}) — relayé ici sur
  stderr à chaque commande réseau, jamais tu. Un compte Pasteur (demandable à Alex) lève la
  barrière.

Piège de données mesuré : les champs de provenance mélangent des graphies distinctes pour
  « non renseigné » SUR LE MÊME CHAMP (`Unknown`, `unknown`, `Not examined`, `not examined`,
  `Unknow` observés sur `serogroup`/`serovar`/`host`/`sample_type`), et la casse des valeurs
  réelles varie aussi (`human` vs `Human`). La complétude ne se lit donc jamais en comptant les
  valeurs non vides : NON_INFORMATIVE liste les graphies vues, comparées après strip+lower.
  `search`/`genomes` exportent les valeurs BRUTES (fidélité) ; seule `breakdown` calcule une
  complétude.

Piège réseau mesuré (AG1bis, 2026-09-23) : sur un lot de plusieurs centaines d'isolats
  (`search`/`genomes` interrogent un isolat par requête HTTP séquentielle), le serveur BIGSdb
  coupe la connexion sous charge soutenue (`ConnectionError`, `Timeout`, `ChunkedEncodingError`),
  et une panne réseau locale transitoire produit le même symptôme. `_get`/`_post`/`_download`
  retentent désormais 5 fois avec un délai exponentiel (2, 4, 8, 16, 32 s) avant d'abandonner,
  patron porté depuis le premier consommateur réel (`mtbc/leptospira_p1_specificite`,
  `analyses/p2_2_inventory.py`). `search --out fichier.tsv --resume` reprend depuis les lignes
  déjà écrites (colonne `id` en tête) plutôt que de refaire tout le lot ; `genomes` saute tout
  isolat dont le fichier FASTA de destination existe déjà sur disque.

Usage :
    bigsdb_leptospira.py stats
    bigsdb_leptospira.py fields
    bigsdb_leptospira.py breakdown clade serogroup serovar host sample_type country
    bigsdb_leptospira.py search --filter clade=P2 --filter host=human --out p2_human.tsv
    bigsdb_leptospira.py genomes --filter clade=S2 --out-dir genomes_s2/
    bigsdb_leptospira.py isolate 2
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

BASE = "https://bigsdb.pasteur.fr/api"
DEFAULT_DB = "pubmlst_leptospira_isolates"
NON_INFORMATIVE = {"unknown", "unknow", "not examined", "n/a", "na", "none", ""}
SEP = "\t"


class BigsdbError(RuntimeError):
    pass


def _session():
    import requests
    return requests.Session()


def _url(db: str, path: str = "") -> str:
    base = f"{BASE}/db/{db}"
    return f"{base}/{path}" if path else base


def _raise_for(resp) -> None:
    try:
        message = resp.json().get("message", resp.text[:500])
    except ValueError:
        message = resp.text[:500]
    raise BigsdbError(f"HTTP {resp.status_code} sur {resp.url} : {message}")


def _with_retry(fn, *args, attempts: int = 5, base_sleep: float = 2.0, **kwargs):
    """Retry générique sur les seules erreurs transitoires (coupure réseau, timeout) — une
    réponse HTTP reçue (400, 404, 500...) n'est pas retentée, elle est une erreur légitime."""
    import requests
    transient = (requests.exceptions.ConnectionError, requests.exceptions.Timeout,
                 requests.exceptions.ChunkedEncodingError)
    for i in range(attempts):
        try:
            return fn(*args, **kwargs)
        except transient as exc:
            if i == attempts - 1:
                raise
            wait = base_sleep * (2 ** i)
            print(f"  [retry {i + 1}/{attempts}] {exc} -- attente {wait:.0f}s", file=sys.stderr)
            time.sleep(wait)
    raise AssertionError("inatteignable : la dernière tentative relève toujours")


def _get(session, url: str, params: dict | None = None, timeout: int = 60):
    resp = _with_retry(session.get, url, params=params, timeout=timeout)
    if resp.status_code == 404:
        return None
    if not resp.ok:
        _raise_for(resp)
    return resp.json()


def _post(session, url: str, payload: dict, params: dict | None = None, timeout: int = 120):
    resp = _with_retry(session.post, url, json=payload, params=params, timeout=timeout)
    if not resp.ok:
        _raise_for(resp)
    return resp.json()


def _is_informative(value) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() not in NON_INFORMATIVE


def relay_access_warning(session, db: str) -> None:
    """Relais de l'avertissement serveur (piège b) : plafond 2024-12-31 sans authentification."""
    data = _get(session, _url(db))
    message = (data or {}).get("message")
    if message:
        print(f"[BIGSdb] {message}", file=sys.stderr)


def fetch_fields(session, db: str) -> list[dict]:
    return _get(session, _url(db, "fields")) or []


def fetch_total(session, db: str) -> int:
    data = _get(session, _url(db, "isolates"), params={"page_size": 1})
    return int((data or {}).get("records", 0))


def fetch_breakdown(session, db: str, field: str) -> dict:
    data = _get(session, _url(db, f"fields/{field}/breakdown"))
    if data is None:
        raise BigsdbError(f"champ '{field}' sans répartition (breakdown) disponible")
    return data


def validate_fields(session, db: str, names: list[str]) -> None:
    known = {f["name"] for f in fetch_fields(session, db)}
    unknown = [n for n in names if n not in known]
    if unknown:
        raise BigsdbError(
            f"champ(s) inconnu(s) : {', '.join(unknown)} — champs valides : "
            f"{', '.join(sorted(known))}"
        )


def search_isolates(session, db: str, filters: dict, timeout: int = 120) -> list[str]:
    """POST /isolates/search : seul endpoint qui filtre réellement (piège a, cf. docstring)."""
    payload = {f"field.{k}": v for k, v in filters.items()}
    data = _post(session, _url(db, "isolates/search"), payload,
                 params={"return_all": 1}, timeout=timeout)
    return data.get("isolates", [])


def list_all_isolates(session, db: str, timeout: int = 120) -> list[str]:
    data = _get(session, _url(db, "isolates"), params={"return_all": 1}, timeout=timeout)
    return (data or {}).get("isolates", [])


def fetch_isolate(session, db: str, isolate_id: str) -> dict:
    data = _get(session, _url(db, f"isolates/{isolate_id}"))
    if data is None:
        raise BigsdbError(f"isolat {isolate_id} introuvable")
    return data


def _isolate_id_from_url(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def _parse_filters(pairs: list[str]) -> dict:
    filters = {}
    for pair in pairs:
        if "=" not in pair:
            raise BigsdbError(f"filtre mal formé (attendu champ=valeur) : {pair!r}")
        key, value = pair.split("=", 1)
        filters[key.strip()] = value.strip()
    return filters


def _cell(value) -> str:
    return " ".join(str(value).split()) if value is not None else ""


# --- sous-commandes ---------------------------------------------------------

def cmd_stats(_args, session, db) -> None:
    relay_access_warning(session, db)
    total = fetch_total(session, db)
    n_genomes = int((_get(session, _url(db, "genomes"), params={"page_size": 1}) or {})
                     .get("records", 0))
    clade = fetch_breakdown(session, db, "clade")
    print(SEP.join(["item", "valeur"]))
    print(SEP.join(["isolats", str(total)]))
    print(SEP.join(["génomes assemblés", str(n_genomes)]))
    for name, count in sorted(clade.items(), key=lambda kv: -kv[1]):
        print(SEP.join([f"clade {name}", str(count)]))


def cmd_fields(_args, session, db) -> None:
    print(SEP.join(["nom", "type", "requis", "valeurs_autorisées", "commentaire"]))
    for f in fetch_fields(session, db):
        allowed = f.get("allowed_values")
        allowed_s = f"{len(allowed)} valeurs" if allowed and len(allowed) > 8 else \
            ",".join(allowed) if allowed else ""
        print(SEP.join([f["name"], f.get("type", ""), str(f.get("required", False)),
                         allowed_s, _cell(f.get("comments", ""))]))


def cmd_breakdown(args, session, db) -> None:
    relay_access_warning(session, db)
    all_fields = [f["name"] for f in fetch_fields(session, db)]
    names = args.fields or all_fields
    validate_fields(session, db, names)
    total = fetch_total(session, db)
    print(SEP.join(["champ", "valeur", "n"]))
    for name in names:
        breakdown = fetch_breakdown(session, db, name)
        informative = sum(n for v, n in breakdown.items() if _is_informative(v))
        pct = 100 * informative / total if total else 0.0
        print(f"# {name} : {informative}/{total} informatif ({pct:.1f} %)", file=sys.stderr)
        for value, n in sorted(breakdown.items(), key=lambda kv: -kv[1]):
            print(SEP.join([name, value, str(n)]))


def cmd_search(args, session, db) -> None:
    if args.resume and args.format != "tsv":
        raise BigsdbError("--resume n'est supporté qu'avec --format tsv (colonne id en tête)")
    if args.resume and not args.out:
        raise BigsdbError("--resume exige --out (rien à reprendre sur stdout)")

    relay_access_warning(session, db)
    filters = _parse_filters(args.filter)
    if filters:
        validate_fields(session, db, list(filters))
    urls = search_isolates(session, db, filters, timeout=args.timeout)
    print(f"[BIGSdb] {len(urls)} isolat(s) pour le filtre {filters or '(aucun, base entière)'}",
          file=sys.stderr)

    fields = ["id"] + [f["name"] for f in fetch_fields(session, db) if f["name"] != "id"]

    already = set()
    resuming = bool(args.resume and args.out and args.out.exists())
    if resuming:
        with open(args.out) as fh:
            next(fh, None)  # en-tête
            for line in fh:
                iso_id = line.split(SEP, 1)[0]
                if iso_id:
                    already.add(iso_id)
        print(f"[BIGSdb] reprise : {len(already)} isolat(s) déjà écrit(s) dans {args.out}",
              file=sys.stderr)

    handle = open(args.out, "a" if resuming else "w") if args.out else sys.stdout
    n_written = 0
    n_skipped = 0
    try:
        if args.format == "json":
            rows = []
            for i, url in enumerate(urls, 1):
                iso_id = _isolate_id_from_url(url)
                record = fetch_isolate(session, db, iso_id)
                row = dict(record.get("provenance", {}))
                row["id"] = iso_id
                rows.append(row)
                if args.sleep:
                    time.sleep(args.sleep)
                if i % 100 == 0:
                    print(f"  ... {i}/{len(urls)} enregistrements récupérés", file=sys.stderr)
            json.dump(rows, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            n_written = len(rows)
        else:
            if not resuming:
                handle.write(SEP.join(fields) + "\n")
            for i, url in enumerate(urls, 1):
                iso_id = _isolate_id_from_url(url)
                if iso_id in already:
                    n_skipped += 1
                    continue
                record = fetch_isolate(session, db, iso_id)
                row = dict(record.get("provenance", {}))
                row["id"] = iso_id
                handle.write(SEP.join(_cell(row.get(f, "")) for f in fields) + "\n")
                handle.flush()
                n_written += 1
                if args.sleep:
                    time.sleep(args.sleep)
                if i % 100 == 0:
                    print(f"  ... {i}/{len(urls)} enregistrements récupérés", file=sys.stderr)
    finally:
        if args.out:
            handle.close()
    suffix = f", {n_skipped} déjà présent(s) ignoré(s) (reprise)" if n_skipped else ""
    print(f"OK : {n_written} enregistrement(s) écrit(s){suffix} -> {args.out or '(stdout)'}",
          file=sys.stderr)


def _download(session, url: str, dest: Path, timeout: int) -> None:
    def _do() -> None:
        resp = session.get(url, timeout=timeout, stream=True)
        if not resp.ok:
            _raise_for(resp)
        with open(dest, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    fh.write(chunk)
    _with_retry(_do)


def cmd_genomes(args, session, db) -> None:
    relay_access_warning(session, db)
    filters = _parse_filters(args.filter)
    if not filters and not args.all_isolates:
        raise BigsdbError(
            "aucun --filter fourni : passer --all-isolates explicitement pour télécharger la "
            "base entière (jusqu'à ~1557 génomes, plusieurs Gio)."
        )
    if filters:
        validate_fields(session, db, list(filters))
    urls = search_isolates(session, db, filters, timeout=args.timeout) if filters \
        else list_all_isolates(session, db, timeout=args.timeout)

    n_total = len(urls)
    if args.limit and n_total > args.limit:
        print(f"[BIGSdb] {n_total} isolat(s) correspondent au filtre, limité à {args.limit} "
              f"(--limit 0 pour tout prendre)", file=sys.stderr)
        urls = urls[:args.limit]
    elif n_total == 0:
        raise BigsdbError(
            f"aucun isolat pour le filtre {filters} — filtre légitimement vide (valeur hors "
            f"des `allowed_values`) ou faute de frappe : vérifier avec `breakdown` avant de "
            f"conclure à un lot vide."
        )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.out_dir / "manifest.tsv"
    cols = ["id", "isolate", "clade", "species", "n_contigs", "total_length", "path"]
    already = set()
    if manifest_path.exists():
        with open(manifest_path) as fh:
            next(fh, None)  # en-tête
            for line in fh:
                iso_id = line.split(SEP, 1)[0]
                if iso_id:
                    already.add(iso_id)
        if already:
            print(f"[BIGSdb] reprise : {len(already)} génome(s) déjà présent(s) dans "
                  f"{manifest_path}", file=sys.stderr)

    manifest = []
    n_missing = 0
    n_skipped = 0
    with open(manifest_path, "a" if already else "w") as manifest_fh:
        if not already:
            manifest_fh.write(SEP.join(cols) + "\n")
        for i, url in enumerate(urls, 1):
            isolate_id = _isolate_id_from_url(url)
            if isolate_id in already:
                n_skipped += 1
                continue
            record = fetch_isolate(session, db, isolate_id)
            prov = record.get("provenance", {})
            seq_bin = record.get("sequence_bin") or {}
            fasta_url = seq_bin.get("contigs_fasta")
            if not fasta_url:
                n_missing += 1
                print(f"  [{i}/{len(urls)}] isolat {isolate_id} : pas de génome assemblé, ignoré",
                      file=sys.stderr)
                continue
            name = prov.get("isolate", isolate_id)
            safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in str(name))
            dest = args.out_dir / f"{isolate_id}_{safe_name}.fasta"
            _download(session, fasta_url, dest, args.timeout)
            row = {
                "id": isolate_id, "isolate": name, "clade": prov.get("clade", ""),
                "species": prov.get("species", ""), "n_contigs": seq_bin.get("contig_count", ""),
                "total_length": seq_bin.get("total_length", ""), "path": str(dest),
            }
            manifest.append(row)
            manifest_fh.write(SEP.join(_cell(row.get(c, "")) for c in cols) + "\n")
            manifest_fh.flush()
            if args.sleep:
                time.sleep(args.sleep)
            if i % 20 == 0:
                print(f"  ... {i}/{len(urls)} génomes traités", file=sys.stderr)

    suffix = f", {n_skipped} déjà présent(s) ignoré(s) (reprise)" if n_skipped else ""
    print(f"OK : {len(manifest)} génome(s) écrit(s) dans {args.out_dir}, {n_missing} isolat(s) "
          f"sans génome ignoré(s){suffix}, manifeste -> {manifest_path}", file=sys.stderr)
    if not manifest and not already:
        raise BigsdbError(
            "aucun génome téléchargé (tous les isolats du lot filtré sont sans assemblage) — "
            "lot non vide côté métadonnées mais vide côté génomes, à ne pas confondre."
        )


def cmd_isolate(args, session, db) -> None:
    record = fetch_isolate(session, db, args.isolate_id)
    print(json.dumps(record, indent=2, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", default=DEFAULT_DB,
                         help=f"base BIGSdb (défaut : {DEFAULT_DB})")
    parser.add_argument("--timeout", type=int, default=120, help="timeout HTTP par requête (s)")
    parser.add_argument("--sleep", type=float, default=0.2,
                         help="pause entre requêtes séquentielles (politesse, serveur partagé)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("stats", help="volumétrie et répartition par clade").set_defaults(func=cmd_stats)
    sub.add_parser("fields", help="champs de provenance disponibles").set_defaults(func=cmd_fields)

    p = sub.add_parser("breakdown", help="répartition + complétude d'un ou plusieurs champs")
    p.add_argument("fields", nargs="*", help="défaut : tous les champs (~38 requêtes)")
    p.set_defaults(func=cmd_breakdown)

    p = sub.add_parser("search", help="filtre les isolats et exporte leurs métadonnées")
    p.add_argument("--filter", action="append", default=[], metavar="champ=valeur",
                    help="répétable ; combiné en ET logique")
    p.add_argument("--format", choices=["tsv", "json"], default="tsv")
    p.add_argument("--out", type=Path, default=None, help="défaut : stdout")
    p.add_argument("--resume", action="store_true",
                    help="reprend depuis --out existant (tsv only) au lieu de tout refaire")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("genomes", help="télécharge les génomes FASTA d'un lot filtré")
    p.add_argument("--filter", action="append", default=[], metavar="champ=valeur")
    p.add_argument("--all-isolates", action="store_true",
                    help="requis si --filter est omis (garde-fou contre un tirage massif)")
    p.add_argument("--limit", type=int, default=50,
                    help="plafond du lot (0 = illimité, défaut 50)")
    p.add_argument("--out-dir", type=Path, required=True)
    p.set_defaults(func=cmd_genomes)

    p = sub.add_parser("isolate", help="enregistrement JSON brut d'un isolat (debug)")
    p.add_argument("isolate_id")
    p.set_defaults(func=cmd_isolate)

    args = parser.parse_args()
    session = _session()
    try:
        args.func(args, session, args.db)
    except BigsdbError as exc:
        print(f"erreur : {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
