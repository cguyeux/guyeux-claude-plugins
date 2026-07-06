"""Shell CLI for the aadr skill.

    python -m aadr_client cohort --countries Germany Hungary --period-bp 0 1500 --tsv
    python -m aadr_client cohort --countries Sweden --period-bp 0 2000        # count
    python -m aadr_client inspect      # print the raw header of the resolved file
    python -m aadr_client info         # show resolved version + provenance

Exit codes: 0 ok, 1 error, 2 schema drift, 3 data unavailable.
"""
from __future__ import annotations

import argparse
import sys

from ._base import DatasetError, DatasetUnavailable, SchemaDrift
from .client import OUTPUT_COLUMNS, AadrClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aadr")
    sub = parser.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("cohort", help="filter individuals by country / period / QC")
    c.add_argument("--countries", nargs="*", default=None,
                   help="modern country names (Political Entity), case-insensitive")
    c.add_argument("--period-bp", nargs=2, type=float, metavar=("LO", "HI"),
                   default=None, help="age window in years BP (present-day == 0)")
    c.add_argument("--all", action="store_true",
                   help="include non-PASS individuals (default: PASS only)")
    c.add_argument("--tsv", action="store_true",
                   help="write the cohort as TSV to stdout (default: print a count)")

    sub.add_parser("inspect", help="print the raw column header of the resolved file")
    sub.add_parser("info", help="print resolved version + source provenance")

    args = parser.parse_args(argv)
    client = AadrClient()

    try:
        if args.cmd == "cohort":
            period = (args.period_bp[0], args.period_bp[1]) if args.period_bp else None
            rows = client.cohort(countries=args.countries, period_bp=period,
                                 pass_only=not args.all)
            if args.tsv:
                client.write_tsv(rows, OUTPUT_COLUMNS, sys.stdout)
            else:
                print(f"{len(rows)} individuals (source={client.last_source}, "
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
        print(f"aadr unavailable:\n{e}", file=sys.stderr)
        return 3
    except SchemaDrift as e:
        print(f"aadr schema drift: {e}", file=sys.stderr)
        return 2
    except DatasetError as e:
        print(f"aadr error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
