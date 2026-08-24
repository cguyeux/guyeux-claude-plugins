---

name: p3k14c
description: >-
  Query the p3k14c global archaeological radiocarbon database (Bird et al. 2022,
  180,070 ¹⁴C dates) to anchor MTBC lineage emergence in archaeological
  chronologies, especially animal domestication hotspots (cattle → M. bovis,
  caprines → M. caprae) and Neolithic sedentarization.

  Use when: dating the emergence of a zoonotic MTBC lineage, building a
  Neolithic/domestication narrative for an article, correlating TMRCA estimates
  with archaeological cultural periods, or identifying archaeological sites
  near modern TB strain sampling locations.
---

# p3k14c : Global Archaeological Radiocarbon Database for MTBC Contextualization

## Client (resilient, tool-first)

A stdlib-only client ships with this skill (`src/p3k14c_client/`, nothing to
pip-install). Filter the global 14C database without hand-rolling pandas:

```bash
SRC=<this skill>/src
export P3K14C_FILE=/path/to/p3k14c_raw.csv          # downloaded from tDAR
PYTHONPATH="$SRC" python3 -m p3k14c_client dates --continent SAmerica --age-bp 500 1500 --material bone --tsv
PYTHONPATH="$SRC" python3 -m p3k14c_client.smoke_test   # offline, bundled fixture
```

`dates(bbox=(S,W,N,E), age_bp=(lo,hi), material=..., continent=...)` returns
`list[dict]` with stable keys `date_id, age_bp, error, material, species, site, lat,
lon, country, continent, source` (ages uncalibrated 14C BP). `inspect` prints the
real header, reads .csv/.xlsx.

## Overview

**p3k14c** (PAGES People3000 Archaeological Radiocarbon Database) is the most
comprehensive synthetic global compilation of archaeological ¹⁴C dates currently
available. It aggregates multiple pre-existing regional databases plus dates
from publications not previously indexed, under a unified schema.

- **Reference**: Bird D., Miranda L., Vander Linden M. et al. *p3k14c, a synthetic
  global database of archaeological radiocarbon dates.* **Scientific Data** 9, 27
  (2022). DOI: `10.1038/s41597-022-01118-7`
- **Records**: 180,070 radiocarbon ages (from 272,534 raw entries)
- **Coverage**: global, with Europe (~77k) and North America (~65k) dominating
- **Temporal range**: ~55,000 BP → present (bounded by IntCal calibration limit)
- **Licenses**: data CC0 (attribution requested) · code MIT · text CC BY 4.0

**Why it matters for MTBC**: two of the biggest drivers of MTBC evolution are
(i) **animal domestication**, the ancestral host-jumps giving rise to *M. bovis*,
*M. caprae*, and related animal ecotypes, and (ii) **sedentarization and
population density thresholds** required for human-adapted TB to persist.
p3k14c provides the archaeological chronological scaffold to anchor both
phenomena.

> [!NOTE]
> p3k14c has **no public REST API**. Access is either through the R package
> (recommended for analysis) or by downloading the raw CSV from tDAR. Never
> invent an API endpoint.

## Data Access

### Option A : R package (recommended)

```r
# Install
install.packages("remotes")
remotes::install_github("people3k/p3k14c")

# Load
library(p3k14c)
data(p3k14c_data)   # cleaned/scrubbed version
str(p3k14c_data)
```

GitHub repo: `https://github.com/people3k/p3k14c`

### Option B : Raw CSV

The raw, un-scrubbed dataset is archived on **tDAR**:

- Landing page: `https://core.tdar.org/dataset/459173/p3k14c-version-202201-raw-data`
- Dataset DOI: `10.48512/XCV8459173`
- File name: `p3k14c_raw.csv`
- License: CC0

Once downloaded:

```python
import pandas as pd
df = pd.read_csv("p3k14c_raw.csv", low_memory=False)
print(df.shape, df.columns.tolist())
```

## Dataset Columns

| Field | Required | Description |
|---|---|---|
| `LabID` | ✓ | Unique laboratory identifier |
| `Age` | ✓ | Radiocarbon age (uncalibrated BP) |
| `Error` | ✓ | One-sigma standard error on `Age` |
| `Continent` | ✓ | Africa / Asia / Europe / NAmerica / SAmerica / Oceania |
| `Material` |   | Sample material (charcoal, bone, shell, wood, seed…) |
| `Taxa` |   | Taxon when applicable, **non-normalized**, copied from source |
| `δ13C` |   | Isotopic fractionation correction |
| `Method` |   | Conventional / AMS / other |
| `Period` |   | Cultural period label (free text) |
| `SiteID`, `SiteName` |   | Archaeological site identifier/name |
| `Longitude`, `Latitude` |   | Decimal degrees (WGS84) |
| `LocAccuracy` |   | Coordinate precision flag |
| `Country`, `Province`, `Region` |   | Administrative geography |
| `Source` |   | Originating database |
| `Reference` |   | Bibliographic citation |

> [!WARNING]
> The `Taxa` field is **not taxonomically standardized**, it is copied verbatim
> from the source dataset. Domesticate queries require fuzzy/regex matching
> (see snippets below).

## Key Archaeological Context for MTBC

Reference table to connect MTBC branches with archaeological horizons you are
likely to look up:

| MTBC branch | Host | Archaeological context | Approx. dates |
|---|---|---|---|
| *M. bovis* | Cattle (*Bos taurus*, *B. indicus*) | Near East + Indus domestication | ~10,500–8,000 BP |
| *M. caprae* | Goats, sheep | Zagros / Fertile Crescent caprine domestication | ~11,000–9,000 BP |
| *M. pinnipedii* | Pinnipeds (primary) + pre-Columbian humans (secondary) | Late Pleistocene / Holocene coastal sites; Pacific coast South America | variable; 500–1 000 BP for human crossover |
| *M. orygis* | Antelopes, humans (South Asia) | South Asian wild ungulates |, |
| Human L1–L9 | Humans | Post-Neolithic demographic transition | last ~10 ka |

> [!WARNING]
> **Important epistemic caveat.** As of this skill's writing, **no ancient
> DNA is published for *M. bovis*, *M. caprae*, *M. africanum*, or
> *M. canettii*** (verified against SPAAM AncientMetagenomeDir, see
> `spaam-ancient-metagenome-dir`). The only ancient MTBC lineages with
> published genomes are human-adapted *M. tuberculosis* (Kay2015, Sabin2020,
> Jager2022, all <300 BP) and ***M. pinnipedii*** in pre-contact /
> colonial-era humans (Bos2014, Vagene2022, 500–1 000 BP in Peru and
> Colombia). Any "domestication-era" narrative built from p3k14c must
> therefore be framed as a **testable hypothesis based on archaeological and
> modern-genome evidence**, not as a story backed by ancient pathogen DNA.
> The most robustly documented ancient MTBC story is currently the
> ***M. pinnipedii* in pre-Columbian Andeans** hypothesis (Bos 2014 extended
> by Vagene 2022), which connects coastal foraging, sea-mammal contact, and
> a host-jump event around the end of the 1st millennium CE.

## Workflows

### Workflow 1 : Anchor a TMRCA with archaeological evidence

1. Obtain TMRCA + 95% HPD from TBannotator / TreeTime / BEAST for a lineage of
   interest.
2. Convert the HPD interval (years CE) to calibrated BP.
3. Calibrate relevant p3k14c dates with `rcarbon::calibrate()` (see Calibration
   section below) to get calendar BP ranges.
4. Filter `p3k14c_data` on `Region`/`Country` + calibrated range.
5. When the lineage is zoonotic, filter `Taxa` for the relevant domesticate.
6. Build the narrative: *"The divergence of [lineage] at [TMRCA, HPD] coincides
   with the [cultural period] in [region], during which [N] radiocarbon-dated
   sites in p3k14c document the presence of [taxon/activity], consistent with
   a host-jump from [host] to [host]."*

### Workflow 2 : Spatial co-location of a modern sampling site

1. Obtain (lat, lon) for a modern MTBC isolate (e.g. from TBannotator metadata).
2. Compute great-circle distance to all p3k14c sites within N km:
   ```python
   from geopy.distance import great_circle
   def nearby(lat, lon, radius_km=200):
       mask = df.apply(
           lambda r: great_circle((lat, lon), (r.Latitude, r.Longitude)).km < radius_km
               if pd.notna(r.Latitude) and pd.notna(r.Longitude) else False,
           axis=1,
       )
       return df[mask]
   ```
3. Filter the result by `Period` or `Taxa` to surface only context-relevant sites.

### Workflow 3 : Neolithic demographic transition and human TB persistence

1. Compute Summed Probability Distributions (SPD) of calibrated dates per
   region using the R package `rcarbon`:
   ```r
   library(rcarbon)
   dates <- calibrate(x = subset$Age, errors = subset$Error, calCurves = "intcal20")
   spd_out <- spd(dates, timeRange = c(12000, 2000))
   plot(spd_out)
   ```
2. Identify population expansions / declines in the region of interest.
3. Compare with divergence / star-like radiations of human-adapted L4 or L2
   sublineages, population density is a prerequisite for sustained TB
   transmission chains.

## Pandas Snippets

### Load and basic summary

```python
import pandas as pd
df = pd.read_csv("p3k14c_raw.csv", low_memory=False)
print(df.Continent.value_counts())
print(df.Country.value_counts().head(20))
```

### Filter by continent and age window

```python
near_east = df[
    (df.Country.isin(["Turkey", "Iran", "Iraq", "Syria", "Jordan", "Israel", "Lebanon"]))
    & (df.Age.between(8000, 12000))   # uncalibrated BP — calibrate before reporting!
]
```

### Extract cattle / caprine domesticate entries

Because `Taxa` is unnormalized, use a permissive regex:

```python
domesticates = df[
    df.Taxa.str.contains(r"\b(Bos|Ovis|Capra|cattle|goat|sheep)\b",
                         regex=True, case=False, na=False)
]
print(domesticates.groupby(["Country", "Period"]).size().sort_values(ascending=False).head(20))
```

### Export to GeoPandas for mapping

```python
import geopandas as gpd
gdf = gpd.GeoDataFrame(
    df.dropna(subset=["Latitude", "Longitude"]),
    geometry=gpd.points_from_xy(df.Longitude, df.Latitude),
    crs="EPSG:4326",
)
gdf.to_file("p3k14c_sites.gpkg", driver="GPKG")
```

## Calibration : **do not skip**

p3k14c stores **uncalibrated** radiocarbon BP dates. Before reporting any date
in an article or comparing to a molecular-clock TMRCA, calibrate with:

- **R**, `rcarbon::calibrate(x, errors, calCurves = "intcal20")` (or
  `"shcal20"` for Southern Hemisphere, `"marine20"` for marine samples)
- **Python**, [`iosacal`](https://iosacal.readthedocs.io/) with IntCal20/SHCal20/Marine20

Reporting uncalibrated BP as if it were calendar years is a common error,
it misaligns with molecular-clock estimates by up to several thousand years.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **TBannotator MCP** | Lineage geography, TMRCA, strain metadata |
| **slavevoyages** | Historical human movement (post-1500) |
| **p3k14c** | Deep-time archaeological anchoring (this skill) |
| **rcarbon** (R) / **iosacal** (Python) | Radiocarbon calibration |
| **SITVIT2** | Spoligotype clade geography |
| **TreeTime / BEAST** | Molecular dating to compare with archaeological chronologies |

## Citation

```bibtex
@article{bird2022p3k14c,
  title   = {p3k14c, a synthetic global database of archaeological radiocarbon dates},
  author  = {Bird, Darcy and Miranda, Lux and Vander Linden, Marc and others},
  journal = {Scientific Data},
  volume  = {9},
  number  = {1},
  pages   = {27},
  year    = {2022},
  doi     = {10.1038/s41597-022-01118-7},
  note    = {Data licensed CC0; attribution requested}
}
```

## Codex packaging note

This packaged copy targets Codex. MCP tool names in `allowed-tools` are prerequisites: verify them with `codex mcp list` in the active profile before relying on live queries.
