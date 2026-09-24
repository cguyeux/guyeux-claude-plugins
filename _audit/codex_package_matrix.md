# Matrice CCX-10 d'empaquetage Codex

Ce fichier est genere par `_audit/tools/generate_codex_package_matrix.py`.
Il inventorie les skills canoniques absents de `codex_skills.json` et indique le premier traitement requis pour les empaqueter dans Codex.

- Total non exporte Codex : 152
- Deja materialises dans un paquet pilote : 5
- Deja materialises dans des paquets directs : 48
- Deja materialises dans des paquets payload audites : 19
- Deja materialises avec adaptation runtime Codex : 62
- Deja materialises avec garde-fou workflow Codex : 12
- Bloques par workflow personnel d'ecriture : 2
- Adaptation runtime Claude ou MCP requise : 2
- Audit de payload requis : 2
- Candidats directs sans verrou mecanique majeur : 0

## Comptes par paquet cible

| paquet | skills |
|---|---:|
| bacteria | 17 |
| bioinfo | 9 |
| carriere | 1 |
| diffusion | 2 |
| guyeux-phylo-pilot | 5 |
| ia | 16 |
| litterature | 6 |
| maboss | 12 |
| mtbc | 32 |
| multimedia | 3 |
| ops | 4 |
| phylo | 9 |
| popgen | 26 |
| redaction | 3 |
| science-commun | 1 |
| structure | 4 |
| web | 2 |

## Matrice complete

| skill | source | paquet | statut | signaux | action |
|---|---|---|---|---|---|
| aadr | popgen | popgen | packaged-runtime-adapted | mcp-runtime, supporting-resources, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| aap | carriere | carriere | packaged-workflow-guarded | claude-runtime-reference, project-memory-write, script-payload, supporting-resources | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| abc-xgboost | popgen | popgen | packaged-direct | supporting-resources | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| active-site-check | structure | structure | packaged-runtime-adapted | claude-runtime-reference, script-payload | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| amtdb | popgen | popgen | packaged-runtime-adapted | mcp-runtime, supporting-resources, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| ancestral-reconstruction | phylo | phylo | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| ani-panel-classify | bacteria | bacteria | needs-codex-runtime-adaptation | claude-runtime-reference, script-payload, unsupported-frontmatter, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| astrologics | maboss | maboss | packaged-direct | web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| atlantic-voyages | popgen | popgen | packaged-payload | script-payload, unsupported-frontmatter, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| atlas-add-lineage | mtbc | mtbc | packaged-workflow-guarded | claude-runtime-reference, project-memory-write, unsupported-frontmatter, web-runtime | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| bacdive | bacteria | bacteria | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| bactrline | bacteria | bacteria | packaged-direct | provenance-recorded, unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| bayesian-skyline | phylo | phylo | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| bdd-bridge | mtbc | mtbc | packaged-workflow-guarded | claude-runtime-reference, mcp-runtime, project-memory-write, script-payload, unsupported-frontmatter | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| beast2-dating | phylo | phylo | packaged-payload | script-payload | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| beast2-phylogeography | phylo | phylo | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| bioc-pmc | litterature | litterature | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| biolqm-convert | maboss | maboss | packaged-runtime-adapted | mcp-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| biopython | bioinfo | bioinfo | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| bioskills | bioinfo | bioinfo | packaged-payload | script-payload, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| bn-control | maboss | maboss | packaged-runtime-adapted | mcp-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| boltz | structure | structure | packaged-runtime-adapted | claude-runtime-reference, script-payload, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| boolean-attractors | maboss | maboss | packaged-runtime-adapted | mcp-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| bovine-genomics | popgen | popgen | packaged-direct | web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| cadrage-editorial | diffusion | diffusion | packaged-workflow-guarded | claude-runtime-reference, project-memory-write, script-payload, supporting-resources, unsupported-frontmatter, web-runtime | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| card | popgen | popgen | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| causal-inference | ia | ia | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| coevolution | popgen | popgen | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| colomoto-run | maboss | maboss | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| convergent-evolution | mtbc | mtbc | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| d-place | popgen | popgen | packaged-runtime-adapted | mcp-runtime, supporting-resources, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| denovo-content-qc | mtbc | mtbc | packaged-workflow-guarded | project-memory-write, script-payload | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| deploy-predictops | ops | ops | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| documentation | ops | ops | packaged-workflow-guarded | project-memory-write | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| domestication-pathways | popgen | popgen | packaged-payload | script-payload, unsupported-frontmatter, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| enterobase | bacteria | bacteria | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| esm-atlas-cli | structure | structure | packaged-direct | supporting-resources, unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| europe-pmc | litterature | litterature | packaged-runtime-adapted | claude-runtime-reference, mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| fetch-tbannotator | mtbc | mtbc | packaged-workflow-guarded | claude-runtime-reference, mcp-runtime, project-memory-write, script-payload, unsupported-frontmatter, web-runtime | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| fig-ideation | redaction | redaction | packaged-workflow-guarded | claude-runtime-reference, data-payload, mcp-runtime, project-memory-write, script-payload, supporting-resources, unsupported-frontmatter, web-runtime | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| frontend-design | web | web | packaged-direct | none | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| geopandas | ia | ia | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| glottolog | popgen | popgen | packaged-direct | supporting-resources, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| gwas-clonal-lineage | mtbc | mtbc | packaged-payload | script-payload, supporting-resources, unsupported-frontmatter | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| helicobacter-pylori-phylogeography | bacteria | bacteria | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| hgt-direction-check | bacteria | bacteria | packaged-runtime-adapted | claude-runtime-reference, script-payload | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| hgt-interdomain-check | bacteria | bacteria | blocked-by-personal-workflow | claude-runtime-reference, project-memory-write, script-payload | Porter ou neutraliser les ecritures de memoire projet avant empaquetage. |
| host-pathogen-pair | popgen | popgen | packaged-payload | script-payload, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| imdb | multimedia | multimedia | packaged-runtime-adapted | claude-runtime-reference, script-payload, supporting-resources, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| incident-response | ops | ops | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| indian-ocean-voyages | popgen | popgen | packaged-payload | script-payload, unsupported-frontmatter, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| iqtree-lsd2 | phylo | guyeux-phylo-pilot | packaged-pilot | mcp-runtime, web-runtime | Deja materialise dans le lot temoin, verifier lors de l'extension. |
| itol | phylo | phylo | packaged-payload | script-payload | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| jgi-imgvr | bacteria | bacteria | needs-payload-package-audit | provenance-recorded, script-payload, unsupported-frontmatter | Copier scripts, donnees et references, puis tester le payload installe. |
| leptospira-bigsdb | bacteria | bacteria | needs-payload-package-audit | provenance-recorded, script-payload, web-runtime | Copier scripts, donnees et references, puis tester le payload installe. |
| lineage-comparison | mtbc | mtbc | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| lineage-subdivision | mtbc | mtbc | packaged-runtime-adapted | claude-runtime-reference, script-payload, unsupported-frontmatter, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| maboss-advanced | maboss | maboss | packaged-runtime-adapted | mcp-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| maboss-ecosystem | maboss | maboss | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| maboss-model | maboss | maboss | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| migration-data | popgen | popgen | packaged-payload | script-payload, unsupported-frontmatter | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| mk-ascertainment | mtbc | mtbc | packaged-runtime-adapted | claude-runtime-reference, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| ml-model-explainer | ia | ia | packaged-payload | script-payload | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| model-inference | maboss | maboss | packaged-direct | none | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| model-repositories | maboss | maboss | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| modern-human-reference-panels | popgen | popgen | packaged-payload | script-payload, supporting-resources, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| molecular-clock | phylo | guyeux-phylo-pilot | packaged-pilot | mcp-runtime, script-payload, unsupported-frontmatter, web-runtime | Deja materialise dans le lot temoin, verifier lors de l'extension. |
| mtbc-bilan | mtbc | mtbc | packaged-workflow-guarded | claude-runtime-reference, mcp-runtime, project-memory-write, supporting-resources, unsupported-frontmatter, web-runtime | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| mtbc-epistasis | mtbc | mtbc | packaged-runtime-adapted | claude-runtime-reference, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| mtbc-gene | mtbc | mtbc | packaged-runtime-adapted | claude-runtime-reference, script-payload, supporting-resources, unsupported-frontmatter, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| mtbc-gene-network | mtbc | mtbc | packaged-payload | script-payload, supporting-resources, unsupported-frontmatter | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| mtbc-lineages | mtbc | mtbc | packaged-runtime-adapted | claude-runtime-reference, data-payload, mcp-runtime, script-payload, supporting-resources, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| mtbc-prospect | mtbc | guyeux-phylo-pilot | packaged-pilot | claude-runtime-reference, mcp-runtime, project-memory-write, supporting-resources, unsupported-frontmatter, web-runtime | Deja materialise dans le lot temoin, verifier lors de l'extension. |
| mtbc-reboot | mtbc | mtbc | packaged-runtime-adapted | claude-runtime-reference, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| mycobacterium-leprae | bacteria | bacteria | packaged-runtime-adapted | mcp-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| ncbi-pathogen-detection | bacteria | bacteria | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| neolithic-14c | popgen | popgen | packaged-direct | supporting-resources, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| networkx | ia | ia | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| nextflow-development | bioinfo | bioinfo | packaged-runtime-adapted | claude-runtime-reference, script-payload, supporting-resources, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| nextstrain | phylo | phylo | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| ntm-resources | bacteria | bacteria | packaged-direct | provenance-recorded, supporting-resources, unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| numpy | ia | ia | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| numpy-low-level | ia | ia | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| ontologies | bioinfo | bioinfo | packaged-direct | web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| openalex | litterature | litterature | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| orbis | popgen | popgen | packaged-runtime-adapted | mcp-runtime, supporting-resources, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| owtrad | popgen | popgen | packaged-direct | supporting-resources, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| p3k14c | popgen | popgen | packaged-runtime-adapted | mcp-runtime, supporting-resources, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| paleoclimate | popgen | popgen | packaged-direct | supporting-resources, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| pandas-performance | ia | ia | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| pangenome-enrichment | mtbc | mtbc | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| parity-check | redaction | redaction | blocked-by-personal-workflow | claude-runtime-reference, project-memory-write, script-payload, unsupported-frontmatter | Porter ou neutraliser les ecritures de memoire projet avant empaquetage. |
| pastml | phylo | phylo | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| pathogens-portal | bacteria | bacteria | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| pectinated-subclade-mining | mtbc | mtbc | packaged-workflow-guarded | claude-runtime-reference, mcp-runtime, project-memory-write, script-payload, unsupported-frontmatter | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| phylo-forest | phylo | phylo | packaged-payload | script-payload, unsupported-frontmatter | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| phylo-history | mtbc | mtbc | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| phylo-narrative | mtbc | mtbc | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| phylo-placement | phylo | phylo | needs-codex-runtime-adaptation | claude-runtime-reference, script-payload, unsupported-frontmatter | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| phylogeography | mtbc | mtbc | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| pleiades | popgen | popgen | packaged-direct | supporting-resources, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| pubmed-database | litterature | litterature | packaged-runtime-adapted | mcp-runtime, supporting-resources, unsupported-frontmatter, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| pubtator | litterature | litterature | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| pydruglogics | maboss | maboss | packaged-runtime-adapted | mcp-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| pymaboss | maboss | maboss | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| pymlst | bacteria | bacteria | packaged-runtime-adapted | mcp-runtime, provenance-recorded, unsupported-frontmatter, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| pysam | bioinfo | bioinfo | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| raxml | phylo | guyeux-phylo-pilot | packaged-pilot | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise dans le lot temoin, verifier lors de l'extension. |
| rdkit | structure | structure | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| registres-sans-referent | mtbc | mtbc | packaged-payload | script-payload | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| resistance-catalogue | mtbc | mtbc | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| resistance-profiler | mtbc | mtbc | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| scanpy | bioinfo | bioinfo | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| sci-table | redaction | redaction | packaged-runtime-adapted | claude-runtime-reference, script-payload, supporting-resources, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| scientific-problem-selection | science-commun | science-commun | packaged-direct | supporting-resources | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| scikit-bio | bioinfo | bioinfo | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| scikit-learn | ia | ia | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| scipy | ia | ia | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| senior-data-scientist | ia | ia | packaged-direct | none | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| seshat | popgen | popgen | packaged-runtime-adapted | mcp-runtime, supporting-resources, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| shapely | ia | ia | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| silent-film-subs | multimedia | multimedia | packaged-payload | script-payload, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| sitvitweb | mtbc | mtbc | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| sklearn-advanced | ia | ia | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| sklearn-explainability | ia | ia | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| slavevoyages | popgen | popgen | packaged-runtime-adapted | mcp-runtime, supporting-resources, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| snp-distance | mtbc | mtbc | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| soumission | diffusion | diffusion | packaged-workflow-guarded | claude-runtime-reference, mcp-runtime, project-memory-write, script-payload, supporting-resources, web-runtime | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| spaam-ancient-metagenome-dir | popgen | popgen | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| spaam-community | popgen | popgen | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| spdi-annotation | mtbc | mtbc | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| species-id | bacteria | bacteria | packaged-runtime-adapted | claude-runtime-reference, mcp-runtime, unsupported-frontmatter, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| sra-geolocate | mtbc | mtbc | packaged-runtime-adapted | claude-runtime-reference, mcp-runtime, script-payload, unsupported-frontmatter, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| statistical-analysis | science-commun | ia | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| statsmodels | ia | ia | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| strain-qc | mtbc | mtbc | packaged-workflow-guarded | claude-runtime-reference, project-memory-write, unsupported-frontmatter | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| string-db | bioinfo | bioinfo | packaged-direct | supporting-resources, unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| supp-tables | litterature | litterature | packaged-payload | provenance-recorded, script-payload, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| tb-cli | mtbc | mtbc | packaged-runtime-adapted | mcp-runtime, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| tbannotator-mcp | mtbc | mtbc | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| tbmonitor-papers | mtbc | guyeux-phylo-pilot | packaged-pilot | mcp-runtime, unsupported-frontmatter, web-runtime | Deja materialise dans le lot temoin, verifier lors de l'extension. |
| text-to-speech | multimedia | multimedia | packaged-payload | script-payload, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| thd | bacteria | bacteria | packaged-runtime-adapted | claude-runtime-reference, mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| tooluniverse-sequence-retrieval | bioinfo | bioinfo | packaged-direct | web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| tsne-hdbscan | mtbc | mtbc | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| upstream-contribution | ops | ops | packaged-direct | provenance-recorded | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| variant-reality-check | mtbc | mtbc | packaged-payload | script-payload, unsupported-frontmatter | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| wals | popgen | popgen | packaged-direct | supporting-resources, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| webapp-testing | web | web | packaged-payload | script-payload, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| worldclim-bioclim | popgen | popgen | packaged-direct | supporting-resources, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| xgboost-iterative-optimizer | ia | ia | packaged-direct | supporting-resources | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| yersinia-resources | bacteria | bacteria | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
