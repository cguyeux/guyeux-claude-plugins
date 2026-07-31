---
name: active-site-check
description: >
  Academic research toolkit (Guyeux group, FEMTO-ST) : valide une requalification
  d'enzyme « same fold → enzyme active » en vérifiant que les RÉSIDUS CATALYTIQUES
  de l'enzyme M-CSA appariée par Foldseek sont conservés dans la protéine requête.
  Utiliser quand : gène « hypothetical »/dark du MTBC avec hit Foldseek vers une
  enzyme, annotation d'un protéome par structure, preuve de site actif demandée
  par un reviewer.
---

# active-site-check : validation du site catalytique via M-CSA

## Quand l'utiliser

- Un gène « hypothetical » / dark du MTBC a un hit Foldseek vers une enzyme connue et il faut
  trancher « enzyme active vs simple homologie de repli » avant d'écrire une fonction dans une
  fiche (projets `annotation_mtbc`, `TA_repertoire`, `dark_enzymes`).
- On annote un protéome bactérien par structure et il faut **graduer la confiance** des
  requalifications enzymatiques.
- Un reviewer demande des **preuves de site actif** à l'appui d'une annotation fonctionnelle.

Formulations qui doivent déclencher ce skill : « est-ce une enzyme active ou juste le même
repli », « résidus catalytiques », « site actif conservé », « M-CSA », « valider un hit
Foldseek enzyme ».

## Pourquoi ce skill

Le pipeline d'annotation structure-guidée (ESMFold + Foldseek + Pfam + eggNOG/UniProt, cf.
`annotation_mtbc/`) répond à « quel repli ? » et transfère des GO/EC par similarité. Mais **un hit
Foldseek significatif signifie « même repli », pas « enzyme active »** : beaucoup de protéines
adoptent un repli enzymatique sans en avoir le site actif (résidus catalytiques mutés/absents,
pseudo-enzymes, domaines détournés). Ce skill ajoute la couche manquante : confronter le hit aux
**résidus catalytiques curés de M-CSA** et vérifier leur présence/conservation dans la requête.

C'est l'apport additif par rapport :
- au pipeline atlas actuel (Foldseek seul → repli) ;
- au papier *Functional (re)annotation of Mycobacteroides abscessus proteome* (Gnanasekar et al.,
  Curr Res Struct Biol 2025, `10.1016/j.crstbi.2025.100172`), qui fait du transfert de GO par
  Foldseek sur modèles AlphaFold mais **ne valide pas les sites actifs**. Ce skill est précisément
  le cran de rigueur en plus, réutilisable sur tout protéome.

## Données : M-CSA

Mechanism and Catalytic Site Atlas (Thornton group, EBI). ~1003 entrées / 895 EC, résidus
catalytiques curés à la main, mappés sur PDB **et** UniProt, avec leurs rôles mécanistiques.
API REST (utilisée par le script, cache disque sous `$MCSA_CACHE` ou `~/.cache/mcsa/`) :
- `…/api/entries/<id>/?format=json`, entrée détaillée (résidus embarqués).
- `…/api/entries/?format=json`, liste paginée (indexée localement par EC/UniProt/PDB).
Champs clés : `reaction.ec`, `reference_uniprot_id`, `residues[i].residue_sequences[0].resid`
(numérotation UniProt), `residues[i].residue_chains[0].{pdb_id,chain_name,auth_resid,code}`,
`residues[i].roles_summary`. Citation : Ribeiro et al., NAR 2018 (M-CSA), CC-BY 4.0.

## Usage

```bash
PY=~/.claude/skills/active-site-check/active_site_check.py   # (symlink) ou chemin canonical

# 1) Lister les résidus catalytiques d'une enzyme M-CSA (par EC, UniProt, PDB ou M-CSA id)
python3 $PY residues --mcsa 2
python3 $PY residues --ec 3.5.2.6
python3 $PY residues --pdb 1btl        # (charge la liste complète au 1er appel, puis cache)

# 2) Vérifier la conservation du site actif dans la requête
#    qaln/taln = chaînes alignées requête/cible (avec '-'), en coordonnées de SÉQUENCE de la cible ;
#    tstart = numéro de résidu UniProt du premier résidu cible aligné.
python3 $PY check --uniprot P62593 --tstart 68 --qaln "S-ALK..." --taln "SXALK..."
```

Verdict : sur N résidus catalytiques, k présents (non-gap) et m identiques.
`m/N ≥ 0.8` → **site actif conservé → enzyme probablement active** ; `k/N < 0.5` → **fold-only**
(même repli, site actif non retenu) ; entre les deux → partiel/ambigu à inspecter.

## Branchement sur le pipeline atlas (Foldseek)

L'alignement requête↔cible vient directement de Foldseek (phase2c) lancé avec
`--format-output query,target,...,qaln,taln,qstart,tstart,...`. Pour chaque hit dont la cible est
une enzyme cataloguée M-CSA (résoudre l'EC/UniProt de la cible PDB), passer `qaln/taln/tstart` à
`check`. Pour une intégration proteome-wide, en faire une phase `phase2i_mcsa.py` qui itère sur les
hits Foldseek significatifs et écrit une colonne `mcsa` sur la fiche (résidus catalytiques attendus,
présents, identiques, verdict).

## Limites / garde-fous (à respecter, cf. conventions MTBC)

- **Réconciliation de numérotation** (le point délicat). M-CSA donne le résidu en numérotation
  UniProt ET PDB (`auth_resid`), souvent décalées (ex. entrée 2 : SER68 UniProt = PDB A:70). Le
  script mappe en coordonnées de **séquence cible** (UniProt) : il faut donc que `taln/tstart`
  soient dans la même numérotation que les `uniprot_resid` de M-CSA. Si l'alignement Foldseek est en
  coordonnées de structure PDB, convertir via le mapping SEQRES↔auth_resid de la cible avant `check`.
  En cas de doute, lister d'abord les résidus (`residues`) et vérifier l'ancrage sur 1-2 positions.
- **Conservation ≠ activité prouvée.** Un site actif conservé est une forte présomption, pas une
  preuve d'activité ; rester au niveau « probablement active », corroborer (littérature, contexte
  opéron/voie, expression) avant d'écrire un fait. Cohérent avec le garde-fou ESM/structure de
  `annotation_mtbc/CLAUDE.md`.
- **Couverture M-CSA limitée** (~895 EC) : beaucoup d'enzymes n'y sont pas ; absence d'entrée ≠
  absence de fonction. Le skill ne s'applique qu'aux hits dont la cible est cataloguée M-CSA.
- **Pseudo-enzymes** : un verdict fold-only peut révéler une pseudo-enzyme régulatrice
  (intéressant en soi), pas forcément une erreur d'annotation.

## Statut

v1 (2026-06-09) : récupération M-CSA + mapping/conservation au niveau séquence, testée (entrée 2,
β-lactamase). Reste à industrialiser : la réconciliation de numérotation structure↔séquence pour un
branchement proteome-wide automatique (phase2i), et l'option d'un test SPATIAL (superposition 3D
plutôt qu'alignement de séquence) pour les cas de faible identité de séquence mais repli conservé.
