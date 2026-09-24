#!/usr/bin/env python3
"""
Objet: accès JGI Data Portal / IMG-VR (téléchargement, BLAST en streaming par lots, extraction
  d'un enregistrement FASTA unique, pilotage du formulaire web « Viral/Spacer BLAST ») sans jamais
  matérialiser le FASTA décompressé entier sur disque.
Entrées: jeton de session JGI (`~/.jgi_session_token`, "Copy My Session Token" dans le menu avatar
  du portail), un export ZIP JGI Data Portal déjà téléchargé (pour scan/extract), ou un FASTA de
  requêtes (< 10 000 caractères pour blast).
Sorties: fichier téléchargé (download), résultats BLAST par lot en JSON (scan), un enregistrement
  FASTA unique (extract), résultats BLAST du formulaire web en JSON (blast).
Réutilisable: oui — promu skill partagé le 2026-09-22 après un second projet effectivement
  réutilisateur (SpacerEgalVirus, cf. PROVENANCE.md et SKILL.md pour le détail des deux usages).
Projet: archeo_crispr (origine, A1.5.e-f, A1.5.g).
Date: 2026-08-11 (rédaction initiale) ; reforgé le 2026-08-11 (garde-fou RAM après OOM-kill),
  2026-08-24 (timeout blastn attrapé proprement).

Deux garde-fous transversaux aux quatre sous-commandes (RAM et disque), et un garde-fou
protospacer propre au projet d'origine :

  download  Télécharge un export JGI Data Portal par API (jeton de session, PAS l'ancien
            hand-shake `signon.jgi.doe.gov`).
  scan      Décompresse le `.fna.gz` interne EN STREAMING, par lots plafonnés en taille
            décompressée (jamais `gzip -l` pour estimer un ratio de décompression : peu fiable
            au-delà de 4 Gio décompressés, mesurer sur un échantillon réel). Pour chaque lot :
            `makeblastdb` + `blastn -task blastn-short` contre les requêtes, puis le lot et son
            index sont supprimés avant le suivant.
  extract   Décompresse le `.fna.gz` interne EN STREAMING (même mécanisme que `scan`, même
            garde-fou mémoire O(1 ligne)) mais SANS `makeblastdb`/`blastn` : cherche un seul
            enregistrement FASTA par sous-chaîne d'en-tête, l'écrit dès qu'il est trouvé, et
            s'arrête. Beaucoup plus rapide que `scan` pour récupérer UNE séquence précise.
  blast     Pilote le formulaire web « Viral/Spacer BLAST » d'IMG/VR (même jeton que `download`,
            AUCUN navigateur requis) : soumission multipart, scrape du couple file/queuefile
            dans la réponse pour construire l'URL de ping, poll jusqu'à `running != "yes"`,
            dérivation de l'URL de résultats (`done_...` -> `blastout_...`), scrape du lien JSON
            statique embarqué dans la page de résultats, parsing en lignes {en-tête: valeur} à
            partir des en-têtes RÉELS de la page (jamais codés en dur).
            ⚠ **RÉGRESSION SERVEUR CONNUE, TOUJOURS ACTIVE** (détectée 2026-08-12, reconfirmée
            2026-09-01 et 2026-09-22) : la récupération des résultats échoue systématiquement
            (« Software error: 'null' expected, at character offset 0 ... WorkspaceBlast.pm
            line 454 »), y compris via le lien de repli « View raw Blast data file » de la page
            d'erreur elle-même (aussi cassé). La SOUMISSION reste acceptée et mise en file sans
            erreur (jeton valide, job accepté) : seule la RÉCUPÉRATION échoue, côté serveur IMG/VR,
            pas côté client. Ne pas re-router vers ce fallback tant qu'aucun test de fumée récent
            ne l'a confirmé réparé. Utiliser `scan`/`extract` en attendant (mêmes données
            nucléotidiques, chemin d'accès différent : dump complet plutôt que formulaire web).

Garde-fou disque (`scan`/`extract`) : vérifie l'espace libre avant CHAQUE lot et PENDANT
l'écriture (pas seulement avant/après), s'arrête proprement si la marge tombe sous
`--min-free-gb` (défaut : 2x la taille de lot), plutôt que de risquer un disque plein.

Garde-fou RAM (`scan`/`extract`) : `_available_ram_gb` lit `MemAvailable` de `/proc/meminfo`
(jamais le swap libre) et arrête AVANT d'indexer un lot si la marge est trop faible. Ajouté après
un OOM-kill silencieux (SIGKILL, aucun log, aucun fichier orphelin) sur une machine partagée avec
d'autres calculs concurrents — l'écriture des lots FASTA est directe sur disque, ligne par ligne
(jamais accumulée en RAM), et l'indexation BLAST d'un lot est le seul pic mémoire restant.

Authentification, deux mécanismes distincts et NON interchangeables dans le code actuel : le
Bearer token de `~/.jgi_session_token` sert à `download`/`scan`/`extract`/`blast`. Un second
mécanisme, découvert et validé le 2026-09-03 sur un usage tiers (SpacerEgalVirus, téléchargement
de `IMGVR_all_Host_information-high_confidence.tsv` via le bouton « Command line download » du
panier du NOUVEAU JGI Data Portal, qui échoue en HTTP 401 avec le Bearer classique) : cookie de
session Keycloak (`kc_session=<JWT>`), obtenu depuis le bouton « Command line download » de
l'interface web, testé HTTP 200 fichier intact. Non encapsulé ici — à ajouter comme repli
`--auth cookie` si le Bearer venait à se périmer ou si un usage futur en a besoin (n'importe quel
dataset du JGI Data Portal expose le même bouton, pas seulement IMG/VR).

Usage :
    jgi_imgvr_access.py download --source Custom_MPI-IMG_VR \\
        --file-id 632a1b312de7c323533daabd --top-hit 63a22c8a3b5d0133c73fb0a8 \\
        --out data/imgvr/imgvr_all_nucleotides_download.zip

    jgi_imgvr_access.py scan --zip data/imgvr/imgvr_all_nucleotides_download.zip \\
        --query variables.fa --control controle.fa --batch-gb 8 \\
        --out résultats/protospacer_imgvr.json

    jgi_imgvr_access.py extract --zip data/imgvr/imgvr_all_nucleotides_download.zip \\
        --id-substring 2565956756_000002 --out résultats/candidat.fasta

    jgi_imgvr_access.py blast --fasta requêtes.fasta \\
        --use-db nucleotide_db --evalue 1e-0 --out résultats/protospacer_imgvr_online.json
        # (cassé côté serveur au 2026-09-22, cf. avertissement ci-dessus)
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import TextIO

DOWNLOAD_URL = "https://files-download.jgi.doe.gov/download_files/"
IMGVR_MAIN_URL = "https://img.jgi.doe.gov/cgi-bin/vr/main.cgi"
IMGVR_PING_URL = "https://img.jgi.doe.gov/cgi-bin/vr/xml.cgi"
DEFAULT_TOKEN_FILE = Path.home() / ".jgi_session_token"
GB = 1024**3


def _auth_header(token_file: Path) -> dict:
    token = token_file.read_text().strip()
    if not token:
        raise SystemExit(f"Jeton vide dans {token_file}")
    return {"Authorization": token if token.lower().startswith("bearer ") else f"Bearer {token}"}


def _free_gb(path: Path) -> float:
    usage = shutil.disk_usage(path)
    return usage.free / GB


def _available_ram_gb() -> float:
    """MemAvailable de /proc/meminfo (pas MemFree : compte le cache réclamable).

    Ajouté après un crash silencieux (OOM-kill) : la cause réelle était la RAM, pas le disque —
    un OOM-kill ne laisse aucune trace exploitable (SIGKILL, buffers perdus). Machine PARTAGÉE
    (autres calculs, autres sessions) : ne jamais supposer que la RAM nominale de la machine est
    disponible.
    """
    try:
        with open("/proc/meminfo") as fh:
            for line in fh:
                if line.startswith("MemAvailable:"):
                    kb = int(line.split()[1])
                    return kb / (1024 * 1024)
    except OSError:
        pass
    return float("inf")  # pas Linux / non lisible : ne bloque pas, mais ne protège pas non plus


def cmd_download(args: argparse.Namespace) -> None:
    import requests

    headers = _auth_header(args.token_file)
    headers["Content-Type"] = "application/json"
    payload = {"ids": {args.source: {"file_ids": args.file_id, "top_hit": args.top_hit}}}

    print(f"POST {DOWNLOAD_URL} source={args.source} file_ids={args.file_id}", file=sys.stderr)
    with requests.post(DOWNLOAD_URL, headers=headers, json=payload, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        args.out.parent.mkdir(parents=True, exist_ok=True)
        written = 0
        t0 = time.time()
        with open(args.out, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=8 * 1024 * 1024):
                if not chunk:
                    continue
                fh.write(chunk)
                written += len(chunk)
                if written % (1024 * 1024 * 1024) < len(chunk):
                    elapsed = time.time() - t0
                    print(f"  {written / GB:6.2f} Gio ecrits, {elapsed:6.0f} s", file=sys.stderr)
        print(f"OK : {written} octets -> {args.out} (HTTP {resp.status_code})", file=sys.stderr)


def _open_member_stream(zip_path: Path, member: str | None):
    zf = zipfile.ZipFile(zip_path)
    if member is None:
        gz_members = [n for n in zf.namelist() if n.endswith(".gz")]
        if len(gz_members) != 1:
            raise SystemExit(
                f"--member requis : {len(gz_members)} entrées .gz dans l'archive "
                f"({gz_members})"
            )
        member = gz_members[0]
    raw = zf.open(member, "r")
    return zf, gzip.GzipFile(fileobj=raw, mode="rb")


class DiskTooLowError(RuntimeError):
    pass


def _write_fasta_batches(zip_path: Path, member: str | None, batch_bytes: int, workdir: Path,
                          hard_floor_gb: float, check_every_bytes: int = 200 * 1024 * 1024):
    """Écrit les lots DIRECTEMENT sur disque au fil du flux (jamais accumulés en mémoire).

    Une première version accumulait chaque lot en RAM (liste de chaînes Python, `"".join()`)
    avant de l'écrire — sur une machine PARTAGÉE proche de saturation, le process a disparu sans
    trace (0 octet de log, aucun fichier orphelin, aucun octet de disque consommé) : signature
    d'un OOM-kill (SIGKILL, aucun nettoyage possible). Coupure UNIQUEMENT à une frontière
    d'enregistrement FASTA (jamais au milieu d'une séquence), mais l'écriture ligne par ligne ne
    garde jamais plus qu'une poignée de lignes en mémoire, quelle que soit la taille du lot.

    Vérifie aussi l'espace disque PENDANT l'écriture (pas seulement avant/après un lot) : sur un
    lot de plusieurs Gio, la marge peut s'épuiser en cours d'écriture elle-même.
    """
    zf, gz = _open_member_stream(zip_path, member)
    batch_idx = 1
    written = 0
    since_check = 0
    n_seq = 0
    path = workdir / f"_scan_batch_{batch_idx}.fa"
    out: TextIO = open(path, "w")

    try:
        with gz as fh:
            text_fh = (line.decode("utf-8", errors="replace") for line in fh)
            for line in text_fh:
                if line.startswith(">"):
                    if written >= batch_bytes and n_seq > 0:
                        out.close()
                        yield path, n_seq
                        batch_idx += 1
                        written = 0
                        since_check = 0
                        n_seq = 0
                        path = workdir / f"_scan_batch_{batch_idx}.fa"
                        out = open(path, "w")
                    n_seq += 1
                out.write(line)
                written += len(line)
                since_check += len(line)
                if since_check >= check_every_bytes:
                    since_check = 0
                    if _free_gb(workdir) < hard_floor_gb:
                        out.close()
                        path.unlink(missing_ok=True)
                        raise DiskTooLowError(
                            f"espace disque sous {hard_floor_gb} Gio pendant l'écriture du "
                            f"lot {batch_idx} ({written / GB:.2f} Gio déjà écrits) : arrêt "
                            f"immédiat, lot partiel supprimé."
                        )
        out.close()
        if n_seq > 0:
            yield path, n_seq
        else:
            path.unlink(missing_ok=True)
    finally:
        zf.close()
        if not out.closed:
            out.close()


def _run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    out = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if out.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} a échoué : {out.stderr[:2000]}")
    return out


def cmd_scan(args: argparse.Namespace) -> None:
    batch_bytes = int(args.batch_gb * GB)
    min_free = args.min_free_gb if args.min_free_gb is not None else 2 * args.batch_gb
    workdir = args.workdir or args.zip.parent
    workdir.mkdir(parents=True, exist_ok=True)

    query_path = args.query
    if args.control is not None:
        # garde-fou protospacer : toujours soumettre testé + contrôle apparié dans le même appel blastn
        merged = workdir / "_scan_query_plus_control.fa"
        merged.write_text(args.query.read_text() + args.control.read_text())
        query_path = merged
        args._merged_query = merged  # nettoyé en fin de run

    hits_by_batch: list[dict] = []
    n_batches = 0
    t0 = time.time()
    stopped_reason = None

    batches = _write_fasta_batches(args.zip, args.member, batch_bytes, workdir,
                                    hard_floor_gb=min(min_free, args.batch_gb))
    try:
        for batch_fasta, n_seq in batches:
            n_batches += 1
            if args.max_batches and n_batches > args.max_batches:
                print(f"--max-batches={args.max_batches} atteint, arrêt volontaire", file=sys.stderr)
                batch_fasta.unlink(missing_ok=True)
                break

            free = _free_gb(workdir)
            ram = _available_ram_gb()
            size_gb = batch_fasta.stat().st_size / GB
            print(
                f"[lot {n_batches}] {n_seq} séquences, {size_gb:.2f} Gio, "
                f"{free:.1f} Gio libres disque, {ram:.1f} Gio RAM disponible "
                f"avant construction de l'index",
                file=sys.stderr,
            )
            if ram < args.min_ram_gb:
                print(
                    f"ARRÊT : {ram:.1f} Gio RAM disponible < seuil {args.min_ram_gb:.1f} Gio "
                    f"avant l'indexation du lot {n_batches} (machine partagée). Le lot écrit "
                    f"est supprimé sans être indexé.",
                    file=sys.stderr,
                )
                batch_fasta.unlink(missing_ok=True)
                break
            if free < min_free:
                print(
                    f"ARRÊT : {free:.1f} Gio libres < seuil {min_free:.1f} Gio "
                    f"avant l'indexation du lot {n_batches}. Le lot écrit est supprimé sans "
                    f"être indexé ; relancer plus tard ou avec --batch-gb plus petit.",
                    file=sys.stderr,
                )
                batch_fasta.unlink(missing_ok=True)
                break

            try:
                _run(["makeblastdb", "-in", str(batch_fasta), "-dbtype", "nucl",
                      "-out", str(batch_fasta)])
                cmd = [
                    "blastn", "-task", "blastn-short", "-query", str(query_path),
                    "-db", str(batch_fasta), "-evalue", str(args.evalue), "-dust", "no",
                    "-outfmt", "6", "-max_target_seqs", "20",
                    "-num_threads", str(args.threads),
                ]
                res = _run(cmd, timeout=args.blast_timeout)
                rows = [line.split("\t") for line in res.stdout.splitlines() if line.strip()]
                hits_by_batch.append({"batch": n_batches, "n_seq": n_seq, "hits": rows})
                print(f"[lot {n_batches}] {len(rows)} lignes de hit brutes", file=sys.stderr)
            except subprocess.TimeoutExpired as exc:
                # Un timeout blastn non attrapé faisait planter tout le scan (traceback non
                # catché, aucun résultat déjà acquis écrit), forçant à tout relancer depuis le
                # lot 1 sur un run de plusieurs heures.
                stopped_reason = (
                    f"timeout blastn au lot {n_batches} après {args.blast_timeout}s "
                    f"(--threads={args.threads}) : {exc}"
                )
                print(f"ARRÊT (timeout) : {stopped_reason}", file=sys.stderr)
                break
            finally:
                # glob, pas une liste d'extensions figée : makeblastdb varie selon la version
                # (.ndb/.njs peuvent manquer d'une première liste codée en dur).
                for p in workdir.glob(batch_fasta.name + ".n*"):
                    p.unlink()
                if batch_fasta.exists():
                    batch_fasta.unlink()
    except DiskTooLowError as exc:
        stopped_reason = str(exc)
        print(f"ARRÊT (disque, pendant l'écriture) : {exc}", file=sys.stderr)

    merged = getattr(args, "_merged_query", None)
    if merged is not None and merged.exists():
        merged.unlink()

    elapsed = time.time() - t0
    result = {
        "zip": str(args.zip), "member": args.member, "batch_gb": args.batch_gb,
        "n_batches": n_batches, "elapsed_s": elapsed, "hits_by_batch": hits_by_batch,
        "stopped_reason": stopped_reason,
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2))
        print(f"Résultat -> {args.out}", file=sys.stderr)
    else:
        print(json.dumps(result, indent=2))


def cmd_extract(args: argparse.Namespace) -> None:
    ram = _available_ram_gb()
    if ram < args.min_ram_gb:
        raise SystemExit(
            f"ARRÊT avant lecture : {ram:.1f} Gio RAM disponible < seuil {args.min_ram_gb:.1f} "
            f"Gio (machine partagée). Rien n'a été ouvert."
        )

    zf, gz = _open_member_stream(args.zip, args.member)
    t0 = time.time()
    processed = 0
    last_report_gb = 0.0
    capturing = False
    found = False
    out: TextIO | None = None

    try:
        with gz as fh:
            text_fh = (line.decode("utf-8", errors="replace") for line in fh)
            for line in text_fh:
                processed += len(line)
                processed_gb = processed / GB
                if processed_gb - last_report_gb >= args.progress_every_gb:
                    last_report_gb = processed_gb
                    print(
                        f"  {processed_gb:6.1f} Gio décompressés parcourus, "
                        f"{time.time() - t0:6.0f} s, cible {'trouvée, en cours de capture' if capturing else 'pas encore vue'}",
                        file=sys.stderr,
                    )
                if line.startswith(">"):
                    if capturing:
                        # nouvel en-tête = fin de l'enregistrement cible, inutile de lire la suite
                        break
                    if args.id_substring in line:
                        capturing = True
                        found = True
                        args.out.parent.mkdir(parents=True, exist_ok=True)
                        out = open(args.out, "w")
                        print(f"[trouvé] {line.strip()} (à {processed_gb:.2f} Gio)", file=sys.stderr)
                if capturing and out is not None:
                    out.write(line)
    finally:
        zf.close()
        if out is not None:
            out.close()

    elapsed = time.time() - t0
    if not found:
        raise SystemExit(
            f"Aucun en-tête contenant {args.id_substring!r} trouvé après "
            f"{processed / GB:.2f} Gio décompressés ({elapsed:.0f} s). Rien écrit."
        )
    print(f"OK : enregistrement écrit -> {args.out} ({processed / GB:.2f} Gio parcourus, {elapsed:.0f} s)",
          file=sys.stderr)


def _submit_blast(headers: dict, fasta_text: str, use_db: str, evalue: str, num_hits: int,
                   restricted: bool, timeout: int) -> str:
    import requests

    fields = {
        "fasta": (None, fasta_text),
        "use_db": (None, use_db),
        "blast_evalue": (None, evalue),
        "num_hits": (None, str(num_hits)),
        "outputformat": (None, "table"),
        "page": (None, "fireviralResults"),
        "section": (None, "WorkspaceBlast"),
        "_section_Blast16s_blast16sResults": (None, "Run Blast"),
    }
    if restricted:
        fields["restricted"] = (None, "yes")
    resp = requests.post(IMGVR_MAIN_URL, headers=headers, files=fields, timeout=timeout)
    resp.raise_for_status()
    return resp.text


_PING_RE = re.compile(
    r"file=(done_[^&'\"]+)&queuefile=(queue_[^&'\"]+)&use_db=([^&'\"]+)&server=([^&'\"]+)"
)


def _parse_ping_params(submit_html: str) -> dict:
    m = _PING_RE.search(submit_html)
    if not m:
        raise RuntimeError(
            "Motif de ping BLAST (file=done_...&queuefile=queue_...) introuvable dans la page "
            "de soumission — le formulaire IMG/VR a peut-être changé de structure. Rien de plus "
            "tenté automatiquement."
        )
    file_id, queuefile_id, use_db, server = m.groups()
    return {"file": file_id, "queuefile": queuefile_id, "use_db": use_db, "server": server}


def _poll_blast(headers: dict, ping_params: dict, poll_interval: float, timeout_s: float) -> None:
    import requests

    t0 = time.time()
    while True:
        r = requests.get(IMGVR_PING_URL, headers=headers,
                          params={"section": "WorkspaceBlast", "page": "fireBlastallPing", **ping_params},
                          timeout=60)
        r.raise_for_status()
        ans = r.json()
        if ans.get("status") == "error":
            raise RuntimeError(f"Le job BLAST IMG/VR a échoué : {ans.get('message', ans)}")
        if ans.get("running") != "yes":
            return
        elapsed = time.time() - t0
        if elapsed > timeout_s:
            raise TimeoutError(
                f"Job BLAST IMG/VR toujours en file/en cours après {elapsed:.0f} s "
                f"(seuil {timeout_s:.0f} s) : {ans}"
            )
        print(f"  en cours ({elapsed:.0f} s écoulées) : {ans}", file=sys.stderr)
        time.sleep(poll_interval)


_THEAD_RE = re.compile(r"<thead>.*?</thead>", re.S)
_TH_RE = re.compile(r"<th>(.*?)</th>", re.S)
_TAG_RE = re.compile(r"<.*?>")
_RESULT_URL_RE = re.compile(r'id="url" name="url" value="([^"]+)"')


def _fetch_blast_results(headers: dict, ping_params: dict, evalue: str, timeout: int) -> list[dict]:
    import requests

    blastout_id = ping_params["file"].replace("done_", "blastout_", 1)
    r = requests.get(IMGVR_MAIN_URL, headers=headers, params={
        "section": "WorkspaceBlast", "page": "fireBlastallGet", "evalue": evalue,
        "use_db": ping_params["use_db"], "blast": "", "file": blastout_id,
        "server": ping_params["server"], "format": "15",
    }, timeout=timeout)
    r.raise_for_status()

    if "Software error" in r.text:
        raise RuntimeError(
            "Régression serveur IMG/VR connue et toujours active (2026-08-12 -> 2026-09-22 au "
            "moins) : la page de résultats renvoie 'Software error ... WorkspaceBlast.pm line "
            "454' au lieu du tableau de hits. Le job a bien tourné côté serveur (soumission et "
            "poll acceptés) ; seule la récupération échoue. Utiliser scan/extract en attendant "
            "un correctif côté IMG/VR — cf. l'avertissement en tête de ce module."
        )

    thead_m = _THEAD_RE.search(r.text)
    if not thead_m:
        raise RuntimeError(
            "En-tête de tableau introuvable dans la page de résultats IMG/VR — structure de "
            "page changée, ne pas deviner les colonnes en dur."
        )
    heads = [_TAG_RE.sub("", h).strip() for h in _TH_RE.findall(thead_m.group(0))]
    heads = [h for h in heads if h]  # la 1re colonne (case à cocher) n'a pas de libellé

    json_url_m = _RESULT_URL_RE.search(r.text)
    if not json_url_m:
        raise RuntimeError(
            "Lien JSON des résultats introuvable dans la page IMG/VR (champ caché 'url') — "
            "structure de page changée."
        )
    rj = requests.get(json_url_m.group(1), headers=headers, timeout=timeout)
    rj.raise_for_status()
    raw_rows = rj.json().get("data", [])

    rows = []
    for raw in raw_rows:
        cells = raw[1:] if len(raw) == len(heads) + 1 else raw  # 1re cellule = id de ligne, pas une colonne
        row = {}
        for h, v in zip(heads, cells):
            row[h] = v.split("#==#")[0] if isinstance(v, str) else v
        rows.append(row)
    return rows


def cmd_blast(args: argparse.Namespace) -> None:
    headers = _auth_header(args.token_file)
    fasta_text = args.fasta.read_text()

    print(f"Soumission de {args.fasta} (use_db={args.use_db}, evalue={args.evalue}) ...", file=sys.stderr)
    submit_html = _submit_blast(headers, fasta_text, args.use_db, args.evalue, args.num_hits,
                                 args.restricted, args.timeout)
    ping_params = _parse_ping_params(submit_html)
    print(f"  job {ping_params['file']} en file sur {ping_params['server']}", file=sys.stderr)

    _poll_blast(headers, ping_params, args.poll_interval, args.timeout_s)
    print("  job terminé, récupération des résultats ...", file=sys.stderr)

    rows = _fetch_blast_results(headers, ping_params, args.evalue, args.timeout)
    print(f"OK : {len(rows)} lignes de hits", file=sys.stderr)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
        print(f"Résultat -> {args.out}", file=sys.stderr)
    else:
        print(json.dumps(rows, indent=2, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    dl = sub.add_parser("download", help="Télécharge un export JGI Data Portal par API")
    dl.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN_FILE)
    dl.add_argument("--source", required=True, help='ex. "Custom_MPI-IMG_VR"')
    dl.add_argument("--file-id", nargs="+", required=True)
    dl.add_argument("--top-hit", required=True)
    dl.add_argument("--out", type=Path, required=True)
    dl.set_defaults(func=cmd_download)

    sc = sub.add_parser("scan", help="BLAST par lots en streaming, jamais matérialisé entier")
    sc.add_argument("--zip", type=Path, required=True)
    sc.add_argument("--member", default=None, help="Chemin interne du .gz (auto-détecté si absent)")
    sc.add_argument("--query", type=Path, required=True, help="FASTA des spacers testés")
    sc.add_argument("--control", type=Path, default=None, help="FASTA du contrôle apparié (fusionné avec --query avant blastn)")
    sc.add_argument("--batch-gb", type=float, default=8.0)
    sc.add_argument("--min-free-gb", type=float, default=None, help="Défaut : 2x --batch-gb")
    sc.add_argument("--min-ram-gb", type=float, default=3.0,
                     help="MemAvailable minimum avant d'indexer un lot (machine partagée)")
    sc.add_argument("--evalue", type=float, default=1.0)
    sc.add_argument("--max-batches", type=int, default=None, help="Limite pour un test borné")
    sc.add_argument("--workdir", type=Path, default=None, help="Défaut : dossier du zip")
    sc.add_argument("--out", type=Path, default=None)
    sc.add_argument("--threads", type=int, default=max(1, (os.cpu_count() or 4) - 4),
                     help="-num_threads passé à blastn (défaut : cœurs disponibles - 4, "
                          "machine partagée). blastn-short reste mono-thread par défaut si "
                          "omis, ce qui peut faire dépasser --blast-timeout sur des lots de "
                          "plusieurs Gio.")
    sc.add_argument("--blast-timeout", type=int, default=21600,
                     help="Timeout (s) par lot pour l'appel blastn (défaut 6h). Un "
                          "TimeoutExpired est attrapé proprement : le scan s'arrête et écrit "
                          "--out avec les lots déjà acquis, au lieu de planter sans rien écrire.")
    sc.set_defaults(func=cmd_scan)

    ex = sub.add_parser("extract", help="Récupère UN enregistrement FASTA par sous-chaîne d'en-tête, sans BLAST")
    ex.add_argument("--zip", type=Path, required=True)
    ex.add_argument("--member", default=None, help="Chemin interne du .gz (auto-détecté si absent)")
    ex.add_argument("--id-substring", required=True, help="Sous-chaîne recherchée dans la ligne d'en-tête FASTA")
    ex.add_argument("--out", type=Path, required=True)
    ex.add_argument("--progress-every-gb", type=float, default=5.0)
    ex.add_argument("--min-ram-gb", type=float, default=1.0,
                     help="MemAvailable minimum avant d'ouvrir le flux (machine partagée)")
    ex.set_defaults(func=cmd_extract)

    bl = sub.add_parser("blast", help="Pilote le formulaire web « Viral/Spacer BLAST » d'IMG/VR par API (jeton, sans navigateur) — CASSÉ CÔTÉ SERVEUR au 2026-09-22, cf. docstring")
    bl.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN_FILE)
    bl.add_argument("--fasta", type=Path, required=True, help="FASTA des requêtes (< 10 000 caractères, limite du formulaire)")
    bl.add_argument("--use-db", default="nucleotide_db",
                     help="nucleotide_db (Virus DNA DB) | protein_db | viral_spacers.fna | meta_spacers.fna")
    bl.add_argument("--evalue", default="1e-0", help="Valeur du select E-value du formulaire (ex. 1e-0, 1e-5, 1e-10)")
    bl.add_argument("--num-hits", type=int, default=500)
    bl.add_argument("--restricted", action="store_true", help="Inclure les jeux de données restreints (défaut : public uniquement)")
    bl.add_argument("--poll-interval", type=float, default=15.0)
    bl.add_argument("--timeout-s", type=float, default=900.0, help="Délai max d'attente du job (dépasse largement les 2-15 min annoncés par le portail)")
    bl.add_argument("--timeout", type=int, default=120, help="Timeout HTTP par requête (soumission, ping, résultats)")
    bl.add_argument("--out", type=Path, default=None)
    bl.set_defaults(func=cmd_blast)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
