#!/usr/bin/env python3
"""Generate the Codex packaging matrix for canonical skills not yet exported.

The matrix is derived from ``canon_skills.json`` and ``codex_skills.json``.
It does not mutate a Codex profile. It only records the remaining packaging
surface for CCX-10.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
JSON_OUT = ROOT / "_audit" / "codex_package_matrix.json"
MD_OUT = ROOT / "_audit" / "codex_package_matrix.md"

UNSUPPORTED_FRONTMATTER = {"argument-hint", "disable-model-invocation", "user-invocable", "version"}
CLAUDE_RUNTIME = re.compile(
    r"(~/.claude|CLAUDE_PLUGIN_ROOT|CLAUDE\.md|Claude Code|CLAUDE_CONFIG_DIR)"
)
PROJECT_MEMORY = re.compile(
    r"(pistes\.md|cahier_de_labo\.md|etat_des_decouvertes\.md|JOURNAL\.md)"
)
WRITE_WORDS = re.compile(
    r"\b(write|edit|append|create|modifier|ecrire|inscrire|ajouter|reecrire|"
    r"réécrire|cré(?:er|e)|enrichir)\b",
    re.I,
)
MCP_RUNTIME = re.compile(r"(mcp__|\.mcp\.json|\bMCP\b|codex mcp|claude mcp)", re.I)
WEB_RUNTIME = re.compile(r"\b(WebSearch|WebFetch|curl|requests\.|https?://)", re.I)

PACKAGE_BY_PLUGIN = {
    "bio_bacteria": "bio-bacteria",
    "bio_pathogens": "bio-pathogens",
    "bio_population_genetics": "bio-population-genetics",
    "bio_redac": "bio-redac",
    "ia": "ia",
    "maboss": "maboss",
    "multimedia": "multimedia",
    "ops": "ops",
    "web": "web",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    frontmatter: dict[str, str] = {}
    key: str | None = None
    for line in text[3:end].splitlines():
        if not line.strip():
            continue
        match = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if match:
            key = match.group(1)
            frontmatter[key] = match.group(2).strip()
        elif key and line[:1] in " \t":
            frontmatter[key] = f"{frontmatter[key]} {line.strip()}".strip()
    return frontmatter, text[end + 4 :]


def packaged_skills(root: Path = ROOT) -> dict[str, list[str]]:
    packages_root = root / "codex_packages" / "plugins"
    if not packages_root.is_dir():
        return {}
    found: dict[str, list[str]] = defaultdict(list)
    for plugin in sorted(entry for entry in packages_root.iterdir() if entry.is_dir()):
        skills = plugin / "skills"
        if not skills.is_dir():
            continue
        for skill in sorted(entry for entry in skills.iterdir() if entry.is_dir()):
            if (skill / "SKILL.md").is_file():
                found[skill.name].append(plugin.name)
    return dict(found)


def file_count(path: Path) -> int:
    return sum(1 for entry in path.rglob("*") if entry.is_file())


def has_support_dir(path: Path, dirname: str) -> bool:
    candidate = path / dirname
    return candidate.is_dir() and any(candidate.rglob("*"))


def classify(signals: set[str], packages: list[str]) -> str:
    if packages:
        if packages == ["guyeux-phylo-pilot"]:
            return "packaged-pilot"
        if "project-memory-write" in signals:
            return "packaged-workflow-guarded"
        if "claude-runtime-reference" in signals or "mcp-runtime" in signals:
            return "packaged-runtime-adapted"
        if "script-payload" in signals or "data-payload" in signals:
            return "packaged-payload"
        return "packaged-direct"
    if "project-memory-write" in signals:
        return "blocked-by-personal-workflow"
    if "claude-runtime-reference" in signals or "mcp-runtime" in signals:
        return "needs-codex-runtime-adaptation"
    if "script-payload" in signals or "data-payload" in signals:
        return "needs-payload-package-audit"
    return "direct-package-candidate"


def action_for(row: dict[str, Any]) -> str:
    classification = row["classification"]
    if classification == "packaged-pilot":
        return "Deja materialise dans le lot temoin, verifier lors de l'extension."
    if classification == "packaged-direct":
        return "Deja materialise dans un paquet direct, verifier lors de l'installation isolee."
    if classification == "packaged-payload":
        return "Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee."
    if classification == "packaged-runtime-adapted":
        return "Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie."
    if classification == "packaged-workflow-guarded":
        return "Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution."
    if classification == "blocked-by-personal-workflow":
        return "Porter ou neutraliser les ecritures de memoire projet avant empaquetage."
    if classification == "needs-codex-runtime-adaptation":
        return "Remplacer les references Claude et declarer les prerequis MCP Codex."
    if classification == "needs-payload-package-audit":
        return "Copier scripts, donnees et references, puis tester le payload installe."
    return "Copier le skill dans son paquet cible, puis retirer les champs Claude si presents."


def build_rows(root: Path = ROOT) -> list[dict[str, Any]]:
    registry = load_json(root / "canon_skills.json")
    exports = set(load_json(root / "codex_skills.json"))
    packaged = packaged_skills(root)
    rows: list[dict[str, Any]] = []

    for name in sorted(set(registry) - exports):
        relative = registry[name]
        path = root / relative
        text = (path / "SKILL.md").read_text(encoding="utf-8", errors="replace")
        frontmatter, body = parse_frontmatter(text)
        source_plugin = Path(relative).parts[0]
        packages = packaged.get(name, [])
        signals: set[str] = set()
        unsupported = sorted(UNSUPPORTED_FRONTMATTER & set(frontmatter))
        if unsupported:
            signals.add("unsupported-frontmatter")
        allowed_tools = frontmatter.get("allowed-tools", "")
        if CLAUDE_RUNTIME.search(text):
            signals.add("claude-runtime-reference")
        if PROJECT_MEMORY.search(text) and (WRITE_WORDS.search(body) or any(tool in allowed_tools for tool in ("Write", "Edit"))):
            signals.add("project-memory-write")
        if MCP_RUNTIME.search(text):
            signals.add("mcp-runtime")
        if WEB_RUNTIME.search(text):
            signals.add("web-runtime")
        if has_support_dir(path, "scripts") or any(path.glob("*.py")) or any(path.glob("*.sh")):
            signals.add("script-payload")
        if has_support_dir(path, "data") or has_support_dir(path, "assets"):
            signals.add("data-payload")
        if has_support_dir(path, "references") or has_support_dir(path, "templates") or has_support_dir(path, "src"):
            signals.add("supporting-resources")
        if (path / "PROVENANCE.md").is_file():
            signals.add("provenance-recorded")

        row = {
            "name": name,
            "source_plugin": source_plugin,
            "canonical_path": relative,
            "package_candidate": packages[0] if packages else PACKAGE_BY_PLUGIN.get(source_plugin, source_plugin.replace("_", "-")),
            "packaged_in": packages,
            "classification": classify(signals, packages),
            "signals": sorted(signals),
            "unsupported_frontmatter": unsupported,
            "file_count": file_count(path),
        }
        row["action"] = action_for(row)
        rows.append(row)

    return rows


def summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for field in ("source_plugin", "package_candidate", "classification"):
        counts = Counter(row[field] for row in rows)
        result[field] = dict(sorted(counts.items()))
    return result


def markdown(rows: list[dict[str, Any]]) -> str:
    counts = summary(rows)
    lines = [
        "# Matrice CCX-10 d'empaquetage Codex",
        "",
        "Ce fichier est genere par `_audit/tools/generate_codex_package_matrix.py`.",
        "Il inventorie les skills canoniques absents de `codex_skills.json` et indique le premier traitement requis pour les empaqueter dans Codex.",
        "",
        f"- Total non exporte Codex : {len(rows)}",
        f"- Deja materialises dans un paquet pilote : {counts['classification'].get('packaged-pilot', 0)}",
        f"- Deja materialises dans des paquets directs : {counts['classification'].get('packaged-direct', 0)}",
        f"- Deja materialises dans des paquets payload audites : {counts['classification'].get('packaged-payload', 0)}",
        f"- Deja materialises avec adaptation runtime Codex : {counts['classification'].get('packaged-runtime-adapted', 0)}",
        f"- Deja materialises avec garde-fou workflow Codex : {counts['classification'].get('packaged-workflow-guarded', 0)}",
        f"- Bloques par workflow personnel d'ecriture : {counts['classification'].get('blocked-by-personal-workflow', 0)}",
        f"- Adaptation runtime Claude ou MCP requise : {counts['classification'].get('needs-codex-runtime-adaptation', 0)}",
        f"- Audit de payload requis : {counts['classification'].get('needs-payload-package-audit', 0)}",
        f"- Candidats directs sans verrou mecanique majeur : {counts['classification'].get('direct-package-candidate', 0)}",
        "",
        "## Comptes par paquet cible",
        "",
        "| paquet | skills |",
        "|---|---:|",
    ]
    for package, count in counts["package_candidate"].items():
        lines.append(f"| {package} | {count} |")

    lines.extend([
        "",
        "## Matrice complete",
        "",
        "| skill | source | paquet | statut | signaux | action |",
        "|---|---|---|---|---|---|",
    ])
    for row in rows:
        signals = ", ".join(row["signals"]) if row["signals"] else "none"
        lines.append(
            "| {name} | {source_plugin} | {package_candidate} | {classification} | {signals} | {action} |".format(
                name=row["name"],
                source_plugin=row["source_plugin"],
                package_candidate=row["package_candidate"],
                classification=row["classification"],
                signals=signals,
                action=row["action"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def write_outputs(rows: list[dict[str, Any]], json_out: Path = JSON_OUT, md_out: Path = MD_OUT) -> None:
    payload = {"summary": summary(rows), "rows": rows}
    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_out.write_text(markdown(rows), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated files are stale")
    args = parser.parse_args()

    rows = build_rows()
    if args.check:
        expected_json = json.dumps({"summary": summary(rows), "rows": rows}, ensure_ascii=False, indent=2) + "\n"
        expected_md = markdown(rows)
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

    print(f"OK : {len(rows)} skills non exportes classes pour CCX-10")
    for field, values in summary(rows).items():
        print(f"{field}: " + ", ".join(f"{key}={value}" for key, value in values.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
