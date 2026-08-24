"""Offline smoke test for the amtdb skill (bundled fixture, no network)."""
from __future__ import annotations

import sys

from ._base import DatasetError
from .client import AmtdbClient


def main() -> int:
    client = AmtdbClient(offline=True)
    try:
        alls = client.samples(allow_download=False)
        print(f"resolved source = {client.last_source}")
        if client.last_source != "fixture" or not alls:
            print("FAIL: fixture not resolved or empty", file=sys.stderr)
            return 2
        for need in ("id", "mt_hg", "lat", "lon", "year_from"):
            if need not in alls[0]:
                print(f"FAIL: stable column {need!r} missing", file=sys.stderr)
                return 2
        h = client.samples(haplogroup="H", period=(-5000, 0), allow_download=False)
        print(f"fixture: {len(alls)} samples; {len(h)} hg H* within 5000 BCE-0")
        if len(h) < 1:
            print("FAIL: expected >=1 H* sample in window", file=sys.stderr)
            return 2
    except DatasetError as e:
        print(f"FAIL (dataset): {e}", file=sys.stderr)
        return 3
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
