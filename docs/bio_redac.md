# Plugin `bio_redac`

> Un plugin pour l'analyse bioinformatique et la rédaction d'articles sur M.tuberculosis

## Rôle dans un projet M. tuberculosis

Phase hybride analyse et rédaction. Agrège par symlink les skills des autres plugins pour le moment où l'on passe des résultats phylogénomiques M. tuberculosis (arbre daté, profils de résistance, figures) au manuscrit.

Skills propres (canoniques) : **1** ; skills partagés utilisés (symlinks) : **147**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [phylo-history](#phylo-history)

### phylo-history

Rédige un paragraphe de manuscrit décrivant le placement phylogénétique d'une souche MTBC à travers les arbres où elle a figuré. Exploite investigate_phylo/history/ et les fichiers Newick archivés pour produire une narration sourcée sur les voisins, la sister clade, la stabilité de l'assignation et le voisinage inter-reconstructions.

Compétences : rédiger la section Résultats d'un article de lignée et justifier le placement d'une souche ; documenter pourquoi une souche a été retenue, reclassée ou exclue ; préparer un supplément décrivant la position phylogénétique de souches aberrantes ; répondre à un relecteur demandant des preuves sur la lignée d'une souche précise

## Skills partagés (via symlink)

Documentés sur la page de leur plugin d'origine.

| Skill | Origine |
|-------|---------|
| [aadr](bio_population_genetics.md#aadr) | `bio_population_genetics` |
| [active-site-check](bio_pathogens.md#active-site-check) | `bio_pathogens` |
| [amtdb](bio_population_genetics.md#amtdb) | `bio_population_genetics` |
| [ancestral-reconstruction](bio_pathogens.md#ancestral-reconstruction) | `bio_pathogens` |
| [atlantic-voyages](bio_population_genetics.md#atlantic-voyages) | `bio_population_genetics` |
| [atlas-add-lineage](bio_pathogens.md#atlas-add-lineage) | `bio_pathogens` |
| [bacdive](bio_pathogens.md#bacdive) | `bio_pathogens` |
| [bactrline](bio_bacteria.md#bactrline) | `bio_bacteria` |
| [bayesian-skyline](bio_population_genetics.md#bayesian-skyline) | `bio_population_genetics` |
| [bdd-bridge](bio_pathogens.md#bdd-bridge) | `bio_pathogens` |
| [beamer-slides](redac.md#beamer-slides) | `redac` |
| [beast2-dating](bio_pathogens.md#beast2-dating) | `bio_pathogens` |
| [beast2-phylogeography](bio_population_genetics.md#beast2-phylogeography) | `bio_population_genetics` |
| [bib-check](redac.md#bib-check) | `redac` |
| [biblatex](redac.md#biblatex) | `redac` |
| [binary-coclustering](bio_pathogens.md#binary-coclustering) | `bio_pathogens` |
| [bioc-pmc](bio_population_genetics.md#bioc-pmc) | `bio_population_genetics` |
| [bioproject-scout](bio_pathogens.md#bioproject-scout) | `bio_pathogens` |
| [biopython](bio_population_genetics.md#biopython) | `bio_population_genetics` |
| [bioskills](bio_population_genetics.md#bioskills) | `bio_population_genetics` |
| [biotools](bio_population_genetics.md#biotools) | `bio_population_genetics` |
| [boltz](bio_population_genetics.md#boltz) | `bio_population_genetics` |
| [bovine-genomics](bio_population_genetics.md#bovine-genomics) | `bio_population_genetics` |
| [card](bio_population_genetics.md#card) | `bio_population_genetics` |
| [claim-check](redac.md#claim-check) | `redac` |
| [clinical-trial-protocol-skill](bio_population_genetics.md#clinical-trial-protocol-skill) | `bio_population_genetics` |
| [coevolution](bio_pathogens.md#coevolution) | `bio_pathogens` |
| [convergent-evolution](bio_pathogens.md#convergent-evolution) | `bio_pathogens` |
| [create-viz](bio_population_genetics.md#create-viz) | `bio_population_genetics` |
| [crispr-spacer-null](bio_pathogens.md#crispr-spacer-null) | `bio_pathogens` |
| [crisprbuilder](bio_pathogens.md#crisprbuilder) | `bio_pathogens` |
| [crisprcasdb](bio_pathogens.md#crisprcasdb) | `bio_pathogens` |
| [cv](redac.md#cv) | `redac` |
| [d-place](bio_population_genetics.md#d-place) | `bio_population_genetics` |
| [deai-latex](redac.md#deai-latex) | `redac` |
| [denovo-content-qc](bio_pathogens.md#denovo-content-qc) | `bio_pathogens` |
| [docs-latex](redac.md#docs-latex) | `redac` |
| [domestication-pathways](bio_population_genetics.md#domestication-pathways) | `bio_population_genetics` |
| [enterobase](bio_bacteria.md#enterobase) | `bio_bacteria` |
| [esm-atlas-cli](bio_population_genetics.md#esm-atlas-cli) | `bio_population_genetics` |
| [europe-pmc](bio_population_genetics.md#europe-pmc) | `bio_population_genetics` |
| [fetch-tbannotator](bio_pathogens.md#fetch-tbannotator) | `bio_pathogens` |
| [fig-check](redac.md#fig-check) | `redac` |
| [geo-map](bio_population_genetics.md#geo-map) | `bio_population_genetics` |
| [glottolog](bio_population_genetics.md#glottolog) | `bio_population_genetics` |
| [grant-proposal](redac.md#grant-proposal) | `redac` |
| [helicobacter-pylori-phylogeography](bio_bacteria.md#helicobacter-pylori-phylogeography) | `bio_bacteria` |
| [host-pathogen-pair](bio_pathogens.md#host-pathogen-pair) | `bio_pathogens` |
| [humanizer](redac.md#humanizer) | `redac` |
| [indian-ocean-voyages](bio_population_genetics.md#indian-ocean-voyages) | `bio_population_genetics` |
| [iqtree-lsd2](bio_population_genetics.md#iqtree-lsd2) | `bio_population_genetics` |
| [isfinder-offline](bio_pathogens.md#isfinder-offline) | `bio_pathogens` |
| [itol](bio_population_genetics.md#itol) | `bio_population_genetics` |
| [latex-build](redac.md#latex-build) | `redac` |
| [latex-document](redac.md#latex-document) | `redac` |
| [latex-formatting](redac.md#latex-formatting) | `redac` |
| [latex-paper-en](redac.md#latex-paper-en) | `redac` |
| [latex-posters](redac.md#latex-posters) | `redac` |
| [latex-tables](redac.md#latex-tables) | `redac` |
| [latex-writing](redac.md#latex-writing) | `redac` |
| [lineage-comparison](bio_pathogens.md#lineage-comparison) | `bio_pathogens` |
| [lineage-subdivision](bio_pathogens.md#lineage-subdivision) | `bio_pathogens` |
| [lit-review](redac.md#lit-review) | `redac` |
| [literature-access](redac.md#literature-access) | `redac` |
| [manuscript-review](redac.md#manuscript-review) | `redac` |
| [marker-laminarity](bio_pathogens.md#marker-laminarity) | `bio_pathogens` |
| [migration-data](bio_population_genetics.md#migration-data) | `bio_population_genetics` |
| [miru-vntr](bio_pathogens.md#miru-vntr) | `bio_pathogens` |
| [mixed-infection](bio_pathogens.md#mixed-infection) | `bio_pathogens` |
| [mk-ascertainment](bio_pathogens.md#mk-ascertainment) | `bio_pathogens` |
| [modern-human-reference-panels](bio_population_genetics.md#modern-human-reference-panels) | `bio_population_genetics` |
| [molecular-clock](bio_pathogens.md#molecular-clock) | `bio_pathogens` |
| [mtbc-bilan](bio_pathogens.md#mtbc-bilan) | `bio_pathogens` |
| [mtbc-epistasis](bio_pathogens.md#mtbc-epistasis) | `bio_pathogens` |
| [mtbc-gene](bio_pathogens.md#mtbc-gene) | `bio_pathogens` |
| [mtbc-gene-network](bio_pathogens.md#mtbc-gene-network) | `bio_pathogens` |
| [mtbc-lineages](bio_pathogens.md#mtbc-lineages) | `bio_pathogens` |
| [mtbc-prospect](bio_pathogens.md#mtbc-prospect) | `bio_pathogens` |
| [mtbc-reboot](bio_pathogens.md#mtbc-reboot) | `bio_pathogens` |
| [mycobacterium-leprae](bio_bacteria.md#mycobacterium-leprae) | `bio_bacteria` |
| [ncbi-pathogen-detection](bio_bacteria.md#ncbi-pathogen-detection) | `bio_bacteria` |
| [neolithic-14c](bio_population_genetics.md#neolithic-14c) | `bio_population_genetics` |
| [nextflow-development](bio_population_genetics.md#nextflow-development) | `bio_population_genetics` |
| [nextstrain](bio_population_genetics.md#nextstrain) | `bio_population_genetics` |
| [ntm-resources](bio_bacteria.md#ntm-resources) | `bio_bacteria` |
| [ontologies](bio_population_genetics.md#ontologies) | `bio_population_genetics` |
| [openalex](bio_population_genetics.md#openalex) | `bio_population_genetics` |
| [orbis](bio_population_genetics.md#orbis) | `bio_population_genetics` |
| [overleaf-bridge](redac.md#overleaf-bridge) | `redac` |
| [owtrad](bio_population_genetics.md#owtrad) | `bio_population_genetics` |
| [p3k14c](bio_population_genetics.md#p3k14c) | `bio_population_genetics` |
| [paleoclimate](bio_population_genetics.md#paleoclimate) | `bio_population_genetics` |
| [pangenome-enrichment](bio_pathogens.md#pangenome-enrichment) | `bio_pathogens` |
| [panisa](bio_bacteria.md#panisa) | `bio_bacteria` |
| [pastml](bio_population_genetics.md#pastml) | `bio_population_genetics` |
| [pathogens-portal](bio_pathogens.md#pathogens-portal) | `bio_pathogens` |
| [pdf-to-latex](redac.md#pdf-to-latex) | `redac` |
| [pectinated-subclade-mining](bio_pathogens.md#pectinated-subclade-mining) | `bio_pathogens` |
| [phylogeography](bio_pathogens.md#phylogeography) | `bio_pathogens` |
| [pleiades](bio_population_genetics.md#pleiades) | `bio_population_genetics` |
| [pocket-detection](bio_pathogens.md#pocket-detection) | `bio_pathogens` |
| [pubmed-database](bio_population_genetics.md#pubmed-database) | `bio_population_genetics` |
| [pubtator](bio_population_genetics.md#pubtator) | `bio_population_genetics` |
| [pymlst](bio_bacteria.md#pymlst) | `bio_bacteria` |
| [pysam](bio_population_genetics.md#pysam) | `bio_population_genetics` |
| [raxml](bio_pathogens.md#raxml) | `bio_pathogens` |
| [rd-detection](bio_pathogens.md#rd-detection) | `bio_pathogens` |
| [rdkit](bio_population_genetics.md#rdkit) | `bio_population_genetics` |
| [read-scientific-pdf](bio_population_genetics.md#read-scientific-pdf) | `bio_population_genetics` |
| [remote-compute](bio_population_genetics.md#remote-compute) | `bio_population_genetics` |
| [resistance-catalogue](bio_pathogens.md#resistance-catalogue) | `bio_pathogens` |
| [resistance-profiler](bio_pathogens.md#resistance-profiler) | `bio_pathogens` |
| [reviewer-response](redac.md#reviewer-response) | `redac` |
| [scanpy](bio_population_genetics.md#scanpy) | `bio_population_genetics` |
| [sci-figure](bio_population_genetics.md#sci-figure) | `bio_population_genetics` |
| [scientific-problem-selection](bio_population_genetics.md#scientific-problem-selection) | `bio_population_genetics` |
| [scikit-bio](bio_population_genetics.md#scikit-bio) | `bio_population_genetics` |
| [scikit-learn](bio_population_genetics.md#scikit-learn) | `bio_population_genetics` |
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
| [statsmodels](bio_population_genetics.md#statsmodels) | `bio_population_genetics` |
| [strain-qc](bio_pathogens.md#strain-qc) | `bio_pathogens` |
| [string-db](bio_pathogens.md#string-db) | `bio_pathogens` |
| [supp-check](redac.md#supp-check) | `redac` |
| [synthesize-research](redac.md#synthesize-research) | `redac` |
| [tb-cli](bio_pathogens.md#tb-cli) | `bio_pathogens` |
| [tbannotator-es](bio_pathogens.md#tbannotator-es) | `bio_pathogens` |
| [tbannotator-mcp](bio_pathogens.md#tbannotator-mcp) | `bio_pathogens` |
| [tbannotator-upstream](bio_pathogens.md#tbannotator-upstream) | `bio_pathogens` |
| [tbmonitor-papers](bio_pathogens.md#tbmonitor-papers) | `bio_pathogens` |
| [thd](bio_pathogens.md#thd) | `bio_pathogens` |
| [theme-factory](redac.md#theme-factory) | `redac` |
| [tooluniverse-sequence-retrieval](bio_population_genetics.md#tooluniverse-sequence-retrieval) | `bio_population_genetics` |
| [tsne-hdbscan](bio_pathogens.md#tsne-hdbscan) | `bio_pathogens` |
| [wals](bio_population_genetics.md#wals) | `bio_population_genetics` |
| [worldclim-bioclim](bio_population_genetics.md#worldclim-bioclim) | `bio_population_genetics` |
| [yersinia-resources](bio_bacteria.md#yersinia-resources) | `bio_bacteria` |
| [zenodo-deposit](redac.md#zenodo-deposit) | `redac` |
