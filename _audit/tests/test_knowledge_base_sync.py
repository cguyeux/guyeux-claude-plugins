import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_audit" / "tools" / "sync_knowledge_base.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("sync_knowledge_base", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class KnowledgeBaseSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool()

    def test_classifies_union_and_divergence(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            claude = base / "claude"
            codex = base / "codex"
            canonical = base / "agents" / "knowledge"
            claude.mkdir()
            codex.mkdir()
            (claude / "same.md").write_text("same\n", encoding="utf-8")
            (codex / "same.md").write_text("same\n", encoding="utf-8")
            (claude / "left.md").write_text("left\n", encoding="utf-8")
            (codex / "right.md").write_text("right\n", encoding="utf-8")
            (claude / "diff.md").write_text("claude\n", encoding="utf-8")
            (codex / "diff.md").write_text("codex\n", encoding="utf-8")

            report = self.tool.build_report(claude, codex, canonical)
            statuses = {row["path"]: row["status"] for row in report["rows"]}
            self.assertEqual("common-identical", statuses["same.md"])
            self.assertEqual("claude-only", statuses["left.md"])
            self.assertEqual("codex-only", statuses["right.md"])
            self.assertEqual("common-divergent", statuses["diff.md"])
            self.assertEqual(4, len(report["canonical"]["missing_from_canonical"]))

    def test_materialize_preserves_divergent_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            claude = base / "claude"
            codex = base / "codex"
            canonical = base / "agents" / "knowledge"
            claude.mkdir()
            codex.mkdir()
            (claude / "diff.md").write_text("# Claude\n", encoding="utf-8")
            (codex / "diff.md").write_text("# Codex\n", encoding="utf-8")

            report = self.tool.build_report(claude, codex, canonical)
            counts = self.tool.materialize(report)
            merged = (canonical / "diff.md").read_text(encoding="utf-8")
            self.assertEqual(1, counts["merged_staging"])
            self.assertIn("needs-human-dedup", merged)
            self.assertIn("# Claude", merged)
            self.assertIn("# Codex", merged)

    def test_materialize_does_not_overwrite_existing_canonical_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            claude = base / "claude"
            codex = base / "codex"
            canonical = base / "agents" / "knowledge"
            claude.mkdir()
            codex.mkdir()
            canonical.mkdir(parents=True)
            (claude / "left.md").write_text("left\n", encoding="utf-8")
            (canonical / "left.md").write_text("custom\n", encoding="utf-8")

            report = self.tool.build_report(claude, codex, canonical)
            counts = self.tool.materialize(report)
            self.assertEqual(1, counts["preserved_existing"])
            self.assertEqual("custom\n", (canonical / "left.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
