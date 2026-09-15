# Plugin `mtbc`

> Academic research toolkit for computational genomic studies of the Mycobacterium tuberculosis complex (MTBC): phylogenomics, comparative genomics, lineage assignment, antimicrobial-resistance allele frequencies from published research isolates, and TB surveillance literature. Guyeux group (FEMTO-ST, Universite Marie et Louis Pasteur), peer-reviewed research only.

Skills propres (canoniques) : **42** ; skills partagés utilisés (symlinks) : **0**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [atlas-add-lineage](#atlas-add-lineage) ; [bdd-bridge](#bdd-bridge) ; [binary-coclustering](#binary-coclustering) ; [bioproject-scout](#bioproject-scout) ; [convergent-evolution](#convergent-evolution) ; [denovo-content-qc](#denovo-content-qc) ; [fetch-tbannotator](#fetch-tbannotator) ; [gwas-clonal-lineage](#gwas-clonal-lineage) ; [lineage-comparison](#lineage-comparison) ; [lineage-subdivision](#lineage-subdivision) ; [marker-laminarity](#marker-laminarity) ; [miru-vntr](#miru-vntr) ; [mixed-infection](#mixed-infection) ; [mk-ascertainment](#mk-ascertainment) ; [mtbc-bilan](#mtbc-bilan) ; [mtbc-epistasis](#mtbc-epistasis) ; [mtbc-gene](#mtbc-gene) ; [mtbc-gene-network](#mtbc-gene-network) ; [mtbc-lineages](#mtbc-lineages) ; [mtbc-prospect](#mtbc-prospect) ; [mtbc-reboot](#mtbc-reboot) ; [pangenome-enrichment](#pangenome-enrichment) ; [pectinated-subclade-mining](#pectinated-subclade-mining) ; [phylo-history](#phylo-history) ; [phylo-narrative](#phylo-narrative) ; [phylogeography](#phylogeography) ; [rd-detection](#rd-detection) ; [registres-sans-referent](#registres-sans-referent) ; [resistance-catalogue](#resistance-catalogue) ; [resistance-profiler](#resistance-profiler) ; [sitvitweb](#sitvitweb) ; [snp-distance](#snp-distance) ; [spdi-annotation](#spdi-annotation) ; [sra-geolocate](#sra-geolocate) ; [strain-qc](#strain-qc) ; [tb-cli](#tb-cli) ; [tbannotator-es](#tbannotator-es) ; [tbannotator-mcp](#tbannotator-mcp) ; [tbannotator-upstream](#tbannotator-upstream) ; [tbmonitor-papers](#tbmonitor-papers) ; [tsne-hdbscan](#tsne-hdbscan) ; [variant-reality-check](#variant-reality-check)

### atlas-add-lineage

Boîte à outils du MTBC Atlas (groupe Guyeux, FEMTO-ST) : génère la trame d'une nouvelle page de lignée (meta.yaml, en.md, fr.md) à partir d'un manuscrit évalué ou d'un cahier de labo d'un projet de caractérisation de sous-lignée du MTBC. Lit le projet source (main.tex + strains.csv), produit une page de brouillon aux champs structurés (phylogénie, datation, sélection, codivergence, épidémiologie, hôte, méthodes, références) puis l'injecte dans la base de l'Atlas.

Compétences : une caractérisation de sous-lignée a atteint une maturité publiable et doit être exposée sur l'Atlas ; rafraîchir une fiche existante à partir d'un manuscrit mis à jour

### bdd-bridge

Boîte à outils académique. Pont en lecture seule sur la base MTBC locale curée (bdd/actuelle/, groupe Guyeux, FEMTO-ST), instantané d'isolats publiés stockés en listes de variants SPDI par souche. Expose deux CLI sans dépendances, appelables à l'identique depuis Claude Code et depuis un agent de calcul : bdd_query.py (clades, QC par souche, matrices binaires de SNP, synapomorphies) et phylo_job.py (alignement binaire, RAxML-NG en local ou en paquet SLURM portable).

Compétences : rapporter les effectifs de souches ou le QC par clade pour un manuscrit de phylogénomique ; extraire des synapomorphies pour définir une sous-lignée publiée ; construire une phylogénie d'un clade MTBC à partir de la base locale

### binary-coclustering

Co-clustering binaire (Latent Block Model de Bernoulli) d'une matrice souche x marqueur : rend SIMULTANEMENT les blocs de souches et les blocs de marqueurs qui les definissent, la ou lineage-subdivision et tsne-hdbscan ne rendent que les premiers. Compresse par PROFIL au lieu de sous-echantillonner, donc tient sur les pools geants (L2.2.1, L3, L4.1). Placement de souches NOUVELLES a modele fige, avec mesure de confiance et detection du « ne rentre nulle part »

Compétences : subdiviser une lignee trop grosse pour un arbre focalise, obtenir des synapomorphies candidates avec les clusters, classer des souches de a_ranger avec une probabilite a posteriori, ou detecter une sous-lignee non encore decrite

### bioproject-scout

Recherche des BioProjects NCBI recents, ou d'anciens BioProjects qui recoivent encore de nouveaux runs, pertinents pour le MTBC : filtrables par espece/organisme (M. africanum, M. bovis...), pays, mot-cle de resistance. Recoupe chaque candidat avec TBannotator (tb_ncbi_strain) pour distinguer jamais-ingere / partiellement ingere / deja couvert, enrichit le cache central bioproject_geo, et prepare la liste d'accessions SRA a faire ingerer en priorite (handoff vers /fetch-tbannotator, qui reste le seul point d'ingestion reel)

Compétences : veille periodique sur une espece ou lignee avant de lancer une caracterisation, recherche de cohortes recentes par pays ou phenotype de resistance, verification qu'aucun depot recent n'a ete manque avant de conclure un jeu de donnees complet

### convergent-evolution

Boîte à outils académique (groupe Guyeux, FEMTO-ST) pour détecter l'évolution convergente/parallèle entre lignées MTBC : identification de gènes mutés indépendamment dans plusieurs lignées, analyse d'enrichissement des voies PE/PPE, ESX, PKS/PDIM. Pour vérifier si un gène convergent candidat a des rapports antérieurs dans la littérature, à coupler avec tbmonitor-papers.

Compétences : comparer les schémas de mutation entre lignées animales et humaines ; identifier des gènes sous sélection convergente ; analyser des signatures d'adaptation à l'hôte ; étudier l'évolution des systèmes PE/PPE ou ESX

### denovo-content-qc

Boîte à outils académique (groupe Guyeux, FEMTO-ST) pour caractériser et contrôler le contenu génomique « absent de H37Rv » d'une lignée MTBC, reconstruit par assemblage de novo des reads non mappés. Répond à la question des lignées basales/rares (L8, L9, L10, écotypes animaux) : un contig est-il un vrai module ancestral, un accessoire de pangénome propre à une souche, ou un contaminant ? Trois outils : filtre de contamination, cartographie de pangénome, distribution d'îlots par BLAST.

Compétences : trier vrai-contenu vs contaminant après un assemblage de novo des reads non-mappés-H37Rv ; mesurer l'accessoire propre d'une souche ; prouver qu'un îlot est vraiment spécifique avant de l'écrire ; Complémentaire de strain-qc, species-id et pangenome-enrichment

### fetch-tbannotator

Récupère report.json et génère spdi.txt pour des souches MTBC depuis le serveur TBannotator.

Compétences : peupler les répertoires de la BDD avec les données génomiques manquantes de souches déjà présentes dans la base TBannotator

### gwas-clonal-lineage

Academic research toolkit (Guyeux group, FEMTO-ST) for testing whether a variant, gene or locus is genuinely associated with a clinical or phenotypic trait (drug resistance, tissue tropism, disease form) in a bacterial GWAS on a CLONAL population such as the MTBC, where population structure (lineage) is the dominant confounder and a naive association almost always recovers lineage instead of the phenotype. Packages the full pipeline reforged independently at least 4 times in this repo (mtbc/Rv2566, mtbc/Rv1125, mtbc/ tissue_tropism_mtbc, mtbc/mixed_infections_multimarker) into one reusable module: lineage-stratified Cochran-Mantel-Haenszel (CMH) at BOTH the cohort level (is the lineage itself associated with the phenotype?) and the locus level (does carrying this specific variant stay associated once lineage is controlled?), Breslow-Day heterogeneity test to flag a pooled odds ratio that hides opposite effects between strata, a paucibacillarity/ dropout direction filter, a mappability/paralogy BLAST check to catch cross-mapping artefacts (PE/PPE, esx, pks/pps, lpp, the ~10% of MTBC that is not uniquely mappable at Illumina read length), and a tree-free homoplasy probe via nested clade-code depth. Use this whenever a GWAS hit, a candidate resistance/tropism gene, or a "top-N genes" table from a published bacterial GWAS (Cambau/Bridier-Nahmias, CRyPTIC, or any pyseer/treeWAS/ DBGWAS output) needs to be checked for robustness before being written into a manuscript, do NOT trust a published or in-house GWAS hit on a clonal pathogen without running at least the lineage-stratified locus-level CMH first, even if a cohort-level lineage check already came back non-significant (the two are different questions, see below).

### lineage-comparison

Boite a outils de recherche academique pour la phylogenomique MTBC evaluee par les pairs (groupe Guyeux, FEMTO-ST). Comparaison statistique entre lignees ou sous-lignees du complexe Mycobacterium tuberculosis dans des collections de recherche publiees : test exact de Fisher, khi-deux, intervalles de confiance binomiaux exacts, correction FDR, rapports de cotes et tableaux comparatifs prets pour publication.

Compétences : comparer les frequences d'alleles de resistance aux antimicrobiens entre lignees dans un jeu de recherche ; tester si un trait est significativement associe a une sous-lignee ; produire des tableaux statistiques pour un article ; calculer des intervalles de confiance pour un manuscrit

### lineage-subdivision

Subdivise une lignée MTBC (ou toute bactérie clonale) en sous-lignées, en deux temps. Mode explore : vecteurs de features par SRA (pan-SPDI, positions IS6110, RD) lus dans report.json ou spdi.txt de bdd/actuelle/L<x>/, t-SNE + HDBSCAN, dendrogramme UPGMA, PNG haute résolution et page HTML interactive (dendrogramme D3 lié au t-SNE, comptage de synapomorphies candidates par nœud, exclusion de souche à la volée). Mode optimize : définition des bornes par optimisation multicritères sous contraintes, le bruit étant traité en amont, débruitage puis contraintes de faisabilité (assez de synapomorphies propres multi-signal, ≥5 souches, monophylie) puis objectif MDL de cohérence géographique résolu par programmation dynamique, balayage de lambda vers un front de Pareto, matérialisation réversible. Règle cardinale du skill : un cluster phénétique n'est pas un clade, seul le mode optimize pose des bornes.

Compétences : explorer la structure en sous-lignées d'une lignée ; chercher des clusters de population ; décider si une lignée doit être scindée ; obtenir une taxonomie reproductible et défendable pour des études évolutives (phylogéographie, datation) plutôt qu'un découpage arbitraire ; quand un clade est dense, clonal et sur-séquencé, et qu'un seuil constant sur- ou sous-résout ; Complémentaire de pectinated-subclade-mining (extraction d'un seul sous-clade) : ici on optimise la partition entière

### marker-laminarity

Teste si un jeu de marqueurs binaires (SPDI, RD, IS, spacers) est compatible avec un ARBRE, et si non, dit QUI casse QUOI. Borne combinatoire gratuite, matrice de relations a 5 codes, laminarisation gloutonne, arbre + Newick, et diagnostic de chaque croisement par fragilite avec les souches temoins. Codage 3-etats ON / OFF / UNKNOWN a partir de la couverture reelle des report.json, qui distingue enfin ABSENT de NON COUVERT

Compétences : valider une charpente reconstruite (M ; bovis, L6, L3), verifier que des marqueurs core-exclusifs extraits sont mutuellement compatibles, decider si un clade tient ou repose sur de l'homoplasie, diagnostiquer un arbre instable, ou avant de publier une taxonomie

### miru-vntr

Academic research toolkit (Guyeux group, FEMTO-ST), peer-reviewed MTBC phylogenomics: use MIRU-VNTR loci as a bridge to legacy literature and databases, never as a replacement for WGS/SNP lineage inference. Provides lookup, interpretation limits, and safe handling of MIRU-profiler/TBannotator outputs

Compétences : mapping published MIRU-VNTR profiles to MTBC context, comparing pre-WGS studies, or checking whether a VNTR signal is only historical or epidemiological support

### mixed-infection

Academic research toolkit (Guyeux group, FEMTO-ST) for detecting mixed infections and within-host heterogeneity in published MTBC research isolates, with QuantTB (Anglin/Abeel lab, BMC Genomics 2020) for identifying and quantifying co-infecting strains, and binoSNP (Research Center Borstel, Scientific Reports 2020) for low-frequency antimicrobial-resistance alleles under a binomial model

Compétences : a strain shows an impossible marker combination or an inflated variant count, a resistance allele appears at intermediate frequency, a candidate new sublineage must be ruled out as an artefact of co-infection, or within-host diversity is the object itself

### mk-ascertainment

Test de McDonald-Kreitman et simulation de biais d'échantillonnage pour des variants SPDI MTBC stratifiés par tier. Quantifie si l'excès non-synonyme observé parmi les variants définissant les lignées est réel ou un artefact du filtre d'exclusivité. Un script compagnon écrit une table MK par gène (Dn/Ds/Pn/Ps, alpha, DoS, p de Fisher) consommée par mtbc-pathway-explain, fermant la chaîne du test de sélection à la narration de voie.

Compétences : une caractérisation de sous-lignée rapporte un dN/dS élevé ou un excès non-synonyme parmi les marqueurs core-exclusifs et l'on se demande si un biais d'échantillonnage explique le signal ; Requiert un CSV annoté par tier avec comptes NS/S

### mtbc-bilan

Bilan complet et honnête d'un projet MTBC : état consolidé des connaissances acquises et plan d'action pour la suite. Le bilan ne raconte pas le cheminement itératif : il consolide ce qui est actuellement su, comment cela a été établi, et ce qui reste à faire d'après le cahier. En cas de conflit entre entrées, on garde la dernière version consolidée. Le mode --full compare tous les projets MTBC.

Compétences : faire le point sur un projet ; décider quoi faire ensuite ; préparer une réunion ; arbitrer entre plusieurs projets ; évaluer si un projet est prêt à être clos ; repartir après une pause

### mtbc-epistasis

Boite a outils de recherche academique (groupe Guyeux, FEMTO-ST), phylogenomique MTBC evaluee par les pairs : detecte l'evolution COMPENSATOIRE et l'epistasie de la resistance dans le complexe Mycobacterium tuberculosis, en POLARISANT le signal par lignee pour ecarter le piege de l'homoplasie. Teste si une mutation de resistance couteuse (rpoB dans la RRDR) co-occurre avec une mutation compensatoire candidate (rpoC, rpoA ; ahpC pour katG) plus que le hasard, non pas globalement (ce qui confond avec les marqueurs de lignee) mais entre isolats resistants et non resistants de la MEME lignee, agrege par Mantel-Haenszel.

Compétences : se demander si les clones resistants, surtout importes, sont deja compenses donc adaptes et transmissibles ; tester l'affirmation d'une resistance transmise clonalement ; distinguer une vraie compensation d'un simple marqueur de sous-lignee ; alimenter un volet phylodynamique

### mtbc-gene

Boite a outils de recherche academique (groupe Guyeux, FEMTO-ST), phylogenomique MTBC evaluee par les pairs : la couche gene et proteine de H37Rv. A partir d'un nom de gene (katG) ou d'un identifiant de locus Rv (Rv1908c) : fonction curee hors ligne d'abord (UniProt, EC, Pfam, STRING, conservation) ; impact ESM-1v en rapport de vraisemblance d'une mutation ponctuelle (katG S315T) ; narration de voie ou d'ensemble de genes, y compris depuis une table de McDonald-Kreitman ; recherche a l'echelle de l'atlas, statistiques et couches d'evidence via l'API REST mtbc.gclab.fr.

Compétences : savoir ce que fait un gene ou un locus Rv ; estimer si une substitution est probablement deleteres ; formuler une hypothese sur un gene non caracterise ; narrer un ensemble de genes ou une voie pour un manuscrit ; un nom de gene ou un identifiant Rv apparait dans une question de biologie MTBC

### mtbc-gene-network

Boite a outils de recherche academique pour la genomique fonctionnelle MTBC evaluee par les pairs (groupe Guyeux, FEMTO-ST). Interroge le reseau d'interactions geniques MTBC comme un graphe, en local d'abord, depuis le reseau STRING proteome-entier precalcule par le groupe (environ 4000 genes, environ 38 000 aretes de confiance moyenne, evidence par canal), charge avec networkx. Expose les operations de graphe absentes du pipeline d'annotation : voisins d'interaction d'un gene, sous-reseau induit d'un ensemble de genes, plus court chemin entre deux genes, hubs par degre et centralite d'intermediarite, modules fonctionnels par detection de communautes, et culpabilite par association pour un locus Rv non caracterise. L'API STRING (skill string-db) n'est que le recours pour un gene absent en local.

Compétences : trouver avec quoi un gene interagit ; construire un sous-reseau d'interactions pour une voie ; localiser les genes hubs ou goulots de l'interactome ; detecter des modules de type operon ; formuler une hypothese de fonction depuis un voisinage ; produire une evidence de reseau pour une figure de manuscrit

### mtbc-lineages

Source faisant autorité sur les définitions de lignées du MTBC, les hiérarchies de sous-lignées et les marqueurs SNP/SPDI. La hiérarchie source-de-vérité est fixée dans SOURCES_OF_TRUTH.md : le placement vivant dans bdd/actuelle/ et son registre barcode_complete.tsv font foi ; lignees.py (clé « moi » = Guyeux) est une banque de marqueurs SPDI historique, fiable pour les lignées majeures stables mais possiblement désynchronisée pour les sous-lignées issues du cycle multi-signal.

Compétences : chercher le marqueur définissant une lignée ; trouver le parent d'une sous-lignée ; déterminer à quelle lignée appartient un SPDI ; confirmer la hiérarchie L1 à L10 ; réconcilier des classifications contradictoires ; citer la publication d'origine (confirmer titre/auteurs/DOI via tbmonitor-papers) ; À préférer aux requêtes TBannotator ou lectures CSV ad hoc pour les faits de lignée

### mtbc-prospect

Boite a outils de recherche academique (groupe Guyeux, FEMTO-ST), phylogenomique MTBC evaluee par les pairs : moteur d'ideation divergente qui genere de nouvelles pistes de recherche pour un projet MTBC et les inscrit dans pistes.md. Parcourt des axes lateraux interdisciplinaires (coevolution avec l'hote humain, histoire genetique humaine, routes commerciales, reseaux de genes et evolution compensatoire, conformation 3D des proteines, place du MTBC parmi les mycobacteries), audite chaque skill disponible comme lentille de decouverte, propose de nouveaux skills a forger, relit retrospectivement pistes.md et le cahier de labo, auto-challenge chaque idee (contre-argument le plus fort, modele nul falsifiant, gain contre cout) et inscrit les survivantes.

Compétences : un projet a besoin de directions neuves ; un brainstorming d'angles originaux ; la gap-analysis de mtbc-bilan --deepen ne suffit pas ; trancher s'il reste quelque chose a explorer

### mtbc-reboot

Reboot complet d'un projet MTBC. Archive toute la connaissance accumulée (découvertes, affirmations, scripts, données) dans archives/YYYY-MM-DD_reboot/ avec tags de confiance (vérifié / à vérifier / incertain / réfuté), réinitialise le projet en structure propre, scanne les projets voisins pour convergences, et réanalyse affirmation par affirmation avec revue critique du code source (littérature via tbmonitor avant WebSearch). Bloque la rédaction tant que la réanalyse n'est pas complète.

Compétences : un projet a accumulé trop de dérive, de résultats périmés ou d'affirmations non vérifiées pour continuer incrémentalement ; redémarrer une étude après une longue pause à héritage incertain ; quand claim-check révèle trop d'affirmations non vérifiées ; pivoter la direction d'un projet en préservant l'acquis

### pangenome-enrichment

Analyse de pangénome et enrichissement fonctionnel par lignée MTBC : classification core/soft-core/shell/cloud des gènes, enrichissement de voies KEGG, analyse du contenu génique spécifique de lignée.

Compétences : comparer le contenu génique entre lignées ; identifier des gènes spécifiques de lignée ; réaliser un enrichissement KEGG sur des gènes différentiels ; analyser la structure du pangénome pour un article

### pectinated-subclade-mining

Méthodologie d'extraction itérative des sous-lignées pectinées au sein d'une lignée MTBC (ou autre bactérie clonale) en utilisant les SPDI core présents dans le sous-clade candidat et absents des autres sous-clades et lignées externes proches. Travaille sur les fichiers spdi.txt directement sur disque (pas de SQL), filtre per-pool (jamais global) pour garantir l'exclusivité, et produit un répertoire dédié par sous-clade avec son fichier de marqueurs TSV.

Compétences : on observe une topologie pectinée dans un arbre RAxML focalisé et l'on veut extraire itérativement les sous-clades pour raffiner la taxonomie ; on suspecte qu'un clade trop hétérogène contient plusieurs sous-lignées ; on veut un classifieur SPDI pour reclasser des souches en attente

### phylo-history

Rédige un paragraphe de manuscrit décrivant le placement phylogénétique d'une souche MTBC à travers les arbres où elle a figuré. Exploite investigate_phylo/history/ et les fichiers Newick archivés pour produire une narration sourcée sur les voisins, la sister clade, la stabilité de l'assignation et le voisinage inter-reconstructions.

Compétences : rédiger la section Résultats d'un article de lignée et justifier le placement d'une souche ; documenter pourquoi une souche a été retenue, reclassée ou exclue ; préparer un supplément décrivant la position phylogénétique de souches aberrantes ; répondre à un relecteur demandant des preuves sur la lignée d'une souche précise

### phylo-narrative

Rédige un paragraphe pour un manuscrit scientifique décrivant le placement phylogénétique d'une souche MTBC à travers les arbres dans lesquels elle a figuré. Exploite investigate_phylo/history/ et les fichiers Newick archivés pour produire une narration sourcée sur les voisins, la sister clade, la stabilité de l'assignation et le voisinage inter-reconstructions

Compétences : writing the Results section of a lineage paper and needing a justified sentence about a strain's placement ; documenting why a strain was retained, reclassified or excluded ; preparing supplementary material describing the phylogenetic position of outlier strains ; responding to a reviewer asking for evidence about a specific strain's lineage

### phylogeography

Boîte à outils académique (groupe Guyeux, FEMTO-ST) pour l'analyse de distribution géographique des lignées MTBC via TBannotator : tableau croisé pays × lignée, cartes choroplèthes, barplots empilés et indices de diversité géographique. Pour retrouver des études phylogéographiques antérieures sur une lignée ou un pays, à coupler avec tbmonitor-papers.

Compétences : cartographier la distribution géographique d'une lignée pour un article ; comparer la structure géographique entre sous-lignées ; produire figures de distribution et tables supplémentaires ; identifier des points chauds géographiques

### rd-detection

Academic research toolkit (Guyeux group, FEMTO-ST) for regions of difference (RD) in MTBC genomes of published research isolates: reading the RD calls the TBannotator pipeline already produces, and cross-checking them with an independent published implementation (RDscan, Bespiatykh et al., mSphere 2021)

Compétences : an RD-based argument enters a manuscript, a clade is defined by a deletion, a new candidate deletion (CUS) needs confirming, or an RD call contradicts the literature and one needs to know which side is wrong

### registres-sans-referent

Auditer et reparer les ENONCES d'un depot dont la nomenclature a bouge : noms de clades qui ne designent plus rien, effectifs perimes, enonces refutes qui survivent ailleurs, et le cas qu'aucun test d'existence n'attrape, le label VIVANT mais FAUX d'une table de correspondance. Mesure d'abord (combien, ou, dans quel fichier), repare ensuite en posant un renvoi de peremption en tete de chaque entree concernee, sans jamais reecrire l'entree elle-meme

Compétences : une lignee vient d'etre renommee, re-peignee ou re-decoupee ; un effectif cite ne correspond plus au disque ; un resultat s'appuie sur un clade dont le nom a change ; une base de connaissances partagee entre projets nomme des clades ; avant de reutiliser une calibration ou une mesure datee ; a chaque ouverture d'iteration sur un projet taxonomique

### resistance-catalogue

Boite a outils de recherche academique pour la genomique de la resistance aux antimicrobiens du MTBC evaluee par les pairs (groupe Guyeux, FEMTO-ST). Interroge ou reconstruit le catalogue de mutations OMS et tb-profiler, resout HGVS vers SPDI, profile ou predit le phenotype d'un isolat de recherche publie, lance une GWAS tenant compte des lignees pour les determinants non catalogues, et construit le dossier mecanistique d'un variant (association empirique, litterature TB, rapport de vraisemblance ESM-1v, contexte 3D).

Compétences : savoir si un variant est un determinant de resistance connu du catalogue publie ; connaitre le phenotype predit d'un isolat de recherche ; identifier les determinants expliquant un phenotype inexplique dans une collection d'etude ; comprendre comment une entree de catalogue a ete graduee

### resistance-profiler

Boîte à outils académique. Calcule des synthèses, au sens de la littérature publiée, des fréquences alléliques de résistance antimicrobienne entre lignées du MTBC, en interrogeant la base de recherche curée TBannotator (groupe Guyeux, FEMTO-ST). Produit des tableaux croisés et des fichiers d'annotation iTOL pour des publications phylogénomiques évaluées. Pour contextualiser dans la littérature publiée, utiliser en parallèle tbmonitor-papers.

Compétences : rédiger un article de phylogénomique rapportant des fréquences alléliques de résistance par lignée ; produire tables et figures supplémentaires ; générer des pistes d'annotation iTOL pour un manuscrit sur l'évolution du MTBC

### sitvitweb

Interroge la base de spoligotypes SITVIT2 (Institut Pasteur de Guadeloupe) pour les assignations de spoligotype MTBC, les recherches de SIT, les noms de clades (Beijing, LAM, Haarlem, T1...) et les distributions géographiques. Accès navigateur uniquement (pas d'API REST).

Compétences : convertir un spoligotype octal en numéro SIT ; identifier le clade d'une souche ; trouver la distribution géographique d'un SIT ; croiser les champs spol43/spol98 des métadonnées TBannotator

### snp-distance

Boîte à outils académique (groupe Guyeux, FEMTO-ST) : calcule des matrices de distances SNP par paires à partir de données SPDI présence/absence. Interroge TBannotator pour les profils SPDI et construit une matrice de distance de Hamming/Jaccard.

Compétences : calculer des distances génétiques entre souches MTBC ; préparer l'entrée de t-SNE+HDBSCAN ou THD ; identifier des clusters de transmission par seuil de SNP ; construire des matrices de distances pour arbres NJ ou génétique des populations

### spdi-annotation

Boîte à outils académique (groupe Guyeux, FEMTO-ST) : annote les variants SPDI du MTBC avec gène, effet (faux-sens/synonyme/stop/décalage), changement d'acide aminé et catégorie fonctionnelle. Interroge d'abord TBannotator pour les annotations existantes, puis se replie sur une annotation locale GenBank/GFF3. Pour vérifier si un SPDI (surtout à fort impact) a déjà été décrit dans la littérature, à coupler avec tbmonitor-papers.

Compétences : annoter une liste de variants SPDI pour un article MTBC ; construire des tables supplémentaires avec impact fonctionnel ; classer les variants par type d'effet

### sra-geolocate

Consolidation de l'origine et de la date d'une souche SRA, ou construction d'un dataset de SRA correspondant à une zone géographique. Deux cascades parallèles (lieu + date) puisent dans les mêmes sources : métadonnées BioSample (geo_loc_name, lat_lon, collection_date), BioProject, publications PubMed/Europe PMC liées, supplementary materials, texte intégral PDF. Chaque résultat est assorti d'un score de confiance et de sa source, et distingue lieu de collection vs séquençage, date de collection vs publication.

Compétences : enrichir la métadonnée d'une souche dont geo_loc_name ou collection_date est vague ou vide ; construire une cohorte TB par région ; vérifier l'origine et la date revendiquées d'un SRA avant inclusion ; détecter des incohérences entre BioSample, BioProject et publications ; extraire les métadonnées par souche depuis les supplements open access

### strain-qc

Boite a outils de recherche academique pour la phylogenomique MTBC evaluee par les pairs (groupe Guyeux, FEMTO-ST). Controle qualite d'un genome de recherche MTBC avant integration en base ou dans un arbre phylogenetique : 7 criteres (chimere intra-MTBC, taux GC, couverture, profondeur, SPDI contre lignee, melange inter-especes, qualite de mapping), verdict PASS/WARN/FAIL justifie, genome unique ou lot.

Compétences : importer depuis SRA ou ENA ; filtrer avant une reconstruction phylogenetique ; face a un genome au placement aberrant ou a longue branche ; auditer la base ; decider des exclusions de get_phylo.py

### tb-cli

CLI de recherche académique pour les études de génomique comparative du MTBC, via la commande tb. Utilisée par le groupe Guyeux (FEMTO-ST) pour des publications évaluées sur la phylogénomique et la biologie évolutive du MTBC.

Compétences : le contexte mentionne des lignées MTBC, des souches de recherche déposées, des annotations SPDI/SNP, des variants publiés dans des gènes comme katG/rpoB/embB, le catalogage d'allèles de résistance, l'analyse des régions de différence, la fouille de littérature MTBC ou des requêtes à la base TBannotator

### tbannotator-es

Academic research database client for the TBannotator Elasticsearch indices (strain, snp, gene, is, rd) used in peer-reviewed MTBC phylogenomics by the Guyeux group (FEMTO-ST). Exposes fields absent from the PostgreSQL server: CRISPR spacer statistics, fastp quality and mapping metrics, missing genes and regions of difference with coverage, insertion sequences, published antimicrobial-resistance allele annotations with source DOI, and sample metadata (coordinates, host, isolation source, BioProject). Also reproduces the web interface's clade-exclusivity score

Compétences : looking for markers exclusive to a clade, filtering published research isolates on sequencing quality, or querying IS/RD/CRISPR content of strains

### tbannotator-mcp

Interroge le serveur MCP TBannotator v3.6 (~274 800 génomes MTBC) via PostgreSQL. Accède aux métadonnées de souches, classifications de lignées (Coll, Gagneux, Senelle...), fréquences SNP/SPDI, arbres phylogénétiques (NJ, RAxML) et profils de résistance.

Compétences : compter les souches par lignée ; obtenir les métadonnées d'un code de lignée ; trouver des marqueurs core-exclusifs ; valider des fichiers supplémentaires ; construire des arbres phylogénétiques pour un article de caractérisation de lignée MTBC

### tbannotator-upstream

Academic research tooling: watch the upstream public GitLab of the TBannotator webapp (gitlab.com/tbannotator/webapp) for changes that would silently invalidate our MTBC skills: repository commits, live FastAPI routes, Elasticsearch document schema, and the definition of the clade-exclusivity score. Peer-reviewed phylogenomics context, Guyeux group (FEMTO-ST)

Compétences : a TBannotator query returns unexpectedly empty results, before relying on the Elasticsearch field names in an analysis, or to review what changed upstream since the last pinned state

### tbmonitor-papers

Interroge le serveur MCP tbmonitor, miroir SQLite pré-indexé en lecture seule du corpus PubMed tuberculose (~330 000 articles de 1848 à aujourd'hui, ~81 % TB-spécifiques). Expose titre, résumé, DOI, lien PubMed, journal, date, plus auteurs / mots-clés / termes MeSH / types de publication / affiliations / liste de références en tableaux JSON directement interrogeables via json_each(). Réponse sub-seconde sur des recherches filtrées.

Compétences : récupérer des articles TB par auteur, terme MeSH, mot-clé, journal ou plage d'années ; assembler une liste BibTeX pour une revue ou un financement ; vérifier qu'une affirmation a une couverture antérieure ; relier des résultats de souches TBannotator à la littérature ; bâtir un état de l'art rapide avant de recourir à lit-review

### tsne-hdbscan

Réduction de dimension t-SNE + clustering par densité HDBSCAN pour explorer la diversité génomique du MTBC. Fonctionne sur des matrices SPDI présence/absence, des matrices de distances SNP ou des profils MIRU-VNTR.

Compétences : explorer la structure de population des souches MTBC ; identifier des clusters de transmission ; détecter aberrants ou lignées mal classées ; visualiser les relations génomiques en 2D ; clustering non supervisé sans fixer le nombre de clusters

### variant-reality-check

Academic research toolkit (Guyeux group, FEMTO-ST), peer-reviewed MTBC phylogenomics: decide whether a called variant is REAL and which allele is ANCESTRAL, before it becomes a claim in a manuscript. Two complementary gestes. (1) Sequence context of a called indel: placement ambiguity after normalisation (the measure that actually settles polymerase slippage, not homopolymer length), tandem repeats, local GC read against the genome background, k-mer uniqueness against cross-mapping, each with a null model built by sampling positions and measuring them exactly like the site. (2) Polarisation on CLOSED COMPLETE ASSEMBLIES instead of variant calls, locating the site by its unique flanks and measuring the gap between them, which answers coverage, mapping and calling artefacts at once. Also translates a CDS to the REAL stop rather than to the annotated boundary

Compétences : an indel or frameshift is suspected to be a calling artefact, a variant is about to be called a synapomorphy, a `disrupt_frac` or a snpEff HIGH label is about to be written as pseudogenisation, an outgroup appears to LACK a variant, or a reference annotation looks unrepresentative
