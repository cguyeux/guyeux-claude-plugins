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
AUDIT = ROOT / "_audit" / "codex_payload_package_audit.json"


def load_module(name: str):
    path = TOOLS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module introuvable: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end == -1:
        return ""
    return text[:end]


class CodexPayloadPackagesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = load_module("generate_codex_package_matrix")

    def test_payload_candidates_are_materialized(self):
        rows = [
            row for row in self.matrix.build_rows()
            if row["classification"] == "packaged-payload"
        ]
        self.assertEqual(19, len(rows))
        for row in rows:
            with self.subTest(name=row["name"]):
                skill = PACKAGES / row["package_candidate"] / "skills" / row["name"]
                self.assertTrue((skill / "SKILL.md").is_file())
                self.assertFalse(skill.is_symlink())

    def test_payload_packages_strip_claude_frontmatter_fields(self):
        rows = [
            row for row in self.matrix.build_rows()
            if row["classification"] == "packaged-payload"
        ]
        for row in rows:
            with self.subTest(name=row["name"]):
                text = (PACKAGES / row["package_candidate"] / "skills" / row["name"] / "SKILL.md").read_text(encoding="utf-8")
                fm = frontmatter(text)
                self.assertNotIn("argument-hint:", fm)
                self.assertNotIn("disable-model-invocation:", fm)
                self.assertNotIn("user-invocable:", fm)
                self.assertNotIn("version:", fm)

    def test_text_to_speech_excludes_local_environments(self):
        skill = PACKAGES / "multimedia" / "skills" / "text-to-speech"
        self.assertTrue((skill / "SKILL.md").is_file())
        self.assertFalse((skill / ".venv").exists())
        self.assertFalse((skill / "scripts" / ".venv").exists())
        self.assertFalse((skill / "scripts" / "__pycache__").exists())

    def test_payload_audit_records_exclusions(self):
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        rows = {row["name"]: row for row in audit["rows"]}
        self.assertEqual(19, len(rows))
        self.assertGreater(rows["text-to-speech"]["audit"]["excluded_files"], 1000)
        self.assertIn(".venv", rows["text-to-speech"]["audit"]["excluded_roots"])


if __name__ == "__main__":
    unittest.main()
