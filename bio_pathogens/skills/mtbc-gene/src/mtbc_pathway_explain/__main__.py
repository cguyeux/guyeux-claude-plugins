"""CLI: narrate a pathway, gene set, neighbourhood -- or a lineage's selection signal.

    mtbc-pathway-explain ESX-2 --paragraph                 # a catalogue pathway
    mtbc-pathway-explain neighbors:katG --paragraph        # a gene's interaction neighbourhood
    mtbc-pathway-explain katG,ahpC,furA,sodA,sodC          # an explicit gene set / subnetwork
    mtbc-pathway-explain ESX-2 --esm                       # add the optional ESM enrichment
    mtbc-pathway-explain --from-selection dnds.tsv --lineage L4.13 --paragraph
                                                           # selection signal -> affected pathways

`target` is a catalogue pathway id, `neighbors:GENE`, or a comma-separated gene list.
`--from-selection TABLE` reads a lineage's per-gene/per-variant selection table and
narrates the affected pathways (it does NOT recompute the test; that is mk-ascertainment).
Curated-first (annotation_mtbc via mtbc-gene-function) + PPI context (mtbc-gene-network).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import (PathwayNotFound, SelectionInputError, explain_gene_set,
                   explain_pathway, from_selection, genes_from_network)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="mtbc-pathway-explain")
    p.add_argument("target", nargs="?",
                   help="catalogue pathway id | neighbors:GENE | gene1,gene2,...")
    p.add_argument("--from-selection", type=Path, default=None, metavar="TABLE",
                   help="a lineage's per-gene/per-variant selection table -> affected pathways")
    p.add_argument("--lineage", default=None, help="lineage label for the selection narration")
    p.add_argument("--catalogue", type=Path, default=None,
                   help="Extra YAML catalogue to merge on top of the bundled one.")
    p.add_argument("--esm", action="store_true", help="add the optional ESM Atlas enrichment")
    p.add_argument("--no-network", action="store_true", help="skip the PPI network context")
    p.add_argument("--min-score", type=int, default=400, help="STRING confidence for the network")
    p.add_argument("--paragraph", action="store_true")
    # --from-selection tuning (drift-tolerant; auto-detected if omitted)
    p.add_argument("--gene-col", default=None, help="override the gene/locus column")
    p.add_argument("--stat-col", default=None, help="override the dN/dS-style statistic column")
    p.add_argument("--p-col", default=None, help="override the p-value column")
    p.add_argument("--min-stat", type=float, default=1.0, help="keep genes with stat > this")
    p.add_argument("--max-p", type=float, default=0.05, help="keep genes with p < this")
    p.add_argument("--min-variants", type=int, default=1,
                   help="variant-level mode: min non-synonymous variants per gene")
    p.add_argument("--alpha-min", type=float, default=0.0,
                   help="MK mode: min adaptive direction (alpha / DoS) to call positive selection")
    p.add_argument("--no-fdr", action="store_true",
                   help="MK mode: gate on raw p instead of BH-FDR-corrected q")
    p.add_argument("--top", type=int, default=5, help="narrate the top-N affected pathways in full")
    args = p.parse_args(argv)
    with_net = not args.no_network

    if args.from_selection is not None:
        try:
            rep = from_selection(
                args.from_selection, lineage=args.lineage, catalogue_path=args.catalogue,
                use_esm=args.esm, with_network=with_net, min_score=args.min_score,
                top=args.top, gene_col=args.gene_col, stat_col=args.stat_col,
                p_col=args.p_col, min_stat=args.min_stat, max_p=args.max_p,
                min_variants=args.min_variants, alpha_min=args.alpha_min,
                fdr=not args.no_fdr)
        except SelectionInputError as e:
            print(f"{e}", file=sys.stderr)
            return 2
        print(json.dumps(rep.to_dict(), indent=2, ensure_ascii=False))
        if args.paragraph:
            print()
            print(rep.paragraph)
        return 0

    if not args.target:
        p.error("provide a pathway / neighbors:GENE / gene list, or --from-selection TABLE")

    try:
        if args.target.startswith(("neighbors:", "neighbours:")) or "," in args.target:
            genes, label = genes_from_network(args.target, min_score=args.min_score)
            rep = explain_gene_set(genes, name=label, use_esm=args.esm,
                                   with_network=with_net, min_score=args.min_score)
        else:
            rep = explain_pathway(args.target, catalogue_path=args.catalogue,
                                  use_esm=args.esm, with_network=with_net, min_score=args.min_score)
    except PathwayNotFound as e:
        print(f"{e}\n(hint: try `neighbors:{args.target}` for its network neighbourhood, "
              "or a comma-separated gene list)", file=sys.stderr)
        return 1

    print(json.dumps(rep.to_dict(), indent=2, ensure_ascii=False))
    if args.paragraph:
        print()
        print(rep.paragraph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
