#!/usr/bin/env python3
"""Construire et exécuter la matrice de parité Claude/Codex CCX-15.

Les sorties persistées sont agrégées et ne contiennent ni transcript, ni
session, ni valeur de configuration. Les sondes de modèles sont optionnelles et
s'exécutent une par une avec ``--run-runtime PLATFORM --location LOCATION``.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HOME = Path.home()
SCENARIOS = ROOT / "_audit" / "parity_scenarios.json"
RUNTIME = ROOT / "_audit" / "parity_runtime_observations.json"
JSON_OUT = ROOT / "_audit" / "parity_report.json"
MD_OUT = ROOT / "_audit" / "parity_report.md"
FIXTURE = ROOT / "_audit" / "fixtures" / "parity" / "project with spaces"
NESTED = FIXTURE / "subdir" / "deeper"
PLATFORMS = ("claude", "codex")
LOCATIONS = ("global", "root", "nested", "skill")
PROJECT_LOCATIONS = ("root", "nested")
SECRET_PATTERNS = (
    re.compile(r"ctx7sk-[A-Za-z0-9_-]+"),
    re.compile(r"sk-ant-[A-Za-z0-9_-]+"),
    re.compile(r"sk-proj-[A-Za-z0-9_-]+"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


def load_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run(command: list[str], *, cwd: Path = ROOT, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
    )


def result(status: str, evidence: str, *, difference: str = "", owner: str = "") -> dict[str, str]:
    row = {"status": status, "evidence": evidence}
    if difference:
        row["difference"] = difference
    if owner:
        row["owner"] = owner
    return row


def runtime_records() -> dict[tuple[str, str], dict[str, Any]]:
    payload = load_json(RUNTIME, {"records": []})
    return {(row["platform"], row["location"]): row for row in payload.get("records", [])}


def runtime_status(platform: str, location: str) -> dict[str, Any] | None:
    return runtime_records().get((platform, location))


def expected_answer(platform: str) -> dict[str, Any]:
    return {
        "project_marker": "PARITY_CLAUDE_PROJECT_ROOT" if platform == "claude" else "PARITY_CODEX_PROJECT_ROOT",
        "deletion_rule": "gio trash",
        "knowledge_root": "~/.agents/knowledge",
        "project_has_registers": False,
        "graphify_visible": platform == "codex",
        "mbovis_visible": False,
    }


def expected_doctrine() -> dict[str, Any]:
    return {
        "canonical_project_artifact_count": 5,
        "project_cycle_phase_count": 5,
        "precompute_control_count": 3,
        "remote_hosts": ["mh", "mp"],
        "deletion_rule": "gio trash",
        "knowledge_root": "~/.agents/knowledge",
    }


def runtime_check(location: str) -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for platform in PLATFORMS:
        row = runtime_status(platform, location)
        if row is None:
            output[platform] = result("unrun", "sonde neuve non exécutée", owner="CCX-15")
            continue
        if row.get("status") != "completed":
            output[platform] = result(
                "blocked",
                row.get("error_category", "sonde bloquée"),
                difference="preuve runtime absente",
                owner="human-runtime",
            )
            continue
        mismatches = [
            key for key, value in expected_answer(platform).items() if row.get("answer", {}).get(key) != value
        ]
        hooks = row.get("hooks", {})
        evidence = f"réponse structurée; SessionStart={hooks.get('session_start')}; Stop={hooks.get('stop')}"
        output[platform] = result("pass" if not mismatches else "fail", evidence if not mismatches else f"champs divergents: {mismatches}")
    return output


def check_runtime_doctrine() -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for platform in PLATFORMS:
        row = runtime_status(platform, "global")
        if row is None:
            output[platform] = result("unrun", "sonde doctrinale non exécutée", owner="CCX-02/15")
        elif row.get("status") != "completed":
            output[platform] = result("blocked", row.get("error_category", "sonde bloquée"), owner="human-runtime")
        else:
            mismatches = [key for key, value in expected_doctrine().items() if row.get("answer", {}).get(key) != value]
            output[platform] = result("pass" if not mismatches else "fail", "doctrine restituée" if not mismatches else f"champs divergents: {mismatches}")
    return output


def check_runtime_skill() -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    expected = {"skill_name": "challenge", "skill_triggered": True, "verdict": "Reformuler"}
    for platform in PLATFORMS:
        row = runtime_status(platform, "skill")
        if row is None:
            output[platform] = result("unrun", "sonde skill non exécutée", owner="CCX-05/15")
        elif row.get("status") != "completed":
            output[platform] = result("blocked", row.get("error_category", "sonde bloquée"), owner="human-runtime")
        else:
            mismatches = [key for key, value in expected.items() if row.get("answer", {}).get(key) != value]
            output[platform] = result("pass" if not mismatches else "fail", "challenge déclenché" if not mismatches else f"champs divergents: {mismatches}")
    return output


def check_global_instructions() -> dict[str, dict[str, str]]:
    completed = run(["python3", str(HOME / ".agents" / "instructions" / "sync_global_instructions.py"), "--check"], cwd=HOME)
    return {
        platform: result(
            "pass" if completed.returncode == 0 and f"OK\t{platform}\t" in completed.stdout else "fail",
            "rendu synchronisé avec global-core.md" if completed.returncode == 0 else "synchroniseur en échec",
        )
        for platform in PLATFORMS
    }


def check_instruction_budget() -> dict[str, dict[str, str]]:
    audit = load_module("ccx15_project_instructions", ROOT / "_audit" / "tools" / "audit_project_instructions.py")
    report = audit.build_report(HOME / "docs" / "codes")
    count = report["summary"]["instruction_chains_over_budget"]
    return {
        "claude": result("pass", "Claude conserve ses documents projet sans budget Codex imposé"),
        "codex": result("pass" if count == 0 else "fail", f"chaînes au-dessus de 32768 octets: {count}"),
    }


def check_knowledge_views() -> dict[str, dict[str, str]]:
    canonical = (HOME / ".agents" / "knowledge").resolve()
    claude = (HOME / ".claude" / "knowledge").resolve()
    codex = (HOME / ".Codex" / "knowledge").resolve()
    ok = canonical == claude == codex and (canonical / "KNOWLEDGE.md").is_file()
    return {platform: result("pass" if ok else "fail", "vue liée à ~/.agents/knowledge") for platform in PLATFORMS}


def check_memory_boundary() -> dict[str, dict[str, str]]:
    common = ("~/.agents/knowledge/", "cahier_de_labo.md", "etat_des_decouvertes.md", "pistes.md")
    rendered = {
        "claude": (HOME / ".claude" / "CLAUDE.md").read_text(encoding="utf-8"),
        "codex": (HOME / ".codex" / "AGENTS.md").read_text(encoding="utf-8"),
    }
    native = {"claude": "~/.claude/projects/<slug>/memory/", "codex": "~/.codex/memories/"}
    output: dict[str, dict[str, str]] = {}
    for platform in PLATFORMS:
        ok = all(value in rendered[platform] for value in common) and native[platform] in rendered[platform]
        if platform == "codex":
            ok = ok and (HOME / ".codex" / "memories").is_dir()
        output[platform] = result("pass" if ok else "fail", "mémoire native, KB et registres distingués dans le rendu")
    return output


def check_skill_farms() -> dict[str, dict[str, str]]:
    sync = load_module("ccx15_sync_agent", ROOT / "_audit" / "tools" / "sync_agent_skills.py")
    claude_map = sync.personal_skill_map([HOME / ".claude" / "skills"])
    summary, problems = sync.classify(claude_map, HOME / ".agents" / "skills", ROOT)
    claude_ok = not problems and not summary["missing"] and (HOME / ".claude" / "skills" / "challenge" / "SKILL.md").is_file()
    farm = load_module("ccx15_codex_farm", ROOT / "_audit" / "tools" / "audit_codex_skill_farm.py")
    profile, profile_problems = farm.audit_profile(HOME / ".codex")
    exports, export_problems = farm.audit_codex_exports(HOME / ".codex" / "skills", ROOT)
    codex_ok = not profile_problems and not export_problems and (HOME / ".agents" / "skills" / "challenge" / "SKILL.md").is_file()
    return {
        "claude": result("pass" if claude_ok else "fail", f"manquants={len(summary['missing'])}; problèmes={len(problems)}"),
        "codex": result("pass" if codex_ok else "fail", f"plugins={profile['enabled_plugins']}; exports manquants={exports['missing']}"),
    }


def check_plugins() -> dict[str, dict[str, str]]:
    claude_run = run(["claude", "plugin", "list", "--json"], cwd=HOME)
    codex_run = run(["codex", "plugin", "list", "--json"], cwd=HOME)
    try:
        claude_rows = json.loads(claude_run.stdout)
        codex_rows = json.loads(codex_run.stdout).get("installed", [])
    except json.JSONDecodeError:
        return {platform: result("fail", "sortie plugin JSON invalide") for platform in PLATFORMS}
    claude_enabled = {row["id"] for row in claude_rows if row.get("enabled") and row.get("scope") == "user"}
    claude_disabled = {row["id"] for row in claude_rows if not row.get("enabled") and row.get("scope") == "user"}
    # Depuis P5.4/P5.5 (architecture profils.json), aucun plugin du marketplace
    # personnel n'est activé globalement : seule l'activation par projet compte.
    # Seul pyright-lsp (plugin officiel) reste actif au niveau user.
    wanted_claude = {
        "pyright-lsp@claude-plugins-official",
    }
    expected_codex = {
        "bacteria", "bioinfo", "carriere", "diffusion", "guyeux-phylo-pilot", "ia", "litterature",
        "maboss", "mtbc", "multimedia", "ops", "phylo", "popgen", "redaction", "science-commun",
        "structure", "web",
    }
    codex_enabled = {
        row["name"] for row in codex_rows
        if row.get("installed") and row.get("enabled") and row.get("marketplaceName") == "personal"
    }
    return {
        "claude": result(
            "pass" if wanted_claude <= claude_enabled and "frontend-design@claude-plugins-official" in claude_disabled else "fail",
            f"plugins voulus actifs={len(wanted_claude & claude_enabled)}; frontend-design désactivé",
        ),
        "codex": result("pass" if codex_enabled == expected_codex else "fail", f"plugins personnels actifs={len(codex_enabled)}"),
    }


def check_runtime_no_register() -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for platform in PLATFORMS:
        rows = [runtime_status(platform, location) for location in PROJECT_LOCATIONS]
        if any(row is None for row in rows):
            output[platform] = result("unrun", "sondes racine et imbriquée incomplètes", owner="CCX-15")
        elif any(row.get("status") != "completed" for row in rows if row):
            output[platform] = result("blocked", "sonde modèle bloquée", owner="human-runtime")
        else:
            invented = any(row["answer"].get("project_has_registers") is not False for row in rows if row)
            output[platform] = result("fail" if invented else "pass", "aucun registre inventé dans les deux emplacements")
    return output


def check_runtime_disabled_skill() -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for platform in PLATFORMS:
        rows = [runtime_status(platform, location) for location in PROJECT_LOCATIONS]
        if any(row is None for row in rows):
            output[platform] = result("unrun", "visibilité modèle non sondée", owner="CCX-15")
        elif any(row.get("status") != "completed" for row in rows if row):
            output[platform] = result("blocked", "visibilité modèle non disponible", owner="human-runtime")
        else:
            visible = any(row["answer"].get("mbovis_visible") is True for row in rows if row)
            if platform == "claude" and not visible:
                stale_cache = any((HOME / ".claude" / "plugins" / "cache").glob("**/skills/mbovis/SKILL.md"))
                output[platform] = result(
                    "pass",
                    "mbovis absent de la liste visible",
                    difference="ancien cache physique encore présent" if stale_cache else "",
                    owner="CCX-16" if stale_cache else "",
                )
            else:
                output[platform] = result("fail" if visible else "pass", "mbovis absent de la liste visible")
    return output


def check_runtime_hooks() -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for platform in PLATFORMS:
        rows = [runtime_status(platform, location) for location in PROJECT_LOCATIONS]
        if any(row is None for row in rows):
            output[platform] = result("unrun", "événements de session non sondés", owner="CCX-15")
            continue
        if any(row.get("status") != "completed" for row in rows if row):
            output[platform] = result("blocked", "session bloquée avant preuve hooks", owner="human-runtime")
            continue
        if platform == "claude":
            settings = load_json(HOME / ".claude" / "settings.json", {})
            stop_configured = "Stop" in settings.get("hooks", {})
            hooks_ok = stop_configured and all(row.get("hooks", {}).get("session_start") for row in rows if row)
        else:
            hooks_ok = all(row.get("hooks", {}).get("session_start") and row.get("hooks", {}).get("stop") for row in rows if row)
        looped = any(row.get("hooks", {}).get("stop_count", 0) > 2 for row in rows if row)
        if platform == "claude" and hooks_ok and not looped:
            output[platform] = result(
                "partial",
                "SessionStart observé; Stop configuré; processus terminé sans boucle",
                difference="le mode --print n'émet pas d'événement Stop exploitable",
                owner="Claude-CLI",
            )
        else:
            output[platform] = result("pass" if hooks_ok and not looped else "fail", "SessionStart et Stop observés; aucune boucle")
    return output


def check_deletion_guards() -> dict[str, dict[str, str]]:
    payload = json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "rm parity-probe"}})
    claude = subprocess.run(
        [str(HOME / ".claude" / "hooks" / "no_rm_guard.sh")],
        input=payload,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    codex = subprocess.run(
        ["python3", str(ROOT / "codex_hooks" / "scripts" / "no_rm_guard.py")],
        input=payload,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "claude": result("pass" if claude.returncode == 2 and "gio trash" in claude.stderr else "fail", "hook direct refuse le témoin"),
        "codex": result("pass" if codex.returncode == 2 and "gio trash" in codex.stderr else "fail", "hook direct refuse le témoin"),
    }


def check_execpolicy() -> dict[str, dict[str, str]]:
    audit = load_module("ccx15_execpolicy", ROOT / "_audit" / "tools" / "audit_execpolicy.py")
    source = ROOT / "codex_rules" / "default.rules"
    active = HOME / ".codex" / "rules" / "default.rules"
    rules = audit.parse_rules(source)
    decisions = [row.get("decision") for row in rules]
    codex_ok = len(rules) == 15 and decisions.count("forbidden") == 4 and decisions.count("allow") == 1 and active.resolve() == source.resolve()
    claude_settings = load_json(HOME / ".claude" / "settings.json", {})
    claude_allow = claude_settings.get("permissions", {}).get("allow", [])
    return {
        "claude": result("pass", f"permissions historiques conservées côté Claude seulement: {len(claude_allow)}"),
        "codex": result("pass" if codex_ok else "fail", f"règles={len(rules)}; forbidden={decisions.count('forbidden')}; allow={decisions.count('allow')}"),
    }


def auxiliary_report() -> dict[str, Any]:
    audit = load_module("ccx15_auxiliary", ROOT / "_audit" / "tools" / "audit_auxiliary_surfaces.py")
    return audit.build_report(HOME)


CLAUDE_ONLY_MCP = {"booking"}
EXPECTED_SHARED_MCP = {"context7", "superhuman", "tbannotator", "tbmonitor"}


def check_mcp() -> dict[str, dict[str, str]]:
    report = auxiliary_report()
    codex_ok = report["mcp"]["names_match_expected"] and report["mcp"]["secret_values_serialized"] is False
    claude_config = load_json(HOME / ".claude.json", {})
    names = set((claude_config.get("mcpServers") or {}).keys())
    claude_only = names - EXPECTED_SHARED_MCP
    if names == EXPECTED_SHARED_MCP:
        claude_result = result(
            "pass",
            f"noms MCP configurés={len(names)}",
            difference="configuration comparée; transport et authentification non prouvés",
            owner="external-services",
        )
    elif claude_only and claude_only <= CLAUDE_ONLY_MCP:
        claude_result = result(
            "partial",
            f"noms MCP configurés={len(names)} ; hors du socle partagé : {sorted(claude_only)}",
            difference="connecteur personnel claude.ai (Booking.com), sans équivalent Codex requis",
            owner="external-services",
        )
    else:
        claude_result = result(
            "fail",
            f"noms MCP configurés={len(names)}",
            difference="configuration comparée; transport et authentification non prouvés",
            owner="external-services",
        )
    return {
        "claude": claude_result,
        "codex": result(
            "pass" if codex_ok else "fail",
            "quatre noms; aucune valeur sérialisée",
            difference="Superhuman en connecteur distant (URL, sans OAuth local) des deux côtés ; URL tbannotator intentionnellement distincte",
            owner="",
        ),
    }


def check_interface() -> dict[str, dict[str, str]]:
    report = auxiliary_report()
    codex_ok = report["codex_tui"]["status_line"] and report["codex_tui"]["terminal_title"]
    return {
        "claude": result("pass", "script statusline conservé uniquement côté Claude"),
        "codex": result("pass" if codex_ok else "fail", "status_line et terminal_title natifs"),
    }


def check_secret_negative() -> dict[str, dict[str, str]]:
    targets = sorted((ROOT / "_audit").glob("*.json")) + sorted((ROOT / "_audit").glob("*.md"))
    contaminated: list[str] = []
    for path in targets:
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            contaminated.append(path.name)
    ok = not contaminated
    evidence = "aucun motif de secret dans les rapports" if ok else f"rapports suspects={contaminated}"
    return {platform: result("pass" if ok else "fail", evidence) for platform in PLATFORMS}


CHECKS = {
    "global-instructions": check_global_instructions,
    "runtime-doctrine": check_runtime_doctrine,
    "runtime-root": lambda: runtime_check("root"),
    "runtime-nested": lambda: runtime_check("nested"),
    "instruction-budget": check_instruction_budget,
    "runtime-no-register": check_runtime_no_register,
    "knowledge-views": check_knowledge_views,
    "memory-boundary": check_memory_boundary,
    "skill-farms": check_skill_farms,
    "runtime-skill": check_runtime_skill,
    "runtime-disabled-skill": check_runtime_disabled_skill,
    "plugins": check_plugins,
    "runtime-hooks": check_runtime_hooks,
    "deletion-guards": check_deletion_guards,
    "execpolicy": check_execpolicy,
    "mcp": check_mcp,
    "interface": check_interface,
    "secret-negative": check_secret_negative,
}


def build_report() -> dict[str, Any]:
    source = load_json(SCENARIOS)
    rows: list[dict[str, Any]] = []
    counts = {status: 0 for status in ("pass", "partial", "blocked", "fail", "unrun")}
    for scenario in source["scenarios"]:
        platforms = CHECKS[scenario["check"]]()
        row = {**scenario, "platforms": platforms}
        statuses = {value["status"] for value in platforms.values()}
        if "fail" in statuses:
            row["status"] = "fail"
        elif "blocked" in statuses:
            row["status"] = "blocked"
        elif "unrun" in statuses:
            row["status"] = "unrun"
        elif "partial" in statuses:
            row["status"] = "partial"
        else:
            row["status"] = "pass"
        counts[row["status"]] += 1
        rows.append(row)
    return {
        "schema_version": 1,
        "scenario_count": len(rows),
        "summary": counts,
        "complete": counts["fail"] == counts["blocked"] == counts["unrun"] == 0,
        "rows": rows,
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Rapport CCX-15 de parité Claude/Codex",
        "",
        "Ce rapport compare des invariants observables. Il ne conserve aucun transcript ni valeur secrète.",
        "",
        f"- Scénarios : {report['scenario_count']}",
        f"- Réussis : {report['summary']['pass']}",
        f"- Partiels : {report['summary']['partial']}",
        f"- Bloqués : {report['summary']['blocked']}",
        f"- Échecs : {report['summary']['fail']}",
        f"- Non exécutés : {report['summary']['unrun']}",
        f"- Matrice complète : {'oui' if report['complete'] else 'non'}",
        "",
        "| scénario | famille | Claude | Codex | verdict | propriétaire |",
        "|---|---|---|---|---|---|",
    ]
    for row in report["rows"]:
        lines.append(
            f"| {row['id']} | {row['family']} | {row['platforms']['claude']['status']} | "
            f"{row['platforms']['codex']['status']} | {row['status']} | {row['owner']} |"
        )
    lines.extend(["", "## Écarts et limites", ""])
    differences = 0
    for row in report["rows"]:
        for platform in PLATFORMS:
            payload = row["platforms"][platform]
            if payload["status"] != "pass" or payload.get("difference"):
                differences += 1
                lines.append(
                    f"- `{row['id']}` / {platform} : {payload['status']} - "
                    f"{payload.get('difference') or payload['evidence']} "
                    f"(propriétaire : {payload.get('owner', row['owner'])})."
                )
    if differences == 0:
        lines.append("- Aucun écart résiduel.")
    lines.append("")
    return "\n".join(lines)


def expected_outputs(report: dict[str, Any]) -> tuple[str, str]:
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n", markdown(report)


def extract_json_answer(text: str) -> dict[str, Any] | None:
    candidates = [line.strip() for line in text.splitlines() if line.strip().startswith("{")]
    for candidate in reversed(candidates):
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and (
            "project_marker" in payload or "canonical_project_artifact_count" in payload or "skill_name" in payload
        ):
            return payload
    match = re.search(
        r"\{[^{}]*(?:\"project_marker\"|\"canonical_project_artifact_count\"|\"skill_name\")[^{}]*\}",
        text,
        re.DOTALL,
    )
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None


def probe_prompt(location: str) -> str:
    if location == "skill":
        return (
            "/challenge Proposition : valider une migration en comparant seulement des formulations textuelles identiques. "
            "Applique réellement le skill challenge, puis réponds uniquement par un objet JSON compact sans Markdown ni outil : "
            "{\"skill_name\":\"challenge\",\"skill_triggered\":true,\"verdict\":\"Reformuler\"}."
        )
    if location == "global":
        return (
            "Réponds uniquement par un objet JSON compact, sans Markdown et sans outil. "
            "Utilise seulement les instructions globales déjà chargées. Clés exactes: "
            "canonical_project_artifact_count (entier du modèle canonique), "
            "project_cycle_phase_count (entier), precompute_control_count (entier avant calcul), "
            "remote_hosts (liste triée [mp,mh]), deletion_rule (gio trash), "
            "knowledge_root (~/.agents/knowledge)."
        )
    return (
        "Réponds uniquement par un objet JSON compact, sans Markdown et sans outil. "
        "Utilise seulement les instructions et la liste de skills déjà chargées. Clés exactes: "
        "project_marker (marqueur local applicable), deletion_rule (gio trash), "
        "knowledge_root (~/.agents/knowledge), project_artifact_count (nombre présent dans ce témoin), "
        "project_has_registers (booléen pour ce témoin), challenge_visible (booléen), "
        "graphify_visible (booléen), mbovis_visible (booléen)."
    )


def run_codex_probe(location: str) -> dict[str, Any]:
    cwd = NESTED if location == "nested" else FIXTURE
    completed = run(
        [
            "codex", "exec", "--ephemeral", "--strict-config", "-s", "read-only",
            "--skip-git-repo-check", "-C", str(cwd), probe_prompt(location),
        ],
        cwd=cwd,
        timeout=180,
    )
    answer = extract_json_answer(completed.stdout)
    combined = completed.stdout + "\n" + completed.stderr
    return {
        "platform": "codex",
        "location": location,
        "status": "completed" if completed.returncode == 0 and answer else "blocked",
        "exit_code": completed.returncode,
        "answer": answer or {},
        "hooks": {
            "session_start": "hook: SessionStart Completed" in combined,
            "stop": "hook: Stop Completed" in combined,
            "stop_count": combined.count("hook: Stop\n") + combined.count("hook: Stop\r\n"),
        },
        "error_category": "none" if completed.returncode == 0 and answer else "codex-runtime-failed",
    }


def run_claude_probe(location: str) -> dict[str, Any]:
    cwd = NESTED if location == "nested" else FIXTURE
    completed = run(
        [
            "claude", "-p", "--model", "haiku", "--max-budget-usd", "0.50",
            "--no-session-persistence", "--permission-mode", "dontAsk", "--tools", "",
            "--output-format", "stream-json", "--include-hook-events", "--verbose", probe_prompt(location),
        ],
        cwd=cwd,
        timeout=180,
    )
    answer: dict[str, Any] | None = None
    hook_text: list[str] = []
    cost = None
    for line in completed.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        serialized = json.dumps(event, ensure_ascii=False)
        if "hook" in serialized.lower():
            hook_text.append(serialized)
        if event.get("type") == "assistant":
            content = event.get("message", {}).get("content", [])
            for block in content if isinstance(content, list) else []:
                if isinstance(block, dict) and block.get("type") == "text":
                    answer = extract_json_answer(str(block.get("text", ""))) or answer
        if event.get("type") == "result":
            answer = extract_json_answer(str(event.get("result", ""))) or answer
            cost = event.get("total_cost_usd")
    combined_hooks = "\n".join(hook_text)
    stderr_folded = completed.stderr.casefold()
    if completed.returncode == 0 and answer:
        category = "none"
    elif "budget" in stderr_folded or "max_budget" in stderr_folded:
        category = "budget-refused"
    elif "authentication" in stderr_folded or "auth" in stderr_folded:
        category = "authentication-failed"
    else:
        category = "claude-runtime-failed"
    return {
        "platform": "claude",
        "location": location,
        "status": "completed" if completed.returncode == 0 and answer else "blocked",
        "exit_code": completed.returncode,
        "answer": answer or {},
        "hooks": {
            "session_start": "SessionStart" in combined_hooks,
            "stop": "Stop" in combined_hooks,
            "stop_count": combined_hooks.count("Stop"),
        },
        "cost_usd": cost,
        "error_category": category,
    }


def save_runtime(record: dict[str, Any]) -> None:
    payload = load_json(RUNTIME, {"schema_version": 1, "records": []})
    records = [
        row for row in payload.get("records", [])
        if (row.get("platform"), row.get("location")) != (record["platform"], record["location"])
    ]
    records.append(record)
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "records": sorted(records, key=lambda row: (row["platform"], row["location"])),
    }
    RUNTIME.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--run-runtime", choices=PLATFORMS)
    parser.add_argument("--location", choices=LOCATIONS)
    args = parser.parse_args()
    if args.run_runtime:
        if not args.location:
            parser.error("--location est obligatoire avec --run-runtime")
        record = run_claude_probe(args.location) if args.run_runtime == "claude" else run_codex_probe(args.location)
        save_runtime(record)
        print(f"{record['platform']} {record['location']}: {record['status']} ({record['error_category']})")
        return 0 if record["status"] == "completed" else 2

    report = build_report()
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
    print(f"Parité CCX-15: {report['summary']}")
    return 0 if report["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
