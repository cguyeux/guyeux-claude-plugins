"""Pinned ORBIS v2 snapshots (two tables: nodes and edges).

ORBIS has no REST API. The static node/edge tables are deposited on the Stanford
Digital Repository (purl.stanford.edu/mn425tz9757, CC BY 3.0) and mirrored on
GitHub (github.com/emeeks/orbis_v2). There is no single stable per-file URL, so we
pin the version and require explicit local files:

    # from the Stanford deposit or the orbis_v2 repo:
    export ORBIS_NODES_FILE=/path/to/orbis_nodes.csv
    export ORBIS_EDGES_FILE=/path/to/orbis_edges.csv

With neither file nor cache, the client falls back to the bundled fixtures
(offline tests only) and otherwise raises DatasetUnavailable with instructions.
"""
from ._base import Snapshot

NODE_SNAPSHOTS = {
    "v2": Snapshot(
        version="v2",
        url=None,                       # manual download (see module docstring)
        filename="orbis_nodes.csv",
        doi="https://purl.stanford.edu/mn425tz9757",
        license="CC BY 3.0",
    ),
}

EDGE_SNAPSHOTS = {
    "v2": Snapshot(
        version="v2",
        url=None,
        filename="orbis_edges.csv",
        doi="https://purl.stanford.edu/mn425tz9757",
        license="CC BY 3.0",
    ),
}

DEFAULT_VERSION = "v2"
