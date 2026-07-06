---
name: neolithic-14c
description: >-
  Index of regional radiocarbon databases for the Neolithic and adjacent
  periods — EUROEVOL (European Neolithic, 14,053 dates from 4,757 sites,
  Shennan/Manning et al. UCL), NERD (Near East, 11,072 dates from 1,027
  sites, Palmisano et al.), plus RADON (Central Europe), NeoNet
  (Mediterranean), and the Radiocarbon Palaeolithic Europe Database (KU
  Leuven). Together they give continuous ¹⁴C coverage from the primary
  Near Eastern domestication centre through the secondary European
  expansion — the ideal substrate for building demographic-transition
  and farming-expansion arguments for MTBC / M. bovis narratives.

  Use when: building a Neolithic demographic transition argument for
  the rise of human-adapted MTBC, mapping the arrival of farming and
  animal husbandry across Europe in relation to a TB phylogeny,
  producing summed probability distribution (SPD) plots of population
  dynamics, or complementing the global p3k14c dataset with higher-
  resolution regional data.
---

# Neolithic ¹⁴C — Regional Radiocarbon Databases for Europe and the Near East

## Client (resilient, tool-first)

A stdlib-only client ships with this skill (`src/neolithic14c_client/`, nothing to
pip-install; auto-downloads the NERD CSV and caches it). Filter dates without
hand-rolling pandas:

```bash
SRC=<this skill>/src
PYTHONPATH="$SRC" python3 -m neolithic14c_client dates --bbox 35 -10 60 40 --age-bp 5000 7000 --material bone --tsv
PYTHONPATH="$SRC" python3 -m neolithic14c_client.smoke_test   # offline, bundled fixture
```

`dates(bbox=(S,W,N,E), age_bp=(lo,hi), material=...)` returns `list[dict]` with stable
keys `date_id, lab_id, age_bp, error, material, species, site, lat, lon, country,
source` (ages are uncalibrated 14C BP). `NEOLITHIC_14C_FILE` overrides the source,
`inspect` prints the real header, reads .csv/.xlsx.

## Overview

This skill indexes the main **open regional radiocarbon databases** for
the Neolithic and adjacent periods, with a focus on Europe and the Near
East — the two domestication centres for wheat, barley, cattle, sheep,
goat, and pig, and by extension the historical substrate for the rise
of human-adapted MTBC and *M. bovis*.

These regional databases are **higher-resolution, better-curated
alternatives** to the global **`p3k14c`** skill for their specific
footprints. They are often the *sources* that p3k14c integrates — so
when you need the raw, detailed, up-to-date regional record, go
straight to them.

| Database | Footprint | Dates | Sites | Period |
|---|---|---|---|---|
| **EUROEVOL** | Europe | **14,053** | **4,757** | Late Mesolithic → Early Bronze Age |
| **NERD** | Near East | **11,072** | **1,027** | Late Pleistocene → Late Holocene (15–1.5 ka cal BP) |
| **RADON** | Central Europe + S. Scandinavia | ~10,000+ | many | Neolithic + Early Bronze Age |
| **NeoNet** | Central-Western Mediterranean | 2,506 | 526 | Late Meso / Early Neolithic transition |
| **Radiocarbon Palaeolithic Europe DB** | Europe + Siberia | — | — | Palaeolithic (v32, March 2025) |
| **Mediterranean Neolithic Database** | NW Med Arc → High Rhine | 3,617 | — | 5900–2000 cal BC |

## Why it matters for MTBC × anthropology

The **Neolithic demographic transition** is the moment when:

- Cattle, sheep, goats, and pigs were **domesticated** in the Fertile
  Crescent (~10,500–8,000 BP) — the presumed origin of *M. bovis*,
  *M. caprae*, and related zoonotic MTBC lineages.
- Farming populations reached **density thresholds** needed to sustain
  human-adapted MTBC in a chain of transmission.
- **Population expansions and contractions** ("boom-bust") defined by
  the EUROEVOL project showed that Neolithic Europe was not a
  monotonic growth trajectory but punctuated — relevant for episodes
  of pathogen emergence or local extinction.

These regional ¹⁴C databases give you the quantitative scaffold to
anchor all of the above in concrete, calibrated chronologies. The
**paired EUROEVOL + NERD coverage** is particularly valuable: it lets
you trace the demographic signal from the primary domestication centre
(Near East) through the secondary expansion into Europe.

---

## 1. EUROEVOL — European Neolithic

### Summary

The core radiocarbon-and-site database of the **EUROEVOL project**
(*Cultural Evolution of Neolithic Europe*, led by **Prof. Stephen
Shennan** at University College London). Compiled by Katie Manning,
Sue Colledge, Enrico Crema, Stephen Shennan, and Adrian Timpson.

- **Reference**: Manning K., Colledge S., Crema E., Shennan S. & Timpson A.
  *The Cultural Evolution of Neolithic Europe. EUROEVOL Dataset 1: Sites,
  Phases and Radiocarbon Data.* **Journal of Open Archaeology Data**
  5: e2 (2016). DOI: `10.5334/joad.40`
- **UCL Discovery**: `https://discovery.ucl.ac.uk/id/eprint/1469811/`
- **Size**: **14,053 radiocarbon samples** from **4,757 sites**
- **Temporal range**: Late Mesolithic → Early Bronze Age
- **Geographic scope**: Europe (broad)
- **License**: Journal of Open Archaeology Data — CC BY

### Three datasets

| Dataset | Content |
|---|---|
| **EUROEVOL Dataset 1** | Sites, phases, and radiocarbon data (the main one) |
| EUROEVOL Dataset 2 | Faunal (zooarchaeological) data |
| EUROEVOL Dataset 3 | Archaeobotanical data |

### Key finding (Shennan, Timpson et al. 2013 *Nature Communications*)

> The introduction of farming to Europe was **not** a steady population
> increase but a pattern of **boom and bust** in many regions,
> which climate change alone cannot explain.

This finding has inspired a rich literature on summed probability
distributions (SPD) as a demographic proxy. It is directly useful as a
**null model** when discussing any Neolithic pathogen narrative: don't
assume monotonic expansion.

### Access

- Download the XLSX / CSV from UCL Discovery or the Journal of Open
  Archaeology Data article
- Integrated in the **`rcarbon`** R package (`data("euroevol")`) —
  the easiest path for analysis:

```r
library(rcarbon)
data(euroevol)
str(euroevol)
# Typical columns: SiteID, C14Age, C14SD, Longitude, Latitude, Country, ...
```

- In Python, load with pandas from the raw XLSX / CSV file.

---

## 2. NERD — Near East Radiocarbon Dates

### Summary

A curated dataset of radiocarbon dates from the **Near East**, compiled
by **Alessio Palmisano** (University of Chieti-Pescara / University of
Turin, Italy) in collaboration with Andrew Bevan, Dan Lawrence, and
Stephen Shennan. Maintained as a GitHub repository with versioned
releases.

- **Reference**: Palmisano A., Bevan A., Lawrence D. & Shennan S.
  *The NERD Dataset: Near East Radiocarbon Dates between 15,000 and
  1,500 cal. yr. BP.* **Journal of Open Archaeology Data** 10: 6 (2022).
  DOI: `10.5334/joad.90`
- **GitHub**: `https://github.com/apalmisano82/NERD`
- **Current version**: **6.0** (23 September 2022)
- **Size**: **11,072 radiocarbon dates** from **1,027 archaeological sites**
- **Temporal range**: **15,000 – 1,500 cal. yr BP** (Late Pleistocene → Late Holocene)
- **License**: **CC BY 4.0**

### Verified columns (from the GitHub repository)

| Column | Meaning |
|---|---|
| `DateID` | Unique identifier for the date record |
| `LabID` | Radiocarbon laboratory code |
| `OthLabID` | Alternative lab code |
| `Problems` | Flag for problematic dates |
| `CRA` | Conventional Radiocarbon Age (BP) |
| `Error` | 1σ uncertainty on CRA |
| `DC13` | δ¹³C value |
| `Material` | Dated material (charcoal, bone, shell, seed, …) |
| `Species` | Species when identified (taxa) |
| `SiteID` | Site identifier |
| `SiteName` | Site name |
| `SiteContext` | Context within the site |
| `SiteType` | Type of site (settlement, cave, burial, …) |
| `Country` | Modern country |
| `Longitude`, `Latitude` | WGS84 decimal degrees |
| `LocQual` | Location quality: **A** (exact) → **E** (within 20 km) |
| `Source` | Bibliographic source |
| `Comments` | Free-text notes (note: plural in the actual file) |

### Caveats reported by the authors

- **87%** of dates have material information; only **~29%** have taxon
  information — filter carefully for faunal/domesticate analyses.
- Heterogeneous source quality → `LocQual` is the critical filter for
  spatial work.

### Access

```bash
git clone https://github.com/apalmisano82/NERD.git
```

Or fetch the raw CSV:

```bash
curl -LO https://raw.githubusercontent.com/apalmisano82/NERD/master/nerd.csv
```

---

## 3. RADON — Central European Neolithic & Early Bronze Age

- **Portal**: `https://radon.ufg.uni-kiel.de/`
- **Reference**: Hinz M. et al. *RADON — Radiocarbon dates online 2012.
  Central European database of ¹⁴C dates for the Neolithic and the
  Early Bronze Age.* **Journal of Neolithic Archaeology** (2012).
- **Host**: University of Kiel
- **Focus**: Neolithic + Early Bronze Age, Central Europe + S. Scandinavia
- **Access**: Web search UI, XML/CSV export

---

## 4. NeoNet — NW Mediterranean Late Meso / Early Neolithic transition

- **Reference**: NeoNet Dataset paper on Journal of Open Archaeology Data
- **Size**: 2,506 dates from 526 archaeological sites, 1,769 archaeological
  records
- **Focus**: Late Mesolithic / Early Neolithic transition, North
  Central-Western Mediterranean
- **Use case**: Maritime expansion of Neolithic lifestyles → complementary
  to EUROEVOL which is biased toward continental interiors

---

## 5. Radiocarbon Palaeolithic Europe Database (KU Leuven)

- **Host**: KU Leuven, Division of Geography and Tourism
- **Current version**: **v32 (March 2025)**
- **Scope**: Palaeolithic, Europe + Siberia
- **Reference**: Vermeersch P.M. (regularly updated dataset on
  ScienceDirect / Data in Brief)
- **Complements** EUROEVOL at the deep end of the time range (before
  the Mesolithic) — useful when discussing the population substrate on
  which the Neolithic arrived.

---

## 6. Unified interface: `c14bazAAR` (R package)

All of the above can be accessed through a single R package:

- **`c14bazAAR`** (rOpenSci) — `https://docs.ropensci.org/c14bazAAR/`
- Provides a unified downloader + harmoniser for EUROEVOL, NERD, RADON,
  p3k14c, Neotoma, and several other databases.

```r
library(c14bazAAR)
euroevol <- get_c14data("EUROEVOL")
nerd     <- get_c14data("NERD")
radon    <- get_c14data("RADON")
combined <- bind_rows(euroevol, nerd, radon)
```

**This is the recommended entry point** if you want to work at scale
across multiple regional databases.

---

## Workflows

### Workflow 1 — Summed Probability Distribution (SPD) of the Neolithic demographic transition

Goal: reproduce the Shennan / Timpson "boom-bust" SPD for a specific
region and overlay it with a pathogen TMRCA.

```r
library(rcarbon)
data(euroevol)

# Restrict to a region
germany <- subset(euroevol, Country == "Germany")

# Calibrate
caldates <- calibrate(x = germany$C14Age,
                      errors = germany$C14SD,
                      calCurves = "intcal20",
                      verbose = FALSE)

# SPD over the Neolithic window
spd_out <- spd(caldates, timeRange = c(9000, 4000))
plot(spd_out)
abline(v = 5500, col = "red")   # example: TMRCA of an MTBC clade
```

### Workflow 2 — Near East first-appearance chronology for domesticates

Goal: identify the earliest dated sites carrying a specific domesticate
(cattle, sheep, goat) from NERD.

```python
import pandas as pd
nerd = pd.read_csv("nerd.csv", low_memory=False)

# IMPORTANT: NERD stores countries as ISO2 codes, not full names.
# Fertile Crescent core + extended:
fc_iso = ['TR', 'IR', 'IQ', 'SY', 'JO', 'IL', 'LB', 'PS', 'CY', 'GE', 'AM', 'AZ']
fc = nerd[nerd.Country.isin(fc_iso)]

# Fuzzy match on Species / Material columns (both are needed: Species is filled for ~29% of dates)
bos_regex = r"\bBos\b|cattle|aurochs|bovid"
cattle = fc[
    fc.Species.fillna("").str.contains(bos_regex, regex=True, case=False)
    | fc.Material.fillna("").str.contains(bos_regex, regex=True, case=False)
]
earliest = (cattle.sort_values("CRA", ascending=False)
                 .head(20)
                 [["SiteName","Country","CRA","Error","Material","Species","SiteContext"]])
print(earliest)
```

### Verified Bos chronology in NERD (session-fetched snapshot)

A session-fetched query returned **30 Bos entries in the Fertile Crescent**
(TR, IR, IQ, SY, JO, CY, GE) covering **11 700 → 1 967 BP**. The
oldest iconic sites are:

| Site | Country | CRA BP | Context | Interpretation |
|---|---|---|---|---|
| Sakazhia cave | GE | **11 700** | — | Late Pleistocene wild aurochs |
| Abu Hureyra | SY | 11 090–10 820 | **Late Natufian** (Level 326) | Wild Bos in pre-agricultural context — the direct ancestral window |
| Göbekli Tepe | TR | 9 800 | PPNA monumental | Still wild/transitional |
| Ain Ghazal | JO | 8 554 | PPNB | Transitional |
| **Çatalhöyük East** | TR | **8 085** | KOPAL Area, quarry pits | **First Bos at Mellaart's iconic site** |
| Jarmo | IQ | 7 270–6 180 | Soundings PQ/K | Braidwood's early Mesopotamian farming village |
| **Çatalhöyük West** | TR | **6 944** | Building 98 | **First explicit ***Bos taurus*** (domesticated)** |
| Tepe Zagheh | IR | 6 100–5 900 | Trench TT-IX | Iranian Plateau farming spread |
| **Çukuriçi Höyük** | TR | **4 100** | CuHö IV | ***Bos primigenius* (wild aurochs)** still present at the Early Bronze Age — **wild/domestic co-existence persists 3 000 years after initial domestication** |

> [!WARNING]
> **NERD uses ISO2 country codes** (`TR`, `IR`, `IQ`...), not full
> English names. Filters like `Country.isin(["Turkey", "Iran"])` return
> empty results. Use ISO2.

> [!NOTE]
> The *Bos primigenius* at Çukuriçi Höyük (4 100 BP, Bronze Age Anatolia)
> is an important caveat for any domestication narrative: **wild aurochs
> persisted for >3 000 years alongside domesticated Bos taurus**. This
> creates a window of potential gene flow and pathogen spill-over between
> wild and domestic Bos that may matter for *M. bovis* evolutionary history.

Cross-reference with the ancient cattle genome literature (Verdugo
et al. 2019 *Science*) and the `p3k14c` domesticate workflow.

### Workflow 3 — Combined EUROEVOL + NERD chronology for farming expansion

Goal: trace the westward expansion of farming from the Fertile Crescent
into Europe by combining the two databases.

```r
library(c14bazAAR)

ne <- get_c14data("NERD")      %>% filter(c14age_bp >= 7000, c14age_bp <= 10000)
eu <- get_c14data("EUROEVOL")  %>% filter(c14age_bp >= 5000, c14age_bp <= 9000)

combined <- bind_rows(ne, eu)
# Then plot the earliest dates per longitude band, demonstrating the
# farming expansion arc from the Levant through Anatolia to the
# Danube and finally to Atlantic Europe.
```

This is the quantitative backbone for the classic "Neolithic wave of
advance" narrative (Ammerman & Cavalli-Sforza), and it sets the stage
for any co-dispersal argument involving human-adapted MTBC or
*M. bovis*.

### Workflow 4 — Cross-reference to bovine-genomics domestication

Goal: anchor the *Bos taurus* primary-domestication signal from
`bovine-genomics` with the earliest dated cattle contexts from NERD.

1. From NERD, filter for `Species` containing `Bos` / `Bos taurus` in
   the Near Eastern core zone (Turkey, Syria, Iran, Iraq, Israel).
2. Extract the **earliest** cal BP dates per site.
3. Plot on the same map as the Decker 2014 / 1000 Bull Genomes breed
   clustering.
4. Discuss whether the Near Eastern NERD chronology fits the 10,500 BP
   primary domestication window implied by the modern cattle breed
   structure.

### Workflow 5 — Higher-resolution alternative to p3k14c for a European/Near Eastern question

When `p3k14c` coverage feels sparse for your region of interest, use
EUROEVOL or NERD directly. These are more recent, more curated, and
often denser than the p3k14c integration.

```python
# Count coverage for a bounding box in EUROEVOL vs p3k14c
import pandas as pd

euroevol = pd.read_csv("euroevol.csv")
p3k = pd.read_csv("p3k14c_raw.csv", low_memory=False)

# Anatolia bbox
def count(df, lat_col="Latitude", lon_col="Longitude"):
    m = (df[lat_col].between(36, 42)) & (df[lon_col].between(26, 45))
    return int(m.sum())

print("EUROEVOL Anatolia:", count(euroevol))
print("p3k14c  Anatolia:", count(p3k))
```

## Caveats

- **Coverage overlap with p3k14c.** p3k14c integrates many of these
  regional databases but may lag behind the latest regional release.
  For recent work, prefer the regional database directly.
- **Inhomogeneous quality.** Especially in NERD, only ~29% of dates
  have taxon information. Use `LocQual` and material filters
  aggressively.
- **Uncalibrated BP in raw files.** Same caveat as for p3k14c — always
  calibrate with IntCal20 / SHCal20 before reporting dates in calendar
  years.
- **No pathogen data.** These are human / archaeological records, not
  pathogen records. Pair with `spaam-ancient-metagenome-dir`, `aadr`,
  and `amtdb` for the host-pathogen side.
- **Fragmented access.** Each database has its own download URL,
  versioning, and schema. The `c14bazAAR` R package mitigates this
  but may not always be up to date.
- **Version drift.** EUROEVOL dates from 2016 and has not been
  substantially updated; NERD is at v6 (2022); RADON is continuously
  updated. Record the version you used.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`p3k14c`** | Global counterpart — integrates these regional databases |
| **`aadr`** | Ancient human genomes from the same sites |
| **`amtdb`** | Ancient human mtDNA from the same sites |
| **`spaam-ancient-metagenome-dir`** | Ancient pathogen samples — overlay on ¹⁴C chronology |
| **`bovine-genomics`** | Cattle breed structure — anchor primary-domestication signal with NERD dates |
| **`d-place`** | Subsistence classification of ethnographic-present successor populations |
| **`seshat`** | Polity-level history in the same regions |
| **`pleiades`** | Stable place identifiers for the archaeological sites |
| **`glottolog`** | Modern language classification of the regions |
| **`rcarbon`** (R) | Canonical analysis package — ships with EUROEVOL |
| **`c14bazAAR`** (R) | Unified downloader for multiple ¹⁴C databases |
| **IntCal20 / SHCal20** | Calibration curves |

## Citations

```bibtex
@article{manning2016euroevol,
  title   = {The Cultural Evolution of Neolithic Europe. EUROEVOL
             Dataset 1: Sites, Phases and Radiocarbon Data},
  author  = {Manning, Katie and Colledge, Sue and Crema, Enrico R. and
             Shennan, Stephen and Timpson, Adrian},
  journal = {Journal of Open Archaeology Data},
  volume  = {5},
  pages   = {e2},
  year    = {2016},
  doi     = {10.5334/joad.40}
}

@article{palmisano2022nerd,
  title   = {The NERD Dataset: Near East Radiocarbon Dates between
             15,000 and 1,500 cal. yr. BP},
  author  = {Palmisano, Alessio and Bevan, Andrew and Lawrence, Dan and
             Shennan, Stephen},
  journal = {Journal of Open Archaeology Data},
  volume  = {10},
  pages   = {6},
  year    = {2022},
  doi     = {10.5334/joad.90}
}

@article{shennan2013regional,
  title   = {Regional population collapse followed initial agriculture
             booms in mid-Holocene Europe},
  author  = {Shennan, Stephen and Downey, Sean S. and Timpson, Adrian and
             Edinborough, Kevan and Colledge, Sue and Kerig, Tim and
             Manning, Katie and Thomas, Mark G.},
  journal = {Nature Communications},
  volume  = {4},
  pages   = {2486},
  year    = {2013},
  doi     = {10.1038/ncomms3486}
}

@article{hinz2012radon,
  title   = {RADON -- Radiocarbon dates online 2012. Central European
             database of 14C dates for the Neolithic and the Early
             Bronze Age},
  author  = {Hinz, Martin and Furholt, Martin and Müller, Johannes and
             Raetzel-Fabian, Dirk and Rinne, Christoph and Sjögren,
             Karl-Göran and Wotzka, Hans-Peter},
  journal = {Journal of Neolithic Archaeology},
  year    = {2012}
}
```

**Remember**: in Methods, specify the regional database and version
used (e.g. *EUROEVOL 2016 dataset 1, NERD v6.0, RADON accessed YYYY-MM-DD*).
