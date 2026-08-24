#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_audit" / "tools"
PACKAGES = ROOT / "codex_packages" / "plugins"
MARKETPLACE = ROOT / "codex_packages" / ".agents" / "plugins" / "marketplace.json"


def load_module(name: str):
    path = TOOLS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module introuvable: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class CodexDirectPackagesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = load_module("generate_codex_package_matrix")

    def test_direct_candidates_are_materialized_in_package_candidates(self):
        rows = [
            row for row in self.matrix.build_rows()
            if row["classification"] == "packaged-direct"
        ]
        self.assertEqual(48, len(rows))
        for row in rows:
            with self.subTest(name=row["name"]):
                skill = PACKAGES / row["package_candidate"] / "skills" / row["name"]
                self.assertTrue((skill / "SKILL.md").is_file())
                self.assertFalse(skill.is_symlink())

    def test_direct_packages_strip_claude_frontmatter_fields(self):
        rows = [
            row for row in self.matrix.build_rows()
            if row["classification"] == "packaged-direct"
        ]
        for row in rows:
            with self.subTest(name=row["name"]):
                text = (PACKAGES / row["package_candidate"] / "skills" / row["name"] / "SKILL.md").read_text(encoding="utf-8")
                self.assertNotIn("argument-hint:", text)
                self.assertNotIn("user-invocable:", text)
                self.assertNotIn("version:", text)

    def test_marketplace_contains_all_direct_packages(self):
        direct_packages = {
            row["package_candidate"]
            for row in self.matrix.build_rows()
            if row["classification"] == "packaged-direct"
        }
        marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
        entries = {entry["name"]: entry for entry in marketplace["plugins"]}
        self.assertTrue(direct_packages <= set(entries))
        for package_name in direct_packages:
            with self.subTest(package=package_name):
                self.assertEqual(f"./plugins/{package_name}", entries[package_name]["source"]["path"])
                self.assertEqual("AVAILABLE", entries[package_name]["policy"]["installation"])
                self.assertEqual("ON_INSTALL", entries[package_name]["policy"]["authentication"])


if __name__ == "__main__":
    unittest.main()
