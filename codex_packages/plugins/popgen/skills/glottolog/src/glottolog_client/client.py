"""Glottolog client: filter languoids by macroarea, region, level.

    from glottolog_client import GlottologClient
    rows = GlottologClient().languages(macroarea="Africa", bbox=(-35, -20, 15, 52))

``languages`` returns dicts with STABLE keys (see OUTPUT_COLUMNS). Glottolog encodes
family as a parent Glottocode (not a name), so filter by macroarea / bbox / level /
name here; for a family-NAME filter use `wals`. Reads .csv/.xlsx, offline-capable.
"""
from __future__ import annotations

import csv
from pathlib import Path

from ._base import FileDatasetClient
from .schema import SCHEMA
from .sources import DEFAULT_VERSION, SNAPSHOTS

REQUIRED = ["glottocode", "name"]
OUTPUT_COLUMNS = ["glottocode", "name", "level", "family", "macroarea", "lat", "lon", "iso639"]


def in_bbox(lat, lon, bbox) -> bool:
    if lat is None or lon is None:
        return False
    s, w, n, e = bbox
    return s <= lat <= n and w <= lon <= e


class GlottologClient(FileDatasetClient):
    def __init__(self, **kwargs):
        fixture = Path(__file__).resolve().parents[2] / "fixtures" / "glottolog_sample.csv"
        super().__init__(slug="glottolog", snapshots=SNAPSHOTS, default_version=DEFAULT_VERSION,
                         schema=SCHEMA, fixture=fixture, delimiter=",",
                         quoting=csv.QUOTE_MINIMAL, **kwargs)

    def languages(self, *, macroarea: str | None = None,
                  bbox: tuple[float, float, float, float] | None = None,
                  level: str | None = None, name: str | None = None,
                  allow_download: bool = True) -> list[dict]:
        """Filter languoids by macroarea, bounding box, level, and name (substring)."""
        rows = self.read_rows(allow_download=allow_download, required=REQUIRED)
        ma = macroarea.strip().lower() if macroarea else None
        lv = level.strip().lower() if level else None
        nm = name.strip().lower() if name else None
        out: list[dict] = []
        for r in rows:
            if ma is not None and ma not in (r.get("macroarea") or "").lower():
                continue
            if lv is not None and lv not in (r.get("level") or "").lower():
                continue
            if nm is not None and nm not in (r.get("name") or "").lower():
                continue
            if bbox is not None and not in_bbox(self.as_float(r.get("lat")),
                                                self.as_float(r.get("lon")), bbox):
                continue
            out.append(r)
        return out
