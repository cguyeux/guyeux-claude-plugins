from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_audit" / "tools" / "audit_project_instructions.py"
SPEC = importlib.util.spec_from_file_location("audit_project_instructions", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ProjectInstructionAuditTests(unittest.TestCase):
    def write(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_classifies_only_observable_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root / "protected" / "CLAUDE.md", "long instructions\n")
            self.write(root / "protected" / "AGENTS.md", "short instructions\n")
            self.write(root / "active" / "CLAUDE.md", "instructions\n")
            self.write(root / "active" / "pistes.md", "- [ ] P1 a examiner\n")
            self.write(root / "archives" / "old" / "CLAUDE.md", "instructions\n")
            self.write(root / "fini" / "stale" / "CLAUDE.md", "instructions\n")
            self.write(root / "fini" / "stale" / "pistes.md", "- [ ] ancienne piste\n")
            self.write(root / "unknown" / "CLAUDE.md", "instructions\n")
            self.write(root / "large" / "CLAUDE.md", "x" * 101)

            report = MODULE.build_report(root, max_bytes=100)
            by_path = {row["path"]: row for row in report["rows"]}

            self.assertEqual(by_path["protected"]["classification"], "agents-local")
            self.assertEqual(by_path["active"]["classification"], "fallback-active-signal")
            self.assertEqual(by_path["archives/old"]["classification"], "fallback-archive-signal")
            self.assertEqual(by_path["fini/stale"]["classification"], "fallback-archive-signal")
            self.assertEqual(by_path["unknown"]["classification"], "fallback-review-required")
            self.assertEqual(by_path["large"]["classification"], "instruction-chain-over-budget")
            self.assertEqual(report["summary"]["fallback_only"], 5)
            self.assertEqual(report["summary"]["fallback_over_budget"], 1)

    def test_agents_takes_precedence_over_other_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root / "archives" / "active" / "CLAUDE.md", "x" * 101)
            self.write(root / "archives" / "active" / "AGENTS.md", "short\n")
            self.write(root / "archives" / "active" / "TASKS.md", "- [ ] open\n")

            row = MODULE.build_report(root, max_bytes=100)["rows"][0]

            self.assertTrue(row["claude_over_budget"])
            self.assertTrue(row["archive_path_signal"])
            self.assertEqual(row["open_work_signals"], ["TASKS.md"])
            self.assertEqual(row["classification"], "agents-local")

    def test_measures_selected_instruction_chain_from_git_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            (root / ".git" / "objects").mkdir()
            self.write(root / ".git" / "HEAD", "ref: refs/heads/main\n")
            self.write(root / "CLAUDE.md", "r" * 60)
            self.write(root / "nested" / "CLAUDE.md", "n" * 50)

            report = MODULE.build_report(root, max_bytes=100)
            by_path = {row["path"]: row for row in report["rows"]}

            self.assertEqual(by_path["."]["instruction_chain_bytes"], 60)
            self.assertEqual(by_path["nested"]["instruction_chain_bytes"], 110)
            self.assertEqual(
                by_path["nested"]["classification"],
                "instruction-chain-over-budget",
            )
            self.assertEqual(
                by_path["nested"]["instruction_chain"],
                ["CLAUDE.md", "nested/CLAUDE.md"],
            )

    def test_override_precedes_agents_and_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root / "CLAUDE.md", "c" * 90)
            self.write(root / "AGENTS.md", "a" * 80)
            self.write(root / "AGENTS.override.md", "o" * 20)

            row = MODULE.build_report(root, max_bytes=50)["rows"][0]

            self.assertTrue(row["agents_local"])
            self.assertTrue(row["agents_override_local"])
            self.assertEqual(row["instruction_chain"], ["AGENTS.override.md"])
            self.assertEqual(row["instruction_chain_bytes"], 20)
            self.assertEqual(row["classification"], "agents-local")

    def test_ignores_incomplete_git_sentinel(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            self.write(root / "parent" / "CLAUDE.md", "p" * 60)
            self.write(root / "parent" / "child" / "CLAUDE.md", "c" * 60)

            report = MODULE.build_report(root, max_bytes=100)
            by_path = {row["path"]: row for row in report["rows"]}

            self.assertEqual(by_path["parent/child"]["git_root"], "parent/child")
            self.assertEqual(by_path["parent/child"]["instruction_chain_bytes"], 60)

    def test_excludes_agent_state_and_dependencies_from_project_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root / "real" / "CLAUDE.md", "real\n")
            self.write(root / ".claude" / "worktrees" / "copy" / "CLAUDE.md", "copy\n")
            self.write(root / "app" / "node_modules" / "package" / "CLAUDE.md", "dependency\n")
            self.write(root / "app" / ".venv_local" / "site-packages" / "lib" / "CLAUDE.md", "venv\n")
            self.write(root / "claude_plugins_index_probe" / "CLAUDE.md", "projection\n")

            report = MODULE.build_report(root)

            self.assertEqual(report["summary"]["discovered_claude_files"], 4)
            self.assertEqual(report["summary"]["project_claude_files"], 1)
            self.assertEqual(report["summary"]["excluded_internal_or_dependency"], 3)
            self.assertEqual([row["path"] for row in report["rows"]], ["real"])

    def test_markdown_contains_every_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root / "a" / "CLAUDE.md", "a\n")
            self.write(root / "b" / "CLAUDE.md", "b\n")

            markdown = MODULE.render_markdown(MODULE.build_report(root))

            self.assertIn("| `a` |", markdown)
            self.assertIn("| `b` |", markdown)
            self.assertIn("decision humaine", markdown)


if __name__ == "__main__":
    unittest.main()
