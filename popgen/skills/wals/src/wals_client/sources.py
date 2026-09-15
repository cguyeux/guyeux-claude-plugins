"""Pinned WALS snapshot.

WALS has no public REST API; download the CLDF release and point the client at the
languages table:

    export WALS_FILE=/path/to/wals-cldf/cldf/languages.csv
"""
from ._base import Snapshot

SNAPSHOTS = {
    "cldf": Snapshot(
        version="cldf",
        url=None,
        filename="wals_languages.csv",
        doi="https://doi.org/10.5281/zenodo.7385533",
        license="CC BY 4.0",
    ),
}

DEFAULT_VERSION = "cldf"
