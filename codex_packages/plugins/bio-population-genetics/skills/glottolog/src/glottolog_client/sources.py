"""Pinned Glottolog snapshot.

Glottolog has no dynamic API; download a CLDF release (or the pyglottolog
`languoids.csv`) and point the client at the languages table:

    export GLOTTOLOG_FILE=/path/to/glottolog-cldf/cldf/languages.csv
"""
from ._base import Snapshot

SNAPSHOTS = {
    "cldf": Snapshot(
        version="cldf",
        url=None,
        filename="glottolog_languages.csv",
        doi="https://doi.org/10.5281/zenodo.8131084",
        license="CC BY 4.0",
    ),
}

DEFAULT_VERSION = "cldf"
