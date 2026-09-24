"""Shell CLI for the seshat skill.

    python -m seshat_client polities --nga Latium --period -500 500 --variable "Polity Population" --tsv
    python -m seshat_client polities --nga "Upper Egypt" --period -3000 -1000        # count
    python -m seshat_client inspect     # print the raw header of the resolved snapshot
    python -m seshat_client info        # show resolved version + provenance

Exit codes: 0 ok, 1 error, 2 schema drift, 3 data unavailable.
"""
from __future__ import annotations

import argparse
import sys

from ._base import DatasetError, DatasetUnavailable, SchemaDrift
from .client import OUTPUT_COLUMNS, SeshatClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="seshat")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("polities", help="filter polity records by NGA / period / variable")
    p.add_argument("--nga", nargs="*", default=None, help="Natural Geographic Areas")
    p.add_argument("--period", nargs=2, type=float, metavar=("LO", "HI"),
                   default=None, help="calendar-year window (BCE negative)")
    p.add_argument("--variable", default=None,
                   help='coded trait, e.g. "Polity Population" (substring match)')
    p.add_argument("--tsv", action="store_true",
                   help="write the records as TSV to stdout (default: print a count)")

    sub.add_parser("inspect", help="print the raw column header of the resolved snapshot")
    sub.add_parser("info", help="print resolved version + source provenance")

    args = parser.parse_args(argv)
    client = SeshatClient()

    try:
        if args.cmd == "polities":
            period = (args.period[0], args.period[1]) if args.period else None
            rows = client.polities(nga=args.nga, period=period, variable=args.variable)
            if args.tsv:
                client.write_tsv(rows, OUTPUT_COLUMNS, sys.stdout)
            else:
                print(f"{len(rows)} records (source={client.last_source}, "
                      f"version={client.version})")
            return 0

        if args.cmd == "inspect":
            header = client.header_of()
            print(f"# source={client.last_source} version={client.version} "
                  f"ncols={len(header)}")
            for h in header:
                print(h)
            return 0

        if args.cmd == "info":
            path = client.resolve_dataset(allow_download=False)
            print(f"version = {client.version}")
            print(f"source  = {client.last_source}")
            print(f"path    = {path}")
            return 0

    except DatasetUnavailable as e:
        print(f"seshat unavailable:\n{e}", file=sys.stderr)
        return 3
    except SchemaDrift as e:
        print(f"seshat schema drift: {e}", file=sys.stderr)
        return 2
    except DatasetError as e:
        print(f"seshat error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
