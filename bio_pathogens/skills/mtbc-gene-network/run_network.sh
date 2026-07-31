#!/usr/bin/env bash
# mtbc-gene-network launcher: wires the multi-skill PYTHONPATH so guilt-by-association
# (via mtbc-gene, function mode) and the STRING-API fallback (via string-db) work alongside
# the local interactome graph. Basic ops (neighbors/path/hubs/communities/subnetwork)
# also run standalone with just this skill's src on PYTHONPATH.
#
#   ./run_network.sh --min-score 700 neighbors katG --top 10   # --min-score is global:
#   ./run_network.sh path katG rpoB
#   ./run_network.sh hubs --top 20
#   ./run_network.sh --min-score 700 communities --top 15      # it precedes the subcommand
#   ./run_network.sh --min-score 700 guilt Rv2239c
set -euo pipefail

BP=/home/christophe/docs/codes/claude_plugins/bio_pathogens/skills
BPG=/home/christophe/docs/codes/claude_plugins/bio_population_genetics/skills

export PYTHONPATH="$BP/mtbc-gene-network/src:$BP/mtbc-gene/src:$BPG/esm-atlas-cli/src:$BP/string-db/src"
exec python3 -m mtbc_gene_network "$@"
