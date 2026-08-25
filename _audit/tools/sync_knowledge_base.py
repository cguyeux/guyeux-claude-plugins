#!/usr/bin/env python3
"""Audit et staging CCX-04 de la base de connaissances Claude/Codex.

Le script compare ``~/.claude/knowledge`` et ``~/.Codex/knowledge`` puis
produit un rapport versionne. Avec ``--apply``, il materialise une source
canonique neutre sous ``~/.agents/knowledge`` sans supprimer ni remplacer les
vues Claude/Codex existantes.

Pour les fichiers presents d'un seul cote, la copie canonique reprend le fichier
source. Pour les fichiers homologues divergents, la copie canonique conserve les
deux contenus dans un fichier de staging marque ``needs-human-dedup``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
JSON_OUT = ROOT / "_audit" / "knowledge_base_report.json"
MD_OUT = ROOT / "_audit" / "knowledge_base_report.md"
EXCLUDED_NAMES = {".git", "__pycache__", ".venv", "venv"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def included_files(root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    if not root.is_dir():
        return files
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in EXCLUDED_NAMES for part in relative.parts):
            continue
        if path.suffix in EXCLUDED_SUFFIXES:
            continue
        files[str(relative)] = path
    return files


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    return {
        "sha256": sha256(path),
        "size": path.stat().st_size,
        "lines": len(path.read_text(encoding="utf-8", errors="replace").splitlines())
        if path.suffix.lower() in {".md", ".txt", ".tsv", ".csv", ".json", ".yaml", ".yml"}
        else None,
    }


def classify(claude_files: dict[str, Path], codex_files: dict[str, Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    all_relatives = sorted(set(claude_files) | set(codex_files))
    for relative in all_relatives:
        claude_path = claude_files.get(relative)
        codex_path = codex_files.get(relative)
        if claude_path is not None and codex_path is not None:
            status = "common-identical" if sha256(claude_path) == sha256(codex_path) else "common-divergent"
        elif claude_path is not None:
            status = "claude-only"
        else:
            status = "codex-only"
        rows.append(
            {
                "path": relative,
                "status": status,
                "claude": file_record(claude_path) if claude_path is not None else None,
                "codex": file_record(codex_path) if codex_path is not None else None,
            }
        )
    return rows


def build_report(claude_root: Path, codex_root: Path, canonical_root: Path) -> dict[str, Any]:
    claude_files = included_files(claude_root)
    codex_files = included_files(codex_root)
    canonical_files = included_files(canonical_root)
    rows = classify(claude_files, codex_files)
    summary: dict[str, int] = {}
    for row in rows:
        summary[row["status"]] = summary.get(row["status"], 0) + 1
    canonical_missing = sorted({row["path"] for row in rows} - set(canonical_files))
    canonical_extra = sorted(set(canonical_files) - {row["path"] for row in rows})
    return {
        "claude_root": str(claude_root),
        "codex_root": str(codex_root),
        "canonical_root": str(canonical_root),
        "total_union": len(rows),
        "summary": dict(sorted(summary.items())),
        "canonical": {
            "files": len(canonical_files),
            "missing_from_canonical": canonical_missing,
            "extra_in_canonical": canonical_extra,
        },
        "rows": rows,
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Rapport CCX-04 base de connaissances Claude/Codex",
        "",
        "Ce fichier est genere par `_audit/tools/sync_knowledge_base.py`.",
        "Il compare les vues `~/.claude/knowledge` et `~/.Codex/knowledge`, puis controle la source neutre `~/.agents/knowledge`.",
        "",
        f"- Total union : {report['total_union']}",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key} : {value}")
    lines.extend(
        [
            f"- Fichiers canoniques : {report['canonical']['files']}",
            f"- Manquants du canonique : {len(report['canonical']['missing_from_canonical'])}",
            f"- Extras dans le canonique : {len(report['canonical']['extra_in_canonical'])}",
            "",
            "| chemin | statut | lignes Claude | lignes Codex |",
            "|---|---|---:|---:|",
        ]
    )
    for row in report["rows"]:
        claude_lines = row["claude"]["lines"] if row["claude"] else ""
        codex_lines = row["codex"]["lines"] if row["codex"] else ""
        lines.append(f"| {row['path']} | {row['status']} | {claude_lines} | {codex_lines} |")
    lines.append("")
    return "\n".join(lines)


def expected_outputs(report: dict[str, Any]) -> tuple[str, str]:
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n", markdown(report)


def merge_text(relative: str, claude_path: Path, codex_path: Path) -> str:
    claude_text = claude_path.read_text(encoding="utf-8", errors="replace").rstrip()
    codex_text = codex_path.read_text(encoding="utf-8", errors="replace").rstrip()
    return "\n".join(
        [
            "<!--",
            "CCX-04 canonical knowledge staging.",
            f"path: {relative}",
            "status: needs-human-dedup",
            "source-1: ~/.claude/knowledge",
            "source-2: ~/.Codex/knowledge",
            "This file preserves both divergent sources until manual reconciliation.",
            "-->",
            "",
            "<!-- BEGIN CLAUDE KNOWLEDGE SOURCE -->",
            claude_text,
            "<!-- END CLAUDE KNOWLEDGE SOURCE -->",
            "",
            "<!-- BEGIN CODEX KNOWLEDGE SOURCE -->",
            codex_text,
            "<!-- END CODEX KNOWLEDGE SOURCE -->",
            "",
        ]
    )


def materialize(report: dict[str, Any]) -> dict[str, int]:
    claude_root = Path(report["claude_root"])
    codex_root = Path(report["codex_root"])
    canonical_root = Path(report["canonical_root"])
    counts = {"copied": 0, "merged_staging": 0, "preserved_existing": 0}
    canonical_root.mkdir(parents=True, exist_ok=True)
    for row in report["rows"]:
        target = canonical_root / row["path"]
        if target.exists():
            counts["preserved_existing"] += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        status = row["status"]
        if status in {"claude-only", "common-identical"}:
            shutil.copy2(claude_root / row["path"], target)
            counts["copied"] += 1
        elif status == "codex-only":
            shutil.copy2(codex_root / row["path"], target)
            counts["copied"] += 1
        elif status == "common-divergent":
            target.write_text(merge_text(row["path"], claude_root / row["path"], codex_root / row["path"]), encoding="utf-8")
            counts["merged_staging"] += 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claude-root", type=Path, default=Path.home() / ".claude" / "knowledge")
    parser.add_argument("--codex-root", type=Path, default=Path.home() / ".Codex" / "knowledge")
    parser.add_argument("--canonical-root", type=Path, default=Path.home() / ".agents" / "knowledge")
    parser.add_argument("--apply", action="store_true", help="materialiser ~/.agents/knowledge sans supprimer les vues existantes")
    parser.add_argument("--check", action="store_true", help="echouer si le rapport versionne est stale")
    args = parser.parse_args()

    report = build_report(args.claude_root.expanduser(), args.codex_root.expanduser(), args.canonical_root.expanduser())
    if args.apply:
        counts = materialize(report)
        print(
            "APPLY : copied={copied}, merged_staging={merged_staging}, preserved_existing={preserved_existing}".format(
                **counts
            )
        )
        report = build_report(args.claude_root.expanduser(), args.codex_root.expanduser(), args.canonical_root.expanduser())
    json_text, md_text = expected_outputs(report)
    if args.check:
        stale = []
        if not JSON_OUT.is_file() or JSON_OUT.read_text(encoding="utf-8") != json_text:
            stale.append(str(JSON_OUT.relative_to(ROOT)))
        if not MD_OUT.is_file() or MD_OUT.read_text(encoding="utf-8") != md_text:
            stale.append(str(MD_OUT.relative_to(ROOT)))
        if stale:
            print("STALE: " + ", ".join(stale))
            return 1
    else:
        JSON_OUT.write_text(json_text, encoding="utf-8")
        MD_OUT.write_text(md_text, encoding="utf-8")
    print(f"OK : {report['total_union']} fichiers KB rapportes")
    for key, value in report["summary"].items():
        print(f"{key}: {value}")
    print(f"canonical_missing: {len(report['canonical']['missing_from_canonical'])}")
    print(f"canonical_extra: {len(report['canonical']['extra_in_canonical'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
