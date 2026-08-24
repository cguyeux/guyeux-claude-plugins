#!/usr/bin/env python3
"""Materialize direct Codex package candidates from the CCX-10 matrix."""
from __future__ import annotations

import json
import fnmatch
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "_audit" / "codex_package_matrix.json"
PACKAGES_ROOT = ROOT / "codex_packages" / "plugins"
MARKETPLACE = ROOT / "codex_packages" / ".agents" / "plugins" / "marketplace.json"
UNSUPPORTED_FRONTMATTER = {"argument-hint", "disable-model-invocation", "user-invocable", "version"}
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
    ".txt",
    ".yaml",
    ".yml",
}

PACKAGE_METADATA = {
    "bio-bacteria": {
        "display": "Bio Bacteria Direct",
        "short": "Direct bacterial research skills.",
        "long": "Direct Codex package for bacterial research skills that do not need runtime adaptation before packaging.",
    },
    "bio-pathogens": {
        "display": "Bio Pathogens Direct",
        "short": "Direct pathogen research skills.",
        "long": "Direct Codex package for pathogen research skills that do not need runtime adaptation before packaging.",
    },
    "bio-population-genetics": {
        "display": "Bio Population Genetics Direct",
        "short": "Direct population genetics skills.",
        "long": "Direct Codex package for population genetics skills that do not need runtime adaptation before packaging.",
    },
    "bio-redac": {
        "display": "Bio Redac Direct",
        "short": "Direct scientific writing bridge skill.",
        "long": "Direct Codex package for scientific writing bridge skills that do not need runtime adaptation before packaging.",
    },
    "ia": {
        "display": "IA Direct",
        "short": "Direct data science and AI skills.",
        "long": "Direct Codex package for data science and AI skills that do not need runtime adaptation before packaging.",
    },
    "maboss": {
        "display": "MaBoSS Direct",
        "short": "Direct MaBoSS modelling skills.",
        "long": "Direct Codex package for MaBoSS modelling skills that do not need runtime adaptation before packaging.",
    },
    "ops": {
        "display": "Ops Direct",
        "short": "Direct operational skills.",
        "long": "Direct Codex package for operational skills that do not need runtime adaptation before packaging.",
    },
    "web": {
        "display": "Web Direct",
        "short": "Direct web development skills.",
        "long": "Direct Codex package for web development skills that do not need runtime adaptation before packaging.",
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


def direct_rows() -> list[dict[str, Any]]:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    return [
        row for row in matrix["rows"]
        if row["classification"] in {"direct-package-candidate", "packaged-direct"}
    ]


def ignore(_directory: str, names: list[str]) -> set[str]:
    ignored = set()
    for name in names:
        if name in EXCLUDE_DIRS or any(fnmatch.fnmatch(name, pattern) for pattern in EXCLUDE_GLOBS):
            ignored.add(name)
    return ignored


def copy_skill(source: Path, target: Path) -> None:
    shutil.copytree(source, target, dirs_exist_ok=True, ignore=ignore)
    skill_md = target / "SKILL.md"
    skill_md.write_text(strip_unsupported_frontmatter(skill_md.read_text(encoding="utf-8")), encoding="utf-8")
    clean_text_payload(target)


def clean_text_payload(target: Path) -> None:
    for path in target.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        lines = [line.rstrip(" \t\r") for line in text.splitlines()]
        while lines and lines[-1] == "":
            lines.pop()
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def manifest(package_name: str, skill_count: int) -> dict[str, Any]:
    meta = PACKAGE_METADATA[package_name]
    return {
        "name": package_name,
        "version": "0.1.0",
        "description": f"Local direct Codex package for {skill_count} migrated Claude skills.",
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


def materialize() -> dict[str, list[str]]:
    by_package: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in direct_rows():
        by_package[row["package_candidate"]].append(row)

    for package_name, rows in sorted(by_package.items()):
        if package_name not in PACKAGE_METADATA:
            raise ValueError(f"metadata absente pour le paquet {package_name}")
        package_root = PACKAGES_ROOT / package_name
        skills_root = package_root / "skills"
        (package_root / ".codex-plugin").mkdir(parents=True, exist_ok=True)
        skills_root.mkdir(parents=True, exist_ok=True)
        for row in sorted(rows, key=lambda item: item["name"]):
            copy_skill(ROOT / row["canonical_path"], skills_root / row["name"])
        (package_root / ".codex-plugin" / "plugin.json").write_text(
            json.dumps(manifest(package_name, len(rows)), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (package_root / "README.md").write_text(
            "\n".join([
                f"# {package_name}",
                "",
                "Local Codex package generated from CCX-10 direct candidates.",
                "",
                "The skills in this package are materialized copies of the canonical Claude plugin repository.",
                "Package-only adaptation removes Codex-incompatible Claude frontmatter fields.",
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
    return {package: sorted(row["name"] for row in rows) for package, rows in sorted(by_package.items())}


def main() -> int:
    packages = materialize()
    print(f"OK : {sum(len(names) for names in packages.values())} skills directs materialises")
    for package, names in packages.items():
        print(f"{package}: {len(names)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
