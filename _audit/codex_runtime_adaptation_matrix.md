# Matrice CCX-10 des adaptations runtime Codex

Ce fichier est genere par `_audit/tools/generate_codex_runtime_adaptation_matrix.py`.
Il decompose les skills classes `needs-codex-runtime-adaptation` par la matrice principale.

- Total a adapter : 64

## Comptes par famille d'adaptation

| famille | skills |
|---|---:|
| await-canonical-knowledge-path | 1 |
| claude-branding-only | 1 |
| codex-mcp-documentation-only | 24 |
| codex-mcp-tool-prerequisite | 12 |
| mcp-narrative-only | 11 |
| rewrite-cache-path | 1 |
| rewrite-claude-skill-paths | 11 |
| unclassified-runtime-signal | 3 |

## Matrice complete

| skill | source | paquet | famille | problemes | action |
|---|---|---|---|---|---|
| aadr | popgen | popgen | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| active-site-check | structure | structure | rewrite-claude-skill-paths | claude-skill-path | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| amtdb | popgen | popgen | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| ancestral-reconstruction | phylo | phylo | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name, generic-mcp-mention | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| ani-panel-classify | bacteria | bacteria | unclassified-runtime-signal | none | Relire manuellement avant empaquetage. |
| bacdive | bacteria | bacteria | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| bayesian-skyline | phylo | phylo | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| beast2-phylogeography | phylo | phylo | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| bioc-pmc | litterature | litterature | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, web-tool-name, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| biolqm-convert | maboss | maboss | mcp-narrative-only | generic-mcp-mention | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| bn-control | maboss | maboss | mcp-narrative-only | generic-mcp-mention | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| boltz | structure | structure | await-canonical-knowledge-path | claude-knowledge-path, http-literal | Attendre CCX-04 ou remplacer par le chemin KB Codex actuel avec mention de migration future. |
| boolean-attractors | maboss | maboss | mcp-narrative-only | generic-mcp-mention | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| card | popgen | popgen | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| coevolution | popgen | popgen | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name, generic-mcp-mention | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| colomoto-run | maboss | maboss | mcp-narrative-only | generic-mcp-mention, http-literal | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| convergent-evolution | mtbc | mtbc | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name, generic-mcp-mention | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| d-place | popgen | popgen | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| enterobase | bacteria | bacteria | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| europe-pmc | litterature | litterature | rewrite-claude-skill-paths | claude-plugin-root, tbannotator-mcp, generic-mcp-mention, web-tool-name, http-literal | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| helicobacter-pylori-phylogeography | bacteria | bacteria | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| hgt-direction-check | bacteria | bacteria | unclassified-runtime-signal | none | Relire manuellement avant empaquetage. |
| imdb | multimedia | multimedia | rewrite-claude-skill-paths | claude-plugin-root | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| lineage-comparison | mtbc | mtbc | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name, generic-mcp-mention | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| lineage-subdivision | mtbc | mtbc | rewrite-claude-skill-paths | claude-plugin-root, http-literal | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| maboss-advanced | maboss | maboss | mcp-narrative-only | generic-mcp-mention | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| mk-ascertainment | mtbc | mtbc | rewrite-claude-skill-paths | claude-plugin-root | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| model-repositories | maboss | maboss | mcp-narrative-only | generic-mcp-mention, http-literal | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| mtbc-epistasis | mtbc | mtbc | rewrite-claude-skill-paths | claude-plugin-root, claude-knowledge-path | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| mtbc-gene | mtbc | mtbc | rewrite-claude-skill-paths | claude-plugin-root, claude-knowledge-path, http-literal | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| mtbc-lineages | mtbc | mtbc | rewrite-claude-skill-paths | claude-plugin-root, tbannotator-mcp, generic-mcp-mention | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| mtbc-reboot | mtbc | mtbc | rewrite-claude-skill-paths | claude-skill-path | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| mycobacterium-leprae | bacteria | bacteria | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| ncbi-pathogen-detection | bacteria | bacteria | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| nextflow-development | bioinfo | bioinfo | claude-branding-only | claude-config-or-branding, http-literal | Emballage possible apres neutralisation de la mention de marque si necessaire. |
| nextstrain | phylo | phylo | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| openalex | litterature | litterature | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| orbis | popgen | popgen | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| p3k14c | popgen | popgen | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| pangenome-enrichment | mtbc | mtbc | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name, generic-mcp-mention, http-literal | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| pastml | phylo | phylo | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| pathogens-portal | bacteria | bacteria | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| phylo-placement | phylo | phylo | unclassified-runtime-signal | none | Relire manuellement avant empaquetage. |
| phylogeography | mtbc | mtbc | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name, generic-mcp-mention | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| pubmed-database | litterature | litterature | codex-mcp-documentation-only | tbmonitor-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| pubtator | litterature | litterature | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, web-tool-name, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| pydruglogics | maboss | maboss | mcp-narrative-only | generic-mcp-mention | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| pymlst | bacteria | bacteria | mcp-narrative-only | generic-mcp-mention, http-literal | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| resistance-catalogue | mtbc | mtbc | codex-mcp-tool-prerequisite | tbannotator-mcp, tbmonitor-mcp, mcp-tool-name | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| resistance-profiler | mtbc | mtbc | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name, generic-mcp-mention | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| sci-table | redaction | redaction | rewrite-claude-skill-paths | claude-plugin-root | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| seshat | popgen | popgen | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| sitvitweb | mtbc | mtbc | mcp-narrative-only | generic-mcp-mention, http-literal | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| slavevoyages | popgen | popgen | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| snp-distance | mtbc | mtbc | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name, generic-mcp-mention | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| spaam-ancient-metagenome-dir | popgen | popgen | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| spaam-community | popgen | popgen | codex-mcp-documentation-only | tbannotator-mcp, generic-mcp-mention, http-literal | Emballage possible ; conserver la mention comme prerequis ou comparaison documentee. |
| spdi-annotation | mtbc | mtbc | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name, generic-mcp-mention | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| species-id | bacteria | bacteria | mcp-narrative-only | generic-mcp-mention, web-tool-name, http-literal | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| sra-geolocate | mtbc | mtbc | rewrite-cache-path | claude-cache-path, generic-mcp-mention, web-tool-name, http-literal | Remplacer le cache Claude par un cache neutre sous ~/.cache ou par une sortie projet explicite. |
| tb-cli | mtbc | mtbc | mcp-narrative-only | generic-mcp-mention | Emballage possible ; la mention MCP n'est pas un appel runtime direct. |
| tbannotator-mcp | mtbc | mtbc | codex-mcp-tool-prerequisite | claude-config-or-branding, tbannotator-mcp, mcp-tool-name, generic-mcp-mention, http-literal | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
| thd | bacteria | bacteria | rewrite-claude-skill-paths | claude-plugin-root, tbannotator-mcp, mcp-tool-name, generic-mcp-mention | Reecrire les chemins de scripts vers le chemin relatif du skill empaquete, puis materialiser le payload. |
| tsne-hdbscan | mtbc | mtbc | codex-mcp-tool-prerequisite | tbannotator-mcp, mcp-tool-name, generic-mcp-mention | Emballer apres declaration explicite du prerequis MCP Codex et validation dans un profil temporaire. |
