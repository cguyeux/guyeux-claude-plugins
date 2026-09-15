#!/usr/bin/env bash
# mtbc-gene pathway launcher: wires the PYTHONPATH so the curated per-gene annotation
# (this skill's own src/mtbc_gene_function -> annotation_mtbc) and the PPI network
# context (mtbc-gene-network) are available. --esm additionally uses esm-atlas-cli.
#
#   ./run_pathway.sh ESX-2 --paragraph
#   ./run_pathway.sh neighbors:katG --paragraph        # narrate a gene's neighbourhood
#   ./run_pathway.sh katG,ahpC,furA,sodA,sodC --paragraph
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BP=/home/christophe/docs/codes/claude_plugins/bio_pathogens/skills
BPG=/home/christophe/docs/codes/claude_plugins/bio_population_genetics/skills

export PYTHONPATH="$HERE/src:$BP/mtbc-gene-network/src:$BPG/esm-atlas-cli/src:$BP/string-db/src"
exec python3 -m mtbc_pathway_explain "$@"
