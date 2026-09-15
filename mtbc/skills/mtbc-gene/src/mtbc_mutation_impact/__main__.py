"""CLI: mtbc-mutation-impact <gene_or_locus> <mutation> [--max-labels N]"""
from __future__ import annotations

import argparse
import json
import sys

from .core import MutationError, impact_of


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="mtbc-mutation-impact")
    p.add_argument("gene_or_locus")
    p.add_argument("mutation", help="e.g. S315T")
    p.add_argument("--max-labels", type=int, default=5,
                   help="Number of features to hydrate with a label in each bucket.")
    p.add_argument("--paragraph", action="store_true")
    args = p.parse_args(argv)

    try:
        rep = impact_of(args.gene_or_locus, args.mutation, max_labels=args.max_labels)
    except MutationError as e:
        print(f"{e}", file=sys.stderr)
        return 1

    print(json.dumps(rep.to_dict(), indent=2, ensure_ascii=False))
    if args.paragraph:
        print()
        print(rep.paragraph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
