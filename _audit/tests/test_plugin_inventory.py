#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_audit" / "tools"


def load_module(name: str):
    path = TOOLS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module introuvable: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class PluginInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_module("generate_canon_skills")
        cls.auditor = load_module("audit_skills")
        cls.sync = load_module("sync_project_skills")
        cls.codex_sync = load_module("sync_codex_skills")

    def test_all_tools_read_the_seventeen_marketplace_plugins(self):
        expected = [
            "mtbc",
            "bacteria",
            "popgen",
            "ia",
            "maboss",
            "ops",
            "droit",
            "multimedia",
            "web",
            "phylo",
            "bioinfo",
            "structure",
            "litterature",
            "science-commun",
            "redaction",
            "diffusion",
            "carriere",
        ]
        for module in (self.generator, self.auditor, self.sync):
            self.assertEqual(expected, [name for name, _path in module.marketplace_plugins()])

    def test_registry_is_relative_complete_and_active(self):
        registry, duplicates = self.generator.canonical_registry()
        visible_names = set()
        for _plugin, plugin_root in self.generator.marketplace_plugins():
            skills_dir = plugin_root / "skills"
            if skills_dir.is_dir():
                visible_names.update(entry.name for entry in skills_dir.iterdir() if entry.is_dir())
        self.assertEqual(199, len(registry))
        self.assertEqual(visible_names, set(registry))
        self.assertNotIn("phylo-history", duplicates)
        self.assertEqual("mtbc/skills/phylo-history", registry["phylo-history"])
        self.assertEqual("mtbc/skills/phylo-narrative", registry["phylo-narrative"])
        self.assertEqual("bacteria/skills/yersinia-resources", registry["yersinia-resources"])
        self.assertEqual("droit/skills/notes-et-citations", registry["notes-et-citations"])
        for relative in registry.values():
            self.assertFalse(Path(relative).is_absolute())
            self.assertNotIn("skills_disabled", relative)
            path = ROOT / relative
            self.assertTrue(path.is_dir(), relative)
            self.assertFalse(path.is_symlink(), relative)
            self.assertTrue((path / "SKILL.md").is_file(), relative)

    def test_checked_in_registry_matches_generator(self):
        registry, _duplicates = self.generator.canonical_registry()
        current = json.loads((ROOT / "canon_skills.json").read_text(encoding="utf-8"))
        self.assertEqual(registry, current)

    def test_mtbc_mirror_scope_includes_bacteria_but_not_separate_domains(self):
        skills, _notes = self.sync.canonical_skills(False, False)
        self.assertEqual(ROOT / "bacteria/skills/yersinia-resources", skills["yersinia-resources"])
        self.assertNotIn("notes-et-citations", skills)
        self.assertNotIn("maboss-model", skills)

        with_droit, _notes = self.sync.canonical_skills(False, True)
        self.assertEqual(ROOT / "droit/skills/notes-et-citations", with_droit["notes-et-citations"])

    def test_codex_exports_resolve_to_real_canonicals(self):
        desired = self.codex_sync.desired_links()
        remaining_canons = {
            "biotools", "foldseek", "isfinder-offline", "mixed-infection",
            "pocket-detection", "tbannotator-upstream", "binary-coclustering",
            "bioproject-scout", "crispr-spacer-null", "marker-laminarity",
            "rd-detection", "crisprbuilder", "crisprcasdb", "miru-vntr",
            "literature-access", "panisa", "remote-compute", "tbannotator-es",
            "cinema_info", "film_documentaire", "notes-et-citations",
        }
        self.assertTrue(remaining_canons <= set(desired))
        for path in desired.values():
            self.assertTrue((path / "SKILL.md").is_file())

    def test_codex_inventory_is_a_partition_of_the_canonical_registry(self):
        desired, omitted = self.codex_sync.inventory()
        omitted_names = {name for names in omitted.values() for name in names}
        registry = self.codex_sync.load_registry()
        self.assertEqual(199, len(registry))
        self.assertEqual(53, len(desired))
        self.assertEqual(146, len(omitted_names))
        self.assertEqual(set(registry), set(desired) | omitted_names)
        self.assertTrue(set(desired).isdisjoint(omitted_names))
        self.assertIn("tbmonitor-papers", omitted_names)
        self.assertIn("remote-compute", desired)

    def test_codex_sync_classifies_without_overwriting(self):
        import tempfile

        desired = {"one": ROOT / "redaction/skills/bib-check"}
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            self.assertEqual((["one"], [], []), self.codex_sync.classify(target, desired))
            (target / "one").symlink_to(desired["one"], target_is_directory=True)
            self.assertEqual(([], ["one"], []), self.codex_sync.classify(target, desired))


if __name__ == "__main__":
    unittest.main()
