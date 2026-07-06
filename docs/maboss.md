# Plugin `maboss`

> Academic toolkit for MaBoSS (Markovian Boolean Stochastic Simulator) and the CoLoMoTo ecosystem: authoring and validating .bnd/.cfg Boolean models, driving the pyMaBoSS Python API (simulation, mutations, probability trajectories, the temporal-logic / CCT assertion evaluator of Oscar Dufossez, MaBoSS server, Jupyter widgets), and navigating the ecosystem (WebMaBoSS by Vincent Noel, model repositories BioModels/CellCollective, PhysiBoSS, positioning vs INDRA). Ground truth captured from the official refcard and repository trees (July 2026). Used by the Guyeux group (FEMTO-ST, University Marie et Louis Pasteur) for cancer signalling modelling and the mabossDemo literature-coherency project.

## Positionnement

Projet distinct. maboss / CoLoMoTo n'appartient pas au programme M. tuberculosis : il concerne la modélisation booléenne stochastique de réseaux de signalisation (signalisation cancéreuse, projet mabossDemo). Il est documenté ici uniquement parce qu'il partage le même dépôt de plugins, et reste hors du pipeline de recherche M. tuberculosis.

Skills propres (canoniques) : **3** ; skills partagés utilisés (symlinks) : **0**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [maboss-ecosystem](#maboss-ecosystem) ; [maboss-model](#maboss-model) ; [pymaboss](#pymaboss)

### maboss-ecosystem

Carte de l'écosystème MaBoSS/CoLoMoTo et positionnement d'un nouvel outil : le moteur C++ MaBoSS (Gillespie, ≤64 nœuds), les bindings pyMaBoSS, l'évaluateur d'assertions en logique temporelle CCT (Oscar Dufossez), WebMaBoSS (interface web, Vincent Noël 2021), PopMaBoSS/UPMaBoSS/PhysiBoSS, les dépôts de modèles (BioModels, Cell Collective, GINsim) et les tutoriels de référence. Positionne un outil de cohérence littérature-modèle face à INDRA.

Compétences : décider entre construire et réutiliser (bibliothèque de modèles, évaluateur, vérificateur de cohérence existants) ; positionner la nouveauté d'un projet ; citer le bon article/auteur ; choisir la provenance des modèles ; identifier qui contacter ; Complément de pymaboss (API) et maboss-model (format de fichier)

### maboss-model

Rédige, lit et valide les fichiers de modèles booléens MaBoSS : le couple .bnd (logique des nœuds + taux de transition) et .cfg (états initiaux, variables externes, paramètres). Encode la grammaire officielle de la Reference Card (moteur 2.6.6) : syntaxe des nœuds, préfixes @ et $, opérateurs, sémantique rate_up/rate_down/logic, clés .cfg, la CLI et les sorties (_probtraj.csv, _fp.csv, _statdist.csv).

Compétences : écrire ou corriger un .bnd/.cfg ; expliquer l'idiome logique/taux d'un nœud ; choisir des priors d'état initial ; décider des nœuds internes/observés ; déboguer un modèle qui ne simule pas ; Se combine avec pymaboss (exécution) et maboss-ecosystem (provenance)

### pymaboss

Pilote l'API Python réelle pyMaBoSS (colomoto/pyMaBoSS, bindings sur le moteur C++ MaBoSS). Couvre le chargement (load/loadBNet/loadSBML), l'objet Simulation (.run, .mutate, .copy, update_parameters), l'extraction des résultats (probtraj des nœuds/états), l'interopérabilité, le client serveur MaBoSS, UPMaBoSS, PopMaBoSS, les widgets Jupyter, et surtout l'évaluateur d'assertions en logique temporelle CCT (MaBoSSEvaluator.querying) écrit par Oscar Dufossez.

Compétences : exécuter un modèle MaBoSS depuis Python ; appliquer un knock-out/surexpression ; lire P(nœud) au dernier pas de temps ; vérifier une affirmation directionnelle de la littérature (« inhiber X diminue-t-il Y ? ») via MaBoSSEvaluator ; câbler un runner pyMaBoSS réel ; Se combine avec maboss-model (écriture) et maboss-ecosystem (contexte)

