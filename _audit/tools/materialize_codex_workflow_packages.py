#!/usr/bin/env python3
"""Materialize project-workflow Codex packages with explicit guardrails."""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "_audit" / "codex_package_matrix.json"
JSON_OUT = ROOT / "_audit" / "codex_workflow_package_audit.json"
MD_OUT = ROOT / "_audit" / "codex_workflow_package_audit.md"
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
    ".tsv",
    ".txt",
    ".yaml",
    ".yml",
}

PACKAGE_METADATA = {
    "bio-redac": {
        "display": "Bio Redac Direct",
        "short": "Direct biological writing skills.",
        "long": "Codex package for biological writing skills already audited for direct or guarded workflow packaging.",
    },
    "bio-pathogens": {
        "display": "Bio Pathogens Direct",
        "short": "Direct pathogen research skills.",
        "long": "Codex package for pathogen research skills already audited for direct, payload, runtime, or guarded workflow packaging.",
    },
    "ops": {
        "display": "Ops Direct",
        "short": "Direct operational skills.",
        "long": "Codex package for operational skills already audited for direct or guarded workflow packaging.",
    },
}

PACKAGE_OVERRIDES = {
    "redac": "bio-redac",
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
    if line.startswith("description: ") and ": " in line.removeprefix("description: "):
        value = line.removeprefix("description: ")
        return "description: " + json.dumps(value, ensure_ascii=False)
    line = re.sub(r">(\d)", r"more than \1", line)
    line = re.sub(r"<(\d)", r"less than \1", line)
    return line.replace("<->", "to").replace("<", "").replace(">", "")


def adapt_workflow_text(text: str, row: dict[str, Any]) -> str:
    text = strip_unsupported_frontmatter(text)
    text = text.replace("Claude Code", "Codex")
    text = text.replace("`CLAUDE.md`", "`AGENTS.md` or `CLAUDE.md` fallback")
    text = text.replace("CLAUDE.md", "AGENTS.md or CLAUDE.md fallback")
    text = text.replace("~/.claude/knowledge/tuberculosis.md", "~/.Codex/knowledge/tuberculosis.md")
    text = text.replace("~/.claude/projects/.../memory/MEMORY.md", "~/.codex/memories/ or project registers")
    text = text.replace("~/.claude/skills/recadrage/recadrage_signals.py", "recadrage_signals.py, once CCX-05 has ported recadrage")
    skill_name = re.escape(row["name"])
    text = re.sub(rf"\$\{{CLAUDE_PLUGIN_ROOT\}}/skills/{skill_name}/", "", text)
    text = re.sub(rf"\$CLAUDE_PLUGIN_ROOT/skills/{skill_name}/", "", text)
    text = text.replace("${CLAUDE_PLUGIN_ROOT}/skills/mtbc-gene", "../mtbc-gene")
    text = text.replace("${CLAUDE_PLUGIN_ROOT}/skills/mtbc-lineages", "../mtbc-lineages")
    text = text.replace("${CLAUDE_PLUGIN_ROOT}/skills/fetch-tbannotator", "")
    text = text.replace(
        "${CLAUDE_PLUGIN_ROOT}/skills/claim-check/references/CLAIM_TAXONOMY.md",
        "../../bio-redac/skills/claim-check/references/CLAIM_TAXONOMY.md",
    )
    text = text.replace("${CLAUDE_PLUGIN_ROOT}/../bio_pathogens/skills/", "../")
    text = text.replace("${CLAUDE_PLUGIN_ROOT}/../bio_population_genetics/skills/", "../../bio-population-genetics/skills/")
    text = text.replace("${CLAUDE_PLUGIN_ROOT}", "packaged skill root")
    text = re.sub(
        r"claude mcp add --transport http --scope user\s+([A-Za-z0-9_-]+)\s+(https?://\S+)",
        r"codex mcp add \1 --url \2",
        text,
    )
    text = text.replace("claude mcp list", "codex mcp list")
    guard = (
        "\n## Codex workflow guardrail\n\n"
        "This packaged copy imports a Claude-origin project workflow into Codex. "
        "Before writing project registers, moving BDD files, changing Atlas content, appending remote queues, "
        "archiving a project, or launching remote compute, require an explicit user request in the current turn. "
        "Use recoverable operations only, keep project provenance boundaries, and follow the global rule that files "
        "are moved to the trash rather than permanently deleted.\n"
    )
    if "## Codex workflow guardrail" not in text:
        text = text.rstrip() + "\n" + guard
    if ("mcp__" in text or "MCP" in text) and "## Codex MCP note" not in text:
        text = text.rstrip() + (
            "\n\n## Codex MCP note\n\n"
            "MCP tool names in `allowed-tools` are prerequisites. Verify them with `codex mcp list` before relying on live queries.\n"
        )
    return text


def adapt_submission_text(text: str) -> str:
    """Replace Claude-only submission runtime details in the Codex copy."""
    text = re.sub(
        r"\nallowed-tools:\n(?:[ \t]+-[^\n]*\n)+",
        "\n",
        text,
        count=1,
    )
    replacements = {
        "~/.claude/knowledge/journals": "~/.agents/knowledge/journals",
        "`tabs_context_mcp{createIfEmpty:true}`": "`agent-browser --session soumission open <url>`",
        "tabs_context_mcp{createIfEmpty:true}": "agent-browser --session soumission open <url>",
        "`tabs_close_mcp`": "`agent-browser --session soumission close`",
        "tabs_close_mcp": "agent-browser --session soumission close",
        "`tabs_create_mcp`": "`agent-browser click <ref> --new-tab`",
        "tabs_create_mcp": "agent-browser click <ref> --new-tab",
        "`navigate`": "`agent-browser open`",
        "`read_page`": "`agent-browser snapshot -i`",
        "`get_page_text`": "`agent-browser get text body`",
        "`AskUserQuestion`": "une question explicite à l'utilisateur",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace("---\n\nname:", "---\nname:", 1)
    text = text.replace(
        "puis un `tabId` explicite passé à chaque `agent-browser open`",
        "puis la même session nommée utilisée avec `agent-browser open`",
    )
    text = text.replace(
        "puis `AGENTS.md` ou, à défaut,\n"
        "   `AGENTS.md` or `AGENTS.md or CLAUDE.md fallback` fallback.",
        "puis `AGENTS.md`, ou `CLAUDE.md` seulement comme registre historique.",
    )
    navigation_note = (
        "\n## Navigation sous Codex\n\n"
        "Utiliser le skill `agent-browser` avec une session nommée propre au manuscrit. "
        "Suivre la boucle `open`, `snapshot -i`, action, nouveau `snapshot -i`, puis "
        "fermer la session avant de rendre la main. Activer les limites de domaine et "
        "les frontières de contenu quand elles sont disponibles. Ne jamais enregistrer "
        "un état d'authentification, saisir un secret ou franchir une confirmation légale. "
        "Si `agent-browser` ou un navigateur équivalent n'est pas disponible, rester en "
        "préparation locale et signaler le verrou au lieu de simuler l'action externe.\n"
    )
    if "# /soumission" in text and "## Navigation sous Codex" not in text:
        text = text.rstrip() + "\n" + navigation_note
    return text


def adapt_submission_payload(target: Path) -> None:
    for path in target.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        path.write_text(adapt_submission_text(text), encoding="utf-8")


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
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    rows = [
        row for row in matrix["rows"]
        if row["classification"] in {"blocked-by-personal-workflow", "packaged-workflow-guarded"}
    ]
    for row in rows:
        if row["package_candidate"] in PACKAGE_OVERRIDES:
            row["package_candidate"] = PACKAGE_OVERRIDES[row["package_candidate"]]
    return rows


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
    skill_md.write_text(adapt_workflow_text(skill_md.read_text(encoding="utf-8"), row), encoding="utf-8")
    if row["name"] == "soumission":
        adapt_submission_payload(target)
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
    manifest_path = PACKAGES_ROOT / package_name / ".codex-plugin" / "plugin.json"
    version = "0.1.0"
    if manifest_path.is_file():
        current = json.loads(manifest_path.read_text(encoding="utf-8"))
        version = current.get("version") or version
    return {
        "name": package_name,
        "version": version,
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
            "defaultPrompt": "Use the installed skills with their documented prerequisites, guardrails, and evidence boundaries.",
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
        "# Audit des paquets workflow Codex",
        "",
        "Ce fichier est genere par `_audit/tools/materialize_codex_workflow_packages.py`.",
        "Il couvre les workflows projet importes avec garde-fou explicite de mutation.",
        "",
        "| skill | paquet | fichiers copies | fichiers exclus | racines exclues |",
        "|---|---|---:|---:|---|",
    ]
    for row in rows:
        roots = ", ".join(row["audit"]["excluded_roots"]) if row["audit"]["excluded_roots"] else "none"
        lines.append(
            f"| {row['name']} | {row['package_candidate']} | "
            f"{row['audit']['copied_files_actual']} | {row['audit']['excluded_files']} | {roots} |"
        )
    lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def materialize(selected_names: set[str] | None = None) -> list[dict[str, Any]]:
    audit_rows: list[dict[str, Any]] = []
    by_package: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows_to_materialize():
        if selected_names is not None and row["name"] not in selected_names:
            continue
        by_package[row["package_candidate"]].append(row)

    found = {row["name"] for rows in by_package.values() for row in rows}
    if selected_names is not None and found != selected_names:
        missing = sorted(selected_names - found)
        raise ValueError(f"skills workflow absents de la matrice : {', '.join(missing)}")

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
                "Workflow packaging adds explicit Codex guardrails for project, Atlas, BDD, remote queue and archive mutations.",
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
    materialized_rows = list(audit_rows)
    if selected_names is not None and JSON_OUT.is_file():
        previous = json.loads(JSON_OUT.read_text(encoding="utf-8")).get("rows", [])
        current = {row["name"]: row for row in rows_to_materialize()}
        merged = {
            row["name"]: {**current.get(row["name"], row), "audit": row["audit"]}
            for row in previous
            if row["name"] not in selected_names
        }
        merged.update({row["name"]: row for row in audit_rows})
        audit_rows = [merged[name] for name in sorted(merged)]
    write_audit(audit_rows)
    return materialized_rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skill",
        action="append",
        default=[],
        help="materialiser seulement ce skill et conserver les autres lignes d'audit",
    )
    args = parser.parse_args()
    selected = set(args.skill) or None
    rows = materialize(selected)
    by_package = Counter(row["package_candidate"] for row in rows)
    print(f"OK : {len(rows)} skills workflow materialises")
    print("package: " + ", ".join(f"{key}={value}" for key, value in sorted(by_package.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
