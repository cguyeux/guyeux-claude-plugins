"""Pinned p3k14c snapshot.

p3k14c has no stable per-file URL (download `p3k14c_raw.csv` from tDAR). Pin the
version and point the client at the downloaded file:

    export P3K14C_FILE=/path/to/p3k14c_raw.csv
"""
from ._base import Snapshot

SNAPSHOTS = {
    "v1": Snapshot(
        version="v1",
        url=None,
        filename="p3k14c_raw.csv",
        doi="https://doi.org/10.1038/s41597-022-01118-7",
        license="CC BY 4.0",
    ),
}

DEFAULT_VERSION = "v1"
