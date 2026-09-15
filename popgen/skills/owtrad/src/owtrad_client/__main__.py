"""Shell CLI for the owtrad skill.

    python -m owtrad_client routes --name Silk --type trade --bbox 20 30 50 110 --tsv
    python -m owtrad_client routes --tsv
    python -m owtrad_client info

Exit codes: 0 ok, 1 error, 3 data/dependency unavailable.
"""
from __future__ import annotations

import argparse
import sys

from ._base import DatasetError, DatasetUnavailable
from .client import OUTPUT_COLUMNS, OwtradClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="owtrad")
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("routes", help="filter routes by name / type / bbox")
    r.add_argument("--name", default=None)
    r.add_argument("--type", dest="route_type", default=None, help="trade | pilgrimage | military | caravan | transhumance ...")
    r.add_argument("--bbox", nargs=4, type=float, metavar=("S", "W", "N", "E"), default=None)
    r.add_argument("--tsv", action="store_true")
    sub.add_parser("info")
    args = parser.parse_args(argv)
    client = OwtradClient()
    try:
        if args.cmd == "routes":
            bbox = tuple(args.bbox) if args.bbox else None
            rows = client.routes(name=args.name, route_type=args.route_type, bbox=bbox)
            if args.tsv:
                client.write_tsv(rows, OUTPUT_COLUMNS, sys.stdout)
            else:
                total = sum(r["length_km"] for r in rows if isinstance(r["length_km"], (int, float)))
                print(f"{len(rows)} routes, {total:.0f} km total (source={client.last_source})")
            return 0
        if args.cmd == "info":
            path = client.resolve_dataset(allow_download=False)
            print(f"version = {client.version}\nsource  = {client.last_source}\npath    = {path}")
            return 0
    except DatasetUnavailable as e:
        print(f"owtrad unavailable:\n{e}", file=sys.stderr)
        return 3
    except DatasetError as e:
        print(f"owtrad error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
