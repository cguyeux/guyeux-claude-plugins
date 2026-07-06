---
name: phylogeography
description: >-
  Academic research toolkit for the Guyeux group (FEMTO-ST, University of Franche-Comte). Geographic-distribution analysis of published-research MTBC lineages for peer-reviewed phylogeographic publications. Geographic distribution analysis of MTBC lineages via TBannotator.
  Cross-tabulation country × lineage, choropleth maps, stacked barplots,
  and geographic diversity indices. To find prior phylogeographic
  studies on a lineage or country (and cite them in the article), pair
  with `tbmonitor-papers` — search by country name + lineage code in
  title/abstract against the pre-indexed PubMed TB corpus.

  Use when: mapping the geographic distribution of a lineage for an article,
  comparing geographic structure between sub-lineages, producing distribution
  figures and supplementary tables, identifying geographic hotspots.
argument-hint: "<lineage or strain_sql> [-o distribution.csv] [-p map.png]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres
---

# Phylogeography — Distribution géographique MTBC

Analyse de la distribution géographique des lignées MTBC. Produit des tableaux pays × lignée, des cartes choroplèthes, et des barplots empilés pour articles.

## Phase 1 : Découverte (OBLIGATOIRE)

1. **Quelle lignée ?** (ex. L4.15, L2, toutes les L4)
2. **Quel niveau géographique ?**
   - Pays (défaut, données les plus complètes)
   - Continent/région (agrégation)
   - Combinaison (pays + continent pour le barplot)
3. **Quel type de figure ?**
   - **Barplot empilé** (pays par proportion de sous-lignées) — le plus courant en article
   - **Carte choroplèthe** (coloration des pays par prévalence)
   - **Heatmap** (pays × sous-lignée, intensité = proportion)
   - Tableau seul (pas de figure)
4. **Filtres ?**
   - Minimum de souches par pays (défaut : 5)
   - Exclure les pays avec données insuffisantes
   - Période de collecte (ex. 2010-2024)

## Phase 2 : Extraction des données

### Distribution pays × lignée

```sql
-- Distribution géographique d'une lignée
SELECT m.country, c.lineage_code, COUNT(*) as n
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.sra_id
WHERE c.system = 'Senelle' AND c.lineage_code LIKE '4.15%'
  AND m.country IS NOT NULL AND m.country != ''
GROUP BY m.country, c.lineage_code
ORDER BY n DESC;
```

### Avec proportions

```sql
-- Proportions par pays (pour barplot empilé)
WITH country_totals AS (
  SELECT m.country, COUNT(*) as total
  FROM mv_strain_metadata m
  JOIN mv_strain_classification c ON m.strain_id = c.sra_id
  WHERE c.system = 'Senelle' AND c.lineage_code LIKE '4.15%'
    AND m.country IS NOT NULL AND m.country != ''
  GROUP BY m.country
  HAVING COUNT(*) >= 5
)
SELECT m.country, c.lineage_code, COUNT(*) as n,
       ct.total,
       ROUND(100.0 * COUNT(*) / ct.total, 1) as pct
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.sra_id
JOIN country_totals ct ON m.country = ct.country
WHERE c.system = 'Senelle' AND c.lineage_code LIKE '4.15%'
GROUP BY m.country, c.lineage_code, ct.total
ORDER BY ct.total DESC, m.country, c.lineage_code;
```

### Contexte : proportion de la lignée parmi toutes les souches d'un pays

```sql
-- Quelle fraction du TB national est L4.15 ?
WITH country_all AS (
  SELECT m.country, COUNT(*) as total_all
  FROM mv_strain_metadata m
  JOIN mv_strain_classification c ON m.strain_id = c.sra_id
  WHERE c.system = 'Senelle' AND m.country IS NOT NULL
  GROUP BY m.country
  HAVING COUNT(*) >= 20
),
country_target AS (
  SELECT m.country, COUNT(*) as n_target
  FROM mv_strain_metadata m
  JOIN mv_strain_classification c ON m.strain_id = c.sra_id
  WHERE c.system = 'Senelle' AND c.lineage_code LIKE '4.15%'
    AND m.country IS NOT NULL
  GROUP BY m.country
)
SELECT a.country, COALESCE(t.n_target, 0) as n_target, a.total_all,
       ROUND(100.0 * COALESCE(t.n_target, 0) / a.total_all, 2) as pct_of_total
FROM country_all a
LEFT JOIN country_target t ON a.country = t.country
ORDER BY pct_of_total DESC;
```

## Phase 3 : Génération des figures

### Script principal

```bash
python3 scripts/phylogeography.py distribution.csv \
  --type barplot --min-strains 5 \
  -o summary.csv -p distribution.png --title "L4.15 geographic distribution"
```

### Barplot empilé (le plus courant)

Axes :
- X : pays (triés par nombre total décroissant)
- Y : proportion (0-100%)
- Couleurs : sous-lignées (dégradé dans la teinte parente)
- Annotation : nombre total au-dessus de chaque barre

### Carte choroplèthe

Coloration des pays par prévalence de la lignée d'intérêt. Nécessite `geopandas` + `naturalearth` shapefiles.

### Heatmap pays × sous-lignée

Matrice colorée par proportion, avec dendrogramme de clustering hiérarchique sur les lignes (pays) et colonnes (sous-lignées).

## Phase 4 : Indices de diversité géographique

### Calculés par le script

| Indice | Formule | Interprétation |
|--------|---------|----------------|
| **Shannon** | H = -Σ pᵢ ln(pᵢ) | Diversité géographique (0 = 1 pays, élevé = cosmopolite) |
| **Simpson** | D = 1 - Σ pᵢ² | Probabilité que 2 souches soient de pays différents |
| **Nombre effectif de pays** | exp(H) | Équivalent en pays équi-fréquents |
| **Pays dominant** | max(pᵢ) | Fraction du pays le plus représenté |

### Comparaison entre lignées

```json
{
  "lineage": "4.15",
  "n_strains": 523,
  "n_countries": 34,
  "shannon_diversity": 2.87,
  "simpson_diversity": 0.89,
  "effective_countries": 17.6,
  "dominant_country": "India",
  "dominant_pct": 18.3
}
```

## Biais d'échantillonnage — ATTENTION

Les données TBannotator reflètent les séquençages publiés, pas la vraie prévalence. Biais connus :

| Biais | Impact | Mitigation |
|-------|--------|------------|
| Sur-représentation UK/USA | Gonfle la proportion occidentale | Mentionner dans article, normaliser par pays |
| Sous-représentation Afrique | Sous-estime lignées africaines (L5, L6) | Citer comme limitation |
| Biais MDR | Études de résistance → sur-représentation MDR | Séparer analyses résistance/géo |
| Projets mono-pays | Un gros projet peut dominer | Vérifier les BioProjects dominants |

**Recommandation article** : toujours inclure une phrase comme *"Geographic distributions should be interpreted with caution given sampling biases inherent to public sequence databases."*

## Régions géographiques OMS

Pour agréger par continent/région :

| Région OMS | Pays principaux (TB) |
|-----------|---------------------|
| AFR | South Africa, Ethiopia, Nigeria, DR Congo, Kenya |
| AMR | Peru, Brazil, USA, Mexico, Colombia |
| SEAR | India, Indonesia, Bangladesh, Myanmar, Thailand |
| EUR | UK, Russia, Germany, France, Romania |
| EMR | Pakistan, Afghanistan, Somalia, Sudan, Iraq |
| WPR | China, Philippines, Vietnam, Papua New Guinea, Japan |

## Intégration

| Skill | Usage |
|-------|-------|
| `tbannotator-mcp` | Source des données géographiques |
| `lineage-comparison` | Tests statistiques (Fisher) sur distribution pays |
| `resistance-profiler` | Corrélation résistance × géographie |
| `itol` | Color strip pays sur la phylogénie |
| `create-viz` | Figures supplémentaires personnalisées |

## Dépendances

```bash
pip install pandas numpy matplotlib seaborn
# Optionnel pour cartes :
pip install geopandas
```
