#!/usr/bin/env python3
"""Run deterministic smoke tests for imdb_lookup.py without network access.

The caller supplies a disposable work directory. The script never removes files
and refuses to overwrite an existing test database.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
from typing import Sequence


SKILL_DIR = Path(__file__).resolve().parents[1]
LOOKUP_SCRIPT = SKILL_DIR / "scripts" / "imdb_lookup.py"
EXAMPLES_DIR = SKILL_DIR / "examples"


def load_lookup_module():
    spec = importlib.util.spec_from_file_location("imdb_lookup", LOOKUP_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {LOOKUP_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_cli(module, argv: list[str]) -> str:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        result = module.main(argv)
    if result != 0:
        raise AssertionError(f"Command returned {result}: {argv}")
    return output.getvalue()


def smoke_test(work_dir: Path) -> dict[str, object]:
    work_dir.mkdir(parents=True, exist_ok=True)
    db_path = work_dir / "imdb-smoke.sqlite"
    if db_path.exists():
        raise SystemExit(f"Refusing to overwrite existing test database: {db_path}")

    module = load_lookup_module()
    update_payload = json.loads(
        run_cli(
            module,
            [
                "update",
                "--db",
                str(db_path),
                "--basics-source",
                str(EXAMPLES_DIR / "title.basics.tsv"),
                "--ratings-source",
                str(EXAMPLES_DIR / "title.ratings.tsv"),
            ],
        )
    )
    assert update_payload["titles_count"] == 4
    assert update_payload["ratings_count"] == 4

    lookup_payload = json.loads(
        run_cli(
            module,
            [
                "lookup",
                "The Ninth Gate",
                "--year",
                "1999",
                "--db",
                str(db_path),
                "--format",
                "json",
            ],
        )
    )
    assert lookup_payload[0]["tconst"] == "tt0142688"
    assert lookup_payload[0]["cache_built_at_utc"]
    assert len(lookup_payload) == 2

    id_payload = json.loads(
        run_cli(
            module,
            [
                "lookup",
                "--imdb-id",
                "tt0093779",
                "--db",
                str(db_path),
                "--format",
                "json",
            ],
        )
    )
    assert id_payload[0]["primary_title"] == "The Princess Bride"

    batch_output = run_cli(
        module,
        [
            "batch",
            str(EXAMPLES_DIR / "films.tsv"),
            "--db",
            str(db_path),
            "--format",
            "tsv",
        ],
    )
    assert "cache_built_at_utc" in batch_output.splitlines()[0]
    assert "tt0142688" in batch_output
    assert "tt0093779" in batch_output

    missing_db = work_dir / "missing.sqlite"
    try:
        run_cli(
            module,
            ["lookup", "Alien", "--db", str(missing_db), "--format", "json"],
        )
    except SystemExit as exc:
        assert "update command first" in str(exc)
    else:
        raise AssertionError("A missing cache should stop with a rebuild hint")
    assert not missing_db.exists()

    try:
        run_cli(
            module,
            ["lookup", "--imdb-id", "0142688", "--db", str(db_path)],
        )
    except SystemExit as exc:
        assert "Invalid IMDb id" in str(exc)
    else:
        raise AssertionError("An invalid IMDb id should be rejected")

    return {
        "status": "ok",
        "database": str(db_path),
        "checks": 12,
        "network_used": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", required=True, help="new or empty test directory")
    args = parser.parse_args(argv)
    print(json.dumps(smoke_test(Path(args.work_dir).expanduser()), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
