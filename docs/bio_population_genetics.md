# Plugin `bio_population_genetics`

> Academic research toolkit for ancient and modern human population genetics, archaeological radiocarbon databases, paleoclimate reconstructions, historical migration corpora, and linguistic/cultural atlases. Bundles general-purpose phylogenetic, statistical, and literature-mining tools used by the Guyeux group (FEMTO-ST, University of Franche-Comte) for peer-reviewed scientific publications on human evolutionary history and eco-anthropology.

## Rôle dans un projet M. tuberculosis

Contexte hôte et outillage générique. Pour une étude M. tuberculosis, l'histoire des populations humaines, les migrations, la paléoclimatologie et l'archéologie éclairent la co-évolution hôte-pathogène et la dispersion des lignées du MTBC. Le plugin porte aussi les briques transversales (phylogénétique, statistiques, fouille de littérature) réutilisées par les analyses MTBC elles-mêmes.

Skills propres (canoniques) : **47** ; skills partagés utilisés (symlinks) : **7**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [aadr](#aadr) ; [abc-xgboost](#abc-xgboost) ; [amtdb](#amtdb) ; [atlantic-voyages](#atlantic-voyages) ; [bayesian-skyline](#bayesian-skyline) ; [beast2-phylogeography](#beast2-phylogeography) ; [bioc-pmc](#bioc-pmc) ; [biopython](#biopython) ; [bioskills](#bioskills) ; [bovine-genomics](#bovine-genomics) ; [card](#card) ; [clinical-trial-protocol-skill](#clinical-trial-protocol-skill) ; [d-place](#d-place) ; [domestication-pathways](#domestication-pathways) ; [esm-atlas-cli](#esm-atlas-cli) ; [europe-pmc](#europe-pmc) ; [geo-map](#geo-map) ; [glottolog](#glottolog) ; [indian-ocean-voyages](#indian-ocean-voyages) ; [iqtree-lsd2](#iqtree-lsd2) ; [itol](#itol) ; [migration-data](#migration-data) ; [modern-human-reference-panels](#modern-human-reference-panels) ; [neolithic-14c](#neolithic-14c) ; [nextflow-development](#nextflow-development) ; [nextstrain](#nextstrain) ; [ontologies](#ontologies) ; [openalex](#openalex) ; [orbis](#orbis) ; [owtrad](#owtrad) ; [p3k14c](#p3k14c) ; [paleoclimate](#paleoclimate) ; [pastml](#pastml) ; [pleiades](#pleiades) ; [pubmed-database](#pubmed-database) ; [pubtator](#pubtator) ; [pysam](#pysam) ; [rdkit](#rdkit) ; [read-scientific-pdf](#read-scientific-pdf) ; [scanpy](#scanpy) ; [scikit-bio](#scikit-bio) ; [seaborn](#seaborn) ; [seshat](#seshat) ; [slavevoyages](#slavevoyages) ; [tooluniverse-sequence-retrieval](#tooluniverse-sequence-retrieval) ; [wals](#wals) ; [worldclim-bioclim](#worldclim-bioclim)

### aadr

Interroge l'Allen Ancient DNA Resource (AADR, laboratoire Reich), le compendium de référence de plus de 16 000 génomes humains anciens et actuels au format EIGENSTRAT, avec de riches métadonnées archéologiques et démographiques. Sert à croiser les populations humaines anciennes avec la phylogéographie des lignées du MTBC et à construire des récits de coévolution hôte-pathogène.

Compétences : contextualiser une lignée MTBC par l'histoire des populations humaines anciennes ; vérifier si une région ou période dispose de génomes humains anciens à corréler à un scénario TB ; identifier des squelettes ayant livré à la fois l'ADN de l'hôte et du pathogène ; rédiger une section éco-anthropologie ou coévolution pour un article ou un séminaire

### abc-xgboost

Calcul bayésien approché (ABC) accéléré par un régresseur/classifieur XGBoost avec interprétation SHAP, pour inférer le coefficient de sélection et le scénario démographie × sélection derrière une trajectoire ancienne de fréquence allélique. Conçu pour la question TYK2 P1104A (Kerner et al. 2021) : un déclin observé est-il reproductible, quelle était la force de la sélection, quelles statistiques résumées portent le signal. Simule les trajectoires par un modèle de Wright-Fisher diploïde.

Compétences : estimer le coefficient de sélection s d'un allèle humain (ou pathogène) à partir de fréquences d'ADN ancien dans le temps ; comparer des scénarios neutre / sélection faible / forte ; répliquer ou étendre Kerner 2021 sur TYK2 P1104A ; établir une base d'inférence par simulation avant une étude coalescente complète (msprime/SLiM)

### amtdb

Interroge AmtDB, la base d'ADN mitochondrial ancien (Université Charles de Prague, Ehler et al. 2019), dépôt de référence des génomes mitochondriaux humains anciens (2 548 échantillons, Paléolithique tardif à âge du Fer, surtout eurasiens) avec haplogroupe maternel, haplogroupe Y quand disponible, culture archéologique, site, datation radiocarbone. Complément matrilinéaire léger de l'AADR.

Compétences : suivre l'histoire des lignées maternelles de populations utiles à un argument phylogéographique TB ; récupérer de l'ADNmt ancien quand l'AADR n'a pas de génome nucléaire pour un squelette ; construire une carte des lignées maternelles néolithiques/âge du Bronze d'une région ; corréler des mutations pathologiques mitochondriales en paléopathologie

### atlantic-voyages

Agrège et met en forme les données historiques de traversées maritimes atlantiques pour comparaison avec la phylogéographie de M. tuberculosis L5/L6 (M. africanum) et des sous-lignées L4. Enveloppe six sources ouvertes : SlaveVoyages transatlantique (36 000 voyages, 1514-1866), AfricanOrigins, Liberated Africans Database, le portail Slavery Abolition and Social Justice, les voyages intra-américains et Voyages to Liberty.

Compétences : comparer la dispersion des sous-lignées L5/L6 aux routes commerciales atlantiques ; construire des matrices origine-destination pour tests de Mantel contre les distances MTBC ; superposer des TMRCA aux chronologies de voyages ; relier la phylogéographie de M ; africanum aux départs ouest-africains ; corréler des souches L5/L6 de diaspora à leurs régions sources probables

### bayesian-skyline

Emploie la famille des méthodes Bayesian Skyline de BEAST (BSP, Skyride, Skygrid, Birth-Death Skyline) pour reconstruire la taille efficace de population Ne(t) ou le nombre de reproduction effectif Re(t) d'un pathogène au cours du temps à partir de génomes échantillonnés. Méthodes phylodynamiques de référence pour relier les phylogénies MTBC aux transitions démographiques humaines et aux dynamiques épidémiques historiques.

Compétences : reconstruire la taille efficace historique d'une lignée MTBC ; tester si son expansion coïncide avec une transition démographique humaine (Néolithique, âge du Bronze, contact colombien) ; estimer Re au cours du temps pendant une épidémie ; produire un skyline plot pour un séminaire

### beast2-phylogeography

Emploie BEAST2 et ses paquets de phylogéographie (MASCOT, BASTA, DTA classique) pour la datation moléculaire bayésienne rigoureuse, le tip-dating d'échantillons anciens et l'inférence phylogéographique par coalescent structuré. Cadre bayésien de référence pour la phylogénétique à petite/moyenne échelle où l'on veut les distributions postérieures complètes sur la topologie, les temps de divergence, les taux de migration et les états ancestraux.

Compétences : dater des tips MTBC anciens avec intervalles de crédibilité complets ; lancer une phylogéographie par coalescent structuré (MASCOT/BASTA) ; produire un arbre bayésien calibré dans le temps ; tester des modèles démographiques concurrents ; quand un pipeline maximum de vraisemblance/Nextstrain manque de rigueur pour un relecteur

### bioc-pmc

Emploie BioC-PMC, le sous-ensemble PubMed Central Open Access + manuscrits d'auteurs au format BioC (NCBI/NLM) : environ 3 millions d'articles biomédicaux en texte intégral, avec sections structurées (titre, résumé, corps, figures, tableaux) en XML ou JSON, optimisé pour le TAL. Corpus de référence pour la fouille de texte biomédicale à grande échelle.

Compétences : construire un corpus texte intégral pour la fouille MTBC ou M ; bovis ; récupérer des sections structurées pour reconnaissance d'entités et extraction de relations ; télécharger en masse des articles PMC OA ; alimenter PubTator ou un modèle NER ; reproduire un corpus « 150k articles » depuis une source publique ; Pour du résumé seul (pas texte intégral) en TB, préférer tbmonitor-papers

### biopython

Guide complet de Biopython, la bibliothèque Python de référence en biologie computationnelle et bioinformatique. Sert à l'analyse de séquences ADN/ARN/protéines, aux entrées-sorties (FASTA, FASTQ, GenBank, PDB), à l'alignement, aux recherches BLAST, à l'analyse phylogénétique et structurale, et à l'accès aux bases NCBI.

Compétences : manipuler des séquences ou fichiers biologiques en Python ; interroger les bases NCBI (Bio.Entrez) ; scripter des analyses phylogénétiques ou d'alignement

### bioskills

Installe 425 skills de bioinformatique couvrant l'analyse de séquences, le RNA-seq, le single-cell, l'appel de variants, la métagénomique, la biologie structurale et 56 autres catégories.

Compétences : mettre en place des capacités de bioinformatique ; quand une tâche bioinfo requiert un skill spécialisé pas encore installé

### bovine-genomics

Index des ressources génomiques bovines en accès public pour la génétique des populations et les études phylogéographiques : 1000 Bull Genomes (~2 700 bovins WGS, ~90 M variants), Bovine HapMap (37 470 SNP, 19 races) et Bovine Genome Variation Database (BGVD, ~60 M SNP). Couvre la structure des races, la divergence taurin/zébu et le signal néolithique de domestication bovine.

Compétences : construire une référence phylogéographique côté bovin ; récupérer des données WGS ou SNP bovines ; comparer les distributions taurin/zébu ; ancrer une étude sur la domestication néolithique du bœuf

### card

Interroge CARD 2.0 (Canadian Archaeological Radiocarbon Database), compilation de référence des datations radiocarbone archéologiques d'Amérique du Nord (~50 000 dates, plus ~104 000 pour les 48 États contigus) couvrant contextes archéologiques, paléontologiques et géologiques, avec extension vers l'Amérique centrale et du Sud. Pendant américain d'EUROEVOL (Europe) et NERD (Proche-Orient) pour l'ancrage chronologique.

Compétences : construire une toile de fond chronologique pour des récits pré-colombiens et coloniaux des Amériques ; contextualiser le saut d'hôte pré-colombien de M ; pinnipedii dans les Andes ; extraire des dates par site pour des régions sous-représentées dans p3k14c

### clinical-trial-protocol-skill

Génère des protocoles d'essais cliniques pour dispositifs médicaux ou médicaments.

Compétences : l'utilisateur demande de créer un protocole d'essai clinique, de concevoir une étude clinique, de rechercher des essais similaires, ou de préparer une documentation de soumission FDA

### d-place

Interroge D-PLACE (Database of Places, Language, Culture and Environment), base ouverte de référence des traits culturels, linguistiques et environnementaux de plus de 1 400 sociétés humaines préindustrielles. Fournit des variables interculturelles (Ethnographic Atlas, jeu de Binford) reliées aux couches bioclimatiques et aux langues Glottolog, avec pour certaines familles des phylogénies linguistiques bayésiennes.

Compétences : construire un contexte culturel/écologique de la diffusion d'un pathogène ; tester si un mode de subsistance (pastoralisme, agriculture, chasse-cueillette) corrèle avec la distribution d'une lignée MTBC ; contrôler la non-indépendance phylogénétique en analyses interculturelles ; rédiger une section éco-anthropologie

### domestication-pathways

Agrège et met en forme les centres de domestication, routes de dispersion et données de transition néolithique pour les études de coévolution avec le MTBC. Enveloppe quatre familles de sources ouvertes : zooarchéologie (ABMAP, sous-ensemble animal AADR), archéobotanique (ADEMNES, BRAIN), ADN humain ancien (AADR) et radiocarbone mondial (p3k14c, CONTEXT, AgriChange). Inclut des tables curées de centres d'origine et de routes de dispersion.

Compétences : construire le contexte coévolutif de M ; bovis, M ; caprae, M ; orygis ; cadrer l'émergence de M ; tuberculosis à partir d'un ancêtre M ; canettii-like via la sédentarisation néolithique ; relier des TMRCA du MTBC aux transitions agricoles

### esm-atlas-cli

Boîte à outils académique (groupe Guyeux, FEMTO-ST) pour l'évolution des protéines : client Python résilient de l'API Protein Atlas (EvolutionaryScale × BioHub), qui expose les features d'autoencodeur parcimonieux (SAE) d'ESMC et les structures ESMFold2 sur 6,8 milliards de protéines. Recherche par hash de contenu, par similarité de séquence, interprétation des features SAE, métadonnées de cluster et récupération de structures 3D, avec cache disque et repli gracieux quand l'API alpha est dégradée.

Compétences : traduire une séquence protéique en résumé de fonction biologique ; récupérer une structure prédite ; trouver des homologues dans l'espace ESM ; comparer deux séquences (sauvage vs variant) par différence de features SAE

### europe-pmc

Interroge Europe PMC (EMBL-EBI), dépôt européen de littérature biomédicale couvrant résumés PubMed, texte intégral PMC, préprints de 32+ serveurs (bioRxiv, medRxiv...), livres, brevets et financements. API REST pour recherche, texte intégral et annotations de fouille pré-calculées (gènes, maladies, chimie, organismes, termes GO, numéros d'accession). Index le plus large en accès ouvert, complémentaire d'OpenAlex et de BioC-PMC.

Compétences : chercher de la littérature biomédicale préprints inclus ; récupérer le texte intégral d'articles OA ; obtenir des annotations pré-calculées en JSON/XML ; construire un corpus TB incluant préprints ; relier publications et accessions de données ; Pour de la littérature TB PubMed seule (sans préprints), tbmonitor-papers est plus rapide

### geo-map

Génère des cartes géographiques de qualité publication pour les études MTBC, avec projections cartographiques correctes, fonds Natural Earth multi-résolution, échelle, flèche nord, graticule et style prêt pour revue. Gère choroplèthes, bulles, camemberts, points GPS (lat/lon), arcs phylogéographiques, atlas multi-panneaux et compositions multi-couches.

Compétences : illustrer la distribution géographique d'une lignée dans un article ; montrer des taux de résistance par pays sur une carte ; tracer des sites d'échantillonnage à partir de coordonnées GPS ; dessiner des flux de migration phylogéographiques ; produire des figures pour présentations ou posters

### glottolog

Interroge Glottolog, catalogue de référence des langues, familles et dialectes du monde (8 238 languoïdes, 246 familles, 183 isolats, 227 langues des signes). Fournit des identifiants Glottocode stables, la classification généalogique, des coordonnées, la macroaire, la correspondance ISO 639-3, le statut de mise en danger et 460k+ références bibliographiques. Couche fondamentale de toute analyse cross-linguistique ou de coévolution biologie-langue.

Compétences : résoudre un nom de langue en Glottocode stable ; obtenir la classification généalogique de la langue d'une population ; joindre un jeu génétique ou pathogène à des métadonnées linguistiques ; construire un contrôle par famille de langues ; appuyer un workflow D-PLACE en identifiants linguistiques faisant autorité

### indian-ocean-voyages

Agrège et met en forme les données historiques de traversées de l'océan Indien pour comparaison avec la phylogéographie de M. tuberculosis L1 (indo-océanique). Enveloppe quatre sources ouvertes : ESTA (traite en Asie, ~5 300 voyages), GLOBALISE (5 millions de pages d'archives de la VOC), CLIWOC (287 114 journaux de bord européens géocodés) et le sous-ensemble océan Indien de SlaveVoyages.

Compétences : comparer la dispersion des sous-lignées L1 aux routes maritimes de l'océan Indien ; construire des matrices origine-destination pour tests de Mantel ; superposer des TMRCA aux chronologies de voyages ; relier la phylogéographie L1 aux réseaux VOC, à la traite Île de France/Bourbon ou au commerce omano-swahili

### iqtree-lsd2

Emploie IQ-TREE 2 et son LSD2 intégré (Least-Squares Dating 2) pour l'inférence phylogénétique en maximum de vraisemblance rapide et la datation moléculaire, alternative pragmatique à BEAST2 quand il faut un arbre daté sur 10³ à 10⁵ tips en minutes ou heures plutôt qu'en jours. IQ-TREE gère la sélection de modèle (ModelFinder), l'ultrafast bootstrap et la recherche d'arbre ; LSD2 convertit les longueurs de branche en temps calendaire via les dates des tips.

Compétences : construire un arbre MTBC en maximum de vraisemblance avec sélection de modèle et bootstrap ; dater l'arbre par tip-dating (LSD2) en alternative rapide à BEAST2 ; passer à l'échelle de milliers de génomes ; générer un arbre de départ pour un raffinement BEAST2 ultérieur

### itol

Téléverse, annote et exporte des figures d'arbres phylogénétiques de qualité publication via iTOL (Interactive Tree Of Life) avec le pipeline itolapi intégré. Transforme un arbre Newick/Nexus plus des pistes d'annotation (plages de couleur de lignées, couleurs de branches, symboles de bootstrap, jeux de données) en SVG/PDF/PNG, avec des presets pour article, supplément, présentation ou poster, plus export par lots et mode comparaison.

Compétences : produire une figure finale d'arbre de lignées MTBC pour un manuscrit ou une slide ; rendre un arbre RAxML/IQ-TREE annoté avec plages de couleur et bootstrap ; exporter le même arbre en plusieurs formats/presets ; scripter les téléversements iTOL plutôt que cliquer dans l'interface web

### migration-data

Agrège et met en forme des données de migration humaine pour comparaison avec les schémas MTBC : SlaveVoyages, stocks de migrants ONU, structure génétique HGDP, événements d'ADN ancien, charge TB de l'OMS et frise historique curée des migrations.

Compétences : comparer la dispersion des lignées MTBC aux mouvements humains ; construire des matrices de migration pour tests de Mantel ; superposer des TMRCA à une chronologie de migration ; préparer des figures reliant histoire bactérienne et humaine

### modern-human-reference-panels

Index des panels ouverts de génomes humains modernes de référence : 1000 Genomes (2 504 individus, 26 populations), Simons Genome Diversity Project (300 individus haute couverture, 142 populations), Human Genome Diversity Project (929 individus, 54 populations) et gnomAD. Comparateurs modernes canoniques pour toute analyse ADMIXTOOLS/qpAdm/statistiques f sur génomes anciens de l'AADR.

Compétences : préparer un run ADMIXTOOLS sur une cohorte AADR (outgroups et sources modernes) ; bâtir un fond de PCA pour échantillons anciens ; croiser une population humaine moderne avec une phylogéographie de pathogène ; vérifier la fréquence allélique d'un variant entre populations mondiales

### neolithic-14c

Index des bases radiocarbone régionales pour le Néolithique et les périodes adjacentes : EUROEVOL (Néolithique européen, 14 053 dates), NERD (Proche-Orient, 11 072 dates), plus RADON (Europe centrale), NeoNet (Méditerranée) et la base radiocarbone du Paléolithique européen (KU Leuven). Ensemble, ils donnent une couverture ¹⁴C continue du centre de domestication proche-oriental à l'expansion européenne secondaire, substrat idéal des arguments de transition démographique.

Compétences : construire un argument de transition démographique néolithique pour l'essor du MTBC adapté à l'humain ; cartographier l'arrivée de l'agriculture et de l'élevage en Europe face à une phylogénie TB ; produire des courbes de probabilité sommée (SPD) ; compléter le jeu mondial p3k14c par des données régionales plus fines

### nextflow-development

Exécute des pipelines de bioinformatique nf-core (rnaseq, sarek, atacseq) sur des données de séquençage.

Compétences : analyser des données RNA-seq, WGS/WES ou ATAC-seq, FASTQ locaux ou jeux publics GEO/SRA ; l'utilisateur mentionne nf-core, Nextflow, appel de variants, expression différentielle, réanalyse GEO, accessions GSE/GSM/SRR, ou création de samplesheet

### nextstrain

Emploie Nextstrain (Augur + Auspice + TreeTime + Nextclade) pour l'analyse phylogéographique en temps réel et la visualisation interactive de l'évolution des pathogènes à grande échelle. Augur chaîne filtrage, alignement, construction d'arbre, calibration temporelle, reconstruction ancestrale et inférence de trait discret (géographie) en un pipeline reproductible produisant du JSON pour le visualiseur web Auspice.

Compétences : produire une phylogéographie calibrée dans le temps pour une lignée ou un jeu MTBC de 10² à 10⁵ génomes ; construire une visualisation Auspice interactive pour un séminaire ou une revue par un collaborateur ; inférer les événements de transmission les plus probables entre pays ; dater les nœuds ancestraux avec TreeTime ; écrire un build Snakemake reproductible

### ontologies

Index et helper d'accès à l'OBO Foundry (150+ ontologies biomédicales actives) et à sa ressource pivot, la taxonomie NCBI. Fournit des vocabulaires de normalisation canoniques pour espèces et souches (NCBITaxon/LPSN), maladies (DOID), maladies infectieuses (IDO), environnements (ENVO), chimie (ChEBI), lieux (GAZ) et interactions hôte-microbiome (OHMI). Le liant qui rend interopérables les métadonnées d'aadr, enterobase, spaam, bacdive et pubtator.

Compétences : normaliser un champ libre espèce/souche/maladie/hôte/environnement/lieu en identifiant canonique ; ajouter des métadonnées codées par ontologie à un manuscrit ou jeu de données ; vérifier si un terme existe déjà dans une ontologie OBO ; produire des annotations conformes au Linked Data pour un supplément

### openalex

Interroge OpenAlex, le graphe de connaissances savant entièrement ouvert (307 M travaux, 118 M auteurs, 124k institutions, 65k concepts) publié par OurResearch comme successeur de Microsoft Academic Graph. API REST gratuite, métadonnées CC0 et dumps en masse. Substrat bibliométrique de référence pour les revues de littérature, l'analyse de réseaux de co-auteurs et la découverte par concept, complémentaire de PubMed/Europe PMC et de Google Scholar.

Compétences : construire une revue de littérature depuis une requête thématique ; cartographier les réseaux de co-signature autour d'une lignée MTBC ou d'un article ; lister les publications d'un labo ou chercheur ; résoudre des identifiants d'institution ; calculer des métriques de citation sans accès Web of Science ; enrichir une bibliographie de tags de concepts

### orbis

Interroge ORBIS, le modèle géospatial du réseau de transport du monde romain (Stanford, Scheidel & Meeks, ~200 apr. J.-C.). Fournit un réseau multimodal de 678 sites et 1 104 liens (route, fleuve, mer) avec modèles réalistes de temps de trajet, de coût financier et de variation saisonnière. Source de référence de la connectivité pré-moderne quantitative en Méditerranée.

Compétences : raisonner sur la diffusion du MTBC (ou tout pathogène bactérien) dans l'Empire romain et le bassin méditerranéen ; bâtir une hypothèse de dispersion d'une sous-lignée L4 à l'époque romaine ; modéliser la connectivité entre sites à ADN pathogène ancien (peste de Justinien, peste antonine) ; ancrer un récit de mobilité pré-moderne à des échelles concrètes de coût de voyage

### owtrad

Interroge OWTRAD (Old World Trade Routes Project, T.M. Ciolek, ANU), archive SIG communautaire de référence des routes terrestres, fluviales et maritimes de commerce, pèlerinage, militaires et postales d'Eurasie et d'Afrique de ~10 000 av. J.-C. à ~1820. Inclut Route de la soie, Route des épices, de l'ambre, du sel, et un gazetteer de 3 130 lieux plus des catalogues de caravansérails, ponts et forts.

Compétences : construire un récit Route de la soie ou caravanier pour des lignées MTBC (surtout L2 Beijing et L3 CAS en Asie centrale) ; superposer une phylogénie TB ou Y ; pestis sur des corridors historiques ; identifier des caravansérails comme sites candidats de mélange humain/animal ; assembler un contexte de mobilité pré-moderne

### p3k14c

Interroge la base radiocarbone archéologique mondiale p3k14c (Bird et al. 2022, 180 070 dates ¹⁴C) pour ancrer l'émergence des lignées MTBC dans les chronologies archéologiques, en particulier les foyers de domestication animale (bovins → M. bovis, caprins → M. caprae) et la sédentarisation néolithique.

Compétences : dater l'émergence d'une lignée MTBC zoonotique ; construire un récit néolithique/domestication ; corréler des TMRCA aux périodes culturelles archéologiques ; identifier des sites archéologiques proches des lieux d'échantillonnage de souches TB modernes

### paleoclimate

Index de reconstructions paléoclimatiques ouvertes pour coupler phylogéographie des pathogènes et épidémiologie historique à la variabilité climatique passée : PAGES 2k (reconstruction multi-proxy des 2 000 dernières années), NOAA Paleoclimatology, carottes de glace du Groenland et de l'Antarctique (GISP2, NGRIP, EPICA) et reconstructions bioclimatiques paléo WorldClim/CHELSA (LGM, mi-Holocène).

Compétences : tester si l'expansion d'une lignée MTBC coïncide avec un intervalle climatique chaud/froid ; corréler la peste de Justinien au petit âge glaciaire de l'Antiquité tardive ; cadrer la transition démographique néolithique dans l'optimum climatique holocène ; extraire des séries de température/précipitations pour une région et période

### pastml

Emploie PastML (Institut Pasteur, Ishikawa, Zhukova, Gascuel) pour la reconstruction rapide de caractères ancestraux en maximum de vraisemblance sur arbres enracinés, avec visualisation en arbre compressé intégrée. Reconstruit les valeurs les plus probables de caractères discrets (localisation, hôte, phénotype de résistance, lignée) à chaque nœud interne, puis condense l'arbre en une carte HTML interactive ne montrant que les zones de changement d'état. Conçu pour des arbres de 10⁴ à 10⁵ tips.

Compétences : reconstruire l'origine géographique d'une sous-lignée MTBC ; inférer des sauts d'hôte ancestraux d'écotypes zoonotiques ; visualiser l'émergence de la résistance sur un arbre TB ; produire un arbre compressé HTML pour une slide ; mapper un trait discret sur une phylogénie existante sans reconstruire l'arbre

### pleiades

Interroge Pleiades, le gazetteer communautaire et graphe des lieux antiques (NYU ISAW + UNC AWMC), dérivé du Barrington Atlas du monde grec et romain. Contient 42 000+ lieux avec URI stables, coordonnées géocodées, codage de période (archaïque à Antiquité tardive), types de sites et un graphe explicite de connexions lieu à lieu. Résolveur de référence pour tout toponyme antique méditerranéen.

Compétences : résoudre un nom de lieu antique en identifiant stable et coordonnées ; géocoder des métadonnées d'échantillons TB / Y ; pestis anciens ; construire une carte de sites filtrée par chronologie pour un argument phylogéographique ; chaîner des toponymes antiques à ORBIS et OWTRAD via des identifiants stables

### pubmed-database

Accès direct à l'API REST de PubMed : requêtes booléennes/MeSH avancées, API E-utilities, traitement par lots, gestion des citations. Pour les workflows Python, préférer biopython (Bio.Entrez). Pour la littérature TB/MTBC spécifiquement, préférer tbmonitor-papers (SQL sub-seconde sur un corpus pré-indexé de ~190k articles PubMed TB avec MeSH/mots-clés/auteurs en JSON).

Compétences : sujets non-TB ; travail HTTP/REST direct ; implémentations d'API personnalisées

### pubtator

Interroge PubTator 3.0 / PubTator Central (NCBI BioNLP), service de référence d'annotations d'entités biomédicales pré-calculées sur les résumés PubMed et le texte intégral PMC. Utilise un NER de pointe (AIONER) pour étiqueter six types d'entités : gènes/protéines, maladies, chimie, espèces, variants génétiques et lignées cellulaires, avec extraction de relations en v3. Évite d'entraîner son propre NER biomédical.

Compétences : pré-annoter des résumés ou textes intégraux MTBC avec des entités standardisées ; extraire des mentions de gènes/variants/médicaments d'un article TB ; construire un graphe d'associations gène-maladie depuis la littérature ; accélérer un pipeline de fouille de texte ; Pour des corpus TB seuls, bâtir la liste d'abstracts avec tbmonitor-papers avant de passer les PMID à PubTator

### pysam

Module Python pour lire, manipuler et écrire les formats d'alignement génomique (SAM/BAM/CRAM) et de variants (VCF/BCF). Enveloppe de htslib.

Compétences : lire ou écrire des BAM/CRAM/VCF ; manipuler des alignements ou des variants en Python

### rdkit

Boîte à outils open source de chémoinformatique et de machine learning pour la découverte de médicaments, la manipulation moléculaire et le calcul de propriétés chimiques. RDKit gère les SMILES, les empreintes moléculaires, la recherche de sous-structures, la génération de conformères 3D, la modélisation de pharmacophores et le QSAR.

Compétences : travailler avec des structures chimiques ; propriétés drug-like, similarité moléculaire, criblage virtuel ou workflows de chimie computationnelle

### read-scientific-pdf

Extraction rapide du texte d'un PDF scientifique (articles, thèses, rapports) via pdftotext, markitdown ou pdfminer, puis relecture du fichier texte intermédiaire avec Read. Pipeline plus efficace que la lecture multimodale native pour les documents longs (>10 pages), les PDF à colonnes multiples, les tableaux complexes et la lecture en lot pour revues de littérature.

Compétences : PDF scientifique long ; article à colonnes ou tableaux complexes ; lecture séquentielle d'un corpus pour une revue ; PDF scanné nécessitant OCR ; quand la lecture native d'un PDF renvoie un résultat partiel ou inattendu

### scanpy

Boîte à outils passant à l'échelle pour l'analyse de données d'expression génique en cellule unique. Bâtie sur AnnData, axée sur le clustering, l'inférence de trajectoires et la visualisation.

Compétences : analyser des données single-cell ; clustering, inférence de trajectoires, visualisation d'expression cellulaire

### scikit-bio

Bibliothèque de bioinformatique et de statistiques d'écologie des communautés. Fournit structures de données et algorithmes pour séquences, alignements, phylogénétique et analyse de diversité. Essentielle pour la recherche sur le microbiome et la data science écologique : diversité alpha/bêta, ordination (PCoA), arbres phylogénétiques, matrices de distances, PERMANOVA.

Compétences : calculer des métriques de diversité alpha/bêta ; ordination (PCoA) ; manipuler séquences ou matrices de distances ; PERMANOVA et analyse d'écologie des communautés

### seaborn

Bibliothèque de visualisation de données Python basée sur matplotlib. Offre une interface de haut niveau pour des graphiques statistiques attrayants et informatifs. Idéale pour explorer les relations entre variables et visualiser des distributions : EDA, graphes de relation, de distribution, comparaisons catégorielles, régression, cartes de chaleur et clustermaps.

Compétences : visualisation statistique et analyse exploratoire (EDA) ; graphes de relation/distribution ; comparaisons catégorielles ; heatmaps ; graphiques de qualité publication depuis des DataFrames pandas

### seshat

Interroge Seshat: Global History Databank, base historique quantitative de référence de ~400 entités politiques du Néolithique à ~1900, couvrant complexité sociale, guerre, religion, agriculture et événements de crise/effondrement. Fournit l'échafaudage quantitatif au niveau des polities pour tester comment formation d'État, densité de population, urbanisation et crises ont façonné la persistance et la dispersion des pathogènes adaptés à l'humain.

Compétences : construire un argument quantitatif densité/urbanisation pour la persistance du MTBC adapté à l'humain ; corréler l'émergence d'un pathogène à des crises ou effondrements de polities (CrisisDB) ; cadrer l'essor d'une lignée dans un contexte de formation d'État ; écrire une section cliodynamique sur la coévolution pathogènes et complexité sociale

### slavevoyages

Interroge slavevoyages.org (36k+ voyages, 1514-1866) pour construire des scénarios phylogéographiques d'articles sur les lignées MTBC. Corrèle les distributions de lignées TB aux routes commerciales transatlantiques, aux TMRCA et aux événements migratoires historiques.

Compétences : expliquer la présence dans le Nouveau Monde de lignées TB africaines (L5, L6, L4) ; bâtir une hypothèse de dispersion d'une lignée ; corréler un TMRCA à des mouvements de population historiques (Côte de l'Or → Amériques, golfe du Bénin, etc.)

### tooluniverse-sequence-retrieval

Récupère des séquences biologiques (ADN, ARN, protéines) depuis NCBI et ENA, avec désambiguïsation de gènes, gestion des types d'accession et profils de séquence complets. Produit des rapports détaillés avec métadonnées, références inter-bases et options de téléchargement.

Compétences : récupérer des séquences nucléotidiques ou protéiques, des données de génome ; l'utilisateur mentionne des accessions GenBank, RefSeq ou EMBL

### wals

Interroge WALS, le World Atlas of Language Structures (Dryer & Haspelmath, Institut Max Planck), base ouverte de référence des traits typologiques (phonologie, morphologie, syntaxe, ordre des mots, lexique) pour ~3 500 langues. Fournit 192 paramètres typologiques (~76 000 codages), tous rattachés aux Glottocodes pour jointure avec le reste de la constellation d'anthropologie linguistique.

Compétences : tester si un trait typologique linguistique corrèle avec la distribution géographique d'une lignée MTBC ; construire une covariable de typologie linguistique pour des analyses interculturelles ; contrôler la similarité typologique dans des études comparatives ; produire un profil typologique de populations utiles à un récit phylogéographique

### worldclim-bioclim

Emploie WorldClim 2.1 et CHELSA v2.1, les deux jeux raster bioclimatiques mondiaux haute résolution de référence (19 variables BIO jusqu'à 1 km, versions actuelle et paléo pour LGM et mi-Holocène). Substrat canonique pour la modélisation de niche écologique des pathogènes, l'extraction du climat au point pour des lieux d'échantillonnage TB et les superpositions climatiques haute résolution sur cartes phylogéographiques.

Compétences : extraire des variables bioclimatiques aux sites d'échantillonnage TB modernes ou anciens ; modéliser la niche climatique d'une lignée MTBC ; comparer les niches de M ; bovis, M ; caprae et M ; tuberculosis ; produire des couches climatiques pour une carte ; calculer des statistiques de recouvrement de niche entre écotypes

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

