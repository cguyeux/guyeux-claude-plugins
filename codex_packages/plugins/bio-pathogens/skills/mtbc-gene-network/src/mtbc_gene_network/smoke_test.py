"""Offline smoke test for mtbc-gene-network (needs networkx; no network, no real data).

Builds a tiny interactome with a KNOWN topology in a temp dir -- a hub Rv0010 wired to
Rv0001..Rv0005, plus a 4-edge chain Rv0001-..-Rv0005 -- and checks the graph operations
against that ground truth.

    python3 -m mtbc_gene_network.smoke_test
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

from mtbc_gene_network.graph import GeneNetwork


def _build_fixture(root: str) -> None:
    sdir = os.path.join(root, "résultats", "phase2h_string")
    ddir = os.path.join(root, "data")
    os.makedirs(sdir)
    os.makedirs(ddir)

    def partner(rv: str, score: int) -> dict:
        return {"rv": rv, "gene": "", "product": "p", "hypothetical": False,
                "combined": score, "channels": {}}

    string_json = {
        "Rv0010": {"string_id": "x", "n_partners": 5,
                   "partners": [partner(f"Rv000{i}", 900) for i in range(1, 6)]},
        "Rv0001": {"partners": [partner("Rv0002", 800)]},
        "Rv0002": {"partners": [partner("Rv0003", 800)]},
        "Rv0003": {"partners": [partner("Rv0004", 800)]},
        "Rv0004": {"partners": [partner("Rv0005", 800)]},
    }
    with open(os.path.join(sdir, "string.json"), "w") as f:
        json.dump(string_json, f)
    names = {"Rv0010": "hubGene", "Rv0001": "geneA", "Rv0002": "geneB",
             "Rv0003": "geneC", "Rv0004": "geneD", "Rv0005": "geneE"}
    with open(os.path.join(ddir, "gene_xref_all.tsv"), "w") as f:
        f.write("rv\tgene\tproduct_h37rv\tis_hypothetical_h37rv\tlen_aa\n")
        for rv, g in names.items():
            f.write(f"{rv}\t{g}\tproduct\tfalse\t100\n")


def main() -> int:
    root = tempfile.mkdtemp(prefix="genenet_smoke_")
    _build_fixture(root)
    net = GeneNetwork(root=root, min_score=400)
    g = net.graph()
    print(f"graph: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges")

    nb = net.neighbors("hubGene")
    if len(nb) != 5:
        print(f"FAIL: hubGene should have 5 neighbours, got {len(nb)}", file=sys.stderr)
        return 2

    h = net.hubs(top=1)
    if not h or h[0]["rv"] != "Rv0010":
        print(f"FAIL: top degree hub should be Rv0010, got {h}", file=sys.stderr)
        return 2

    sp = net.shortest_path("geneA", "geneE")
    print(f"path geneA->geneE: {sp['path']} ({sp['hops']} hops)")
    if sp["hops"] != 2 or "hubGene" not in sp["path"]:
        print(f"FAIL: geneA->geneE should be 2 hops via hubGene, got {sp}", file=sys.stderr)
        return 2

    cm = net.communities(top=5)
    snet = net.subnetwork(["geneA", "geneB", "hubGene"])
    print(f"communities={len(cm)}; subnetwork(3 genes)={snet['n_nodes']} nodes, {snet['n_edges']} edges")
    if not cm or snet["n_nodes"] != 3:
        print(f"FAIL: communities/subnetwork sanity (cm={len(cm)}, sub={snet})", file=sys.stderr)
        return 2

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
