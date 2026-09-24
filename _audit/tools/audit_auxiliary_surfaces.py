#!/usr/bin/env python3
"""Audit CCX-14 des surfaces auxiliaires Claude et Codex.

Le rapport ne sérialise jamais les valeurs de configuration MCP. Il conserve
seulement les noms de serveurs, les transports et le nombre d'en-têtes secrets.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
JSON_OUT = ROOT / "_audit" / "auxiliary_surfaces_report.json"
MD_OUT = ROOT / "_audit" / "auxiliary_surfaces_report.md"
EXPECTED_MCP = {"context7", "superhuman", "tbannotator", "tbmonitor"}
EXPECTED_STATUS = ["current-dir", "model-with-reasoning", "context-remaining"]
EXPECTED_TITLE = ["project-name", "git-branch", "model-with-reasoning", "task-progress"]
FORBIDDEN_GRAPHIFY = (
    re.compile(r"\brm\s+-"),
    re.compile(r"\bunlink\b"),
    re.compile(r"\bshred\b"),
    re.compile(r"\bfind\b[^\n]*\s-delete\b"),
    re.compile(r"\bclose_agent\b"),
    re.compile(r"\bagent_type\s*="),
)


def command_output(command: list[str]) -> str:
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip()


def tool_version(tool: str, args: list[str]) -> str:
    output = command_output([tool, *args])
    return output.splitlines()[0] if output else ""


def graphify_version() -> str:
    match = re.search(r"^graphifyy v([^\s]+)$", command_output(["uv", "tool", "list"]), re.MULTILINE)
    return match.group(1) if match else "unknown"


def command_markdown_files(root: Path) -> list[str]:
    if not root.is_dir():
        return []
    return sorted(str(path) for path in root.rglob("commands/*.md") if path.is_file())


def agent_markdown_files(root: Path) -> list[str]:
    if not root.is_dir():
        return []
    return sorted(str(path) for path in root.rglob("agents/*.md") if path.is_file())


def safe_mcp_summary(config: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, raw in sorted(config.get("mcp_servers", {}).items()):
        server = raw if isinstance(raw, dict) else {}
        header_count = sum(
            len(server.get(key, {}))
            for key in ("http_headers", "env_http_headers")
            if isinstance(server.get(key), dict)
        )
        rows.append(
            {
                "name": name,
                "transport": "http" if "url" in server else "stdio" if "command" in server else "unknown",
                "credential_header_count": header_count,
            }
        )
    return rows


def graphify_checks(home: Path) -> dict[str, Any]:
    skill = home / ".agents" / "skills" / "graphify"
    skill_md = skill / "SKILL.md"
    provenance = skill / "PROVENANCE.md"
    text = skill_md.read_text(encoding="utf-8") if skill_md.is_file() else ""
    violations = sorted({pattern.pattern for pattern in FORBIDDEN_GRAPHIFY if pattern.search(text)})
    return {
        "canonical_path": str(skill),
        "installed": skill_md.is_file(),
        "provenance_present": provenance.is_file(),
        "historical_codex_duplicate_absent": not (home / ".codex" / "skills" / "graphify").exists(),
        "forbidden_instruction_patterns": violations,
    }


def build_report(home: Path = Path.home()) -> dict[str, Any]:
    codex_config_path = home / ".codex" / "config.toml"
    with codex_config_path.open("rb") as handle:
        codex_config = tomllib.load(handle)
    graphify = graphify_checks(home)
    mcp = safe_mcp_summary(codex_config)
    mcp_names = {row["name"] for row in mcp}
    features = codex_config.get("features", {})
    tui = codex_config.get("tui", {})
    claude_root = home / ".claude"
    agents = agent_markdown_files(ROOT / "redaction")
    commands = command_markdown_files(claude_root / "commands") + command_markdown_files(ROOT)
    decisions = [
        {"surface": "graphify", "decision": "import-adapte", "reason": "capacité absente, source amont épinglée"},
        {"surface": "pyright-lsp", "decision": "remplace-runtime-local", "reason": "plugin Claude sans payload serveur"},
        {"surface": "agents-bio-redac", "decision": "abandonne-redondant", "reason": "prompts Claude obsolètes, pipelines Codex déjà présents"},
        {"surface": "commandes-Claude", "decision": "aucun-import", "reason": "aucune commande Markdown détectée"},
        {"surface": "MCP", "decision": "conserve", "reason": "les quatre noms observés sont déjà configurés dans Codex"},
        {"surface": "statusline", "decision": "remplace-TUI-native", "reason": "configuration Codex persistante"},
        {"surface": "caches-marketplace", "decision": "aucun-import", "reason": "caches non canoniques"},
        {"surface": "frontend-design", "decision": "aucun-import", "reason": "plugin Claude désactivé et capacité Codex déjà disponible"},
    ]
    report = {
        "schema_version": 1,
        "codex_version": tool_version("codex", ["--version"]),
        "pyright_version": tool_version("pyright", ["--version"]),
        "graphify_version": graphify_version(),
        "graphify": graphify,
        "codex_tui": {"status_line": tui.get("status_line"), "terminal_title": tui.get("terminal_title")},
        "codex_features": {
            "memories": features.get("memories"),
            "terminal_resize_reflow_absent": "terminal_resize_reflow" not in features,
            "external_migration_absent": "external_migration" not in features,
        },
        "mcp": {
            "servers": mcp,
            "names_match_expected": mcp_names == EXPECTED_MCP,
            "secret_values_serialized": False,
            "note": "Un en-tête statique porteur d'un secret reste à durcir, sans copie ni exposition de sa valeur.",
        },
        "claude_auxiliary_inventory": {
            "agent_markdown_count": len(agents),
            "agent_names": sorted(Path(path).stem for path in agents),
            "command_markdown_count": len(commands),
            "statusline_script_present": (claude_root / "statusline-command.sh").is_file(),
        },
        "decisions": decisions,
    }
    report["ok"] = all(
        (
            report["graphify_version"] == "0.9.50",
            graphify["installed"],
            graphify["provenance_present"],
            graphify["historical_codex_duplicate_absent"],
            not graphify["forbidden_instruction_patterns"],
            report["pyright_version"].startswith("pyright "),
            report["codex_tui"]["status_line"] == EXPECTED_STATUS,
            report["codex_tui"]["terminal_title"] == EXPECTED_TITLE,
            report["codex_features"]["memories"] is True,
            report["codex_features"]["terminal_resize_reflow_absent"],
            report["codex_features"]["external_migration_absent"],
            report["mcp"]["names_match_expected"],
            report["claude_auxiliary_inventory"]["agent_markdown_count"] == 4,
            report["claude_auxiliary_inventory"]["command_markdown_count"] == 0,
        )
    )
    return report


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Audit CCX-14 des surfaces auxiliaires",
        "",
        "Ce fichier est généré par `_audit/tools/audit_auxiliary_surfaces.py`.",
        "Aucune valeur secrète MCP n'est sérialisée.",
        "",
        f"- Statut : {'OK' if report['ok'] else 'ÉCHEC'}",
        f"- Codex : `{report['codex_version']}`",
        f"- Pyright : `{report['pyright_version']}`",
        f"- Graphify : `{report['graphify_version']}`",
        f"- MCP Codex : {', '.join(row['name'] for row in report['mcp']['servers'])}",
        f"- Agents Claude classés : {report['claude_auxiliary_inventory']['agent_markdown_count']}",
        f"- Commandes Claude à importer : {report['claude_auxiliary_inventory']['command_markdown_count']}",
        "",
        "| surface | décision | raison |",
        "|---|---|---|",
    ]
    for row in report["decisions"]:
        lines.append(f"| {row['surface']} | {row['decision']} | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Réserves",
            "",
            "- Les quatre noms MCP sont présents dans Codex. La divergence d'URL de `tbannotator` a été conservée pour ne pas écraser silencieusement une configuration Codex opérationnelle.",
            "- Un en-tête MCP statique porteur d'un secret existe encore. Sa valeur n'est jamais copiée dans cet audit. Le passage à une variable d'environnement relève du durcissement ultérieur.",
            "- Les modifications TUI et Graphify ne deviennent visibles dans la découverte d'une session déjà ouverte qu'après une nouvelle session.",
            "",
        ]
    )
    return "\n".join(lines)


def expected_outputs(report: dict[str, Any]) -> tuple[str, str]:
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n", markdown(report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = build_report(args.home.expanduser())
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
    print("OK : surfaces auxiliaires auditées" if report["ok"] else "ÉCHEC : surfaces auxiliaires non conformes")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
