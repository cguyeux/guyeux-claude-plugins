import importlib.util
import shlex
from pathlib import Path


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sra_to_add_quotes_user_selected_remote_samples_path(monkeypatch):
    module = _load(
        Path("bio_pathogens/skills/fetch-tbannotator/scripts/sra_to_add.py"),
        "sra_to_add",
    )
    hostile_path = "/tmp/samples with spaces;touch /tmp/unwanted.tsv"
    commands = []

    monkeypatch.setattr(module, "_samples_path", hostile_path)
    monkeypatch.setattr(module, "ssh", lambda command, **_kwargs: commands.append(command) or "")

    module.remote_state([])

    assert commands == [f"cat {shlex.quote(hostile_path)} 2>/dev/null || true"]
