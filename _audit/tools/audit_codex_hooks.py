#!/usr/bin/env python3
"""Audit CCX-07 des hooks Codex personnels."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "codex_hooks" / "hooks.json"
DEFAULT_INSTALLED = Path.home() / ".codex" / "hooks.json"
JSON_OUT = ROOT / "_audit" / "codex_hooks_report.json"
MD_OUT = ROOT / "_audit" / "codex_hooks_report.md"
SCRIPTS = ROOT / "codex_hooks" / "scripts"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_hook(script: str, payload: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPTS / script)],
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def bash(command: str) -> dict[str, Any]:
    return {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command}}


def stop(cwd: Path, message: str, *, active: bool = False) -> dict[str, Any]:
    return {
        "hook_event_name": "Stop",
        "cwd": str(cwd),
        "stop_hook_active": active,
        "last_assistant_message": message,
    }


def scenario_results() -> dict[str, bool]:
    cases: dict[str, bool] = {}
    for name, command in {
        "block_rm": "rm file.txt",
        "block_unlink": "unlink file.txt",
        "block_shred": "shred file.txt",
        "block_find_delete": "find . -name '*.tmp' -delete",
        "block_xargs_rm": "printf '%s\\n' file.txt | xargs rm",
    }.items():
        cases[name] = run_hook("no_rm_guard.py", bash(command)).returncode == 2
    for name, command in {
        "allow_git_rm": "git rm tracked.txt",
        "allow_docker_rm_flag": "docker run --rm image",
        "allow_grep_rm": "grep rm notes.md",
        "allow_heredoc_body": "cat <<'EOF' > note.md\nancien rm documente\nEOF\n",
    }.items():
        cases[name] = run_hook("no_rm_guard.py", bash(command)).returncode == 0

    patch = "*** Begin Patch\n*** Add File: analyses/new_calc.py\n+print('x')\n*** End Patch\n"
    precompute = run_hook(
        "precompute_reminder.py",
        {"hook_event_name": "PreToolUse", "tool_name": "apply_patch", "tool_input": {"command": patch}},
    )
    cases["precompute_apply_patch"] = precompute.returncode == 0 and "challenge" in precompute.stdout

    remote = run_hook("remote_compute_reminder.py", bash("iqtree2 -s aln.fasta -B 1000"))
    cases["remote_compute_local_heavy"] = remote.returncode == 0 and "mp" in remote.stdout
    silent = run_hook("remote_compute_reminder.py", bash("ssh mp iqtree2 -s aln.fasta"))
    cases["remote_compute_silent_remote"] = silent.returncode == 0 and silent.stdout == ""

    with tempfile.TemporaryDirectory(prefix="codex_stop_guard_") as tmp_name:
        tmp = Path(tmp_name)
        tasks = tmp / "TASKS.md"
        tasks.write_text("- [ ] **CCX-08 Refaire le controle**\n", encoding="utf-8")
        material_missing = run_hook("stop_guard.py", stop(tmp, "Validation complète OK. Commit créé."))
        cases["stop_blocks_material_without_tracks"] = '"decision": "block"' in material_missing.stdout
        with_tracks = run_hook(
            "stop_guard.py",
            stop(tmp, "Validation complète OK.\n\nPistes ouvertes : CCX-08.\n\n## Enchaînement proposé\n\nSuite."),
        )
        cases["stop_allows_material_with_tracks"] = '"continue": true' in with_tracks.stdout
        ccx_open = run_hook(
            "stop_guard.py",
            stop(tmp, "CCX-08 est terminé.\n\nPistes ouvertes : CCX-08.\n\n## Enchaînement proposé\n\nSuite."),
        )
        cases["stop_blocks_open_ccx_claim"] = "CCX-08" in ccx_open.stdout and '"decision": "block"' in ccx_open.stdout
        anti_loop = run_hook("stop_guard.py", stop(tmp, "Validation complète OK.", active=True))
        cases["stop_anti_loop_allows"] = '"continue": true' in anti_loop.stdout
    return cases


def python_syntax_ok() -> dict[str, bool]:
    results: dict[str, bool] = {}
    for path in sorted(SCRIPTS.glob("*.py")):
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError:
            results[path.name] = False
        else:
            results[path.name] = True
    return results


def build_report(installed: Path = DEFAULT_INSTALLED) -> dict[str, Any]:
    installed = installed.expanduser()
    source_payload = load_json(SOURCE)
    installed_payload = load_json(installed) if installed.is_file() else None
    scenarios = scenario_results()
    syntax = python_syntax_ok()
    source_commands = sorted(
        hook["command"]
        for groups in source_payload["hooks"].values()
        for group in groups
        for hook in group["hooks"]
        if hook.get("type") == "command"
    )
    scripts_referenced = sorted(str(path) for path in SCRIPTS.glob("*.py"))
    report = {
        "source": str(SOURCE),
        "installed": str(installed),
        "installed_present": installed.is_file(),
        "installed_matches_source": installed_payload == source_payload,
        "source_commands": source_commands,
        "scripts_referenced": scripts_referenced,
        "syntax": syntax,
        "scenarios": scenarios,
    }
    report["ok"] = (
        report["installed_present"]
        and report["installed_matches_source"]
        and all(syntax.values())
        and all(scenarios.values())
    )
    return report


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Rapport CCX-07 des hooks Codex",
        "",
        "Ce fichier est genere par `_audit/tools/audit_codex_hooks.py`.",
        "",
        f"- Source : `{report['source']}`",
        f"- Installation : `{report['installed']}`",
        f"- Installe : {'oui' if report['installed_present'] else 'non'}",
        f"- Identique a la source : {'oui' if report['installed_matches_source'] else 'non'}",
        f"- Statut : {'OK' if report['ok'] else 'ECHEC'}",
        "",
        "| controle | statut |",
        "|---|---|",
    ]
    for name, ok in sorted(report["syntax"].items()):
        lines.append(f"| syntaxe {name} | {'OK' if ok else 'ECHEC'} |")
    for name, ok in sorted(report["scenarios"].items()):
        lines.append(f"| scenario {name} | {'OK' if ok else 'ECHEC'} |")
    lines.append("")
    return "\n".join(lines)


def expected_outputs(report: dict[str, Any]) -> tuple[str, str]:
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n", markdown(report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installed", type=Path, default=DEFAULT_INSTALLED)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    report = build_report(args.installed)
    json_text, md_text = expected_outputs(report)
    if args.check:
        stale = []
        if not JSON_OUT.is_file() or JSON_OUT.read_text(encoding="utf-8") != json_text:
            stale.append(str(JSON_OUT.relative_to(ROOT)))
        if not MD_OUT.is_file() or MD_OUT.read_text(encoding="utf-8") != md_text:
            stale.append(str(MD_OUT.relative_to(ROOT)))
        if stale:
            print("STALE: " + ", ".join(stale))
            return 1
    else:
        JSON_OUT.write_text(json_text, encoding="utf-8")
        MD_OUT.write_text(md_text, encoding="utf-8")

    print("OK : hooks Codex audites" if report["ok"] else "ECHEC : hooks Codex non conformes")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
