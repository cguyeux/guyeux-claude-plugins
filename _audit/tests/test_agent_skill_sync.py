import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_audit" / "tools" / "sync_agent_skills.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("sync_agent_skills", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_skill(root: Path, name: str, body: str = "same") -> None:
    skill = root / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(f"---\nname: {name}\ndescription: x\n---\n{body}\n", encoding="utf-8")


def write_delta_root(root: Path, *, claude_only=None, agents_only=None, divergent=None) -> Path:
    audit = root / "_audit"
    audit.mkdir(parents=True)
    (audit / "agent_farm_expected_delta.json").write_text(
        json.dumps(
            {
                "common_divergent_expected": divergent or [],
                "claude_only_expected": claude_only or [],
                "agents_only_expected": agents_only or [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return root


class AgentSkillSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sync = load_tool()

    def test_real_agent_farm_has_no_unplanned_sync_action(self):
        summary, problems = self.sync.classify(
            Path.home() / ".claude" / "skills",
            Path.home() / ".agents" / "skills",
            ROOT,
        )
        self.assertEqual([], problems)
        self.assertEqual([], summary["missing"])
        self.assertEqual(23, len(summary["expected_divergent"]))
        self.assertEqual(7, len(summary["expected_claude_only"]))

    def test_missing_skill_is_actionable_and_apply_creates_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            claude = base / "claude"
            agents = base / "agents"
            delta_root = write_delta_root(base / "repo")
            write_skill(claude, "new-skill")

            summary, problems = self.sync.classify(claude, agents, delta_root)
            self.assertEqual([], problems)
            self.assertEqual(["new-skill"], summary["missing"])

            self.sync.apply_missing(claude, agents, summary["missing"])
            summary, problems = self.sync.classify(claude, agents, delta_root)
            self.assertEqual([], problems)
            self.assertEqual([], summary["missing"])
            self.assertTrue((agents / "new-skill").is_symlink())
            self.assertEqual((claude / "new-skill").resolve(), (agents / "new-skill").resolve())

    def test_unexpected_agents_only_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            claude = base / "claude"
            agents = base / "agents"
            delta_root = write_delta_root(base / "repo")
            write_skill(claude, "shared")
            write_skill(agents, "shared")
            write_skill(agents, "unexpected")

            _summary, problems = self.sync.classify(claude, agents, delta_root)
            self.assertTrue(any("Agents-only non whitelistes" in problem for problem in problems))

    def test_unexpected_common_divergence_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            claude = base / "claude"
            agents = base / "agents"
            delta_root = write_delta_root(base / "repo")
            write_skill(claude, "shared", "claude")
            write_skill(agents, "shared", "agents")

            _summary, problems = self.sync.classify(claude, agents, delta_root)
            self.assertTrue(any("divergences communes non whitelistees" in problem for problem in problems))


if __name__ == "__main__":
    unittest.main()
