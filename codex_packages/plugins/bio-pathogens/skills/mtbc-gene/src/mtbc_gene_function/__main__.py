"""CLI: mtbc-gene-function <gene_or_locus> [--paragraph] [--json]"""
from __future__ import annotations

import argparse
import json
import sys

from .core import GeneNotFound, annotate_gene


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="mtbc-gene-function")
    p.add_argument("gene_or_locus")
    p.add_argument("--paragraph", action="store_true",
                   help="Print a Markdown-friendly prose block after the JSON.")
    p.add_argument("--json", action="store_true",
                   help="Suppress everything except the JSON payload.")
    p.add_argument("--no-esm", action="store_true",
                   help="Curated annotation_mtbc only; skip the ESM Atlas enrichment (offline).")
    args = p.parse_args(argv)

    try:
        ann = annotate_gene(args.gene_or_locus, use_esm=not args.no_esm)
    except GeneNotFound as e:
        print(f"{e}", file=sys.stderr)
        return 1

    payload = ann.to_dict()
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if args.paragraph and not args.json:
        print()
        print(ann.function_summary)
    # success when a curated or ESM annotation was produced
    return 0 if (ann.local_available or ann.esm_available or ann.product) else 1


if __name__ == "__main__":
    sys.exit(main())
