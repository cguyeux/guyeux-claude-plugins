#!/usr/bin/env python3
"""Acces lecture a l'Elasticsearch de TBannotator : serveur MCP + CLI de secours.

POSITIONNEMENT (ne pas confondre trois sources)
-----------------------------------------------
  * `tbannotator-mcp`  -> base PostgreSQL v3.6 (IDEEV), classifications de lignees,
                          ~255 000 souches, arbres NJ/RAxML.
  * `tbmonitor`        -> corpus SQLite de litterature TB (PubMed).
  * CE SCRIPT          -> les indices Elasticsearch de la webapp (strain, snp,
                          gene, is, rd), qui portent des champs ABSENTS de
                          PostgreSQL : crisprStats, mappingStats, quality
                          (fastp), missingGenes / missingRegionsOfDifference avec
                          couverture, insertionSequences, resistances avec
                          `isPhenotypic` et `sourceDoi`, metadonnees de run
                          (coordonnees, host, hostHiv, isolationSource,
                          bioProjectId).
Une reponse vide ici ne signifie donc pas "absent de TBannotator" : verifier
aussi PostgreSQL, comme `fetch-tbannotator` le fait deja entre `mp` et HTTP.

ETAT AU 2026-08-17 : l'ES n'est PAS joignable depuis l'exterieur. Le nginx de
l'instance ne route que `/` (webapp) et `/fastapi/` ; le cluster ecoute en
interne (`quickstart-es-http:9200`). Ce fichier est donc utilisable des que l'un
des deux acces existe :
  (a) exposition en lecture cote serveur -- le role `readonly` (privilege `read`
      sur tous les indices + `monitor`) est DEJA defini dans
      `compose/es_entrypoint/roles.yml`, il ne manque qu'une route ;
  (b) tunnel SSH vers l'hote qui heberge le cluster.
Tant qu'aucun des deux n'existe, `--selftest` echoue proprement : c'est le
comportement voulu, pas un bug a contourner.

CONFIGURATION (aucun secret dans ce depot)
  export TBANNOTATOR_ES_URL=https://127.0.0.1:9200
  export TBANNOTATOR_ES_USER=readonly
  export TBANNOTATOR_ES_PASSWORD=...
ou un fichier `~/.config/tbannotator_es.env` en lignes `CLE=valeur` (chmod 600).
`TBANNOTATOR_ES_INSECURE=1` pour un certificat auto-signe (cas du deploiement
actuel). Ne JAMAIS recopier ici un identifiant lu dans les depots publics : ceux
qui y trainent sont a considerer comme compromis.

USAGE
  serveur MCP (stdio) :   python3 tbannotator_es_mcp.py
  enregistrement     :   claude mcp add --scope user tbannotator-es -- python3 <chemin absolu>
  CLI de secours     :   python3 tbannotator_es_mcp.py --selftest
                         python3 tbannotator_es_mcp.py --get strain SRR1234567
                         python3 tbannotator_es_mcp.py --agg strain lineages.lineageNames
                         python3 tbannotator_es_mcp.py --exclusivity '{"term": {"lineages.lineageNames": "L6.1.1"}}'

Le mode CLI n'a besoin que de la bibliotheque standard ; seul le mode serveur
demande le paquet `mcp` (present dans le venv du site :
`~/docs/codes/mtbc/annotation_mtbc/site/.venv/bin/python`).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

CONFIG_FILE = Path.home() / ".config" / "tbannotator_es.env"
INDICES = ("strain", "snp", "gene", "is", "rd")

# Les quatre familles de marqueurs agregees par le front pour l'exclusivite.
EXCLUSIVITY_FIELDS = {
    "variants": "snps.spdi",
    "missingGenes": "missingGenes.gene.id",
    "insertionSequences": "insertionSequences.id",
    "missingRegionsOfDifference": "missingRegionsOfDifference.id",
}

# Heuristique painless recopiee TELLE QUELLE du front (remix_app, commit
# f5bd6294 "fix: exclusivite"). Toute divergence rendrait nos chiffres
# incomparables a ceux affiches dans l'interface : ne pas "ameliorer" sans
# synchroniser des deux cotes. `tbannotator-upstream` surveille cette ligne.
EXCLUSIVITY_SCRIPT = (
    "params._subset_freq*1.0/"
    "(params._superset_freq - params._subset_freq + params._subset_size)"
)


# --------------------------------------------------------------------------- #
# Transport
# --------------------------------------------------------------------------- #

def _load_config() -> dict[str, str]:
    cfg: dict[str, str] = {}
    if CONFIG_FILE.exists():
        for line in CONFIG_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    cfg.update({k: v for k, v in os.environ.items() if k.startswith("TBANNOTATOR_ES_")})
    return cfg


class ESError(RuntimeError):
    """Erreur d'acces au cluster, formulee pour etre lisible telle quelle."""


def _request(path: str, payload: dict[str, Any] | None = None,
             method: str | None = None, timeout: int = 120) -> Any:
    cfg = _load_config()
    base = cfg.get("TBANNOTATOR_ES_URL")
    if not base:
        raise ESError(
            "TBANNOTATOR_ES_URL non defini. L'ES de TBannotator n'est pas expose "
            f"publiquement : ouvrir un tunnel SSH ou demander l'exposition du role "
            f"`readonly`, puis renseigner {CONFIG_FILE}.")

    url = base.rstrip("/") + "/" + path.lstrip("/")
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"))
    req.add_header("Content-Type", "application/json")

    user, pwd = cfg.get("TBANNOTATOR_ES_USER"), cfg.get("TBANNOTATOR_ES_PASSWORD")
    if user:
        token = base64.b64encode(f"{user}:{pwd or ''}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")

    ctx = None
    if cfg.get("TBANNOTATOR_ES_INSECURE") == "1":
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:600]
        raise ESError(f"HTTP {exc.code} sur {path} : {body}") from exc
    except Exception as exc:                                     # noqa: BLE001
        raise ESError(f"cluster injoignable ({url}) : {exc}") from exc


# --------------------------------------------------------------------------- #
# Operations (partagees par le serveur MCP et la CLI)
# --------------------------------------------------------------------------- #

def op_health() -> dict[str, Any]:
    """Sante du cluster et nombre de documents par indice."""
    health = _request("_cluster/health")
    counts = {}
    for idx in INDICES:
        try:
            counts[idx] = _request(f"{idx}/_count")["count"]
        except ESError as exc:
            counts[idx] = f"indisponible ({exc})"
    return {"cluster": {k: health.get(k) for k in
                        ("status", "number_of_nodes", "active_shards")},
            "documents": counts}


def op_search(index: str, query: dict[str, Any] | None = None, size: int = 10,
              fields: list[str] | None = None, sort: list[Any] | None = None) -> dict[str, Any]:
    """Recherche brute. `fields` limite le `_source` : un document `strain`
    complet pese plusieurs centaines de kilo-octets (des milliers de SNP), donc
    toujours projeter sauf besoin explicite du document entier."""
    body: dict[str, Any] = {"query": query or {"match_all": {}}, "size": size,
                            "track_total_hits": True}
    if fields:
        body["_source"] = fields
    if sort:
        body["sort"] = sort
    res = _request(f"{index}/_search", body)
    return {
        "total": res["hits"]["total"]["value"],
        "returned": len(res["hits"]["hits"]),
        "hits": [{"id": h["_id"], **h.get("_source", {})} for h in res["hits"]["hits"]],
    }


def op_get(index: str, doc_id: str) -> dict[str, Any]:
    """Document complet par identifiant (accession SRA pour `strain`, SPDI pour `snp`)."""
    res = _request(f"{index}/_doc/{urllib.parse.quote(doc_id, safe='')}", method="GET")
    return {"id": res.get("_id"), "found": res.get("found"), "source": res.get("_source")}


def op_aggregate(index: str, field: str, query: dict[str, Any] | None = None,
                 size: int = 50) -> dict[str, Any]:
    """Agregation `terms` : compter les souches par lignee, pays, IS, RD, resistance."""
    body = {"query": query or {"match_all": {}}, "size": 0,
            "aggs": {"t": {"terms": {"field": field, "size": size}}}}
    res = _request(f"{index}/_search", body)
    buckets = res["aggregations"]["t"]["buckets"]
    return {"field": field, "buckets": [{"key": b["key"], "count": b["doc_count"]}
                                        for b in buckets],
            "other_count": res["aggregations"]["t"].get("sum_other_doc_count")}


def op_exclusivity(query: dict[str, Any], size: int = 50,
                   background_ids: list[str] | None = None,
                   families: list[str] | None = None) -> dict[str, Any]:
    """Marqueurs sur-representes dans le sous-ensemble defini par `query`.

    Reproduit exactement le calcul de l'interface web : quatre agregations
    `significant_terms` en une passe, avec l'heuristique maison. Le score n'est
    PAS une p-valeur : c'est `subset_freq / (superset_freq - subset_freq +
    subset_size)`, qui vaut 1 pour un marqueur present dans tout le sous-ensemble
    et nulle part ailleurs, et decroit avec les porteurs hors sous-ensemble.

    PIEGES a garder en tete avant de publier un chiffre issu d'ici :
      * `min_doc_count = 1` (comme le front) fait remonter des singletons ;
        filtrer sur `in_set_count` avant toute interpretation.
      * le fond de comparaison est l'ensemble des documents ayant le champ,
        sauf si `background_ids` restreint la comparaison a un clade parent --
        c'est ce dernier usage qui repond a "exclusif AU SEIN de la lignee".
      * un marqueur absent d'un fond mal choisi n'est pas un marqueur exclusif,
        c'est un artefact de cadrage.
    """
    chosen = families or list(EXCLUSIVITY_FIELDS)
    aggs: dict[str, Any] = {}
    for name in chosen:
        field = EXCLUSIVITY_FIELDS[name]
        must: list[dict[str, Any]] = [{"exists": {"field": field}}]
        if background_ids:
            must.append({"terms": {"_id": background_ids}})
        aggs[name] = {"significant_terms": {
            "field": field,
            "size": size,
            "min_doc_count": 1,
            "background_filter": {"bool": {"must": must}},
            "script_heuristic": {"script": {"lang": "painless",
                                            "source": EXCLUSIVITY_SCRIPT}},
        }}

    res = _request("strain/_search", {"query": query, "size": 0,
                                      "track_total_hits": True, "aggs": aggs})
    out: dict[str, Any] = {
        "subset_size": res["hits"]["total"]["value"],
        "heuristic": EXCLUSIVITY_SCRIPT,
        "background": "clade parent restreint" if background_ids else "tous les documents du champ",
    }
    for name in chosen:
        out[name] = [{"id": b["key"], "score": b["score"],
                      "in_set_count": b["doc_count"], "total_count": b["bg_count"]}
                     for b in res["aggregations"][name]["buckets"]]
    return out


# --------------------------------------------------------------------------- #
# Serveur MCP
# --------------------------------------------------------------------------- #

def serve() -> int:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print("Le paquet `mcp` est absent. Utiliser le venv du site :\n"
              "  ~/docs/codes/mtbc/annotation_mtbc/site/.venv/bin/python "
              f"{Path(__file__).resolve()}", file=sys.stderr)
        return 2

    mcp = FastMCP("tbannotator-es")

    @mcp.tool()
    def es_health() -> dict:
        """Sante du cluster Elasticsearch TBannotator et volume par indice
        (strain, snp, gene, is, rd). A appeler en premier : c'est aussi le test
        d'accessibilite du cluster."""
        return op_health()

    @mcp.tool()
    def es_search(index: str, query: dict | None = None, size: int = 10,
                  fields: list[str] | None = None, sort: list | None = None) -> dict:
        """Recherche Elasticsearch (DSL brut) sur un indice TBannotator.
        `fields` projette le _source : indispensable sur `strain`, dont les
        documents complets font plusieurs centaines de kilo-octets."""
        return op_search(index, query, size, fields, sort)

    @mcp.tool()
    def es_get(index: str, doc_id: str) -> dict:
        """Document complet par identifiant : accession SRA pour `strain`,
        SPDI (`NC_000962.3:pos:ref:alt`) pour `snp`."""
        return op_get(index, doc_id)

    @mcp.tool()
    def es_aggregate(index: str, field: str, query: dict | None = None,
                     size: int = 50) -> dict:
        """Agregation `terms` : repartition des souches par lignee, pays, IS, RD
        ou resistance, sur un sous-ensemble optionnel."""
        return op_aggregate(index, field, query, size)

    @mcp.tool()
    def es_exclusivity(query: dict, size: int = 50,
                       background_ids: list[str] | None = None,
                       families: list[str] | None = None) -> dict:
        """Marqueurs sur-representes dans un sous-ensemble de souches, sur les
        quatre familles a la fois (SNP, genes manquants, sequences d'insertion,
        RD manquantes), avec l'heuristique exacte de l'interface web.
        `background_ids` restreint le fond de comparaison a un clade parent, ce
        qui est le seul cadrage correct pour "exclusif au sein de la lignee".
        Le score n'est pas une p-valeur et `min_doc_count=1` laisse passer des
        singletons : filtrer sur `in_set_count`."""
        return op_exclusivity(query, size, background_ids, families)

    mcp.run()
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true", help="tester l'acces au cluster")
    ap.add_argument("--get", nargs=2, metavar=("INDEX", "ID"))
    ap.add_argument("--agg", nargs=2, metavar=("INDEX", "FIELD"))
    ap.add_argument("--search", nargs=2, metavar=("INDEX", "QUERY_JSON"))
    ap.add_argument("--exclusivity", metavar="QUERY_JSON")
    ap.add_argument("--size", type=int, default=20)
    args = ap.parse_args()

    try:
        if args.selftest:
            out = op_health()
        elif args.get:
            out = op_get(*args.get)
        elif args.agg:
            out = op_aggregate(args.agg[0], args.agg[1], size=args.size)
        elif args.search:
            out = op_search(args.search[0], json.loads(args.search[1]), size=args.size)
        elif args.exclusivity:
            out = op_exclusivity(json.loads(args.exclusivity), size=args.size)
        else:
            return serve()
    except ESError as exc:
        print(f"ACCES ES INDISPONIBLE : {exc}", file=sys.stderr)
        return 2

    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
