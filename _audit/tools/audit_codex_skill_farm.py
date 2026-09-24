#!/usr/bin/env python3
"""Audit unique de la ferme de skills Codex.

Controle en lecture seule :

- registre canonique et exports directs ;
- partition entre exports directs et paquets Codex materialises ;
- marketplace local et manifests de plugins ;
- frontmatter des skills empaquetes ;
- absence de caches/environnements locaux copies ;
- optionnellement, profil Codex reel ou temporaire.

Usage :
    python3 _audit/tools/audit_codex_skill_farm.py
    python3 _audit/tools/audit_codex_skill_farm.py --profile-root ~/.codex
    python3 _audit/tools/audit_codex_skill_farm.py --json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PACKAGES_ROOT = ROOT / "codex_packages" / "plugins"
MARKETPLACE = ROOT / "codex_packages" / ".agents" / "plugins" / "marketplace.json"
PACKAGE_MATRIX = ROOT / "_audit" / "codex_package_matrix.json"
FORBIDDEN_FRONTMATTER = ("argument-hint:", "disable-model-invocation:", "user-invocable:", "version:")
EXCLUDED_NAMES = {".venv", "venv", "__pycache__"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
EXPECTED_PLUGINS = {
    "guyeux-phylo-pilot",
    "bacteria",
    "bioinfo",
    "carriere",
    "diffusion",
    "litterature",
    "mtbc",
    "phylo",
    "popgen",
    "redaction",
    "science-commun",
    "structure",
    "ia",
    "maboss",
    "multimedia",
    "ops",
    "web",
}
AGENT_DELTA = ROOT / "_audit" / "agent_farm_expected_delta.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end == -1:
        return ""
    return text[:end]


def skill_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(path for path in root.iterdir() if path.is_dir())


def package_skill_dirs(packages_root: Path = PACKAGES_ROOT) -> dict[str, list[Path]]:
    result: dict[str, list[Path]] = {}
    if not packages_root.is_dir():
        return result
    for plugin in sorted(path for path in packages_root.iterdir() if path.is_dir()):
        result[plugin.name] = skill_dirs(plugin / "skills")
    return result


def package_skill_names(packages_root: Path = PACKAGES_ROOT) -> set[str]:
    names: set[str] = set()
    for skills in package_skill_dirs(packages_root).values():
        for skill in skills:
            names.add(skill.name)
    return names


def direct_exports(root: Path = ROOT) -> set[str]:
    exports = load_json(root / "codex_skills.json")
    if not isinstance(exports, list):
        raise ValueError("codex_skills.json invalide")
    return set(exports)


def canonical_registry(root: Path = ROOT) -> dict[str, str]:
    registry = load_json(root / "canon_skills.json")
    if not isinstance(registry, dict):
        raise ValueError("canon_skills.json invalide")
    return registry


def omitted_canonicals(root: Path = ROOT) -> set[str]:
    return set(canonical_registry(root)) - direct_exports(root)


def matrix_rows(root: Path = ROOT) -> list[dict[str, Any]]:
    payload = load_json(root / "_audit" / "codex_package_matrix.json")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("matrice paquet invalide")
    return rows


def profile_plugin_cache(profile_root: Path) -> Path:
    return profile_root / "plugins" / "cache" / "personal"


def installed_profile_skill_dirs(profile_root: Path) -> list[Path]:
    cache = profile_plugin_cache(profile_root)
    if not cache.is_dir():
        return []
    installed: list[Path] = []
    known_plugins: set[str] = set()
    for plugin in sorted(PACKAGES_ROOT.iterdir()):
        manifest_path = plugin / ".codex-plugin" / "plugin.json"
        if not manifest_path.is_file():
            continue
        known_plugins.add(plugin.name)
        version = load_json(manifest_path).get("version")
        if isinstance(version, str) and version:
            installed.extend((cache / plugin.name / version / "skills").glob("*"))
    for plugin in sorted(path for path in cache.iterdir() if path.is_dir() and path.name not in known_plugins):
        installed.extend(plugin.glob("*/skills/*"))
    return sorted(installed)


def profile_config(profile_root: Path) -> dict[str, Any]:
    path = profile_root / "config.toml"
    if not path.is_file():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def scan_forbidden_frontmatter(skill_roots: list[Path]) -> list[str]:
    problems: list[str] = []
    for skill in skill_roots:
        skill_md = skill / "SKILL.md"
        if not skill_md.is_file():
            problems.append(f"{skill}: SKILL.md manquant")
            continue
        fm = frontmatter(skill_md.read_text(encoding="utf-8", errors="replace"))
        for forbidden in FORBIDDEN_FRONTMATTER:
            if forbidden in fm:
                problems.append(f"{skill_md}: champ interdit {forbidden.rstrip(':')}")
    return problems


def scan_excluded_payload(root: Path) -> list[str]:
    if not root.exists():
        return []
    problems: list[str] = []
    for path in root.rglob("*"):
        if any(part in EXCLUDED_NAMES for part in path.parts) or path.suffix in EXCLUDED_SUFFIXES:
            problems.append(str(path))
    return sorted(problems)


def readlink_target(path: Path) -> str:
    try:
        return str(path.resolve())
    except OSError:
        return ""


def audit_codex_exports(target: Path, root: Path = ROOT) -> tuple[dict[str, int], list[str]]:
    problems: list[str] = []
    registry = canonical_registry(root)
    exports = direct_exports(root)
    current = 0
    missing = 0
    conflicts = 0
    for name in sorted(exports):
        expected = (root / registry[name]).resolve()
        link = target / name
        if not link.exists() and not link.is_symlink():
            missing += 1
            problems.append(f"export manquant: {link}")
        elif link.is_symlink() and link.resolve() == expected:
            current += 1
        else:
            conflicts += 1
            problems.append(f"export divergent: {link} -> {readlink_target(link)} attendu {expected}")
    return {"current": current, "missing": missing, "conflicts": conflicts}, problems


def audit_repository(root: Path = ROOT) -> tuple[dict[str, Any], list[str]]:
    problems: list[str] = []
    registry = canonical_registry(root)
    exports = direct_exports(root)
    omitted = set(registry) - exports
    packaged = package_skill_names(root / "codex_packages" / "plugins")
    rows = matrix_rows(root)
    classifications = {row["classification"] for row in rows}
    row_names = {row["name"] for row in rows}

    if len(registry) != 199:
        problems.append(f"registre canonique inattendu: {len(registry)}")
    if len(exports) != 53:
        problems.append(f"exports directs inattendus: {len(exports)}")
    if len(omitted) != 146:
        problems.append(f"canoniques empaquetes attendus 146, obtenu {len(omitted)}")
    if row_names != omitted:
        problems.append("la matrice paquet ne couvre pas exactement canon - exports")
    if packaged != omitted:
        problems.append(f"paquets != canoniques omis: manquants={sorted(omitted - packaged)} extra={sorted(packaged - omitted)}")
    if any(name.startswith("needs-") or name.startswith("blocked-") for name in classifications):
        problems.append(f"matrice non fermee: {sorted(classifications)}")

    marketplace = load_json(root / "codex_packages" / ".agents" / "plugins" / "marketplace.json")
    marketplace_names = {entry.get("name") for entry in marketplace.get("plugins", [])}
    package_names = set(package_skill_dirs(root / "codex_packages" / "plugins"))
    if marketplace_names != EXPECTED_PLUGINS:
        problems.append(f"marketplace inattendu: {sorted(marketplace_names)}")
    if package_names != EXPECTED_PLUGINS:
        problems.append(f"paquets inattendus: {sorted(package_names)}")

    for plugin_name, skills in package_skill_dirs(root / "codex_packages" / "plugins").items():
        manifest_path = root / "codex_packages" / "plugins" / plugin_name / ".codex-plugin" / "plugin.json"
        if not manifest_path.is_file():
            problems.append(f"manifest manquant: {plugin_name}")
            continue
        manifest = load_json(manifest_path)
        if manifest.get("name") != plugin_name:
            problems.append(f"manifest {plugin_name}: name={manifest.get('name')!r}")
        if not (root / "codex_packages" / "plugins" / plugin_name / "skills").is_dir():
            problems.append(f"skills dir manquant: {plugin_name}")
        if len(skills) == 0:
            problems.append(f"paquet sans skill: {plugin_name}")

    packaged_roots = [skill for skills in package_skill_dirs(root / "codex_packages" / "plugins").values() for skill in skills]
    problems.extend(scan_forbidden_frontmatter(packaged_roots))
    excluded = scan_excluded_payload(root / "codex_packages" / "plugins")
    if excluded:
        problems.append(f"payload exclu present dans paquets: {excluded[:10]}")

    return {
        "canonicals": len(registry),
        "direct_exports": len(exports),
        "packaged_skills": len(packaged),
        "matrix_rows": len(rows),
        "plugins": len(package_names),
        "classifications": sorted(classifications),
    }, problems


def audit_profile(profile_root: Path) -> tuple[dict[str, Any], list[str]]:
    problems: list[str] = []
    config = profile_config(profile_root)
    marketplaces = config.get("marketplaces", {}) if isinstance(config, dict) else {}
    personal = marketplaces.get("personal", {}) if isinstance(marketplaces, dict) else {}
    if personal.get("source") != str(ROOT / "codex_packages"):
        problems.append(f"marketplace personal non pointe vers le depot: {personal.get('source')!r}")

    plugins_cfg = config.get("plugins", {}) if isinstance(config, dict) else {}
    enabled = {
        name.removesuffix("@personal")
        for name, payload in plugins_cfg.items()
        if name.endswith("@personal") and isinstance(payload, dict) and payload.get("enabled") is True
    }
    if enabled != EXPECTED_PLUGINS:
        problems.append(f"plugins actives inattendus: {sorted(enabled)}")

    installed = installed_profile_skill_dirs(profile_root)
    installed_names = {path.name for path in installed}
    expected = omitted_canonicals(ROOT)
    if installed_names != expected:
        problems.append(f"cache profile != canoniques empaquetes: manquants={sorted(expected - installed_names)} extra={sorted(installed_names - expected)}")
    problems.extend(scan_forbidden_frontmatter(installed))
    excluded = scan_excluded_payload(profile_plugin_cache(profile_root))
    if excluded:
        problems.append(f"payload exclu present dans cache profile: {excluded[:10]}")
    return {
        "enabled_plugins": len(enabled),
        "installed_skills": len(installed_names),
        "profile_root": str(profile_root),
    }, problems


def personal_skill_names(root: Path) -> set[str]:
    if not root.is_dir():
        return set()
    return {path.parent.name for path in root.glob("*/SKILL.md")}


def dead_direct_symlinks(root: Path) -> list[str]:
    if not root.is_dir():
        return []
    return sorted(str(path) for path in root.iterdir() if path.is_symlink() and not path.exists())


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


def divergent_common_skills(claude_root: Path, agents_root: Path, common: set[str]) -> list[str]:
    divergent: list[str] = []
    for name in sorted(common):
        if tree_digest(claude_root / name) != tree_digest(agents_root / name):
            divergent.append(name)
    return divergent


def audit_agent_farms(claude_root: Path, agents_root: Path, root: Path = ROOT) -> tuple[dict[str, Any], list[str]]:
    problems: list[str] = []
    expected = load_json(root / "_audit" / "agent_farm_expected_delta.json")
    expected_divergent = set(expected.get("common_divergent_expected", []))
    expected_claude_only = set(expected.get("claude_only_expected", []))
    expected_agents_only = set(expected.get("agents_only_expected", []))
    claude = personal_skill_names(claude_root)
    agents = personal_skill_names(agents_root)
    common = claude & agents
    claude_only = claude - agents
    agents_only = agents - claude
    divergent = set(divergent_common_skills(claude_root, agents_root, common))
    if claude_only != expected_claude_only:
        problems.append(f"delta Claude-only inattendu: actuel={sorted(claude_only)} attendu={sorted(expected_claude_only)}")
    if agents_only != expected_agents_only:
        problems.append(f"delta Agents-only inattendu: actuel={sorted(agents_only)} attendu={sorted(expected_agents_only)}")
    if divergent != expected_divergent:
        problems.append(f"divergences communes inattendues: actuel={sorted(divergent)} attendu={sorted(expected_divergent)}")
    dead = dead_direct_symlinks(claude_root) + dead_direct_symlinks(agents_root)
    if dead:
        problems.append(f"liens morts dans fermes personnelles: {dead}")
    return {
        "claude_skills": len(claude),
        "agents_skills": len(agents),
        "common": len(common),
        "claude_only": sorted(claude_only),
        "agents_only": sorted(agents_only),
        "common_divergent": sorted(divergent),
    }, problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-skills-target", type=Path, default=Path.home() / ".codex" / "skills")
    parser.add_argument("--profile-root", type=Path, default=None, help="profil Codex a auditer, par exemple ~/.codex")
    parser.add_argument("--claude-skills-root", type=Path, default=Path.home() / ".claude" / "skills")
    parser.add_argument("--agents-skills-root", type=Path, default=Path.home() / ".agents" / "skills")
    parser.add_argument("--json", action="store_true", help="emettre un rapport JSON")
    args = parser.parse_args()

    report: dict[str, Any] = {}
    problems: list[str] = []
    repository, repo_problems = audit_repository(ROOT)
    exports, export_problems = audit_codex_exports(args.codex_skills_target.expanduser(), ROOT)
    report["repository"] = repository
    report["direct_export_farm"] = exports
    problems.extend(repo_problems)
    problems.extend(export_problems)
    agent_farms, agent_farm_problems = audit_agent_farms(
        args.claude_skills_root.expanduser(),
        args.agents_skills_root.expanduser(),
        ROOT,
    )
    report["agent_farms"] = agent_farms
    problems.extend(agent_farm_problems)
    if args.profile_root is not None:
        profile, profile_problems = audit_profile(args.profile_root.expanduser())
        report["profile"] = profile
        problems.extend(profile_problems)
    report["problems"] = problems
    report["ok"] = not problems

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("Codex skill farm audit")
        print(f"  canonicals      : {repository['canonicals']}")
        print(f"  direct exports  : {repository['direct_exports']} ({exports['current']} a jour, {exports['missing']} manquants, {exports['conflicts']} conflits)")
        print(f"  packaged skills : {repository['packaged_skills']}")
        print(f"  plugins         : {repository['plugins']}")
        print(f"  classifications : {', '.join(repository['classifications'])}")
        print(f"  Claude/Agents   : {agent_farms['common']} communs, {len(agent_farms['common_divergent'])} divergents attendus, {len(agent_farms['claude_only'])} Claude-only attendus, {len(agent_farms['agents_only'])} Agents-only")
        if "profile" in report:
            profile = report["profile"]
            print(f"  profile plugins : {profile['enabled_plugins']}")
            print(f"  profile skills  : {profile['installed_skills']}")
        if problems:
            print("\nProblemes:")
            for problem in problems:
                print(f"  - {problem}")
        else:
            print("\nSain.")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
