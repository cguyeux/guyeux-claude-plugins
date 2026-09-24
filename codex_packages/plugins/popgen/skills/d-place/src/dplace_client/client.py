"""D-PLACE client: filter ethnographic societies by area, language, dataset.

    from dplace_client import DplaceClient
    rows = DplaceClient().societies(bbox=(-35, -20, 15, 52), dataset="EA")

``societies`` returns dicts with STABLE keys (see OUTPUT_COLUMNS) from the unified
``societies.csv``. To pull cultural variable VALUES for these societies, join the
D-PLACE ``values.csv`` / ``codes.csv`` separately. Reads .csv/.xlsx, offline-capable.
"""
from __future__ import annotations

import csv
from pathlib import Path

from ._base import FileDatasetClient
from .schema import SCHEMA
from .sources import DEFAULT_VERSION, SNAPSHOTS

REQUIRED = ["id", "name"]
OUTPUT_COLUMNS = ["id", "name", "glottocode", "lat", "lon", "family", "dataset"]


def in_bbox(lat, lon, bbox) -> bool:
    if lat is None or lon is None:
        return False
    s, w, n, e = bbox
    return s <= lat <= n and w <= lon <= e


class DplaceClient(FileDatasetClient):
    def __init__(self, **kwargs):
        fixture = Path(__file__).resolve().parents[2] / "fixtures" / "dplace_sample.csv"
        super().__init__(slug="dplace", snapshots=SNAPSHOTS, default_version=DEFAULT_VERSION,
                         schema=SCHEMA, fixture=fixture, delimiter=",",
                         quoting=csv.QUOTE_MINIMAL, **kwargs)

    def societies(self, *, bbox: tuple[float, float, float, float] | None = None,
                  glottocode: str | None = None, family: str | None = None,
                  dataset: str | None = None, allow_download: bool = True) -> list[dict]:
        """Filter societies by bbox, Glottocode, language family, and source dataset."""
        rows = self.read_rows(allow_download=allow_download, required=REQUIRED)
        gc = glottocode.strip().lower() if glottocode else None
        fam = family.strip().lower() if family else None
        ds = dataset.strip().lower() if dataset else None
        out: list[dict] = []
        for r in rows:
            if gc is not None and gc != (r.get("glottocode") or "").lower():
                continue
            if fam is not None and fam not in (r.get("family") or "").lower():
                continue
            if ds is not None and ds not in (r.get("dataset") or "").lower():
                continue
            if bbox is not None and not in_bbox(self.as_float(r.get("lat")),
                                                self.as_float(r.get("lon")), bbox):
                continue
            out.append(r)
        return out
