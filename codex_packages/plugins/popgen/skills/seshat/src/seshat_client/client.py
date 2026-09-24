"""Seshat client: turn a pinned snapshot into a filtered polity-record table.

Tool-first entry point for the seshat skill. Instead of re-deriving an
``sc[sc.variable == ...]`` filter by hand in every project, call::

    from seshat_client import SeshatClient
    rows = SeshatClient().polities(nga=["Latium"], period=(-500, 500),
                                   variable="Polity Population")

``polities`` returns a list of dicts with STABLE keys (see OUTPUT_COLUMNS), reads
either a `.csv` or `.xlsx` snapshot (or the bundled fixture in offline mode), and
never requires pandas. It propagates the ``[value_from, value_to]`` uncertainty
interval and adds ``value_mid`` without silently collapsing to the midpoint.
"""
from __future__ import annotations

import csv
from pathlib import Path

from ._base import FileDatasetClient
from .schema import SCHEMA
from .sources import DEFAULT_VERSION, SNAPSHOTS

# A record is meaningful as a dated polity even without a coded variable value.
REQUIRED = ["nga", "polity", "start_year", "end_year"]

# Stable output contract (consumed by downstream skills and by `polities --tsv`).
OUTPUT_COLUMNS = [
    "nga", "polity", "start_year", "end_year",
    "variable", "value_from", "value_to", "value_mid", "source",
]


class SeshatClient(FileDatasetClient):
    def __init__(self, **kwargs):
        here = Path(__file__).resolve()
        fixture = here.parents[2] / "fixtures" / "seshat_sc_sample.csv"
        super().__init__(
            slug="seshat",
            snapshots=SNAPSHOTS,
            default_version=DEFAULT_VERSION,
            schema=SCHEMA,
            fixture=fixture,
            delimiter=",",
            quoting=csv.QUOTE_MINIMAL,
            **kwargs,
        )

    def polities(self, *, nga: list[str] | None = None,
                 period: tuple[float, float] | None = None,
                 variable: str | None = None,
                 allow_download: bool = True) -> list[dict]:
        """Filter polity records by NGA, calendar-year window, and variable.

        Args:
            nga: keep only these Natural Geographic Areas (case-insensitive).
            period: ``(lo, hi)`` calendar years (BCE negative); keep polities whose
                ``[start_year, end_year]`` OVERLAPS the window.
            variable: keep records whose ``variable`` contains this text
                (case-insensitive), e.g. ``"Polity Population"``.

        Each row carries both bounds plus ``value_mid`` (mean of the interval, or
        ``""`` if either bound is missing): propagate the interval, do not take the
        bare midpoint downstream.
        """
        rows = self.read_rows(allow_download=allow_download, required=REQUIRED)
        ngaset = {n.strip().lower() for n in nga} if nga else None
        lo, hi = period if period is not None else (None, None)
        vneedle = variable.strip().lower() if variable else None

        out: list[dict] = []
        for r in rows:
            if ngaset is not None and (r.get("nga") or "").strip().lower() not in ngaset:
                continue
            if vneedle is not None and vneedle not in (r.get("variable") or "").lower():
                continue
            if lo is not None or hi is not None:
                s = self.as_float(r.get("start_year"))
                e = self.as_float(r.get("end_year"))
                if s is None or e is None:
                    continue
                if hi is not None and s > hi:      # polity begins after the window
                    continue
                if lo is not None and e < lo:      # polity ends before the window
                    continue
            vf = self.as_float(r.get("value_from"))
            vt = self.as_float(r.get("value_to"))
            row = dict(r)
            row["value_mid"] = "" if (vf is None or vt is None) else (vf + vt) / 2
            out.append(row)
        return out
