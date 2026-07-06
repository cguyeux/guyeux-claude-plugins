---
name: orbis
description: >-
  Query ORBIS, the Stanford Geospatial Network Model of the Roman World
  (Scheidel & Meeks, ~200 CE). Provides a multimodal transport network of
  678 sites and 1,104 links (road, river, sea) with realistic travel-time,
  financial-cost, and seasonal-variation models. The authoritative source
  for quantitative pre-modern Mediterranean connectivity.

  Use when: reasoning about the spread of MTBC (or any bacterial pathogen)
  through the Roman Empire and Mediterranean basin, building a Roman-era
  dispersal hypothesis for an L4 sublineage, modeling connectivity between
  sites with ancient pathogen DNA (Justinian plague, Antonine plague), or
  anchoring a narrative on pre-modern mobility at concrete travel-cost scales.
---

# ORBIS — Stanford Geospatial Network Model of the Roman World

## Overview

**ORBIS** is the Stanford Geospatial Network Model of the Roman World,
designed by Walter Scheidel (Stanford History) and Elijah Meeks (Stanford
Digital Humanities). It simulates the Roman transport system around the
peak of the empire (~200 CE, with late-antique additions) as a
**multimodal, seasonally variable network** of roads, navigable rivers,
and sea routes, and computes realistic travel time and monetary cost
between sites using empirical data on transport modes (pedestrian, wagon,
pack animal, horse relay, sailing ship, river barge…).

- **Canonical reference**: Scheidel W. & Meeks E. (2012–2015). *ORBIS: The
  Stanford Geospatial Network Model of the Roman World.* Stanford University
  Libraries. Web URL: `https://orbis.stanford.edu/`
- **Design & implementation paper**: Meeks E. *The design and implementation
  of ORBIS: The Stanford geospatial network model of the Roman world.*
  **Bulletin of the Association for Information Science and Technology**
  41(6): 22–26 (2015). DOI: `10.1002/bult.2015.1720410206`
- **Network data deposit** (v2 nodes & edges): Stanford Digital Repository,
  `https://purl.stanford.edu/mn425tz9757`
- **Code repositories**:
  - `https://github.com/emeeks/orbis_stanford` (v1, original)
  - `https://github.com/emeeks/orbis_v2` (v2, D3.js rewrite, includes
    `base_routes.geojson`)
  - `https://github.com/sfsheath/gorbit` (Go helpers to make ORBIS data
    easier to consume)
- **License**: **CC BY 3.0 Unported** for the v2 network data (nodes/edges);
  map tiles are AWMC CC BY-NC 3.0

> [!NOTE]
> ORBIS has no REST API. Access is either through the interactive web
> interface at `orbis.stanford.edu` (session-based routing calculator) or
> by downloading the v2 node/edge tables from Stanford Digital Repository
> or the GitHub repositories and computing routes yourself with any graph
> library (NetworkX, igraph, graph-tool).

## Client (resilient, tool-first)

A **stdlib-only** client ships with this skill (`src/orbis_client/`, nothing to
pip-install, **no NetworkX needed**: Dijkstra is built in via `heapq`). It resolves
the node + edge tables, normalises their columns to a **stable schema**, and exposes
the three things ORBIS is actually used for, so you never rebuild a graph by hand:

```bash
SRC=<this skill>/src          # absolute path to orbis/src

# point it at the downloaded v2 tables (Stanford deposit or orbis_v2 repo):
export ORBIS_NODES_FILE=/path/to/orbis_nodes.csv
export ORBIS_EDGES_FILE=/path/to/orbis_edges.csv

PYTHONPATH="$SRC" python3 -m orbis_client route --from carthago --to roma --weight days
PYTHONPATH="$SRC" python3 -m orbis_client nearest --lat 36.8 --lon 10.3   # snap a TB site
PYTHONPATH="$SRC" python3 -m orbis_client matrix --sites roma,carthago,alexandria --weight days --tsv

# offline reproducibility / CI: runs against the bundled fixtures, no network
PYTHONPATH="$SRC" python3 -m orbis_client.smoke_test
```

Python API and the bridge to `coevolution`:

```python
from orbis_client import OrbisClient
orb = OrbisClient()
node, km   = orb.nearest(lat, lon)                       # 1. snap each TB site to a node
ids, costM = orb.distance_matrix(node_ids, weight="cost")  # 2. ORBIS cost/time matrix
# 3. feed costM + a phylogenetic distance matrix to a Mantel test (coevolution skill)
#    and compare against great-circle distance: does an L4 sublineage's structure
#    track Roman transport cost better than straight-line distance?
```

**Weights**: `days` (travel time), `cost` (denarii/kg of grain), `distance` (km).
The graph is **undirected by default** (symmetric matrix, ideal for Mantel); pass
`directed=True` to respect edge direction. The matrix is a square TSV (row/col =
site labels) that `coevolution`'s Mantel test consumes directly.

**Resolution cascade**: `ORBIS_NODES_FILE` / `ORBIS_EDGES_FILE` overrides -> disk
cache -> bundled fixtures -> `DatasetUnavailable`. Not auto-downloaded (no stable
file URL); `ORBIS_OFFLINE=1` forbids the network. `inspect` prints both raw headers;
a missing mapped column raises `SchemaDrift`.

## Network topology (v2)

| Metric | Value |
|---|---|
| Sites (nodes) | **678** |
| Links (edges) | **1,104** |
| Transport modes | Road, Coastal Sea, Open Sea, River |
| Seasonal variation | 12 months (or 4 seasons) |
| Transport profiles | Fast / Slow / Daylight-only; Civilian / Military |
| Cost units | Denarii per kilogram of grain (wagon baseline) |
| Time units | Days |
| Temporal focus | ~200 CE, with late-antique additions |

The deposit also emphasizes an important simplification:

> *Only the cheapest edge has been kept where parallel routes exist between
> sites, to support network-analysis tools that don't handle multiple edges
> between the same nodes.*

The interactive web version keeps parallel edges; the static tables do not.

## Data structure

### Nodes table

| Column | Meaning |
|---|---|
| `id` | Stable site identifier |
| `label` | Site name (e.g. *Roma*, *Alexandria*, *Lugdunum*) |
| `x`, `y` (or `lon`, `lat`) | Coordinates (WGS84 decimal degrees) |
| `type` | Site category (city, coastal city, river crossing, pass, …) |

### Edges table

| Column | Meaning |
|---|---|
| `source`, `target` | Node IDs of the endpoints |
| `distance_km` | Geodesic or network distance in km |
| `cost_denarii_per_kg` | Monetary cost (grain-by-wagon baseline) |
| `duration_days` | Travel time in days (varies by month & profile) |
| `type` | `road` / `river` / `coastal_sea` / `open_sea` |

For seasonal or transport-profile specific values, the v2 web model
recomputes on the fly; the static dump contains a canonical "cheapest"
representation.

## Why it matters for MTBC × anthropology

The Roman Empire is the quantitative test-bed for **pre-modern Mediterranean
connectivity**. Three concrete contributions to a TB coevolution narrative:

1. **Roman-era dispersal of TB lineage 4.** L4 is the "modern" Euro-American
   MTBC lineage, and multiple phylogenetic studies place parts of its
   diversification during the late antique / early medieval Mediterranean.
   ORBIS lets you compute concrete travel-cost distances between sampling
   sites and test whether phylogenetic distance tracks Roman transport
   cost better than great-circle distance.
2. **Justinian plague reconstruction.** The first plague pandemic (541 CE)
   spread through the Roman Mediterranean; ancient *Y. pestis* genomes
   from this period are catalogued in `spaam-ancient-metagenome-dir` and
   `enterobase`. ORBIS provides the connectivity layer for modeling its
   diffusion.
3. **Antonine / Cyprian plague narratives.** The mid-2nd and mid-3rd c.
   CE imperial epidemics (of debated pathogen identity) are core historical
   events. ORBIS lets you reason concretely about propagation timelines
   given empirical travel speeds.

Beyond plagues, ORBIS is also the right tool to anchor any argument about
**urban network size and bacterial persistence**: cities connected at less
than ~N days' travel from Rome share a metapopulation and can sustain
obligate human pathogens like human-adapted MTBC that require high host
densities.

## Data access

### Option A — Interactive web UI (exploration)

1. Go to `https://orbis.stanford.edu/`
2. Select an origin and a destination site.
3. Set priority (**Fastest / Cheapest / Shortest**), season, and
   transport profile (road/river/sea mix; civilian/military; fast/slow;
   daylight).
4. The model returns the route, travel time in days, and total cost.
5. Useful for quick narrative work and producing figures for a talk —
   you can screenshot the route map.

### Option B — Stanford Digital Repository (static node/edge tables)

1. Navigate to `https://purl.stanford.edu/mn425tz9757`.
2. Download the node and edge CSVs.
3. Load as a NetworkX graph:

```python
import pandas as pd
import networkx as nx

nodes = pd.read_csv("orbis_nodes.csv")
edges = pd.read_csv("orbis_edges.csv")

G = nx.DiGraph()
for _, r in nodes.iterrows():
    G.add_node(r["id"], label=r["label"], pos=(r["x"], r["y"]))
for _, r in edges.iterrows():
    G.add_edge(
        r["source"], r["target"],
        distance=r["distance_km"],
        cost=r["cost_denarii_per_kg"],
        days=r["duration_days"],
        type=r["type"],
    )
```

### Option C — GitHub repositories

```bash
git clone https://github.com/emeeks/orbis_v2.git
# contains base_routes.geojson and the web-app source

git clone https://github.com/sfsheath/gorbit.git
# Go helpers that bundle the data for programmatic use
```

The `base_routes.geojson` in `orbis_v2` is directly loadable in GeoPandas /
QGIS / Leaflet.

## Workflows

> Prefer the **client** (`python -m orbis_client route|matrix|nearest`, see above)
> over rebuilding a NetworkX graph by hand; the snippets below show the equivalent
> logic and the GeoPandas mapping steps the client does not cover.

### Workflow 1 — Test a Roman-era dispersal hypothesis for an L4 sublineage

Goal: check whether a sublineage found in multiple Mediterranean sites has
a phylogeographic signal better explained by ORBIS cost distance than by
straight-line distance.

```python
import networkx as nx
# Assume G built as above, and tb_sites is a DataFrame with TB sampling
# coordinates; snap each to the nearest ORBIS node.

def snap_to_orbis(lat, lon, nodes_df):
    import numpy as np
    d2 = (nodes_df.y - lat)**2 + (nodes_df.x - lon)**2
    return nodes_df.iloc[d2.idxmin()]["id"]

tb_sites["orbis_node"] = tb_sites.apply(
    lambda r: snap_to_orbis(r.lat, r.lon, nodes), axis=1,
)

# Pairwise shortest-path cost
cost_matrix = dict(nx.all_pairs_dijkstra_path_length(G, weight="cost"))
time_matrix = dict(nx.all_pairs_dijkstra_path_length(G, weight="days"))
```

Then correlate pairwise phylogenetic distance (from a TB tree) with:
- Great-circle distance (baseline)
- ORBIS cost distance
- ORBIS time distance

If the ORBIS metrics explain more variance, that is direct quantitative
support for a Roman-era dispersal narrative.

### Workflow 2 — Justinian plague diffusion timing

Goal: given the ancient *Y. pestis* genomes from the Justinian plague
catalogued in `spaam-ancient-metagenome-dir` (Keller 2019, Wagner 2014,
Feldman 2016, etc.) and their sampling sites, model the minimum travel
time from Pelusium (the reported origin, 541 CE) to each site.

```python
origin = "pelusium"  # Nile Delta, where Procopius reports the outbreak
travel_time = nx.shortest_path_length(G, origin, weight="days")
```

Compare with the historical chronology of outbreaks reported by Procopius,
Evagrius, etc., and ask: does ORBIS travel time correlate with the time
it took the pandemic to reach each city?

### Workflow 3 — Metropolitan connectivity and human-adapted TB persistence

Goal: test whether the N cities best connected to Rome (by ORBIS cost
distance) had the highest bacterial population loads / diversity in
human-adapted MTBC (if ancient DNA is available) or modern TB isolates.

1. Compute betweenness centrality and closeness centrality in ORBIS.
2. For each site, extract TB lineage diversity from TBannotator.
3. Correlate centrality with lineage richness controlling for sampling
   effort (this is a rough null-breaking test).

### Workflow 4 — Reconstruct a trade / military route for a narrative slide

Goal: produce a publication-ready map for a seminar slide showing the
modeled route between two specific sites.

1. Use the interactive UI for the route + cost/time numbers → screenshot.
2. Or compute the path yourself from the static dump:

```python
path = nx.shortest_path(G, "carthago", "roma", weight="days")
print(" → ".join(G.nodes[n]["label"] for n in path))
print("Total:",
      nx.shortest_path_length(G, "carthago", "roma", weight="days"), "days")
```

3. Export the path as a GeoDataFrame and plot on a map with coastlines.

## When NOT to use

- **Any period that is not ~200 CE.** ORBIS is one imperial snapshot. For medieval
  or post-Roman networks use `owtrad` (Old World trade routes); for the
  trans-Atlantic window use `slavevoyages`.
- **Non-Roman regions.** Central Asia, sub-Saharan Africa, northern Europe are
  almost absent; ORBIS silence is not historical isolation.
- **A transmission model.** ORBIS gives a connectivity *prior* (cost / time), not a
  pathogen transmission rate; density and contact intensity at endpoints matter.
- **The Mantel test itself.** This skill produces the ORBIS distance matrix; run the
  test with `coevolution` (Mantel / partial Mantel against a phylogenetic matrix).
- **Pathogen or host genomes.** Use `spaam-ancient-metagenome-dir` / `enterobase`
  (pathogen) and `aadr` (host); ORBIS is the connectivity layer only.

## Caveats

- **One snapshot (~200 CE).** ORBIS models the empire at its peak. It is
  **not** a dynamic model covering the Republic, the Crisis, or the late
  empire transportation regime — and it specifically does **not** model
  post-Roman networks. For other periods you need a different source
  (medieval: ORBIS Latinus, *OWTRAD*, Silk Road networks…).
- **Cheapest-edge simplification in the static dump.** Where parallel
  routes exist, only the cheapest is retained in the node/edge deposit.
  This is fine for most network-analysis work but will bias multi-mode
  comparisons.
- **Travel cost ≠ pathogen transmission rate.** Cost models human movement;
  MTBC transmission depends on demographic density and contact intensity
  at endpoints. ORBIS gives you a connectivity *prior*, not a transmission
  model.
- **Coordinates are stylized.** Node positions are approximately historical,
  sometimes rounded — don't treat them as archaeological precision.
- **Map tile license is stricter than data.** If you reuse ORBIS screenshots
  in a commercial product, note that the AWMC basemap is CC BY-NC 3.0 even
  though the v2 network data are CC BY.
- **Pre-modern connectivity ≠ Roman only.** Non-Roman regions (central Asia,
  sub-Saharan Africa, northern Europe) are almost absent. Do not interpret
  ORBIS silence as historical isolation.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`spaam-ancient-metagenome-dir`** | Ancient *Y. pestis*, *S. enterica* etc. from Roman & post-Roman sites |
| **`aadr`** | Ancient human genomes from Roman-era skeletons |
| **`enterobase`** | Modern / ancient *Y. pestis*, *V. cholerae*, *S. enterica* phylogenies |
| **`p3k14c`** | Archaeological ¹⁴C for dating Roman and pre-Roman sites |
| **`d-place`** | Cultural context of non-Roman populations at the imperial periphery |
| **`glottolog`** | Language identifiers for ancient Mediterranean populations |
| **`slavevoyages`** | Post-Roman analogue (trans-Atlantic connectivity, much later) |
| **TBannotator MCP** | Modern TB lineage geography to snap onto ORBIS nodes |
| **NetworkX / igraph / graph-tool** | Computing shortest paths, centralities, distance matrices |
| **GeoPandas** | Spatial joins, mapping routes for publication figures |

## Citations

```bibtex
@misc{scheidel2012orbis,
  title     = {ORBIS: The Stanford Geospatial Network Model of the Roman World},
  author    = {Scheidel, Walter and Meeks, Elijah},
  year      = {2012},
  publisher = {Stanford University Libraries},
  url       = {https://orbis.stanford.edu/},
  note      = {License CC BY 3.0 Unported for the network data}
}

@article{meeks2015orbis,
  title   = {The design and implementation of ORBIS: The Stanford geospatial
             network model of the Roman world},
  author  = {Meeks, Elijah},
  journal = {Bulletin of the Association for Information Science and Technology},
  volume  = {41},
  number  = {6},
  pages   = {22--26},
  year    = {2015},
  doi     = {10.1002/bult.2015.1720410206}
}
```
