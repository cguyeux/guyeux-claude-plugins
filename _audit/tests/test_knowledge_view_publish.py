import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_audit" / "tools" / "publish_knowledge_views.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("publish_knowledge_views", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class KnowledgeViewPublishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool()

    def test_refuses_canonical_with_staging_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            canonical = Path(tmp) / "canonical"
            canonical.mkdir()
            (canonical / "x.md").write_text("status: needs-human-dedup\n", encoding="utf-8")
            ready, problems = self.tool.canonical_is_ready(canonical)
            self.assertFalse(ready)
            self.assertIn("staging marker remains: x.md", problems)

    def test_publish_moves_existing_view_and_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            canonical = base / "agents" / "knowledge"
            canonical.mkdir(parents=True)
            (canonical / "KNOWLEDGE.md").write_text("# ok\n", encoding="utf-8")
            view = base / ".claude" / "knowledge"
            view.mkdir(parents=True)
            (view / "old.md").write_text("old\n", encoding="utf-8")
            backup_root = base / "backups"

            actions = self.tool.publish(canonical, [view], backup_root, apply=True)
            self.assertTrue(view.is_symlink())
            self.assertEqual(canonical.resolve(), view.resolve())
            backups = list(backup_root.glob("*/claude_knowledge/old.md"))
            self.assertEqual(1, len(backups))
            self.assertIn("backup:", actions[0])

    def test_check_views_reports_missing_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            canonical = base / "agents" / "knowledge"
            canonical.mkdir(parents=True)
            (canonical / "KNOWLEDGE.md").write_text("# ok\n", encoding="utf-8")
            view = base / ".Codex" / "knowledge"
            problems = self.tool.check_views(canonical, [view])
            self.assertEqual([f"not-linked:{view}"], problems)

    def test_publish_is_idempotent_for_existing_correct_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            canonical = base / "agents" / "knowledge"
            canonical.mkdir(parents=True)
            (canonical / "KNOWLEDGE.md").write_text("# ok\n", encoding="utf-8")
            view = base / ".Codex" / "knowledge"
            view.parent.mkdir()
            view.symlink_to(canonical, target_is_directory=True)
            actions = self.tool.publish(canonical, [view], base / "backups", apply=True)
            self.assertEqual([f"ok-already-linked:{view}"], actions)


if __name__ == "__main__":
    unittest.main()
