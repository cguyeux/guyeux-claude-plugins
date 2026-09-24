"""Shell CLI for the amtdb skill.

    python -m amtdb_client samples --bbox 35 -10 60 40 --period -3000 0 --haplogroup H --tsv
    python -m amtdb_client inspect
    python -m amtdb_client info

Exit codes: 0 ok, 1 error, 2 schema drift, 3 data unavailable.
"""
from __future__ import annotations

import argparse
import sys

from ._base import DatasetError, DatasetUnavailable, SchemaDrift
from .client import OUTPUT_COLUMNS, AmtdbClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="amtdb")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("samples", help="filter samples by bbox / period / haplogroup")
    sp.add_argument("--bbox", nargs=4, type=float, metavar=("S", "W", "N", "E"), default=None)
    sp.add_argument("--period", nargs=2, type=float, metavar=("LO", "HI"), default=None)
    sp.add_argument("--haplogroup", default=None)
    sp.add_argument("--tsv", action="store_true")
    sub.add_parser("inspect")
    sub.add_parser("info")
    args = parser.parse_args(argv)
    client = AmtdbClient()
    try:
        if args.cmd == "samples":
            bbox = tuple(args.bbox) if args.bbox else None
            period = (args.period[0], args.period[1]) if args.period else None
            rows = client.samples(bbox=bbox, period=period, haplogroup=args.haplogroup)
            if args.tsv:
                client.write_tsv(rows, OUTPUT_COLUMNS, sys.stdout)
            else:
                print(f"{len(rows)} samples (source={client.last_source})")
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
        print(f"amtdb unavailable:\n{e}", file=sys.stderr)
        return 3
    except SchemaDrift as e:
        print(f"amtdb schema drift: {e}", file=sys.stderr)
        return 2
    except DatasetError as e:
        print(f"amtdb error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
