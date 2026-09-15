"""Offline smoke test for the glottolog skill (bundled fixture, no network)."""
from __future__ import annotations

import sys

from ._base import DatasetError
from .client import GlottologClient


def main() -> int:
    client = GlottologClient(offline=True)
    try:
        alll = client.languages(allow_download=False)
        print(f"resolved source = {client.last_source}")
        if client.last_source != "fixture" or not alll:
            print("FAIL: fixture not resolved or empty", file=sys.stderr)
            return 2
        for need in ("glottocode", "name", "macroarea", "lat", "lon"):
            if need not in alll[0]:
                print(f"FAIL: stable column {need!r} missing", file=sys.stderr)
                return 2
        afr = client.languages(macroarea="Africa", allow_download=False)
        print(f"fixture: {len(alll)} languoids; {len(afr)} in Africa")
        if len(afr) < 1:
            print("FAIL: expected >=1 African languoid", file=sys.stderr)
            return 2
    except DatasetError as e:
        print(f"FAIL (dataset): {e}", file=sys.stderr)
        return 3
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
