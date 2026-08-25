#!/usr/bin/env python3
"""Injecte un contexte projet leger au demarrage d'une session Codex."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


MAX_LEVELS = 6
RECADRAGE = Path.home() / ".agents" / "skills" / "recadrage" / "recadrage_signals.py"
GENE_SYNC = Path.home() / "docs" / "codes" / "mtbc" / "annotation_mtbc" / "analyses" / "gene_project_sync.py"


def read_hook_input() -> dict:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def find_project_root(start: Path) -> Path | None:
    current = start.resolve()
    for _ in range(MAX_LEVELS):
        if (current / "cahier_de_labo.md").is_file():
            return current
        if current.parent == current:
            return None
        current = current.parent
    return None


def non_empty_head(text: str, limit: int) -> str:
    return "\n".join(line for line in text.splitlines() if line.strip())[:4000].splitlines()[:limit]


def section_between(text: str, start: str, end: str | None, limit: int) -> str:
    lines = text.splitlines()
    active = False
    out: list[str] = []
    for line in lines:
        if line.startswith(start):
            active = True
            continue
        if active and end and line.startswith(end):
            break
        if active and line.strip():
            out.append(line)
        if len(out) >= limit:
            break
    return "\n".join(out)


def grep_open_pistes(path: Path) -> str:
    out: list[str] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if re.search(r"^\s*(#{1,3}|-).*\[(en cours|à faire)\]", line):
            out.append(f"{idx}:{line}")
        if len(out) >= 12:
            break
    return "\n".join(out)


def run_quiet(script: Path, *args: str, timeout: int = 15) -> str:
    if not script.is_file():
        return ""
    try:
        completed = subprocess.run(
            ["python3", str(script), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
        )
    except Exception:
        return ""
    return completed.stdout.strip()


def build_context(root: Path) -> str:
    parts = [f"=== CONTEXTE PROJET : {root.name} (charge au demarrage) ==="]
    etat = root / "etat_des_decouvertes.md"
    if etat.is_file():
        txt = etat.read_text(encoding="utf-8", errors="replace")
        phase = "NON DECLAREE"
        match = re.search(r"\*\*Phase\s*:\*\*\s*([1-5]/5[^*\n]*)", txt)
        if match:
            phase = match.group(1).strip()
        parts.append(f"[CYCLE - phase] {phase}")
        obj = section_between(txt, "## 1.", "## 2.", 6)
        verdict = section_between(txt, "## 8.", None, 3)
        if obj:
            parts.append("[ETAT - objectifs]\n" + obj)
        if verdict:
            parts.append("[ETAT - verdict]\n" + verdict)
    else:
        parts.append("[ETAT] etat_des_decouvertes.md absent.")

    pistes = root / "pistes.md"
    if pistes.is_file():
        open_lines = grep_open_pistes(pistes)
        parts.append("[PISTES - en cours / a faire]\n" + (open_lines or "Aucune piste ouverte detectee dans pistes.md."))
    else:
        parts.append("[PISTES] pistes.md absent.")

    rv = root.name
    if re.fullmatch(r"Rv[0-9]{4}[A-Za-z]?c?", rv):
        drift = run_quiet(GENE_SYNC, rv, "--quiet", timeout=20)
        if drift:
            parts.append("[DERIVE data/ - fiche atlas locale potentiellement perimee]\n" + drift)

    recad = run_quiet(RECADRAGE, str(root), "--quiet", timeout=15)
    if recad:
        parts.append("[RECADRAGE]\n" + recad)

    cahier = root / "cahier_de_labo.md"
    titles = []
    for idx, line in enumerate(cahier.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if line.startswith("## "):
            titles.append(f"{idx}:{line}")
    parts.append("[CAHIER - 3 dernieres entrees]\n" + "\n".join(titles[-3:]))
    parts.append("(Detail : /etat read ; /pistes ; /cahier-de-labo read.)")
    return "\n".join(parts)


def main() -> int:
    payload = read_hook_input()
    start = Path(payload.get("cwd") or Path.cwd()).expanduser()
    root = find_project_root(start)
    if root is None:
        return 0
    context = build_context(root)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
