from pathlib import Path
import subprocess


def test_research_canonicals_have_provenance_files():
    for skill in (
        "binary-coclustering",
        "bioproject-scout",
        "crispr-spacer-null",
        "marker-laminarity",
        "rd-detection",
    ):
        provenance = Path("bio_pathogens/skills") / skill / "PROVENANCE.md"
        text = provenance.read_text()
        assert "Provenance" in text
        assert "Garde-fou" in text


def test_no_python_caches_are_tracked_for_research_canonicals():
    tracked = subprocess.check_output(
        ["git", "ls-files", "bio_pathogens/skills"], text=True
    ).splitlines()
    for path in tracked:
        assert "__pycache__" not in path
        assert not path.endswith(".pyc")
