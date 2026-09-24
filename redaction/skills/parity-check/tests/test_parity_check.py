#!/usr/bin/env python3
"""Tests de `parity_check.py` (piste Y2, environnement, 2026-09-22).

Cas fondateur reproduit : `lineage_subdivision_methods`, porte 3bis du
2026-09-19, un correctif applique a `main_fr.tex` seul laissait dans
`main.tex` un chiffre non defini par la version anglaise. `test_number_only_in_fr_is_flagged`
et `test_number_only_in_en_is_flagged` couvrent les deux sens de ce defaut.
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "parity_check.py"

PREAMBLE_EN = "\\documentclass{article}\n\\begin{document}\n"
PREAMBLE_FR = "\\documentclass{article}\n\\usepackage[french]{babel}\n\\begin{document}\n"
FOOTER = "\n\\end{document}\n"


def _run(en: Path, fr: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(en), str(fr), *extra],
        capture_output=True, text=True,
    )


def _write_pair(tmp_path, en_body: str, fr_body: str) -> tuple[Path, Path]:
    en = tmp_path / "main.tex"
    fr = tmp_path / "main_fr.tex"
    en.write_text(PREAMBLE_EN + en_body + FOOTER, encoding="utf-8")
    fr.write_text(PREAMBLE_FR + fr_body + FOOTER, encoding="utf-8")
    return en, fr


def test_identical_sections_are_ok(tmp_path):
    body_en = "\\section{Results}\\label{sec:results}\nWe obtained an accuracy of 96.91 percent.\n"
    body_fr = "\\section{Resultats}\\label{sec:results}\nNous avons obtenu une precision de 96,91 pourcent.\n"
    en, fr = _write_pair(tmp_path, body_en, body_fr)

    res = _run(en, fr)

    assert res.returncode == 0, res.stdout
    assert "PARITE OK" in res.stdout


def test_number_only_in_fr_is_flagged(tmp_path):
    """Cas fondateur, sens direct : la FR porte un correctif (96,91) que l'EN n'a jamais recu."""
    body_en = "\\section{Results}\\label{sec:results}\nWe obtained an accuracy of 95.00 percent.\n"
    body_fr = "\\section{Resultats}\\label{sec:results}\nNous avons obtenu une precision de 96,91 pourcent.\n"
    en, fr = _write_pair(tmp_path, body_en, body_fr)

    res = _run(en, fr)

    assert res.returncode == 1, res.stdout
    assert "DIVERGENCES DETECTEES" in res.stdout
    assert "96.91" in res.stdout or "96.91" in res.stdout.replace(",", ".")


def test_number_only_in_en_is_flagged(tmp_path):
    """Cas fondateur, sens inverse : un chiffre existe en EN, jamais reporte en FR."""
    body_en = "\\section{Results}\\label{sec:results}\nWe obtained an accuracy of 96.91 percent.\n"
    body_fr = "\\section{Resultats}\\label{sec:results}\nNous avons obtenu une precision de 95,00 pourcent.\n"
    en, fr = _write_pair(tmp_path, body_en, body_fr)

    res = _run(en, fr, "--json")

    assert res.returncode == 1, res.stdout
    data = json.loads(res.stdout)
    assert data["status"] == "MISMATCH"
    pair = data["pairs"][0]
    assert "96.91" in {str(k) for k in pair["numbers_only_en"]}


def test_citation_only_on_one_side_is_flagged(tmp_path):
    body_en = "\\section{Intro}\\label{sec:intro}\nAs shown by \\cite{smith2020,doe2019}.\n"
    body_fr = "\\section{Introduction}\\label{sec:intro}\nComme montre par \\cite{smith2020}.\n"
    en, fr = _write_pair(tmp_path, body_en, body_fr)

    res = _run(en, fr)

    assert res.returncode == 1, res.stdout
    assert "doe2019" in res.stdout


def test_missing_section_is_structural_mismatch(tmp_path):
    body_en = ("\\section{Results}\\label{sec:results}\nText.\n"
               "\\section{Discussion}\\label{sec:discussion}\nText.\n")
    body_fr = "\\section{Resultats}\\label{sec:results}\nTexte.\n"
    en, fr = _write_pair(tmp_path, body_en, body_fr)

    res = _run(en, fr)

    assert res.returncode == 1, res.stdout
    assert "STRUCTURE" in res.stdout
    assert "Discussion" in res.stdout


def test_input_files_are_resolved(tmp_path):
    (tmp_path / "results_en.tex").write_text(
        "\\section{Results}\\label{sec:results}\nAccuracy 96.91 percent.\n", encoding="utf-8")
    (tmp_path / "results_fr.tex").write_text(
        "\\section{Resultats}\\label{sec:results}\nPrecision 95,00 pourcent.\n", encoding="utf-8")
    en = tmp_path / "main.tex"
    fr = tmp_path / "main_fr.tex"
    en.write_text(PREAMBLE_EN + "\\input{results_en}" + FOOTER, encoding="utf-8")
    fr.write_text(PREAMBLE_FR + "\\input{results_fr}" + FOOTER, encoding="utf-8")

    res = _run(en, fr)

    assert res.returncode == 1, res.stdout
    assert "96.91" in res.stdout
