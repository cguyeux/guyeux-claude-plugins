"""Local-first MTBC gene interaction network from annotation_mtbc/phase2h_string.

annotation_mtbc has already computed the WHOLE-proteome STRING network once
(résultats/phase2h_string/string.json: ~3900 genes, ~10^5 undirected edges, each
edge carrying the combined score and the per-channel evidence). This module loads it
as a networkx graph and exposes the graph operations that annotation_mtbc does NOT do
(neighbourhood, induced subnetwork, shortest path, hubs, communities/modules, and
guilt-by-association for a dark gene). The STRING API (`string-db` skill) is only the
fallback for a gene absent from the local interactome.

networkx is a guarded import; the loader degrades to a clear message if absent.
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path

ANNOTATION_DIR = Path(
    os.environ.get("MTBC_ANNOTATION_DIR", "~/docs/codes/mtbc/annotation_mtbc")
).expanduser()
DEFAULT_MIN_SCORE = 400      # STRING "medium" confidence
HIGH_MIN_SCORE = 700         # STRING "high" confidence


class GeneNetworkUnavailable(Exception):
    """Raised when phase2h_string / networkx is not available."""


def _networkx():
    try:
        import networkx as nx
        return nx
    except Exception as exc:  # pragma: no cover - import guard
        raise GeneNetworkUnavailable(
            "mtbc-gene-network needs networkx (pip install networkx; present on the "
            f"system Python). ({exc})"
        ) from exc


class GeneNetwork:
    def __init__(self, root: Path | None = None, min_score: int = DEFAULT_MIN_SCORE):
        self.root = Path(root or ANNOTATION_DIR)
        self.min_score = int(min_score)
        self._g = None
        self._g_min: int | None = None
        self._name_to_rv: dict[str, str] = {}
        self._rv_to_name: dict[str, str] = {}
        self._product: dict[str, str] = {}
        self._hyp: dict[str, bool] = {}
        self._xref_loaded = False

    # ── resolution / availability ────────────────────────────────────────────

    def _string_path(self) -> Path:
        return self.root / "résultats" / "phase2h_string" / "string.json"

    def available(self) -> bool:
        return self._string_path().exists()

    def _load_xref(self) -> None:
        if self._xref_loaded:
            return
        self._xref_loaded = True
        p = self.root / "data" / "gene_xref_all.tsv"
        if not p.exists():
            return
        with p.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                rv = (row.get("rv") or "").strip()
                if not rv:
                    continue
                gene = (row.get("gene") or "").strip()
                if gene:
                    self._name_to_rv.setdefault(gene.lower(), rv)
                    self._rv_to_name.setdefault(rv, gene)
                prod = (row.get("product_h37rv") or "").strip()
                if prod:
                    self._product[rv] = prod
                hyp = (row.get("is_hypothetical_h37rv") or "").strip().lower()
                if hyp:
                    self._hyp[rv] = hyp in {"1", "true", "yes", "y"}

    def resolve(self, query: str) -> str | None:
        """Gene name or Rv locus tag -> Rv id (uses the network nodes + the xref)."""
        self._load_xref()
        q = query.strip()
        g = self.graph()
        if q in g:
            return q
        ql = q.lower()
        if ql in self._name_to_rv:
            return self._name_to_rv[ql]
        # node-attribute gene names (covers genes named only inside string.json)
        for n, data in g.nodes(data=True):
            if (data.get("gene") or "").lower() == ql or n.lower() == ql:
                return n
        return None

    def label(self, rv: str) -> str:
        g = self.graph()
        return (g.nodes[rv].get("gene") if rv in g else None) or rv

    # ── graph build (cached) ─────────────────────────────────────────────────

    def graph(self, min_score: int | None = None):
        ms = self.min_score if min_score is None else int(min_score)
        if self._g is not None and self._g_min == ms:
            return self._g
        if not self.available():
            raise GeneNetworkUnavailable(
                f"phase2h_string not found under {self.root} "
                "(set MTBC_ANNOTATION_DIR to the annotation_mtbc path)."
            )
        nx = _networkx()
        self._load_xref()
        data = json.loads(self._string_path().read_text(encoding="utf-8"))
        g = nx.Graph()
        for rv, entry in data.items():
            g.add_node(rv)
            for p in entry.get("partners", []):
                prv = p.get("rv")
                score = p.get("combined")
                if not prv or score is None or score < ms:
                    continue
                g.add_node(prv)
                # partner gene/product names (handy for nodes absent from the xref)
                if p.get("gene"):
                    g.nodes[prv].setdefault("gene", p["gene"])
                if p.get("product"):
                    g.nodes[prv].setdefault("product", p["product"])
                if p.get("hypothetical") is not None:
                    g.nodes[prv].setdefault("hypothetical", bool(p["hypothetical"]))
                if g.has_edge(rv, prv) and g[rv][prv]["weight"] >= score:
                    continue
                g.add_edge(rv, prv, weight=int(score), dist=1000 - int(score),
                           context=bool(p.get("context_driven")))
        # enrich node attributes from the xref (single O(n) pass)
        for rv in g.nodes:
            nd = g.nodes[rv]
            if rv in self._product:
                nd.setdefault("product", self._product[rv])
            if rv in self._hyp:
                nd.setdefault("hypothetical", self._hyp[rv])
            if rv in self._rv_to_name and "gene" not in nd:
                nd["gene"] = self._rv_to_name[rv]
        self._g, self._g_min = g, ms
        return g

    # ── operations ───────────────────────────────────────────────────────────

    def _rv(self, query: str) -> str:
        rv = self.resolve(query)
        if rv is None:
            raise GeneNetworkUnavailable(
                f"{query!r} is not in the local interactome (set min-score lower, or "
                "use the `string-db` skill for an API lookup)."
            )
        return rv

    def neighbors(self, gene: str, *, min_score: int | None = None, top: int | None = None) -> list[dict]:
        g = self.graph(min_score)
        rv = self._rv(gene)
        out = [{"rv": n, "gene": g.nodes[n].get("gene"), "product": g.nodes[n].get("product"),
                "hypothetical": g.nodes[n].get("hypothetical"), "score": g[rv][n]["weight"]}
               for n in g.neighbors(rv)]
        out.sort(key=lambda d: d["score"], reverse=True)
        return out[:top] if top else out

    def subnetwork(self, genes: list[str], *, min_score: int | None = None) -> dict:
        g = self.graph(min_score)
        rvs = [self._rv(x) for x in genes]
        sub = g.subgraph(rvs)
        edges = [{"a": self.label(u), "b": self.label(v), "score": d["weight"]}
                 for u, v, d in sub.edges(data=True)]
        return {"n_nodes": sub.number_of_nodes(), "n_edges": sub.number_of_edges(), "edges": edges}

    def shortest_path(self, a: str, b: str, *, min_score: int | None = None, weighted: bool = False) -> dict:
        nx = _networkx()
        g = self.graph(min_score)
        ra, rb = self._rv(a), self._rv(b)
        try:
            path = nx.shortest_path(g, ra, rb, weight="dist" if weighted else None)
        except nx.NetworkXNoPath:
            return {"path": [], "hops": None, "connected": False}
        edge_scores = [g[path[i]][path[i + 1]]["weight"] for i in range(len(path) - 1)]
        return {"path": [self.label(n) for n in path], "rv_path": path,
                "hops": len(path) - 1, "min_edge_score": min(edge_scores) if edge_scores else None,
                "connected": True}

    def hubs(self, *, top: int = 20, metric: str = "degree", min_score: int | None = None,
             k: int = 400) -> list[dict]:
        nx = _networkx()
        g = self.graph(min_score)
        if metric == "betweenness":
            cent = nx.betweenness_centrality(g, k=min(k, g.number_of_nodes()), weight="dist", seed=0)
            ranked = sorted(cent, key=lambda n: cent[n], reverse=True)
            return [{"rv": n, "gene": g.nodes[n].get("gene"), "betweenness": round(cent[n], 5),
                     "degree": g.degree(n)} for n in ranked[:top]]
        ranked = sorted(g.degree, key=lambda kv: kv[1], reverse=True)
        return [{"rv": n, "gene": g.nodes[n].get("gene"), "degree": d} for n, d in ranked[:top]]

    def communities(self, *, top: int = 15, min_score: int | None = None) -> list[dict]:
        from networkx.algorithms.community import greedy_modularity_communities
        g = self.graph(min_score)
        comms = greedy_modularity_communities(g, weight="weight")
        comms = sorted(comms, key=len, reverse=True)[:top]
        return [{"size": len(c), "members": [self.label(n) for n in list(c)[:25]]} for c in comms]

    def guilt_by_association(self, gene: str, *, min_score: int = HIGH_MIN_SCORE,
                             top: int = 10) -> dict:
        """Infer a (dark) gene's role from its high-confidence neighbours' functions."""
        rv = self._rv(gene)
        nbrs = self.neighbors(gene, min_score=min_score, top=top)
        try:
            from mtbc_gene_function.core import annotate_gene  # lazy: needs that skill on PYTHONPATH
            for nb in nbrs:
                try:
                    ann = annotate_gene(nb["rv"], use_esm=False)
                    nb["function"] = (ann.uniprot_function or ann.product or "")[:140]
                except Exception:
                    nb["function"] = nb.get("product")
        except Exception:
            for nb in nbrs:
                nb["function"] = nb.get("product")
        g = self.graph()
        return {"gene": self.label(rv), "rv": rv,
                "hypothetical": g.nodes[rv].get("hypothetical"),
                "n_high_conf_partners": len(nbrs), "partners": nbrs}

    def string_fallback(self, query: str) -> list | None:
        """Best-effort STRING-API partners for a gene absent locally (string-db skill)."""
        try:
            from string_db import partners
            return partners([query])
        except Exception:
            return None
