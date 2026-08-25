#!/usr/bin/env python3
"""Audit et synchronisation prudente des fermes de skills Claude et Codex.

La source de verite est ``canon_skills.json`` dans le depot Git. ``audit`` est
strictement en lecture seule. ``sync`` est un dry-run par defaut et ne sait que
creer des liens symboliques manquants. Il ne remplace et ne supprime jamais un
chemin existant.

Claude decouvre aussi les ``.claude/skills`` de projet, avec masquage possible
par le premier niveau rencontre. Codex decouvre la ferme personnelle Agents,
les exports directs ``.codex/skills`` et les plugins installes. L'outil audite
donc ces surfaces separement au lieu de supposer une fusion identique.

Exemples :
    skills_farm.py audit --root ~/docs --profile-root ~/.codex
    skills_farm.py sync --farm ~/docs/.claude/skills --skill fig-ideation --dry-run
    skills_farm.py sync --farm ~/docs/.claude/skills --skill fig-ideation --apply
    skills_farm.py sync --farm ~/docs/.claude/skills --all-missing --allow-mixed --apply
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import audit_codex_skill_farm as codex_audit  # noqa: E402


DEFAULT_ROOT = Path.home() / "docs"
DEFAULT_PROFILE = Path.home() / ".codex"
DEFAULT_CLAUDE = Path.home() / ".claude" / "skills"
DEFAULT_AGENTS = Path.home() / ".agents" / "skills"
DEFAULT_CODEX = Path.home() / ".codex" / "skills"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.S)
DESCRIPTION_RE = re.compile(r"^description:\s*(.*?)(?=^[A-Za-z_][\w-]*:|\Z)", re.S | re.M)


def canonical_sources(repo: Path = REPO) -> dict[str, Path]:
    payload = json.loads((repo / "canon_skills.json").read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("canon_skills.json invalide")
    return {name: (repo / relative).resolve() for name, relative in payload.items()}


def selected_sources(
    sources: dict[str, Path],
    source: Path | None,
    plugin: str | None,
) -> dict[str, Path]:
    if source is not None and plugin is not None:
        raise ValueError("--source et --plugin sont mutuellement exclusifs")
    if source is not None:
        parent = source.expanduser().resolve()
        return {name: path for name, path in sources.items() if path.parent == parent}
    if plugin is not None:
        prefix = (REPO / plugin / "skills").resolve()
        return {name: path for name, path in sources.items() if path.parent == prefix}
    return sources


def skill_listing_size(skill_dir: Path) -> int:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return 0
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    frontmatter = FRONTMATTER_RE.search(text)
    if not frontmatter:
        return 0
    match = DESCRIPTION_RE.search(frontmatter.group(1))
    description = " ".join(match.group(1).split()) if match else ""
    return len(skill_dir.name) + len(description)


def measure(root: Path) -> dict[str, Any]:
    sizes: list[tuple[int, str]] = []
    if root.is_dir():
        for entry in sorted(root.iterdir()):
            if entry.is_dir():
                size = skill_listing_size(entry)
                if size:
                    sizes.append((size, entry.name))
    sizes.sort(reverse=True)
    return {
        "root": str(root),
        "skills": len(sizes),
        "characters": sum(size for size, _name in sizes),
        "largest": [{"name": name, "characters": size} for size, name in sizes[:5]],
    }


@dataclass
class FarmAudit:
    path: Path
    canonical: list[str]
    missing: list[str]
    divergent: list[str]
    extensions: list[str]
    noncanonical: list[str]
    foreign: list[str]
    dead: list[str]

    @property
    def kind(self) -> str:
        return "mixed" if self.divergent or self.noncanonical or self.foreign else "pure"

    @property
    def problems(self) -> bool:
        return bool(self.missing or self.divergent or self.dead)

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "kind": self.kind,
            "canonical": self.canonical,
            "missing": self.missing,
            "divergent": self.divergent,
            "canonical_extensions": self.extensions,
            "noncanonical_sources": self.noncanonical,
            "foreign": self.foreign,
            "dead": self.dead,
        }


def audit_farm(
    path: Path,
    expected: dict[str, Path],
    all_expected: dict[str, Path] | None = None,
) -> FarmAudit:
    all_expected = expected if all_expected is None else all_expected
    canonical: list[str] = []
    divergent: list[str] = []
    extensions: list[str] = []
    noncanonical: list[str] = []
    foreign: list[str] = []
    dead: list[str] = []
    entries = sorted(path.iterdir()) if path.is_dir() else []
    for entry in entries:
        if entry.is_symlink() and not entry.exists():
            dead.append(entry.name)
            continue
        wanted = expected.get(entry.name)
        if wanted is None:
            global_wanted = all_expected.get(entry.name)
            if global_wanted is not None and entry.is_symlink() and entry.resolve() == global_wanted:
                extensions.append(entry.name)
            elif global_wanted is not None and entry.is_symlink():
                noncanonical.append(entry.name)
            else:
                foreign.append(entry.name)
        elif entry.is_symlink() and entry.resolve() == wanted:
            canonical.append(entry.name)
        else:
            divergent.append(entry.name)
    present = set(canonical) | set(divergent)
    return FarmAudit(
        path=path,
        canonical=sorted(canonical),
        missing=sorted(set(expected) - present),
        divergent=sorted(divergent),
        extensions=sorted(extensions),
        noncanonical=sorted(noncanonical),
        foreign=sorted(foreign),
        dead=sorted(dead),
    )


def find_project_farms(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(path for path in root.glob("**/.claude/skills") if path.is_dir())


def canonical_collisions(sources: dict[str, Path]) -> list[dict[str, Any]]:
    by_target: dict[Path, list[str]] = {}
    for name, target in sources.items():
        by_target.setdefault(target, []).append(name)
    return [
        {"target": str(target), "names": sorted(names)}
        for target, names in sorted(by_target.items(), key=lambda item: str(item[0]))
        if len(names) > 1
    ]


def audit_report(args: argparse.Namespace) -> tuple[dict[str, Any], list[str]]:
    sources = canonical_sources()
    project_sources = selected_sources(sources, args.source, args.plugin or (None if args.source else "redac"))
    if not project_sources:
        raise ValueError("la selection canonique de skills est vide")

    repository, repository_problems = codex_audit.audit_repository(REPO)
    exports, export_problems = codex_audit.audit_codex_exports(args.codex_skills_root, REPO)
    personal, personal_problems = codex_audit.audit_agent_farms(
        args.claude_skills_root,
        args.agents_skills_root,
        REPO,
    )
    profile, profile_problems = codex_audit.audit_profile(args.profile_root)

    farms = [audit_farm(path, project_sources, sources) for path in find_project_farms(args.root)]
    relevant = [
        farm for farm in farms
        if farm.canonical or farm.divergent or farm.extensions or farm.noncanonical or farm.dead
    ]
    project_problems: list[str] = []
    project_warnings: list[str] = []
    for farm in relevant:
        if farm.missing:
            message = f"farm en derive, skills manquants: {farm.path}: {farm.missing}"
            if farm.kind == "pure":
                project_problems.append(message)
            else:
                project_warnings.append(message + " (farm mixte, selection humaine requise)")
        if farm.divergent:
            project_problems.append(f"sources non canoniques ou collisions: {farm.path}: {farm.divergent}")
        if farm.noncanonical:
            project_problems.append(f"liens hors registre canonique: {farm.path}: {farm.noncanonical}")
        if farm.dead:
            project_problems.append(f"liens morts: {farm.path}: {farm.dead}")

    report = {
        "discovery": {
            "claude": "ferme personnelle et premier .claude/skills de projet rencontre",
            "codex": "ferme personnelle Agents, exports directs Codex et plugins; aucun farm projet suppose",
        },
        "repository": repository,
        "codex_direct_exports": exports,
        "personal_farms": personal,
        "profile": profile,
        "project_selection": {
            "plugin": args.plugin,
            "source": str(args.source) if args.source else None,
            "canonical_skills": len(project_sources),
        },
        "project_farms": [farm.as_dict() for farm in relevant],
        "project_warnings": project_warnings,
        "metadata": [
            measure(args.claude_skills_root),
            measure(args.agents_skills_root),
            measure(args.codex_skills_root),
            measure(args.root / ".claude" / "skills"),
        ],
        "canonical_target_collisions": canonical_collisions(sources),
    }
    problems = repository_problems + export_problems + personal_problems + profile_problems + project_problems
    report["problems"] = problems
    report["ok"] = not problems
    return report, problems


def print_audit(report: dict[str, Any]) -> None:
    repository = report["repository"]
    personal = report["personal_farms"]
    print("Audit unifie des fermes de skills")
    print(f"  canonique Git       : {repository['canonicals']} skills")
    print(f"  exports Codex       : {repository['direct_exports']} directs, {repository['packaged_skills']} empaquetes")
    print(f"  Claude / Agents     : {personal['claude_skills']} / {personal['agents_skills']} personnels")
    print(f"  doublons de nom     : {personal['common']} entre fermes personnelles")
    print(f"  collisions contenu : {len(personal['common_divergent'])} divergences connues")
    print(f"  farms projet vus    : {len(report['project_farms'])}")
    print(f"  collisions canon.   : {len(report['canonical_target_collisions'])}")
    print("  decouverte Claude   : personnelle + premier farm projet, avec masquage")
    print("  decouverte Codex    : personnelle + exports + plugins, sans farm projet suppose")
    print("\nPoids des metadonnees de routage:")
    for item in report["metadata"]:
        print(f"  {item['root']}: {item['skills']} skills, {item['characters']} caracteres")
    for farm in report["project_farms"]:
        print(f"\n[{farm['kind'].upper()}] {farm['path']}")
        print(f"  canoniques={len(farm['canonical'])} etrangers={len(farm['foreign'])}")
        if farm["canonical_extensions"]:
            print(f"  extensions canoniques: {', '.join(farm['canonical_extensions'])}")
        if farm["missing"]:
            print(f"  manquants: {', '.join(farm['missing'])}")
        if farm["divergent"]:
            print(f"  sources non canoniques/collisions: {', '.join(farm['divergent'])}")
        if farm["noncanonical_sources"]:
            print(f"  liens hors registre canonique: {', '.join(farm['noncanonical_sources'])}")
        if farm["dead"]:
            print(f"  liens morts: {', '.join(farm['dead'])}")
    if report["project_warnings"]:
        print("\nAvertissements, fermes mixtes non modifiees:")
        for warning in report["project_warnings"]:
            print(f"  - {warning}")
    if report["problems"]:
        print("\nProblemes:")
        for problem in report["problems"]:
            print(f"  - {problem}")
    else:
        print("\nSain.")


def sync(args: argparse.Namespace) -> int:
    all_sources = canonical_sources()
    sources = selected_sources(all_sources, args.source, args.plugin)
    if not sources:
        print("ERREUR: la selection canonique de skills est vide", file=sys.stderr)
        return 2
    if args.all_missing and args.skill:
        print("ERREUR: --all-missing et --skill sont mutuellement exclusifs", file=sys.stderr)
        return 2
    if not args.all_missing and not args.skill:
        print("ERREUR: selection explicite requise: --skill ou --all-missing", file=sys.stderr)
        return 2
    if args.all_missing and args.source is None and args.plugin is None:
        print("ERREUR: --all-missing exige --source ou --plugin", file=sys.stderr)
        return 2

    farm = args.farm
    state = audit_farm(farm, sources, all_sources)
    if state.kind == "mixed" and args.all_missing and not args.allow_mixed:
        print("ERREUR: farm mixte; utiliser des --skill explicites ou --allow-mixed", file=sys.stderr)
        return 2
    requested = state.missing if args.all_missing else sorted(set(args.skill))
    unknown = sorted(set(requested) - set(sources))
    if unknown:
        print(f"ERREUR: skills absents du registre canonique selectionne: {unknown}", file=sys.stderr)
        return 2

    actions: list[tuple[Path, Path]] = []
    conflicts: list[str] = []
    for name in requested:
        link = farm / name
        target = sources[name]
        if link.is_symlink() and link.exists() and link.resolve() == target:
            continue
        if link.exists() or link.is_symlink():
            conflicts.append(f"refus de remplacer {link}")
            continue
        if not (target / "SKILL.md").is_file():
            conflicts.append(f"source canonique incomplete {target}")
            continue
        actions.append((link, target))
    if conflicts:
        for conflict in conflicts:
            print(f"ERREUR: {conflict}", file=sys.stderr)
        return 2

    mode = "apply" if args.apply else "dry-run"
    print(f"Skill farm sync ({mode})")
    print(f"  farm: {farm}")
    for link, target in actions:
        print(f"  + {link.name} -> {target}")
    if args.apply:
        farm.mkdir(parents=True, exist_ok=True)
        for link, target in actions:
            link.symlink_to(target, target_is_directory=True)
        print(f"{len(actions)} lien(s) cree(s), aucun remplacement, aucune suppression.")
    else:
        print(f"Dry-run: {len(actions)} lien(s) seraient crees, aucune mutation.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command")
    audit = subparsers.add_parser("audit", help="audit unifie en lecture seule")
    audit.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    audit.add_argument("--profile-root", type=Path, default=DEFAULT_PROFILE)
    audit.add_argument("--claude-skills-root", type=Path, default=DEFAULT_CLAUDE)
    audit.add_argument("--agents-skills-root", type=Path, default=DEFAULT_AGENTS)
    audit.add_argument("--codex-skills-root", type=Path, default=DEFAULT_CODEX)
    audit.add_argument("--source", type=Path, default=None, help="repertoire plugin skills canonique")
    audit.add_argument("--plugin", default=None, help="plugin projet a auditer, redac par defaut")
    audit.add_argument("--json", action="store_true")

    sync_parser = subparsers.add_parser("sync", help="creer seulement des liens canoniques manquants")
    sync_parser.add_argument("--farm", type=Path, required=True, help="ferme cible explicitement selectionnee")
    sync_parser.add_argument("--source", type=Path, default=None)
    sync_parser.add_argument("--plugin", default=None)
    sync_parser.add_argument("--skill", action="append", default=[])
    sync_parser.add_argument("--all-missing", action="store_true")
    sync_parser.add_argument("--allow-mixed", action="store_true")
    mode = sync_parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="defaut; explicite pour les scripts")
    mode.add_argument("--apply", action="store_true", help="creer les liens selectionnes")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command is None:
        args = parser.parse_args(["audit"])
    for name in ("root", "profile_root", "claude_skills_root", "agents_skills_root", "codex_skills_root", "source", "farm"):
        value = getattr(args, name, None)
        if isinstance(value, Path):
            setattr(args, name, value.expanduser())
    try:
        if args.command == "sync":
            return sync(args)
        report, problems = audit_report(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_audit(report)
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
