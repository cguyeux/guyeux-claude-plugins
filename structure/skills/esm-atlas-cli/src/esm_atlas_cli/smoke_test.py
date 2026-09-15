"""End-to-end smoke test: fetch katG (H37Rv Rv1908c), exercise the API.

Pulls the CDS sequence from
    ~/docs/codes/mtbc/investigate_phylo/resources/NC_000962.3_CDS.fasta
translates it (the file holds DNA CDS), hashes the protein, then exercises
lookup / cluster.

Run with:
    python -m esm_atlas_cli.smoke_test
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from .client import EsmAtlasClient, EsmAtlasError, EsmAtlasUnavailable, hash_sequence


OFFLINE = os.environ.get("ESM_ATLAS_OFFLINE", "0") == "1"


CDS_FASTA = Path("~/docs/codes/mtbc/investigate_phylo/resources/NC_000962.3_CDS.fasta").expanduser()

CODON_TABLE = {
    # The MTBC translation table (11). Mostly standard genetic code; alternative
    # start codons (GTG, TTG) all code for Met when used as initiator. After
    # initiator, GTG = Val and TTG = Leu.
    "TTT": "F", "TTC": "F", "TTA": "L", "TTG": "L",
    "CTT": "L", "CTC": "L", "CTA": "L", "CTG": "L",
    "ATT": "I", "ATC": "I", "ATA": "I", "ATG": "M",
    "GTT": "V", "GTC": "V", "GTA": "V", "GTG": "V",
    "TCT": "S", "TCC": "S", "TCA": "S", "TCG": "S",
    "CCT": "P", "CCC": "P", "CCA": "P", "CCG": "P",
    "ACT": "T", "ACC": "T", "ACA": "T", "ACG": "T",
    "GCT": "A", "GCC": "A", "GCA": "A", "GCG": "A",
    "TAT": "Y", "TAC": "Y", "TAA": "*", "TAG": "*",
    "CAT": "H", "CAC": "H", "CAA": "Q", "CAG": "Q",
    "AAT": "N", "AAC": "N", "AAA": "K", "AAG": "K",
    "GAT": "D", "GAC": "D", "GAA": "E", "GAG": "E",
    "TGT": "C", "TGC": "C", "TGA": "*", "TGG": "W",
    "CGT": "R", "CGC": "R", "CGA": "R", "CGG": "R",
    "AGT": "S", "AGC": "S", "AGA": "R", "AGG": "R",
    "GGT": "G", "GGC": "G", "GGA": "G", "GGG": "G",
}


def _translate(dna: str) -> str:
    dna = dna.upper().replace("U", "T")
    aa: list[str] = []
    if dna[:3] in {"GTG", "TTG"}:
        aa.append("M")
        i = 3
    else:
        i = 0
    while i + 3 <= len(dna):
        codon = dna[i:i+3]
        c = CODON_TABLE.get(codon, "X")
        if c == "*":
            break
        aa.append(c)
        i += 3
    return "".join(aa)


def _extract_cds(gene_name: str) -> str | None:
    """Return the DNA CDS of the named gene from the bundled fasta."""
    if not CDS_FASTA.exists():
        print(f"FAIL: CDS fasta not found at {CDS_FASTA}", file=sys.stderr)
        return None
    in_target = False
    chunks: list[str] = []
    needle = f"[gene={gene_name}]"
    with CDS_FASTA.open() as f:
        for line in f:
            if line.startswith(">"):
                if in_target:
                    break
                in_target = needle in line
                continue
            if in_target:
                chunks.append(line.strip())
    return "".join(chunks) if chunks else None


def main() -> int:
    gene = "katG"
    print(f"== {gene} smoke test ==")

    dna = _extract_cds(gene)
    if dna is None:
        print(f"could not find {gene} CDS in {CDS_FASTA}", file=sys.stderr)
        return 1
    protein = _translate(dna)
    h = hash_sequence(protein)
    print(f"  DNA  length: {len(dna)} nt")
    print(f"  prot length: {len(protein)} aa")
    print(f"  hash:        {h}")
    print(f"  prot[:60]:   {protein[:60]}")

    with EsmAtlasClient() as client:
        try:
            data = client.lookup(h, topk_features=5)
            print("\n-- lookup OK --")
            features = data.get("sae_features") or []
            for f in features[:5]:
                idx = f.get("index") or f.get("feature_index")
                act = f.get("activation") or f.get("value")
                label = f.get("label") or f.get("description") or ""
                act_str = f"{act:.3f}" if isinstance(act, (int, float)) else str(act)
                print(f"  feature {idx}: act={act_str}  {str(label)[:80]}")
            rep_hash = data.get("cluster_rep_protein_hash")
            print(f"\n  cluster rep hash: {rep_hash or '(this protein is a rep)'}")
            print(f"  api version:      {client.last_seen_api_version or 'not advertised'}")
        except EsmAtlasUnavailable as e:
            if OFFLINE:
                print(f"  OFFLINE degradation OK (clean EsmAtlasUnavailable): {e}")
                print("\nDone (offline: local logic + graceful degradation verified).")
                return 0
            print(f"  API unavailable: {e}", file=sys.stderr)
            return 3
        except EsmAtlasError as e:
            print(f"  API error: {e}", file=sys.stderr)
            return 2

        try:
            target = rep_hash or h
            cl = client.cluster(target)
            print(f"\n-- cluster OK (queried {target[:12]}...) --")
            print(f"  cluster_size:               {cl.get('cluster_size') or cl.get('size')}")
            print(f"  cluster_pct_characterized:  {cl.get('cluster_pct_characterized')}")
            members = cl.get("members") or cl.get("member_hashes") or []
            print(f"  members in payload:         {len(members) if hasattr(members, '__len__') else '?'}")
        except EsmAtlasError as e:
            print(f"  cluster error: {e}", file=sys.stderr)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
