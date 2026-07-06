"""Stdlib-only client + CLI for the STRING v12 protein-association API."""
from .client import (  # noqa: F401
    StringError, map_ids, partners, network, enrichment,
    functional_annotation, ppi_enrichment, network_image,
    DEFAULT_SPECIES, CHANNEL_FIELDS,
)

__version__ = "0.1.0"
