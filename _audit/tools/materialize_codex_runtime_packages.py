#!/usr/bin/env python3
"""Materialize low-risk runtime-adapted Codex package candidates."""
from __future__ import annotations

import fnmatch
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_MATRIX = ROOT / "_audit" / "codex_runtime_adaptation_matrix.json"
JSON_OUT = ROOT / "_audit" / "codex_runtime_package_audit.json"
MD_OUT = ROOT / "_audit" / "codex_runtime_package_audit.md"
PACKAGES_ROOT = ROOT / "codex_packages" / "plugins"
MARKETPLACE = ROOT / "codex_packages" / ".agents" / "plugins" / "marketplace.json"
UNSUPPORTED_FRONTMATTER = {"argument-hint", "disable-model-invocation", "user-invocable", "version"}
LOW_RISK_BUCKETS = {
    "codex-mcp-documentation-only",
    "codex-mcp-tool-prerequisite",
    "mcp-narrative-only",
    "claude-branding-only",
}
EXCLUDE_DIRS = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv", "__pycache__", "venv"}
EXCLUDE_GLOBS = {"*.pyc", "*.pyo"}
TEXT_SUFFIXES = {
    ".csv",
    ".geojson",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".tsv",
    ".txt",
    ".yaml",
    ".yml",
}

PACKAGE_METADATA = {
    "bio-bacteria": {
        "display": "Bio Bacteria Direct",
        "short": "Direct bacterial research skills.",
        "long": "Codex package for bacterial research skills already audited for direct, payload, or runtime-adapted packaging.",
    },
    "bio-pathogens": {
        "display": "Bio Pathogens Direct",
        "short": "Direct pathogen research skills.",
        "long": "Codex package for pathogen research skills already audited for direct, payload, or runtime-adapted packaging.",
    },
    "bio-population-genetics": {
        "display": "Bio Population Genetics Direct",
        "short": "Direct population genetics skills.",
        "long": "Codex package for population genetics skills already audited for direct, payload, or runtime-adapted packaging.",
    },
    "maboss": {
        "display": "MaBoSS Direct",
        "short": "Direct MaBoSS modelling skills.",
        "long": "Codex package for MaBoSS modelling skills already audited for direct or runtime-adapted packaging.",
    },
}


def strip_unsupported_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    kept = ["---"]
    skipping = False
    for line in text[3:end].splitlines():
        key = line.split(":", 1)[0] if ":" in line else None
        if key in UNSUPPORTED_FRONTMATTER:
            skipping = True
            continue
        if skipping and line[:1] in " \t":
            continue
        skipping = False
        kept.append(sanitize_frontmatter_value(line))
    kept.append("---")
    return "\n".join(kept) + text[end + 4 :]


def sanitize_frontmatter_value(line: str) -> str:
    if re.match(r"^description:\s*[>|]", line):
        return line
    line = re.sub(r">(\d)", r"more than \1", line)
    line = re.sub(r"<(\d)", r"less than \1", line)
    return line.replace("<->", "to").replace("<", "").replace(">", "")


def adapt_runtime_text(text: str, row: dict[str, Any]) -> str:
    text = strip_unsupported_frontmatter(text)
    text = text.replace("Claude Code", "Codex")
    text = re.sub(
        r"claude mcp add --transport http --scope user\s+([A-Za-z0-9_-]+)\s+(https?://\S+)",
        r"codex mcp add \1 --url \2",
        text,
    )
    text = re.sub(
        r"claude mcp add --scope user\s+([A-Za-z0-9_-]+)\s+(https?://\S+)",
        r"codex mcp add \1 --url \2",
        text,
    )
    text = text.replace("claude mcp list", "codex mcp list")
    if "mcp" in " ".join(row["runtime_issues"]).lower():
        note = (
            "\n## Codex packaging note\n\n"
            "This packaged copy targets Codex. MCP tool names in `allowed-tools` are prerequisites: "
            "verify them with `codex mcp list` in the active profile before relying on live queries.\n"
        )
        if "## Codex packaging note" not in text:
            text = text.rstrip() + "\n" + note
    return text


def clean_text_payload(target: Path) -> None:
    for path in target.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        lines = [line.rstrip(" \t\r") for line in text.splitlines()]
        while lines and lines[-1] == "":
            lines.pop()
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def rows_to_materialize() -> list[dict[str, Any]]:
    matrix = json.loads(RUNTIME_MATRIX.read_text(encoding="utf-8"))
    return [
        row for row in matrix["rows"]
        if row["runtime_bucket"] in LOW_RISK_BUCKETS
    ]


def should_exclude(path: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return True
    return any(fnmatch.fnmatch(path.name, pattern) for pattern in EXCLUDE_GLOBS)


def ignore(_directory: str, names: list[str]) -> set[str]:
    ignored = set()
    for name in names:
        if name in EXCLUDE_DIRS or any(fnmatch.fnmatch(name, pattern) for pattern in EXCLUDE_GLOBS):
            ignored.add(name)
    return ignored


def payload_inventory(source: Path, target: Path | None = None) -> dict[str, Any]:
    copied_files = 0
    copied_bytes = 0
    excluded_files = 0
    excluded_bytes = 0
    excluded_roots: set[str] = set()
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        size = path.stat().st_size
        if should_exclude(relative):
            excluded_files += 1
            excluded_bytes += size
            excluded_parts = [part for part in relative.parts if part in EXCLUDE_DIRS]
            excluded_roots.update(excluded_parts or [relative.parts[0]])
            continue
        copied_files += 1
        copied_bytes += size
    actual_files = None
    actual_bytes = None
    if target is not None and target.is_dir():
        actual_paths = [path for path in target.rglob("*") if path.is_file()]
        actual_files = len(actual_paths)
        actual_bytes = sum(path.stat().st_size for path in actual_paths)
    return {
        "copied_files_expected": copied_files,
        "copied_bytes_expected": copied_bytes,
        "copied_files_actual": actual_files,
        "copied_bytes_actual": actual_bytes,
        "excluded_files": excluded_files,
        "excluded_bytes": excluded_bytes,
        "excluded_roots": sorted(excluded_roots),
    }


def copy_skill(source: Path, target: Path, row: dict[str, Any]) -> None:
    shutil.copytree(source, target, dirs_exist_ok=True, ignore=ignore)
    skill_md = target / "SKILL.md"
    skill_md.write_text(adapt_runtime_text(skill_md.read_text(encoding="utf-8"), row), encoding="utf-8")
    clean_text_payload(target)


def all_package_skill_counts() -> dict[str, int]:
    counts = {}
    for plugin in PACKAGES_ROOT.iterdir():
        skills = plugin / "skills"
        if skills.is_dir():
            counts[plugin.name] = sum(1 for entry in skills.iterdir() if entry.is_dir())
    return counts


def manifest(package_name: str, skill_count: int) -> dict[str, Any]:
    meta = PACKAGE_METADATA[package_name]
    return {
        "name": package_name,
        "version": "0.1.0",
        "description": f"Local Codex package for {skill_count} migrated Claude skills.",
        "author": {"name": "Christophe Guyeux"},
        "skills": "./skills/",
        "interface": {
            "displayName": meta["display"],
            "shortDescription": meta["short"],
            "longDescription": meta["long"],
            "developerName": "Christophe Guyeux",
            "category": "Developer tools",
            "capabilities": [],
            "defaultPrompt": "Use the installed skills with their documented prerequisites and evidence boundaries.",
        },
    }


def marketplace_entry(package_name: str) -> dict[str, Any]:
    return {
        "name": package_name,
        "source": {
            "source": "local",
            "path": f"./plugins/{package_name}",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Developer tools",
    }


def write_audit(rows: list[dict[str, Any]]) -> None:
    JSON_OUT.write_text(json.dumps({"rows": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Audit des paquets runtime Codex",
        "",
        "Ce fichier est genere par `_audit/tools/materialize_codex_runtime_packages.py`.",
        "Il couvre les familles runtime faibles, materialisees avec une note Codex et sans environnements locaux.",
        "",
        "| skill | paquet | famille | fichiers copies | fichiers exclus | racines exclues |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in rows:
        roots = ", ".join(row["audit"]["excluded_roots"]) if row["audit"]["excluded_roots"] else "none"
        lines.append(
            f"| {row['name']} | {row['package_candidate']} | {row['runtime_bucket']} | "
            f"{row['audit']['copied_files_actual']} | {row['audit']['excluded_files']} | {roots} |"
        )
    lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def materialize() -> list[dict[str, Any]]:
    audit_rows: list[dict[str, Any]] = []
    by_package: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows_to_materialize():
        by_package[row["package_candidate"]].append(row)

    for package_name, rows in sorted(by_package.items()):
        if package_name not in PACKAGE_METADATA:
            raise ValueError(f"metadata absente pour le paquet {package_name}")
        package_root = PACKAGES_ROOT / package_name
        skills_root = package_root / "skills"
        (package_root / ".codex-plugin").mkdir(parents=True, exist_ok=True)
        skills_root.mkdir(parents=True, exist_ok=True)
        for row in sorted(rows, key=lambda item: item["name"]):
            source = ROOT / row["canonical_path"]
            target = skills_root / row["name"]
            copy_skill(source, target, row)
            audit_rows.append({**row, "audit": payload_inventory(source, target)})

    counts = all_package_skill_counts()
    for package_name in sorted(by_package):
        package_root = PACKAGES_ROOT / package_name
        (package_root / ".codex-plugin" / "plugin.json").write_text(
            json.dumps(manifest(package_name, counts[package_name]), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (package_root / "README.md").write_text(
            "\n".join([
                f"# {package_name}",
                "",
                "Local Codex package generated from CCX-10 candidates.",
                "",
                "The skills in this package are materialized copies of the canonical Claude plugin repository.",
                "Package-only adaptation removes Codex-incompatible Claude frontmatter fields.",
                "Runtime packaging adds Codex MCP prerequisite notes and neutralizes Claude-specific wording in generated copies.",
                "Local virtual environments, bytecode caches and compiled Python files are excluded.",
                "",
                "Canonical source remains the repository root, not this generated package copy.",
                "",
            ]),
            encoding="utf-8",
        )

    marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    existing = {entry["name"]: entry for entry in marketplace["plugins"]}
    for package_name in sorted(by_package):
        existing[package_name] = marketplace_entry(package_name)
    ordered_names = ["guyeux-phylo-pilot"] + sorted(name for name in existing if name != "guyeux-phylo-pilot")
    marketplace["plugins"] = [existing[name] for name in ordered_names]
    MARKETPLACE.write_text(json.dumps(marketplace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_audit(audit_rows)
    return audit_rows


def main() -> int:
    rows = materialize()
    by_package = CounterLike(row["package_candidate"] for row in rows)
    by_bucket = CounterLike(row["runtime_bucket"] for row in rows)
    print(f"OK : {len(rows)} skills runtime materialises")
    print("package: " + ", ".join(f"{key}={value}" for key, value in by_package.items()))
    print("runtime_bucket: " + ", ".join(f"{key}={value}" for key, value in by_bucket.items()))
    return 0


def CounterLike(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


if __name__ == "__main__":
    raise SystemExit(main())
