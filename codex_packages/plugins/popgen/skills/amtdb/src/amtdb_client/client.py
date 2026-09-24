"""AmtDB client: filter ancient human mtDNA samples by area, period, haplogroup.

    from amtdb_client import AmtdbClient
    rows = AmtdbClient().samples(bbox=(35, -10, 60, 40), period=(-3000, 0), haplogroup="H")

``samples`` returns dicts with STABLE keys (see OUTPUT_COLUMNS); ``period`` is in
calendar years (BCE negative) matched against the [year_from, year_to] interval.
Reads .csv or .xlsx, offline-capable, never needs pandas.
"""
from __future__ import annotations

import csv
from pathlib import Path

from ._base import FileDatasetClient
from .schema import SCHEMA
from .sources import DEFAULT_VERSION, SNAPSHOTS

REQUIRED = ["id", "mt_hg"]
OUTPUT_COLUMNS = ["id", "country", "lat", "lon", "culture", "epoch", "site",
                  "mt_hg", "year_from", "year_to", "bp", "reference"]


def in_bbox(lat, lon, bbox) -> bool:
    """bbox = (south, west, north, east)."""
    if lat is None or lon is None:
        return False
    s, w, n, e = bbox
    return s <= lat <= n and w <= lon <= e


class AmtdbClient(FileDatasetClient):
    def __init__(self, **kwargs):
        fixture = Path(__file__).resolve().parents[2] / "fixtures" / "amtdb_sample.csv"
        super().__init__(slug="amtdb", snapshots=SNAPSHOTS, default_version=DEFAULT_VERSION,
                         schema=SCHEMA, fixture=fixture, delimiter=",",
                         quoting=csv.QUOTE_MINIMAL, **kwargs)

    def samples(self, *, bbox: tuple[float, float, float, float] | None = None,
                period: tuple[float, float] | None = None,
                haplogroup: str | None = None, allow_download: bool = True) -> list[dict]:
        """Filter by bbox, calendar-year window (overlap of [year_from, year_to]),
        and mtDNA haplogroup (prefix/substring, e.g. ``"H"`` matches H, H1, H5a)."""
        rows = self.read_rows(allow_download=allow_download, required=REQUIRED)
        lo, hi = period if period is not None else (None, None)
        hg = haplogroup.strip().lower() if haplogroup else None
        out: list[dict] = []
        for r in rows:
            if bbox is not None and not in_bbox(self.as_float(r.get("lat")),
                                                self.as_float(r.get("lon")), bbox):
                continue
            if lo is not None or hi is not None:
                yf = self.as_float(r.get("year_from"))
                yt = self.as_float(r.get("year_to"))
                if yf is None or yt is None:
                    continue
                if hi is not None and yf > hi:
                    continue
                if lo is not None and yt < lo:
                    continue
            if hg is not None and not (r.get("mt_hg") or "").lower().startswith(hg):
                continue
            out.append(r)
        return out
