---
name: resistance-discovery
description: >-
  Academic research toolkit for the Guyeux group (FEMTO-ST, University of
  Franche-Comté) MTBC pipeline: discover NON-catalogued antimicrobial-resistance
  determinants in the Mycobacterium tuberculosis complex by genome-wide
  association, controlling for population structure and co-resistance, and
  validating candidates by phylogenetic convergence. Complements the curated
  `resistance-catalogue` (the known, deterministic part) by surfacing variants
  associated with resistance that the catalogue misses, for peer-reviewed
  phylogenomic and AMR-evolution publications. Also documents and corrects the
  three representation blind spots of SPDI-indexed catalogues (synonymous codons,
  rare determinants, MNV-vs-SNP) that otherwise inflate false discoveries.
  Pairs with `convergent-evolution`, `mtbc-mutation-impact` and `tbmonitor-papers`
  to confirm and contextualise candidates.

  Use when: searching for novel resistance determinants beyond the WHO catalogue,
  auditing why a drug's catalogue baseline has low sensitivity, building a
  lineage-aware GWAS of an antitubercular medicine, or screening candidates while
  rejecting clonal-linkage artefacts.
argument-hint: "<--drug ethambutol [--sanity]>  (méthode + scripts dans le projet Resistance_antibio)"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres
---

# Resistance Discovery — déterminants de résistance HORS catalogue (MTBC)

Découverte de déterminants génomiques de résistance que le catalogue (`resistance-catalogue`)
ne contient pas, par **GWAS à correction de structure**, conditionnée sur la **co-résistance**,
et validée par **convergence phylogénétique**. Le catalogue est le savoir déterministe ;
ce skill cherche le résiduel — et seulement le résiduel réel, pas des artefacts.

Scripts dans le projet `Resistance_antibio/analyses/` (`phase4_build_matrix.py`,
`phase6_feature_mask.py`, `phase7_gwas_logistic.py`, `aa_propagation.py`) ; le module
réutilisable `variant_match.py` est embarqué ici (`scripts/`).

## Principe fondateur

Un modèle prédictif ou une GWAS n'a d'intérêt **qu'au-delà du catalogue**. Inclure les
déterminants connus parmi les features ne fait que réapprendre le catalogue et le biais
MDR/phylogénétique. On exclut donc le connu, et on cherche le nouveau, en contrôlant
rigoureusement les deux confondants : structure de population et co-résistance.

## ÉTAPE 0 (CRITIQUE) — corriger les trois angles morts de représentation

Avant toute découverte, le matching variant↔catalogue doit être correct, sinon la GWAS
« redécouvre » des déterminants connus mal représentés. Trois angles morts d'un catalogue
SPDI-indexé, tous mesurés sur données réelles :

1. **Codons synonymes** d'un même acide aminé (embB Met306Ile via ATG→ATC absent quand
   seul ATG→ATT est catalogué). Correction : propagation AA (`aa_propagation.py`, intégrée
   au build du catalogue). Gain baseline : **éthambutol +23 pts** de sensibilité.
2. **Déterminants rares** élagués par le filtre de fréquence de la matrice de features.
   Correction : inclure de force les déterminants R catalogués observés (`phase4`).
3. **MNV (pangénome) vs SNP (catalogue)** sur la QRDR gyrA : le pangénome appelle des
   variants multi-bases que le catalogue, en SNP, ne croise jamais. Correction :
   **décomposition** des MNV en SNP composants (`variant_match.py`). Gain baseline :
   **moxifloxacine +55 pts** (0.25→0.80), lévofloxacine +51 pts.

Conséquence : tout matching (baseline, exclusion, prédiction) passe par `variant_match`
(`determinant_snp_set`, `carrier_columns`, `carries`), pas par une égalité SPDI brute.
Limite résiduelle : indels (longueurs ref/alt ≠) non décomposables.

## ÉTAPE 1 — jeu de données

`phase4_build_matrix.py` : matrice creuse souche×SPDI sur les souches phénotypées ayant
des features (cascade pangénome ∪ `bdd/actuelle/`), + métadonnées (phénotypes, lignée Coll).
Inclut de force les déterminants R catalogués même rares (angle mort #2).

## ÉTAPE 2 — masque des features

- **Catalogue** : exclure les déterminants R de la drogue (réconciliés SNP+MNV) pour ne pas
  redécouvrir le connu.
- **Lignée** : `phase6_feature_mask.py` exclut les marqueurs de lignée (barcoding_v2,
  `role==positive`) SAUF ceux tombant dans un gène de résistance (règle gid/streptomycine ;
  un marqueur de lignée dans un gène AMR peut être une mutation R fondatrice de clone).

## ÉTAPE 3 — GWAS à correction de structure (`phase7_gwas_logistic.py`)

`logit(R ~ variant + PC1..20 + score_co-résistance)` par variant candidat :
- **PC** (TruncatedSVD de la matrice) absorbent la structure phylogénétique ;
- **score de co-résistance** = nb d'autres médicaments avec déterminant R porté (réconcilié),
  neutralise le confondant MDR ;
- pré-filtre χ² vectorisé → régression complète sur le top ; FDR Benjamini-Hochberg.

## ÉTAPE 4 — filtres anti-artefact (décisifs)

- **Convergence** : un déterminant causal apparaît dans plusieurs fonds génétiques ; un
  marqueur de clone est mono-lignée. On rejette `frac_top_sublineage > 0.6` ou `n_lineages ≤ 1`.
  (Sur l'éthambutol, ce filtre fait tomber 264 hits à 2.)
- **Direction** : ne garder que `OR > 1` (résistance, pas marqueurs protecteurs de fond).

## ÉTAPE 5 — validation d'un candidat

- **Homoplasie** sur arbre (`convergent-evolution`, `pastml`, `iqtree-lsd2`) : compter les
  acquisitions indépendantes.
- **Impact protéique** (`mtbc-mutation-impact`, ESM + LLR Meier 2021).
- **Littérature** (`tbmonitor-papers`) : déjà décrit ?

## Validation de la machinerie (sanity)

`phase7 --drug isoniazid --sanity` (sans exclusion) doit retrouver **fabG1/inhA** (OR≈42)
en tête : preuve que la GWAS remonte les vrais signaux.

## Commandes

```bash
cd "${RESISTANCE_PROJECT:-$HOME/docs/codes/mtbc/Resistance_antibio}"
.venv-ingest/bin/python analyses/phase4_build_matrix.py        # matrice (cascade)
.venv-ingest/bin/python analyses/phase6_feature_mask.py        # masque lignée
.venv-ingest/bin/python analyses/phase7_gwas_logistic.py --drug ethambutol     # découverte
.venv-ingest/bin/python analyses/phase7_gwas_logistic.py --drug isoniazid --sanity   # validation
```

## Enseignement (résultat publiable)

Sur les médicaments de 1re ligne bien catalogués (INH, RIF), une fois les angles morts
corrigés, le catalogue capture l'essentiel de la résistance et le résiduel hors-catalogue
est faible. Les médicaments où la découverte a du potentiel sont ceux à catalogue incomplet
(angle mort de représentation ou résistance par mécanismes non-cible). Le pipeline distingue
un vrai déterminant convergent d'un artefact de clone ou de co-résistance — c'est sa valeur.

## Dépendances

```bash
pip install pandas numpy scipy scikit-learn statsmodels
```
