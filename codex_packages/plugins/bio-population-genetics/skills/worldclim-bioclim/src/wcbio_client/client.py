"""WorldClim/CHELSA bioclim client: sample BIO variables at lat/lon points.

    from wcbio_client import WorldclimClient
    rows = WorldclimClient().sample([("Roma", 41.9, 12.5), ("Lima", -12.0, -77.0)],
                                    variables=["bio_1", "bio_12"])
    # -> [{point_id, lat, lon, bio_1, bio_12}, ...]

Resolves a DIRECTORY of single-band BIO GeoTIFFs (``WORLDCLIM_DIR``) and samples each
requested variable at each point with rasterio. Needs rasterio (not stdlib): run via
a venv that has it (e.g. /home/christophe/venvs/geo311/bin/python). Reuses the
gabarit's exception types; offline tests run against a tiny bundled raster fixture.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from ._base import DatasetError, DatasetUnavailable, FileDatasetClient
from .sources import DEFAULT_VERSION

OUTPUT_BASE = ["point_id", "lat", "lon"]


def _bio_key(stem: str) -> str:
    m = re.search(r"bio[_-]?(\d+)", stem, re.I)
    return f"bio_{int(m.group(1))}" if m else stem


def _bio_sort(key: str):
    m = re.fullmatch(r"bio_(\d+)", key)
    return (0, int(m.group(1))) if m else (1, key)


class WorldclimClient:
    """Raster point-sampler for the 19 WorldClim/CHELSA BIO variables."""

    def __init__(self, *, offline: bool | None = None, version: str = DEFAULT_VERSION):
        self.version = version
        env_off = os.environ.get("WORLDCLIM_OFFLINE")
        self.offline = (env_off == "1") if env_off is not None else bool(offline)
        self._dir_override = os.environ.get("WORLDCLIM_DIR")
        self._fixture_dir = Path(__file__).resolve().parents[2] / "fixtures" / "worldclim"
        self.last_source: str | None = None

    @staticmethod
    def _rasterio():
        try:
            import rasterio
            return rasterio
        except Exception as exc:  # pragma: no cover - import guard
            raise DatasetUnavailable(
                "worldclim-bioclim needs rasterio (not stdlib). Run with a venv that has "
                "it, e.g. /home/christophe/venvs/geo311/bin/python -m wcbio_client ... "
                f"({exc})"
            ) from exc

    def _raster_dir(self) -> Path:
        if self._dir_override and not self.offline:
            d = Path(self._dir_override).expanduser()
            if d.is_dir():
                self.last_source = "env"
                return d
            raise DatasetUnavailable(f"WORLDCLIM_DIR={self._dir_override} is not a directory")
        if self._fixture_dir.is_dir() and any(self._fixture_dir.glob("*.tif")):
            self.last_source = "fixture"
            return self._fixture_dir
        raise DatasetUnavailable(
            "no raster data. Download WorldClim 2.1 (worldclim.org) and set "
            "WORLDCLIM_DIR=/path/to/wc2.1_10m (a directory of bio_*.tif)."
        )

    def _rasters(self) -> dict[str, Path]:
        d = self._raster_dir()
        files = {_bio_key(p.stem): p for p in sorted(d.glob("*.tif"))}
        if not files:
            raise DatasetUnavailable(f"no .tif rasters in {d}")
        return files

    def variables(self) -> list[str]:
        return sorted(self._rasters(), key=_bio_sort)

    def sample(self, points, variables: list[str] | None = None) -> list[dict]:
        """Sample BIO variables at points. ``points`` = iterable of (id, lat, lon)."""
        pts = [(str(pid), float(lat), float(lon)) for (pid, lat, lon) in points]
        files = self._rasters()
        vs = variables or sorted(files, key=_bio_sort)
        missing = [v for v in vs if v not in files]
        if missing:
            raise DatasetError(f"variables not found: {missing}; available: {sorted(files, key=_bio_sort)}")
        rio = self._rasterio()
        coords = [(lon, lat) for (_, lat, lon) in pts]
        cols: dict[str, list] = {}
        for v in vs:
            with rio.open(files[v]) as ds:
                nodata = ds.nodata
                vals = []
                for rec in ds.sample(coords):
                    x = rec[0]
                    vals.append(None if (nodata is not None and x == nodata) else float(x))
                cols[v] = vals
        rows = []
        for i, (pid, lat, lon) in enumerate(pts):
            row = {"point_id": pid, "lat": lat, "lon": lon}
            for v in vs:
                row[v] = cols[v][i]
            rows.append(row)
        return rows

    @staticmethod
    def write_tsv(rows, columns, out):
        FileDatasetClient.write_tsv(rows, columns, out)
