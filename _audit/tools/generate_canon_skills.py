#!/usr/bin/env python3
"""Generer le registre portable des skills canoniques actifs du marketplace.

Le marketplace est la seule source de la liste des plugins. Les symlinks et les
repertoires ``skills_disabled`` sont exclus. Les chemins ecrits dans le JSON sont
relatifs a la racine du depot afin que le registre reste valide apres clonage.

Usage :
    python3 _audit/tools/generate_canon_skills.py
    python3 _audit/tools/generate_canon_skills.py --check
    python3 _audit/tools/generate_canon_skills.py --output /chemin/candidat.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "canon_skills.json"

# P5.2 (2026-09-15) : phylo-history n'a plus qu'une copie physique reelle,
# mtbc/skills/phylo-history (version diagnostic), qui porte en reference
# nichee l'ancienne variante narrative de bio_redac (sous-dossier
# phylo-history-bio-redac/, non un skill frere). Plus de doublon a arbitrer ;
# override conserve vide au cas ou une vraie fusion future en recree un.
CANONICAL_OVERRIDES: dict[str, Path] = {}


def marketplace_plugins(root: Path = ROOT) -> list[tuple[str, Path]]:
    marketplace = root / ".claude-plugin" / "marketplace.json"
    data = json.loads(marketplace.read_text(encoding="utf-8"))
    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        raise ValueError(f"liste `plugins` absente de {marketplace}")

    resolved_root = root.resolve()
    result: list[tuple[str, Path]] = []
    seen: set[str] = set()
    for record in plugins:
        if not isinstance(record, dict):
            raise ValueError(f"entree plugin invalide dans {marketplace}")
        name, source = record.get("name"), record.get("source")
        if not isinstance(name, str) or not isinstance(source, str):
            raise ValueError(f"plugin sans nom/source valide dans {marketplace}")
        if name in seen:
            raise ValueError(f"plugin duplique dans {marketplace}: {name}")
        path = (root / source).resolve()
        try:
            path.relative_to(resolved_root)
        except ValueError as exc:
            raise ValueError(f"source plugin hors depot: {source}") from exc
        if not path.is_dir():
            raise ValueError(f"source plugin absente: {source}")
        seen.add(name)
        result.append((name, path))
    return result


def canonical_registry(root: Path = ROOT) -> tuple[dict[str, str], dict[str, list[str]]]:
    candidates: dict[str, list[Path]] = {}
    for _plugin, plugin_root in marketplace_plugins(root):
        skills_dir = plugin_root / "skills"
        if not skills_dir.is_dir():
            continue
        for entry in sorted(skills_dir.iterdir()):
            if not entry.is_dir():
                continue
            target = entry.resolve()
            try:
                relative = target.relative_to(root.resolve())
            except ValueError as exc:
                raise ValueError(f"skill actif hors depot: {entry.relative_to(root)}") from exc
            if "skills_disabled" in relative.parts:
                raise ValueError(f"skill actif lie vers skills_disabled: {entry.relative_to(root)}")
            if not (target / "SKILL.md").is_file():
                raise ValueError(f"skill actif sans SKILL.md: {entry.relative_to(root)}")
            paths = candidates.setdefault(entry.name, [])
            if relative not in paths:
                paths.append(relative)

    registry: dict[str, str] = {}
    duplicates: dict[str, list[str]] = {}
    for name, paths in sorted(candidates.items()):
        if len(paths) == 1:
            chosen = paths[0]
        else:
            duplicates[name] = [path.as_posix() for path in paths]
            chosen = CANONICAL_OVERRIDES.get(name)
            if chosen is None or chosen not in paths:
                rendered = ", ".join(path.as_posix() for path in paths)
                raise ValueError(f"canoniques multiples sans override pour {name}: {rendered}")
        registry[name] = chosen.as_posix()
    return registry, duplicates


def render_registry(registry: dict[str, str]) -> str:
    return json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="echouer si le registre a derive")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    registry, duplicates = canonical_registry()
    rendered = render_registry(registry)
    output = args.output.expanduser()

    if args.check:
        current = output.read_text(encoding="utf-8") if output.is_file() else None
        if current != rendered:
            print(f"DERIVE : {output} doit etre regenere ({len(registry)} entrees attendues).")
            return 1
        print(f"OK : {output} est a jour ({len(registry)} entrees).")
    else:
        output.write_text(rendered, encoding="utf-8")
        print(f"ECRIT : {output} ({len(registry)} entrees).")

    for name, paths in sorted(duplicates.items()):
        chosen = registry[name]
        print(f"EXCEPTION : {name} -> {chosen} ; variantes={','.join(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
