"""Offline provenance and projection tests for the ntm-resources catalog."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parent
SKILL_ROOT = PLUGIN_ROOT / "skills" / "ntm-resources"
CATALOG = SKILL_ROOT / "references" / "resources.json"


class NtmResourcesContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads(CATALOG.read_text())
        cls.resources = cls.catalog["resources"]

    def test_catalog_has_three_unique_primary_resources(self) -> None:
        self.assertEqual(self.catalog["schema_version"], 1)
        self.assertEqual(self.catalog["verified_on"], "2026-08-21")
        self.assertEqual(
            {resource["slug"] for resource in self.resources},
            {"ntm-db", "mabellini", "mac-inmv-ssr"},
        )
        self.assertEqual(len(self.resources), 3)

    def test_each_resource_has_citation_access_and_rights_evidence(self) -> None:
        allowed_statuses = {"reachable", "not-reproducibly-reachable"}
        for resource in self.resources:
            with self.subTest(resource=resource["slug"]):
                self.assertTrue(resource["homepage"].startswith(("https://", "http://")))
                self.assertRegex(resource["citation"]["doi"], r"^10\.")
                self.assertIn(resource["live_check"]["status"], allowed_statuses)
                self.assertEqual(resource["live_check"]["checked_on"], "2026-08-21")
                self.assertTrue(resource["rights"]["evidence"].startswith("https://"))
                self.assertTrue(resource["rights"]["reuse_note"])

    def test_database_rights_are_not_inferred_from_article_access(self) -> None:
        resources = {resource["slug"]: resource for resource in self.resources}
        self.assertEqual(
            resources["ntm-db"]["rights"]["resource_license"], "CC-BY-3.0-CN"
        )
        for slug in ("mabellini", "mac-inmv-ssr"):
            with self.subTest(resource=slug):
                self.assertEqual(
                    resources[slug]["rights"]["resource_license_status"],
                    "not-found",
                )
                self.assertIsNone(resources[slug]["rights"]["resource_license"])

    def test_skill_points_to_the_audited_catalog(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text()
        provenance = (SKILL_ROOT / "PROVENANCE.md").read_text()

        self.assertIn("references/resources.json", skill)
        self.assertIn("Accès public ne signifie pas licence", skill)
        self.assertIn("bd0dbcb56cbe3746c4fbad08867695a4492920e315a538e0b9533dbc4cfdc19b", provenance)

    def test_bio_redac_projection_resolves_to_the_canonical_skill(self) -> None:
        link = REPO_ROOT / "bio_redac" / "skills" / "ntm-resources"
        self.assertTrue(link.is_symlink())
        self.assertEqual(link.resolve(strict=True), SKILL_ROOT.resolve(strict=True))


if __name__ == "__main__":
    unittest.main()
