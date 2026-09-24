"""Shell CLI for the glottolog skill.

    python -m glottolog_client languages --macroarea Africa --bbox -35 -20 15 52 --tsv
    python -m glottolog_client languages --name swahili
    python -m glottolog_client inspect
    python -m glottolog_client info
"""
from __future__ import annotations

import argparse
import sys

from ._base import DatasetError, DatasetUnavailable, SchemaDrift
from .client import OUTPUT_COLUMNS, GlottologClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="glottolog")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("languages", help="filter languoids by macroarea / bbox / level / name")
    p.add_argument("--macroarea", default=None)
    p.add_argument("--bbox", nargs=4, type=float, metavar=("S", "W", "N", "E"), default=None)
    p.add_argument("--level", default=None, help="language | family | dialect")
    p.add_argument("--name", default=None)
    p.add_argument("--tsv", action="store_true")
    sub.add_parser("inspect")
    sub.add_parser("info")
    args = parser.parse_args(argv)
    client = GlottologClient()
    try:
        if args.cmd == "languages":
            bbox = tuple(args.bbox) if args.bbox else None
            rows = client.languages(macroarea=args.macroarea, bbox=bbox,
                                    level=args.level, name=args.name)
            if args.tsv:
                client.write_tsv(rows, OUTPUT_COLUMNS, sys.stdout)
            else:
                print(f"{len(rows)} languoids (source={client.last_source})")
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
        print(f"glottolog unavailable:\n{e}", file=sys.stderr)
        return 3
    except SchemaDrift as e:
        print(f"glottolog schema drift: {e}", file=sys.stderr)
        return 2
    except DatasetError as e:
        print(f"glottolog error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
