"""Pinned AADR snapshots.

AADR has NO REST API and no small, stable per-file URL: a release is a multi-GB
EIGENSTRAT bundle (.anno/.ind/.snp/.geno) on Harvard Dataverse. We therefore pin
the version + DOI for reproducibility but never auto-download. Point the client
at a locally mirrored ``.anno`` file:

    export AADR_FILE=/path/to/aadr_v62.0_1240K_public.anno

or drop that file at ``~/.cache/aadr/<version>/aadr_<version>.anno``. With neither,
the client falls back to the bundled fixture (offline tests only) and otherwise
raises DatasetUnavailable with download instructions.
"""
from ._base import Snapshot

SNAPSHOTS = {
    "v62.0": Snapshot(
        version="v62.0",
        url=None,                       # manual download only (huge bundle, no stable file URL)
        sha256=None,
        member=None,
        filename="aadr_v62.0.anno",
        doi="10.7910/DVN/FFIDCW",
        license="CC BY 4.0",
    ),
    "v54.1.p1": Snapshot(
        version="v54.1.p1",
        url=None,
        filename="aadr_v54.1.p1.anno",
        doi="10.7910/DVN/FFIDCW",
        license="CC BY 4.0",
    ),
}

DEFAULT_VERSION = "v62.0"
