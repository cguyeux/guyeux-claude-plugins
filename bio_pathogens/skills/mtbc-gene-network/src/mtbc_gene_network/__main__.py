"""Shell CLI for the mtbc-gene-network skill (local interactome graph operations).

    python3 -m mtbc_gene_network --min-score 700 neighbors katG --top 10
    python3 -m mtbc_gene_network path katG rpoB
    python3 -m mtbc_gene_network subnetwork katG,ahpC,furA
    python3 -m mtbc_gene_network hubs --top 15 [--metric betweenness]
    python3 -m mtbc_gene_network --min-score 700 communities --top 10
    python3 -m mtbc_gene_network guilt Rv2239c          # guilt-by-association for a dark gene
    python3 -m mtbc_gene_network info

Reads annotation_mtbc/phase2h_string (set MTBC_ANNOTATION_DIR to relocate). Exit
codes: 0 ok, 3 network/dependency unavailable.
"""
from __future__ import annotations

import argparse
import json
import sys

from .graph import DEFAULT_MIN_SCORE, GeneNetwork, GeneNetworkUnavailable


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="mtbc-gene-network")
    p.add_argument("--min-score", type=int, default=DEFAULT_MIN_SCORE,
                   help="STRING combined-score threshold (400 medium, 700 high)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sn = sub.add_parser("neighbors", help="interaction partners of a gene")
    sn.add_argument("gene")
    sn.add_argument("--top", type=int, default=None)

    sp = sub.add_parser("path", help="shortest path between two genes")
    sp.add_argument("a")
    sp.add_argument("b")
    sp.add_argument("--weighted", action="store_true", help="minimise summed 1-confidence")

    ss = sub.add_parser("subnetwork", help="induced subnetwork over a comma-separated gene set")
    ss.add_argument("genes")

    sh = sub.add_parser("hubs", help="most connected / central genes")
    sh.add_argument("--top", type=int, default=20)
    sh.add_argument("--metric", choices=["degree", "betweenness"], default="degree")

    sc = sub.add_parser("communities", help="functional modules (greedy modularity)")
    sc.add_argument("--top", type=int, default=15)

    sg = sub.add_parser("guilt", help="guilt-by-association function for a (dark) gene")
    sg.add_argument("gene")
    sg.add_argument("--top", type=int, default=10)

    sub.add_parser("info", help="network size + provenance")

    args = p.parse_args(argv)
    net = GeneNetwork(min_score=args.min_score)

    def out(obj):
        print(json.dumps(obj, indent=2, ensure_ascii=False))

    try:
        if args.cmd == "neighbors":
            out(net.neighbors(args.gene, top=args.top))
        elif args.cmd == "path":
            out(net.shortest_path(args.a, args.b, weighted=args.weighted))
        elif args.cmd == "subnetwork":
            out(net.subnetwork([g.strip() for g in args.genes.split(",") if g.strip()]))
        elif args.cmd == "hubs":
            out(net.hubs(top=args.top, metric=args.metric))
        elif args.cmd == "communities":
            out(net.communities(top=args.top))
        elif args.cmd == "guilt":
            out(net.guilt_by_association(args.gene, top=args.top))
        elif args.cmd == "info":
            g = net.graph()
            print(f"nodes = {g.number_of_nodes()}\nedges = {g.number_of_edges()}\n"
                  f"min_score = {net.min_score}\nsource = {net._string_path()}")
        return 0
    except GeneNetworkUnavailable as e:
        print(f"gene-network unavailable: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
