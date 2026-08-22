#!/usr/bin/env python3
"""Build and query a local IMDb ratings cache.

The script uses IMDb Non-Commercial Datasets:
https://datasets.imdbws.com/title.basics.tsv.gz
https://datasets.imdbws.com/title.ratings.tsv.gz

It intentionally avoids scraping IMDb HTML pages.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import json
import math
import os
import re
import sqlite3
import sys
import tempfile
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence


IMDB_BASICS_URL = "https://datasets.imdbws.com/title.basics.tsv.gz"
IMDB_RATINGS_URL = "https://datasets.imdbws.com/title.ratings.tsv.gz"
DEFAULT_DB = Path("~/.cache/imdb-skill/imdb.sqlite").expanduser()
DEFAULT_CACHE_DIR = Path("~/.cache/imdb-skill/datasets").expanduser()
DEFAULT_TITLE_TYPES = "movie,tvMovie,short"
OMDB_URL = "https://www.omdbapi.com/"
REQUIRED_CACHE_TABLES = {"titles", "ratings", "meta"}
IMDB_ID_RE = re.compile(r"^tt[0-9]{7,}$", re.IGNORECASE)


def normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def none_if_missing(value: str | None) -> str | None:
    if value is None or value == r"\N" or value == "":
        return None
    return value


def parse_int(value: str | None) -> int | None:
    value = none_if_missing(value)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def parse_float(value: str | None) -> float | None:
    value = none_if_missing(value)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def source_is_url(source: str) -> bool:
    return source.startswith("http://") or source.startswith("https://")


def resolve_source(source: str, cache_dir: Path, refresh: bool) -> Path:
    if source_is_url(source):
        cache_dir.mkdir(parents=True, exist_ok=True)
        parsed = urllib.parse.urlparse(source)
        filename = Path(parsed.path).name or "dataset.tsv.gz"
        dest = cache_dir / filename
        if refresh or not dest.exists() or dest.stat().st_size == 0:
            download(source, dest)
        return dest
    if source.startswith("file://"):
        return Path(urllib.parse.urlparse(source).path)
    return Path(source).expanduser()


def download(url: str, dest: Path) -> None:
    print(f"Downloading {url} -> {dest}", file=sys.stderr)
    dest.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "imdb-skill/0.1 (+local non-commercial dataset cache)"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as response:
        with tempfile.NamedTemporaryFile(
            "wb", delete=False, dir=str(dest.parent), prefix=f".{dest.name}.", suffix=".tmp"
        ) as tmp:
            tmp_path = Path(tmp.name)
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                tmp.write(chunk)
    tmp_path.replace(dest)


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", newline="")
    return path.open("rt", encoding="utf-8", newline="")


def connect_db(path: Path) -> sqlite3.Connection:
    path = path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def connect_existing_db(path: Path) -> sqlite3.Connection:
    path = path.expanduser()
    update_hint = f"Run the update command first: imdb_lookup.py update --db {path}"
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"IMDb cache not found at {path}. {update_hint}")
    try:
        conn = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True, timeout=30)
    except sqlite3.Error as exc:
        raise SystemExit(f"Cannot open IMDb cache at {path}: {exc}. {update_hint}") from exc
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    tables = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    missing = sorted(REQUIRED_CACHE_TABLES - tables)
    if missing:
        conn.close()
        raise SystemExit(
            f"IMDb cache at {path} is incomplete (missing: {', '.join(missing)}). "
            f"{update_hint}"
        )
    return conn


def normalize_imdb_id(value: str) -> str:
    imdb_id = value.strip().lower()
    if not IMDB_ID_RE.fullmatch(imdb_id):
        raise SystemExit(
            f"Invalid IMDb id {value!r}; expected a title id such as tt0142688"
        )
    return imdb_id


def cache_built_at(conn: sqlite3.Connection) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key = 'built_at_utc'").fetchone()
    return str(row["value"]) if row else None


def add_cache_provenance(rows: list[dict[str, Any]], conn: sqlite3.Connection) -> None:
    built_at = cache_built_at(conn)
    for row in rows:
        row["cache_built_at_utc"] = built_at


def reset_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS titles;
        DROP TABLE IF EXISTS ratings;
        DROP TABLE IF EXISTS meta;

        CREATE TABLE titles (
            tconst TEXT PRIMARY KEY,
            title_type TEXT NOT NULL,
            primary_title TEXT NOT NULL,
            original_title TEXT,
            is_adult INTEGER,
            start_year INTEGER,
            end_year INTEGER,
            runtime_minutes INTEGER,
            genres TEXT,
            norm_title TEXT NOT NULL
        );

        CREATE TABLE ratings (
            tconst TEXT PRIMARY KEY,
            average_rating REAL,
            num_votes INTEGER
        );

        CREATE TABLE meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )
    conn.commit()


def create_indexes(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_titles_norm ON titles(norm_title);
        CREATE INDEX IF NOT EXISTS idx_titles_year ON titles(start_year);
        CREATE INDEX IF NOT EXISTS idx_titles_type ON titles(title_type);
        CREATE INDEX IF NOT EXISTS idx_ratings_votes ON ratings(num_votes);
        """
    )
    conn.commit()


def iter_tsv(path: Path) -> Iterator[dict[str, str]]:
    with open_text(path) as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            yield row


def load_titles(
    conn: sqlite3.Connection,
    basics_path: Path,
    title_types: set[str],
    include_adult: bool,
    batch_size: int = 10000,
) -> int:
    sql = """
        INSERT INTO titles
        (tconst, title_type, primary_title, original_title, is_adult, start_year,
         end_year, runtime_minutes, genres, norm_title)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    batch: list[tuple[Any, ...]] = []
    total = 0
    for row in iter_tsv(basics_path):
        title_type = row.get("titleType") or ""
        if title_type not in title_types:
            continue
        is_adult = parse_int(row.get("isAdult")) or 0
        if is_adult and not include_adult:
            continue
        primary_title = none_if_missing(row.get("primaryTitle")) or ""
        norm = normalize_title(primary_title)
        if not norm:
            continue
        batch.append(
            (
                row.get("tconst"),
                title_type,
                primary_title,
                none_if_missing(row.get("originalTitle")),
                is_adult,
                parse_int(row.get("startYear")),
                parse_int(row.get("endYear")),
                parse_int(row.get("runtimeMinutes")),
                none_if_missing(row.get("genres")),
                norm,
            )
        )
        if len(batch) >= batch_size:
            conn.executemany(sql, batch)
            conn.commit()
            total += len(batch)
            print(f"Loaded titles: {total}", file=sys.stderr)
            batch.clear()
    if batch:
        conn.executemany(sql, batch)
        conn.commit()
        total += len(batch)
    return total


def load_ratings(conn: sqlite3.Connection, ratings_path: Path, batch_size: int = 10000) -> int:
    sql = "INSERT INTO ratings (tconst, average_rating, num_votes) VALUES (?, ?, ?)"
    batch: list[tuple[Any, ...]] = []
    total = 0
    for row in iter_tsv(ratings_path):
        batch.append(
            (
                row.get("tconst"),
                parse_float(row.get("averageRating")),
                parse_int(row.get("numVotes")),
            )
        )
        if len(batch) >= batch_size:
            conn.executemany(sql, batch)
            conn.commit()
            total += len(batch)
            print(f"Loaded ratings: {total}", file=sys.stderr)
            batch.clear()
    if batch:
        conn.executemany(sql, batch)
        conn.commit()
        total += len(batch)
    return total


def update_cache(args: argparse.Namespace) -> None:
    db_path = Path(args.db).expanduser()
    cache_dir = Path(args.cache_dir).expanduser()
    basics = resolve_source(args.basics_source, cache_dir, args.refresh)
    ratings = resolve_source(args.ratings_source, cache_dir, args.refresh)
    title_types = {item.strip() for item in args.title_types.split(",") if item.strip()}
    conn = connect_db(db_path)
    reset_schema(conn)
    titles_count = load_titles(conn, basics, title_types, args.include_adult)
    ratings_count = load_ratings(conn, ratings)
    create_indexes(conn)
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    conn.executemany(
        "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
        [
            ("built_at_utc", now),
            ("basics_source", str(basics)),
            ("ratings_source", str(ratings)),
            ("title_types", ",".join(sorted(title_types))),
            ("include_adult", str(bool(args.include_adult))),
            ("titles_count", str(titles_count)),
            ("ratings_count", str(ratings_count)),
        ],
    )
    conn.commit()
    print(
        json.dumps(
            {
                "db": str(db_path),
                "built_at_utc": now,
                "titles_count": titles_count,
                "ratings_count": ratings_count,
            },
            ensure_ascii=False,
        )
    )


SELECT_FIELDS = """
    t.tconst,
    t.title_type,
    t.primary_title,
    t.original_title,
    t.start_year,
    t.runtime_minutes,
    t.genres,
    t.norm_title,
    r.average_rating,
    r.num_votes
"""


def row_to_dict(row: sqlite3.Row, score: float | None = None) -> dict[str, Any]:
    item = dict(row)
    item["imdb_url"] = f"https://www.imdb.com/title/{item['tconst']}/"
    if score is not None:
        item["match_score"] = round(score, 3)
    return item


def score_candidate(row: sqlite3.Row, query_norm: str, year: int | None) -> float:
    score = 0.0
    if row["norm_title"] == query_norm:
        score += 100.0
    elif query_norm and query_norm in row["norm_title"]:
        score += 65.0
    else:
        q_tokens = set(query_norm.split())
        r_tokens = set((row["norm_title"] or "").split())
        if q_tokens:
            score += 50.0 * (len(q_tokens & r_tokens) / len(q_tokens))
    if year is not None and row["start_year"] is not None:
        diff = abs(int(row["start_year"]) - year)
        score += max(0.0, 35.0 - diff * 7.0)
    votes = row["num_votes"] or 0
    if votes:
        score += min(25.0, math.log10(votes + 1) * 4.0)
    rating = row["average_rating"]
    if rating is not None:
        score += float(rating)
    if row["title_type"] == "movie":
        score += 3.0
    return score


def parse_types(value: str | None) -> set[str] | None:
    if not value:
        return None
    return {item.strip() for item in value.split(",") if item.strip()}


def lookup_rows(
    conn: sqlite3.Connection,
    title: str | None,
    imdb_id: str | None,
    year: int | None,
    limit: int,
    min_votes: int,
    title_types: set[str] | None,
) -> list[dict[str, Any]]:
    params: list[Any] = []
    where: list[str] = []
    if imdb_id:
        imdb_id = normalize_imdb_id(imdb_id)
        where.append("t.tconst = ?")
        params.append(imdb_id)
    else:
        if not title:
            raise SystemExit("lookup requires --imdb-id or a title")
        query_norm = normalize_title(title)
        if not query_norm:
            raise SystemExit("empty normalized title")
        exact_where = ["t.norm_title = ?"]
        exact_params: list[Any] = [query_norm]
        if title_types:
            exact_where.append("t.title_type IN (%s)" % ",".join("?" for _ in title_types))
            exact_params.extend(sorted(title_types))
        if min_votes:
            exact_where.append("(r.num_votes IS NOT NULL AND r.num_votes >= ?)")
            exact_params.append(min_votes)
        exact = query_candidates(conn, exact_where, exact_params, max(limit * 5, 25))
        if exact:
            scored = [(score_candidate(row, query_norm, year), row) for row in exact]
            scored.sort(key=lambda x: x[0], reverse=True)
            return [row_to_dict(row, score) for score, row in scored[:limit]]
        tokens = [token for token in query_norm.split() if len(token) > 1]
        if not tokens:
            tokens = [query_norm]
        for token in tokens[:5]:
            where.append("t.norm_title LIKE ?")
            params.append(f"%{token}%")
    if title_types:
        where.append("t.title_type IN (%s)" % ",".join("?" for _ in title_types))
        params.extend(sorted(title_types))
    if min_votes:
        where.append("(r.num_votes IS NOT NULL AND r.num_votes >= ?)")
        params.append(min_votes)
    rows = query_candidates(conn, where, params, max(limit * 10, 50))
    if imdb_id:
        return [row_to_dict(row, None) for row in rows[:limit]]
    query_norm = normalize_title(title or "")
    scored = [(score_candidate(row, query_norm, year), row) for row in rows]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [row_to_dict(row, score) for score, row in scored[:limit]]


def query_candidates(
    conn: sqlite3.Connection, where: Sequence[str], params: Sequence[Any], limit: int
) -> list[sqlite3.Row]:
    if not where:
        raise SystemExit("internal error: empty lookup where clause")
    sql = f"""
        SELECT {SELECT_FIELDS}
        FROM titles t
        LEFT JOIN ratings r ON r.tconst = t.tconst
        WHERE {" AND ".join(where)}
        ORDER BY COALESCE(r.num_votes, 0) DESC, COALESCE(r.average_rating, 0) DESC
        LIMIT ?
    """
    return list(conn.execute(sql, [*params, limit]))


def print_output(rows: list[dict[str, Any]], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    fields = [
        "input_title",
        "input_year",
        "input_imdb_id",
        "tconst",
        "primary_title",
        "start_year",
        "title_type",
        "average_rating",
        "num_votes",
        "runtime_minutes",
        "genres",
        "cache_built_at_utc",
        "imdb_url",
        "match_score",
        "match_error",
    ]
    fields = [field for field in fields if rows and any(field in row for row in rows)]
    if fmt == "tsv":
        print("\t".join(fields))
        for row in rows:
            print("\t".join("" if row.get(k) is None else str(row.get(k)) for k in fields))
        return
    if not rows:
        print("No match")
        return
    for row in rows:
        rating = row.get("average_rating")
        votes = row.get("num_votes")
        year = row.get("start_year") or "?"
        runtime = row.get("runtime_minutes") or "?"
        score = row.get("match_score")
        score_text = f" score={score}" if score is not None else ""
        cache_text = f" cache={row.get('cache_built_at_utc') or '?'}"
        print(
            f"{row['tconst']} | {row['primary_title']} ({year}) | "
            f"{row['title_type']} | IMDb {rating or '?'} ({votes or 0} votes) | "
            f"{runtime} min | {row.get('genres') or '?'} | "
            f"{row['imdb_url']}{score_text}{cache_text}"
        )


def lookup_command(args: argparse.Namespace) -> None:
    conn = connect_existing_db(Path(args.db).expanduser())
    try:
        rows = lookup_rows(
            conn,
            title=args.title,
            imdb_id=args.imdb_id,
            year=args.year,
            limit=args.limit,
            min_votes=args.min_votes,
            title_types=parse_types(args.title_types),
        )
        add_cache_provenance(rows, conn)
        print_output(rows, args.format)
    finally:
        conn.close()


def batch_command(args: argparse.Namespace) -> None:
    conn = connect_existing_db(Path(args.db).expanduser())
    input_path = Path(args.input).expanduser()
    rows_out: list[dict[str, Any]] = []
    with input_path.open("rt", encoding="utf-8", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters="\t,;")
        reader = csv.DictReader(handle, dialect=dialect)
        for row in reader:
            title = row.get("title") or row.get("titre") or row.get("film")
            imdb_id = row.get("imdb_id") or row.get("tconst") or None
            year = parse_int(row.get("year") or row.get("annee"))
            matches = lookup_rows(
                conn,
                title=title,
                imdb_id=imdb_id,
                year=year,
                limit=1,
                min_votes=args.min_votes,
                title_types=parse_types(args.title_types),
            )
            prefix = {
                "input_title": title or "",
                "input_year": year if year is not None else "",
                "input_imdb_id": imdb_id or "",
            }
            if matches:
                out = {**prefix, **matches[0]}
            else:
                out = {**prefix, "match_error": "no_match"}
            rows_out.append(out)
    add_cache_provenance(rows_out, conn)
    conn.close()
    print_output(rows_out, args.format)


def omdb_command(args: argparse.Namespace) -> None:
    api_key = os.environ.get("OMDB_API_KEY")
    if not api_key:
        raise SystemExit("OMDB_API_KEY is required in the environment")
    if not args.imdb_id:
        raise SystemExit("--imdb-id is required for OMDb lookup")
    params = {
        "i": normalize_imdb_id(args.imdb_id),
        "apikey": api_key,
        "plot": args.plot,
        "r": "json",
    }
    url = OMDB_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "imdb-skill/0.1"})
    with urllib.request.urlopen(req, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def meta_command(args: argparse.Namespace) -> None:
    conn = connect_existing_db(Path(args.db).expanduser())
    rows = conn.execute("SELECT key, value FROM meta ORDER BY key").fetchall()
    conn.close()
    print(json.dumps({row["key"]: row["value"] for row in rows}, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite cache path")
    sub = parser.add_subparsers(dest="command", required=True)

    update = sub.add_parser("update", help="download datasets and rebuild the SQLite cache")
    update.add_argument("--db", default=str(DEFAULT_DB), help="SQLite cache path")
    update.add_argument("--cache-dir", default=str(DEFAULT_CACHE_DIR), help="dataset cache directory")
    update.add_argument("--basics-source", default=IMDB_BASICS_URL, help="URL or local path")
    update.add_argument("--ratings-source", default=IMDB_RATINGS_URL, help="URL or local path")
    update.add_argument("--title-types", default=DEFAULT_TITLE_TYPES, help="comma-separated titleType list")
    update.add_argument("--include-adult", action="store_true", help="include rows marked isAdult=1")
    update.add_argument("--refresh", action="store_true", help="redownload remote sources")
    update.set_defaults(func=update_cache)

    lookup = sub.add_parser("lookup", help="lookup one title or IMDb id")
    lookup.add_argument("title", nargs="?", help="film title")
    lookup.add_argument("--db", default=str(DEFAULT_DB), help="SQLite cache path")
    lookup.add_argument("--imdb-id", help="IMDb id, for example tt0142688")
    lookup.add_argument("--year", type=int, help="release year hint")
    lookup.add_argument("--limit", type=int, default=5, help="number of candidates")
    lookup.add_argument("--min-votes", type=int, default=0, help="minimum IMDb votes")
    lookup.add_argument("--title-types", default=DEFAULT_TITLE_TYPES, help="comma-separated titleType list")
    lookup.add_argument("--format", choices=["table", "tsv", "json"], default="table")
    lookup.set_defaults(func=lookup_command)

    batch = sub.add_parser("batch", help="lookup a TSV/CSV list with title/year columns")
    batch.add_argument("input", help="input TSV/CSV")
    batch.add_argument("--db", default=str(DEFAULT_DB), help="SQLite cache path")
    batch.add_argument("--min-votes", type=int, default=0, help="minimum IMDb votes")
    batch.add_argument("--title-types", default=DEFAULT_TITLE_TYPES, help="comma-separated titleType list")
    batch.add_argument("--format", choices=["tsv", "json"], default="tsv")
    batch.set_defaults(func=batch_command)

    omdb = sub.add_parser("omdb", help="fetch optional OMDb metadata by IMDb id")
    omdb.add_argument("--imdb-id", required=True, help="IMDb id, for example tt0142688")
    omdb.add_argument("--plot", choices=["short", "full"], default="short")
    omdb.set_defaults(func=omdb_command)

    meta = sub.add_parser("meta", help="show cache metadata")
    meta.add_argument("--db", default=str(DEFAULT_DB), help="SQLite cache path")
    meta.set_defaults(func=meta_command)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
