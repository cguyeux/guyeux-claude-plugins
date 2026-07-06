#!/usr/bin/env bash
# Turnkey ESM-1v LLR (Meier et al. 2021) launcher.
#
# Wires the 3-skill PYTHONPATH (mtbc-mutation-impact + mtbc-gene-function +
# esm-atlas-cli) and the dedicated torch+fair-esm venv, so projects NEVER need to
# recreate an ad-hoc /tmp venv for variant-effect scoring.
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
set -euo pipefail

BP=/home/christophe/docs/codes/claude_plugins/bio_pathogens/skills
BPG=/home/christophe/docs/codes/claude_plugins/bio_population_genetics/skills
VENV=/home/christophe/venvs/esm1v/bin/python

export PYTHONPATH="$BP/mtbc-mutation-impact/src:$BP/mtbc-gene-function/src:$BPG/esm-atlas-cli/src"

if [[ "${1:-}" == "--smoke" ]]; then
    exec "$VENV" -m mtbc_mutation_impact.smoke_test
fi
exec "$VENV" -m mtbc_mutation_impact.llr "$@"
