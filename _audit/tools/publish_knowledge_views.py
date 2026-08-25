#!/usr/bin/env python3
"""Publie les vues historiques de KB vers la source canonique neutre.

CCX-04 choisit ``~/.agents/knowledge`` comme racine canonique. Ce script rend
les chemins historiques ``~/.claude/knowledge`` et ``~/.Codex/knowledge``
visibles comme liens symboliques vers ce canonique, apres sauvegarde
recoverable des repertoires existants.

Il ne supprime rien. Les anciennes vues sont deplacees vers
``~/.agents/migration/backups/knowledge_views/<timestamp>/``.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil


DEFAULT_CANONICAL = Path.home() / ".agents" / "knowledge"
DEFAULT_BACKUP_ROOT = Path.home() / ".agents" / "migration" / "backups" / "knowledge_views"
DEFAULT_VIEWS = [Path.home() / ".claude" / "knowledge", Path.home() / ".Codex" / "knowledge"]
STAGING_MARKERS = (
    "status: needs-human-dedup",
    "<!-- BEGIN CLAUDE KNOWLEDGE SOURCE -->",
    "<!-- BEGIN CODEX KNOWLEDGE SOURCE -->",
)


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def included_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return [path for path in root.rglob("*") if path.is_file()]


def canonical_is_ready(canonical: Path) -> tuple[bool, list[str]]:
    problems: list[str] = []
    if not canonical.is_dir():
        problems.append(f"canonical missing: {canonical}")
        return False, problems
    files = included_files(canonical)
    if not files:
        problems.append(f"canonical empty: {canonical}")
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(marker in text for marker in STAGING_MARKERS):
            problems.append(f"staging marker remains: {path.relative_to(canonical)}")
    return not problems, problems


def is_correct_symlink(path: Path, canonical: Path) -> bool:
    return path.is_symlink() and path.resolve() == canonical.resolve()


def backup_name_for(view: Path) -> str:
    parent = view.parent.name.replace(".", "") or "root"
    return f"{parent}_{view.name}"


def publish_view(view: Path, canonical: Path, backup_dir: Path, apply: bool) -> str:
    if is_correct_symlink(view, canonical):
        return f"ok-already-linked:{view}"
    if view.exists() or view.is_symlink():
        destination = backup_dir / backup_name_for(view)
        if destination.exists():
            raise RuntimeError(f"backup destination already exists: {destination}")
        if apply:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(view), str(destination))
        action = f"backup:{view}->{destination}"
    else:
        action = f"create:{view}"
    if apply:
        view.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(canonical, view, target_is_directory=True)
    return f"{action}; link:{view}->{canonical}"


def check_views(canonical: Path, views: list[Path]) -> list[str]:
    problems: list[str] = []
    ready, canonical_problems = canonical_is_ready(canonical)
    if not ready:
        problems.extend(canonical_problems)
    for view in views:
        if not is_correct_symlink(view, canonical):
            problems.append(f"not-linked:{view}")
    return problems


def publish(canonical: Path, views: list[Path], backup_root: Path, apply: bool) -> list[str]:
    ready, problems = canonical_is_ready(canonical)
    if not ready:
        raise RuntimeError("; ".join(problems))
    backup_dir = backup_root / timestamp()
    actions = []
    for view in views:
        actions.append(publish_view(view, canonical, backup_dir, apply))
    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical", type=Path, default=DEFAULT_CANONICAL)
    parser.add_argument("--backup-root", type=Path, default=DEFAULT_BACKUP_ROOT)
    parser.add_argument("--view", type=Path, action="append", default=None, help="vue a publier ; repetable")
    parser.add_argument("--apply", action="store_true", help="deplacer les anciennes vues et creer les symlinks")
    parser.add_argument("--check", action="store_true", help="verifier que les vues pointent deja vers le canonique")
    args = parser.parse_args()
    canonical = args.canonical.expanduser()
    backup_root = args.backup_root.expanduser()
    views = [path.expanduser() for path in (args.view if args.view is not None else DEFAULT_VIEWS)]

    if args.check:
        problems = check_views(canonical, views)
        if problems:
            for problem in problems:
                print(problem)
            return 1
        print("OK : knowledge views linked to canonical")
        return 0

    actions = publish(canonical, views, backup_root, args.apply)
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(mode)
    for action in actions:
        print(action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
