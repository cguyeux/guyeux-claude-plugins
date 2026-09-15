"""AADR client: turn the `.anno` index into a filtered cohort table.

This is the tool-first entry point for the aadr skill. Instead of re-deriving a
``pd.read_csv(...).between(...)`` by hand in every project, call::

    from aadr_client import AadrClient
    rows = AadrClient().cohort(countries=["Germany", "Hungary"], period_bp=(0, 1500))

``cohort`` returns a list of dicts with STABLE keys (see OUTPUT_COLUMNS), works on
a locally mirrored `.anno` (or the bundled fixture in offline mode), and never
requires pandas.
"""
from __future__ import annotations

import csv
from pathlib import Path

from ._base import FileDatasetClient
from .schema import SCHEMA
from .sources import DEFAULT_VERSION, SNAPSHOTS

# Columns that must resolve for a cohort query to be meaningful (others optional,
# so older releases lacking e.g. coverage still work).
REQUIRED = ["genetic_id", "group", "country", "lat", "lon", "date_bp", "qc"]

# Stable output contract consumed by downstream skills (host-pathogen-pair,
# geo-map, migration-data) and by `cohort --tsv`.
OUTPUT_COLUMNS = [
    "genetic_id", "master_id", "group", "country", "locality",
    "lat", "lon", "date_bp", "date_sd_bp", "coverage", "sex", "publication", "qc",
]


class AadrClient(FileDatasetClient):
    def __init__(self, **kwargs):
        here = Path(__file__).resolve()
        fixture = here.parents[2] / "fixtures" / "aadr_sample.anno.tsv"
        super().__init__(
            slug="aadr",
            snapshots=SNAPSHOTS,
            default_version=DEFAULT_VERSION,
            schema=SCHEMA,
            fixture=fixture,
            delimiter="\t",
            quoting=csv.QUOTE_NONE,
            **kwargs,
        )

    def cohort(self, *, countries: list[str] | None = None,
               period_bp: tuple[float, float] | None = None,
               pass_only: bool = True,
               allow_download: bool = True) -> list[dict]:
        """Filter individuals by modern country, calibrated age (years BP), and QC.

        Args:
            countries: keep only these ``Political Entity`` values (case-insensitive).
            period_bp: keep individuals with ``date_bp`` in ``[lo, hi]`` (years
                before 1950; present-day == 0). ``(0, 10000)`` = "10000 BP -> present".
            pass_only: keep only individuals whose ``Assessment`` contains ``PASS``.
        """
        rows = self.read_rows(allow_download=allow_download, required=REQUIRED)
        cset = {c.strip().lower() for c in countries} if countries else None
        lo, hi = period_bp if period_bp is not None else (None, None)

        out: list[dict] = []
        for r in rows:
            if cset is not None and (r.get("country") or "").strip().lower() not in cset:
                continue
            if lo is not None or hi is not None:
                d = self.as_float(r.get("date_bp"))
                if d is None:
                    continue
                if lo is not None and d < lo:
                    continue
                if hi is not None and d > hi:
                    continue
            if pass_only and "PASS" not in (r.get("qc") or "").upper():
                continue
            out.append(r)
        return out
