#!/usr/bin/env python3
"""Controle deterministe de fin de tour pour Codex.

Ce hook remplace seulement la partie mecanique du gros hook Stop Claude. Il ne
pretend pas juger toute la semantique de la session : quand un doute exige une
interpretation, il demande une continuation courte et explicite.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


MAX_LEVELS = 6
REGISTRY_FILES = ("TASKS.md", "pistes.md", "cahier_de_labo.md", "JOURNAL.md", "etat_des_decouvertes.md")

MATERIAL_RE = re.compile(
    r"\b(commit créé|committé|validation complète|tests? .*OK|audit .*OK|implémenté|installé|"
    r"terminé|clôturé|fait\s*:|créé|porté|mis à jour)\b",
    re.IGNORECASE,
)
STRUCTURAL_RE = re.compile(
    r"\b(résultat structurant|hypothèse tranchée|verdict|acquis solide|pivot d'objectif|itération close)\b",
    re.IGNORECASE,
)
KNOWLEDGE_RE = re.compile(
    r"\b(connaissance produite|apprentissage|hypothèse|interprétation|résultat structurant|"
    r"bug non trivial|logique comprise|approche débloqué|approche débloquée)\b",
    re.IGNORECASE,
)
OPEN_TRACKS_RE = re.compile(r"\b(pistes ouvertes|pistes encore ouvertes|liste actualisée des pistes|CCX-\d+)\b", re.IGNORECASE)
CHAINING_RE = re.compile(r"(^|\n)##\s+Enchaînement proposé\b", re.IGNORECASE)
ETAT_MENTION_RE = re.compile(
    r"\b(etat_des_decouvertes\.md|/etat|état .*réécrit|état .*mis à jour|état non modifié|état inchangé)\b",
    re.IGNORECASE,
)
CAHIER_MENTION_RE = re.compile(
    r"\b(cahier_de_labo\.md|cahier|JOURNAL\.md|/cahier-de-labo|audit en lecture seule|lecture seule|"
    r"pas de mise à jour du cahier)\b",
    re.IGNORECASE,
)
TASK_DONE_RE = re.compile(r"\b(CCX-\d+)\b.{0,80}\b(terminé|clôturé|fermé|done)\b", re.IGNORECASE | re.DOTALL)


@dataclass(frozen=True)
class ProjectRoot:
    path: Path
    has_tasks: bool
    has_pistes: bool
    has_cahier: bool
    has_etat: bool

    @property
    def has_registry(self) -> bool:
        return self.has_tasks or self.has_pistes or self.has_cahier or self.has_etat

    @property
    def has_open_tracks_registry(self) -> bool:
        return self.has_tasks or self.has_pistes


def load_payload() -> dict:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def find_project_root(cwd: Path) -> ProjectRoot | None:
    current = cwd.expanduser().resolve()
    for _ in range(MAX_LEVELS):
        present = {name: (current / name).is_file() for name in REGISTRY_FILES}
        if any(present.values()):
            return ProjectRoot(
                path=current,
                has_tasks=present["TASKS.md"],
                has_pistes=present["pistes.md"],
                has_cahier=present["cahier_de_labo.md"] or present["JOURNAL.md"],
                has_etat=present["etat_des_decouvertes.md"],
            )
        if current.parent == current:
            break
        current = current.parent
    return None


def task_status(root: ProjectRoot, task: str) -> str | None:
    if not root.has_tasks:
        return None
    text = (root.path / "TASKS.md").read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        if task in line:
            if re.search(r"- \[x\]", line, re.IGNORECASE):
                return "done"
            if re.search(r"- \[ \]", line):
                return "open"
    return None


def material_work(message: str) -> bool:
    return bool(MATERIAL_RE.search(message))


def task_claims_done(message: str) -> list[str]:
    return sorted({match.group(1).upper() for match in TASK_DONE_RE.finditer(message)})


def issues(payload: dict, root: ProjectRoot | None) -> list[str]:
    if payload.get("stop_hook_active"):
        return []
    if root is None or not root.has_registry:
        return []
    message = payload.get("last_assistant_message") or ""
    if not isinstance(message, str) or not message.strip():
        return []

    found: list[str] = []
    material = material_work(message)

    if material and root.has_open_tracks_registry:
        if not OPEN_TRACKS_RE.search(message):
            found.append("Réponse de clôture matérielle sans liste actualisée des pistes ouvertes.")
        if not CHAINING_RE.search(message):
            found.append("Réponse de clôture matérielle sans rubrique `## Enchaînement proposé`.")

    for task in task_claims_done(message):
        if task_status(root, task) == "open":
            found.append(f"{task} est annoncé terminé, mais `TASKS.md` le garde ouvert.")

    if STRUCTURAL_RE.search(message) and root.has_etat and not ETAT_MENTION_RE.search(message):
        found.append("Résultat structurant annoncé sans mention de réécriture ou décision explicite sur `etat_des_decouvertes.md`.")

    if KNOWLEDGE_RE.search(message) and root.has_cahier and not CAHIER_MENTION_RE.search(message):
        found.append("Connaissance produite annoncée sans mention du cahier/JOURNAL ni exemption de lecture seule.")

    return found


def approve() -> int:
    print(json.dumps({"continue": True}))
    return 0


def block(messages: list[str]) -> int:
    reason = "Contrôle de fin de session Codex : " + " ".join(messages)
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    return 0


def main() -> int:
    payload = load_payload()
    cwd = payload.get("cwd") or "."
    root = find_project_root(Path(cwd))
    found = issues(payload, root)
    if found:
        return block(found)
    return approve()


if __name__ == "__main__":
    raise SystemExit(main())
