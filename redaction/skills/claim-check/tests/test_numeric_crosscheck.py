#!/usr/bin/env python3
"""Tests de `numeric_crosscheck.py`, en particulier l'entree synthetique `__n_rows__`.

Piste Y1 (environnement, 2026-09-22) : la porte 3bis de `lineage_subdivision_methods`
(2026-09-18/19) a laisse passer un manuscrit citant « 5 temoins » alors que le `.tsv`
regenere en portait 9 -- chaque cellule du tableau etait juste, seul le COMPTE avait
derive. Le mode declaratif d'origine ne comparait que des CELLULES (`fichier:colonne
[rowN]`) : un claim de comptage n'avait aucun chemin de donnees a designer. `__n_rows__`
comble ce trou. Ces tests reproduisent le cas temoin et verifient qu'il est desormais
signale au lieu d'etre valide.
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "numeric_crosscheck.py"


def _write_witnesses_tsv(path: Path, n: int) -> None:
    lines = ["id\tlocus\tstatus"]
    lines += [f"w{i}\tRv{i:04d}\tconfirme" for i in range(1, n + 1)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_assert(tex: Path, data: Path, claims: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(tex), "--data", str(data),
         "--assert-file", str(claims)],
        capture_output=True, text=True,
    )


def test_row_count_mismatch_is_flagged(tmp_path):
    """Cas temoin exact de la porte 3bis : 5 declares, 9 reels -> ECART, exit 1."""
    tsv = tmp_path / "witnesses.tsv"
    _write_witnesses_tsv(tsv, 9)
    tex = tmp_path / "main.tex"
    tex.write_text("\\begin{document}\nLe tableau comporte 5 temoins valides.\n\\end{document}\n")
    claims = tmp_path / "claims.json"
    claims.write_text(json.dumps({"claims": [
        {"label": "n_temoins", "tex": 5, "path": "witnesses.tsv:__n_rows__"},
    ]}))

    res = _run_assert(tex, tsv, claims)

    assert res.returncode == 1, res.stdout
    assert "ECART" in res.stdout
    assert "n_temoins" in res.stdout


def test_row_count_match_is_not_flagged(tmp_path):
    """Le meme mecanisme ne doit pas crier quand le compte concorde (pas de faux positif)."""
    tsv = tmp_path / "witnesses.tsv"
    _write_witnesses_tsv(tsv, 5)
    tex = tmp_path / "main.tex"
    tex.write_text("\\begin{document}\nLe tableau comporte 5 temoins valides.\n\\end{document}\n")
    claims = tmp_path / "claims.json"
    claims.write_text(json.dumps({"claims": [
        {"label": "n_temoins", "tex": 5, "path": "witnesses.tsv:__n_rows__"},
    ]}))

    res = _run_assert(tex, tsv, claims)

    assert res.returncode == 0, res.stdout
    assert "TOUS LES CHIFFRES CONCORDENT" in res.stdout


def test_json_list_row_count(tmp_path):
    """Meme mecanisme pour une liste JSON de records (pas seulement CSV/TSV)."""
    data = tmp_path / "witnesses.json"
    data.write_text(json.dumps([{"id": f"w{i}"} for i in range(1, 10)]))
    tex = tmp_path / "main.tex"
    tex.write_text("\\begin{document}\nLe jeu comporte 5 genomes temoins.\n\\end{document}\n")
    claims = tmp_path / "claims.json"
    claims.write_text(json.dumps({"claims": [
        {"label": "n_genomes", "tex": 5, "path": "witnesses.json:__n_rows__"},
    ]}))

    res = _run_assert(tex, data, claims)

    assert res.returncode == 1, res.stdout
    assert "ECART" in res.stdout


def test_existing_cell_matching_unaffected(tmp_path):
    """Non-regression : le mode cellule-a-cellule pre-existant continue de fonctionner
    a cote de la nouvelle entree __n_rows__ (les deux coexistent dans le meme LUT)."""
    tsv = tmp_path / "results.tsv"
    tsv.write_text("value\n0.924\n0.881\n0.803\n", encoding="utf-8")
    tex = tmp_path / "main.tex"
    tex.write_text("\\begin{document}\nLe taux de validation croisee etait de 0.924.\n\\end{document}\n")
    claims = tmp_path / "claims.json"
    claims.write_text(json.dumps({"claims": [
        {"label": "taux_cv", "tex": 0.924, "path": "results.tsv:value[row0]"},
    ]}))

    res = _run_assert(tex, tsv, claims)

    assert res.returncode == 0, res.stdout
    assert "TOUS LES CHIFFRES CONCORDENT" in res.stdout
