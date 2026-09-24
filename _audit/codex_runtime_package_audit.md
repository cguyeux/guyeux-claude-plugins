# Audit des paquets runtime Codex

Ce fichier est genere par `_audit/tools/materialize_codex_runtime_packages.py`.
Il couvre les familles runtime materialisees avec une note Codex et sans environnements locaux.

| skill | paquet | famille | fichiers copies | fichiers exclus | racines exclues |
|---|---|---|---:|---:|---|
| bacdive | bacteria | codex-mcp-documentation-only | 1 | 0 | none |
| enterobase | bacteria | codex-mcp-documentation-only | 1 | 0 | none |
| helicobacter-pylori-phylogeography | bacteria | codex-mcp-documentation-only | 1 | 0 | none |
| mycobacterium-leprae | bacteria | codex-mcp-documentation-only | 1 | 0 | none |
| ncbi-pathogen-detection | bacteria | codex-mcp-documentation-only | 1 | 0 | none |
| pathogens-portal | bacteria | codex-mcp-documentation-only | 1 | 0 | none |
| pymlst | bacteria | mcp-narrative-only | 2 | 0 | none |
| species-id | bacteria | mcp-narrative-only | 1 | 0 | none |
| thd | bacteria | rewrite-claude-skill-paths | 2 | 0 | none |
| nextflow-development | bioinfo | claude-branding-only | 22 | 0 | none |
| bioc-pmc | litterature | codex-mcp-documentation-only | 1 | 0 | none |
| europe-pmc | litterature | rewrite-claude-skill-paths | 1 | 0 | none |
| openalex | litterature | codex-mcp-documentation-only | 1 | 0 | none |
| pubmed-database | litterature | codex-mcp-documentation-only | 4 | 0 | none |
| pubtator | litterature | codex-mcp-documentation-only | 1 | 0 | none |
| biolqm-convert | maboss | mcp-narrative-only | 1 | 0 | none |
| bn-control | maboss | mcp-narrative-only | 1 | 0 | none |
| boolean-attractors | maboss | mcp-narrative-only | 1 | 0 | none |
| colomoto-run | maboss | mcp-narrative-only | 1 | 0 | none |
| maboss-advanced | maboss | mcp-narrative-only | 1 | 0 | none |
| model-repositories | maboss | mcp-narrative-only | 1 | 0 | none |
| pydruglogics | maboss | mcp-narrative-only | 1 | 0 | none |
| convergent-evolution | mtbc | codex-mcp-tool-prerequisite | 2 | 0 | none |
| lineage-comparison | mtbc | codex-mcp-tool-prerequisite | 2 | 0 | none |
| lineage-subdivision | mtbc | rewrite-claude-skill-paths | 4 | 0 | none |
| mk-ascertainment | mtbc | rewrite-claude-skill-paths | 4 | 1 | __pycache__ |
| mtbc-epistasis | mtbc | rewrite-claude-skill-paths | 2 | 0 | none |
| mtbc-gene | mtbc | rewrite-claude-skill-paths | 22 | 8 | __pycache__ |
| mtbc-lineages | mtbc | rewrite-claude-skill-paths | 15 | 0 | none |
| pangenome-enrichment | mtbc | codex-mcp-tool-prerequisite | 2 | 0 | none |
| phylogeography | mtbc | codex-mcp-tool-prerequisite | 2 | 0 | none |
| resistance-catalogue | mtbc | codex-mcp-tool-prerequisite | 7 | 0 | none |
| resistance-profiler | mtbc | codex-mcp-tool-prerequisite | 2 | 0 | none |
| sitvitweb | mtbc | mcp-narrative-only | 3 | 0 | none |
| snp-distance | mtbc | codex-mcp-tool-prerequisite | 2 | 0 | none |
| spdi-annotation | mtbc | codex-mcp-tool-prerequisite | 2 | 0 | none |
| sra-geolocate | mtbc | rewrite-cache-path | 1 | 0 | none |
| tb-cli | mtbc | mcp-narrative-only | 1 | 0 | none |
| tbannotator-mcp | mtbc | codex-mcp-tool-prerequisite | 4 | 2 | __pycache__ |
| tsne-hdbscan | mtbc | codex-mcp-tool-prerequisite | 2 | 0 | none |
| imdb | multimedia | rewrite-claude-skill-paths | 9 | 0 | none |
| ancestral-reconstruction | phylo | codex-mcp-tool-prerequisite | 2 | 0 | none |
| bayesian-skyline | phylo | codex-mcp-documentation-only | 1 | 0 | none |
| beast2-phylogeography | phylo | codex-mcp-documentation-only | 1 | 0 | none |
| nextstrain | phylo | codex-mcp-documentation-only | 1 | 0 | none |
| pastml | phylo | codex-mcp-documentation-only | 1 | 0 | none |
| aadr | popgen | codex-mcp-documentation-only | 10 | 0 | none |
| amtdb | popgen | codex-mcp-documentation-only | 10 | 0 | none |
| card | popgen | codex-mcp-documentation-only | 1 | 0 | none |
| coevolution | popgen | codex-mcp-tool-prerequisite | 3 | 0 | none |
| d-place | popgen | codex-mcp-documentation-only | 10 | 0 | none |
| orbis | popgen | codex-mcp-documentation-only | 11 | 0 | none |
| p3k14c | popgen | codex-mcp-documentation-only | 10 | 0 | none |
| seshat | popgen | codex-mcp-documentation-only | 10 | 0 | none |
| slavevoyages | popgen | codex-mcp-documentation-only | 10 | 0 | none |
| spaam-ancient-metagenome-dir | popgen | codex-mcp-documentation-only | 1 | 0 | none |
| spaam-community | popgen | codex-mcp-documentation-only | 1 | 0 | none |
| sci-table | redaction | rewrite-claude-skill-paths | 6 | 0 | none |
| active-site-check | structure | rewrite-claude-skill-paths | 4 | 1 | __pycache__ |
| boltz | structure | await-canonical-knowledge-path | 2 | 0 | none |
