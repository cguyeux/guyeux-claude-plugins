"""Pleiades client: filter the ancient-places gazetteer by area and period.

    from pleiades_client import PleiadesClient
    rows = PleiadesClient().places(bbox=(30, -10, 47, 40), period="R", feature_type="settlement")

``places`` returns dicts with STABLE keys (see OUTPUT_COLUMNS). ``period`` is a
Pleiades period code (A archaic, C classical, H hellenistic, R roman, L late-antique,
M medieval), matched as a substring of the concatenated ``timePeriods`` field.
Reads .csv / .csv.gz / .xlsx, offline-capable, never needs pandas.
"""
from __future__ import annotations

import csv
from pathlib import Path

from ._base import FileDatasetClient
from .schema import SCHEMA
from .sources import DEFAULT_VERSION, SNAPSHOTS

REQUIRED = ["id", "title", "lat", "lon"]
OUTPUT_COLUMNS = ["id", "title", "lat", "lon", "feature_type",
                  "time_periods", "min_date", "max_date", "geo_context"]


def in_bbox(lat, lon, bbox) -> bool:
    """bbox = (south, west, north, east)."""
    if lat is None or lon is None:
        return False
    s, w, n, e = bbox
    return s <= lat <= n and w <= lon <= e


class PleiadesClient(FileDatasetClient):
    def __init__(self, **kwargs):
        fixture = Path(__file__).resolve().parents[2] / "fixtures" / "pleiades_sample.csv"
        super().__init__(slug="pleiades", snapshots=SNAPSHOTS, default_version=DEFAULT_VERSION,
                         schema=SCHEMA, fixture=fixture, delimiter=",",
                         quoting=csv.QUOTE_MINIMAL, **kwargs)

    def places(self, *, bbox: tuple[float, float, float, float] | None = None,
               period: str | None = None, feature_type: str | None = None,
               allow_download: bool = True) -> list[dict]:
        """Filter by bbox, period code (substring of timePeriods), and feature type."""
        rows = self.read_rows(allow_download=allow_download, required=REQUIRED)
        pneedle = period.strip().lower() if period else None
        fneedle = feature_type.strip().lower() if feature_type else None
        out: list[dict] = []
        for r in rows:
            if bbox is not None and not in_bbox(self.as_float(r.get("lat")),
                                                self.as_float(r.get("lon")), bbox):
                continue
            if pneedle is not None and pneedle not in (r.get("time_periods") or "").lower():
                continue
            if fneedle is not None and fneedle not in (r.get("feature_type") or "").lower():
                continue
            out.append(r)
        return out
