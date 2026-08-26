from __future__ import annotations

import importlib.util
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "_audit" / "tools" / "maintain_environment.py"


def load_module():
    spec = importlib.util.spec_from_file_location("maintain_environment", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        cache = Path.home() / ".cache"
        cache.mkdir(parents=True, exist_ok=True)
        self.tmp = Path(tempfile.mkdtemp(prefix="ccx16-test-", dir=cache))
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.module = load_module()

    def tearDown(self):
        subprocess.run(["gio", "trash", str(self.tmp)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def seed_sources(self):
        instructions = self.home / ".agents" / "instructions"
        self.module.copy_source(Path.home() / ".agents" / "instructions", instructions)
        (self.home / ".agents" / "knowledge").mkdir(parents=True)

    def check(self, report, name):
        return next(row for row in report["checks"] if row["name"] == name)

    def test_manifest_separates_snapshots_private_and_never_copy(self):
        manifest = json.loads((ROOT / "maintenance" / "environment_manifest.json").read_text(encoding="utf-8"))
        snapshot_paths = {row["path"] for row in manifest["snapshot_items"]}
        never = set(manifest["never_snapshot"])
        self.assertFalse(snapshot_paths & never)
        self.assertIn(".codex/config.toml", never)
        self.assertIn("shared-knowledge", {row["id"] for row in manifest["manual_private_sources"]})
        self.assertEqual(self.module.validate(), 0)

    def test_reconstruct_is_dry_run_by_default(self):
        self.seed_sources()
        with contextlib.redirect_stdout(io.StringIO()):
            result = self.module.reconstruct(self.home, None, apply=False, plugins=False)
        self.assertEqual(result, 0)
        self.assertFalse((self.home / ".codex" / "AGENTS.md").exists())
        self.assertFalse((self.home / ".codex" / "hooks.json").exists())

    def test_reconstruct_moves_conflict_to_recoverable_rollback(self):
        self.seed_sources()
        old_hooks = self.home / ".codex" / "hooks.json"
        old_hooks.parent.mkdir(parents=True)
        old_hooks.write_text("legacy\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            result = self.module.reconstruct(self.home, None, apply=True, plugins=False)
        self.assertEqual(result, 0)
        self.assertEqual(old_hooks.read_bytes(), (ROOT / "codex_hooks" / "hooks.json").read_bytes())
        rollbacks = list((self.home / ".agents" / "migration" / "rollbacks").glob("reconstruct-*/.codex/hooks.json"))
        self.assertEqual(len(rollbacks), 1)
        self.assertEqual(rollbacks[0].read_text(encoding="utf-8"), "legacy\n")
        report, _ = self.module.audit(self.home)
        self.assertEqual(self.check(report, "codex-global-instructions")["status"], "pass")
        self.assertEqual(self.check(report, "codex-hooks")["status"], "pass")
        self.assertEqual(self.check(report, "codex-execpolicy")["status"], "pass")
        self.assertEqual(self.check(report, "codex-direct-skills")["status"], "pass")

    def test_disabled_skill_is_detected(self):
        self.seed_sources()
        with contextlib.redirect_stdout(io.StringIO()):
            self.module.reconstruct(self.home, None, apply=True, plugins=False)
        disabled = self.home / ".codex" / "skills" / "mbovis"
        disabled.symlink_to(ROOT / "bio_pathogens" / "skills_disabled" / "mbovis", target_is_directory=True)
        report, code = self.module.audit(self.home)
        self.assertEqual(code, 1)
        self.assertEqual(self.check(report, "disabled-skills")["status"], "fail")

    def test_unapproved_hook_and_dead_link_are_detected(self):
        self.seed_sources()
        with contextlib.redirect_stdout(io.StringIO()):
            self.module.reconstruct(self.home, None, apply=True, plugins=False)
        (self.home / ".codex" / "hooks.json").write_text("{}\n", encoding="utf-8")
        dead = self.home / ".agents" / "skills" / "dead-example"
        dead.parent.mkdir(parents=True)
        dead.symlink_to(self.home / "missing-skill", target_is_directory=True)
        report, code = self.module.audit(self.home)
        self.assertEqual(code, 1)
        self.assertEqual(self.check(report, "codex-hooks")["status"], "fail")
        self.assertEqual(self.check(report, "skill-links")["status"], "fail")

    def test_no_permanent_deletion_primitive(self):
        text = SCRIPT.read_text(encoding="utf-8")
        for token in ("shutil.rmtree(", ".unlink(", "os.remove(", "os.unlink("):
            self.assertNotIn(token, text)

    def test_file_digest_is_independent_of_payload_name(self):
        first = self.tmp / "first-name"
        second = self.tmp / "payload-id"
        first.write_text("same bytes\n", encoding="utf-8")
        second.write_text("same bytes\n", encoding="utf-8")
        self.assertEqual(self.module.tree_digest(first), self.module.tree_digest(second))

    def test_child_snapshot_items_are_isolated(self):
        farm = self.home / ".agents" / "skills"
        (farm / "one").mkdir(parents=True)
        (farm / "two").mkdir()
        items = [{"id": "skills", "path": ".agents/skills", "children": True, "required": False}]
        expanded = self.module.expanded_snapshot_items(self.home, items)
        self.assertEqual([row["id"] for row in expanded], ["skills/one", "skills/two"])


if __name__ == "__main__":
    unittest.main()
