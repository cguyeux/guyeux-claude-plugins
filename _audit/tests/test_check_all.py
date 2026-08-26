import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_audit" / "tools" / "check_all.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("check_all", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CheckAllTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.check_all = load_tool()

    def test_check_all_includes_all_ccx11_controls(self):
        commands = [" ".join(command) for command in self.check_all.build_commands(Path("/tmp/codex-profile"))]
        joined = "\n".join(commands)
        self.assertIn("generate_canon_skills.py --check", joined)
        self.assertIn("generate_codex_package_matrix.py --check", joined)
        self.assertIn("generate_codex_runtime_adaptation_matrix.py --check", joined)
        self.assertIn("docs/build_docs.py --check", joined)
        self.assertIn("audit_skills.py --detail", joined)
        self.assertIn("audit_claude_memories.py --check", joined)
        self.assertIn("sync_codex_skills.py", joined)
        self.assertIn("sync_agent_skills.py", joined)
        self.assertIn("report_agent_skill_divergences.py --check", joined)
        self.assertIn("audit_personal_workflow_skills.py --check", joined)
        self.assertIn("audit_codex_hooks.py --check", joined)
        self.assertIn("audit_auxiliary_surfaces.py --check", joined)
        self.assertIn("validate_parity.py --check", joined)
        self.assertIn("maintain_environment.py validate", joined)
        self.assertIn("sync_execpolicy.py", joined)
        self.assertIn("import_claude_memories.py --check", joined)
        self.assertIn("audit_codex_skill_farm.py --profile-root /tmp/codex-profile", joined)
        self.assertIn("skills_farm.py audit --profile-root /tmp/codex-profile", joined)
        self.assertIn("unittest discover -s _audit/tests", joined)


if __name__ == "__main__":
    unittest.main()
