import json
from pathlib import Path


def test_isfinder_uses_pinned_commit_and_no_bundled_data():
    skill = Path("bio_pathogens/skills/isfinder-offline/SKILL.md").read_text()
    assert "bedbeb5c16618eca3e16ef74adf865d6b88cafb5" in skill
    assert "Isfinder-sequences/master" not in skill
    assert not Path("bio_pathogens/skills/isfinder-offline/data").exists()


def test_pocket_detection_uses_pinned_upstreams():
    skill = Path("bio_pathogens/skills/pocket-detection/SKILL.md").read_text()
    for commit in (
        "4bb0d8447f62fee77e2c3c29f54b5fcaf5e2c066",
        "3328ca0376d3e4959545bac35e036435d582ff2e",
    ):
        assert commit in skill
    assert "git clone --depth 1 https://github.com/Discngine/fpocket.git" not in skill


def test_tbannotator_diff_reports_schema_drift():
    import importlib.util

    path = Path("bio_pathogens/skills/tbannotator-upstream/scripts/check_upstream.py")
    spec = importlib.util.spec_from_file_location("check_upstream", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pinned = json.loads(Path("bio_pathogens/skills/tbannotator-upstream/references/upstream_pinned.json").read_text())
    now = json.loads(json.dumps(pinned))
    first_interface = next(iter(now["es_schema"]["interfaces"]))
    now["es_schema"]["interfaces"][first_interface].append("__codex_test_field")
    report = module.diff(pinned, now)
    assert any("[CHAMP AJOUTE]" in line for line in report)
