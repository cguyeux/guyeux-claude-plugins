#!/usr/bin/env python3
"""Inventorier la couverture Codex des instructions projet Claude.

Le script est en lecture seule vis-a-vis des projets. Il ne transforme aucun
`CLAUDE.md` et ne cree aucun `AGENTS.md`. Les signaux d'activite sont des faits
de triage, jamais un verdict automatique sur le cycle de vie d'un projet.

Usage :
    python3 _audit/tools/audit_project_instructions.py
    python3 _audit/tools/audit_project_instructions.py --check
    python3 _audit/tools/audit_project_instructions.py --scan-root /chemin
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCAN_ROOT = Path.home() / "docs" / "codes"
DEFAULT_JSON = ROOT / "_audit" / "project_instruction_report.json"
DEFAULT_MARKDOWN = ROOT / "_audit" / "project_instruction_report.md"
DEFAULT_MAX_BYTES = 32_768
REGISTER_NAMES = (
    "cahier_de_labo.md",
    "etat_des_decouvertes.md",
    "pistes.md",
    "JOURNAL.md",
    "TASKS.md",
)
ARCHIVE_PARTS = {
    "abandonne",
    "abandonné",
    "archive",
    "archives",
    "archived",
    "fini",
    "obsolete",
    "projets_abandonnes",
}
EXCLUDED_PROJECT_PARTS = {
    ".agents",
    ".claude",
    ".codex",
    ".venv",
    "__pycache__",
    "node_modules",
    "venv",
}
IGNORED_TRANSIENT_PREFIXES = ("claude_plugins_index_",)
OPEN_STATUS_RE = re.compile(
    r"(?:^\s*[-*]\s*\[\s\]\s+|\[(?:a faire|à faire|en cours|partiel(?:le)?|bloqu[eé]e?)\]|"
    r"\|\s*(?:a faire|à faire|en cours|partiel(?:le)?|bloqu[eé]e?)\s*\|)",
    re.IGNORECASE,
)


def project_files(scan_root: Path) -> tuple[list[Path], list[dict[str, str]]]:
    found: list[Path] = []
    excluded: list[dict[str, str]] = []
    for current, dirnames, filenames in os.walk(scan_root, followlinks=False):
        dirnames[:] = sorted(name for name in dirnames if name != ".git")
        if "CLAUDE.md" in filenames:
            claude_md = Path(current) / "CLAUDE.md"
            relative = claude_md.parent.relative_to(scan_root)
            if relative.parts and relative.parts[0].startswith(IGNORED_TRANSIENT_PREFIXES):
                continue
            if is_protection_snapshot(claude_md.parent):
                excluded.append(
                    {
                        "path": relative.as_posix(),
                        "reason": "protection-backup-snapshot",
                    }
                )
                continue
            excluded_part = next((part for part in relative.parts if excluded_project_part(part)), None)
            if excluded_part is None:
                found.append(claude_md)
            else:
                excluded.append(
                    {
                        "path": relative.as_posix(),
                        "reason": f"internal-or-dependency-directory:{excluded_part}",
                    }
                )
    return sorted(found), sorted(excluded, key=lambda row: row["path"])


def is_protection_snapshot(project_dir: Path) -> bool:
    """Un `CLAUDE.md` posé sous un dossier `avant*/` dont le parent porte
    `protection_avant.json` est une sauvegarde de protection prise avant une tache
    (`résultats/<tache>/avant_registres/`, cf. lineaire_a), pas un projet actif : aucune
    session Codex n'y travaille, la reduire romprait l'integrite du snapshot."""
    parent = project_dir.parent
    return project_dir.name.startswith("avant") and (parent / "protection_avant.json").is_file()


def excluded_project_part(part: str) -> bool:
    folded = part.casefold()
    return (
        folded in EXCLUDED_PROJECT_PARTS
        or folded in {"site-packages", "dist-packages"}
        or folded.startswith(".venv")
        or folded.startswith("venv_")
    )


def has_open_work(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return any(OPEN_STATUS_RE.search(line) for line in text.splitlines())


def date_from_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone().date().isoformat()


def nearest_git_root(project: Path, scan_root: Path) -> Path:
    current = project
    while True:
        if valid_git_marker(current / ".git"):
            return current
        if current == scan_root:
            return project
        current = current.parent


def valid_git_marker(marker: Path) -> bool:
    if marker.is_file():
        return marker.read_text(encoding="utf-8", errors="replace").startswith("gitdir:")
    if not marker.is_dir():
        return False
    return (marker / "HEAD").is_file() and (
        (marker / "objects").is_dir() or (marker / "commondir").is_file()
    )


def instruction_chain(project: Path, scan_root: Path) -> tuple[Path, list[Path]]:
    git_root = nearest_git_root(project, scan_root)
    relative = project.relative_to(git_root)
    directories = [git_root]
    current = git_root
    for part in relative.parts:
        current = current / part
        directories.append(current)
    selected: list[Path] = []
    for directory in directories:
        override = directory / "AGENTS.override.md"
        agents = directory / "AGENTS.md"
        claude = directory / "CLAUDE.md"
        if override.is_file():
            selected.append(override)
        elif agents.is_file():
            selected.append(agents)
        elif claude.is_file():
            selected.append(claude)
    return git_root, selected


def classify(
    *,
    agents_local: bool,
    chain_over_budget: bool,
    open_signals: list[str],
    archive_signal: bool,
) -> str:
    if chain_over_budget:
        return "instruction-chain-over-budget"
    if agents_local:
        return "agents-local"
    if archive_signal:
        return "fallback-archive-signal"
    if open_signals:
        return "fallback-active-signal"
    return "fallback-review-required"


def inspect_project(claude_md: Path, scan_root: Path, max_bytes: int) -> dict[str, Any]:
    project = claude_md.parent
    agents = project / "AGENTS.md"
    override = project / "AGENTS.override.md"
    registers = [name for name in REGISTER_NAMES if (project / name).is_file()]
    open_signals = [name for name in ("pistes.md", "TASKS.md") if has_open_work(project / name)]
    relative = project.relative_to(scan_root)
    archive_signal = any(part.casefold() in ARCHIVE_PARTS for part in relative.parts)
    claude_bytes = claude_md.stat().st_size
    git_root, selected_chain = instruction_chain(project, scan_root)
    chain_bytes = sum(path.stat().st_size for path in selected_chain)
    chain_over_budget = chain_bytes > max_bytes
    local_docs = [claude_md, *(project / name for name in registers)]
    if agents.is_file():
        local_docs.append(agents)
    latest = max(local_docs, key=lambda path: path.stat().st_mtime)
    agents_local = agents.is_file()
    override_local = override.is_file()
    over_budget = claude_bytes > max_bytes
    return {
        "path": relative.as_posix() if relative.parts else ".",
        "claude_bytes": claude_bytes,
        "claude_modified": date_from_mtime(claude_md),
        "latest_local_doc_modified": date_from_mtime(latest),
        "agents_local": agents_local,
        "agents_override_local": override_local,
        "claude_over_budget": over_budget,
        "git_root": git_root.relative_to(scan_root).as_posix()
        if git_root != scan_root
        else ".",
        "instruction_chain": [
            path.relative_to(scan_root).as_posix() for path in selected_chain
        ],
        "instruction_chain_bytes": chain_bytes,
        "instruction_chain_over_budget": chain_over_budget,
        "registers": registers,
        "open_work_signals": open_signals,
        "archive_path_signal": archive_signal,
        "classification": classify(
            agents_local=agents_local,
            chain_over_budget=chain_over_budget,
            open_signals=open_signals,
            archive_signal=archive_signal,
        ),
    }


def build_report(scan_root: Path, max_bytes: int = DEFAULT_MAX_BYTES) -> dict[str, Any]:
    scan_root = scan_root.expanduser().resolve()
    included, excluded = project_files(scan_root)
    rows = [inspect_project(path, scan_root, max_bytes) for path in included]
    classes = Counter(row["classification"] for row in rows)
    return {
        "schema_version": 1,
        "scan_root": str(scan_root),
        "project_doc_max_bytes": max_bytes,
        "summary": {
            "discovered_claude_files": len(rows) + len(excluded),
            "project_claude_files": len(rows),
            "excluded_internal_or_dependency": len(excluded),
            "agents_local": sum(row["agents_local"] for row in rows),
            "agents_override_local": sum(row["agents_override_local"] for row in rows),
            "fallback_only": sum(not row["agents_local"] for row in rows),
            "claude_over_budget": sum(row["claude_over_budget"] for row in rows),
            "fallback_over_budget": sum(
                row["claude_over_budget"] and not row["agents_local"] for row in rows
            ),
            "instruction_chains_over_budget": sum(
                row["instruction_chain_over_budget"] for row in rows
            ),
            "classifications": dict(sorted(classes.items())),
        },
        "excluded": excluded,
        "rows": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    classes = summary["classifications"]
    lines = [
        "# Couverture des instructions projet Claude vers Codex",
        "",
        "Rapport deterministe de CCX-03. Les signaux d'activite servent au triage",
        "et ne ferment ni n'archivent automatiquement aucun projet.",
        "",
        "## Resume",
        "",
        f"- Racine auditee : `{report['scan_root']}`",
        f"- Budget par fichier : {report['project_doc_max_bytes']} octets",
        f"- `CLAUDE.md` bruts decouverts : {summary['discovered_claude_files']}",
        f"- Instructions de projets retenues : {summary['project_claude_files']}",
        f"- Copies internes ou dependances exclues : {summary['excluded_internal_or_dependency']}",
        f"- Avec `AGENTS.md` local : {summary['agents_local']}",
        f"- Avec `AGENTS.override.md` local : {summary['agents_override_local']}",
        f"- Fallback seul : {summary['fallback_only']}",
        f"- `CLAUDE.md` au-dessus du budget : {summary['claude_over_budget']}",
        f"- Fallback seul au-dessus du budget : {summary['fallback_over_budget']}",
        f"- Chaines d'instructions au-dessus du budget : {summary['instruction_chains_over_budget']}",
        "",
        "## Classes de triage",
        "",
        "| Classe | Nombre | Portee |",
        "|---|---:|---|",
        f"| `agents-local` | {classes.get('agents-local', 0)} | Couche Codex locale presente |",
        f"| `instruction-chain-over-budget` | {classes.get('instruction-chain-over-budget', 0)} | Remediation prioritaire |",
        f"| `fallback-active-signal` | {classes.get('fallback-active-signal', 0)} | Travail ouvert explicitement signale |",
        f"| `fallback-archive-signal` | {classes.get('fallback-archive-signal', 0)} | Chemin d'archive, a confirmer |",
        f"| `fallback-review-required` | {classes.get('fallback-review-required', 0)} | Activite indeterminee, decision humaine |",
        "",
        "## Inventaire complet",
        "",
        "| Projet | CLAUDE | Chaine | AGENTS | Registres | Signaux ouverts | Dernier document | Classe |",
        "|---|---:|---:|:---:|---|---|---|---|",
    ]
    for row in report["rows"]:
        registers = ", ".join(row["registers"]) or "-"
        signals = ", ".join(row["open_work_signals"]) or "-"
        lines.append(
            f"| `{row['path']}` | {row['claude_bytes']} | {row['instruction_chain_bytes']} | "
            f"{'oui' if row['agents_local'] else 'non'} | {registers} | {signals} | "
            f"{row['latest_local_doc_modified']} | `{row['classification']}` |"
        )
    lines.extend(
        [
            "",
            "## Exclusions de perimetre",
            "",
            "Les chemins sous `.claude`, `.codex`, `.agents`, environnements Python,",
            "`node_modules` et caches Python sont comptes dans le total brut mais ne",
            "sont jamais traites comme des projets. La liste exacte et la raison de",
            "chaque exclusion sont conservees dans le rapport JSON.",
            "",
            "## Regle de decision",
            "",
            "Un signal ouvert provient uniquement d'une case Markdown non cochee ou",
            "d'un statut explicite dans `pistes.md` ou `TASKS.md`. Une date recente,",
            "la presence d'un depot Git ou un nom de domaine ne suffisent jamais a",
            "declarer un projet actif. Les lignes `fallback-review-required` exigent",
            "donc un arbitrage humain ou une preuve dans le registre du projet.",
            "",
        ]
    )
    return "\n".join(lines)


def json_text(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def check_file(path: Path, expected: str) -> bool:
    return path.is_file() and path.read_text(encoding="utf-8") == expected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan-root", type=Path, default=DEFAULT_SCAN_ROOT)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    report = build_report(args.scan_root, args.max_bytes)
    expected_json = json_text(report)
    expected_markdown = render_markdown(report)
    if args.check:
        stale = []
        if not check_file(args.json_output, expected_json):
            stale.append(str(args.json_output))
        if not check_file(args.markdown_output, expected_markdown):
            stale.append(str(args.markdown_output))
        if stale:
            print(f"ECHEC : rapports projet obsoletes : {', '.join(stale)}", file=sys.stderr)
            return 1
    else:
        args.json_output.write_text(expected_json, encoding="utf-8")
        args.markdown_output.write_text(expected_markdown, encoding="utf-8")

    summary = report["summary"]
    print(
        "OK : "
        f"{summary['discovered_claude_files']} CLAUDE.md bruts, "
        f"{summary['project_claude_files']} projets retenus, "
        f"{summary['agents_local']} avec AGENTS.md, "
        f"{summary['fallback_only']} fallback seuls, "
        f"{summary['fallback_over_budget']} fallback au-dessus du budget, "
        f"{summary['instruction_chains_over_budget']} chaines au-dessus du budget"
    )
    for name, count in summary["classifications"].items():
        print(f"{name}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
