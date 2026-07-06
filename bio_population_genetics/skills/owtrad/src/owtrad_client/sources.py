"""Pinned OWTRAD snapshot.

OWTRAD has no consolidated dump: each route dataset is a standalone file (MapInfo
.mif/.mid, KML, GeoJSON, or shapefile). Point the client at any OWTRAD vector file
(geopandas.read_file handles all of them via fiona/GDAL):

    export OWTRAD_FILE=/path/to/tmcCNa0100d.kml      # or .geojson / .mif / .shp
"""
from ._base import Snapshot

SNAPSHOTS = {
    "v": Snapshot(
        version="v",
        url=None,
        filename="owtrad.geojson",
        doi="http://www.ciolek.com/owtrad.html",
        license="OWTRAD / Ciolek (academic use, attribution)",
    ),
}

DEFAULT_VERSION = "v"
