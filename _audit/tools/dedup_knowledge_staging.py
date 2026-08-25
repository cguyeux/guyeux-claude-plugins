#!/usr/bin/env python3
"""Dedoublonne les fichiers KB canoniques crees en staging CCX-04.

Le script ne lit que ``~/.agents/knowledge``. Il remplace les fichiers contenant
les marqueurs ``BEGIN CLAUDE/CODEX KNOWLEDGE SOURCE`` par une version canonique
sans marqueur de staging :

- quand la source Codex est seulement un pointeur vers Claude, conserver Claude ;
- pour ``KNOWLEDGE.md``, conserver l'index Claude et ajouter les pointeurs Codex
  absents ;
- pour les fiches a entrees, conserver Claude comme historique principal et
  importer la source Codex sous une section separee datee.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


DEFAULT_ROOT = Path.home() / ".agents" / "knowledge"
DEFAULT_CLAUDE_ROOT = Path.home() / ".claude" / "knowledge"
DEFAULT_CODEX_ROOT = Path.home() / ".Codex" / "knowledge"
STAGED = [
    "KNOWLEDGE.md",
    "collaborators.md",
    "deployment.md",
    "linux-desktop.md",
    "predictops.md",
    "python-patterns.md",
    "scientific-journals.md",
]


class StagingFormatError(RuntimeError):
    pass


def split_sources(text: str) -> tuple[str, str]:
    try:
        claude = text.split("<!-- BEGIN CLAUDE KNOWLEDGE SOURCE -->", 1)[1].split(
            "<!-- END CLAUDE KNOWLEDGE SOURCE -->", 1
        )[0]
        codex = text.split("<!-- BEGIN CODEX KNOWLEDGE SOURCE -->", 1)[1].split(
            "<!-- END CODEX KNOWLEDGE SOURCE -->", 1
        )[0]
    except IndexError as exc:
        raise StagingFormatError("marqueurs de staging absents ou incomplets") from exc
    return claude.strip() + "\n", codex.strip() + "\n"


def strip_h1(markdown: str) -> str:
    lines = markdown.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:]).strip() + "\n"
    return markdown.strip() + "\n"


def codex_is_pointer(codex: str) -> bool:
    return "historique canonique est conservée" in codex or "historique canonique est conservee" in codex


def import_section(title: str, codex: str) -> str:
    body = strip_h1(codex).strip()
    if not body:
        return ""
    return "\n".join(
        [
            "",
            f"## {title}",
            "",
            "<!-- Import CCX-04 depuis l'ancienne vue ~/.Codex/knowledge. -->",
            "",
            body,
            "",
        ]
    )


def merge_knowledge_index(claude: str, codex: str) -> str:
    bullets = []
    existing = set(re.findall(r"\]\(([^)]+)\)", claude))
    for line in codex.splitlines():
        match = re.match(r"^- `([^`]+)`\s*:\s*(.+)$", line)
        if not match:
            continue
        target, description = match.groups()
        if target in existing or target in claude:
            continue
        bullets.append(f"- [{target}]({target}) — {description}")
    if not bullets:
        return claude.rstrip() + "\n"
    return "\n".join(
        [
            claude.rstrip(),
            "",
            "## Entrées Codex importées le 2026-08-25",
            "",
            "<!-- Import CCX-04 depuis l'ancienne vue ~/.Codex/knowledge. -->",
            "",
            *bullets,
            "",
        ]
    )


def merge_file(relative: str, text: str) -> str:
    claude, codex = split_sources(text)
    if codex_is_pointer(codex):
        return claude
    if relative == "KNOWLEDGE.md":
        return merge_knowledge_index(claude, codex)
    section_titles = {
        "collaborators.md": "Entrées Codex importées le 2026-08-25",
        "deployment.md": "Entrées Codex importées le 2026-08-25",
        "python-patterns.md": "Entrées Codex importées le 2026-08-25",
        "scientific-journals.md": "Entrées Codex importées le 2026-08-25",
    }
    title = section_titles.get(relative, "Entrées Codex importées le 2026-08-25")
    return claude.rstrip() + import_section(title, codex)


def dedup(root: Path) -> dict[str, int]:
    counts = {"rewritten": 0, "skipped": 0}
    for relative in STAGED:
        path = root / relative
        if not path.is_file():
            counts["skipped"] += 1
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "needs-human-dedup" not in text and "BEGIN CLAUDE KNOWLEDGE SOURCE" not in text:
            counts["skipped"] += 1
            continue
        merged = merge_file(relative, text)
        path.write_text(merged, encoding="utf-8")
        counts["rewritten"] += 1
    return counts


def rebuild_from_sources(root: Path, claude_root: Path, codex_root: Path) -> dict[str, int]:
    counts = {"rewritten": 0, "skipped": 0}
    root.mkdir(parents=True, exist_ok=True)
    for relative in STAGED:
        claude_path = claude_root / relative
        codex_path = codex_root / relative
        if not claude_path.is_file() or not codex_path.is_file():
            counts["skipped"] += 1
            continue
        staged_text = "\n".join(
            [
                "<!-- status: needs-human-dedup -->",
                "<!-- BEGIN CLAUDE KNOWLEDGE SOURCE -->",
                claude_path.read_text(encoding="utf-8", errors="replace").rstrip(),
                "<!-- END CLAUDE KNOWLEDGE SOURCE -->",
                "<!-- BEGIN CODEX KNOWLEDGE SOURCE -->",
                codex_path.read_text(encoding="utf-8", errors="replace").rstrip(),
                "<!-- END CODEX KNOWLEDGE SOURCE -->",
                "",
            ]
        )
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(merge_file(relative, staged_text), encoding="utf-8")
        counts["rewritten"] += 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--claude-root", type=Path, default=DEFAULT_CLAUDE_ROOT)
    parser.add_argument("--codex-root", type=Path, default=DEFAULT_CODEX_ROOT)
    parser.add_argument(
        "--rebuild-from-sources",
        action="store_true",
        help="reconstruire les 7 fichiers homologues depuis ~/.claude/knowledge et ~/.Codex/knowledge",
    )
    args = parser.parse_args()
    if args.rebuild_from_sources:
        counts = rebuild_from_sources(
            args.root.expanduser(), args.claude_root.expanduser(), args.codex_root.expanduser()
        )
    else:
        counts = dedup(args.root.expanduser())
    print("OK : rewritten={rewritten}, skipped={skipped}".format(**counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
