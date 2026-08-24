"""Offline smoke test for the neolithic-14c skill (bundled fixture, no network)."""
from __future__ import annotations

import sys

from ._base import DatasetError
from .client import NerdClient


def main() -> int:
    client = NerdClient(offline=True)
    try:
        alld = client.dates(allow_download=False)
        print(f"resolved source = {client.last_source}")
        if client.last_source != "fixture" or not alld:
            print("FAIL: fixture not resolved or empty", file=sys.stderr)
            return 2
        for need in ("age_bp", "lat", "lon", "material"):
            if need not in alld[0]:
                print(f"FAIL: stable column {need!r} missing", file=sys.stderr)
                return 2
        eu = client.dates(bbox=(35, -10, 60, 40), age_bp=(5000, 7000), allow_download=False)
        print(f"fixture: {len(alld)} dates; {len(eu)} in Europe 5000-7000 BP")
        if len(eu) < 1:
            print("FAIL: expected >=1 European date in window", file=sys.stderr)
            return 2
    except DatasetError as e:
        print(f"FAIL (dataset): {e}", file=sys.stderr)
        return 3
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
