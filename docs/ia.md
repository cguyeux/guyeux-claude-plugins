# Plugin `ia`

> Un plugin faire de l'IA

## Rôle dans un projet M. tuberculosis

Machine learning et data science au service des analyses MTBC : classification de lignées, prédiction de phénotypes de résistance à partir de génotypes, réduction de dimension sur des matrices de SNP, explication des modèles obtenus.

Skills propres (canoniques) : **14** ; skills partagés utilisés (symlinks) : **3**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [causal-inference](#causal-inference) ; [geopandas](#geopandas) ; [ml-model-explainer](#ml-model-explainer) ; [networkx](#networkx) ; [numpy](#numpy) ; [numpy-low-level](#numpy-low-level) ; [pandas-performance](#pandas-performance) ; [scipy](#scipy) ; [senior-data-scientist](#senior-data-scientist) ; [shapely](#shapely) ; [sklearn-advanced](#sklearn-advanced) ; [sklearn-explainability](#sklearn-explainability) ; [statistical-analysis](#statistical-analysis) ; [xgboost-iterative-optimizer](#xgboost-iterative-optimizer)

### causal-inference

Inférence causale et raisonnement contrefactuel pour le machine learning. Sert à estimer les effets de traitement moyens/conditionnels/individuels (ATE/CATE/ITE), tester les hypothèses causales derrière un modèle prédictif, identifier les facteurs de confusion via des DAG, et valider par tests de réfutation et analyses de sensibilité.

Compétences : l'utilisateur mentionne DoWhy, EconML, CausalML, le do-calcul, les variables instrumentales, l'appariement par score de propension, le double machine learning, les forêts causales, l'hétérogénéité des effets, la découverte causale (PC, FCI, GES, LiNGAM, NOTEARS), ou veut passer de « X est corrélé à Y » à « X cause Y 

### geopandas

Projet open source facilitant le travail sur données géospatiales en Python. Étend les types de pandas pour autoriser des opérations spatiales sur des géométries, en s'appuyant sur Shapely, Fiona et Pyproj. Sert à lire/écrire des formats spatiaux (Shapefile, GeoJSON, GeoPackage, KML), aux jointures spatiales, aux reprojections, à l'analyse géométrique et à la cartographie thématique.

Compétences : manipuler des données vectorielles géographiques en Python ; jointures spatiales, reprojections, cartes choroplèthes ; travailler avec des données OpenStreetMap ou dérivées de satellite

### ml-model-explainer

Explique les predictions d'un modele ajuste par valeurs SHAP, importance par permutation et importance native, plus les chemins de decision par instance, avec graphiques. Pour l'API d'inspection scikit-learn sous-jacente et les compromis LIME/SHAP, voir sklearn-explainability.

Compétences : comprendre pourquoi un modele a predit un resultat donne ; savoir quelles variables le pilotent ; produire un graphique SHAP resume ou en cascade pour une figure d'article ; auditer un modele avant de se fier a son classement

### networkx

Paquet Python pour la création, la manipulation et l'étude de la structure, de la dynamique et des fonctions des réseaux complexes. Gère divers types de graphes (orientés, non orientés, multigraphes) et offre une vaste bibliothèque d'algorithmes standard.

Compétences : analyse de réseaux et théorie des graphes ; réseaux sociaux ou biologiques ; recherche de chemins, mesures de centralité, détection de communautés, plus courts chemins, PageRank, analyse de connectivité

### numpy

Guide complet de NumPy, paquet fondamental du calcul scientifique en Python. Sert aux opérations sur tableaux, à l'algèbre linéaire, à la génération de nombres aléatoires, aux transformées de Fourier, aux fonctions mathématiques et au calcul numérique performant. Fondation de SciPy, pandas et scikit-learn.

Compétences : manipuler des tableaux numériques ; algèbre linéaire, aléatoire, transformées de Fourier ; calcul numérique performant

### numpy-low-level

Sous-skill NumPy avance : disposition memoire, strides, vues contre copies, tableaux structures et d'enregistrements, protocole tampon, et interfacage avec C/Cython.

Compétences : une operation sur tableau est anormalement lente ou gourmande en memoire ; une mutation se propage a travers une vue ; construire des fenetres glissantes ou des statistiques roulantes sans copier ; lire une disposition binaire dans un dtype structure ; l'utilisateur mentionne strides, as_strided, sliding_window_view, ascontiguousarray, zero-copy ou vectorisation SIMD

### pandas-performance

Sous-skill pandas avance pour l'empreinte memoire et la vitesse d'execution sur de grandes tables (10M+ lignes) : reduction de dtypes, categorielles, indexation efficace, vectorisation de la logique ligne a ligne, lectures par morceaux et hors memoire, et backend PyArrow.

Compétences : une operation DataFrame est trop lente ou epuise la memoire ; remplacer apply ou iterrows par des operations vectorisees ; un groupby ou un merge explose ; charger un fichier trop gros pour la RAM

### scipy

Guide complet de SciPy, bibliothèque fondamentale du calcul scientifique et technique en Python. Sert à l'intégration, l'optimisation, l'interpolation, l'algèbre linéaire, le traitement du signal, les statistiques, les EDO, les transformées de Fourier et les algorithmes scientifiques avancés. Bâtie sur NumPy.

Compétences : optimisation, interpolation, intégration ; traitement du signal ; statistiques ; algorithmes scientifiques avancés

### senior-data-scientist

Boite a outils de recherche academique pour concevoir une analyse statistiquement defendable sur des donnees genomiques et de population avant de la lancer, et pour aiguiller vers le skill specialise adapte. Formalise les quatre modes d'echec qui invalident le plus souvent une conclusion dans ce domaine : non-independance due a l'ascendance partagee, tests multiples a l'echelle du genome, biais de constatation dans les archives publiques, et fuite par apparentement dans un modele predictif. N'execute ni ajustement ni graphique : delegue a statsmodels, scikit-learn, statistical-analysis, causal-inference, mk-ascertainment ou sci-figure.

Compétences : savoir comment monter une analyse plutot que la lancer ; quel test ou estimateur convient a la question ; si un resultat survit a la non-independance phylogenetique ; comment corriger pour les tests multiples sur des milliers de sites ou de genes ; comment decouper les donnees en validation croisee quand les isolats sont clonaux ; si un resultat de frequence allelique est un artefact d'echantillonnage ; ce qu'un relecteur attaquera dans les statistiques d'un manuscrit

### shapely

Manipulation et analyse d'objets géométriques planaires, basée sur la bibliothèque GEOS. Fournit points, courbes et surfaces, et des algorithmes standardisés d'opérations géométriques. Sert aux opérations de géométrie 2D, relations spatiales, opérations ensemblistes (intersection, union, différence), tests point-dans-polygone, calculs géométriques (aire, distance, centroïde), buffering et nettoyage de géométries invalides.

Compétences : opérations de géométrie 2D et relations spatiales ; intersection/union/différence ; point-dans-polygone ; calculs d'aire/distance/centroïde ; buffering et nettoyage de géométries pour SIG

### sklearn-advanced

Sous-skill scikit-learn professionnel : architecture robuste de Pipeline et ColumnTransformer, estimateurs et transformateurs personnalises respectant le contrat fit/transform, encodage de cible et de categories rares, et validation rigoureuse dont la validation croisee imbriquee.

Compétences : il y a un risque de fuite de donnees ; une etape de pretraitement doit etre ajustee a l'interieur de la validation croisee ; regler et evaluer dans la meme procedure ; ecrire un estimateur reutilisable ; un score de validation semble trop beau pour etre vrai

### sklearn-explainability

Sous-skill scikit-learn d'interpretation d'un modele ajuste : importance par permutation, courbes de dependance partielle et ICE, lecture des coefficients sous colinearite, integration SHAP et LIME. Pour un chemin SHAP rapide sur des modeles a arbres, utiliser TreeExplainer plutot que l'explicateur agnostique.

Compétences : savoir quelles variables comptent et pourquoi ; defendre un classement d'importance dans un article ; les importances natives par impurete semblent suspectes sur des variables a forte cardinalite ; produire une figure d'interpretabilite

### statistical-analysis

Applique des méthodes statistiques : statistiques descriptives, analyse de tendance, détection d'aberrants et tests d'hypothèses.

Compétences : analyser des distributions ; tester la significativité ; détecter des anomalies ; calculer des corrélations ; interpréter des résultats statistiques

### xgboost-iterative-optimizer

Optimisation itérative de modèles XGBoost selon un workflow de chercheur en ML scientifique. Diagnostique les erreurs de prédiction par inspection visuelle des courbes prédit-vs-observé (primaire), renforcée par SHAP, analyse des résidus et métriques. Améliore les modèles par feature engineering, réglage d'hyperparamètres, choix de fonction objectif et stratégies d'ensemble.

Compétences : prédictions XGBoost médiocres ; MAE/RMSE à réduire ; résidus montrant des motifs ; sous/sur-apprentissage ;  prédictions trop plates/biaisées 

## Skills partagés (via symlink)

Documentés sur la page de leur plugin d'origine.

| Skill | Origine |
|-------|---------|
| [scientific-problem-selection](bio_population_genetics.md#scientific-problem-selection) | `bio_population_genetics` |
| [scikit-learn](bio_population_genetics.md#scikit-learn) | `bio_population_genetics` |
| [statsmodels](bio_population_genetics.md#statsmodels) | `bio_population_genetics` |

