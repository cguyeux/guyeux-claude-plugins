---
name: maboss-ecosystem
description: >-
  Map of the MaBoSS / CoLoMoTo ecosystem and where a new tool fits: the MaBoSS C++ engine
  (2.6.6, Gillespie, up to 64 nodes; Stoll 2012 and 2017), pyMaBoSS bindings, the CCT
  temporal-logic assertion evaluator (Oscar Dufossez), WebMaBoSS (Vincent Noel 2021, Docker
  and MariaDB, imports from BioModels and Cell Collective, maboss.curie.fr/WebMaBoSS),
  PopMaBoSS, UPMaBoSS, PhysiBoSS, and the model repositories. Also the reference tutorials
  (p53 DNA damage, Montagud 2022 prostate cancer, Cohen 2015 tumour invasion) and prior-art
  positioning against INDRA and WebMaBoSS. Use when deciding whether to build or reuse,
  positioning a project's novelty, citing the right paper or author, choosing where models
  come from, or identifying who to contact. Companion to pymaboss (API) and maboss-model
  (file format).
argument-hint: "[question]   # e.g. 'is there a curated cancer model library?' / 'novelty vs INDRA?'"
allowed-tools: Read, WebSearch, WebFetch, Bash
user-invocable: true
---

# /maboss-ecosystem : who does what, and what already exists

Captured by navigating the official sites/repos (July 2026). The recurring lesson: **most
"obvious extensions" already exist in the CoLoMoTo ecosystem, reuse and position, do not reinvent.**

## The tools

- **MaBoSS engine** (`github.com/sysbio-curie/MaBoSS`, C++ 2.6.6): continuous/discrete-time stochastic
  Boolean simulation (Gillespie/Monte-Carlo) → probability trajectories. ≤64 nodes by default
  (recompile with `MAXNODES`). Also ships cMaBoSS (C-API bindings) and PopMaBoSS. Refs: Stoll et al.
  2012 (BMC Syst Biol), **Stoll et al. 2017, MaBoSS 2.0 (Bioinformatics)**. Refcard PDF in
  `engine/doc/MaBoSS-RefCard.pdf`. Install `conda install -c colomoto maboss`.
- **pyMaBoSS** (`github.com/colomoto/pyMaBoSS`): Python bindings + Jupyter widgets + interop
  (bioLQM/minibn) + server client + the CCT evaluator. See the `pymaboss` skill.
- **CCT / temporal_logic** (`maboss.temporal_logic.MaBoSSEvaluator`): the assertion/query language
  (P/T/Pmax/Pmin/Tmax/Tmin/Inc/Dec, `node:`/`state:A--B`), author **Oscar Dufossez** (2026). This is
  the real thing a "MCCT assertion" maps to. Contact Oscar for its scope.
- **WebMaBoSS** (`github.com/sysbio-curie/WebMaBoSS`): web interface to MaBoSS. **First author Vincent
  Noel** (Noel, Ruscone, Stoll, Viara, Zinovyev, Barillot, Calzone, 2021, Front. Mol. Biosci.). Docker
  (`sysbiocurie/webmaboss`) + MariaDB, user accounts, store/edit/simulate models, **import from
  BioModels and CellCollective**, and from SBML-qual / GINsim / BNet. Live: `maboss.curie.fr/WebMaBoSS`.
  → A per-user model store WITH repository import already exists here.
- **PopMaBoSS / UPMaBoSS / PhysiBoSS**: population and multiscale/agent-based extensions.

## Where models come from (the "model library" question)

There is no need to invent a cancer-model library, browse/import from:
- **Cell Collective** (`cellcollective.org`): logical models by biological process incl. cancer
  (breast, prostate, blood).
- **BioModels**: ~800 curated models, Boolean ones in SBML-qual.
- **GINsim** model repository; **PhysiBoSS `Boolean-models`** (`github.com/PhysiBoSS/Boolean-models`);
  the "PhysiBoSS-Models" database (arXiv 2508.05550, 2025).
- **WebMaBoSS** already wires BioModels + CellCollective import. pyMaBoSS can `loadSBML`/`loadBNet`.

Reference cancer models to know: **Cohen 2015** (tumour cell invasion/migration, EMT/metastasis, 32
nodes, this is `models/demo/ginsimout_export.bnd` in mabossDemo), **Montagud 2022** (prostate, LNCaP),
Fumia (pan-cancer signalling), Flobak (gastric), Beal (breast personalisation).

## Positioning a literature→coherency tool (prior art : argue the delta before building)

- **INDRA** (Sorger/Gyori/Bachman, Harvard): NLP → mechanistic "Statements" → assemble into executable
  models, WITH a `ModelChecker` that checks a model against statements. So "literature→assertion→model
  checking" already exists and is mature. INDRA's belief model gives principled statement-level
  uncertainty; its readers are classic (REACH/Sparser/TRIPS), so LLM extraction has a *recall* edge but
  not a durable moat (LLM self-confidence is poorly calibrated).
- **MaBoSS/CCT** already provides the directional stochastic verdict (Inc/Dec, Δprobability vs
  threshold) and the evaluator (Oscar). WebMaBoSS provides the models.
- **The remaining defensible niche of an LLM+MaBoSS tool** = automating *literature → CCT query* with an
  LLM (extraction + strict grounding: drug/antibody/ligand ≠ node; separated confidences), feeding the
  EXISTING evaluator and models, a front-end layer, not a new evaluator or repository. Any novelty
  claim must be benchmarked against INDRA (extraction) and shown to add over WebMaBoSS+CCT.

## Contacts

Vincent Noel : WebMaBoSS, pyMaBoSS, MaBoSS server. Oscar Dufossez, CCT / temporal_logic evaluator.
Curie/CoLoMoTo team: Laurence Calzone, Gautier Stoll, Emmanuel Barillot, Andrei Zinovyev, Aurelien Naldi.
