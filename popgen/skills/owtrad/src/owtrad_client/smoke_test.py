"""Offline smoke test for the owtrad skill (bundled GeoJSON fixture, no network).

Needs geopandas (present on the system Python). Validates: the vector file resolves,
geometries are read, and a name/type/bbox filter returns routes with a sane length.

    python -m owtrad_client.smoke_test
"""
from __future__ import annotations

import sys

from ._base import DatasetError
from .client import OwtradClient


def main() -> int:
    client = OwtradClient(offline=True)
    try:
        allr = client.routes(allow_download=False)
        print(f"resolved source = {client.last_source}; {len(allr)} routes")
        if client.last_source != "fixture" or not allr:
            print("FAIL: fixture not resolved or empty", file=sys.stderr)
            return 2
        for need in ("name", "route_type", "geom_type", "n_points", "length_km"):
            if need not in allr[0]:
                print(f"FAIL: stable column {need!r} missing", file=sys.stderr)
                return 2
        silk = client.routes(name="Silk", allow_download=False)
        print(f"{len(silk)} route(s) matching 'Silk'; "
              f"first length = {silk[0]['length_km'] if silk else 'n/a'} km")
        if len(silk) < 1 or not (silk[0]["length_km"] > 0):
            print("FAIL: expected a 'Silk' route with positive length", file=sys.stderr)
            return 2
        trade = client.routes(route_type="trade", allow_download=False)
        if len(trade) < 1:
            print("FAIL: expected >=1 trade route", file=sys.stderr)
            return 2
    except DatasetError as e:
        print(f"FAIL (dataset/deps): {e}", file=sys.stderr)
        return 3
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
