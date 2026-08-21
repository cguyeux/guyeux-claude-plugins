"""Minimal reproducibility tests for the bactrline and pymlst wrappers."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parent

BACTRLINE_COMMIT = "b87e2b19198629f453a8c05607b18ae7aa8a80fb"
PYMLST_COMMIT = "389679b18dad9f92c3f212b98fb6d9878f95bb5a"


class WrapperContractTests(unittest.TestCase):
    def test_manifest_and_marketplace_contract(self) -> None:
        manifest = json.loads(
            (PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text()
        )
        marketplace = json.loads(
            (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text()
        )
        entries = [
            plugin
            for plugin in marketplace["plugins"]
            if plugin["name"] == "bio_bacteria"
        ]

        self.assertEqual(manifest["name"], "bio_bacteria")
        self.assertEqual(manifest["version"], "1.0.0")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source"], "./bio_bacteria")

    def test_bactrline_is_pinned_and_uses_official_dry_run(self) -> None:
        skill = (PLUGIN_ROOT / "skills" / "bactrline" / "SKILL.md").read_text()
        provenance = (
            PLUGIN_ROOT / "skills" / "bactrline" / "PROVENANCE.md"
        ).read_text()

        self.assertIn(BACTRLINE_COMMIT, skill)
        self.assertIn(BACTRLINE_COMMIT, provenance)
        self.assertIn("https://github.com/bvalot/bactrline", provenance)
        self.assertIn("GPL-3.0-only", provenance)
        self.assertIn("--snakefile workflow/Snakefile", skill)
        self.assertIn("--configfile config/config.yml", skill)
        self.assertIn("--dry-run", skill)

    def test_pymlst_is_pinned_and_uses_current_entry_points(self) -> None:
        skill = (PLUGIN_ROOT / "skills" / "pymlst" / "SKILL.md").read_text()
        provenance = (
            PLUGIN_ROOT / "skills" / "pymlst" / "PROVENANCE.md"
        ).read_text()

        self.assertIn(PYMLST_COMMIT, skill)
        self.assertIn(PYMLST_COMMIT, provenance)
        self.assertIn("https://github.com/bvalot/pyMLST", provenance)
        self.assertIn("GPL-3.0-or-later", provenance)
        self.assertIn("wgMLST create", skill)
        self.assertIn("claMLST", skill)
        self.assertIn("pyTyper", skill)
        self.assertNotIn("pymlst wg", skill.lower())

    def test_bio_redac_links_resolve_to_the_canonical_wrappers(self) -> None:
        for name in ("bactrline", "pymlst"):
            canonical = PLUGIN_ROOT / "skills" / name
            link = REPO_ROOT / "bio_redac" / "skills" / name
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.resolve(strict=True), canonical.resolve(strict=True))


class PymlstSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.wgmlst = shutil.which("wgMLST")

    def run_wgmlst(self, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        if self.wgmlst is None:
            self.skipTest("wgMLST is not installed")
        return subprocess.run(
            [self.wgmlst, *args],
            cwd=cwd,
            check=True,
            text=True,
            capture_output=True,
        )

    @staticmethod
    def write_toy_inputs(root: Path) -> tuple[Path, Path, Path]:
        gene_a = "ATG" + "GCTGAACCGTTC" * 10 + "TAA"
        gene_b = "ATG" + "AACGGTCTGCAA" * 10 + "TGA"
        gene_b_variant = gene_b[:45] + "GAT" + gene_b[48:]
        scheme = root / "scheme.fasta"
        genome_a = root / "toy-a.fasta"
        genome_b = root / "toy-b.fasta"

        scheme.write_text(f">geneA\n{gene_a}\n>geneB\n{gene_b}\n")
        genome_a.write_text(f">toy-a\nTTTT{gene_a}{'N' * 40}{gene_b}AAAA\n")
        genome_b.write_text(
            f">toy-b\nTTTT{gene_a}{'N' * 40}{gene_b_variant}AAAA\n"
        )
        return scheme, genome_a, genome_b

    def test_create_and_inspect_toy_database(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pymlst-wrapper-") as tmp:
            root = Path(tmp)
            scheme, _, _ = self.write_toy_inputs(root)
            database = root / "toy.db"

            self.run_wgmlst(
                "create",
                "--species",
                "Toy bacterium",
                "--version",
                "toy-v1",
                str(database),
                str(scheme),
                cwd=root,
            )
            stats = self.run_wgmlst("stats", str(database), cwd=root)

            self.assertIn("species\tToy bacterium", stats.stdout)
            self.assertIn("Coregenes\t2", stats.stdout)

    @unittest.skipUnless(shutil.which("blat"), "BLAT is required for assemblies")
    def test_add_two_toy_assemblies(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pymlst-wrapper-") as tmp:
            root = Path(tmp)
            scheme, genome_a, genome_b = self.write_toy_inputs(root)
            database = root / "toy.db"

            self.run_wgmlst("create", str(database), str(scheme), cwd=root)
            self.run_wgmlst(
                "add", "--strain", "toy-a", str(database), str(genome_a), cwd=root
            )
            self.run_wgmlst(
                "add", "--strain", "toy-b", str(database), str(genome_b), cwd=root
            )
            distance = self.run_wgmlst("distance", str(database), cwd=root)

            self.assertIn("toy-a", distance.stdout)
            self.assertIn("toy-b", distance.stdout)


if __name__ == "__main__":
    unittest.main()
