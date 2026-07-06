---
name: aadr
description: >-
  Query the Allen Ancient DNA Resource (AADR, Reich Lab), the reference curated
  compendium of >16,000 ancient and present-day human genomes in EIGENSTRAT
  format with rich archaeological/demographic metadata. Use for cross-referencing
  ancient human populations with MTBC lineage phylogeography, identifying
  individuals for which ancient TB DNA has also been published, and building
  population-level coevolutionary narratives.

  Use when: contextualizing an MTBC lineage with ancient human population
  history, checking whether a region/period has ancient human genomes to
  correlate with a TB scenario, identifying skeletons that yielded both host
  and pathogen DNA, or writing an eco-anthropology / human–pathogen coevolution
  section for an article or seminar.
---

# AADR — Allen Ancient DNA Resource for MTBC × Ancient Humans

## Overview

The **Allen Ancient DNA Resource (AADR)** is the reference curated compendium
of ancient human genomes, maintained by the David Reich Lab at Harvard Medical
School. It unifies published ancient DNA into a consistent EIGENSTRAT-format
dataset with rich annotation, and is the de-facto entry point for
paleogenomics, population genetics of admixture, and eco-anthropology.

- **Reference**: Mallick S., Micco A., Mah M. et al. *The Allen Ancient DNA
  Resource (AADR) a curated compendium of ancient human genomes.* **Scientific
  Data** 11:182 (2024). DOI: `10.1038/s41597-024-03031-7`
- **Size**: crossed 10,000 individuals in 2022 (v54.1); current releases
  (v62 / late 2024) hold **>16,000** ancient + present-day individuals
- **Format**: EIGENSTRAT (`.ind` / `.snp` / `.geno`) + annotation file (`.anno`)
- **License**: **CC BY 4.0** (attribution required)
- **Host**: Harvard Dataverse, `https://dataverse.harvard.edu/dataverse/reich_lab`
- **DOI of peer-reviewed release**: `10.7910/DVN/FFIDCW`
- **Landing page (Reich Lab)**: `https://reich.hms.harvard.edu/allen-ancient-dna-resource-aadr-downloadable-genotypes-present-day-and-ancient-dna-data`

> [!WARNING]
> The project's Paul G. Allen Foundation grant **ended in September 2024** and
> updated releases have been postponed due to funding uncertainty (Harvard
> Crimson, 2025-10). Always record the exact version + DOI you used, and
> mirror the files locally; do not assume the live download page will keep
> serving them indefinitely.

> [!NOTE]
> AADR has **no REST API**. Access is by version-pinned ZIP download from
> Harvard Dataverse. Do not invent endpoints.

## Client (resilient, tool-first)

A **stdlib-only** client ships with this skill (`src/aadr_client/`, nothing to
pip-install). It resolves a locally mirrored `.anno`, normalises AADR's drifting
column names to a **stable schema**, and filters to a cohort, so you never
hand-roll a `pd.read_csv(...).between(...)` again.

```bash
SRC=<this skill>/src          # absolute path to aadr/src

# point it at your mirrored release (any version), then query:
export AADR_FILE=/path/to/aadr_v62.0_1240K_public.anno
PYTHONPATH="$SRC" python3 -m aadr_client cohort \
    --countries Germany Hungary --period-bp 0 1500 --tsv

# what columns does my downloaded file actually have? (reconcile schema drift)
PYTHONPATH="$SRC" python3 -m aadr_client inspect

# offline reproducibility / CI: runs against the bundled fixture, no network
PYTHONPATH="$SRC" python3 -m aadr_client.smoke_test
```

Python API:

```python
from aadr_client import AadrClient
# Europe, 10,000 BP -> present, PASS-only (a Kerner-2021-style host cohort):
rows = AadrClient().cohort(
    countries=["Germany", "Hungary", "Italy", "England", "France"],
    period_bp=(0, 10000),
)
# rows: list[dict] with STABLE keys; never breaks on a version's column rename
```

**Stable output columns** (the contract downstream skills consume): `genetic_id,
master_id, group, country, locality, lat, lon, date_bp, date_sd_bp, coverage,
sex, publication, qc`. Provenance is on `client.last_source`
(`env | cache | download | fixture`); the pinned release on `client.version`.

**Resolution cascade** (reproducible, offline-capable): `AADR_FILE=/path` override
-> disk cache (`~/.cache/aadr/<version>/`) -> bundled fixture -> a clear
`DatasetUnavailable` telling you to download + pin the release. AADR is never
auto-downloaded (multi-GB bundle, no stable file URL); set `AADR_OFFLINE=1` to
forbid the network. If a mapped column is absent, `SchemaDrift` names it and
`inspect` prints the real header so you can add a candidate in `schema.py`.

## Why it matters for MTBC

AADR is a **host** dataset, not a pathogen dataset. Its value for TB research
is three-fold:

1. **Host–pathogen cross-referencing.** Some skeletons yielded both ancient
   human DNA (catalogued in AADR) *and* ancient *M. tuberculosis* / *M. leprae*
   DNA (catalogued in separate ancient-metagenome directories — see
   `spaam-ancient-metagenome-dir`). Crossing the two gives per-individual
   host-pathogen pairs — the tightest possible coevolution evidence.
2. **Population-level context.** For a given region and period, AADR reveals
   population continuity, migration, and admixture events. A TB lineage that
   appears in a region coincident with a detected human population turnover
   is a strong signal for co-dispersal.
3. **Demographic-transition timing.** TB requires a density threshold to
   persist. AADR's population-level reconstructions of Neolithic/Bronze-Age
   expansions provide the demographic scaffold to ask when a region
   could first sustain human-adapted MTBC lineages.

Published ancient MTBC / *Mycobacterium* papers (the set **actually
catalogued** in SPAAM AncientMetagenomeDir as of this skill's writing —
verify the current state with `spaam-ancient-metagenome-dir`):

| Reference | Site / Population | Age (BP) | Pathogen | Project tag |
|---|---|---|---|---|
| Bos et al. 2014, *Nature* (`10.1038/nature13591`) | Peru (pre-Columbian) — El Yaral, El Algodonal, Chiribaya Alta | 900–1 000 | ***M. pinnipedii*** (3 individuals) | `Bos2014` |
| Kay et al. 2015, *Nat Commun* (`10.1038/ncomms7717`) | Hungary — Dominican church of Vác (mummies) | 100–200 | *M. tuberculosis* (8 individuals) | `Kay2015` |
| Sabin et al. 2020, *Genome Biol* (`10.1186/s13059-020-02112-1`) | Sweden — Lund Cathedral (Bishop Peder Winstrup, calcified nodule) | ~300 | *M. tuberculosis* (1 individual) | `Sabin2020` |
| Vågene et al. 2018, *Nat Ecol Evol* | Mexico — Teposcolula-Yucundaa (*cocoliztli*, 1545 CE) | ~500 | *Salmonella enterica* Paratyphi C (context, not MTBC) | `Vagene2018` / `SabinSalmonella` |
| Vagene et al. 2022, *Nat Commun* (`10.1038/s41467-022-28562-8`) | Peru & Colombia (colonial) — Moquegua M6-Estuquiña, Bogotá | 500–700 | ***M. pinnipedii*** in humans (3 individuals) | `Vagene2022` |
| Jager et al. 2022, *Tuberculosis* (`10.1016/j.tube.2022.102181`) | Hungary — Vác (additional sample) | ~200 | *M. tuberculosis* (1 individual) | `Jager2022` |
| Schuenemann et al. 2013 / 2018 | Medieval Europe, broad | variable | *M. leprae* (not TB but genus *Mycobacterium*; cross-reference) | `Schuenemann*` |

> [!WARNING]
> The MTBC ancient-DNA corpus is **very small** (16 individuals, 5 projects,
> 4 countries, nothing older than ~1 000 BP). There is currently **no
> published ancient DNA for *M. bovis* or *M. caprae*** in this catalogue,
> and no Bronze Age / Neolithic human-adapted MTBC. Any narrative built on
> "domestication-era MTBC ancient DNA" is therefore under-constrained.

## Data Access

### Download the latest version

1. Go to the Reich Lab AADR page (link above) or Harvard Dataverse (DOI above).
2. Download the release ZIP (contains `.anno`, `.ind`, `.snp`, `.geno`).
3. Record the **version string** (e.g. `v54.1.p1` or `v62.0`) + the **DOI**
   of the exact deposit — this is critical for reproducibility.

### Typical release files

| File | Format | Content |
|---|---|---|
| `*.anno` | TSV, ~130 columns | Rich per-individual metadata (see below) |
| `*.ind` | EIGENSTRAT individuals | One line per individual: ID, sex, population label |
| `*.snp` | EIGENSTRAT SNP map | ~1.2M (1240K panel) or ~600k (HO panel) positions |
| `*.geno` | EIGENSTRAT genotype matrix | Pseudohaploid for ancient, diploid for present-day |

### Data type suffixes in the individual ID

| Suffix | Meaning |
|---|---|
| `.SG` | Shotgun sequencing, pseudohaploid calls |
| `.DG` | Diploid calls (usually present-day or high-coverage ancient) |
| `.HO` | Human Origins array (present-day reference panel) |
| `_contam`, `_outlier`, `_lowcov` | Quality flags (exclude by default) |

## Key `.anno` columns

The `.anno` file is a TSV with ~130 columns. The subset most useful for
MTBC × anthropology cross-referencing:

| Column | Meaning |
|---|---|
| `Genetic ID` | Primary identifier (matches `.ind`) |
| `Master ID` | De-duplicated individual identifier |
| `Skeletal code` | Archaeological skeleton code (links to excavation reports) |
| `Group Label` | Population assignment used in publications |
| `Date mean in BP` | Mean calibrated age (years before 1950) |
| `Date standard deviation in BP` | 1σ on the date |
| `Full Date` | Free-text date range |
| `Lat.` / `Long.` | Decimal coordinates (WGS84) |
| `Political Entity` | Modern country |
| `Locality` | Site name / region |
| `Data source` | Publication citation |
| `Publication year` | First reporting year |
| `Coverage` | Mean autosomal coverage |
| `Molecular Sex` | XX / XY / XXY / uncertain |
| `Y haplogroup` | Paternal lineage (ISOGG nomenclature) |
| `mtDNA haplogroup` | Maternal lineage (PhyloTree) |
| `Damage rate` | C→T terminal damage (authenticity proxy) |
| `Contamination` | Estimated contamination fraction |
| `ROH` | Runs of homozygosity (consanguinity / demography) |
| `Family ID` | Inferred relatives |
| `Assessment` | Curator's quality verdict (`PASS` / flag) |

## Workflows

> Prefer the **client** (`python -m aadr_client cohort ...`, see above) over the
> hand-rolled pandas below. The snippets here illustrate the underlying logic and
> the ADMIXTOOLS steps the client deliberately does not cover.

### Workflow 1 — Ancient host–pathogen pair lookup

Goal: for a region/period of MTBC interest, find skeletons that have **both**
AADR-catalogued human DNA **and** published ancient MTBC DNA.

```python
import pandas as pd
anno = pd.read_csv("v62.0.anno", sep="\t", low_memory=False)

# Spatial + temporal filter
europe_medieval = anno[
    (anno["Political Entity"].isin(["Germany", "Hungary", "Italy", "England"]))
    & (anno["Date mean in BP"].between(500, 1500))
    & (anno["Assessment"].fillna("").str.contains("PASS"))
]

# Cross with a curated list of ancient-TB / pinnipedii publications
# (project tags as used in SPAAM AncientMetagenomeDir)
tb_papers = {"Bos2014", "Kay2015", "Sabin2020", "Vagene2022", "Jager2022"}
pairs = europe_medieval[europe_medieval["Data source"].isin(tb_papers)]
```

Then join the result to the `spaam-ancient-metagenome-dir` skill to get the
corresponding pathogen accession.

### Workflow 2 — Population context for a modern TB lineage

Goal: for a modern TB lineage with strong geographic signal, describe the
ancient human population history of that region.

1. Get the geographic centroid(s) of a lineage from TBannotator MCP.
2. Query AADR for all ancient individuals within a radius (e.g. 500 km) and
   a relevant time window.
3. Group by `Group Label` and time → sketch the sequence of populations that
   occupied the region.
4. Use this to frame the lineage's emergence/expansion in the article
   ("… the spread of L4.X across region Y is contemporaneous with the
   [Bronze Age steppe] ancestry expansion documented in AADR …").

### Workflow 3 — Demographic transition ↔ TB persistence

Goal: anchor the emergence of human-adapted MTBC clades in Neolithic/Bronze
Age demographic expansions.

1. Filter `.anno` by region + `Date mean in BP` between 12,000 and 2,000.
2. Bin by 500-year slices, count individuals per slice as a crude proxy of
   sample density (real demography requires SMC/IBD analyses — see below).
3. Overlay with TMRCA + expansion times of human-adapted L1–L9 lineages.
4. Complement with **p3k14c** SPD workflow for archaeological demographic
   transitions.

### Workflow 4 — ADMIXTOOLS / qpAdm (Paul Verdu's toolkit)

AADR is the standard input for ADMIXTOOLS 2, `qpAdm`, `qpGraph`, `f3`/`f4`
statistics, and Approximate Bayesian Computation (ABC) population inference
(the Éco-anthropologie UMR 7206 approach). For a candidate coevolution
narrative:

```r
library(admixtools)
f2 <- f2_from_geno("v62.0", pops = c("Target", "Source1", "Source2", "Outgroup"))
qpadm(f2, target = "Target",
           sources = c("Source1", "Source2"),
           outgroups = c("Mbuti", "Han", "Papuan"))
```

The admixture proportions can then be temporally aligned with TB lineage
turnover in the same region.

## Pandas snippets

### Load and triage

```python
import pandas as pd
anno = pd.read_csv("v62.0.anno", sep="\t", low_memory=False)
print(anno.shape)
print(anno.columns.tolist()[:30])
print(anno["Assessment"].value_counts())
```

### Keep only high-quality ancients

```python
pass_ancient = anno[
    anno["Assessment"].fillna("").str.contains("PASS", na=False)
    & (anno["Date mean in BP"] > 0)
    & (anno["Coverage"].astype(str).str.replace(".", "", 1).str.isdigit())
]
```

### Map-ready GeoPandas export

```python
import geopandas as gpd
gdf = gpd.GeoDataFrame(
    anno.dropna(subset=["Lat.", "Long."]),
    geometry=gpd.points_from_xy(anno["Long."], anno["Lat."]),
    crs="EPSG:4326",
)
gdf.to_file("aadr_sites.gpkg", driver="GPKG")
```

## When NOT to use

- **Pathogen / TB genomes** — AADR is host-only. For ancient *M. tuberculosis* /
  *M. leprae* reads use `spaam-ancient-metagenome-dir`, ENA, or the pathogen
  paper supplements. To pair a skeleton's host + pathogen DNA, use
  `host-pathogen-pair`.
- **Dating an MTBC clade** — that is `molecular-clock` / `iqtree-lsd2` /
  `beast2-phylogeography`. AADR supplies the *human* dates to compare against.
- **Admixture / f-statistics** — the `.geno` genotype matrix is the input to
  ADMIXTOOLS 2 / qpAdm; this client parses only the `.anno` index (the metadata),
  not the genotypes.
- **Filtering by Ethnographic-Atlas code** — that is `d-place`; AADR has no EA code.

## Important caveats

- **Curation, not raw data.** AADR is a *compendium*: individual BAMs/FASTQs
  live in ENA/SRA under each original study. AADR provides the harmonized
  pseudohaploid genotype calls on standard panels (1240K, Human Origins).
- **No pathogen data.** AADR does not contain microbial reads. For ancient
  TB DNA use `spaam-ancient-metagenome-dir`, ENA searches, or the curated
  supplementary tables of the pathogen papers themselves.
- **Ancestry models ≠ population history.** `qpAdm` / `f`-statistics model
  **inferred admixture**, not ground truth. Always report uncertainty (feasible
  model space, p-values) and do not equate `Group Label` with a biological
  population in a naive sense.
- **Version drift.** Columns and individual IDs change between versions.
  Always pin the version (e.g. `v54.1.p1`) in articles and skill outputs.
- **Ethics.** AADR comes from skeletal remains — respect the ethical framing
  of the source publications (descendant community consultation, repatriation
  status, etc.).

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **TBannotator MCP** | Modern TB lineage geography + TMRCA |
| **spaam-ancient-metagenome-dir** | Ancient microbial/pathogen metagenomes (planned skill) |
| **p3k14c** | Archaeological radiocarbon context to frame AADR dates |
| **slavevoyages** | Post-1500 human movement — downstream of AADR's window |
| **ADMIXTOOLS 2 / qpAdm** | Canonical analysis of the AADR genotype matrix |
| **TreeTime / BEAST** | Molecular dating of TB clades, comparable to AADR dates |

## Citation

```bibtex
@article{mallick2024aadr,
  title   = {The Allen Ancient DNA Resource (AADR) a curated compendium of ancient human genomes},
  author  = {Mallick, Swapan and Micco, Adam and Mah, Matthew and others},
  journal = {Scientific Data},
  volume  = {11},
  number  = {1},
  pages   = {182},
  year    = {2024},
  doi     = {10.1038/s41597-024-03031-7},
  note    = {License CC BY 4.0; data at Harvard Dataverse DOI 10.7910/DVN/FFIDCW}
}
```
