"""NERD client: filter Neolithic radiocarbon dates by area, age, and material.

    from neolithic14c_client import NerdClient
    rows = NerdClient().dates(bbox=(35, -10, 60, 40), age_bp=(5000, 7000), material="bone")

``dates`` returns dicts with STABLE keys (see OUTPUT_COLUMNS); ages are uncalibrated
14C BP. Reads .csv or .xlsx, offline-capable, never needs pandas.
"""
from __future__ import annotations

import csv
from pathlib import Path

from ._base import FileDatasetClient
from .schema import SCHEMA
from .sources import DEFAULT_VERSION, SNAPSHOTS

REQUIRED = ["age_bp", "lat", "lon"]
OUTPUT_COLUMNS = ["date_id", "lab_id", "age_bp", "error", "material",
                  "species", "site", "lat", "lon", "country", "source"]


def in_bbox(lat, lon, bbox) -> bool:
    """bbox = (south, west, north, east); lat/lon are floats or None."""
    if lat is None or lon is None:
        return False
    s, w, n, e = bbox
    return s <= lat <= n and w <= lon <= e


class NerdClient(FileDatasetClient):
    def __init__(self, **kwargs):
        fixture = Path(__file__).resolve().parents[2] / "fixtures" / "neolithic_14c_sample.csv"
        super().__init__(slug="neolithic_14c", snapshots=SNAPSHOTS,
                         default_version=DEFAULT_VERSION, schema=SCHEMA, fixture=fixture,
                         delimiter=",", quoting=csv.QUOTE_MINIMAL, **kwargs)

    def dates(self, *, bbox: tuple[float, float, float, float] | None = None,
              age_bp: tuple[float, float] | None = None,
              material: str | None = None, allow_download: bool = True) -> list[dict]:
        """Filter by geographic bounding box, 14C age window (BP), and material."""
        rows = self.read_rows(allow_download=allow_download, required=REQUIRED)
        lo, hi = age_bp if age_bp is not None else (None, None)
        mneedle = material.strip().lower() if material else None
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
            out.append(r)
        return out
