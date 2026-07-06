---
name: resistance-catalogue
description: >-
  Academic research toolkit for the Guyeux group (FEMTO-ST, University of
  Franche-Comté) MTBC pipeline: query and (re)build a consolidated
  mutation-to-antimicrobial-resistance reference catalogue for the
  Mycobacterium tuberculosis complex, cross-referencing the WHO catalogue of
  mutations (2nd ed., 2023), the tb-profiler reference database, and empirical
  CRyPTIC signal. Resolves HGVS variant notation (gene_mutation) to the
  project's 0-based SPDI coordinates via the official WHO genomic-coordinates
  file, and returns, for a given variant or antitubercular medicine, the
  catalogued association grade and its provenance, for peer-reviewed
  phylogenomic and AMR-evolution publications. Pairs with `tbmonitor-papers`
  to check whether a variant has prior coverage in the published TB literature.

  Use when: looking up the WHO/tb-profiler association grade of a variant,
  listing the catalogued markers of a medicine, computing a deterministic
  catalogue-based baseline for a strain (TB-Profiler-like), converting HGVS to
  SPDI, or regenerating the consolidated catalogue after a source update.
argument-hint: "<--variant katG_p.Ser315Thr | --drug isoniazid | --spdi NC_000962.3:2155167:C:G | --stats>"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# Resistance Catalogue — catalogue consolidé mutation → résistance (MTBC)

Outil de consultation et de (re)construction du **catalogue consolidé
mutation → résistance** du groupe Guyeux, qui croise quatre sources hétérogènes
en une table longue unique, et du **pont HGVS → SPDI** qui rend les variants
croisables avec le pangénome du groupe.

Le catalogue matérialisé vit dans le projet `Resistance_antibio`
(`catalogue/catalogue_consolide.tsv`, ~62 000 assertions, 21 médicaments,
~37 800 SPDI uniques, 97 % résolus en SPDI). Ce skill l'interroge ; il ne
duplique pas les données. Variable d'environnement `RESISTANCE_PROJECT` pour
pointer une autre racine (défaut : `~/docs/codes/mtbc/Resistance_antibio`).

## Distinction fondamentale (à garder en tête)

Ce catalogue est un **savoir au niveau mutation** (variant → médicament → verdict),
c'est-à-dire un prédicteur **déterministe** de type TB-Profiler. Il ne faut pas le
confondre avec l'apprentissage : un modèle prédictif n'a d'intérêt que **hors
catalogue** (cf. skill `resistance-discovery`). Ici on consulte et on construit la
référence ; on s'en sert comme **baseline déterministe** à battre.

## Phase 1 : Découverte (que cherche-t-on ?)

1. **Une mutation précise** → son grade de confiance et sa provenance (`--variant` HGVS, ou `--spdi`).
2. **Un médicament** → ses variants catalogués (`--drug`, filtrable par `--call`).
3. **Une souche** (liste de SPDI) → verdict déterministe par médicament (`--strain-spdi --drug`).
4. **Convertir** une notation HGVS en SPDI 0-based (`hgvs_to_spdi.py`).
5. **Régénérer** le catalogue après mise à jour d'une source (voir Phase 4).

## Phase 2 : Consultation

```bash
S=scripts   # depuis le répertoire du skill
python3 $S/query_catalogue.py --stats
python3 $S/query_catalogue.py --variant katG_p.Ser315Thr
python3 $S/query_catalogue.py --spdi NC_000962.3:2155167:C:G
python3 $S/query_catalogue.py --drug isoniazid --call R-associated
python3 $S/query_catalogue.py --strain-spdi souche_spdi.txt --drug isoniazid   # baseline déterministe
python3 $S/hgvs_to_spdi.py katG_p.Ser315Thr        # -> NC_000962.3:2155167:C:G
python3 $S/hgvs_to_spdi.py --report                # couverture du résolveur
```

`--strain-spdi` reproduit la logique TB-Profiler : la souche est dite R si elle
porte au moins un SPDI R-associé catalogué pour le médicament. C'est le baseline
de référence pour évaluer tout modèle (cf. `resistance-predict`).

## Phase 3 : Interprétation des grades

Schéma de la table : `spdi gene variant drug drug_code call source source_grade n_R n_S metric notes`.

| `call` | grades sources (OMS / tb-profiler) | sens |
|---|---|---|
| `R-associated` | 1) Assoc w R ; 2) Assoc w R - Interim ; "Assoc w R" | associé à la résistance |
| `uncertain` | 3) Uncertain significance | signification incertaine |
| `S-associated` | 4)/5) Not assoc w R | non associé (souvent un marqueur de lignée neutre) |
| `empirical-enriched` | différentiel CRyPTIC (non curé, AMK) | signal brut, **biaisé MDR**, à ne pas traiter comme expert |

Sources et fiabilité :

| source | fichier | assertions | notation |
|---|---|---|---|
| `WHO_catalogue` | `data/sources/who_catalogue/WHO-UCN-TB-2023.7-eng.xlsx` (feuille `Catalogue_master_file`) | 58 994 | HGVS, SPDI résolu à 100 % |
| `tbprofiler` | `data/sources/tbprofiler/tb-profiler-db.csv` | 2 523 | HGVS, SPDI résolu à 48 % |
| `CRyPTIC_empirical` | `résultats/resistance_ami.csv` | 500 | SPDI (AMK, non curé) |

## Phase 4 : Régénération / mise à jour

Le catalogue se reconstruit dans le projet `Resistance_antibio` (idempotent, journalisé) :

```bash
cd "${RESISTANCE_PROJECT:-$HOME/docs/codes/mtbc/Resistance_antibio}"
.venv-ingest/bin/python update_database.py            # fetch sources + reconstruit catalogue + phénotypes
.venv-ingest/bin/python analyses/phase1_build_catalogue.py   # catalogue seul
```

## Propagation au niveau acide aminé (codons synonymes)

Le catalogue est **enrichi au niveau acide aminé** : pour chaque variant missense
R-associated, tous les SPDI mono-base produisant le **même changement d'AA** (codons
synonymes) sont ajoutés (source `<source>_AAprop`). Cela comble un angle mort des
catalogues SPDI-indexés : un déterminant connu via un codon (ex. embB Met306Ile par
ATG→ATT) était manqué via un codon synonyme (ATG→ATC), pourtant même AA et même
résistance. Impact mesuré : **+23 points de sensibilité sur l'éthambutol** (0.63→0.86),
+5 sur le pyrazinamide, spécificité quasi inchangée. La conversion AA→SPDI gère le brin
du gène (validée sur katG Ser315Thr brin − et embB Met306Ile brin +). Implémentée dans
`analyses/aa_propagation.py` (projet), appliquée en fin de `phase1_build_catalogue.py`.
Conséquence : faire l'exclusion catalogue et le baseline déterministe au niveau AA, pas
seulement SPDI.

## Le pont HGVS → SPDI

`hgvs_to_spdi.py` mappe `gene_mutation` (notation identique OMS et tb-profiler) → SPDI
**0-based** du groupe, via le fichier officiel de coordonnées génomiques OMS
(`WHO-UCN-TB-2023.7-eng_genomic_coordinates.txt`, **1-based** → décalage `-1`, validé
contre `pan_spdi.pkl`). Le fichier est téléchargé et mis en cache si absent.
**Limites** : indels/MNV (~10 %) non croisables avec le pangénome SNP ; entrées
gène-niveau (LoF) de tb-profiler non résolues.

## Intégration avec d'autres skills

| Skill | Usage |
|---|---|
| `resistance-discovery` | découverte de déterminants **hors** catalogue (GWAS modèle mixte) ; ce skill fournit la liste à exclure |
| `resistance-predict` | prédiction par médicament ; ce skill fournit le baseline déterministe |
| `spdi-annotation` | annoter gène/effet des SPDI non catalogués |
| `mtbc-mutation-impact` | impact protéique (ESM, LLR Meier) d'un variant catalogué ou candidat |
| `tbmonitor-papers` | un variant a-t-il déjà été décrit dans la littérature TB ? |

## Dépendances

```bash
pip install pandas
```
