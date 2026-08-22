#!/usr/bin/env python3
"""Synchroniser un miroir `.claude/skills` de projet avec les skills du depot.

LE PROBLEME QU'IL RESOUT
------------------------
Les projets de `~/docs/codes/mtbc/` ne voient pas les plugins de ce depot via le
marketplace : ils passent par un MIROIR de symlinks dans
`~/docs/codes/mtbc/.claude/skills`, un lien par skill, cree a la main. Rien ne le
synchronise, donc tout skill ajoute au depot apres la derniere mise a jour du
miroir est INVISIBLE dans les projets, sans aucun message d'erreur : le skill
n'existe simplement pas pour la session. Constat du 2026-08-17 : 78 liens pour
169 skills canoniques, soit 95 skills muets.

L'ecart ne se voit pas non plus a l'usage : un skill absent ne se declenche pas,
et un skill qui ne se declenche pas est indiscernable d'un skill qui a juge la
tache hors de son perimetre.

> Ce script est un PIS-ALLER. La vraie solution est d'installer le depot comme
> marketplace (`claude plugin marketplace add ~/docs/codes/claude_plugins`), ce
> pour quoi il est deja outille (`.claude-plugin/marketplace.json`, onze
> `plugin.json`). Le mode plugin charge tous les skills d'un plugin active,
> definit `${CLAUDE_PLUGIN_ROOT}` (dont 21 skills du miroir dependent), et
> permet l'activation selective par projet, qui est la regle AUP du depot.
> Utiliser ce script tant que la migration n'est pas faite, ou pour un projet
> ou l'on veut un sous-ensemble choisi de skills.

USAGE
  python3 sync_project_skills.py                          # dry-run sur mtbc/
  python3 sync_project_skills.py --apply
  python3 sync_project_skills.py --target ~/docs/codes/autre/.claude/skills
  python3 sync_project_skills.py --apply --prune          # + retirer les liens morts
  python3 sync_project_skills.py --include-maboss         # projet distinct, exclu par defaut
  python3 sync_project_skills.py --include-droit          # domaine juridique, exclu par defaut

CODES DE SORTIE
  0 = miroir a jour ; 1 = ecart detecte (ou applique) ; 2 = cible inutilisable.

SUPPRESSIONS : jamais `rm`, toujours `gio trash` (regle du CLAUDE.md global).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MABOSS = "maboss"
DROIT = "droit"
DEFAULT_TARGET = Path.home() / "docs/codes/mtbc/.claude/skills"


def marketplace_plugins(root: Path = REPO) -> list[tuple[str, Path]]:
    """Lire les onze plugins depuis le manifeste canonique du marketplace."""
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


def canonical_skills(include_maboss: bool, include_droit: bool = False) -> tuple[dict[str, Path], list[str]]:
    """Nom -> repertoire canonique. Un skill est canonique la ou il est un VRAI
    repertoire ; les symlinks entre plugins sont ignores (c'est la convention du
    depot). `external/` est inclus : ces skills tiers doivent aussi etre vus.
    """
    skills: dict[str, Path] = {}
    notes: list[str] = []

    excluded = set()
    if not include_maboss:
        excluded.add(MABOSS)
    if not include_droit:
        excluded.add(DROIT)
    for plugin, plugin_root in marketplace_plugins():
        if plugin in excluded:
            continue
        d = plugin_root / "skills"
        if not d.is_dir():
            continue
        for entry in sorted(d.iterdir()):
            if not entry.is_dir() or entry.is_symlink():
                continue
            if not (entry / "SKILL.md").exists():
                notes.append(f"{plugin}/{entry.name} : pas de SKILL.md, ignore")
                continue
            prev = skills.get(entry.name)
            if prev is not None:
                # Deux vrais repertoires pour un meme nom : c'est l'exception
                # documentee (phylo-history) ou une divergence a corriger. On ne
                # devine pas, on signale et on garde le premier.
                notes.append(f"{entry.name} : DEUX versions reelles "
                             f"({prev.parent.parent.name} et {plugin}), le miroir garde "
                             f"{prev.parent.parent.name} — verifier si c'est voulu")
                continue
            skills[entry.name] = entry

    ext = REPO / "external"
    if ext.is_dir():
        for provider in sorted(p for p in ext.iterdir() if p.is_dir()):
            for entry in sorted((provider / "skills").glob("*")):
                if entry.is_dir() and (entry / "SKILL.md").exists():
                    skills.setdefault(entry.name, entry)

    orphan_dir = REPO / "mes_skills"
    if orphan_dir.is_dir():
        for entry in sorted(orphan_dir.iterdir()):
            if entry.is_dir() and (entry / "SKILL.md").exists() and entry.name not in skills:
                notes.append(f"{entry.name} : dans `mes_skills/`, donc dans AUCUN plugin — "
                             "invisible par le marketplace ; lie quand meme ici, mais sa place "
                             "est dans un plugin")
                skills[entry.name] = entry
    return skills, notes


def gio_trash(path: Path) -> bool:
    if shutil.which("gio") is None:
        return False
    return subprocess.run(["gio", "trash", str(path)],
                          capture_output=True).returncode == 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", default=str(DEFAULT_TARGET), help=f"defaut {DEFAULT_TARGET}")
    ap.add_argument("--apply", action="store_true", help="creer les liens manquants")
    ap.add_argument("--prune", action="store_true",
                    help="avec --apply : mettre a la corbeille les liens morts ou hors depot")
    ap.add_argument("--include-maboss", action="store_true")
    ap.add_argument("--include-droit", action="store_true")
    args = ap.parse_args()

    target = Path(args.target).expanduser()
    if not target.parent.exists():
        print(f"CIBLE INUTILISABLE : {target.parent} n'existe pas.", file=sys.stderr)
        return 2
    target.mkdir(parents=True, exist_ok=True)

    skills, notes = canonical_skills(args.include_maboss, args.include_droit)

    existing = {e.name: e for e in target.iterdir() if e.name != "README.md"}
    missing = sorted(set(skills) - set(existing))
    dead, foreign, ok = [], [], []
    for name, entry in sorted(existing.items()):
        if not entry.exists():                      # lien casse
            dead.append(name)
        elif name not in skills:
            foreign.append((name, entry.resolve() if entry.is_symlink() else entry))
        else:
            ok.append(name)

    print(f"miroir   : {target}")
    print(f"depot    : {len(skills)} skills canoniques (external/ inclus"
          f"{', maboss inclus' if args.include_maboss else ', maboss exclu'}"
          f"{', droit inclus' if args.include_droit else ', droit exclu'})")
    print(f"present  : {len(ok)} a jour | {len(missing)} manquants | "
          f"{len(dead)} casses | {len(foreign)} hors depot")

    if missing:
        print(f"\nMANQUANTS ({len(missing)}) — invisibles dans les projets :")
        for n in missing:
            print(f"  + {n:38s} <- {skills[n].relative_to(REPO)}")
    if dead:
        print(f"\nLIENS CASSES ({len(dead)}) :")
        for n in dead:
            print(f"  x {n}")
    if foreign:
        print(f"\nHORS DEPOT ({len(foreign)}) — a garder si voulu, sinon --prune :")
        for n, t in foreign:
            print(f"  ? {n:38s} -> {t}")
    if notes:
        print("\nA VERIFIER :")
        for n in notes:
            print(f"  - {n}")

    if not args.apply:
        if missing or dead:
            print("\nDry-run. Relancer avec --apply (et --prune pour nettoyer).")
        else:
            print("\nMiroir a jour.")
        return 1 if (missing or dead) else 0

    created = 0
    for n in missing:
        # Liens ABSOLUS ici, volontairement : la cible est hors du depot et n'est
        # pas destinee a etre clonee. La regle des liens relatifs ne vaut qu'A
        # L'INTERIEUR du depot, ou un lien absolu casse au clonage.
        (target / n).symlink_to(skills[n])
        created += 1
    removed = 0
    if args.prune:
        for n in dead + [f for f, _ in foreign]:
            p = target / n
            if gio_trash(p):
                removed += 1
            else:
                print(f"  ! `gio trash` indisponible ou en echec pour {p} : "
                      "retirer le lien a la main, ne PAS utiliser rm sans le demander")

    print(f"\n{created} lien(s) cree(s), {removed} retire(s).")
    using_root = sum(1 for n in list(skills) if (skills[n] / "SKILL.md").exists()
                     and "CLAUDE_PLUGIN_ROOT" in (skills[n] / "SKILL.md").read_text(errors="replace"))
    if using_root:
        print(f"\nRAPPEL : {using_root} skills ecrivent leurs chemins avec "
              "`${CLAUDE_PLUGIN_ROOT}`, variable qui n'est definie QUE pour un skill charge "
              "comme plugin. Dans un miroir de projet, elle est vide : substituer le chemin "
              "reel du depot au moment d'executer la commande, ou migrer vers le marketplace.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
