"""Shell CLI for the orbis skill.

    python -m orbis_client route --from carthago --to roma --weight days
    python -m orbis_client nearest --lat 41.9 --lon 12.5
    python -m orbis_client matrix --sites roma,carthago,alexandria --weight days --tsv
    python -m orbis_client inspect      # print the raw headers of the node & edge files
    python -m orbis_client info         # show resolved provenance

Weights: days | cost | distance. Exit codes: 0 ok, 1 error, 2 schema drift, 3 unavailable.
"""
from __future__ import annotations

import argparse
import math
import sys

from ._base import DatasetError, DatasetUnavailable, SchemaDrift
from .client import OrbisClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="orbis")
    sub = parser.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("route", help="cheapest path between two sites")
    r.add_argument("--from", dest="src", required=True, help="origin node id")
    r.add_argument("--to", dest="dst", required=True, help="destination node id")
    r.add_argument("--weight", default="days", choices=["days", "cost", "distance"])
    r.add_argument("--directed", action="store_true", help="respect edge direction")

    n = sub.add_parser("nearest", help="snap a coordinate to the nearest ORBIS site")
    n.add_argument("--lat", type=float, required=True)
    n.add_argument("--lon", type=float, required=True)

    m = sub.add_parser("matrix", help="pairwise travel-cost distance matrix (for Mantel)")
    m.add_argument("--sites", default=None,
                   help="comma-separated node ids (default: all sites)")
    m.add_argument("--weight", default="days", choices=["days", "cost", "distance"])
    m.add_argument("--directed", action="store_true")
    m.add_argument("--tsv", action="store_true", help="write the matrix as TSV to stdout")

    sub.add_parser("inspect", help="print the raw headers of the resolved node & edge files")
    sub.add_parser("info", help="print resolved version + source provenance")

    args = parser.parse_args(argv)
    orb = OrbisClient()

    try:
        if args.cmd == "route":
            path, cost = orb.route(args.src, args.dst, weight=args.weight,
                                   directed=args.directed)
            if not path:
                print(f"no route from {args.src} to {args.dst}", file=sys.stderr)
                return 1
            print(" -> ".join(orb.label(n) for n in path))
            unit = {"days": "days", "cost": "denarii/kg", "distance": "km"}[args.weight]
            print(f"total: {cost:g} {unit}  (source={orb.last_source})")
            return 0

        if args.cmd == "nearest":
            site, km = orb.nearest(args.lat, args.lon)
            if site is None:
                print("no sites with coordinates", file=sys.stderr)
                return 1
            print(f"{site.get('label') or site.get('id')} ({site.get('id')})  {km:.1f} km")
            return 0

        if args.cmd == "matrix":
            ids = args.sites.split(",") if args.sites else None
            keep, mat = orb.distance_matrix(ids, weight=args.weight, directed=args.directed)
            if args.tsv:
                orb.matrix_tsv(keep, mat, sys.stdout)
            else:
                reach = sum(1 for v in mat.values() if not math.isinf(v))
                print(f"{len(keep)} sites, {reach}/{len(keep) ** 2} reachable pairs "
                      f"(weight={args.weight}, source={orb.last_source})")
            return 0

        if args.cmd == "inspect":
            for name, reader in (("nodes", orb.nodes_reader), ("edges", orb.edges_reader)):
                header = reader.header_of()
                print(f"# {name}: source={reader.last_source} ncols={len(header)}")
                print("  " + ", ".join(header))
            return 0

        if args.cmd == "info":
            np = orb.nodes_reader.resolve_dataset(allow_download=False)
            ep = orb.edges_reader.resolve_dataset(allow_download=False)
            print(f"version = {orb.version}")
            print(f"nodes   = {orb.nodes_reader.last_source}  {np}")
            print(f"edges   = {orb.edges_reader.last_source}  {ep}")
            return 0

    except DatasetUnavailable as e:
        print(f"orbis unavailable:\n{e}", file=sys.stderr)
        return 3
    except SchemaDrift as e:
        print(f"orbis schema drift: {e}", file=sys.stderr)
        return 2
    except (DatasetError, ValueError) as e:
        print(f"orbis error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
