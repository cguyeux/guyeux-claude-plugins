import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_audit" / "tools" / "skills_farm.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("skills_farm", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_skill(root: Path, name: str) -> Path:
    skill = root / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: test {name}\n---\n",
        encoding="utf-8",
    )
    return skill


class SkillFarmTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.farm = load_tool()

    def test_audit_detects_dead_missing_and_noncanonical_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            target = base / "farm"
            alpha = write_skill(source, "alpha")
            beta = write_skill(source, "beta")
            target.mkdir()
            (target / "alpha").symlink_to(alpha, target_is_directory=True)
            (target / "beta").mkdir()
            (target / "dead").symlink_to(base / "absent", target_is_directory=True)
            (target / "local").mkdir()

            state = self.farm.audit_farm(target, {"alpha": alpha, "beta": beta})
            self.assertEqual(["alpha"], state.canonical)
            self.assertEqual([], state.missing)
            self.assertEqual(["beta"], state.divergent)
            self.assertEqual([], state.extensions)
            self.assertEqual([], state.noncanonical)
            self.assertEqual(["local"], state.foreign)
            self.assertEqual(["dead"], state.dead)
            self.assertEqual("mixed", state.kind)

    def test_sync_dry_run_never_mutates(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "farm"
            target.mkdir()
            args = self.farm.build_parser().parse_args([
                "sync", "--farm", str(target), "--plugin", "redac", "--skill", "fig-ideation", "--dry-run"
            ])
            code = self.farm.sync(args)
            self.assertEqual(0, code)
            self.assertFalse((target / "fig-ideation").exists())
            self.assertFalse((target / "fig-ideation").is_symlink())

    def test_mixed_farm_requires_explicit_selection_for_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "farm"
            target.mkdir()
            (target / "local").mkdir()
            args = self.farm.build_parser().parse_args([
                "sync", "--farm", str(target), "--plugin", "redac", "--all-missing", "--apply"
            ])
            code = self.farm.sync(args)
            self.assertEqual(2, code)
            self.assertEqual(["local"], [path.name for path in target.iterdir()])

    def test_sync_refuses_replacement_and_creates_only_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "farm"
            target.mkdir()
            (target / "fig-ideation").mkdir()
            args = self.farm.build_parser().parse_args([
                "sync", "--farm", str(target), "--plugin", "redac", "--skill", "fig-ideation", "--apply"
            ])
            self.assertEqual(2, self.farm.sync(args))
            self.assertTrue((target / "fig-ideation").is_dir())
            self.assertFalse((target / "fig-ideation").is_symlink())

            clean = Path(tmp) / "clean"
            clean.mkdir()
            args = self.farm.build_parser().parse_args([
                "sync", "--farm", str(clean), "--plugin", "redac", "--skill", "fig-ideation", "--apply"
            ])
            self.assertEqual(0, self.farm.sync(args))
            self.assertTrue((clean / "fig-ideation").is_symlink())

    def test_source_contains_no_permanent_deletion_primitive(self):
        source = TOOL.read_text(encoding="utf-8")
        self.assertNotIn(".unlink(", source)
        self.assertNotIn("shutil.rmtree", source)
        self.assertNotIn("os.remove", source)
        self.assertNotIn("os.rmdir", source)


if __name__ == "__main__":
    unittest.main()
