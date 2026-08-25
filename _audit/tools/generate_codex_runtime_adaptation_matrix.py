#!/usr/bin/env python3
"""Generate a fine-grained CCX-10 runtime adaptation matrix.

The coarse packaging matrix intentionally treats any Claude path or MCP mention
as requiring runtime adaptation. This report separates real path rewrites from
ordinary Codex prerequisites so that the remaining skills can be processed in
safe batches.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_MATRIX = ROOT / "_audit" / "codex_package_matrix.json"
JSON_OUT = ROOT / "_audit" / "codex_runtime_adaptation_matrix.json"
MD_OUT = ROOT / "_audit" / "codex_runtime_adaptation_matrix.md"

CLAUDE_PLUGIN_ROOT = re.compile(r"CLAUDE_PLUGIN_ROOT|\$CLAUDE_PLUGIN_ROOT|\${CLAUDE_PLUGIN_ROOT}")
CLAUDE_SKILL_PATH = re.compile(r"~/.claude/skills|\.claude/skills")
CLAUDE_KNOWLEDGE_PATH = re.compile(r"~/.claude/knowledge|\.claude/knowledge")
CLAUDE_CACHE_PATH = re.compile(r"~/.claude/cache|\.claude/cache")
CLAUDE_PROJECT_MEMORY = re.compile(r"~/.claude/projects|\.claude/projects")
CLAUDE_CONFIG = re.compile(r"~/.claude/\.claude\.json|CLAUDE_CONFIG_DIR|claude mcp|Claude Code")
MCP_TOOL = re.compile(r"\bmcp__[A-Za-z0-9_]+__[A-Za-z0-9_]+")
TBANNOTATOR = re.compile(r"\bTBannotator MCP\b|\bmcp__tbannotator__", re.I)
TBMONITOR = re.compile(r"\btbmonitor MCP\b|\bmcp__tbmonitor__", re.I)
GENERIC_MCP = re.compile(r"\bMCP\b|\.mcp\.json|codex mcp|claude mcp", re.I)
WEB_TOOL_NAME = re.compile(r"\bWebSearch\b|\bWebFetch\b")
HTTP_LITERAL = re.compile(r"https?://")
SCRIPT_PAYLOAD = re.compile(r"\bscript-payload\b")


def load_runtime_rows() -> list[dict[str, Any]]:
    matrix = json.loads(PACKAGE_MATRIX.read_text(encoding="utf-8"))
    return [
        row for row in matrix["rows"]
        if row["classification"] in {"needs-codex-runtime-adaptation", "packaged-runtime-adapted"}
    ]


def read_skill(row: dict[str, Any]) -> str:
    return (ROOT / row["canonical_path"] / "SKILL.md").read_text(
        encoding="utf-8",
        errors="replace",
    )


def detect_issues(text: str) -> list[str]:
    issues: list[str] = []
    checks = [
        ("claude-plugin-root", CLAUDE_PLUGIN_ROOT),
        ("claude-skill-path", CLAUDE_SKILL_PATH),
        ("claude-knowledge-path", CLAUDE_KNOWLEDGE_PATH),
        ("claude-cache-path", CLAUDE_CACHE_PATH),
        ("claude-project-memory", CLAUDE_PROJECT_MEMORY),
        ("claude-config-or-branding", CLAUDE_CONFIG),
        ("tbannotator-mcp", TBANNOTATOR),
        ("tbmonitor-mcp", TBMONITOR),
        ("mcp-tool-name", MCP_TOOL),
        ("generic-mcp-mention", GENERIC_MCP),
        ("web-tool-name", WEB_TOOL_NAME),
        ("http-literal", HTTP_LITERAL),
    ]
    for label, pattern in checks:
        if pattern.search(text):
            issues.append(label)
    return issues


def bucket_for(row: dict[str, Any], issues: list[str], text: str) -> str:
    if "claude-plugin-root" in issues or "claude-skill-path" in issues:
        return "rewrite-claude-skill-paths"
    if "claude-project-memory" in issues:
        return "blocked-claude-project-memory"
    if "claude-knowledge-path" in issues:
        return "await-canonical-knowledge-path"
    if "claude-cache-path" in issues:
        return "rewrite-cache-path"
    if re.search(r"clinical trials MCP|MCP Server Unavailable|MCP server is required", text, re.I):
        return "external-mcp-fallback-documented"
    if "mcp-tool-name" in issues:
        return "codex-mcp-tool-prerequisite"
    if "tbannotator-mcp" in issues or "tbmonitor-mcp" in issues:
        return "codex-mcp-documentation-only"
    if "generic-mcp-mention" in issues:
        return "mcp-narrative-only"
    if "web-tool-name" in issues:
        return "codex-web-tool-wording"
    if "claude-config-or-branding" in issues:
        return "claude-branding-only"
    if "http-literal" in issues:
        return "url-reference-only"
    return "unclassified-runtime-signal"


def action_for(bucket: str) -> str:
    return {
        "rewrite-claude-skill-paths": "Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload.",
        "blocked-claude-project-memory": "Reporter vers CCX-13 ou reformuler sans dependance a ~/.claude/projects avant empaquetage.",
        "await-canonical-knowledge-path": "Attendre CCX-04 ou remplacer par le chemin KB Codex actuel avec mention de migration future.",
        "rewrite-cache-path": "Remplacer le cache Claude par un cache neutre sous ~/.cache ou par une sortie projet explicite.",
        "external-mcp-fallback-documented": "Emballer seulement avec prerequis MCP Codex explicite et fallback hors-ligne documente, sans inventer de resultats d'essais.",
        "external-mcp-required": "Ne pas empaqueter sans serveur MCP Codex equivalent ou fallback documente.",
        "codex-mcp-tool-prerequisite": "Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire.",
        "codex-mcp-documentation-only": "Emballage possible ; conserver la mention comme prerequis ou comparaison documentee.",
        "mcp-narrative-only": "Emballage possible ; la mention MCP n'est pas un appel runtime direct.",
        "codex-web-tool-wording": "Emballage possible apres reformulation eventuelle WebSearch/WebFetch vers recherche web disponible.",
        "claude-branding-only": "Emballage possible apres neutralisation de la mention de marque si necessaire.",
        "url-reference-only": "Emballage possible ; les URL ne sont pas un verrou runtime.",
        "unclassified-runtime-signal": "Relire manuellement avant empaquetage.",
    }[bucket]


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_runtime_rows():
        text = read_skill(row)
        issues = detect_issues(text)
        bucket = bucket_for(row, issues, text)
        rows.append({
            "name": row["name"],
            "source_plugin": row["source_plugin"],
            "canonical_path": row["canonical_path"],
            "package_candidate": row["package_candidate"],
            "coarse_signals": row["signals"],
            "runtime_issues": issues,
            "runtime_bucket": bucket,
            "action": action_for(bucket),
        })
    return rows


def summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {
        "runtime_bucket": dict(sorted(Counter(row["runtime_bucket"] for row in rows).items())),
        "source_plugin": dict(sorted(Counter(row["source_plugin"] for row in rows).items())),
        "package_candidate": dict(sorted(Counter(row["package_candidate"] for row in rows).items())),
    }


def markdown(rows: list[dict[str, Any]]) -> str:
    counts = summary(rows)
    lines = [
        "# Matrice CCX-10 des adaptations runtime Codex",
        "",
        "Ce fichier est genere par `_audit/tools/generate_codex_runtime_adaptation_matrix.py`.",
        "Il decompose les skills classes `needs-codex-runtime-adaptation` par la matrice principale.",
        "",
        f"- Total a adapter : {len(rows)}",
        "",
        "## Comptes par famille d'adaptation",
        "",
        "| famille | skills |",
        "|---|---:|",
    ]
    for bucket, count in counts["runtime_bucket"].items():
        lines.append(f"| {bucket} | {count} |")
    lines.extend([
        "",
        "## Matrice complete",
        "",
        "| skill | source | paquet | famille | problemes | action |",
        "|---|---|---|---|---|---|",
    ])
    for row in rows:
        lines.append(
            "| {name} | {source_plugin} | {package_candidate} | {runtime_bucket} | {issues} | {action} |".format(
                name=row["name"],
                source_plugin=row["source_plugin"],
                package_candidate=row["package_candidate"],
                runtime_bucket=row["runtime_bucket"],
                issues=", ".join(row["runtime_issues"]) if row["runtime_issues"] else "none",
                action=row["action"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def write_outputs(rows: list[dict[str, Any]]) -> None:
    JSON_OUT.write_text(
        json.dumps({"summary": summary(rows), "rows": rows}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    MD_OUT.write_text(markdown(rows), encoding="utf-8")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated files are stale")
    args = parser.parse_args()
    rows = build_rows()
    expected_json = json.dumps({"summary": summary(rows), "rows": rows}, ensure_ascii=False, indent=2) + "\n"
    expected_md = markdown(rows)
    if args.check:
        stale = []
        if not JSON_OUT.is_file() or JSON_OUT.read_text(encoding="utf-8") != expected_json:
            stale.append(str(JSON_OUT.relative_to(ROOT)))
        if not MD_OUT.is_file() or MD_OUT.read_text(encoding="utf-8") != expected_md:
            stale.append(str(MD_OUT.relative_to(ROOT)))
        if stale:
            print("STALE: " + ", ".join(stale))
            return 1
    else:
        write_outputs(rows)
    print(f"OK : {len(rows)} adaptations runtime classees")
    for field, values in summary(rows).items():
        print(f"{field}: " + ", ".join(f"{key}={value}" for key, value in values.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
