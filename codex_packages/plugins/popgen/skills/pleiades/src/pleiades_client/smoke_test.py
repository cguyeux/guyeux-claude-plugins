"""Offline smoke test for the pleiades skill (bundled fixture, no network)."""
from __future__ import annotations

import sys

from ._base import DatasetError
from .client import PleiadesClient


def main() -> int:
    client = PleiadesClient(offline=True)
    try:
        allp = client.places(allow_download=False)
        print(f"resolved source = {client.last_source}")
        if client.last_source != "fixture" or not allp:
            print("FAIL: fixture not resolved or empty", file=sys.stderr)
            return 2
        for need in ("id", "title", "lat", "lon", "time_periods"):
            if need not in allp[0]:
                print(f"FAIL: stable column {need!r} missing", file=sys.stderr)
                return 2
        roman = client.places(bbox=(30, -10, 47, 40), period="R", allow_download=False)
        print(f"fixture: {len(allp)} places; {len(roman)} Roman-period in the Mediterranean bbox")
        if len(roman) < 1:
            print("FAIL: expected >=1 Roman-period place in bbox", file=sys.stderr)
            return 2
    except DatasetError as e:
        print(f"FAIL (dataset): {e}", file=sys.stderr)
        return 3
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
