# Plugin `bio_redac`

> Un plugin pour l'analyse bioinformatique et la rédaction d'articles sur M.tuberculosis

## Rôle dans un projet M. tuberculosis

Phase hybride analyse et rédaction. Agrège par symlink les skills des autres plugins pour le moment où l'on passe des résultats phylogénomiques M. tuberculosis (arbre daté, profils de résistance, figures) au manuscrit.

Skills propres (canoniques) : **1** ; skills partagés utilisés (symlinks) : **124**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [phylo-history](#phylo-history)

### phylo-history

Rédige un paragraphe pour un manuscrit scientifique décrivant le placement phylogénétique d'une souche MTBC à travers les arbres dans lesquels elle a figuré. Exploite investigate_phylo/history/ et les fichiers Newick archivés pour produire une narration sourcée sur les voisins, la sister clade, la stabilité de l'assignation et le voisinage inter-reconstructions

Compétences : writing the Results section of a lineage paper and needing a justified sentence about a strain's placement ; documenting why a strain was retained, reclassified or excluded ; preparing supplementary material describing the phylogenetic position of outlier strains ; responding to a reviewer asking for evidence about a specific strain's lineage

## Skills partagés (via symlink)

Documentés sur la page de leur plugin d'origine.

| Skill | Origine |
|-------|---------|
| [aadr](bio_population_genetics.md#aadr) | `bio_population_genetics` |
| [amtdb](bio_population_genetics.md#amtdb) | `bio_population_genetics` |
| [ancestral-reconstruction](bio_pathogens.md#ancestral-reconstruction) | `bio_pathogens` |
| [atlas-add-lineage](bio_pathogens.md#atlas-add-lineage) | `bio_pathogens` |
| [bacdive](bio_pathogens.md#bacdive) | `bio_pathogens` |
| [bayesian-skyline](bio_population_genetics.md#bayesian-skyline) | `bio_population_genetics` |
| [bdd-bridge](bio_pathogens.md#bdd-bridge) | `bio_pathogens` |
| [beamer-slides](redac.md#beamer-slides) | `redac` |
| [beast2-dating](bio_pathogens.md#beast2-dating) | `bio_pathogens` |
| [beast2-phylogeography](bio_population_genetics.md#beast2-phylogeography) | `bio_population_genetics` |
| [bib-check](redac.md#bib-check) | `redac` |
| [biblatex](redac.md#biblatex) | `redac` |
| [bioc-pmc](bio_population_genetics.md#bioc-pmc) | `bio_population_genetics` |
| [biopython](bio_population_genetics.md#biopython) | `bio_population_genetics` |
| [bioskills](bio_population_genetics.md#bioskills) | `bio_population_genetics` |
| [bovine-genomics](bio_population_genetics.md#bovine-genomics) | `bio_population_genetics` |
| [card](bio_population_genetics.md#card) | `bio_population_genetics` |
| [clade-finder](bio_pathogens.md#clade-finder) | `bio_pathogens` |
| [claim-check](redac.md#claim-check) | `redac` |
| [clinical-trial-protocol-skill](bio_population_genetics.md#clinical-trial-protocol-skill) | `bio_population_genetics` |
| [coevolution](bio_pathogens.md#coevolution) | `bio_pathogens` |
| [convergent-evolution](bio_pathogens.md#convergent-evolution) | `bio_pathogens` |
| [create-viz](ops.md#create-viz) | `ops` |
| [cv](redac.md#cv) | `redac` |
| [d-place](bio_population_genetics.md#d-place) | `bio_population_genetics` |
| [deai-latex](redac.md#deai-latex) | `redac` |
| [docs-latex](redac.md#docs-latex) | `redac` |
| [enterobase](bio_pathogens.md#enterobase) | `bio_pathogens` |
| [esm-atlas-cli](bio_population_genetics.md#esm-atlas-cli) | `bio_population_genetics` |
| [europe-pmc](bio_population_genetics.md#europe-pmc) | `bio_population_genetics` |
| [fetch-tbannotator](bio_pathogens.md#fetch-tbannotator) | `bio_pathogens` |
| [fig-check](redac.md#fig-check) | `redac` |
| [geo-map](bio_population_genetics.md#geo-map) | `bio_population_genetics` |
| [glottolog](bio_population_genetics.md#glottolog) | `bio_population_genetics` |
| [grant-proposal](redac.md#grant-proposal) | `redac` |
| [helicobacter-pylori-phylogeography](bio_pathogens.md#helicobacter-pylori-phylogeography) | `bio_pathogens` |
| [host-pathogen-pair](bio_pathogens.md#host-pathogen-pair) | `bio_pathogens` |
| [humanizer](redac.md#humanizer) | `redac` |
| [iqtree-lsd2](bio_population_genetics.md#iqtree-lsd2) | `bio_population_genetics` |
| [itol](bio_population_genetics.md#itol) | `bio_population_genetics` |
| [latex-build](redac.md#latex-build) | `redac` |
| [latex-document](redac.md#latex-document) | `redac` |
| [latex-formatting](redac.md#latex-formatting) | `redac` |
| [latex-paper-en](redac.md#latex-paper-en) | `redac` |
| [latex-posters](redac.md#latex-posters) | `redac` |
| [latex-tables](redac.md#latex-tables) | `redac` |
| [latex-writing](redac.md#latex-writing) | `redac` |
| [lineage-comparison](bio_pathogens.md#lineage-comparison) | `bio_pathogens` |
| [lit-review](redac.md#lit-review) | `redac` |
| [manuscript-review](redac.md#manuscript-review) | `redac` |
| [matplotlib](ia.md#matplotlib) | `ia` |
| [matplotlib-pro](ia.md#matplotlib-pro) | `ia` |
| [mbovis](bio_pathogens.md#mbovis) | `bio_pathogens` |
| [migration-data](bio_population_genetics.md#migration-data) | `bio_population_genetics` |
| [mk-ascertainment](bio_pathogens.md#mk-ascertainment) | `bio_pathogens` |
| [modern-human-reference-panels](bio_population_genetics.md#modern-human-reference-panels) | `bio_population_genetics` |
| [molecular-clock](bio_pathogens.md#molecular-clock) | `bio_pathogens` |
| [mtbc-bilan](bio_pathogens.md#mtbc-bilan) | `bio_pathogens` |
| [mtbc-deepen](bio_pathogens.md#mtbc-deepen) | `bio_pathogens` |
| [mtbc-gene-function](bio_pathogens.md#mtbc-gene-function) | `bio_pathogens` |
| [mtbc-lineages](bio_pathogens.md#mtbc-lineages) | `bio_pathogens` |
| [mtbc-mutation-impact](bio_pathogens.md#mtbc-mutation-impact) | `bio_pathogens` |
| [mtbc-pathway-explain](bio_pathogens.md#mtbc-pathway-explain) | `bio_pathogens` |
| [mtbc-reboot](bio_pathogens.md#mtbc-reboot) | `bio_pathogens` |
| [mycobacterium-leprae](bio_pathogens.md#mycobacterium-leprae) | `bio_pathogens` |
| [ncbi-pathogen-detection](bio_pathogens.md#ncbi-pathogen-detection) | `bio_pathogens` |
| [neolithic-14c](bio_population_genetics.md#neolithic-14c) | `bio_population_genetics` |
| [nextflow-development](bio_population_genetics.md#nextflow-development) | `bio_population_genetics` |
| [nextstrain](bio_population_genetics.md#nextstrain) | `bio_population_genetics` |
| [ontologies](bio_population_genetics.md#ontologies) | `bio_population_genetics` |
| [openalex](bio_population_genetics.md#openalex) | `bio_population_genetics` |
| [orbis](bio_population_genetics.md#orbis) | `bio_population_genetics` |
| [owtrad](bio_population_genetics.md#owtrad) | `bio_population_genetics` |
| [p3k14c](bio_population_genetics.md#p3k14c) | `bio_population_genetics` |
| [paleoclimate](bio_population_genetics.md#paleoclimate) | `bio_population_genetics` |
| [pangenome-enrichment](bio_pathogens.md#pangenome-enrichment) | `bio_pathogens` |
| [pastml](bio_population_genetics.md#pastml) | `bio_population_genetics` |
| [pathogens-portal](bio_pathogens.md#pathogens-portal) | `bio_pathogens` |
| [pdf-to-latex](redac.md#pdf-to-latex) | `redac` |
| [phylogeography](bio_pathogens.md#phylogeography) | `bio_pathogens` |
| [pleiades](bio_population_genetics.md#pleiades) | `bio_population_genetics` |
| [plotly](redac.md#plotly) | `redac` |
| [pubmed-database](bio_population_genetics.md#pubmed-database) | `bio_population_genetics` |
| [pubtator](bio_population_genetics.md#pubtator) | `bio_population_genetics` |
| [pysam](bio_population_genetics.md#pysam) | `bio_population_genetics` |
| [raxml](bio_pathogens.md#raxml) | `bio_pathogens` |
| [rdkit](bio_population_genetics.md#rdkit) | `bio_population_genetics` |
| [read-scientific-pdf](bio_population_genetics.md#read-scientific-pdf) | `bio_population_genetics` |
| [resistance-catalogue](bio_pathogens.md#resistance-catalogue) | `bio_pathogens` |
| [resistance-discovery](bio_pathogens.md#resistance-discovery) | `bio_pathogens` |
| [resistance-explain](bio_pathogens.md#resistance-explain) | `bio_pathogens` |
| [resistance-predict](bio_pathogens.md#resistance-predict) | `bio_pathogens` |
| [resistance-profiler](bio_pathogens.md#resistance-profiler) | `bio_pathogens` |
| [reviewer-response](redac.md#reviewer-response) | `redac` |
| [scanpy](bio_population_genetics.md#scanpy) | `bio_population_genetics` |
| [scientific-problem-selection](ia.md#scientific-problem-selection) | `ia` |
| [scikit-bio](bio_population_genetics.md#scikit-bio) | `bio_population_genetics` |
| [scikit-learn](ia.md#scikit-learn) | `ia` |
| [seaborn](bio_population_genetics.md#seaborn) | `bio_population_genetics` |
| [seshat](bio_population_genetics.md#seshat) | `bio_population_genetics` |
| [sitvitweb](bio_pathogens.md#sitvitweb) | `bio_pathogens` |
| [slavevoyages](bio_population_genetics.md#slavevoyages) | `bio_population_genetics` |
| [slide-design](redac.md#slide-design) | `redac` |
| [slide-polish](redac.md#slide-polish) | `redac` |
| [snp-distance](bio_pathogens.md#snp-distance) | `bio_pathogens` |
| [spaam-ancient-metagenome-dir](bio_pathogens.md#spaam-ancient-metagenome-dir) | `bio_pathogens` |
| [spaam-community](bio_pathogens.md#spaam-community) | `bio_pathogens` |
| [spdi-annotation](bio_pathogens.md#spdi-annotation) | `bio_pathogens` |
| [species-id](bio_pathogens.md#species-id) | `bio_pathogens` |
| [sra-geolocate](bio_pathogens.md#sra-geolocate) | `bio_pathogens` |
| [statsmodels](ia.md#statsmodels) | `ia` |
| [strain-qc](bio_pathogens.md#strain-qc) | `bio_pathogens` |
| [supp-check](redac.md#supp-check) | `redac` |
| [synthesize-research](redac.md#synthesize-research) | `redac` |
| [tb-cli](bio_pathogens.md#tb-cli) | `bio_pathogens` |
| [tbannotator-mcp](bio_pathogens.md#tbannotator-mcp) | `bio_pathogens` |
| [tbmonitor-papers](bio_pathogens.md#tbmonitor-papers) | `bio_pathogens` |
| [thd](bio_pathogens.md#thd) | `bio_pathogens` |
| [theme-factory](redac.md#theme-factory) | `redac` |
| [tooluniverse-sequence-retrieval](bio_population_genetics.md#tooluniverse-sequence-retrieval) | `bio_population_genetics` |
| [triangulate-route](bio_pathogens.md#triangulate-route) | `bio_pathogens` |
| [tsne-hdbscan](bio_pathogens.md#tsne-hdbscan) | `bio_pathogens` |
| [wals](bio_population_genetics.md#wals) | `bio_population_genetics` |
| [worldclim-bioclim](bio_population_genetics.md#worldclim-bioclim) | `bio_population_genetics` |

