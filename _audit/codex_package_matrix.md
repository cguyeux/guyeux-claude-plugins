# Matrice CCX-10 d'empaquetage Codex

Ce fichier est genere par `_audit/tools/generate_codex_package_matrix.py`.
Il inventorie les skills canoniques absents de `codex_skills.json` et indique le premier traitement requis pour les empaqueter dans Codex.

- Total non exporte Codex : 135
- Deja materialises dans un paquet pilote : 5
- Bloques par workflow personnel d'ecriture : 9
- Adaptation runtime Claude ou MCP requise : 58
- Audit de payload requis : 15
- Candidats directs sans verrou mecanique majeur : 48

## Comptes par paquet cible

| paquet | skills |
|---|---:|
| bio-bacteria | 8 |
| bio-pathogens | 39 |
| bio-population-genetics | 47 |
| bio-redac | 1 |
| guyeux-phylo-pilot | 5 |
| ia | 14 |
| maboss | 12 |
| multimedia | 3 |
| ops | 4 |
| web | 2 |

## Matrice complete

| skill | source | paquet | statut | signaux | action |
|---|---|---|---|---|---|
| aadr | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | mcp-runtime, supporting-resources, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| abc-xgboost | bio_population_genetics | bio-population-genetics | direct-package-candidate | supporting-resources | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| active-site-check | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | claude-runtime-reference, script-payload | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| amtdb | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | mcp-runtime, supporting-resources, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| ancestral-reconstruction | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | mcp-runtime, script-payload, unsupported-frontmatter | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| astrologics | maboss | maboss | direct-package-candidate | web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| atlantic-voyages | bio_population_genetics | bio-population-genetics | needs-payload-package-audit | script-payload, unsupported-frontmatter, web-runtime | Copier scripts, donnees et references, puis tester le payload installe. |
| atlas-add-lineage | bio_pathogens | bio-pathogens | blocked-by-personal-workflow | claude-runtime-reference, project-memory-write, unsupported-frontmatter, web-runtime | Porter ou neutraliser les ecritures de memoire projet avant empaquetage. |
| bacdive | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | mcp-runtime, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| bactrline | bio_bacteria | bio-bacteria | direct-package-candidate | provenance-recorded, unsupported-frontmatter, web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| bayesian-skyline | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | mcp-runtime, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| bdd-bridge | bio_pathogens | bio-pathogens | blocked-by-personal-workflow | claude-runtime-reference, mcp-runtime, project-memory-write, script-payload, unsupported-frontmatter | Porter ou neutraliser les ecritures de memoire projet avant empaquetage. |
| beast2-dating | bio_pathogens | bio-pathogens | needs-payload-package-audit | script-payload | Copier scripts, donnees et references, puis tester le payload installe. |
| beast2-phylogeography | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | mcp-runtime, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| bioc-pmc | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | mcp-runtime, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| biolqm-convert | maboss | maboss | needs-codex-runtime-adaptation | mcp-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| biopython | bio_population_genetics | bio-population-genetics | direct-package-candidate | web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| bioskills | bio_population_genetics | bio-population-genetics | needs-payload-package-audit | script-payload, web-runtime | Copier scripts, donnees et references, puis tester le payload installe. |
| bn-control | maboss | maboss | needs-codex-runtime-adaptation | mcp-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| boltz | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | claude-runtime-reference, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| boolean-attractors | maboss | maboss | needs-codex-runtime-adaptation | mcp-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| bovine-genomics | bio_population_genetics | bio-population-genetics | direct-package-candidate | web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| card | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | mcp-runtime, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| causal-inference | ia | ia | direct-package-candidate | web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| clinical-trial-protocol-skill | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | data-payload, mcp-runtime, script-payload, supporting-resources | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| coevolution | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | mcp-runtime, script-payload, unsupported-frontmatter | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| colomoto-run | maboss | maboss | needs-codex-runtime-adaptation | mcp-runtime, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| convergent-evolution | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | mcp-runtime, script-payload, unsupported-frontmatter | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| d-place | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | mcp-runtime, supporting-resources, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| denovo-content-qc | bio_pathogens | bio-pathogens | blocked-by-personal-workflow | project-memory-write, script-payload | Porter ou neutraliser les ecritures de memoire projet avant empaquetage. |
| deploy-predictops | ops | ops | direct-package-candidate | unsupported-frontmatter | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| documentation | ops | ops | blocked-by-personal-workflow | project-memory-write | Porter ou neutraliser les ecritures de memoire projet avant empaquetage. |
| domestication-pathways | bio_population_genetics | bio-population-genetics | needs-payload-package-audit | script-payload, unsupported-frontmatter, web-runtime | Copier scripts, donnees et references, puis tester le payload installe. |
| enterobase | bio_bacteria | bio-bacteria | needs-codex-runtime-adaptation | mcp-runtime, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| esm-atlas-cli | bio_population_genetics | bio-population-genetics | direct-package-candidate | supporting-resources, unsupported-frontmatter, web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| europe-pmc | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | claude-runtime-reference, mcp-runtime, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| fetch-tbannotator | bio_pathogens | bio-pathogens | blocked-by-personal-workflow | claude-runtime-reference, mcp-runtime, project-memory-write, script-payload, unsupported-frontmatter, web-runtime | Porter ou neutraliser les ecritures de memoire projet avant empaquetage. |
| frontend-design | web | web | direct-package-candidate | none | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| geopandas | ia | ia | direct-package-candidate | web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| glottolog | bio_population_genetics | bio-population-genetics | direct-package-candidate | supporting-resources, web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| helicobacter-pylori-phylogeography | bio_bacteria | bio-bacteria | needs-codex-runtime-adaptation | mcp-runtime, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| host-pathogen-pair | bio_pathogens | bio-pathogens | needs-payload-package-audit | script-payload, web-runtime | Copier scripts, donnees et references, puis tester le payload installe. |
| imdb | multimedia | multimedia | needs-codex-runtime-adaptation | claude-runtime-reference, script-payload, supporting-resources | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| incident-response | ops | ops | direct-package-candidate | unsupported-frontmatter | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| indian-ocean-voyages | bio_population_genetics | bio-population-genetics | needs-payload-package-audit | script-payload, unsupported-frontmatter, web-runtime | Copier scripts, donnees et references, puis tester le payload installe. |
| iqtree-lsd2 | bio_population_genetics | guyeux-phylo-pilot | packaged-pilot | mcp-runtime, web-runtime | Deja materialise dans le lot temoin, verifier lors de l'extension. |
| itol | bio_population_genetics | bio-population-genetics | needs-payload-package-audit | script-payload | Copier scripts, donnees et references, puis tester le payload installe. |
| lineage-comparison | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | mcp-runtime, script-payload, unsupported-frontmatter | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| lineage-subdivision | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | claude-runtime-reference, script-payload, unsupported-frontmatter, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| maboss-advanced | maboss | maboss | needs-codex-runtime-adaptation | mcp-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| maboss-ecosystem | maboss | maboss | direct-package-candidate | unsupported-frontmatter, web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| maboss-model | maboss | maboss | direct-package-candidate | unsupported-frontmatter | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| migration-data | bio_population_genetics | bio-population-genetics | needs-payload-package-audit | script-payload, unsupported-frontmatter | Copier scripts, donnees et references, puis tester le payload installe. |
| mk-ascertainment | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | claude-runtime-reference, script-payload, unsupported-frontmatter | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| ml-model-explainer | ia | ia | needs-payload-package-audit | script-payload | Copier scripts, donnees et references, puis tester le payload installe. |
| model-inference | maboss | maboss | direct-package-candidate | none | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| model-repositories | maboss | maboss | needs-codex-runtime-adaptation | mcp-runtime, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| modern-human-reference-panels | bio_population_genetics | bio-population-genetics | needs-payload-package-audit | script-payload, supporting-resources, web-runtime | Copier scripts, donnees et references, puis tester le payload installe. |
| molecular-clock | bio_pathogens | guyeux-phylo-pilot | packaged-pilot | mcp-runtime, script-payload, unsupported-frontmatter, web-runtime | Deja materialise dans le lot temoin, verifier lors de l'extension. |
| mtbc-bilan | bio_pathogens | bio-pathogens | blocked-by-personal-workflow | claude-runtime-reference, project-memory-write, supporting-resources, unsupported-frontmatter, web-runtime | Porter ou neutraliser les ecritures de memoire projet avant empaquetage. |
| mtbc-epistasis | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | claude-runtime-reference, script-payload, unsupported-frontmatter | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| mtbc-gene | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | claude-runtime-reference, script-payload, supporting-resources, unsupported-frontmatter, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| mtbc-gene-network | bio_pathogens | bio-pathogens | needs-payload-package-audit | script-payload, supporting-resources, unsupported-frontmatter | Copier scripts, donnees et references, puis tester le payload installe. |
| mtbc-lineages | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | claude-runtime-reference, data-payload, mcp-runtime, script-payload, supporting-resources, unsupported-frontmatter | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| mtbc-prospect | bio_pathogens | guyeux-phylo-pilot | packaged-pilot | claude-runtime-reference, mcp-runtime, project-memory-write, supporting-resources, unsupported-frontmatter, web-runtime | Deja materialise dans le lot temoin, verifier lors de l'extension. |
| mtbc-reboot | bio_pathogens | bio-pathogens | blocked-by-personal-workflow | claude-runtime-reference, mcp-runtime, project-memory-write, unsupported-frontmatter, web-runtime | Porter ou neutraliser les ecritures de memoire projet avant empaquetage. |
| mycobacterium-leprae | bio_bacteria | bio-bacteria | needs-codex-runtime-adaptation | mcp-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| ncbi-pathogen-detection | bio_bacteria | bio-bacteria | needs-codex-runtime-adaptation | mcp-runtime, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| neolithic-14c | bio_population_genetics | bio-population-genetics | direct-package-candidate | supporting-resources, web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| networkx | ia | ia | direct-package-candidate | web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| nextflow-development | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | claude-runtime-reference, script-payload, supporting-resources, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| nextstrain | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | mcp-runtime, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| ntm-resources | bio_bacteria | bio-bacteria | direct-package-candidate | provenance-recorded, supporting-resources, unsupported-frontmatter, web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| numpy | ia | ia | direct-package-candidate | web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| numpy-low-level | ia | ia | direct-package-candidate | none | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| ontologies | bio_population_genetics | bio-population-genetics | direct-package-candidate | web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| openalex | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | mcp-runtime, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| orbis | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | mcp-runtime, supporting-resources, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| owtrad | bio_population_genetics | bio-population-genetics | direct-package-candidate | supporting-resources, web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| p3k14c | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | mcp-runtime, supporting-resources, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| paleoclimate | bio_population_genetics | bio-population-genetics | direct-package-candidate | supporting-resources, web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| pandas-performance | ia | ia | direct-package-candidate | web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| pangenome-enrichment | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | mcp-runtime, script-payload, unsupported-frontmatter, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| pastml | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | mcp-runtime, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| pathogens-portal | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | mcp-runtime, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| pectinated-subclade-mining | bio_pathogens | bio-pathogens | blocked-by-personal-workflow | claude-runtime-reference, mcp-runtime, project-memory-write, script-payload, unsupported-frontmatter | Porter ou neutraliser les ecritures de memoire projet avant empaquetage. |
| phylo-history | bio_redac | bio-redac | direct-package-candidate | unsupported-frontmatter | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| phylogeography | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | mcp-runtime, script-payload, unsupported-frontmatter | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| pleiades | bio_population_genetics | bio-population-genetics | direct-package-candidate | supporting-resources, web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| pubmed-database | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | mcp-runtime, supporting-resources, unsupported-frontmatter, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| pubtator | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | mcp-runtime, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| pydruglogics | maboss | maboss | needs-codex-runtime-adaptation | mcp-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| pymaboss | maboss | maboss | direct-package-candidate | unsupported-frontmatter | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| pymlst | bio_bacteria | bio-bacteria | needs-codex-runtime-adaptation | mcp-runtime, provenance-recorded, unsupported-frontmatter, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| pysam | bio_population_genetics | bio-population-genetics | direct-package-candidate | none | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| raxml | bio_pathogens | guyeux-phylo-pilot | packaged-pilot | mcp-runtime, script-payload, unsupported-frontmatter, web-runtime | Deja materialise dans le lot temoin, verifier lors de l'extension. |
| rdkit | bio_population_genetics | bio-population-genetics | direct-package-candidate | web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| resistance-catalogue | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | mcp-runtime, script-payload, unsupported-frontmatter | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| resistance-profiler | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | mcp-runtime, script-payload, unsupported-frontmatter | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| scanpy | bio_population_genetics | bio-population-genetics | direct-package-candidate | none | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| scientific-problem-selection | bio_population_genetics | bio-population-genetics | direct-package-candidate | supporting-resources | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| scikit-bio | bio_population_genetics | bio-population-genetics | direct-package-candidate | web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| scikit-learn | bio_population_genetics | bio-population-genetics | direct-package-candidate | web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| scipy | ia | ia | direct-package-candidate | web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| senior-data-scientist | ia | ia | direct-package-candidate | none | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| seshat | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | mcp-runtime, supporting-resources, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| shapely | ia | ia | direct-package-candidate | web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| silent-film-subs | multimedia | multimedia | needs-payload-package-audit | script-payload, web-runtime | Copier scripts, donnees et references, puis tester le payload installe. |
| sitvitweb | bio_pathogens | bio-pathogens | needs-payload-package-audit | script-payload, unsupported-frontmatter, web-runtime | Copier scripts, donnees et references, puis tester le payload installe. |
| sklearn-advanced | ia | ia | direct-package-candidate | web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| sklearn-explainability | ia | ia | direct-package-candidate | none | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| slavevoyages | bio_population_genetics | bio-population-genetics | needs-codex-runtime-adaptation | mcp-runtime, supporting-resources, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| snp-distance | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | mcp-runtime, script-payload, unsupported-frontmatter | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| spaam-ancient-metagenome-dir | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | mcp-runtime, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| spaam-community | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | mcp-runtime, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| spdi-annotation | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | mcp-runtime, script-payload, unsupported-frontmatter | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| species-id | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | mcp-runtime, unsupported-frontmatter, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| sra-geolocate | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | claude-runtime-reference, mcp-runtime, unsupported-frontmatter, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| statistical-analysis | ia | ia | direct-package-candidate | unsupported-frontmatter | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| statsmodels | bio_population_genetics | bio-population-genetics | direct-package-candidate | web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| strain-qc | bio_pathogens | bio-pathogens | blocked-by-personal-workflow | claude-runtime-reference, project-memory-write, unsupported-frontmatter | Porter ou neutraliser les ecritures de memoire projet avant empaquetage. |
| string-db | bio_pathogens | bio-pathogens | direct-package-candidate | supporting-resources, unsupported-frontmatter, web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| tb-cli | bio_pathogens | bio-pathogens | direct-package-candidate | unsupported-frontmatter | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| tbannotator-mcp | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | mcp-runtime, script-payload, unsupported-frontmatter, web-runtime | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| tbmonitor-papers | bio_pathogens | guyeux-phylo-pilot | packaged-pilot | claude-runtime-reference, mcp-runtime, unsupported-frontmatter, web-runtime | Deja materialise dans le lot temoin, verifier lors de l'extension. |
| text-to-speech | multimedia | multimedia | needs-payload-package-audit | script-payload, web-runtime | Copier scripts, donnees et references, puis tester le payload installe. |
| thd | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | claude-runtime-reference, mcp-runtime, script-payload, unsupported-frontmatter | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| tooluniverse-sequence-retrieval | bio_population_genetics | bio-population-genetics | direct-package-candidate | web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| tsne-hdbscan | bio_pathogens | bio-pathogens | needs-codex-runtime-adaptation | mcp-runtime, script-payload, unsupported-frontmatter | Remplacer les references Claude et declarer les prerequis MCP Codex. |
| upstream-contribution | ops | ops | direct-package-candidate | provenance-recorded | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| wals | bio_population_genetics | bio-population-genetics | direct-package-candidate | supporting-resources, web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| webapp-testing | web | web | needs-payload-package-audit | script-payload, web-runtime | Copier scripts, donnees et references, puis tester le payload installe. |
| worldclim-bioclim | bio_population_genetics | bio-population-genetics | direct-package-candidate | supporting-resources, web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| xgboost-iterative-optimizer | ia | ia | direct-package-candidate | supporting-resources | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
| yersinia-resources | bio_bacteria | bio-bacteria | direct-package-candidate | unsupported-frontmatter, web-runtime | Copier le skill dans son paquet cible, puis retirer les champs Claude si presents. |
