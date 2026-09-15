# Plugin `bioinfo`

> Generic bioinformatics libraries and registries: Biopython, pysam, sequence retrieval, ontologies, the STRING network, Nextflow pipelines. Guyeux group (FEMTO-ST), peer-reviewed research, transverse to all taxa.

Skills propres (canoniques) : **10** ; skills partagés utilisés (symlinks) : **0**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [biopython](#biopython) ; [bioskills](#bioskills) ; [biotools](#biotools) ; [nextflow-development](#nextflow-development) ; [ontologies](#ontologies) ; [pysam](#pysam) ; [scanpy](#scanpy) ; [scikit-bio](#scikit-bio) ; [string-db](#string-db) ; [tooluniverse-sequence-retrieval](#tooluniverse-sequence-retrieval)

### biopython

Guide complet de Biopython, la bibliothèque Python de référence en biologie computationnelle et bioinformatique. Sert à l'analyse de séquences ADN/ARN/protéines, aux entrées-sorties (FASTA, FASTQ, GenBank, PDB), à l'alignement, aux recherches BLAST, à l'analyse phylogénétique et structurale, et à l'accès aux bases NCBI.

Compétences : manipuler des séquences ou fichiers biologiques en Python ; interroger les bases NCBI (Bio.Entrez) ; scripter des analyses phylogénétiques ou d'alignement

### bioskills

Installe 425 skills de bioinformatique couvrant l'analyse de séquences, le RNA-seq, le single-cell, l'appel de variants, la métagénomique, la biologie structurale et 56 autres catégories.

Compétences : mettre en place des capacités de bioinformatique ; quand une tâche bioinfo requiert un skill spécialisé pas encore installé

### biotools

Academic research toolkit (Guyeux group, FEMTO-ST) for querying the ELIXIR bio.tools registry (~30 000 catalogued bioinformatics tools) and, crucially, diffing the result against the skills and knowledge base we already have, so a sweep returns what is genuinely new rather than what we already use

Compétences : asking whether a published tool exists for a task before writing one, looking for independent implementations to cross-check a home-made method, doing a periodic watch on tooling for MTBC, mycobacteria, Yersinia or any bacterium, or checking whether a tool named in a manuscript is registered and still alive

### nextflow-development

Exécute des pipelines de bioinformatique nf-core (rnaseq, sarek, atacseq) sur des données de séquençage.

Compétences : analyser des données RNA-seq, WGS/WES ou ATAC-seq, FASTQ locaux ou jeux publics GEO/SRA ; l'utilisateur mentionne nf-core, Nextflow, appel de variants, expression différentielle, réanalyse GEO, accessions GSE/GSM/SRR, ou création de samplesheet

### ontologies

Index et helper d'accès à l'OBO Foundry (150+ ontologies biomédicales actives) et à sa ressource pivot, la taxonomie NCBI. Fournit des vocabulaires de normalisation canoniques pour espèces et souches (NCBITaxon/LPSN), maladies (DOID), maladies infectieuses (IDO), environnements (ENVO), chimie (ChEBI), lieux (GAZ) et interactions hôte-microbiome (OHMI). Le liant qui rend interopérables les métadonnées d'aadr, enterobase, spaam, bacdive et pubtator.

Compétences : normaliser un champ libre espèce/souche/maladie/hôte/environnement/lieu en identifiant canonique ; ajouter des métadonnées codées par ontologie à un manuscrit ou jeu de données ; vérifier si un terme existe déjà dans une ontologie OBO ; produire des annotations conformes au Linked Data pour un supplément

### pysam

Lit, manipule et ecrit les formats d'alignement genomique (SAM/BAM/CRAM) et de variants (VCF/BCF) depuis Python ; enveloppe de htslib. Note pour le travail bacterien : les references MTBC comme NC_000962.3 sont mono-contig sans prefixe chr, et les coordonnees de fetch()/pileup() sont 0-based semi-ouvertes alors que VCF et SPDI sont 1-based.

Compétences : inspecter la profondeur ou la couverture a une position ; extraire les lectures d'un intervalle ; construire un pileup pour genotyper un site a la main ; filtrer ou fusionner des BAM ; analyser un VCF par programme plutot qu'avec bcftools ; verifier la qualite de mapping derriere un appel de variant

### scanpy

Boite a outils passant a l'echelle pour l'expression genique en cellule unique, batie sur AnnData : controle qualite, normalisation, reduction de dimension, clustering, inference de trajectoires et graphiques. Pour des matrices d'expression bulk ou du clustering generique, preferer scikit-learn.

Compétences : travailler sur un .h5ad ou un objet AnnData ; derouler un pipeline scRNA-seq (clustering Leiden/Louvain, UMAP, genes marqueurs, pseudotemps) ; l'utilisateur mentionne scanpy, AnnData, scVI ou la transcriptomique en cellule unique

### scikit-bio

Bibliothèque de bioinformatique et de statistiques d'écologie des communautés. Fournit structures de données et algorithmes pour séquences, alignements, phylogénétique et analyse de diversité. Essentielle pour la recherche sur le microbiome et la data science écologique : diversité alpha/bêta, ordination (PCoA), arbres phylogénétiques, matrices de distances, PERMANOVA.

Compétences : calculer des métriques de diversité alpha/bêta ; ordination (PCoA) ; manipuler séquences ou matrices de distances ; PERMANOVA et analyse d'écologie des communautés

### string-db

Boîte à outils académique (groupe Guyeux, FEMTO-ST) : client stdlib résilient de l'API REST STRING v12, qui agrège les associations protéine-protéine connues et prédites décomposées en canaux de preuve (voisinage, fusion, co-occurrence, co-expression, expérimental, base de données, fouille de texte). Résout les locus tags en identifiants STRING, liste les partenaires d'interaction, construit des réseaux, lance l'enrichissement fonctionnel (GO/KEGG/Pfam) et le test d'enrichissement PPI. Espèce par défaut : M. tuberculosis H37Rv.

Compétences : obtenir un second avis guilt-by-association sur un gène (surtout hypothétique) ; tester si un opéron/complexe candidat est significativement connecté ; obtenir l'enrichissement fonctionnel d'un petit ensemble de gènes ; Pour l'enrichissement à l'échelle du protéome entier, ne pas utiliser ce skill (télécharger les fichiers en masse)

### tooluniverse-sequence-retrieval

Récupère des séquences biologiques (ADN, ARN, protéines) depuis NCBI et ENA, avec désambiguïsation de gènes, gestion des types d'accession et profils de séquence complets. Produit des rapports détaillés avec métadonnées, références inter-bases et options de téléchargement.

Compétences : récupérer des séquences nucléotidiques ou protéiques, des données de génome ; l'utilisateur mentionne des accessions GenBank, RefSeq ou EMBL
