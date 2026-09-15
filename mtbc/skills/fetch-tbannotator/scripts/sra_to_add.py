#!/usr/bin/env python3
"""File d'attente d'ingestion TBannotator : qualifier des accessions SRA, puis les
ajouter a `mp:/data/current/run/config/samples.tsv` sans casser le travail en cours.

CE QUE CE SCRIPT REMPLACE
-------------------------
La procedure d'ingestion etait un pipeline `awk` recopie a la main (voir SKILL.md
§ « When a strain is in neither location »). Elle marche, mais elle porte trois
pieges qu'un script elimine par construction :

  1. `samples.tsv` contient le travail EN VOL d'autres campagnes (vu le
     2026-07-31 : 299 candidats `CUS*` sans rapport avec le projet courant). Toute
     ecriture en mode 'w' les detruit -- c'est precisement ce que fait
     `~/integrate_new_sras.py` sur `mp`, a ne jamais utiliser.
  2. Ajouter et LANCER sont deux decisions. Le lancement mobilise un serveur
     partage pour des jours. Ce script n'a AUCUN mode de lancement : il imprime la
     commande, l'humain decide.
  3. Ingerer une accession inexistante, deja annotee, ou hors MTBC coute des
     heures de calcul pour rien. D'ou le pre-vol obligatoire.

TROIS ETATS, DEUX FICHIERS
  file locale (`sra_to_add.txt`, une accession par ligne, dans le projet courant)
      -> ce qu'on veut ingerer, accumule meme quand `mp` est injoignable ;
  `mp:/data/current/run/config/samples.tsv`
      -> la file reelle du pipeline, partagee ;
  `mp:/data/current/run/results/<SRA>/report.json`
      -> deja annote (fenetre glissante : une absence ici ne prouve pas qu'on
         n'a jamais ingere, cf. le caveat de purge du SKILL.md).

USAGE
  # 1. qualifier (aucune ecriture, ni locale ni distante)
  python3 sra_to_add.py --check SRR1234567 ERR9876543
  python3 sra_to_add.py --check --file candidates.tsv

  # 2. empiler dans la file locale ce qui est reellement a ingerer
  python3 sra_to_add.py --queue SRR1234567 ERR9876543
  python3 sra_to_add.py --queue --file new_sras.txt
  python3 sra_to_add.py --list

  # 3. pousser la file locale vers mp (dry-run par defaut)
  python3 sra_to_add.py --push
  python3 sra_to_add.py --push --apply

CODES DE SORTIE
  0 = rien a signaler ; 1 = au moins une accession refusee ou douteuse ;
  2 = `mp` injoignable ou operation impossible (la file locale reste intacte,
      relancer --push plus tard).

DEPENDANCES : bibliotheque standard seule. Reseau : API ENA (portal) et le
serveur HTTP TBannotator, tous deux publics.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

QUEUE_NAME = "sra_to_add.txt"
SAMPLES = "/data/current/run/config/samples.tsv"
RESULTS = "/data/current/run/results"
RUN_DIR = "/data/current/run"
SSH_HOST = "mp"
HTTP_REPORT = ("https://tblearn.tbannotator.ideev.universite-paris-saclay.fr"
               "/mcp/download/report/{acc}")
ENA_PORTAL = ("https://www.ebi.ac.uk/ena/portal/api/filereport"
              "?accession={acc}&result=read_run&format=json&fields="
              "run_accession,scientific_name,tax_id,library_layout,"
              "instrument_platform,base_count,fastq_bytes")

# SRR/ERR/DRR = depots publics ; CUS = FASTQ prives du groupe, qui n'ont ni
# metadonnees ENA ni existence publique : on les accepte sans pre-vol externe.
ACC_RE = re.compile(r"^(?:[SED]RR\d{6,9}|CUS\d{6})$")

SSH_OPTS = ["-o", "ConnectTimeout=20", "-o", "BatchMode=yes"]

# Cible d'ecriture effective. Surchargeable par --samples pour rejouer la
# procedure complete sur une COPIE : la file de production est partagee avec
# d'autres campagnes, on ne l'utilise pas comme bac a sable.
_samples_path = SAMPLES


# --------------------------------------------------------------------------- #
# Utilitaires
# --------------------------------------------------------------------------- #

class MpUnreachable(RuntimeError):
    """`mp` inaccessible.

    PREMIERE CAUSE A VERIFIER : le VPN universitaire est tombe. `mp` (comme tout
    `mesoprivate`/`mesohelios`, via le rebond `bilbo`) n'est joignable que VPN
    monte -- `sudo vpn up`. Le symptome typique est un `Connection timed out
    during banner exchange`, qui ressemble a une panne serveur et n'en est pas
    une. Ne JAMAIS conclure d'un echec ici que la file distante est vide ou que
    la souche n'a jamais ete ingeree."""


def quote_remote_path(path: str) -> str:
    """Protege un chemin avant interpolation dans la commande du shell distant."""
    return shlex.quote(path)


def ssh(cmd: str, timeout: int = 120, stdin: str | None = None) -> str:
    try:
        res = subprocess.run(["ssh", *SSH_OPTS, SSH_HOST, cmd],
                             capture_output=True, text=True, timeout=timeout,
                             input=stdin)
    except subprocess.TimeoutExpired as exc:
        raise MpUnreachable(f"delai depasse sur `ssh {SSH_HOST}` "
                            "(VPN probablement tombe : sudo vpn up)") from exc
    if res.returncode != 0:
        err = (res.stderr or "").strip().splitlines()
        first = err[0] if err else f"code {res.returncode}"
        if any(k in first.lower() for k in ("timed out", "banner", "refused",
                                            "unreachable", "no route")):
            raise MpUnreachable(f"{first} (VPN probablement tombe : sudo vpn up)")
        raise RuntimeError(f"echec distant : {first}")
    return res.stdout


def http_status(url: str, timeout: int = 25) -> int:
    req = urllib.request.Request(url, method="GET",
                                 headers={"User-Agent": "sra-to-add/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:                                            # noqa: BLE001
        return 0                                                 # injoignable


def find_queue(explicit: str | None) -> Path:
    """File locale : a la racine du projet (premier parent avec
    `cahier_de_labo.md`), sinon dans le repertoire courant."""
    if explicit:
        return Path(explicit).expanduser().resolve()
    here = Path.cwd().resolve()
    for d in [here, *here.parents]:
        if (d / "cahier_de_labo.md").exists():
            return d / QUEUE_NAME
    return here / QUEUE_NAME


def read_accessions(args: argparse.Namespace) -> list[str]:
    accs = list(args.accessions or [])
    if args.file:
        text = Path(args.file).expanduser().read_text()
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # tolere un TSV : on prend le premier champ qui ressemble a une accession
            for field in re.split(r"[\t,;\s]+", line):
                if ACC_RE.match(field.upper()):
                    accs.append(field.upper())
                    break
    seen, out = set(), []
    for a in (x.strip().upper() for x in accs):
        if a and a not in seen:
            seen.add(a)
            out.append(a)
    return out


# --------------------------------------------------------------------------- #
# Pre-vol
# --------------------------------------------------------------------------- #

def ena_metadata(acc: str) -> dict | None:
    """Metadonnees ENA. `None` = accession inconnue ou portail muet.

    Le `scientific_name` est DECLARATIF (renseigne par le deposant) : il sert a
    lever un drapeau, jamais a rejeter tout seul. Des runs MTBC sont deposes sous
    « Mycobacterium sp. », et l'inverse existe aussi.
    """
    try:
        raw = urllib.request.urlopen(ENA_PORTAL.format(acc=acc), timeout=30).read()
    except Exception:                                            # noqa: BLE001
        return None
    try:
        rows = json.loads(raw or b"[]")
    except json.JSONDecodeError:
        return None
    return rows[0] if rows else None


def preflight(accs: list[str], remote: dict[str, set[str]] | None) -> list[dict]:
    """Qualifie chaque accession. `remote` = {'samples': set, 'annotated': set}
    ou None si `mp` est injoignable (l'etat distant devient alors 'inconnu')."""
    out = []
    for acc in accs:
        notes: list[str] = []
        row: dict[str, object] = {"accession": acc, "notes": notes}

        if not ACC_RE.match(acc):
            row["statut"] = "INVALIDE"
            notes.append("format inattendu (attendu SRR/ERR/DRR + 6-9 chiffres, ou CUS+6)")
            out.append(row)
            continue

        if acc.startswith("CUS"):
            notes.append("FASTQ prive : aucun pre-vol externe possible")
        else:
            meta = ena_metadata(acc)
            if meta is None:
                notes.append("INCONNUE a l'ENA (accession fausse, ou embargo)")
                row["statut"] = "DOUTEUSE"
                out.append(row)
                continue
            row["organisme"] = meta.get("scientific_name")
            row["layout"] = meta.get("library_layout")
            row["plateforme"] = meta.get("instrument_platform")
            try:
                gb = sum(int(x) for x in str(meta.get("fastq_bytes") or 0).split(";") if x) / 1e9
            except ValueError:
                gb = 0.0
            row["taille_go"] = round(gb, 2)
            name = (row["organisme"] or "").lower()
            if "mycobacterium" not in name and "mycobacteroides" not in name:
                notes.append(f"organisme declare hors Mycobacterium : {row['organisme']!r} "
                                    "(verifier avant d'engager du calcul)")
            if gb > 0.9:
                notes.append(f"{gb:.1f} Go a telecharger : prevoir un timeout de 3 h")
            if (row["plateforme"] or "").upper().startswith("OXFORD") or \
               "PACBIO" in (row["plateforme"] or "").upper():
                notes.append("lectures LONGUES : la chaine TBannotator attend du court")

        if remote is None:
            row["statut"] = "MP_INJOIGNABLE"
            notes.append("etat distant inconnu (VPN ? sudo vpn up) : empiler "
                         "localement et retenter --push")
            out.append(row)
            continue

        if acc in remote["annotated"]:
            row["statut"] = "DEJA_ANNOTE"
            notes.append("report.json present sur mp : utiliser /fetch-tbannotator, pas l'ingestion")
        elif acc in remote["samples"]:
            row["statut"] = "DEJA_EN_FILE"
            notes.append("deja dans samples.tsv : sera traite au prochain run")
        else:
            code = http_status(HTTP_REPORT.format(acc=acc)) if not acc.startswith("CUS") else 0
            if code == 200:
                row["statut"] = "DEJA_ANNOTE"
                notes.append("absent de mp mais servi en HTTP (les deux sources "
                                    "desynchronisent) : fetch, pas ingestion")
            else:
                row["statut"] = "A_AJOUTER"
                if code not in (0, 404):
                    notes.append(f"serveur HTTP en {code} : verdict fonde sur mp seul")
        out.append(row)
    return out


def remote_state(accs: list[str]) -> dict[str, set[str]]:
    """Un seul aller-retour SSH pour les deux etats distants."""
    samples_path = quote_remote_path(_samples_path)
    samples = ssh(f"cat {samples_path} 2>/dev/null || true")
    in_samples = {line.split("\t")[0].strip().upper()
                  for line in samples.splitlines()
                  if line.strip() and line.split("\t")[0].strip().lower() != "accession"}
    if accs:
        quoted = " ".join(f"'{a}'" for a in accs)
        probe = ssh(f"cd {RESULTS} 2>/dev/null && for s in {quoted}; do "
                    f"[ -f \"$s/report.json\" ] && echo \"$s\"; done || true")
        annotated = {line.strip().upper() for line in probe.splitlines() if line.strip()}
    else:
        annotated = set()
    return {"samples": in_samples, "annotated": annotated}


# --------------------------------------------------------------------------- #
# Rendu
# --------------------------------------------------------------------------- #

ORDER = ["A_AJOUTER", "DEJA_EN_FILE", "DEJA_ANNOTE", "DOUTEUSE", "INVALIDE", "MP_INJOIGNABLE"]


def render(rows: list[dict]) -> None:
    for statut in ORDER:
        group = [r for r in rows if r["statut"] == statut]
        if not group:
            continue
        print(f"\n{statut} ({len(group)})")
        for r in group:
            org = f"  {r.get('organisme')}" if r.get("organisme") else ""
            size = f"  {r['taille_go']} Go" if r.get("taille_go") else ""
            print(f"  {r['accession']}{org}{size}")
            for n in r["notes"]:
                print(f"      - {n}")


# --------------------------------------------------------------------------- #
# File locale et poussee
# --------------------------------------------------------------------------- #

def load_queue(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [l.strip().upper() for l in path.read_text().splitlines()
            if l.strip() and not l.startswith("#")]


def save_queue(path: Path, accs: list[str]) -> None:
    header = (f"# File d'ingestion TBannotator, une accession par ligne.\n"
              f"# Poussee vers {SSH_HOST}:{SAMPLES} par sra_to_add.py --push --apply\n")
    path.write_text(header + "\n".join(accs) + ("\n" if accs else ""))


def push(queue_path: Path, apply: bool) -> int:
    accs = load_queue(queue_path)
    if not accs:
        print(f"File locale vide ({queue_path}). Rien a pousser.")
        return 0

    try:
        state = remote_state(accs)
    except MpUnreachable as exc:
        print(f"MP INJOIGNABLE ({exc}).\n"
              "Monter le VPN puis relancer : sudo vpn up && sra_to_add.py --push --apply\n"
              "La file locale est intacte, rien n'a ete perdu.", file=sys.stderr)
        return 2

    already = [a for a in accs if a in state["samples"]]
    annotated = [a for a in accs if a in state["annotated"]]
    todo = [a for a in accs if a not in state["samples"] and a not in state["annotated"]]

    print(f"File locale : {len(accs)} accession(s)")
    print(f"  deja dans samples.tsv : {len(already)}")
    print(f"  deja annotees sur mp  : {len(annotated)}"
          + ("  <- relever avec /fetch-tbannotator" if annotated else ""))
    print(f"  a ajouter             : {len(todo)}")
    if not todo:
        print("\nRien a ajouter. Vider la file locale si le travail est termine.")
        return 0
    for a in todo:
        print(f"    + {a}")

    if not apply:
        print("\nDry-run. Relancer avec --apply pour ecrire sur mp.")
        return 0

    # Fusion cote local, puis ecriture atomique cote distant. On preserve TOUTES
    # les lignes existantes dans leur ordre (candidats en vol des autres
    # campagnes) et on ne dedoublonne que sur le premier champ.
    samples_path = quote_remote_path(_samples_path)
    current = ssh(f"cat {samples_path} 2>/dev/null || true").splitlines()
    body, seen = [], set()
    for line in current:
        if not line.strip():
            continue
        key = line.split("\t")[0].strip().upper()
        if key == "ACCESSION" or key in seen:
            continue
        seen.add(key)
        body.append(line.rstrip("\n"))
    added = [a for a in todo if a not in seen]
    merged = "accession\n" + "\n".join(body + added) + "\n"

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = quote_remote_path(f"{_samples_path}.bak_{stamp}")
    temporary_path = quote_remote_path(f"/tmp/samples_merged_{stamp}.tsv")
    ssh(f"cp {samples_path} {backup_path}")
    ssh(f"cat > {temporary_path}", stdin=merged)
    check = ssh(f"wc -l < {temporary_path}").strip()
    expected = len(body) + len(added) + 1
    if int(check) != expected:
        print(f"ABANDON : le fichier transfere fait {check} lignes au lieu de {expected}. "
              f"{_samples_path} n'a PAS ete modifie (sauvegarde .bak_{stamp}).",
              file=sys.stderr)
        return 2
    ssh(f"mv {temporary_path} {samples_path}")
    final = ssh(f"wc -l < {samples_path}").strip()

    print(f"\n{len(added)} accession(s) ajoutee(s). {_samples_path} : {final} lignes "
          f"(sauvegarde {_samples_path}.bak_{stamp}).")
    save_queue(queue_path, [])
    print(f"File locale videe ({queue_path}).")
    print("\nLE PIPELINE N'A PAS ETE LANCE, et ce script ne le lancera jamais.\n"
          "Lancer mobilise un serveur partage pour des jours et embarque TOUT samples.tsv,\n"
          "y compris le travail d'autres campagnes. Verifier d'abord qu'aucun run ne tourne :\n"
          f"  ssh {SSH_HOST} 'ps -eo user,pid,lstart,cmd | grep \"[s]nakemake\"'   # LIRE les lignes, pas compter\n"
          "puis, seulement sur decision explicite :\n"
          f"  ssh {SSH_HOST} 'cd {RUN_DIR} && nohup ./script.sh > /tmp/snakemake_$(date +%Y%m%d).log 2>&1 & disown'")
    return 0


# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accessions", nargs="*", help="accessions SRR/ERR/DRR/CUS")
    ap.add_argument("--file", help="fichier d'accessions (une par ligne, ou TSV)")
    ap.add_argument("--check", action="store_true", help="pre-vol seul, aucune ecriture")
    ap.add_argument("--queue", action="store_true", help="empiler dans la file locale")
    ap.add_argument("--list", action="store_true", help="afficher la file locale")
    ap.add_argument("--push", action="store_true", help="pousser la file locale vers mp")
    ap.add_argument("--apply", action="store_true", help="avec --push : ecrire reellement")
    ap.add_argument("--queue-file", help="chemin explicite de la file locale")
    ap.add_argument("--samples", help="chemin distant de samples.tsv (pour tester sur une COPIE, "
                                      f"defaut {SAMPLES})")
    args = ap.parse_args()

    global _samples_path
    if args.samples:
        _samples_path = args.samples
        print(f"[MODE TEST] cible d'ecriture : {_samples_path} (pas la file de production)")

    queue_path = find_queue(args.queue_file)

    if args.list:
        accs = load_queue(queue_path)
        print(f"{queue_path} : {len(accs)} accession(s)")
        for a in accs:
            print(f"  {a}")
        return 0

    if args.push:
        return push(queue_path, args.apply)

    accs = read_accessions(args)
    if not accs:
        ap.error("aucune accession (passer des arguments, --file, ou utiliser --list/--push)")

    try:
        remote = remote_state(accs)
    except MpUnreachable as exc:
        print(f"AVERTISSEMENT : mp injoignable ({exc}).\n"
              "  Le pre-vol ENA a bien tourne, mais l'etat de la file et des annotations\n"
              "  reste INCONNU : monter le VPN (sudo vpn up) avant de conclure.",
              file=sys.stderr)
        remote = None
    except RuntimeError as exc:
        print(f"AVERTISSEMENT : etat distant illisible ({exc}).", file=sys.stderr)
        remote = None

    rows = preflight(accs, remote)
    render(rows)

    if args.queue:
        keep = [r["accession"] for r in rows
                if r["statut"] in ("A_AJOUTER", "MP_INJOIGNABLE")]
        # Une accession qualifiee DEJA_ANNOTE / DEJA_EN_FILE est retiree de la file
        # locale si elle y trainait d'un passage precedent : la garder ferait croire
        # a du travail restant. `--push` la sauterait de toute facon, mais autant que
        # `--list` dise la verite.
        settled = {r["accession"] for r in rows
                   if r["statut"] in ("DEJA_ANNOTE", "DEJA_EN_FILE")}
        existing = [a for a in load_queue(queue_path) if a not in settled]
        merged = existing + [a for a in keep if a not in existing]
        save_queue(queue_path, merged)
        print(f"\nFile locale {queue_path} : {len(existing)} -> {len(merged)} accession(s).")
        print("Pousser vers mp : sra_to_add.py --push  (puis --push --apply)")

    # Code 1 = quelque chose est a REFUSER ou a verifier avant d'engager du calcul.
    # Un simple avertissement sur une accession valide (taille, organisme declare)
    # est affiche mais ne fait pas echouer : sinon tout appel finirait en code 1.
    refused = [r for r in rows if r["statut"] in ("INVALIDE", "DOUTEUSE")]
    return 1 if refused else 0


if __name__ == "__main__":
    sys.exit(main())
