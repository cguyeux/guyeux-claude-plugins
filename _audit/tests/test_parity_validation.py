import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_audit" / "tools" / "validate_parity.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("validate_parity", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ParityValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parity = load_tool()

    def test_matrix_has_unique_ids_and_all_required_families(self):
        payload = json.loads((ROOT / "_audit" / "parity_scenarios.json").read_text(encoding="utf-8"))
        rows = payload["scenarios"]
        ids = [row["id"] for row in rows]
        families = {row["family"] for row in rows}
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(
            {"instructions", "project-memory", "knowledge", "memory", "skills", "plugins", "hooks", "rules", "mcp", "interface", "negative"} <= families
        )

    def test_json_extractor_supports_project_doctrine_and_skill_probes(self):
        cases = [
            '{"project_marker":"PARITY_CODEX_PROJECT_ROOT"}',
            '{"canonical_project_artifact_count":5}',
            '{"skill_name":"challenge","skill_triggered":true,"verdict":"Reformuler"}',
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertIsInstance(self.parity.extract_json_answer(text), dict)

    def test_runtime_observations_are_aggregated_only(self):
        payload = json.loads((ROOT / "_audit" / "parity_runtime_observations.json").read_text(encoding="utf-8"))
        forbidden = {"transcript", "session_id", "stdout", "stderr", "raw_output"}
        for row in payload["records"]:
            self.assertFalse(forbidden & set(row))
            self.assertIn(row["platform"], {"claude", "codex"})
            self.assertEqual("completed", row["status"])

    def test_generated_report_is_complete_with_no_failure(self):
        report = json.loads((ROOT / "_audit" / "parity_report.json").read_text(encoding="utf-8"))
        self.assertTrue(report["complete"])
        self.assertEqual(0, report["summary"]["fail"])
        self.assertEqual(0, report["summary"]["blocked"])
        self.assertEqual(0, report["summary"]["unrun"])


if __name__ == "__main__":
    unittest.main()
