import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_audit" / "tools" / "audit_personal_workflow_skills.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("audit_personal_workflow_skills", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_expected_skill(root: Path, name: str, files: list[str]) -> None:
    skill = root / name
    for relative in files:
        path = skill / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".py":
            path.write_text("def ok():\n    return True\n", encoding="utf-8")
        else:
            path.write_text(f"---\nname: {name}\ndescription: test\n---\n", encoding="utf-8")


class PersonalWorkflowSkillAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load_tool()

    def test_real_agents_farm_has_all_personal_workflow_skills(self):
        report = self.audit.build_report(Path.home() / ".agents" / "skills")
        self.assertEqual(7, report["expected_total"])
        self.assertEqual([], report["problems"])
        self.assertTrue(report["ok"])

    def test_complete_temp_farm_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            agents = Path(tmp)
            for name, files in self.audit.EXPECTED_FILES.items():
                write_expected_skill(agents, name, files)
            report = self.audit.build_report(agents)
            self.assertTrue(report["ok"])
            self.assertEqual(7, report["ok_total"])

    def test_forbidden_claude_reference_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            agents = Path(tmp)
            for name, files in self.audit.EXPECTED_FILES.items():
                write_expected_skill(agents, name, files)
            target = agents / "etat" / "SKILL.md"
            target.write_text(target.read_text(encoding="utf-8") + "Lire CLAUDE.md.\n", encoding="utf-8")
            report = self.audit.build_report(agents)
            self.assertFalse(report["ok"])
            etat = next(row for row in report["rows"] if row["name"] == "etat")
            self.assertIn("SKILL.md", etat["forbidden_references"])

    def test_python_syntax_error_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            agents = Path(tmp)
            for name, files in self.audit.EXPECTED_FILES.items():
                write_expected_skill(agents, name, files)
            target = agents / "pistes" / "split_pistes_files.py"
            target.write_text("def broken(:\n", encoding="utf-8")
            report = self.audit.build_report(agents)
            self.assertFalse(report["ok"])
            pistes = next(row for row in report["rows"] if row["name"] == "pistes")
            self.assertIn("split_pistes_files.py", pistes["python_syntax_errors"])


if __name__ == "__main__":
    unittest.main()
