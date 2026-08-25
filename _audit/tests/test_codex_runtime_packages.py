import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
PACKAGES = ROOT / "codex_packages" / "plugins"
AUDIT = ROOT / "_audit" / "codex_runtime_package_audit.json"


def frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end == -1:
        return ""
    return text[:end]


class CodexRuntimePackagesTests(unittest.TestCase):
    def test_runtime_audit_records_the_58_materialized_rows(self):
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        rows = audit["rows"]
        self.assertEqual(58, len(rows))
        self.assertEqual(
            {
                "await-canonical-knowledge-path",
                "claude-branding-only",
                "codex-mcp-documentation-only",
                "codex-mcp-tool-prerequisite",
                "external-mcp-fallback-documented",
                "mcp-narrative-only",
                "rewrite-cache-path",
                "rewrite-claude-skill-paths",
            },
            {row["runtime_bucket"] for row in rows},
        )

    def test_runtime_skills_are_materialized_and_clean(self):
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        for row in audit["rows"]:
            with self.subTest(name=row["name"]):
                skill = PACKAGES / row["package_candidate"] / "skills" / row["name"]
                skill_md = skill / "SKILL.md"
                self.assertTrue(skill_md.is_file())
                self.assertFalse(skill.is_symlink())
                text = skill_md.read_text(encoding="utf-8")
                fm = frontmatter(text)
                self.assertNotIn("argument-hint:", fm)
                self.assertNotIn("disable-model-invocation:", fm)
                self.assertNotIn("user-invocable:", fm)
                self.assertNotIn("version:", fm)
                description_value = "\n".join(
                    line for line in fm.splitlines()
                    if not line.startswith("description:")
                )
                self.assertNotIn("<", description_value)
                self.assertNotIn(">", description_value)
                self.assertNotIn("claude mcp add", text)
                self.assertNotIn("Claude Code", text)

    def test_codex_knowledge_paths_are_documented(self):
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        rows = [row for row in audit["rows"] if row["runtime_bucket"] == "await-canonical-knowledge-path"]
        self.assertEqual(["boltz"], [row["name"] for row in rows])
        text = (PACKAGES / "bio-population-genetics" / "skills" / "boltz" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## Codex knowledge path note", text)
        self.assertIn("~/.Codex/knowledge/", text)
        self.assertNotIn("~/.claude/knowledge", text)

    def test_external_mcp_fallback_is_documented(self):
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        rows = [row for row in audit["rows"] if row["runtime_bucket"] == "external-mcp-fallback-documented"]
        self.assertEqual(["clinical-trial-protocol-skill"], [row["name"] for row in rows])
        text = (PACKAGES / "bio-population-genetics" / "skills" / "clinical-trial-protocol-skill" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## Codex external clinical-trials fallback", text)
        self.assertIn("source-limited mode", text)
        self.assertIn("Do not invent comparable trials", text)
        self.assertIn("codex mcp list", text)

    def test_runtime_mcp_tool_prerequisites_get_codex_note(self):
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        rows = [row for row in audit["rows"] if row["runtime_bucket"] == "codex-mcp-tool-prerequisite"]
        self.assertEqual(12, len(rows))
        for row in rows:
            with self.subTest(name=row["name"]):
                text = (PACKAGES / row["package_candidate"] / "skills" / row["name"] / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("## Codex packaging note", text)
                self.assertIn("codex mcp list", text)

    def test_rewritten_runtime_paths_do_not_keep_claude_paths(self):
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        rows = [
            row for row in audit["rows"]
            if row["runtime_bucket"] in {"rewrite-cache-path", "rewrite-claude-skill-paths"}
        ]
        self.assertEqual(10, len(rows))
        for row in rows:
            with self.subTest(name=row["name"]):
                text = (PACKAGES / row["package_candidate"] / "skills" / row["name"] / "SKILL.md").read_text(encoding="utf-8")
                self.assertNotIn("CLAUDE_PLUGIN_ROOT", text)
                self.assertNotIn("~/.claude/skills", text)
                self.assertNotIn("~/.claude/cache", text)
        sra = (PACKAGES / "bio-pathogens" / "skills" / "sra-geolocate" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("~/.cache/codex/sra-geolocate", sra)


if __name__ == "__main__":
    unittest.main()
