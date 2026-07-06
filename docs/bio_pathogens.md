# Plugin `bio_pathogens`

> Academic research toolkit for computational genomic studies of bacterial pathogens, focused on Mycobacterium tuberculosis complex (MTBC) phylogenomics, comparative genomics, and public-health surveillance literature. Used by the Guyeux group (FEMTO-ST, University of Franche-Comte) for peer-reviewed scientific publications on pathogen evolution and host-pathogen co-evolution.

## Rôle dans un projet M. tuberculosis

Cœur du dispositif. Rassemble les skills qui touchent directement le complexe Mycobacterium tuberculosis (MTBC) et les pathogènes apparentés : accès aux génomes de référence et aux isolats de recherche publiés, fréquences alléliques de résistance aux antituberculeux telles que rapportées dans la littérature évaluée par des pairs, assignation de lignées, bases de données génomiques spécialisées. C'est le plugin qu'on active quand le travail porte effectivement sur M. tuberculosis.

Skills propres (canoniques) : **55** ; skills partagés utilisés (symlinks) : **37**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [active-site-check](#active-site-check) ; [ancestral-reconstruction](#ancestral-reconstruction) ; [atlas-add-lineage](#atlas-add-lineage) ; [bacdive](#bacdive) ; [bdd-bridge](#bdd-bridge) ; [beast2-dating](#beast2-dating) ; [clade-finder](#clade-finder) ; [coevolution](#coevolution) ; [convergent-evolution](#convergent-evolution) ; [denovo-content-qc](#denovo-content-qc) ; [enterobase](#enterobase) ; [fetch-tbannotator](#fetch-tbannotator) ; [helicobacter-pylori-phylogeography](#helicobacter-pylori-phylogeography) ; [host-pathogen-pair](#host-pathogen-pair) ; [lineage-comparison](#lineage-comparison) ; [lineage-mdl](#lineage-mdl) ; [mbovis](#mbovis) ; [mk-ascertainment](#mk-ascertainment) ; [molecular-clock](#molecular-clock) ; [mtbc-atlas](#mtbc-atlas) ; [mtbc-bilan](#mtbc-bilan) ; [mtbc-deepen](#mtbc-deepen) ; [mtbc-gene-function](#mtbc-gene-function) ; [mtbc-gene-network](#mtbc-gene-network) ; [mtbc-lineages](#mtbc-lineages) ; [mtbc-mutation-impact](#mtbc-mutation-impact) ; [mtbc-pathway-explain](#mtbc-pathway-explain) ; [mtbc-reboot](#mtbc-reboot) ; [mycobacterium-leprae](#mycobacterium-leprae) ; [ncbi-pathogen-detection](#ncbi-pathogen-detection) ; [pangenome-enrichment](#pangenome-enrichment) ; [pathogens-portal](#pathogens-portal) ; [pectinated-subclade-mining](#pectinated-subclade-mining) ; [phylogeography](#phylogeography) ; [raxml](#raxml) ; [resistance-catalogue](#resistance-catalogue) ; [resistance-discovery](#resistance-discovery) ; [resistance-explain](#resistance-explain) ; [resistance-predict](#resistance-predict) ; [resistance-profiler](#resistance-profiler) ; [sitvitweb](#sitvitweb) ; [snp-distance](#snp-distance) ; [spaam-ancient-metagenome-dir](#spaam-ancient-metagenome-dir) ; [spaam-community](#spaam-community) ; [spdi-annotation](#spdi-annotation) ; [species-id](#species-id) ; [sra-geolocate](#sra-geolocate) ; [strain-qc](#strain-qc) ; [string-db](#string-db) ; [tb-cli](#tb-cli) ; [tbannotator-mcp](#tbannotator-mcp) ; [tbmonitor-papers](#tbmonitor-papers) ; [thd](#thd) ; [triangulate-route](#triangulate-route) ; [tsne-hdbscan](#tsne-hdbscan)

### active-site-check

Academic research toolkit (Guyeux group, FEMTO-ST). Validation d'annotation fonctionnelle d'enzymes pour des publications de genomique comparative revues par les pairs. Valide une requalification d'enzyme « same fold → enzyme active » en vérifiant que les RÉSIDUS CATALYTIQUES de l'enzyme M-CSA (Mechanism and Catalytic Site Atlas, EBI) appariée par Foldseek sont bien alignés ET conservés dans la protéine requête. C'est la brique de rigueur qui manque à un transfert de fonction purement structural (Foldseek/GO) : un repli partagé n'implique pas un site actif fonctionnel

Compétences : un gène « hypothetical »/dark du MTBC a un hit Foldseek vers une enzyme connue et on veut trancher « enzyme active vs simple homologie de repli » avant d'écrire une fonction dans une fiche (projets annotation_mtbc, TA_repertoire, dark_enzymes) ; quand on annote un protéome bactérien par structure et qu'il faut graduer la confiance des requalifications enzymatiques ; quand un reviewer demande des preuves de site actif ; Déclencheurs : « est-ce une enzyme active ou juste le même repli », « résidus catalytiques », « site actif conservé », « M-CSA », « valider un hit Foldseek enzyme 

### ancestral-reconstruction

Academic research toolkit for the Guyeux group (FEMTO-ST, University of Franche-Comte). Ancestral-state reconstruction on published-research MTBC phylogenies for peer-reviewed phylogeographic publications. Reconstruct ancestral geographic states on MTBC phylogenies. Parsimony (Fitch), ML marginal posteriors (MPPA), stochastic mapping, BEAST DTA XML generation, and iTOL migration arrow export

Compétences : identifying when and how many times a lineage migrated between regions, comparing migration patterns to human movements, annotating phylogenies with ancestral locations, preparing BEAST discrete trait analyses

### atlas-add-lineage

Academic research toolkit for the Guyeux group (FEMTO-ST) MTBC Atlas: scaffold a new lineage page (`content/lineages/<id>/{meta.yaml, en.md, fr.md}`) from a peer-reviewed manuscript or laboratory notebook of a Mycobacterium tuberculosis complex sub-lineage characterisation project. Reads the source project (typically `mtbc/<id>/article/main.tex` + `mtbc/<id>/data/strains.csv`) and produces a draft Atlas page filled with structured fields (phylogeny, dating, selection, codivergence, epidemiology, host, methods, references) plus a prose synthesis. Then runs `ingest.add_lineage` to push it into the Atlas database. Aimed at published research scaling: every characterised lineage gets a fiche without waiting for journal peer-review

Compétences : a sub-lineage characterisation has reached publishable maturity in a `mtbc/<id>/` project and should be exposed on the Atlas ; also when refreshing an existing fiche from an updated manuscript

### bacdive

Academic research database client (Guyeux group, FEMTO-ST). Queries the peer-reviewed BacDive strain metadatabase for published-research isolates. Query BacDive, the DSMZ Bacterial Diversity Metadatabase, the world's largest structured repository of bacterial and archaeal strain information. Covers 97,000+ strains with 2.6 million data points across 1,000+ fields: taxonomy, morphology, physiology, metabolism, cultivation, isolation source, biosafety level, antibiotic susceptibility, fatty acid profiles, and API® test results. The canonical resource for phenotypic and ecological metadata of type strains

Compétences : retrieving phenotypic data for a bacterial species relevant to your TB / historical pathogen work, looking up cultivation conditions, checking biosafety level, finding type-strain reference for a taxon, or enriching a genomic analysis with phenotypic context

### bdd-bridge

Academic research toolkit. Read-only bridge over the local curated MTBC research database (bdd/actuelle/, Guyeux group, FEMTO-ST, University of Franche-Comte), a snapshot of published-research isolates stored as per-strain SPDI variant lists. Exposes two dependency-free CLIs, callable identically from Claude Code and from a compute agent, so that lineage bookkeeping and phylogenetic inference run the same way in both. `bdd_query.py` lists clades, reads per-strain QC, builds binary SNP matrices, and extracts clade synapomorphies; `phylo_job.py` builds a binary alignment and runs or submits RAxML-NG (BIN+G) locally or as a portable SLURM package

Compétences : reporting clade-level strain counts or QC for a peer-reviewed phylogenomics manuscript, extracting synapomorphies to define a published sub-lineage, or building a scientific-publication phylogeny for an MTBC clade from the local research database

### beast2-dating

Academic research toolkit for Bayesian molecular dating of Mycobacterium tuberculosis complex (MTBC) phylogenies with BEAST2. Generates correct BEAST2 XML for BINARY SNP alignments (presence/absence 0/1), the format produced by the Guyeux group (FEMTO-ST) TB pipeline, and runs BEAST2 headless. Fixes the two failures that make BEAST2 runs on MTBC binary data silently fail to converge. For peer-reviewed phylogenomic research.

### clade-finder

Recherche de clades et sous-populations dans une lignee MTBC. Construit des vecteurs de features par SRA (pan-SPDI, positions IS, RD) a partir des fichiers report.json ou spdi.txt du repertoire bdd/actuelle/L<x>/. Applique t-SNE + HDBSCAN et produit un PNG haute resolution pour visualiser les sous-lignees potentielles. Une fois un cluster identifie, verifier dans `tbmonitor-papers` (~190k papiers PubMed TB pre-indexes) s'il a deja ete decrit dans la litterature avant de proposer une nouvelle sous-lignee

Compétences : exploring sub-lineage structure within a lineage directory, looking for population clusters, checking if a lineage should be split ; Pour la phase post-decouverte (extraction iterative pectinee des sous-clades apres avoir construit un arbre RAxML focalise et identifie visuellement les candidats), utiliser le skill complementaire `pectinated-subclade-mining` qui formalise le filtre PER-POOL strict de synapomorphismes SPDI

### coevolution

Academic research toolkit for the Guyeux group (FEMTO-ST, University of Franche-Comte). Statistical co-divergence tests on published-research MTBC data for peer-reviewed publications. Statistical tests for MTBC-human co-divergence and geographic structure. Mantel test, partial Mantel, isolation by distance, PACo (Procrustean Approach to Cophylogeny), FST (Weir & Cockerham), and AMOVA

Compétences : testing whether MTBC genetic diversity correlates with geographic distance, comparing bacterial and human population structure, quantifying differentiation between MTBC populations from different countries or regions

### convergent-evolution

Academic research toolkit for the Guyeux group (FEMTO-ST, University of Franche-Comte). Detects convergent evolution across MTBC lineages for peer-reviewed phylogenomic publications. Detect convergent/parallel evolution across MTBC lineages. Identify genes mutated independently in multiple lineages, enrichment analysis for PE/PPE, ESX, PKS/PDIM pathways. To check whether a candidate convergent gene has prior reports in the literature (and to cite them in the discussion), pair this skill with `tbmonitor-papers` (~190k PubMed TB abstracts, sub-second SQL)

Compétences : comparing mutation patterns between animal and human lineages, identifying genes under convergent selection, analyzing host adaptation signatures, studying PE/PPE or ESX system evolution

### denovo-content-qc

Academic research toolkit (Guyeux group, FEMTO-ST) pour caractériser et CONTRÔLER le contenu génomique "absent de H37Rv" d'une lignée/sous-lignée MTBC, reconstruit par assemblage de novo des reads NON mappés sur H37Rv. Répond à la question récurrente des projets de caractérisation de lignées basales/rares (L8, L9, L10, écotypes animaux) : un contig assemblé est-il un vrai module ancestral que la lignée a gardé, un accessoire de pangénome propre à une souche, ou un simple CONTAMINANT ? Trois outils complémentaires : (1) contamination_filter = re-mappe chaque contig sur le génome FERMÉ de la lignée (verdict cœur / pangénome / singleton-à-arbitrer / bas-cov) ; (2) pangenome_map = pangénome par mapping (breadth, fenêtres à couverture 0, fraction accessoire, GC par souche) ; (3) island_distribution = teste la SPÉCIFICITÉ d'un îlot par BLAST contre un panel de génomes de référence (H37Rv, M. bovis animale, M. leprae outgroup). Corrige deux pièges documentés : "absent de H37Rv" != "spécifique de la lignée" (M. bovis peut l'avoir), et "absent du génome fermé d'UNE souche" != "contaminant" (pangénome)

Compétences : on a assemblé de novo les reads non-mappés-H37Rv d'une lignée et on veut trier vrai-contenu vs contaminant, mesurer l'accessoire propre d'une souche, ou prouver qu'un "îlot spécifique" l'est vraiment (vs conservé ailleurs) avant de l'écrire dans un manuscrit ; Complémentaire de strain-qc (QC souche), species-id (ID d'espèce d'un contaminant), pangenome-enrichment (pangénome sur génomes complets)

### enterobase

Academic research database client (Guyeux group, FEMTO-ST). Queries the peer-reviewed EnteroBase resource for published-research genomes and historical-epidemiology analyses only. Query EnteroBase (Warwick / Achtman group), the reference genome database and cgMLST/HierCC platform for Salmonella, Escherichia, Yersinia, Clostridioides, Helicobacter, Vibrio, and Moraxella. Central resource for Yersinia pestis historical phylogeny (plague, Silk Road, Black Death), Vibrio cholerae pandemics, and bacterial epidemiology at genomic scale

Compétences : building historical narratives around non-MTBC bacterial pathogens, correlating Yersinia pestis lineages with Silk Road or Black Death, researching cholera pandemics (V ; cholerae), Helicobacter pylori as a proxy of human migrations, or transposing the TBannotator methodology to another enteric pathogen

### fetch-tbannotator

Fetch report.json and generate spdi.txt for MTBC strains from the TBannotator server

Compétences : populating BDD directories with missing genomic data for strains already in the TBannotator database

### helicobacter-pylori-phylogeography

Reference framework for Helicobacter pylori phylogeography as a proxy for human migrations, the paradigmatic host-pathogen coevolution case (Linz et al. 2007 Nature; Moodley et al. 2009/2012 Science; Maixner et al. 2016 Science Iceman study). Documents the seven H. pylori populations, their geographic distributions, and the methodological template for transposing the approach to Mycobacterium tuberculosis. Essential for positioning MTBC phylogeography within the broader "pathogens as historians" paradigm

Compétences : framing the seminar narrative of "pathogens racing their hosts" with a canonical precedent, building a comparative slide on H ; pylori vs M ; tuberculosis phylogeography, transposing Linz-style methodology to MTBC, or referencing the classical anchors of the host-pathogen coevolution literature for an MNHN / Paul Verdu jury

### host-pathogen-pair

Academic eco-anthropology research toolkit (Guyeux group, FEMTO-ST). Generates geo-temporal co-occurrence tables of ancient host, ancient microorganism pairs from two published open-science research corpora: SPAAM AncientMetagenomeDir (ancient microbial genomics, covering *Mycobacterium*, *Yersinia pestis*, *Salmonella*, etc.) and the AADR ancient human genome catalogue (Reich Lab, v66, 16,000+ individuals). Output: a TSV of candidate research pairs ranked by Haversine distance and temporal overlap, plus a per-project summary for the top co-located human groups. Used by the Guyeux group to plan peer-reviewed eco-anthropology host, microorganism co-evolution studies, to document data availability for a given research question, or to demonstrate data absence (a publishable negative finding)

Compétences : planifier un projet de recherche sur la co-evolution hote, microorganisme, valider les paires disponibles pour une region/periode donnee, preparer un seminaire ou une candidature academique, ou documenter l'absence de paires (cas negatif valorisable dans une publication scientifique)

### lineage-comparison

Statistical comparison between MTBC lineages or sub-lineages. Fisher exact test, chi-squared, binomial exact CI, FDR correction, odds ratios, and publication-ready comparison tables

Compétences : comparing resistance rates between lineages, testing if a trait is significantly associated with a sub-lineage, producing statistical tables for articles, computing confidence intervals

### lineage-mdl

Definir les sous-lignees d'une lignee MTBC (ou bacterie clonale) par OPTIMISATION MULTICRITERES SOUS CONTRAINTES, le bruit traite en amont. Remplace les seuils heuristiques (GAIN constant, longueur de branche) par une formulation principielle : (A) DEBRUITAGE (masque homoplasie/resistance, QC compte SPDI + RD4, de003replication a rayon SNP, chimeres) ; (B) CONTRAINTES de faisabilite = un clade ssi >=MINSYN synapomorphies PROPRES multi-signal (SNP union RD union IS6110, exclusivite per-pool + globale) ET >=5 souches ET monophylie (polytomies emergent) ; (C) OBJECTIF de selection de modele MDL = maximiser la log-vraisemblance conditionnelle -n*H(pays|lignee) moins lambda par lignee (parcimonie ; single-BioProject penalise), optimise par un DP bottom-up avec REPLI dans le grade des enfants geo-redondants ; balayage de lambda -> front de Pareto -> coude. Flague les terminaux a forte etendue spatio-temporelle ou divergence IS comme candidats a re-investigation relachee

Compétences : on veut une taxonomie de sous-lignees reproductible et defendable pour des etudes evolutives (phylogeographie, datation), pas un decoupage arbitraire ; quand un clade est dense/clonal et sur-sequence (un seuil constant sur/sous-resout) ; quand on veut que la granularite soit PILOTEE par la biologie (coherence geo/hote) sous garantie de support synapomorphique ; NE PAS confondre l'ARBRE (synapo+monophylie = definit les clades) avec les CLUSTERS de distance (servent a dedupliquer/QC) ; Complementaire de pectinated-subclade-mining (extraction manuelle d'UN sous-clade) : ici on OPTIMISE la partition entiere d'une lignee ; Voir aussi clade-finder, mtbc-lineages

### mbovis

Academic research database client for M. bovis and animal MTBC spoligotyping. Queries mbovis.org (the international Spoligo Bovis reference database) for SB number assignments from peer-reviewed published isolates, format conversions (BIN/OCT/HEX), and geographic distribution of animal MTBC spoligotype profiles (M. bovis, M. caprae, M. pinnipedii, M. orygis, M. microti, and other animal hosts). Guyeux group (FEMTO-ST) use case: assigning SB numbers to bovine TB isolates, cross-referencing animal-reservoir spoligotypes with human MTBC data from SITVIT2 ([[sitvitweb]]), identifying clonal complexes (Eu1, Eu2, Af1, Af2)

Compétences : converting a M ; bovis spoligotype pattern to its SB number, looking up a known SB profile (SB0001..SB2902+), downloading the full SB reference database, querying strains by country, or identifying the clonal complex of an animal MTBC isolate

### mk-ascertainment

McDonald-Kreitman test and ascertainment bias simulation for MTBC tier-stratified SPDI variants. Quantifies whether the non-synonymous excess observed among lineage-defining (core-exclusive) variants is genuine or an artefact of the exclusivity filter. A companion script (`mk_per_gene.py`) writes a per-gene MK table (Dn/Ds/Pn/Ps, alpha, DoS, Fisher p) consumed by `mtbc-pathway-explain --from-selection`, closing the chain from selection test to pathway narration and Atlas page

Compétences : a sub-lineage characterisation reports a high dN/dS or non-synonymous excess among core-exclusive SPDI markers and a reviewer (or the authors themselves) question whether ascertainment bias explains the signal ; Requires a tier-annotated CSV with NS/S counts per tier (output of annotate_spdis.py or equivalent)

### molecular-clock

Molecular dating for MTBC phylogenies under weak temporal signal. Root-to-tip regression, TempEst analysis, BEAST XML generation, multi-constraint calibration for MTBC-specific clock challenges

Compétences : estimating divergence times for MTBC lineages, evaluating temporal signal in a phylogeny, preparing BEAST/BEAST2 analyses, dating emergence of sub-lineages or drug resistance

### mtbc-atlas

Academic research toolkit for the Guyeux group (FEMTO-ST) MTBC pipeline: a resilient, stdlib-only client for the MTBC Gene Annotation Atlas REST API (https://mtbc.gclab.fr/api/v1), the re-annotation of the Mycobacterium tuberculosis complex proteome that takes over from the unmaintained Mycobrowser. Queries 3906 genes (anchored on the ancestral MTBC0 genome, joined to H37Rv NC_000962.3), each carrying a curated function, a verdict (requalified / family_assigned / dark) and up to ~35 evidence layers: orthology (eggNOG COG/EC/KO/GO/CAZy), UniProt, intra-MTBC conservation, AlphaFold/ESMFold structure + Foldseek, STRING interaction network, M-CSA catalytic sites, Tn-seq essentiality, CRISPRi vulnerability, PaxDb proteomics, DeepTMHMM localisation, operon/regulon, iModulon expression, PTM, Regions of Difference, mutant phenotypes, and the P8 integrative leads for dark genes

Compétences : you need the current annotation / evidence for an MTBC gene by locus tag (e.g ; Rv3222c), to search genes by name/product/function, to list every gene that carries a given evidence layer (e.g ; all with CRISPRi vulnerability, or the still-dark genes with an integrative lead), to pull one specific layer (structure, conservation, string, vulnerability, ...), or to get dataset-wide counts (verdicts, per-layer coverage) ; This is the machine interface to the atlas served at mtbc.gclab.fr ; prefer it over scraping the HTML pages or re-reading the local content/genes/*.json when the site is live

### mtbc-bilan

Bilan complet et honnete d'un projet MTBC : etat actuel consolide des connaissances acquises, et plan d'action pour la suite. Le bilan ne raconte PAS le cheminement iteratif, il consolide ce qui est actuellement su, comment cela a ete etabli, et ce qui reste a faire d'apres ce qui a deja ete memorise dans le cahier. En cas de conflit entre une ancienne et une nouvelle entree du cahier, on garde la derniere version consolidee. Pour la phase litterature, interroger en priorite tbmonitor-papers (corpus PubMed TB pre-indexe ~190k papiers, sub-seconde) avant les sources externes. Mode --full pour un bilan comparatif de tous les projets MTBC

Compétences : faire le point sur un projet, decider quoi faire ensuite, preparer une reunion, arbitrer entre plusieurs projets, evaluer si un projet est pret a etre clos, repartir d'une etude apres une pause

### mtbc-deepen

Approfondissement systematique d'une etude MTBC en cours. Enchaine : bilan de l'etat du projet (/mtbc-bilan), revue de litterature elargie (/lit-review --wide, en s'appuyant en priorite sur tbmonitor-papers pour le sondage rapide du corpus TB pre-indexe ~190k papiers PubMed), inventaire des skills pertinents non encore mobilises, et synthese de nouvelles pistes d'approfondissement hierarchisees. Ou conclut honnetement qu'il n'y a plus rien a investiguer et que l'etude peut etre close

Compétences : reprendre une etude apres une pause, chercher de nouvelles directions pour un projet qui stagne, decider si un projet merite encore du temps, preparer la suite apres une phase d'analyse terminee, faire le point complet avant une reunion

### mtbc-gene-function

Academic research toolkit for the Guyeux group (FEMTO-ST) MTBC pipeline: produce a structured functional annotation for a Mycobacterium tuberculosis H37Rv gene (by gene name like `katG` or locus tag like `Rv1908c`). Answers from the group's OWN curated annotation_mtbc project FIRST, per-gene UniProt function + EC, Pfam domains, STRING partners, conservation/selection (pN/pS), and Foldseek structural leads for dark genes, and only enriches or falls back to the ESM Atlas API (via `esm-atlas-cli`) for what is not yet annotated. Works fully offline from the curated source. Returns gene + locus tag + product + EC + the evidence channels used + a short citable function paragraph (JSON plus optional prose)

Compétences : an Atlas lineage page mentions a gene (RD content, defining SNP, resistance allele, pathway gene) and needs an automatic functional blurb ; an exploratory analysis hits an unfamiliar Rv locus tag and the Guyeux group wants a 30-second context grounded in their own annotation work

### mtbc-gene-network

Query the MTBC gene interaction network as a graph, LOCAL-FIRST from the group's own precomputed whole-proteome STRING network (annotation_mtbc/résultats/phase2h_string, ~4000 genes, ~38k medium-confidence edges, per-channel evidence). Loads it with networkx and exposes the graph operations the annotation pipeline does not: the interaction neighbours of a gene, the induced subnetwork of a gene set, the shortest path between two genes, the network hubs (degree / betweenness centrality), the functional modules (community detection), and guilt-by-association for a dark gene (infer its role from its high-confidence partners' functions, via mtbc-gene-function). The STRING API (`string-db` skill) is only the fallback for a gene absent locally

Compétences : finding what a gene interacts with, building a PPI subnetwork for a pathway or a gene list, locating the hub/bottleneck genes of the interactome, detecting functional modules/operon-like clusters, hypothesising a function for an uncharacterised Rv locus from its neighbourhood, or producing network evidence for a manuscript figure

### mtbc-lineages

Authoritative source on Mycobacterium tuberculosis complex (MTBC) lineage definitions, sub-lineage hierarchies, and SNP/SPDI markers. The taxonomic source-of-truth hierarchy is fixed in global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md: the live placement in bdd/actuelle/ and its derived registry barcode_complete.tsv are authoritative; lignees.py (key "moi" = Guyeux) is a historical SPDI MARKER BANK, reliable for stable major lineages and for third-party system definitions, but possibly DESYNCHRONISED for any sub-lineage produced by the multi-signal cycle (L1.*, Bovis1.*, BCG.*, deep L6). When no system is specified, "moi" is the implicit default for a marker lookup, but for an authoritative definition/assignment of an active clade, consult bdd/actuelle + barcode_complete.tsv first

Compétences : WHENEVER you need to: (1) look up a lineage's defining marker, (2) find the parent of a sub-lineage, (3) determine which lineage a SPDI belongs to, (4) confirm the hierarchy of L1/L2/L3/L4/L5/L6/L7/L8/ L9/L10 and their sub-lineages, (5) reconcile conflicting classifications across systems, (6) cite the original publication for a taxonomy ; ALWAYS prefer this skill over TBannotator MCP queries, direct CSV reads, or ad-hoc literature lookups for lineage facts ; For step (6), citing the original publication, also consider the `tbmonitor-papers` skill once a candidate citation is in hand: tbmonitor lets you confirm the paper's title, authors, journal and DOI in sub-second time against the pre-indexed PubMed TB corpus

### mtbc-mutation-impact

Academic research toolkit for the Guyeux group (FEMTO-ST) MTBC pipeline: estimate the local functional impact of a point mutation in a Mycobacterium tuberculosis H37Rv gene by comparing ESM Atlas per-residue sparse-autoencoder activations between the wild-type and the mutated protein, at the position of the mutation. Useful when an Atlas lineage page mentions an antimicrobial-resistance allele or a non-synonymous SPDI under positive selection, and the Guyeux group wants a protein-language-model second opinion alongside the literature-derived resistance catalogue. Returns the WT and mutant SAE feature vectors restricted to the mutated residue, the deltas (gained / lost / amplified / attenuated features), and a short interpretive paragraph. The SAE deltas are exploratory only; for a validated, citable variant-effect score the bundled `llr` module computes the ESM-1v masked-marginal log-likelihood ratio (Meier et al. 2021)

Compétences : contextualising a published-research resistance allele (e.g ; katG S315T for INH), characterising a non-synonymous SPDI flagged as defining for a sub-lineage, or sanity-checking a candidate adaptive substitution found by McDonald-Kreitman

### mtbc-pathway-explain

Academic research toolkit for the Guyeux group (FEMTO-ST) MTBC pipeline: produce a structured, CURATED-FIRST narration of a gene set as a pathway, a predefined pathway from the bundled catalogue (ESX-1..5, PDIM, mycolic-acid, DosR, oxidative stress, resistance pathways...), a gene's network neighbourhood (`neighbors:GENE`), or an explicit gene list. Annotates each gene curated-first via `mtbc-gene-function` (annotation_mtbc: UniProt function + EC + Pfam + conservation), aggregates the dominant enzyme classes and Pfam domains across the set, flags the uncharacterised (dark) genes, and narrates it with the PPI network structure (cohesion, density, hub gene) from `mtbc-gene-network`. ESM Atlas is an optional enrichment. Output JSON + a short paragraph for an Atlas page

Compétences : a lineage shows a positive-selection signal on a pathway and the group wants a pathway-level narration that names the proteins, their functions, and how tightly they interact ; or when a network module / a gene's neighbourhood needs to be read as a functional unit ; or, given a lineage's selection table (`--from-selection`, e.g ; McDonald-Kreitman output from `mk-ascertainment`), to map the signal onto the catalogue and narrate the affected pathways, significance-gated (positive alpha + BH-FDR p) so a `selection` section is written only when the test concluded ; It reads an existing result, it does not run the selection test

### mtbc-reboot

Reboot complet d'un projet MTBC. Archive toute la connaissance accumulee (decouvertes, claims, scripts, donnees) dans archives/YYYY-MM-DD_reboot/ avec tags de confiance (VERIFIE/A VERIFIER/INCERTAIN/REFUTE). Reinitialise le projet en structure propre. Scanne les projets voisins pour convergences. Reanalyse claim par claim avec revue critique du code source ; pour les claims qui necessitent un appui litterature, interroge tbmonitor (corpus PubMed TB pre-indexe ~190k papiers) avant WebSearch. Bloque la redaction tant que la reanalyse n'est pas complete

Compétences : a project has accumulated too much drift, stale results, or unverified claims to continue incrementally ; when restarting a study after a long pause with uncertain legacy ; when claim-check reveals too many unverified claims to patch individually ; when pivoting a project's direction while preserving prior knowledge

### mycobacterium-leprae

Academic literature reference. Curated bibliography of peer-reviewed paleogenomic research studies of Mycobacterium leprae, the richest published ancient-DNA research corpus for any Mycobacterium (49 ancient genomes published across 13 countries spanning 2200 years, vs 16 for ancient MTBC). Indexes the canonical academic papers (Schuenemann 2013, 2018; Krause-Kyora 2018; Kerudin 2019; Fotakis 2020; Neukamm 2020; Pfrengle 2021; Bonczarowska 2022; Urban 2024), the documented non-human zoological reservoirs (nine-banded armadillo, medieval English red squirrels), the documented European phylogeographic origin of New World samples, and the five canonical published M. leprae phylogenetic lineages. Used by the Guyeux group as the comparative scholarly reference for academic ancient-DNA evolutionary research on the Mycobacterium genus

Compétences : writing a comparative section of a research manuscript on M ; leprae vs M ; tuberculosis paleogenomic trajectories, preparing scientific seminar slides on ancient Mycobacterium genomics for a peer audience, contextualizing zoonotic reservoirs in a research article, or transposing published paleogenomic methodology to MTBC

### ncbi-pathogen-detection

Academic research database client. Queries the public NCBI Pathogen Detection portal (NIH/NCBI), the open scientific platform that aggregates published bacterial genome assemblies into pre-computed SNP-clusters (PDS accessions) with phylogenetic trees, intended for use by the academic research community in evolutionary-genomics and comparative-genomics scholarly studies. Provides peer-reviewable annotations on virulence-gene content and antimicrobial-susceptibility alleles for academic comparative-genomics research. Complementary to EnteroBase (cgMLST) and the EMBL-EBI Pathogens Portal (ENA)

Compétences : a research manuscript needs to look up the public SNP-cluster assignment of a deposited bacterial isolate, retrieve a published phylogeny for a research article, cite AMR-allele content of a public sample in a scientific paper, or build a research-database integration for a peer-reviewed study

### pangenome-enrichment

Pangenome analysis and functional enrichment by MTBC lineage. Core/soft-core/shell/cloud gene classification, KEGG pathway enrichment, lineage-specific gene content analysis

Compétences : comparing gene content between lineages, identifying lineage-specific genes, performing KEGG enrichment on differential genes, analyzing pangenome structure for an article

### pathogens-portal

Academic research database client. Queries the EMBL-EBI Pathogens Portal, the public European scientific gateway to FAIR bacterial- genome biomolecular data hosted on the European Nucleotide Archive (ENA). Launched in July 2023, it indexes 200,000+ species and strains deposited in published research studies, served via standard ENA Data Hubs. The European peer-reviewed-research counterpart to NCBI Pathogen Detection

Compétences : a research project needs to retrieve ENA/SRA-deposited ancient or modern bacterial-genome sequences for downstream academic comparative-genomics or phylogenomics analysis, locate all ENA projects associated with a research species, or build a Europe-centric scientific data-access workflow for a publication

### pectinated-subclade-mining

Methodologie pour extraire iterativement les sous-lignees pectinees au sein d'une lignee MTBC (ou autre bacterie clonale) en utilisant les SPDI core presents dans le sous-clade candidat et absents dans les autres sous-clades et lignees externes proches. Utilise les fichiers spdi.txt directement sur disque (filesystem-based, pas de SQL), filtre PER-POOL (jamais global) pour garantir l'exclusivite, et produit un repertoire dedie par sous-clade avec son fichier de markers TSV

Compétences : on observe une topologie pectinee dans un arbre phylogenetique RAxML focalise et qu'on veut extraire iterativement les sous-clades pour raffiner la taxonomie ; quand on suspecte qu'un clade trop heterogene contient plusieurs sous-lineages distinctes ; quand on veut produire un classifier SPDI-based pour reclasser des souches en attente (a_ranger)

### phylogeography

Academic research toolkit for the Guyeux group (FEMTO-ST, University of Franche-Comte). Geographic-distribution analysis of published-research MTBC lineages for peer-reviewed phylogeographic publications. Geographic distribution analysis of MTBC lineages via TBannotator. Cross-tabulation country × lineage, choropleth maps, stacked barplots, and geographic diversity indices. To find prior phylogeographic studies on a lineage or country (and cite them in the article), pair with `tbmonitor-papers`, search by country name + lineage code in title/abstract against the pre-indexed PubMed TB corpus

Compétences : mapping the geographic distribution of a lineage for an article, comparing geographic structure between sub-lineages, producing distribution figures and supplementary tables, identifying geographic hotspots

### raxml

Academic research toolkit for the Guyeux group (FEMTO-ST, University of Franche-Comte). Runs peer-reviewed phylogenomic inference (RAxML-NG) for scientific publications. Submit and manage RAxML-NG phylogenetic inference jobs via TBannotator MCP. Supports direct matrix mode, clustering mode, and contextual placement

Compétences : building MTBC phylogenies, placing new strains on reference trees, producing Newick files for iTOL annotation, running RAxML-NG for an article

### resistance-catalogue

Academic research toolkit for the Guyeux group (FEMTO-ST, University of Franche-Comté) MTBC pipeline: query and (re)build a consolidated mutation-to-antimicrobial-resistance reference catalogue for the Mycobacterium tuberculosis complex, cross-referencing the WHO catalogue of mutations (2nd ed., 2023), the tb-profiler reference database, and empirical CRyPTIC signal. Resolves HGVS variant notation (gene_mutation) to the project's 0-based SPDI coordinates via the official WHO genomic-coordinates file, and returns, for a given variant or antitubercular medicine, the catalogued association grade and its provenance, for peer-reviewed phylogenomic and AMR-evolution publications. Pairs with `tbmonitor-papers` to check whether a variant has prior coverage in the published TB literature

Compétences : looking up the WHO/tb-profiler association grade of a variant, listing the catalogued markers of a medicine, computing a deterministic catalogue-based baseline for a strain (TB-Profiler-like), converting HGVS to SPDI, or regenerating the consolidated catalogue after a source update

### resistance-discovery

Academic research toolkit for the Guyeux group (FEMTO-ST, University of Franche-Comté) MTBC pipeline: discover NON-catalogued antimicrobial-resistance determinants in the Mycobacterium tuberculosis complex by genome-wide association, controlling for population structure and co-resistance, and validating candidates by phylogenetic convergence. Complements the curated `resistance-catalogue` (the known, deterministic part) by surfacing variants associated with resistance that the catalogue misses, for peer-reviewed phylogenomic and AMR-evolution publications. Also documents and corrects the three representation blind spots of SPDI-indexed catalogues (synonymous codons, rare determinants, MNV-vs-SNP) that otherwise inflate false discoveries. Pairs with `convergent-evolution`, `mtbc-mutation-impact` and `tbmonitor-papers` to confirm and contextualise candidates

Compétences : searching for novel resistance determinants beyond the WHO catalogue, auditing why a drug's catalogue baseline has low sensitivity, building a lineage-aware GWAS of an antitubercular medicine, or screening candidates while rejecting clonal-linkage artefacts

### resistance-explain

Academic research toolkit for the Guyeux group (FEMTO-ST, University of Franche-Comté) MTBC pipeline: explain the mechanism of a catalogued or candidate antimicrobial-resistance mutation in the Mycobacterium tuberculosis complex, by assembling, into one citable mechanistic dossier, the curated catalogue verdict (`resistance-catalogue`), the empirical phenotype association observed in the project strains, the published TB literature on the variant (`tbmonitor-papers` / `lit-review`), a protein-language-model variant-effect score (ESM-1v log-likelihood ratio, Meier et al. 2021, via `mtbc-mutation-impact`), gene function (`mtbc-gene-function`) and 3D structural context (ESMFold via `esm-atlas-cli`). For peer-reviewed phylogenomic and AMR-evolution publications

Compétences : explaining why a variant confers (or might confer) resistance, interpreting a candidate from `resistance-discovery`, drafting the mechanistic paragraph of a manuscript, or distinguishing a causal determinant from a co-resistance / lineage-linkage artefact

### resistance-predict

Academic research toolkit for the Guyeux group (FEMTO-ST, University of Franche-Comté) MTBC pipeline: predict the antimicrobial-resistance phenotype of a Mycobacterium tuberculosis strain from its genomic variant profile, by combining the deterministic curated catalogue (`resistance-catalogue`) with a residual gradient-boosted model, and explain each prediction (feature importance / SHAP + ESM protein-impact). Evaluated honestly with lineage-stratified cross-validation (GroupKFold) and compared to the catalogue baseline at equal specificity, for peer-reviewed phylogenomic and AMR-evolution publications. Built on variant-representation reconciliation (SNP+MNV, amino-acid level) so the catalogue baseline is not under-counted

Compétences : predicting resistance for a strain or cohort, quantifying how much a machine-learning layer adds over the WHO catalogue per medicine, producing a per-medicine sensitivity/specificity table for a manuscript, or explaining a prediction by the variants driving it

### resistance-profiler

Academic research toolkit. Computes published-literature-style summaries of antimicrobial-resistance allele frequencies across Mycobacterium tuberculosis complex (MTBC) lineages, by querying the curated TBannotator research database (Guyeux group, FEMTO-ST, University of Franche-Comte). Produces cross-tabulations and iTOL annotation files for peer-reviewed phylogenomic publications. To contextualise results in the published scientific literature, use the `tbmonitor-papers` skill in parallel (indexed corpus of ~190k PubMed TB research abstracts)

Compétences : writing a phylogenomics article that reports lineage-level AMR allele frequencies, producing supplementary tables/figures for a scientific publication, or generating iTOL annotation tracks for a peer-reviewed manuscript on MTBC evolution

### sitvitweb

Query the SITVIT2 spoligotype database (Institut Pasteur de Guadeloupe) for MTBC spoligotype assignments, SIT lookups, clade names (Beijing, LAM, Haarlem, T1...), and geographic distributions. Browser-only (no REST API)

Compétences : converting spoligotype octal to SIT number, identifying clade for a strain, finding geographic distribution of a SIT, or cross-referencing spol43/spol98 fields from TBannotator metadata

### snp-distance

Academic research toolkit for the Guyeux group (FEMTO-ST, University of Franche-Comte). Computes pairwise SNP distances on published-research MTBC isolates for peer-reviewed publications. Compute pairwise SNP distance matrices from SPDI presence/absence data. Queries TBannotator for SPDI profiles, builds Hamming/Jaccard distance matrix

Compétences : computing genetic distances between MTBC strains, preparing input for t-SNE+HDBSCAN or THD, identifying transmission clusters by SNP threshold, building distance matrices for NJ trees or population genetics analyses

### spaam-ancient-metagenome-dir

Query the SPAAM community AncientMetagenomeDir, the reference community catalogue of all published ancient metagenomic and ancient microbial single-genome samples. Find ancient Mycobacterium tuberculosis and related pathogen samples, their publications, sites, dates, and ENA/SRA accessions, and pair them with AADR ancient human hosts for coevolution narratives

Compétences : finding published ancient MTBC genomes, locating raw data (ENA/SRA) for ancient pathogens, pairing an ancient TB strain with its human host in AADR, building a list of ancient metagenomes for a region/period, or filling the pathogen side of a host, pathogen coevolution story

### spaam-community

Index of the SPAAM (Standards, Precautions and Advances in Ancient Metagenomics) community ecosystem, the umbrella organisation for ancient metagenomics. Covers tools, pipelines, training materials, metadata standards, lab directories, and reference guides beyond the AncientMetagenomeDir catalogue itself. Use this as a meta-index when you need to find a tool, pipeline, tutorial, or reference resource for working with ancient microbial DNA

Compétences : choosing an ancient-metagenomics pipeline (eager vs aMeta), finding a tutorial on ancient DNA damage patterns, validating metadata against the MInAS standard, identifying labs working on a specific ancient pathogen, looking up the canonical Introduction to Ancient Metagenomics textbook, or onboarding to the SPAAM community infrastructure

### spdi-annotation

Academic research toolkit for the Guyeux group (FEMTO-ST, University of Franche-Comte). Annotates MTBC variants for peer-reviewed phylogenomic publications. Annotate MTBC SPDI variants with gene, effect (missense/synonymous/stop/frameshift), amino acid change, and functional category. First queries TBannotator for existing annotations, then falls back to local GenBank/GFF3 annotation for missing variants. To check whether a SPDI variant (especially a high-impact one) has already been described in the literature, useful to add a citation column to the supplementary table, pair with `tbmonitor-papers` and search for the SPDI string, gene name, or HGVS_p notation in title/abstract

Compétences : annotating a list of SPDI variants for an MTBC article, building supplementary tables with functional impact, or classifying variants by effect type

### species-id

Identification d'espece/genre bacterien pour detecter les souches mal etiquetees "M. tuberculosis". Deux methodes : (1) BLAST API via NCBI (zero stockage local, precise, ~1 min/souche), (2) Mash screen (rapide, ~1 Go de sketch RefSeq, optionnel). Concu pour le screening de souches suspectes avant integration dans la BDD MTBC

Compétences : a strain labeled M ; tuberculosis looks suspicious (aberrant SNP count, odd phylogenetic placement, too few/many SPDI), when importing new strains from SRA/ENA, or when TBannotator reports anomalies suggesting contamination or mislabeling ; Once a non-TB species is identified, `tbmonitor-papers` can confirm whether the underlying BioProject/SRA has already been reported as misclassified in the published literature (search by SRA / BioProject ID in title or abstract)

### sra-geolocate

Consolidation de l'origine **et de la date** d'une souche SRA, ou construction d'un dataset de SRA correspondant a une zone geographique donnee. Deux cascades paralleles (location + date) puisent dans les memes sources : metadonnees BioSample (geo_loc_name, lat_lon, collection_date), metadonnees BioProject (titre, abstract, submission_date), publications PubMed/Europe PMC liees, supplementary materials des articles (tables S1/S2 par souche), texte integral PDF quand disponible. Chaque resultat est assorti d'un score de confiance et de la source qui l'a produit. Gere les zones non-pays : villes, regions administratives, zones supranationales (Sahel, Maghreb, Corne de l'Afrique), coordonnees x/y. Distingue lieu de **collection** vs lieu de **sequencage**, date de collection vs date de publication

Compétences : enrichir la metadonnee d'une souche dont `geo_loc_name` ou `collection_date` est vague ou vide, construire une cohorte TB par region (ex ; tuberculose en Franche-Comte"), verifier l'origine et la date revendiquees d'un SRA avant inclusion dans une analyse, detecter des incoherences entre BioSample, BioProject et publications liees, extraire les metadonnees par souche depuis les supplementary materials des articles open access

### strain-qc

Controle qualite d'une souche MTBC avant integration dans la BDD ou un arbre phylogenetique. Verifie 7 criteres : (1) chimere intra-MTBC par classification multi-systeme, (2) taux GC, (3) couverture du genome, (4) profondeur de sequencage, (5) nombre de SPDI vs distribution de la lignee, (6) contamination inter-especes par signature des genes housekeeping, (7) qualite de mapping (genes manquants vs depth). Produit un verdict PASS/WARN/FAIL avec justification. Fonctionne en mode souche unique ou lot

Compétences : importing new strains from SRA/ENA, filtering strains before phylogenetic reconstruction, investigating a strain with aberrant placement or long branch in a tree, screening a BDD for problematic entries, or when get_phylo.py reports exclusions and you want to understand why ; When a WARN/FAIL verdict is produced on a strain, check `tbmonitor-papers` for any published study mentioning the same SRA / BioProject (could be a known problematic dataset reported elsewhere, or conversely a strain validated in a previous study despite borderline metrics)

### string-db

Academic research toolkit for the Guyeux group (FEMTO-ST) MTBC pipeline: a resilient, stdlib-only client for the STRING v12 protein-association REST API (https://string-db.org), which aggregates known and predicted protein-protein associations decomposed into evidence channels (neighborhood, fusion, co-occurrence, co-expression, experimental, database, text-mining). Resolves locus tags to STRING ids, lists functional or physical interaction partners with per-channel scores, builds networks among a gene set, runs functional enrichment (GO/KEGG/Pfam/InterPro) and the PPI-enrichment test, and downloads network pictures. Default species is 83332 (M. tuberculosis H37Rv) but works for any organism in STRING

Compétences : you need a *guilt-by-association* second opinion on a gene (especially a hypothetical), to ask "what does this unknown gene work with?", to test whether a candidate operon/complex is significantly connected, or to get the functional enrichment of a small gene set ; Reusable across coevolution, pathway-explanation, pangenome-enrichment and host-pathogen studies ; For WHOLE-PROTEOME enrichment, do NOT use this skill (STRING's API is for occasional access): download the per-organism bulk files instead, as the annotation_mtbc `phase2h_string.py` pipeline does

### tb-cli

Academic research CLI for Mycobacterium tuberculosis complex (MTBC) comparative-genomics studies, via the `tb` command. Used by the Guyeux group (FEMTO-ST, University of Franche-Comte) for peer-reviewed scientific publications on MTBC phylogenomics and evolutionary biology

Compétences : when the research context mentions MTBC lineages, deposited research strains, SPDI/SNP research annotations, published variants in genes such as katG/rpoB/embB, AMR-allele cataloguing for a research article, regions-of-difference scientific analysis, PubMed literature mining for MTBC research, or TBannotator-research-database queries

### tbannotator-mcp

Query TBannotator v3.6 MCP server (~274,800 MTBC genomes) via PostgreSQL. Access strain metadata, lineage classifications (Coll, Gagneux, Senelle...), SNP/SPDI frequencies, phylogenetic trees (NJ, RAxML), drug resistance profiles

Compétences : counting strains per lineage, getting metadata for a lineage code, finding core-exclusive markers, validating supplementary files, or building phylogenetic trees for an MTBC lineage characterisation article

### tbmonitor-papers

Search the tbmonitor MCP server, a pre-indexed read-only SQLite mirror of the PubMed tuberculosis corpus (~330 000 papers spanning 1848 to present, ~81 % TB-specific, source 100 % PubMed). Exposes title, abstract, DOI, PubMed link, journal, publication date, plus authors / keywords / MeSH terms / publication types / author affiliations / reference list as JSON arrays directly queryable via `json_each()`. Sub-second response on filtered fulltext-style searches. The corpus now reaches back to the founding TB literature (dense from ~1945), so it can date drug introductions and surface pre-1995 primary sources that earlier corpus snapshots missed

Compétences : pulling TB-specific papers by author, MeSH term, keyword, journal or year range ; assembling a BibTeX list for a review or grant ; verifying that a literature claim has prior coverage ; cross-linking tbannotator strain results with the published literature about them ; or building a quick state-of-the-art before falling back to lit-review for deeper systematic work

### thd

Compute Time-scaled Haplotypic Density (THD) from Rasigade et al. 2017 (Sci Rep 7:45326). Quantifies epidemic success of pathogen strains using kernel density estimation on pairwise genetic distances with biologically meaningful timescales

Compétences : computing THD for MIRU-VNTR profiles, SNP distance matrices, or WGS haplotype data ; comparing epidemic success across MTBC lineages ; associating strain success with clinical/epidemiological covariates ; distinguishing epidemic (short-term) from endemic (long-term) success

### triangulate-route

Academic phylogeography research toolkit (Guyeux group, FEMTO-ST). Triangulates the published genomic signature of an MTBC research lineage against historical human-migration corpora to produce peer-review-ready dispersal scenarios. Takes a lineage and a target country as input, returns: (a) global published neighbours by sub-lineage (Shitikov23) via TBannotator research database, (b) candidate historical dispersal routes sourced from SlaveVoyages, OWTRAD, and the specialized scholarly literature, (c) a triangulation table formatted for scientific publication. Implements the methodology described in peer-reviewed case studies (e.g. Madagascar MTBC phylogeography)

Compétences : ecrire une section phylogeographique d'un article scientifique sur un pays/region (Bresil, Antilles, Cap Vert, Maurice, Comores, Inde, etc.), valider une signature genomique publiee avec corpus historiques d'archives, preparer une diapositive de seminaire academique, ou rediger un *case study* dans un manuscrit scientifique

### tsne-hdbscan

t-SNE dimensionality reduction + HDBSCAN density-based clustering for exploring MTBC genomic diversity. Works on SPDI presence/absence matrices, SNP distance matrices, or MIRU-VNTR profiles

Compétences : exploring population structure of MTBC strains, identifying transmission clusters, detecting outliers or misclassified lineages, visualizing genomic relationships in 2D, unsupervised clustering of pathogen genomes without specifying the number of clusters

## Skills partagés (via symlink)

Documentés sur la page de leur plugin d'origine.

| Skill | Origine |
|-------|---------|
| [atlantic-voyages](bio_population_genetics.md#atlantic-voyages) | `bio_population_genetics` |
| [bayesian-skyline](bio_population_genetics.md#bayesian-skyline) | `bio_population_genetics` |
| [beast2-phylogeography](bio_population_genetics.md#beast2-phylogeography) | `bio_population_genetics` |
| [bioc-pmc](bio_population_genetics.md#bioc-pmc) | `bio_population_genetics` |
| [biopython](bio_population_genetics.md#biopython) | `bio_population_genetics` |
| [bioskills](bio_population_genetics.md#bioskills) | `bio_population_genetics` |
| [claim-check](redac.md#claim-check) | `redac` |
| [create-viz](ops.md#create-viz) | `ops` |
| [domestication-pathways](bio_population_genetics.md#domestication-pathways) | `bio_population_genetics` |
| [esm-atlas-cli](bio_population_genetics.md#esm-atlas-cli) | `bio_population_genetics` |
| [europe-pmc](bio_population_genetics.md#europe-pmc) | `bio_population_genetics` |
| [geo-map](bio_population_genetics.md#geo-map) | `bio_population_genetics` |
| [indian-ocean-voyages](bio_population_genetics.md#indian-ocean-voyages) | `bio_population_genetics` |
| [iqtree-lsd2](bio_population_genetics.md#iqtree-lsd2) | `bio_population_genetics` |
| [itol](bio_population_genetics.md#itol) | `bio_population_genetics` |
| [lit-review](redac.md#lit-review) | `redac` |
| [migration-data](bio_population_genetics.md#migration-data) | `bio_population_genetics` |
| [nextflow-development](bio_population_genetics.md#nextflow-development) | `bio_population_genetics` |
| [nextstrain](bio_population_genetics.md#nextstrain) | `bio_population_genetics` |
| [ontologies](bio_population_genetics.md#ontologies) | `bio_population_genetics` |
| [openalex](bio_population_genetics.md#openalex) | `bio_population_genetics` |
| [pastml](bio_population_genetics.md#pastml) | `bio_population_genetics` |
| [phylo-history](bio_redac.md#phylo-history) | `bio_redac` |
| [pubmed-database](bio_population_genetics.md#pubmed-database) | `bio_population_genetics` |
| [pubtator](bio_population_genetics.md#pubtator) | `bio_population_genetics` |
| [pysam](bio_population_genetics.md#pysam) | `bio_population_genetics` |
| [rdkit](bio_population_genetics.md#rdkit) | `bio_population_genetics` |
| [read-scientific-pdf](bio_population_genetics.md#read-scientific-pdf) | `bio_population_genetics` |
| [reviewer-response](redac.md#reviewer-response) | `redac` |
| [scanpy](bio_population_genetics.md#scanpy) | `bio_population_genetics` |
| [scientific-problem-selection](ia.md#scientific-problem-selection) | `ia` |
| [scikit-bio](bio_population_genetics.md#scikit-bio) | `bio_population_genetics` |
| [scikit-learn](ia.md#scikit-learn) | `ia` |
| [seaborn](bio_population_genetics.md#seaborn) | `bio_population_genetics` |
| [slavevoyages](bio_population_genetics.md#slavevoyages) | `bio_population_genetics` |
| [statsmodels](ia.md#statsmodels) | `ia` |
| [tooluniverse-sequence-retrieval](bio_population_genetics.md#tooluniverse-sequence-retrieval) | `bio_population_genetics` |

