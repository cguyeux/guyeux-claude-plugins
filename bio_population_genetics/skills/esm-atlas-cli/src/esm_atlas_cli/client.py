"""Resilient client for the EvolutionaryScale × BioHub Protein Atlas API.

Endpoints documented at: https://biohub.ai/esm/protein/atlas/api-docs/

Design notes:
- All GET responses are cached on disk (JSON payloads + binary thumbnails).
- TTL is 30 days for stable resources (features, feature meta, cluster info),
  7 days for sequence-derived lookups, configurable via ESM_ATLAS_CACHE_TTL_DAYS.
- Retries: exponential backoff on 502/503/504, 3 attempts.
- Unrecoverable failures raise EsmAtlasUnavailable so caller code can degrade
  gracefully (e.g. fall back to Mycobrowser-only annotation).
- stdlib-only (urllib): no third-party dependency, nothing to pip-install.
- ESM_ATLAS_OFFLINE=1 forces cache-only mode (raises EsmAtlasUnavailable on a
  cache miss instead of hitting the network) for reproducible / offline runs.
- The API is alpha — endpoints may change. Surface the version string seen in
  the first lookup in the client's `last_seen_api_version` attribute.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


BASE_URL = "https://biohub.ai/esm/protein/api/v1alpha1"
DEFAULT_CACHE_DIR = Path(os.environ.get("ESM_ATLAS_CACHE_DIR", "~/.cache/esm-atlas-cli")).expanduser()
LONG_TTL_DAYS = int(os.environ.get("ESM_ATLAS_CACHE_TTL_DAYS", "30"))
SHORT_TTL_DAYS = max(1, LONG_TTL_DAYS // 4)
RETRY_STATUS = {502, 503, 504}
MAX_ATTEMPTS = 3
USER_AGENT = "esm-atlas-cli/0.1 (Guyeux group academic research)"
OFFLINE = os.environ.get("ESM_ATLAS_OFFLINE", "0") == "1"


class _Response:
    """Minimal httpx-like response shim over urllib (stdlib-only).

    Keeps the endpoint methods (which read .status_code/.json()/.text/.content)
    unchanged after the httpx → urllib swap. `headers` stays an
    email.message.Message so case-insensitive .get() still works.
    """

    def __init__(self, status_code: int, headers: Any, content: bytes):
        self.status_code = status_code
        self.headers = headers
        self.content = content

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", "replace")

    def json(self) -> Any:
        return json.loads(self.content)


class EsmAtlasError(Exception):
    """Base exception for ESM Atlas client errors."""


class EsmAtlasUnavailable(EsmAtlasError):
    """Raised when the API cannot be reached after retries.

    Caller-side skills should catch this and degrade to a Mycobrowser-only
    annotation, with an explicit "ESM Atlas unavailable" note in their output.
    """


class EsmAtlasPending(EsmAtlasError):
    """Raised when a batch job is still running past the polling deadline."""

    def __init__(self, job_id: str, *, message: str = "Batch job still pending"):
        super().__init__(f"{message} (job_id={job_id})")
        self.job_id = job_id


def hash_sequence(seq: str) -> str:
    """Atlas content-addressed identifier for an amino-acid sequence."""
    clean = "".join(seq.split()).upper()
    return hashlib.md5(clean.encode("ascii")).hexdigest()


def _cache_path(cache_dir: Path, kind: str, key: str, suffix: str = "json") -> Path:
    sub = cache_dir / kind
    sub.mkdir(parents=True, exist_ok=True)
    return sub / f"{key}.{suffix}"


def _cache_fresh(path: Path, ttl_days: int) -> bool:
    if not path.exists():
        return False
    if ttl_days <= 0:
        return False
    age = time.time() - path.stat().st_mtime
    return age < ttl_days * 86400


@dataclass
class EsmAtlasClient:
    """Thin, defensive wrapper around the alpha Atlas API.

    Example:
        client = EsmAtlasClient()
        data = client.lookup_sequence("MTEEKVS...")
        print(data["topk_features"][:5])
    """

    base_url: str = BASE_URL
    cache_dir: Path = field(default_factory=lambda: DEFAULT_CACHE_DIR)
    timeout: float = 30.0
    long_ttl_days: int = LONG_TTL_DAYS
    short_ttl_days: int = SHORT_TTL_DAYS
    offline: bool = OFFLINE
    last_seen_api_version: str | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.cache_dir = Path(self.cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ── HTTP plumbing (stdlib urllib, no third-party dependency) ────────────

    def close(self) -> None:  # kept for API compatibility; urllib is stateless
        return None

    def __enter__(self) -> "EsmAtlasClient":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def _build_request(self, method: str, url: str, *,
                       json_body: dict | None) -> urllib.request.Request:
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        data = None
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        return urllib.request.Request(url, data=data, method=method, headers=headers)

    def _request(self, method: str, path: str, *, params: dict | None = None,
                 json_body: dict | None = None) -> _Response:
        if self.offline:
            raise EsmAtlasUnavailable(
                "offline mode (ESM_ATLAS_OFFLINE=1); only cached results are served"
            )
        url = self.base_url.rstrip("/") + "/" + path.lstrip("/")
        if params:
            url += "?" + urllib.parse.urlencode(params)
        last_exc: Exception | None = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            req = self._build_request(method, url, json_body=json_body)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    resp = _Response(r.status, r.headers, r.read())
            except urllib.error.HTTPError as exc:
                resp = _Response(exc.code, exc.headers, exc.read())
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_exc = exc
                if attempt == MAX_ATTEMPTS:
                    raise EsmAtlasUnavailable(f"transport error after {attempt} attempts: {exc}") from exc
                time.sleep(2 ** attempt)
                continue

            api_version = resp.headers.get("X-Api-Version") or resp.headers.get("X-API-Version")
            if api_version:
                self.last_seen_api_version = api_version

            if resp.status_code in RETRY_STATUS and attempt < MAX_ATTEMPTS:
                time.sleep(2 ** attempt)
                continue
            return resp

        # Should be unreachable; defensive.
        raise EsmAtlasUnavailable(f"giving up after {MAX_ATTEMPTS} attempts: {last_exc}")

    def _download(self, url: str) -> bytes:
        """GET an absolute URL, returning raw bytes (batch ZIP downloads)."""
        if self.offline:
            raise EsmAtlasUnavailable("offline mode; cannot download")
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise EsmAtlasUnavailable(f"download failed: {exc}") from exc

    def _get_json(self, path: str, *, params: dict | None = None,
                  cache_kind: str | None = None, cache_key: str | None = None,
                  ttl_days: int | None = None) -> dict:
        if cache_kind and cache_key:
            cpath = _cache_path(self.cache_dir, cache_kind, cache_key)
            ttl = self.long_ttl_days if ttl_days is None else ttl_days
            if _cache_fresh(cpath, ttl):
                return json.loads(cpath.read_text())

        resp = self._request("GET", path, params=params)
        if resp.status_code == 404:
            raise EsmAtlasError(f"not found: {path}")
        if resp.status_code >= 400:
            raise EsmAtlasError(f"HTTP {resp.status_code} on {path}: {resp.text[:200]}")
        data = resp.json()

        if cache_kind and cache_key:
            cpath = _cache_path(self.cache_dir, cache_kind, cache_key)
            cpath.write_text(json.dumps(data))
        return data

    # ── Endpoints ──────────────────────────────────────────────────────────

    def lookup(self, protein_hash: str, *, topk_features: int = 10,
               fold_on_miss: bool = False, normalize_features: bool = True) -> dict:
        """GET /proteins/{hash}"""
        return self._get_json(
            f"proteins/{protein_hash}",
            params={
                "topk_features": topk_features,
                "fold_on_miss": str(fold_on_miss).lower(),
                "normalize_features": str(normalize_features).lower(),
            },
            cache_kind="protein",
            cache_key=f"{protein_hash}.topk{topk_features}.norm{int(normalize_features)}",
            ttl_days=self.short_ttl_days,
        )

    def lookup_sequence(self, sequence: str, **kwargs) -> dict:
        """Hash a sequence locally and look it up. Convenience wrapper."""
        return self.lookup(hash_sequence(sequence), **kwargs)

    def similarity_search(self, sequence: str, *, topk_results: int = 25,
                          topk_features: int = 10, min_similarity: float | None = None,
                          cluster_pct_characterized_max: int | None = None,
                          include_cluster_info: bool = True) -> dict:
        """GET /similarity-search"""
        params: dict[str, Any] = {
            "sequence": sequence,
            "topk_results": topk_results,
            "topk_features": topk_features,
            "include_cluster_info": str(include_cluster_info).lower(),
        }
        if min_similarity is not None:
            params["min_similarity"] = min_similarity
        if cluster_pct_characterized_max is not None:
            params["cluster_pct_characterized_max"] = cluster_pct_characterized_max
        key = f"{hash_sequence(sequence)}.k{topk_results}.f{topk_features}"
        return self._get_json("similarity-search", params=params,
                              cache_kind="similarity", cache_key=key,
                              ttl_days=self.short_ttl_days)

    def features(self) -> dict:
        """GET /features — list of all SAE features (index → label)."""
        return self._get_json("features", cache_kind="features", cache_key="index")

    def feature_meta(self, feature_index: int) -> dict:
        """GET /features/{idx} — full SAE feature metadata, activators, stats."""
        return self._get_json(f"features/{feature_index}",
                              cache_kind="features", cache_key=f"meta-{feature_index}")

    def cluster(self, protein_hash: str, *, topk_features: int = 10) -> dict:
        """GET /clusters/{hash}"""
        return self._get_json(
            f"clusters/{protein_hash}",
            params={"topk_features": topk_features},
            cache_kind="cluster",
            cache_key=f"{protein_hash}.k{topk_features}",
        )

    def thumbnail(self, protein_hash: str, thumbnail_type: str = "default") -> bytes:
        """GET /proteins/{hash}/thumbnail/{type} — returns PNG bytes."""
        cpath = _cache_path(self.cache_dir, "thumbnail",
                            f"{protein_hash}.{thumbnail_type}", suffix="png")
        if _cache_fresh(cpath, self.long_ttl_days):
            return cpath.read_bytes()
        resp = self._request("GET", f"proteins/{protein_hash}/thumbnail/{thumbnail_type}")
        if resp.status_code >= 400:
            raise EsmAtlasError(f"HTTP {resp.status_code} on thumbnail")
        cpath.write_bytes(resp.content)
        return resp.content

    def batch_lookup(self, protein_hashes: list[str], *,
                     topk_features: int = 10,
                     include_structure: bool = True,
                     poll_deadline_seconds: int = 300) -> dict | bytes:
        """POST /proteins/batch — synchronous (ZIP bytes) or async (polled).

        Returns ZIP bytes if small enough, otherwise polls until done or raises
        EsmAtlasPending with the job_id.
        """
        if len(protein_hashes) > 500:
            raise ValueError("max 500 hashes per batch")
        body = {
            "protein_hashes": list(dict.fromkeys(protein_hashes)),  # unique, preserve order
            "topk_features": topk_features,
            "include_structure": include_structure,
        }
        resp = self._request("POST", "proteins/batch", json_body=body)
        if resp.status_code == 200:
            return resp.content  # ZIP bytes
        if resp.status_code == 202:
            job_id = resp.json().get("job_id") or resp.json().get("jobId")
            return self._poll_batch(job_id, deadline=poll_deadline_seconds)
        raise EsmAtlasError(f"HTTP {resp.status_code} on batch")

    def _poll_batch(self, job_id: str, *, deadline: int) -> bytes:
        start = time.time()
        delay = 5
        while time.time() - start < deadline:
            resp = self._request("GET", f"proteins/batch/jobs/{job_id}")
            if resp.status_code == 200:
                payload = resp.json()
                download_url = payload.get("download_url") or payload.get("downloadUrl")
                if download_url:
                    return self._download(download_url)
            if resp.status_code == 410:
                raise EsmAtlasError(f"batch job {job_id} expired")
            time.sleep(delay)
            delay = min(delay * 2, 30)
        raise EsmAtlasPending(job_id)

    def cancel_batch(self, job_id: str) -> None:
        """DELETE /proteins/batch/jobs/{job_id} — idempotent."""
        self._request("DELETE", f"proteins/batch/jobs/{job_id}")

    # ── Utilities ──────────────────────────────────────────────────────────

    def mutate_and_compare(self, sequence: str, mutations: list[str],
                           *, topk_features: int = 50) -> dict:
        """Apply point mutations (e.g. ['S315T']) and compare SAE features.

        Returns:
            {
              "wt_hash", "mt_hash",
              "wt_topk": [...], "mt_topk": [...],
              "gained_features": [...],  # indices present in mutant but not WT topk
              "lost_features":   [...],
              "stable_features": [...],
            }
        """
        wt_seq = sequence
        mt_seq = list(sequence)
        for mut in mutations:
            ref, pos_str, alt = mut[0], mut[1:-1], mut[-1]
            pos = int(pos_str)
            if not (1 <= pos <= len(mt_seq)):
                raise ValueError(f"position {pos} out of range")
            if mt_seq[pos - 1] != ref:
                raise ValueError(
                    f"position {pos} is {mt_seq[pos - 1]!r}, not {ref!r}; mutation {mut} invalid"
                )
            mt_seq[pos - 1] = alt
        mt_seq_str = "".join(mt_seq)

        wt = self.lookup_sequence(wt_seq, topk_features=topk_features)
        mt = self.lookup_sequence(mt_seq_str, topk_features=topk_features)

        # The alpha API uses `sae_features` (sometimes `topk_features` in docs).
        # Each entry has an `index` or `feature_index`. Defend against both.
        def _feature_idx(f: dict) -> int | None:
            return f.get("index") or f.get("feature_index")

        wt_feats = wt.get("sae_features") or wt.get("topk_features") or []
        mt_feats = mt.get("sae_features") or mt.get("topk_features") or []
        wt_idxs = {i for f in wt_feats if (i := _feature_idx(f)) is not None}
        mt_idxs = {i for f in mt_feats if (i := _feature_idx(f)) is not None}
        return {
            "wt_hash": hash_sequence(wt_seq),
            "mt_hash": hash_sequence(mt_seq_str),
            "wt_topk": wt_feats,
            "mt_topk": mt_feats,
            "gained_features": sorted(mt_idxs - wt_idxs),
            "lost_features": sorted(wt_idxs - mt_idxs),
            "stable_features": sorted(wt_idxs & mt_idxs),
        }
