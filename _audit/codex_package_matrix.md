# Matrice CCX-10 d'empaquetage Codex

Ce fichier est genere par `_audit/tools/generate_codex_package_matrix.py`.
Il inventorie les skills canoniques absents de `codex_skills.json` et indique le premier traitement requis pour les empaqueter dans Codex.

- Total non exporte Codex : 137
- Deja materialises dans un paquet pilote : 5
- Deja materialises dans des paquets directs : 48
- Deja materialises dans des paquets payload audites : 15
- Deja materialises avec adaptation runtime Codex : 58
- Deja materialises avec garde-fou workflow Codex : 11
- Bloques par workflow personnel d'ecriture : 0
- Adaptation runtime Claude ou MCP requise : 0
- Audit de payload requis : 0
- Candidats directs sans verrou mecanique majeur : 0

## Comptes par paquet cible

| paquet | skills |
|---|---:|
| bio-bacteria | 8 |
| bio-pathogens | 39 |
| bio-population-genetics | 47 |
| bio-redac | 3 |
| guyeux-phylo-pilot | 5 |
| ia | 14 |
| maboss | 12 |
| multimedia | 3 |
| ops | 4 |
| web | 2 |

## Matrice complete

| skill | source | paquet | statut | signaux | action |
|---|---|---|---|---|---|
| aadr | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | mcp-runtime, supporting-resources, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| abc-xgboost | bio_population_genetics | bio-population-genetics | packaged-direct | supporting-resources | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| active-site-check | bio_pathogens | bio-pathogens | packaged-runtime-adapted | claude-runtime-reference, script-payload | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| amtdb | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | mcp-runtime, supporting-resources, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| ancestral-reconstruction | bio_pathogens | bio-pathogens | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| astrologics | maboss | maboss | packaged-direct | web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| atlantic-voyages | bio_population_genetics | bio-population-genetics | packaged-payload | script-payload, unsupported-frontmatter, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| atlas-add-lineage | bio_pathogens | bio-pathogens | packaged-workflow-guarded | claude-runtime-reference, project-memory-write, unsupported-frontmatter, web-runtime | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| bacdive | bio_pathogens | bio-pathogens | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| bactrline | bio_bacteria | bio-bacteria | packaged-direct | provenance-recorded, unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| bayesian-skyline | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| bdd-bridge | bio_pathogens | bio-pathogens | packaged-workflow-guarded | claude-runtime-reference, mcp-runtime, project-memory-write, script-payload, unsupported-frontmatter | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| beast2-dating | bio_pathogens | bio-pathogens | packaged-payload | script-payload | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| beast2-phylogeography | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| bioc-pmc | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| biolqm-convert | maboss | maboss | packaged-runtime-adapted | mcp-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| biopython | bio_population_genetics | bio-population-genetics | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| bioskills | bio_population_genetics | bio-population-genetics | packaged-payload | script-payload, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| bn-control | maboss | maboss | packaged-runtime-adapted | mcp-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| boltz | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | claude-runtime-reference, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| boolean-attractors | maboss | maboss | packaged-runtime-adapted | mcp-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| bovine-genomics | bio_population_genetics | bio-population-genetics | packaged-direct | web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| card | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| causal-inference | ia | ia | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| clinical-trial-protocol-skill | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | data-payload, mcp-runtime, script-payload, supporting-resources | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| coevolution | bio_pathogens | bio-pathogens | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| colomoto-run | maboss | maboss | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| convergent-evolution | bio_pathogens | bio-pathogens | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| d-place | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | mcp-runtime, supporting-resources, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| denovo-content-qc | bio_pathogens | bio-pathogens | packaged-workflow-guarded | project-memory-write, script-payload | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| deploy-predictops | ops | ops | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| documentation | ops | ops | packaged-workflow-guarded | project-memory-write | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| domestication-pathways | bio_population_genetics | bio-population-genetics | packaged-payload | script-payload, unsupported-frontmatter, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| enterobase | bio_bacteria | bio-bacteria | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| esm-atlas-cli | bio_population_genetics | bio-population-genetics | packaged-direct | supporting-resources, unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| europe-pmc | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | claude-runtime-reference, mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| fetch-tbannotator | bio_pathogens | bio-pathogens | packaged-workflow-guarded | claude-runtime-reference, mcp-runtime, project-memory-write, script-payload, unsupported-frontmatter, web-runtime | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| fig-ideation | redac | bio-redac | packaged-workflow-guarded | claude-runtime-reference, data-payload, mcp-runtime, project-memory-write, script-payload, supporting-resources, unsupported-frontmatter, web-runtime | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| frontend-design | web | web | packaged-direct | none | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| geopandas | ia | ia | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| glottolog | bio_population_genetics | bio-population-genetics | packaged-direct | supporting-resources, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| helicobacter-pylori-phylogeography | bio_bacteria | bio-bacteria | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| host-pathogen-pair | bio_pathogens | bio-pathogens | packaged-payload | script-payload, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| imdb | multimedia | multimedia | packaged-runtime-adapted | claude-runtime-reference, script-payload, supporting-resources, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| incident-response | ops | ops | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| indian-ocean-voyages | bio_population_genetics | bio-population-genetics | packaged-payload | script-payload, unsupported-frontmatter, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| iqtree-lsd2 | bio_population_genetics | guyeux-phylo-pilot | packaged-pilot | mcp-runtime, web-runtime | Deja materialise dans le lot temoin, verifier lors de l'extension. |
| itol | bio_population_genetics | bio-population-genetics | packaged-payload | script-payload | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| lineage-comparison | bio_pathogens | bio-pathogens | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| lineage-subdivision | bio_pathogens | bio-pathogens | packaged-runtime-adapted | claude-runtime-reference, script-payload, unsupported-frontmatter, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| maboss-advanced | maboss | maboss | packaged-runtime-adapted | mcp-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| maboss-ecosystem | maboss | maboss | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| maboss-model | maboss | maboss | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| migration-data | bio_population_genetics | bio-population-genetics | packaged-payload | script-payload, unsupported-frontmatter | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| mk-ascertainment | bio_pathogens | bio-pathogens | packaged-runtime-adapted | claude-runtime-reference, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| ml-model-explainer | ia | ia | packaged-payload | script-payload | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| model-inference | maboss | maboss | packaged-direct | none | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| model-repositories | maboss | maboss | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| modern-human-reference-panels | bio_population_genetics | bio-population-genetics | packaged-payload | script-payload, supporting-resources, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| molecular-clock | bio_pathogens | guyeux-phylo-pilot | packaged-pilot | mcp-runtime, script-payload, unsupported-frontmatter, web-runtime | Deja materialise dans le lot temoin, verifier lors de l'extension. |
| mtbc-bilan | bio_pathogens | bio-pathogens | packaged-workflow-guarded | claude-runtime-reference, project-memory-write, supporting-resources, unsupported-frontmatter, web-runtime | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| mtbc-epistasis | bio_pathogens | bio-pathogens | packaged-runtime-adapted | claude-runtime-reference, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| mtbc-gene | bio_pathogens | bio-pathogens | packaged-runtime-adapted | claude-runtime-reference, script-payload, supporting-resources, unsupported-frontmatter, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| mtbc-gene-network | bio_pathogens | bio-pathogens | packaged-payload | script-payload, supporting-resources, unsupported-frontmatter | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| mtbc-lineages | bio_pathogens | bio-pathogens | packaged-runtime-adapted | claude-runtime-reference, data-payload, mcp-runtime, script-payload, supporting-resources, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| mtbc-prospect | bio_pathogens | guyeux-phylo-pilot | packaged-pilot | claude-runtime-reference, mcp-runtime, project-memory-write, supporting-resources, unsupported-frontmatter, web-runtime | Deja materialise dans le lot temoin, verifier lors de l'extension. |
| mtbc-reboot | bio_pathogens | bio-pathogens | packaged-workflow-guarded | claude-runtime-reference, mcp-runtime, project-memory-write, unsupported-frontmatter, web-runtime | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| mycobacterium-leprae | bio_bacteria | bio-bacteria | packaged-runtime-adapted | mcp-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| ncbi-pathogen-detection | bio_bacteria | bio-bacteria | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| neolithic-14c | bio_population_genetics | bio-population-genetics | packaged-direct | supporting-resources, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| networkx | ia | ia | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| nextflow-development | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | claude-runtime-reference, script-payload, supporting-resources, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| nextstrain | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| ntm-resources | bio_bacteria | bio-bacteria | packaged-direct | provenance-recorded, supporting-resources, unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| numpy | ia | ia | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| numpy-low-level | ia | ia | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| ontologies | bio_population_genetics | bio-population-genetics | packaged-direct | web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| openalex | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| orbis | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | mcp-runtime, supporting-resources, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| owtrad | bio_population_genetics | bio-population-genetics | packaged-direct | supporting-resources, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| p3k14c | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | mcp-runtime, supporting-resources, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| paleoclimate | bio_population_genetics | bio-population-genetics | packaged-direct | supporting-resources, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| pandas-performance | ia | ia | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| pangenome-enrichment | bio_pathogens | bio-pathogens | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| pastml | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| pathogens-portal | bio_pathogens | bio-pathogens | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| pectinated-subclade-mining | bio_pathogens | bio-pathogens | packaged-workflow-guarded | claude-runtime-reference, mcp-runtime, project-memory-write, script-payload, unsupported-frontmatter | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| phylo-history | bio_redac | bio-redac | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| phylogeography | bio_pathogens | bio-pathogens | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| pleiades | bio_population_genetics | bio-population-genetics | packaged-direct | supporting-resources, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| pubmed-database | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | mcp-runtime, supporting-resources, unsupported-frontmatter, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| pubtator | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| pydruglogics | maboss | maboss | packaged-runtime-adapted | mcp-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| pymaboss | maboss | maboss | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| pymlst | bio_bacteria | bio-bacteria | packaged-runtime-adapted | mcp-runtime, provenance-recorded, unsupported-frontmatter, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| pysam | bio_population_genetics | bio-population-genetics | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| raxml | bio_pathogens | guyeux-phylo-pilot | packaged-pilot | mcp-runtime, script-payload, unsupported-frontmatter, web-runtime | Deja materialise dans le lot temoin, verifier lors de l'extension. |
| rdkit | bio_population_genetics | bio-population-genetics | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| resistance-catalogue | bio_pathogens | bio-pathogens | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| resistance-profiler | bio_pathogens | bio-pathogens | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| scanpy | bio_population_genetics | bio-population-genetics | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| scientific-problem-selection | bio_population_genetics | bio-population-genetics | packaged-direct | supporting-resources | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| scikit-bio | bio_population_genetics | bio-population-genetics | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| scikit-learn | bio_population_genetics | bio-population-genetics | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| scipy | ia | ia | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| senior-data-scientist | ia | ia | packaged-direct | none | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| seshat | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | mcp-runtime, supporting-resources, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| shapely | ia | ia | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| silent-film-subs | multimedia | multimedia | packaged-payload | script-payload, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| sitvitweb | bio_pathogens | bio-pathogens | packaged-payload | script-payload, unsupported-frontmatter, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| sklearn-advanced | ia | ia | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| sklearn-explainability | ia | ia | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| slavevoyages | bio_population_genetics | bio-population-genetics | packaged-runtime-adapted | mcp-runtime, supporting-resources, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| snp-distance | bio_pathogens | bio-pathogens | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| soumission | redac | bio-redac | packaged-workflow-guarded | claude-runtime-reference, project-memory-write, script-payload, supporting-resources, web-runtime | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| spaam-ancient-metagenome-dir | bio_pathogens | bio-pathogens | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| spaam-community | bio_pathogens | bio-pathogens | packaged-runtime-adapted | mcp-runtime, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| spdi-annotation | bio_pathogens | bio-pathogens | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| species-id | bio_pathogens | bio-pathogens | packaged-runtime-adapted | mcp-runtime, unsupported-frontmatter, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| sra-geolocate | bio_pathogens | bio-pathogens | packaged-runtime-adapted | claude-runtime-reference, mcp-runtime, unsupported-frontmatter, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| statistical-analysis | ia | ia | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| statsmodels | bio_population_genetics | bio-population-genetics | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| strain-qc | bio_pathogens | bio-pathogens | packaged-workflow-guarded | claude-runtime-reference, project-memory-write, unsupported-frontmatter | Deja materialise avec garde-fou workflow Codex, verifier les mutations explicites avant execution. |
| string-db | bio_pathogens | bio-pathogens | packaged-direct | supporting-resources, unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| tb-cli | bio_pathogens | bio-pathogens | packaged-direct | unsupported-frontmatter | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| tbannotator-mcp | bio_pathogens | bio-pathogens | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter, web-runtime | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| tbmonitor-papers | bio_pathogens | guyeux-phylo-pilot | packaged-pilot | claude-runtime-reference, mcp-runtime, unsupported-frontmatter, web-runtime | Deja materialise dans le lot temoin, verifier lors de l'extension. |
| text-to-speech | multimedia | multimedia | packaged-payload | script-payload, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| thd | bio_pathogens | bio-pathogens | packaged-runtime-adapted | claude-runtime-reference, mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| tooluniverse-sequence-retrieval | bio_population_genetics | bio-population-genetics | packaged-direct | web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| tsne-hdbscan | bio_pathogens | bio-pathogens | packaged-runtime-adapted | mcp-runtime, script-payload, unsupported-frontmatter | Deja materialise avec adaptation runtime Codex, verifier les prerequis MCP et les reecritures de copie. |
| upstream-contribution | ops | ops | packaged-direct | provenance-recorded | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| wals | bio_population_genetics | bio-population-genetics | packaged-direct | supporting-resources, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| webapp-testing | web | web | packaged-payload | script-payload, web-runtime | Deja materialise dans un paquet payload audite, verifier scripts et exclusions lors de l'installation isolee. |
| worldclim-bioclim | bio_population_genetics | bio-population-genetics | packaged-direct | supporting-resources, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| xgboost-iterative-optimizer | ia | ia | packaged-direct | supporting-resources | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
| yersinia-resources | bio_bacteria | bio-bacteria | packaged-direct | unsupported-frontmatter, web-runtime | Deja materialise dans un paquet direct, verifier lors de l'installation isolee. |
