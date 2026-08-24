"""OWTRAD client: read Old-World trade/pilgrimage/transhumance routes as a table.

    from owtrad_client import OwtradClient
    rows = OwtradClient().routes(name="Silk", route_type="trade",
                                 bbox=(20, 30, 50, 110))

``routes`` reads any OWTRAD vector file (KML / MapInfo / GeoJSON / shapefile, via
geopandas.read_file) and returns dicts with STABLE keys (see OUTPUT_COLUMNS): the
route name/type/description plus a geometry summary (type, vertex count, great-circle
length, endpoints). Reuses the gabarit's resolve cascade + exceptions; the vector I/O
needs geopandas (present on the system Python).
"""
from __future__ import annotations

import math
from pathlib import Path

from ._base import DatasetUnavailable, FileDatasetClient
from .sources import DEFAULT_VERSION, SNAPSHOTS

NAME_CANDS = ["Name", "NAME", "name", "route", "Route", "TMC_NAME", "label", "Label"]
TYPE_CANDS = ["type", "Type", "route_type", "TMC_TYPE", "category", "Category"]
DESC_CANDS = ["Description", "description", "desc", "Notes", "notes", "remark"]

OUTPUT_COLUMNS = ["name", "route_type", "description", "geom_type", "n_points",
                  "length_km", "start_lon", "start_lat", "end_lon", "end_lat"]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p = math.pi / 180.0
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def _pick(cols: list[str], cands: list[str]) -> str | None:
    """Resolve a stable attribute to an actual column: exact, then ci, then substring."""
    low = {c.lower(): c for c in cols}
    for c in cands:
        if c in cols:
            return c
    for c in cands:
        if c.lower() in low:
            return low[c.lower()]
    for c in cands:
        cl = c.lower()
        for col in cols:
            if cl in col.lower():
                return col
    return None


def _coords(geom) -> list[tuple[float, float]]:
    """Flatten a (Multi)LineString / Point into an ordered (lon, lat) list."""
    if geom is None:
        return []
    gt = geom.geom_type
    if gt == "Point":
        return [(geom.x, geom.y)]
    if gt in ("LineString", "LinearRing"):
        return [(x, y) for x, y in geom.coords]
    if gt in ("MultiLineString", "MultiPoint", "GeometryCollection"):
        out: list[tuple[float, float]] = []
        for g in geom.geoms:
            out.extend(_coords(g))
        return out
    if gt in ("Polygon",):
        return [(x, y) for x, y in geom.exterior.coords]
    return []


class OwtradClient(FileDatasetClient):
    def __init__(self, **kwargs):
        fixture = Path(__file__).resolve().parents[2] / "fixtures" / "owtrad_sample.geojson"
        super().__init__(slug="owtrad", snapshots=SNAPSHOTS, default_version=DEFAULT_VERSION,
                         schema={}, fixture=fixture, **kwargs)

    @staticmethod
    def _geopandas():
        try:
            import geopandas as gpd
            return gpd
        except Exception as exc:  # pragma: no cover - import guard
            raise DatasetUnavailable(
                "owtrad needs geopandas (read_file for KML/MapInfo/GeoJSON/shapefile). "
                "geopandas is available on the system Python; run with an interpreter "
                f"that has it. ({exc})"
            ) from exc

    def routes(self, *, name: str | None = None, route_type: str | None = None,
               bbox: tuple[float, float, float, float] | None = None,
               allow_download: bool = True) -> list[dict]:
        """Filter routes by name, route type, and bounding box (S, W, N, E)."""
        path = self.resolve_dataset(allow_download=allow_download)
        gpd = self._geopandas()
        gdf = gpd.read_file(path)
        cols = list(gdf.columns)
        ncol, tcol, dcol = _pick(cols, NAME_CANDS), _pick(cols, TYPE_CANDS), _pick(cols, DESC_CANDS)
        nn = name.strip().lower() if name else None
        tt = route_type.strip().lower() if route_type else None
        clip = None
        if bbox is not None:
            from shapely.geometry import box
            s, w, n, e = bbox
            clip = box(w, s, e, n)

        out: list[dict] = []
        for _, row in gdf.iterrows():
            nm = str(row[ncol]) if ncol and row[ncol] is not None else ""
            ty = str(row[tcol]) if tcol and row[tcol] is not None else ""
            ds = str(row[dcol]) if dcol and row[dcol] is not None else ""
            if nn is not None and nn not in nm.lower():
                continue
            if tt is not None and tt not in ty.lower():
                continue
            geom = row.geometry
            if clip is not None and (geom is None or not geom.intersects(clip)):
                continue
            cs = _coords(geom)
            length = sum(
                haversine_km(cs[i][1], cs[i][0], cs[i + 1][1], cs[i + 1][0])
                for i in range(len(cs) - 1)
            ) if len(cs) >= 2 else 0.0
            out.append({
                "name": nm, "route_type": ty, "description": ds,
                "geom_type": geom.geom_type if geom is not None else "",
                "n_points": len(cs), "length_km": round(length, 1),
                "start_lon": cs[0][0] if cs else "", "start_lat": cs[0][1] if cs else "",
                "end_lon": cs[-1][0] if cs else "", "end_lat": cs[-1][1] if cs else "",
            })
        return out
