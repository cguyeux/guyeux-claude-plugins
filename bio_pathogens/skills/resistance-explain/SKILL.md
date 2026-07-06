---
name: resistance-explain
description: >-
  Academic research toolkit for the Guyeux group (FEMTO-ST, University of
  Franche-Comté) MTBC pipeline: explain the mechanism of a catalogued or
  candidate antimicrobial-resistance mutation in the Mycobacterium tuberculosis
  complex, by assembling, into one citable mechanistic dossier, the curated
  catalogue verdict (`resistance-catalogue`), the empirical phenotype association
  observed in the project strains, the published TB literature on the variant
  (`tbmonitor-papers` / `lit-review`), a protein-language-model variant-effect
  score (ESM-1v log-likelihood ratio, Meier et al. 2021, via `mtbc-mutation-impact`),
  gene function (`mtbc-gene-function`) and 3D structural context (ESMFold via
  `esm-atlas-cli`). For peer-reviewed phylogenomic and AMR-evolution publications.

  Use when: explaining why a variant confers (or might confer) resistance,
  interpreting a candidate from `resistance-discovery`, drafting the mechanistic
  paragraph of a manuscript, or distinguishing a causal determinant from a
  co-resistance / lineage-linkage artefact.
argument-hint: "<--variant rpoB_p.Ser450Leu | --spdi NC_000962.3:761154:C:T>"
user-invocable: true
allowed-tools: Bash, Read, Write, mcp__tbmonitor__execute_sql, mcp__tbannotator__tool_query_postgres
---

# Resistance Explain — explication mécanistique d'une mutation (MTBC)

Produit un dossier d'explication mécanistique pour une mutation de résistance
(catalogue connu ou candidat de `resistance-discovery`), en orchestrant les briques
existantes de l'écosystème et en **hiérarchisant les preuves**.

## Hiérarchie de preuve (à respecter)

| Niveau | Source | Force |
|---|---|---|
| 1 | **Catalogue** WHO/tb-profiler (`resistance-catalogue`) : grade, médicament, n_R/n_S | preuve experte directe |
| 1 | **Association empirique** : taux R parmi les souches porteuses (dataset projet) | preuve directe sur données |
| 1 | **Littérature** TB (`tbmonitor-papers`, sinon `lit-review`) | preuve publiée |
| 2 | **LLR ESM-1v** (Meier 2021, via `mtbc-mutation-impact`) | score variant-effect calibré |
| 3 | **Structure 3D** (ESMFold, `esm-atlas-cli`) : position du résidu, proximité site actif/poche | contexte structurel |
| 3 | **SAE feature deltas** (`mtbc-mutation-impact`) | exploratoire — **ne PAS sur-interpréter** |

Garde-fou (documenté, rehumanisation_L6L9L10 2026-05-30) : les deltas de features SAE
n'ont **pas** de mapping validé à l'impact fonctionnel ; compter des features « flippées »
n'est pas une preuve. Pour un score citable, utiliser le **LLR** (mode `llr`).

Distinguer toujours **causal** vs **co-résistance/linkage** : une mutation peut être
associée à la résistance à un médicament uniquement parce que les souches qui la portent
sont MDR (ex. rpoB Ser450Leu apparaît associé à l'INH à 94 % par co-résistance, alors
qu'il n'est causal que pour la rifampicine et la rifabutine, sa classe). L'association
empirique par médicament + la cohérence gène↔cible + la littérature tranchent.

## Orchestration

### 1. Dossier local (catalogue + association empirique + annotation)
```bash
cd "${RESISTANCE_PROJECT:-$HOME/docs/codes/mtbc/Resistance_antibio}"
.venv-ingest/bin/python analyses/explain_mutation.py --variant rpoB_p.Ser450Leu
```
Donne : localisation (gène, codon), verdict catalogue par médicament (grade, n_R/n_S),
et taux R parmi les souches porteuses pour chaque médicament (association empirique).

### 2. Littérature (le « lit-review quand une mutation apparaît »)
`tbmonitor-papers` (corpus PubMed TB ~190 k, sub-seconde) :
```sql
SELECT title, doi, publication_date FROM papers
WHERE (title LIKE '%<gene>%' OR abstract LIKE '%<mutation>%')
  AND (abstract LIKE '%<medicine>%' OR title LIKE '%<medicine>%')
ORDER BY publication_date DESC;
```
Si rien dans le corpus pré-indexé, basculer sur `lit-review` (recherche live).

### 3. Impact protéique (world model ESM)
`/mtbc-mutation-impact <gene> <mutation>` → LLR ESM-1v (Meier 2021, score citable) +
fonction du gène. C'est le « world model atlas » : un modèle de langage protéique qui
score la plausibilité fonctionnelle de la substitution.

### 4. Structure 3D
`esm-atlas-cli` : récupérer la structure ESMFold du gène, situer le résidu muté
(proximité du site actif, de la poche de liaison du médicament, d'une interface).
Contexte structurel, à présenter comme tel (non quantitatif).

### 5. Synthèse
Rédiger un paragraphe citable qui part des preuves fortes (catalogue + association +
littérature), conforte par le LLR, et illustre par la 3D. Conclure causal vs
co-résistance.

## Mise à jour continue

Ce skill est le maillon « explication » du volet *mise à jour continue* du projet :
quand `resistance-discovery` ou l'ingestion quotidienne fait émerger une nouvelle
mutation, l'enchaînement ci-dessus produit automatiquement son dossier mécanistique.

## Intégration

`resistance-catalogue` (verdict), `resistance-discovery` (candidats), `tbmonitor-papers`
/ `lit-review` (littérature), `mtbc-mutation-impact` + `mtbc-gene-function` +
`mtbc-pathway-explain` (ESM, fonction, voie), `esm-atlas-cli` (3D), `spdi-annotation`
(effet).

## Dépendances

```bash
pip install pandas numpy scipy
```
