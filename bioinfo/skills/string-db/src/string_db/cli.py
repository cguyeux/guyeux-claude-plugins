"""Command-line interface for the STRING REST client.

Subcommands:
  map           resolve identifiers / locus tags to STRING ids
  partners      functional (or physical) interaction partners of a protein
  network       interactions among a set of proteins
  enrichment    functional enrichment (GO/KEGG/Pfam/InterPro) of a gene set
  annotation    per-protein functional annotation
  ppi           PPI-enrichment test (is the set a real complex/pathway?)
  image         download a rendered network picture

Default species is 83332 (M. tuberculosis H37Rv); override with --species.
Output is a compact TSV table by default, or raw JSON with --json.
"""
from __future__ import annotations

import argparse
import json
import sys

from . import client


def _emit(rows, columns, as_json: bool) -> None:
    if as_json:
        json.dump(rows, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return
    print("\t".join(columns))
    for r in rows:
        print("\t".join(str(r.get(c, "")) for c in columns))


def _channels_str(r: dict, floor: int = 400) -> str:
    names = ["neighborhood", "fusion", "cooccurrence", "coexpression",
             "experimental", "database", "textmining"]
    return " ".join(f"{n}:{r[n]}" for n in names if r.get(n, 0) >= floor)


def cmd_map(a) -> int:
    rows = client.map_ids(a.identifiers, species=a.species, limit=a.limit)
    _emit(rows, ["queryItem", "stringId", "preferredName", "annotation"], a.json)
    return 0


def cmd_partners(a) -> int:
    rows = client.partners(a.identifiers, species=a.species, limit=a.limit,
                           required_score=a.required_score, physical=a.physical)
    if a.context_only:
        rows = [r for r in rows if r["context"] >= a.required_score or
                (a.required_score is None and r["context"] >= 400)]
    rows.sort(key=lambda r: r["combined"], reverse=True)
    if a.json:
        _emit(rows, [], True)
        return 0
    print("partner\tcombined\tcontext\tchannels(>=400)")
    for r in rows:
        print(f"{r['b']}\t{r['combined']}\t{r['context']}\t{_channels_str(r)}")
    return 0


def cmd_network(a) -> int:
    rows = client.network(a.identifiers, species=a.species,
                          required_score=a.required_score, add_nodes=a.add_nodes,
                          physical=a.physical)
    if a.json:
        _emit(rows, [], True)
        return 0
    print("a\tb\tcombined\tcontext\tchannels(>=400)")
    for r in rows:
        print(f"{r['a']}\t{r['b']}\t{r['combined']}\t{r['context']}\t{_channels_str(r)}")
    return 0


def cmd_enrichment(a) -> int:
    rows = client.enrichment(a.identifiers, species=a.species)
    if a.category:
        cats = {c.lower() for c in a.category}
        rows = [r for r in rows if r.get("category", "").lower() in cats]
    if a.fdr is not None:
        rows = [r for r in rows if float(r.get("fdr", 1)) <= a.fdr]
    _emit(rows, ["category", "term", "description", "number_of_genes", "fdr",
                 "preferredNames"], a.json)
    return 0


def cmd_annotation(a) -> int:
    rows = client.functional_annotation(a.identifiers, species=a.species)
    _emit(rows, ["category", "term", "description", "number_of_genes",
                 "ratio_in_set"], a.json)
    return 0


def cmd_ppi(a) -> int:
    res = client.ppi_enrichment(a.identifiers, species=a.species)
    if a.json:
        json.dump(res, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    for k in ("number_of_nodes", "number_of_edges", "expected_number_of_edges",
              "average_node_degree", "local_clustering_coefficient", "p_value"):
        print(f"{k}\t{res.get(k, '')}")
    return 0


def cmd_image(a) -> int:
    dest = client.network_image(a.identifiers, a.output, species=a.species,
                                highres=a.highres, svg=a.svg,
                                required_score=a.required_score, physical=a.physical)
    print(f"wrote {dest}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="string-db",
                                description="Ad-hoc STRING v12 REST queries "
                                            "(default species 83332 = M. tuberculosis H37Rv).")
    p.add_argument("--species", type=int, default=client.DEFAULT_SPECIES,
                   help="NCBI taxon id (default 83332, H37Rv).")
    p.add_argument("--json", action="store_true", help="emit raw JSON instead of a table.")
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("map", help="resolve identifiers to STRING ids.")
    m.add_argument("identifiers", nargs="+")
    m.add_argument("--limit", type=int, default=1, help="matches per identifier.")
    m.set_defaults(func=cmd_map)

    pa = sub.add_parser("partners", help="interaction partners of the query protein(s).")
    pa.add_argument("identifiers", nargs="+")
    pa.add_argument("--limit", type=int, default=20)
    pa.add_argument("--required-score", type=int, default=None,
                    help="min combined score 0-1000 (e.g. 400 medium, 700 high).")
    pa.add_argument("--physical", action="store_true", help="physical subnetwork only.")
    pa.add_argument("--context-only", action="store_true",
                    help="keep only edges carried by genomic-context channels.")
    pa.set_defaults(func=cmd_partners)

    n = sub.add_parser("network", help="interactions among a set of proteins.")
    n.add_argument("identifiers", nargs="+")
    n.add_argument("--required-score", type=int, default=None)
    n.add_argument("--add-nodes", type=int, default=None,
                   help="add N high-confidence interactors to the set.")
    n.add_argument("--physical", action="store_true")
    n.set_defaults(func=cmd_network)

    e = sub.add_parser("enrichment", help="functional enrichment of a gene set.")
    e.add_argument("identifiers", nargs="+")
    e.add_argument("--category", nargs="*", default=None,
                   help="filter categories (e.g. KEGG Process Pfam InterPro).")
    e.add_argument("--fdr", type=float, default=None, help="max FDR.")
    e.set_defaults(func=cmd_enrichment)

    an = sub.add_parser("annotation", help="per-protein functional annotation.")
    an.add_argument("identifiers", nargs="+")
    an.set_defaults(func=cmd_annotation)

    pp = sub.add_parser("ppi", help="PPI-enrichment test on a gene set.")
    pp.add_argument("identifiers", nargs="+")
    pp.set_defaults(func=cmd_ppi)

    im = sub.add_parser("image", help="download a network picture.")
    im.add_argument("identifiers", nargs="+")
    im.add_argument("-o", "--output", required=True)
    im.add_argument("--required-score", type=int, default=None)
    im.add_argument("--highres", action="store_true")
    im.add_argument("--svg", action="store_true")
    im.add_argument("--physical", action="store_true")
    im.set_defaults(func=cmd_image)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except client.StringError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
