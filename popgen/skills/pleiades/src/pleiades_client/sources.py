"""Pinned Pleiades snapshot.

Pleiades publishes daily gzipped CSV dumps, so the client CAN auto-download the
places table (and cache it). "latest" is a moving target: record the access date,
or mirror a copy and set PLEIADES_FILE for a reproducible pin.
"""
from ._base import Snapshot

SNAPSHOTS = {
    "latest": Snapshot(
        version="latest",
        url="https://atlantides.org/downloads/pleiades/dumps/pleiades-places-latest.csv.gz",
        sha256=None,                    # daily dump; mirror + pin for full reproducibility
        filename="pleiades-places-latest.csv.gz",
        doi="https://pleiades.stoa.org/",
        license="CC BY 3.0",
    ),
}

DEFAULT_VERSION = "latest"
