---
name: lineage-comparison
description: >-
  Statistical comparison between MTBC lineages or sub-lineages.
  Fisher exact test, chi-squared, binomial exact CI, FDR correction,
  odds ratios, and publication-ready comparison tables.

  Use when: comparing resistance rates between lineages, testing if a trait
  is significantly associated with a sub-lineage, producing statistical
  tables for articles, computing confidence intervals.
argument-hint: "<data.csv> --group lineage --variable dr_type [--test fisher|chi2]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres
---

# Lineage Comparison — Comparaison statistique MTBC

Tests statistiques pour comparer des traits (résistance, géographie, mutations) entre lignées ou sous-lignées MTBC. Produit des tableaux publication-ready avec IC95 et p-values corrigées.

## Phase 1 : Découverte (OBLIGATOIRE)

1. **Quels groupes comparer ?**
   - Deux sous-lignées (ex. L4.15.1 vs L4.15.2)
   - Plusieurs sous-lignées (ex. toutes les sous-lignées de L4)
   - Lignée vs reste du MTBC
   - Deux pays/régions pour une même lignée

2. **Quelle variable ?**
   - Résistance (dr_type, mutation spécifique)
   - Géographie (pays, continent)
   - Trait binaire (présence/absence d'un gène, SPDI)
   - Variable continue (nombre de SNPs, THD)

3. **Quel test ?**
   - **Fisher exact** (défaut pour 2×2) : petits effectifs, exact
   - **Chi-squared** : grands effectifs, >2 catégories
   - **Binomial exact** : IC95 pour une proportion
   - **Mann-Whitney U** : variable continue, 2 groupes
   - **Kruskal-Wallis** : variable continue, >2 groupes

4. **Correction pour tests multiples ?**
   - **Benjamini-Hochberg FDR** (défaut) : contrôle le taux de faux positifs
   - **Bonferroni** : plus conservateur
   - Aucune (test unique)

## Phase 2 : Extraction des données

### Depuis TBannotator

```sql
-- Données pour comparaison résistance entre sous-lignées
SELECT c.lineage_code as lineage,
       m.dr_type,
       m.country,
       COUNT(*) as n
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.sra_id
WHERE c.system = 'Senelle' AND c.lineage_code LIKE '4.15%'
GROUP BY c.lineage_code, m.dr_type, m.country;
```

> **Source de vérité (cf. `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`)** : dans TBannotator, `system='Senelle'` EST le système maison (= moi/Guyeux), mais c'est un **snapshot** susceptible d'être en retard sur la taxonomie vivante. Pour tout clade récent du cycle multi-signal (L1.\*, Bovis1.\*, BCG.\*, L6 profond), recouper le label avec `bdd/actuelle/` + `barcoding_v2/barcode_complete.tsv`. Ne jamais lire `snp_barcoding.csv` (v1 obsolète) ni `strain_lineages.csv` (périmé) comme référence taxonomique.

### Depuis un CSV

```csv
strain_id,lineage,dr_type,country,has_mutation_X
ERR551415,4.15.1,susceptible,France,0
SRR33638270,4.15.2,MDR,Germany,1
```

## Phase 3 : Tests statistiques

### Script principal

```bash
python3 scripts/lineage_comparison.py data.csv \
  --group lineage --variable dr_type \
  --test fisher --fdr bh \
  -o comparison_results.csv
```

### Tests disponibles

#### 1. Comparaison de proportions (2×2)

Pour chaque paire de lignées, test de Fisher exact sur un trait binaire (ex. MDR oui/non).

| | MDR | Non-MDR | Total |
|---|---|---|---|
| L4.15.1 | a | b | a+b |
| L4.15.2 | c | d | c+d |

- **Fisher exact** : p-value exacte
- **Odds ratio** : OR = (a×d)/(b×c), IC95 exact
- **Différence de proportions** : Δp = a/(a+b) - c/(c+d), IC95 Wald

#### 2. Tableau de contingence (r×c)

Pour >2 groupes ou >2 catégories : test du chi² avec correction de Yates si nécessaire.

```
Chi² = Σ (O - E)² / E
df = (r-1)(c-1)
```

Post-hoc : résidus standardisés ajustés pour identifier les cellules contribuant le plus.

#### 3. Intervalles de confiance binomiaux

Pour chaque proportion (ex. taux MDR d'une sous-lignée) :

- **Clopper-Pearson** (exact, recommandé) : `scipy.stats.binom.ppf`
- **Wilson** (recommandé n < 30) : correction de continuité
- **Wald** (pour référence) : approximation normale, déconseillé si p proche de 0 ou 1

#### 4. Variables continues

- **Mann-Whitney U** : 2 groupes (ex. THD de L4.15.1 vs L4.15.2)
- **Kruskal-Wallis** : >2 groupes
- Post-hoc **Dunn** avec correction FDR

### Correction FDR

Quand on fait N comparaisons (ex. 10 sous-lignées × 4 antibiotiques = 40 tests) :

```python
from scipy.stats import false_discovery_control
# ou
from statsmodels.stats.multitest import multipletests
reject, pvals_corrected, _, _ = multipletests(pvals, method='fdr_bh')
```

## Phase 4 : Sortie

### Tableau de résultats CSV

```csv
group_1,group_2,variable,n_1,n_2,prop_1,prop_2,ci95_1_lo,ci95_1_hi,ci95_2_lo,ci95_2_hi,odds_ratio,or_ci95_lo,or_ci95_hi,p_value,p_adjusted,significant
4.15.1,4.15.2,MDR,210,313,0.048,0.089,0.024,0.085,0.061,0.127,1.96,0.85,4.51,0.112,0.224,no
4.15.1,4.15.2,any_R,210,313,0.143,0.259,0.098,0.197,0.211,0.312,2.11,1.35,3.29,0.001,0.004,yes
```

### Résumé JSON (stdout)

```json
{
  "n_comparisons": 8,
  "n_significant_raw": 3,
  "n_significant_fdr": 2,
  "fdr_method": "benjamini-hochberg",
  "alpha": 0.05,
  "comparisons": [...]
}
```

### Tableau article (format LaTeX-ready)

Le script peut produire un tableau formaté pour inclusion dans un article :

```
Sub-lineage | n   | MDR (%, 95% CI)      | Any R (%, 95% CI)     | p (FDR)
4.15.1      | 210 | 4.8 (2.4-8.5)        | 14.3 (9.8-19.7)      | ref
4.15.2      | 313 | 8.9 (6.1-12.7)       | 25.9 (21.1-31.2)     | 0.004*
```

## Guide : quel test choisir ?

| Situation | Test | Conditions |
|-----------|------|------------|
| 2 lignées, trait binaire | Fisher exact | Toujours (exact, pas d'approximation) |
| >2 lignées, trait binaire | Chi² + post-hoc Fisher | n attendus > 5 dans chaque cellule |
| 2 lignées, variable continue | Mann-Whitney U | Distribution non-normale (fréquent en génomique) |
| >2 lignées, variable continue | Kruskal-Wallis + Dunn | Idem |
| IC d'une proportion | Clopper-Pearson | Toujours (exact) |
| Tests multiples | FDR Benjamini-Hochberg | Défaut. Bonferroni si très conservateur |

## Intégration

| Skill | Usage |
|-------|-------|
| `resistance-profiler` | Fournit les données de résistance par lignée |
| `phylogeography` | Fournit les données géographiques pour comparaison |
| `tbannotator-mcp` | Source directe des données |
| `thd` | Variable continue à comparer entre lignées |

## Dépendances

```bash
pip install pandas numpy scipy statsmodels
```
