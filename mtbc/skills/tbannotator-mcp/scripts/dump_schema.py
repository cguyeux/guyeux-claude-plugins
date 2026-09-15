#!/usr/bin/env python3
"""dump_schema — écrit le schéma TBannotator courant en CSV, pour `check_schema_drift.py`.

Interroge le MCP TBannotator (`tool_query_postgres`) et produit un CSV
`object_name,column_name,populated` où `populated` vaut `false` pour les vues matérialisées
présentes MAIS non peuplées (piège : elles existent au catalogue, mais toute requête échoue
avec « has not been populated » — cas réel des vues protéiques le 2026-07-31).

Nécessite le paquet `mcp` (présent p. ex. dans le venv du site annotation_mtbc) :
    ~/docs/codes/mtbc/annotation_mtbc/site/.venv/bin/python dump_schema.py -o schema.csv
"""
from __future__ import annotations

import argparse
import ast
import asyncio
import csv
import io
from pathlib import Path

MCP_URL = "https://tblearn.tbannotator.ideev.universite-paris-saclay.fr/mcp"

SQL_COLUMNS = """
SELECT c.relname AS object_name, a.attname AS column_name,
       CASE WHEN c.relkind = 'm' AND NOT c.relispopulated THEN 'false' ELSE 'true' END AS populated
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped
WHERE n.nspname = 'public' AND c.relkind IN ('r', 'v', 'm')
ORDER BY c.relname, a.attnum
"""


async def _query(sql: str) -> str:
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    async with streamablehttp_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as s:
            await s.initialize()
            r = await s.call_tool("tool_query_postgres",
                                  {"query": sql, "max_rows": 100000, "timeout_seconds": 120})
            obj = ast.literal_eval(r.content[0].text)
            if not obj.get("success"):
                raise RuntimeError(obj.get("error", "query failed"))
            return obj["data"]["csv"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", type=Path, default=Path("schema.csv"))
    args = ap.parse_args()

    text = asyncio.run(_query(SQL_COLUMNS))
    rows = list(csv.DictReader(io.StringIO(text)))
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["object_name", "column_name", "populated"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in w.fieldnames})

    objs = {r["object_name"] for r in rows}
    unpop = {r["object_name"] for r in rows if r.get("populated") == "false"}
    print(f"écrit {args.out} : {len(objs)} objets, {len(rows)} colonnes")
    if unpop:
        print(f"⚠ vues matérialisées NON PEUPLÉES ({len(unpop)}) : {', '.join(sorted(unpop))}")


if __name__ == "__main__":
    main()
