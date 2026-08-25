# Audit des paquets runtime Codex

Ce fichier est genere par `_audit/tools/materialize_codex_runtime_packages.py`.
Il couvre les familles runtime materialisees avec une note Codex et sans environnements locaux.

| skill | paquet | famille | fichiers copies | fichiers exclus | racines exclues |
|---|---|---|---:|---:|---|
| enterobase | bio-bacteria | codex-mcp-documentation-only | 1 | 0 | none |
| helicobacter-pylori-phylogeography | bio-bacteria | codex-mcp-documentation-only | 1 | 0 | none |
| mycobacterium-leprae | bio-bacteria | codex-mcp-documentation-only | 1 | 0 | none |
| ncbi-pathogen-detection | bio-bacteria | codex-mcp-documentation-only | 1 | 0 | none |
| pymlst | bio-bacteria | mcp-narrative-only | 2 | 0 | none |
| active-site-check | bio-pathogens | rewrite-claude-skill-paths | 4 | 0 | none |
| ancestral-reconstruction | bio-pathogens | codex-mcp-tool-prerequisite | 2 | 2 | __pycache__ |
| bacdive | bio-pathogens | codex-mcp-documentation-only | 1 | 0 | none |
| coevolution | bio-pathogens | codex-mcp-tool-prerequisite | 3 | 4 | __pycache__ |
| convergent-evolution | bio-pathogens | codex-mcp-tool-prerequisite | 2 | 2 | __pycache__ |
| lineage-comparison | bio-pathogens | codex-mcp-tool-prerequisite | 2 | 0 | none |
| lineage-subdivision | bio-pathogens | rewrite-claude-skill-paths | 4 | 0 | none |
| mk-ascertainment | bio-pathogens | rewrite-claude-skill-paths | 3 | 4 | __pycache__ |
| mtbc-epistasis | bio-pathogens | rewrite-claude-skill-paths | 2 | 1 | __pycache__ |
| mtbc-gene | bio-pathogens | rewrite-claude-skill-paths | 22 | 0 | none |
| mtbc-lineages | bio-pathogens | rewrite-claude-skill-paths | 15 | 6 | __pycache__ |
| pangenome-enrichment | bio-pathogens | codex-mcp-tool-prerequisite | 2 | 2 | __pycache__ |
| pathogens-portal | bio-pathogens | codex-mcp-documentation-only | 1 | 0 | none |
| phylogeography | bio-pathogens | codex-mcp-tool-prerequisite | 2 | 2 | __pycache__ |
| resistance-catalogue | bio-pathogens | codex-mcp-tool-prerequisite | 7 | 9 | __pycache__ |
| resistance-profiler | bio-pathogens | codex-mcp-tool-prerequisite | 2 | 0 | none |
| snp-distance | bio-pathogens | codex-mcp-tool-prerequisite | 2 | 0 | none |
| spaam-ancient-metagenome-dir | bio-pathogens | codex-mcp-documentation-only | 1 | 0 | none |
| spaam-community | bio-pathogens | codex-mcp-documentation-only | 1 | 0 | none |
| spdi-annotation | bio-pathogens | codex-mcp-tool-prerequisite | 2 | 2 | __pycache__ |
| species-id | bio-pathogens | mcp-narrative-only | 1 | 0 | none |
| sra-geolocate | bio-pathogens | rewrite-cache-path | 1 | 0 | none |
| tbannotator-mcp | bio-pathogens | codex-mcp-tool-prerequisite | 3 | 0 | none |
| thd | bio-pathogens | rewrite-claude-skill-paths | 2 | 2 | __pycache__ |
| tsne-hdbscan | bio-pathogens | codex-mcp-tool-prerequisite | 2 | 2 | __pycache__ |
| aadr | bio-population-genetics | codex-mcp-documentation-only | 10 | 14 | __pycache__ |
| amtdb | bio-population-genetics | codex-mcp-documentation-only | 10 | 14 | __pycache__ |
| bayesian-skyline | bio-population-genetics | codex-mcp-documentation-only | 1 | 0 | none |
| beast2-phylogeography | bio-population-genetics | codex-mcp-documentation-only | 1 | 0 | none |
| bioc-pmc | bio-population-genetics | codex-mcp-documentation-only | 1 | 0 | none |
| card | bio-population-genetics | codex-mcp-documentation-only | 1 | 0 | none |
| clinical-trial-protocol-skill | bio-population-genetics | external-mcp-fallback-documented | 11 | 2 | __pycache__ |
| d-place | bio-population-genetics | codex-mcp-documentation-only | 10 | 14 | __pycache__ |
| europe-pmc | bio-population-genetics | rewrite-claude-skill-paths | 1 | 0 | none |
| nextflow-development | bio-population-genetics | claude-branding-only | 22 | 20 | __pycache__ |
| nextstrain | bio-population-genetics | codex-mcp-documentation-only | 1 | 0 | none |
| openalex | bio-population-genetics | codex-mcp-documentation-only | 1 | 0 | none |
| orbis | bio-population-genetics | codex-mcp-documentation-only | 11 | 14 | __pycache__ |
| p3k14c | bio-population-genetics | codex-mcp-documentation-only | 10 | 14 | __pycache__ |
| pastml | bio-population-genetics | codex-mcp-documentation-only | 1 | 0 | none |
| pubmed-database | bio-population-genetics | codex-mcp-documentation-only | 4 | 0 | none |
| pubtator | bio-population-genetics | codex-mcp-documentation-only | 1 | 0 | none |
| seshat | bio-population-genetics | codex-mcp-documentation-only | 10 | 14 | __pycache__ |
| slavevoyages | bio-population-genetics | codex-mcp-documentation-only | 10 | 14 | __pycache__ |
| biolqm-convert | maboss | mcp-narrative-only | 1 | 0 | none |
| bn-control | maboss | mcp-narrative-only | 1 | 0 | none |
| boolean-attractors | maboss | mcp-narrative-only | 1 | 0 | none |
| colomoto-run | maboss | mcp-narrative-only | 1 | 0 | none |
| maboss-advanced | maboss | mcp-narrative-only | 1 | 0 | none |
| model-repositories | maboss | mcp-narrative-only | 1 | 0 | none |
| pydruglogics | maboss | mcp-narrative-only | 1 | 0 | none |
| imdb | multimedia | rewrite-claude-skill-paths | 9 | 0 | none |
