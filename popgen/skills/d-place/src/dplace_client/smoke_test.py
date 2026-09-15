"""Offline smoke test for the d-place skill (bundled fixture, no network)."""
from __future__ import annotations

import sys

from ._base import DatasetError
from .client import DplaceClient


def main() -> int:
    client = DplaceClient(offline=True)
    try:
        alls = client.societies(allow_download=False)
        print(f"resolved source = {client.last_source}")
        if client.last_source != "fixture" or not alls:
            print("FAIL: fixture not resolved or empty", file=sys.stderr)
            return 2
        for need in ("id", "name", "glottocode", "lat", "lon", "dataset"):
            if need not in alls[0]:
                print(f"FAIL: stable column {need!r} missing", file=sys.stderr)
                return 2
        ea = client.societies(dataset="EA", allow_download=False)
        print(f"fixture: {len(alls)} societies; {len(ea)} from the EA dataset")
        if len(ea) < 1:
            print("FAIL: expected >=1 EA society", file=sys.stderr)
            return 2
    except DatasetError as e:
        print(f"FAIL (dataset): {e}", file=sys.stderr)
        return 3
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
