#!/usr/bin/env python3
"""Reconstruct, snapshot, restore and audit the personal Claude/Codex setup.

The tool never copies engine credentials, raw profiles, histories, caches or
native memories. Mutating operations are dry-run by default. When ``--apply``
is used, every conflicting derived target is moved to a timestamped rollback
directory before a replacement is created. No permanent-deletion primitive is
implemented.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "maintenance" / "environment_manifest.json"
MARKETPLACE = ROOT / "codex_packages"
HOOKS_SOURCE = ROOT / "codex_hooks" / "hooks.json"
RULES_SOURCE = ROOT / "codex_rules" / "default.rules"
CANON = ROOT / "canon_skills.json"
EXPORTS = ROOT / "codex_skills.json"
SCANNER = Path.home() / ".agents" / "migration" / "ccx_sensitive_scan.py"
DEFAULT_BACKUPS = Path.home() / ".agents" / "migration" / "backups" / "ccx16"
EXCLUDED_PARTS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


class MaintenanceError(RuntimeError):
    pass


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_manifest() -> dict[str, Any]:
    payload = load_json(MANIFEST)
    if payload.get("schema_version") != 1:
        raise MaintenanceError("unsupported maintenance manifest schema")
    return payload


def excluded(relative: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in relative.parts) or relative.suffix in EXCLUDED_SUFFIXES


def iter_tree(path: Path):
    if path.is_symlink() or path.is_file():
        yield Path("."), path
        return
    for child in sorted(path.rglob("*")):
        relative = child.relative_to(path)
        if excluded(relative):
            continue
        if child.is_symlink() or child.is_file():
            yield relative, child


def tree_digest(path: Path) -> tuple[str, int, int]:
    digest = hashlib.sha256()
    files = 0
    size = 0
    if not path.exists() and not path.is_symlink():
        raise MaintenanceError(f"missing source: {path}")
    for relative, child in iter_tree(path):
        label = relative.as_posix().encode("utf-8")
        digest.update(len(label).to_bytes(8, "big"))
        digest.update(label)
        if child.is_symlink():
            content = os.readlink(child).encode("utf-8")
            digest.update(b"L")
        else:
            content = child.read_bytes()
            digest.update(b"F")
            size += len(content)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
        files += 1
    return digest.hexdigest(), files, size


def copy_source(source: Path, target: Path) -> None:
    if source.is_symlink():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(os.readlink(source), target_is_directory=source.resolve().is_dir())
    elif source.is_dir():
        shutil.copytree(
            source,
            target,
            symlinks=True,
            ignore=shutil.ignore_patterns(*sorted(EXCLUDED_PARTS), "*.pyc", "*.pyo"),
        )
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def run(command: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def scanner_for(home: Path) -> Path:
    candidate = home / ".agents" / "migration" / "ccx_sensitive_scan.py"
    return candidate if candidate.is_file() else SCANNER


def scan_source(home: Path, source: Path, profile: str) -> tuple[bool, str]:
    scanner = scanner_for(home)
    if not scanner.is_file():
        return False, "scanner-missing"
    result = run(
        [sys.executable, str(scanner), "scan", "--profile", profile, str(source)],
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    return result.returncode == 0, "clean" if result.returncode == 0 else "scanner-blocked"


def expanded_snapshot_items(home: Path, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    for item in items:
        source = home / item["path"]
        if not item.get("children") or not source.is_dir():
            expanded.append(dict(item))
            continue
        children = sorted(source.iterdir(), key=lambda path: path.name)
        if not children:
            empty = dict(item)
            empty["empty_children_root"] = True
            expanded.append(empty)
            continue
        for child in children:
            child_item = dict(item)
            child_item["id"] = f"{item['id']}/{child.name}"
            child_item["path"] = f"{item['path']}/{child.name}"
            child_item.pop("children", None)
            expanded.append(child_item)
    return expanded


def snapshot(home: Path, destination: Path, *, apply: bool) -> int:
    manifest = load_manifest()
    stamp = utc_stamp()
    bundle = destination.expanduser() / stamp
    rows: list[dict[str, Any]] = []
    blocked = False
    items = expanded_snapshot_items(home, manifest["snapshot_items"])
    for item in items:
        source = home / item["path"]
        if not source.exists() and not source.is_symlink():
            rows.append({"id": item["id"], "status": "missing", "required": item["required"]})
            blocked = blocked or item["required"]
            continue
        clean, reason = scan_source(home, source, item["scanner_profile"])
        if not clean:
            rows.append({"id": item["id"], "status": reason, "required": item["required"]})
            blocked = blocked or item["required"]
            continue
        digest, files, size = tree_digest(source)
        rows.append(
            {
                "id": item["id"],
                "status": "ready",
                "required": item["required"],
                "relative_path": item["path"],
                "sha256": digest,
                "files": files,
                "bytes": size,
            }
        )
    if blocked:
        print(json.dumps({"operation": "snapshot", "status": "blocked", "items": rows}, ensure_ascii=False))
        return 2
    if not apply:
        print(json.dumps({"operation": "snapshot", "status": "dry-run", "bundle": str(bundle), "items": rows}, ensure_ascii=False))
        return 0
    bundle.mkdir(parents=True, mode=0o700)
    payload = bundle / "payload"
    payload.mkdir(mode=0o700)
    for row in rows:
        if row["status"] != "ready":
            continue
        copy_source(home / row["relative_path"], payload / row["id"])
    record = {
        "schema_version": 1,
        "digest_version": 2,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository_commit": git_commit(),
        "items": rows,
        "excluded_classes": ["credentials", "raw-profiles", "histories", "caches", "native-memories"],
    }
    (bundle / "snapshot.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (bundle / "snapshot.json").chmod(0o600)
    print(json.dumps({"operation": "snapshot", "status": "created", "bundle": str(bundle), "items": len(rows)}))
    return 0


def git_commit() -> str:
    result = run(["git", "rev-parse", "HEAD"])
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def safe_target(home: Path, relative: str) -> Path:
    target = (home / relative).resolve(strict=False)
    home_resolved = home.resolve()
    if target != home_resolved and home_resolved not in target.parents:
        raise MaintenanceError(f"target escapes home: {relative}")
    return target


def move_for_rollback(target: Path, home: Path, rollback: Path) -> Path | None:
    if not target.exists() and not target.is_symlink():
        return None
    relative = target.relative_to(home)
    backup = rollback / relative
    backup.parent.mkdir(parents=True, exist_ok=True)
    if backup.exists() or backup.is_symlink():
        raise MaintenanceError(f"rollback target already exists: {backup}")
    target.rename(backup)
    return backup


def same_file_content(left: Path, right: Path) -> bool:
    return left.is_file() and right.is_file() and left.read_bytes() == right.read_bytes()


def same_bytes(content: bytes, target: Path) -> bool:
    return target.is_file() and target.read_bytes() == content


def install_file(source: Path, target: Path, home: Path, rollback: Path, *, apply: bool, actions: list[dict[str, str]]) -> None:
    if same_file_content(source, target):
        actions.append({"target": str(target), "action": "unchanged"})
        return
    actions.append({"target": str(target), "action": "replace" if target.exists() or target.is_symlink() else "create"})
    if not apply:
        return
    move_for_rollback(target, home, rollback)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def install_bytes(content: bytes, target: Path, home: Path, rollback: Path, *, apply: bool, actions: list[dict[str, str]]) -> None:
    if same_bytes(content, target):
        actions.append({"target": str(target), "action": "unchanged"})
        return
    actions.append({"target": str(target), "action": "replace" if target.exists() or target.is_symlink() else "create"})
    if not apply:
        return
    move_for_rollback(target, home, rollback)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    target.chmod(0o644)


def install_link(source: Path, target: Path, home: Path, rollback: Path, *, apply: bool, actions: list[dict[str, str]]) -> None:
    if target.is_symlink() and target.resolve(strict=False) == source.resolve(strict=False):
        actions.append({"target": str(target), "action": "unchanged"})
        return
    actions.append({"target": str(target), "action": "replace-link" if target.exists() or target.is_symlink() else "create-link"})
    if not apply:
        return
    move_for_rollback(target, home, rollback)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(source, target_is_directory=source.is_dir())


def restore_snapshot(home: Path, bundle: Path, rollback: Path, *, apply: bool, actions: list[dict[str, str]]) -> None:
    record = load_json(bundle / "snapshot.json")
    if record.get("digest_version") != 2:
        raise MaintenanceError("unsupported snapshot digest version")
    payload = bundle / "payload"
    for row in record.get("items", []):
        if row.get("status") != "ready":
            continue
        source = payload / row["id"]
        digest, _, _ = tree_digest(source)
        if digest != row["sha256"]:
            raise MaintenanceError(f"snapshot digest mismatch: {row['id']}")
        target = safe_target(home, row["relative_path"])
        actions.append({"target": str(target), "action": "restore-source"})
        if apply:
            move_for_rollback(target, home, rollback)
            copy_source(source, target)


def render_instructions(source_root: Path) -> tuple[bytes, bytes]:
    script = source_root / "sync_global_instructions.py"
    if not script.is_file():
        raise MaintenanceError(f"instruction renderer missing: {script}")
    import importlib.util

    spec = importlib.util.spec_from_file_location("ccx16_instruction_renderer", script)
    if spec is None or spec.loader is None:
        raise MaintenanceError("instruction renderer cannot be imported")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rendered = module.render_all()
    return rendered["claude"].encode("utf-8"), rendered["codex"].encode("utf-8")


def desired_skills() -> dict[str, Path]:
    registry = load_json(CANON)
    exports = load_json(EXPORTS)
    return {name: (ROOT / registry[name]).resolve() for name in exports}


def install_codex_plugins(home: Path) -> None:
    env = {**os.environ, "CODEX_HOME": str(home / ".codex"), "PYTHONDONTWRITEBYTECODE": "1"}
    add_marketplace = run(["codex", "plugin", "marketplace", "add", str(MARKETPLACE)], env=env)
    if add_marketplace.returncode != 0 and "already" not in (add_marketplace.stdout + add_marketplace.stderr).lower():
        raise MaintenanceError("Codex marketplace installation failed")
    for name in load_manifest()["codex_plugins"]:
        result = run(["codex", "plugin", "add", f"{name}@personal"], env=env)
        if result.returncode != 0 and "already" not in (result.stdout + result.stderr).lower():
            raise MaintenanceError(f"Codex plugin installation failed: {name}")


def reconstruct(home: Path, bundle: Path | None, *, apply: bool, plugins: bool) -> int:
    if apply:
        home.mkdir(parents=True, exist_ok=True)
    rollback = home / ".agents" / "migration" / "rollbacks" / f"reconstruct-{utc_stamp()}"
    actions: list[dict[str, str]] = []
    if bundle is not None:
        restore_snapshot(home, bundle.expanduser(), rollback, apply=apply, actions=actions)
    instructions = home / ".agents" / "instructions"
    if not instructions.is_dir() and bundle is not None and not apply:
        snapshot_instructions = bundle.expanduser() / "payload" / "shared-instructions"
        if snapshot_instructions.is_dir():
            instructions = snapshot_instructions
    if not instructions.is_dir():
        raise MaintenanceError("shared instructions missing; provide a CCX-16 snapshot")
    claude_render, codex_render = render_instructions(instructions)
    install_bytes(claude_render, home / ".claude" / "CLAUDE.md", home, rollback, apply=apply, actions=actions)
    install_bytes(codex_render, home / ".codex" / "AGENTS.md", home, rollback, apply=apply, actions=actions)
    knowledge = home / ".agents" / "knowledge"
    if knowledge.is_dir():
        install_link(knowledge, home / ".claude" / "knowledge", home, rollback, apply=apply, actions=actions)
        install_link(knowledge, home / ".Codex" / "knowledge", home, rollback, apply=apply, actions=actions)
    else:
        actions.append({"target": str(knowledge), "action": "manual-private-source-required"})
    install_file(HOOKS_SOURCE, home / ".codex" / "hooks.json", home, rollback, apply=apply, actions=actions)
    install_link(RULES_SOURCE, home / ".codex" / "rules" / "default.rules", home, rollback, apply=apply, actions=actions)
    skills_root = home / ".codex" / "skills"
    if apply:
        skills_root.mkdir(parents=True, exist_ok=True)
    for name, source in desired_skills().items():
        install_link(source, skills_root / name, home, rollback, apply=apply, actions=actions)
    if apply:
        if plugins:
            install_codex_plugins(home)
    print(
        json.dumps(
            {
                "operation": "reconstruct",
                "status": "applied" if apply else "dry-run",
                "rollback": str(rollback) if apply else None,
                "actions": actions,
                "manual_prerequisites": ["private knowledge and personal skills", "Claude and Codex authentication", "MCP OAuth and secret environment variables"],
            },
            ensure_ascii=False,
        )
    )
    return 0


def audit(home: Path) -> tuple[dict[str, Any], int]:
    manifest = load_manifest()
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "status": "pass" if ok else "fail", "detail": detail})

    source_instructions = home / ".agents" / "instructions"
    add("shared-instructions", source_instructions.is_dir(), "present" if source_instructions.is_dir() else "missing")
    if source_instructions.is_dir():
        try:
            claude_render, codex_render = render_instructions(source_instructions)
            add("claude-global-instructions", same_bytes(claude_render, home / ".claude" / "CLAUDE.md"), "matches-source")
            add("codex-global-instructions", same_bytes(codex_render, home / ".codex" / "AGENTS.md"), "matches-source")
        except MaintenanceError:
            add("global-instruction-render", False, "render-failed")
    knowledge = home / ".agents" / "knowledge"
    for label, target in (("claude-knowledge-view", home / ".claude" / "knowledge"), ("codex-knowledge-view", home / ".Codex" / "knowledge")):
        add(label, target.is_symlink() and target.resolve(strict=False) == knowledge.resolve(strict=False), "canonical-link")
    hooks_target = home / ".codex" / "hooks.json"
    add("codex-hooks", same_file_content(HOOKS_SOURCE, hooks_target), "approved-source-match")
    rules_target = home / ".codex" / "rules" / "default.rules"
    add("codex-execpolicy", rules_target.is_symlink() and rules_target.resolve(strict=False) == RULES_SOURCE.resolve(), "canonical-link")
    desired = desired_skills()
    missing = [name for name, source in desired.items() if not ((home / ".codex" / "skills" / name).is_symlink() and (home / ".codex" / "skills" / name).resolve(strict=False) == source)]
    add("codex-direct-skills", not missing, f"missing-or-divergent={len(missing)}")
    dead = []
    for relative in (".agents/skills", ".claude/skills", ".codex/skills"):
        root = home / relative
        if root.is_dir():
            dead.extend(str(path.relative_to(home)) for path in root.rglob("*") if path.is_symlink() and not path.exists())
    add("skill-links", not dead, f"dead={len(dead)}")
    disabled_hits = []
    for name in manifest["disabled_skill_names"]:
        direct = home / ".codex" / "skills" / name
        if direct.exists() or direct.is_symlink():
            disabled_hits.append(name)
        cache = home / ".codex" / "plugins" / "cache" / "personal"
        if cache.is_dir() and any(cache.glob(f"*/0.1.0/skills/{name}")):
            disabled_hits.append(name)
    add("disabled-skills", not disabled_hits, f"visible={len(set(disabled_hits))}")
    config = home / ".codex" / "config.toml"
    plugin_names: set[str] = set()
    mcp_names: set[str] = set()
    if config.is_file():
        import tomllib

        with config.open("rb") as handle:
            payload = tomllib.load(handle)
        plugin_names = {
            key.removesuffix("@personal")
            for key, value in payload.get("plugins", {}).items()
            if key.endswith("@personal") and isinstance(value, dict) and value.get("enabled") is True
        }
        mcp_names = set(payload.get("mcp_servers", {}))
    add("codex-plugins", plugin_names == set(manifest["codex_plugins"]), f"enabled={len(plugin_names)}")
    add("mcp-names", mcp_names == {"context7", "superhuman", "tbannotator", "tbmonitor"}, f"configured={len(mcp_names)}")
    source_checks = {
        "canon-registry": [sys.executable, "_audit/tools/generate_canon_skills.py", "--check"],
        "package-matrix": [sys.executable, "_audit/tools/generate_codex_package_matrix.py", "--check"],
        "runtime-matrix": [sys.executable, "_audit/tools/generate_codex_runtime_adaptation_matrix.py", "--check"],
    }
    for name, command in source_checks.items():
        result = run(command, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        add(name, result.returncode == 0, f"exit={result.returncode}")
    ok = all(row["status"] == "pass" for row in checks)
    report = {
        "schema_version": 1,
        "status": "pass" if ok else "fail",
        "repository_commit": git_commit(),
        "checks": checks,
        "secrets_serialized": False,
        "manual_private_sources": [item["id"] for item in manifest["manual_private_sources"]],
    }
    return report, 0 if ok else 1


def restore(home: Path, bundle: Path, *, apply: bool) -> int:
    rollback = home / ".agents" / "migration" / "rollbacks" / f"restore-{utc_stamp()}"
    actions: list[dict[str, str]] = []
    restore_snapshot(home, bundle.expanduser(), rollback, apply=apply, actions=actions)
    print(json.dumps({"operation": "restore", "status": "applied" if apply else "dry-run", "rollback": str(rollback) if apply else None, "actions": actions}))
    return 0


def validate() -> int:
    manifest = load_manifest()
    problems: list[str] = []
    snapshot_ids = [item.get("id") for item in manifest.get("snapshot_items", [])]
    if len(snapshot_ids) != len(set(snapshot_ids)):
        problems.append("duplicate-snapshot-id")
    snapshot_paths = {item.get("path") for item in manifest.get("snapshot_items", [])}
    never = set(manifest.get("never_snapshot", []))
    if snapshot_paths & never:
        problems.append("never-snapshot-overlap")
    for path in snapshot_paths | never:
        if not isinstance(path, str) or Path(path).is_absolute() or ".." in Path(path).parts:
            problems.append("unsafe-relative-path")
    marketplace = load_json(MARKETPLACE / ".agents" / "plugins" / "marketplace.json")
    marketplace_names = {item.get("name") for item in marketplace.get("plugins", [])}
    if marketplace_names != set(manifest.get("codex_plugins", [])):
        problems.append("codex-plugin-set-drift")
    for relative in manifest.get("repository_relative_sources", []):
        if not (ROOT / relative).exists():
            problems.append(f"missing-repository-source:{relative}")
    service = ROOT / "maintenance" / "systemd" / "codex-migration-audit.service"
    timer = ROOT / "maintenance" / "systemd" / "codex-migration-audit.timer"
    if "maintain_environment.py audit" not in service.read_text(encoding="utf-8"):
        problems.append("service-command-drift")
    if "OnCalendar=weekly" not in timer.read_text(encoding="utf-8"):
        problems.append("timer-calendar-drift")
    script_text = Path(__file__).read_text(encoding="utf-8")
    forbidden = (
        "shutil." + "rmtree(",
        "." + "unlink(",
        "os." + "remove(",
        "os." + "unlink(",
        "subprocess.run([\"" + "rm\"",
    )
    if any(token in script_text for token in forbidden):
        problems.append("permanent-deletion-primitive")
    report = {
        "schema_version": 1,
        "status": "pass" if not problems else "fail",
        "snapshot_items": len(snapshot_ids),
        "manual_private_sources": len(manifest.get("manual_private_sources", [])),
        "never_snapshot": len(never),
        "codex_plugins": len(marketplace_names),
        "problems": problems,
        "secrets_serialized": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not problems else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("snapshot", "audit"):
        child = sub.add_parser(name)
        child.add_argument("--home", type=Path, default=Path.home())
    sub.add_parser("validate")
    snapshot_parser = sub.choices["snapshot"]
    snapshot_parser.add_argument("--destination", type=Path, default=DEFAULT_BACKUPS)
    snapshot_parser.add_argument("--apply", action="store_true")
    restore_parser = sub.add_parser("restore")
    restore_parser.add_argument("bundle", type=Path)
    restore_parser.add_argument("--home", type=Path, default=Path.home())
    restore_parser.add_argument("--apply", action="store_true")
    reconstruct_parser = sub.add_parser("reconstruct")
    reconstruct_parser.add_argument("--home", type=Path, default=Path.home())
    reconstruct_parser.add_argument("--snapshot", type=Path)
    reconstruct_parser.add_argument("--apply", action="store_true")
    reconstruct_parser.add_argument("--install-codex-plugins", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "validate":
            return validate()
        home = args.home.expanduser().resolve()
        if args.command == "snapshot":
            return snapshot(home, args.destination, apply=args.apply)
        if args.command == "restore":
            return restore(home, args.bundle, apply=args.apply)
        if args.command == "reconstruct":
            return reconstruct(home, args.snapshot, apply=args.apply, plugins=args.install_codex_plugins)
        if args.command == "audit":
            report, code = audit(home)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return code
    except (MaintenanceError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "category": type(exc).__name__, "message": str(exc)}))
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
