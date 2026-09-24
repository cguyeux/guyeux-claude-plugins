"""WALS client: filter languages by family, genus, macroarea, and area.

    from wals_client import WalsClient
    rows = WalsClient().languages(family="Niger-Congo", macroarea="Africa")

``languages`` returns dicts with STABLE keys (see OUTPUT_COLUMNS) from the WALS CLDF
``languages.csv`` (the geo + genealogy table). For per-feature values, join the WALS
``values.csv`` separately. Reads .csv/.xlsx, offline-capable, never needs pandas.
"""
from __future__ import annotations

import csv
from pathlib import Path

from ._base import FileDatasetClient
from .schema import SCHEMA
from .sources import DEFAULT_VERSION, SNAPSHOTS

REQUIRED = ["id", "name"]
OUTPUT_COLUMNS = ["id", "name", "glottocode", "family", "subfamily",
                  "genus", "macroarea", "lat", "lon", "iso639"]


def in_bbox(lat, lon, bbox) -> bool:
    if lat is None or lon is None:
        return False
    s, w, n, e = bbox
    return s <= lat <= n and w <= lon <= e


class WalsClient(FileDatasetClient):
    def __init__(self, **kwargs):
        fixture = Path(__file__).resolve().parents[2] / "fixtures" / "wals_sample.csv"
        super().__init__(slug="wals", snapshots=SNAPSHOTS, default_version=DEFAULT_VERSION,
                         schema=SCHEMA, fixture=fixture, delimiter=",",
                         quoting=csv.QUOTE_MINIMAL, **kwargs)

    def languages(self, *, family: str | None = None, genus: str | None = None,
                  macroarea: str | None = None,
                  bbox: tuple[float, float, float, float] | None = None,
                  allow_download: bool = True) -> list[dict]:
        """Filter languages by family, genus, macroarea (substring), and bbox."""
        rows = self.read_rows(allow_download=allow_download, required=REQUIRED)
        fam = family.strip().lower() if family else None
        gen = genus.strip().lower() if genus else None
        ma = macroarea.strip().lower() if macroarea else None
        out: list[dict] = []
        for r in rows:
            if fam is not None and fam not in (r.get("family") or "").lower():
                continue
            if gen is not None and gen not in (r.get("genus") or "").lower():
                continue
            if ma is not None and ma not in (r.get("macroarea") or "").lower():
                continue
            if bbox is not None and not in_bbox(self.as_float(r.get("lat")),
                                                self.as_float(r.get("lon")), bbox):
                continue
            out.append(r)
        return out
