import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_audit" / "tools" / "report_agent_skill_divergences.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("report_agent_skill_divergences", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_skill(root: Path, name: str, body: str = "same") -> Path:
    skill = root / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(f"---\nname: {name}\ndescription: x\n---\n{body}\n", encoding="utf-8")
    return skill


def write_delta_root(root: Path, divergent: list[str]) -> Path:
    audit = root / "_audit"
    audit.mkdir(parents=True)
    (audit / "agent_farm_expected_delta.json").write_text(
        json.dumps(
            {
                "common_divergent_expected": divergent,
                "claude_only_expected": [],
                "agents_only_expected": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return root


class AgentSkillDivergenceReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reporter = load_tool()

    def test_real_report_covers_expected_divergences(self):
        report = self.reporter.build_report(
            Path.home() / ".claude" / "skills",
            Path.home() / ".agents" / "skills",
            ROOT,
        )
        self.assertEqual(23, report["total"])
        self.assertEqual(21, report["summary"]["instruction-review-required"])
        self.assertEqual(2, report["summary"]["payload-review-required"])

    def test_skill_md_only_diff_is_instruction_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            claude = base / "claude"
            agents = base / "agents"
            root = write_delta_root(base / "repo", ["shared"])
            write_skill(claude, "shared", "claude")
            write_skill(agents, "shared", "agents")
            report = self.reporter.build_report(claude, agents, root)
            row = report["rows"][0]
            self.assertEqual("instruction-review-required", row["classification"])
            self.assertEqual(["SKILL.md"], row["modified_files"])

    def test_support_file_diff_is_payload_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            claude = base / "claude"
            agents = base / "agents"
            root = write_delta_root(base / "repo", ["shared"])
            claude_skill = write_skill(claude, "shared")
            agents_skill = write_skill(agents, "shared")
            (claude_skill / "script.py").write_text("print('claude')\n", encoding="utf-8")
            (agents_skill / "script.py").write_text("print('agents')\n", encoding="utf-8")
            report = self.reporter.build_report(claude, agents, root)
            row = report["rows"][0]
            self.assertEqual("payload-review-required", row["classification"])
            self.assertEqual(["script.py"], row["modified_files"])


if __name__ == "__main__":
    unittest.main()
