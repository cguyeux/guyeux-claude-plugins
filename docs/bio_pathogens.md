# Plugin `bio_pathogens`

> Academic research toolkit for computational genomic studies of bacterial pathogens, focused on Mycobacterium tuberculosis complex (MTBC) phylogenomics, comparative genomics, and public-health surveillance literature. Used by the Guyeux group (FEMTO-ST, University of Franche-Comte) for peer-reviewed scientific publications on pathogen evolution and host-pathogen co-evolution.

## Rôle dans un projet M. tuberculosis

Cœur du dispositif. Rassemble les skills qui touchent directement le complexe Mycobacterium tuberculosis (MTBC) et les pathogènes apparentés : accès aux génomes de référence et aux isolats de recherche publiés, fréquences alléliques de résistance aux antituberculeux telles que rapportées dans la littérature évaluée par des pairs, assignation de lignées, bases de données génomiques spécialisées. C'est le plugin qu'on active quand le travail porte effectivement sur M. tuberculosis.

Skills propres (canoniques) : **49** ; skills partagés utilisés (symlinks) : **38**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [active-site-check](#active-site-check) ; [ancestral-reconstruction](#ancestral-reconstruction) ; [atlas-add-lineage](#atlas-add-lineage) ; [bacdive](#bacdive) ; [bdd-bridge](#bdd-bridge) ; [beast2-dating](#beast2-dating) ; [coevolution](#coevolution) ; [convergent-evolution](#convergent-evolution) ; [denovo-content-qc](#denovo-content-qc) ; [enterobase](#enterobase) ; [fetch-tbannotator](#fetch-tbannotator) ; [helicobacter-pylori-phylogeography](#helicobacter-pylori-phylogeography) ; [host-pathogen-pair](#host-pathogen-pair) ; [lineage-comparison](#lineage-comparison) ; [lineage-subdivision](#lineage-subdivision) ; [mbovis](#mbovis) ; [mk-ascertainment](#mk-ascertainment) ; [molecular-clock](#molecular-clock) ; [mtbc-bilan](#mtbc-bilan) ; [mtbc-epistasis](#mtbc-epistasis) ; [mtbc-gene](#mtbc-gene) ; [mtbc-gene-network](#mtbc-gene-network) ; [mtbc-lineages](#mtbc-lineages) ; [mtbc-prospect](#mtbc-prospect) ; [mtbc-reboot](#mtbc-reboot) ; [mycobacterium-leprae](#mycobacterium-leprae) ; [ncbi-pathogen-detection](#ncbi-pathogen-detection) ; [pangenome-enrichment](#pangenome-enrichment) ; [pathogens-portal](#pathogens-portal) ; [pectinated-subclade-mining](#pectinated-subclade-mining) ; [phylogeography](#phylogeography) ; [raxml](#raxml) ; [resistance-catalogue](#resistance-catalogue) ; [resistance-profiler](#resistance-profiler) ; [sitvitweb](#sitvitweb) ; [snp-distance](#snp-distance) ; [spaam-ancient-metagenome-dir](#spaam-ancient-metagenome-dir) ; [spaam-community](#spaam-community) ; [spdi-annotation](#spdi-annotation) ; [species-id](#species-id) ; [sra-geolocate](#sra-geolocate) ; [strain-qc](#strain-qc) ; [string-db](#string-db) ; [tb-cli](#tb-cli) ; [tbannotator-mcp](#tbannotator-mcp) ; [tbmonitor-papers](#tbmonitor-papers) ; [thd](#thd) ; [triangulate-route](#triangulate-route) ; [tsne-hdbscan](#tsne-hdbscan)

### active-site-check

Boîte à outils de recherche académique (groupe Guyeux, FEMTO-ST). Valide une requalification d'enzyme « même repli → enzyme active » en vérifiant que les résidus catalytiques de l'enzyme M-CSA (Mechanism and Catalytic Site Atlas, EBI) appariée par Foldseek sont bien alignés et conservés dans la protéine requête. C'est la brique de rigueur qui manque à un transfert de fonction purement structural : un repli partagé n'implique pas un site actif fonctionnel.

Compétences : un gène « hypothetical »/dark du MTBC a un hit Foldseek vers une enzyme connue et il faut trancher « enzyme active vs simple homologie de repli » avant d'écrire une fonction ; annoter un protéome bactérien par structure en graduant la confiance des requalifications enzymatiques ; répondre à un relecteur demandant des preuves de site actif

### ancestral-reconstruction

Boîte à outils de recherche académique (groupe Guyeux, FEMTO-ST) pour la reconstruction d'états ancestraux sur les phylogénies MTBC en vue de publications phylogéographiques évaluées par des pairs. Reconstruit les états géographiques ancestraux : parcimonie (Fitch), postérieurs marginaux en maximum de vraisemblance (MPPA), cartographie stochastique, génération de XML DTA pour BEAST et export de flèches de migration vers iTOL.

Compétences : identifier quand et combien de fois une lignée a migré entre régions ; comparer les schémas de migration aux mouvements humains ; annoter des phylogénies avec les localisations ancestrales ; préparer des analyses de traits discrets sous BEAST

### atlas-add-lineage

Boîte à outils du MTBC Atlas (groupe Guyeux, FEMTO-ST) : génère la trame d'une nouvelle page de lignée (meta.yaml, en.md, fr.md) à partir d'un manuscrit évalué ou d'un cahier de labo d'un projet de caractérisation de sous-lignée du MTBC. Lit le projet source (main.tex + strains.csv), produit une page de brouillon aux champs structurés (phylogénie, datation, sélection, codivergence, épidémiologie, hôte, méthodes, références) puis l'injecte dans la base de l'Atlas.

Compétences : une caractérisation de sous-lignée a atteint une maturité publiable et doit être exposée sur l'Atlas ; rafraîchir une fiche existante à partir d'un manuscrit mis à jour

### bacdive

Client de base de données académique (groupe Guyeux, FEMTO-ST). Interroge BacDive, la métabase DSMZ de diversité bactérienne, plus grand dépôt structuré d'informations sur les souches (97 000+ souches, 2,6 millions de données, 1 000+ champs) : taxonomie, morphologie, physiologie, métabolisme, culture, source d'isolement, niveau de biosécurité, sensibilité aux antibiotiques. Ressource de référence pour les métadonnées phénotypiques et écologiques des souches types.

Compétences : récupérer des données phénotypiques pour une espèce bactérienne utile à un travail TB ou paléopathogène ; consulter des conditions de culture ; vérifier un niveau de biosécurité ; trouver une souche type de référence ; enrichir une analyse génomique d'un contexte phénotypique

### bdd-bridge

Boîte à outils académique. Pont en lecture seule sur la base MTBC locale curée (bdd/actuelle/, groupe Guyeux, FEMTO-ST), instantané d'isolats publiés stockés en listes de variants SPDI par souche. Expose deux CLI sans dépendances, appelables à l'identique depuis Claude Code et depuis un agent de calcul : bdd_query.py (clades, QC par souche, matrices binaires de SNP, synapomorphies) et phylo_job.py (alignement binaire, RAxML-NG en local ou en paquet SLURM portable).

Compétences : rapporter les effectifs de souches ou le QC par clade pour un manuscrit de phylogénomique ; extraire des synapomorphies pour définir une sous-lignée publiée ; construire une phylogénie d'un clade MTBC à partir de la base locale

### beast2-dating

Boite a outils de recherche academique pour la datation moleculaire bayesienne des phylogenies du complexe Mycobacterium tuberculosis (MTBC) avec BEAST2, pour la recherche phylogenomique evaluee par les pairs. Genere un XML BEAST2 correct pour des alignements SNP BINAIRES (presence/absence 0/1), le format produit par le pipeline TB du groupe Guyeux (FEMTO-ST), et execute BEAST2 sans affichage. Corrige les deux defauts qui font echouer silencieusement la convergence des runs BEAST2 sur donnees binaires MTBC.

Compétences : dater un noeud ou une lignee avec BEAST2 ; ecrire ou deboguer un XML BEAST2 ; choisir une horloge ou un prior d'arbre pour le MTBC ; diagnostiquer un ESS qui ne monte pas

### coevolution

Boîte à outils académique (groupe Guyeux, FEMTO-ST) pour les tests statistiques de co-divergence MTBC-humain et de structure géographique : test de Mantel, Mantel partiel, isolement par la distance, PACo (approche procustéenne de cophylogénie), FST (Weir & Cockerham) et AMOVA.

Compétences : tester si la diversité génétique du MTBC corrèle avec la distance géographique ; comparer la structure des populations bactériennes et humaines ; quantifier la différenciation entre populations MTBC de pays ou régions distincts

### convergent-evolution

Boîte à outils académique (groupe Guyeux, FEMTO-ST) pour détecter l'évolution convergente/parallèle entre lignées MTBC : identification de gènes mutés indépendamment dans plusieurs lignées, analyse d'enrichissement des voies PE/PPE, ESX, PKS/PDIM. Pour vérifier si un gène convergent candidat a des rapports antérieurs dans la littérature, à coupler avec tbmonitor-papers.

Compétences : comparer les schémas de mutation entre lignées animales et humaines ; identifier des gènes sous sélection convergente ; analyser des signatures d'adaptation à l'hôte ; étudier l'évolution des systèmes PE/PPE ou ESX

### denovo-content-qc

Boîte à outils académique (groupe Guyeux, FEMTO-ST) pour caractériser et contrôler le contenu génomique « absent de H37Rv » d'une lignée MTBC, reconstruit par assemblage de novo des reads non mappés. Répond à la question des lignées basales/rares (L8, L9, L10, écotypes animaux) : un contig est-il un vrai module ancestral, un accessoire de pangénome propre à une souche, ou un contaminant ? Trois outils : filtre de contamination, cartographie de pangénome, distribution d'îlots par BLAST.

Compétences : trier vrai-contenu vs contaminant après un assemblage de novo des reads non-mappés-H37Rv ; mesurer l'accessoire propre d'une souche ; prouver qu'un îlot est vraiment spécifique avant de l'écrire ; Complémentaire de strain-qc, species-id et pangenome-enrichment

### enterobase

Client de base de données académique (groupe Guyeux, FEMTO-ST). Interroge EnteroBase (groupe Achtman, Warwick), base de génomes et plateforme cgMLST/HierCC de référence pour Salmonella, Escherichia, Yersinia, Clostridioides, Helicobacter, Vibrio et Moraxella. Ressource centrale pour la phylogénie historique de Yersinia pestis (peste, Route de la soie, Peste noire), les pandémies de Vibrio cholerae et l'épidémiologie bactérienne à l'échelle génomique.

Compétences : construire des récits historiques autour de pathogènes bactériens non-MTBC ; corréler des lignées de Y ; pestis à la Route de la soie ou à la Peste noire ; étudier les pandémies de choléra ; utiliser H ; pylori comme proxy des migrations humaines ; transposer la méthodologie TBannotator à un autre pathogène entérique

### fetch-tbannotator

Récupère report.json et génère spdi.txt pour des souches MTBC depuis le serveur TBannotator.

Compétences : peupler les répertoires de la BDD avec les données génomiques manquantes de souches déjà présentes dans la base TBannotator

### helicobacter-pylori-phylogeography

Cadre de référence sur la phylogéographie d'Helicobacter pylori comme proxy des migrations humaines, cas paradigmatique de coévolution hôte-pathogène (Linz 2007 ; Moodley 2009/2012 ; Maixner 2016 sur l'Homme de Similaun). Documente les sept populations de H. pylori, leurs distributions géographiques et le modèle méthodologique pour transposer l'approche à M. tuberculosis. Essentiel pour situer la phylogéographie du MTBC dans le paradigme « les pathogènes comme historiens ».

Compétences : cadrer un récit de séminaire « les pathogènes courant avec leurs hôtes » sur un précédent canonique ; construire une slide comparative H ; pylori vs M ; tuberculosis ; transposer la méthodologie de Linz au MTBC ; référencer les ancrages classiques de la littérature de coévolution

### host-pathogen-pair

Boîte à outils d'éco-anthropologie (groupe Guyeux, FEMTO-ST). Génère des tables de co-occurrence géo-temporelle de paires hôte ancien / microorganisme ancien à partir de deux corpus ouverts : SPAAM AncientMetagenomeDir (génomique microbienne ancienne, dont Mycobacterium, Yersinia pestis, Salmonella) et le catalogue AADR de génomes humains anciens (Reich Lab, v66, 16 000+ individus). Sortie : un TSV de paires candidates classées par distance de Haversine et recouvrement temporel.

Compétences : planifier un projet de coévolution hôte-microorganisme ; valider les paires disponibles pour une région/période ; préparer un séminaire ou une candidature académique ; documenter l'absence de paires (résultat négatif valorisable)

### lineage-comparison

Boite a outils de recherche academique pour la phylogenomique MTBC evaluee par les pairs (groupe Guyeux, FEMTO-ST). Comparaison statistique entre lignees ou sous-lignees du complexe Mycobacterium tuberculosis dans des collections de recherche publiees : test exact de Fisher, khi-deux, intervalles de confiance binomiaux exacts, correction FDR, rapports de cotes et tableaux comparatifs prets pour publication.

Compétences : comparer les frequences d'alleles de resistance aux antimicrobiens entre lignees dans un jeu de recherche ; tester si un trait est significativement associe a une sous-lignee ; produire des tableaux statistiques pour un article ; calculer des intervalles de confiance pour un manuscrit

### lineage-subdivision

Subdivise une lignée MTBC (ou toute bactérie clonale) en sous-lignées, en deux temps. Mode explore : vecteurs de features par SRA (pan-SPDI, positions IS6110, RD) lus dans report.json ou spdi.txt de bdd/actuelle/L<x>/, t-SNE + HDBSCAN, dendrogramme UPGMA, PNG haute résolution et page HTML interactive (dendrogramme D3 lié au t-SNE, comptage de synapomorphies candidates par nœud, exclusion de souche à la volée). Mode optimize : définition des bornes par optimisation multicritères sous contraintes, le bruit étant traité en amont, débruitage puis contraintes de faisabilité (assez de synapomorphies propres multi-signal, ≥5 souches, monophylie) puis objectif MDL de cohérence géographique résolu par programmation dynamique, balayage de lambda vers un front de Pareto, matérialisation réversible. Règle cardinale du skill : un cluster phénétique n'est pas un clade, seul le mode optimize pose des bornes.

Compétences : explorer la structure en sous-lignées d'une lignée ; chercher des clusters de population ; décider si une lignée doit être scindée ; obtenir une taxonomie reproductible et défendable pour des études évolutives (phylogéographie, datation) plutôt qu'un découpage arbitraire ; quand un clade est dense, clonal et sur-séquencé, et qu'un seuil constant sur- ou sous-résout ; Complémentaire de pectinated-subclade-mining (extraction d'un seul sous-clade) : ici on optimise la partition entière

### mbovis

Client de base de données académique pour M. bovis et le spoligotypage MTBC animal. Interroge mbovis.org (base internationale de référence Spoligo Bovis) pour l'attribution de numéros SB à partir d'isolats publiés, les conversions de format (BIN/OCT/HEX) et la distribution géographique des profils animaux (M. bovis, M. caprae, M. pinnipedii, M. orygis, M. microti). Cas d'usage du groupe Guyeux : attribuer des SB, croiser avec SITVIT2, identifier les complexes clonaux (Eu1, Eu2, Af1, Af2).

Compétences : convertir un profil de spoligotype M ; bovis en numéro SB ; consulter un profil SB connu ; télécharger la base SB complète ; interroger des souches par pays ; identifier le complexe clonal d'un isolat MTBC animal

### mk-ascertainment

Test de McDonald-Kreitman et simulation de biais d'échantillonnage pour des variants SPDI MTBC stratifiés par tier. Quantifie si l'excès non-synonyme observé parmi les variants définissant les lignées est réel ou un artefact du filtre d'exclusivité. Un script compagnon écrit une table MK par gène (Dn/Ds/Pn/Ps, alpha, DoS, p de Fisher) consommée par mtbc-pathway-explain, fermant la chaîne du test de sélection à la narration de voie.

Compétences : une caractérisation de sous-lignée rapporte un dN/dS élevé ou un excès non-synonyme parmi les marqueurs core-exclusifs et l'on se demande si un biais d'échantillonnage explique le signal ; Requiert un CSV annoté par tier avec comptes NS/S

### molecular-clock

Boite a outils de recherche academique pour la genomique evolutive MTBC evaluee par les pairs (groupe Guyeux, FEMTO-ST). Datation moleculaire des phylogenies du complexe Mycobacterium tuberculosis sous signal temporel faible : regression racine-vers-pointes, analyse TempEst, generation de XML BEAST, calibration multi-contraintes pour les difficultes d'horloge propres au MTBC, et controles par randomisation des dates.

Compétences : estimer des temps de divergence pour des lignees MTBC dans une etude ; evaluer le signal temporel d'une phylogenie publiee ; preparer des analyses BEAST ou BEAST2 ; dater l'emergence d'une sous-lignee ou d'un allele de resistance pour une publication

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

### mycobacterium-leprae

Reference bibliographique academique. Bibliographie curee de la recherche paleogenomique evaluee par les pairs sur Mycobacterium leprae, le corpus d'ADN ancien publie le plus riche pour une mycobacterie : 49 genomes anciens dans 13 pays sur 2200 ans, contre 16 pour le MTBC ancien. Indexe les articles canoniques (Schuenemann 2013 et 2018, Krause-Kyora 2018, Kerudin 2019, Fotakis 2020, Neukamm 2020, Pfrengle 2021, Bonczarowska 2022, Urban 2024), les reservoirs non humains documentes (tatou a neuf bandes, ecureuils roux medievaux anglais), l'origine europeenne des echantillons du Nouveau Monde, et les cinq lignees publiees canoniques.

Compétences : rediger une section comparative M ; leprae contre M ; tuberculosis sur les trajectoires paleogenomiques ; preparer des slides de seminaire sur la genomique des mycobacteries anciennes ; contextualiser les reservoirs zoonotiques dans un article ; transposer une methodologie paleogenomique publiee au MTBC

### ncbi-pathogen-detection

Client de base de données académique. Interroge le portail public NCBI Pathogen Detection (NIH/NCBI), plateforme ouverte qui agrège les assemblages de génomes bactériens publiés en clusters de SNP pré-calculés (accessions PDS) avec arbres phylogénétiques, pour la recherche en génomique évolutive et comparative. Fournit des annotations sur le contenu en gènes de virulence et les allèles de sensibilité antimicrobienne. Complémentaire d'EnteroBase et du Pathogens Portal EMBL-EBI.

Compétences : un manuscrit doit consulter l'assignation de cluster SNP public d'un isolat déposé ; récupérer une phylogénie publiée ; citer le contenu en allèles de résistance d'un échantillon public ; bâtir une intégration de base de données pour une étude évaluée

### pangenome-enrichment

Analyse de pangénome et enrichissement fonctionnel par lignée MTBC : classification core/soft-core/shell/cloud des gènes, enrichissement de voies KEGG, analyse du contenu génique spécifique de lignée.

Compétences : comparer le contenu génique entre lignées ; identifier des gènes spécifiques de lignée ; réaliser un enrichissement KEGG sur des gènes différentiels ; analyser la structure du pangénome pour un article

### pathogens-portal

Client de base de données académique. Interroge le Pathogens Portal EMBL-EBI, passerelle européenne publique vers les données biomoléculaires FAIR de génomes bactériens hébergées à l'European Nucleotide Archive (ENA). Lancé en 2023, il indexe 200 000+ espèces et souches déposées dans des études publiées, servies via les Data Hubs ENA standard. Pendant européen de NCBI Pathogen Detection.

Compétences : un projet doit récupérer des séquences de génomes bactériens (anciens ou modernes) déposées à l'ENA/SRA pour une analyse comparative ou phylogénomique ; localiser tous les projets ENA d'une espèce ; bâtir un workflow d'accès aux données centré Europe pour une publication

### pectinated-subclade-mining

Méthodologie d'extraction itérative des sous-lignées pectinées au sein d'une lignée MTBC (ou autre bactérie clonale) en utilisant les SPDI core présents dans le sous-clade candidat et absents des autres sous-clades et lignées externes proches. Travaille sur les fichiers spdi.txt directement sur disque (pas de SQL), filtre per-pool (jamais global) pour garantir l'exclusivité, et produit un répertoire dédié par sous-clade avec son fichier de marqueurs TSV.

Compétences : on observe une topologie pectinée dans un arbre RAxML focalisé et l'on veut extraire itérativement les sous-clades pour raffiner la taxonomie ; on suspecte qu'un clade trop hétérogène contient plusieurs sous-lignées ; on veut un classifieur SPDI pour reclasser des souches en attente

### phylogeography

Boîte à outils académique (groupe Guyeux, FEMTO-ST) pour l'analyse de distribution géographique des lignées MTBC via TBannotator : tableau croisé pays × lignée, cartes choroplèthes, barplots empilés et indices de diversité géographique. Pour retrouver des études phylogéographiques antérieures sur une lignée ou un pays, à coupler avec tbmonitor-papers.

Compétences : cartographier la distribution géographique d'une lignée pour un article ; comparer la structure géographique entre sous-lignées ; produire figures de distribution et tables supplémentaires ; identifier des points chauds géographiques

### raxml

Boîte à outils académique (groupe Guyeux, FEMTO-ST) pour l'inférence phylogénomique (RAxML-NG) en vue de publications. Soumet et gère des jobs RAxML-NG via le MCP TBannotator. Gère le mode matrice directe, le mode clustering et le placement contextuel.

Compétences : construire des phylogénies MTBC ; placer de nouvelles souches sur des arbres de référence ; produire des Newick pour annotation iTOL ; lancer RAxML-NG pour un article

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

### spaam-ancient-metagenome-dir

Interroge SPAAM AncientMetagenomeDir, catalogue communautaire de référence de tous les échantillons métagénomiques anciens et génomes microbiens anciens publiés. Trouve les échantillons anciens de M. tuberculosis et pathogènes apparentés, leurs publications, sites, dates et accessions ENA/SRA, et les apparie aux hôtes humains anciens de l'AADR pour des récits de coévolution.

Compétences : trouver des génomes MTBC anciens publiés ; localiser les données brutes (ENA/SRA) de pathogènes anciens ; apparier une souche TB ancienne à son hôte humain dans l'AADR ; lister les métagénomes anciens d'une région/période ; alimenter le côté pathogène d'une histoire de coévolution

### spaam-community

Index de l'écosystème communautaire SPAAM (Standards, Precautions and Advances in Ancient Metagenomics), organisation faîtière de la métagénomique ancienne. Couvre outils, pipelines, supports de formation, standards de métadonnées, annuaires de labos et guides de référence au-delà du catalogue AncientMetagenomeDir. À utiliser comme méta-index pour trouver un outil, pipeline, tutoriel ou ressource sur l'ADN microbien ancien.

Compétences : choisir un pipeline de métagénomique ancienne (eager vs aMeta) ; trouver un tutoriel sur les patterns de dommage de l'ADN ancien ; valider des métadonnées contre le standard MInAS ; identifier des labos sur un pathogène ancien précis ; s'initier à l'infrastructure SPAAM

### spdi-annotation

Boîte à outils académique (groupe Guyeux, FEMTO-ST) : annote les variants SPDI du MTBC avec gène, effet (faux-sens/synonyme/stop/décalage), changement d'acide aminé et catégorie fonctionnelle. Interroge d'abord TBannotator pour les annotations existantes, puis se replie sur une annotation locale GenBank/GFF3. Pour vérifier si un SPDI (surtout à fort impact) a déjà été décrit dans la littérature, à coupler avec tbmonitor-papers.

Compétences : annoter une liste de variants SPDI pour un article MTBC ; construire des tables supplémentaires avec impact fonctionnel ; classer les variants par type d'effet

### species-id

Boite a outils de recherche academique pour la genomique des pathogenes evaluee par les pairs (groupe Guyeux, FEMTO-ST). Identification d'espece et de genre bacteriens pour detecter les isolats de recherche publies mal etiquetes M. tuberculosis, par deux methodes : l'API BLAST du NCBI et Mash screen contre une empreinte RefSeq. Etape de controle qualite avant l'ajout d'un genome a la base de recherche du groupe.

Compétences : un isolat de recherche etiquete M ; tuberculosis parait suspect (nombre de SNP aberrant, trop peu ou trop de SPDI, placement phylogenetique curieux) ; importer des genomes depuis SRA ou ENA ; TBannotator signale un echantillon melange ou mal assigne

### sra-geolocate

Consolidation de l'origine et de la date d'une souche SRA, ou construction d'un dataset de SRA correspondant à une zone géographique. Deux cascades parallèles (lieu + date) puisent dans les mêmes sources : métadonnées BioSample (geo_loc_name, lat_lon, collection_date), BioProject, publications PubMed/Europe PMC liées, supplementary materials, texte intégral PDF. Chaque résultat est assorti d'un score de confiance et de sa source, et distingue lieu de collection vs séquençage, date de collection vs publication.

Compétences : enrichir la métadonnée d'une souche dont geo_loc_name ou collection_date est vague ou vide ; construire une cohorte TB par région ; vérifier l'origine et la date revendiquées d'un SRA avant inclusion ; détecter des incohérences entre BioSample, BioProject et publications ; extraire les métadonnées par souche depuis les supplements open access

### strain-qc

Boite a outils de recherche academique pour la phylogenomique MTBC evaluee par les pairs (groupe Guyeux, FEMTO-ST). Controle qualite d'un genome de recherche MTBC avant integration en base ou dans un arbre phylogenetique : 7 criteres (chimere intra-MTBC, taux GC, couverture, profondeur, SPDI contre lignee, melange inter-especes, qualite de mapping), verdict PASS/WARN/FAIL justifie, genome unique ou lot.

Compétences : importer depuis SRA ou ENA ; filtrer avant une reconstruction phylogenetique ; face a un genome au placement aberrant ou a longue branche ; auditer la base ; decider des exclusions de get_phylo.py

### string-db

Boîte à outils académique (groupe Guyeux, FEMTO-ST) : client stdlib résilient de l'API REST STRING v12, qui agrège les associations protéine-protéine connues et prédites décomposées en canaux de preuve (voisinage, fusion, co-occurrence, co-expression, expérimental, base de données, fouille de texte). Résout les locus tags en identifiants STRING, liste les partenaires d'interaction, construit des réseaux, lance l'enrichissement fonctionnel (GO/KEGG/Pfam) et le test d'enrichissement PPI. Espèce par défaut : M. tuberculosis H37Rv.

Compétences : obtenir un second avis guilt-by-association sur un gène (surtout hypothétique) ; tester si un opéron/complexe candidat est significativement connecté ; obtenir l'enrichissement fonctionnel d'un petit ensemble de gènes ; Pour l'enrichissement à l'échelle du protéome entier, ne pas utiliser ce skill (télécharger les fichiers en masse)

### tb-cli

CLI de recherche académique pour les études de génomique comparative du MTBC, via la commande tb. Utilisée par le groupe Guyeux (FEMTO-ST) pour des publications évaluées sur la phylogénomique et la biologie évolutive du MTBC.

Compétences : le contexte mentionne des lignées MTBC, des souches de recherche déposées, des annotations SPDI/SNP, des variants publiés dans des gènes comme katG/rpoB/embB, le catalogage d'allèles de résistance, l'analyse des régions de différence, la fouille de littérature MTBC ou des requêtes à la base TBannotator

### tbannotator-mcp

Interroge le serveur MCP TBannotator v3.6 (~274 800 génomes MTBC) via PostgreSQL. Accède aux métadonnées de souches, classifications de lignées (Coll, Gagneux, Senelle...), fréquences SNP/SPDI, arbres phylogénétiques (NJ, RAxML) et profils de résistance.

Compétences : compter les souches par lignée ; obtenir les métadonnées d'un code de lignée ; trouver des marqueurs core-exclusifs ; valider des fichiers supplémentaires ; construire des arbres phylogénétiques pour un article de caractérisation de lignée MTBC

### tbmonitor-papers

Interroge le serveur MCP tbmonitor, miroir SQLite pré-indexé en lecture seule du corpus PubMed tuberculose (~330 000 articles de 1848 à aujourd'hui, ~81 % TB-spécifiques). Expose titre, résumé, DOI, lien PubMed, journal, date, plus auteurs / mots-clés / termes MeSH / types de publication / affiliations / liste de références en tableaux JSON directement interrogeables via json_each(). Réponse sub-seconde sur des recherches filtrées.

Compétences : récupérer des articles TB par auteur, terme MeSH, mot-clé, journal ou plage d'années ; assembler une liste BibTeX pour une revue ou un financement ; vérifier qu'une affirmation a une couverture antérieure ; relier des résultats de souches TBannotator à la littérature ; bâtir un état de l'art rapide avant de recourir à lit-review

### thd

Boite a outils de recherche academique pour l'epidemiologie moleculaire evaluee par les pairs (groupe Guyeux, FEMTO-ST). Calcule la Time-scaled Haplotypic Density (THD, Rasigade et al. 2017), mesure publiee de l'expansion relative des lignees bacteriennes, par estimation de densite par noyau sur les distances genetiques deux a deux, parametree par une echelle de temps.

Compétences : calculer la THD sur des profils MIRU-VNTR, des matrices de distance SNP ou des haplotypes WGS d'une collection de recherche ; comparer l'expansion relative entre lignees MTBC ; associer la mesure a des covariables d'etude ; separer le signal recent du signal de long terme pour une publication

### triangulate-route

Boîte à outils de recherche phylogéographique (groupe Guyeux, FEMTO-ST). Triangule la signature génomique publiée d'une lignée MTBC contre des corpus historiques de migration humaine pour produire des scénarios de dispersion prêts pour évaluation par les pairs. Prend une lignée et un pays cible en entrée et retourne : les voisins publiés mondiaux par sous-lignée (Shitikov23) via TBannotator, des routes historiques candidates (SlaveVoyages, OWTRAD, littérature spécialisée) et une table de triangulation formatée pour publication.

Compétences : écrire une section phylogéographique sur un pays/région (Brésil, Antilles, Cap-Vert, Maurice, Comores, Inde...) ; valider une signature génomique publiée avec des corpus d'archives historiques ; préparer une diapositive de séminaire ; rédiger un cas d'étude dans un manuscrit

### tsne-hdbscan

Réduction de dimension t-SNE + clustering par densité HDBSCAN pour explorer la diversité génomique du MTBC. Fonctionne sur des matrices SPDI présence/absence, des matrices de distances SNP ou des profils MIRU-VNTR.

Compétences : explorer la structure de population des souches MTBC ; identifier des clusters de transmission ; détecter aberrants ou lignées mal classées ; visualiser les relations génomiques en 2D ; clustering non supervisé sans fixer le nombre de clusters

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
| [boltz](bio_population_genetics.md#boltz) | `bio_population_genetics` |
| [claim-check](redac.md#claim-check) | `redac` |
| [create-viz](bio_population_genetics.md#create-viz) | `bio_population_genetics` |
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
| [sci-figure](bio_population_genetics.md#sci-figure) | `bio_population_genetics` |
| [scientific-problem-selection](bio_population_genetics.md#scientific-problem-selection) | `bio_population_genetics` |
| [scikit-bio](bio_population_genetics.md#scikit-bio) | `bio_population_genetics` |
| [scikit-learn](bio_population_genetics.md#scikit-learn) | `bio_population_genetics` |
| [slavevoyages](bio_population_genetics.md#slavevoyages) | `bio_population_genetics` |
| [statsmodels](bio_population_genetics.md#statsmodels) | `bio_population_genetics` |
| [tooluniverse-sequence-retrieval](bio_population_genetics.md#tooluniverse-sequence-retrieval) | `bio_population_genetics` |

