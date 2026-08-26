#!/usr/bin/env python3
"""Piloter l'import officiel et sélectif des mémoires Claude vers Codex.

Sans ``--apply``, le script détecte seulement les projets proposés par Codex.
Avec ``--apply``, chaque clé doit être explicitement sélectionnée et passer
l'audit local. Une sauvegarde récupérable précède toute écriture. Aucune
suppression ni modification de la source Claude n'est implémentée.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import selectors
import shutil
import subprocess
import sys
import time
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]
SOURCE_TOOL = ROOT / "_audit" / "tools"
if str(SOURCE_TOOL) not in sys.path:
    sys.path.insert(0, str(SOURCE_TOOL))
import audit_claude_memories as memory_audit  # noqa: E402


DEFAULT_SOURCE = Path.home() / ".claude" / "projects"
DEFAULT_PROFILE = Path.home() / ".codex"
DEFAULT_BACKUPS = Path.home() / ".agents" / "migration" / "backups" / "memory"
MIGRATION_SOURCE = "claude-code"


class AppServerError(RuntimeError):
    pass


class AppServerClient:
    def __init__(self, codex: str = "codex", timeout: float = 30.0):
        self.timeout = timeout
        self.process = subprocess.Popen(
            [codex, "app-server", "--enable", "external_agent_memory_import", "--listen", "stdio://"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        if self.process.stdin is None or self.process.stdout is None:
            raise AppServerError("pipes app-server indisponibles")
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        self.request_id = 0
        self.request(
            "initialize",
            {
                "clientInfo": {"name": "ccx13-selective-import", "title": "CCX-13", "version": "1.0.0"},
                "capabilities": None,
            },
        )
        self.notify("initialized", {})

    def send(self, payload: dict[str, Any]) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self.process.stdin.flush()

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self.send({"method": method, "params": params})

    def read_until(self, predicate: Callable[[dict[str, Any]], bool]) -> dict[str, Any]:
        deadline = time.monotonic() + self.timeout
        assert self.process.stdout is not None
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise AppServerError(f"app-server arrêté avec code {self.process.returncode}")
            events = self.selector.select(max(0.0, deadline - time.monotonic()))
            if not events:
                continue
            line = self.process.stdout.readline()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if predicate(message):
                return message
        raise AppServerError("délai app-server dépassé")

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self.request_id += 1
        request_id = self.request_id
        self.send({"id": request_id, "method": method, "params": params})
        response = self.read_until(lambda message: message.get("id") == request_id)
        if "error" in response:
            raise AppServerError(json.dumps(response["error"], ensure_ascii=False))
        return response.get("result", {})

    def wait_import(self, import_id: str) -> dict[str, Any]:
        message = self.read_until(
            lambda candidate: candidate.get("method") == "externalAgentConfig/import/completed"
            and candidate.get("params", {}).get("importId") == import_id
        )
        return message["params"]

    def close(self) -> None:
        try:
            if self.process.stdin is not None:
                self.process.stdin.close()
        finally:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)


def detect(client: AppServerClient) -> dict[str, Any]:
    return client.request(
        "externalAgentConfig/detect",
        {
            "cwds": [],
            "includeHome": True,
            "maxSessionAgeDays": 30,
            "maxSessions": 1,
            "migrationSource": MIGRATION_SOURCE,
        },
    )


def detected_memory_item(result: dict[str, Any]) -> dict[str, Any] | None:
    return next((item for item in result.get("items", []) if item.get("itemType") == "MEMORY"), None)


def detected_keys(item: dict[str, Any] | None) -> list[str]:
    if item is None:
        return []
    return list((item.get("details") or {}).get("memory") or [])


def validate_selection(keys: list[str], detected: list[str], report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if not keys:
        problems.append("aucune clé projet sélectionnée")
    for key in keys:
        if key not in detected:
            problems.append(f"projet non proposé par le détecteur officiel : {key}")
            continue
        project = report["projects"].get(key)
        if project is None:
            problems.append(f"projet absent de l'audit local : {key}")
        elif not project["official_import_candidate"]:
            problems.append(f"projet refusé par l'audit de sensibilité ou d'intégrité : {key}")
    return problems


def selection_state(
    keys: list[str],
    detected: list[str],
    report: dict[str, Any],
    source: Path,
    profile: Path,
) -> tuple[list[str], list[str], list[str]]:
    pending: list[str] = []
    current: list[str] = []
    problems: list[str] = []
    if not keys:
        return pending, current, ["aucune clé projet sélectionnée"]
    for key in keys:
        project = report["projects"].get(key)
        if project is None:
            problems.append(f"projet absent de l'audit local : {key}")
            continue
        if not project["official_import_candidate"]:
            problems.append(f"projet refusé par l'audit de sensibilité ou d'intégrité : {key}")
            continue
        if key in detected:
            pending.append(key)
            continue
        imported = profile / "memories" / "extensions" / "external_agent_import" / "resources" / key
        if imported.is_dir():
            verification = verify_project(source, profile, key)
            if verification:
                problems.extend(verification)
            else:
                current.append(key)
            continue
        problems.append(f"projet non proposé par le détecteur officiel : {key}")
    return pending, current, problems


def selected_item(item: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    selected = json.loads(json.dumps(item))
    selected.setdefault("details", {})["memory"] = list(keys)
    selected["description"] = "Import sélectif CCX-13 de mémoires Claude auditées"
    return selected


def backup_memories(profile: Path, backup_root: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    destination = backup_root / stamp / "memories"
    destination.parent.mkdir(parents=True, exist_ok=False)
    source = profile / "memories"
    if source.exists():
        shutil.copytree(source, destination, symlinks=True)
    else:
        destination.mkdir()
    return destination


def verify_project(source_root: Path, profile: Path, key: str) -> list[str]:
    source = source_root / key / "memory"
    target = profile / "memories" / "extensions" / "external_agent_import" / "resources" / key
    problems: list[str] = []
    scope = target / "scope.json"
    if not scope.is_file():
        problems.append(f"scope.json absent pour {key}")
    else:
        try:
            cwd = json.loads(scope.read_text(encoding="utf-8")).get("cwd")
        except (json.JSONDecodeError, AttributeError):
            cwd = None
        if not cwd or not Path(cwd).is_absolute():
            problems.append(f"cwd absent ou non absolu pour {key}")
    source_files = sorted(source.rglob("*.md"))
    if not source_files:
        problems.append(f"aucune mémoire source pour {key}")
    for source_file in source_files:
        relative = source_file.relative_to(source)
        target_file = target / relative
        if not target_file.is_file():
            problems.append(f"fichier importé absent : {key}/{relative}")
        elif memory_audit.sha256(source_file) != memory_audit.sha256(target_file):
            problems.append(f"hash divergent : {key}/{relative}")
    return problems


def check_imports(source: Path, profile: Path) -> list[str]:
    resources = profile / "memories" / "extensions" / "external_agent_import" / "resources"
    if not resources.is_dir():
        return ["aucun répertoire d'import mémoire officiel"]
    problems: list[str] = []
    keys = sorted(path.name for path in resources.iterdir() if path.is_dir())
    if not keys:
        return ["aucun projet mémoire importé"]
    report = memory_audit.build_report(source, profile / "memories")
    for key in keys:
        project = report["projects"].get(key)
        if project is None:
            problems.append(f"source Claude absente pour l'import {key}")
            continue
        if project["sensitive_files"]:
            problems.append(f"import actif contenant une mémoire sensible : {key}")
        problems.extend(verify_project(source, profile, key))
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--profile-root", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--backup-root", type=Path, default=DEFAULT_BACKUPS)
    parser.add_argument("--project-key", action="append", default=[])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = args.source.expanduser()
    profile = args.profile_root.expanduser()
    if args.check:
        problems = check_imports(source, profile)
        if problems:
            for problem in problems:
                print(f"ÉCHEC : {problem}")
            return 1
        print("OK : imports mémoire officiels présents, non sensibles, rattachés et intègres")
        return 0

    client = AppServerClient()
    try:
        detection = detect(client)
        item = detected_memory_item(detection)
        available = detected_keys(item)
        print("Projets mémoire proposés par Codex :")
        for key in available:
            print(f"- {key}")
        if not args.apply:
            print("Dry-run : aucune mémoire importée. Ajouter --apply et --project-key après revue.")
            return 0
        if item is None:
            print("ÉCHEC : aucun lot MEMORY détecté")
            return 1
        report = memory_audit.build_report(source, profile / "memories")
        pending, current, problems = selection_state(args.project_key, available, report, source, profile)
        if problems:
            for problem in problems:
                print(f"ÉCHEC : {problem}")
            return 1
        for key in current:
            print(f"Déjà à jour : {key}")
        if not pending:
            print(f"OK : {len(current)} projet(s) déjà importé(s), aucun doublon créé")
            return 0
        backup = backup_memories(profile, args.backup_root.expanduser())
        print(f"Sauvegarde récupérable : {backup}")
        response = client.request(
            "externalAgentConfig/import",
            {
                "migrationSource": MIGRATION_SOURCE,
                "providerId": "ccx13-selective",
                "source": "codex-cli-ccx13",
                "migrationItems": [selected_item(item, pending)],
            },
        )
        completed = client.wait_import(response["importId"])
        failures = [
            failure
            for result in completed.get("itemTypeResults", [])
            for failure in result.get("failures", [])
        ]
        if failures:
            for failure in failures:
                print(f"ÉCHEC import : {failure.get('source')}: {failure.get('message')}")
            return 1
        verification = [problem for key in pending for problem in verify_project(source, profile, key)]
        if verification:
            for problem in verification:
                print(f"ÉCHEC : {problem}")
            return 1
        print(f"OK : {len(pending)} projet(s) importé(s), {len(current)} déjà à jour")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
