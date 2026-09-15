"""Shell CLI for the d-place skill.

    python -m dplace_client societies --bbox -35 -20 15 52 --dataset EA --tsv
    python -m dplace_client societies --glottocode swah1253
    python -m dplace_client inspect
    python -m dplace_client info
"""
from __future__ import annotations

import argparse
import sys

from ._base import DatasetError, DatasetUnavailable, SchemaDrift
from .client import OUTPUT_COLUMNS, DplaceClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="d-place")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("societies", help="filter societies by bbox / glottocode / family / dataset")
    p.add_argument("--bbox", nargs=4, type=float, metavar=("S", "W", "N", "E"), default=None)
    p.add_argument("--glottocode", default=None)
    p.add_argument("--family", default=None)
    p.add_argument("--dataset", default=None, help="EA | Binford | SCCS | WNAI | ...")
    p.add_argument("--tsv", action="store_true")
    sub.add_parser("inspect")
    sub.add_parser("info")
    args = parser.parse_args(argv)
    client = DplaceClient()
    try:
        if args.cmd == "societies":
            bbox = tuple(args.bbox) if args.bbox else None
            rows = client.societies(bbox=bbox, glottocode=args.glottocode,
                                    family=args.family, dataset=args.dataset)
            if args.tsv:
                client.write_tsv(rows, OUTPUT_COLUMNS, sys.stdout)
            else:
                print(f"{len(rows)} societies (source={client.last_source})")
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
        print(f"d-place unavailable:\n{e}", file=sys.stderr)
        return 3
    except SchemaDrift as e:
        print(f"d-place schema drift: {e}", file=sys.stderr)
        return 2
    except DatasetError as e:
        print(f"d-place error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
