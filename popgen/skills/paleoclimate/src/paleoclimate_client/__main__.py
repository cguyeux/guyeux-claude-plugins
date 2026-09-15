"""Shell CLI for the paleoclimate skill (run via a rasterio venv).

    PY=/home/christophe/venvs/geo311/bin/python
    $PY -m paleoclimate_client slices
    $PY -m paleoclimate_client sample --time-slice lgm --points "41.9,12.5" --vars bio_1,bio_12 --tsv
    $PY -m paleoclimate_client info

Exit codes: 0 ok, 1 error, 3 data/dependency unavailable.
"""
from __future__ import annotations

import argparse
import sys

from ._base import DatasetError, DatasetUnavailable
from .client import OUTPUT_BASE, PaleoclimateClient


def _parse_points(spec: str):
    pts = []
    for i, chunk in enumerate(p for p in spec.split(";") if p.strip()):
        lat, lon = chunk.split(",")
        pts.append((f"p{i + 1}", float(lat), float(lon)))
    return pts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="paleoclimate")
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample", help="sample paleo BIO variables at points for a time slice")
    s.add_argument("--points", required=True, help='"lat,lon;lat,lon"')
    s.add_argument("--time-slice", default=None, help="e.g. lgm, midholocene (a subdirectory)")
    s.add_argument("--vars", default=None, help="comma-separated, default all")
    s.add_argument("--tsv", action="store_true")
    sub.add_parser("slices", help="list available time slices")
    n = sub.add_parser("sample-nc", help="sample a NetCDF reconstruction at points (xarray)")
    n.add_argument("--points", required=True, help='"lat,lon;lat,lon"')
    n.add_argument("--time", default=None, help="nearest time/age/year (default: most recent)")
    n.add_argument("--vars", default=None, help="comma-separated, default all")
    n.add_argument("--tsv", action="store_true")
    sub.add_parser("nc-vars", help="list NetCDF data variables")
    sub.add_parser("info")
    args = parser.parse_args(argv)
    client = PaleoclimateClient()
    try:
        if args.cmd == "sample":
            pts = _parse_points(args.points)
            vs = args.vars.split(",") if args.vars else None
            rows = client.sample(pts, variables=vs, time_slice=args.time_slice)
            cols = OUTPUT_BASE + (vs if vs else [k for k in rows[0] if k not in OUTPUT_BASE]) if rows else OUTPUT_BASE
            if args.tsv:
                client.write_tsv(rows, cols, sys.stdout)
            else:
                print(f"{len(rows)} points sampled (slice={args.time_slice or '.'}, "
                      f"source={client.last_source})")
            return 0
        if args.cmd == "slices":
            sl = client.time_slices()
            print(f"# {len(sl)} time slices (source={client.last_source})")
            print(" ".join(sl))
            return 0
        if args.cmd == "nc-vars":
            v = client.nc_variables()
            print(f"# {len(v)} NetCDF variables (source={client.last_source})")
            print(" ".join(v))
            return 0
        if args.cmd == "sample-nc":
            pts = _parse_points(args.points)
            vs = args.vars.split(",") if args.vars else None
            t = args.time
            if t is not None:
                try:
                    t = float(t)
                except ValueError:
                    pass
            rows = client.sample_nc(pts, variables=vs, time=t)
            base = ["point_id", "lat", "lon", "time"]
            cols = base + (vs if vs else [k for k in rows[0] if k not in base]) if rows else base
            if args.tsv:
                client.write_tsv(rows, cols, sys.stdout)
            else:
                print(f"{len(rows)} points sampled from NetCDF (source={client.last_source})")
            return 0
        if args.cmd == "info":
            base = client._base_dir()
            print(f"version = {client.version}\nsource  = {client.last_source}\ndir     = {base}")
            return 0
    except DatasetUnavailable as e:
        print(f"paleoclimate unavailable:\n{e}", file=sys.stderr)
        return 3
    except DatasetError as e:
        print(f"paleoclimate error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
