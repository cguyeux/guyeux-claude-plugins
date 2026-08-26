from __future__ import annotations

import csv
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "redac" / "skills" / "soumission"
PACKAGE = ROOT / "codex_packages" / "plugins" / "bio-redac" / "skills" / "soumission"


@contextmanager
def trashed_tempdir():
    path = Path(tempfile.mkdtemp(prefix="soumission-test-"))
    try:
        yield path
    finally:
        subprocess.run(["gio", "trash", str(path)], capture_output=True, text=True, check=False)


class SoumissionSkillTests(unittest.TestCase):
    def run_script(self, name: str, *args: str, kb: Path) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["SOUMISSION_KB"] = str(kb)
        return subprocess.run(
            ["python3", str(SOURCE / "scripts" / name), *args],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
            check=False,
        )

    def test_source_scripts_compile_without_bytecode(self):
        for script in sorted((SOURCE / "scripts").glob("*.py")):
            with self.subTest(script=script.name):
                compile(script.read_text(encoding="utf-8"), str(script), "exec")

    def test_local_registry_round_trip_has_no_external_action(self):
        with trashed_tempdir() as tmp:
            kb = tmp / "journals"
            init = self.run_script("author_profile.py", "init", kb=kb)
            self.assertEqual(0, init.returncode, init.stderr)

            with (kb / "portals.tsv").open(encoding="utf-8", newline="") as handle:
                portals = {row["portal"]: row for row in csv.DictReader(handle, delimiter="\t")}
            self.assertEqual("no", portals["arxiv"]["orcid_sso"])

            journal = self.run_script(
                "journals.py",
                "set",
                "test-journal",
                "name=Test Journal",
                "publisher=Test Publisher",
                "domain=test",
                "free_route=yes",
                "oa_model=subscription",
                "--create",
                kb=kb,
            )
            self.assertEqual(0, journal.returncode, journal.stderr)

            added = self.run_script(
                "submissions.py",
                "add",
                "--project",
                "demo",
                "--title",
                "Local test",
                "--journal-key",
                "test-journal",
                "--status",
                "preparing",
                kb=kb,
            )
            self.assertEqual(0, added.returncode, added.stderr)
            submission_id = added.stdout.split("enregistre : ", 1)[1].split()[0]

            rejected = self.run_script(
                "submissions.py",
                "reject",
                submission_id,
                "--lesson",
                "Verifier le scope reel sur trois articles recents.",
                kb=kb,
            )
            self.assertEqual(0, rejected.returncode, rejected.stderr)
            self.assertIn("reject-desk", rejected.stdout)
            self.assertIn("Verifier le scope reel", (kb / "rejections.md").read_text(encoding="utf-8"))

    def test_codex_copy_has_runtime_adaptation_and_evals(self):
        markdown = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(PACKAGE.rglob("*.md"))
        )
        self.assertIn("agent-browser", markdown)
        self.assertIn("~/.agents/knowledge/journals", markdown)
        self.assertNotIn("tabs_context_mcp", markdown)
        self.assertNotIn("AskUserQuestion", markdown)
        self.assertNotIn("~/.claude/knowledge/journals", markdown)
        self.assertFalse(any(path.name == "__pycache__" for path in PACKAGE.rglob("*")))
        self.assertFalse(any(path.suffix == ".pyc" for path in PACKAGE.rglob("*")))

        evals = json.loads((PACKAGE / "evals" / "evals.json").read_text(encoding="utf-8"))
        self.assertEqual("soumission", evals["skill_name"])
        self.assertEqual(3, len(evals["evals"]))
        self.assertTrue(all(item.get("expectations") for item in evals["evals"]))


if __name__ == "__main__":
    unittest.main()
