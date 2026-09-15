#!/usr/bin/env python3
"""Client MCP minimal pour le serveur tblearn (TBannotator, IDEEV Paris-Saclay).

Objet       : appeler les outils MCP de tblearn en HTTP, sans dependance externe.
Entrees     : nom d'outil + arguments ; token via $TBLEARN_TOKEN ou ~/.config/tblearn/token.
Sorties     : texte rendu par l'outil (stdout) ou exception.
Reutilisable: oui -- destine au skill `tblearn` remplacant `tbannotator-mcp`.
Projet      : mtbc/ (transverse)
Date        : 2026-09-08
"""
import json, os, sys, urllib.request

URL = os.environ.get(
    "TBLEARN_URL",
    "https://tblearn.tbannotator.ideev.universite-paris-saclay.fr/api/v1/mcp",
)


def _token():
    t = os.environ.get("TBLEARN_TOKEN")
    if t:
        return t
    p = os.path.expanduser("~/.config/tblearn/token")
    if os.path.exists(p):
        return open(p).read().strip()
    return None


def call(tool, arguments=None, timeout=180):
    """Appelle un outil MCP et rend le texte concatene de sa reponse."""
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": tool, "arguments": arguments or {}}}
    headers = {"Content-Type": "application/json",
               "Accept": "application/json, text/event-stream"}
    tok = _token()
    if tok:
        headers["Authorization"] = "Bearer " + tok
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", "replace")

    # reponse en SSE (event:/data:) ou en JSON simple
    obj = None
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            line = line[5:].strip()
        if not line or line.startswith("event:"):
            continue
        try:
            cand = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(cand, dict) and ("result" in cand or "error" in cand):
            obj = cand
    if obj is None:
        raise RuntimeError("reponse illisible : " + body[:300])
    if "error" in obj:
        raise RuntimeError("erreur serveur : " + json.dumps(obj["error"])[:400])
    return "".join(c.get("text", "") for c in obj["result"].get("content", []))


def sql(query, timeout=180):
    """Raccourci : requete SQL en lecture seule."""
    return call("tool_query_postgres", {"sql": query}, timeout)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--schema":
        print(call("tool_get_schema"))
    elif len(sys.argv) > 1:
        print(sql(" ".join(sys.argv[1:])))
    else:
        print(__doc__)
