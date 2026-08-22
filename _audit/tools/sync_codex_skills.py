#!/usr/bin/env python3
"""Synchroniser les skills Codex exposes avec les canoniques du depot.

Le depot reste la source unique. ``codex_skills.json`` choisit le sous-ensemble
exporte et ``canon_skills.json`` resout chaque nom vers son repertoire reel.
Le synchroniseur ne remplace jamais un fichier, repertoire ou lien divergent.

Usage :
    python3 _audit/tools/sync_codex_skills.py
    python3 _audit/tools/sync_codex_skills.py --apply
    python3 _audit/tools/sync_codex_skills.py --target /tmp/codex-skills
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TARGET = Path.home() / ".codex" / "skills"


def desired_links(root: Path = ROOT) -> dict[str, Path]:
    registry = json.loads((root / "canon_skills.json").read_text(encoding="utf-8"))
    exports = json.loads((root / "codex_skills.json").read_text(encoding="utf-8"))
    if not isinstance(registry, dict) or not isinstance(exports, list):
        raise ValueError("registres Codex invalides")
    if len(exports) != len(set(exports)) or exports != sorted(exports):
        raise ValueError("codex_skills.json doit etre trie et sans doublon")

    desired: dict[str, Path] = {}
    for name in exports:
        if not isinstance(name, str) or name not in registry:
            raise ValueError(f"skill Codex absent du registre canonique: {name!r}")
        target = (root / registry[name]).resolve()
        if not (target / "SKILL.md").is_file():
            raise ValueError(f"canonique inutilisable pour {name}: {target}")
        desired[name] = target
    return desired


def classify(target: Path, desired: dict[str, Path]) -> tuple[list[str], list[str], list[str]]:
    missing: list[str] = []
    current: list[str] = []
    conflicts: list[str] = []
    for name, expected in desired.items():
        link = target / name
        if not link.exists() and not link.is_symlink():
            missing.append(name)
        elif link.is_symlink() and link.resolve() == expected:
            current.append(name)
        else:
            conflicts.append(name)
    return missing, current, conflicts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--apply", action="store_true", help="creer uniquement les liens manquants")
    args = parser.parse_args()

    desired = desired_links()
    target = args.target.expanduser()
    if not target.exists():
        if not args.apply or not target.parent.is_dir():
            print(f"CIBLE ABSENTE : {target}")
            return 2
        target.mkdir()

    missing, current, conflicts = classify(target, desired)
    print(f"Codex : {len(current)} a jour, {len(missing)} manquants, {len(conflicts)} conflits")
    for name in missing:
        print(f"  + {name} -> {desired[name]}")
    for name in conflicts:
        print(f"  ! {name} existe deja et n'est pas le lien attendu")

    if args.apply:
        for name in missing:
            (target / name).symlink_to(desired[name], target_is_directory=True)
        if missing:
            print(f"CREE : {len(missing)} lien(s)")

    return 1 if (missing and not args.apply) or conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main())
