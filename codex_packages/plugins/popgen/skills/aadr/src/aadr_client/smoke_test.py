"""Offline smoke test for the aadr skill.

Runs entirely on the bundled fixture (``fixtures/aadr_sample.anno.tsv``) in offline
mode, so it needs no network and no AADR download. Validates the three invariants
that actually break in practice:
  1. the dataset resolves (here: to the fixture),
  2. the STABLE schema is found despite the raw column names,
  3. a country/period/QC filter returns the expected rows.

    python -m aadr_client.smoke_test
"""
from __future__ import annotations

import sys

from ._base import DatasetError
from .client import AadrClient


def main() -> int:
    client = AadrClient(offline=True)  # force the fixture (no env file, no download)
    try:
        everyone = client.cohort(pass_only=False, allow_download=False)
        print(f"resolved source = {client.last_source}")
        if client.last_source != "fixture":
            print(f"FAIL: expected fixture, got {client.last_source}", file=sys.stderr)
            return 2
        if not everyone:
            print("FAIL: fixture returned no rows", file=sys.stderr)
            return 2

        cols = set(everyone[0])
        for need in ("genetic_id", "group", "country", "lat", "lon", "date_bp", "qc"):
            if need not in cols:
                print(f"FAIL: stable column {need!r} missing", file=sys.stderr)
                return 2

        sub = client.cohort(countries=["Sweden", "Hungary"], period_bp=(0, 2000),
                            pass_only=True, allow_download=False)
        print(f"fixture rows: {len(everyone)} total; "
              f"{len(sub)} Sweden/Hungary PASS within 2000 BP")
        if len(sub) < 1:
            print("FAIL: expected >=1 Sweden/Hungary PASS individual in fixture",
                  file=sys.stderr)
            return 2
    except DatasetError as e:
        print(f"FAIL (dataset): {e}", file=sys.stderr)
        return 3

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
