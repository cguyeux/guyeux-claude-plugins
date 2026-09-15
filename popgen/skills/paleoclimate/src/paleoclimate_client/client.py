"""Paleoclimate client: sample paleo bioclim rasters at points, by time slice.

    from paleoclimate_client import PaleoclimateClient
    pc = PaleoclimateClient()
    pc.time_slices()                                   # -> ['lgm', 'midholocene', ...]
    rows = pc.sample([("Roma", 41.9, 12.5)], variables=["bio_1"], time_slice="lgm")

Resolves ``PALEOCLIMATE_DIR`` whose subdirectories are time slices of BIO GeoTIFFs,
and samples each variable at each point with rasterio (same engine as
`worldclim-bioclim`, plus a time dimension). Needs rasterio: run via a venv that has
it (e.g. /home/christophe/venvs/geo311/bin/python). NetCDF / proxy archives are out
of scope here (use xarray / the tabular approach).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from ._base import DatasetError, DatasetUnavailable, FileDatasetClient
from .sources import DEFAULT_VERSION

OUTPUT_BASE = ["point_id", "time_slice", "lat", "lon"]


def _bio_key(stem: str) -> str:
    m = re.search(r"bio[_-]?(\d+)", stem, re.I)
    return f"bio_{int(m.group(1))}" if m else stem


def _bio_sort(key: str):
    m = re.fullmatch(r"bio_(\d+)", key)
    return (0, int(m.group(1))) if m else (1, key)


class PaleoclimateClient:
    """Raster point-sampler for paleo BIO variables, organised by time slice."""

    def __init__(self, *, offline: bool | None = None, version: str = DEFAULT_VERSION):
        self.version = version
        env_off = os.environ.get("PALEOCLIMATE_OFFLINE")
        self.offline = (env_off == "1") if env_off is not None else bool(offline)
        self._dir_override = os.environ.get("PALEOCLIMATE_DIR")
        self._nc_override = os.environ.get("PALEOCLIMATE_NC")
        self._fixture_dir = Path(__file__).resolve().parents[2] / "fixtures" / "paleoclimate"
        self.last_source: str | None = None

    @staticmethod
    def _rasterio():
        try:
            import rasterio
            return rasterio
        except Exception as exc:  # pragma: no cover - import guard
            raise DatasetUnavailable(
                "paleoclimate needs rasterio (not stdlib). Run via a venv that has it, "
                "e.g. /home/christophe/venvs/geo311/bin/python -m paleoclimate_client ... "
                f"({exc})"
            ) from exc

    def _base_dir(self) -> Path:
        if self._dir_override and not self.offline:
            d = Path(self._dir_override).expanduser()
            if d.is_dir():
                self.last_source = "env"
                return d
            raise DatasetUnavailable(f"PALEOCLIMATE_DIR={self._dir_override} is not a directory")
        if self._fixture_dir.is_dir():
            self.last_source = "fixture"
            return self._fixture_dir
        raise DatasetUnavailable(
            "no raster data. Download a paleo bioclim set (CHELSA-TraCE21k / PaleoClim) "
            "and set PALEOCLIMATE_DIR=/path (subdirs = time slices of bio_*.tif)."
        )

    def time_slices(self) -> list[str]:
        """Subdirectories that contain BIO rasters; ['.'] if rasters are at the top."""
        base = self._base_dir()
        subs = sorted(p.name for p in base.iterdir() if p.is_dir() and any(p.glob("*.tif")))
        if subs:
            return subs
        return ["."] if any(base.glob("*.tif")) else []

    def _rasters(self, time_slice: str | None) -> dict[str, Path]:
        base = self._base_dir()
        d = base if (time_slice in (None, ".") or not time_slice) else base / time_slice
        if not d.is_dir():
            raise DatasetUnavailable(f"time slice {time_slice!r} not found under {base}")
        files = {_bio_key(p.stem): p for p in sorted(d.glob("*.tif"))}
        if not files:
            raise DatasetUnavailable(f"no .tif rasters in {d}")
        return files

    def sample(self, points, variables: list[str] | None = None,
               time_slice: str | None = None) -> list[dict]:
        """Sample BIO variables at points for a time slice. points = (id, lat, lon)."""
        pts = [(str(pid), float(lat), float(lon)) for (pid, lat, lon) in points]
        files = self._rasters(time_slice)
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
                cols[v] = [
                    (None if (nodata is not None and rec[0] == nodata) else float(rec[0]))
                    for rec in ds.sample(coords)
                ]
        label = time_slice or "."
        rows = []
        for i, (pid, lat, lon) in enumerate(pts):
            row = {"point_id": pid, "time_slice": label, "lat": lat, "lon": lon}
            for v in vs:
                row[v] = cols[v][i]
            rows.append(row)
        return rows

    # ── NetCDF (xarray) — proxy reconstructions, ice-core series, paleo grids ──

    @staticmethod
    def _xarray():
        try:
            import xarray as xr
            return xr
        except Exception as exc:  # pragma: no cover - import guard
            raise DatasetUnavailable(
                "paleoclimate NetCDF needs xarray + netCDF4 (not stdlib). Run via a venv "
                "that has them, e.g. /home/christophe/venvs/geo311/bin/python "
                f"-m paleoclimate_client sample-nc ... ({exc})"
            ) from exc

    def _nc_file(self) -> Path:
        if self._nc_override and not self.offline:
            p = Path(self._nc_override).expanduser()
            if p.is_file():
                self.last_source = "env"
                return p
            raise DatasetUnavailable(f"PALEOCLIMATE_NC={self._nc_override} is not a file")
        if self._fixture_dir.is_dir():
            ncs = sorted(self._fixture_dir.glob("*.nc"))
            if ncs:
                self.last_source = "fixture"
                return ncs[0]
        raise DatasetUnavailable(
            "no NetCDF. Set PALEOCLIMATE_NC=/path/to/reconstruction.nc (PAGES2k, "
            "CHELSA-TraCE21k, ice-core series, ...)."
        )

    @staticmethod
    def _guess_coord(ds, names):
        for n in names:
            if n in ds.coords or n in ds.dims:
                return n
        return None

    def nc_variables(self) -> list[str]:
        """List the data variables in the resolved NetCDF file."""
        xr = self._xarray()
        with xr.open_dataset(self._nc_file()) as ds:
            return list(ds.data_vars)

    def sample_nc(self, points, variables: list[str] | None = None, *, time=None,
                  lat_name: str | None = None, lon_name: str | None = None,
                  time_name: str | None = None) -> list[dict]:
        """Sample NetCDF variables at lat/lon points (nearest grid cell), optionally at
        a given ``time`` (nearest). ``points`` = iterable of (id, lat, lon). With a time
        axis present but no ``time`` given, the most recent slice is used."""
        import numpy as np
        xr = self._xarray()
        pts = [(str(pid), float(lat), float(lon)) for (pid, lat, lon) in points]

        def scalar(val):
            a = np.asarray(val)
            return float(a) if a.ndim == 0 else (float(a.mean()) if a.size else None)

        with xr.open_dataset(self._nc_file()) as ds:
            latn = lat_name or self._guess_coord(ds, ("lat", "latitude", "y", "Y"))
            lonn = lon_name or self._guess_coord(ds, ("lon", "longitude", "x", "X"))
            timen = time_name or self._guess_coord(ds, ("time", "age", "year", "T"))
            if not latn or not lonn:
                raise DatasetUnavailable(
                    f"could not find lat/lon coords (have {list(ds.coords)}); "
                    "pass lat_name/lon_name."
                )
            vs = variables or list(ds.data_vars)
            rows = []
            for pid, lat, lon in pts:
                sub = ds.sel({latn: lat, lonn: lon}, method="nearest")
                tlabel = None
                if timen and timen in sub.coords:
                    sub = (sub.sel({timen: time}, method="nearest") if time is not None
                           else sub.isel({timen: -1}))
                    tlabel = str(np.asarray(sub[timen].values).tolist())
                row = {"point_id": pid, "lat": lat, "lon": lon, "time": tlabel}
                for v in vs:
                    row[v] = scalar(sub[v].values)
                rows.append(row)
            return rows

    @staticmethod
    def write_tsv(rows, columns, out):
        FileDatasetClient.write_tsv(rows, columns, out)
