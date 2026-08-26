#!/usr/bin/env python3
"""Auditer les mémoires projet Claude avant un import sélectif Codex.

Le rapport conserve les chemins relatifs, hashes, types et indicateurs de
risque, mais jamais les valeurs qui ont déclenché un indicateur sensible.
Les fichiers ``.consolidate-lock`` ne sont pas des mémoires et sont comptés à
part.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = Path.home() / ".claude" / "projects"
DEFAULT_CODEX = Path.home() / ".codex" / "memories"
DEFAULT_JSON = ROOT / "_audit" / "claude_memory_report.json"
DEFAULT_MARKDOWN = ROOT / "_audit" / "claude_memory_report.md"

KNOWN_TYPES = {"user", "feedback", "reference", "project"}
PERSONAL_NAME_RE = re.compile(r"(?:^|_)(?:user|beneficiaires?|team|numen|orcid)(?:_|\.|$)", re.I)
PERSONAL_CONTENT_RES = [
    re.compile(r"\bNUMEN\b", re.I),
    re.compile(r"\bORCID\b", re.I),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
]
SECRET_RES = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)\b(?:password|passwd|mot de passe|api[_ -]?key|access[_ -]?token|secret)\b\s*[:=]\s*[^\s`]{6,}"),
    re.compile(r"(?i)\b(?:mongodb|postgres(?:ql)?|mysql|redis)://[^\s/:]+:[^\s/@]+@"),
]
INFRA_RES = [
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    re.compile(r"(?i)\bssh\s+[a-z0-9_.@-]+"),
]
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md(?:#[^)]+)?)\)")
WIKI_LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---\n", 4)
    return text[4:end] if end >= 0 else ""


def source_type(path: Path, text: str) -> str:
    if path.name == "MEMORY.md":
        return "index"
    header = frontmatter(text)
    matches = re.findall(r"^\s*type:\s*['\"]?([a-z_-]+)", header, flags=re.M | re.I)
    for candidate in reversed(matches):
        candidate = candidate.lower().replace("_", "-")
        if candidate in KNOWN_TYPES:
            return candidate
    stem = path.stem.lower()
    for candidate in KNOWN_TYPES:
        if stem.startswith(candidate + "_") or stem.startswith(candidate + "-"):
            return candidate
    if stem.startswith(("prefers-", "verify-", "no-", "use-", "soumission-", "voynich-")):
        return "feedback"
    if stem.endswith("-project") or stem.endswith("_project"):
        return "project"
    return "other"


def local_links(path: Path, text: str) -> tuple[int, list[str], int]:
    targets: list[str] = []
    for raw in MARKDOWN_LINK_RE.findall(text):
        target = raw.split("#", 1)[0]
        if "://" not in target and not target.startswith("/"):
            targets.append(target)
    broken = sorted({target for target in targets if not (path.parent / target).exists()})
    return len(targets), broken, len(WIKI_LINK_RE.findall(text))


def routing(kind: str, personal: bool, secret: bool) -> tuple[str, str]:
    if secret or personal:
        return "exclude-sensitive", "private-review"
    if kind == "index":
        return "index-only", "native-extension-index"
    if kind == "user":
        return "deduplicate-user-context", "global-instructions-or-private-kb"
    if kind in {"feedback", "reference"}:
        return "route-durable-knowledge", "shared-kb"
    if kind == "project":
        return "verify-current-state", "project-registers"
    return "manual-review", "undecided"


def freshness(kind: str, infrastructure: bool) -> str:
    if kind == "index":
        return "routing-index"
    if kind == "project" or infrastructure:
        return "potentially-stale-verify-live"
    return "durable-candidate"


def audit_file(path: Path, source: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    kind = source_type(path, text)
    personal = bool(PERSONAL_NAME_RE.search(path.name)) or any(pattern.search(text) for pattern in PERSONAL_CONTENT_RES)
    secret = any(pattern.search(text) for pattern in SECRET_RES)
    infrastructure = any(pattern.search(text) for pattern in INFRA_RES)
    link_count, broken, wiki_links = local_links(path, text)
    decision, destination = routing(kind, personal, secret)
    stat = path.stat()
    relative = path.relative_to(source)
    project_key = relative.parts[0]
    return {
        "path": str(relative),
        "project_key": project_key,
        "filename": path.name,
        "bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "sha256": sha256(path),
        "source_type": kind,
        "freshness": freshness(kind, infrastructure),
        "decision": decision,
        "destination": destination,
        "flags": {
            "personal_identifier": personal,
            "secret_material": secret,
            "infrastructure_locator": infrastructure,
            "broken_local_links": bool(broken),
        },
        "local_links": link_count,
        "wiki_links": wiki_links,
        "broken_local_link_count": len(broken),
    }


def imported_projects(codex_root: Path) -> dict[str, dict[str, Any]]:
    resources = codex_root / "extensions" / "external_agent_import" / "resources"
    result: dict[str, dict[str, Any]] = {}
    if not resources.is_dir():
        return result
    for directory in sorted(path for path in resources.iterdir() if path.is_dir()):
        scope_path = directory / "scope.json"
        cwd = None
        if scope_path.is_file():
            try:
                cwd = json.loads(scope_path.read_text(encoding="utf-8")).get("cwd")
            except (json.JSONDecodeError, AttributeError):
                pass
        result[directory.name] = {
            "cwd": cwd,
            "files": sorted(path.name for path in directory.glob("*.md")),
        }
    return result


def build_report(source: Path, codex_root: Path) -> dict[str, Any]:
    markdown = sorted(source.glob("*/memory/**/*.md"))
    locks = sorted(source.glob("*/memory/.consolidate-lock"))
    records = [audit_file(path, source) for path in markdown]
    exact_groups: dict[str, list[str]] = {}
    for record in records:
        exact_groups.setdefault(record["sha256"], []).append(record["path"])
    duplicates = [paths for paths in exact_groups.values() if len(paths) > 1]
    projects: dict[str, dict[str, Any]] = {}
    for project_key in sorted({record["project_key"] for record in records}):
        members = [record for record in records if record["project_key"] == project_key]
        unsafe = any(
            record["flags"]["personal_identifier"]
            or record["flags"]["secret_material"]
            or record["flags"]["broken_local_links"]
            for record in members
        )
        projects[project_key] = {
            "files": len(members),
            "bytes": sum(record["bytes"] for record in members),
            "source_types": dict(sorted(Counter(record["source_type"] for record in members).items())),
            "sensitive_files": sum(
                record["flags"]["personal_identifier"] or record["flags"]["secret_material"] for record in members
            ),
            "broken_link_files": sum(record["flags"]["broken_local_links"] for record in members),
            "official_import_candidate": not unsafe,
        }
    problems: list[str] = []
    if not records:
        problems.append("aucune mémoire Markdown trouvée")
    if any(record["source_type"] == "other" for record in records):
        problems.append("des fichiers restent sans type sémantique")
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source),
        "codex_memories": str(codex_root),
        "summary": {
            "markdown_files": len(records),
            "technical_locks": len(locks),
            "bytes": sum(record["bytes"] for record in records),
            "projects": len(projects),
            "source_types": dict(sorted(Counter(record["source_type"] for record in records).items())),
            "decisions": dict(sorted(Counter(record["decision"] for record in records).items())),
            "destinations": dict(sorted(Counter(record["destination"] for record in records).items())),
            "freshness": dict(sorted(Counter(record["freshness"] for record in records).items())),
            "personal_identifier_files": sum(record["flags"]["personal_identifier"] for record in records),
            "secret_material_files": sum(record["flags"]["secret_material"] for record in records),
            "infrastructure_locator_files": sum(record["flags"]["infrastructure_locator"] for record in records),
            "broken_local_link_files": sum(record["flags"]["broken_local_links"] for record in records),
            "exact_duplicate_groups": len(duplicates),
        },
        "projects": projects,
        "imported_projects": imported_projects(codex_root),
        "exact_duplicate_groups": duplicates,
        "files": records,
        "problems": problems,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Audit CCX-13 des mémoires Claude",
        "",
        f"Généré le `{report['generated_at']}`.",
        "",
        "Le rapport ne persiste aucune valeur sensible détectée. Les contenus importés restent des sources avec provenance, pas des instructions autoritatives.",
        "",
        "## Synthèse",
        "",
        f"- Mémoires Markdown : {summary['markdown_files']} fichiers, {summary['bytes']} octets.",
        f"- Verrous techniques exclus : {summary['technical_locks']}.",
        f"- Répertoires projet : {summary['projects']}.",
        f"- Types : {json.dumps(summary['source_types'], ensure_ascii=False, sort_keys=True)}.",
        f"- Destinations : {json.dumps(summary['destinations'], ensure_ascii=False, sort_keys=True)}.",
        f"- Fraîcheur : {json.dumps(summary['freshness'], ensure_ascii=False, sort_keys=True)}.",
        f"- Fichiers avec identifiant personnel : {summary['personal_identifier_files']}.",
        f"- Fichiers avec secret potentiel : {summary['secret_material_files']}.",
        f"- Fichiers avec localisateur d'infrastructure : {summary['infrastructure_locator_files']}.",
        f"- Fichiers avec lien local cassé : {summary['broken_local_link_files']}.",
        f"- Groupes de doublons exacts : {summary['exact_duplicate_groups']}.",
        "",
        "## Projets source",
        "",
        "| Clé Claude | Fichiers | Octets | Sensibles | Liens cassés | Candidat import officiel |",
        "|---|---:|---:|---:|---:|:---:|",
    ]
    for key, project in report["projects"].items():
        lines.append(
            f"| `{key}` | {project['files']} | {project['bytes']} | {project['sensitive_files']} | "
            f"{project['broken_link_files']} | {'oui' if project['official_import_candidate'] else 'non'} |"
        )
    lines.extend(["", "## Imports natifs observés", ""])
    if report["imported_projects"]:
        for key, imported in report["imported_projects"].items():
            lines.append(f"- `{key}` : cwd `{imported['cwd']}`, {len(imported['files'])} fichiers Markdown.")
    else:
        lines.append("- Aucun.")
    lines.extend(["", "## Contrôles", ""])
    lines.extend(f"- ÉCHEC : {problem}" for problem in report["problems"])
    if not report["problems"]:
        lines.append("- OK : inventaire complet et tous les fichiers ont un type sémantique.")
    lines.append("")
    return "\n".join(lines)


def stable_for_check(report: dict[str, Any]) -> dict[str, Any]:
    copy = json.loads(json.dumps(report))
    copy.pop("generated_at", None)
    return copy


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--codex-memories", type=Path, default=DEFAULT_CODEX)
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = build_report(args.source.expanduser(), args.codex_memories.expanduser())
    markdown = render_markdown(report)
    if args.check:
        if not args.json.is_file() or not args.markdown.is_file():
            print("ÉCHEC : rapports CCX-13 absents")
            return 1
        previous = json.loads(args.json.read_text(encoding="utf-8"))
        if stable_for_check(previous) != stable_for_check(report):
            print("ÉCHEC : rapport JSON CCX-13 périmé")
            return 1
        previous_markdown = args.markdown.read_text(encoding="utf-8")
        previous_markdown = re.sub(r"Généré le `[^`]+`\.", "Généré le `<timestamp>`.", previous_markdown)
        current_markdown = re.sub(r"Généré le `[^`]+`\.", "Généré le `<timestamp>`.", markdown)
        if previous_markdown != current_markdown:
            print("ÉCHEC : rapport Markdown CCX-13 périmé")
            return 1
    else:
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        args.markdown.write_text(markdown, encoding="utf-8")
    if report["problems"]:
        for problem in report["problems"]:
            print(f"ÉCHEC : {problem}")
        return 1
    print(
        f"OK : {report['summary']['markdown_files']} mémoires, "
        f"{report['summary']['projects']} projets, "
        f"{len(report['imported_projects'])} import natif"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
