"""Offline smoke test for worldclim-bioclim (bundled raster fixture; needs rasterio).

    /home/christophe/venvs/geo311/bin/python -m wcbio_client.smoke_test
"""
from __future__ import annotations

import sys

from ._base import DatasetError
from .client import WorldclimClient


def main() -> int:
    client = WorldclimClient(offline=True)
    try:
        vs = client.variables()
        print(f"resolved source = {client.last_source}; variables = {vs}")
        if client.last_source != "fixture" or "bio_1" not in vs:
            print("FAIL: fixture not resolved or bio_1 missing", file=sys.stderr)
            return 2
        # fixture bio_1[row,col] = 100*row + col; point (41.5,12.5) -> row 2, col 2 -> 202
        rows = client.sample([("Roma", 41.5, 12.5)], variables=["bio_1"])
        got = rows[0]["bio_1"]
        print(f"sample Roma bio_1 = {got}")
        if got != 202.0:
            print(f"FAIL: expected bio_1=202 at fixture point, got {got}", file=sys.stderr)
            return 2
        # multi-variable + multi-point
        multi = client.sample([("Roma", 41.5, 12.5), ("NW", 43.5, 10.5)],
                              variables=["bio_1", "bio_12"])
        if len(multi) != 2 or "bio_12" not in multi[0]:
            print("FAIL: multi-variable sampling broken", file=sys.stderr)
            return 2
    except DatasetError as e:
        print(f"FAIL (dataset/deps): {e}", file=sys.stderr)
        return 3
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
