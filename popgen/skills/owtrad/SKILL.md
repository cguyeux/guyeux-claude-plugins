---
name: owtrad
description: >-
  Query OWTRAD (Old World Trade Routes Project, T.M. Ciolek, Australian
  National University, 1999–present), the reference community-curated
  GIS archive of land, river and maritime trade, pilgrimage, military, and
  postal routes of Eurasia and Africa from ~10,000 BCE to ~1820 CE.
  Includes the Silk Road, Spice Route, Amber Route, Salt Route, and a
  gazetteer of 3,130 unique places plus catalogues of caravanserais,
  bridges, and forts.

  Use when: building a Silk Road or caravan-route narrative for MTBC
  lineages (especially L2 Beijing and L3 CAS in Central Asia), overlaying
  a TB or Y. pestis phylogeny on historical transport corridors,
  identifying caravanserais / stopping places as candidate mixing sites
  for human + animal MTBC, or assembling a pre-modern mobility context
  for a seminar slide.
---

# OWTRAD : Old World Trade Routes Project

## Client (resilient, tool-first)

A client ships with this skill (`src/owtrad_client/`) that reads any OWTRAD vector
file (KML / MapInfo / GeoJSON / shapefile) via geopandas and returns routes as a
table. geopandas is present on the system Python; nothing to pip-install.

```bash
SRC=<this skill>/src
export OWTRAD_FILE=/path/to/tmcCNa0100d.kml      # or .geojson / .mif / .shp
PYTHONPATH="$SRC" python3 -m owtrad_client routes --name Silk --type trade --bbox 20 30 50 110 --tsv
PYTHONPATH="$SRC" python3 -m owtrad_client.smoke_test   # offline GeoJSON fixture
```

`routes(name=..., route_type=..., bbox=(S,W,N,E))` returns `list[dict]` with stable
keys `name, route_type, description, geom_type, n_points, length_km, start_lon,
start_lat, end_lon, end_lat` (great-circle length summed over vertices). Reuses the
gabarit resolve cascade (`OWTRAD_FILE` -> fixture -> `DatasetUnavailable`); a missing
geopandas degrades to a clear message.

## Overview

**OWTRAD** (*Old World Trade Routes Project*), also known by the author's
term *Dromographic Digital Data Archives* (**ODDDA**), is a
community-referenced GIS archive of land, river, and maritime transport
routes across Eurasia and Africa from the **end of the Ice Age (~10,000
BCE) to ~1820 CE**, i.e. up to the eve of steam-engine transport. It was
created and is maintained by **Dr. T. Matthew Ciolek** (Australian
National University, Canberra) from **1999 to present**, and is the
longest-running open historical-transport GIS resource of its kind.

- **Canonical citation**: Ciolek, T.M. 1999–present. *Old World Trade
  Routes (OWTRAD) Project.* Canberra: `www.ciolek.com/owtrad.html`.
- **Methodology paper**: Ciolek, T.M. 2000. *Digitising Data on Eurasian
  Trade Routes: An Experimental Notation System.* Proceedings of the
  Pacific Neighborhood Consortium, Berkeley.
- **Main URL**: `http://www.ciolek.com/owtrad.html`
- **Hosted at**: `www.ciolek.com` : Asia Pacific Research Online
- **License**: **Creative Commons Attribution-NonCommercial 2.5**
  (unusual : CC BY-NC 2.5, not the more common 4.0)
- **Coverage scope**: Eurasia + Africa; 10,000 BCE → ~1820 CE

> [!WARNING]
> **Single-maintainer infrastructure.** OWTRAD is curated by one scholar
> on a personal domain, not an institutional server. Its longevity is
> impressive (>25 years) but the infrastructure is **more fragile** than
> AADR, SPAAM, or EnteroBase. Mirror any dataset you depend on **locally**
> and pin the access date.

> [!WARNING]
> **HTTPS certificate issues.** The `ciolek.com` server may serve an
> invalid or self-signed TLS certificate on `https://`. Empirically,
> plain `http://` works. When scripting fetches, use `curl -k` (skip
> verification) or pre-validate the TLS chain against the expected
> hostname. Be cautious: downgrading to HTTP defeats man-in-the-middle
> protection, consider asking the user to verify the file hash
> out-of-band if the data will drive a published argument.

## Contents

OWTRAD is organised as a set of **standalone datasets** (one file per
region × period × author), not a single consolidated dump. Naming
convention of each record page follows the pattern:

```
tmc<COUNTRY><a|m><YEAR><letter>.html
```

where `a` = ancient, `m` = medieval/modern, and `<YEAR>` is the central
year of the dataset (e.g. `tmcKGa0100d.html` is Kyrgyzstan, ancient,
~100 CE, version *d*). Each record page links to the downloadable files
for that dataset.

### Central reference tables

| Resource | Contents | Size |
|---|---|---|
| **OWTRAD Gazetteer** | Georeferenced nodes (human settlements, passes, waypoints) | **3,130 unique places** with 12,500 variant names |
| **Caravanserais & Khans catalogue** | Rest houses on long-distance routes | **756 entries** |
| **Travel/Trade Structures catalogue** | Bedestans, qaysariyyas, bridges, forts, lighthouses, markets, wells, sardobas | **328 entries** |

### Route-type taxonomy (Ciolek's classification)

OWTRAD explicitly distinguishes these network types, useful when
framing a TB dispersal hypothesis:

| Type | Relevance for pathogen dispersal |
|---|---|
| **Trade routes** | Merchant caravans, commercial transport, persistent mixing |
| **Pilgrimage routes** | Hajj, Buddhist pilgrimages, medieval European shrines, long-distance low-frequency |
| **Military routes** | Troop supply, campaigns, rapid long-distance dispersal |
| **Caravan routes** | Specific variant: desert and steppe caravans (camel, horse) |
| **Postal routes** | Horse relay, courier networks |
| **Pilgrim migration routes** | Settler movement, demographic transfer |
| **Nomadic transhumance routes** | Seasonal pastoralist movement, key for *M. bovis* reservoirs |
| **Tribute routes** | Imperial politics, periodic mass movement |
| **Signals routes** | Beacon, pigeon, semaphore, people don't physically traverse (irrelevant for pathogens) |

### Named corridors covered

| English | Also |
|---|---|
| **Silk Road** | Seidenstrasse, Route de la Soie, Ruta de la Seda |
| **Spice Route** |, |
| **Amber Route** | Bernsteinstrasse |
| **Salt Route** |, |
| **Tin Route** |, |
| **Incense Route** | (Arabian peninsula) |

## File formats

Each dataset is typically provided in several parallel formats:

| Format | Use |
|---|---|
| **MapInfo Interchange** (`.mif` + `.mid`) | Native MapInfo® format; importable into ArcGIS, QGIS, GeoPandas via GDAL/OGR |
| **KML** | Google Earth; loadable in any modern GIS / Python (e.g. `fiona`, `geopandas.read_file`) |
| **CSV** | Plain-text node lists and waypoint tables |
| **HTML tracks chart** | Narrative description of the route with annotations, often more detailed than the geometry alone |

## Why it matters for MTBC × anthropology

Three concrete uses for a TB / ancient-pathogen narrative:

1. **Silk Road and L2 Beijing / L3 CAS lineages.** The two most Central
   Asian MTBC lineages in Christophe's corpus (L2 Beijing, L3 CAS) are
   classically linked to Eurasian trans-steppe corridors. OWTRAD gives
   you **concrete geometries** of those corridors at multiple time slices,
   to overlay on lineage sampling maps from TBannotator.
2. **Caravanserais as mixing nodes.** The 756-entry catalogue of
   caravanserais/khans is a unique dataset: these were the physical
   **stopping points** where humans, pack animals, merchants, and
   pilgrims converged. They are candidate spatial attractors for
   human↔animal MTBC spillover (*M. bovis* / *M. caprae* from livestock
   to herders) and for human↔human transmission hotspots on long-distance
   trips. Nothing equivalent exists in `orbis` or `slavevoyages`.
3. **Nomadic transhumance & domestication.** OWTRAD explicitly codes
   transhumance routes, which is the closest geospatial proxy you will
   find for pastoralist mobility in the pre-modern Old World,
   directly relevant to the *M. bovis* / *M. caprae* domestication
   argument.

Unlike `orbis` (a quantitative travel-cost model for 200 CE only),
OWTRAD is **descriptive and multi-period**, and it covers the **non-Roman
world** (Central Asia, India, China, sub-Saharan Africa) that ORBIS barely
touches.

## Data access

### Option A : Browse and download individual datasets

1. Go to `http://www.ciolek.com/owtrad.html`
2. Follow *Free Online Data Sets* → the index lists datasets by region
   and period (naming convention `tmcXXa/mYYYY.html`).
3. Each dataset page offers MIF/MID, KML, CSV, and a tracks chart.
4. Record the **dataset ID + access date** in your Methods.

### Option B : Fetch a specific dataset with curl

```bash
# Example: Ancient Silk Road segment (Kyrgyzstan ~100 CE)
curl -kLO http://www.ciolek.com/OWTRAD/DATA/tmcKGa0100d.html
# Then follow the links on the HTML page to the actual geometry files.
# -k is required because the HTTPS certificate is invalid; use -L
# to follow redirects.
```

> [!NOTE]
> There is **no bulk download archive**. Each dataset is fetched
> individually. If you need many datasets, script it and **mirror
> locally** to a versioned folder you control.

### Option C : Load a KML file in Python

Once you have a KML file locally:

```python
import geopandas as gpd

routes = gpd.read_file("tmcKGa0100d.kml", driver="KML")
print(routes.columns, len(routes))
# Typical columns: geometry (LineString), Name, Description
```

Or for MapInfo:

```python
# Requires GDAL/OGR with the MapInfo driver
mif_routes = gpd.read_file("tmcKGa0100d.mif")
```

### Option D : Load the gazetteer as a CSV

The OWTRAD Gazetteer (3,130 nodes) is the most reusable cross-cutting
table: a simple lat/lon/name list you can spatially join against TB
sampling locations.

```python
import pandas as pd
gaz = pd.read_csv("owtrad_gazetteer.csv")   # download from the site
print(gaz.columns, len(gaz))
```

## Workflows

### Workflow 1 : Snap TB samples to Silk Road corridor nodes

Goal: assess how close modern L2 Beijing / L3 CAS sampling locations are
to historical Silk Road waypoints.

```python
import pandas as pd
from scipy.spatial import cKDTree

gaz = pd.read_csv("owtrad_gazetteer.csv")   # lat, lon, name, period
silk_road = gaz[gaz.route_type.str.contains("silk", case=False, na=False)]

tb = pd.read_csv("tb_samples.tsv", sep="\t")  # from TBannotator
tree = cKDTree(silk_road[["lat","lon"]].values)
d, idx = tree.query(tb[["lat","lon"]].values, k=1)
tb["nearest_silk_road_node"] = silk_road.iloc[idx]["name"].values
tb["km_to_silk_road"] = d * 111  # rough deg → km
```

Then compare the distance distribution between L2/L3 samples and
other lineages, if L2/L3 are systematically closer, that is a
quantitative hint of corridor-mediated dispersal.

### Workflow 2 : Caravanserais as mixing nodes for *M. bovis*

Goal: test whether modern *M. bovis* isolates cluster geographically
around ancient caravanserai positions.

1. Download the 756-entry caravanserai catalogue.
2. Compute pairwise nearest-distance from each *M. bovis* isolate
   (from TBannotator) to the closest caravanserai.
3. Compare with a null model (random points within the same
   geographic bounding box).
4. Narrative: *"*M. bovis* isolates sampled in modern [region] cluster
   significantly closer to pre-modern caravanserai sites than expected
   under uniform sampling, consistent with long-standing
   herder-merchant mixing nodes."*

### Workflow 3 : Overlaying on the ORBIS network

Goal: use OWTRAD for the non-Roman parts of the pre-modern world that
`orbis` does not cover (Central Asia, Arabia, East Africa, India, China)
and combine the two into a single "pre-modern connectivity" layer for
a slide.

1. Extract relevant OWTRAD routes as GeoDataFrames.
2. Extract ORBIS routes (from `orbis_v2` GitHub, `base_routes.geojson`).
3. Concatenate into one GeoDataFrame with a `source` column.
4. Plot in GeoPandas / Folium / Kepler.gl, differentiating by source
   and route type.

### Workflow 4 : Pilgrimage routes and historical outbreaks

Goal: test whether ancient Hajj pilgrimage routes correlate with
cholera pandemic dispersal (pair with `enterobase` *V. cholerae* 7PET
analysis).

1. Select OWTRAD pilgrimage-route datasets for the Islamic world.
2. Overlay on *V. cholerae* sampling sites from EnteroBase, grouped by
   HierCC cluster.
3. Discuss the role of the Hajj as a historical super-spreader network
   for enteric pathogens.

## Caveats

- **Fragility of the infrastructure.** See warnings above. Mirror locally.
- **Heterogeneous data quality.** OWTRAD datasets are contributed /
  compiled from heterogeneous analogue historical sources. Coordinate
  precision varies from <1 km (NIMA gazetteer anchors) to several
  tens of km (reconstructed routes through difficult terrain). Treat
  coordinates as **approximate**.
- **Not a quantitative travel-cost model.** OWTRAD gives you **geometries
  and types** of routes, not distances-in-days or costs. For quantitative
  modelling use `orbis` (for the Roman window) or compute network
  distances yourself on the OWTRAD geometries.
- **License is CC BY-NC 2.5.** Old-version CC licence, attribution
  required, no commercial use, no explicit share-alike. Cite the
  dataset ID, Ciolek, and the access date.
- **Single-author project** → editorial choices are not peer-reviewed
  at the level of each dataset. For high-stakes claims, cross-reference
  any specific route against the primary historical sources listed in
  the dataset's tracks chart.
- **No official DOI.** Pin the access date and, if possible, the local
  mirror hash instead.
- **Incomplete coverage of sub-Saharan Africa and the Americas.** OWTRAD
  is strongest for Eurasia and Mediterranean Africa. For the Atlantic
  world, pair with `slavevoyages`. For the Americas, there is no
  equivalent OWTRAD-like archive of precolombian routes.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`orbis`** | Roman-world quantitative network, combine for pre-modern connectivity |
| **`slavevoyages`** | Trans-Atlantic routes (post-1500), complementary geography |
| **`seshat`** | Quantitative polity history for the states along OWTRAD corridors |
| **`d-place`** | Cultural variables of the populations living along the routes |
| **`glottolog`** | Language identifiers for regional populations |
| **`p3k14c`** | Archaeological ¹⁴C for pre-literate periods of the routes |
| **`aadr`** | Ancient human genomes from Silk Road cemeteries |
| **`spaam-ancient-metagenome-dir`** | Ancient pathogen samples to overlay on corridors |
| **`enterobase`** | *Y. pestis* phylogeny, essential partner for any Silk Road / Black Death argument |
| **GeoPandas / Folium / Kepler.gl** | Mapping the routes for publication and slides |

## Citation

```bibtex
@misc{ciolek1999owtrad,
  title        = {Old World Trade Routes (OWTRAD) Project},
  author       = {Ciolek, T. Matthew},
  year         = {1999--present},
  howpublished = {Canberra: www.ciolek.com -- Asia Pacific Research Online},
  url          = {http://www.ciolek.com/owtrad.html},
  note         = {License CC BY-NC 2.5. Cite the specific dataset ID
                  (e.g. tmcKGa0100d) and the access date.}
}

@incollection{ciolek2000dromography,
  title     = {Digitising Data on Eurasian Trade Routes: An Experimental Notation System},
  author    = {Ciolek, T. Matthew},
  booktitle = {Proceedings of the Pacific Neighborhood Consortium},
  year      = {2000},
  address   = {Berkeley, CA},
  url       = {http://www.ciolek.com/PAPERS/pnc-berkeley-02.html}
}
```
