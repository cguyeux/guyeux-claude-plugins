---
name: pleiades
description: >-
  Query Pleiades, the community-built gazetteer and graph of ancient places
  (NYU ISAW + UNC AWMC), derived from the Barrington Atlas of the Greek and
  Roman World. Contains 42,000+ places with stable URIs, geocoded
  coordinates, time-period coding (Archaic → Late Antique), feature types
  (settlement, villa, fort, road, cemetery, temple, etc.), and an explicit
  graph of place-to-place connections. The reference resolver for any
  ancient toponym in the Mediterranean and circum-Mediterranean.

  Use when: resolving an ancient place name to a stable identifier and
  coordinates, geocoding historical metadata for ancient TB / Y. pestis
  samples, building a chronologically filtered map of settlements relevant
  to a phylogeographic argument, or chaining ancient toponyms to ORBIS
  (transport) and OWTRAD (trade routes) via stable IDs.
---

# Pleiades : Gazetteer and Graph of Ancient Places

## Client (resilient, tool-first)

A stdlib-only client ships with this skill (`src/pleiades_client/`, nothing to
pip-install; auto-downloads the daily places dump, gzip-aware). Filter places
without hand-rolling pandas:

```bash
SRC=<this skill>/src
PYTHONPATH="$SRC" python3 -m pleiades_client places --bbox 30 -10 47 40 --period R --feature-type settlement --tsv
PYTHONPATH="$SRC" python3 -m pleiades_client.smoke_test   # offline, bundled fixture
```

`places(bbox=(S,W,N,E), period="R", feature_type=...)` returns `list[dict]` with stable
keys `id, title, lat, lon, feature_type, time_periods, min_date, max_date, geo_context`.
`period` is a Pleiades code (A/C/H/R/L/M) matched in `timePeriods`. `PLEIADES_FILE`
overrides the source, `inspect` prints the real header, reads .csv/.csv.gz/.xlsx.

## Overview

**Pleiades** is the reference open community-curated gazetteer of ancient
places, jointly published by the **Institute for the Study of the Ancient
World (ISAW, NYU)** and the **Ancient World Mapping Center (AWMC, UNC
Chapel Hill)**. It is derived initially from the *Barrington Atlas of the
Greek and Roman World* (Princeton University Press, 2000) and continually
extended by volunteer scholars under editorial review (Senior Editor:
Roger S. Bagnall). It assigns a **stable URI** to each ancient place,
making it the de-facto authority for "Linked Ancient World Data."

- **Project URL**: `https://pleiades.stoa.org/`
- **Bulk dumps directory**: `https://atlantides.org/downloads/pleiades/dumps/`
- **License**: **CC BY 3.0** (Creative Commons Attribution) for the data
- **Hosting**: ISAW (NYU) + AWMC (UNC), supported by NEH
- **Atlas of record**: Barrington Atlas of the Greek and Roman World
  (Talbert et al., 2000), the cartographic backbone Pleiades extends
- **Verified content** (snapshot dated April 2026): **42,111 places**
  catalogued in the daily dump

> [!NOTE]
> Pleiades has **no public REST query API**. The two reproducible access
> paths are: (i) per-place stable URLs (each returns HTML, JSON, KML,
> RDF/XML, Turtle, Atom representations); (ii) the **daily CSV dumps**
> at `atlantides.org/downloads/pleiades/dumps/`. For analysis at scale,
> always use the dumps and pin the date.

## Why it matters for MTBC × anthropology

Three concrete uses:

1. **Toponym resolution for ancient samples.** Ancient pathogen samples
   from `spaam-ancient-metagenome-dir` and ancient human samples from
   `aadr` often carry free-text site names (e.g. *Vác Dominican church*,
   *Bishop Winstrup, Lund*). Pleiades is the reference resolver from
   ancient/historical toponyms to stable identifiers and coordinates,
   joinable across the constellation.
2. **Chronologically filtered settlement maps.** Each place carries
   period codes (A / C / H / R / L) so you can extract, e.g., all
   settlements occupied in the **Roman period (R)** within a region of
   interest, and overlay them on TB lineage sampling sites for narrative
   maps.
3. **Place graph for connectivity.** Pleiades places carry
   `connectsWith` / `hasConnectionsWith` fields encoding place-to-place
   relationships (administrative, contains, near, succeeds, etc.). This
   gives you a **lightweight graph of the ancient world** complementing
   the ORBIS quantitative transport model and the OWTRAD descriptive
   route geometries.

## Data model

### Place / Location / Name distinction

Pleiades distinguishes three resource classes, joined via ID:

| Resource | What it represents |
|---|---|
| **Place** | An abstract ancient place (concept), has period coding, feature types, prose description, and coordinates if known |
| **Location** | A specific spatial reference for a place (one place can have multiple locations: e.g. excavation, attested ruins, modern town) |
| **Name** | An attested ancient name for a place (one place can have several variants and translations) |

The three parallel tables are joined by:

```
location.pid  ==  name.pid  ==  place.id
```

### Time period coding

The official 5-period scheme used by Pleiades (per Bagnall et al.):

| Code | Period | Years |
|---|---|---|
| **A** | Archaic | 1000–550 BC |
| **C** | Classical | 550–330 BC |
| **H** | Hellenistic | 330–30 BC |
| **R** | Roman | AD 30–300 |
| **L** | Late Antique | AD 300–640 |
| **M** | Medieval (not in the original Bagnall scheme but observed in the data) | post-640 |

A place's `timePeriods` field is a concatenation, e.g. `RL` = Roman *and*
Late Antique, `HRL` = Hellenistic + Roman + Late Antique. This is the
column to filter on when you need a chronologically scoped subset.

### Verified distributions (April 2026 snapshot)

| timePeriods | N places |
|---|---|
| `R` (Roman only) | 7,823 |
| `RL` (Roman + Late Antique) | 7,338 |
| `L` (Late Antique only) | 2,922 |
| `HR` (Hellenistic + Roman) | 2,543 |
| `HRL` | 1,515 |
| `H` (Hellenistic only) | 1,360 |
| `M` (Medieval) | 845 |

| Feature type (top 15) | N places |
|---|---|
| settlement | 13,210 |
| **unlocated** ⚠ | 6,487 |
| villa | 2,374 |
| label | 1,772 |
| river | 1,595 |
| fort | 1,555 |
| people | 1,462 |
| archaeological-site | 1,415 |
| station | 1,404 |
| road | 1,032 |
| unlabeled | 986 |
| settlement-modern | 933 |
| cemetery | 894 |
| temple-2 | 790 |
| island | 779 |

> [!WARNING]
> **6,487 of 42,111 places (15%) are flagged `unlocated`**, they have
> no usable coordinates. Filter them out before any spatial join.
> Also inspect the `locationPrecision` column when precision matters.

## Key columns (places dump, 26 fields total)

| Column | Meaning |
|---|---|
| `id` | Stable place ID (matches `pid` in locations and names tables) |
| `uid` | Internal framework UID |
| `path` | Append to `https://pleiades.stoa.org/` to obtain canonical URL |
| `title` | Canonical English title (e.g. *Roma*, *Alexandria*) |
| `description` | Prose description of the place |
| `authors`, `creators`, `created`, `modified` | Provenance metadata |
| `featureTypes` | Comma-separated type codes (`settlement`, `villa`, `fort`, …) |
| `timePeriods` | Period codes (A / C / H / R / L / M, possibly concatenated) |
| `timePeriodsKeys`, `timePeriodsRange` | Auxiliary period encodings |
| `minDate`, `maxDate` | Numeric Julian-year bounds for sorting |
| `reprLat`, `reprLong`, `reprLatLong` | Representative point coordinates |
| `bbox` | Bounding box (when extent is known) |
| `extent` | GeoJSON of broader extent |
| `locationPrecision` | Precision flag (precise / approximate / unlocated) |
| `connectsWith`, `hasConnectionsWith` | Comma-separated IDs of related places (graph edges) |
| `tags` | Freeform tags |
| `geoContext` | Modern administrative context (e.g. country / region) |
| `currentVersion` | Version of the place record |

## Data access

### Option A : Daily CSV dumps (recommended for analysis)

```bash
mkdir -p ~/data/pleiades && cd ~/data/pleiades

# Daily snapshots, gzip-compressed
curl -LO https://atlantides.org/downloads/pleiades/dumps/pleiades-places-latest.csv.gz
curl -LO https://atlantides.org/downloads/pleiades/dumps/pleiades-locations-latest.csv.gz
curl -LO https://atlantides.org/downloads/pleiades/dumps/pleiades-names-latest.csv.gz

# Or pin a specific date for reproducibility
curl -LO https://atlantides.org/downloads/pleiades/dumps/pleiades-places-20260408.csv.gz

gunzip -k *.csv.gz
```

**Sizes** (April 2026 snapshot): places ~6.3 MB, locations ~37 MB,
names ~3.5 MB.

```python
import pandas as pd

places    = pd.read_csv("pleiades-places-latest.csv",    low_memory=False)
locations = pd.read_csv("pleiades-locations-latest.csv", low_memory=False)
names     = pd.read_csv("pleiades-names-latest.csv",     low_memory=False)

# Join name → place
joined = names.merge(places, left_on="pid", right_on="id", suffixes=("_name","_place"))
```

### Option B : Per-place URLs (single lookup)

Each place has a stable URL of the form:

```
https://pleiades.stoa.org/places/<id>
```

with content negotiation: append `/json`, `/kml`, `/turtle`, `/rdf+xml`,
or `/atom` for the corresponding representation. Example:

```bash
curl -LH "Accept: application/json" \
  https://pleiades.stoa.org/places/423025/json
```

returns the JSON record for *Roma*.

### Option C : Linked Open Data (RDF)

Pleiades is a node in the LAWDI / Pelagios linked-data graph. Whole-dataset
RDF is published by AWMC at `http://atlantides.org/downloads/pleiades/rdf/`.
Useful when chaining with other Linked Ancient World Data (Pelagios,
Nomisma, Trismegistos, Perseus).

## Workflows

### Workflow 1 : Resolve free-text ancient site names from SPAAM samples

Goal: take the `site_name` column from `spaam-ancient-metagenome-dir`
and assign a Pleiades ID + coordinates wherever possible.

```python
import pandas as pd
spaam = pd.read_csv("amdir_singlegenome_samples.tsv", sep="\t", low_memory=False)
names = pd.read_csv("pleiades-names-latest.csv", low_memory=False)
places = pd.read_csv("pleiades-places-latest.csv", low_memory=False)

# Build a normalised lookup index on attested names
names["normalised"] = names["nameAttested"].fillna("").str.lower().str.strip()

def resolve(site):
    if not isinstance(site, str): return None
    s = site.lower().strip()
    hits = names[names.normalised == s]
    if len(hits) == 0:
        # Fallback: substring match
        hits = names[names.normalised.str.contains(s, na=False)]
    if len(hits) == 0: return None
    return hits.iloc[0]["pid"]

spaam["pleiades_id"] = spaam["site_name"].apply(resolve)
spaam_geocoded = spaam.merge(
    places[["id","reprLat","reprLong","timePeriods","featureTypes"]],
    left_on="pleiades_id", right_on="id", how="left",
)
```

The unmatched rows are typically modern site names (e.g. *Vác*, *Lund
Cathedral*), the gazetteer doesn't claim to handle modern toponyms;
fall back to OpenStreetMap / Nominatim for those.

### Workflow 2 : Chronologically scoped settlement map

Goal: extract every Pleiades settlement occupied in the Roman period
within a bounding box, to plot as background context for an ORBIS or
OWTRAD overlay.

```python
mediterranean = places[
    (places.featureTypes.fillna("").str.contains("settlement", case=False))
    & (places.timePeriods.fillna("").str.contains("R"))
    & (places.reprLat.between(30, 47))
    & (places.reprLong.between(-10, 45))
    & (places.locationPrecision != "unlocated")
]
print(len(mediterranean), "Roman-period Mediterranean settlements")
```

Plot with GeoPandas and overlay TB sample locations from TBannotator.

### Workflow 3 : Chain to ORBIS via stable IDs

Goal: identify the Pleiades places that correspond to ORBIS network
nodes, so that you can display ancient site context (`featureTypes`,
`description`) on top of an ORBIS shortest-path computation.

1. Load ORBIS nodes (lat/lon + label).
2. For each ORBIS node, find the nearest Pleiades place within e.g.
   5 km that has matching `title`.
3. Inherit Pleiades period codes and feature types as attributes of
   the ORBIS node.

```python
from scipy.spatial import cKDTree
plac_geo = places.dropna(subset=["reprLat","reprLong"])
tree = cKDTree(plac_geo[["reprLat","reprLong"]].values)

# orbis_nodes: from the orbis skill
d, idx = tree.query(orbis_nodes[["y","x"]].values, k=1)
orbis_nodes["pleiades_id"] = plac_geo.iloc[idx]["id"].values
orbis_nodes["pleiades_title"] = plac_geo.iloc[idx]["title"].values
```

### Workflow 4 : Build a place graph from `connectsWith`

Goal: construct a NetworkX graph of Pleiades places connected by
explicit relationships, for centrality analysis on a subregion.

```python
import networkx as nx

G = nx.Graph()
for _, r in places.iterrows():
    G.add_node(r["id"], title=r["title"], featureTypes=r["featureTypes"])
    if isinstance(r["connectsWith"], str):
        for target in r["connectsWith"].split(","):
            target = target.strip()
            if target:
                G.add_edge(r["id"], target)

print(G.number_of_nodes(), "nodes,", G.number_of_edges(), "edges")
```

This is a sparser graph than ORBIS (Pleiades only encodes a few
relationship classes) but it covers a much wider spatial and temporal
range.

## Caveats

- **15% unlocated.** 6,487 places have no usable coordinates (April 2026
  snapshot). Always filter on `locationPrecision != "unlocated"` for
  spatial work.
- **Mediterranean and circum-Mediterranean focus.** Coverage is strongest
  for the Greek, Roman, and Late Antique world. Persian / Sasanian /
  Indian / Chinese coverage is sparse to nonexistent, use other
  gazetteers for those (CHGIS for China, TIB for Late Antique Anatolia,
  etc.).
- **Period coding is reductive.** The 5-period scheme is a coarse
  classification; for precise chronology use `minDate` / `maxDate`
  (Julian years) instead of period codes.
- **Modern toponym fallback needed.** Pleiades resolves *ancient* names.
  For sites known only by modern names (most ancient-DNA papers), you
  need a separate fallback (Nominatim, GeoNames, or manual lookup).
- **Connectivity graph is sparse.** `connectsWith` is editorially
  populated and not exhaustive. Do not interpret absence of an edge as
  absence of a real-world connection.
- **No DOI, but stable URIs.** The canonical citation is the stable URL
  per place. For dataset-level reproducibility, pin the dump filename
  (e.g. `pleiades-places-20260408.csv.gz`) and date.
- **Volunteer-curated.** As with D-PLACE and Seshat, individual records
  are uneven in depth. Always read the prose `description` and check
  the `authors` field before relying on a single record.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`orbis`** | Roman-world transport network, **chain to Pleiades via stable IDs** for chronological context |
| **`owtrad`** | Old World Trade Routes geometries, pair with Pleiades for ancient toponym lookup |
| **`seshat`** | Polity histories : Pleiades supplies place URIs for Seshat NGAs |
| **`d-place`** | Cultural variables, joinable via geographic proximity |
| **`glottolog`** | Language identifiers, many Pleiades `people` records have a Glottolog match |
| **`spaam-ancient-metagenome-dir`** | Ancient pathogen samples, use Pleiades to **resolve site names to coordinates** |
| **`aadr`** | Ancient human samples, same use case as SPAAM |
| **`p3k14c`** | Archaeological ¹⁴C : Pleiades places provide context for the dated sites |
| **`enterobase`** | *Y. pestis* / *V. cholerae* historical sites, geocoding via Pleiades |
| **Pelagios / LAWDI / Trismegistos / Nomisma** | Linked Ancient World Data ecosystem : Pleiades is the central hub |

## Citation

```bibtex
@misc{pleiades2026,
  title        = {Pleiades: A community-built gazetteer and graph of ancient places},
  author       = {{Pleiades Project}},
  editor       = {Bagnall, Roger S. and Talbert, Richard J.A. and others},
  year         = {2026},
  publisher    = {Institute for the Study of the Ancient World, NYU and
                  Ancient World Mapping Center, UNC Chapel Hill},
  url          = {https://pleiades.stoa.org/},
  note         = {Derived from the Barrington Atlas of the Greek and Roman
                  World (Talbert 2000). License CC BY 3.0. Cite the
                  per-place stable URL and pin the dump date used.}
}

@misc{talbert2000barrington,
  title     = {Barrington Atlas of the Greek and Roman World},
  editor    = {Talbert, Richard J.A.},
  year      = {2000},
  publisher = {Princeton University Press},
  address   = {Princeton}
}
```
