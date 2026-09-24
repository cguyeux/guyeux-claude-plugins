"""Resilient stdlib-only client for the Seshat Global History Databank."""
from ._base import DatasetError, DatasetUnavailable, SchemaDrift, Snapshot
from .client import OUTPUT_COLUMNS, SeshatClient

__all__ = [
    "SeshatClient",
    "OUTPUT_COLUMNS",
    "DatasetError",
    "DatasetUnavailable",
    "SchemaDrift",
    "Snapshot",
]
