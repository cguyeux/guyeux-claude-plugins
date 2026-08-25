#!/usr/bin/env python3
"""Auditer les permissions Claude et les règles execpolicy Codex.

Le rapport ne conserve jamais les commandes complètes des sessions. Il compte
seulement leurs exécutables observés afin d'estimer l'usage réel sans recopier
arguments, chemins, URL ou secrets.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import re
import shlex
import shutil
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = ROOT / "codex_rules" / "default.rules"
DEFAULT_LEGACY = Path.home() / ".codex" / "rules" / "default.rules"
DEFAULT_ACTIVE = Path.home() / ".codex" / "rules" / "default.rules"
DEFAULT_BASELINE = ROOT / "_audit" / "execpolicy_legacy_baseline.json"
DEFAULT_CLAUDE = Path.home() / ".claude" / "settings.json"
DEFAULT_SESSIONS = Path.home() / ".codex" / "sessions"
DEFAULT_JSON = ROOT / "_audit" / "execpolicy_report.json"
DEFAULT_MARKDOWN = ROOT / "_audit" / "execpolicy_report.md"
DESTRUCTIVE = {"rm", "rmdir", "unlink", "shred"}
REMOTE = {"ssh", "scp", "rsync", "curl", "wget", "scw", "gh", "kubectl", "terraform"}
WRAPPERS = {"bash", "/bin/bash", "sh", "/bin/sh", "zsh", "/bin/zsh"}
CMD_RE = re.compile(r'\bcmd\s*:\s*("(?:\\.|[^"\\])*")')
NON_EXECUTABLE_TOKENS = {
    "{", "}", "+", "-", "PY", "EOF", "case", "class", "def", "do", "done",
    "elif", "else", "esac", "except", "fi", "finally", "for", "from", "function",
    "if", "import", "in", "raise", "return", "select", "then", "try", "until",
    "while", "with", "yield",
}


def parse_rules(path: Path) -> list[dict[str, Any]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    rules: list[dict[str, Any]] = []
    for node in tree.body:
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if not isinstance(call.func, ast.Name) or call.func.id != "prefix_rule":
            continue
        values = {keyword.arg: ast.literal_eval(keyword.value) for keyword in call.keywords if keyword.arg}
        values["line"] = node.lineno
        rules.append(values)
    return rules


def first_literals(pattern: list[Any]) -> set[str]:
    if not pattern:
        return set()
    first = pattern[0]
    if isinstance(first, str):
        return {first}
    if isinstance(first, list) and all(isinstance(value, str) for value in first):
        return set(first)
    return set()


def string_atoms(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [atom for item in value for atom in string_atoms(item)]
    return []


def classify_rule(rule: dict[str, Any]) -> set[str]:
    pattern = rule.get("pattern", [])
    flattened = json.dumps(pattern, ensure_ascii=False)
    joined = " ".join(string_atoms(pattern))
    first = first_literals(pattern)
    categories: set[str] = set()
    if (
        first & DESTRUCTIVE
        or re.search(r"\brm\s+-|\bfind\b.*\s-delete\b", joined)
        or ("git" in first and any(value in joined for value in (" clean", " reset --hard", " --force", " -f")))
    ):
        categories.add("destructive")
    if first & REMOTE or ("git" in first and any(value in flattened for value in ("push", "fetch", "pull"))):
        categories.add("remote")
    if first & WRAPPERS:
        categories.add("shell-wrapper")
    if "/tmp/" in flattened:
        categories.add("temporary-path")
    if ".claude/knowledge" in flattened:
        categories.add("legacy-knowledge-path")
    if len(pattern) == 1:
        categories.add("broad-prefix")
    if len(pattern) >= 3 or first & WRAPPERS:
        categories.add("exact-or-long")
    return categories or {"other"}


def claude_permissions(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    permissions = payload.get("permissions", {})
    allow = permissions.get("allow", [])
    bash = [entry for entry in allow if entry.startswith("Bash(")]
    destructive = [entry for entry in bash if re.search(r"\brm\b|-delete\b", entry)]
    exact = [entry for entry in bash if not entry.endswith(":*)") and entry not in {"Bash(python3:)", "Bash(python:)", "Bash(cd:)", "Bash(find:)", "Bash(grep:)", "Bash(awk:)", "Bash(wc:)", "Bash(sort:)", "Bash(cp:)", "Bash(mkdir:)"}]
    return {
        "allow": len(allow),
        "bash": len(bash),
        "non_bash": len(allow) - len(bash),
        "destructive": len(destructive),
        "exact_or_historical": len(exact),
        "deny": len(permissions.get("deny", [])),
        "ask": len(permissions.get("ask", [])),
        "default_mode": permissions.get("defaultMode"),
    }


def command_from_payload(payload: dict[str, Any]) -> str | None:
    if payload.get("type") == "function_call" and payload.get("name") in {"exec_command", "functions.exec_command"}:
        arguments = payload.get("arguments")
        try:
            parsed = json.loads(arguments) if isinstance(arguments, str) else arguments
        except json.JSONDecodeError:
            return None
        return parsed.get("cmd") if isinstance(parsed, dict) else None
    if payload.get("type") == "custom_tool_call" and payload.get("name") == "exec":
        match = CMD_RE.search(payload.get("input", ""))
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
    return None


def executables(command: str) -> list[str]:
    result: list[str] = []
    for line in command.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            tokens = shlex.split(stripped, comments=False, posix=True)
        except ValueError:
            continue
        while tokens and "=" in tokens[0] and not tokens[0].startswith(("/", "./")):
            tokens.pop(0)
        if tokens and tokens[0] not in NON_EXECUTABLE_TOKENS:
            executable = tokens[0]
            if shutil.which(executable) is not None or "/" in executable:
                result.append(Path(executable).name)
    return result


def session_frequency(root: Path, since_days: int) -> dict[str, Any]:
    threshold = date.today() - timedelta(days=max(since_days - 1, 0))
    counter: Counter[str] = Counter()
    files = calls = 0
    if not root.is_dir():
        return {"days": since_days, "files": 0, "tool_calls": 0, "executables": {}}
    for path in root.rglob("*.jsonl"):
        try:
            relative = path.relative_to(root)
            session_date = date(int(relative.parts[0]), int(relative.parts[1]), int(relative.parts[2]))
        except (ValueError, IndexError):
            session_date = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).date()
        if session_date < threshold:
            continue
        files += 1
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("type") != "response_item":
                    continue
                command = command_from_payload(event.get("payload", {}))
                if command is None:
                    continue
                calls += 1
                counter.update(executables(command))
    return {
        "days": since_days,
        "files": files,
        "tool_calls": calls,
        "executables": dict(counter.most_common(30)),
    }


def summarize_rules(rules: list[dict[str, Any]]) -> dict[str, Any]:
    decisions = Counter(rule.get("decision", "allow") for rule in rules)
    categories: Counter[str] = Counter()
    executables_count: Counter[str] = Counter()
    quality = Counter()
    for rule in rules:
        categories.update(classify_rule(rule))
        executables_count.update(sorted(first_literals(rule.get("pattern", []))))
        for field in ("justification", "match", "not_match"):
            if not rule.get(field):
                quality[f"missing_{field}"] += 1
    return {
        "rules": len(rules),
        "decisions": dict(sorted(decisions.items())),
        "categories": dict(sorted(categories.items())),
        "top_executables": dict(executables_count.most_common(20)),
        "quality": dict(sorted(quality.items())),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    if args.legacy_rules is not None:
        legacy_summary = summarize_rules(parse_rules(args.legacy_rules))
    else:
        legacy_summary = json.loads(args.legacy_baseline.read_text(encoding="utf-8"))
    policy = parse_rules(args.policy)
    policy_summary = summarize_rules(policy)
    problems: list[str] = []
    if policy_summary["quality"]:
        problems.append(f"champs de qualité manquants: {policy_summary['quality']}")
    if any(".claude/knowledge" in json.dumps(rule) for rule in policy):
        problems.append("la politique canonique référence encore .claude/knowledge")
    if any("/tmp/" in json.dumps(rule.get("pattern", [])) for rule in policy):
        problems.append("la politique canonique contient encore un chemin temporaire")
    if not any(rule.get("decision") == "forbidden" for rule in policy):
        problems.append("aucune règle forbidden")
    active = {
        "path": str(args.active_rules),
        "is_symlink": args.active_rules.is_symlink(),
        "resolved": str(args.active_rules.resolve()) if args.active_rules.exists() else None,
        "canonical": args.active_rules.exists() and args.active_rules.resolve() == args.policy.resolve(),
    }
    if not active["canonical"]:
        problems.append("la politique active ne pointe pas vers la source canonique")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "claude": claude_permissions(args.claude_settings),
        "legacy_codex": legacy_summary,
        "canonical_codex": policy_summary,
        "active_codex": active,
        "observed_usage": session_frequency(args.sessions_root, args.since_days),
        "problems": problems,
        "ok": not problems,
    }


def render_markdown(report: dict[str, Any]) -> str:
    claude = report["claude"]
    legacy = report["legacy_codex"]
    canonical = report["canonical_codex"]
    usage = report["observed_usage"]
    lines = [
        "# Audit CCX-12 des permissions Claude et Codex",
        "",
        f"Date UTC : `{report['generated_at']}`",
        "",
        "## Inventaire",
        "",
        f"- Claude : {claude['allow']} autorisations, dont {claude['bash']} Bash, {claude['destructive']} destructives et {claude['exact_or_historical']} exactes ou historiques.",
        f"- Codex historique : {legacy['rules']} règles, décisions {legacy['decisions']}.",
        f"- Codex canonique : {canonical['rules']} règles, décisions {canonical['decisions']}.",
        f"- Politique active canonique : {report['active_codex']['canonical']} (`{report['active_codex']['path']}`).",
        f"- Réduction : {legacy['rules'] - canonical['rules']} règles retirées de la politique active.",
        "",
        "## Signaux de dérive historiques",
        "",
    ]
    for name, count in legacy["categories"].items():
        lines.append(f"- `{name}` : {count}")
    lines.extend(["", f"## Usage observé sur {usage['days']} jours", ""])
    lines.append(f"{usage['tool_calls']} appels shell ont été lus dans {usage['files']} fichiers de session. Seuls les noms d'exécutables sont conservés.")
    lines.extend(["", "| Exécutable | Occurrences |", "|---|---:|"])
    for name, count in usage["executables"].items():
        lines.append(f"| `{name}` | {count} |")
    lines.extend(["", "## Politique retenue", ""])
    for decision, count in canonical["decisions"].items():
        lines.append(f"- `{decision}` : {count}")
    lines.extend([
        "",
        "Les commandes ordinaires restent confinées au sandbox. Les règles explicites servent seulement aux sorties du sandbox : suppression permanente interdite, mutations distantes ou système soumises à approbation, et `gio trash` autorisé comme retrait récupérable.",
        "",
        "Les autorisations Claude exactes ne sont pas recopiées. Les commandes sûres n'ont pas besoin d'une permission globale lorsqu'elles restent dans le workspace; les commandes externes ou destructrices doivent conserver une décision contextuelle.",
        "",
        "## Validation",
        "",
        f"Statut structurel : {'OK' if report['ok'] else 'ECHEC'}.",
    ])
    for problem in report["problems"]:
        lines.append(f"- {problem}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--active-rules", type=Path, default=DEFAULT_ACTIVE)
    parser.add_argument("--legacy-rules", type=Path, default=None, help="fichier historique à réinventorier")
    parser.add_argument("--legacy-baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--claude-settings", type=Path, default=DEFAULT_CLAUDE)
    parser.add_argument("--sessions-root", type=Path, default=DEFAULT_SESSIONS)
    parser.add_argument("--since-days", type=int, default=7)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = build_report(args)
    if args.check and args.json_output.is_file():
        previous = json.loads(args.json_output.read_text(encoding="utf-8"))
        report["generated_at"] = previous.get("generated_at", report["generated_at"])
        report["observed_usage"] = previous.get("observed_usage", report["observed_usage"])
    json_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    markdown = render_markdown(report)
    if args.check:
        stale = []
        if not args.json_output.is_file() or args.json_output.read_text(encoding="utf-8") != json_text:
            stale.append(str(args.json_output))
        if not args.markdown_output.is_file() or args.markdown_output.read_text(encoding="utf-8") != markdown:
            stale.append(str(args.markdown_output))
        if stale:
            print(f"STALE: {', '.join(stale)}")
            return 1
    else:
        args.json_output.write_text(json_text, encoding="utf-8")
        args.markdown_output.write_text(markdown, encoding="utf-8")
    print(f"OK: Claude={report['claude']['allow']}, legacy={report['legacy_codex']['rules']}, canonique={report['canonical_codex']['rules']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
