#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
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


class CodexPackageMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = load_module("generate_codex_package_matrix")

    def test_matrix_covers_the_136_non_exported_skills(self):
        rows = self.matrix.build_rows()
        names = {row["name"] for row in rows}
        self.assertEqual(136, len(rows))
        self.assertEqual(136, len(names))
        self.assertIn("tbmonitor-papers", names)
        self.assertIn("mtbc-prospect", names)
        self.assertNotIn("remote-compute", names)

    def test_pilot_package_is_marked_without_hiding_the_ccx10_gap(self):
        rows = self.matrix.build_rows()
        pilot = {row["name"]: row for row in rows if row["classification"] == "packaged-pilot"}
        self.assertEqual(
            {
                "iqtree-lsd2",
                "molecular-clock",
                "mtbc-prospect",
                "raxml",
                "tbmonitor-papers",
            },
            set(pilot),
        )
        for row in pilot.values():
            self.assertEqual("guyeux-phylo-pilot", row["package_candidate"])

    def test_direct_packages_are_marked_after_materialization(self):
        rows = self.matrix.build_rows()
        direct = [row for row in rows if row["classification"] == "packaged-direct"]
        self.assertEqual(48, len(direct))
        self.assertEqual(
            {
                "bio-bacteria",
                "bio-pathogens",
                "bio-population-genetics",
                "bio-redac",
                "ia",
                "maboss",
                "ops",
                "web",
            },
            {row["package_candidate"] for row in direct},
        )

    def test_payload_packages_are_marked_after_materialization(self):
        rows = self.matrix.build_rows()
        payload = [row for row in rows if row["classification"] == "packaged-payload"]
        self.assertEqual(15, len(payload))
        self.assertEqual(
            {
                "bio-pathogens",
                "bio-population-genetics",
                "ia",
                "multimedia",
                "web",
            },
            {row["package_candidate"] for row in payload},
        )

    def test_runtime_packages_are_marked_after_materialization(self):
        rows = self.matrix.build_rows()
        runtime = [row for row in rows if row["classification"] == "packaged-runtime-adapted"]
        self.assertEqual(58, len(runtime))
        self.assertEqual(
            {
                "bio-bacteria",
                "bio-pathogens",
                "bio-population-genetics",
                "maboss",
                "multimedia",
            },
            {row["package_candidate"] for row in runtime},
        )

    def test_workflow_packages_are_marked_after_materialization(self):
        rows = self.matrix.build_rows()
        workflow = [row for row in rows if row["classification"] == "packaged-workflow-guarded"]
        self.assertEqual(10, len(workflow))
        self.assertEqual({"bio-pathogens", "bio-redac", "ops"}, {row["package_candidate"] for row in workflow})

    def test_matrix_keeps_required_verrous_visible(self):
        rows = {row["name"]: row for row in self.matrix.build_rows()}
        self.assertIn("unsupported-frontmatter", rows["tbmonitor-papers"]["signals"])
        self.assertIn("script-payload", rows["active-site-check"]["signals"])
        self.assertIn("project-memory-write", rows["mtbc-bilan"]["signals"])
        self.assertEqual("packaged-workflow-guarded", rows["mtbc-bilan"]["classification"])
        self.assertEqual("packaged-runtime-adapted", rows["active-site-check"]["classification"])
        self.assertEqual("packaged-runtime-adapted", rows["boltz"]["classification"])
        self.assertEqual("packaged-runtime-adapted", rows["clinical-trial-protocol-skill"]["classification"])


if __name__ == "__main__":
    unittest.main()
