#!/usr/bin/env bash
# Turnkey ESM-1v LLR (Meier et al. 2021) launcher.
#
# Wires the PYTHONPATH (this skill's own src/, which holds mtbc_mutation_impact and
# mtbc_gene_function, plus esm-atlas-cli) and the dedicated torch+fair-esm venv, so
# projects NEVER need to recreate an ad-hoc /tmp venv for variant-effect scoring.
#
# One-time venv setup (already done once; recreate if missing):
#   python3 -m venv --system-site-packages /home/christophe/venvs/esm1v
#   /home/christophe/venvs/esm1v/bin/pip install --no-deps fair-esm
#   (inherits the system torch; the ~2.6 GB ESM-1v weights download on first score)
#
# Usage:
#   ./run_llr.sh katG S315T
#   ./run_llr.sh eccE1 G346A
#   ./run_llr.sh --smoke            # torch-free self-check (no weight download)
#   ./run_llr.sh --protein-fasta mbovis_mmpL6.faa mmpL6_Mbovis N551K
#     (residue absent from H37Rv -- inside a region of difference such as TbD1 --
#     score against the full-length protein of a strain with the intact locus)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STRUCT=/home/christophe/docs/environnement/plugins/structure/skills
VENV=/home/christophe/venvs/esm1v/bin/python

export PYTHONPATH="$HERE/src:$STRUCT/esm-atlas-cli/src"

if [[ "${1:-}" == "--smoke" ]]; then
    exec "$VENV" -m mtbc_mutation_impact.smoke_test
fi
exec "$VENV" -m mtbc_mutation_impact.llr "$@"
