#!/usr/bin/env python3
"""Classify one or more query genomes against a curated panel of type-strain
genomes by whole-genome ANI (skani), and assign each query to the panel's
group label (clade, species, sublineage...) of its best-matching reference.

Genus-agnostic: the panel (clade/group definitions, species, type strains,
GenBank/RefSeq accessions) is supplied as a TSV, never hardcoded here. This
is the runner prescribed but never executed by the MTBC anti-false-positive
taxonomic guard-fou (skani vs a panel including outgroups), generalised so
any project under codes/ can reuse it with its own panel.

Panel TSV columns (tab-separated, header required):
    group       clade/group label assigned to a query matching this reference
    species     binomial name (free text)
    strain      strain designation (free text)
    accession   GenBank/RefSeq assembly accession (GCA_/GCF_...)
    source      short citation key or DOI for where this type-strain
                assignment comes from (traceability, not used for logic)

Requires: skani on PATH, curl on PATH (NCBI Datasets REST API v2, no
`datasets` CLI dependency).
"""
import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

NCBI_DATASETS_DOWNLOAD = (
    "https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession/{accession}/download"
    "?include_annotation_type=GENOME_FASTA"
)
NCBI_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=assembly&retmode=json&term={term}"
NCBI_ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=assembly&retmode=json&id={ids}"
ASSEMBLY_ACCESSION_RE = re.compile(r"^GC[AF]_\d{9}\.\d+$")


class DownloadFailed(Exception):
    """One panel/query genome could not be resolved or hydrated. Caller
    decides whether that is fatal (query) or just excludes this one
    reference (panel)."""


def load_panel(panel_tsv: Path) -> list[dict]:
    with open(panel_tsv, newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    required = {"group", "species", "strain", "accession"}
    missing = required - set(rows[0].keys()) if rows else required
    if missing:
        sys.exit(f"panel {panel_tsv}: colonnes manquantes {sorted(missing)}")
    return rows


def _curl_json(url: str) -> dict:
    result = subprocess.run(["curl", "-sS", "-f", url], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def resolve_assembly_accession(accession: str) -> str:
    """Resolve a WGS-master or nucleotide/contig accession to its GCA_/GCF_
    assembly accession via NCBI ESearch+ESummary (db=assembly). Accessions
    already in GCA_/GCF_ form are returned unchanged, no network call.

    The NCBI Datasets v2 download endpoint silently accepts a WGS-master
    accession (HTTP 200) but returns a tiny DEHYDRATED stub (no sequence,
    `grpc-metadata-logging-hydrated: 0`) instead of the genome — this
    resolution step exists because that failure mode has no error status to
    catch on, only a suspiciously small zip.
    """
    if ASSEMBLY_ACCESSION_RE.match(accession):
        return accession
    stripped = re.sub(r"^[A-Z]{1,3}_", "", accession)  # NZ_/NC_... ne matchent pas toujours l'index assembly
    # Une accession WGS complète (AAAA00000000) échoue parfois la ou seul le prefixe
    # WGS+version (AAAA02, 6 caracteres) est indexe -- ex. mesure 2026-09-18 sur
    # NZ_AHMM02000000 (L. inadai) : "AHMM02000000" ne resout rien, "AHMM02" resout.
    search_terms = [accession, stripped, stripped[:6], stripped[:4]]
    seen = set()
    ids = []
    search_term = accession
    for term in search_terms:
        if not term or term in seen:
            continue
        seen.add(term)
        if term != search_terms[0]:
            time.sleep(0.34)
        ids = _curl_json(NCBI_ESEARCH.format(term=term)).get("esearchresult", {}).get("idlist", [])
        if ids:
            search_term = term
            break
    if not ids:
        raise DownloadFailed(f"{accession} : non résolu en accession d'assemblage (ESearch db=assembly vide, "
                              f"essayé {search_terms})")
    time.sleep(0.34)  # NCBI E-utilities sans clé : max ~3 req/s
    summary = _curl_json(NCBI_ESUMMARY.format(ids=",".join(ids)))
    candidates = [summary["result"][uid] for uid in ids if uid in summary.get("result", {})]
    candidates = [c for c in candidates if c.get("assemblyaccession")]
    if not candidates:
        raise DownloadFailed(f"{accession} : ESummary sans assemblyaccession exploitable")
    if len(candidates) > 1:
        # Plusieurs assemblages partagent le même terme de recherche (ex. plusieurs releases
        # d'un même projet WGS) : départager par le préfixe WGS exact plutôt que prendre le
        # premier au hasard.
        wgs_prefix = search_term[:6].upper()
        matching = [c for c in candidates if str(c.get("wgs", "")).upper().startswith(wgs_prefix)]
        if matching:
            candidates = matching
    refseq = [c for c in candidates if c["assemblyaccession"].startswith("GCF_")]
    chosen = (refseq or candidates)[0]
    resolved = chosen["assemblyaccession"]
    print(f"  {accession} -> {resolved} ({chosen.get('organism', '?')}, {chosen.get('assemblyname', '?')})",
          file=sys.stderr)
    return resolved


def _try_download_hydrated(dl_accession: str, dest: Path) -> bool:
    """Attempt one hydrated download of `dl_accession` into `dest`. Returns
    True on success (dest written), False on a DEHYDRATED response (small
    stub zip, no .fna — NCBI's silent failure mode for a superseded or
    otherwise non-hydratable assembly version)."""
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "genome.zip"
        url = NCBI_DATASETS_DOWNLOAD.format(accession=dl_accession)
        subprocess.run(["curl", "-sS", "-f", "-L", "-o", str(zip_path), url], check=True)
        try:
            with zipfile.ZipFile(zip_path) as zf:
                fna_members = [n for n in zf.namelist() if n.endswith(".fna")]
                if not fna_members:
                    return False
                zf.extract(fna_members[0], tmp)
                shutil.move(str(Path(tmp) / fna_members[0]), dest)
                return True
        except zipfile.BadZipFile:
            return False


def ensure_panel_genome(accession: str, cache_dir: Path) -> Path:
    """Download+cache one genome's FASTA, keyed by its ORIGINAL accession (so
    the panel TSV / query argument and the cache stay in sync even when the
    accession had to be resolved). Raises DownloadFailed if no hydratable
    assembly version could be found.

    NCBI's v2 download endpoint sometimes returns a DEHYDRATED stub (tiny
    zip, no sequence, `grpc-metadata-logging-hydrated: 0`) for a specific
    assembly VERSION that has since been superseded (`assemblyStatus:
    "previous"` in its own report), even though ESummary still lists that
    exact version as current — ESummary and the download endpoint disagree.
    Observed on GCF_000243815.1 (superseded by .2) resolved from
    NZ_AHMT00000000. Mitigation: bump the trailing version a few times.
    """
    fasta = cache_dir / f"{accession}.fasta"
    if fasta.exists() and fasta.stat().st_size > 0:
        return fasta
    cache_dir.mkdir(parents=True, exist_ok=True)
    dl_accession = resolve_assembly_accession(accession)

    candidates = [dl_accession]
    m = re.match(r"^(GC[AF]_\d{9})\.(\d+)$", dl_accession)
    if m:
        prefix, version = m.group(1), int(m.group(2))
        candidates += [f"{prefix}.{v}" for v in range(version + 1, version + 4)]

    for attempt in candidates:
        if _try_download_hydrated(attempt, fasta):
            if attempt != dl_accession:
                print(f"  {accession} : {dl_accession} déshydraté, {attempt} utilisé à la place",
                      file=sys.stderr)
            return fasta
    raise DownloadFailed(
        f"{accession} ({dl_accession}) : aucune version hydratable trouvée "
        f"(essayé {', '.join(candidates)})"
    )


def run_skani(query_paths: list[Path], ref_paths: list[Path], threads: int, mode: str) -> str:
    mode_flag = {"fast": "--fast", "medium": "--medium", "slow": "--slow"}[mode]
    cmd = [
        "skani", "dist",
        "-q", *[str(p) for p in query_paths],
        "-r", *[str(p) for p in ref_paths],
        "-t", str(threads),
        mode_flag,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"skani a échoué :\n{result.stderr}")
    return result.stdout


def parse_skani_tsv(stdout: str) -> list[dict]:
    lines = [l for l in stdout.splitlines() if l and not l.startswith("[")]
    if not lines:
        return []
    reader = csv.DictReader(lines, delimiter="\t")
    return list(reader)


def classify(hits: list[dict], panel_by_accession: dict, min_af: float) -> dict:
    """Group skani hits by query, keep the best hit per query above min_af."""
    by_query: dict[str, list[dict]] = {}
    for h in hits:
        # skani names the ref/query columns by filename stem; match back to accession
        ref_acc = Path(h["Ref_file"]).stem
        panel_row = panel_by_accession.get(ref_acc)
        if panel_row is None:
            continue
        af = min(float(h["Align_fraction_ref"]), float(h["Align_fraction_query"]))
        if af < min_af:
            continue
        by_query.setdefault(h["Query_file"], []).append(
            {**h, "align_fraction_min": af, "panel": panel_row}
        )
    verdicts = {}
    for query, query_hits in by_query.items():
        query_hits.sort(key=lambda h: float(h["ANI"]), reverse=True)
        verdicts[query] = query_hits
    return verdicts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="+", type=Path, help="génome(s) FASTA à classer")
    ap.add_argument("--panel", required=True, type=Path, help="TSV du panel (group, species, strain, accession, source)")
    ap.add_argument("--cache-dir", type=Path, default=Path.home() / ".cache" / "ani-panel-classify",
                     help="répertoire de cache des génomes du panel téléchargés")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--mode", choices=["fast", "medium", "slow"], default="slow",
                     help="préréglage skani ; 'slow' par défaut car ce runner sert à comparer des "
                          "génomes DIVERGENTS entre clades/groupes, pas des souches proches")
    ap.add_argument("--min-af", type=float, default=15.0,
                     help="fraction alignée minimale (%%, min des deux sens) pour retenir un hit ; "
                          "en dessous, l'ANI n'est pas interprétable (trop peu de génome partagé)")
    ap.add_argument("-o", "--output", type=Path, help="TSV de sortie (défaut : stdout, tableau lisible)")
    args = ap.parse_args()

    panel = load_panel(args.panel)
    panel_by_accession = {row["accession"]: row for row in panel}

    ref_paths = []
    skipped = []
    for row in panel:
        try:
            ref_paths.append(ensure_panel_genome(row["accession"], args.cache_dir))
        except DownloadFailed as e:
            skipped.append((row["accession"], row["species"], str(e)))
    if skipped:
        print(f"AVERTISSEMENT : {len(skipped)}/{len(panel)} référence(s) du panel non téléchargeable(s), "
              f"exclue(s) de ce classement (pas de la définition du panel) :", file=sys.stderr)
        for acc, species, msg in skipped:
            print(f"  - {species} ({acc}) : {msg}", file=sys.stderr)
    if not ref_paths:
        sys.exit("Aucune référence du panel n'a pu être téléchargée — rien à classer.")
    # skani identifies refs/queries by filename stem; rename cached refs to <accession>.fasta
    # already done by ensure_panel_genome, so Ref_file stem == accession.

    stdout = run_skani(args.query, ref_paths, args.threads, args.mode)
    hits = parse_skani_tsv(stdout)
    if not hits:
        print("Aucun hit skani au-dessus du seuil (--min-af) : requêtes trop divergentes du panel, ou panel vide.",
              file=sys.stderr)
        sys.exit(1)

    verdicts = classify(hits, panel_by_accession, args.min_af)

    rows_out = []
    for query in [str(q) for q in args.query]:
        query_hits = verdicts.get(query, [])
        if not query_hits:
            rows_out.append({
                "query": query, "verdict_group": "NON_CLASSE", "best_species": "",
                "best_strain": "", "best_accession": "", "ani": "", "align_fraction_min": "",
                "note": "aucun hit exploitable au-dessus de --min-af",
            })
            continue
        best = query_hits[0]
        rows_out.append({
            "query": query,
            "verdict_group": best["panel"]["group"],
            "best_species": best["panel"]["species"],
            "best_strain": best["panel"]["strain"],
            "best_accession": best["panel"]["accession"],
            "ani": best["ANI"],
            "align_fraction_min": f"{best['align_fraction_min']:.2f}",
            "note": "",
        })

    fieldnames = ["query", "verdict_group", "best_species", "best_strain", "best_accession", "ani", "align_fraction_min", "note"]
    if args.output:
        with open(args.output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows_out)
        print(f"Résultats écrits : {args.output}", file=sys.stderr)
    else:
        widths = {k: max(len(k), *(len(str(r[k])) for r in rows_out)) for k in fieldnames}
        print("  ".join(k.ljust(widths[k]) for k in fieldnames))
        for r in rows_out:
            print("  ".join(str(r[k]).ljust(widths[k]) for k in fieldnames))

    for query in [str(q) for q in args.query]:
        query_hits = verdicts.get(query, [])
        if len(query_hits) >= 2:
            top, second = query_hits[0], query_hits[1]
            if top["panel"]["group"] != second["panel"]["group"] and \
               float(top["ANI"]) - float(second["ANI"]) < 1.0:
                print(f"AVERTISSEMENT {query} : les deux meilleurs hits (groupes "
                      f"{top['panel']['group']!r} et {second['panel']['group']!r}) sont à moins de "
                      f"1 point d'ANI l'un de l'autre — placement incertain, à confirmer autrement.",
                      file=sys.stderr)


if __name__ == "__main__":
    main()
