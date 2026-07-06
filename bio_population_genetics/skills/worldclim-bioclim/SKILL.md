---
name: worldclim-bioclim
description: >-
  Use WorldClim 2.1 and CHELSA v2.1 — the two reference high-resolution
  global bioclimatic raster datasets (19 BIO variables at up to 1 km
  resolution, present-day and paleo versions for LGM and Mid-Holocene).
  The canonical substrate for ecological niche modelling of pathogens,
  climate-at-point extraction for TB sampling locations, and
  high-resolution climate overlays on phylogeographic maps. Complements
  paleoclimate time-series reconstructions with the spatial raster view.

  Use when: extracting bioclimatic variables at modern or ancient TB
  sampling sites, modelling the climatic niche of an MTBC lineage,
  comparing niches of M. bovis vs M. caprae vs M. tuberculosis,
  producing climate overlay layers for a phylogeographic map, or
  computing niche overlap statistics between pathogen ecotypes.
---

# WorldClim 2.1 and CHELSA — High-Resolution Bioclimatic Rasters

## Client (resilient, tool-first)

A client ships with this skill (`src/wcbio_client/`) that samples the 19 BIO
variables at lat/lon points. Raster I/O needs **rasterio** (not stdlib), so run it via
a venv that has it:

```bash
PY=/home/christophe/venvs/geo311/bin/python   # a venv with rasterio installed
SRC=<this skill>/src
export WORLDCLIM_DIR=/path/to/wc2.1_10m       # directory of bio_*.tif
PYTHONPATH="$SRC" $PY -m wcbio_client variables
PYTHONPATH="$SRC" $PY -m wcbio_client sample --points "41.9,12.5;-12.0,-77.0" --vars bio_1,bio_12 --tsv
PYTHONPATH="$SRC" $PY -m wcbio_client.smoke_test    # offline raster fixture
```

`sample(points, variables=None)` (points = `(id, lat, lon)`) returns `list[dict]`
keyed `point_id, lat, lon, bio_1, ...`. Resolves a directory of single-band BIO
GeoTIFFs (`WORLDCLIM_DIR`); `WORLDCLIM_OFFLINE=1` forces the bundled fixture; a missing
rasterio degrades to a clear "run via venvs/geo311" message. WorldClim 2.1 temperature
BIO are in degrees C (older v1 were x10 — check your release).

## Overview

**WorldClim 2.1** and **CHELSA v2.1** are the two reference open
global high-resolution bioclimatic raster datasets for ecological
niche modelling and point-based climate extraction. Both provide
the classical **19 BIO variables** (BIO1–BIO19) derived from
monthly minimum, maximum, and mean temperature and precipitation,
at resolutions from 10 arc-minutes (~18 km) down to 30 arc-seconds
(~1 km). Both offer present-day climatologies plus **paleo**
reconstructions for the Last Glacial Maximum (LGM, ~22 ka BP),
Mid-Holocene (~6 ka BP), and Last Inter-Glacial (~120 ka BP).

| Dataset | Author | Reference period | Min resolution | Latest paper |
|---|---|---|---|---|
| **WorldClim 2.1** | Fick & Hijmans (UC Davis) | 1970–2000 | **30 arcsec (~1 km)** | Fick & Hijmans 2017 *IJC* |
| **CHELSA v2.1** | Karger et al. (WSL/ETH Zürich) | 1981–2010 | **30 arcsec (~1 km)** | Karger et al. 2017 *Sci Data* |
| **PaleoClim** | Brown et al. (aggregator) | Paleo snapshots (LGM, MH, LIG) | 2.5 arcmin | Brown et al. 2018 *Sci Data* |

- **WorldClim portal**: `https://www.worldclim.org/`
- **CHELSA portal**: `https://chelsa-climate.org/`
- **PaleoClim aggregator**: `http://www.paleoclim.org/`
- **License**: CC BY 4.0 for both main datasets
- **Format**: GeoTIFF (single-band per variable per time slice), also
  available as NetCDF

> [!NOTE]
> WorldClim and CHELSA are **competing products** with different
> statistical methodologies. CHELSA handles orographic precipitation
> better (a known WorldClim weakness in mountainous regions). For
> robust analyses, run both and report the sensitivity.

## The 19 bioclimatic variables

| Code | Variable | Unit |
|---|---|---|
| BIO1 | Annual Mean Temperature | °C (2.1) — ×10 en 1.4 |
| BIO2 | Mean Diurnal Range (monthly max–min) | °C (2.1) — ×10 en 1.4 |
| BIO3 | Isothermality (BIO2 / BIO7) × 100 | — |
| BIO4 | Temperature Seasonality (std. dev. × 100) | — |
| BIO5 | Max Temperature of Warmest Month | °C (2.1) — ×10 en 1.4 |
| BIO6 | Min Temperature of Coldest Month | °C (2.1) — ×10 en 1.4 |
| BIO7 | Temperature Annual Range (BIO5 − BIO6) | °C (2.1) — ×10 en 1.4 |
| BIO8 | Mean Temperature of Wettest Quarter | °C (2.1) — ×10 en 1.4 |
| BIO9 | Mean Temperature of Driest Quarter | °C (2.1) — ×10 en 1.4 |
| BIO10 | Mean Temperature of Warmest Quarter | °C (2.1) — ×10 en 1.4 |
| BIO11 | Mean Temperature of Coldest Quarter | °C (2.1) — ×10 en 1.4 |
| BIO12 | Annual Precipitation | mm |
| BIO13 | Precipitation of Wettest Month | mm |
| BIO14 | Precipitation of Driest Month | mm |
| BIO15 | Precipitation Seasonality (CV) | — |
| BIO16 | Precipitation of Wettest Quarter | mm |
| BIO17 | Precipitation of Driest Quarter | mm |
| BIO18 | Precipitation of Warmest Quarter | mm |
| BIO19 | Precipitation of Coldest Quarter | mm |

> [!WARNING]
> **Temperature encoding depends on the WorldClim version.**
> - **WorldClim 2.1** (this skill's default, `wc2.1_*`): temperature BIO
>   are **float °C already** — do **NOT** divide by 10.
> - **WorldClim 1.4** (legacy integer GeoTIFFs): stored as **°C × 10** —
>   divide by 10.
> - **CHELSA v2.1**: float °C (some products use offset/scale in metadata —
>   read the band `scale`/`offset`).
>
> Check `rasterio`'s reported dtype: float32 ⇒ already °C (2.1); int16 with
> values like 234 ⇒ ×10 (1.4). Applying the ×10 rule to 2.1 gives
> temperatures **10× too low** — a silent, common error.

## Why it matters for MTBC × anthropology

Three concrete uses:

1. **Climatic niche of MTBC lineages.** Extract BIO1–BIO19 at all
   modern *M. bovis* sampling locations from TBannotator, and
   compare with *M. caprae*, *M. pinnipedii*, and human-adapted
   lineages. Quantitative niches can be compared with **niche
   overlap metrics** (Schoener's D, Hellinger I, Warren's I).
2. **Paleo niche at ancient sites.** Extract LGM / Mid-Holocene
   bioclimatic values at ancient TB sampling sites (Vác, Lund,
   Peru) to contextualise the environment the ancient individuals
   lived in.
3. **High-resolution climate overlays for phylogeographic maps.**
   Unlike `d-place` (society-level point climate) and `paleoclimate`
   (time series), WorldClim/CHELSA give you the **full 2D raster
   at km-scale** — ready for publication-grade choropleth maps
   overlaid with lineage sampling points.

## Data access

### Option A — WorldClim direct download

```bash
mkdir -p ~/data/worldclim && cd ~/data/worldclim

# Present-day 30 arcsec (~1 km) — the finest resolution
wget "https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_30s_bio.zip"
unzip wc2.1_30s_bio.zip
# Produces 19 GeoTIFFs: wc2.1_30s_bio_1.tif, ..., wc2.1_30s_bio_19.tif
```

Available resolutions:

| Resolution | Approx km | URL fragment |
|---|---|---|
| 30 arcsec | ~1 km | `30s` |
| 2.5 arcmin | ~4.5 km | `2.5m` |
| 5 arcmin | ~9 km | `5m` |
| 10 arcmin | ~18 km | `10m` |

### Option B — WorldClim paleo (LGM, Mid-Holocene)

```bash
# Mid-Holocene (6 ka BP), CCSM4 model, 2.5 arcmin
wget "https://geodata.ucdavis.edu/cmip6/2.5m/ACCESS-CM2/ssp126/wc2.1_2.5m_bioc_ACCESS-CM2_ssp126_2021-2040.tif"
# (adjust the URL for your target model and time period)
```

WorldClim 2.1 paleo uses downscaled CMIP5 / CMIP6 climate model
output — not a direct reconstruction, but a physically consistent
model-based estimate.

### Option C — CHELSA

```bash
mkdir -p ~/data/chelsa && cd ~/data/chelsa

# Present-day annual temperature (BIO1) at 30 arcsec
wget "https://os.zhdk.cloud.switch.ch/envicloud/chelsa/chelsa_V2/GLOBAL/climatologies/1981-2010/bio/CHELSA_bio1_1981-2010_V.2.1.tif"
```

CHELSA v2.1 covers 1981–2010 and includes 30 arcsec present-day
data plus paleo timeslices via CHELSA-TraCE21k (a transient
simulation back to 21 ka BP).

### Option D — PaleoClim aggregator

- `http://www.paleoclim.org/` provides paleo bioclimatic variables
  from multiple sources (WorldClim, CHELSA, others) in a unified
  format for several time slices: Late Holocene, Mid-Holocene, Early
  Holocene, Younger Dryas, Bølling-Allerød, Heinrich 1, LGM, Last
  Interglacial, Marine Isotope Stage 19 (~787 ka BP)
- Reference: Brown J.L. et al. 2018 *Scientific Data* 5: 180254.
  DOI: `10.1038/sdata.2018.254`
- Convenient single-stop shop when you want several paleo time slices
  in a consistent format

### Option E — `pastclim` R package

The **most convenient** interface for programmatic point-based
extraction across multiple time slices:

```r
# Install
remotes::install_github("EvolEcolGroup/pastclim")
library(pastclim)

# Download WorldClim 2.1 present-day
download_dataset("WorldClim_2.1_10m")

# Extract bioclimatic variables at TB sampling points
pts <- data.frame(x = c(28.1, -77.0), y = c(21.7, -12.0),
                  time = c(0, 0))  # BP (0 = present)
climate_for_locations(pts, dataset = "WorldClim_2.1_10m",
                      bio_variables = c("bio01", "bio12"))
```

`pastclim` also handles PaleoClim's paleo time slices through the
same API. This is the **recommended path** for anyone already in R.

### Option F — Python `xarray` + `rasterio`

```python
import rasterio
import pandas as pd

# Load BIO1 (annual mean temperature)
with rasterio.open("wc2.1_30s_bio_1.tif") as src:
    # Sample at a list of (lon, lat) points
    tb_sites = pd.read_csv("tb_samples.tsv", sep="\t")
    coords = list(zip(tb_sites.longitude, tb_sites.latitude))
    values = [v[0] for v in src.sample(coords)]
    # WorldClim 2.1 : deja en °C (float). NE PAS diviser par 10.
    tb_sites["bio1_temp_C"] = values
    # (WorldClim 1.4 seulement : tb_sites["bio1_temp_C"] = [v/10.0 for v in values])
```

## Workflows

### Workflow 1 — Extract bioclimatic variables at MTBC sampling sites

Goal: produce a table of BIO1–BIO19 values at every TBannotator
sample location.

```python
import pandas as pd
import rasterio

tb = pd.read_csv("tb_samples.tsv", sep="\t")
coords = list(zip(tb.longitude, tb.latitude))

bio_values = {}
for v in range(1, 20):
    with rasterio.open(f"wc2.1_30s_bio_{v}.tif") as src:
        bio_values[f"bio{v}"] = [val[0] for val in src.sample(coords)]

bio_df = pd.DataFrame(bio_values)
# WorldClim 2.1 : bio1–bio11 sont deja en °C (float) — NE PAS diviser.
# Pour du WorldClim 1.4 (int16, °C×10) uniquement :
#   for v in range(1, 12): bio_df[f"bio{v}"] = bio_df[f"bio{v}"] / 10.0

tb_climate = pd.concat([tb.reset_index(drop=True), bio_df], axis=1)
```

### Workflow 2 — Niche overlap between MTBC ecotypes

Goal: compute Schoener's D niche overlap between *M. bovis*,
*M. caprae*, and human-adapted L4.

```python
from sklearn.neighbors import KernelDensity
import numpy as np

# For each ecotype, extract bioclimatic values at sampling points
# (see Workflow 1)
# Then fit a kernel density in bioclimatic space
def fit_kde(df, vars=("bio1", "bio12")):
    x = df[list(vars)].dropna().values
    return KernelDensity(bandwidth=0.5).fit(x)

bovis_kde  = fit_kde(m_bovis_sites)
caprae_kde = fit_kde(m_caprae_sites)
l4_kde     = fit_kde(l4_sites)

# Schoener's D: sum over grid of |p1(x) - p2(x)| / 2
# Code not shown — use ecospat or similar for rigorous niche overlap
```

The **`ENMeval`**, **`dismo`**, and **`ecospat`** R packages are the
canonical tools for rigorous niche overlap calculation.

### Workflow 3 — Paleo climate at ancient MTBC sites

Goal: get LGM and Mid-Holocene bioclimatic values at ancient sample
locations to contextualise the environment at time of infection.

```r
library(pastclim)

# Load the ancient sample metadata
ancient <- read.csv("ancient_mtbc_samples.tsv", sep = "\t")
# Columns: sample_name, latitude, longitude, age_bp

# For each sample, extract climate at its age (or the nearest available slice)
climate <- climate_for_locations(
  data.frame(x = ancient$longitude, y = ancient$latitude,
             time = -ancient$age_bp),  # pastclim uses negative BP
  dataset = "Beyer2020",   # Beyer et al. 2020 is a recommended paleo dataset
  bio_variables = c("bio01", "bio12")
)
```

### Workflow 4 — Niche-model prediction for a lineage

Goal: train a niche model on known *M. bovis* occurrences and
predict its potential range under current and paleo climates.

1. Assemble a presence dataset of *M. bovis* sampling sites from
   TBannotator.
2. Assemble a background (pseudo-absence) sample — random points
   in the study region (e.g. Europe).
3. Train a **MaxEnt** or **Random Forest** model with
   `dismo::maxent()` or `ENMeval` on the 19 bioclimatic variables.
4. Predict the suitable range under present-day WorldClim.
5. Re-project the model onto LGM / Mid-Holocene bioclimatic rasters
   to see how the potential range shifted with Holocene climate.
6. Compare with the modern observed distribution to identify
   refugia, colonisation fronts, or anthropogenic niche expansion.

### Workflow 5 — Climate overlay for a Nextstrain map

Goal: add a bioclimatic background layer to a phylogeographic map
produced in Auspice or externally.

1. Extract the mean annual temperature (BIO1) and annual precipitation
   (BIO12) for a bounding box covering your lineage's distribution.
2. Render as a colour-coded raster in GeoPandas / rasterio / Folium.
3. Overlay the lineage sampling points and the tree-inferred
   migration routes (from `beast2-phylogeography` or `pastml`).
4. The climate-coloured background supports a narrative like
   *"the lineage expansion traces a corridor of moderate temperature
   and high precipitation, consistent with its predicted climatic
   niche"*.

## Caveats

- **Temperature encoding is version-dependent.** WorldClim **2.1** BIO1–BIO11
  are float °C — do **not** divide. Only WorldClim **1.4** (int16) is °C×10.
  Applying ×10 to 2.1 gives temperatures 10× too low — **the** recurring bug.
- **Projection and coordinate system.** All WorldClim/CHELSA rasters
  are in EPSG:4326 (WGS84 geographic lat/lon). If you need a
  projected system for distance calculations, reproject with
  rasterio or GDAL.
- **Version drift.** WorldClim 1.4 and 2.0 are still in circulation;
  use **2.1 (2020)** as the current stable version and pin it.
- **Paleo reconstructions are model-based.** LGM and Mid-Holocene
  bioclimatic layers come from climate-model downscaling, not from
  proxy data directly. They carry model-structural uncertainty.
  Use several models and report the range.
- **Sampling bias.** Modern TB sampling locations over-represent
  high-income countries with strong surveillance. A niche model
  built on this is skewed.
- **WorldClim vs CHELSA differ.** Especially in mountains and arid
  regions. Report sensitivity to the choice of product.
- **Resolution matters.** 30 arcsec gives the crispest maps but
  ~5 GB per variable globally; 10 arcmin is often sufficient for
  continental-scale analyses at ~200 MB per variable.
- **GeoTIFF file size.** A global 30-arcsec raster is ~700 MB per
  variable uncompressed. Use cloud-optimized GeoTIFFs (COG) when
  possible for incremental access.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`paleoclimate`** | Time-series reconstructions (PAGES 2k, Büntgen, ice cores) — complementary to WorldClim's spatial view |
| **`d-place`** | Society-level bioclimatic summaries — WorldClim is the raster version |
| **`p3k14c`** / **`neolithic-14c`** / **`card`** | Archaeological sites to extract paleo climate at |
| **`aadr`** / **`amtdb`** | Ancient human sites — extract present + paleo climate |
| **`spaam-ancient-metagenome-dir`** | Ancient pathogen sites for climate context |
| **`beast2-phylogeography`** / **`pastml`** | Phylogeographic inference — climate as a covariate or background |
| **`pastclim`** (R) | Convenient interface to WorldClim + PaleoClim + Beyer2020 |
| **`rasterio`** / **`xarray`** (Python) | Raster manipulation |
| **`dismo`** / **`ENMeval`** / **`ecospat`** (R) | Niche modelling and niche overlap |
| **GeoPandas** / **Folium** / **QGIS** | Mapping and visualisation |

## Citations

```bibtex
@article{fick2017worldclim2,
  title   = {WorldClim 2: new 1-km spatial resolution climate surfaces
             for global land areas},
  author  = {Fick, Stephen E. and Hijmans, Robert J.},
  journal = {International Journal of Climatology},
  volume  = {37},
  number  = {12},
  pages   = {4302--4315},
  year    = {2017},
  doi     = {10.1002/joc.5086}
}

@article{karger2017chelsa,
  title   = {Climatologies at high resolution for the earth's land
             surface areas},
  author  = {Karger, Dirk Nikolaus and Conrad, Olaf and Böhner, Jürgen
             and Kawohl, Tobias and Kreft, Holger and Soria-Auza, Rodrigo W.
             and Zimmermann, Niklaus E. and Linder, H. Peter and Kessler, Michael},
  journal = {Scientific Data},
  volume  = {4},
  pages   = {170122},
  year    = {2017},
  doi     = {10.1038/sdata.2017.122}
}

@article{brown2018paleoclim,
  title   = {PaleoClim, high spatial resolution paleoclimate surfaces
             for global land areas},
  author  = {Brown, Jason L. and Hill, Daniel J. and Dolan, Aisling M. and
             Carnaval, Ana C. and Haywood, Alan M.},
  journal = {Scientific Data},
  volume  = {5},
  pages   = {180254},
  year    = {2018},
  doi     = {10.1038/sdata.2018.254}
}

@article{beyer2020pastclim,
  title   = {High-resolution terrestrial climate, bioclimate and
             vegetation for the last 120,000 years},
  author  = {Beyer, Robert M. and Krapp, Mario and Manica, Andrea},
  journal = {Scientific Data},
  volume  = {7},
  pages   = {236},
  year    = {2020},
  doi     = {10.1038/s41597-020-0552-1}
}
```

**Remember**: in Methods, state the exact dataset version (e.g.
*WorldClim 2.1, 30 arcsec, accessed YYYY-MM-DD*) and the spatial
resolution. Temperature values must be reported in °C, not °C × 10.