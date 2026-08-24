# Matrice CCX-10 des adaptations runtime Codex

Ce fichier est genere par `_audit/tools/generate_codex_runtime_adaptation_matrix.py`.
Il decompose les skills classes `needs-codex-runtime-adaptation` par la matrice principale.

- Total a adapter : 58

## Comptes par famille d'adaptation

| famille | skills |
|---|---:|
| await-canonical-knowledge-path | 1 |
| claude-branding-only | 1 |
| codex-mcp-documentation-only | 24 |
| codex-mcp-tool-prerequisite | 12 |
| external-mcp-required | 1 |
| mcp-narrative-only | 9 |
| rewrite-cache-path | 1 |
| rewrite-claude-skill-paths | 9 |

## Matrice complete

| skill | source | paquet | famille | problemes | action |
|---|---|---|---|---|---|
| aadr | bio_population_genetics | bio-population-genetics | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| active-site-check | bio_pathogens | bio-pathogens | rewrite-claude-skill-paths | claude-skill-path | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| amtdb | bio_population_genetics | bio-population-genetics | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| ancestral-reconstruction | bio_pathogens | bio-pathogens | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| bacdive | bio_pathogens | bio-pathogens | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| bayesian-skyline | bio_population_genetics | bio-population-genetics | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| beast2-phylogeography | bio_population_genetics | bio-population-genetics | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| bioc-pmc | bio_population_genetics | bio-population-genetics | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, web-tool-name, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| biolqm-convert | maboss | maboss | mcp-narrative-only | generic-mcp-mention | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| bn-control | maboss | maboss | mcp-narrative-only | generic-mcp-mention | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| boltz | bio_population_genetics | bio-population-genetics | await-canonical-knowledge-path | claude-knowledge-path, http-literal | Attendre CCX-04 ou remplacer par le chemin KB Codex actuel avec mention de migration future. |
| boolean-attractors | maboss | maboss | mcp-narrative-only | generic-mcp-mention | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| card | bio_population_genetics | bio-population-genetics | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| clinical-trial-protocol-skill | bio_population_genetics | bio-population-genetics | external-mcp-required | generic-mcp-mention | Ne pas empaqueter sans serveur MCP Codex equivalent ou fallback documente. |
| coevolution | bio_pathogens | bio-pathogens | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| colomoto-run | maboss | maboss | mcp-narrative-only | generic-mcp-mention, http-literal | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| convergent-evolution | bio_pathogens | bio-pathogens | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name, generic-mcp-mention | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| d-place | bio_population_genetics | bio-population-genetics | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| enterobase | bio_bacteria | bio-bacteria | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| europe-pmc | bio_population_genetics | bio-population-genetics | rewrite-claude-skill-paths | claude-plugin-root, tbannotator-mcp, generic-mcp-mention, web-tool-name, http-literal | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| helicobacter-pylori-phylogeography | bio_bacteria | bio-bacteria | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| imdb | multimedia | multimedia | rewrite-claude-skill-paths | claude-plugin-root | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| lineage-comparison | bio_pathogens | bio-pathogens | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name, generic-mcp-mention | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| lineage-subdivision | bio_pathogens | bio-pathogens | rewrite-claude-skill-paths | claude-plugin-root, http-literal | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| maboss-advanced | maboss | maboss | mcp-narrative-only | generic-mcp-mention | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| mk-ascertainment | bio_pathogens | bio-pathogens | rewrite-claude-skill-paths | claude-plugin-root | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| model-repositories | maboss | maboss | mcp-narrative-only | generic-mcp-mention, http-literal | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| mtbc-epistasis | bio_pathogens | bio-pathogens | rewrite-claude-skill-paths | claude-plugin-root, claude-knowledge-path | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| mtbc-gene | bio_pathogens | bio-pathogens | rewrite-claude-skill-paths | claude-plugin-root, claude-knowledge-path, http-literal | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| mtbc-lineages | bio_pathogens | bio-pathogens | rewrite-claude-skill-paths | claude-plugin-root, tbannotator-mcp, generic-mcp-mention | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| mycobacterium-leprae | bio_bacteria | bio-bacteria | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| ncbi-pathogen-detection | bio_bacteria | bio-bacteria | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| nextflow-development | bio_population_genetics | bio-population-genetics | claude-branding-only | claude-config-or-branding, http-literal | Emballage possible apres neutralisation de la mention de marque si necessaire. |
| nextstrain | bio_population_genetics | bio-population-genetics | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| openalex | bio_population_genetics | bio-population-genetics | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| orbis | bio_population_genetics | bio-population-genetics | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| p3k14c | bio_population_genetics | bio-population-genetics | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| pangenome-enrichment | bio_pathogens | bio-pathogens | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name, generic-mcp-mention, http-literal | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| pastml | bio_population_genetics | bio-population-genetics | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| pathogens-portal | bio_pathogens | bio-pathogens | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| phylogeography | bio_pathogens | bio-pathogens | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name, generic-mcp-mention | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| pubmed-database | bio_population_genetics | bio-population-genetics | codex-mcp-documentation-only | tbmonitor-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| pubtator | bio_population_genetics | bio-population-genetics | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, web-tool-name, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| pydruglogics | maboss | maboss | mcp-narrative-only | generic-mcp-mention | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| pymlst | bio_bacteria | bio-bacteria | mcp-narrative-only | generic-mcp-mention, http-literal | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| resistance-catalogue | bio_pathogens | bio-pathogens | codex-mcp-tool-prerequisite | tbannotator-mcp, tbmonitor-mcp, mcp-tool-name | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| resistance-profiler | bio_pathogens | bio-pathogens | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name, generic-mcp-mention | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| seshat | bio_population_genetics | bio-population-genetics | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| slavevoyages | bio_population_genetics | bio-population-genetics | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| snp-distance | bio_pathogens | bio-pathogens | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| spaam-ancient-metagenome-dir | bio_pathogens | bio-pathogens | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| spaam-community | bio_pathogens | bio-pathogens | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| spdi-annotation | bio_pathogens | bio-pathogens | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name, generic-mcp-mention | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| species-id | bio_pathogens | bio-pathogens | mcp-narrative-only | generic-mcp-mention, web-tool-name, http-literal | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| sra-geolocate | bio_pathogens | bio-pathogens | rewrite-cache-path | claude-cache-path, generic-mcp-mention, web-tool-name, http-literal | Remplacer le cache Claude par un cache neutre sous ~/.cache ou par une sortie projet explicite. |
| tbannotator-mcp | bio_pathogens | bio-pathogens | codex-mcp-tool-prerequisite | claude-config-or-branding, tbannotator-mcp, mcp-tool-name, generic-mcp-mention, http-literal | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| thd | bio_pathogens | bio-pathogens | rewrite-claude-skill-paths | claude-plugin-root, tbannotator-mcp, mcp-tool-name | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| tsne-hdbscan | bio_pathogens | bio-pathogens | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name, generic-mcp-mention | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
