#!/usr/bin/env python3
"""atlas_query.py -- stdlib-only client for the MTBC Gene Annotation Atlas REST API.

Queries the public, citable API served at https://mtbc.gclab.fr/api/v1 (self-contained
FastAPI sub-app; OpenAPI at /api/v1/docs). Read-only. No third-party deps (urllib+json).

Subcommands:
  stats                              dataset counts (verdicts, per-layer coverage)
  layers                             list the ~35 evidence layers + descriptions
  get <Rv> [--layer L]               full record for one gene, or just one layer
  search <query> [filters]           search/filter genes (paginated summaries)

search filters: --verdict {requalified,family_assigned,dark}  --hypothetical
                --has-layer <layer>  --limit N  --offset N

Global: --base URL (default env MTBC_ATLAS_API or https://mtbc.gclab.fr/api/v1)
        --raw   print raw JSON (default: a compact human view)
Examples:
  atlas_query.py get Rv2516c --layer vulnerability
  atlas_query.py search kinase --verdict dark --has-layer structure
  atlas_query.py search "" --has-layer integrative_lead --limit 100 --raw
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE = os.environ.get("MTBC_ATLAS_API", "https://mtbc.gclab.fr/api/v1")


def _get(base: str, path: str, params: dict | None = None, timeout: int = 30) -> dict:
    url = base.rstrip("/") + path
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "", False)})
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                               "User-Agent": "mtbc-atlas-skill/1.0"})
    last = None
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # 4xx are definitive (bad gene / bad layer) — surface the API message, don't retry.
            try:
                msg = json.loads(e.read().decode("utf-8")).get("detail", str(e))
            except Exception:
                msg = str(e)
            sys.exit(f"API error {e.code}: {msg}  ({url})")
        except Exception as e:  # transient (network, CDN): retry
            last = e
    sys.exit(f"Could not reach the atlas API after 3 tries: {last}\n  URL: {url}\n"
             "  (since 2026-09-08 the atlas is a STATIC site on GitHub Pages, so there is no\n"
             "   cold start to wait out: a persistent failure here is DNS, CDN or a wrong path,\n"
             "   not a container waking up. The API is frozen at the same URLs and returns valid\n"
             "   JSON, but served with Content-Type text/html — never gate on the MIME type.)")


# --- Repli sur déploiement STATIQUE de l'atlas (depuis 2026-09-06) -----------
# L'atlas n'est plus servi par un container mais par des fichiers figés (le container
# se dégradait en ~90 s sous trafic, cf. annotation_mtbc/pistes/P37.md). Toutes les URL
# de l'API restent valides, à deux réserves près, que ces deux fonctions absorbent :
#  - `/genes/{rv}/{layer}` n'est pas figé (3974 x 54 fichiers) ; la couche est servie
#    dans la fiche complète, sous la clé `layers` ;
#  - `/genes` ne FILTRE plus (la query string ne choisit plus le fichier) et rend la
#    collection entière, ce qu'elle annonce par un champ `static_note` : on refait alors
#    le filtrage ici plutôt que de laisser croire à une recherche qui n'a pas eu lieu.

def _get_layer(base: str, rv: str, layer: str) -> dict:
    """Une couche d'évidence, que l'API soit dynamique ou figée."""
    try:
        return _get(base, f"/genes/{rv}/{layer}")
    except SystemExit:
        pass  # 404 attendu sur un déploiement statique : on passe par la fiche complète
    full = _get(base, f"/genes/{rv}")
    layers = full.get("layers") or {}
    if layer not in layers:
        sys.exit(f"layer '{layer}' absent for {rv} (available: {', '.join(sorted(layers)) or 'none'})")
    return {"rv": rv, "layer": layer, "description": "", "data": layers[layer]}


def _match(g: dict, q: str) -> bool:
    q = q.strip().lower()
    return any(q in str(g.get(k) or "").lower()
               for k in ("rv", "gene_name", "mtbc0", "product_h37rv", "product_pgap",
                         "function_revised"))


def _search(base: str, params: dict) -> dict:
    """Recherche de gènes, avec repli de filtrage local si l'API est figée."""
    res = _get(base, "/genes", params)
    if "static_note" not in res:
        return res
    rows = res.get("results", [])
    if params.get("q"):
        rows = [g for g in rows if _match(g, params["q"])]
    if params.get("verdict"):
        rows = [g for g in rows if g.get("verdict") == params["verdict"]]
    if params.get("hypothetical"):
        rows = [g for g in rows if g.get("is_hypothetical")]
    if params.get("has_layer"):
        # les résumés ne portent pas les couches : on ne peut pas filtrer sans mentir
        sys.exit("--has-layer is not available on the static atlas deployment; "
                 "use `layers` then `get --layer` per gene, or query the local pipeline.")
    off = int(params.get("offset") or 0)
    lim = int(params.get("limit") or 50)
    return {"total": len(rows), "limit": lim, "offset": off,
            "results": rows[off:off + lim],
            "static_note": "filtered locally (static atlas deployment)"}


def _print(data, raw: bool, view=None):
    if raw or view is None:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        view(data)


def v_stats(d):
    print(f"genes: {d['total_genes']}  (hypothetical: {d['hypothetical']})")
    print("verdicts:", ", ".join(f"{k}={v}" for k, v in sorted(d["by_verdict"].items())))
    print("layer coverage (non-empty / gene):")
    for k, v in sorted(d["layer_coverage"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:<18} {v}")


def v_layers(d):
    print(f"{d['count']} evidence layers:")
    for name, desc in d["layers"].items():
        print(f"  {name:<18} {desc}")


def v_search(d):
    print(f"{d['total']} match(es) — showing {len(d['results'])} (offset {d['offset']}):")
    for g in d["results"]:
        name = f" {g['gene_name']}" if g.get("gene_name") else ""
        fn = g.get("function_revised") or g.get("product") or ""
        print(f"  {g['rv']:<9}{name:<10} [{g['verdict']}] {fn[:70]}")


def v_gene(d):
    print(f"# {d['rv']}" + (f" ({d['gene_name']})" if d.get("gene_name") else ""))
    print(f"  product: {d.get('product_pgap') or d.get('product_h37rv')}")
    print(f"  verdict: {d.get('verdict')}/{d.get('confidence')}  hypothetical={d.get('is_hypothetical')}")
    if d.get("function_revised"):
        print(f"  function_revised: {d['function_revised']}")
    layers = d.get("layers") or {}
    print(f"  layers present ({len(layers)}): {', '.join(sorted(layers))}")


def v_layer(d):
    print(f"# {d['rv']} / {d['layer']} — {d['description']}")
    print(json.dumps(d["data"], indent=2, ensure_ascii=False))


def main(argv=None):
    p = argparse.ArgumentParser(description="Query the MTBC Gene Annotation Atlas REST API.")
    p.add_argument("--base", default=DEFAULT_BASE, help=f"API base URL (default {DEFAULT_BASE})")
    p.add_argument("--raw", action="store_true", help="print raw JSON")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("stats", help="dataset counts")
    sub.add_parser("layers", help="list evidence layers")

    g = sub.add_parser("get", help="full record or one layer for a gene")
    g.add_argument("rv")
    g.add_argument("--layer", help="return only this evidence layer")

    s = sub.add_parser("search", help="search/filter genes")
    s.add_argument("query", nargs="?", default="", help="free text (rv/name/product/function)")
    s.add_argument("--verdict", choices=["requalified", "family_assigned", "dark"])
    s.add_argument("--hypothetical", action="store_true")
    s.add_argument("--has-layer", dest="has_layer", help="only genes carrying this layer")
    s.add_argument("--limit", type=int, default=50)
    s.add_argument("--offset", type=int, default=0)

    a = p.parse_args(argv)
    if a.cmd == "stats":
        _print(_get(a.base, "/stats"), a.raw, v_stats)
    elif a.cmd == "layers":
        _print(_get(a.base, "/layers"), a.raw, v_layers)
    elif a.cmd == "get":
        if a.layer:
            _print(_get_layer(a.base, a.rv, a.layer), a.raw, v_layer)
        else:
            _print(_get(a.base, f"/genes/{a.rv}"), a.raw, v_gene)
    elif a.cmd == "search":
        params = {"q": a.query, "verdict": a.verdict, "hypothetical": a.hypothetical or None,
                  "has_layer": a.has_layer, "limit": a.limit, "offset": a.offset}
        _print(_search(a.base, params), a.raw, v_search)


if __name__ == "__main__":
    main()
