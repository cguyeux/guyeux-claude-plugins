"""Pinned modern-human-reference-panels snapshot.

Use the harmonised HGDP+1kGP sample metadata (TSV). Point the client at it:

    export MHRP_FILE=/path/to/hgdp_tgp_meta.tsv

(The genotype VCFs themselves live in gnomAD / 1kGP; this client handles the
sample-level metadata table that downstream geography/population joins need.)
"""
from ._base import Snapshot

SNAPSHOTS = {
    "hgdp_tgp": Snapshot(
        version="hgdp_tgp",
        url=None,
        filename="hgdp_tgp_meta.tsv",
        doi="https://doi.org/10.1126/science.aay5012",
        license="open (HGDP+1kGP harmonised release)",
    ),
}

DEFAULT_VERSION = "hgdp_tgp"
