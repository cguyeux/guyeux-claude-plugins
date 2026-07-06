#!/usr/bin/env bash
# mtbc-gene-network launcher: wires the multi-skill PYTHONPATH so guilt-by-association
# (via mtbc-gene-function) and the STRING-API fallback (via string-db) work alongside
# the local interactome graph. Basic ops (neighbors/path/hubs/communities/subnetwork)
# also run standalone with just this skill's src on PYTHONPATH.
#
#   ./run_network.sh neighbors katG --top 10 --min-score 700
#   ./run_network.sh path katG rpoB
#   ./run_network.sh hubs --top 20
#   ./run_network.sh communities --min-score 700 --top 15
#   ./run_network.sh guilt Rv2239c --min-score 700
set -euo pipefail

BP=/home/christophe/docs/codes/claude_plugins/bio_pathogens/skills
BPG=/home/christophe/docs/codes/claude_plugins/bio_population_genetics/skills

export PYTHONPATH="$BP/mtbc-gene-network/src:$BP/mtbc-gene-function/src:$BPG/esm-atlas-cli/src:$BP/string-db/src"
exec python3 -m mtbc_gene_network "$@"
