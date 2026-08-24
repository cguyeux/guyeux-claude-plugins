"""Shell CLI for the worldclim-bioclim skill (run via a rasterio venv).

    PY=/home/christophe/venvs/geo311/bin/python
    $PY -m wcbio_client variables
    $PY -m wcbio_client sample --points "41.9,12.5;-12.0,-77.0" --vars bio_1,bio_12 --tsv
    $PY -m wcbio_client info

Exit codes: 0 ok, 1 error, 3 data/dependency unavailable.
"""
from __future__ import annotations

import argparse
import sys

from ._base import DatasetError, DatasetUnavailable
from .client import OUTPUT_BASE, WorldclimClient


def _parse_points(spec: str):
    pts = []
    for i, chunk in enumerate(p for p in spec.split(";") if p.strip()):
        lat, lon = chunk.split(",")
        pts.append((f"p{i + 1}", float(lat), float(lon)))
    return pts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wcbio")
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample", help="sample BIO variables at points")
    s.add_argument("--points", required=True, help='"lat,lon;lat,lon"')
    s.add_argument("--vars", default=None, help="comma-separated, e.g. bio_1,bio_12 (default: all)")
    s.add_argument("--tsv", action="store_true")
    sub.add_parser("variables", help="list available BIO variables in the resolved directory")
    sub.add_parser("info")
    args = parser.parse_args(argv)
    client = WorldclimClient()
    try:
        if args.cmd == "sample":
            pts = _parse_points(args.points)
            vs = args.vars.split(",") if args.vars else None
            rows = client.sample(pts, variables=vs)
            cols = OUTPUT_BASE + (vs if vs else client.variables())
            if args.tsv:
                client.write_tsv(rows, cols, sys.stdout)
            else:
                print(f"{len(rows)} points sampled (source={client.last_source}, "
                      f"vars={vs or 'all'})")
            return 0
        if args.cmd == "variables":
            v = client.variables()
            print(f"# {len(v)} variables (source={client.last_source})")
            print(" ".join(v))
            return 0
        if args.cmd == "info":
            d = client._raster_dir()
            print(f"version = {client.version}\nsource  = {client.last_source}\ndir     = {d}")
            return 0
    except DatasetUnavailable as e:
        print(f"worldclim unavailable:\n{e}", file=sys.stderr)
        return 3
    except DatasetError as e:
        print(f"worldclim error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
