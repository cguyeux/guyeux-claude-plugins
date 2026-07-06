---
name: resistance-profiler
description: >-
  Academic research toolkit. Computes published-literature-style summaries
  of antimicrobial-resistance allele frequencies across Mycobacterium
  tuberculosis complex (MTBC) lineages, by querying the curated TBannotator
  research database (Guyeux group, FEMTO-ST, University of Franche-Comte).
  Produces cross-tabulations and iTOL annotation files for peer-reviewed
  phylogenomic publications. To contextualise results in the published
  scientific literature, use the `tbmonitor-papers` skill in parallel
  (indexed corpus of ~190k PubMed TB research abstracts).

  Use when: writing a phylogenomics article that reports lineage-level
  AMR allele frequencies, producing supplementary tables/figures for a
  scientific publication, or generating iTOL annotation tracks for a
  peer-reviewed manuscript on MTBC evolution.
argument-hint: "<lineage or strain_sql> [--drugs RIF,INH,EMB,PZA] [--output table.csv]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres
---

# Resistance Profiler — Profil de résistance MTBC

Profil automatisé de résistance aux antituberculeux pour une collection de souches MTBC. Produit des tableaux de résistance, des cross-tabulations lignée × résistance, et des fichiers d'annotation iTOL.

## Phase 1 : Découverte (OBLIGATOIRE)

1. **Quelles souches ?** (lignée, pays, SQL, SRA IDs)
2. **Quels antibiotiques ?** (défaut : RIF, INH, EMB, PZA — les 4 first-line)
3. **Quel niveau de détail ?**
   - Phénotypique : `dr_type` (susceptible, mono-R, MDR, pre-XDR, XDR)
   - Génotypique : mutations individuelles (rpoB S450L, katG S315T, etc.)
   - Les deux (recommandé pour articles)
4. **Sorties souhaitées ?**
   - Tableau résumé (CSV)
   - Cross-tabulation lignée × résistance
   - Dataset iTOL binaire
   - Tableau supplémentaire article (mutations détaillées)

## Phase 2 : Extraction des données

> **Source de vérité (cf. `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`)** : dans TBannotator, `system='Senelle'` EST le système maison (= moi/Guyeux), mais c'est un **snapshot** susceptible d'être en retard sur la taxonomie vivante. Ici l'usage (fréquences d'allèles sur des lignées déjà assignées) n'est pas fautif ; c'est seulement une précaution sur la fraîcheur du label. Pour tout clade récent du cycle multi-signal (L1.\*, Bovis1.\*, BCG.\*, L6 profond), recouper le label avec `bdd/actuelle/` + `barcoding_v2/barcode_complete.tsv`. Ne jamais lire `snp_barcoding.csv` (v1 obsolète) ni `strain_lineages.csv` (périmé) comme référence taxonomique.

### Profil phénotypique (dr_type)

```sql
-- Distribution des types de résistance pour une lignée
SELECT m.dr_type, COUNT(*) as n,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as pct
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.sra_id
WHERE c.system = 'Senelle' AND c.lineage_code LIKE '4.15%'
  AND m.dr_type IS NOT NULL
GROUP BY m.dr_type
ORDER BY n DESC;
```

### Cross-tabulation sous-lignée × résistance

```sql
-- Résistance par sous-lignée
SELECT c.lineage_code, m.dr_type, COUNT(*) as n
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.sra_id
WHERE c.system = 'Senelle' AND c.lineage_code LIKE '4.15%'
  AND m.dr_type IS NOT NULL
GROUP BY c.lineage_code, m.dr_type
ORDER BY c.lineage_code, m.dr_type;
```

### Profil génotypique (mutations de résistance)

```sql
-- Mutations dans les gènes de résistance WHO
SELECT p.sra_id, p.gene, p.aa_change, p.effect
FROM mv_protein_position_mutations p
JOIN mv_strain_classification c ON p.sra_id = c.sra_id
WHERE c.system = 'Senelle' AND c.lineage_code LIKE '4.15%'
  AND p.gene IN ('rpoB', 'katG', 'inhA', 'embB', 'pncA', 'rpsL',
                  'rrs', 'gyrA', 'gyrB', 'ethA', 'tlyA')
ORDER BY p.sra_id, p.gene;
```

### Gènes de résistance par antibiotique

| Antibiotique | Gènes principaux | Mutations sentinelles |
|-------------|-------------------|----------------------|
| Rifampicine (RIF) | `rpoB` | S450L (>95% RIF-R) |
| Isoniazide (INH) | `katG`, `inhA` promoteur | S315T (~65% INH-R) |
| Ethambutol (EMB) | `embB` | M306V/I/L |
| Pyrazinamide (PZA) | `pncA` | Très divers (>600 mutations) |
| Streptomycine (SM) | `rpsL`, `rrs` | K43R, K88R |
| Fluoroquinolones (FQ) | `gyrA`, `gyrB` | D94G/N/A/Y |
| Aminoglycosides | `rrs`, `tlyA` | a1401g, c1402t |
| Ethionamide (ETH) | `ethA`, `inhA` | Divers |

## Phase 3 : Génération des sorties

### Tableau résumé CSV

```csv
lineage,total,susceptible,mono_R,poly_R,MDR,pre_XDR,XDR,pct_any_R
4.15,523,412,45,12,38,10,6,21.2
4.15.1,210,180,12,3,10,3,2,14.3
4.15.2,313,232,33,9,28,7,4,25.9
```

### Dataset binaire iTOL

Générer un fichier `02_resistance.txt` au format DATASET_BINARY :

```
DATASET_BINARY
SEPARATOR TAB
DATASET_LABEL	Drug Resistance
COLOR	#ff0000
FIELD_SHAPES	2	2	2	2
FIELD_LABELS	RIF	INH	EMB	PZA
FIELD_COLORS	#ff0000	#ff6600	#0066ff	#009933
LEGEND_TITLE	Drug Resistance
LEGEND_SHAPES	2	2
LEGEND_COLORS	#333333	#cccccc
LEGEND_LABELS	Resistant	Susceptible
DATA
ERR551415	1	1	0	0
SRR33638270	0	0	0	0
```

### Tableau supplémentaire article

Format pour supplément :

```csv
strain_id,lineage,dr_type,rpoB,katG,inhA,embB,pncA,gyrA,rpsL,rrs
ERR551415,4.15.1,MDR,S450L,S315T,,,,,
SRR33638270,4.15.2,susceptible,,,,,,,
```

## Phase 4 : Analyse

### Statistiques calculées par le script

```bash
python3 scripts/resistance_profiler.py strains_metadata.csv \
  -o summary.csv --itol resistance.txt --supplement supplement.csv
```

Le script calcule :
- Prévalence de résistance par sous-lignée avec IC95 (binomial exact)
- Test de Fisher exact pour comparer les taux entre sous-lignées
- Odds ratio (ex. L4.15.2 vs L4.15.1 pour MDR)

### Interprétation

| Indicateur | Seuil | Interprétation |
|-----------|-------|----------------|
| Taux MDR > 5% | Élevé | Lignée à surveiller |
| MDR + FQ-R | pre-XDR | Alerte clinique |
| MDR + FQ-R + injectables-R | XDR | Urgence |
| Taux R significativement différent entre sous-lignées | p < 0.05 (Fisher) | Association lignée-résistance |

## Intégration avec d'autres skills

| Skill | Usage |
|-------|-------|
| `itol` | Ajouter le dataset binaire résistance sur la phylogénie |
| `lineage-comparison` | Tests statistiques avancés (FDR, régression) |
| `phylogeography` | Corrélation résistance × géographie |
| `tbannotator-mcp` | Source des données de résistance |

## Dépendances

```bash
pip install pandas numpy scipy
```
