"""Pinned WorldClim / CHELSA bioclim snapshot (raster directory, not one file).

The 19 BIO variables ship as single-band GeoTIFFs (multi-GB at high resolution).
Download from worldclim.org / CHELSA and point the client at the directory:

    export WORLDCLIM_DIR=/path/to/wc2.1_10m      # contains wc2.1_10m_bio_1.tif ...

Needs rasterio (not stdlib). Run with a venv that has it, e.g.:
    /home/christophe/venvs/geo311/bin/python -m wcbio_client ...
"""
from ._base import Snapshot

SNAPSHOTS = {
    "wc2.1": Snapshot(
        version="wc2.1",
        url=None,
        filename="",
        doi="https://doi.org/10.1002/joc.5086",
        license="CC BY 4.0 (WorldClim 2.1)",
    ),
}

DEFAULT_VERSION = "wc2.1"

# BIO variable short labels (WorldClim convention).
BIO_LABELS = {
    "bio_1": "Annual Mean Temperature", "bio_2": "Mean Diurnal Range",
    "bio_3": "Isothermality", "bio_4": "Temperature Seasonality",
    "bio_5": "Max Temp of Warmest Month", "bio_6": "Min Temp of Coldest Month",
    "bio_7": "Temperature Annual Range", "bio_8": "Mean Temp of Wettest Quarter",
    "bio_9": "Mean Temp of Driest Quarter", "bio_10": "Mean Temp of Warmest Quarter",
    "bio_11": "Mean Temp of Coldest Quarter", "bio_12": "Annual Precipitation",
    "bio_13": "Precip of Wettest Month", "bio_14": "Precip of Driest Month",
    "bio_15": "Precip Seasonality", "bio_16": "Precip of Wettest Quarter",
    "bio_17": "Precip of Driest Quarter", "bio_18": "Precip of Warmest Quarter",
    "bio_19": "Precip of Coldest Quarter",
}
