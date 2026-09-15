# Plugin `science-commun`

> Transverse scientific toolkit used across every research domain of the Guyeux group (FEMTO-ST): figures and maps for publication, PDF extraction, remote compute, problem selection, statistical analysis.

Skills propres (canoniques) : **7** ; skills partagés utilisés (symlinks) : **0**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [create-viz](#create-viz) ; [geo-map](#geo-map) ; [read-scientific-pdf](#read-scientific-pdf) ; [remote-compute](#remote-compute) ; [sci-figure](#sci-figure) ; [scientific-problem-selection](#scientific-problem-selection) ; [statistical-analysis](#statistical-analysis)

### create-viz

Crée des visualisations de qualité publication avec Python.

Compétences : transformer un résultat de requête ou un DataFrame en graphique ; choisir le bon type de graphique pour une tendance ou une comparaison ; produire une figure pour un rapport ou une présentation ; obtenir un graphique interactif avec survol et zoom

### geo-map

Boite a outils de recherche academique pour les publications de genomique des pathogenes evaluees par les pairs (groupe Guyeux, FEMTO-ST). Cartes geographiques de qualite publication pour les etudes MTBC : projections cartographiques, fonds Natural Earth multi-resolution, echelle, fleche nord, graticule, gabarits de revues. Types : choroplethe, bulles, camemberts, points GPS, arcs phylogeographiques, atlas multi-panneaux, composites multi-couches.

Compétences : cartographier la distribution d'une lignee dans une collection de recherche ; les frequences d'alleles de resistance par pays dans un jeu publie ; les sites d'echantillonnage ; des flux migratoires inferes ; toute figure de carte pour un article, un poster ou une slide

### read-scientific-pdf

Extraction rapide du texte d'un PDF scientifique (articles, thèses, rapports) via pdftotext, markitdown ou pdfminer, puis relecture du fichier texte intermédiaire avec Read. Pipeline plus efficace que la lecture multimodale native pour les documents longs (>10 pages), les PDF à colonnes multiples, les tableaux complexes et la lecture en lot pour revues de littérature.

Compétences : PDF scientifique long ; article à colonnes ou tableaux complexes ; lecture séquentielle d'un corpus pour une revue ; PDF scanné nécessitant OCR ; quand la lecture native d'un PDF renvoie un résultat partiel ou inattendu

### remote-compute

Deploy long, memory-hungry, disk-hungry or GPU computations onto the two remote machines reachable over SSH: `mp` (standalone 64-thread / 125 GB / 51 TB box, no scheduler) and `mh` (Helios, the Slurm cluster of the Mesocentre de calcul de Franche-Comte: A100 and L40 GPUs, 1 TB bigmem node, BeeGFS). Any discipline, not only bioinformatics: model training, LLM inference, audio transcription, OCR of scanned documents, simulation, optimisation, GIS, MATLAB, large data processing. Covers choosing between the two, Slurm QOS ceilings, sbatch recipes, module and architecture traps, data staging, local scratch, job chaining, and the mesocentre's other services

Compétences : a computation needs more RAM, disk, cores, a GPU or more wall-clock time than the laptop can give, or when asked to run something "sur mp", "sur mh", "sur le cluster", "en GPU", "en batch", "sur Helios", "au mesocentre

### sci-figure

Figures d'article aux normes des revues : gabarits Nature, Science, PLOS et Cell (largeur en millimetres, resolution, police, PDF vectoriel), palettes compatibles avec le daltonisme, multi-panneaux GridSpec, export PGF et LaTeX. Partage la table de gabarits avec geo-map pour que figures de donnees et cartes d'un meme article sortent aux memes dimensions.

Compétences : toute figure de manuscrit, de poster ou de slide a partir d'un CSV ou d'un DataFrame

### scientific-problem-selection

À utiliser quand des scientifiques ont besoin d'aide pour choisir un problème de recherche, imaginer un projet, débloquer un projet enlisé ou prendre des décisions scientifiques stratégiques.

Compétences : pitcher une nouvelle idée ; travailler un problème de projet ; évaluer les risques d'un projet ; planifier une stratégie de recherche ; choisir sur quel problème travailler (« j'ai une idée de projet », « je suis bloqué », « aide-moi à évaluer ce projet », « sur quoi travailler »)

### statistical-analysis

Applique des méthodes statistiques : statistiques descriptives, analyse de tendance, détection d'aberrants et tests d'hypothèses.

Compétences : analyser des distributions ; tester la significativité ; détecter des anomalies ; calculer des corrélations ; interpréter des résultats statistiques
