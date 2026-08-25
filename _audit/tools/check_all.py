#!/usr/bin/env python3
"""Harnais de validation complet de la migration Claude/Codex.

Ce script orchestre les controles reproductibles sans modifier les fermes
utilisateur. Il echoue au premier controle en erreur et affiche la commande
exacte a relancer.

Usage :
    python3 _audit/tools/check_all.py
    python3 _audit/tools/check_all.py --profile-root ~/.codex
    python3 _audit/tools/check_all.py --source git-index --profile-root ~/.codex
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def build_commands(profile_root: Path) -> list[list[str]]:
    return build_internal_commands() + build_external_farm_commands(profile_root)


def build_internal_commands() -> list[list[str]]:
    return [
        [sys.executable, "_audit/tools/generate_canon_skills.py", "--check"],
        [sys.executable, "_audit/tools/generate_codex_package_matrix.py", "--check"],
        [sys.executable, "_audit/tools/generate_codex_runtime_adaptation_matrix.py", "--check"],
        [sys.executable, "docs/build_docs.py", "--check"],
        [sys.executable, "_audit/tools/audit_skills.py", "--detail"],
        [sys.executable, "_audit/tools/audit_project_instructions.py", "--check"],
        [sys.executable, "-m", "unittest", "discover", "-s", "_audit/tests"],
    ]


def build_external_farm_commands(profile_root: Path) -> list[list[str]]:
    return [
        [sys.executable, "_audit/tools/sync_codex_skills.py"],
        [sys.executable, "_audit/tools/sync_agent_skills.py"],
        [sys.executable, "_audit/tools/report_agent_skill_divergences.py", "--check"],
        [sys.executable, "_audit/tools/audit_personal_workflow_skills.py", "--check"],
        [sys.executable, "_audit/tools/audit_codex_hooks.py", "--check"],
        [sys.executable, "_audit/tools/sync_knowledge_base.py", "--check"],
        [sys.executable, "_audit/tools/publish_knowledge_views.py", "--check"],
        [sys.executable, "_audit/tools/audit_codex_skill_farm.py", "--profile-root", str(profile_root)],
    ]


def display_command(command: list[str]) -> str:
    return " ".join(command)


def git_output(args: list[str], cwd: Path = ROOT) -> str:
    completed = subprocess.run(["git", *args], cwd=cwd, check=True, text=True, stdout=subprocess.PIPE)
    return completed.stdout.strip()


def trash_path(path: Path) -> None:
    gio = shutil.which("gio")
    if gio is None:
        print(f"NOTE : gio indisponible, projection conservee : {path}", file=sys.stderr)
        return
    completed = subprocess.run([gio, "trash", str(path)], check=False)
    if completed.returncode != 0:
        print(f"NOTE : mise a la corbeille impossible, projection conservee : {path}", file=sys.stderr)


def create_index_projection() -> Path:
    tree = git_output(["write-tree"])
    target = Path(tempfile.mkdtemp(prefix="claude_plugins_index_", dir=str(ROOT.parent)))
    archive = subprocess.Popen(["git", "archive", tree], cwd=ROOT, stdout=subprocess.PIPE)
    try:
        completed = subprocess.run(["tar", "-x", "-C", str(target)], stdin=archive.stdout, check=False)
        if archive.stdout is not None:
            archive.stdout.close()
        archive_code = archive.wait()
        if completed.returncode != 0 or archive_code != 0:
            raise RuntimeError(f"projection Git impossible: git archive={archive_code}, tar={completed.returncode}")
    except Exception:
        trash_path(target)
        raise
    return target


def run_all(profile_root: Path, root: Path = ROOT) -> int:
    for command in build_commands(profile_root):
        print(f"\n$ {display_command(command)}", flush=True)
        completed = subprocess.run(command, cwd=root, check=False)
        if completed.returncode != 0:
            print(f"\nECHEC : {display_command(command)}", file=sys.stderr)
            return completed.returncode
    print("\nValidation complete OK.")
    return 0


def run_commands(commands: list[list[str]], root: Path) -> int:
    for command in commands:
        print(f"\n$ {display_command(command)}", flush=True)
        completed = subprocess.run(command, cwd=root, check=False)
        if completed.returncode != 0:
            print(f"\nECHEC : {display_command(command)}", file=sys.stderr)
            return completed.returncode
    return 0


def run_index_projection(profile_root: Path) -> int:
    projection = create_index_projection()
    print(f"Projection Git index : {projection}")
    try:
        code = run_commands(build_internal_commands(), projection)
        if code != 0:
            return code
    finally:
        trash_path(projection)
    code = run_commands(build_external_farm_commands(profile_root), ROOT)
    if code != 0:
        return code
    print("\nValidation complete OK.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile-root", type=Path, default=Path.home() / ".codex", help="profil Codex a auditer")
    parser.add_argument(
        "--source",
        choices=("worktree", "git-index"),
        default="worktree",
        help="source a valider ; git-index ignore les brouillons non stages en projetant l'index courant",
    )
    args = parser.parse_args()
    profile_root = args.profile_root.expanduser()
    if args.source == "worktree":
        return run_all(profile_root, ROOT)
    return run_index_projection(profile_root)


if __name__ == "__main__":
    raise SystemExit(main())
