"""Modern human reference panels client: filter sample metadata by population/region.

    from mhrp_client import MhrpClient
    rows = MhrpClient().samples(project="HGDP", region="AFRICA")

``samples`` returns dicts with STABLE keys (see OUTPUT_COLUMNS) from the harmonised
HGDP+1kGP sample-metadata TSV. Handy to pick representative individuals per
population for a cross-cultural join (e.g. to `d-place` via Glottocode/country).
Reads .tsv/.csv/.xlsx, offline-capable, never needs pandas.
"""
from __future__ import annotations

import csv
from pathlib import Path

from ._base import FileDatasetClient
from .schema import SCHEMA
from .sources import DEFAULT_VERSION, SNAPSHOTS

REQUIRED = ["sample", "population"]
OUTPUT_COLUMNS = ["sample", "project", "population", "region", "lat", "lon", "sex"]


def in_bbox(lat, lon, bbox) -> bool:
    if lat is None or lon is None:
        return False
    s, w, n, e = bbox
    return s <= lat <= n and w <= lon <= e


class MhrpClient(FileDatasetClient):
    def __init__(self, **kwargs):
        fixture = Path(__file__).resolve().parents[2] / "fixtures" / "mhrp_sample.tsv"
        super().__init__(slug="mhrp", snapshots=SNAPSHOTS, default_version=DEFAULT_VERSION,
                         schema=SCHEMA, fixture=fixture, delimiter="\t",
                         quoting=csv.QUOTE_NONE, **kwargs)

    def samples(self, *, population: str | None = None, region: str | None = None,
                project: str | None = None,
                bbox: tuple[float, float, float, float] | None = None,
                allow_download: bool = True) -> list[dict]:
        """Filter samples by population, region, project/panel (substring), and bbox."""
        rows = self.read_rows(allow_download=allow_download, required=REQUIRED)
        pop = population.strip().lower() if population else None
        reg = region.strip().lower() if region else None
        proj = project.strip().lower() if project else None
        out: list[dict] = []
        for r in rows:
            if pop is not None and pop not in (r.get("population") or "").lower():
                continue
            if reg is not None and reg not in (r.get("region") or "").lower():
                continue
            if proj is not None and proj not in (r.get("project") or "").lower():
                continue
            if bbox is not None and not in_bbox(self.as_float(r.get("lat")),
                                                self.as_float(r.get("lon")), bbox):
                continue
            out.append(r)
        return out
