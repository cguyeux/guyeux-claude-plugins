import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_audit" / "tools" / "audit_codex_skill_farm.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("audit_codex_skill_farm", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CodexSkillFarmAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load_tool()

    def test_repository_audit_is_closed(self):
        summary, problems = self.audit.audit_repository(ROOT)
        self.assertEqual([], problems)
        self.assertEqual(190, summary["canonicals"])
        self.assertEqual(53, summary["direct_exports"])
        self.assertEqual(137, summary["packaged_skills"])
        self.assertEqual(137, summary["matrix_rows"])
        self.assertEqual(10, summary["plugins"])
        self.assertEqual(
            [
                "packaged-direct",
                "packaged-payload",
                "packaged-pilot",
                "packaged-runtime-adapted",
                "packaged-workflow-guarded",
            ],
            summary["classifications"],
        )

    def test_direct_export_audit_detects_missing_and_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            summary, problems = self.audit.audit_codex_exports(target, ROOT)
            self.assertEqual(0, summary["current"])
            self.assertEqual(53, summary["missing"])
            self.assertEqual(0, summary["conflicts"])
            self.assertEqual(53, len(problems))

            desired = next(iter(self.audit.direct_exports(ROOT)))
            (target / desired).write_text("not a symlink", encoding="utf-8")
            summary, problems = self.audit.audit_codex_exports(target, ROOT)
            self.assertEqual(52, summary["missing"])
            self.assertEqual(1, summary["conflicts"])
            self.assertTrue(any("export divergent" in problem for problem in problems))

    def test_profile_audit_accepts_materialized_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp)
            cache = profile / "plugins" / "cache" / "personal"
            for plugin, skills in self.audit.package_skill_dirs(ROOT / "codex_packages" / "plugins").items():
                manifest = json.loads(
                    (ROOT / "codex_packages" / "plugins" / plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
                )
                for skill in skills:
                    target = cache / plugin / manifest["version"] / "skills" / skill.name
                    target.mkdir(parents=True)
                    (target / "SKILL.md").write_text((skill / "SKILL.md").read_text(encoding="utf-8"), encoding="utf-8")
            config_lines = [
                "[marketplaces.personal]",
                'source_type = "local"',
                f'source = "{ROOT / "codex_packages"}"',
                "",
            ]
            for plugin in sorted(self.audit.EXPECTED_PLUGINS):
                config_lines.extend([
                    f'[plugins."{plugin}@personal"]',
                    "enabled = true",
                    "",
                ])
            (profile / "config.toml").write_text("\n".join(config_lines), encoding="utf-8")

            summary, problems = self.audit.audit_profile(profile)
            self.assertEqual([], problems)
            self.assertEqual(10, summary["enabled_plugins"])
            self.assertEqual(137, summary["installed_skills"])

    def test_profile_audit_rejects_forbidden_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp)
            skill = profile / "plugins" / "cache" / "personal" / "bad" / "0.1.0" / "skills" / "bad"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: bad\nargument-hint: x\n---\n", encoding="utf-8")
            (profile / "config.toml").write_text("[marketplaces.personal]\nsource = \"wrong\"\n", encoding="utf-8")
            _summary, problems = self.audit.audit_profile(profile)
            self.assertTrue(any("champ interdit argument-hint" in problem for problem in problems))

    def test_agent_farm_delta_is_whitelisted(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            claude = base / ".claude" / "skills"
            agents = base / ".agents" / "skills"
            delta_root = base / "repo"
            (delta_root / "_audit").mkdir(parents=True)
            expected_claude_only = ["challenge", "etat"]
            (delta_root / "_audit" / "agent_farm_expected_delta.json").write_text(
                json.dumps(
                    {
                        "common_divergent_expected": [],
                        "claude_only_expected": expected_claude_only,
                        "agents_only_expected": [],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            for name in ["common", *expected_claude_only]:
                skill = claude / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(f"---\nname: {name}\ndescription: x\n---\n", encoding="utf-8")
            common = agents / "common"
            common.mkdir(parents=True)
            (common / "SKILL.md").write_text("---\nname: common\ndescription: x\n---\n", encoding="utf-8")

            summary, problems = self.audit.audit_agent_farms(claude, agents, delta_root)
            self.assertEqual([], problems)
            self.assertEqual(1, summary["common"])
            self.assertEqual(expected_claude_only, summary["claude_only"])
            self.assertEqual([], summary["common_divergent"])

            extra = agents / "unexpected"
            extra.mkdir()
            (extra / "SKILL.md").write_text("---\nname: unexpected\ndescription: x\n---\n", encoding="utf-8")
            _summary, problems = self.audit.audit_agent_farms(claude, agents, delta_root)
            self.assertTrue(any("Agents-only inattendu" in problem for problem in problems))


if __name__ == "__main__":
    unittest.main()
