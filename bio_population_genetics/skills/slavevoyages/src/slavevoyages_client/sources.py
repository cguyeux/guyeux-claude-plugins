"""Pinned SlaveVoyages snapshots.

The public REST API requires authentication; the reproducible path is the CSV
download of the Trans-Atlantic Voyages dataset
(slavevoyages.org/voyage/database#downloads). No stable per-file URL, so we pin a
version label and require an explicit local file:

    export SLAVEVOYAGES_FILE=/path/to/tast_voyages.csv

With neither file nor cache, the client falls back to the bundled fixture (offline
tests only) and otherwise raises DatasetUnavailable with download instructions.
"""
from ._base import Snapshot

SNAPSHOTS = {
    "tast": Snapshot(
        version="tast",
        url=None,                       # CSV download, see module docstring
        filename="tast_voyages.csv",
        doi="https://www.slavevoyages.org/voyage/database",
        license="slavevoyages.org terms (academic use)",
    ),
}

DEFAULT_VERSION = "tast"
