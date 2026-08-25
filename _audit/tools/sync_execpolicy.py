#!/usr/bin/env python3
"""Installer la politique execpolicy versionnée sans suppression.

Dry-run par défaut. Un fichier historique existant n'est déplacé vers la
sauvegarde que si ``--replace-legacy`` est explicitement fourni.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "codex_rules" / "default.rules"
DEFAULT_TARGET = Path.home() / ".codex" / "rules" / "default.rules"
DEFAULT_BACKUPS = Path.home() / ".agents" / "migration" / "backups" / "execpolicy"


def status(source: Path, target: Path) -> str:
    if target.is_symlink() and target.exists() and target.resolve() == source.resolve():
        return "current"
    if target.is_symlink():
        return "divergent-symlink"
    if target.exists():
        return "legacy-file"
    return "missing"


def install(source: Path, target: Path, backups: Path, *, apply: bool, replace_legacy: bool) -> tuple[int, Path | None]:
    state = status(source, target)
    if state == "current":
        print(f"À jour : {target} -> {source}")
        return 0, None
    if state == "divergent-symlink":
        print(f"REFUS : lien divergent {target}")
        return 2, None
    if state == "legacy-file" and not replace_legacy:
        print("REFUS : fichier historique présent; ajouter --replace-legacy après revue du dry-run")
        return 2, None
    if not apply:
        print(f"Dry-run : état={state}, cible={target}, source={source}")
        if state == "legacy-file":
            print(f"Le fichier serait déplacé sous {backups} avant création du lien.")
        return 0, None

    target.parent.mkdir(parents=True, exist_ok=True)
    backup: Path | None = None
    if state == "legacy-file":
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        backup_dir = backups / stamp
        backup_dir.mkdir(parents=True, exist_ok=False)
        backup = backup_dir / target.name
        target.rename(backup)
    target.symlink_to(source.resolve())
    print(f"Installé : {target} -> {source.resolve()}")
    if backup is not None:
        print(f"Sauvegarde récupérable : {backup}")
    return 0, backup


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--backups", type=Path, default=DEFAULT_BACKUPS)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--replace-legacy", action="store_true")
    args = parser.parse_args()
    code, _backup = install(
        args.source.expanduser(),
        args.target.expanduser(),
        args.backups.expanduser(),
        apply=args.apply,
        replace_legacy=args.replace_legacy,
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
