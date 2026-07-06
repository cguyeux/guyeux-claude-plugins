"""Shell CLI for the wals skill.

    python -m wals_client languages --family Niger-Congo --macroarea Africa --tsv
    python -m wals_client languages --bbox -35 -20 15 52
    python -m wals_client inspect
    python -m wals_client info
"""
from __future__ import annotations

import argparse
import sys

from ._base import DatasetError, DatasetUnavailable, SchemaDrift
from .client import OUTPUT_COLUMNS, WalsClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wals")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("languages", help="filter languages by family / genus / macroarea / bbox")
    p.add_argument("--family", default=None)
    p.add_argument("--genus", default=None)
    p.add_argument("--macroarea", default=None)
    p.add_argument("--bbox", nargs=4, type=float, metavar=("S", "W", "N", "E"), default=None)
    p.add_argument("--tsv", action="store_true")
    sub.add_parser("inspect")
    sub.add_parser("info")
    args = parser.parse_args(argv)
    client = WalsClient()
    try:
        if args.cmd == "languages":
            bbox = tuple(args.bbox) if args.bbox else None
            rows = client.languages(family=args.family, genus=args.genus,
                                    macroarea=args.macroarea, bbox=bbox)
            if args.tsv:
                client.write_tsv(rows, OUTPUT_COLUMNS, sys.stdout)
            else:
                print(f"{len(rows)} languages (source={client.last_source})")
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
        print(f"wals unavailable:\n{e}", file=sys.stderr)
        return 3
    except SchemaDrift as e:
        print(f"wals schema drift: {e}", file=sys.stderr)
        return 2
    except DatasetError as e:
        print(f"wals error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
