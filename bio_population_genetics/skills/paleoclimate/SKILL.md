---
name: paleoclimate
description: >-
  Index of open paleoclimate reconstructions for coupling pathogen
  phylogeography and historical epidemiology with past climate
  variability. Covers PAGES 2k (the reference multi-proxy global
  reconstruction of the last 2,000 years), NOAA Paleoclimatology
  (the primary WDS archive), Greenland and Antarctic ice cores
  (GISP2, NGRIP, EPICA), and WorldClim / CHELSA paleo bioclimatic
  reconstructions (LGM, Mid-Holocene). The temperature-and-climate
  layer that pairs with p3k14c / neolithic-14c / card to build
  eco-anthropological narratives.

  Use when: testing whether a MTBC lineage expansion coincides with
  a climatic warm/cold interval, correlating the Justinian plague
  with the Late Antique Little Ice Age, framing the Neolithic
  demographic transition in the context of the Holocene Climatic
  Optimum, or extracting temperature / precipitation time series
  for a given region and period.
---

# Paleoclimate — Open Climate Reconstructions for Eco-Anthropology

## Client (resilient, tool-first)

A client ships with this skill (`src/paleoclimate_client/`) that samples paleo BIO
variables at points, by time slice. Raster I/O needs **rasterio**; run via a venv
that has it:

```bash
PY=/home/christophe/venvs/geo311/bin/python
SRC=<this skill>/src
export PALEOCLIMATE_DIR=/path/to/paleoclim     # subdirs = time slices of bio_*.tif
PYTHONPATH="$SRC" $PY -m paleoclimate_client slices
PYTHONPATH="$SRC" $PY -m paleoclimate_client sample --time-slice lgm --points "41.9,12.5" --vars bio_1 --tsv
PYTHONPATH="$SRC" $PY -m paleoclimate_client.smoke_test   # offline raster fixture
```

`sample(points, variables=None, time_slice=...)` returns `list[dict]` keyed
`point_id, time_slice, lat, lon, bio_1, ...`; `time_slices()` lists the available
slices (subdirectories). Same raster engine as `worldclim-bioclim`, plus a time
dimension.

**NetCDF reconstructions** (PAGES2k, CHELSA-TraCE21k, ice-core grids) are also supported
via xarray (needs `xarray + netCDF4`, installed in the same `geo311` venv):

```bash
export PALEOCLIMATE_NC=/path/to/reconstruction.nc
PYTHONPATH="$SRC" $PY -m paleoclimate_client nc-vars
PYTHONPATH="$SRC" $PY -m paleoclimate_client sample-nc \
    --points "41.9,12.5;-12.0,-77.0" --time -6000 --vars tas,pr --tsv
```

`sample_nc(points, variables=None, time=..., lat_name=, lon_name=, time_name=)` selects
the nearest grid cell (and nearest time; most recent slice if `time` is omitted),
auto-detecting the lat/lon/time coordinate names. Tabular proxy records (CSV) still use
the generic tabular approach. A missing xarray/netCDF4 degrades to a clear
"run via venvs/geo311" message.

## Overview

Paleoclimate reconstructions quantify past temperature, precipitation,
and other climatic variables from proxy data (tree rings, ice cores,
corals, lake sediments, speleothems, historical records). For a
seminar on MTBC and human history, they provide the **climate axis**
that complements archaeological chronologies (`p3k14c`,
`neolithic-14c`, `card`) and historical records (`seshat`).

This skill indexes the main open resources, with a focus on those
with the clearest relevance to **host-pathogen coevolution narratives
in the Holocene and Common Era**.

- **Main NOAA archive**: `https://www.ncei.noaa.gov/products/paleoclimatology`
- **PAGES (Past Global Changes)**: `https://pastglobalchanges.org/`
- **World Data Service for Paleoclimatology (WDS)**: hosted by NOAA

> [!NOTE]
> Paleoclimate is a vast field with dozens of specialised archives.
> This skill indexes the **most widely used and open** resources;
> for a deeper dive, follow the references to the original papers.

## Why it matters for MTBC × anthropology

Three concrete hooks for the seminar:

1. **Late Antique Little Ice Age (LALIA) and the Justinian Plague.**
   Büntgen et al. 2016 *Nature Geoscience* identified a cold interval
   536–660 CE triggered by three volcanic eruptions in 536, 540, and
   547. This coincides with the first plague pandemic (541 CE). A
   seminar slide overlaying the LALIA temperature drop with the
   Justinian plague genomes from `spaam-ancient-metagenome-dir` /
   `enterobase` makes the climate–epidemic link visible.
2. **Medieval Climate Anomaly and the Black Death.** The 9th–13th
   centuries warm period preceded the 14th-century plague pandemic
   (Black Death, 1347–1353). The climate shift into the Little Ice
   Age in the 14th c. has been hypothesised as contributing to
   plague ecology via rodent populations.
3. **Holocene Climatic Optimum and Neolithic expansion.** The warm
   period ~9 000–5 000 BP coincides with the European Neolithic
   expansion documented in `neolithic-14c`. Cross-referencing PAGES
   2k-style reconstructions with the EUROEVOL SPD gives a joint
   climate-demographic context for the emergence of human-adapted
   MTBC.

## Main resources

### 1. PAGES 2k — the reference Common Era temperature reconstruction

- **Reference**: PAGES 2k Consortium / Neukom R., Steiger N.,
  Gómez-Navarro J.J., Wang J., Werner J.P. *Consistent multidecadal
  variability in global temperature reconstructions and simulations
  over the Common Era.* **Nature Geoscience** 12: 643–649 (2019).
  DOI: `10.1038/s41561-019-0400-0`
- **Related**: PAGES 2k Consortium (Emile-Geay et al.) *A global
  multiproxy database for temperature reconstructions of the Common
  Era.* **Scientific Data** 4: 170088 (2017). DOI:
  `10.1038/sdata.2017.88`
- **Data location**: `https://www.ncei.noaa.gov/access/paleo-search/study/26872`
  (reconstructions); `https://www.ncei.noaa.gov/access/paleo-search/study/21171`
  (raw proxy data, v2.0.0)
- **Content**: 692 temperature-sensitive proxy records (tree rings,
  corals, ice cores, lake sediments, speleothems, documentary
  records) from 7 continental-scale regions; global and regional
  temperature reconstructions at annual resolution for the past
  2000 years using 7 statistical methods
- **Coverage**: 1 CE → present, global with regional breakdowns for
  Arctic, North America, Europe, Asia, Australasia, South America,
  Africa, Antarctica

**Key finding for your seminar**: the 1st millennium CE shows cooling
episodes, the **Late Antique Little Ice Age (LALIA) around 536–660 CE**
is visible in the data, the **Medieval Climate Anomaly (~950–1250 CE)**
shows warming, and the **Little Ice Age (~1300–1850 CE)** shows
sustained cooling.

### 2. Büntgen et al. 2016 — the Late Antique Little Ice Age

- **Reference**: Büntgen U., Myglan V.S., Ljungqvist F.C., McCormick M.,
  Di Cosmo N., Sigl M., Jungclaus J., Wagner S., Krusic P.J.,
  Esper J., Kaplan J.O., de Vaan M.A.C., Luterbacher J., Wacker L.,
  Tegel W., Kirdyanov A.V. *Cooling and societal change during the
  Late Antique Little Ice Age from 536 to around 660 AD.* **Nature
  Geoscience** 9: 231–236 (2016). DOI: `10.1038/ngeo2652`
- **Content**: 1200-year tree-ring-based summer temperature
  reconstruction for the Russian Altai mountains; identifies the
  **~125-year cold period 536–660 CE** triggered by volcanic forcing
  (eruptions of 536, 540, 547); links to societal disruptions
  including the **Justinian Plague** and the Arab conquests

This single paper is the **essential citation** for a seminar
connecting climate to the Justinian plague.

### 3. Ice core records — Greenland and Antarctica

The longest continuous high-resolution climate records available.

| Ice core | Location | Depth / time | Key variables |
|---|---|---|---|
| **GISP2** | Greenland Summit | ~100k yrs | δ¹⁸O, accumulation, chemistry |
| **NGRIP** | North Greenland | ~123k yrs | δ¹⁸O, chemistry, events |
| **GRIP** | Summit Greenland | ~100k yrs | δ¹⁸O |
| **EPICA Dome C** | Antarctica | **~800k yrs** (oldest) | δD, CO₂, CH₄, dust |
| **Vostok** | East Antarctica | ~420k yrs | δD, CO₂, CH₄ |
| **WAIS Divide** | West Antarctica | ~68k yrs high-res | δ¹⁸O, CH₄, chemistry |

All archived at **NOAA WDS Paleoclimatology** or the **PANGAEA**
data repository.

Reference for GISP2 and Holocene temperature: **Alley R.B. 2000
*Quaternary Science Reviews* 19: 213–226 — *The Younger Dryas cold
interval as viewed from central Greenland.* DOI:
`10.1016/S0277-3791(99)00062-1`**

### 4. WorldClim and CHELSA — bioclimatic rasters including paleo

- **WorldClim 2.1** (Fick & Hijmans 2017 *International Journal of
  Climatology* 37: 4302–4315, DOI: `10.1002/joc.5086`) — 19
  bioclimatic variables (BIO1–BIO19) at up to 30 arcsec resolution,
  with paleo versions for the **Last Glacial Maximum (LGM, ~22 ka)**
  and **Mid-Holocene (~6 ka)** via CMIP5/CMIP6 model downscaling
- **CHELSA 2.1** (Karger et al. 2017 *Scientific Data* 4: 170122,
  DOI: `10.1038/sdata.2017.122`) — competing high-resolution
  bioclimatic product with better handling of orographic
  precipitation
- **Access**: `https://www.worldclim.org/` and `https://chelsa-climate.org/`
- **Use case**: extract bioclimatic variables at TB sampling
  locations (modern or ancient) for niche modelling

See the separate `worldclim-bioclim` skill for detailed workflows.

### 5. Speleothem archives — SISAL database

- **SISAL**: Speleothem Isotopes Synthesis and AnaLysis Working Group
  of PAGES
- **Database**: `https://www.ncei.noaa.gov/access/paleo-search/?dataTypeId=4`
  (SISAL entries) or the SISAL GitHub repository
- **Content**: global compilation of speleothem (stalagmite, stalactite)
  δ¹⁸O and δ¹³C records — the best archive for hydroclimate
  (precipitation) over the Holocene and beyond
- **Reference**: Comas-Bru L. et al. 2020 *Earth System Science Data*
  12: 2579–2606. DOI: `10.5194/essd-12-2579-2020`

### 6. NOAA Paleoclimatology — the archive umbrella

- **Portal**: `https://www.ncei.noaa.gov/products/paleoclimatology`
- **Search**: `https://www.ncei.noaa.gov/access/paleo-search/`
- **Content**: the canonical US archive for paleoclimate data
  contributions across all proxies (ice, tree ring, coral, marine
  sediment, lake sediment, speleothem, pollen, historical…)
- **License**: public domain (US government data)

Use NOAA as the **first stop** for finding any published paleoclimate
dataset — most authors deposit here.

### 7. PANGAEA — the European counterpart

- **Portal**: `https://www.pangaea.de/`
- **Host**: AWI Bremen / MARUM Bremen
- **Content**: Earth and environmental science data, including
  paleoclimate, marine sediment cores, ice cores
- **License**: CC-BY per dataset

## Data access

### Option A — NOAA Paleo Search

```bash
# Find a dataset by study ID
curl -sL "https://www.ncei.noaa.gov/access/paleo-search/study/26872" -o pages2k_reconstruction.html

# Or use the JSON API
curl -sL "https://www.ncei.noaa.gov/access/paleo-search/study/search.json?NOAAStudyId=26872"
```

Each study page has direct links to the data files (typically
tab-delimited text with metadata headers).

### Option B — R packages for paleoclimate

| Package | Purpose |
|---|---|
| **`pastclim`** | Extract paleo bioclimatic variables at points/times |
| **`paleoclim`** | Alternative paleo bioclimatic interface |
| **`PaleoSpec`** | Spectral analysis of paleo time series |
| **`sisal`** | SISAL speleothem database interface |
| **`treeclim`** | Tree-ring based climate reconstructions |

### Option C — Python tools

```bash
pip install xarray rasterio netcdf4
```

Most modern paleoclimate datasets are provided as **NetCDF** files
readable with xarray:

```python
import xarray as xr
ds = xr.open_dataset("pages2k_reconstruction.nc")
print(ds.data_vars)
# Temperature anomaly time series, bulk extraction, regional slicing
```

For proxy records in tabular format, use pandas as usual.

## Workflows

### Workflow 1 — Overlay PAGES 2k with an MTBC lineage expansion

Goal: plot the PAGES 2k global temperature reconstruction as a
background for a BEAST2 skyline (Ne(t)) of an MTBC lineage.

```python
import pandas as pd
import matplotlib.pyplot as plt

# 1. Load PAGES 2k reconstruction (download from NOAA)
pages2k = pd.read_csv("pages2k_neukom2019.txt", sep="\t",
                     comment="#")  # time, temp anomaly, uncertainty

# 2. Load the BEAST2 skyline output for your MTBC lineage
skyline = pd.read_csv("mtbc_lineage_skyline.tsv", sep="\t")
# columns: time, Ne_median, Ne_lower, Ne_upper

# 3. Dual-axis plot
fig, ax1 = plt.subplots(figsize=(10, 5))
ax2 = ax1.twinx()
ax1.plot(pages2k.time, pages2k.temp_anomaly, color="blue", alpha=0.6,
         label="PAGES 2k T anomaly")
ax2.plot(skyline.time, skyline.Ne_median, color="red", label="Ne(t)")
ax2.fill_between(skyline.time, skyline.Ne_lower, skyline.Ne_upper,
                 color="red", alpha=0.2)
ax1.set_xlabel("Year CE")
ax1.set_ylabel("T anomaly (°C)", color="blue")
ax2.set_ylabel("Ne (MTBC lineage)", color="red")
plt.title("MTBC lineage demography vs Common Era climate")
```

### Workflow 2 — Büntgen LALIA vs Justinian plague

Goal: demonstrate the temporal coincidence of the 536–660 CE cooling
with the Justinian plague (541 CE onwards).

1. Fetch the Büntgen 2016 reconstruction (supplementary data or NOAA).
2. Fetch the Justinian-plague *Y. pestis* samples from
   `spaam-ancient-metagenome-dir` (filter Wagner2014, Feldman2016,
   Keller2019).
3. Plot both on the same time axis: temperature reconstruction (blue)
   and plague-sample age distribution (red points).
4. The first cooling step (536 CE) precedes the first recorded plague
   outbreak (541 CE) by 5 years — a short enough gap to argue for a
   climate-plague coupling hypothesis.
5. Cite Büntgen 2016 + the plague genome papers + Harper 2017 *The
   Fate of Rome* for the historical narrative.

### Workflow 3 — Holocene Climatic Optimum vs Neolithic expansion

Goal: frame the EUROEVOL demographic boom-bust in the context of the
Holocene climate.

1. Load the EUROEVOL SPD from `neolithic-14c` workflow 1.
2. Load a Holocene reconstruction (e.g. Marcott et al. 2013 *Science*
   339: 1198 — DOI `10.1126/science.1228026`).
3. Plot both on the same 12 000 BP → present axis.
4. Discuss whether the Neolithic expansion aligns with the warmer
   Early Holocene, and whether the boom-bust pattern (Shennan 2013)
   correlates with climate oscillations.

### Workflow 4 — Climate at specific sampling sites

Goal: extract climate time-series at the locations of ancient MTBC
samples.

1. Use `worldclim-bioclim` for modern climate at the sample point.
2. Use PAGES 2k regional reconstructions for Common Era temperature
   at the same region (e.g. PAGES 2k Europe regional average).
3. Plot the temperature history at each ancient sampling site (Vác
   Hungary, Lund Sweden, Peru) — useful contextual panels for a
   paper.

### Workflow 5 — Volcanic forcing events

Goal: identify volcanic eruptions in the ice-core record that may
have triggered epidemics.

- **Sigl M. et al. 2015 *Nature* 523: 543–549. DOI:
  `10.1038/nature14565`** — "Timing and climate forcing of volcanic
  eruptions for the past 2,500 years". The reference eruption
  chronology from Greenland and Antarctic ice cores.
- Key events: **536 CE** (Büntgen-triggered LALIA), 540 CE, 547 CE,
  **1257 CE Samalas** (massive; preceded the Little Ice Age onset
  according to some proposals), **1815 Tambora** (Year without a
  Summer 1816).

Cross-reference with plague / cholera / TB historical records for
climate-event coincidences.

## Caveats

- **Reconstructions are not measurements.** Proxy-based reconstructions
  carry uncertainties that grow with distance from the calibration
  period (the 20th century). For the Common Era, a ±0.2–0.5°C
  uncertainty is typical. Always plot the confidence envelope.
- **Regional heterogeneity.** Global-mean reconstructions can hide
  large regional differences. PAGES 2k provides continental-scale
  reconstructions — use those when possible.
- **Proxy sampling is biased.** Tree rings dominate the Northern
  Hemisphere extratropics; corals dominate the tropics. Precipitation
  proxies are sparser than temperature proxies.
- **Correlation ≠ causation.** A temporal coincidence between climate
  and pathogen expansion does not prove causation. Cite alternative
  explanations (demographic, migratory, political).
- **Calibration varies.** Different reconstruction methods produce
  slightly different results. For a robust claim, show results from
  at least 2 independent reconstructions.
- **"Medieval Warm Period" is debated.** It was not globally
  synchronous; the term "Medieval Climate Anomaly" is preferred
  because warming was regional and not strictly warmer than modern.
- **Ice-core age models have intrinsic uncertainty.** Particularly
  deep in the core, dating uncertainties can reach decades to
  centuries.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`p3k14c`** / **`neolithic-14c`** / **`card`** | Archaeological chronologies to overlay on climate curves |
| **`seshat`** | Quantitative history of polities — pair with climate for societal collapse narratives |
| **`aadr`** / **`amtdb`** | Ancient human demography to compare with climate |
| **`spaam-ancient-metagenome-dir`** | Ancient pathogens with their dates → direct overlay with LALIA, MCA, LIA |
| **`bayesian-skyline`** | Ne(t) trajectories to overlay on climate |
| **`beast2-phylogeography`** | Time-scaled trees to anchor climate events |
| **`worldclim-bioclim`** | High-resolution modern and paleo bioclimatic rasters |
| **`pastclim`** (R) | Point-extraction interface to paleo bioclim rasters |
| **NOAA Paleoclimatology / PANGAEA** | Primary archive portals |

## Citations

```bibtex
@article{neukom2019pages2k,
  title   = {Consistent multidecadal variability in global temperature
             reconstructions and simulations over the Common Era},
  author  = {{PAGES 2k Consortium} and Neukom, Raphael and
             Steiger, Nathan and G{\'o}mez-Navarro, Juan Jos{\'e} and
             Wang, Jianghao and Werner, Johannes P.},
  journal = {Nature Geoscience},
  volume  = {12},
  pages   = {643--649},
  year    = {2019},
  doi     = {10.1038/s41561-019-0400-0}
}

@article{emilegeay2017pages2k,
  title   = {A global multiproxy database for temperature
             reconstructions of the Common Era},
  author  = {{PAGES 2k Consortium} and Emile-Geay, Julien and McKay, Nicholas P.
             and Kaufman, Darrell S. and von Gunten, Lucien and Wang, Jianghao
             and Anchukaitis, Kevin J. and others},
  journal = {Scientific Data},
  volume  = {4},
  pages   = {170088},
  year    = {2017},
  doi     = {10.1038/sdata.2017.88}
}

@article{buntgen2016lalia,
  title   = {Cooling and societal change during the Late Antique Little
             Ice Age from 536 to around 660 AD},
  author  = {Büntgen, Ulf and Myglan, Vladimir S. and Ljungqvist, Fredrik Charpentier
             and McCormick, Michael and Di Cosmo, Nicola and Sigl, Michael and
             Jungclaus, Johann and Wagner, Sebastian and Krusic, Paul J. and
             Esper, Jan and Kaplan, Jed O. and others},
  journal = {Nature Geoscience},
  volume  = {9},
  pages   = {231--236},
  year    = {2016},
  doi     = {10.1038/ngeo2652}
}

@article{sigl2015volcanic,
  title   = {Timing and climate forcing of volcanic eruptions for the
             past 2,500 years},
  author  = {Sigl, Michael and Winstrup, Mai and McConnell, Joseph R. and
             Welten, Kees C. and Plunkett, Gill and Ludlow, Francis and
             Büntgen, Ulf and Caffee, Marc and Chellman, Nathan and
             Dahl-Jensen, Dorthe and others},
  journal = {Nature},
  volume  = {523},
  pages   = {543--549},
  year    = {2015},
  doi     = {10.1038/nature14565}
}

@article{marcott2013reconstruction,
  title   = {A Reconstruction of Regional and Global Temperature for
             the Past 11,300 Years},
  author  = {Marcott, Shaun A. and Shakun, Jeremy D. and Clark, Peter U.
             and Mix, Alan C.},
  journal = {Science},
  volume  = {339},
  number  = {6124},
  pages   = {1198--1201},
  year    = {2013},
  doi     = {10.1126/science.1228026}
}
```
