from pathlib import Path


def test_data_access_canonicals_have_provenance():
    for rel in (
        "bio_pathogens/skills/crisprbuilder/PROVENANCE.md",
        "bio_pathogens/skills/crisprcasdb/PROVENANCE.md",
        "bio_pathogens/skills/miru-vntr/PROVENANCE.md",
        "redac/skills/literature-access/PROVENANCE.md",
    ):
        text = Path(rel).read_text()
        assert "Provenance" in text
        assert "Garde-fou" in text


def test_crisprbuilder_catalogue_is_present_and_tsv_shaped():
    path = Path("bio_pathogens/skills/crisprbuilder/data/dr_genres_ev4.tsv")
    header = path.read_text().splitlines()[0]
    assert header == "dr\tn_loci\tn_genres\tgenres"


def test_literature_access_declares_no_paywall_bypass():
    text = Path("redac/skills/literature-access/SKILL.md").read_text()
    assert "ne contourne AUCUN paywall" in text
    assert "Sci-Hub" in text
