---
name: indian-ocean-voyages
description: >-
  Aggregate and format historical Indian Ocean maritime voyage data for
  comparison with M. tuberculosis L1 (Indo-Oceanic) phylogeography.
  Wraps four open-data sources : ESTA (Exploring Slave Trade in Asia,
  IISG Amsterdam, ~5 300 voyages, ~440 000 enslaved persons, 16th–19th c.),
  GLOBALISE (Huygens/KNAW,5 million pages of VOC archives, commodity and
  route metadata, 1602–1799), CLIWOC (287 114 European logbooks, 1750–1854,
  daily geocoded ship positions), and SlaveVoyages Indian Ocean subset
  (~1 000 voyages stopping in East Africa / Indian Ocean).

  Use when : comparing L1 sub-lineage dispersal to historical maritime
  routes in the Indian Ocean, building origin-destination matrices for
  Mantel tests against MTBC pairwise distances, overlaying TMRCA estimates
  on documented voyage chronologies, preparing figures linking M. tuberculosis
  L1 phylogeography to VOC trade networks, French Île de France/Bourbon
  slave trade, or Omani-Swahili commerce.
argument-hint: "<command: esta|globalise|cliwoc|slavevoyages-io|routes|timeline|fetch> [options]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebFetch
---

# Indian Ocean Voyages : Données maritimes historiques pour études MTBC L1

Skill complémentaire à `migration-data` (qui couvre la traite atlantique et les
événements généraux). Ici on cible exclusivement l'océan Indien et la mer de
Chine pour l'étude phylogéographique de la lignée L1 (Indo-Oceanic / EAI) de
*M. tuberculosis*, sur le modèle de l'approche *H. pylori* (Linz et al. 2007).

## Phase 1 : Découverte (OBLIGATOIRE)

### 1. Quelle source ?

| Source | Contenu | Période | Granularité | Usage L1 |
|--------|---------|---------|-------------|----------|
| **ESTA** | ~5 300 voyages traite, ~440 000 individus | 1500-1900 | O-D, dates, individus | Routes Madagascar, Mozambique, Inde → îles, Cap, Batavia |
| **GLOBALISE** | 5M pages archives VOC, commodities, événements | 1602-1799 | Escales, cargaisons, lieux | Routes commerciales VOC : Cap → Mascareignes → Inde → Batavia → Chine |
| **CLIWOC** | 287 k journaux de bord, positions quotidiennes | 1750-1854 | Trajectoires jour par jour, géocodées | Routes réelles (vs O-D agrégées), validation des chemins de dispersion |
| **SlaveVoyages-IO** | ~1 000 voyages atlantique avec escale océan Indien | 1514-1866 | O-D, dates, volumes | Lien Brésil-Mozambique, Madagascar-Caraïbes |

### 2. Quelle période ?

- **Pré-européenne** (avant 1500) : commerce arabo-swahili, indo-malais, **non couverte par les bases**, à compléter par littérature
- **VOC + portugaise** (1500-1799) : GLOBALISE + ESTA + SlaveVoyages-IO
- **Britannique + française + traite tardive** (1800-1900) : ESTA + CLIWOC + SlaveVoyages-IO
- **Engagisme indien** (1834-1920) : non couvert directement, voir `migration-data ancient`

### 3. Quel format de sortie ?

- `routes` : liste de routes (from_port, to_port, volume, period, source)
- `matrix` : matrice bilatérale ports × ports (pour Mantel test)
- `trajectories` : positions quotidiennes (CLIWOC uniquement)
- `timeline` : chronologie événementielle pour overlay TMRCA L1

## Phase 2 : Commandes

### Script principal

```bash
# Agréger les voyages ESTA par route
python3 scripts/indian_ocean_voyages.py esta \
  --input esta_voyages.csv --period 1600:1800 \
  --format routes -o esta_routes.csv

# Routes commerciales VOC depuis GLOBALISE
python3 scripts/indian_ocean_voyages.py globalise \
  --input globalise_events.csv --period 1602:1799 \
  --format routes -o voc_routes.csv

# Trajectoires CLIWOC dans l'océan Indien
python3 scripts/indian_ocean_voyages.py cliwoc \
  --input CLIWOC21.csv --bbox -40,-20,20,120 --period 1750:1854 \
  --format trajectories -o ocean_indien_traj.csv

# SlaveVoyages, sous-ensemble océan Indien
python3 scripts/indian_ocean_voyages.py slavevoyages-io \
  --input tast.csv --indian-ocean-only \
  --format routes -o sv_io_routes.csv

# Routes curées (table intégrée, pas d'input)
python3 scripts/indian_ocean_voyages.py routes \
  --period 1500:1900 -o curated_routes.csv

# Timeline événementielle pour overlay TMRCA L1
python3 scripts/indian_ocean_voyages.py timeline \
  --tmrca l1_tmrca.csv -p l1_overlay.png

# Téléchargement aidé (URLs curées)
python3 scripts/indian_ocean_voyages.py fetch --source esta
python3 scripts/indian_ocean_voyages.py fetch --source globalise
python3 scripts/indian_ocean_voyages.py fetch --source cliwoc
```

## Arguments par commande

### `esta`

| Argument | Description |
|----------|-------------|
| `--input` | CSV ESTA téléchargé depuis https://datasets.iisg.amsterdam/dataverse/IOMASTD |
| `--period` | Période (ex. `1600:1800`) |
| `--from-region` | Filtrer région source (ex. `Madagascar`, `Mozambique`, `India`) |
| `--to-region` | Filtrer région destination (ex. `Cape`, `Mascarenes`, `Batavia`) |
| `--format` | `routes` ou `matrix` |

### `globalise`

| Argument | Description |
|----------|-------------|
| `--input` | Dataset CSV depuis https://datasets.iisg.amsterdam/dataverse/globalise |
| `--commodity` | Filtrer par marchandise (ex. `slaves`, `spices`, `textiles`) |
| `--period` | Période (`1602:1799` par défaut) |
| `--format` | `routes` ou `events` |

### `cliwoc`

| Argument | Description |
|----------|-------------|
| `--input` | CLIWOC21 CSV/TSV depuis historicalclimatology.com/cliwoc |
| `--bbox` | Bounding box `lat_min,lat_max,lon_min,lon_max` |
| `--period` | Période |
| `--nationality` | `Dutch`, `English`, `French`, `Spanish` ou `all` |
| `--format` | `trajectories` (positions) ou `routes` (O-D agrégées) |

### `slavevoyages-io`

| Argument | Description |
|----------|-------------|
| `--input` | TAST CSV depuis slavevoyages.org/voyage/database#downloads |
| `--indian-ocean-only` | Garder uniquement les voyages avec une escale océan Indien |
| `--format` | `routes` ou `matrix` |

### `routes`

Routes curées (table intégrée). Aucun input requis.

| Argument | Description |
|----------|-------------|
| `--period` | Filtrer par période |
| `--source` | `voc`, `swahili`, `french`, `british`, `all` |

### `timeline`

| Argument | Description |
|----------|-------------|
| `--tmrca` | CSV des estimations TMRCA L1 pour overlay |
| `--period` | Période d'affichage (par défaut `1500:1900`) |
| `-p` | Figure (PNG/PDF) |

### `fetch`

Affiche les URLs et instructions de téléchargement pour la source demandée.

| Argument | Description |
|----------|-------------|
| `--source` | `esta`, `globalise`, `cliwoc`, `slavevoyages` |

### Arguments communs

| Argument | Default | Description |
|----------|---------|-------------|
| `-o` | none | Fichier CSV de sortie |
| `-p` | none | Figure (PNG/PDF) |
| `--summary` | off | Résumé JSON |

## Routes maritimes curées (intégrées dans le script)

Routes principales documentées dans la littérature historique, formatées
de la même manière que la sortie agrégée des bases de données. Permet de
travailler sans téléchargement quand on n'a besoin que d'un cadrage général.

| De | Vers | Période | Volume estimé | Réseau | Lien L1 |
|----|------|---------|----------------|--------|---------|
| East Africa (Kilwa, Mombasa) | Oman, Yemen | 800-1500 | ~1M (estimé) | Swahili-arabe | L1 ancestrale → côte est-africaine |
| Mozambique, Madagascar | Cape Colony | 1652-1808 | ~70 000 | VOC | L1 vers Afrique du Sud |
| Madagascar | Mascarenes (Réunion, Maurice) | 1670-1810 | ~160 000 | Française | L1 vers îles Mascareignes |
| India (Coromandel, Bengal) | Batavia, Ceylon | 1602-1799 | ~50 000 | VOC | L1 indienne → Asie SE |
| India (Goa, Bombay) | East Africa | 1500-1900 | flux continu | Portugais/Britannique | Échanges bilatéraux L1 |
| China, Macao | Batavia, Manila | 1600-1900 | flux commercial | VOC, espagnole | L2 + L1 résiduel ? |
| Mozambique | Brazil | 1810-1850 | ~410 000 | Brésilienne (post-Atlantique) | Lien L1 Brésil documenté |

## Format de sortie : matrice de flux comparable

Sortie clé (CSV) au même schéma que `migration-data` :

```csv
from_port,to_port,from_country,to_country,volume,period_start,period_end,source,reference
Mozambique Island,Cape Town,Mozambique,South Africa,12000,1700,1799,VOC,GLOBALISE
Antongil Bay,Port Louis,Madagascar,Mauritius,45000,1721,1810,French,ESTA
Madras,Batavia,India,Indonesia,8000,1602,1799,VOC,GLOBALISE
```

Ce schéma permet :
- Comparaison directe avec la matrice de transitions L1 produite par
  `ancestral-reconstruction`
- Test de Mantel : `corr(matrix_voyages_O-D, matrix_distances_SNP_L1)`
- Overlay chronologique avec TMRCA L1 par `molecular-clock`

## Centroïdes des ports historiques (intégrés)

Table de ~80 ports majeurs de l'océan Indien (lat/lon) :
- **Côte est-africaine** : Mombasa, Kilwa, Mozambique Island, Quelimane, Sofala
- **Mer Rouge / Golfe** : Mocha, Aden, Muscat, Bandar Abbas
- **Inde** : Surat, Bombay, Goa, Cochin, Madras, Pondichéry, Calcutta, Chittagong
- **Asie SE** : Aceh, Malacca, Batavia, Macassar, Banda
- **Mascareignes** : Port Louis, Saint-Denis, Port-Saint-Louis (Mahé)
- **Cap** : Cape Town, Saldanha
- **Madagascar** : Tamatave, Antongil, Saint-Augustin, Diego-Suarez

Utilisée pour calculer distances Haversine et positionner les ports sur cartes.

## Sources de données externes

| Source | URL | Format | Licence |
|--------|-----|--------|---------|
| ESTA Database | https://esta.iisg.nl/ | CSV via Dataverse IISG | CC-BY |
| ESTA Dataverse | https://datasets.iisg.amsterdam/dataverse/IOMASTD | CSV/TSV | CC-BY |
| GLOBALISE | https://datasets.iisg.amsterdam/dataverse/globalise | CSV/RDF | CC-BY |
| CLIWOC | https://www.historicalclimatology.com/cliwoc.html | ODS, TSV, Geopackage | Open |
| CLIWOC DANS | https://phys-techsciences.datastations.nl/dataset.xhtml?persistentId=doi:10.17026/dans-2bx-dutg | Multiple | CC0 |
| SlaveVoyages | https://www.slavevoyages.org/voyage/database#downloads | CSV/Excel | CC-BY-NC |
| VOC-Data | https://www.vocdata.nl/ | Multiple | Open |

## Intégration

| Skill | Usage |
|-------|-------|
| `helicobacter-pylori-phylogeography` | Cadre théorique de référence (pathogène = traceur de migrations) |
| `migration-data` | Données complémentaires (Atlantique, événements pré-1500) |
| `ancestral-reconstruction` | Matrice de transitions L1 à comparer aux routes |
| `coevolution` | Test de Mantel entre routes maritimes et phylogénie L1 |
| `beast2-phylogeography` | Inférence MASCOT/BASTA avec routes documentées comme prior |
| `geo-map` | Cartes ports + flèches de routes |
| `molecular-clock` | TMRCA L1 pour overlay chronologique |
| `phylogeography` | Distribution géographique actuelle de L1 |
| `d-place` | Contexte culturel/linguistique des sociétés concernées |

## Dépendances

```bash
pip install pandas numpy matplotlib requests openpyxl shapely
```

`shapely` pour les opérations spatiales (bounding box, intersections).
`requests` pour le téléchargement aidé via la commande `fetch`.

## Notes méthodologiques

- **L1 et la traite** : La L1 est la lignée ancestrale du clade humain strict,
  distribuée historiquement dans l'océan Indien et l'Afrique de l'Est.
  Les voyages dans ce skill peuvent expliquer trois patterns L1 :
  (i) sa concentration côtière est-africaine (commerce swahili-arabe),
  (ii) sa présence en Asie du Sud-Est (routes VOC),
  (iii) son introduction au Brésil via Mozambique (post-1810).
- **Précédent voyageslave** : la démonstration que la L1 brésilienne provient
  d'Afrique de l'Est plutôt que de l'Ouest a utilisé l'extension océan Indien
  de SlaveVoyages. Ce skill généralise cette logique aux autres routes.
- **Limites** : les bases couvrent surtout 1500-1900. Pour les périodes
  antérieures (commerce arabo-swahili, expansion austronésienne vers Madagascar
  ~700 EC), s'appuyer sur la littérature et les datations BEAST2 plutôt que
  sur des données documentaires.
