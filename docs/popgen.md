# Plugin `popgen`

> Academic research toolkit for ancient and modern human population genetics, archaeology, paleoclimate, linguistics and historical migration corpora, plus host-pathogen co-evolution. Guyeux group (FEMTO-ST), peer-reviewed research.

Skills propres (canoniques) : **26** ; skills partagés utilisés (symlinks) : **0**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [aadr](#aadr) ; [abc-xgboost](#abc-xgboost) ; [amtdb](#amtdb) ; [atlantic-voyages](#atlantic-voyages) ; [bovine-genomics](#bovine-genomics) ; [card](#card) ; [coevolution](#coevolution) ; [d-place](#d-place) ; [domestication-pathways](#domestication-pathways) ; [glottolog](#glottolog) ; [host-pathogen-pair](#host-pathogen-pair) ; [indian-ocean-voyages](#indian-ocean-voyages) ; [migration-data](#migration-data) ; [modern-human-reference-panels](#modern-human-reference-panels) ; [neolithic-14c](#neolithic-14c) ; [orbis](#orbis) ; [owtrad](#owtrad) ; [p3k14c](#p3k14c) ; [paleoclimate](#paleoclimate) ; [pleiades](#pleiades) ; [seshat](#seshat) ; [slavevoyages](#slavevoyages) ; [spaam-ancient-metagenome-dir](#spaam-ancient-metagenome-dir) ; [spaam-community](#spaam-community) ; [wals](#wals) ; [worldclim-bioclim](#worldclim-bioclim)

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

Agrege et met en forme les donnees historiques de voyages maritimes atlantiques pour comparaison avec la phylogeographie de M. tuberculosis L5/L6 (M. africanum) et des sous-lignees L4. Enveloppe six sources ouvertes : SlaveVoyages Trans-Atlantic (Eltis et al., Emory/Rice, 36 000 voyages, 1514-1866), AfricanOrigins (environ 92 000 individus nommes avec origine ethnolinguistique inferee), Liberated Africans Database (environ 250 000 individus, 1808-1862), le portail Slavery, Abolition and Social Justice, Intra-American Voyages (environ 11 000 voyages, 1626-1860) et Voyages to Liberty.

Compétences : comparer la dispersion L5/L6 aux routes atlantiques documentees ; construire des matrices origine-destination pour des tests de Mantel contre les distances MTBC deux a deux ; superposer des estimations de TMRCA a des chronologies de voyages ; relier des souches L5/L6 de diaspora a leurs regions sources ouest-africaines probables

### bovine-genomics

Index des ressources génomiques bovines en accès public pour la génétique des populations et les études phylogéographiques : 1000 Bull Genomes (~2 700 bovins WGS, ~90 M variants), Bovine HapMap (37 470 SNP, 19 races) et Bovine Genome Variation Database (BGVD, ~60 M SNP). Couvre la structure des races, la divergence taurin/zébu et le signal néolithique de domestication bovine.

Compétences : construire une référence phylogéographique côté bovin ; récupérer des données WGS ou SNP bovines ; comparer les distributions taurin/zébu ; ancrer une étude sur la domestication néolithique du bœuf

### card

Interroge CARD 2.0 (Canadian Archaeological Radiocarbon Database), compilation de référence des datations radiocarbone archéologiques d'Amérique du Nord (~50 000 dates, plus ~104 000 pour les 48 États contigus) couvrant contextes archéologiques, paléontologiques et géologiques, avec extension vers l'Amérique centrale et du Sud. Pendant américain d'EUROEVOL (Europe) et NERD (Proche-Orient) pour l'ancrage chronologique.

Compétences : construire une toile de fond chronologique pour des récits pré-colombiens et coloniaux des Amériques ; contextualiser le saut d'hôte pré-colombien de M ; pinnipedii dans les Andes ; extraire des dates par site pour des régions sous-représentées dans p3k14c

### coevolution

Boîte à outils académique (groupe Guyeux, FEMTO-ST) pour les tests statistiques de co-divergence MTBC-humain et de structure géographique : test de Mantel, Mantel partiel, isolement par la distance, PACo (approche procustéenne de cophylogénie), FST (Weir & Cockerham) et AMOVA.

Compétences : tester si la diversité génétique du MTBC corrèle avec la distance géographique ; comparer la structure des populations bactériennes et humaines ; quantifier la différenciation entre populations MTBC de pays ou régions distincts

### d-place

Interroge D-PLACE (Database of Places, Language, Culture and Environment), base ouverte de référence des traits culturels, linguistiques et environnementaux de plus de 1 400 sociétés humaines préindustrielles. Fournit des variables interculturelles (Ethnographic Atlas, jeu de Binford) reliées aux couches bioclimatiques et aux langues Glottolog, avec pour certaines familles des phylogénies linguistiques bayésiennes.

Compétences : construire un contexte culturel/écologique de la diffusion d'un pathogène ; tester si un mode de subsistance (pastoralisme, agriculture, chasse-cueillette) corrèle avec la distribution d'une lignée MTBC ; contrôler la non-indépendance phylogénétique en analyses interculturelles ; rédiger une section éco-anthropologie

### domestication-pathways

Agrege centres de domestication, routes de dispersion et donnees de transition neolithique pour les etudes de coevolution avec le complexe M. tuberculosis. Enveloppe quatre familles de sources ouvertes : zooarcheologie (ABMAP, sous-ensemble animal AADR), archeobotanique (ADEMNES, BRAIN), ADN humain ancien (AADR) et radiocarbone mondial (p3k14c, CONTEXT, AgriChange). Inclut des tables curees de centres d'origine (Croissant fertile, Indus, Yangtze, Sahel, Mesoamerique, Andes, Nouvelle-Guinee, Ethiopie, Sahara vert, Amazonie), de routes de dispersion (LBK, Cardial, bantoue, steppique, austronesienne, Lapita, transsaharienne, echange colombien) et d'evenements chronologiques lies a l'emergence du MTBC.

Compétences : construire l'arriere-plan coevolutif de M ; bovis, M ; caprae ou M ; orygis ; cadrer l'emergence de M ; tuberculosis sensu stricto a partir d'un ancetre de type M ; canettii via la sedentarisation neolithique ; relier des TMRCA MTBC aux transitions agricoles

### glottolog

Interroge Glottolog, catalogue de référence des langues, familles et dialectes du monde (8 238 languoïdes, 246 familles, 183 isolats, 227 langues des signes). Fournit des identifiants Glottocode stables, la classification généalogique, des coordonnées, la macroaire, la correspondance ISO 639-3, le statut de mise en danger et 460k+ références bibliographiques. Couche fondamentale de toute analyse cross-linguistique ou de coévolution biologie-langue.

Compétences : résoudre un nom de langue en Glottocode stable ; obtenir la classification généalogique de la langue d'une population ; joindre un jeu génétique ou pathogène à des métadonnées linguistiques ; construire un contrôle par famille de langues ; appuyer un workflow D-PLACE en identifiants linguistiques faisant autorité

### host-pathogen-pair

Boîte à outils d'éco-anthropologie (groupe Guyeux, FEMTO-ST). Génère des tables de co-occurrence géo-temporelle de paires hôte ancien / microorganisme ancien à partir de deux corpus ouverts : SPAAM AncientMetagenomeDir (génomique microbienne ancienne, dont Mycobacterium, Yersinia pestis, Salmonella) et le catalogue AADR de génomes humains anciens (Reich Lab, v66, 16 000+ individus). Sortie : un TSV de paires candidates classées par distance de Haversine et recouvrement temporel.

Compétences : planifier un projet de coévolution hôte-microorganisme ; valider les paires disponibles pour une région/période ; préparer un séminaire ou une candidature académique ; documenter l'absence de paires (résultat négatif valorisable)

### indian-ocean-voyages

Agrège et met en forme les données historiques de traversées de l'océan Indien pour comparaison avec la phylogéographie de M. tuberculosis L1 (indo-océanique). Enveloppe quatre sources ouvertes : ESTA (traite en Asie, ~5 300 voyages), GLOBALISE (5 millions de pages d'archives de la VOC), CLIWOC (287 114 journaux de bord européens géocodés) et le sous-ensemble océan Indien de SlaveVoyages.

Compétences : comparer la dispersion des sous-lignées L1 aux routes maritimes de l'océan Indien ; construire des matrices origine-destination pour tests de Mantel ; superposer des TMRCA aux chronologies de voyages ; relier la phylogéographie L1 aux réseaux VOC, à la traite Île de France/Bourbon ou au commerce omano-swahili

### migration-data

Agrège et met en forme des données de migration humaine pour comparaison avec les schémas MTBC : SlaveVoyages, stocks de migrants ONU, structure génétique HGDP, événements d'ADN ancien, charge TB de l'OMS et frise historique curée des migrations.

Compétences : comparer la dispersion des lignées MTBC aux mouvements humains ; construire des matrices de migration pour tests de Mantel ; superposer des TMRCA à une chronologie de migration ; préparer des figures reliant histoire bactérienne et humaine

### modern-human-reference-panels

Index des panels ouverts de génomes humains modernes de référence : 1000 Genomes (2 504 individus, 26 populations), Simons Genome Diversity Project (300 individus haute couverture, 142 populations), Human Genome Diversity Project (929 individus, 54 populations) et gnomAD. Comparateurs modernes canoniques pour toute analyse ADMIXTOOLS/qpAdm/statistiques f sur génomes anciens de l'AADR.

Compétences : préparer un run ADMIXTOOLS sur une cohorte AADR (outgroups et sources modernes) ; bâtir un fond de PCA pour échantillons anciens ; croiser une population humaine moderne avec une phylogéographie de pathogène ; vérifier la fréquence allélique d'un variant entre populations mondiales

### neolithic-14c

Index des bases radiocarbone régionales pour le Néolithique et les périodes adjacentes : EUROEVOL (Néolithique européen, 14 053 dates), NERD (Proche-Orient, 11 072 dates), plus RADON (Europe centrale), NeoNet (Méditerranée) et la base radiocarbone du Paléolithique européen (KU Leuven). Ensemble, ils donnent une couverture ¹⁴C continue du centre de domestication proche-oriental à l'expansion européenne secondaire, substrat idéal des arguments de transition démographique.

Compétences : construire un argument de transition démographique néolithique pour l'essor du MTBC adapté à l'humain ; cartographier l'arrivée de l'agriculture et de l'élevage en Europe face à une phylogénie TB ; produire des courbes de probabilité sommée (SPD) ; compléter le jeu mondial p3k14c par des données régionales plus fines

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

### pleiades

Interroge Pleiades, le gazetteer communautaire et graphe des lieux antiques (NYU ISAW + UNC AWMC), dérivé du Barrington Atlas du monde grec et romain. Contient 42 000+ lieux avec URI stables, coordonnées géocodées, codage de période (archaïque à Antiquité tardive), types de sites et un graphe explicite de connexions lieu à lieu. Résolveur de référence pour tout toponyme antique méditerranéen.

Compétences : résoudre un nom de lieu antique en identifiant stable et coordonnées ; géocoder des métadonnées d'échantillons TB / Y ; pestis anciens ; construire une carte de sites filtrée par chronologie pour un argument phylogéographique ; chaîner des toponymes antiques à ORBIS et OWTRAD via des identifiants stables

### seshat

Interroge Seshat: Global History Databank, base historique quantitative de référence de ~400 entités politiques du Néolithique à ~1900, couvrant complexité sociale, guerre, religion, agriculture et événements de crise/effondrement. Fournit l'échafaudage quantitatif au niveau des polities pour tester comment formation d'État, densité de population, urbanisation et crises ont façonné la persistance et la dispersion des pathogènes adaptés à l'humain.

Compétences : construire un argument quantitatif densité/urbanisation pour la persistance du MTBC adapté à l'humain ; corréler l'émergence d'un pathogène à des crises ou effondrements de polities (CrisisDB) ; cadrer l'essor d'une lignée dans un contexte de formation d'État ; écrire une section cliodynamique sur la coévolution pathogènes et complexité sociale

### slavevoyages

Interroge slavevoyages.org (36k+ voyages, 1514-1866) pour construire des scénarios phylogéographiques d'articles sur les lignées MTBC. Corrèle les distributions de lignées TB aux routes commerciales transatlantiques, aux TMRCA et aux événements migratoires historiques.

Compétences : expliquer la présence dans le Nouveau Monde de lignées TB africaines (L5, L6, L4) ; bâtir une hypothèse de dispersion d'une lignée ; corréler un TMRCA à des mouvements de population historiques (Côte de l'Or → Amériques, golfe du Bénin, etc.)

### spaam-ancient-metagenome-dir

Interroge SPAAM AncientMetagenomeDir, catalogue communautaire de référence de tous les échantillons métagénomiques anciens et génomes microbiens anciens publiés. Trouve les échantillons anciens de M. tuberculosis et pathogènes apparentés, leurs publications, sites, dates et accessions ENA/SRA, et les apparie aux hôtes humains anciens de l'AADR pour des récits de coévolution.

Compétences : trouver des génomes MTBC anciens publiés ; localiser les données brutes (ENA/SRA) de pathogènes anciens ; apparier une souche TB ancienne à son hôte humain dans l'AADR ; lister les métagénomes anciens d'une région/période ; alimenter le côté pathogène d'une histoire de coévolution

### spaam-community

Index de l'écosystème communautaire SPAAM (Standards, Precautions and Advances in Ancient Metagenomics), organisation faîtière de la métagénomique ancienne. Couvre outils, pipelines, supports de formation, standards de métadonnées, annuaires de labos et guides de référence au-delà du catalogue AncientMetagenomeDir. À utiliser comme méta-index pour trouver un outil, pipeline, tutoriel ou ressource sur l'ADN microbien ancien.

Compétences : choisir un pipeline de métagénomique ancienne (eager vs aMeta) ; trouver un tutoriel sur les patterns de dommage de l'ADN ancien ; valider des métadonnées contre le standard MInAS ; identifier des labos sur un pathogène ancien précis ; s'initier à l'infrastructure SPAAM

### wals

Interroge WALS, le World Atlas of Language Structures (Dryer & Haspelmath, Institut Max Planck), base ouverte de référence des traits typologiques (phonologie, morphologie, syntaxe, ordre des mots, lexique) pour ~3 500 langues. Fournit 192 paramètres typologiques (~76 000 codages), tous rattachés aux Glottocodes pour jointure avec le reste de la constellation d'anthropologie linguistique.

Compétences : tester si un trait typologique linguistique corrèle avec la distribution géographique d'une lignée MTBC ; construire une covariable de typologie linguistique pour des analyses interculturelles ; contrôler la similarité typologique dans des études comparatives ; produire un profil typologique de populations utiles à un récit phylogéographique

### worldclim-bioclim

Emploie WorldClim 2.1 et CHELSA v2.1, les deux jeux raster bioclimatiques mondiaux haute résolution de référence (19 variables BIO jusqu'à 1 km, versions actuelle et paléo pour LGM et mi-Holocène). Substrat canonique pour la modélisation de niche écologique des pathogènes, l'extraction du climat au point pour des lieux d'échantillonnage TB et les superpositions climatiques haute résolution sur cartes phylogéographiques.

Compétences : extraire des variables bioclimatiques aux sites d'échantillonnage TB modernes ou anciens ; modéliser la niche climatique d'une lignée MTBC ; comparer les niches de M ; bovis, M ; caprae et M ; tuberculosis ; produire des couches climatiques pour une carte ; calculer des statistiques de recouvrement de niche entre écotypes
