"""Offline smoke test for the seshat skill.

Runs entirely on the bundled CSV fixture (``fixtures/seshat_sc_sample.csv``) in
offline mode: no network, no Seshat download. Validates the three invariants:
  1. the snapshot resolves (here: to the fixture),
  2. the STABLE schema is found despite the raw column names,
  3. an NGA / period / variable filter returns the expected records.

    python -m seshat_client.smoke_test
"""
from __future__ import annotations

import sys

from ._base import DatasetError
from .client import SeshatClient


def main() -> int:
    client = SeshatClient(offline=True)  # force the fixture (no env file, no download)
    try:
        everything = client.polities(allow_download=False)
        print(f"resolved source = {client.last_source}")
        if client.last_source != "fixture":
            print(f"FAIL: expected fixture, got {client.last_source}", file=sys.stderr)
            return 2
        if not everything:
            print("FAIL: fixture returned no rows", file=sys.stderr)
            return 2

        cols = set(everything[0])
        for need in ("nga", "polity", "start_year", "end_year", "variable", "value_mid"):
            if need not in cols:
                print(f"FAIL: stable column {need!r} missing", file=sys.stderr)
                return 2

        latium_pop = client.polities(nga=["Latium"], period=(-500, 500),
                                     variable="Polity Population", allow_download=False)
        print(f"fixture rows: {len(everything)} total; "
              f"{len(latium_pop)} Latium 'Polity Population' records within -500..500 CE")
        if len(latium_pop) < 1:
            print("FAIL: expected >=1 Latium Polity Population record in window",
                  file=sys.stderr)
            return 2
        # interval propagation: value_mid present and numeric when bounds exist
        with_mid = [r for r in latium_pop if r.get("value_mid") not in ("", None)]
        if not with_mid:
            print("FAIL: expected value_mid computed from the interval", file=sys.stderr)
            return 2
    except DatasetError as e:
        print(f"FAIL (dataset): {e}", file=sys.stderr)
        return 3

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
