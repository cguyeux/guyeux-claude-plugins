from pathlib import Path


def test_multimedia_canonicals_have_provenance():
    for skill in ("cinema_info", "film_documentaire"):
        provenance = Path("multimedia/skills") / skill / "PROVENANCE.md"
        text = provenance.read_text()
        assert "Provenance" in text
        assert "Garde-fou" in text


def test_scrapers_never_install_dependencies_implicitly():
    scripts = (
        Path("multimedia/skills/cinema_info/scripts/cinema_search.py"),
        Path("multimedia/skills/film_documentaire/scripts/film_doc_lookup.py"),
    )
    for script in scripts:
        text = script.read_text()
        assert "subprocess.check_call" not in text
        assert "pip\", \"install" not in text


def test_english_wikipedia_api_endpoint_is_valid():
    source = Path("multimedia/skills/cinema_info/scripts/cinema_search.py").read_text()
    assert "https://en.wikipedia.org/w/api.php" in source
    assert "https://en.wikipedia.org/wiki/w/api.php" not in source
