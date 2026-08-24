"""Offline smoke test for the wals skill (bundled fixture, no network)."""
from __future__ import annotations

import sys

from ._base import DatasetError
from .client import WalsClient


def main() -> int:
    client = WalsClient(offline=True)
    try:
        alll = client.languages(allow_download=False)
        print(f"resolved source = {client.last_source}")
        if client.last_source != "fixture" or not alll:
            print("FAIL: fixture not resolved or empty", file=sys.stderr)
            return 2
        for need in ("id", "name", "family", "genus", "lat", "lon"):
            if need not in alll[0]:
                print(f"FAIL: stable column {need!r} missing", file=sys.stderr)
                return 2
        nc = client.languages(family="Niger-Congo", allow_download=False)
        print(f"fixture: {len(alll)} languages; {len(nc)} Niger-Congo")
        if len(nc) < 1:
            print("FAIL: expected >=1 Niger-Congo language", file=sys.stderr)
            return 2
    except DatasetError as e:
        print(f"FAIL (dataset): {e}", file=sys.stderr)
        return 3
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
