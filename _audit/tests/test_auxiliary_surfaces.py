import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_audit" / "tools" / "audit_auxiliary_surfaces.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("audit_auxiliary_surfaces", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AuxiliarySurfacesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load_tool()

    def test_mcp_summary_never_serializes_values(self):
        config = {
            "mcp_servers": {
                "example": {
                    "url": "https://example.invalid/mcp",
                    "http_headers": {"API_KEY": "top-secret-value"},
                }
            }
        }
        rows = self.audit.safe_mcp_summary(config)
        self.assertEqual([{"name": "example", "transport": "http", "credential_header_count": 1}], rows)
        self.assertNotIn("top-secret-value", repr(rows))

    def test_graphify_check_rejects_destructive_and_legacy_calls(self):
        with tempfile.TemporaryDirectory() as tmp_name:
            home = Path(tmp_name)
            skill = home / ".agents" / "skills" / "graphify"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("rm -f x\nclose_agent(handle)\n", encoding="utf-8")
            result = self.audit.graphify_checks(home)
        self.assertTrue(result["forbidden_instruction_patterns"])

    def test_decision_matrix_covers_expected_surfaces(self):
        source = TOOL.read_text(encoding="utf-8")
        for surface in ("graphify", "pyright-lsp", "agents-bio-redac", "commandes-Claude", "MCP", "statusline"):
            self.assertIn(f'"surface": "{surface}"', source)


if __name__ == "__main__":
    unittest.main()
