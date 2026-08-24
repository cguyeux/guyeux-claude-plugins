import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
PACKAGES = ROOT / "codex_packages" / "plugins"
AUDIT = ROOT / "_audit" / "codex_workflow_package_audit.json"


def frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end == -1:
        return ""
    return text[:end]


class CodexWorkflowPackagesTests(unittest.TestCase):
    def test_workflow_audit_records_ten_rows(self):
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        rows = audit["rows"]
        self.assertEqual(10, len(rows))
        self.assertEqual(
            {
                "atlas-add-lineage",
                "bdd-bridge",
                "denovo-content-qc",
                "documentation",
                "fig-ideation",
                "fetch-tbannotator",
                "mtbc-bilan",
                "mtbc-reboot",
                "pectinated-subclade-mining",
                "strain-qc",
            },
            {row["name"] for row in rows},
        )

    def test_workflow_copies_have_guardrails_and_clean_frontmatter(self):
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        for row in audit["rows"]:
            with self.subTest(name=row["name"]):
                skill = PACKAGES / row["package_candidate"] / "skills" / row["name"]
                text = (skill / "SKILL.md").read_text(encoding="utf-8")
                fm = frontmatter(text)
                self.assertIn("## Codex workflow guardrail", text)
                self.assertNotIn("argument-hint:", fm)
                self.assertNotIn("disable-model-invocation:", fm)
                self.assertNotIn("user-invocable:", fm)
                self.assertNotIn("version:", fm)
                self.assertNotIn("CLAUDE_PLUGIN_ROOT", text)
                self.assertNotIn("~/.claude/cache", text)


if __name__ == "__main__":
    unittest.main()
