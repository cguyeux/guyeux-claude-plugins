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

MTBC=/home/christophe/docs/environnement/plugins/mtbc/skills
STRUCT=/home/christophe/docs/environnement/plugins/structure/skills
BIOINFO=/home/christophe/docs/environnement/plugins/bioinfo/skills

export PYTHONPATH="$MTBC/mtbc-gene-network/src:$MTBC/mtbc-gene/src:$STRUCT/esm-atlas-cli/src:$BIOINFO/string-db/src"
exec python3 -m mtbc_gene_network "$@"
