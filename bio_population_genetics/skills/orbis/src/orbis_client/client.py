"""ORBIS client: the Roman-world transport network as travel-cost distances.

Tool-first entry point for the orbis skill. Composes two resilient gabarit
readers (nodes + edges) and adds a stdlib graph layer (Dijkstra via heapq, no
networkx dependency) to answer the questions ORBIS is actually used for:

    from orbis_client import OrbisClient
    orb = OrbisClient()
    ids, mat = orb.distance_matrix(["roma", "carthago", "alexandria"], weight="days")
    path, cost = orb.route("carthago", "roma", weight="days")
    node, km = orb.nearest(41.9, 12.5)          # snap a TB sampling coordinate

The distance matrix is the bridge to `coevolution`: feed it (ORBIS cost/time
distance) and a phylogenetic distance matrix to a Mantel test to ask whether an
L4 sublineage's structure tracks Roman transport cost better than great-circle
distance. Stable, stdlib-only, offline-capable; reads .csv or .xlsx.
"""
from __future__ import annotations

import csv
import heapq
import math
import os
from pathlib import Path

from ._base import DatasetError, FileDatasetClient
from .schema import EDGES_SCHEMA, NODES_SCHEMA
from .sources import DEFAULT_VERSION, EDGE_SNAPSHOTS, NODE_SNAPSHOTS

# stable weight name -> stable edge column produced by EDGES_SCHEMA
WEIGHTS = {"days": "days", "cost": "cost", "distance": "distance_km"}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p = math.pi / 180.0
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


class OrbisClient:
    """Two-table (nodes + edges) ORBIS reader with a stdlib graph layer."""

    def __init__(self, *, offline: bool | None = None, version: str | None = None):
        env_off = os.environ.get("ORBIS_OFFLINE")
        off = (env_off == "1") if env_off is not None else offline
        fx = Path(__file__).resolve().parents[2] / "fixtures"
        common = dict(default_version=DEFAULT_VERSION, delimiter=",",
                      quoting=csv.QUOTE_MINIMAL, offline=off, version=version)
        self.nodes_reader = FileDatasetClient(
            slug="orbis_nodes", snapshots=NODE_SNAPSHOTS, schema=NODES_SCHEMA,
            fixture=fx / "orbis_nodes_sample.csv", **common)
        self.edges_reader = FileDatasetClient(
            slug="orbis_edges", snapshots=EDGE_SNAPSHOTS, schema=EDGES_SCHEMA,
            fixture=fx / "orbis_edges_sample.csv", **common)
        self.version = self.nodes_reader.version
        self._sites: list[dict] | None = None
        self._edges: list[dict] | None = None
        self._by_id: dict[str, dict] = {}

    # ── data access ──────────────────────────────────────────────────────────

    def sites(self, *, allow_download: bool = True) -> list[dict]:
        if self._sites is None:
            rows = self.nodes_reader.read_rows(
                allow_download=allow_download, required=["id", "label", "lat", "lon"])
            self._sites = rows
            self._by_id = {s["id"]: s for s in rows}
        assert self._sites is not None
        return self._sites

    def edges(self, *, allow_download: bool = True) -> list[dict]:
        if self._edges is None:
            self._edges = self.edges_reader.read_rows(
                allow_download=allow_download, required=["source", "target"])
        assert self._edges is not None
        return self._edges

    @property
    def last_source(self) -> str:
        return f"nodes={self.nodes_reader.last_source},edges={self.edges_reader.last_source}"

    def label(self, node_id: str) -> str:
        s = self._by_id.get(node_id)
        return (s.get("label") if s else None) or node_id

    # ── graph layer (stdlib Dijkstra) ────────────────────────────────────────

    def _graph(self, weight: str, *, directed: bool) -> dict[str, list[tuple[str, float]]]:
        if weight not in WEIGHTS:
            raise ValueError(f"weight must be one of {sorted(WEIGHTS)}")
        wkey = WEIGHTS[weight]
        adj: dict[str, list[tuple[str, float]]] = {}
        for e in self.edges():
            s, t = e.get("source"), e.get("target")
            w = FileDatasetClient.as_float(e.get(wkey))
            if not s or not t or w is None:
                continue
            adj.setdefault(s, []).append((t, w))
            if not directed:
                adj.setdefault(t, []).append((s, w))
        return adj

    def shortest_costs(self, source: str, *, weight: str = "days",
                       directed: bool = False) -> dict[str, float]:
        """Dijkstra single-source shortest costs from ``source`` to all reachable nodes."""
        self.sites()
        adj = self._graph(weight, directed=directed)
        dist: dict[str, float] = {source: 0.0}
        pq: list[tuple[float, str]] = [(0.0, source)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist.get(u, math.inf):
                continue
            for v, w in adj.get(u, ()):
                nd = d + w
                if nd < dist.get(v, math.inf):
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
        return dist

    def route(self, source: str, target: str, *, weight: str = "days",
              directed: bool = False) -> tuple[list[str], float]:
        """Return (path of node ids, total cost) of the cheapest route, or ([], inf)."""
        self.sites()
        adj = self._graph(weight, directed=directed)
        dist: dict[str, float] = {source: 0.0}
        prev: dict[str, str] = {}
        pq: list[tuple[float, str]] = [(0.0, source)]
        while pq:
            d, u = heapq.heappop(pq)
            if u == target:
                break
            if d > dist.get(u, math.inf):
                continue
            for v, w in adj.get(u, ()):
                nd = d + w
                if nd < dist.get(v, math.inf):
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))
        if target not in dist:
            return [], math.inf
        path = [target]
        while path[-1] != source:
            path.append(prev[path[-1]])
        path.reverse()
        return path, dist[target]

    def distance_matrix(self, site_ids: list[str] | None = None, *,
                        weight: str = "days", directed: bool = False,
                        symmetric: bool = True) -> tuple[list[str], dict[tuple[str, str], float]]:
        """Pairwise shortest-cost matrix among ``site_ids`` (default: all sites).

        Returns ``(ids, matrix)`` where ``matrix[(a, b)]`` is the travel cost.
        With ``symmetric=True`` on a directed graph, ``(d_ab + d_ba) / 2`` is used
        (or ``min`` if one direction is unreachable) so the result is a valid
        symmetric distance matrix for a Mantel test.
        """
        self.sites()
        if site_ids is None:
            ids = [s["id"] for s in (self._sites or [])]
        else:
            ids = [i for i in site_ids if i in self._by_id]
        mat: dict[tuple[str, str], float] = {}
        for a in ids:
            da = self.shortest_costs(a, weight=weight, directed=directed)
            for b in ids:
                mat[(a, b)] = 0.0 if a == b else da.get(b, math.inf)
        if symmetric and directed:
            for i, a in enumerate(ids):
                for b in ids[i + 1:]:
                    x, y = mat[(a, b)], mat[(b, a)]
                    m = min(x, y) if (math.isinf(x) or math.isinf(y)) else (x + y) / 2
                    mat[(a, b)] = mat[(b, a)] = m
        return ids, mat

    def nearest(self, lat: float, lon: float, *,
                allow_download: bool = True) -> tuple[dict | None, float]:
        """Snap a coordinate to the nearest ORBIS site (great-circle km)."""
        best: dict | None = None
        best_km = math.inf
        for s in self.sites(allow_download=allow_download):
            slat = FileDatasetClient.as_float(s.get("lat"))
            slon = FileDatasetClient.as_float(s.get("lon"))
            if slat is None or slon is None:
                continue
            km = haversine_km(lat, lon, slat, slon)
            if km < best_km:
                best_km, best = km, s
        return best, best_km

    # ── output ───────────────────────────────────────────────────────────────

    def matrix_tsv(self, ids: list[str], mat: dict[tuple[str, str], float], out,
                   *, use_labels: bool = True) -> None:
        """Write a square distance matrix as TSV (consumable by coevolution Mantel)."""
        close = isinstance(out, (str, Path))
        fh = open(out, "w", encoding="utf-8", newline="") if close else out
        try:
            w = csv.writer(fh, delimiter="\t", lineterminator="\n")
            head = [self.label(i) if use_labels else i for i in ids]
            w.writerow(["site"] + head)
            for a in ids:
                row = [self.label(a) if use_labels else a]
                for b in ids:
                    v = mat.get((a, b), math.inf)
                    row.append("inf" if math.isinf(v) else f"{v:g}")
                w.writerow(row)
        finally:
            if close:
                fh.close()


__all__ = ["OrbisClient", "haversine_km", "DatasetError"]
