---

name: phylogeography
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST): geographic distribution of
  MTBC lineages via TBannotator, for peer-reviewed phylogeographic publications.
  Country × lineage cross-tabulation, choropleth maps, stacked barplots,
  diversity indices. Pair with `tbmonitor-papers` to cite prior studies. Use
  when: mapping a lineage's distribution, comparing sub-lineages, producing
  figures and supplementary tables, identifying hotspots.

  Scope: developed on the MTBC, applies to any clonal bacterial pathogen
  (Yersinia, Leptospira...) — cross-tabulation, maps and diversity indices are
  generic. Outside the MTBC: supply the geographic metadata source (TBannotator
  and tbmonitor-papers are TB-only; use sra-geolocate or a metadata table).
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres
---

> [!WARNING]
> **[2026-09-08] Les requêtes de ce skill qui filtrent sur un système de lignée MAISON ne rendent
> plus rien.** Le MCP TBannotator est arrêté ; le serveur `tblearn` qui le remplace ne porte que
> huit systèmes **externes** (Coll, Coscolla, Freschi, Lipworth, Napier, Palittapongarnpim,
> Shitikov, Stucki). `system_name = 'guyeux'` et `system_name = 'tblearn'` y rendent **zéro ligne
> sans lever d'erreur**, ce qu'un script lira comme « aucune souche ne satisfait le critère ».
>
> **Substitution, décidée le 2026-09-08 :** les lignées maison se lisent désormais dans la base
> LOCALE `bdd/actuelle/`, qui fait déjà autorité selon
> `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`, via le skill `bdd-bridge` :
>
> ```bash
> B=~/docs/environnement/plugins/mtbc/skills/bdd-bridge/scripts
> export TBANNOTATOR_BDD=~/docs/codes/mtbc/bdd
> python3 $B/bdd_query.py clades                # tous les clades et leurs effectifs
> python3 $B/bdd_query.py denominator <clade>   # effectif réellement exploitable
> python3 $B/bdd_query.py strains <clade>       # souches d'un clade
> ```
>
> `tblearn` reste utilisable pour tout le reste (SPDI, QC, métadonnées, RD, IS, CRISPR) et pour
> **comparer** à une taxonomie externe, mais ce n'est plus la source des lignées maison. Toute
> requête qui filtre sur `system_name` doit d'abord vérifier que le filtre a matché :
> `SELECT system_name, count(*) FROM mv_strain_lineage WHERE system_name = '<x>' GROUP BY 1;`
> — zéro ligne signifie « ce système n'existe pas ici », jamais « aucune souche ».
>
> Détail complet : `~/.agents/knowledge/tblearn-migration.md`.


# Phylogeography : Distribution géographique MTBC

Analyse de la distribution géographique des lignées MTBC. Produit des tableaux pays × lignée, des cartes choroplèthes, et des barplots empilés pour articles.

**Quand l'utiliser** : cartographier la distribution géographique d'une lignée pour un article, comparer la structure géographique entre sous-lignées, produire les figures de distribution **et les tables supplementary**, identifier des **hotspots géographiques**.

## Phase 1 : Découverte (OBLIGATOIRE)

1. **Quelle lignée ?** (ex. L4.15, L2, toutes les L4)
2. **Quel niveau géographique ?**
   - Pays (défaut, données les plus complètes)
   - Continent/région (agrégation)
   - Combinaison (pays + continent pour le barplot)
3. **Quel type de figure ?**
   - **Barplot empilé** (pays par proportion de sous-lignées), le plus courant en article
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
SELECT m.geo_country, c.lineage_code, COUNT(*) as n
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.strain_id
WHERE c.system_name = 'guyeux' AND c.lineage_code LIKE '4.15%'
  AND m.geo_country IS NOT NULL AND m.geo_country != ''
GROUP BY m.geo_country, c.lineage_code
ORDER BY n DESC;
```

### Avec proportions

```sql
-- Proportions par pays (pour barplot empilé)
WITH country_totals AS (
  SELECT m.geo_country, COUNT(*) as total
  FROM mv_strain_metadata m
  JOIN mv_strain_classification c ON m.strain_id = c.strain_id
  WHERE c.system_name = 'guyeux' AND c.lineage_code LIKE '4.15%'
    AND m.geo_country IS NOT NULL AND m.geo_country != ''
  GROUP BY m.geo_country
  HAVING COUNT(*) >= 5
)
SELECT m.geo_country, c.lineage_code, COUNT(*) as n,
       ct.total,
       ROUND(100.0 * COUNT(*) / ct.total, 1) as pct
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.strain_id
JOIN country_totals ct ON m.geo_country = ct.geo_country
WHERE c.system_name = 'guyeux' AND c.lineage_code LIKE '4.15%'
GROUP BY m.geo_country, c.lineage_code, ct.total
ORDER BY ct.total DESC, m.geo_country, c.lineage_code;
```

### Contexte : proportion de la lignée parmi toutes les souches d'un pays

```sql
-- Quelle fraction du TB national est L4.15 ?
WITH country_all AS (
  SELECT m.geo_country, COUNT(*) as total_all
  FROM mv_strain_metadata m
  JOIN mv_strain_classification c ON m.strain_id = c.strain_id
  WHERE c.system_name = 'guyeux' AND m.geo_country IS NOT NULL
  GROUP BY m.geo_country
  HAVING COUNT(*) >= 20
),
country_target AS (
  SELECT m.geo_country, COUNT(*) as n_target
  FROM mv_strain_metadata m
  JOIN mv_strain_classification c ON m.strain_id = c.strain_id
  WHERE c.system_name = 'guyeux' AND c.lineage_code LIKE '4.15%'
    AND m.geo_country IS NOT NULL
  GROUP BY m.geo_country
)
SELECT a.geo_country, COALESCE(t.n_target, 0) as n_target, a.total_all,
       ROUND(100.0 * COALESCE(t.n_target, 0) / a.total_all, 2) as pct_of_total
FROM country_all a
LEFT JOIN country_target t ON a.geo_country = t.geo_country
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

## Biais d'échantillonnage : ATTENTION

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
| `sci-figure` | Figures supplémentaires personnalisées |
| `tbmonitor-papers` | Retrouver les études phylogéographiques antérieures sur une lignée ou un pays, pour les citer dans l'article : rechercher **nom de pays + code de lignée** dans le titre/abstract du corpus PubMed TB pré-indexé |

## Dépendances

```bash
pip install pandas numpy matplotlib seaborn
# Optionnel pour cartes :
pip install geopandas
```

## Codex packaging note

This packaged copy targets Codex. MCP tool names in `allowed-tools` are prerequisites: verify them with `codex mcp list` in the active profile before relying on live queries.
