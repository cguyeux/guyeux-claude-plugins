#!/usr/bin/env python3
"""Audit CCX-05 des skills personnels de workflow importes dans Agents.

Le controle porte sur les sept skills Claude-only importes durablement dans
``~/.agents/skills``. Il verifie la presence du payload attendu, l'absence de
cache Python copie et l'absence de references canoniques Claude obsoletes dans
les copies Agents.

Usage :
    python3 _audit/tools/audit_personal_workflow_skills.py
    python3 _audit/tools/audit_personal_workflow_skills.py --check
    python3 _audit/tools/audit_personal_workflow_skills.py --agents-root /tmp/agents
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AGENTS_ROOT = Path.home() / ".agents" / "skills"
JSON_OUT = ROOT / "_audit" / "personal_workflow_skill_report.json"
MD_OUT = ROOT / "_audit" / "personal_workflow_skill_report.md"

EXPECTED_FILES = {
    "challenge": ["SKILL.md"],
    "cycle-projet": [
        "SKILL.md",
        "cycle_status.py",
        "references/plugins.md",
        "references/soumission.md",
    ],
    "etat": ["SKILL.md"],
    "legifrance-query": [
        "SKILL.md",
        "scripts/legifrance.py",
    ],
    "pistes": [
        "SKILL.md",
        "archive_closed_pistes.py",
        "split_pistes_files.py",
    ],
    "qcm-generator": [
        "SKILL.md",
        "references/question-design.md",
        "scripts/build_qcm.py",
    ],
    "recadrage": [
        "SKILL.md",
        "recadrage_signals.py",
    ],
}

FORBIDDEN_PATTERNS = (
    "~/.claude/skills",
    "~/.claude/knowledge",
    "~/.Codex/knowledge",
    ".claude/settings.json",
    "CLAUDE.md",
)
EXCLUDED_NAMES = {".venv", "venv"}
PYTHON_SUFFIXES = {".py"}


def included_files(skill_root: Path) -> list[Path]:
    if not skill_root.is_dir():
        return []
    files: list[Path] = []
    for path in skill_root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(skill_root)
        if any(part in EXCLUDED_NAMES for part in relative.parts):
            continue
        files.append(path)
    return sorted(files)


def relative(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


def text_matches(path: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except UnicodeDecodeError:
        return findings
    for lineno, line in enumerate(text.splitlines(), 1):
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in line:
                findings.append({"line": lineno, "pattern": pattern, "text": line.strip()})
    return findings


def compile_python(path: Path) -> str | None:
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    except SyntaxError as exc:
        return f"{exc.msg} at line {exc.lineno}"
    return None


def audit_skill(name: str, agents_root: Path) -> dict[str, Any]:
    skill_root = agents_root / name
    expected = EXPECTED_FILES[name]
    missing = [item for item in expected if not (skill_root / item).is_file()]
    forbidden_files: list[str] = []
    pyc_files: list[str] = []
    forbidden_refs: dict[str, list[dict[str, Any]]] = {}
    syntax_errors: dict[str, str] = {}

    for path in included_files(skill_root):
        rel = relative(path, skill_root)
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            pyc_files.append(rel)
        if path.suffix in {".md", ".py", ".txt", ".json", ".yaml", ".yml", ".toml"}:
            matches = text_matches(path)
            if matches:
                forbidden_refs[rel] = matches
        if path.suffix in PYTHON_SUFFIXES:
            error = compile_python(path)
            if error:
                syntax_errors[rel] = error

    ok = bool(skill_root.is_dir()) and not missing and not pyc_files and not forbidden_refs and not syntax_errors
    return {
        "name": name,
        "present": skill_root.is_dir(),
        "expected_files": expected,
        "missing_files": missing,
        "pyc_or_cache_files": pyc_files,
        "forbidden_references": forbidden_refs,
        "python_syntax_errors": syntax_errors,
        "ok": ok,
    }


def build_report(agents_root: Path = DEFAULT_AGENTS_ROOT) -> dict[str, Any]:
    agents_root = agents_root.expanduser()
    rows = [audit_skill(name, agents_root) for name in sorted(EXPECTED_FILES)]
    problems = []
    for row in rows:
        if not row["ok"]:
            problems.append(row["name"])
    return {
        "agents_root": str(agents_root),
        "expected_total": len(EXPECTED_FILES),
        "ok_total": sum(1 for row in rows if row["ok"]),
        "problems": problems,
        "forbidden_patterns": list(FORBIDDEN_PATTERNS),
        "rows": rows,
        "ok": not problems,
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Rapport CCX-05 des skills personnels de workflow",
        "",
        "Ce fichier est genere par `_audit/tools/audit_personal_workflow_skills.py`.",
        "",
        f"- Racine Agents : `{report['agents_root']}`",
        f"- Skills attendus : {report['expected_total']}",
        f"- Skills OK : {report['ok_total']}",
        f"- Statut : {'OK' if report['ok'] else 'ECHEC'}",
        "",
        "| skill | present | missing | cache/bytecode | refs interdites | syntaxe Python | statut |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["rows"]:
        lines.append(
            "| {name} | {present} | {missing} | {cache} | {refs} | {syntax} | {status} |".format(
                name=row["name"],
                present="oui" if row["present"] else "non",
                missing=len(row["missing_files"]),
                cache=len(row["pyc_or_cache_files"]),
                refs=sum(len(items) for items in row["forbidden_references"].values()),
                syntax=len(row["python_syntax_errors"]),
                status="OK" if row["ok"] else "ECHEC",
            )
        )
    lines.append("")
    return "\n".join(lines)


def expected_outputs(report: dict[str, Any]) -> tuple[str, str]:
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n", markdown(report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agents-root", type=Path, default=DEFAULT_AGENTS_ROOT)
    parser.add_argument("--check", action="store_true", help="echouer si le rapport versionne est stale")
    args = parser.parse_args()

    report = build_report(args.agents_root)
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

    print(f"OK : {report['ok_total']}/{report['expected_total']} skills personnels controles")
    if report["problems"]:
        print("Problemes: " + ", ".join(report["problems"]))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
