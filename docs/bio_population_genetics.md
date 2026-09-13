# Plugin `bio_population_genetics`

> Academic research toolkit for ancient and modern human population genetics, archaeological radiocarbon databases, paleoclimate reconstructions, historical migration corpora, and linguistic/cultural atlases. Bundles general-purpose phylogenetic, statistical, and literature-mining tools used by the Guyeux group (FEMTO-ST, University of Franche-Comte) for peer-reviewed scientific publications on human evolutionary history and eco-anthropology.

## Rôle dans un projet M. tuberculosis

Contexte hôte et outillage générique. Pour une étude M. tuberculosis, l'histoire des populations humaines, les migrations, la paléoclimatologie et l'archéologie éclairent la co-évolution hôte-pathogène et la dispersion des lignées du MTBC. Le plugin porte aussi les briques transversales (phylogénétique, statistiques, fouille de littérature) réutilisées par les analyses MTBC elles-mêmes.

Skills propres (canoniques) : **55** ; skills partagés utilisés (symlinks) : **3**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [aadr](#aadr) ; [abc-xgboost](#abc-xgboost) ; [amtdb](#amtdb) ; [atlantic-voyages](#atlantic-voyages) ; [bayesian-skyline](#bayesian-skyline) ; [beast2-phylogeography](#beast2-phylogeography) ; [bioc-pmc](#bioc-pmc) ; [biopython](#biopython) ; [bioskills](#bioskills) ; [biotools](#biotools) ; [boltz](#boltz) ; [bovine-genomics](#bovine-genomics) ; [card](#card) ; [clinical-trial-protocol-skill](#clinical-trial-protocol-skill) ; [create-viz](#create-viz) ; [d-place](#d-place) ; [domestication-pathways](#domestication-pathways) ; [esm-atlas-cli](#esm-atlas-cli) ; [europe-pmc](#europe-pmc) ; [foldseek](#foldseek) ; [geo-map](#geo-map) ; [glottolog](#glottolog) ; [indian-ocean-voyages](#indian-ocean-voyages) ; [iqtree-lsd2](#iqtree-lsd2) ; [itol](#itol) ; [migration-data](#migration-data) ; [modern-human-reference-panels](#modern-human-reference-panels) ; [neolithic-14c](#neolithic-14c) ; [nextflow-development](#nextflow-development) ; [nextstrain](#nextstrain) ; [ontologies](#ontologies) ; [openalex](#openalex) ; [orbis](#orbis) ; [owtrad](#owtrad) ; [p3k14c](#p3k14c) ; [paleoclimate](#paleoclimate) ; [pastml](#pastml) ; [pleiades](#pleiades) ; [pubmed-database](#pubmed-database) ; [pubtator](#pubtator) ; [pysam](#pysam) ; [rdkit](#rdkit) ; [read-scientific-pdf](#read-scientific-pdf) ; [remote-compute](#remote-compute) ; [scanpy](#scanpy) ; [sci-figure](#sci-figure) ; [scientific-problem-selection](#scientific-problem-selection) ; [scikit-bio](#scikit-bio) ; [scikit-learn](#scikit-learn) ; [seshat](#seshat) ; [slavevoyages](#slavevoyages) ; [statsmodels](#statsmodels) ; [tooluniverse-sequence-retrieval](#tooluniverse-sequence-retrieval) ; [wals](#wals) ; [worldclim-bioclim](#worldclim-bioclim)

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

### bayesian-skyline

Boite a outils de recherche academique pour la recherche phylodynamique evaluee par les pairs. Famille des skylines bayesiens de BEAST (Bayesian Skyline Plot, Skyride, Skygrid, Birth-Death Skyline) pour reconstruire la taille efficace de population Ne(t) ou le nombre de reproduction effectif Re(t) au cours du temps a partir de genomes dates d'une collection d'etude publiee. Inclut une recette sans interface graphique pour emettre les priors skyline en XML et executer BEAST sans affichage.

Compétences : reconstruire le Ne(t) historique d'une lignee MTBC ; tester une expansion contre une transition demographique humaine (Neolithique, age du Bronze, contact colombien) ; estimer un Re(t) sur une periode historique ; produire une figure skyline pour un manuscrit

### beast2-phylogeography

Emploie BEAST2 et ses paquets de phylogéographie (MASCOT, BASTA, DTA classique) pour la datation moléculaire bayésienne rigoureuse, le tip-dating d'échantillons anciens et l'inférence phylogéographique par coalescent structuré. Cadre bayésien de référence pour la phylogénétique à petite/moyenne échelle où l'on veut les distributions postérieures complètes sur la topologie, les temps de divergence, les taux de migration et les états ancestraux.

Compétences : dater des tips MTBC anciens avec intervalles de crédibilité complets ; lancer une phylogéographie par coalescent structuré (MASCOT/BASTA) ; produire un arbre bayésien calibré dans le temps ; tester des modèles démographiques concurrents ; quand un pipeline maximum de vraisemblance/Nextstrain manque de rigueur pour un relecteur

### bioc-pmc

BioC-PMC, le sous-ensemble Open Access et manuscrits d'auteur de PubMed Central au format BioC (NCBI/NLM) : environ 3 millions d'articles biomedicaux en texte integral avec sections structurees (titre, resume, corps, figures, tableaux) en XML ou JSON, optimise pour les pipelines de TAL. Pour les flux TB limites aux resumes, preferer tbmonitor-papers (environ 190 000 resumes TB preindexes, SQL en moins d'une seconde) ; BioC-PMC est le bon outil des que le corps du texte, les figures ou les tableaux sont necessaires.

Compétences : construire un corpus plein texte pour le text mining MTBC ou M ; bovis ; recuperer des sections structurees pour de la reconnaissance d'entites nommees ou de l'extraction de relations ; telecharger en masse des articles PMC OA en format lisible par machine ; alimenter PubTator ou un modele de NER

### biopython

Guide complet de Biopython, la bibliothèque Python de référence en biologie computationnelle et bioinformatique. Sert à l'analyse de séquences ADN/ARN/protéines, aux entrées-sorties (FASTA, FASTQ, GenBank, PDB), à l'alignement, aux recherches BLAST, à l'analyse phylogénétique et structurale, et à l'accès aux bases NCBI.

Compétences : manipuler des séquences ou fichiers biologiques en Python ; interroger les bases NCBI (Bio.Entrez) ; scripter des analyses phylogénétiques ou d'alignement

### bioskills

Installe 425 skills de bioinformatique couvrant l'analyse de séquences, le RNA-seq, le single-cell, l'appel de variants, la métagénomique, la biologie structurale et 56 autres catégories.

Compétences : mettre en place des capacités de bioinformatique ; quand une tâche bioinfo requiert un skill spécialisé pas encore installé

### biotools

Academic research toolkit (Guyeux group, FEMTO-ST) for querying the ELIXIR bio.tools registry (~30 000 catalogued bioinformatics tools) and, crucially, diffing the result against the skills and knowledge base we already have, so a sweep returns what is genuinely new rather than what we already use

Compétences : asking whether a published tool exists for a task before writing one, looking for independent implementations to cross-check a home-made method, doing a periodic watch on tooling for MTBC, mycobacteria, Yersinia or any bacterium, or checking whether a tool named in a manuscript is registered and still alive

### boltz

Boite a outils de recherche academique (groupe Guyeux, FEMTO-ST), bio-informatique structurale evaluee par les pairs : predit EN LOCAL des complexes biomoleculaires (multimeres, ions metalliques, ligands) avec Boltz-2, sans compte ni GPU (inference sur processeur), la ou AlphaFold Server n'est pas automatisable. Fournit la recette d'installation validee, l'ecriture des entrees YAML, la reutilisation d'un MSA deja produit, la lecture correcte des sorties (le schema Boltz differe du schema AF3) et les garde-fous d'interpretation.

Compétences : tester une interaction ou une homo-oligomerisation ; savoir si un site metallique est complete en trans ; cribler un ligand ou un substrat candidat ; refaire une prediction de complexe sans solliciter l'utilisateur

### bovine-genomics

Index des ressources génomiques bovines en accès public pour la génétique des populations et les études phylogéographiques : 1000 Bull Genomes (~2 700 bovins WGS, ~90 M variants), Bovine HapMap (37 470 SNP, 19 races) et Bovine Genome Variation Database (BGVD, ~60 M SNP). Couvre la structure des races, la divergence taurin/zébu et le signal néolithique de domestication bovine.

Compétences : construire une référence phylogéographique côté bovin ; récupérer des données WGS ou SNP bovines ; comparer les distributions taurin/zébu ; ancrer une étude sur la domestication néolithique du bœuf

### card

Interroge CARD 2.0 (Canadian Archaeological Radiocarbon Database), compilation de référence des datations radiocarbone archéologiques d'Amérique du Nord (~50 000 dates, plus ~104 000 pour les 48 États contigus) couvrant contextes archéologiques, paléontologiques et géologiques, avec extension vers l'Amérique centrale et du Sud. Pendant américain d'EUROEVOL (Europe) et NERD (Proche-Orient) pour l'ancrage chronologique.

Compétences : construire une toile de fond chronologique pour des récits pré-colombiens et coloniaux des Amériques ; contextualiser le saut d'hôte pré-colombien de M ; pinnipedii dans les Andes ; extraire des dates par site pour des régions sous-représentées dans p3k14c

### clinical-trial-protocol-skill

Génère des protocoles d'essais cliniques pour dispositifs médicaux ou médicaments.

Compétences : l'utilisateur demande de créer un protocole d'essai clinique, de concevoir une étude clinique, de rechercher des essais similaires, ou de préparer une documentation de soumission FDA

### create-viz

Crée des visualisations de qualité publication avec Python.

Compétences : transformer un résultat de requête ou un DataFrame en graphique ; choisir le bon type de graphique pour une tendance ou une comparaison ; produire une figure pour un rapport ou une présentation ; obtenir un graphique interactif avec survol et zoom

### d-place

Interroge D-PLACE (Database of Places, Language, Culture and Environment), base ouverte de référence des traits culturels, linguistiques et environnementaux de plus de 1 400 sociétés humaines préindustrielles. Fournit des variables interculturelles (Ethnographic Atlas, jeu de Binford) reliées aux couches bioclimatiques et aux langues Glottolog, avec pour certaines familles des phylogénies linguistiques bayésiennes.

Compétences : construire un contexte culturel/écologique de la diffusion d'un pathogène ; tester si un mode de subsistance (pastoralisme, agriculture, chasse-cueillette) corrèle avec la distribution d'une lignée MTBC ; contrôler la non-indépendance phylogénétique en analyses interculturelles ; rédiger une section éco-anthropologie

### domestication-pathways

Agrege centres de domestication, routes de dispersion et donnees de transition neolithique pour les etudes de coevolution avec le complexe M. tuberculosis. Enveloppe quatre familles de sources ouvertes : zooarcheologie (ABMAP, sous-ensemble animal AADR), archeobotanique (ADEMNES, BRAIN), ADN humain ancien (AADR) et radiocarbone mondial (p3k14c, CONTEXT, AgriChange). Inclut des tables curees de centres d'origine (Croissant fertile, Indus, Yangtze, Sahel, Mesoamerique, Andes, Nouvelle-Guinee, Ethiopie, Sahara vert, Amazonie), de routes de dispersion (LBK, Cardial, bantoue, steppique, austronesienne, Lapita, transsaharienne, echange colombien) et d'evenements chronologiques lies a l'emergence du MTBC.

Compétences : construire l'arriere-plan coevolutif de M ; bovis, M ; caprae ou M ; orygis ; cadrer l'emergence de M ; tuberculosis sensu stricto a partir d'un ancetre de type M ; canettii via la sedentarisation neolithique ; relier des TMRCA MTBC aux transitions agricoles

### esm-atlas-cli

Boîte à outils académique (groupe Guyeux, FEMTO-ST) pour l'évolution des protéines : client Python résilient de l'API Protein Atlas (EvolutionaryScale × BioHub), qui expose les features d'autoencodeur parcimonieux (SAE) d'ESMC et les structures ESMFold2 sur 6,8 milliards de protéines. Recherche par hash de contenu, par similarité de séquence, interprétation des features SAE, métadonnées de cluster et récupération de structures 3D, avec cache disque et repli gracieux quand l'API alpha est dégradée.

Compétences : traduire une séquence protéique en résumé de fonction biologique ; récupérer une structure prédite ; trouver des homologues dans l'espace ESM ; comparer deux séquences (sauvage vs variant) par différence de features SAE

### europe-pmc

Interroge Europe PMC (EMBL-EBI), le depot europeen de litterature biomedicale couvrant les resumes PubMed, le texte integral PMC, les preprints de plus de 32 serveurs (bioRxiv, medRxiv, Research Square), livres, brevets, recommandations et financements. Fournit une API REST pour la recherche, la recuperation du texte integral et des annotations de text mining precalculees (genes, maladies, molecules, organismes, termes GO, numeros d'acces). Pour la litterature TB limitee a PubMed sans preprints, tbmonitor-papers est plus rapide.

Compétences : chercher de la litterature biomedicale y compris des preprints ; recuperer le texte integral d'un article en acces ouvert ; recuperer des annotations en JSON ou XML ; relier des publications a des numeros d'acces de donnees (ENA, UniProt, ChEMBL, PDB) ; decouvrir des articles lies via le graphe de citations

### foldseek

Academic research toolkit for peer-reviewed structural bioinformatics in the Guyeux group (FEMTO-ST). This skill should be used when the user asks to search a protein structure with Foldseek, compare AlphaFold or ESMFold models against PDB, AlphaFold DB or CATH, investigate a structurally conserved dark gene, interpret Foldseek E-values and TM-scores, or cluster predicted protein structures without overclaiming molecular function.

### geo-map

Boite a outils de recherche academique pour les publications de genomique des pathogenes evaluees par les pairs (groupe Guyeux, FEMTO-ST). Cartes geographiques de qualite publication pour les etudes MTBC : projections cartographiques, fonds Natural Earth multi-resolution, echelle, fleche nord, graticule, gabarits de revues. Types : choroplethe, bulles, camemberts, points GPS, arcs phylogeographiques, atlas multi-panneaux, composites multi-couches.

Compétences : cartographier la distribution d'une lignee dans une collection de recherche ; les frequences d'alleles de resistance par pays dans un jeu publie ; les sites d'echantillonnage ; des flux migratoires inferes ; toute figure de carte pour un article, un poster ou une slide

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

Boite a outils de recherche academique pour la recherche phylogeographique evaluee par les pairs. Nextstrain (Augur, Auspice, TreeTime, Nextclade) pour l'analyse phylogeographique et la visualisation interactive de collections de genomes de pathogenes publiees. Augur est la boite a outils Python qui enchaine filtrage, alignement, construction d'arbre, mise a l'echelle temporelle, reconstruction ancestrale et inference de trait discret (geographie) en un pipeline reproductible, produisant du JSON pour le visualiseur Auspice.

Compétences : construire un pipeline phylogeographique reproductible sur un jeu de recherche ; dater un arbre avec TreeTime ; inferer la geographie ancestrale ; produire un arbre interactif accompagnant une publication

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

Boite a outils de recherche academique pour la genomique evolutive evaluee par les pairs. PastML (Institut Pasteur) pour la reconstruction rapide de caracteres ancestraux discrets par maximum de vraisemblance (localisation, hote, allele de resistance aux antimicrobiens, lignee) sur un arbre enracine, avec sortie HTML en arbre compresse ; passe a l'echelle de 10^4 a 10^5 feuilles.

Compétences : inferer l'origine geographique d'une sous-lignee MTBC dans une collection de recherche ; reconstruire des sauts d'hote ancestraux de mycobacteries zoonotiques ; dater l'emergence d'un allele de resistance sur une phylogenie publiee ; projeter un trait discret sur un arbre existant

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

Lit, manipule et ecrit les formats d'alignement genomique (SAM/BAM/CRAM) et de variants (VCF/BCF) depuis Python ; enveloppe de htslib. Note pour le travail bacterien : les references MTBC comme NC_000962.3 sont mono-contig sans prefixe chr, et les coordonnees de fetch()/pileup() sont 0-based semi-ouvertes alors que VCF et SPDI sont 1-based.

Compétences : inspecter la profondeur ou la couverture a une position ; extraire les lectures d'un intervalle ; construire un pileup pour genotyper un site a la main ; filtrer ou fusionner des BAM ; analyser un VCF par programme plutot qu'avec bcftools ; verifier la qualite de mapping derriere un appel de variant

### rdkit

Boîte à outils open source de chémoinformatique et de machine learning pour la découverte de médicaments, la manipulation moléculaire et le calcul de propriétés chimiques. RDKit gère les SMILES, les empreintes moléculaires, la recherche de sous-structures, la génération de conformères 3D, la modélisation de pharmacophores et le QSAR.

Compétences : travailler avec des structures chimiques ; propriétés drug-like, similarité moléculaire, criblage virtuel ou workflows de chimie computationnelle

### read-scientific-pdf

Extraction rapide du texte d'un PDF scientifique (articles, thèses, rapports) via pdftotext, markitdown ou pdfminer, puis relecture du fichier texte intermédiaire avec Read. Pipeline plus efficace que la lecture multimodale native pour les documents longs (>10 pages), les PDF à colonnes multiples, les tableaux complexes et la lecture en lot pour revues de littérature.

Compétences : PDF scientifique long ; article à colonnes ou tableaux complexes ; lecture séquentielle d'un corpus pour une revue ; PDF scanné nécessitant OCR ; quand la lecture native d'un PDF renvoie un résultat partiel ou inattendu

### remote-compute

Deploy long, memory-hungry, disk-hungry or GPU computations onto the two remote machines reachable over SSH: `mp` (standalone 64-thread / 125 GB / 51 TB box, no scheduler) and `mh` (Helios, the Slurm cluster of the Mesocentre de calcul de Franche-Comte: A100 and L40 GPUs, 1 TB bigmem node, BeeGFS). Any discipline, not only bioinformatics: model training, LLM inference, audio transcription, OCR of scanned documents, simulation, optimisation, GIS, MATLAB, large data processing. Covers choosing between the two, Slurm QOS ceilings, sbatch recipes, module and architecture traps, data staging, local scratch, job chaining, and the mesocentre's other services

Compétences : a computation needs more RAM, disk, cores, a GPU or more wall-clock time than the laptop can give, or when asked to run something "sur mp", "sur mh", "sur le cluster", "en GPU", "en batch", "sur Helios", "au mesocentre

### scanpy

Boite a outils passant a l'echelle pour l'expression genique en cellule unique, batie sur AnnData : controle qualite, normalisation, reduction de dimension, clustering, inference de trajectoires et graphiques. Pour des matrices d'expression bulk ou du clustering generique, preferer scikit-learn.

Compétences : travailler sur un .h5ad ou un objet AnnData ; derouler un pipeline scRNA-seq (clustering Leiden/Louvain, UMAP, genes marqueurs, pseudotemps) ; l'utilisateur mentionne scanpy, AnnData, scVI ou la transcriptomique en cellule unique

### sci-figure

Figures d'article aux normes des revues : gabarits Nature, Science, PLOS et Cell (largeur en millimetres, resolution, police, PDF vectoriel), palettes compatibles avec le daltonisme, multi-panneaux GridSpec, export PGF et LaTeX. Partage la table de gabarits avec geo-map pour que figures de donnees et cartes d'un meme article sortent aux memes dimensions.

Compétences : toute figure de manuscrit, de poster ou de slide a partir d'un CSV ou d'un DataFrame

### scientific-problem-selection

À utiliser quand des scientifiques ont besoin d'aide pour choisir un problème de recherche, imaginer un projet, débloquer un projet enlisé ou prendre des décisions scientifiques stratégiques.

Compétences : pitcher une nouvelle idée ; travailler un problème de projet ; évaluer les risques d'un projet ; planifier une stratégie de recherche ; choisir sur quel problème travailler (« j'ai une idée de projet », « je suis bloqué », « aide-moi à évaluer ce projet », « sur quoi travailler »)

### scikit-bio

Bibliothèque de bioinformatique et de statistiques d'écologie des communautés. Fournit structures de données et algorithmes pour séquences, alignements, phylogénétique et analyse de diversité. Essentielle pour la recherche sur le microbiome et la data science écologique : diversité alpha/bêta, ordination (PCoA), arbres phylogénétiques, matrices de distances, PERMANOVA.

Compétences : calculer des métriques de diversité alpha/bêta ; ordination (PCoA) ; manipuler séquences ou matrices de distances ; PERMANOVA et analyse d'écologie des communautés

### scikit-learn

La bibliotheque de reference d'apprentissage automatique en Python : classification, regression, clustering, reduction de dimension, selection de modele et pretraitement. Quand les echantillons sont apparentes (isolats clonaux, ascendance partagee), decouper par groupe et non au hasard : voir senior-data-scientist pour les regles de conception.

Compétences : ajuster ou comparer des modeles predictifs sur des donnees tabulaires ; construire un Pipeline ou un ColumnTransformer ; lancer une validation croisee ou une recherche d'hyperparametres ; calculer des metriques de classification ; reduire la dimension par ACP, t-SNE ou UMAP

### seshat

Interroge Seshat: Global History Databank, base historique quantitative de référence de ~400 entités politiques du Néolithique à ~1900, couvrant complexité sociale, guerre, religion, agriculture et événements de crise/effondrement. Fournit l'échafaudage quantitatif au niveau des polities pour tester comment formation d'État, densité de population, urbanisation et crises ont façonné la persistance et la dispersion des pathogènes adaptés à l'humain.

Compétences : construire un argument quantitatif densité/urbanisation pour la persistance du MTBC adapté à l'humain ; corréler l'émergence d'un pathogène à des crises ou effondrements de polities (CrisisDB) ; cadrer l'essor d'une lignée dans un contexte de formation d'État ; écrire une section cliodynamique sur la coévolution pathogènes et complexité sociale

### slavevoyages

Interroge slavevoyages.org (36k+ voyages, 1514-1866) pour construire des scénarios phylogéographiques d'articles sur les lignées MTBC. Corrèle les distributions de lignées TB aux routes commerciales transatlantiques, aux TMRCA et aux événements migratoires historiques.

Compétences : expliquer la présence dans le Nouveau Monde de lignées TB africaines (L5, L6, L4) ; bâtir une hypothèse de dispersion d'une lignée ; corréler un TMRCA à des mouvements de population historiques (Côte de l'Or → Amériques, golfe du Bénin, etc.)

### statsmodels

Modélisation statistique avancée et tests d'hypothèses. Complémentaire du module stats de SciPy, il fournit des classes et fonctions pour estimer de nombreux modèles statistiques et conduire tests et exploration. Sert à la régression linéaire, aux GLM, aux séries temporelles, à l'ANOVA, à l'analyse de survie, à l'inférence causale et aux tests d'hypothèses.

Compétences : OLS/WLS, régression logistique ou de Poisson ; ARIMA/SARIMAX ; diagnostics statistiques, p-values, intervalles de confiance ; analyse statistique à la R

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
| [lit-review](redac.md#lit-review) | `redac` |
| [reviewer-response](redac.md#reviewer-response) | `redac` |
