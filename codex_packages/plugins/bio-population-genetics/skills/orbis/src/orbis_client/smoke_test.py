"""Offline smoke test for the orbis skill.

Runs entirely on the bundled fixtures (``fixtures/orbis_nodes_sample.csv`` +
``orbis_edges_sample.csv``) in offline mode: no network, no ORBIS download.
Validates the graph layer end to end:
  1. both tables resolve (here: to the fixtures),
  2. Dijkstra route + cost are correct on the known fixture network,
  3. the distance matrix is symmetric and finite, and `nearest` snaps a coordinate.

    python -m orbis_client.smoke_test
"""
from __future__ import annotations

import math
import sys

from ._base import DatasetError
from .client import OrbisClient


def main() -> int:
    orb = OrbisClient(offline=True)  # force fixtures
    try:
        sites = orb.sites(allow_download=False)
        n_edges = len(orb.edges(allow_download=False))
        print(f"resolved {orb.last_source}; {len(sites)} sites, {n_edges} edges")
        if "fixture" not in orb.nodes_reader.last_source:
            print(f"FAIL: expected fixture nodes, got {orb.nodes_reader.last_source}",
                  file=sys.stderr)
            return 2

        # Dijkstra: Roma -> Mediolanum is the 12-day direct road, not via Ravenna (14).
        path, cost = orb.route("roma", "mediolanum", weight="days")
        print(f"route roma->mediolanum: {' -> '.join(orb.label(n) for n in path)} = {cost:g} d")
        if path != ["roma", "mediolanum"] or cost != 12.0:
            print(f"FAIL: expected [roma, mediolanum] = 12, got {path} = {cost}",
                  file=sys.stderr)
            return 2

        # Distance matrix: Roma -> Carthago via Ostia = 1 + 4 = 5 days.
        _, mat = orb.distance_matrix(["roma", "carthago"], weight="days")
        rc = mat[("roma", "carthago")]
        print(f"matrix roma<->carthago = {rc:g} d (symmetric={mat[('carthago','roma')]:g})")
        if rc != 5.0 or mat[("carthago", "roma")] != 5.0:
            print(f"FAIL: expected 5 days roma<->carthago, got {rc}", file=sys.stderr)
            return 2

        # Pelusium (Justinian-plague origin) reachable from Roma.
        if math.isinf(orb.shortest_costs("roma", weight="days").get("pelusium", math.inf)):
            print("FAIL: pelusium unreachable from roma", file=sys.stderr)
            return 2

        # Snap a coordinate near Rome.
        site, km = orb.nearest(41.9, 12.5)
        print(f"nearest to (41.9, 12.5) = {site and site.get('label')} ({km:.1f} km)")
        if not site or site.get("id") != "roma":
            print(f"FAIL: expected roma nearest, got {site}", file=sys.stderr)
            return 2
    except DatasetError as e:
        print(f"FAIL (dataset): {e}", file=sys.stderr)
        return 3

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
