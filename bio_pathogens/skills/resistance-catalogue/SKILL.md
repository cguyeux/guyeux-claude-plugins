---
name: resistance-catalogue
description: >-
  Academic research toolkit for peer-reviewed MTBC antimicrobial-resistance genomics (Guyeux
  group, FEMTO-ST). Query or rebuild the WHO / tb-profiler mutation catalogue, resolve HGVS
  to SPDI, profile or predict a published research isolate's phenotype, run lineage-aware
  GWAS for non-catalogued determinants, and build a variant's mechanistic dossier (empirical
  association, TB literature, ESM-1v LLR, 3D context). Use when asked whether a variant is a
  known resistance determinant in the published catalogue, what a research isolate's
  predicted phenotype is, which determinants explain an unexplained phenotype in a study
  collection, or how a catalogue entry was graded.
argument-hint: "catalogue: <--variant katG_p.Ser315Thr | --drug isoniazid | --spdi NC_000962.3:2155167:C:G | --stats> · profil: <--spdi FILE | --vcf FILE | --strains ids.txt> · découverte: <--drug ethambutol [--sanity]>"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbmonitor__execute_sql, mcp__tbannotator__tool_query_postgres
---

# Resistance Catalogue : catalogue, profil, découverte et explication (MTBC)

> Cadre : groupe Guyeux, Institut FEMTO-ST (CNRS UMR 6174), Université Marie et Louis
> Pasteur (ex-Université de Franche-Comté), Besançon. Outil de recherche académique,
> destiné à des publications évaluées par les pairs en phylogénomique et en évolution
> de la résistance aux antimicrobiens (AMR evolution).

Skill unique du volet résistance du groupe. Il couvre la chaîne complète, du savoir
catalogué jusqu'au dossier mécanistique d'un variant, autour d'un **socle de
réconciliation SNP / MNV / acide aminé** commun aux quatre modes.

Toutes les données vivent dans le projet `Resistance_antibio` ; ce skill les interroge
et ne les duplique pas. Racine surchargeable par `RESISTANCE_PROJECT`
(défaut `~/docs/codes/mtbc/Resistance_antibio`).

## Routeur d'intention

| Ce que l'on cherche | Mode |
|---|---|
| Grade et provenance d'une mutation, marqueurs catalogués d'un médicament, régénération du catalogue, conversion HGVS → SPDI | [1. Catalogue](#mode-1--catalogue) |
| Profil d'une souche ou d'une cohorte, prédiction par médicament, table sensibilité/spécificité pour un manuscrit, gain du ML sur le catalogue | [2. Profil et prédiction](#mode-2--profil-et-prédiction) |
| Déterminants **hors** catalogue, baseline faible sur un médicament, GWAS à correction de structure, artefacts de clonalité | [3. Découverte](#mode-3--découverte-hors-catalogue) |
| Pourquoi un variant confère la résistance, interprétation d'un candidat, paragraphe mécanistique, causal contre co-résistance | [4. Explication](#mode-4--explication-mécanistique) |

## Socle commun (valable pour les quatre modes)

### Catalogue déterministe contre apprentissage hors catalogue

Le catalogue est un **savoir au niveau mutation** (variant → médicament → verdict),
c'est-à-dire un prédicteur déterministe de type TB-Profiler. Un modèle appris ou une
GWAS n'ont d'intérêt qu'**au-delà** de ce savoir : inclure les déterminants connus
parmi les features ne fait que réapprendre le catalogue et le biais MDR/phylogénétique.
Le catalogue sert donc de **baseline à battre**, et d'ensemble à exclure.

### Les trois angles morts de représentation (ÉTAPE 0, critique)

Avant tout baseline, toute exclusion et toute prédiction, le matching variant ↔ catalogue
doit être correct, sinon la GWAS « redécouvre » des déterminants connus mal représentés et
le ML paraît faussement utile. Trois angles morts d'un catalogue SPDI-indexé, tous mesurés
sur données réelles :

1. **Codons synonymes** d'un même acide aminé : embB Met306Ile via ATG→ATC est manqué quand
   seul ATG→ATT est catalogué. Correction : propagation AA (`analyses/aa_propagation.py`,
   intégrée au build du catalogue, source `<source>_AAprop`). La conversion AA → SPDI gère
   le brin du gène (validée sur katG Ser315Thr brin − et embB Met306Ile brin +).
   Gain baseline : **éthambutol +23 points** de sensibilité (0.63 → 0.86), +5 sur le
   pyrazinamide, spécificité quasi inchangée.
2. **Déterminants rares** élagués par le filtre de fréquence de la matrice de features.
   Correction : inclure de force les déterminants R catalogués observés (`phase4`).
3. **MNV (pangénome) contre SNP (catalogue)** sur la QRDR gyrA : le pangénome appelle des
   variants multi-bases que le catalogue, en SNP, ne croise jamais. Correction :
   **décomposition** des MNV en SNP composants (`variant_match.py`).
   Gain baseline : **moxifloxacine +55 points** (0.25 → 0.80), lévofloxacine +51 points.

**Règle qui en découle** : tout matching (baseline, exclusion, profil, prédiction) passe par
`variant_match` (`determinant_snp_set`, `carrier_columns`, `carries`), **jamais** par une
égalité SPDI brute. L'exclusion catalogue et le baseline déterministe se font au niveau AA,
pas seulement SPDI. Limite résiduelle : les indels (longueurs ref/alt différentes) ne sont
pas décomposables.

### Garde-fous transverses

- **Recherche, pas de diagnostic clinique.** Faire précéder tout profilage d'un sas QC
  (`species-id` anti-kansasii, `strain-qc`).
- **Causal contre co-résistance / linkage.** Une mutation peut être associée à un médicament
  uniquement parce que les souches porteuses sont MDR : rpoB Ser450Leu apparaît associé à
  l'isoniazide à 94 % par co-résistance seule, alors qu'il n'est causal que pour la
  rifampicine et la rifabutine, sa classe. L'association empirique par médicament, la
  cohérence gène ↔ cible et la littérature tranchent.
- **Garde-fou SAE** (documenté, rehumanisation_L6L9L10, 2026-05-30) : les deltas de features
  SAE n'ont **pas** de mapping validé à l'impact fonctionnel ; compter des features
  « flippées » n'est pas une preuve. Pour un score citable, utiliser le **LLR** (mode `llr`).
- **Marqueurs de lignée.** Un marqueur de lignée tombant dans un gène de résistance peut être
  une mutation R fondatrice de clone (règle gid / streptomycine) : ne pas l'exclure aveuglément.

---

## Mode 1 : Catalogue

Consultation et (re)construction du **catalogue consolidé mutation → résistance**, qui croise
quatre sources hétérogènes en une table longue unique, et du **pont HGVS → SPDI** qui rend les
variants croisables avec le pangénome du groupe. Le catalogue matérialisé
(`catalogue/catalogue_consolide.tsv`) compte environ 62 000 assertions, 21 médicaments et
37 800 SPDI uniques, résolus à 97 %.

```bash
S=scripts   # depuis le répertoire du skill
python3 $S/query_catalogue.py --stats
python3 $S/query_catalogue.py --variant katG_p.Ser315Thr
python3 $S/query_catalogue.py --spdi NC_000962.3:2155167:C:G
python3 $S/query_catalogue.py --drug isoniazid --call R-associated
python3 $S/query_catalogue.py --strain-spdi souche_spdi.txt --drug isoniazid   # baseline SPDI brut
python3 $S/hgvs_to_spdi.py katG_p.Ser315Thr        # -> NC_000962.3:2155167:C:G
python3 $S/hgvs_to_spdi.py --report                # couverture du résolveur
```

`--strain-spdi` reproduit la logique TB-Profiler (souche R si elle porte au moins un SPDI
R-associé catalogué pour le médicament), mais **sur SPDI brut et un seul médicament** : c'est
une version dégradée du mode 2, à ne garder que pour une vérification ponctuelle. Le baseline
publiable est celui de `resistance_profile.py`, réconcilié.

**Sortie** : lignes du catalogue avec grade, source et compteurs `n_R`/`n_S`.

### Interprétation des grades

Schéma de la table : `spdi gene variant drug drug_code call source source_grade n_R n_S metric notes`.

| `call` | grades sources (OMS / tb-profiler) | sens |
|---|---|---|
| `R-associated` | 1) Assoc w R ; 2) Assoc w R - Interim ; "Assoc w R" | associé à la résistance |
| `uncertain` | 3) Uncertain significance | signification incertaine |
| `S-associated` | 4)/5) Not assoc w R | non associé (souvent un marqueur de lignée neutre) |
| `empirical-enriched` | différentiel CRyPTIC (non curé, AMK) | signal brut, **biaisé MDR**, à ne pas traiter comme expert |

| source | fichier | assertions | notation |
|---|---|---|---|
| `WHO_catalogue` | `data/sources/who_catalogue/WHO-UCN-TB-2023.7-eng.xlsx` (feuille `Catalogue_master_file`) | 58 994 | HGVS, SPDI résolu à 100 % |
| `tbprofiler` | `data/sources/tbprofiler/tb-profiler-db.csv` | 2 523 | HGVS, SPDI résolu à 48 % |
| `CRyPTIC_empirical` | `résultats/resistance_ami.csv` | 500 | SPDI (AMK, non curé) |

### Le pont HGVS → SPDI

`hgvs_to_spdi.py` mappe `gene_mutation` (notation identique OMS et tb-profiler) vers le SPDI
**0-based** du groupe, via le fichier officiel de coordonnées génomiques OMS
(`WHO-UCN-TB-2023.7-eng_genomic_coordinates.txt`, **1-based**, d'où le décalage `-1`, validé
contre `pan_spdi.pkl`). Le fichier est téléchargé et mis en cache s'il est absent.
**Limites** : indels et MNV (environ 10 %) non croisables avec le pangénome SNP ; entrées
gène-niveau (LoF) de tb-profiler non résolues.

### Régénération après mise à jour d'une source

Reconstruction dans le projet, idempotente et journalisée :

```bash
cd "${RESISTANCE_PROJECT:-$HOME/docs/codes/mtbc/Resistance_antibio}"
.venv-ingest/bin/python update_database.py                   # sources + catalogue + phénotypes
.venv-ingest/bin/python analyses/phase1_build_catalogue.py   # catalogue seul (aa_propagation en fin)
```

---

## Mode 2 : Profil et prédiction

Prédicteur par médicament, à **deux étages** : le catalogue déterministe réconcilié SNP+MNV au
niveau AA (`variant_match`), très spécifique, puis un **XGBoost résiduel** sur les features
génomiques, qui capte le signal au-delà du catalogue et le contexte MDR.

```
prédiction(souche, médicament) =
    catalogue_carries(souche)            # déterministe, réconcilié SNP+MNV
    OU  XGBoost_proba(features) > seuil  # résiduel, seuil calibré
```

Le seuil ML se calibre selon le compromis visé (haute spécificité pour un usage confirmatoire,
haute sensibilité pour un dépistage de cohorte).

### Profilage déterministe autonome (`resistance_profile.py`)

L'étage déterministe est packagé en CLI autonome, sans réseau, souche unique ou cohorte :

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

**Sorties** : profil texte par médicament avec les déterminants touchés, `--json` pour la
sortie structurée, `--out` pour le TSV souche × médicament et son résumé de cohorte.

Le matching réconcilié capte les angles morts : un gyrA Asp94Gly présenté en MNV ressort « R »
aux fluoroquinolones, là où un matching SPDI brut le manque.

### Entraînement et évaluation

```bash
cd "${RESISTANCE_PROJECT:-$HOME/docs/codes/mtbc/Resistance_antibio}"
.venv-ingest/bin/python analyses/phase10_predict.py --drugs pyrazinamide,isoniazid --folds 5
# prérequis : phase4 (matrice), phase6 (masque), catalogue enrichi (phase1 + aa_propagation)
```

**Sortie** : par médicament, couple (sensibilité, spécificité) du baseline catalogue et du
combiné, AUC, et importances.

Principes d'évaluation honnête :

- **GroupKFold par lignée Coll** : le test tombe sur des lignées non vues, donc pas de fuite
  phylogénétique. Une CV aléatoire gonfle l'AUC de 0.02 à 0.04, mesuré.
- **Comparaison à spécificité égale** : le ML n'est utile que s'il gagne en sensibilité sans
  perdre en spécificité face au baseline. Rapporter le couple, pas une AUC seule.
- **Baseline = catalogue réconcilié.** Sans la réconciliation du socle, le baseline est
  sous-estimé (fluoroquinolones : 0.25 au lieu de 0.80) et le ML semble faussement utile.

### Explicabilité

Importance (gain) et SHAP donnent les variants qui pèsent le plus, annotés par gène, avec un
flag catalogué / hors-catalogue. Un variant hors-catalogue important n'est **pas** forcément
causal : il peut tracer le contexte MDR. Le confirmer par le mode 3 (GWAS et convergence) et
`mtbc-gene` (mode mutation) avant toute conclusion.

### Ce que le ML apporte, et où

Mesuré : là où le catalogue est complet (INH, RIF), le ML n'ajoute presque rien à spécificité
contrôlée. Là où il est incomplet (PZA, `pncA` très diverse), il porte un signal réel
(AUC environ 0.84) mais limité à haute spécificité, et capte surtout le contexte MDR. Le
prédicteur opérationnel reste donc catalogue-centré, le ML servant de filet pour les cas non
couverts, à condition d'expliciter le compromis sensibilité / spécificité.

---

## Mode 3 : Découverte hors catalogue

GWAS à **correction de structure**, conditionnée sur la **co-résistance**, validée par
**convergence phylogénétique**, pour les déterminants que le catalogue ne contient pas.
Le code exécuté vit dans le projet (`analyses/phase4`, `phase6`, `phase7`) ; le module
réutilisable `variant_match.py` est embarqué ici.

Prérequis absolu : l'ÉTAPE 0 du socle. Sans elle, la GWAS redécouvre du connu mal représenté.

**Étape 1, jeu de données** (`phase4_build_matrix.py`) : matrice creuse souche × SPDI sur les
souches phénotypées ayant des features (cascade pangénome ∪ `bdd/actuelle/`), plus les
métadonnées (phénotypes, lignée Coll). Inclut de force les déterminants R catalogués même
rares (angle mort 2).

**Étape 2, masque des features** : exclure du catalogue les déterminants R du médicament,
réconciliés SNP+MNV, pour ne pas redécouvrir le connu ; `phase6_feature_mask.py` exclut les
marqueurs de lignée (barcoding_v2, `role==positive`) sauf ceux tombant dans un gène de
résistance.

**Étape 3, GWAS** (`phase7_gwas_logistic.py`) : `logit(R ~ variant + PC1..20 + score_co-résistance)`
par variant candidat. Les 20 PC (TruncatedSVD de la matrice) absorbent la structure
phylogénétique ; le score de co-résistance (nombre d'autres médicaments avec déterminant R
porté, réconcilié) neutralise le confondant MDR ; pré-filtre χ² vectorisé puis régression
complète sur le top, FDR Benjamini-Hochberg.

**Étape 4, filtres anti-artefact** (décisifs) : la **convergence** d'abord, un déterminant
causal apparaissant dans plusieurs fonds génétiques alors qu'un marqueur de clone est
mono-lignée, d'où le rejet de `frac_top_sublineage > 0.6` ou `n_lineages <= 1` (sur
l'éthambutol, ce seul filtre fait tomber 264 hits à 2) ; puis la **direction**, en ne gardant
que `OR > 1`.

**Étape 5, validation d'un candidat** : homoplasie sur arbre (`convergent-evolution`, `pastml`,
`iqtree-lsd2`) pour compter les acquisitions indépendantes, impact protéique
(`mtbc-gene` mode mutation, ESM et LLR Meier 2021), littérature (`tbmonitor-papers`).

```bash
cd "${RESISTANCE_PROJECT:-$HOME/docs/codes/mtbc/Resistance_antibio}"
.venv-ingest/bin/python analyses/phase4_build_matrix.py                             # matrice
.venv-ingest/bin/python analyses/phase6_feature_mask.py                             # masque lignée
.venv-ingest/bin/python analyses/phase7_gwas_logistic.py --drug ethambutol           # découverte
.venv-ingest/bin/python analyses/phase7_gwas_logistic.py --drug isoniazid --sanity   # validation
```

**Sortie** : table de hits par variant (OR, p, q-value FDR, `n_lineages`,
`frac_top_sublineage`), avant et après filtres anti-artefact.

**Sanity de la machinerie** : `phase7 --drug isoniazid --sanity` (sans exclusion) doit
retrouver **fabG1/inhA** (OR environ 42) en tête. C'est la preuve que la GWAS remonte les
vrais signaux.

**Enseignement publiable** : sur les médicaments de première ligne bien catalogués, une fois
les angles morts corrigés, le catalogue capture l'essentiel de la résistance et le résiduel
hors-catalogue est faible. La découverte a du potentiel là où le catalogue est incomplet
(angle mort de représentation, ou résistance par mécanismes non-cible). La valeur du pipeline
est de distinguer un vrai déterminant convergent d'un artefact de clone ou de co-résistance.

---

## Mode 4 : Explication mécanistique

Dossier d'explication pour une mutation cataloguée ou candidate du mode 3, en orchestrant les
briques de l'écosystème et en **hiérarchisant les preuves**.

| Niveau | Source | Force |
|---|---|---|
| 1 | **Catalogue** WHO/tb-profiler (mode 1) : grade, médicament, `n_R`/`n_S` | preuve experte directe |
| 1 | **Association empirique** : taux R parmi les souches porteuses (dataset projet) | preuve directe sur données |
| 1 | **Littérature** TB (`tbmonitor-papers`, sinon `lit-review`) | preuve publiée |
| 2 | **LLR ESM-1v** (Meier 2021, via `mtbc-gene` mode mutation) | score variant-effect calibré |
| 3 | **Structure 3D** (ESMFold, `esm-atlas-cli`) : position du résidu, proximité site actif/poche | contexte structurel |
| 3 | **SAE feature deltas** (`mtbc-gene` mode mutation) | exploratoire, **ne PAS sur-interpréter** |

Orchestration en cinq étapes :

1. **Dossier local** (catalogue, association empirique, annotation) :
   ```bash
   cd "${RESISTANCE_PROJECT:-$HOME/docs/codes/mtbc/Resistance_antibio}"
   .venv-ingest/bin/python analyses/explain_mutation.py --variant rpoB_p.Ser450Leu
   ```
   **Sortie** : localisation (gène, codon), verdict catalogue par médicament (grade,
   `n_R`/`n_S`), et taux R parmi les souches porteuses pour chaque médicament.
2. **Littérature** via `tbmonitor-papers` (corpus PubMed TB d'environ 190 000 entrées,
   sub-seconde) :
   ```sql
   SELECT title, doi, publication_date FROM papers
   WHERE (title LIKE '%<gene>%' OR abstract LIKE '%<mutation>%')
     AND (abstract LIKE '%<medicine>%' OR title LIKE '%<medicine>%')
   ORDER BY publication_date DESC;
   ```
   Si le corpus pré-indexé ne donne rien, basculer sur `lit-review` (recherche live).
3. **Impact protéique** : `/mtbc-gene mutation <gene> <mutation>` donne le LLR ESM-1v
   (Meier 2021, score citable) et la fonction du gène.
4. **Structure 3D** : `esm-atlas-cli` pour récupérer la structure ESMFold du gène et situer le
   résidu muté (site actif, poche de liaison, interface). Contexte structurel, non quantitatif.
5. **Synthèse** : rédiger un paragraphe citable qui part des preuves fortes (catalogue,
   association, littérature), conforte par le LLR, illustre par la 3D, et conclut causal
   contre co-résistance.

**Mise à jour continue** : quand le mode 3 ou l'ingestion quotidienne fait émerger une nouvelle
mutation, cet enchaînement produit automatiquement son dossier mécanistique.

---

## Scripts embarqués et copie faisant foi

`scripts/` est plat : `query_catalogue.py` fait `from vocab import canonical_drug` et
`resistance_profile.py` fait `from variant_match import parse_spdi, decompose`, tous deux
résolus par le répertoire du script. Ne pas les déplacer en sous-répertoires.

Certains scripts existent aussi dans `Resistance_antibio/analyses/` et **ont divergé**. Avant
toute mise à jour, vérifier laquelle des deux copies fait foi, sinon le décalage sera silencieux :

| script | copie faisant foi | remarque |
|---|---|---|
| `hgvs_to_spdi.py` | **skill** | la version skill ajoute le téléchargement et le cache du fichier de coordonnées OMS, plus `--report` |
| `resistance_profile.py` | **skill** | version skill plus avancée que celle du projet |
| `vocab.py` | **skill** | vocabulaire des médicaments, diverge du projet |
| `variant_match.py` | identiques | socle de réconciliation SNP/MNV/AA, à garder synchronisé dans les deux sens |
| `explain_mutation.py` | **projet** | la copie embarquée fait `import paths` (module de la racine du projet, absent ici) : elle est de référence, **non exécutable depuis le skill**. Lancer la version projet, comme indiqué au mode 4 |

## Intégration avec d'autres skills

| Skill | Usage |
|---|---|
| `resistance-profiler` | fréquences de résistance **par lignée** depuis TBannotator ; granularité population, complémentaire de la granularité souche d'ici |
| `spdi-annotation` | annoter gène et effet des SPDI non catalogués |
| `mtbc-gene` (modes mutation, function, pathway) | impact protéique (ESM, LLR Meier 2021) d'un variant catalogué ou candidat ; fonction du gène ; voie métabolique |
| `esm-atlas-cli` | structure ESMFold pour le contexte 3D du mode 4 |
| `convergent-evolution`, `pastml`, `iqtree-lsd2` | homoplasie et acquisitions indépendantes d'un candidat |
| `tbmonitor-papers`, `lit-review` | le variant a-t-il déjà été décrit dans la littérature TB ? |
| `species-id`, `strain-qc` | sas QC obligatoire avant tout profilage |

## Dépendances

```bash
pip install pandas numpy scipy scikit-learn statsmodels xgboost
```

Le mode 1 et le profilage déterministe du mode 2 n'exigent que `pandas` ; `scikit-learn`,
`statsmodels` et `xgboost` ne servent qu'à la GWAS et à l'entraînement.
