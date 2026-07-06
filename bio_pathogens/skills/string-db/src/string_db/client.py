"""Resilient, stdlib-only client for the STRING database REST API (v12).

STRING (https://string-db.org) aggregates known and predicted protein-protein
associations, decomposed into evidence channels (neighborhood, fusion,
co-occurrence, co-expression, experimental, database, text-mining). This module
wraps the REST API for *occasional* / ad-hoc queries -- the use STRING's own
documentation endorses for the API. For whole-proteome enrichment, download the
per-organism bulk files instead (see the annotation_mtbc phase2h pipeline).

Design notes:
  * stdlib only (urllib) -- no requests/pandas, so it drops into any venv.
  * Disk cache keyed by the request URL (STRING data is static per version, so
    cached responses never go stale within a release).
  * Polite rate limiting (STRING asks for limited API use); a small minimum
    interval between *live* calls, cache hits are free.
  * Every call carries a `caller_identity` as STRING requests.
  * Default species = 83332 (M. tuberculosis H37Rv); override per call.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

API_ROOT = os.environ.get("STRING_API_ROOT", "https://string-db.org/api")
CALLER = os.environ.get("STRING_CALLER", "annotation_mtbc.guyeux.femto-st")
CACHE_DIR = Path(os.environ.get("STRING_CACHE", Path.home() / ".cache" / "string-db"))
DEFAULT_SPECIES = int(os.environ.get("STRING_SPECIES", "83332"))  # H37Rv
MIN_INTERVAL = float(os.environ.get("STRING_MIN_INTERVAL", "0.45"))  # seconds between live calls

# Per-channel score fields in interaction_partners / network responses.
CHANNEL_FIELDS = {
    "nscore": "neighborhood", "fscore": "fusion", "pscore": "cooccurrence",
    "ascore": "coexpression", "escore": "experimental", "dscore": "database",
    "tscore": "textmining",
}

_last_call = [0.0]


class StringError(RuntimeError):
    pass


def _cache_path(url: str) -> Path:
    h = hashlib.sha256(url.encode()).hexdigest()[:32]
    return CACHE_DIR / f"{h}.bin"


def _throttle() -> None:
    dt = time.monotonic() - _last_call[0]
    if dt < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - dt)
    _last_call[0] = time.monotonic()


def _build_url(fmt: str, method: str, identifiers: list[str] | None,
               species: int | None, extra: dict) -> str:
    params: dict[str, str] = {"caller_identity": CALLER}
    if species is not None:
        params["species"] = str(species)
    if identifiers:
        # STRING separates identifiers by a carriage return (%0d).
        params["identifiers"] = "\r".join(identifiers)
    for k, v in extra.items():
        if v is None:
            continue
        params[k] = str(v)
    return f"{API_ROOT}/{fmt}/{method}?{urllib.parse.urlencode(params)}"


def fetch(method: str, identifiers: list[str] | None = None, *, fmt: str = "json",
          species: int | None = DEFAULT_SPECIES, use_cache: bool = True,
          **extra) -> bytes:
    """Low-level call. Returns raw response bytes (JSON, TSV or image)."""
    url = _build_url(fmt, method, identifiers, species, extra)
    cp = _cache_path(url)
    if use_cache and cp.exists():
        return cp.read_bytes()
    _throttle()
    req = urllib.request.Request(url, headers={"User-Agent": f"string-db-skill ({CALLER})"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:300]
        raise StringError(f"STRING {method} HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise StringError(f"STRING {method} unreachable: {e.reason}") from e
    # STRING returns 200 + an error blob for some bad inputs; surface it.
    if fmt == "json" and data[:1] not in (b"[", b"{"):
        raise StringError(f"STRING {method}: unexpected response: {data[:200]!r}")
    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cp.write_bytes(data)
    return data


def fetch_json(method: str, identifiers: list[str] | None = None, **kw) -> list[dict]:
    data = fetch(method, identifiers, fmt="json", **kw)
    return json.loads(data)


# --- High-level helpers ------------------------------------------------------

def map_ids(identifiers: list[str], *, species: int | None = DEFAULT_SPECIES,
            limit: int = 1, **kw) -> list[dict]:
    """Resolve free-text / locus tags to STRING ids (get_string_ids)."""
    return fetch_json("get_string_ids", identifiers, species=species,
                      limit=limit, echo_query=1, **kw)


def _annotate_channels(rows: list[dict]) -> list[dict]:
    """Rename STRING's *score fields to channel names and scale 0..1 -> 0..1000."""
    out = []
    for r in rows:
        rec = {
            "a": r.get("preferredName_A") or r.get("stringId_A"),
            "b": r.get("preferredName_B") or r.get("stringId_B"),
            "stringId_A": r.get("stringId_A"),
            "stringId_B": r.get("stringId_B"),
            "combined": round(float(r.get("score", 0)) * 1000),
        }
        for fld, name in CHANNEL_FIELDS.items():
            rec[name] = round(float(r.get(fld, 0)) * 1000)
        # Context channels = the prokaryote-strong, orthogonal-to-orthology ones.
        rec["context"] = max(rec["neighborhood"], rec["fusion"], rec["cooccurrence"])
        out.append(rec)
    return out


def partners(identifiers: list[str], *, species: int | None = DEFAULT_SPECIES,
             limit: int | None = None, required_score: int | None = None,
             physical: bool = False, **kw) -> list[dict]:
    """Functional (or physical) interaction partners of the query protein(s)."""
    rows = fetch_json("interaction_partners", identifiers, species=species,
                      limit=limit, required_score=required_score,
                      network_type="physical" if physical else "functional", **kw)
    return _annotate_channels(rows)


def network(identifiers: list[str], *, species: int | None = DEFAULT_SPECIES,
            required_score: int | None = None, add_nodes: int | None = None,
            physical: bool = False, **kw) -> list[dict]:
    """Interactions *among* the input set (+ optional extra nodes)."""
    rows = fetch_json("network", identifiers, species=species,
                      required_score=required_score, add_white_nodes=add_nodes,
                      network_type="physical" if physical else "functional", **kw)
    return _annotate_channels(rows)


def enrichment(identifiers: list[str], *, species: int | None = DEFAULT_SPECIES,
               **kw) -> list[dict]:
    """Functional enrichment (GO/KEGG/Pfam/InterPro...) of a gene set, with FDR."""
    rows = fetch_json("enrichment", identifiers, species=species, **kw)
    rows.sort(key=lambda r: float(r.get("fdr", 1.0)))
    return rows


def functional_annotation(identifiers: list[str], *,
                          species: int | None = DEFAULT_SPECIES, **kw) -> list[dict]:
    return fetch_json("functional_annotation", identifiers, species=species, **kw)


def ppi_enrichment(identifiers: list[str], *,
                   species: int | None = DEFAULT_SPECIES, **kw) -> dict:
    """Is the set more densely connected than random (a real complex/pathway)?"""
    rows = fetch_json("ppi_enrichment", identifiers, species=species, **kw)
    return rows[0] if rows else {}


def network_image(identifiers: list[str], dest: Path, *,
                  species: int | None = DEFAULT_SPECIES, highres: bool = False,
                  svg: bool = False, required_score: int | None = None,
                  physical: bool = False, **kw) -> Path:
    """Download a rendered network picture to `dest`."""
    fmt = "svg" if svg else ("highres_image" if highres else "image")
    data = fetch("network", identifiers, fmt=fmt, species=species,
                 required_score=required_score,
                 network_type="physical" if physical else "functional",
                 use_cache=False, **kw)
    dest = Path(dest)
    dest.write_bytes(data)
    return dest
