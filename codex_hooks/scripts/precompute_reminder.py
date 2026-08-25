#!/usr/bin/env python3
"""Rappel non bloquant avant modification d'un script d'analyse."""
from __future__ import annotations

import json
import re
import sys


TARGET = re.compile(r"(^|/)(analyses|experiments)/.*\.(py|R|r|sh)$")
PATCH_PATH = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", re.MULTILINE)


def load_payload() -> dict:
    try:
        value = json.load(sys.stdin)
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def candidate_paths(payload: dict) -> list[str]:
    tool_input = payload.get("tool_input") or {}
    paths: list[str] = []
    for key in ("file_path", "path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            paths.append(value)
    command = tool_input.get("command")
    if isinstance(command, str):
        paths.extend(match.group(1).strip() for match in PATCH_PATH.finditer(command))
    return paths


def should_remind(payload: dict) -> bool:
    return any(TARGET.search(path) for path in candidate_paths(payload))


def main() -> int:
    payload = load_payload()
    if not should_remind(payload):
        return 0
    msg = (
        "AVANT d'ecrire ou modifier ce calcul : verifier 1) deja fait dans cahier_de_labo.md "
        "et pistes.md ; 2) deja publie dans litterature_review/ ou via lit-review, avec "
        "tbmonitor-papers en priorite pour TB/MTBC ; 3) alignement avec etat_des_decouvertes.md "
        "section 1 ; 4) passage au crible challenge : contre-argument, modele nul falsifiant, "
        "gain attendu versus cout."
    )
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": msg}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
