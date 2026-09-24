"""Generic resilient client base for file-based external datasets (stdlib-only).

This is the FROZEN HARDENING TEMPLATE for the Guyeux-group data-access skills
(aadr, seshat, orbis, slavevoyages, d-place, glottolog, ...). It is *vendored*
(copied verbatim) into each skill's package; the skill then subclasses
``FileDatasetClient`` and supplies only what differs:

  - ``SNAPSHOTS``       dict[str, Snapshot]   version -> pinned source
  - ``DEFAULT_VERSION`` str
  - ``SCHEMA``          dict[str, list[str]]  stable name -> [candidate raw columns]
  - one or more query methods (``cohort()``, ``polities()``, ...) on ``read_rows()``

Design contract (identical across every data-access skill, which is what makes
this a template and not a one-off):

  resolve_dataset()   env override -> cache -> download(+sha256) -> fixture
                      -> DatasetUnavailable(actionable message)
  read_rows()         resolve + parse (.tsv/.csv, optionally .gz / .zip member)
                      + rename to STABLE column names (version-drift tolerant)
  offline mode        ``<SLUG>_OFFLINE=1`` forbids the network; cache/fixture only
  reproducibility     version is pinned; ``<SLUG>_FILE=/path`` overrides explicitly;
                      ``<SLUG>_CACHE_DIR`` relocates the cache

No third-party dependency: only ``csv/json/gzip/zipfile/urllib/hashlib``. pandas
is never required (``read_rows`` returns ``list[dict]``); a skill MAY add a pandas
convenience behind a guarded import, but the stdlib path must always work so the
skill runs on the bare system Python with nothing to pip-install.

HOW TO INSTANTIATE A NEW SKILL (worked twice in aadr/ and seshat/):
  1. copy this file unchanged into ``src/<slug>_client/_base.py``
  2. write ``sources.py`` (SNAPSHOTS + DEFAULT_VERSION) and ``schema.py`` (SCHEMA)
  3. write ``client.py``: ``class XClient(FileDatasetClient)`` with __init__ wiring
     slug/snapshots/schema/fixture, plus the domain query method(s)
  4. drop a tiny real sample in ``fixtures/<slug>_sample.tsv`` (a leading ``#``
     comment line is allowed and ignored by the parser)
  5. copy ``__main__.py`` / ``smoke_test.py`` and adjust the command names
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import os
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator


USER_AGENT = "guyeux-dataset-client/1.0 (academic research)"


class DatasetError(Exception):
    """Base exception for data-access skills."""


class DatasetUnavailable(DatasetError):
    """No usable local file, no cache, no fixture, and no (working) download.

    Caller skills should catch this and degrade explicitly (e.g. report that the
    dataset must be downloaded and pinned) rather than crash.
    """


class SchemaDrift(DatasetError):
    """A column the skill maps in SCHEMA is absent from the resolved file.

    Usually means the snapshot version changed its column names; pin the version
    that the SCHEMA was written against, or update SCHEMA.
    """


@dataclass(frozen=True)
class Snapshot:
    """A pinned, reproducible release of an external dataset."""

    version: str
    url: str | None = None        # direct download URL; None => manual download only
    sha256: str | None = None     # integrity anchor of the downloaded bytes; None => unverified
    member: str | None = None     # member to extract when the download is a .zip
    filename: str | None = None    # cache filename; defaults to "<slug>.data"
    doi: str = ""
    license: str = ""


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class FileDatasetClient:
    """Resilient, stdlib-only reader for a version-pinned tabular dataset.

    Subclasses set the four class-data arguments and add query methods that call
    :meth:`read_rows`.
    """

    slug: str
    snapshots: dict
    default_version: str
    schema: dict
    fixture: Path | None = None
    delimiter: str = "\t"
    quoting: int = csv.QUOTE_MINIMAL
    cache_root: Path | None = None
    version: str | None = None
    offline: bool | None = None
    last_source: str | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        env = self.slug.upper().replace("-", "_")
        self._env = env
        self.version = self.version or os.environ.get(f"{env}_VERSION") or self.default_version
        if self.offline is None:
            self.offline = os.environ.get(f"{env}_OFFLINE", "0") == "1"
        root = self.cache_root or os.environ.get(f"{env}_CACHE_DIR") or f"~/.cache/{self.slug}"
        self.cache_root = Path(root).expanduser()
        if self.fixture is not None:
            self.fixture = Path(self.fixture)

    # ── snapshot resolution ─────────────────────────────────────────────────

    @property
    def snapshot(self) -> Snapshot:
        try:
            return self.snapshots[self.version]
        except KeyError:
            known = ", ".join(sorted(self.snapshots)) or "(none)"
            raise DatasetError(
                f"unknown {self.slug} version {self.version!r}; known: {known}"
            )

    def _cache_file(self, snap: Snapshot) -> Path:
        assert self.cache_root is not None and self.version is not None  # set in __post_init__
        return self.cache_root / self.version / (snap.filename or f"{self.slug}.data")

    def resolve_dataset(self, *, allow_download: bool = True) -> Path:
        """Return a concrete local file to parse, by the resilience cascade.

        Order: ``<SLUG>_FILE`` override -> disk cache -> download -> fixture
        -> raise DatasetUnavailable. Sets ``self.last_source`` to one of
        ``env|cache|download|fixture``.
        """
        override = os.environ.get(f"{self._env}_FILE")
        if override:
            p = Path(override).expanduser()
            if not p.exists():
                raise DatasetUnavailable(f"{self._env}_FILE={override} does not exist")
            self.last_source = "env"
            return p

        snap = self.snapshot
        cache_file = self._cache_file(snap)
        if cache_file.exists():
            # Verify integrity only when the cached file IS the raw download
            # (no zip extraction) and a hash is pinned.
            if snap.sha256 and snap.member is None:
                got = sha256_of(cache_file)
                if got != snap.sha256:
                    raise DatasetError(
                        f"sha256 mismatch for cached {cache_file} "
                        f"(got {got[:12]}, expected {snap.sha256[:12]})"
                    )
            self.last_source = "cache"
            return cache_file

        if snap.url and allow_download and not self.offline:
            self._download_to(cache_file, snap)
            self.last_source = "download"
            return cache_file

        if self.fixture and self.fixture.exists():
            self.last_source = "fixture"
            return self.fixture

        raise DatasetUnavailable(self._howto(snap, cache_file))

    def _howto(self, snap: Snapshot, cache_file: Path) -> str:
        lines = [
            f"{self.slug}: no usable data for version {self.version!r}.",
            f"Expected a local file at: {cache_file}",
        ]
        if snap.url:
            lines.append(f"Download it from: {snap.url}")
        if snap.doi:
            lines.append(f"DOI: {snap.doi}")
        lines.append(
            f"Or point the skill at an already-downloaded file: "
            f"export {self._env}_FILE=/path/to/file"
        )
        if self.offline:
            lines.append("(offline mode is on; remote download was skipped)")
        return "\n".join(lines)

    def _download_to(self, cache_file: Path, snap: Snapshot) -> None:
        if not snap.url:
            raise DatasetUnavailable(f"{self.slug} {self.version}: no download URL for this snapshot")
        req = urllib.request.Request(snap.url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise DatasetUnavailable(f"download failed for {snap.url}: {exc}") from exc

        if snap.sha256:
            got = hashlib.sha256(raw).hexdigest()
            if got != snap.sha256:
                raise DatasetError(
                    f"sha256 mismatch on download of {snap.url} "
                    f"(got {got[:12]}, expected {snap.sha256[:12]})"
                )

        payload = raw
        if snap.member:
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                payload = zf.read(snap.member)

        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_bytes(payload)

    # ── parsing ──────────────────────────────────────────────────────────────

    def _open_text(self, path: Path):
        if str(path).endswith(".gz"):
            return io.TextIOWrapper(gzip.open(path, "rb"), encoding="utf-8", errors="replace")
        return path.open("r", encoding="utf-8", errors="replace", newline="")

    def _iter_raw(self, path: Path) -> Iterator[dict]:
        """Yield one dict per data row. For .csv/.tsv (optionally .gz) lines
        starting with ``#`` are skipped (fixtures self-document) and the first
        non-comment line is the header; .xlsx is read via a stdlib reader."""
        if str(path).endswith(".xlsx"):
            yield from self._iter_xlsx(path)
            return
        with self._open_text(path) as fh:
            rows = (ln for ln in fh if not ln.lstrip().startswith("#"))
            reader = csv.reader(rows, delimiter=self.delimiter, quoting=self.quoting)  # type: ignore[arg-type]
            header: list[str] | None = None
            for parts in reader:
                if header is None:
                    header = [c.strip() for c in parts]
                    continue
                if not parts:
                    continue
                yield dict(zip(header, parts))

    @staticmethod
    def _col_index(letters: str) -> int:
        """Excel column letters -> 0-based index ('A'->0, 'AA'->26)."""
        n = 0
        for ch in letters:
            if ch.isalpha():
                n = n * 26 + (ord(ch.upper()) - ord("A") + 1)
        return n - 1

    def _iter_xlsx(self, path: Path) -> Iterator[dict]:
        """Minimal stdlib .xlsx reader (first worksheet). Handles shared and
        inline strings; numbers come through as their text. No third-party dep.
        Many historical/archaeological snapshots ship as .xlsx (e.g. Seshat
        Social Complexity), so this lives in the shared base."""
        import xml.etree.ElementTree as ET

        def local(tag: str) -> str:
            return tag.split("}")[-1]

        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            shared: list[str] = []
            if "xl/sharedStrings.xml" in names:
                sroot = ET.fromstring(zf.read("xl/sharedStrings.xml"))
                for si in sroot:
                    shared.append("".join(
                        t.text or "" for t in si.iter() if local(t.tag) == "t"))
            sheet = next((n for n in names
                          if n.startswith("xl/worksheets/") and n.endswith(".xml")), None)
            if sheet is None:
                return
            wroot = ET.fromstring(zf.read(sheet))
            header: list[str] | None = None
            for row in wroot.iter():
                if local(row.tag) != "row":
                    continue
                cells: dict[int, str] = {}
                maxi = -1
                for c in row:
                    if local(c.tag) != "c":
                        continue
                    idx = self._col_index("".join(ch for ch in c.attrib.get("r", "") if ch.isalpha()))
                    ctype = c.attrib.get("t")
                    vtext: str | None = None
                    for child in c:
                        ln = local(child.tag)
                        if ln == "v":
                            vtext = child.text
                        elif ln == "is":
                            vtext = "".join(tt.text or "" for tt in child.iter()
                                            if local(tt.tag) == "t")
                    if ctype == "s" and vtext is not None and vtext.isdigit():
                        val = shared[int(vtext)]
                    else:
                        val = vtext if vtext is not None else ""
                    cells[idx] = val
                    if idx > maxi:
                        maxi = idx
                values = [cells.get(i, "") for i in range(maxi + 1)]
                if header is None:
                    header = [h.strip() for h in values]
                    continue
                while len(values) < len(header):
                    values.append("")
                yield dict(zip(header, values))

    def _resolve_header(self, header: list[str]) -> dict[str, str | None]:
        """Map each stable name to an actual column from ``header``.

        For each ``stable -> [candidate, ...]`` entry, try an exact header match
        first, then a case-insensitive substring match, so a terse pinned name
        like ``"Date mean in BP"`` still matches a verbose real-world header
        (``"Date mean in BP in years before 1950 CE ..."``) and a renamed column
        is caught by listing both names as candidates.
        """
        mapping: dict[str, str | None] = {}
        for stable, candidates in self.schema.items():
            found: str | None = None
            for cand in candidates:
                if cand in header:
                    found = cand
                    break
            if found is None:
                for cand in candidates:
                    needle = cand.lower()
                    for h in header:
                        if needle in h.lower():
                            found = h
                            break
                    if found is not None:
                        break
            mapping[stable] = found
        return mapping

    def _check_schema(self, mapping: dict, required: Iterable[str]) -> None:
        missing = [s for s in required if mapping.get(s) is None]
        if missing:
            raise SchemaDrift(
                f"{self.slug} {self.version}: could not locate column(s) for {missing}. "
                f"The snapshot schema may have drifted; pin the matching version, add "
                f"candidates to SCHEMA, or run `inspect` to print the actual header."
            )

    def read_rows(self, *, allow_download: bool = True,
                  required: Iterable[str] | None = None) -> list[dict]:
        """Resolve the dataset and return rows keyed by STABLE column names.

        Only columns declared in ``SCHEMA`` are kept (renamed to their stable
        names), so downstream consumers never break on a version's column rename.
        ``required`` (default: every stable name) is the subset that must be
        present; a missing required column raises :class:`SchemaDrift`.
        """
        path = self.resolve_dataset(allow_download=allow_download)
        req = list(self.schema.keys()) if required is None else list(required)
        out: list[dict] = []
        mapping: dict[str, str | None] | None = None
        for raw in self._iter_raw(path):
            if mapping is None:
                mapping = self._resolve_header(list(raw.keys()))
                self._check_schema(mapping, req)
            out.append({stable: (raw.get(col) if col else None)
                        for stable, col in mapping.items()})
        return out

    def header_of(self, *, allow_download: bool = False) -> list[str]:
        """Return the raw column header of the resolved file (powers `inspect`)."""
        for raw in self._iter_raw(self.resolve_dataset(allow_download=allow_download)):
            return list(raw.keys())
        return []

    # ── small filtering helpers for subclasses ───────────────────────────────

    @staticmethod
    def as_float(value) -> float | None:
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            return None

    @staticmethod
    def write_tsv(rows: list[dict], columns: list[str], out) -> None:
        """Write rows as a TSV to a path or open file (stable output contract)."""
        close = False
        if isinstance(out, (str, Path)):
            fh = open(out, "w", encoding="utf-8", newline="")
            close = True
        else:
            fh = out
        try:
            w = csv.writer(fh, delimiter="\t", lineterminator="\n")
            w.writerow(columns)
            for r in rows:
                w.writerow([r.get(c, "") for c in columns])
        finally:
            if close:
                fh.close()
