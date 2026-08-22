from pathlib import Path


def test_notes_canonical_carries_norm_and_provenance():
    root = Path("droit/skills/notes-et-citations")
    skill = (root / "SKILL.md").read_text()
    norm = (root / "references/norme-aynes.md").read_text()
    provenance = (root / "PROVENANCE.md").read_text()
    assert "references/norme-aynes.md" in skill
    assert "Camille Ayn" in norm
    assert "Garde-fou" in provenance
    assert "feuille de style" in provenance
