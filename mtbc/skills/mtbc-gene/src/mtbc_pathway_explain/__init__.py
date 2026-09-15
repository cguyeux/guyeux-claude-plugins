"""Curated, network-aware narration of MTBC pathways and gene sets."""
from .core import (
    PathwayNotFound,
    PathwayReport,
    SelectionInputError,
    SelectionReport,
    explain_gene_set,
    explain_pathway,
    from_selection,
    genes_from_network,
    genes_under_selection,
    load_catalogue,
)

__all__ = [
    "explain_pathway",
    "explain_gene_set",
    "genes_from_network",
    "from_selection",
    "genes_under_selection",
    "load_catalogue",
    "PathwayReport",
    "SelectionReport",
    "PathwayNotFound",
    "SelectionInputError",
]
