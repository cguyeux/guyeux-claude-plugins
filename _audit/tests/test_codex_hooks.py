import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "codex_hooks"


def run_hook(script: str, payload: dict, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(HOOKS / "scripts" / script)],
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd or ROOT,
        check=False,
    )


def bash_payload(command: str) -> dict:
    return {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command}}


class CodexHooksTests(unittest.TestCase):
    def test_hooks_json_is_valid_and_uses_wrapper(self):
        payload = json.loads((HOOKS / "hooks.json").read_text(encoding="utf-8"))
        self.assertIn("hooks", payload)
        self.assertIn("PreToolUse", payload["hooks"])
        self.assertIn("SessionStart", payload["hooks"])

    def test_no_rm_blocks_rm_variants(self):
        for command in [
            "rm file.txt",
            "unlink file.txt",
            "shred file.txt",
            "find . -name '*.tmp' -delete",
            "printf '%s\\n' file.txt | xargs rm",
        ]:
            with self.subTest(command=command):
                result = run_hook("no_rm_guard.py", bash_payload(command))
                self.assertEqual(2, result.returncode)
                self.assertIn("gio trash", result.stderr)

    def test_no_rm_allows_safe_near_misses_and_git_rm(self):
        for command in [
            "git rm tracked.txt",
            "docker run --rm image",
            "rmdir empty_dir",
            "chmod 644 file",
            "grep rm notes.md",
        ]:
            with self.subTest(command=command):
                result = run_hook("no_rm_guard.py", bash_payload(command))
                self.assertEqual(0, result.returncode, result.stderr)

    def test_no_rm_ignores_heredoc_body(self):
        command = "cat <<'EOF' > notes.md\nSuppression faite par rm dans un ancien log.\nEOF\n"
        result = run_hook("no_rm_guard.py", bash_payload(command))
        self.assertEqual(0, result.returncode, result.stderr)

    def test_precompute_reminder_reads_apply_patch_paths(self):
        patch = "*** Begin Patch\n*** Add File: analyses/new_calc.py\n+print('x')\n*** End Patch\n"
        result = run_hook(
            "precompute_reminder.py",
            {"hook_event_name": "PreToolUse", "tool_name": "apply_patch", "tool_input": {"command": patch}},
        )
        self.assertEqual(0, result.returncode, result.stderr)
        data = json.loads(result.stdout)
        self.assertIn("challenge", data["hookSpecificOutput"]["additionalContext"])

    def test_precompute_reminder_is_silent_for_markdown_patch(self):
        patch = "*** Begin Patch\n*** Add File: docs/note.md\n+x\n*** End Patch\n"
        result = run_hook(
            "precompute_reminder.py",
            {"hook_event_name": "PreToolUse", "tool_name": "apply_patch", "tool_input": {"command": patch}},
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_remote_compute_reminder_triggers_only_for_local_heavy_command(self):
        local = run_hook("remote_compute_reminder.py", bash_payload("iqtree2 -s aln.fasta -B 1000"))
        self.assertEqual(0, local.returncode, local.stderr)
        self.assertIn("mp", json.loads(local.stdout)["hookSpecificOutput"]["additionalContext"])

        remote = run_hook("remote_compute_reminder.py", bash_payload("ssh mp iqtree2 -s aln.fasta"))
        self.assertEqual(0, remote.returncode, remote.stderr)
        self.assertEqual("", remote.stdout)

        probe = run_hook("remote_compute_reminder.py", bash_payload("iqtree2 --version"))
        self.assertEqual(0, probe.returncode, probe.stderr)
        self.assertEqual("", probe.stdout)

    def test_session_context_emits_project_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "cahier_de_labo.md").write_text("## 2026-08-25 Test\n", encoding="utf-8")
            (root / "etat_des_decouvertes.md").write_text(
                "**Phase :** 1/5\n\n## 1. Objectifs\nObjectif.\n\n## 2. Acquis\n\n## 8. Verdict\nVerdict.\n",
                encoding="utf-8",
            )
            (root / "pistes.md").write_text("## P1. Exemple [à faire]\n", encoding="utf-8")
            child = root / "a" / "b"
            child.mkdir(parents=True)
            result = run_hook(
                "session_context.py",
                {"hook_event_name": "SessionStart", "cwd": str(child), "source": "startup"},
                cwd=child,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        data = json.loads(result.stdout)
        self.assertIn("CONTEXTE PROJET", data["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
