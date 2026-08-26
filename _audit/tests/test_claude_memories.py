import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_audit" / "tools" / "audit_claude_memories.py"
IMPORT_TOOL = ROOT / "_audit" / "tools" / "import_claude_memories.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("audit_claude_memories", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ClaudeMemoryAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool()
        spec = importlib.util.spec_from_file_location("import_claude_memories", IMPORT_TOOL)
        cls.importer = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = cls.importer
        spec.loader.exec_module(cls.importer)

    def test_classification_and_sensitive_values_are_not_persisted(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "projects"
            memory = source / "project-key" / "memory"
            memory.mkdir(parents=True)
            path = memory / "reference_secret.md"
            value = "super-secret-value"
            path.write_text(
                "---\ntype: reference\n---\npassword: " + value + "\n",
                encoding="utf-8",
            )
            record = self.tool.audit_file(path, source)
            self.assertEqual("reference", record["source_type"])
            self.assertEqual("durable-candidate", record["freshness"])
            self.assertTrue(record["flags"]["secret_material"])
            self.assertEqual("exclude-sensitive", record["decision"])
            self.assertNotIn(value, json.dumps(record))

    def test_broken_relative_markdown_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "projects"
            memory = source / "project-key" / "memory"
            memory.mkdir(parents=True)
            path = memory / "MEMORY.md"
            path.write_text("- [Absent](missing.md)\n", encoding="utf-8")
            record = self.tool.audit_file(path, source)
            self.assertEqual("index", record["source_type"])
            self.assertEqual(1, record["broken_local_link_count"])
            self.assertTrue(record["flags"]["broken_local_links"])

    def test_project_candidate_requires_no_sensitive_or_broken_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "projects"
            codex = Path(tmp) / "codex"
            memory = source / "project-key" / "memory"
            memory.mkdir(parents=True)
            (memory / "MEMORY.md").write_text("# Index\n", encoding="utf-8")
            (memory / "feedback_rule.md").write_text("---\ntype: feedback\n---\nRègle durable.\n", encoding="utf-8")
            report = self.tool.build_report(source, codex)
            self.assertEqual(2, report["summary"]["markdown_files"])
            self.assertEqual([], report["problems"])
            self.assertTrue(report["projects"]["project-key"]["official_import_candidate"])

    def test_selection_requires_official_detection_and_clean_audit(self):
        report = {
            "projects": {
                "clean": {"official_import_candidate": True},
                "risky": {"official_import_candidate": False},
            }
        }
        self.assertEqual([], self.importer.validate_selection(["clean"], ["clean"], report))
        self.assertTrue(self.importer.validate_selection(["unknown"], ["clean"], report))
        self.assertTrue(self.importer.validate_selection(["risky"], ["risky"], report))

    def test_verify_imported_hashes_and_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            memory = source / "project-key" / "memory"
            memory.mkdir(parents=True)
            (memory / "MEMORY.md").write_text("# Index\n", encoding="utf-8")
            profile = base / "profile"
            target = profile / "memories/extensions/external_agent_import/resources/project-key"
            target.mkdir(parents=True)
            (target / "MEMORY.md").write_text("# Index\n", encoding="utf-8")
            (target / "scope.json").write_text('{"cwd":"/tmp/project"}', encoding="utf-8")
            self.assertEqual([], self.importer.verify_project(source, profile, "project-key"))
            report = {"projects": {"project-key": {"official_import_candidate": True}}}
            pending, current, problems = self.importer.selection_state(
                ["project-key"], [], report, source, profile
            )
            self.assertEqual([], pending)
            self.assertEqual(["project-key"], current)
            self.assertEqual([], problems)


if __name__ == "__main__":
    unittest.main()
