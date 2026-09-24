#!/usr/bin/env python3
"""Rappel non bloquant avant lancement local d'un calcul lourd."""
from __future__ import annotations

import json
import re
import sys


HEAVY = (
    r"iqtree2?|raxml-ng|raxmlHPC|raxml|beast2?|mrbayes|treetime|mafft|muscle|"
    r"gubbins|[Ff]ast[Tt]ree|modeltest-ng|colabfold_batch|boltz|spades\.py|"
    r"shovill|bwa|bowtie2|hmmsearch|admixture|plink2?"
)
REMOTE_OR_SCHEDULER = re.compile(r"(ssh +(mp|mh)|\bsbatch\b|\bsrun\b|\bsqueue\b|\bscancel\b)")
PROBE_OR_INSTALL = re.compile(r"(--version|--help|\bwhich\b|command -v|pip install|conda install|conda create|apt install)")
POSITION = re.compile(rf"(^|[;&|]|\bnohup |\btime |\bnice(?: -n [0-9]+ )?|\btaskset [^ ]+ |\bxargs )\s*({HEAVY})\b")


def load_command() -> str:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return ""
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def reminder(command: str) -> str | None:
    if not command or REMOTE_OR_SCHEDULER.search(command) or PROBE_OR_INSTALL.search(command):
        return None
    match = POSITION.search(command)
    if not match:
        return None
    tool = match.group(2)
    return (
        f"RAPPEL calcul distant : la commande lance `{tool}` en local. "
        "Pour un calcul lourd, preferer `mp` (64 threads, 125 Gio, /data 51 To) "
        "ou `mh` (Slurm, A100 40 Go, noeuds 1 To) apres VPN monte par l'agent lui-meme (`sudo -n /usr/local/bin/vpn up`, sans mot de passe). "
        "Si c'est un jeu jouet, une mise au point ou si le VPN est indisponible, le local reste acceptable."
    )


def main() -> int:
    msg = reminder(load_command())
    if msg:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": msg}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
