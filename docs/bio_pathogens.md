# Plugin `bio_pathogens`

> Academic research toolkit for computational genomic studies of bacterial pathogens, focused on Mycobacterium tuberculosis complex (MTBC) phylogenomics, comparative genomics, and public-health surveillance literature. Used by the Guyeux group (FEMTO-ST, University of Franche-Comte) for peer-reviewed scientific publications on pathogen evolution and host-pathogen co-evolution.

## Rôle dans un projet M. tuberculosis

Cœur du dispositif. Rassemble les skills qui touchent directement le complexe Mycobacterium tuberculosis (MTBC) et les pathogènes apparentés : accès aux génomes de référence et aux isolats de recherche publiés, fréquences alléliques de résistance aux antituberculeux telles que rapportées dans la littérature évaluée par des pairs, assignation de lignées, bases de données génomiques spécialisées. C'est le plugin qu'on active quand le travail porte effectivement sur M. tuberculosis.

Skills propres (canoniques) : **55** ; skills partagés utilisés (symlinks) : **37**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [active-site-check](#active-site-check) ; [ancestral-reconstruction](#ancestral-reconstruction) ; [atlas-add-lineage](#atlas-add-lineage) ; [bacdive](#bacdive) ; [bdd-bridge](#bdd-bridge) ; [beast2-dating](#beast2-dating) ; [clade-finder](#clade-finder) ; [coevolution](#coevolution) ; [convergent-evolution](#convergent-evolution) ; [denovo-content-qc](#denovo-content-qc) ; [enterobase](#enterobase) ; [fetch-tbannotator](#fetch-tbannotator) ; [helicobacter-pylori-phylogeography](#helicobacter-pylori-phylogeography) ; [host-pathogen-pair](#host-pathogen-pair) ; [lineage-comparison](#lineage-comparison) ; [lineage-mdl](#lineage-mdl) ; [mbovis](#mbovis) ; [mk-ascertainment](#mk-ascertainment) ; [molecular-clock](#molecular-clock) ; [mtbc-atlas](#mtbc-atlas) ; [mtbc-bilan](#mtbc-bilan) ; [mtbc-deepen](#mtbc-deepen) ; [mtbc-gene-function](#mtbc-gene-function) ; [mtbc-gene-network](#mtbc-gene-network) ; [mtbc-lineages](#mtbc-lineages) ; [mtbc-mutation-impact](#mtbc-mutation-impact) ; [mtbc-pathway-explain](#mtbc-pathway-explain) ; [mtbc-reboot](#mtbc-reboot) ; [mycobacterium-leprae](#mycobacterium-leprae) ; [ncbi-pathogen-detection](#ncbi-pathogen-detection) ; [pangenome-enrichment](#pangenome-enrichment) ; [pathogens-portal](#pathogens-portal) ; [pectinated-subclade-mining](#pectinated-subclade-mining) ; [phylogeography](#phylogeography) ; [raxml](#raxml) ; [resistance-catalogue](#resistance-catalogue) ; [resistance-discovery](#resistance-discovery) ; [resistance-explain](#resistance-explain) ; [resistance-predict](#resistance-predict) ; [resistance-profiler](#resistance-profiler) ; [sitvitweb](#sitvitweb) ; [snp-distance](#snp-distance) ; [spaam-ancient-metagenome-dir](#spaam-ancient-metagenome-dir) ; [spaam-community](#spaam-community) ; [spdi-annotation](#spdi-annotation) ; [species-id](#species-id) ; [sra-geolocate](#sra-geolocate) ; [strain-qc](#strain-qc) ; [string-db](#string-db) ; [tb-cli](#tb-cli) ; [tbannotator-mcp](#tbannotator-mcp) ; [tbmonitor-papers](#tbmonitor-papers) ; [thd](#thd) ; [triangulate-route](#triangulate-route) ; [tsne-hdbscan](#tsne-hdbscan)

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

Boîte à outils académique pour la datation moléculaire bayésienne des phylogénies MTBC avec BEAST2. Génère un XML BEAST2 correct pour des alignements binaires de SNP (présence/absence 0/1), format produit par le pipeline TB du groupe Guyeux (FEMTO-ST), et lance BEAST2 sans interface. Corrige les deux défaillances qui font échouer silencieusement la convergence sur données binaires MTBC.

Compétences : dater une phylogénie MTBC à partir d'un alignement binaire de SNP ; produire un arbre daté bayésien pour un article de phylogénomique ; éviter les non-convergences silencieuses propres aux données binaires

### clade-finder

Recherche de clades et sous-populations dans une lignée MTBC. Construit des vecteurs de features par SRA (pan-SPDI, positions IS, RD) à partir des fichiers report.json ou spdi.txt de bdd/actuelle/L<x>/, applique t-SNE + HDBSCAN et produit un PNG haute résolution pour visualiser les sous-lignées potentielles. Une fois un cluster identifié, vérifier dans tbmonitor-papers s'il a déjà été décrit dans la littérature.

Compétences : explorer la structure en sous-lignées d'une lignée ; chercher des clusters de population ; décider si une lignée doit être scindée ; Pour la phase post-découverte (extraction pectinée des sous-clades), utiliser pectinated-subclade-mining

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

Comparaison statistique entre lignées ou sous-lignées MTBC : test exact de Fisher, khi-deux, intervalle exact binomial, correction FDR, odds ratios et tables de comparaison prêtes à publier.

Compétences : comparer des taux de résistance entre lignées ; tester si un trait est significativement associé à une sous-lignée ; produire des tables statistiques pour articles ; calculer des intervalles de confiance

### lineage-mdl

Définit les sous-lignées d'une lignée MTBC (ou bactérie clonale) par optimisation multicritères sous contraintes, le bruit étant traité en amont. Remplace les seuils heuristiques par une formulation principielle : débruitage (masque homoplasie/résistance, QC, chimères), contraintes de faisabilité (un clade seulement si assez de synapomorphies propres multi-signal, ≥5 souches et monophylie), et objectif de sélection de modèle MDL optimisé par programmation dynamique avec balayage de lambda vers un front de Pareto.

Compétences : obtenir une taxonomie de sous-lignées reproductible et défendable pour des études évolutives (phylogéographie, datation) plutôt qu'un découpage arbitraire ; quand un clade est dense/clonal et sur-séquencé ; quand on veut une granularité pilotée par la biologie sous garantie de support synapomorphique ; Complémentaire de pectinated-subclade-mining (un sous-clade) : ici on optimise la partition entière

### mbovis

Client de base de données académique pour M. bovis et le spoligotypage MTBC animal. Interroge mbovis.org (base internationale de référence Spoligo Bovis) pour l'attribution de numéros SB à partir d'isolats publiés, les conversions de format (BIN/OCT/HEX) et la distribution géographique des profils animaux (M. bovis, M. caprae, M. pinnipedii, M. orygis, M. microti). Cas d'usage du groupe Guyeux : attribuer des SB, croiser avec SITVIT2, identifier les complexes clonaux (Eu1, Eu2, Af1, Af2).

Compétences : convertir un profil de spoligotype M ; bovis en numéro SB ; consulter un profil SB connu ; télécharger la base SB complète ; interroger des souches par pays ; identifier le complexe clonal d'un isolat MTBC animal

### mk-ascertainment

Test de McDonald-Kreitman et simulation de biais d'échantillonnage pour des variants SPDI MTBC stratifiés par tier. Quantifie si l'excès non-synonyme observé parmi les variants définissant les lignées est réel ou un artefact du filtre d'exclusivité. Un script compagnon écrit une table MK par gène (Dn/Ds/Pn/Ps, alpha, DoS, p de Fisher) consommée par mtbc-pathway-explain, fermant la chaîne du test de sélection à la narration de voie.

Compétences : une caractérisation de sous-lignée rapporte un dN/dS élevé ou un excès non-synonyme parmi les marqueurs core-exclusifs et l'on se demande si un biais d'échantillonnage explique le signal ; Requiert un CSV annoté par tier avec comptes NS/S

### molecular-clock

Datation moléculaire des phylogénies MTBC en présence d'un signal temporel faible : régression racine-à-tip, analyse TempEst, génération de XML BEAST, calibration multi-contraintes adaptée aux défis d'horloge propres au MTBC.

Compétences : estimer les temps de divergence de lignées MTBC ; évaluer le signal temporel d'une phylogénie ; préparer des analyses BEAST/BEAST2 ; dater l'émergence de sous-lignées ou de la résistance

### mtbc-atlas

Boîte à outils académique (groupe Guyeux, FEMTO-ST) : client stdlib résilient de l'API REST du MTBC Gene Annotation Atlas, ré-annotation du protéome du MTBC qui succède à Mycobrowser. Interroge 3906 gènes (ancrés sur le génome ancestral MTBC0, joints à H37Rv), chacun portant une fonction curée, un verdict (requalifié/famille assignée/dark) et jusqu'à ~35 couches de preuves : orthologie, UniProt, conservation intra-MTBC, structure AlphaFold/ESMFold + Foldseek, réseau STRING, sites catalytiques M-CSA, essentialité Tn-seq, vulnérabilité CRISPRi, etc.

Compétences : obtenir l'annotation/preuves courantes d'un gène MTBC par locus tag ; rechercher des gènes par nom/produit/fonction ; lister tous les gènes portant une couche de preuve donnée ; extraire une couche précise ; obtenir des comptes à l'échelle du jeu de données ; Interface machine de l'atlas mtbc.gclab.fr, préférable au scraping HTML

### mtbc-bilan

Bilan complet et honnête d'un projet MTBC : état consolidé des connaissances acquises et plan d'action pour la suite. Le bilan ne raconte pas le cheminement itératif : il consolide ce qui est actuellement su, comment cela a été établi, et ce qui reste à faire d'après le cahier. En cas de conflit entre entrées, on garde la dernière version consolidée. Le mode --full compare tous les projets MTBC.

Compétences : faire le point sur un projet ; décider quoi faire ensuite ; préparer une réunion ; arbitrer entre plusieurs projets ; évaluer si un projet est prêt à être clos ; repartir après une pause

### mtbc-deepen

Approfondissement systématique d'une étude MTBC en cours. Enchaîne bilan du projet (mtbc-bilan), revue de littérature élargie (lit-review --wide, appuyée d'abord sur tbmonitor-papers), inventaire des skills pertinents non mobilisés, et synthèse de nouvelles pistes hiérarchisées. Ou conclut honnêtement qu'il n'y a plus rien à investiguer et que l'étude peut être close.

Compétences : reprendre une étude après une pause ; chercher de nouvelles directions pour un projet qui stagne ; décider si un projet mérite encore du temps ; préparer la suite après une phase d'analyse ; faire le point avant une réunion

### mtbc-gene-function

Boîte à outils académique (groupe Guyeux, FEMTO-ST) : produit une annotation fonctionnelle structurée pour un gène H37Rv (par nom comme katG ou locus tag comme Rv1908c). Répond d'abord depuis le projet curé annotation_mtbc du groupe (fonction UniProt + EC, domaines Pfam, partenaires STRING, conservation/sélection, pistes structurales Foldseek), et n'enrichit via l'API ESM Atlas que ce qui n'est pas encore annoté. Fonctionne hors ligne depuis la source curée.

Compétences : une page de lignée de l'Atlas mentionne un gène (contenu RD, SNP définissant, allèle de résistance, gène de voie) et il faut un encart fonctionnel automatique ; une analyse tombe sur un locus Rv inconnu et l'on veut un contexte de 30 secondes ancré dans le travail d'annotation du groupe

### mtbc-gene-network

Interroge le réseau d'interactions géniques du MTBC comme un graphe, local-first depuis le réseau STRING pré-calculé du groupe (~4000 gènes, ~38k arêtes de confiance moyenne). Le charge avec networkx et expose ce que le pipeline d'annotation ne fait pas : voisins d'un gène, sous-réseau induit d'un ensemble, plus court chemin, hubs (degré/betweenness), modules fonctionnels (détection de communautés), et guilt-by-association pour un gène dark. L'API STRING n'est que le repli.

Compétences : trouver avec quoi un gène interagit ; construire un sous-réseau d'interactions pour une voie ou une liste de gènes ; localiser les hubs/goulots de l'interactome ; détecter des modules fonctionnels ; hypothéser la fonction d'un locus Rv non caractérisé depuis son voisinage ; produire une figure de réseau pour un manuscrit

### mtbc-lineages

Source faisant autorité sur les définitions de lignées du MTBC, les hiérarchies de sous-lignées et les marqueurs SNP/SPDI. La hiérarchie source-de-vérité est fixée dans SOURCES_OF_TRUTH.md : le placement vivant dans bdd/actuelle/ et son registre barcode_complete.tsv font foi ; lignees.py (clé « moi » = Guyeux) est une banque de marqueurs SPDI historique, fiable pour les lignées majeures stables mais possiblement désynchronisée pour les sous-lignées issues du cycle multi-signal.

Compétences : chercher le marqueur définissant une lignée ; trouver le parent d'une sous-lignée ; déterminer à quelle lignée appartient un SPDI ; confirmer la hiérarchie L1 à L10 ; réconcilier des classifications contradictoires ; citer la publication d'origine (confirmer titre/auteurs/DOI via tbmonitor-papers) ; À préférer aux requêtes TBannotator ou lectures CSV ad hoc pour les faits de lignée

### mtbc-mutation-impact

Boîte à outils académique (groupe Guyeux, FEMTO-ST) : estime l'impact fonctionnel local d'une mutation ponctuelle d'un gène H37Rv en comparant les activations d'autoencodeur parcimonieux (SAE) de l'ESM Atlas par résidu entre protéine sauvage et mutée, à la position de la mutation. Utile quand une page de lignée mentionne un allèle de résistance ou un SPDI non-synonyme sous sélection et qu'on veut un second avis par modèle de langage protéique. Retourne les deltas de features et un score citable (log-likelihood ratio ESM-1v).

Compétences : contextualiser un allèle de résistance publié (ex ; katG S315T pour l'INH) ; caractériser un SPDI non-synonyme définissant une sous-lignée ; contrôler la plausibilité d'une substitution adaptative trouvée par McDonald-Kreitman

### mtbc-pathway-explain

Boîte à outils académique (groupe Guyeux, FEMTO-ST) : produit une narration structurée et curée-d'abord d'un ensemble de gènes vu comme une voie (voie prédéfinie du catalogue ESX-1..5, PDIM, acide mycolique, DosR, stress oxydatif, voies de résistance...), le voisinage réseau d'un gène, ou une liste explicite. Annote chaque gène via mtbc-gene-function, agrège les classes d'enzymes et domaines Pfam dominants, signale les gènes dark et narre avec la structure du réseau PPI.

Compétences : une lignée montre un signal de sélection positive sur une voie et l'on veut une narration qui nomme les protéines, leurs fonctions et leur cohésion ; lire un module réseau comme une unité fonctionnelle ; à partir d'une table de sélection (--from-selection, sortie de mk-ascertainment), mapper le signal sur le catalogue avec seuil de significativité

### mtbc-reboot

Reboot complet d'un projet MTBC. Archive toute la connaissance accumulée (découvertes, affirmations, scripts, données) dans archives/YYYY-MM-DD_reboot/ avec tags de confiance (vérifié / à vérifier / incertain / réfuté), réinitialise le projet en structure propre, scanne les projets voisins pour convergences, et réanalyse affirmation par affirmation avec revue critique du code source (littérature via tbmonitor avant WebSearch). Bloque la rédaction tant que la réanalyse n'est pas complète.

Compétences : un projet a accumulé trop de dérive, de résultats périmés ou d'affirmations non vérifiées pour continuer incrémentalement ; redémarrer une étude après une longue pause à héritage incertain ; quand claim-check révèle trop d'affirmations non vérifiées ; pivoter la direction d'un projet en préservant l'acquis

### mycobacterium-leprae

Référence de littérature académique. Bibliographie curée des études paléogénomiques évaluées de Mycobacterium leprae, le corpus d'ADN ancien le plus riche pour un Mycobacterium (49 génomes anciens publiés, 13 pays, 2200 ans, contre 16 pour le MTBC ancien). Indexe les articles canoniques, les réservoirs zoologiques non-humains documentés (tatou, écureuils roux médiévaux anglais), l'origine phylogéographique européenne des échantillons du Nouveau Monde et les cinq lignées phylogénétiques publiées.

Compétences : rédiger une section comparative M ; leprae vs M ; tuberculosis en paléogénomique ; préparer des slides de séminaire sur la génomique ancienne des Mycobacterium ; contextualiser des réservoirs zoonotiques ; transposer une méthodologie paléogénomique publiée au MTBC

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

Boîte à outils académique (groupe Guyeux, FEMTO-ST) : interroge et (re)construit un catalogue de référence consolidé mutation → résistance antimicrobienne pour le MTBC, croisant le catalogue OMS des mutations (2e éd., 2023), la base de tb-profiler et le signal empirique CRyPTIC. Résout la notation HGVS (gène_mutation) vers les coordonnées SPDI 0-based du projet via le fichier officiel de coordonnées OMS, et retourne, pour un variant ou un antituberculeux, le grade d'association catalogué et sa provenance.

Compétences : consulter le grade d'association OMS/tb-profiler d'un variant ; lister les marqueurs catalogués d'un médicament ; calculer une base déterministe par souche (type TB-Profiler) ; convertir HGVS en SPDI ; régénérer le catalogue consolidé après mise à jour d'une source

### resistance-discovery

Boîte à outils académique (groupe Guyeux, FEMTO-ST) : découvre des déterminants de résistance non catalogués dans le MTBC par association pangénomique, en contrôlant la structure de population et la co-résistance, et en validant les candidats par convergence phylogénétique. Complète le catalogue curé (resistance-catalogue) en révélant les variants que le catalogue manque, et documente/corrige les trois angles morts des catalogues indexés en SPDI (codons synonymes, déterminants rares, MNV vs SNP).

Compétences : chercher de nouveaux déterminants de résistance au-delà du catalogue OMS ; auditer pourquoi la base catalogue d'un médicament a une faible sensibilité ; construire une GWAS consciente de la lignée d'un antituberculeux ; cribler des candidats en rejetant les artefacts de liaison clonale

### resistance-explain

Boîte à outils académique (groupe Guyeux, FEMTO-ST) : explique le mécanisme d'une mutation de résistance cataloguée ou candidate dans le MTBC en assemblant, en un dossier mécanistique citable, le verdict du catalogue curé, l'association phénotypique empirique observée dans les souches du projet, la littérature TB publiée sur le variant, un score d'effet par modèle de langage protéique (ESM-1v, Meier 2021), la fonction du gène et le contexte structural 3D (ESMFold).

Compétences : expliquer pourquoi un variant confère (ou pourrait conférer) une résistance ; interpréter un candidat de resistance-discovery ; rédiger le paragraphe mécanistique d'un manuscrit ; distinguer un déterminant causal d'un artefact de co-résistance ou de liaison de lignée

### resistance-predict

Boîte à outils académique (groupe Guyeux, FEMTO-ST) : prédit le phénotype de résistance d'une souche de M. tuberculosis à partir de son profil de variants génomiques, en combinant le catalogue curé déterministe avec un modèle résiduel à gradient boosting, et explique chaque prédiction (importance des features / SHAP + impact protéique ESM). Évalué honnêtement par validation croisée stratifiée par lignée (GroupKFold) et comparé à la base catalogue à spécificité égale.

Compétences : prédire la résistance d'une souche ou cohorte ; quantifier l'apport d'une couche de machine learning au-dessus du catalogue OMS par médicament ; produire une table sensibilité/spécificité par médicament pour un manuscrit ; expliquer une prédiction par les variants qui la portent

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

Identification d'espèce/genre bactérien pour détecter les souches mal étiquetées « M. tuberculosis ». Deux méthodes : BLAST via l'API NCBI (zéro stockage local, précis, ~1 min/souche) et Mash screen (rapide, ~1 Go de sketch RefSeq, optionnel). Conçu pour le criblage de souches suspectes avant intégration dans la BDD MTBC.

Compétences : une souche étiquetée M ; tuberculosis paraît suspecte (compte de SNP aberrant, placement phylogénétique étrange, trop peu/trop de SPDI) ; importer de nouvelles souches depuis SRA/ENA ; quand TBannotator signale des anomalies suggérant contamination ou mauvaise étiquette (confirmation d'un BioProject mal classé via tbmonitor-papers)

### sra-geolocate

Consolidation de l'origine et de la date d'une souche SRA, ou construction d'un dataset de SRA correspondant à une zone géographique. Deux cascades parallèles (lieu + date) puisent dans les mêmes sources : métadonnées BioSample (geo_loc_name, lat_lon, collection_date), BioProject, publications PubMed/Europe PMC liées, supplementary materials, texte intégral PDF. Chaque résultat est assorti d'un score de confiance et de sa source, et distingue lieu de collection vs séquençage, date de collection vs publication.

Compétences : enrichir la métadonnée d'une souche dont geo_loc_name ou collection_date est vague ou vide ; construire une cohorte TB par région ; vérifier l'origine et la date revendiquées d'un SRA avant inclusion ; détecter des incohérences entre BioSample, BioProject et publications ; extraire les métadonnées par souche depuis les supplements open access

### strain-qc

Contrôle qualité d'une souche MTBC avant intégration dans la BDD ou un arbre phylogénétique. Vérifie 7 critères : chimère intra-MTBC par classification multi-systèmes, taux GC, couverture du génome, profondeur de séquençage, nombre de SPDI vs distribution de la lignée, contamination inter-espèces par signature des gènes de ménage, et qualité de mapping. Produit un verdict PASS/WARN/FAIL justifié, en mode souche unique ou lot.

Compétences : importer de nouvelles souches depuis SRA/ENA ; filtrer avant reconstruction phylogénétique ; investiguer une souche à placement aberrant ou longue branche ; cribler la BDD ; comprendre pourquoi get_phylo.py exclut une souche (vérifier via tbmonitor-papers un dataset déjà signalé problématique)

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

Calcule la Time-scaled Haplotypic Density (THD) d'après Rasigade et al. 2017 (Sci Rep 7:45326). Quantifie le succès épidémique des souches de pathogènes par estimation de densité par noyau sur les distances génétiques par paires, avec des échelles de temps biologiquement pertinentes.

Compétences : calculer la THD pour des profils MIRU-VNTR, des matrices de distances SNP ou des haplotypes WGS ; comparer le succès épidémique entre lignées MTBC ; associer le succès des souches à des covariables clinico-épidémiologiques ; distinguer succès épidémique (court terme) et endémique (long terme)

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

