# Plugin `bio_bacteria`

> Academic research toolkit for comparative genomics of bacteria BEYOND the Mycobacterium tuberculosis complex stricto sensu: non-tuberculous mycobacteria (M. abscessus, M. avium, M. ulcerans...) and other genera. Genome assembly and characterisation, core-genome MLST clonality, ab initio mobile-element detection, antimicrobial-resistance allele frequencies from published research isolates. Used by the Guyeux group (FEMTO-ST, University of Franche-Comte) for peer-reviewed scientific publications. For MTBC stricto sensu, use the bio_pathogens plugin.

## Positionnement

Domaine bactérien hors MTBC stricto sensu. Porte les méthodes qui ne se transposent pas correctement au complexe M. tuberculosis : assemblage de novo, clonalité cgMLST, mobilome ab initio, bases et corpus consacrés aux mycobactéries non tuberculeuses et aux autres genres bactériens.

Skills propres (canoniques) : **9** ; skills partagés utilisés (symlinks) : **15**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [bactrline](#bactrline) ; [enterobase](#enterobase) ; [helicobacter-pylori-phylogeography](#helicobacter-pylori-phylogeography) ; [mycobacterium-leprae](#mycobacterium-leprae) ; [ncbi-pathogen-detection](#ncbi-pathogen-detection) ; [ntm-resources](#ntm-resources) ; [panisa](#panisa) ; [pymlst](#pymlst) ; [yersinia-resources](#yersinia-resources)

### bactrline

Academic research toolkit (Guyeux group, FEMTO-ST) wrapping bactRline, the Snakemake workflow of B. Valot for bacterial genome assembly and characterisation: read trimming (TrimGalore, Filtlong), assembly (SPAdes for Illumina, Flye for Oxford Nanopore), quality control (QUAST, Kraken2, CheckM2), annotation and typing (AMRFinderPlus, pyMLST), optional plasmid detection (Platon, PlasClass)

Compétences : turning raw reads or SRA accessions of a published research isolate into an assembled, QC'd and typed genome for any bacterium beyond the MTBC (non-tuberculous mycobacteria, other genera), or when an analysis needs assemblies that do not exist yet

### enterobase

Client de base de données académique (groupe Guyeux, FEMTO-ST). Interroge EnteroBase (groupe Achtman, Warwick), base de génomes et plateforme cgMLST/HierCC de référence pour Salmonella, Escherichia, Yersinia, Clostridioides, Helicobacter, Vibrio et Moraxella. Ressource centrale pour la phylogénie historique de Yersinia pestis (peste, Route de la soie, Peste noire), les pandémies de Vibrio cholerae et l'épidémiologie bactérienne à l'échelle génomique.

Compétences : construire des récits historiques autour de pathogènes bactériens non-MTBC ; corréler des lignées de Y ; pestis à la Route de la soie ou à la Peste noire ; étudier les pandémies de choléra ; utiliser H ; pylori comme proxy des migrations humaines ; transposer la méthodologie TBannotator à un autre pathogène entérique

### helicobacter-pylori-phylogeography

Cadre de référence sur la phylogéographie d'Helicobacter pylori comme proxy des migrations humaines, cas paradigmatique de coévolution hôte-pathogène (Linz 2007 ; Moodley 2009/2012 ; Maixner 2016 sur l'Homme de Similaun). Documente les sept populations de H. pylori, leurs distributions géographiques et le modèle méthodologique pour transposer l'approche à M. tuberculosis. Essentiel pour situer la phylogéographie du MTBC dans le paradigme « les pathogènes comme historiens ».

Compétences : cadrer un récit de séminaire « les pathogènes courant avec leurs hôtes » sur un précédent canonique ; construire une slide comparative H ; pylori vs M ; tuberculosis ; transposer la méthodologie de Linz au MTBC ; référencer les ancrages classiques de la littérature de coévolution

### mycobacterium-leprae

Reference bibliographique academique. Bibliographie curee de la recherche paleogenomique evaluee par les pairs sur Mycobacterium leprae, le corpus d'ADN ancien publie le plus riche pour une mycobacterie : 49 genomes anciens dans 13 pays sur 2200 ans, contre 16 pour le MTBC ancien. Indexe les articles canoniques (Schuenemann 2013 et 2018, Krause-Kyora 2018, Kerudin 2019, Fotakis 2020, Neukamm 2020, Pfrengle 2021, Bonczarowska 2022, Urban 2024), les reservoirs non humains documentes (tatou a neuf bandes, ecureuils roux medievaux anglais), l'origine europeenne des echantillons du Nouveau Monde, et les cinq lignees publiees canoniques.

Compétences : rediger une section comparative M ; leprae contre M ; tuberculosis sur les trajectoires paleogenomiques ; preparer des slides de seminaire sur la genomique des mycobacteries anciennes ; contextualiser les reservoirs zoonotiques dans un article ; transposer une methodologie paleogenomique publiee au MTBC

### ncbi-pathogen-detection

Client de base de données académique. Interroge le portail public NCBI Pathogen Detection (NIH/NCBI), plateforme ouverte qui agrège les assemblages de génomes bactériens publiés en clusters de SNP pré-calculés (accessions PDS) avec arbres phylogénétiques, pour la recherche en génomique évolutive et comparative. Fournit des annotations sur le contenu en gènes de virulence et les allèles de sensibilité antimicrobienne. Complémentaire d'EnteroBase et du Pathogens Portal EMBL-EBI.

Compétences : un manuscrit doit consulter l'assignation de cluster SNP public d'un isolat déposé ; récupérer une phylogénie publiée ; citer le contenu en allèles de résistance d'un échantillon public ; bâtir une intégration de base de données pour une étude évaluée

### ntm-resources

Academic research database client (Guyeux group, FEMTO-ST) for non-tuberculous mycobacteria (NTM): NTM-DB genomic resource, Mabellini structural proteome of M. abscessus, and MAC-INMV-SSR genotyping of the M. avium complex including subsp. paratuberculosis

Compétences : identifying or typing an NTM isolate from published research data, looking for a genomic or structural resource for M ; abscessus, M ; avium or another environmental mycobacterium, or checking whether an MTBC method transposes to an NTM species

### panisa

Academic research toolkit (Guyeux group, FEMTO-ST) for ab initio detection of insertion sequences (IS) in bacterial genomes from short-read alignments, using panISa (Treepong, Guyeux, Meunier, Couchoud, Hocquet, Valot, Bioinformatics 2018). Detects IS insertion sites WITHOUT any IS database, from clipped-read signatures, direct repeats and reconstructed inverted repeats, then optionally assigns families against ISfinder

Compétences : looking for mobile elements in a published research isolate of any bacterium (non-tuberculous mycobacteria, Pseudomonas, Salmonella, Helicobacter...), hunting IS types ABSENT from a known IS panel, or documenting one insertion with publication-grade evidence (direct repeat plus both border sequences)

### pymlst

Academic research toolkit (Guyeux group, FEMTO-ST) for assessing bacterial clonality by core-genome and whole-genome MLST with pyMLST (Biguenet, Bordy, Atchon, Hocquet, Valot, Microbial Genomics 2023). Builds a local SQLite allele database from assembled genomes, calls cgMLST/wgMLST profiles, and produces allelic distance matrices, minimum-spanning trees and per-gene alignments for published research isolates of any bacterium (non-tuberculous mycobacteria, Pseudomonas, Klebsiella, Salmonella, Staphylococcus...)

Compétences : deciding whether isolates form a clonal group, typing a strain against a PubMLST or cgMLST scheme, or producing a distance matrix for a peer-reviewed manuscript

### yersinia-resources

Academic research database client (Guyeux group, FEMTO-ST) for genus Yersinia: Yersiniomics multi-omics database, BIGSdb-Pasteur Yersinia (genus-wide cgMLST and species identification), the Y. enterocolitica cgMLST surveillance scheme, plus the routes for plague palaeogenomics of published research isolates (ancient Y. pestis genomes)

Compétences : identifying or typing a Yersinia isolate, looking for a cgMLST scheme for the genus, situating an ancient Y ; pestis genome in the published phylogeny (Black Death, Silk Road, Bronze Age lineages), or transposing an MTBC method to Y ; pestis

## Skills partagés (via symlink)

Documentés sur la page de leur plugin d'origine.

| Skill | Origine |
|-------|---------|
| [bacdive](bio_pathogens.md#bacdive) | `bio_pathogens` |
| [biopython](bio_population_genetics.md#biopython) | `bio_population_genetics` |
| [biotools](bio_population_genetics.md#biotools) | `bio_population_genetics` |
| [card](bio_population_genetics.md#card) | `bio_population_genetics` |
| [claim-check](redac.md#claim-check) | `redac` |
| [iqtree-lsd2](bio_population_genetics.md#iqtree-lsd2) | `bio_population_genetics` |
| [isfinder-offline](bio_pathogens.md#isfinder-offline) | `bio_pathogens` |
| [lit-review](redac.md#lit-review) | `redac` |
| [nextflow-development](bio_population_genetics.md#nextflow-development) | `bio_population_genetics` |
| [pathogens-portal](bio_pathogens.md#pathogens-portal) | `bio_pathogens` |
| [pysam](bio_population_genetics.md#pysam) | `bio_population_genetics` |
| [remote-compute](bio_population_genetics.md#remote-compute) | `bio_population_genetics` |
| [sci-figure](bio_population_genetics.md#sci-figure) | `bio_population_genetics` |
| [snp-distance](bio_pathogens.md#snp-distance) | `bio_pathogens` |
| [species-id](bio_pathogens.md#species-id) | `bio_pathogens` |
