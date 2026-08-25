import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_audit" / "tools" / "dedup_knowledge_staging.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("dedup_knowledge_staging", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def staged(claude: str, codex: str) -> str:
    return "\n".join(
        [
            "<!-- status: needs-human-dedup -->",
            "<!-- BEGIN CLAUDE KNOWLEDGE SOURCE -->",
            claude.rstrip(),
            "<!-- END CLAUDE KNOWLEDGE SOURCE -->",
            "<!-- BEGIN CODEX KNOWLEDGE SOURCE -->",
            codex.rstrip(),
            "<!-- END CODEX KNOWLEDGE SOURCE -->",
            "",
        ]
    )


class KnowledgeBaseDedupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool()

    def test_pointer_codex_keeps_claude_source(self):
        merged = self.tool.merge_file(
            "predictops.md",
            staged(
                "# PredictOps\n\nHistorique complet.\n",
                "# PredictOps\n\nLa base PredictOps historique canonique est conservée dans `~/.claude/knowledge/predictops.md`.\n",
            ),
        )
        self.assertIn("Historique complet.", merged)
        self.assertNotIn("needs-human-dedup", merged)
        self.assertNotIn("BEGIN CODEX", merged)
        self.assertNotIn("historique canonique est conservée", merged)

    def test_knowledge_index_imports_missing_codex_entries(self):
        merged = self.tool.merge_file(
            "KNOWLEDGE.md",
            staged(
                "# Index\n\n- [python-patterns.md](python-patterns.md) — Python.\n",
                "# Index Codex\n\n- `agent-tooling.md` : agents.\n- `python-patterns.md` : doublon.\n",
            ),
        )
        self.assertIn("[agent-tooling.md](agent-tooling.md)", merged)
        self.assertNotIn("`python-patterns.md` : doublon", merged)
        self.assertNotIn("needs-human-dedup", merged)

    def test_entry_file_imports_codex_under_dated_section(self):
        merged = self.tool.merge_file(
            "deployment.md",
            staged("# Déploiement\n\n### Ancien\n", "# Déploiement\n\n### Nouveau\n\nTexte.\n"),
        )
        self.assertIn("## Entrées Codex importées le 2026-08-25", merged)
        self.assertIn("### Ancien", merged)
        self.assertIn("### Nouveau", merged)
        self.assertNotIn("BEGIN CLAUDE", merged)

    def test_dedup_rewrites_files_in_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "predictops.md").write_text(
                staged("# PredictOps\n\nComplet.\n", "# PredictOps\n\nhistorique canonique est conservée ailleurs.\n"),
                encoding="utf-8",
            )
            counts = self.tool.dedup(root)
            self.assertEqual(1, counts["rewritten"])
            self.assertNotIn("needs-human-dedup", (root / "predictops.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
