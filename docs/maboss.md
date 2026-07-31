# Plugin `maboss`

> Academic toolkit for MaBoSS (Markovian Boolean Stochastic Simulator) and the CoLoMoTo ecosystem: authoring and validating .bnd/.cfg Boolean models, driving the pyMaBoSS Python API (simulation, mutations, probability trajectories, the temporal-logic / CCT assertion evaluator of Oscar Dufossez, MaBoSS server, Jupyter widgets), and navigating the ecosystem (WebMaBoSS by Vincent Noel, model repositories BioModels/CellCollective, PhysiBoSS, positioning vs INDRA). Ground truth captured from the official refcard and repository trees (July 2026). Used by the Guyeux group (FEMTO-ST, University Marie et Louis Pasteur) for cancer signalling modelling and the mabossDemo literature-coherency project.

## Positionnement

Projet distinct. maboss / CoLoMoTo n'appartient pas au programme M. tuberculosis : il concerne la modélisation booléenne stochastique de réseaux de signalisation (signalisation cancéreuse, projet mabossDemo). Il est documenté ici uniquement parce qu'il partage le même dépôt de plugins, et reste hors du pipeline de recherche M. tuberculosis.

Skills propres (canoniques) : **12** ; skills partagés utilisés (symlinks) : **0**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [astrologics](#astrologics) ; [biolqm-convert](#biolqm-convert) ; [bn-control](#bn-control) ; [boolean-attractors](#boolean-attractors) ; [colomoto-run](#colomoto-run) ; [maboss-advanced](#maboss-advanced) ; [maboss-ecosystem](#maboss-ecosystem) ; [maboss-model](#maboss-model) ; [model-inference](#model-inference) ; [model-repositories](#model-repositories) ; [pydruglogics](#pydruglogics) ; [pymaboss](#pymaboss)

### astrologics

Analyse des ENSEMBLES de modeles booleens avec AstroLogics (sysbio-curie, le meme groupe que pyMaBoSS et WebMaBoSS) : compare de nombreux modeles booleens monotones candidats, etudie la variabilite de leurs dynamiques et de leurs attracteurs, et raisonne sur une famille de modeles plutot que sur un seul. Point de collaboration naturel avec le groupe Noel/Dufossez.

Compétences : l'inference de modeles (BoNesis, Caspo) produit de NOMBREUX modeles compatibles avec les donnees et il faut caracteriser l'ensemble ; quantifier l'incertitude entre modeles ; retenir les predictions robustes ; declencheurs : ensemble de modeles, variabilite entre modeles, AstroLogics, quelles predictions valent pour tous les modeles

### biolqm-convert

Convertit de facon robuste des modeles logiques ou booleens entre formats avec bioLQM (la boite a outils de modelisation qualitative logique de CoLoMoTo) : SBML-qual, MaBoSS .bnd/.cfg, BoolNet .bnet, GINML et .zginml, plus reduction de modele, booleanisation et determinisation. Sert notamment a REGENERER un modele MaBoSS complet depuis un .zginml GINsim ou un export SBML-qual, en particulier pour REPARER un .bnd degenere (export ou la plupart des noeuds sortent en rate_up = 0 sans logic, donc figes a OFF et le modele n'a plus de dynamique).

Compétences : convertir un zginml vers MaBoSS ; un .bnd degenere ou fige ; la plupart des noeuds n'ont pas de logique ; passer de SBML-qual a .bnd ; reexporter le modele GINsim ; le modele n'a pas de dynamique

### bn-control

Trouve les interventions (mutations, fixations de noeuds) qui REPROGRAMMENT un reseau booleen vers un attracteur ou un phenotype vise, ou l'en eloignent, ou PROUVE qu'il n'en existe aucune. Les outils de base AEON.py (controle formel) et mpbn (accessibilite) sont deja dans l'image maboss-mcp ; Pint, CABEAN et pyStableMotifs sont des alternatives qui exigent l'image CoLoMoTo.

Compétences : quelles perturbations induisent ou bloquent l'EMT ; amener le modele vers l'etat apoptotique ; interventions minimales pour atteindre un phenotype ; l'etat X est-il seulement accessible ; controle permanent contre temporaire ; controle par cible

### boolean-attractors

Calcule et nomme les ATTRACTEURS (etats stables, phenotypes) d'un modele booleen avec mpbn (Most Permissive), PyBoolNet ou pyStableMotifs, en partant d'un couple MaBoSS .bnd/.cfg via maboss.to_minibn. Identifie les etats discrets dans lesquels un modele peut se stabiliser (epithelial, hybride, mesenchymateux ; proliferatif, apoptotique), la ou une simple execution MaBoSS ne rapporte que des probabilites par noeud et non des attracteurs nommes. Couvre aussi les points fixes et les trap spaces.

Compétences : trouver les attracteurs ; les etats epithelial et mesenchymateux ; etats stables ou points fixes ; phenotypes du modele ; trap spaces ; quels etats stationnaires ; mpbn ; attracteurs PyBoolNet

### colomoto-run

Execute le CoLoMoTo Interactive Notebook (image Docker colomoto/colomoto-docker) qui reunit environ 27 outils de reseaux booleens et logiques (MaBoSS, GINsim, bioLQM, PyBoolNet, mpbn, Pint, CABEAN, pyStableMotifs, CaSQ, NuSMV, BoNesis, Caspo, scBoolSeq, PyDrugLogics, NORDic, AEON.py, BooleanNet, boolSim, BNS, minibn, ERODE, CellCollective) dans un environnement Jupyter reproductible.

Compétences : une tache exige un outil CoLoMoTo non installable par pip dans une image legere (dependances Java, OCaml ou conda : bioLQM, GINsim, Pint, CABEAN) ; reproduire une analyse de modelisation qualitative publiee ; ouvrir un modele .zginml, SBML-qual ou .bnd dans une chaine d'outils complete

### maboss-advanced

Va au-dela d'une simple execution MaBoSS : dynamique au niveau de la population avec UPMaBoSS (UpdatePopulation) et PopMaBoSS, ensembles de modeles, balayages de mutants et de parametres, sensibilite aux taux et aux etats initiaux, et evaluateur d'assertions CCT/MCCT (maboss.temporal_logic.MaBoSSEvaluator).

Compétences : une comparaison simple entre reference et perturbation ne suffit pas ; proportions de destins cellulaires au cours du temps ; criblages systematiques de mutants simples ou doubles ; verifier par programme des affirmations directionnelles de la litterature (augmentation ou diminution) ; UPMaBoSS, PopMaBoSS, verdict CCT ou MCCT

### maboss-ecosystem

Carte de l'ecosysteme MaBoSS et CoLoMoTo et positionnement d'un nouvel outil : le moteur C++ MaBoSS (2.6.6, Gillespie, jusqu'a 64 noeuds ; Stoll 2012 et 2017), les bindings pyMaBoSS, l'evaluateur d'assertions en logique temporelle CCT (Oscar Dufossez), WebMaBoSS (Vincent Noel 2021, Docker et MariaDB, imports depuis BioModels et Cell Collective), PopMaBoSS, UPMaBoSS, PhysiBoSS, et les depots de modeles. Aussi les tutoriels de reference (dommage a l'ADN p53, Montagud 2022 cancer de la prostate, Cohen 2015 invasion tumorale) et le positionnement face a INDRA et WebMaBoSS.

Compétences : decider entre construire et reutiliser ; positionner la nouveaute d'un projet ; citer le bon article ou le bon auteur ; choisir la provenance des modeles ; identifier qui contacter ; complement de pymaboss (API) et maboss-model (format de fichier)

### maboss-model

Ecrit, lit et valide les fichiers de modeles booleens MaBoSS : le couple .bnd (logique des noeuds et taux de transition) et .cfg (etats initiaux, variables externes, parametres d'execution). Encode la grammaire officielle de la Reference Card du moteur 2.6.6 : syntaxe des noeuds, prefixes @ pour les variables de noeud et $ pour les variables externes, jeu d'operateurs, semantique rate_up / rate_down / logic (taux derives de la logique quand ils sont omis), cles du .cfg (poids d'istate, is_internal, refstate, time_tick, max_time, sample_count, thread_count, graines, statdist), la ligne de commande, et les fichiers de sortie. Limite de 64 noeuds sauf recompilation du moteur.

Compétences : ecrire ou reparer un .bnd ou un .cfg ; expliquer l'idiome de logique ou de taux d'un noeud ; choisir des priors d'istate ; decider quels noeuds sont internes ; distinguer un noeud pilote d'un noeud derive ; comprendre pourquoi un modele ne simule pas

### model-inference

Construit ou affine un modele booleen A PARTIR DE DONNEES et de contraintes : BoNesis (synthese de reseaux booleens depuis un graphe d'influence et des proprietes dynamiques, par programmation par ensembles-reponses), Caspo (apprentissage de modeles logiques depuis des donnees de signalisation phosphoproteomiques), scBoolSeq (binarisation de scRNA-seq et generation de donnees synthetiques depuis une dynamique booleenne), et la reconstruction R-BoolNet.

Compétences : on dispose d'observations (etats stationnaires, series temporelles, reponses a des perturbations, scRNA-seq) et on veut un modele compatible ; enumerer tous les modeles ajustant les donnees ; binariser du scRNA-seq

### model-repositories

Trouve et importe des modeles booleens ou logiques existants de cancer et de signalisation sous une forme prete pour MaBoSS, depuis BioModels (API REST), Cell Collective, le depot de modeles GINsim, et CaSQ (construction d'un modele executable a partir d'une carte d'interactions CellDesigner ou SBML).

Compétences : il faut un vrai modele publie plutot qu'un .bnd ecrit a la main ; alimenter le catalogue mabossDemo ou l'outil d'import de maboss-mcp ; recuperer un modele precis, par exemple le modele EMT de Selvaggio

### pydruglogics

Construit et optimise des modeles booleens, execute des perturbations medicamenteuses in silico et predit des synergies avec PyDrugLogics (pile DrugLogics), et fait du repositionnement de medicaments oriente reseau avec NORDic. Aligne sur le contexte de signalisation du cancer de l'Institut Curie.

Compétences : predire l'effet d'un medicament seul ou en combinaison sur un modele de signalisation ; cribler des synergies ; repositionner des medicaments contre un phenotype cible ; quelle combinaison de medicaments

### pymaboss

Pilote la veritable API Python pyMaBoSS (colomoto/pyMaBoSS, bindings du moteur C++ MaBoSS). Couvre le chargement (load, loadBNet, loadSBML, loadTabularQual), l'objet Simulation (run, mutate, copy, update_parameters, get_logical_rules), copy_and_mutate, set_output, set_nodes_istate, l'extraction des resultats (get_nodes_probtraj, get_states_probtraj, get_last_nodes_probtraj), l'interoperabilite (to_biolqm, to_minibn), MaBoSSClient, UPMaBoSS, Ensemble et PopMaBoSS, les widgets Jupyter, et l'evaluateur d'assertions en logique temporelle CCT maboss.temporal_logic.MaBoSSEvaluator.querying d'Oscar Dufossez, veritable implementation de la grammaire de requetes P/T/Pmax/Pmin/Tmax/Tmin/Inc/Dec. Installation : conda install -c colomoto pymaboss puis python -m maboss_setup.

Compétences : executer un modele MaBoSS depuis Python ; appliquer une invalidation ou une surexpression ; lire P(noeud) au dernier pas de temps ; verifier une affirmation directionnelle de la litterature via MaBoSSEvaluator

