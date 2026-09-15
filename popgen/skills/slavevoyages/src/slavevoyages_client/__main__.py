"""Shell CLI for the slavevoyages skill.

    python -m slavevoyages_client voyages --embark "Gold Coast" --disembark Brazil --period 1700 1800 --tsv
    python -m slavevoyages_client summary --embark "Gold Coast" --disembark Brazil
    python -m slavevoyages_client inspect    # print the raw header of the resolved CSV
    python -m slavevoyages_client info       # show resolved provenance

Exit codes: 0 ok, 1 error, 2 schema drift, 3 data unavailable.
"""
from __future__ import annotations

import argparse
import sys

from ._base import DatasetError, DatasetUnavailable, SchemaDrift
from .client import OUTPUT_COLUMNS, SlaveVoyagesClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="slavevoyages")
    sub = parser.add_subparsers(dest="cmd", required=True)

    for name, helptxt in (("voyages", "filter individual voyages"),
                          ("summary", "aggregate volume + date window for a route")):
        sp = sub.add_parser(name, help=helptxt)
        sp.add_argument("--embark", default=None, help="embarkation region or port")
        sp.add_argument("--disembark", default=None, help="disembarkation region or port")
        sp.add_argument("--period", nargs=2, type=float, metavar=("LO", "HI"), default=None,
                        help="year-of-arrival window")
        if name == "voyages":
            sp.add_argument("--tsv", action="store_true",
                            help="write voyages as TSV to stdout (default: count)")

    sub.add_parser("inspect", help="print the raw column header of the resolved file")
    sub.add_parser("info", help="print resolved version + source provenance")

    args = parser.parse_args(argv)
    client = SlaveVoyagesClient()

    try:
        if args.cmd in ("voyages", "summary"):
            period = (args.period[0], args.period[1]) if args.period else None
            if args.cmd == "voyages":
                rows = client.voyages(embark=args.embark, disembark=args.disembark, period=period)
                if args.tsv:
                    client.write_tsv(rows, OUTPUT_COLUMNS, sys.stdout)
                else:
                    print(f"{len(rows)} voyages (source={client.last_source})")
            else:
                s = client.route_summary(embark=args.embark, disembark=args.disembark, period=period)
                span = (f"{s['year_min']:.0f}-{s['year_max']:.0f}"
                        if s["year_min"] is not None else "n/a")
                print(f"{s['voyages']} voyages, {s['embarked']:.0f} embarked / "
                      f"{s['disembarked']:.0f} disembarked, {span} "
                      f"(source={client.last_source})")
            return 0

        if args.cmd == "inspect":
            header = client.header_of()
            print(f"# source={client.last_source} version={client.version} ncols={len(header)}")
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
        print(f"slavevoyages unavailable:\n{e}", file=sys.stderr)
        return 3
    except SchemaDrift as e:
        print(f"slavevoyages schema drift: {e}", file=sys.stderr)
        return 2
    except DatasetError as e:
        print(f"slavevoyages error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
