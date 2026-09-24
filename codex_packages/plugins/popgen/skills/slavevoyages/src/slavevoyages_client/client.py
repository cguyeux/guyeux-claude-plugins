"""SlaveVoyages client: filter trans-Atlantic voyages and quantify route volume.

Tool-first entry point for the slavevoyages skill. Instead of re-deriving a pandas
filter over the SPSS variable codes in every project, call::

    from slavevoyages_client import SlaveVoyagesClient
    sv = SlaveVoyagesClient()
    rows = sv.voyages(embark="Gold Coast", disembark="Brazil", period=(1700, 1800))
    summ = sv.route_summary(embark="Gold Coast", disembark="Brazil")
    # summ -> {voyages, embarked, disembarked, year_min, year_max}

``voyages`` returns dicts with STABLE keys (see OUTPUT_COLUMNS); ``route_summary``
aggregates the imputed embarked/disembarked volumes and the date window for a
region pair (the standard MTBC phylogeography use: tie a New-World lineage to a
trans-Atlantic route and its peak period). Reads .csv or .xlsx; never needs pandas.
"""
from __future__ import annotations

import csv
from pathlib import Path

from ._base import FileDatasetClient
from .schema import SCHEMA
from .sources import DEFAULT_VERSION, SNAPSHOTS

REQUIRED = ["voyage_id", "year"]

OUTPUT_COLUMNS = [
    "voyage_id", "year", "embark_region", "embark_port",
    "disembark_region", "disembark_port", "embarked", "disembarked", "flag",
]


class SlaveVoyagesClient(FileDatasetClient):
    def __init__(self, **kwargs):
        here = Path(__file__).resolve()
        fixture = here.parents[2] / "fixtures" / "slavevoyages_sample.csv"
        super().__init__(
            slug="slavevoyages",
            snapshots=SNAPSHOTS,
            default_version=DEFAULT_VERSION,
            schema=SCHEMA,
            fixture=fixture,
            delimiter=",",
            quoting=csv.QUOTE_MINIMAL,
            **kwargs,
        )

    def voyages(self, *, embark: str | None = None, disembark: str | None = None,
                period: tuple[float, float] | None = None,
                allow_download: bool = True) -> list[dict]:
        """Filter voyages by embarkation, disembarkation, and year of arrival.

        ``embark`` / ``disembark`` match (case-insensitive substring) against the
        region OR the principal port, so "Gold Coast", "Anomabu", "Brazil" or
        "Bahia" all work. ``period=(lo, hi)`` filters on ``year`` (year of arrival).
        """
        rows = self.read_rows(allow_download=allow_download, required=REQUIRED)
        en = embark.strip().lower() if embark else None
        dn = disembark.strip().lower() if disembark else None
        lo, hi = period if period is not None else (None, None)

        out: list[dict] = []
        for r in rows:
            if en is not None:
                hay = f"{r.get('embark_region') or ''} {r.get('embark_port') or ''}".lower()
                if en not in hay:
                    continue
            if dn is not None:
                hay = f"{r.get('disembark_region') or ''} {r.get('disembark_port') or ''}".lower()
                if dn not in hay:
                    continue
            if lo is not None or hi is not None:
                y = self.as_float(r.get("year"))
                if y is None:
                    continue
                if lo is not None and y < lo:
                    continue
                if hi is not None and y > hi:
                    continue
            out.append(r)
        return out

    def route_summary(self, *, embark: str | None = None, disembark: str | None = None,
                      period: tuple[float, float] | None = None) -> dict:
        """Aggregate a region pair: voyage count, imputed embarked/disembarked, dates."""
        rows = self.voyages(embark=embark, disembark=disembark, period=period)
        embarked = sum(v for r in rows if (v := self.as_float(r.get("embarked"))) is not None)
        disembarked = sum(v for r in rows if (v := self.as_float(r.get("disembarked"))) is not None)
        years = [y for r in rows if (y := self.as_float(r.get("year"))) is not None]
        return {
            "voyages": len(rows),
            "embarked": embarked,
            "disembarked": disembarked,
            "year_min": min(years) if years else None,
            "year_max": max(years) if years else None,
        }
