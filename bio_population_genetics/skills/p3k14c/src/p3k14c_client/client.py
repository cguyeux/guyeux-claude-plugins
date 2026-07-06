"""p3k14c client: filter the global archaeological radiocarbon database.

    from p3k14c_client import P3k14cClient
    rows = P3k14cClient().dates(continent="SAmerica", age_bp=(500, 1500), material="bone")

``dates`` returns dicts with STABLE keys (see OUTPUT_COLUMNS); ages are uncalibrated
14C BP. Reads .csv or .xlsx, offline-capable, never needs pandas.
"""
from __future__ import annotations

import csv
from pathlib import Path

from ._base import FileDatasetClient
from .schema import SCHEMA
from .sources import DEFAULT_VERSION, SNAPSHOTS

REQUIRED = ["age_bp"]
OUTPUT_COLUMNS = ["date_id", "age_bp", "error", "material", "species",
                  "site", "lat", "lon", "country", "continent", "source"]


def in_bbox(lat, lon, bbox) -> bool:
    """bbox = (south, west, north, east)."""
    if lat is None or lon is None:
        return False
    s, w, n, e = bbox
    return s <= lat <= n and w <= lon <= e


class P3k14cClient(FileDatasetClient):
    def __init__(self, **kwargs):
        fixture = Path(__file__).resolve().parents[2] / "fixtures" / "p3k14c_sample.csv"
        super().__init__(slug="p3k14c", snapshots=SNAPSHOTS, default_version=DEFAULT_VERSION,
                         schema=SCHEMA, fixture=fixture, delimiter=",",
                         quoting=csv.QUOTE_MINIMAL, **kwargs)

    def dates(self, *, bbox: tuple[float, float, float, float] | None = None,
              age_bp: tuple[float, float] | None = None,
              material: str | None = None, continent: str | None = None,
              allow_download: bool = True) -> list[dict]:
        """Filter by bbox, 14C age window (BP), material, and continent."""
        rows = self.read_rows(allow_download=allow_download, required=REQUIRED)
        lo, hi = age_bp if age_bp is not None else (None, None)
        mneedle = material.strip().lower() if material else None
        cneedle = continent.strip().lower() if continent else None
        out: list[dict] = []
        for r in rows:
            if bbox is not None and not in_bbox(self.as_float(r.get("lat")),
                                                self.as_float(r.get("lon")), bbox):
                continue
            if lo is not None or hi is not None:
                a = self.as_float(r.get("age_bp"))
                if a is None or (lo is not None and a < lo) or (hi is not None and a > hi):
                    continue
            if mneedle is not None and mneedle not in (r.get("material") or "").lower():
                continue
            if cneedle is not None and cneedle not in (r.get("continent") or "").lower():
                continue
            out.append(r)
        return out
