#!/usr/bin/env python3
"""Trie les figures ORPHELINES d'un depot par recuperabilite.

`fig_gap_scan.py` rend une liste de FICHIERS jamais inclus dans un manuscrit.
Cette liste sur-compte : un meme graphique existe en `.png`, `.pdf` et `.svg`,
parfois dans deux repertoires, et compte alors pour cinq. Elle melange aussi trois
populations que rien ne separe a l'oeil : le rebut de versions successives, les
figures d'outillage jamais destinees a un manuscrit, et le travail reellement
perdu.

Ce script regroupe d'abord par STEM (une figure = un nom, tous formats confondus),
puis classe chaque figure :

  REBUT       une version plus recente du meme graphique existe (suffixe de
              version, ou prefixe commun avec un stem plus long)
  OUTILLAGE   nom de controle interne (qc, checklist, validation, debug, test...)
  CANDIDAT    un script du projet la produit, et ce script tourne encore
  DONNEE MORTE un script la produit mais son entree a disparu (Newick absent de
              la foret, fichier source manquant)
  INDETERMINE aucun script ne la nomme : ni regenerable, ni datable autrement que
              par son mtime

Le classement est un TRI, pas un verdict : « REBUT » veut dire « regarder en
dernier », jamais « supprimer ».

Usage :
    python3 fig_triage.py <racine_depot> --gap <gap_all.json> [--json out.json]
    python3 fig_triage.py <racine_depot> --project L4.11

`--gap` attend la sortie agregee de `fig_gap_scan.py` : {projet: {"orphans": [...]}}.
Sans elle, le script relance le scan projet par projet (plus lent).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
GAP = HERE / "fig_gap_scan.py"

# Suffixes qui disent explicitement « une autre version existe ».
VERSION_SUFFIX = re.compile(
    r"_(v\d+|old|new|final|enhanced|comprehensive|improved|fixed|corrected|"
    r"bis|draft|tmp|temp|backup|orig|previous|legacy|v\d+_\d+)$", re.I)
# Noms qui disent « ceci sert au travail, pas au manuscrit ».
TOOLING = re.compile(
    r"(quality_check|checklist|_qc\b|\bqc_|debug|sanity|validation|verif|"
    r"decision_matrix|improvement|diagnostic|scratch|essai|test_|style_guide|"
    r"_enhancement|_rigor)", re.I)
IMG_EXT = {".pdf", ".png", ".svg", ".tiff", ".tif", ".jpg", ".jpeg", ".eps"}
SCRIPT_EXT = ("*.py", "*.sh", "*.R", "*.ipynb", "*.tex")
TREE_LITERAL = re.compile(
    r"[\"']([^\"'\n]*(?:bestTree|\.nwk|\.newick|\.treefile|\.contree|"
    r"\.support|\.nex|\.nexus)[^\"'\n]*)[\"']")
# Fichiers d'entree cites par un script : on ne teste que ce qui est nommable.
DATA_LITERAL = re.compile(r"[\"']([^\"'\n]{4,120}\.(?:tsv|csv|json|fasta|fa|txt|nwk))[\"']")


def load_gap(root: Path, gap: Path | None, only: str | None) -> dict[str, list[str]]:
    if gap and gap.is_file():
        d = json.loads(gap.read_text())
        out = {k: v["orphans"] if isinstance(v, dict) else v for k, v in d.items()}
        return {k: v for k, v in out.items() if not only or k == only}
    out = {}
    for m in sorted(root.rglob("article/main.tex")):
        proj = str(m.relative_to(root).parent.parent)
        if only and proj != only:
            continue
        tmp = Path(os.environ.get("TMPDIR", "/tmp")) / f"_gap_{abs(hash(proj))}.json"
        subprocess.run([sys.executable, str(GAP), str(m), "--json", str(tmp), "--quiet"],
                       capture_output=True, text=True, timeout=600)
        if tmp.is_file():
            out[proj] = json.loads(tmp.read_text())["orphan_files"]
            tmp.unlink()
    return out


def project_scripts(root: Path, proj: str) -> list[tuple[Path, str]]:
    base = root / proj
    hits = []
    for pat in SCRIPT_EXT:
        for p in base.rglob(pat):
            if any(x in p.parts for x in (".git", "__pycache__", ".venv", "node_modules",
                                          ".ipynb_checkpoints")):
                continue
            try:
                txt = p.read_text(errors="replace")
            except OSError:
                continue
            # Un .tex ne PRODUIT une figure que s'il est standalone (il la compose).
            # Un manuscrit qui nomme un stem ne le produit pas : le compter donnait
            # « SCITEPRESS ← main.tex », c'est-a-dire un logo d'editeur pris pour une
            # figure orpheline regenerable.
            if p.suffix == ".tex" and not re.search(
                    r"\\documentclass\s*(?:\[[^\]]*\])?\s*\{(?:standalone|tikz)", txt):
                continue
            hits.append((p, txt))
    return hits


def forest_alive(root: Path) -> set[str]:
    """Basenames des arbres presents dans l'index de la foret, s'il existe."""
    idx = root / ".forest" / "index.jsonl"
    if not idx.is_file():
        return set()
    names = set()
    for line in idx.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        for p in r["paths"]:
            names.add(os.path.basename(p.split("#")[0]))
    return names


# Registres ou un humain a DEJA tranche le sort d'une figure. Les ignorer fait
# reproposer ce qui a ete refuse, ce qui est exactement le travers combattu.
REGISTRIES = ("fig_plan.md", "fig_check.md", "claim_check.md", "supp_check.md")
DECISION = (
    (re.compile(r"\babandonn|\bdiscard|\bne doit pas etre integr|ne doit pas être intégr", re.I), "abandonner"),
    (re.compile(r"\bsupplementary|\bannexe\b", re.I), "supplementary"),
    (re.compile(r"\bintegr|\bintégr|\binclude\b", re.I), "integrer"),
    (re.compile(r"a examiner|à examiner|a trier|à trier", re.I), "a examiner"),
    (re.compile(r"nettoyer|doublon", re.I), "nettoyer"),
)


def project_registries(root: Path, proj: Path) -> list[tuple[str, str]]:
    """(chemin, texte) des registres qualite du projet, racine et article*/."""
    out = []
    for d in (proj, *sorted(proj.glob("article*"))):
        for name in REGISTRIES:
            p = d / name
            if p.is_file():
                try:
                    out.append((str(p.relative_to(root)), p.read_text(errors="replace")))
                except OSError:
                    continue
    return out


def already_ruled(stem: str, regs: list[tuple[str, str]]) -> tuple[str, str] | None:
    """La figure a-t-elle deja une decision ecrite ? Rend (registre, decision)."""
    for path, txt in regs:
        for m in re.finditer(re.escape(stem), txt):
            # la decision se lit dans la ligne, ou dans la ligne suivante d'un tableau
            start = txt.rfind("\n", 0, m.start()) + 1
            end = txt.find("\n", m.end())
            line = txt[start:end if end > 0 else len(txt)]
            for rx, label in DECISION:
                if rx.search(line):
                    return path, label
            return path, "mentionnee"
    return None


# Un registre peut trancher un LOT (« les 7 fichiers de resultats/ predatent le
# cadre statistique actuel ») sans nommer une seule figure. Le detecter par nom
# rate alors la decision, d'ou ce drapeau au niveau du projet.
BULK_RULING = re.compile(
    r"(orphelin|orphan|non int[ée]gr|jamais inclus|non incluse|figures? candidates?|"
    r"pr[ée]datent|p[ée]rim[ée]es?|ancien cadre)", re.I)


def bulk_ruling(regs: list[tuple[str, str]]) -> list[str]:
    """Registres qui statuent en bloc sur les figures non integrees."""
    return [p for p, txt in regs if BULK_RULING.search(txt)]


def classify(root: Path, proj: str, orphans: list[str], alive: set[str]) -> list[dict]:
    base = root / proj
    # 1) une figure = un stem, tous formats et tous repertoires confondus
    by_stem: dict[str, list[str]] = defaultdict(list)
    for f in orphans:
        by_stem[Path(f).stem].append(f)
    # les stems REELLEMENT inclus quelque part, pour reperer les familles de versions
    included = set()
    for tex in base.rglob("*.tex"):
        if ".git" in tex.parts:
            continue
        try:
            body = tex.read_text(errors="replace")
        except OSError:
            continue
        for g in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\s*\{([^}]+)\}", body):
            included.add(Path(g).stem)

    scripts = project_scripts(root, proj)
    regs = project_registries(root, base)
    bulk = bulk_ruling(regs)
    stems = sorted(by_stem)
    rows = []
    for stem in stems:
        files = sorted(by_stem[stem])
        mt = max((base / f).stat().st_mtime for f in files if (base / f).is_file())
        # 2) rebut : un membre de la meme famille est plus RECENT sur le disque.
        # Se fier a la longueur du nom classait `fig2_geographic_enhanced` comme
        # perime au profit de `fig2_geographic_distribution` alors que « enhanced »
        # etait la version suivante. Seule la date tranche.
        bare = VERSION_SUFFIX.sub("", stem)
        fam = [s for s in stems if s != stem and (s.startswith(bare) or bare.startswith(VERSION_SUFFIX.sub("", s)))]
        newer = []
        for s in fam:
            other = max((base / x).stat().st_mtime for x in by_stem[s] if (base / x).is_file())
            if other > mt:
                newer.append(s)
        # une version incluse dans un manuscrit prime toujours sur une orpheline
        newer += [s for s in included if s != stem and s.startswith(bare)]
        versioned = bool(VERSION_SUFFIX.search(stem))
        # 3) script producteur
        prod = [str(p.relative_to(root)) for p, txt in scripts if stem in txt]
        # 4) entrees du script : arbre mort, donnee absente
        dead_tree, dead_data = [], []
        for p, txt in scripts:
            if stem not in txt:
                continue
            for lit in TREE_LITERAL.findall(txt):
                b = os.path.basename(lit)
                # Trois garde-fous, chacun paye par un faux positif : une phrase de
                # documentation entre guillemets (« Input topology: ... run.treefile »)
                # n'est pas un chemin ; un fragment d'extension non plus ; et un
                # fichier PRESENT sur le disque n'est pas mort meme s'il est absent de
                # la foret (un `partition.nex` d'IQ-TREE n'est pas un arbre).
                if not b or " " in lit or "{" in lit or "*" in lit or b.startswith("."):
                    continue
                if not re.fullmatch(r"[A-Za-z0-9_.\-]+", b) or b in alive:
                    continue
                if not alive:
                    continue
                if any((base / lit).is_file() or c.is_file()
                       for c in (base / b, p.parent / b)):
                    continue
                if next(base.rglob(b), None) is not None:
                    continue
                dead_tree.append(b)
            for lit in DATA_LITERAL.findall(txt):
                if "{" in lit or "*" in lit or lit.startswith("http"):
                    continue
                cand = [base / lit, root / lit, p.parent / lit]
                if not any(c.is_file() for c in cand) and "/" in lit:
                    dead_data.append(lit)
        ruled = already_ruled(stem, regs)
        if ruled:
            kind = "ARBITREE"
        elif TOOLING.search(stem):
            kind = "OUTILLAGE"
        elif newer:
            kind = "REBUT"
        elif dead_tree:
            kind = "DONNEE MORTE"
        elif prod:
            kind = "CANDIDAT"
        else:
            kind = "INDETERMINE"
        rows.append({"project": proj, "bulk": bulk, "stem": stem, "n_files": len(files),
                     "files": files, "mtime": mt, "kind": kind,
                     "ruled": list(ruled) if ruled else None,
                     "scripts": sorted(set(prod))[:3],
                     "dead_tree": sorted(set(dead_tree))[:3],
                     "dead_data": sorted(set(dead_data))[:3],
                     "newer": sorted(set(newer))[:3]})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root")
    ap.add_argument("--gap", type=Path)
    ap.add_argument("--project")
    ap.add_argument("--json", type=Path)
    ap.add_argument("--kind", help="n'afficher qu'une categorie")
    ap.add_argument("-k", type=int, default=25)
    a = ap.parse_args()
    root = Path(a.root).resolve()
    orph = load_gap(root, a.gap, a.project)
    alive = forest_alive(root)
    rows = []
    for proj, files in orph.items():
        if files:
            rows += classify(root, proj, files, alive)
    if a.json:
        a.json.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

    nfiles = sum(r["n_files"] for r in rows)
    print(f"{nfiles} fichiers orphelins = {len(rows)} FIGURES distinctes "
          f"dans {len({r['project'] for r in rows})} projets"
          + (" (index de foret absent : arbres non testes)" if not alive else ""))
    flagged = {}
    for r in rows:
        if r.get("bulk"):
            flagged.setdefault(r["project"], r["bulk"])
    if flagged:
        print("\n!! registres qui statuent DEJA en bloc sur les figures non integrees —"
              " les lire avant de proposer un raccordement :")
        for p, regs in sorted(flagged.items()):
            print(f"   {p:38s} {', '.join(regs)}")
    order = ["CANDIDAT", "DONNEE MORTE", "INDETERMINE", "REBUT", "OUTILLAGE", "ARBITREE"]
    counts = {k: sum(1 for r in rows if r["kind"] == k) for k in order}
    print("  " + " | ".join(f"{k} {counts[k]}" for k in order))
    for k in order:
        sel = [r for r in rows if r["kind"] == k]
        if a.kind and k != a.kind:
            continue
        if not sel:
            continue
        print(f"\n### {k} ({len(sel)})")
        for r in sorted(sel, key=lambda x: -x["mtime"])[:a.k]:
            extra = ""
            if r.get("ruled"):
                extra = f"  déjà tranché ({r['ruled'][1]}) dans {os.path.basename(r['ruled'][0])}"
            elif r["dead_tree"]:
                extra = "  arbre absent: " + ",".join(r["dead_tree"])
            elif r["newer"]:
                extra = "  plus récent: " + ",".join(r["newer"])
            elif r["scripts"]:
                extra = "  ← " + os.path.basename(r["scripts"][0])
            print(f"  {r['project'][:34]:34s} {r['stem'][:40]:40s} "
                  f"{r['n_files']}f{extra}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
