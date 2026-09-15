"""Pinned AmtDB snapshot.

AmtDB has no public REST API; download the samples CSV from amtdb.org and pin it:

    export AMTDB_FILE=/path/to/amtdb_samples_v1.009.csv
"""
from ._base import Snapshot

SNAPSHOTS = {
    "v1.009": Snapshot(
        version="v1.009",
        url=None,
        filename="amtdb_samples.csv",
        doi="https://doi.org/10.1093/nar/gky843",
        license="amtdb.org terms (academic use)",
    ),
}

DEFAULT_VERSION = "v1.009"
