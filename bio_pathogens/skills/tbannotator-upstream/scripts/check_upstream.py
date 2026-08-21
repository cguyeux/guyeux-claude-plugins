#!/usr/bin/env python3
"""Veille sur le GitLab amont de la webapp TBannotator (groupe public tbannotator/webapp).

POURQUOI CE SCRIPT EXISTE
-------------------------
Les skills MTBC de ce depot encodent des hypotheses sur une plateforme qu'on ne
developpe pas : noms d'indices Elasticsearch, champs des documents `strain`,
routes de l'API FastAPI, definition de l'"exclusivite". Quand Clement pousse un
commit, ces hypotheses deviennent fausses SILENCIEUSEMENT : une requete sur un
champ renomme ne leve pas d'erreur, elle renvoie zero resultat, ce qui se lit
comme un resultat biologique ("aucun marqueur exclusif") alors que c'est une
derive de schema. Meme logique que `tbannotator-mcp/scripts/dump_schema.py`
pour la base PostgreSQL.

CE QU'IL SURVEILLE (quatre signaux, du plus grossier au plus fin)
  1. la liste des depots du groupe et leur `last_activity_at` ;
  2. le SHA de tete de chaque depot (detecte tout commit) ;
  3. les routes de l'instance vivante, via son `openapi.json` (detecte un
     endpoint ajoute, retire, renomme, SANS cloner quoi que ce soit) ;
  4. le schema des documents ES tel que le front le declare, en lisant les
     `interface` de `remix_app/app/utils/elasticsearch.server.ts`, plus le
     script painless de l'heuristique d'exclusivite.

Le signal 4 est le plus important scientifiquement : c'est celui qui invalide
des requetes sans provoquer d'erreur.

ACCES : le groupe et les quatre depots sont PUBLICS. Aucun jeton, aucune cle SSH
n'est necessaire. Stdlib uniquement, pas de dependance a installer.

USAGE
  python3 check_upstream.py --pin        # ecrit l'etat de reference (a relire avant commit)
  python3 check_upstream.py              # compare l'amont a l'etat epingle
  python3 check_upstream.py --json       # meme chose, sortie machine

CODES DE SORTIE
  0 = rien n'a bouge ; 1 = derive detectee (lire le rapport) ; 2 = amont
  injoignable ou etat de reference absent (ne PAS interpreter comme "rien n'a
  bouge").

PIEGE CONNU : l'instance vivante est derriere un certificat auto-signe
(nip.io), d'ou le contexte SSL permissif ci-dessous. C'est acceptable ici parce
qu'on ne lit que des metadonnees publiques et qu'on n'envoie aucun secret ; ne
pas recopier ce contexte dans un script qui transmet des identifiants.
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

GITLAB_API = "https://gitlab.com/api/v4"
GROUP = "tbannotator"
LIVE_OPENAPI = "https://tbannotator.82.64.250.114.nip.io/fastapi/openapi.json"

# Fichier source dont on suit le schema (chemin dans le depot remix_app).
SCHEMA_FILE = "app/utils/elasticsearch.server.ts"
SCHEMA_REPO = "tbannotator/webapp/remix_app"

PIN_PATH = Path(__file__).resolve().parent.parent / "references" / "upstream_pinned.json"

_LAX_SSL = ssl.create_default_context()
_LAX_SSL.check_hostname = False
_LAX_SSL.verify_mode = ssl.CERT_NONE


def fetch(url: str, lax_ssl: bool = False, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "tbannotator-upstream/1.0"})
    ctx = _LAX_SSL if lax_ssl else None
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read()


def fetch_json(url: str, lax_ssl: bool = False) -> Any:
    return json.loads(fetch(url, lax_ssl=lax_ssl))


# --------------------------------------------------------------------------- #
# Collecte
# --------------------------------------------------------------------------- #

def collect_projects() -> dict[str, dict[str, Any]]:
    """Depots du groupe, sous-groupes inclus.

    `include_subgroups=true` est INDISPENSABLE : les quatre depots vivent dans
    le sous-groupe `tbannotator/webapp`, et l'endpoint sans ce parametre renvoie
    un tableau vide, ce qui se lit a tort comme "groupe vide".
    """
    url = (f"{GITLAB_API}/groups/{GROUP}/projects"
           "?include_subgroups=true&per_page=100&order_by=path&sort=asc")
    out: dict[str, dict[str, Any]] = {}
    for p in fetch_json(url):
        path = p["path_with_namespace"]
        entry = {
            "id": p["id"],
            "default_branch": p.get("default_branch"),
            "last_activity_at": p.get("last_activity_at"),
            "visibility": p.get("visibility"),
            "head_sha": None,
            "head_title": None,
            "head_date": None,
        }
        branch = entry["default_branch"]
        if branch:
            try:
                commits = fetch_json(
                    f"{GITLAB_API}/projects/{p['id']}/repository/commits"
                    f"?ref_name={urllib.parse.quote(branch)}&per_page=1")
                if commits:
                    entry["head_sha"] = commits[0]["id"][:12]
                    entry["head_title"] = commits[0]["title"]
                    entry["head_date"] = commits[0]["committed_date"][:10]
            except urllib.error.HTTPError:
                pass
        out[path] = entry
    return out


def collect_live_routes() -> dict[str, Any]:
    """Routes de l'instance vivante + etat de sante de chaque route non triviale.

    On ne teste PAS chaque endpoint (trop couteux, effets de bord possibles) :
    on releve seulement l'inventaire declare par OpenAPI. Le fait qu'une route
    existe ne dit rien de son bon fonctionnement (au 2026-08-17 les routes
    `/genes/{locus_tag}/snps*` renvoient 500 sur `/cache/embeddings`).
    """
    spec = fetch_json(LIVE_OPENAPI, lax_ssl=True)
    routes = sorted(f"{m.upper()} {path}"
                    for path, ops in spec.get("paths", {}).items()
                    for m in ops)
    return {"reachable": True, "count": len(routes), "routes": routes}


def _project_id(projects: dict[str, dict[str, Any]], path: str) -> int | None:
    p = projects.get(path)
    return p["id"] if p else None


def collect_es_schema(projects: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Champs des `interface` TypeScript + heuristique painless d'exclusivite.

    Le front est la source de verite la plus lisible sur la forme des documents
    ES : le mapping lui-meme n'est pas dans ces depots (l'indexation est faite
    par le pipeline C# Dataflow, ailleurs).
    """
    pid = _project_id(projects, SCHEMA_REPO)
    if pid is None:
        return {"reachable": False, "interfaces": {}, "exclusivity_heuristic": None}

    branch = projects[SCHEMA_REPO]["default_branch"] or "main"
    url = (f"{GITLAB_API}/projects/{pid}/repository/files/"
           f"{urllib.parse.quote(SCHEMA_FILE, safe='')}/raw?ref={urllib.parse.quote(branch)}")
    src = fetch(url).decode("utf-8", errors="replace")

    # Blocs `interface X { ... }` au premier niveau d'accolade. Regex volontairement
    # simple : ces interfaces sont plates, un vrai parseur TS serait du luxe ici.
    interfaces: dict[str, list[str]] = {}
    for m in re.finditer(r"(?:export\s+)?interface\s+(\w+)\s*\{", src):
        name = m.group(1)
        depth, i = 1, m.end()
        while i < len(src) and depth:
            depth += (src[i] == "{") - (src[i] == "}")
            i += 1
        body = src[m.end():i - 1]
        fields = sorted(set(re.findall(r"^\s*(\w+)\??\s*:", body, re.MULTILINE)))
        interfaces[name] = fields

    heur = re.search(r"params\._subset_freq[^\"']+", src)
    # Les indices apparaissent sous trois formes dans ce fichier : `index: "snp"`,
    # `queryWithTermsAggregation("is", ...)` et le 2e argument d'`extractExclusivity`.
    # Ne garder que la premiere forme ferait rater `gene`, `is` et `rd`.
    indices = sorted(set(
        re.findall(r"index:\s*[\"'](\w+)[\"']", src)
        + re.findall(r"queryWithTermsAggregation\(\s*[\"'](\w+)[\"']", src)
        + re.findall(r"extractExclusivity<[^>]+>\(\s*[\"'][^\"']+[\"'],\s*\n?\s*[\"'](\w+)[\"']", src)
    ))
    agg_fields = sorted(set(re.findall(r"getAggregation\(\s*\n?\s*[\"']([\w.]+)[\"']", src)))

    return {
        "reachable": True,
        "interfaces": interfaces,
        "es_indices": indices,
        "exclusivity_agg_fields": agg_fields,
        "exclusivity_heuristic": heur.group(0).strip() if heur else None,
    }


def collect() -> dict[str, Any]:
    projects = collect_projects()
    try:
        live = collect_live_routes()
    except Exception as exc:                                    # noqa: BLE001
        live = {"reachable": False, "error": str(exc), "routes": []}
    try:
        schema = collect_es_schema(projects)
    except Exception as exc:                                    # noqa: BLE001
        schema = {"reachable": False, "error": str(exc), "interfaces": {}}
    return {"projects": projects, "live_api": live, "es_schema": schema}


# --------------------------------------------------------------------------- #
# Comparaison
# --------------------------------------------------------------------------- #

def diff(pinned: dict[str, Any], now: dict[str, Any]) -> list[str]:
    report: list[str] = []

    old_p, new_p = pinned["projects"], now["projects"]
    for path in sorted(set(new_p) - set(old_p)):
        report.append(f"[DEPOT AJOUTE] {path} ({new_p[path]['visibility']})")
    for path in sorted(set(old_p) - set(new_p)):
        report.append(f"[DEPOT DISPARU] {path} (prive, renomme ou supprime)")
    for path in sorted(set(old_p) & set(new_p)):
        o, n = old_p[path], new_p[path]
        if o.get("head_sha") != n.get("head_sha"):
            report.append(
                f"[COMMIT] {path} : {o.get('head_sha')} -> {n.get('head_sha')} "
                f"({n.get('head_date')}) {n.get('head_title')!r}")
        if o.get("visibility") != n.get("visibility"):
            report.append(f"[VISIBILITE] {path} : {o.get('visibility')} -> {n.get('visibility')}")

    old_r = set(pinned["live_api"].get("routes") or [])
    new_r = set(now["live_api"].get("routes") or [])
    if not now["live_api"].get("reachable"):
        report.append(f"[API INJOIGNABLE] {now['live_api'].get('error', 'sans detail')}")
    else:
        for r in sorted(new_r - old_r):
            report.append(f"[ROUTE AJOUTEE] {r}")
        for r in sorted(old_r - new_r):
            report.append(f"[ROUTE RETIREE] {r}")

    o_s, n_s = pinned["es_schema"], now["es_schema"]
    if not n_s.get("reachable"):
        report.append(f"[SCHEMA ES ILLISIBLE] {n_s.get('error', 'sans detail')}")
    else:
        o_i, n_i = o_s.get("interfaces", {}), n_s.get("interfaces", {})
        for name in sorted(set(n_i) - set(o_i)):
            report.append(f"[TYPE AJOUTE] interface {name}")
        for name in sorted(set(o_i) - set(n_i)):
            report.append(f"[TYPE RETIRE] interface {name}")
        for name in sorted(set(o_i) & set(n_i)):
            added, removed = set(n_i[name]) - set(o_i[name]), set(o_i[name]) - set(n_i[name])
            if added:
                report.append(f"[CHAMP AJOUTE] {name}: {', '.join(sorted(added))}")
            if removed:
                report.append(
                    f"[CHAMP RETIRE] {name}: {', '.join(sorted(removed))} "
                    "<-- une requete sur ce champ renverra 0 resultat SANS erreur")
        if o_s.get("es_indices") != n_s.get("es_indices"):
            report.append(f"[INDICES ES] {o_s.get('es_indices')} -> {n_s.get('es_indices')}")
        if o_s.get("exclusivity_agg_fields") != n_s.get("exclusivity_agg_fields"):
            report.append(f"[CHAMPS EXCLUSIVITE] {o_s.get('exclusivity_agg_fields')} "
                          f"-> {n_s.get('exclusivity_agg_fields')}")
        if o_s.get("exclusivity_heuristic") != n_s.get("exclusivity_heuristic"):
            report.append("[HEURISTIQUE EXCLUSIVITE MODIFIEE] la definition du score a change :\n"
                          f"    avant : {o_s.get('exclusivity_heuristic')}\n"
                          f"    apres : {n_s.get('exclusivity_heuristic')}")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pin", action="store_true",
                    help="ecrire l'etat courant comme reference (relire le diff avant commit)")
    ap.add_argument("--json", action="store_true", help="sortie machine")
    args = ap.parse_args()

    try:
        now = collect()
    except Exception as exc:                                    # noqa: BLE001
        print(f"AMONT INJOIGNABLE : {exc}", file=sys.stderr)
        return 2

    if args.pin:
        PIN_PATH.parent.mkdir(parents=True, exist_ok=True)
        PIN_PATH.write_text(json.dumps(now, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"Etat epingle -> {PIN_PATH}")
        for path, p in sorted(now["projects"].items()):
            print(f"  {path:40s} {p.get('head_sha')} {p.get('head_date')} {p.get('head_title')}")
        print(f"  routes API vivantes : {now['live_api'].get('count')}")
        print(f"  interfaces ES suivies : {len(now['es_schema'].get('interfaces', {}))}")
        return 0

    if not PIN_PATH.exists():
        print(f"Aucun etat de reference ({PIN_PATH}). Lancer --pin d'abord.", file=sys.stderr)
        return 2

    pinned = json.loads(PIN_PATH.read_text())
    report = diff(pinned, now)

    if args.json:
        print(json.dumps({"drift": bool(report), "report": report}, indent=2, ensure_ascii=False))
    elif report:
        print("DERIVE AMONT DETECTEE\n")
        for line in report:
            print(f"  {line}")
        print("\nActions : relire le commit en cause sur gitlab.com/tbannotator/webapp, "
              "verifier les skills qui dependent des champs touches, puis --pin pour reprendre "
              "la surveillance a partir du nouvel etat.")
    else:
        print("Amont inchange (depots, routes de l'API vivante, schema ES).")

    return 1 if report else 0


if __name__ == "__main__":
    sys.exit(main())
