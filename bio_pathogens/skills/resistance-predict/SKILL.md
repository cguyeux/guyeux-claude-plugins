---
name: resistance-predict
description: >-
  Academic research toolkit for the Guyeux group (FEMTO-ST, University of
  Franche-Comté) MTBC pipeline: predict the antimicrobial-resistance phenotype
  of a Mycobacterium tuberculosis strain from its genomic variant profile, by
  combining the deterministic curated catalogue (`resistance-catalogue`) with a
  residual gradient-boosted model, and explain each prediction (feature
  importance / SHAP + ESM protein-impact). Evaluated honestly with
  lineage-stratified cross-validation (GroupKFold) and compared to the catalogue
  baseline at equal specificity, for peer-reviewed phylogenomic and AMR-evolution
  publications. Built on variant-representation reconciliation (SNP+MNV, amino-acid
  level) so the catalogue baseline is not under-counted.

  Use when: predicting resistance for a strain or cohort, quantifying how much a
  machine-learning layer adds over the WHO catalogue per medicine, producing a
  per-medicine sensitivity/specificity table for a manuscript, or explaining a
  prediction by the variants driving it.
argument-hint: "profil: <--spdi FILE | --vcf FILE | --variant katG_p.Ser315Thr | --strains ids.txt> · entraînement: <--drugs pyrazinamide,isoniazid [--folds 5]>"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# Resistance Predict — prédiction de résistance par médicament (MTBC)

Prédicteur opérationnel par médicament, qui **combine deux étages** :
1. **catalogue déterministe** (`resistance-catalogue`) réconcilié SNP+MNV au niveau AA
   (`variant_match`) — capture la résistance connue, très spécifique ;
2. **modèle XGBoost résiduel** sur les features génomiques — capture le signal au-delà
   du catalogue (et le contexte MDR).

Implémentation projet : `Resistance_antibio/analyses/phase10_predict.py`.

## Principe d'évaluation (honnête)

- **GroupKFold par lignée Coll** : le test tombe sur des lignées non vues → pas de fuite
  phylogénétique (une CV aléatoire gonfle l'AUC de ~0.02–0.04, mesuré).
- **Comparaison à spécificité égale** : le ML n'est utile que s'il gagne en sensibilité
  SANS perdre en spécificité par rapport au baseline catalogue. Rapporter le combiné avec
  son couple (sensibilité, spécificité), pas une AUC seule.
- **Baseline = catalogue réconcilié** (`variant_match`, gère les 3 angles morts de
  représentation : codons synonymes, déterminants rares, MNV vs SNP). Sans cette
  réconciliation, le baseline est sous-estimé (FQ : 0.25 au lieu de 0.80) et le ML
  semble faussement utile.

## Architecture

```
prédiction(souche, médicament) =
    catalogue_carries(souche)            # déterministe, réconcilié SNP+MNV
    OU  XGBoost_proba(features) > seuil  # résiduel, seuil calibré
```
Le seuil ML se calibre selon le compromis sensibilité/spécificité visé (clinique → haute
spécificité ; dépistage → haute sensibilité).

## Outil d'interrogation opérationnel (`scripts/resistance_profile.py`)

L'étage déterministe est packagé en CLI autonome (chemins via `RESISTANCE_PROJECT`,
matching réconcilié `variant_match`). Souche unique ou cohorte, **sans réseau** :

```bash
S=scripts
# souche unique -> profil détaillé par médicament + déterminants touchés
python3 $S/resistance_profile.py --spdi souche.txt          # liste de SPDI 0-based
python3 $S/resistance_profile.py --vcf souche.vcf           # VCF H37Rv (POS-1)
python3 $S/resistance_profile.py --variant rpoB_p.Ser450Leu # une mutation HGVS
# cohorte -> tableau souche × médicament + résumé (taux R, MDR, pré-XDR)
python3 $S/resistance_profile.py --spdi-dir dossier/ --out profils.tsv
python3 $S/resistance_profile.py --strains ids.txt [--pangenome]   # résout via bdd/actuelle
```

`--json` pour la sortie structurée. Le matching réconcilié capte les angles morts : un
gyrA Asp94Gly présenté en MNV ressort « R » aux fluoroquinolones, là où un matching SPDI
brut le manque. C'est le baseline déterministe (l'essentiel du signal à spécificité
contrôlée) ; le ML résiduel (`phase10_predict.py`) ne s'y ajoute que marginalement.
**Recherche, pas de diagnostic clinique** : précéder d'un sas QC (`species-id`
anti-kansasii, `strain-qc`). Dépendances : pandas (le profil seul n'exige pas xgboost).

## Explicabilité

- **Importance (gain) / SHAP** : variants qui pèsent le plus dans la prédiction, annotés
  gène, avec flag catalogué / hors-catalogue.
- Un variant hors-catalogue important n'est PAS forcément causal : il peut tracer le
  contexte MDR/co-résistance. Le confirmer via `resistance-discovery` (GWAS + convergence)
  et `mtbc-mutation-impact` (impact protéique ESM, LLR Meier 2021) avant toute conclusion.

## Commandes

```bash
cd "${RESISTANCE_PROJECT:-$HOME/docs/codes/mtbc/Resistance_antibio}"
.venv-ingest/bin/python analyses/phase10_predict.py --drugs pyrazinamide,isoniazid --folds 5
# prérequis : phase4 (matrice), phase6 (masque), catalogue enrichi (phase1+aa_propagation)
```

## Enseignement (ce que le ML apporte, et où)

Mesuré : là où le catalogue est complet (INH, RIF), le ML n'ajoute presque rien à
spécificité contrôlée. Là où il est incomplet (PZA : pncA très diverse), le ML porte un
signal réel (AUC ~0.84) mais limité à haute spécificité, et capte surtout le contexte MDR.
Le prédicteur opérationnel reste donc **catalogue-centré**, le ML servant de filet pour les
cas non couverts — à condition d'expliciter le compromis sensibilité/spécificité.

## Dépendances

```bash
pip install pandas numpy scipy scikit-learn xgboost
```
