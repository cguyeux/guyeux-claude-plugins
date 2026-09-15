# Plugin `bacteria`

> Academic research toolkit for comparative genomics of bacteria beyond the Mycobacterium tuberculosis complex stricto sensu: non-tuberculous mycobacteria, Yersinia, Helicobacter, Salmonella and other genera. Genome assembly and characterisation, core-genome MLST clonality, ab initio mobile-element detection, from published research isolates. Guyeux group (FEMTO-ST).

Skills propres (canoniques) : **18** ; skills partagés utilisés (symlinks) : **0**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [bacdive](#bacdive) ; [bactrline](#bactrline) ; [crispr-spacer-null](#crispr-spacer-null) ; [crisprbuilder](#crisprbuilder) ; [crisprcasdb](#crisprcasdb) ; [enterobase](#enterobase) ; [helicobacter-pylori-phylogeography](#helicobacter-pylori-phylogeography) ; [hgt-direction-check](#hgt-direction-check) ; [isfinder-offline](#isfinder-offline) ; [mycobacterium-leprae](#mycobacterium-leprae) ; [ncbi-pathogen-detection](#ncbi-pathogen-detection) ; [ntm-resources](#ntm-resources) ; [panisa](#panisa) ; [pathogens-portal](#pathogens-portal) ; [pymlst](#pymlst) ; [species-id](#species-id) ; [thd](#thd) ; [yersinia-resources](#yersinia-resources)

### bacdive

Client de base de données académique (groupe Guyeux, FEMTO-ST). Interroge BacDive, la métabase DSMZ de diversité bactérienne, plus grand dépôt structuré d'informations sur les souches (97 000+ souches, 2,6 millions de données, 1 000+ champs) : taxonomie, morphologie, physiologie, métabolisme, culture, source d'isolement, niveau de biosécurité, sensibilité aux antibiotiques. Ressource de référence pour les métadonnées phénotypiques et écologiques des souches types.

Compétences : récupérer des données phénotypiques pour une espèce bactérienne utile à un travail TB ou paléopathogène ; consulter des conditions de culture ; vérifier un niveau de biosécurité ; trouver une souche type de référence ; enrichir une analyse génomique d'un contexte phénotypique

### bactrline

Academic research toolkit (Guyeux group, FEMTO-ST) wrapping bactRline, the Snakemake workflow of B. Valot for bacterial genome assembly and characterisation: read trimming (TrimGalore, Filtlong), assembly (SPAdes for Illumina, Flye for Oxford Nanopore), quality control (QUAST, Kraken2, CheckM2), annotation and typing (AMRFinderPlus, pyMLST), optional plasmid detection (Platon, PlasClass)

Compétences : turning raw reads or SRA accessions of a published research isolate into an assembled, QC'd and typed genome for any bacterium beyond the MTBC (non-tuberculous mycobacteria, other genera), or when an analysis needs assemblies that do not exist yet

### crispr-spacer-null

Academic research toolkit (Guyeux group, FEMTO-ST), peer-reviewed comparative genomics: evaluate whether a CRISPR spacer, primer, amplicon, or short marker sequence is truly absent from a published bacterial genome set, rather than an artefact of assembly, orientation, masking, read depth, database scope, or taxonomy

Compétences : testing spacer or marker null claims, comparing CRISPR arrays, auditing negative PCR or BLAST results, or deciding whether a zero-hit sequence can support an evolutionary claim

### crisprbuilder

Academic research toolkit (Guyeux group, FEMTO-ST), peer-reviewed comparative genomics: extrait un locus CRISPR (DR consensus, arrays, spacers) d'un genome, d'un assemblage ou de reads, SANS catalogue de motifs prealable, par decouverte de novo du direct repeat. Successeur outille de CRISPRbuilder-TB (Guyeux 2021), dont il leve le verrou : celui-ci ne reconnait que les 221 motifs du MTBC et ne trouve donc RIEN chez une souche a DR different, comme les M. canettii a systeme de type I-G, I-E ou I-C

Compétences : extraire les spacers d'une souche, comparer des repertoires d'espaceurs entre lignees ou especes, spoligotypage in-silico, verifier si un locus a survecu a l'assemblage, ou identifier un systeme CRISPR inconnu chez une bacterie hors MTBC

### crisprcasdb

Academic research database client (Guyeux group, FEMTO-ST, peer-reviewed comparative genomics) for the LOCAL copy of CRISPRCasdb, the PostgreSQL database behind CRISPR-Cas++ (I2BC, Universite Paris-Saclay): 36 605 complete prokaryote genomes, 143 878 CRISPR arrays, 608 232 spacers, 17 369 cas gene clusters, all produced by CRISPRCasFinder

Compétences : extracting the spacers or direct repeats of a published genome, asking which organisms carry a given spacer, comparing CRISPR-Cas system types across taxa, retrieving the DR consensus of a lineage, cross-checking an in-silico spoligotype against an independent source, or querying CRISPR content for a scientific manuscript

### enterobase

Client de base de données académique (groupe Guyeux, FEMTO-ST). Interroge EnteroBase (groupe Achtman, Warwick), base de génomes et plateforme cgMLST/HierCC de référence pour Salmonella, Escherichia, Yersinia, Clostridioides, Helicobacter, Vibrio et Moraxella. Ressource centrale pour la phylogénie historique de Yersinia pestis (peste, Route de la soie, Peste noire), les pandémies de Vibrio cholerae et l'épidémiologie bactérienne à l'échelle génomique.

Compétences : construire des récits historiques autour de pathogènes bactériens non-MTBC ; corréler des lignées de Y ; pestis à la Route de la soie ou à la Peste noire ; étudier les pandémies de choléra ; utiliser H ; pylori comme proxy des migrations humaines ; transposer la méthodologie TBannotator à un autre pathogène entérique

### helicobacter-pylori-phylogeography

Cadre de référence sur la phylogéographie d'Helicobacter pylori comme proxy des migrations humaines, cas paradigmatique de coévolution hôte-pathogène (Linz 2007 ; Moodley 2009/2012 ; Maixner 2016 sur l'Homme de Similaun). Documente les sept populations de H. pylori, leurs distributions géographiques et le modèle méthodologique pour transposer l'approche à M. tuberculosis. Essentiel pour situer la phylogéographie du MTBC dans le paradigme « les pathogènes comme historiens ».

Compétences : cadrer un récit de séminaire « les pathogènes courant avec leurs hôtes » sur un précédent canonique ; construire une slide comparative H ; pylori vs M ; tuberculosis ; transposer la méthodologie de Linz au MTBC ; référencer les ancrages classiques de la littérature de coévolution

### hgt-direction-check

Academic research toolkit (Guyeux group, FEMTO-ST), peer-reviewed comparative genomics: decide the DIRECTION of a horizontal transfer before it becomes a claim, and kill the commonest way of getting it backwards. A high sequence identity between a bacterial gene and a viral (or plasmid, or any other donor candidate) gene says NOTHING about who captured whom: it measures a position inside the structure of the gene family. The test that does settle direction is topological, and it comes with its own null. (1) NESTING: build the family tree from a reference panel of CELLULAR homologues plus the sequences carried by the candidate donor, and ask whether each donor-borne sequence sits INSIDE the cellular diversity (capture cell -> donor) or BASAL to it (the family would then originate in the donor). (2) HOST CONCORDANCE: nesting alone is not enough, each donor-borne sequence must land next to the homologues of its OWN host taxon, which is what separates a real capture from an arbitrary placement, and what turns one case into a repeated, independent result. (3) LONG-BRANCH CONTROL: the host clade must still exist in a tree inferred independently WITHOUT the donor sequences, otherwise the nesting was manufactured by the analysis. Also carries the correlation pre-test that disqualifies an identity-based argument in seconds, before any tree is built

Compétences : a manuscript is about to say "this bacterial gene derives from a phage" (or from a plasmid, or an integron) on the strength of a BLAST identity ; an insertion sequence, transposase or any mobile-element gene is found in a viral genome ; a reviewer asks which way a transfer went ; a striking identity to a viral gene needs to be checked against the plain alternative that it is simply the family's internal structure ; or a negative result (no transfer detectable) must be made publishable rather than silent

### isfinder-offline

Academic research toolkit (Guyeux group, FEMTO-ST). Repli LOCAL/hors-ligne pour identifier ou classer une séquence d'insertion (IS) quand isfinder.biotoul.fr est injoignable, ce qui arrive souvent (échec SSL/connexion direct, pas seulement un blocage d'outil de fetch, vérifié à deux reprises en 2026-08). Mirroir GitHub statique (thanhleviet/Isfinder-sequences, ~6000 IS, snapshot figé ~2020-10) : recherche par nom (IS.csv) ou par séquence (blastn/blastp contre IS.fna/IS.faa)

Compétences : classer un élément mobile candidat trouvé dans un génome bactérien, vérifier la famille/groupe d'une IS déjà nommée dans la littérature, ou chercher des répétitions inversées terminales (IR) de référence ; TOUJOURS essayer ISfinder EN DIRECT d'abord si le site répond ; ce skill est un repli, pas une source plus autorisée que le site lui-même

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

### pathogens-portal

Client de base de données académique. Interroge le Pathogens Portal EMBL-EBI, passerelle européenne publique vers les données biomoléculaires FAIR de génomes bactériens hébergées à l'European Nucleotide Archive (ENA). Lancé en 2023, il indexe 200 000+ espèces et souches déposées dans des études publiées, servies via les Data Hubs ENA standard. Pendant européen de NCBI Pathogen Detection.

Compétences : un projet doit récupérer des séquences de génomes bactériens (anciens ou modernes) déposées à l'ENA/SRA pour une analyse comparative ou phylogénomique ; localiser tous les projets ENA d'une espèce ; bâtir un workflow d'accès aux données centré Europe pour une publication

### pymlst

Academic research toolkit (Guyeux group, FEMTO-ST) for assessing bacterial clonality by core-genome and whole-genome MLST with pyMLST (Biguenet, Bordy, Atchon, Hocquet, Valot, Microbial Genomics 2023). Builds a local SQLite allele database from assembled genomes, calls cgMLST/wgMLST profiles, and produces allelic distance matrices, minimum-spanning trees and per-gene alignments for published research isolates of any bacterium (non-tuberculous mycobacteria, Pseudomonas, Klebsiella, Salmonella, Staphylococcus...)

Compétences : deciding whether isolates form a clonal group, typing a strain against a PubMLST or cgMLST scheme, or producing a distance matrix for a peer-reviewed manuscript

### species-id

Boite a outils de recherche academique pour la genomique des pathogenes evaluee par les pairs (groupe Guyeux, FEMTO-ST). Identification d'espece et de genre bacteriens pour detecter les isolats de recherche publies mal etiquetes M. tuberculosis, par deux methodes : l'API BLAST du NCBI et Mash screen contre une empreinte RefSeq. Etape de controle qualite avant l'ajout d'un genome a la base de recherche du groupe.

Compétences : un isolat de recherche etiquete M ; tuberculosis parait suspect (nombre de SNP aberrant, trop peu ou trop de SPDI, placement phylogenetique curieux) ; importer des genomes depuis SRA ou ENA ; TBannotator signale un echantillon melange ou mal assigne

### thd

Boite a outils de recherche academique pour l'epidemiologie moleculaire evaluee par les pairs (groupe Guyeux, FEMTO-ST). Calcule la Time-scaled Haplotypic Density (THD, Rasigade et al. 2017), mesure publiee de l'expansion relative des lignees bacteriennes, par estimation de densite par noyau sur les distances genetiques deux a deux, parametree par une echelle de temps.

Compétences : calculer la THD sur des profils MIRU-VNTR, des matrices de distance SNP ou des haplotypes WGS d'une collection de recherche ; comparer l'expansion relative entre lignees MTBC ; associer la mesure a des covariables d'etude ; separer le signal recent du signal de long terme pour une publication

### yersinia-resources

Academic research database client (Guyeux group, FEMTO-ST) for genus Yersinia: Yersiniomics multi-omics database, BIGSdb-Pasteur Yersinia (genus-wide cgMLST and species identification), the Y. enterocolitica cgMLST surveillance scheme, plus the routes for plague palaeogenomics of published research isolates (ancient Y. pestis genomes)

Compétences : identifying or typing a Yersinia isolate, looking for a cgMLST scheme for the genus, situating an ancient Y ; pestis genome in the published phylogeny (Black Death, Silk Road, Bronze Age lineages), or transposing an MTBC method to Y ; pestis
