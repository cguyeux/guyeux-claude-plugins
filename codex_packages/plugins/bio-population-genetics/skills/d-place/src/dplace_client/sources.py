"""Pinned D-PLACE snapshot.

D-PLACE has no public REST API; clone the data repo and point the client at the
unified societies table:

    git clone https://github.com/D-PLACE/dplace-data.git
    export DPLACE_FILE=/path/to/dplace-data/csv/societies.csv
"""
from ._base import Snapshot

SNAPSHOTS = {
    "v2": Snapshot(
        version="v2",
        url=None,
        filename="dplace_societies.csv",
        doi="https://doi.org/10.1038/sdata.2016.7",
        license="CC BY 4.0",
    ),
}

DEFAULT_VERSION = "v2"
