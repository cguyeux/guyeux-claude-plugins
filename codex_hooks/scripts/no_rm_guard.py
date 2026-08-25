#!/usr/bin/env python3
"""Bloque les suppressions definitives dans les commandes Bash Codex.

Regle portee depuis Claude : jamais `rm`, `unlink`, `shred` ni `find -delete`.
Utiliser `gio trash` pour une suppression recuperable. `git rm` reste autorise
car il s'agit d'une operation versionnee recuperable par Git.
"""
from __future__ import annotations

import json
import re
import shlex
import sys


BLOCKED = {"rm", "unlink", "shred", "-delete"}
COMMAND_SEPARATORS = {";", "&&", "||", "|", "&"}
COMMAND_PREFIXES = {"sudo", "env", "command", "xargs", "nohup", "time", "nice", "taskset"}


def load_command() -> str:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return ""
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def strip_heredoc_bodies(command: str) -> str:
    """Retire les corps de heredoc sans essayer d'interpreter le shell complet."""
    pattern = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
    cursor = 0
    out: list[str] = []
    for match in pattern.finditer(command):
        out.append(command[cursor:match.end()])
        tag = re.escape(match.group(2))
        end = re.search(rf"^\s*{tag}\s*$", command[match.end():], re.MULTILINE)
        if end is None:
            cursor = match.end()
        else:
            cursor = match.end() + end.end()
    out.append(command[cursor:])
    return "".join(out)


def shell_tokens(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError:
        return command.split()


def has_blocked_operation(command: str) -> bool:
    tokens = shell_tokens(strip_heredoc_bodies(command))
    command_position = True
    for index, token in enumerate(tokens):
        if token in COMMAND_SEPARATORS or set(token) <= {";", "&", "|"}:
            command_position = True
            continue
        if token == "-delete":
            return True
        if token in COMMAND_PREFIXES:
            command_position = True
            continue
        if token not in {"rm", "unlink", "shred"}:
            if command_position and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=.*", token):
                command_position = True
            else:
                command_position = False
            continue
        if not command_position:
            continue
        if token == "rm" and index > 0 and tokens[index - 1] == "git":
            command_position = False
            continue
        return True
    return False


def main() -> int:
    command = load_command()
    if not command or not has_blocked_operation(command):
        return 0
    print(
        "BLOQUE : suppression definitive interdite dans cet environnement Codex. "
        "Utiliser `gio trash <fichier_ou_dossier>`. "
        "Si une suppression definitive est indispensable, demander une confirmation explicite a l'utilisateur.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
