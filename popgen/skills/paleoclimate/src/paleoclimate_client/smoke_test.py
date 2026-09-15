"""Offline smoke test for paleoclimate (bundled raster fixture; needs rasterio).

    /home/christophe/venvs/geo311/bin/python -m paleoclimate_client.smoke_test
"""
from __future__ import annotations

import sys

from ._base import DatasetError
from .client import PaleoclimateClient


def main() -> int:
    client = PaleoclimateClient(offline=True)
    try:
        slices = client.time_slices()
        print(f"resolved source = {client.last_source}; time slices = {slices}")
        if client.last_source != "fixture" or "lgm" not in slices:
            print("FAIL: fixture not resolved or 'lgm' slice missing", file=sys.stderr)
            return 2
        # fixture lgm/bio_1[row,col] = 100*row + col; point (41.5,12.5) -> 202
        rows = client.sample([("Roma", 41.5, 12.5)], variables=["bio_1"], time_slice="lgm")
        got = rows[0]["bio_1"]
        print(f"sample Roma bio_1 @ lgm = {got} (time_slice={rows[0]['time_slice']})")
        if got != 202.0 or rows[0]["time_slice"] != "lgm":
            print(f"FAIL: expected bio_1=202 @ lgm, got {got}", file=sys.stderr)
            return 2

        # NetCDF path (xarray): sample the bundled reconstruction fixture.
        # fixture tas[t,lat,lon] = 100*t_idx + 10*lat_idx + lon_idx;
        # point (41,12) -> lat idx 1, lon idx 2; t=-6000 -> t idx 1 -> 112.
        ncv = client.nc_variables()
        print(f"NetCDF variables = {ncv}")
        nc = client.sample_nc([("p", 41.0, 12.0)], variables=["tas"], time=-6000)
        tas = nc[0]["tas"]
        print(f"sample_nc tas @ (41,12), t=-6000 = {tas} (time={nc[0]['time']})")
        if tas != 112.0:
            print(f"FAIL: expected tas=112 from NetCDF fixture, got {tas}", file=sys.stderr)
            return 2
    except DatasetError as e:
        print(f"FAIL (dataset/deps): {e}", file=sys.stderr)
        return 3
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
