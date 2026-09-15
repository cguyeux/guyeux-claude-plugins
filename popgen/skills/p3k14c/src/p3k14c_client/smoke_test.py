"""Offline smoke test for the p3k14c skill (bundled fixture, no network)."""
from __future__ import annotations

import sys

from ._base import DatasetError
from .client import P3k14cClient


def main() -> int:
    client = P3k14cClient(offline=True)
    try:
        alld = client.dates(allow_download=False)
        print(f"resolved source = {client.last_source}")
        if client.last_source != "fixture" or not alld:
            print("FAIL: fixture not resolved or empty", file=sys.stderr)
            return 2
        for need in ("age_bp", "continent", "lat", "lon"):
            if need not in alld[0]:
                print(f"FAIL: stable column {need!r} missing", file=sys.stderr)
                return 2
        sa = client.dates(continent="SAmerica", age_bp=(500, 1500), allow_download=False)
        print(f"fixture: {len(alld)} dates; {len(sa)} in SAmerica 500-1500 BP")
        if len(sa) < 1:
            print("FAIL: expected >=1 SAmerica date in window", file=sys.stderr)
            return 2
    except DatasetError as e:
        print(f"FAIL (dataset): {e}", file=sys.stderr)
        return 3
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
