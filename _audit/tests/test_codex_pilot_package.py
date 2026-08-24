#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "codex_packages" / "plugins" / "guyeux-phylo-pilot"
MARKETPLACE = ROOT / "codex_packages" / ".agents" / "plugins" / "marketplace.json"
EXPECTED_SKILLS = {
    "tbmonitor-papers",
    "mtbc-prospect",
    "molecular-clock",
    "raxml",
    "iqtree-lsd2",
}


class CodexPilotPackageTests(unittest.TestCase):
    def test_repo_marketplace_points_to_the_pilot(self):
        marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
        self.assertEqual("personal", marketplace["name"])
        self.assertEqual(["guyeux-phylo-pilot"], [entry["name"] for entry in marketplace["plugins"]])
        self.assertEqual(
            "./plugins/guyeux-phylo-pilot",
            marketplace["plugins"][0]["source"]["path"],
        )

    def test_manifest_and_materialized_skill_set(self):
        manifest = json.loads((PACKAGE / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual("guyeux-phylo-pilot", manifest["name"])
        self.assertEqual("./skills/", manifest["skills"])
        skills = {entry.name for entry in (PACKAGE / "skills").iterdir() if entry.is_dir()}
        self.assertEqual(EXPECTED_SKILLS, skills)
        for name in EXPECTED_SKILLS:
            path = PACKAGE / "skills" / name
            self.assertTrue((path / "SKILL.md").is_file(), name)
            self.assertFalse(path.is_symlink(), name)

    def test_packaged_skills_do_not_keep_claude_frontmatter_fields(self):
        for name in EXPECTED_SKILLS:
            with self.subTest(name=name):
                text = (PACKAGE / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertNotIn("argument-hint:", text)
                self.assertNotIn("user-invocable:", text)

    def test_claude_specific_runtime_references_are_removed_from_adapted_copies(self):
        tbmonitor = (PACKAGE / "skills" / "tbmonitor-papers" / "SKILL.md").read_text(encoding="utf-8")
        prospect = (PACKAGE / "skills" / "mtbc-prospect" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("codex mcp add tbmonitor", tbmonitor)
        self.assertNotIn("~/.claude", tbmonitor)
        self.assertNotIn("~/.claude", prospect)
        self.assertNotIn("CLAUDE_PLUGIN_ROOT", prospect)
        self.assertIn("Gate de portabilite Codex", prospect)


if __name__ == "__main__":
    unittest.main()
