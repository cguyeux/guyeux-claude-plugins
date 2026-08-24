"""Pinned paleoclimate snapshot (paleo bioclim rasters, by time slice).

Paleo bioclimatic reconstructions (CHELSA-TraCE21k, WorldClim past, PaleoClim) ship
as GeoTIFFs, usually organised by time slice. Download and point the client at the
base directory; time slices are subdirectories of BIO GeoTIFFs:

    export PALEOCLIMATE_DIR=/path/to/paleoclim     # contains lgm/bio_1.tif, midholo/bio_1.tif ...

Needs rasterio (run via /home/christophe/venvs/geo311/bin/python). For NetCDF archives
(PAGES2k reconstructions, ice-core series) use xarray/netCDF4 separately; for tabular
proxy records use the generic tabular approach.
"""
from ._base import Snapshot

SNAPSHOTS = {
    "chelsa_trace21k": Snapshot(
        version="chelsa_trace21k",
        url=None,
        filename="",
        doi="https://doi.org/10.5194/cp-19-2493-2023",
        license="CHELSA-TraCE21k (academic use)",
    ),
}

DEFAULT_VERSION = "chelsa_trace21k"
