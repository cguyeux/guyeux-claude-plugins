#!/usr/bin/env python3
"""Synchronisation controlee entre les fermes de skills Claude et Agents.

La ferme Claude est traitee comme source d'observation historique et la ferme
Agents comme cible Codex personnelle. Le script ne remplace jamais un fichier,
un repertoire ou un lien divergent. Par defaut, il produit seulement un dry-run.

Les ecarts intentionnels vivent dans ``_audit/agent_farm_expected_delta.json`` :

- ``claude_only_expected`` : skills Claude a ne pas creer dans Agents ;
- ``agents_only_expected`` : skills Agents absents de Claude, acceptes ;
- ``common_divergent_expected`` : skills presents des deux cotes mais divergents
  en contenu, suivis par CCX-06.

Usage :
    python3 _audit/tools/sync_agent_skills.py
    python3 _audit/tools/sync_agent_skills.py --apply
    python3 _audit/tools/sync_agent_skills.py --claude-root /tmp/claude --agents-root /tmp/agents
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CLAUDE_ROOTS = [Path.home() / ".claude" / "skills"]
DEFAULT_AGENTS_ROOT = Path.home() / ".agents" / "skills"
EXCLUDED_NAMES = {".venv", "venv", "__pycache__"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def expected_delta(root: Path = ROOT) -> dict[str, set[str]]:
    payload = load_json(root / "_audit" / "agent_farm_expected_delta.json")
    return {
        "claude_only": set(payload.get("claude_only_expected", [])),
        "agents_only": set(payload.get("agents_only_expected", [])),
        "divergent": set(payload.get("common_divergent_expected", [])),
    }


def personal_skill_names(root: Path) -> set[str]:
    if not root.is_dir():
        return set()
    return {path.parent.name for path in root.glob("*/SKILL.md")}


def personal_skill_map(roots: list[Path]) -> dict[str, Path]:
    """Nom de skill -> répertoire réel, la première racine citée l'emportant."""
    trouve: dict[str, Path] = {}
    for root in roots:
        for name in personal_skill_names(root):
            trouve.setdefault(name, root / name)
    return trouve


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in EXCLUDED_NAMES for part in relative.parts) or path.suffix in EXCLUDED_SUFFIXES:
            continue
        files.append(relative)
    for relative in sorted(files):
        digest.update(str(relative).encode("utf-8"))
        digest.update(b"\0")
        digest.update((root / relative).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def readlink_target(path: Path) -> str:
    try:
        return str(path.resolve())
    except OSError:
        return ""


def classify(
    claude_map: dict[str, Path],
    agents_root: Path,
    root: Path = ROOT,
) -> tuple[dict[str, list[str]], list[str]]:
    expected = expected_delta(root)
    claude = set(claude_map)
    agents = personal_skill_names(agents_root)
    common = claude & agents

    missing = sorted(claude - agents - expected["claude_only"])
    expected_claude_only_present = sorted(claude & expected["claude_only"])
    unexpected_agents_only = sorted((agents - claude) - expected["agents_only"])
    divergent = sorted(name for name in common if tree_digest(claude_map[name]) != tree_digest(agents_root / name))
    unexpected_divergent = sorted(set(divergent) - expected["divergent"])
    stale_expected_divergent = sorted(expected["divergent"] - set(divergent))
    stale_expected_claude_only = sorted(expected["claude_only"] - (claude - agents))
    stale_expected_agents_only = sorted(expected["agents_only"] - (agents - claude))

    problems: list[str] = []
    if unexpected_agents_only:
        problems.append(f"Agents-only non whitelistes: {unexpected_agents_only}")
    if unexpected_divergent:
        problems.append(f"divergences communes non whitelistees: {unexpected_divergent}")
    if stale_expected_divergent:
        problems.append(f"whitelist divergente obsolete: {stale_expected_divergent}")
    if stale_expected_claude_only:
        problems.append(f"whitelist Claude-only obsolete: {stale_expected_claude_only}")
    if stale_expected_agents_only:
        problems.append(f"whitelist Agents-only obsolete: {stale_expected_agents_only}")

    return {
        "current": sorted(common - set(divergent)),
        "missing": missing,
        "expected_claude_only": expected_claude_only_present,
        "expected_divergent": sorted(set(divergent) & expected["divergent"]),
        "unexpected_agents_only": unexpected_agents_only,
        "unexpected_divergent": unexpected_divergent,
    }, problems


def apply_missing(claude_map: dict[str, Path], agents_root: Path, missing: list[str]) -> None:
    agents_root.mkdir(parents=True, exist_ok=True)
    for name in missing:
        target = agents_root / name
        if target.exists() or target.is_symlink():
            raise RuntimeError(f"refus de remplacer {target} -> {readlink_target(target)}")
        target.symlink_to(claude_map[name].resolve(), target_is_directory=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claude-root", type=Path, action="append", dest="claude_roots",
                        help="racine de skills personnels, répétable (défaut : ~/.claude/skills)")
    parser.add_argument("--agents-root", type=Path, default=DEFAULT_AGENTS_ROOT)
    parser.add_argument("--apply", action="store_true", help="creer seulement les liens Agents manquants non whitelistes")
    parser.add_argument("--json", action="store_true", help="emettre un rapport JSON")
    args = parser.parse_args()

    claude_roots = [p.expanduser() for p in (args.claude_roots or DEFAULT_CLAUDE_ROOTS)]
    agents_root = args.agents_root.expanduser()
    claude_map = personal_skill_map(claude_roots)
    summary, problems = classify(claude_map, agents_root, ROOT)

    if args.apply and problems:
        problems.append("apply refuse tant que le dry-run contient des problemes")
    elif args.apply and summary["missing"]:
        apply_missing(claude_map, agents_root, summary["missing"])
        summary, problems = classify(claude_map, agents_root, ROOT)

    report = {
        "claude_roots": [str(p) for p in claude_roots],
        "agents_root": str(agents_root),
        "summary": {key: len(value) for key, value in summary.items()},
        "detail": summary,
        "problems": problems,
        "ok": not problems and not summary["missing"],
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("Agents skill farm sync")
        print(f"  a jour identiques       : {len(summary['current'])}")
        print(f"  manquants a creer       : {len(summary['missing'])}")
        print(f"  Claude-only attendus    : {len(summary['expected_claude_only'])}")
        print(f"  divergents attendus     : {len(summary['expected_divergent'])}")
        print(f"  Agents-only inattendus  : {len(summary['unexpected_agents_only'])}")
        print(f"  divergents inattendus   : {len(summary['unexpected_divergent'])}")
        for name in summary["missing"]:
            print(f"  + {name} -> {claude_map[name].resolve()}")
        if problems:
            print("\nProblemes:")
            for problem in problems:
                print(f"  - {problem}")
        elif summary["missing"]:
            print("\nDry-run : relancer avec --apply pour creer les liens manquants.")
        else:
            print("\nSain.")
    return 0 if not problems and (args.apply or not summary["missing"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
