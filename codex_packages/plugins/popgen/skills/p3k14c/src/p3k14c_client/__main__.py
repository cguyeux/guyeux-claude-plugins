"""Shell CLI for the p3k14c skill.

    python -m p3k14c_client dates --continent SAmerica --age-bp 500 1500 --material bone --tsv
    python -m p3k14c_client dates --bbox -56 -82 13 -34 --age-bp 0 2000
    python -m p3k14c_client inspect
    python -m p3k14c_client info

Exit codes: 0 ok, 1 error, 2 schema drift, 3 data unavailable.
"""
from __future__ import annotations

import argparse
import sys

from ._base import DatasetError, DatasetUnavailable, SchemaDrift
from .client import OUTPUT_COLUMNS, P3k14cClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="p3k14c")
    sub = parser.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dates", help="filter dates by bbox / age / material / continent")
    d.add_argument("--bbox", nargs=4, type=float, metavar=("S", "W", "N", "E"), default=None)
    d.add_argument("--age-bp", nargs=2, type=float, metavar=("LO", "HI"), default=None)
    d.add_argument("--material", default=None)
    d.add_argument("--continent", default=None)
    d.add_argument("--tsv", action="store_true")
    sub.add_parser("inspect")
    sub.add_parser("info")
    args = parser.parse_args(argv)
    client = P3k14cClient()
    try:
        if args.cmd == "dates":
            bbox = tuple(args.bbox) if args.bbox else None
            age = (args.age_bp[0], args.age_bp[1]) if args.age_bp else None
            rows = client.dates(bbox=bbox, age_bp=age, material=args.material,
                                continent=args.continent)
            if args.tsv:
                client.write_tsv(rows, OUTPUT_COLUMNS, sys.stdout)
            else:
                print(f"{len(rows)} dates (source={client.last_source})")
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
        print(f"p3k14c unavailable:\n{e}", file=sys.stderr)
        return 3
    except SchemaDrift as e:
        print(f"p3k14c schema drift: {e}", file=sys.stderr)
        return 2
    except DatasetError as e:
        print(f"p3k14c error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
