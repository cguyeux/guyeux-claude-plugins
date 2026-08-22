import importlib.util
from pathlib import Path


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_private_infra_canonicals_have_provenance_and_no_embedded_credentials():
    roots = (
        Path("bio_bacteria/skills/panisa"),
        Path("bio_population_genetics/skills/remote-compute"),
        Path("bio_pathogens/skills/tbannotator-es"),
    )
    forbidden = ("BEGIN OPENSSH PRIVATE KEY", "BEGIN RSA PRIVATE KEY")
    for root in roots:
        provenance = (root / "PROVENANCE.md").read_text()
        assert "Provenance" in provenance
        assert "Garde-fou" in provenance
        for path in root.rglob("*"):
            if path.is_file():
                text = path.read_text(errors="replace")
                assert all(marker not in text for marker in forbidden)


def test_remote_compute_recommendation_is_available_offline():
    module = _load(
        Path("bio_population_genetics/skills/remote-compute/scripts/remote_probe.py"),
        "remote_probe",
    )
    mp = {"reachable": True, "ram_free_gb": 100, "pipeline_running": False, "load": "0 0 0"}
    mh = {"reachable": True, "nodes": []}
    recommendation = module.recommend({"gpu": True}, mp, mh)
    assert any("mh" in line for line in recommendation)
    assert any("AUCUN GPU" in line for line in recommendation)


def test_tbannotator_client_keeps_credentials_external(monkeypatch, tmp_path):
    module = _load(
        Path("bio_pathogens/skills/tbannotator-es/scripts/tbannotator_es_mcp.py"),
        "tbannotator_es_mcp",
    )
    module.CONFIG_FILE = tmp_path / "missing.env"
    for key in tuple(module.os.environ):
        if key.startswith("TBANNOTATOR_ES_"):
            monkeypatch.delenv(key, raising=False)
    assert module._load_config() == {}
