"""Pinned Seshat snapshots.

Seshat ships periodic snapshots (XLSX / CSV) tied to publications; the canonical
reproducible path is a pinned snapshot, not the experimental web API. The main
Social Complexity table (Turchin 2018 PNAS) is XLSX, and the base reads both
``.xlsx`` and ``.csv``. There is no single stable per-file URL, so we pin the
version + repo and require an explicit local file:

    git clone https://github.com/datasets/seshat.git
    export SESHAT_FILE=/path/to/seshat/sc_dataset.12.2017.xlsx   # or a CSV export

With neither file nor cache, the client falls back to the bundled CSV fixture
(offline tests only) and otherwise raises DatasetUnavailable with instructions.
Data is CC BY-NC-SA 4.0 (non-commercial, share-alike).
"""
from ._base import Snapshot

SNAPSHOTS = {
    "Equinox-2020": Snapshot(
        version="Equinox-2020",
        url=None,                       # manual snapshot download (see module docstring)
        filename="seshat_Equinox-2020.csv",
        doi="10.1073/pnas.1708800115",
        license="CC BY-NC-SA 4.0",
    ),
    "sc_2017": Snapshot(
        version="sc_2017",
        url=None,
        filename="sc_dataset.12.2017.xlsx",
        doi="10.1073/pnas.1708800115",
        license="CC BY-NC-SA 4.0",
    ),
}

DEFAULT_VERSION = "Equinox-2020"
