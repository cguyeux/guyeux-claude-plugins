---
name: geo-map
description: >-
  Academic research toolkit for peer-reviewed pathogen-genomics publications (Guyeux group,
  FEMTO-ST). Publication-quality geographic maps for MTBC studies: cartographic projections,
  Natural Earth multi-resolution basemaps, scale bar, north arrow, graticule, journal
  presets. Types: choropleth, bubble, pie, GPS points, phylogeographic arcs, multi-panel
  atlases, multi-layer composites. Use when mapping the distribution of a lineage in a
  research collection, antimicrobial-resistance allele frequencies by country in a published
  dataset, sampling sites, inferred migration flows, or any map figure for a scientific
  article, poster or slide.
argument-hint: "<data.csv|spec.json> [-t choropleth|pie|bubble|points|arcs|layered] [-o map.pdf] [--preset nature_double]"
user-invocable: true
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
> B=~/docs/codes/claude_plugins/bio_pathogens/skills/bdd-bridge/scripts
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


# Geo-Map : Cartes géographiques MTBC qualité publication

Génère des cartes publication-quality pour MTBC avec projections cartographiques propres (Robinson, Albers, Lambert, LAEA), couches Natural Earth multi-résolution (110m / 50m / 10m), océan coloré, graticule, barre d'échelle, north arrow, et presets de format journaux (Nature, Science, PLOS, Cell).

## Phase 1 : Découverte (OBLIGATOIRE)

1. **Quel type de carte ?**

   | Type | Usage | Quand l'utiliser |
   |------|-------|-----------------|
   | `choropleth` | Coloration des pays par intensité | Prévalence d'une lignée, taux de résistance |
   | `gradient` | Choropleth avec colormap par défaut `Reds` | Taux MDR, résistance |
   | `bubble` | Cercles proportionnels aux valeurs | Nombre de souches par pays |
   | `pie` | Camemberts sur chaque pays | Composition en sous-lignées |
   | `points` | Marqueurs aux coordonnées GPS lat/lon | Sites d'échantillonnage, isolats individuels |
   | `arcs` | Flèches courbes entre régions | Reconstruction phylogéographique, migrations |
   | `layered` | Composition multi-couches (JSON spec) | Choropleth + points + arcs combinés |
   | `--facet-column` | Multi-panel atlas | Comparaison entre lignées ou périodes |

2. **Quelle donnée ?**
   - Distribution d'une lignée par pays (depuis TBannotator)
   - Coordonnées GPS d'isolats (latitude, longitude, lignée, année...)
   - Flux phylogéographiques (src_lat, src_lon, dst_lat, dst_lon, weight)
   - Composition en sous-lignées (country, lineage, n)

3. **Quelle région ?** (auto-déduit la projection optimale)
   - `world` (Robinson par défaut), `africa` (Albers), `europe` (Lambert EU), `asia` (Albers), `americas` (Albers), `mediterranean`, `horn_africa`, `sub_saharan`, `central_asia`, `middle_east`, `southeast_asia`, `south_asia`, `east_asia`, `north_america`, `south_america`
   - **Bbox personnalisée** : `--region "lon_min,lat_min,lon_max,lat_max"`

4. **Quel preset ?**
   - `generic` (défaut, 174 mm × 110 mm, 300 dpi, PNG)
   - `nature_single` (89 mm, 600 dpi, PDF, Arial)
   - `nature_double` (183 mm, 600 dpi, PDF, Arial)
   - `science` (120 mm, 600 dpi, PDF, Helvetica)
   - `plos` (174 mm, 300 dpi, TIFF, Arial)
   - `cell` (174 mm, 300 dpi, PDF, Helvetica)
   - `poster` (400 mm × 280 mm, 300 dpi, grandes polices)
   - `slide` (16:9, polices adaptées présentation)

## Phase 2 : Extraction des données

### Depuis TBannotator (cartes par pays)

```sql
-- Distribution par pays pour une lignée
SELECT m.geo_country, COUNT(*) AS n
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.strain_id
WHERE c.system_name = 'guyeux' AND c.lineage_code LIKE '4.15%'
  AND m.geo_country IS NOT NULL AND m.geo_country != ''
GROUP BY m.geo_country
ORDER BY n DESC;

-- Composition en sous-lignées par pays
SELECT m.geo_country, c.lineage_code AS lineage, COUNT(*) AS n
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.strain_id
WHERE c.system_name = 'guyeux' AND c.lineage_code LIKE '4%'
GROUP BY m.geo_country, c.lineage_code;

-- Taux MDR par pays
-- NB : pas de `dr_type` en v3.6 → MDR dérivé de l'antibiogramme (INH-R ET RIF-R).
-- Le dénominateur est restreint aux souches ANTIBIOGRAMMÉES (~23k/255k), sinon le taux est faussement bas.
SELECT m.geo_country,
       COUNT(*) AS n_tested,
       SUM(CASE WHEN m.antibiogram_inh = 'INH-R' AND m.antibiogram_rif = 'RIF-R' THEN 1 ELSE 0 END) AS n_mdr,
       ROUND(100.0 * SUM(CASE WHEN m.antibiogram_inh = 'INH-R' AND m.antibiogram_rif = 'RIF-R' THEN 1 ELSE 0 END)
             / COUNT(*), 1) AS pct_mdr
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.strain_id
WHERE c.system_name = 'guyeux' AND c.lineage_code LIKE '2%'
  AND m.antibiogram_inh IS NOT NULL AND m.antibiogram_rif IS NOT NULL
GROUP BY m.geo_country
HAVING COUNT(*) >= 10;
```

### Depuis TBannotator (sites GPS)

```sql
-- Coordonnées GPS des isolats
-- Colonnes réelles v3.6 : `latitude`/`longitude` (pas lat/lon) ; l'année se dérive de
-- `collection_date_parsed` (il n'y a pas de colonne `collection_year`).
SELECT m.strain_id, m.strain_name, m.latitude, m.longitude,
       c.lineage_code AS lineage,
       EXTRACT(YEAR FROM m.collection_date_parsed) AS collection_year
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.strain_id
WHERE c.system_name = 'guyeux' AND c.lineage_code LIKE '2%'
  AND m.latitude IS NOT NULL AND m.longitude IS NOT NULL;
```

### Formats CSV attendus

**Choropleth / bubble / gradient** :
```csv
country,n
France,125
India,340
```

**Pie** :
```csv
country,lineage,n
France,L4,80
France,L2,15
India,L1,180
```

**Points (GPS)** :
```csv
strain_id,latitude,longitude,lineage,year
TB001,28.6139,77.2090,L1,2018
TB002,-26.2041,28.0473,L4,2019
```

**Arcs** (phylogéo) :
```csv
src_lat,src_lon,dst_lat,dst_lon,n
20.5937,78.9629,55.3781,-3.4360,45
35.8617,104.1954,36.2048,138.2529,80
```

**Layered** (composition multi-couches, JSON) :
```json
{
  "layers": [
    {"type": "choropleth", "csv": "country_n.csv", "value_col": "n",
     "cmap": "Blues", "log_scale": true, "legend_title": "Strains"},
    {"type": "points", "csv": "samples.csv", "lat_col": "lat",
     "lon_col": "lon", "group_col": "lineage", "marker_size": 30},
    {"type": "arcs", "csv": "flows.csv", "weight_col": "n",
     "color": "#D0021B"}
  ]
}
```

## Phase 3 : Génération de la carte

### Exemples courants

```bash
# Choroplèthe mondiale (Robinson), preset Nature double colonne
python3 scripts/geo_map.py countries.csv -t choropleth -v n \
  --preset nature_double --log-scale \
  --title "Global distribution of L4.15 (n=523)" \
  --subtitle "TBannotator, May 2025" \
  --legend-title "Strains" -o fig1_map.pdf

# Choroplèthe Afrique (Albers Equal Area Africa automatique)
python3 scripts/geo_map.py africa.csv -t choropleth -v n \
  --region africa --cmap Reds \
  --title "L5 (M. africanum West) in Africa" -o fig2.pdf

# Choroplèthe DIVERGENT d'enrichissement (log-ratio centré sur 0) + significativité
# Colonnes attendues : country, log2_enrichment, p_fisher
python3 scripts/geo_map.py enrichment.csv -t choropleth -v log2_enrichment \
  --cmap RdBu_r --center 0 --sig-column p_fisher --sig-threshold 0.05 \
  --title "Enrichment per country (corrected for sampling bias)" \
  --subtitle "log2(observed/expected); * = Fisher p<0.05" \
  --legend-title "log2(obs/exp)" -o fig_enrichment.pdf

# Camemberts par pays
python3 scripts/geo_map.py composition.csv -t pie -g lineage \
  --title "L4 sub-lineage composition" \
  --pie-scale 1.3 -o fig3_pie.pdf

# Bulles (Asie de l'Est)
python3 scripts/geo_map.py beijing.csv -t bubble -v n \
  --region east_asia --color "#D0021B" \
  --title "L2.2.1 Beijing distribution" -o fig4.pdf

# Points GPS par lignée (Asie du Sud-Est)
python3 scripts/geo_map.py samples.csv -t points \
  --lat-col lat --lon-col lon -g lineage \
  --region southeast_asia --marker-size 30 \
  --title "Sampling sites — Indonesia & Philippines" \
  -o fig5_points.pdf

# Arcs phylogéographiques
python3 scripts/geo_map.py flows.csv -t arcs --weight-column n \
  --title "BEAST 2 phylogeographic reconstruction" \
  --subtitle "Inferred L4 migration paths" -o fig6_flows.pdf

# Multi-panel atlas (un panel par lignée)
python3 scripts/geo_map.py all_lineages.csv -t choropleth -v n \
  --facet-column lineage --ncols 3 --log-scale --cmap YlOrRd \
  --preset nature_double --title "Distribution by major lineage" \
  -o atlas.pdf

# Composition multi-couches
python3 scripts/geo_map.py composite.json -t layered \
  --title "Strain density and sampling sites" \
  -o composite.pdf
```

## Phase 4 : Arguments

### Données et type

| Argument | Default | Description |
|----------|---------|-------------|
| `input_file` | requis | CSV (ou JSON pour `layered`) |
| `-t`, `--type` | `choropleth` | `choropleth`, `gradient`, `bubble`, `pie`, `points`, `arcs`, `layered` |
| `-v`, `--value-column` | `n` | Colonne numérique |
| `-g`, `--group-column` | none | Colonne de groupes (pie, points) |
| `--country-column` | `country` | Colonne nom de pays |
| `--lat-col` / `--lon-col` | `lat`/`lon` | Colonnes GPS (points) |
| `--src-lat-col` / `--src-lon-col` | `src_lat`/`src_lon` | Source (arcs) |
| `--dst-lat-col` / `--dst-lon-col` | `dst_lat`/`dst_lon` | Destination (arcs) |
| `--weight-column` | none | Poids des arcs |
| `--facet-column` | none | Faceting multi-panel |
| `--ncols` | `2` | Colonnes en multi-panel |

### Cartographie

| Argument | Default | Description |
|----------|---------|-------------|
| `-r`, `--region` | `world` | Région prédéfinie ou bbox `lon_min,lat_min,lon_max,lat_max` |
| `--projection` | `auto` | Projection (voir tableau) |
| `--resolution` | `auto` | `110m`, `50m`, `10m` |

### Style et habillage

| Argument | Default | Description |
|----------|---------|-------------|
| `--preset` | `generic` | Format journal (voir tableau) |
| `--dpi` | preset | Résolution |
| `--figsize` | preset | `w_inches,h_inches` |
| `--title` | none | Titre principal |
| `--subtitle` | none | Sous-titre |
| `--note` | none | Note supplémentaire dans le pied |
| `--legend-title` | auto | Titre de la légende |
| `--cmap` | `YlOrRd` | Colormap matplotlib |
| `--palette` | MTBC | JSON ou `colorblind` pour palette CB-safe |
| `--log-scale` | off | Échelle log pour valeurs |
| `--show-labels` | off | Afficher noms de pays |
| `--legend-loc` | `lower left` | Position de la légende de couleurs (`lower left/right`, `upper left/right`, `center left`). La barre d'échelle est TOUJOURS en bas à gauche → pour un choroplèthe catégoriel / pie / bubble, mettre `lower right` ou `upper right` pour éviter le chevauchement légende↔échelle. |
| `--categorical` | off | Choroplèthe CATÉGORIEL : colore chaque pays par la valeur (chaîne) de la colonne `-v` (ex. famille linguistique, écotype) avec une légende catégorielle. `--palette` (JSON `{catégorie: hex}`) fixe les couleurs, sinon `--cmap` qualitatif (`Set2`, `tab10`). |
| `--label-threshold` | médiane | Seuil pour les labels |
| `--min-value` / `--max-value` | auto | Bornes échelle |
| `--center` | none | Centre d'un choroplèthe DIVERGENT : auto-symétrise vmin/vmax autour de cette valeur (ex. `--center 0` avec `--cmap RdBu_r` pour des données log-ratio / enrichissement, neutre=blanc). Ignoré si `--min/--max-value` posés. |
| `--sig-column` | none | Colonne CSV (ex. p-value de Fisher) : marque d'un astérisque gras les pays où la valeur < `--sig-threshold`. |
| `--sig-threshold` | `0.05` | Seuil pour le marquage `--sig-column`. |
| `--sig-style` | `asterisk` | Style de marquage des pays significatifs : `asterisk` (astérisque, plus visible sur les petits pays), `hatch` (hachures diagonales, standard publication), `edge` (contour noir épais). Une vignette de légende auto-documentée (symbole + seuil) est ajoutée in-figure. |
| `--sig-legend-loc` | `lower left` | Coin de la vignette de légende de significativité (`lower left`, `lower right`, `upper left`, `upper right`). |
| `--color` | `#E03D31` | Couleur bulles/arcs |
| `--marker-size` / `--max-size` | `25` / `250` | Taille marker (points) |
| `--alpha` | `0.85` | Transparence des marqueurs |
| `--jitter` | `0` | Jitter en degrés (échantillons co-localisés) |
| `--min-width` / `--max-width` | `0.5` / `3.0` | Épaisseur arcs |
| `--min-total` | `5` | Min souches/pays pour pie |
| `--pie-scale` | `1.0` | Facteur taille pies |

### Extensions avancées (arguments)

| Argument | Default | Description |
|----------|---------|-------------|
| `--insets` | `none` | `none` \| `auto` (petits pays détectés) \| `Country1,Country2,...` |
| `--smart-labels` | `none` | `none` \| `fast` (1 itération) \| `quality` (3 itérations) |
| `--show-cities` | off | Affiche les grandes villes Natural Earth |
| `--min-pop` | `1000000` | Population minimale pour afficher une ville |
| `--hillshade` | off | Ajoute le relief ombré (GRAY Shaded Relief) |
| `--show-tropics` | off | Trace Cancer / équateur / Capricorne |
| `--animate-by` | none | Colonne temporelle pour générer un GIF/MP4 |
| `--animate-fps` | `2` | Frames par seconde |
| `--animate-subtitle` | `{frame}` | Template du sous-titre par frame |
| `--insets-numbered` | off | Numérote les insets et marque leur position sur la carte principale |
| `--show-biomes` | off | Bandes climatiques par latitude (approximation pédagogique) |
| `--climate-raster` | none | Raster Köppen-Geiger (TIF/PNG, PlateCarrée monde entier) à overlayer |

## Projections

| Nom | Code | Usage MTBC |
|-----|------|------------|
| `robinson` | ESRI:54030 | Vue mondiale par défaut |
| `mollweide` | ESRI:54009 | Vue mondiale equal-area |
| `winkel` | ESRI:54019 | Vue mondiale compromis |
| `eckert4` | ESRI:54012 | Vue mondiale equal-area |
| `equal_earth` | proj=eqearth | Vue mondiale moderne |
| `mercator` | EPSG:3857 | Web maps, déconseillé en publication |
| `albers_africa` | proj=aea | Afrique entière (L5, L6, M. africanum) |
| `albers_europe` | proj=aea | Europe entière (L4) |
| `albers_asia` | proj=aea | Asie (L1, L2, L3) |
| `albers_americas` | proj=aea | Amériques |
| `lambert_europe` | EPSG:3035 | Europe ETRS89-LAEA officiel |
| `lambert_us` | EPSG:5070 | États-Unis NAD83-LAEA officiel |
| `platecarree` | EPSG:4326 | Brut lon/lat (pas recommandé) |

Auto-sélection : `world→robinson`, `africa→albers_africa`, `europe→lambert_europe`, `asia→albers_asia`, `americas→albers_americas`, etc.

## Régions prédéfinies (bbox lon_min, lat_min, lon_max, lat_max)

| Région | Bounding box | Usage MTBC |
|--------|--------------|------------|
| `world` | -180, -60, 180, 85 | Vue globale |
| `africa` | -25, -38, 55, 38 | L5, L6, M. africanum |
| `sub_saharan` | -20, -38, 55, 18 | TB endémique |
| `horn_africa` | 28, -5, 52, 20 | L7 Éthiopie/Érythrée |
| `mediterranean` | -10, 28, 40, 48 | Bassin méditerranéen |
| `europe` | -15, 34, 45, 72 | L4, UE |
| `middle_east` | 25, 10, 65, 45 | L4 régional |
| `central_asia` | 45, 25, 90, 55 | Asie centrale |
| `south_asia` | 60, 5, 100, 40 | L1, L3 |
| `southeast_asia` | 90, -15, 155, 30 | L1 Indo-Oceanic |
| `east_asia` | 70, 15, 150, 55 | L2 Beijing |
| `north_america` | -170, 15, -50, 75 | L4 importations |
| `south_america` | -85, -58, -30, 15 | L4 |
| `americas` | -170, -60, -30, 75 | Continent entier |

## Presets journaux

| Preset | Largeur | Hauteur | DPI | Format | Police |
|--------|---------|---------|-----|--------|--------|
| `generic` | 174 mm | 110 mm | 300 | PNG | DejaVu Sans |
| `nature_single` | 89 mm | 70 mm | 600 | PDF | Arial |
| `nature_double` | 183 mm | 110 mm | 600 | PDF | Arial |
| `science` | 120 mm | 80 mm | 600 | PDF | Helvetica |
| `plos` | 174 mm | 110 mm | 300 | TIFF | Arial |
| `cell` | 174 mm | 110 mm | 300 | PDF | Helvetica |
| `poster` | 400 mm | 280 mm | 300 | PNG | DejaVu Sans |
| `slide` | 330 mm | 186 mm | 200 | PNG | DejaVu Sans |

## Palette MTBC

Cohérente avec iTOL et t-SNE :

```json
{
  "L1": "#F5A623", "L2": "#D0021B", "L3": "#4A90D9",
  "L4": "#E03D31", "L5": "#7B2D8E", "L6": "#9B59B6",
  "L7": "#B8860B", "L8": "#1B9AAA", "L9": "#2D6A4F",
  "L10": "#52B788",
  "M. bovis": "#3D2B1F", "M. caprae": "#6B4226",
  "M. africanum": "#7B2D8E", "M. canettii": "#5D4037",
  "Unknown": "#9E9E9E"
}
```

Variante daltonien-safe disponible via `--palette colorblind` (palette Okabe-Ito étendue).

### Colormaps recommandées par usage

| Usage | Colormap | Justification |
|-------|----------|---------------|
| Nombre de souches | `YlOrRd` | Gradient jaune→rouge intuitif |
| Taux de résistance | `Reds` | Rouge = danger |
| Diversité génétique | `viridis` | Perceptuellement uniforme |
| THD (succès épidémique) | `RdYlBu_r` | Rouge = épidémique, bleu = calme |
| Comparaison binaire | `RdBu` | Divergent autour de 0 |

## Correspondance noms de pays

Les noms de pays dans TBannotator ne correspondent pas toujours exactement aux shapefiles Natural Earth. Le script inclut un dictionnaire de correspondance étendu (USA, UK, DR Congo, Ivory Coast, South/North Korea, Czechia, eSwatini, Myanmar, Timor-Leste, Russia, South Sudan, Central African Republic, Bosnia, North Macedonia, Dominican Republic, Equatorial Guinea, Solomon Islands, Guinea-Bissau, Western Sahara, etc.).

## Extensions avancées

### Insets pour petits pays / îles

Les pays comme Singapour, Eswatini, Maldives, Bahreïn, Hong Kong, La Réunion, Maurice, Cap-Vert, Comores, etc. disparaissent à l'échelle mondiale ou régionale. L'option `--insets` ajoute des encarts agrandis en bas de la figure.

```bash
# Encarts auto pour tous les petits pays présents dans les données
geo_map.py data.csv -t choropleth -v n --region southeast_asia \
  --insets auto -o map.pdf

# Encarts pour pays spécifiques
geo_map.py data.csv -t choropleth -v n --region africa \
  --insets "Eswatini,Comoros,Cape Verde" -o map.pdf
```

Pays supportés en inset (avec extent prédéfini) :

- **Petits États** : Singapore, Maldives, Bahrain, eSwatini, Hong Kong, Mauritius, Cape Verde, Comoros, São Tomé and Príncipe, Trinidad and Tobago, Jamaica, Cyprus, Lebanon, Qatar, Kuwait, Brunei, Timor-Leste, Lesotho, Djibouti.
- **DOM/TOM français** : Réunion, Mayotte, Guadeloupe, Martinique, French Guiana, New Caledonia, French Polynesia, Wallis and Futuna, Saint Pierre and Miquelon, Saint Martin, Saint Barthélemy.

Les insets sont chargés en résolution Natural Earth 50m (force) pour que les petits territoires aient une géométrie utilisable. Les DOM/TOM (qui ne sont pas des `admin_0_countries` séparés dans NE mais des morceaux de France) sont rendus en intersectant la géométrie de France avec le bbox de l'inset.

### Insets numérotés

Mode `--insets-numbered` : chaque inset est préfixé d'un numéro (1, 2, 3, ...) et un marqueur circulaire portant ce numéro est tracé sur la carte principale, au centroïde du bbox de l'inset. Indispensable dès qu'il y a >5 insets sur des îles dispersées.

```bash
geo_map.py data.csv -t choropleth -v n \
  --insets "Singapore,Mauritius,Cape Verde,Réunion,Mayotte" \
  --insets-numbered -o map.pdf
```

### Biomes climatiques

`--show-biomes` superpose une approximation pédagogique des grandes zones climatiques par latitude (tropical entre Cancer et Capricorne, subtropical/aride entre 23.4° et 35°, tempéré entre 35° et 60°, polaire au-delà). C'est une carte indicative pour discuter écologie TB en première approche.

```bash
geo_map.py data.csv -t choropleth -v n --show-biomes --show-tropics \
  -o map.pdf --subtitle "MTBC across climate zones"
```

Pour une vraie carte Köppen-Geiger, fournir un raster TIF/PNG via `--climate-raster path/to/koppen.tif`. Le script accepte :

- la version simplifiée 5 classes (A,B,C,D,E)
- les codes Beck et al. 2018 (1-30), qui sont agrégés automatiquement en 5 classes (Tropical, Aride, Tempéré, Continental, Polaire).

Le raster est supposé couvrir le monde entier en projection PlateCarrée (`-180..180`, `-90..90`). Téléchargements de référence :

- Beck et al. (2023, 1 km) : <https://www.gloh2o.org/koppen/>
- Beck et al. (2018, 0.5°) : Figshare (1.6 Mo)

### Labels non-superposables (smart labels)

Algorithme greedy de placement des noms de pays pour éviter les chevauchements. Adapté quand vous voulez identifier les pays à forte valeur sans clutter.

```bash
# Mode 'fast' (1 itération, suffit la plupart du temps)
geo_map.py data.csv -t choropleth -v n --smart-labels fast \
  --label-threshold 50 -o map.pdf

# Mode 'quality' (3 itérations, plus lent mais meilleur placement)
geo_map.py data.csv -t choropleth -v n --smart-labels quality -o map.pdf
```

`--label-threshold` filtre quels pays sont labellisés (par défaut médiane des valeurs).

### Villes principales

Affiche les grandes villes (Natural Earth `populated_places`), filtrables par population minimale.

```bash
# Villes ≥ 5M habitants
geo_map.py data.csv -t choropleth -v n --region east_asia \
  --show-cities --min-pop 5000000 -o map.pdf

# Toutes les capitales / villes majeures (≥ 1M)
geo_map.py data.csv -t choropleth -v n --show-cities -o map.pdf
```

Utile pour donner le contexte géographique dans les analyses de transmission TB (les épidémies se concentrent souvent autour des grandes agglomérations).

### Hillshade (relief ombré)

Superpose le relief ombré Natural Earth (GRAY_*_SR) comme arrière-plan. Très efficace pour les cartes régionales en montagne (Afrique de l'Est, Andes, Himalaya, Caucase).

```bash
geo_map.py data.csv -t choropleth -v n --region east_asia \
  --hillshade --resolution 50m -o map.pdf
```

Le hillshade est téléchargé automatiquement (~5 Mo pour 50m, ~50 Mo pour 10m, ~1 Mo pour 110m) et mis en cache. Combiner avec `--alpha` faible (pour le choropleth) si vous voulez garder le relief visible sous les couleurs.

### Tropiques et équateur

Trace le Tropique du Cancer (23.4°N), l'équateur, et le Tropique du Capricorne (23.4°S). Utile pour discuter la zone intertropicale et les facteurs climatiques de la TB.

```bash
geo_map.py data.csv -t choropleth -v n --show-tropics -o map.pdf
```

### Animation temporelle

Génère un GIF (Pillow) ou MP4 (ffmpeg) en itérant sur une colonne temporelle. Une frame par valeur distincte de la colonne.

```bash
# Évolution d'une lignée sur 10 ans (GIF)
geo_map.py data.csv -t choropleth -v n --animate-by year \
  --animate-fps 2 --log-scale -o evolution.gif \
  --title "L4 expansion" --animate-subtitle "Year {frame}"

# Même chose en MP4 (ffmpeg requis)
geo_map.py data.csv -t choropleth -v n --animate-by year \
  --animate-fps 3 -o evolution.mp4
```

Le placeholder `{frame}` dans `--animate-subtitle` est remplacé par la valeur courante. L'échelle (vmin, vmax) est calculée globalement pour rester cohérente entre les frames.

### Combinaison de toutes les extensions

```bash
geo_map.py sea_data.csv -t choropleth -v n --region southeast_asia \
  --preset nature_double --log-scale \
  --insets auto \
  --smart-labels fast \
  --show-cities --min-pop 5000000 \
  --hillshade \
  --show-tropics \
  --title "L1 distribution — Southeast Asia" \
  -o fig.pdf
```

## Habillage cartographique inclus automatiquement

- **Océan** colorisé (bleu pâle `#D6E6F2`)
- **Terres** colorisées (`#FAF7F2`)
- **Côtes** en gris foncé (`#5E7A8C`, lw 0.4)
- **Lacs** (`#BBD6E8`)
- **Frontières** (`#999999`, lw 0.3)
- **Graticule** méridiens/parallèles automatiques (pas adapté à la région)
- **Barre d'échelle** géographique (cartes régionales uniquement, km)
- **North arrow** (cartes régionales uniquement)
- **Crédits Natural Earth** (public domain) en pied
- **Titre** en gras, **sous-titre** italique gris
- **Légende** encadrée avec fond translucide

## Sortie

| Extension | Usage |
|-----------|-------|
| `.pdf` | Recommandé pour publication (vectoriel, polices embarquées via fonttype 42) |
| `.svg` | Édition Inkscape/Illustrator |
| `.png` | Présentations, posters |
| `.tiff` | Soumissions PLOS, certains éditeurs |
| `.tex` | Export TikZ via tikzplotlib (`pip install tikzplotlib`). Fallback PDF si non installé. Limitations : hillshade et climate-raster ne sont pas exportés (images), arcs courbes simplifiées. |

## Intégration avec d'autres skills

| Skill | Usage |
|-------|-------|
| `phylogeography` | Fournit pays×lignée, indices de diversité, flux phylogéo |
| `tbannotator-mcp` | Source des distributions et coordonnées GPS |
| `resistance-profiler` | Taux de résistance par pays pour gradient map |
| `lineage-comparison` | Significativité des différences géographiques |
| `beast2-phylogeography` | Coordonnées des nœuds ancestraux pour `arcs` |
| `sci-figure` | Figures complémentaires non cartographiques ; partage les presets de revue de ce skill (`JOURNAL_PRESETS`) via son `figstyle.py`, donc mêmes largeur, police et dpi |

## Dépendances

```bash
pip install geopandas matplotlib shapely numpy pandas
# (cartopy non requis ; geopandas + matplotlib suffit)
```

### Données cartographiques

Les shapefiles Natural Earth (110m, 50m, 10m) sont téléchargés automatiquement à la première utilisation et mis en cache dans `~/.cache/geo_map/` (variable d'environnement `GEO_MAP_CACHE` pour override). Sources : `https://naciscdn.org/naturalearth/`. Toutes les données Natural Earth sont en domaine public.

## Cache et performance

- Premier appel sur région donnée : téléchargement automatique des couches Natural Earth (~10 Mo pour 110m, ~50 Mo pour 50m, ~200 Mo pour 10m).
- Appels suivants : lecture cache local, ~1 s par carte.
- Pour invalider le cache : supprimer `~/.cache/geo_map/`.

## Notes d'usage pour les agents de rédaction

- Pour insertion dans un manuscrit LaTeX : utiliser un `--preset` qui correspond au journal cible (`nature_double`, `plos`, `cell`) et sortir en `.pdf`. La police et la taille seront alignées avec les guidelines du journal.
- Pour discuter géographiquement dans un texte : appeler ce skill avec une requête concise (`-t choropleth --region europe --title "L4.10 in Europe"`) et insérer la figure obtenue avec un caption explicite.
- Toujours mentionner Natural Earth en crédit dans le caption (« Basemap: Natural Earth, public domain »). Le pied de carte le fait déjà automatiquement, mais le caption doit aussi être conforme.
- Pour BEAST 2 / phylogeographic discrete trait : exporter les transitions ancestrales en CSV (src_lat, src_lon, dst_lat, dst_lon, weight) puis appeler `-t arcs` ou en `layered` au-dessus d'un fond choropleth.
