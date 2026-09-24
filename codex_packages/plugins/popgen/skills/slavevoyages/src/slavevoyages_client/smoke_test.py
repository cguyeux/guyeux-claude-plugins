"""Offline smoke test for the slavevoyages skill.

Runs entirely on the bundled fixture (``fixtures/slavevoyages_sample.csv``) in
offline mode: no network, no SlaveVoyages download. Validates:
  1. the dataset resolves (here: to the fixture),
  2. the STABLE schema is found despite the SPSS variable codes,
  3. an embark/disembark/period filter and the route summary return sane values.

    python -m slavevoyages_client.smoke_test
"""
from __future__ import annotations

import sys

from ._base import DatasetError
from .client import SlaveVoyagesClient


def main() -> int:
    client = SlaveVoyagesClient(offline=True)  # force the fixture
    try:
        allv = client.voyages(allow_download=False)
        print(f"resolved source = {client.last_source}")
        if client.last_source != "fixture":
            print(f"FAIL: expected fixture, got {client.last_source}", file=sys.stderr)
            return 2
        if not allv:
            print("FAIL: fixture returned no rows", file=sys.stderr)
            return 2

        cols = set(allv[0])
        for need in ("voyage_id", "year", "embark_region", "disembark_region", "embarked"):
            if need not in cols:
                print(f"FAIL: stable column {need!r} missing", file=sys.stderr)
                return 2

        gc_br = client.voyages(embark="Gold Coast", disembark="Brazil",
                               period=(1700, 1800), allow_download=False)
        summ = client.route_summary(embark="Gold Coast", disembark="Brazil",
                                    period=(1700, 1800))
        print(f"fixture rows: {len(allv)} voyages; Gold Coast->Brazil 1700-1800 = "
              f"{summ['voyages']} voyages, {summ['embarked']:.0f} embarked "
              f"({summ['year_min']:.0f}-{summ['year_max']:.0f})")
        if len(gc_br) < 1 or summ["embarked"] <= 0:
            print("FAIL: expected >=1 Gold Coast->Brazil voyage with embarked>0",
                  file=sys.stderr)
            return 2
    except DatasetError as e:
        print(f"FAIL (dataset): {e}", file=sys.stderr)
        return 3

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
