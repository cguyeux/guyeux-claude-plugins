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
    def test_workflow_audit_records_eleven_rows(self):
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        rows = audit["rows"]
        self.assertEqual(11, len(rows))
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
                "soumission",
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

    def test_submission_copy_uses_codex_runtime_and_current_turn_authority(self):
        skill = PACKAGES / "bio-redac" / "skills" / "soumission"
        text = (skill / "SKILL.md").read_text(encoding="utf-8")
        payload = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(skill.rglob("*.md"))
        )
        self.assertIn("## Navigation sous Codex", text)
        self.assertIn("agent-browser", payload)
        self.assertIn("demande explicite dans le tour courant", text)
        self.assertIn("~/.agents/knowledge/journals", payload)
        self.assertNotIn("tabs_context_mcp", payload)
        self.assertNotIn("tabs_close_mcp", payload)
        self.assertNotIn("AskUserQuestion", payload)
        self.assertNotIn("~/.claude/knowledge/journals", payload)


if __name__ == "__main__":
    unittest.main()
