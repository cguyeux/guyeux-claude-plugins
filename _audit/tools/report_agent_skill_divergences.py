#!/usr/bin/env python3
"""Rapport des divergences de contenu entre skills Claude et Agents.

Le rapport est derive de ``_audit/agent_farm_expected_delta.json`` et compare
les skills presents des deux cotes mais declares divergents. Il ne modifie ni
``~/.claude/skills`` ni ``~/.agents/skills``.

Usage :
    python3 _audit/tools/report_agent_skill_divergences.py
    python3 _audit/tools/report_agent_skill_divergences.py --check
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CLAUDE_ROOT = Path.home() / ".claude" / "skills"
DEFAULT_AGENTS_ROOT = Path.home() / ".agents" / "skills"
JSON_OUT = ROOT / "_audit" / "agent_farm_divergence_report.json"
MD_OUT = ROOT / "_audit" / "agent_farm_divergence_report.md"
EXCLUDED_NAMES = {".venv", "venv", "__pycache__"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def expected_divergent(root: Path = ROOT) -> list[str]:
    payload = load_json(root / "_audit" / "agent_farm_expected_delta.json")
    return sorted(payload.get("common_divergent_expected", []))


def included_files(skill_root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    if not skill_root.is_dir():
        return files
    for path in skill_root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(skill_root)
        if any(part in EXCLUDED_NAMES for part in relative.parts) or path.suffix in EXCLUDED_SUFFIXES:
            continue
        files[str(relative)] = path
    return files


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def frontmatter_keys(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return []
    end = text.find("\n---", 3)
    if end == -1:
        return []
    keys: list[str] = []
    for line in text[3:end].splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            keys.append(line.split(":", 1)[0].strip())
    return sorted(keys)


def line_delta(left: Path, right: Path) -> dict[str, int]:
    added = 0
    removed = 0
    for line in difflib.unified_diff(text_lines(left), text_lines(right), lineterm=""):
        if line.startswith(("+++", "---", "@@")):
            continue
        if line.startswith("+"):
            added += 1
        elif line.startswith("-"):
            removed += 1
    return {"added": added, "removed": removed}


def classify_row(added_files: list[str], removed_files: list[str], modified_files: list[str]) -> str:
    support_changes = [path for path in added_files + removed_files + modified_files if path != "SKILL.md"]
    if support_changes:
        return "payload-review-required"
    if modified_files == ["SKILL.md"]:
        return "instruction-review-required"
    return "manual-review-required"


def compare_skill(name: str, claude_root: Path, agents_root: Path) -> dict[str, Any]:
    claude_skill = claude_root / name
    agents_skill = agents_root / name
    claude_files = included_files(claude_skill)
    agents_files = included_files(agents_skill)
    added_in_claude = sorted(set(claude_files) - set(agents_files))
    added_in_agents = sorted(set(agents_files) - set(claude_files))
    common = sorted(set(claude_files) & set(agents_files))
    modified: list[str] = []
    line_deltas: dict[str, dict[str, int]] = {}
    for relative in common:
        if sha256(claude_files[relative]) != sha256(agents_files[relative]):
            modified.append(relative)
            if relative.endswith((".md", ".py", ".txt", ".toml", ".json", ".yaml", ".yml")):
                line_deltas[relative] = line_delta(claude_files[relative], agents_files[relative])
    return {
        "name": name,
        "classification": classify_row(added_in_claude + added_in_agents, [], modified),
        "decision": "manual-review-required",
        "claude_only_files": added_in_claude,
        "agents_only_files": added_in_agents,
        "modified_files": modified,
        "line_delta_claude_to_agents": line_deltas,
        "claude_skill_md_frontmatter_keys": frontmatter_keys(claude_skill / "SKILL.md"),
        "agents_skill_md_frontmatter_keys": frontmatter_keys(agents_skill / "SKILL.md"),
    }


def build_report(claude_root: Path, agents_root: Path, root: Path = ROOT) -> dict[str, Any]:
    rows = [compare_skill(name, claude_root, agents_root) for name in expected_divergent(root)]
    summary: dict[str, int] = {}
    for row in rows:
        summary[row["classification"]] = summary.get(row["classification"], 0) + 1
    return {
        "claude_root": str(claude_root),
        "agents_root": str(agents_root),
        "total": len(rows),
        "summary": dict(sorted(summary.items())),
        "rows": rows,
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Rapport CCX-06 des divergences Claude/Agents",
        "",
        "Ce fichier est genere par `_audit/tools/report_agent_skill_divergences.py`.",
        "Il compare les skills communs declares divergents dans `_audit/agent_farm_expected_delta.json`.",
        "",
        f"- Total : {report['total']}",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key} : {value}")
    lines.extend([
        "",
        "| skill | classification | decision | fichiers Claude-only | fichiers Agents-only | fichiers modifies | delta lignes |",
        "|---|---|---|---:|---:|---:|---|",
    ])
    for row in report["rows"]:
        delta_bits = []
        for relative, delta in row["line_delta_claude_to_agents"].items():
            delta_bits.append(f"{relative}:+{delta['added']}/-{delta['removed']}")
        lines.append(
            "| {name} | {classification} | {decision} | {claude_only} | {agents_only} | {modified} | {delta} |".format(
                name=row["name"],
                classification=row["classification"],
                decision=row["decision"],
                claude_only=len(row["claude_only_files"]),
                agents_only=len(row["agents_only_files"]),
                modified=len(row["modified_files"]),
                delta=", ".join(delta_bits) if delta_bits else "none",
            )
        )
    lines.append("")
    return "\n".join(lines)


def expected_outputs(report: dict[str, Any]) -> tuple[str, str]:
    json_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    return json_text, markdown(report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claude-root", type=Path, default=DEFAULT_CLAUDE_ROOT)
    parser.add_argument("--agents-root", type=Path, default=DEFAULT_AGENTS_ROOT)
    parser.add_argument("--check", action="store_true", help="echouer si le rapport versionne est stale")
    args = parser.parse_args()

    report = build_report(args.claude_root.expanduser(), args.agents_root.expanduser(), ROOT)
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
    print(f"OK : {report['total']} divergences Claude/Agents rapportees")
    for key, value in report["summary"].items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
