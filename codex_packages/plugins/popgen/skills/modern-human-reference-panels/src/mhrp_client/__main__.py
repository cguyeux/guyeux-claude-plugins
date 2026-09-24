"""Shell CLI for the modern-human-reference-panels skill.

    python -m mhrp_client samples --project HGDP --region AFRICA --tsv
    python -m mhrp_client samples --population Yoruba
    python -m mhrp_client inspect
    python -m mhrp_client info
"""
from __future__ import annotations

import argparse
import sys

from ._base import DatasetError, DatasetUnavailable, SchemaDrift
from .client import OUTPUT_COLUMNS, MhrpClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mhrp")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("samples", help="filter samples by population / region / project / bbox")
    p.add_argument("--population", default=None)
    p.add_argument("--region", default=None)
    p.add_argument("--project", default=None, help="HGDP | 1kGP | ...")
    p.add_argument("--bbox", nargs=4, type=float, metavar=("S", "W", "N", "E"), default=None)
    p.add_argument("--tsv", action="store_true")
    sub.add_parser("inspect")
    sub.add_parser("info")
    args = parser.parse_args(argv)
    client = MhrpClient()
    try:
        if args.cmd == "samples":
            bbox = tuple(args.bbox) if args.bbox else None
            rows = client.samples(population=args.population, region=args.region,
                                  project=args.project, bbox=bbox)
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
        print(f"mhrp unavailable:\n{e}", file=sys.stderr)
        return 3
    except SchemaDrift as e:
        print(f"mhrp schema drift: {e}", file=sys.stderr)
        return 2
    except DatasetError as e:
        print(f"mhrp error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
