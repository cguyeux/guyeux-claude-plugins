"""Resilient stdlib-only client for the SlaveVoyages Trans-Atlantic dataset."""
from ._base import DatasetError, DatasetUnavailable, SchemaDrift, Snapshot
from .client import OUTPUT_COLUMNS, SlaveVoyagesClient

__all__ = [
    "SlaveVoyagesClient",
    "OUTPUT_COLUMNS",
    "DatasetError",
    "DatasetUnavailable",
    "SchemaDrift",
    "Snapshot",
]
