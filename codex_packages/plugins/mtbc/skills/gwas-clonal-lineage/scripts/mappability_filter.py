#!/usr/bin/env python3
"""mappability_filter.py -- flag GWAS hits sitting in a paralogous / repeated region of the
reference genome, where short-read cross-mapping can fabricate a SNP call.

Generalises `tissue_tropism_mtbc/analyses/phase5_mappability.py`. The KB lesson this closes
(tuberculosis.md, "LE FILTRE QUI A TOUT TUE : mappabilite/paralogie") : on a documented TBM-
vs-pulmonary GWAS, 10/10 replicated GAIN candidates across two independent cohorts sat in
paralogous regions (esx family, pps operon, lpp tandem duplication) -- replication across
cohorts did NOT disculpate the artefact, because the SAME reference-genome paralogy and the
SAME calling pipeline produced it identically in both cohorts. Any family that recurs across
short-read MTBC GWAS studies (PE/PPE, esx, pks/pps, lpp, IS elements) is the ~10% of the
genome that is not uniquely mappable at Illumina read length -- treat a hit there as the
top suspect for cross-mapping, not as a stronger replicated signal.

Method: extract a window of `read_length` bp centred on each candidate SNP position, BLAST
it against the reference genome. A hit elsewhere in the genome at >=`min_identity`% over
>=`min_length` bp (excluding the self-hit at the query's own position) means reads from
that other locus could misalign onto the candidate -- PARALOG-RISK. Requires `blastn` and
`makeblastdb` (NCBI BLAST+) on PATH.

CLI:
    python mappability_filter.py <genome.fasta> <candidates.tsv> [--half-window 50]
        [--min-identity 80] [--min-length 50] [--out results.tsv]

`candidates.tsv`: two columns, `name<TAB>position` (1-based, SPDI-style coordinate on the
reference). No header.
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MappabilityVerdict:
    name: str
    position: int
    n_hits_total: int
    n_paralogs: int
    best_paralog_identity: float | None
    best_paralog_length: int | None
    best_paralog_position: int | None
    verdict: str  # "unique-mappable" | "PARALOG-RISK"


def load_genome(fasta_path: Path) -> str:
    seq = []
    with open(fasta_path) as f:
        for line in f:
            if not line.startswith(">"):
                seq.append(line.strip())
    return "".join(seq).upper()


def extract_window(genome: str, position_1based: int, half_window: int) -> str:
    """1-based SPDI-style position -> 0-based slice, `2*half_window+1` bp centred window."""
    start = max(position_1based - 1 - half_window, 0)
    end = position_1based - 1 + half_window + 1
    return genome[start:end]


def run_blast(genome_fasta: Path, queries: dict[str, str], *, evalue: str = "1e-3") -> dict[str, list[dict]]:
    with tempfile.TemporaryDirectory() as tmp:
        db = f"{tmp}/db"
        subprocess.run(
            ["makeblastdb", "-in", str(genome_fasta), "-dbtype", "nucl", "-out", db],
            check=True, capture_output=True,
        )
        qf = f"{tmp}/queries.fasta"
        with open(qf, "w") as f:
            for name, seq in queries.items():
                f.write(f">{name}\n{seq}\n")
        res = subprocess.run(
            ["blastn", "-task", "blastn", "-query", qf, "-db", db,
             "-evalue", evalue, "-dust", "no",
             "-outfmt", "6 qseqid sstart send pident length bitscore"],
            check=True, capture_output=True, text=True,
        )
    hits: dict[str, list[dict]] = {}
    for line in res.stdout.strip().split("\n"):
        if not line:
            continue
        q, ss, se, pid, ln, bit = line.split("\t")
        hits.setdefault(q, []).append({
            "sstart": int(ss), "send": int(se),
            "pident": float(pid), "length": int(ln), "bit": float(bit),
        })
    return hits


def classify(position: int, hits: list[dict], *, min_identity: float, min_length: int) -> dict:
    self_hits = [h for h in hits if min(h["sstart"], h["send"]) <= position <= max(h["sstart"], h["send"])]
    others = [h for h in hits if h not in self_hits]
    paralogs = [h for h in others if h["pident"] >= min_identity and h["length"] >= min_length]
    best = max(paralogs, key=lambda h: h["pident"]) if paralogs else None
    return {
        "n_hits_total": len(hits), "n_paralogs": len(paralogs),
        "best_paralog_identity": best["pident"] if best else None,
        "best_paralog_length": best["length"] if best else None,
        "best_paralog_position": min(best["sstart"], best["send"]) if best else None,
        "verdict": "PARALOG-RISK" if paralogs else "unique-mappable",
    }


def check_mappability(
    genome_fasta: Path,
    candidates: list[tuple[str, int]],
    *,
    half_window: int = 50,
    min_identity: float = 80.0,
    min_length: int = 50,
) -> list[MappabilityVerdict]:
    """Main entry point. `candidates`: list of `(name, 1-based position)`."""
    genome = load_genome(genome_fasta)
    queries = {name: extract_window(genome, pos, half_window) for name, pos in candidates}
    hits = run_blast(genome_fasta, queries)
    out = []
    for name, pos in candidates:
        c = classify(pos, hits.get(name, []), min_identity=min_identity, min_length=min_length)
        out.append(MappabilityVerdict(name=name, position=pos, **c))
    return out


def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("genome_fasta", type=Path)
    ap.add_argument("candidates_tsv", type=Path)
    ap.add_argument("--half-window", type=int, default=50)
    ap.add_argument("--min-identity", type=float, default=80.0)
    ap.add_argument("--min-length", type=int, default=50)
    ap.add_argument("--out", type=Path, default=Path("mappability_results.tsv"))
    args = ap.parse_args()

    candidates = []
    with open(args.candidates_tsv) as f:
        for row in csv.reader(f, delimiter="\t"):
            if not row:
                continue
            candidates.append((row[0], int(row[1])))

    results = check_mappability(
        args.genome_fasta, candidates,
        half_window=args.half_window, min_identity=args.min_identity, min_length=args.min_length,
    )
    with open(args.out, "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["name", "position", "n_hits_total", "n_paralogs",
                    "best_paralog_identity", "best_paralog_length", "best_paralog_position", "verdict"])
        for r in results:
            w.writerow([r.name, r.position, r.n_hits_total, r.n_paralogs,
                        r.best_paralog_identity, r.best_paralog_length, r.best_paralog_position, r.verdict])
    n_risk = sum(1 for r in results if r.verdict == "PARALOG-RISK")
    print(f"{n_risk}/{len(results)} candidat(s) PARALOG-RISK -> {args.out}")


if __name__ == "__main__":
    _main()
