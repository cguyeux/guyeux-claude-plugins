import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "_audit" / "codex_runtime_adaptation_matrix.json"


class CodexRuntimeAdaptationMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(
            [sys.executable, "_audit/tools/generate_codex_runtime_adaptation_matrix.py"],
            cwd=ROOT,
            check=True,
        )
        cls.payload = json.loads(MATRIX.read_text(encoding="utf-8"))
        cls.rows = cls.payload["rows"]

    def test_all_coarse_runtime_rows_are_classified(self):
        self.assertEqual(len(self.rows), 61)
        self.assertEqual(sum(self.payload["summary"]["runtime_bucket"].values()), 61)

    def test_expected_runtime_buckets_are_stable(self):
        self.assertEqual(
            self.payload["summary"]["runtime_bucket"],
            {
                "await-canonical-knowledge-path": 1,
                "claude-branding-only": 1,
                "codex-mcp-documentation-only": 24,
                "codex-mcp-tool-prerequisite": 12,
                "mcp-narrative-only": 11,
                "rewrite-cache-path": 1,
                "rewrite-claude-skill-paths": 10,
                "unclassified-runtime-signal": 1,
            },
        )

    def test_high_risk_runtime_cases_are_named(self):
        by_name = {row["name"]: row["runtime_bucket"] for row in self.rows}
        self.assertNotIn("clinical-trial-protocol-skill", by_name)
        self.assertEqual(by_name["sra-geolocate"], "rewrite-cache-path")
        self.assertEqual(by_name["boltz"], "await-canonical-knowledge-path")
        self.assertEqual(by_name["imdb"], "rewrite-claude-skill-paths")
        self.assertEqual(by_name["hgt-direction-check"], "unclassified-runtime-signal")

    def test_generated_files_are_current(self):
        result = subprocess.run(
            [sys.executable, "_audit/tools/generate_codex_runtime_adaptation_matrix.py", "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
