"""Shell CLI for ESM Atlas client.

Usage:
    esm-atlas-cli hash <sequence>
    esm-atlas-cli lookup <hash>
    esm-atlas-cli lookup-seq <sequence_or_fasta_path>
    esm-atlas-cli similarity <sequence_or_fasta_path> [--topk N]
    esm-atlas-cli features
    esm-atlas-cli feature <feature_index>
    esm-atlas-cli cluster <hash>
    esm-atlas-cli structure <hash> [--out file.pdb]      # batch_lookup with structure
    esm-atlas-cli thumbnail <hash> [--out file.png]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .client import (
    EsmAtlasClient,
    EsmAtlasError,
    EsmAtlasPending,
    EsmAtlasUnavailable,
    hash_sequence,
)


def _read_sequence(arg: str) -> str:
    """If arg is a path to a FASTA file, read the first sequence; else return arg."""
    p = Path(arg)
    if p.exists() and p.is_file():
        lines = p.read_text().splitlines()
        seq_lines = [ln for ln in lines if not ln.startswith(">")]
        return "".join(seq_lines).strip()
    return arg.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="esm-atlas-cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("hash"); sp.add_argument("sequence")
    sp = sub.add_parser("lookup"); sp.add_argument("hash"); sp.add_argument("--topk", type=int, default=10)
    sp = sub.add_parser("lookup-seq"); sp.add_argument("sequence"); sp.add_argument("--topk", type=int, default=10)
    sp = sub.add_parser("similarity"); sp.add_argument("sequence"); sp.add_argument("--topk", type=int, default=25)
    sp = sub.add_parser("features")
    sp = sub.add_parser("feature"); sp.add_argument("feature_index", type=int)
    sp = sub.add_parser("cluster"); sp.add_argument("hash")
    sp = sub.add_parser("structure"); sp.add_argument("hash"); sp.add_argument("--out", default=None)
    sp = sub.add_parser("thumbnail"); sp.add_argument("hash"); sp.add_argument("--out", default=None)

    args = parser.parse_args(argv)

    with EsmAtlasClient() as client:
        try:
            if args.cmd == "hash":
                seq = _read_sequence(args.sequence)
                print(hash_sequence(seq))
                return 0

            if args.cmd == "lookup":
                print(json.dumps(client.lookup(args.hash, topk_features=args.topk), indent=2))
                return 0

            if args.cmd == "lookup-seq":
                seq = _read_sequence(args.sequence)
                print(json.dumps(client.lookup_sequence(seq, topk_features=args.topk), indent=2))
                return 0

            if args.cmd == "similarity":
                seq = _read_sequence(args.sequence)
                print(json.dumps(client.similarity_search(seq, topk_results=args.topk), indent=2))
                return 0

            if args.cmd == "features":
                print(json.dumps(client.features(), indent=2))
                return 0

            if args.cmd == "feature":
                print(json.dumps(client.feature_meta(args.feature_index), indent=2))
                return 0

            if args.cmd == "cluster":
                print(json.dumps(client.cluster(args.hash), indent=2))
                return 0

            if args.cmd == "structure":
                content = client.batch_lookup([args.hash], include_structure=True)
                if args.out:
                    Path(args.out).write_bytes(content if isinstance(content, bytes) else content.encode())
                    print(f"saved {args.out}")
                else:
                    sys.stdout.buffer.write(content if isinstance(content, bytes) else content.encode())
                return 0

            if args.cmd == "thumbnail":
                png = client.thumbnail(args.hash)
                if args.out:
                    Path(args.out).write_bytes(png)
                    print(f"saved {args.out}")
                else:
                    sys.stdout.buffer.write(png)
                return 0

        except EsmAtlasPending as e:
            print(f"pending: {e}", file=sys.stderr)
            return 2
        except EsmAtlasUnavailable as e:
            print(f"ESM Atlas unavailable: {e}", file=sys.stderr)
            return 3
        except EsmAtlasError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
