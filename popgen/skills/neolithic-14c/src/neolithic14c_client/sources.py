"""Pinned NERD (Neolithic Radiocarbon Dates) snapshot.

NERD ships as a single CSV on GitHub, so the client CAN auto-download it (and cache
it). For a perfectly reproducible pin, record the commit and set NEOLITHIC_14C_FILE
to a mirrored copy instead.
"""
from ._base import Snapshot

SNAPSHOTS = {
    "NERD": Snapshot(
        version="NERD",
        url="https://raw.githubusercontent.com/apalmisano82/NERD/master/nerd.csv",
        sha256=None,                    # repo updates over time; pin a commit for full reproducibility
        filename="nerd.csv",
        doi="https://doi.org/10.5334/joad.61",
        license="CC BY 4.0",
    ),
}

DEFAULT_VERSION = "NERD"
