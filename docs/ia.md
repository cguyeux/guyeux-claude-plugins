# Plugin `ia`

> Un plugin faire de l'IA

## Rôle dans un projet M. tuberculosis

Machine learning et data science au service des analyses MTBC : classification de lignées, prédiction de phénotypes de résistance à partir de génotypes, réduction de dimension sur des matrices de SNP, explication des modèles obtenus.

Skills propres (canoniques) : **20** ; skills partagés utilisés (symlinks) : **1**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [causal-inference](#causal-inference) ; [data-visualization](#data-visualization) ; [geopandas](#geopandas) ; [matplotlib](#matplotlib) ; [matplotlib-pro](#matplotlib-pro) ; [ml-model-explainer](#ml-model-explainer) ; [networkx](#networkx) ; [numpy](#numpy) ; [numpy-low-level](#numpy-low-level) ; [pandas-performance](#pandas-performance) ; [scientific-problem-selection](#scientific-problem-selection) ; [scikit-learn](#scikit-learn) ; [scipy](#scipy) ; [senior-data-scientist](#senior-data-scientist) ; [shapely](#shapely) ; [sklearn-advanced](#sklearn-advanced) ; [sklearn-explainability](#sklearn-explainability) ; [statistical-analysis](#statistical-analysis) ; [statsmodels](#statsmodels) ; [xgboost-iterative-optimizer](#xgboost-iterative-optimizer)

### causal-inference

Inférence causale et raisonnement contrefactuel pour le machine learning. Sert à estimer les effets de traitement moyens/conditionnels/individuels (ATE/CATE/ITE), tester les hypothèses causales derrière un modèle prédictif, identifier les facteurs de confusion via des DAG, et valider par tests de réfutation et analyses de sensibilité.

Compétences : l'utilisateur mentionne DoWhy, EconML, CausalML, le do-calcul, les variables instrumentales, l'appariement par score de propension, le double machine learning, les forêts causales, l'hétérogénéité des effets, la découverte causale (PC, FCI, GES, LiNGAM, NOTEARS), ou veut passer de « X est corrélé à Y » à « X cause Y 

### data-visualization

Crée des visualisations de données efficaces avec Python (matplotlib, seaborn, plotly).

Compétences : construire des graphiques ; choisir le bon type de graphique pour un jeu de données ; produire des figures de qualité publication ; appliquer des principes de design (accessibilité, théorie des couleurs)

### geopandas

Projet open source facilitant le travail sur données géospatiales en Python. Étend les types de pandas pour autoriser des opérations spatiales sur des géométries, en s'appuyant sur Shapely, Fiona et Pyproj. Sert à lire/écrire des formats spatiaux (Shapefile, GeoJSON, GeoPackage, KML), aux jointures spatiales, aux reprojections, à l'analyse géométrique et à la cartographie thématique.

Compétences : manipuler des données vectorielles géographiques en Python ; jointures spatiales, reprojections, cartes choroplèthes ; travailler avec des données OpenStreetMap ou dérivées de satellite

### matplotlib

Bibliothèque fondamentale pour les visualisations statiques, animées et interactives en Python. Hautement personnalisable, standard de l'industrie pour les figures de qualité publication. Sert au tracé 2D, à la visualisation scientifique, aux cartes de chaleur, contours, champs de vecteurs, figures multi-panneaux, tracés au format LaTeX et depuis des tableaux NumPy ou DataFrames pandas.

Compétences : produire des figures scientifiques précises et personnalisées ; tracer depuis NumPy/pandas ; construire des figures multi-panneaux de qualité publication

### matplotlib-pro

Sous-skill professionnel de Matplotlib axé sur les animations performantes, les mises en page multi-figures complexes (GridSpec), les widgets interactifs et la typographie prête à publier (LaTeX/PGF).

Compétences : réaliser des animations performantes ; composer des mises en page multi-figures complexes ; soigner la typographie d'une figure publiée

### ml-model-explainer

Explique les prédictions d'un modèle de ML via les valeurs SHAP, l'importance des features et les chemins de décision, avec visualisations.

Compétences : interpréter les prédictions d'un modèle ; identifier les features déterminantes ; visualiser des chemins de décision

### networkx

Paquet Python pour la création, la manipulation et l'étude de la structure, de la dynamique et des fonctions des réseaux complexes. Gère divers types de graphes (orientés, non orientés, multigraphes) et offre une vaste bibliothèque d'algorithmes standard.

Compétences : analyse de réseaux et théorie des graphes ; réseaux sociaux ou biologiques ; recherche de chemins, mesures de centralité, détection de communautés, plus courts chemins, PageRank, analyse de connectivité

### numpy

Guide complet de NumPy, paquet fondamental du calcul scientifique en Python. Sert aux opérations sur tableaux, à l'algèbre linéaire, à la génération de nombres aléatoires, aux transformées de Fourier, aux fonctions mathématiques et au calcul numérique performant. Fondation de SciPy, pandas et scikit-learn.

Compétences : manipuler des tableaux numériques ; algèbre linéaire, aléatoire, transformées de Fourier ; calcul numérique performant

### numpy-low-level

Sous-skill avancé de NumPy axé sur la gestion mémoire interne, la manipulation des strides, les tableaux structurés et l'interfaçage avec C/Cython. Couvre les opérations zéro-copie et les principes de vectorisation SIMD.

Compétences : optimiser la mémoire ou la vitesse d'un code NumPy ; opérations zéro-copie ; interfaçage C/Cython ; tableaux structurés

### pandas-performance

Sous-skill avancé de pandas axé sur l'optimisation mémoire, la vitesse d'exécution et le traitement de jeux à grande échelle (10 M+ lignes). Couvre les dtypes bas niveau, l'indexation efficace et la vectorisation de logiques complexes.

Compétences : optimiser la mémoire ou la vitesse d'un traitement pandas ; gérer de très gros DataFrames ; vectoriser une logique complexe

### scientific-problem-selection

À utiliser quand des scientifiques ont besoin d'aide pour choisir un problème de recherche, imaginer un projet, débloquer un projet enlisé ou prendre des décisions scientifiques stratégiques.

Compétences : pitcher une nouvelle idée ; travailler un problème de projet ; évaluer les risques d'un projet ; planifier une stratégie de recherche ; choisir sur quel problème travailler (« j'ai une idée de projet », « je suis bloqué », « aide-moi à évaluer ce projet », « sur quoi travailler »)

### scikit-learn

Bibliothèque standard de l'industrie pour le machine learning en Python. Offre des outils simples et efficaces d'analyse prédictive : classification, régression, clustering, réduction de dimension, sélection de modèle et prétraitement.

Compétences : entraîner un modèle de classification ou de régression ; clustering ou réduction de dimension ; sélection de modèle et prétraitement de features

### scipy

Guide complet de SciPy, bibliothèque fondamentale du calcul scientifique et technique en Python. Sert à l'intégration, l'optimisation, l'interpolation, l'algèbre linéaire, le traitement du signal, les statistiques, les EDO, les transformées de Fourier et les algorithmes scientifiques avancés. Bâtie sur NumPy.

Compétences : optimisation, interpolation, intégration ; traitement du signal ; statistiques ; algorithmes scientifiques avancés

### senior-data-scientist

Skill de data science de haut niveau pour la modélisation statistique, l'expérimentation, l'inférence causale et l'analytique avancée. Expertise Python (NumPy, Pandas, Scikit-learn), R, SQL, méthodes statistiques, tests A/B, séries temporelles, avec conception d'expériences, feature engineering, évaluation de modèles et communication aux parties prenantes.

Compétences : concevoir des expériences ; construire des modèles prédictifs ; réaliser une analyse causale ; piloter des décisions fondées sur les données

### shapely

Manipulation et analyse d'objets géométriques planaires, basée sur la bibliothèque GEOS. Fournit points, courbes et surfaces, et des algorithmes standardisés d'opérations géométriques. Sert aux opérations de géométrie 2D, relations spatiales, opérations ensemblistes (intersection, union, différence), tests point-dans-polygone, calculs géométriques (aire, distance, centroïde), buffering et nettoyage de géométries invalides.

Compétences : opérations de géométrie 2D et relations spatiales ; intersection/union/différence ; point-dans-polygone ; calculs d'aire/distance/centroïde ; buffering et nettoyage de géométries pour SIG

### sklearn-advanced

Sous-skill professionnel de scikit-learn axé sur l'architecture robuste de pipelines, le développement d'estimateurs personnalisés, le feature engineering avancé et la validation rigoureuse de modèles. Couvre le Target Encoding, la validation croisée imbriquée et le déploiement en production.

Compétences : construire des pipelines robustes ; développer un estimateur personnalisé ; feature engineering avancé ; validation croisée imbriquée et déploiement

### sklearn-explainability

Sous-skill avancé de scikit-learn axé sur l'interprétabilité des modèles, l'importance des features et les outils de diagnostic. Couvre les explications globales et locales via les outils d'inspection intégrés et les intégrations SHAP/LIME.

Compétences : interpréter un modèle scikit-learn ; explications globales et locales ; importance des features ; intégrer SHAP ou LIME

### statistical-analysis

Applique des méthodes statistiques : statistiques descriptives, analyse de tendance, détection d'aberrants et tests d'hypothèses.

Compétences : analyser des distributions ; tester la significativité ; détecter des anomalies ; calculer des corrélations ; interpréter des résultats statistiques

### statsmodels

Modélisation statistique avancée et tests d'hypothèses. Complémentaire du module stats de SciPy, il fournit des classes et fonctions pour estimer de nombreux modèles statistiques et conduire tests et exploration. Sert à la régression linéaire, aux GLM, aux séries temporelles, à l'ANOVA, à l'analyse de survie, à l'inférence causale et aux tests d'hypothèses.

Compétences : OLS/WLS, régression logistique ou de Poisson ; ARIMA/SARIMAX ; diagnostics statistiques, p-values, intervalles de confiance ; analyse statistique à la R

### xgboost-iterative-optimizer

Optimisation itérative de modèles XGBoost selon un workflow de chercheur en ML scientifique. Diagnostique les erreurs de prédiction par inspection visuelle des courbes prédit-vs-observé (primaire), renforcée par SHAP, analyse des résidus et métriques. Améliore les modèles par feature engineering, réglage d'hyperparamètres, choix de fonction objectif et stratégies d'ensemble.

Compétences : prédictions XGBoost médiocres ; MAE/RMSE à réduire ; résidus montrant des motifs ; sous/sur-apprentissage ;  prédictions trop plates/biaisées 

## Skills partagés (via symlink)

Documentés sur la page de leur plugin d'origine.

| Skill | Origine |
|-------|---------|
| [create-viz](ops.md#create-viz) | `ops` |

