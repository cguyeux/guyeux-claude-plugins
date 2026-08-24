---

name: d-place
description: >-
  Query D-PLACE (Database of Places, Language, Culture and Environment),
  the reference open database of cultural, linguistic, and environmental
  traits for 1,400+ pre-industrial human societies. Provides cross-cultural
  variables from the Ethnographic Atlas, Binford Hunter-Gatherer dataset,
  and linked bioclimatic/ecological layers, all tied to Glottolog languages
  and (for some families) Bayesian language phylogenies.

  Use when: building cultural/ecological context for the spread of a pathogen,
  testing whether a subsistence mode (pastoralism, agriculture, foraging)
  correlates with MTBC lineage distribution, controlling for phylogenetic
  non-independence in comparative cross-cultural analyses, or writing an
  eco-anthropology / bio-culture section in an article or seminar.
---

# D-PLACE : Cultural, Linguistic and Environmental Diversity of Human Societies

## Client (resilient, tool-first)

A stdlib-only client ships with this skill (`src/dplace_client/`, nothing to
pip-install). Filter societies without hand-rolling pandas:

```bash
SRC=<this skill>/src
export DPLACE_FILE=/path/to/dplace-data/csv/societies.csv
PYTHONPATH="$SRC" python3 -m dplace_client societies --bbox -35 -20 15 52 --dataset EA --tsv
PYTHONPATH="$SRC" python3 -m dplace_client.smoke_test   # offline, bundled fixture
```

`societies(bbox=(S,W,N,E), glottocode=..., family=..., dataset=...)` returns
`list[dict]` with stable keys `id, name, glottocode, lat, lon, family, dataset`. To
pull cultural variable VALUES, join D-PLACE `values.csv` / `codes.csv` separately.
`inspect` prints the real header; reads .csv/.xlsx.

## Overview

**D-PLACE** (Database of Places, Language, Culture and Environment) is the
open, community-curated reference for cross-cultural research on
pre-industrial human societies. It unifies classic ethnographic datasets
with linked linguistic classifications (Glottolog) and environmental
variables sampled at society locations, and provides time-calibrated
Bayesian language phylogenies for several major families.

- **Reference**: Kirby K.R., Gray R.D., Greenhill S.J., Jordan F.M.,
  Gomes-Ng S., Bibiko H.-J., Blasi D.E., Botero C.A., Bowern C., Ember C.R.,
  Leehr D., Low B.S., McCarter J., Divale W., Gavin M.C. *D-PLACE: A Global
  Database of Cultural, Linguistic and Environmental Diversity.* **PLOS ONE**
  11(7):e0158391 (2016). DOI: `10.1371/journal.pone.0158391`
- **Web interface**: `https://d-place.org/`
- **Data repository**: `https://github.com/D-PLACE/dplace-data`
- **Host institution**: Max Planck Institute for Evolutionary Anthropology
  (Linguistic & Cultural Evolution department)
- **License** (web portal): **CC BY-NC 4.0**, **non-commercial**
- **License** (GitHub code repository): CC BY 4.0 (but the aggregated data
  inherit the more restrictive NC terms from several source datasets, check
  per-variable metadata)
- **Citation requirement**: cite **both** Kirby et al. 2016 **and** each
  source dataset you use (EA, Binford, etc.), plus pin the data version.

> [!NOTE]
> D-PLACE does **not** expose a public REST API. Access is via the website's
> filtered downloads (CSV), the full GitHub repository, or Python/R helper
> packages. Do not invent endpoints.

## Why it matters for MTBC × anthropology

D-PLACE is the natural bridge between phylogenomic TB data and the
eco-anthropology framing of UMR 7206. Three concrete uses:

1. **Subsistence mode ↔ zoonotic MTBC.** Map the distribution of a zoonotic
   TB lineage (*M. bovis*, *M. caprae*) against societies coded as pastoralist
   vs agricultural vs hunter-gatherer in D-PLACE. A signal of enrichment in
   pastoralist societies is a strong coevolution argument.
2. **Population density & social complexity ↔ human-adapted TB persistence.**
   Human-adapted TB requires a density and contact-rate threshold. D-PLACE
   variables on settlement pattern, community size, and political complexity
   let you test this explicitly across >1,000 societies.
3. **Phylogenetic control in comparative analyses.** D-PLACE ships
   time-calibrated language phylogenies (Bantu, Austronesian, Indo-European,
   Pama-Nyungan, etc.). Using these to control for non-independence is the
   standard eco-anthropology / comparative method, and directly aligned
   with Paul Verdu's toolkit.

## Data sources (aggregated into D-PLACE)

| Dataset | Societies | Variables | Focus |
|---|---|---|---|
| **Ethnographic Atlas** (Murdock 1967, updated) | 1,291 | ~90+ cultural traits | Kinship, marriage, subsistence, religion, labor |
| **Binford Hunter-Gatherer** (Binford 2001) | 339 | ~40 | Hunter-gatherer ethnology |
| **Standard Cross-Cultural Sample (SCCS)** | 186 | ~2,000 | Deeply coded reference subsample |
| **Western North American Indians (WNAI)** | ~170 | cultural | Regional focus |
| **Environmental layers** | all societies | mean/variance/predictability of annual precipitation, temperature, NPP, species counts (birds, mammals, amphibians, plants), ecoregion, biome, elevation, slope | Sampled at society coordinates |

Linguistic classification: every society is linked to **Glottolog**
(`https://glottolog.org/`) for language family, subgroup, and ISO codes.

Phylogenies (select families): Bantu, Austronesian, Indo-European,
Pama-Nyungan, Uto-Aztecan, Sino-Tibetan, time-calibrated Bayesian trees
derived from published dated phylolinguistic analyses.

## Variable categories (thematic)

| Theme | Example variables |
|---|---|
| **Subsistence** | Gathering / hunting / fishing / animal husbandry / agriculture (% dependence); type of cultivation; intensity |
| **Social organization** | Community size; settlement pattern (nomadic → permanent); political hierarchy levels above community |
| **Kinship & marriage** | Descent rule; residence after marriage; cousin marriage preference; polygyny |
| **Religion** | High gods; ancestor worship; shamanism |
| **Material culture** | House type; metallurgy; textile production |
| **Division of labor** | Sex specialization by task |
| **Economic** | Property inheritance; class stratification; slavery |
| **Linguistic** | Glottocode, ISO 639-3, language family, subgroup |
| **Environmental** | BioClim subset (annual mean T, precipitation, seasonality, NPP), biome, ecoregion, elevation |

Variable codes are integers or short strings; the `codes.csv` table holds
human-readable labels, and the `values.csv` table holds per-society values.

## Data access

### Option A : Web UI (recommended for exploration)

1. Go to `https://d-place.org/`.
2. Use the **Societies / Variables** browsers to filter.
3. Build a custom query: pick variables, restrict to a dataset (EA / Binford
   / …), restrict to a region or language family.
4. Download as CSV / GeoJSON; also downloadable as a visualization on a
   world map or on a language tree.

### Option B : GitHub repository (recommended for analysis)

Clone the full data repository:

```bash
git clone https://github.com/D-PLACE/dplace-data.git
```

Relevant directories:

| Path | Content |
|---|---|
| `datasets/` | Per-source data (EA, Binford, SCCS, WNAI, …) in CSV |
| `csv/` | Unified flat CSV exports (`societies.csv`, `variables.csv`, `codes.csv`, `values.csv`) |
| `geo/` | Society centroid coordinates |
| `phylogenies/` | Nexus / Newick files for the Bayesian language phylogenies |
| `legacy/` | Older data formats |

Key cross-join tables (unified export, in `csv/`):

- `societies.csv`, one row per society (Glottocode, coordinates, source dataset)
- `variables.csv`, one row per cultural/environmental variable (ID, name, category)
- `codes.csv`, value code lookup (integer → label)
- `values.csv`, long-format: `(society, variable, code, source)`

### Option C : Python / R helper packages

- **`pydplace`** (Python), `pip install pydplace`, lightweight loader for
  the GitHub repo (check PyPI for current maintenance status).
- **`dplace`** R package, see CRAN or GitHub.
- **`pycldf`** (Python), if a CLDF-compliant release is published under
  `datasets/`, pycldf can load it directly (D-PLACE releases sometimes ship
  as CLDF StructureDataset).

Pin the version or commit hash in your Methods section.

## Workflows

### Workflow 1 : Pastoralism ↔ *M. bovis* lineage distribution

Goal: test whether an *M. bovis* (or *M. caprae*) sublineage is enriched in
regions inhabited historically by pastoralist societies.

1. From TBannotator, extract the modern geographic distribution of the
   lineage (country, region, lat/lon).
2. Load D-PLACE societies and EA variable **EA004** (*subsistence
   dependence on animal husbandry*, coded 0–9 in decile bins).
3. Assign each TB sample to the nearest (or same-country) EA society.
4. Compare the distribution of EA004 values in the sampled population vs a
   null expectation (random resampling of societies weighted by coverage).
5. Report: "This lineage is found disproportionately in societies with
   high animal-husbandry dependence (EA004 ≥ X), consistent with a
   pastoralist reservoir."

Snippet (pandas + geopandas):

```python
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

soc = pd.read_csv("csv/societies.csv")
val = pd.read_csv("csv/values.csv")

ea004 = val[val.var_id == "EA004"]
pastoral = (
    soc.merge(ea004, left_on="id", right_on="soc_id")
       .assign(ea004_val=lambda d: d.code.astype(int))
)

gdf_soc = gpd.GeoDataFrame(
    pastoral,
    geometry=gpd.points_from_xy(pastoral.Long, pastoral.Lat),
    crs="EPSG:4326",
)
# then spatial join to TB sample locations from TBannotator
```

### Workflow 2 : Settlement pattern ↔ human-adapted TB persistence

Goal: correlate human-adapted L4 sublineage presence with societies coded as
sedentary vs nomadic.

1. Extract EA variables on **settlement pattern** (EA030: fixity of
   residence) and **community size** (EA031).
2. Build a per-region "density proxy" from D-PLACE societies.
3. Compare with TMRCA/expansion times of the TB sublineage.

### Workflow 3 : Phylogenetic-comparative control

Goal: avoid Galton's problem when comparing cultural traits across
language-related societies.

1. Load a D-PLACE time-calibrated phylogeny (e.g., Bantu from
   `phylogenies/bantu_grollemund_et_al2015/`).
2. Map the cultural/environmental variable of interest onto the tree tips.
3. Use `phytools` (R) or `dendropy`/`ete3` (Python) for PGLS / Blomberg's K
   / ancestral state reconstruction, the same methods the éco-anthropologie
   community uses routinely.

### Workflow 4 : Ecological niche of a lineage

Goal: characterize the bioclimatic envelope where a TB lineage is found.

1. Join TB sample coordinates to D-PLACE environmental variables via
   nearest-society lookup.
2. Compare distributions of temperature / precipitation / NPP across
   lineages.
3. Complement with direct WorldClim raster queries when higher spatial
   resolution is needed : D-PLACE environmental values are society-level,
   not pixel-level.

## Caveats

- **Ethnographic present ≠ pre-contact.** Most EA coding reflects 19th- /
  early 20th-century ethnography, not pre-contact conditions. Use with
  caution for deep-time inferences.
- **Galton's problem.** Societies are not independent observations, always
  control for phylogenetic and spatial autocorrelation.
- **License heterogeneity.** Individual source datasets may impose
  non-commercial (NC) terms. Check `datasets/<source>/LICENSE.md`.
- **Coverage gaps.** The Americas and Africa are better represented than
  parts of Asia for hunter-gatherers; conversely EA is weak on industrial
  societies (by design).
- **Variable codings are interpretive.** EA codes are categorizations made
  by 20th-century anthropologists and inherit their biases, cite Murdock's
  original work and discuss limitations.
- **Not a genetic database.** D-PLACE is cultural + linguistic +
  environmental, for genetic data you still need AADR and the primary
  literature.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`aadr`** | Ancient human genomes for populations whose descendants are in D-PLACE |
| **`p3k14c`** | Archaeological chronology of domestication / sedentarization |
| **`spaam-ancient-metagenome-dir`** | Ancient pathogen reads paired with societies |
| **`enterobase`** | Non-MTBC pathogens (*Y. pestis*, *V. cholerae*) dispersed along cultural routes |
| **`slavevoyages`** | Post-1500 population displacement |
| **TBannotator MCP** | Modern TB lineage geography to join with cultural variables |
| **Glottolog** | Linguistic classification (planned skill) |
| **WorldClim** | Higher-resolution bioclimatic layers (future integration) |
| **phytools / ape** (R), **ete3 / dendropy** (Python) | Phylogenetic comparative methods on D-PLACE phylogenies |

## Citation

```bibtex
@article{kirby2016dplace,
  title   = {D-PLACE: A Global Database of Cultural, Linguistic and
             Environmental Diversity},
  author  = {Kirby, Kathryn R. and Gray, Russell D. and Greenhill, Simon J.
             and Jordan, Fiona M. and Gomes-Ng, Stephanie and Bibiko, Hans-J{\"o}rg
             and Blasi, Dami{\'a}n E. and Botero, Carlos A. and Bowern, Claire
             and Ember, Carol R. and Leehr, Dan and Low, Bobbi S. and
             McCarter, Joe and Divale, William and Gavin, Michael C.},
  journal = {PLOS ONE},
  volume  = {11},
  number  = {7},
  pages   = {e0158391},
  year    = {2016},
  doi     = {10.1371/journal.pone.0158391},
  note    = {License CC BY-NC 4.0 for web portal}
}
```

**Remember**: also cite the underlying source dataset(s) : Murdock 1967
(Ethnographic Atlas), Binford 2001 (Hunter-Gatherer), Murdock & White 1969
(SCCS), etc., and pin the data version (commit hash or release tag).

## Codex packaging note

This packaged copy targets Codex. MCP tool names in `allowed-tools` are prerequisites: verify them with `codex mcp list` in the active profile before relying on live queries.
