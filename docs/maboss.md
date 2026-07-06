# Plugin `maboss`

> Academic toolkit for MaBoSS (Markovian Boolean Stochastic Simulator) and the CoLoMoTo ecosystem: authoring and validating .bnd/.cfg Boolean models, driving the pyMaBoSS Python API (simulation, mutations, probability trajectories, the temporal-logic / CCT assertion evaluator of Oscar Dufossez, MaBoSS server, Jupyter widgets), and navigating the ecosystem (WebMaBoSS by Vincent Noel, model repositories BioModels/CellCollective, PhysiBoSS, positioning vs INDRA). Ground truth captured from the official refcard and repository trees (July 2026). Used by the Guyeux group (FEMTO-ST, University Marie et Louis Pasteur) for cancer signalling modelling and the mabossDemo literature-coherency project.

## Positionnement

Projet distinct. maboss / CoLoMoTo n'appartient pas au programme M. tuberculosis : il concerne la modélisation booléenne stochastique de réseaux de signalisation (signalisation cancéreuse, projet mabossDemo). Il est documenté ici uniquement parce qu'il partage le même dépôt de plugins, et reste hors du pipeline de recherche M. tuberculosis.

Skills propres (canoniques) : **3** ; skills partagés utilisés (symlinks) : **0**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [maboss-ecosystem](#maboss-ecosystem) ; [maboss-model](#maboss-model) ; [pymaboss](#pymaboss)

### maboss-ecosystem

Map of the MaBoSS / CoLoMoTo ecosystem and where a new tool fits: the MaBoSS C++ engine (2.6.6, Gillespie, ≤64 nodes; Stoll 2012 & 2017), pyMaBoSS bindings, the CCT temporal-logic assertion evaluator (Oscar Dufossez), WebMaBoSS (web interface, FIRST author Vincent Noel 2021; Docker+MariaDB; imports models from BioModels and CellCollective; SBML-qual/GINsim/BNet; live at maboss.curie.fr/WebMaBoSS), PopMaBoSS/UPMaBoSS/PhysiBoSS, and the model repositories (BioModels, Cell Collective by disease, GINsim, PhysiBoSS Boolean-models). Also the reference tutorials (p53 DNA-damage; Montagud 2022 prostate cancer; Cohen 2015 tumour invasion/EMT = the 32-node ginsimout_export model in mabossDemo) and the prior-art positioning of a literature→model-coherency tool against INDRA (Sorger; NLP→statements→ModelChecker) and WebMaBoSS

Compétences : deciding whether to build vs reuse (a model library, an assertion evaluator, a coherency checker already exist), positioning a project's novelty, citing the right paper/author, choosing where models come from, or identifying who to contact (Vincent Noel for WebMaBoSS/pyMaBoSS/server ; Oscar Dufossez for CCT) ; Companion to `pymaboss` (API) and `maboss-model` (file format)

### maboss-model

Author, read, and validate MaBoSS Boolean-model files: the .bnd (node logic + transition rates) and .cfg (initial states, external variables, run parameters) couple. Encodes the official MaBoSS Reference Card grammar (engine 2.6.6): node syntax `node NAME { logic = (...); rate_up = @logic ? $u : 0; ... }`, the @ node- variable prefix and $ external-variable prefix, operators (! && & || | ^/XOR, ternary ? :), the rate_up/rate_down/logic semantics (if rates omitted, MaBoSS derives them from logic), .cfg keys (NODE.istate weighted `0.5 [0], 0.5 [1]`, is_internal, refstate, time_tick, max_time, sample_count, discrete_time, thread_count, use_physrandgen/seed_pseudorandom, statdist_*), the CLI (`MaBoSS -c m.cfg -o prefix m.bnd`, plus -t template, -l logical-expr, -d dump), and the outputs (_probtraj.csv, _fp.csv, _statdist.csv)

Compétences : writing or fixing a .bnd/.cfg, explaining a node's logic/rate idiom, choosing istate priors, deciding is_internal/observed nodes, converting a driver node (`logic = (X)` holds its initial state) vs a derived node, or debugging why a model does not simulate ; Pairs with the `pymaboss` skill (to run it) and `maboss-ecosystem` (where models come from) ; ≤64 nodes unless the engine was recompiled with MAXNODES

### pymaboss

Drive the real pyMaBoSS Python API (colomoto/pyMaBoSS, bindings over the MaBoSS C++ engine). Covers loading (maboss.load / loadBNet / loadSBML / loadTabularQual), the Simulation object (.run, .mutate(node, ON|OFF|WT), .copy, .update_parameters, .get_logical_rules), copy_and_mutate / set_output / set_nodes_istate, extracting results (get_nodes_probtraj, get_states_probtraj, get_last_nodes_probtraj), interop (to_biolqm, to_minibn), the MaBoSS server client (MaBoSSClient), UPMaBoSS (UpdatePopulation), Ensemble and PopMaBoSS, Jupyter widgets, AND crucially the temporal-logic / CCT assertion evaluator `maboss.temporal_logic.MaBoSSEvaluator.querying(query, cfg, bnd, [istate], [output])` written by Oscar Dufossez, the real implementation of the P/T/Pmax/ Pmin/Tmax/Tmin/Inc/Dec query grammar (node:A, state:A--B, `/ [constraints] [mutations]`). Install: `conda install -c colomoto pymaboss` then `python -m maboss_setup` for the binaries

Compétences : running a MaBoSS model from Python, applying a knock-out/over-expression, reading P(node) at the last time point, checking a directional literature claim ("does inhibiting X decrease Y?") via MaBoSSEvaluator instead of reimplementing an evaluator, or wiring a real pyMaBoSS runner (e.g ; mabossDemo's PyMaBoSSRunner stub) ; Pairs with `maboss-model` (write the files) and `maboss-ecosystem` (who/what)

