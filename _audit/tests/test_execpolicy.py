import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
AUDIT_TOOL = ROOT / "_audit" / "tools" / "audit_execpolicy.py"
SYNC_TOOL = ROOT / "_audit" / "tools" / "sync_execpolicy.py"
POLICY = ROOT / "codex_rules" / "default.rules"


def load_tool(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ExecPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load_tool("audit_execpolicy", AUDIT_TOOL)
        cls.sync = load_tool("sync_execpolicy", SYNC_TOOL)

    def test_policy_is_small_documented_and_tested(self):
        rules = self.audit.parse_rules(POLICY)
        summary = self.audit.summarize_rules(rules)
        self.assertEqual(15, len(rules))
        self.assertEqual({}, summary["quality"])
        self.assertEqual({"allow": 1, "forbidden": 4, "prompt": 10}, summary["decisions"])
        self.assertNotIn(".claude/knowledge", POLICY.read_text(encoding="utf-8"))

    def test_execpolicy_direct_decisions(self):
        cases = [
            (["rm", "-rf", "/tmp/test"], "forbidden"),
            (["gio", "trash", "/tmp/test"], "allow"),
            (["git", "push", "origin", "main"], "prompt"),
            (["git", "push", "--force", "origin", "main"], "forbidden"),
            (["ssh", "serveur", "hostname"], "prompt"),
        ]
        for command, expected in cases:
            completed = subprocess.run(
                ["codex", "execpolicy", "check", "--rules", str(POLICY), "--", *command],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn(f'"decision":"{expected}"', completed.stdout.replace(" ", "").replace("\n", ""))

    def test_compound_and_opaque_wrappers_never_auto_allow(self):
        scripts = [
            "git status && rm -rf /tmp/test",
            'target=/tmp/test; rm -rf "$target"',
        ]
        for script in scripts:
            completed = subprocess.run(
                ["codex", "execpolicy", "check", "--rules", str(POLICY), "--", "bash", "-lc", script],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertNotIn('"decision":"allow"', completed.stdout.replace(" ", "").replace("\n", ""))

    def test_sync_refuses_unselected_legacy_and_preserves_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source.rules"
            source.write_text("prefix_rule(pattern=[\"gio\", \"trash\"], decision=\"allow\")\n", encoding="utf-8")
            target = base / "profile" / "default.rules"
            target.parent.mkdir()
            target.write_text("legacy\n", encoding="utf-8")
            backups = base / "backups"

            code, backup = self.sync.install(source, target, backups, apply=True, replace_legacy=False)
            self.assertEqual(2, code)
            self.assertIsNone(backup)
            self.assertEqual("legacy\n", target.read_text(encoding="utf-8"))

            code, backup = self.sync.install(source, target, backups, apply=True, replace_legacy=True)
            self.assertEqual(0, code)
            self.assertIsNotNone(backup)
            self.assertTrue(target.is_symlink())
            self.assertEqual("legacy\n", backup.read_text(encoding="utf-8"))

    def test_sync_dry_run_does_not_create_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source.rules"
            source.write_text("policy\n", encoding="utf-8")
            target = base / "target.rules"
            code, backup = self.sync.install(source, target, base / "backups", apply=False, replace_legacy=False)
            self.assertEqual(0, code)
            self.assertIsNone(backup)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
