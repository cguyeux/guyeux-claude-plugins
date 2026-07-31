---
name: seshat
description: >-
  Query Seshat: Global History Databank, the reference quantitative historical
  database of ~400 polities from the Neolithic to ~1900 CE, covering social
  complexity, warfare, religion, agriculture, and crisis/collapse events.
  Provides the polity-level quantitative scaffold needed to test hypotheses
  about how state formation, population density, urbanization, and crises
  shaped the persistence and dispersal of human-adapted pathogens.

  Use when: building a quantitative density/urbanization argument for
  human-adapted MTBC persistence, correlating pathogen emergence with
  polity crises or collapses (CrisisDB), framing the rise of a bacterial
  lineage in a specific state formation context, or writing a
  cliodynamics-style section on the co-evolution of pathogens and social
  complexity.
---

# Seshat : Global History Databank for Quantitative History

## Overview

**Seshat: Global History Databank** is the reference open quantitative
historical database, designed and maintained by an international editorial
board (Peter Turchin, Harvey Whitehouse, Pieter François, Thomas Currie,
Kevin Feeney, and many others) under the Evolution Institute umbrella
since **2011**. It systematically codes the social, political, religious,
economic, and military organisation of ~400 **polities** (states,
empires, chiefdoms) covering a temporal range from the **Neolithic
(~4000 BCE) through ~1900 CE**, across **30 Natural Geographic Areas
(NGAs)** drawn from 10 world regions (World Sample-30).

- **Introductory reference**: Turchin P., Brennan R., Currie T.E.,
  Feeney K.C., François P., Hoyer D., Manning J.G., Marciniak A.,
  Mullins D.A., Palmisano A., Peregrine P., Turner E.A.L., Whitehouse H.
  *An Introduction to Seshat: Global History Databank.* **Journal of
  Cognitive Historiography** 5: 115–123 (2018).
- **Major finding paper**: Turchin P. et al. *Quantitative historical
  analysis uncovers a single dimension of complexity that structures
  global variation in human social organization.* **PNAS** 115(2):
  E144–E151 (2018). DOI: `10.1073/pnas.1708800115`
- **Current snapshot**: **Equinox-2020** (and successive GitHub snapshots,
  e.g. `Equinox_on_GitHub_June9_2022.xlsx`)
- **Main web portal**: `https://seshat-db.com/` (older URL
  `https://seshatdatabank.info/` still works)
- **Data releases on GitHub** (mirror): `https://github.com/datasets/seshat`
- **License**: **CC BY-NC-SA 4.0** (non-commercial, share-alike) for data.
  Note: the GitHub mirror README flags a "license-confused" situation
  between CC Zero and CC BY-NC-SA, for safety, treat all data as
  **CC BY-NC-SA** unless a specific release says otherwise.

> [!NOTE]
> There is an API at `https://seshat-db.com/api/`, but the canonical way
> to access Seshat for analysis is to download a **periodic snapshot**
> (Excel / CSV) that corresponds to a published article, so that your
> analysis is reproducible and version-pinned. Do not invent API endpoints
>, consult the downloads page instead.

## Client (resilient, tool-first)

A **stdlib-only** client ships with this skill (`src/seshat_client/`, nothing to
pip-install; reads both `.csv` and `.xlsx` snapshots). It resolves a pinned
snapshot, normalises Seshat's varying column names to a **stable schema**, and
filters polity records by NGA, calendar-year window, and variable, so you never
hand-roll an `sc[sc.variable == ...]` filter again.

```bash
SRC=<this skill>/src          # absolute path to seshat/src

# clone the snapshot once, point the client at it (CSV or XLSX both work):
git clone https://github.com/datasets/seshat.git
export SESHAT_FILE=/path/to/seshat/sc_dataset.12.2017.xlsx
PYTHONPATH="$SRC" python3 -m seshat_client polities \
    --nga Latium --period -500 500 --variable "Polity Population" --tsv

# which columns does my snapshot actually have? (reconcile schema drift)
PYTHONPATH="$SRC" python3 -m seshat_client inspect

# offline reproducibility / CI: runs against the bundled fixture, no network
PYTHONPATH="$SRC" python3 -m seshat_client.smoke_test
```

Python API:

```python
from seshat_client import SeshatClient
# Latium polity population across the Roman window, intervals preserved:
rows = SeshatClient().polities(nga=["Latium"], period=(-500, 500),
                               variable="Polity Population")
# rows: list[dict] with STABLE keys; value_mid added, [value_from, value_to] kept
```

**Stable output columns**: `nga, polity, start_year, end_year, variable,
value_from, value_to, value_mid, source`. A polity is kept when its
`[start_year, end_year]` **overlaps** the requested window (years BCE negative).
`value_mid` is the interval mean (or `""` if a bound is missing): propagate the
interval, do not silently collapse to the midpoint downstream. Provenance is on
`client.last_source`, the pinned snapshot on `client.version`.

**Resolution cascade**: `SESHAT_FILE=/path` override -> disk cache -> bundled
fixture -> `DatasetUnavailable` with download instructions. Snapshots are not
auto-downloaded (license-pinned, no stable file URL); `SESHAT_OFFLINE=1` forbids
the network. A missing mapped column raises `SchemaDrift` and `inspect` prints the
real header so you can add a candidate in `schema.py`.

## Why it matters for MTBC × anthropology

Human-adapted MTBC lineages require **sustained host density** to persist,
this is a textbook epidemiological fact. What Seshat adds is a **quantitative
historical scaffold** to test specific claims about when and where density
thresholds were crossed, and to anchor TB narratives in concrete cliodynamics
rather than hand-waving.

Three concrete uses:

1. **Social complexity ↔ human-adapted MTBC persistence.** The Turchin 2018
   PNAS paper shows that social complexity is remarkably well captured by a
   single dominant dimension (polity population, territorial extent,
   hierarchy, writing, infrastructure). Use this dimension as a quantitative
   covariate when explaining the geography / chronology of L4 or L2 lineage
   expansion.
2. **Crisis and collapse ↔ epidemic outbreaks (CrisisDB).** Seshat's
   CrisisDB module codes instability events, power transitions, and crisis
   consequences for each polity. This lets you test whether pathogen
   expansions (e.g. ancient *Y. pestis* waves, or late-antique TB) cluster
   temporally around polity-level crises.
3. **Warfare & mass mobility (MilTech).** Seshat codes military organisation
   and troop movements. This is a quantitative proxy for pathogen dispersal
   pathways in the pre-modern world, complementary to `orbis` for the
   Roman window and `slavevoyages` for the trans-Atlantic window.

Unlike `d-place` (which is ethnographic present), Seshat is **diachronic**,
it codes each polity at multiple time-slices, so you can follow a given NGA
(say, Upper Egypt) from ~3000 BCE to 1900 CE.

## Data model

### Polity
The fundamental unit. Each polity has a unique identifier, a start date,
an end date, a territorial extent (usually an NGA), and a cultural /
dynastic name (e.g. *Old Kingdom Egypt*, *Early Dynastic Mesopotamia*,
*Kushan Empire*, *Byzantine-Palaiologan*).

### Natural Geographic Area (NGA)
One of **30 regions** selected for representative sampling across 10
world regions (3 NGAs per region: one with early complex state
development, one with late/absent state formation, one intermediate).

### Variable
A coded trait with a formal definition (e.g. *Polity Population*,
*Writing Present*, *Money Present*, *Professional Military Officers*,
*Moralizing High Gods*). Variables are grouped into five top-level
categories plus CrisisDB:

| Category | Example variables |
|---|---|
| **General Variables** | Duration, predecessors, successors, language family |
| **Social Complexity (SC)** | Polity population, polity territory, capital population, hierarchy levels, writing, money, postal system, roads, irrigation |
| **Warfare / MilTech** | Weapons (iron, bronze), armour, cavalry, professional military, fortifications, chariots |
| **Religion** | Moralizing High Gods, supernatural punishment, formal religious bureaucracy, ritual orthopraxy |
| **Economy** | Markets, coinage, agricultural productivity, irrigation systems |
| **CrisisDB** | Instability events, power transitions, crisis consequences, elite turnover |

### Value / record
The atomic data unit: a triple of (polity, variable, time-slice) plus a
coded value, confidence flag, and a prose note with references. Seshat
is **source-tracked**, every coded value carries its bibliographic
justification.

Volumes (as publicly reported): **~400 polities**, **~300,000 records**,
**~1,500 variables** across all categories (approximate; varies by
snapshot).

## Data access

### Option A : Downloads page (recommended for reproducibility)

1. Go to `https://seshat-db.com/downloads_page/`
2. Download the snapshot corresponding to a specific publication, or the
   most recent Equinox consolidated release
3. Record the **snapshot name / date** in your Methods (e.g. *"Seshat
   Equinox-2020, accessed via seshat-db.com on 2026-04-08"*)

Key files on the GitHub mirror `datasets/seshat`:

| File | Topic | Format |
|---|---|---|
| `Equinox_on_GitHub_June9_2022.xlsx` | Main consolidated snapshot | XLSX |
| `sc_dataset.12.2017.xlsx` | Social Complexity (Turchin 2018 PNAS) | XLSX |
| `agri_dataset.07.2020.csv` | Agricultural Productivity | CSV |
| `axial_dataset.05.2018.csv` | Axial Age variables | CSV |
| `mr_dataset.04.2021.csv` | Moralizing Religion | CSV |
| `CrisisConsequencesData_NavigatingPolycrisis_2023.03.csv` | CrisisDB | CSV |

### Option B : GitHub mirror

```bash
git clone https://github.com/datasets/seshat.git
```

This gives you all the snapshots above in one place, pinned by commit hash
for reproducibility.

### Option C : Web API (limited, experimental)

Some endpoints are exposed at `https://seshat-db.com/api/`. Use with care:
pagination, versioning, and authentication rules may change, and the
API is not the canonical reproducible access path.

## Workflows

> Prefer the **client** (`python -m seshat_client polities ...`, see above) over the
> hand-rolled pandas below; the snippets illustrate the underlying logic and the
> joins/CrisisDB steps the client does not (yet) cover.

### Workflow 1 : Density threshold for human-adapted TB persistence

Goal: for each NGA, extract the time series of `Polity Population` and
`Capital Population`, and identify the first crossing of a threshold
(e.g. ~500 k for sustained TB transmission chains, this number is
illustrative, use the epidemiological literature you actually cite).

```python
import pandas as pd
sc = pd.read_excel("sc_dataset.12.2017.xlsx")
# columns typically include: NGA, Polity, start_year, end_year,
# variable, value_from, value_to, source, note

pop = sc[sc.variable == "Polity Population"].copy()
pop["value_mid"] = pop[["value_from","value_to"]].mean(axis=1)

# First crossing per NGA
def first_cross(df, thr):
    crossed = df[df.value_mid >= thr].sort_values("start_year")
    return crossed.iloc[0] if len(crossed) else None

first = pop.groupby("NGA").apply(first_cross, thr=500_000)
print(first[["Polity","start_year","value_mid"]])
```

Overlay the result with the emergence / radiation dates of human-adapted
MTBC sublineages from TBannotator.

### Workflow 2 : Crises and epidemic windows (CrisisDB)

Goal: check whether ancient pathogen samples (from
`spaam-ancient-metagenome-dir`) cluster temporally around polity-level
crises.

```python
crisis = pd.read_csv("CrisisConsequencesData_NavigatingPolycrisis_2023.03.csv")
# Typical columns: Polity, Crisis_start, Crisis_end, Consequences, ...

# Join with SPAAM ancient samples by country + date window
import pandas as pd
spaam = pd.read_csv("amdir_singlegenome_samples.tsv", sep="\t")

# Convert sample_age (BP) to calendar year CE
spaam["year_ce"] = 1950 - spaam["sample_age"]

# For each crisis, count ancient samples within the crisis window
# (pseudo-code — adjust to the actual schemas of each file)
```

### Workflow 3 : Warfare and long-distance pathogen dispersal

Goal: test whether the timing of a TB lineage's geographic expansion
coincides with campaigns of a given polity that Seshat codes as having
professional standing armies and long-range logistics.

1. Extract `Professional Military Officers`, `Capital Population`, and
   `Polity Territory` variables for the polity of interest.
2. Identify time-slices where all three signal high mobilization capacity.
3. Cross-reference with TB lineage expansion dates from TBannotator.
4. Narrative: *"The expansion of lineage X coincides with the period of
   maximal mobilisation capacity of polity Y, consistent with
   army-mediated dispersal."*

### Workflow 4 : Cross-reference NGAs with MTBC lineage distributions

Seshat NGAs are geographic cells, assign each TB sampling location to
its nearest NGA and bring in the Seshat variables at the right time-slice.

```python
# Pseudo-code: load NGA centroids, snap TB sites
from scipy.spatial import cKDTree
nga_coords = pd.read_csv("nga_centroids.csv")  # NGA, lat, lon
tree = cKDTree(nga_coords[["lat","lon"]].values)

tb["nga"] = nga_coords.iloc[tree.query(tb[["lat","lon"]].values, k=1)[1]]["NGA"].values

# Now each TB sample has an NGA — join to Seshat polity variables
```

### Workflow 5 : Controlling for historical non-independence

Polities in the same NGA across time are not independent, and polities
linked by dynastic succession are even less so. Seshat provides explicit
`predecessors` and `successors` fields to build polity genealogies, use
these as random-effect structure in mixed models, analogous to how
`d-place` Bayesian phylogenies are used for cross-cultural analyses.

## When NOT to use

- **Pathogen data** : Seshat is political/cultural history; epidemics appear only
  indirectly (CrisisDB consequences, narrative notes). For pathogen genomes use
  `aadr` (host), `spaam-ancient-metagenome-dir`, `enterobase`, or the primary
  literature.
- **Ethnographic present / cross-cultural traits**, that is `d-place` (and its
  Ethnographic-Atlas codes); Seshat is diachronic polity-level coding.
- **Roman-world mobility distances**, use `orbis` for the network / Dijkstra
  costs; Seshat gives the polity-level scaffold, not the route graph.
- **Admixture / `.geno`**, unrelated; that is `aadr` + ADMIXTOOLS.
- **Moralizing-gods variables**, read the Whitehouse 2019 critique / correction
  literature first (see below) before building an argument on them.

## Caveats

- **Coding is not fully objective.** Every coded value is an expert
  judgment; Seshat mitigates this with multi-coder workflows and explicit
  prose justifications, but critics have pointed out that the coding
  process is interpretive. Always cite the specific snapshot and coders.
- **The moralizing gods paper.** Whitehouse et al. 2019 *Nature* ("Complex
  societies precede moralizing gods throughout world history") received
  substantial criticism and required data corrections. If you touch the
  religion / moralizing-gods variables, read the subsequent critique and
  response literature before building an argument on them.
- **Uneven temporal and regional coverage.** Some NGAs are densely coded
  (Upper Egypt, Kachi Plain, Latium, Kansai) while others are sparse.
  Report coverage in your Methods.
- **Point estimates with wide intervals.** Many numeric variables (e.g.
  polity population) are coded as `[value_from, value_to]` intervals
  reflecting the coders' uncertainty. Always propagate this uncertainty
  into your downstream analyses, do not just take the midpoint.
- **License is restrictive.** CC BY-NC-SA 4.0 forbids commercial use and
  requires share-alike derivatives. If the "license-confused" flag on
  the GitHub mirror matters for your use case, clarify with the Seshat
  editorial board before publishing.
- **Not a pathogen database.** Seshat is cultural and political history;
  epidemics are only coded indirectly (via CrisisDB consequences or
  isolated narrative notes). For pathogen data you still need `aadr`,
  `spaam-ancient-metagenome-dir`, `enterobase`, and the primary literature.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`d-place`** | Ethnographic cross-sectional counterpart (present-day snapshot vs Seshat's diachronic coverage) |
| **`glottolog`** | Language identifiers for the populations living in Seshat NGAs |
| **`aadr`** | Ancient human genomes from polity territories, joinable via NGA + date window |
| **`spaam-ancient-metagenome-dir`** | Ancient pathogen samples to overlay on polity timelines |
| **`enterobase`** | *Y. pestis* historical phylogeny to align with Seshat crisis events |
| **`orbis`** | Roman-world network model (quantitative mobility) complements Seshat Roman polity data |
| **`p3k14c`** | Archaeological radiocarbon chronology for polities before written records |
| **`slavevoyages`** | Post-1500 population movements, downstream of Seshat's window |
| **TBannotator MCP** | Modern TB lineage geography + TMRCA for matching against polity timelines |

## Citations

```bibtex
@article{turchin2018seshat,
  title   = {An Introduction to Seshat: Global History Databank},
  author  = {Turchin, Peter and Brennan, Rob and Currie, Thomas E. and
             Feeney, Kevin C. and Fran{\c{c}}ois, Pieter and Hoyer, Daniel
             and Manning, Joseph G. and Marciniak, Arkadiusz and
             Mullins, Daniel A. and Palmisano, Alessio and Peregrine, Peter
             and Turner, Edward A.L. and Whitehouse, Harvey},
  journal = {Journal of Cognitive Historiography},
  volume  = {5},
  pages   = {115--123},
  year    = {2018}
}

@article{turchin2018complexity,
  title   = {Quantitative historical analysis uncovers a single dimension
             of complexity that structures global variation in human
             social organization},
  author  = {Turchin, Peter and Currie, Thomas E. and Whitehouse, Harvey
             and Fran{\c{c}}ois, Pieter and Feeney, Kevin and Mullins, Daniel
             and Hoyer, Daniel and Collins, Christina and Grohmann, Stephanie
             and Savage, Patrick and others},
  journal = {Proceedings of the National Academy of Sciences},
  volume  = {115},
  number  = {2},
  pages   = {E144--E151},
  year    = {2018},
  doi     = {10.1073/pnas.1708800115}
}
```

**Always pin the snapshot** you used (e.g. *Equinox-2020*, or a specific
GitHub commit of the mirror) and cite the source publication that
accompanies it.
