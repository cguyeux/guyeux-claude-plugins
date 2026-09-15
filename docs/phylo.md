# Plugin `phylo`

> Academic research toolkit for phylogenetic and phylodynamic inference: tree building (RAxML-NG, IQ-TREE), molecular dating (BEAST2, LSD2), ancestral reconstruction, and iTOL annotation. Guyeux group (FEMTO-ST), peer-reviewed research, transverse to all taxa.

Skills propres (canoniques) : **11** ; skills partagés utilisés (symlinks) : **0**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [ancestral-reconstruction](#ancestral-reconstruction) ; [bayesian-skyline](#bayesian-skyline) ; [beast2-dating](#beast2-dating) ; [beast2-phylogeography](#beast2-phylogeography) ; [iqtree-lsd2](#iqtree-lsd2) ; [itol](#itol) ; [molecular-clock](#molecular-clock) ; [nextstrain](#nextstrain) ; [pastml](#pastml) ; [phylo-forest](#phylo-forest) ; [raxml](#raxml)

### ancestral-reconstruction

Boîte à outils de recherche académique (groupe Guyeux, FEMTO-ST) pour la reconstruction d'états ancestraux sur les phylogénies MTBC en vue de publications phylogéographiques évaluées par des pairs. Reconstruit les états géographiques ancestraux : parcimonie (Fitch), postérieurs marginaux en maximum de vraisemblance (MPPA), cartographie stochastique, génération de XML DTA pour BEAST et export de flèches de migration vers iTOL.

Compétences : identifier quand et combien de fois une lignée a migré entre régions ; comparer les schémas de migration aux mouvements humains ; annoter des phylogénies avec les localisations ancestrales ; préparer des analyses de traits discrets sous BEAST

### bayesian-skyline

Boite a outils de recherche academique pour la recherche phylodynamique evaluee par les pairs. Famille des skylines bayesiens de BEAST (Bayesian Skyline Plot, Skyride, Skygrid, Birth-Death Skyline) pour reconstruire la taille efficace de population Ne(t) ou le nombre de reproduction effectif Re(t) au cours du temps a partir de genomes dates d'une collection d'etude publiee. Inclut une recette sans interface graphique pour emettre les priors skyline en XML et executer BEAST sans affichage.

Compétences : reconstruire le Ne(t) historique d'une lignee MTBC ; tester une expansion contre une transition demographique humaine (Neolithique, age du Bronze, contact colombien) ; estimer un Re(t) sur une periode historique ; produire une figure skyline pour un manuscrit

### beast2-dating

Boite a outils de recherche academique pour la datation moleculaire bayesienne des phylogenies du complexe Mycobacterium tuberculosis (MTBC) avec BEAST2, pour la recherche phylogenomique evaluee par les pairs. Genere un XML BEAST2 correct pour des alignements SNP BINAIRES (presence/absence 0/1), le format produit par le pipeline TB du groupe Guyeux (FEMTO-ST), et execute BEAST2 sans affichage. Corrige les deux defauts qui font echouer silencieusement la convergence des runs BEAST2 sur donnees binaires MTBC.

Compétences : dater un noeud ou une lignee avec BEAST2 ; ecrire ou deboguer un XML BEAST2 ; choisir une horloge ou un prior d'arbre pour le MTBC ; diagnostiquer un ESS qui ne monte pas

### beast2-phylogeography

Emploie BEAST2 et ses paquets de phylogéographie (MASCOT, BASTA, DTA classique) pour la datation moléculaire bayésienne rigoureuse, le tip-dating d'échantillons anciens et l'inférence phylogéographique par coalescent structuré. Cadre bayésien de référence pour la phylogénétique à petite/moyenne échelle où l'on veut les distributions postérieures complètes sur la topologie, les temps de divergence, les taux de migration et les états ancestraux.

Compétences : dater des tips MTBC anciens avec intervalles de crédibilité complets ; lancer une phylogéographie par coalescent structuré (MASCOT/BASTA) ; produire un arbre bayésien calibré dans le temps ; tester des modèles démographiques concurrents ; quand un pipeline maximum de vraisemblance/Nextstrain manque de rigueur pour un relecteur

### iqtree-lsd2

Emploie IQ-TREE 2 et son LSD2 intégré (Least-Squares Dating 2) pour l'inférence phylogénétique en maximum de vraisemblance rapide et la datation moléculaire, alternative pragmatique à BEAST2 quand il faut un arbre daté sur 10³ à 10⁵ tips en minutes ou heures plutôt qu'en jours. IQ-TREE gère la sélection de modèle (ModelFinder), l'ultrafast bootstrap et la recherche d'arbre ; LSD2 convertit les longueurs de branche en temps calendaire via les dates des tips.

Compétences : construire un arbre MTBC en maximum de vraisemblance avec sélection de modèle et bootstrap ; dater l'arbre par tip-dating (LSD2) en alternative rapide à BEAST2 ; passer à l'échelle de milliers de génomes ; générer un arbre de départ pour un raffinement BEAST2 ultérieur

### itol

Téléverse, annote et exporte des figures d'arbres phylogénétiques de qualité publication via iTOL (Interactive Tree Of Life) avec le pipeline itolapi intégré. Transforme un arbre Newick/Nexus plus des pistes d'annotation (plages de couleur de lignées, couleurs de branches, symboles de bootstrap, jeux de données) en SVG/PDF/PNG, avec des presets pour article, supplément, présentation ou poster, plus export par lots et mode comparaison.

Compétences : produire une figure finale d'arbre de lignées MTBC pour un manuscrit ou une slide ; rendre un arbre RAxML/IQ-TREE annoté avec plages de couleur et bootstrap ; exporter le même arbre en plusieurs formats/presets ; scripter les téléversements iTOL plutôt que cliquer dans l'interface web

### molecular-clock

Boite a outils de recherche academique pour la genomique evolutive MTBC evaluee par les pairs (groupe Guyeux, FEMTO-ST). Datation moleculaire des phylogenies du complexe Mycobacterium tuberculosis sous signal temporel faible : regression racine-vers-pointes, analyse TempEst, generation de XML BEAST, calibration multi-contraintes pour les difficultes d'horloge propres au MTBC, et controles par randomisation des dates.

Compétences : estimer des temps de divergence pour des lignees MTBC dans une etude ; evaluer le signal temporel d'une phylogenie publiee ; preparer des analyses BEAST ou BEAST2 ; dater l'emergence d'une sous-lignee ou d'un allele de resistance pour une publication

### nextstrain

Boite a outils de recherche academique pour la recherche phylogeographique evaluee par les pairs. Nextstrain (Augur, Auspice, TreeTime, Nextclade) pour l'analyse phylogeographique et la visualisation interactive de collections de genomes de pathogenes publiees. Augur est la boite a outils Python qui enchaine filtrage, alignement, construction d'arbre, mise a l'echelle temporelle, reconstruction ancestrale et inference de trait discret (geographie) en un pipeline reproductible, produisant du JSON pour le visualiseur Auspice.

Compétences : construire un pipeline phylogeographique reproductible sur un jeu de recherche ; dater un arbre avec TreeTime ; inferer la geographie ancestrale ; produire un arbre interactif accompagnant une publication

### pastml

Boite a outils de recherche academique pour la genomique evolutive evaluee par les pairs. PastML (Institut Pasteur) pour la reconstruction rapide de caracteres ancestraux discrets par maximum de vraisemblance (localisation, hote, allele de resistance aux antimicrobiens, lignee) sur un arbre enracine, avec sortie HTML en arbre compresse ; passe a l'echelle de 10^4 a 10^5 feuilles.

Compétences : inferer l'origine geographique d'une sous-lignee MTBC dans une collection de recherche ; reconstruire des sauts d'hote ancestraux de mycobacteries zoonotiques ; dater l'emergence d'un allele de resistance sur une phylogenie publiee ; projeter un trait discret sur un arbre existant

### phylo-forest

Bibliothèque interrogeable des arbres phylogénétiques déjà calculés dans un dépôt de recherche : moissonne les Newick existants, en extrait une fiche (outil, modèle, alignement, taxons, composition par clade avec son système taxonomique), et répond à « ai-je déjà un arbre qui ferait l'affaire ? » AVANT de relancer un calcul. Rend aussi des FORÊTS pour les statistiques inter-arbres qu'un arbre isolé ne permet pas (fréquence d'un clade à travers des reconstructions indépendantes)

Compétences : avant tout RAxML / IQ-TREE / FastTree, pour chercher un arbre existant ; après un calcul, pour le verser à la forêt ; pour retrouver l'arbre d'une figure ; pour mesurer la stabilité d'un clade entre études

### raxml

Boîte à outils académique (groupe Guyeux, FEMTO-ST) pour l'inférence phylogénomique (RAxML-NG) en vue de publications. Soumet et gère des jobs RAxML-NG via le MCP TBannotator. Gère le mode matrice directe, le mode clustering et le placement contextuel.

Compétences : construire des phylogénies MTBC ; placer de nouvelles souches sur des arbres de référence ; produire des Newick pour annotation iTOL ; lancer RAxML-NG pour un article
