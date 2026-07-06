# Plugin `bio_population_genetics`

> Academic research toolkit for ancient and modern human population genetics, archaeological radiocarbon databases, paleoclimate reconstructions, historical migration corpora, and linguistic/cultural atlases. Bundles general-purpose phylogenetic, statistical, and literature-mining tools used by the Guyeux group (FEMTO-ST, University of Franche-Comte) for peer-reviewed scientific publications on human evolutionary history and eco-anthropology.

## Rôle dans un projet M. tuberculosis

Contexte hôte et outillage générique. Pour une étude M. tuberculosis, l'histoire des populations humaines, les migrations, la paléoclimatologie et l'archéologie éclairent la co-évolution hôte-pathogène et la dispersion des lignées du MTBC. Le plugin porte aussi les briques transversales (phylogénétique, statistiques, fouille de littérature) réutilisées par les analyses MTBC elles-mêmes.

Skills propres (canoniques) : **47** ; skills partagés utilisés (symlinks) : **7**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [aadr](#aadr) ; [abc-xgboost](#abc-xgboost) ; [amtdb](#amtdb) ; [atlantic-voyages](#atlantic-voyages) ; [bayesian-skyline](#bayesian-skyline) ; [beast2-phylogeography](#beast2-phylogeography) ; [bioc-pmc](#bioc-pmc) ; [biopython](#biopython) ; [bioskills](#bioskills) ; [bovine-genomics](#bovine-genomics) ; [card](#card) ; [clinical-trial-protocol-skill](#clinical-trial-protocol-skill) ; [d-place](#d-place) ; [domestication-pathways](#domestication-pathways) ; [esm-atlas-cli](#esm-atlas-cli) ; [europe-pmc](#europe-pmc) ; [geo-map](#geo-map) ; [glottolog](#glottolog) ; [indian-ocean-voyages](#indian-ocean-voyages) ; [iqtree-lsd2](#iqtree-lsd2) ; [itol](#itol) ; [migration-data](#migration-data) ; [modern-human-reference-panels](#modern-human-reference-panels) ; [neolithic-14c](#neolithic-14c) ; [nextflow-development](#nextflow-development) ; [nextstrain](#nextstrain) ; [ontologies](#ontologies) ; [openalex](#openalex) ; [orbis](#orbis) ; [owtrad](#owtrad) ; [p3k14c](#p3k14c) ; [paleoclimate](#paleoclimate) ; [pastml](#pastml) ; [pleiades](#pleiades) ; [pubmed-database](#pubmed-database) ; [pubtator](#pubtator) ; [pysam](#pysam) ; [rdkit](#rdkit) ; [read-scientific-pdf](#read-scientific-pdf) ; [scanpy](#scanpy) ; [scikit-bio](#scikit-bio) ; [seaborn](#seaborn) ; [seshat](#seshat) ; [slavevoyages](#slavevoyages) ; [tooluniverse-sequence-retrieval](#tooluniverse-sequence-retrieval) ; [wals](#wals) ; [worldclim-bioclim](#worldclim-bioclim)

### aadr

Query the Allen Ancient DNA Resource (AADR, Reich Lab), the reference curated compendium of >16,000 ancient and present-day human genomes in EIGENSTRAT format with rich archaeological/demographic metadata. Use for cross-referencing ancient human populations with MTBC lineage phylogeography, identifying individuals for which ancient TB DNA has also been published, and building population-level coevolutionary narratives

Compétences : contextualizing an MTBC lineage with ancient human population history, checking whether a region/period has ancient human genomes to correlate with a TB scenario, identifying skeletons that yielded both host and pathogen DNA, or writing an eco-anthropology / human, pathogen coevolution section for an article or seminar

### abc-xgboost

Approximate Bayesian Computation (ABC) accelerated by an XGBoost regressor/classifier with SHAP interpretation, to infer the selection coefficient and the demography x selection scenario behind an ancient allele-frequency trajectory. Built for the TYK2 P1104A question (Kerner et al. 2021, axe 2 of TYK2-MTBC-coevolution): is an observed decline reproducible, how strong was selection, and which summary statistics carry the signal. Simulates trajectories with a diploid Wright-Fisher model (dominance h: recessive for TYK2), trains XGBoost on the simulations, and compares XGBoost point estimates with acceptance-rejection ABC posteriors

Compétences : estimating the selection coefficient s on a human (or pathogen) allele from ancient DNA frequencies through time, comparing neutral vs weak vs strong selection scenarios, replicating or extending Kerner 2021 on TYK2 P1104A, or building a simulation-based-inference baseline before a full coalescent (msprime/SLiM) study

### amtdb

Query AmtDB, the Ancient mtDNA Database (Charles University Prague, Ehler et al. 2019), the reference open repository of ancient human mitochondrial genomes (2,548 samples in v1.009, late Paleolithic → Iron Age, mostly Eurasian) with rich metadata: maternal haplogroup, Y-chromosome haplogroup when available, archaeological culture, site, radiocarbon date, and mitochondrial pathological mutations. Lightweight, matrilineally focused complement to the AADR

Compétences : tracking maternal lineage histories of populations relevant to a TB phylogeographic argument, retrieving ancient mtDNA when AADR has no nuclear-genome record for a skeleton, building a Neolithic / Bronze Age maternal lineage map for a region, or correlating mitochondrial pathological mutations with ancient samples in paleopathology contexts

### atlantic-voyages

Aggregate and format historical Atlantic maritime voyage data for comparison with M. tuberculosis L5/L6 (M. africanum) and L4 sub-lineages phylogeography. Wraps six open-data sources : SlaveVoyages Trans-Atlantic (Eltis et al., Emory/Rice, 36 000 voyages, 12 M enslaved persons, 1514-1866), AfricanOrigins (~92 000 named enslaved persons with inferred ethnolinguistic origin), Liberated Africans Database (~250 000 individuals freed 1808-1862), Slavery, Abolition and Social Justice portal (Adam Matthew, voyage logs, letters, contracts), Intra-American Voyages (~11 000 inter-Caribbean and coastwise voyages 1626-1860), and Voyages to Liberty (post-1808 returnees from Sierra Leone, Liberia, Bahia)

Compétences : comparing L5/L6 sub-lineage dispersal to historical Atlantic trade routes, building origin-destination matrices for Mantel tests against MTBC pairwise distances, overlaying TMRCA estimates on documented voyage chronologies, preparing figures linking M ; africanum phylogeography to Senegambia, Gold Coast, Bight of Benin/Biafra, West-Central Africa or Southeast Africa departures, or correlating diaspora L5/L6 strains (USA, Brazil, Europe) with their probable West African source regions

### bayesian-skyline

Use BEAST Bayesian Skyline family methods, Bayesian Skyline Plot (BSP), Skyride, Skygrid, and Birth-Death Skyline (BDSKY), to reconstruct the effective population size Ne(t) or the effective reproduction number Re(t) of a pathogen through time from sampled genome sequences. These are the reference coalescent-based (and birth-death-based) phylodynamic methods for asking "how did this pathogen population grow or decline historically?" The key tool for connecting MTBC phylogenies to human demographic transitions, plague waves, and historical epidemic dynamics

Compétences : reconstructing the historical effective population size of an MTBC lineage, testing whether its expansion coincides with a human demographic transition (Neolithic, Bronze Age, Columbian contact…), estimating the effective reproduction number Re over time during an epidemic, or producing a skyline plot for a seminar slide on pathogen dynamics

### beast2-phylogeography

Use BEAST2 with its phylogeography packages (MASCOT, BASTA, and the classical DTA approach) for rigorous Bayesian molecular dating, tip-dating of ancient samples, and structured-coalescent phylogeographic inference. BEAST2 is the reference Bayesian framework for low- to mid-scale phylogenetics (10^1, 10^3 tips) where full posterior distributions on tree topology, divergence times, migration rates, and ancestral states are required, the gold standard when tip-dating ancient pathogens or testing specific demographic hypotheses

Compétences : dating ancient MTBC tips with full posterior confidence intervals, running a structured-coalescent phylogeography for a lineage of interest (MASCOT / BASTA), producing a time-scaled Bayesian tree for a seminar slide, testing competing demographic models, or when a Maximum-Likelihood / Nextstrain pipeline is not rigorous enough for a reviewer

### bioc-pmc

Use BioC-PMC, the PubMed Central Open Access + Author Manuscript subset in BioC format (NCBI/NLM). Provides ~3 million full-text biomedical articles with structured sections (title, abstract, body, figures, tables) in XML or JSON, optimised for NLP pipelines. The reference bulk-access corpus for biomedical text mining and the native substrate for "150k articles"-style MTBC text-mining workflows

Compétences : building a full-text corpus for MTBC or M ; bovis text mining, retrieving structured article sections for named-entity recognition / relation extraction, bulk-downloading PMC OA articles in a machine-readable format, feeding PubTator or a custom NER model with consistent input, or reproducing the "150k articles" TBannotator text-mining corpus from a public source ; For abstract-only (not full-text) TB workflows, prefer `tbmonitor-papers`: ~190k pre-indexed PubMed TB abstracts with MeSH/keywords as JSON, no bulk download needed ; BioC-PMC remains the right tool when full body text, figures, or tables are required

### biopython

Comprehensive guide for Biopython - the premier Python library for computational biology and bioinformatics. Use for DNA/RNA/protein sequence analysis, file I/O (FASTA, FASTQ, GenBank, PDB), sequence alignment, BLAST searches, phylogenetic analysis, structure analysis, and NCBI database access.

### bioskills

Installs 425 bioinformatics skills covering sequence analysis, RNA-seq, single-cell, variant calling, metagenomics, structural biology, and 56 more categories

Compétences : setting up bioinformatics capabilities or when a bioinformatics task requires specialized skills not yet installed

### bovine-genomics

Index of public-access cattle genomic resources for population genetics and phylogeographic studies: the 1000 Bull Genomes Project (~2,700 WGS cattle, ~90M variants), the Bovine HapMap Consortium (37,470 SNPs, 19 breeds), and the Bovine Genome Variation Database (BGVD, ~60M SNPs, 432 samples). Covers breed structure, the taurine vs indicine split, and the Neolithic cattle domestication signal

Compétences : building a cattle-side phylogeographic reference, retrieving bovine WGS or SNP data, comparing taurine and indicine breed distributions, or anchoring a study on the Neolithic cattle domestication event

### card

Query CARD 2.0 (Canadian Archaeological Radiocarbon Database), the reference compilation of archaeological radiocarbon dates for North America, ~50,000 dates plus an additional ~104,000 dates from the lower 48 US states, covering archaeological, paleontological, and geological contexts, with expanding coverage into Central and South America. Operated jointly by the Canadian Museum of History and the UBC Laboratory of Archaeology under Andrew Martindale. The Americas counterpart to EUROEVOL (Europe) and NERD (Near East) for chronological anchoring

Compétences : building a chronological backdrop for pre-Columbian and colonial-era narratives in the Americas, contextualizing the M ; pinnipedii pre-Columbian Andean host-jump (Bos2014, Vagene2022), extracting site-level dates for regions underrepresented in p3k14c, or cross-referencing North American ancient-DNA samples with a regional chronology

### clinical-trial-protocol-skill

Generate clinical trial protocols for medical devices or drugs. This skill should be used when users say "Create a clinical trial protocol", "Generate protocol for [device/drug]", "Help me design a clinical study", "Research similar trials for [intervention]", or when developing FDA submission documentation for investigational products.

### d-place

Query D-PLACE (Database of Places, Language, Culture and Environment), the reference open database of cultural, linguistic, and environmental traits for 1,400+ pre-industrial human societies. Provides cross-cultural variables from the Ethnographic Atlas, Binford Hunter-Gatherer dataset, and linked bioclimatic/ecological layers, all tied to Glottolog languages and (for some families) Bayesian language phylogenies

Compétences : building cultural/ecological context for the spread of a pathogen, testing whether a subsistence mode (pastoralism, agriculture, foraging) correlates with MTBC lineage distribution, controlling for phylogenetic non-independence in comparative cross-cultural analyses, or writing an eco-anthropology / bio-culture section in an article or seminar

### domestication-pathways

Aggregate and format domestication centres, dispersal routes, and Neolithic transition data for co-evolution studies with the M. tuberculosis complex. Wraps four families of open-data sources : zooarchaeology (ABMAP, AADR animal subset), archaeobotany (ADEMNES, BRAIN), ancient human DNA (AADR), and global radiocarbon (p3k14c, CONTEXT, AgriChange). Includes curated tables of origin centres (Fertile Crescent, Indus, Yangtze, Sahel, Mesoamerica, Andes, New Guinea, Ethiopia, Green Sahara, Amazonia), dispersal routes (LBK, Cardial, Bantu, Steppe, Austronesian, Lapita, Trans-Saharan, trans-Atlantic / Columbian Exchange), and timeline events linked to MTBC emergence and lineage dispersal

Compétences : building the co-evolutionary background of M ; bovis, M ; caprae, M ; orygis (animal hosts) ; cadrer l'émergence de M ; tuberculosis sensu stricto à partir d'un ancêtre M ; canettii-like via la sédentarisation néolithique ; relating MTBC TMRCA to documented agricultural transitions

### esm-atlas-cli

Academic research toolkit for the Guyeux group (FEMTO-ST) protein-evolution studies: a resilient Python client for the EvolutionaryScale × BioHub Protein Atlas API (https://biohub.ai/esm/protein/atlas/), which exposes ESMC sparse-autoencoder (SAE) features and ESMFold2 structures across 6.8 billion proteins. Provides lookup by content hash, similarity search by amino-acid sequence, SAE-feature interpretation, cluster metadata (Pfam annotation rate), and 3-D structure / thumbnail retrieval, with a disk cache and graceful fallback when the alpha API is degraded. Reusable across any peer-reviewed published research project that maps a protein sequence to a functional annotation: phylogenomic characterisation, codivergence studies, antimicrobial-resistance allele interpretation in the Guyeux group MTBC pipeline, or comparative protein analyses in population genetics

Compétences : a project step needs to translate a protein sequence into a biological function summary, retrieve a predicted structure, find ESM-space homologs, or compare two sequences (wild-type vs variant) via SAE feature differences

### europe-pmc

Query Europe PMC (EMBL-EBI), the European biomedical literature repository covering PubMed abstracts, PMC full text, preprints from 32+ servers (bioRxiv, medRxiv, Research Square, etc.), books, patents, clinical guidelines, and grants. Provides a REST API for search, full text retrieval, and pre-computed text-mining annotations (genes, diseases, chemicals, organisms, GO terms, accession numbers). The broadest open-access biomedical literature index, complementary to OpenAlex (bibliometric) and BioC-PMC (PMC OA only)

Compétences : searching biomedical literature including preprints, fetching full text of OA papers, retrieving pre-computed annotations in JSON or XML, building a TB corpus that includes preprints (bioRxiv / medRxiv), cross-linking publications to data accessions (ENA, UniProt, ChEMBL, PDB), or discovering related articles via citation graph ; For PubMed-only TB literature (no preprints), `tbmonitor-papers` is a faster alternative: ~190k pre-indexed TB abstracts queryable in sub-second SQL with MeSH and keywords as JSON ; Use Europe PMC when preprints, full-text, or non-PubMed sources are needed

### geo-map

Generate publication-quality geographic maps for MTBC studies, with proper cartographic projections, Natural Earth multi-resolution basemaps, scale bar, north arrow, graticule, and journal-ready styling. Supports choropleth, bubble, pie, GPS points (lat/lon), phylogeographic arcs, multi-panel atlases, and multi-layer composites

Compétences : illustrating geographic distribution of a lineage in an article, showing resistance rates by country on a map, plotting sampling sites from GPS coordinates, drawing phylogeographic migration flows, or producing figures for presentations or posters

### glottolog

Query Glottolog, the reference catalogue of the world's languages, language families, and dialects (8,238 languoids, 246 families, 183 isolates, 227 sign languages). Provides stable Glottocode identifiers, genealogical classification, geographic coordinates, macroarea, ISO 639-3 mapping, endangerment status, and 460k+ bibliographic references. Foundation layer for any cross-linguistic or biology-language coevolution analysis

Compétences : resolving a language name to a stable Glottocode, fetching the genealogical classification of a population's language, joining a genetic or pathogen dataset to linguistic metadata, building a language-family control for comparative analyses, or backing a D-PLACE / eco-anthropology workflow with authoritative language identifiers

### indian-ocean-voyages

Aggregate and format historical Indian Ocean maritime voyage data for comparison with M. tuberculosis L1 (Indo-Oceanic) phylogeography. Wraps four open-data sources : ESTA (Exploring Slave Trade in Asia, IISG Amsterdam, ~5 300 voyages, ~440 000 enslaved persons, 16th, 19th c.), GLOBALISE (Huygens/KNAW, 5 million pages of VOC archives, commodity and route metadata, 1602, 1799), CLIWOC (287 114 European logbooks, 1750, 1854, daily geocoded ship positions), and SlaveVoyages Indian Ocean subset (~1 000 voyages stopping in East Africa / Indian Ocean)

Compétences : comparing L1 sub-lineage dispersal to historical maritime routes in the Indian Ocean, building origin-destination matrices for Mantel tests against MTBC pairwise distances, overlaying TMRCA estimates on documented voyage chronologies, preparing figures linking M ; tuberculosis L1 phylogeography to VOC trade networks, French Île de France/Bourbon slave trade, or Omani-Swahili commerce

### iqtree-lsd2

Use IQ-TREE 2 with its integrated LSD2 (Least-Squares Dating 2) for fast Maximum-Likelihood phylogenetic inference plus molecular dating, the pragmatic alternative to BEAST2 when you need a time-scaled tree on 10^3, 10^5 tips in minutes to hours rather than days. IQ-TREE handles model selection (ModelFinder), ultrafast bootstrap (UFBoot2), and tree search; LSD2 converts branch lengths to calendar time using tip dates via a least-squares criterion. The reference pipeline for large-scale bacterial / MTBC phylogenetics where BEAST2 does not scale

Compétences : building a maximum-likelihood MTBC tree with full model selection and bootstrap support, dating the tree via tip dates (LSD2) as a fast alternative to BEAST2 tip-dating, scaling to thousands of MTBC genomes, generating a starting tree for a later BEAST2 refinement, or producing quick-turnaround time-scaled trees for exploratory analysis

### itol

Upload, annotate, and export publication-quality phylogenetic tree figures via iTOL (Interactive Tree Of Life) using the bundled itolapi pipeline (scripts/itol_pipeline.py). Turns a Newick/Nexus tree plus annotation tracks (lineage colour ranges, branch colours, bootstrap symbols, datasets) into SVG/PDF/PNG figures with presets tuned for an article, a supplement, a presentation, or a poster, plus batch export and comparison mode

Compétences : producing a final MTBC lineage tree figure for a manuscript or a slide, rendering an annotated RAxML/IQ-TREE tree with lineage colour ranges and bootstrap support, exporting the same tree in several formats/presets at once, or scripting iTOL uploads and exports instead of clicking through the web UI

### migration-data

Aggregate and format human migration data for comparison with MTBC patterns. SlaveVoyages, UN migration stock, HGDP genetic structure, ancient DNA events, WHO TB burden, and curated historical migration timeline

Compétences : comparing MTBC lineage dispersal to human movements, building migration matrices for Mantel tests, overlaying TMRCA with migration chronology, preparing figures linking bacterial and human history

### modern-human-reference-panels

Index of open modern human genome reference panels, the 1000 Genomes Project (1kGP, 2,504 individuals in 26 populations), the Simons Genome Diversity Project (SGDP, 300 high-coverage individuals from 142 populations), the Human Genome Diversity Project (HGDP, 929 individuals from 54 populations, now sequenced to high coverage), and gnomAD. The canonical modern comparators for any ADMIXTOOLS / qpAdm / f-statistic analysis on ancient human genomes from AADR, and the reference populations for H. pylori-style phylogeographic host comparisons

Compétences : setting up an ADMIXTOOLS run on an AADR cohort (modern outgroups and sources), building a PCA background for ancient samples, cross-referencing a modern human population against a pathogen phylogeography, or checking allele frequency of a variant across global populations

### neolithic-14c

Index of regional radiocarbon databases for the Neolithic and adjacent periods, EUROEVOL (European Neolithic, 14,053 dates from 4,757 sites, Shennan/Manning et al. UCL), NERD (Near East, 11,072 dates from 1,027 sites, Palmisano et al.), plus RADON (Central Europe), NeoNet (Mediterranean), and the Radiocarbon Palaeolithic Europe Database (KU Leuven). Together they give continuous ¹⁴C coverage from the primary Near Eastern domestication centre through the secondary European expansion, the ideal substrate for building demographic-transition and farming-expansion arguments for MTBC / M. bovis narratives

Compétences : building a Neolithic demographic transition argument for the rise of human-adapted MTBC, mapping the arrival of farming and animal husbandry across Europe in relation to a TB phylogeny, producing summed probability distribution (SPD) plots of population dynamics, or complementing the global p3k14c dataset with higher- resolution regional data

### nextflow-development

Run nf-core bioinformatics pipelines (rnaseq, sarek, atacseq) on sequencing data

Compétences : analyzing RNA-seq, WGS/WES, or ATAC-seq data, either local FASTQs or public datasets from GEO/SRA ; Triggers on nf-core, Nextflow, FASTQ analysis, variant calling, gene expression, differential expression, GEO reanalysis, GSE/GSM/SRR accessions, or samplesheet creation

### nextstrain

Use Nextstrain (Augur + Auspice + TreeTime + Nextclade) for real-time phylogeographic analysis and interactive visualization of pathogen evolution at scale. Augur is the Python bioinformatics toolkit that chains filtering, alignment, tree building, time-scaling, ancestral reconstruction, and discrete trait (geography) inference into a reproducible pipeline, producing JSON for the Auspice web viewer. Used historically for Ebola, Zika, Influenza, SARS-CoV-2, MTBC, and many other pathogens

Compétences : producing a time-scaled phylogeography for an MTBC lineage or dataset of 10^2, 10^5 genomes, building an interactive Auspice visualization for a seminar slide or a collaborator review, inferring most-likely transmission events between countries, dating ancestral nodes with TreeTime, or authoring a reproducible Snakemake build from a FASTA + metadata TSV pair

### ontologies

Index and access helper for the Open Biological and Biomedical Ontology Foundry (OBO Foundry, 150+ active ontologies) and its anchor resource, the NCBI Taxonomy. Provides canonical normalisation vocabularies for species and strains (NCBITaxon / LPSN), diseases (DOID), infectious disease concepts (IDO), environments (ENVO), chemicals (ChEBI), gazetteer places (GAZ), and host, microbiome interactions (OHMI). The glue that makes metadata from `aadr`, `enterobase`, `spaam-ancient-metagenome-dir`, `bacdive`, `pubtator`, and the anthropology-layer skills interoperable

Compétences : normalizing a free-text species / strain / disease / host / environment / place field to a canonical identifier, adding ontology-coded metadata to a manuscript or dataset, checking whether a term is already in an existing OBO ontology, or producing Linked-Data-compliant annotations for a publication's supplementary material

### openalex

Query OpenAlex, the fully open scholarly knowledge graph (307M works, 118M authors, 124k institutions, 281k sources, 65k concepts, 4.5k topics, April 2026 snapshot) published by OurResearch as the successor to Microsoft Academic Graph. Free REST API with email-based polite pool, CC0 metadata, and bulk dumps. The reference bibliometric substrate for lit-reviews, co-author-network analysis, institution mapping, and concept-based discovery, complementary to PubMed/Europe PMC (which have biomedical focus) and to Google Scholar (which has no API)

Compétences : building a literature review from a topic query, mapping co-authorship networks around an MTBC lineage or a paper, listing all publications of a given lab or researcher, resolving institution IDs across publications, computing citation metrics without institutional Web of Science access, or enriching a manuscript bibliography with concept / topic tags

### orbis

Query ORBIS, the Stanford Geospatial Network Model of the Roman World (Scheidel & Meeks, ~200 CE). Provides a multimodal transport network of 678 sites and 1,104 links (road, river, sea) with realistic travel-time, financial-cost, and seasonal-variation models. The authoritative source for quantitative pre-modern Mediterranean connectivity

Compétences : reasoning about the spread of MTBC (or any bacterial pathogen) through the Roman Empire and Mediterranean basin, building a Roman-era dispersal hypothesis for an L4 sublineage, modeling connectivity between sites with ancient pathogen DNA (Justinian plague, Antonine plague), or anchoring a narrative on pre-modern mobility at concrete travel-cost scales

### owtrad

Query OWTRAD (Old World Trade Routes Project, T.M. Ciolek, Australian National University, 1999, present), the reference community-curated GIS archive of land, river and maritime trade, pilgrimage, military, and postal routes of Eurasia and Africa from ~10,000 BCE to ~1820 CE. Includes the Silk Road, Spice Route, Amber Route, Salt Route, and a gazetteer of 3,130 unique places plus catalogues of caravanserais, bridges, and forts

Compétences : building a Silk Road or caravan-route narrative for MTBC lineages (especially L2 Beijing and L3 CAS in Central Asia), overlaying a TB or Y ; pestis phylogeny on historical transport corridors, identifying caravanserais / stopping places as candidate mixing sites for human + animal MTBC, or assembling a pre-modern mobility context for a seminar slide

### p3k14c

Query the p3k14c global archaeological radiocarbon database (Bird et al. 2022, 180,070 ¹⁴C dates) to anchor MTBC lineage emergence in archaeological chronologies, especially animal domestication hotspots (cattle → M. bovis, caprines → M. caprae) and Neolithic sedentarization

Compétences : dating the emergence of a zoonotic MTBC lineage, building a Neolithic/domestication narrative for an article, correlating TMRCA estimates with archaeological cultural periods, or identifying archaeological sites near modern TB strain sampling locations

### paleoclimate

Index of open paleoclimate reconstructions for coupling pathogen phylogeography and historical epidemiology with past climate variability. Covers PAGES 2k (the reference multi-proxy global reconstruction of the last 2,000 years), NOAA Paleoclimatology (the primary WDS archive), Greenland and Antarctic ice cores (GISP2, NGRIP, EPICA), and WorldClim / CHELSA paleo bioclimatic reconstructions (LGM, Mid-Holocene). The temperature-and-climate layer that pairs with p3k14c / neolithic-14c / card to build eco-anthropological narratives

Compétences : testing whether a MTBC lineage expansion coincides with a climatic warm/cold interval, correlating the Justinian plague with the Late Antique Little Ice Age, framing the Neolithic demographic transition in the context of the Holocene Climatic Optimum, or extracting temperature / precipitation time series for a given region and period

### pastml

Use PastML (Ishikawa, Zhukova, Iwasaki, Gascuel, Institut Pasteur) for fast Maximum-Likelihood Ancestral Character Reconstruction (ACR) on rooted phylogenetic trees, with built-in compressed-tree visualisation. PastML reconstructs the most likely values of discrete characters (geographic location, host, drug-resistance phenotype, lineage, etc.) at every internal node of a tree, then collapses the tree into an interactive HTML "compressed map" that surfaces only the regions of state change. Designed to handle 10^4, 10^5-tip trees

Compétences : reconstructing the geographic origin of an MTBC sublineage, inferring ancestral host-jumps for zoonotic Mycobacterium ecotypes, visualising drug-resistance emergence on a TB tree, producing a compressed-tree HTML for a slide, or any task that maps a discrete trait onto an existing phylogeny without rebuilding the tree

### pleiades

Query Pleiades, the community-built gazetteer and graph of ancient places (NYU ISAW + UNC AWMC), derived from the Barrington Atlas of the Greek and Roman World. Contains 42,000+ places with stable URIs, geocoded coordinates, time-period coding (Archaic → Late Antique), feature types (settlement, villa, fort, road, cemetery, temple, etc.), and an explicit graph of place-to-place connections. The reference resolver for any ancient toponym in the Mediterranean and circum-Mediterranean

Compétences : resolving an ancient place name to a stable identifier and coordinates, geocoding historical metadata for ancient TB / Y ; pestis samples, building a chronologically filtered map of settlements relevant to a phylogeographic argument, or chaining ancient toponyms to ORBIS (transport) and OWTRAD (trade routes) via stable IDs

### pubmed-database

Direct REST API access to PubMed. Advanced Boolean/MeSH queries, E-utilities API, batch processing, citation management. For Python workflows, prefer biopython (Bio.Entrez). For TB/MTBC literature specifically, prefer the `tbmonitor-papers` skill (sub-second SQL on a pre-indexed corpus of ~190k PubMed TB papers with MeSH/keywords/authors as queryable JSON)

Compétences : for non-TB topics, direct HTTP/REST work, or custom API implementations

### pubtator

Query PubTator 3.0 / PubTator Central (NCBI BioNLP), the reference service for pre-computed biomedical entity annotations on PubMed abstracts and PMC full-text articles. Uses state-of-the-art NER (AIONER) to tag six entity types: genes/proteins, diseases, chemicals, species, genetic variants, and cell lines. Optional relation extraction in v3. Saves you from training your own biomedical NER for any MTBC / TB text-mining project

Compétences : pre-annotating MTBC abstracts or full-text articles with standardised biomedical entities, extracting mentions of specific genes/variants/drugs from a TB paper, building a gene-disease association graph from the literature, or accelerating a text-mining pipeline that would otherwise require training BioBERT / PubMedBERT on your own corpus ; For TB-only corpora, build the abstract list with `tbmonitor-papers` (PubMed TB pre-filtered, ~190k papers, MeSH/keywords as JSON) before passing PMIDs to PubTator, this is faster than re-querying PubMed directly

### pysam

Python module for reading, manipulating and writing genomic alignment formats (SAM/BAM/CRAM) and variant files (VCF/BCF). Wrapper for htslib.

### rdkit

Open-source cheminformatics and machine learning toolkit for drug discovery, molecular manipulation, and chemical property calculation. RDKit handles SMILES, molecular fingerprints, substructure searching, 3D conformer generation, pharmacophore modeling, and QSAR

Compétences : working with chemical structures, drug-like properties, molecular similarity, virtual screening, or computational chemistry workflows

### read-scientific-pdf

Extraction rapide du texte d'un PDF scientifique (articles, theses, rapports) via pdftotext, markitdown ou pdfminer, puis relecture du fichier texte intermediaire avec Read. Pipeline plus efficace que la lecture multimodale native pour les documents longs (>10 pages), les PDFs a colonnes multiples, les tableaux complexes, et la lecture en lot pour revues de litterature

Compétences : PDF scientifique long, article avec colonnes ou tableaux complexes, lecture sequentielle d'un corpus pour une revue, PDF scanne necessitant OCR, ou lorsque la lecture native d'un PDF retourne un resultat partiel ou inattendu

### scanpy

Scalable toolkit for analyzing single-cell gene expression data. Built on top of Anndata, focusing on clustering, trajectory inference, and visualization.

### scikit-bio

Library for bioinformatics and community ecology statistics. Provides data structures and algorithms for sequences, alignments, phylogenetics, and diversity analysis. Essential for microbiome research and ecological data science. Use for alpha/beta diversity metrics, ordination (PCoA), phylogenetic trees, sequence manipulation (DNA/RNA/Protein), distance matrices, PERMANOVA, and community ecology analysis.

### seaborn

A Python data visualization library based on matplotlib. It provides a high-level interface for drawing attractive and informative statistical graphics. Great for exploring relationships between variables and visualizing distributions. Use for statistical data visualization, exploratory data analysis (EDA), relationship plots, distribution plots, categorical comparisons, regression visualization, heatmaps, cluster maps, and creating publication-quality statistical graphics from Pandas DataFrames.

### seshat

Query Seshat: Global History Databank, the reference quantitative historical database of ~400 polities from the Neolithic to ~1900 CE, covering social complexity, warfare, religion, agriculture, and crisis/collapse events. Provides the polity-level quantitative scaffold needed to test hypotheses about how state formation, population density, urbanization, and crises shaped the persistence and dispersal of human-adapted pathogens

Compétences : building a quantitative density/urbanization argument for human-adapted MTBC persistence, correlating pathogen emergence with polity crises or collapses (CrisisDB), framing the rise of a bacterial lineage in a specific state formation context, or writing a cliodynamics-style section on the co-evolution of pathogens and social complexity

### slavevoyages

Query slavevoyages.org (36k+ voyages, 1514-1866) to build phylogeographic scenarios for MTBC lineage articles. Correlates TB lineage distributions with trans-Atlantic trade routes, TMRCA estimates, and historical migration events

Compétences : explaining New World presence of African TB lineages (L5, L6, L4), building a dispersal hypothesis for a lineage, or correlating TMRCA with historical population movements (Gold Coast → Americas, Bight of Benin, etc.)

### tooluniverse-sequence-retrieval

Retrieves biological sequences (DNA, RNA, protein) from NCBI and ENA with gene disambiguation, accession type handling, and comprehensive sequence profiles. Creates detailed reports with sequence metadata, cross-database references, and download options

Compétences : users need nucleotide sequences, protein sequences, genome data, or mention GenBank, RefSeq, EMBL accessions

### wals

Query WALS, the World Atlas of Language Structures (Dryer & Haspelmath eds., Max Planck Institute), the reference open database of typological features (phonology, morphology, syntax, word order, lexicon) for ~3,500 languages worldwide. Provides 192 typological parameters with ~76,000 codings, all keyed to Glottocodes for joining with the rest of the linguistic-anthropology constellation

Compétences : testing whether a linguistic typological feature correlates with the geographic distribution of an MTBC lineage, building a language-typology covariate for cross-cultural eco-anthropology analyses, controlling for typological similarity in comparative studies, or producing a typological profile of populations relevant to a phylogeographic narrative

### worldclim-bioclim

Use WorldClim 2.1 and CHELSA v2.1, the two reference high-resolution global bioclimatic raster datasets (19 BIO variables at up to 1 km resolution, present-day and paleo versions for LGM and Mid-Holocene). The canonical substrate for ecological niche modelling of pathogens, climate-at-point extraction for TB sampling locations, and high-resolution climate overlays on phylogeographic maps. Complements paleoclimate time-series reconstructions with the spatial raster view

Compétences : extracting bioclimatic variables at modern or ancient TB sampling sites, modelling the climatic niche of an MTBC lineage, comparing niches of M ; bovis vs M ; caprae vs M ; tuberculosis, producing climate overlay layers for a phylogeographic map, or computing niche overlap statistics between pathogen ecotypes

## Skills partagés (via symlink)

Documentés sur la page de leur plugin d'origine.

| Skill | Origine |
|-------|---------|
| [claim-check](redac.md#claim-check) | `redac` |
| [create-viz](ops.md#create-viz) | `ops` |
| [lit-review](redac.md#lit-review) | `redac` |
| [reviewer-response](redac.md#reviewer-response) | `redac` |
| [scientific-problem-selection](ia.md#scientific-problem-selection) | `ia` |
| [scikit-learn](ia.md#scikit-learn) | `ia` |
| [statsmodels](ia.md#statsmodels) | `ia` |

