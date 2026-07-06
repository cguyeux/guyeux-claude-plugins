"""Shell CLI for the pleiades skill.

    python -m pleiades_client places --bbox 30 -10 47 40 --period R --feature-type settlement --tsv
    python -m pleiades_client inspect
    python -m pleiades_client info

Exit codes: 0 ok, 1 error, 2 schema drift, 3 data unavailable.
"""
from __future__ import annotations

import argparse
import sys

from ._base import DatasetError, DatasetUnavailable, SchemaDrift
from .client import OUTPUT_COLUMNS, PleiadesClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pleiades")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("places", help="filter places by bbox / period / feature type")
    p.add_argument("--bbox", nargs=4, type=float, metavar=("S", "W", "N", "E"), default=None)
    p.add_argument("--period", default=None, help="period code A/C/H/R/L/M")
    p.add_argument("--feature-type", default=None)
    p.add_argument("--tsv", action="store_true")
    sub.add_parser("inspect")
    sub.add_parser("info")
    args = parser.parse_args(argv)
    client = PleiadesClient()
    try:
        if args.cmd == "places":
            bbox = tuple(args.bbox) if args.bbox else None
            rows = client.places(bbox=bbox, period=args.period, feature_type=args.feature_type)
            if args.tsv:
                client.write_tsv(rows, OUTPUT_COLUMNS, sys.stdout)
            else:
                print(f"{len(rows)} places (source={client.last_source})")
            return 0
        if args.cmd == "inspect":
            header = client.header_of()
            print(f"# source={client.last_source} version={client.version} ncols={len(header)}")
            print("\n".join(header))
            return 0
        if args.cmd == "info":
            path = client.resolve_dataset(allow_download=False)
            print(f"version = {client.version}\nsource  = {client.last_source}\npath    = {path}")
            return 0
    except DatasetUnavailable as e:
        print(f"pleiades unavailable:\n{e}", file=sys.stderr)
        return 3
    except SchemaDrift as e:
        print(f"pleiades schema drift: {e}", file=sys.stderr)
        return 2
    except DatasetError as e:
        print(f"pleiades error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
