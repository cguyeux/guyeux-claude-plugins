---
name: spaam-ancient-metagenome-dir
description: >-
  Query the SPAAM community AncientMetagenomeDir — the reference community
  catalogue of all published ancient metagenomic and ancient microbial
  single-genome samples. Find ancient Mycobacterium tuberculosis and related
  pathogen samples, their publications, sites, dates, and ENA/SRA accessions,
  and pair them with AADR ancient human hosts for coevolution narratives.

  Use when: finding published ancient MTBC genomes, locating raw data (ENA/SRA)
  for ancient pathogens, pairing an ancient TB strain with its human host
  in AADR, building a list of ancient metagenomes for a region/period, or
  filling the pathogen side of a host–pathogen coevolution story.
---

# SPAAM AncientMetagenomeDir — Ancient Metagenomes & Pathogen Genomes

## Overview

**AncientMetagenomeDir** is a community-curated catalogue of every published
shotgun-sequenced ancient metagenome or microbial single-genome sample. It is
maintained by the **SPAAM** community (Standards, Precautions and Advances in
Ancient Metagenomics) on GitHub, as version-controlled TSV tables with strict
schema and pull-request review.

- **Reference**: Fellows Yates J.A., Andrades Valtueña A., Vågene Å.J. et al.
  *Community-curated and standardised metadata of published ancient metagenomic
  samples with AncientMetagenomeDir.* **Scientific Data** 8:31 (2021).
  DOI: `10.1038/s41597-021-00816-y`
- **Repository**: `https://github.com/SPAAM-community/AncientMetagenomeDir`
- **Companion toolkit**: **AMDirT** (`amdirt`), Python package — Fellows Yates
  et al. *F1000Research* 12:926 (2023)
- **License**: **CC BY 4.0** (data) — the directory citation alone is
  **insufficient**; also cite each original paper whose data you use
- **Caveat (quoted from repo)**: *"The AncientMetagenomeDir community curates
  this data on a voluntary basis, and therefore provides no warranty or
  completeness or accuracy of the data."*

## Why it matters for MTBC

AncientMetagenomeDir is **the** entry point for published ancient TB DNA. It
lists every ancient *M. tuberculosis*, *M. leprae*, *M. pinnipedii*, and
related single-genome reconstructions alongside their publications and the
**raw-data accessions** (ENA/SRA), so you can go from a paper reference to a
downloadable FASTQ in a single lookup.

It is the **pathogen-side** counterpart to **`aadr`** (host-side): the two
together let you build per-individual host–pathogen pairs for coevolution
narratives.

## Directory structure

The repository contains three top-level data directories, each with samples
and libraries TSVs:

| Directory | What it catalogues |
|---|---|
| `ancientsinglegenome-hostassociated/` | **Ancient single-genome reconstructions** of host-associated microbes (e.g. ancient MTBC, *Y. pestis*, *Salmonella*, *M. leprae*, HBV, B19, etc.) — **the table for ancient TB** |
| `ancientmetagenome-hostassociated/` | Host-associated shotgun metagenomes (oral microbiome from dental calculus, gut from coprolites, etc.) |
| `ancientmetagenome-environmental/` | Environmental shotgun metagenomes (sediments, permafrost, lake cores, etc.) |

Each directory contains:

```
<directory>/
├── samples/
│   └── <directory>_samples.tsv
└── libraries/
    └── <directory>_libraries.tsv
```

The **samples** TSV holds one row per biological sample; the **libraries** TSV
holds one row per sequencing library (a sample can have several).

## Key columns — `ancientsinglegenome-hostassociated_samples.tsv` (19 fields)

| Column | Meaning |
|---|---|
| `project_name` | Short study tag (e.g. `Kay2015`, `Sabin2020`, `Bos2014`) |
| `publication_year` | Year of publication |
| `publication_doi` | DOI of the source paper |
| `site_name` | Archaeological site name |
| `latitude` | Decimal latitude (WGS84) |
| `longitude` | Decimal longitude (WGS84) |
| `geo_loc_name` | Country (INSDC convention) |
| `sample_name` | Author-supplied sample label (often matches AADR `Genetic ID`) |
| `sample_host` | Host organism (*Homo sapiens*, *Bos taurus*, etc.) |
| `sample_age` | Age in years BP |
| `sample_age_doi` | DOI for the dating reference |
| `singlegenome_domain` | Taxonomic domain (Bacteria, Virus…) |
| `singlegenome_species` | Pathogen species (**`Mycobacterium tuberculosis`**, *M. leprae*, *Y. pestis*…) |
| `material` | Substrate (bone, tooth, calcified nodule, lung tissue, coprolite…) |
| `genome_type` | chromosome / plasmid / viral segment |
| `archive` | ENA / SRA / other |
| `data_type` | raw / enriched / shotgun… |
| `archive_project` | Project-level accession (PRJEB…, PRJNA…) |
| `archive_accession` | Sample-level or run-level accession |

MTBC-bearing studies **actually present** in the directory (verified
snapshot — always re-check the live TSV):

| `project_name` | N indiv. | Site / host | Age (BP) | Pathogen | DOI |
|---|---|---|---|---|---|
| `Bos2014` | 3 | Peru (pre-Columbian) — El Yaral, El Algodonal, Chiribaya Alta | 900–1 000 | ***M. pinnipedii*** in humans | `10.1038/nature13591` |
| `Kay2015` | 8 | Hungary — Dominican church of Vác (mummies, bone + lung + abdomen) | 100–200 | *M. tuberculosis* | `10.1038/ncomms7717` |
| `Sabin2020` | 1 | Sweden — Lund Cathedral (Bishop Winstrup, calcified nodule) | ~300 | *M. tuberculosis* | `10.1186/s13059-020-02112-1` |
| `Vagene2022` | 3 | Peru + Colombia — Moquegua M6-Estuquiña, Bogotá (colonial) | 500–700 | ***M. pinnipedii*** in humans | `10.1038/s41467-022-28562-8` |
| `Jager2022` | 1 | Hungary — Dominican church of Vác (additional sample) | ~200 | *M. tuberculosis* | `10.1016/j.tube.2022.102181` |

Related (non-MTBC, but ancient *Mycobacterium* or useful context):

| `project_name` | Pathogen | Notes |
|---|---|---|
| `Schuenemann*` | *M. leprae* | 49 individuals across 13 European + Middle Eastern countries, 100–2 200 BP |
| `Vagene` (2018) | *Salmonella enterica* Paratyphi C | 1545 CE Mexican *cocoliztli* (Teposcolula-Yucundaa), cross-reference for post-contact epidemics |

> [!WARNING]
> The MTBC corpus in SPAAM is **very small** — **16 individuals, 5 projects,
> 4 countries** (Peru, Hungary, Sweden, Colombia), and **nothing older than
> ~1 000 BP**. By contrast, ancient *M. leprae* counts **49 individuals across
> 13 countries and 2 200 years**. There is currently **no ancient DNA for
> *M. bovis*, *M. caprae*, *M. africanum*, or *M. canettii*** in the catalogue,
> and no Bronze Age or Neolithic human-adapted MTBC. Narratives built on
> "domestication-era MTBC ancient DNA" are therefore under-constrained by the
> published record — frame them as testable hypotheses, not demonstrated facts.

> [!NOTE]
> The directory grows regularly via community pull requests. Always
> re-download the master-branch TSV and filter for *Mycobacterium* before
> writing a Methods section.

## *Yersinia pestis* — the richest ancient-pathogen corpus in SPAAM

*Y. pestis* is the **#1 species** in the SPAAM single-genome table
by count, with **214 individuals** across **36 distinct projects**
(verified snapshot). This is **3.1× larger than ancient *M. leprae***
and **~13× larger than ancient MTBC**. The corpus spans **5 300 years
BP → modern**, making it the deepest-time ancient-pathogen record
available — the canonical test-bed for the "history of humans
through pathogens" paradigm.

### Verified composition (current snapshot) — by historical period

| Period | N | Projects |
|---|---|---|
| **Modern (<500 BP)** | 70 | various modern surveys |
| **Medieval / Black Death (500–1 200 BP)** | 47 | 11 projects — see below |
| **Late Antique / Justinian (1 200–1 600 BP)** | **35** | 5 projects — see below |
| **Bronze Age → Iron Age (1 600–3 000 BP)** | 6 | minor |
| **Late Neolithic Bronze Age / LNBA (2 500–5 300 BP)** | **65** | 14 projects — **the origin-of-plague corpus** |

### The Late Neolithic / Bronze Age plague corpus (65 individuals, 14 projects)

This is **the corpus that established the ~5 000 year origin** of human-
infecting *Y. pestis* in Eurasia, beginning with Rasmussen et al. 2015
*Cell* and now comprising:

| Project | N | Age range (BP) | Geography |
|---|---|---|---|
| **Seersholm2024** | **17** | **4 700–5 300** | Denmark, Sweden — **the oldest *Y. pestis* known (~3 300 BCE)** |
| **AndradesValtuena2022** | 17 | 2 500–4 200 | Czechia, Germany, Kazakhstan, Mongolia, Poland, Russia, Spain, Ukraine — pan-Eurasian Bronze Age |
| **Rasmussen2015** | 7 | 2 800–4 200 | Armenia, Estonia, Poland, Russia — the founding Bronze Age plague paper |
| **AndradesValtuena2017** | 6 | 3 600–4 200 | Croatia, Estonia, Germany, Lithuania, Russia |
| **Swali2023** | 3 | 3 900–4 000 | United Kingdom |
| **Neumann2022** | 2 | 4 100–4 200 | Greece |
| **Neumann2023** | 2 | 3 900 | Austria |
| **Kilinc2021** | 2 | 3 500–4 000 | Russia |
| **Yu2020** | 2 | 4 400–4 600 | Russia |
| **Susat2024** | 2 | 5 100–5 200 | Germany |
| **Spyrou2018** | 2 | 3 500 | Russia |
| **Rascovan2019** | 1 | 4 400 | Sweden |
| **Susat2021** | 1 | 5 200 | Latvia |
| **LightMaka2025** | 1 | 3 800 | Russia |

**Key finding**: the oldest strains (Seersholm 2024, Susat 2021/2024)
lack the `ymt` gene required for flea-borne transmission, suggesting
that the early Neolithic plague was **transmitted directly between
humans** (respiratory or pneumonic route) rather than via rodent-flea
cycles. The transition to flea-borne plague happened sometime during
the Bronze Age, enabling the explosive epidemic dynamics of later
pandemics.

### The Justinian plague corpus (35 individuals, 5 projects)

| Project | N | Age range (BP) | Countries | Key site(s) |
|---|---|---|---|---|
| **Keller2019** | **30** | 1 300–1 600 | France, Germany, Spain, UK | **Edix Hill (UK), Lunel-Viel, Saint-Doulchard (FR), Dittenheim, Petting (DE)** — the dominant Justinian corpus |
| **Wagner2014** | 2 | 1 400 | Germany | Aschheim-Bajuwarenring (the first published Justinian *Y. pestis*) |
| **Feldman2016** | 1 | 1 500 | Germany | Altenerding |
| **Guellil2022** | 1 | 1 500 | UK | Edix Hill, Cambridgeshire |
| **deBarrosDamgaard2018** | 1 | 1 300 | Russia | Unknown |

### The Black Death / Medieval corpus (47 individuals, 11 projects)

| Project | N | Countries | Note |
|---|---|---|---|
| **Eaton2023** | 13 | Denmark | — |
| **Spyrou2019** | 9 | France, Germany, Russia, UK | — |
| **Namouchi2018** | 5 | France, Italy, Netherlands, Norway | — |
| **Parker2023** | 5 | Germany | — |
| **Bos2011** | 4 | UK | **East Smithfield (London 1348–1350), Nature 2011 — a first of its kind** |
| **Spyrou2022** | 3 | **Kyrgyzstan** | ***Nature* 2022 — the Kara-Djigach + Burana cemeteries near Lake Issyk-Kul, dated 1338–1339 CE by tombstone inscriptions — the canonical "origin of the Black Death" paper** |
| **Morozova2020** | 3 | Poland, Russia | — |
| **Spyrou2016** | 2 | Russia, Spain | — |
| **Schuenemann2011** | 1 | UK | — |
| **Guellil2020** | 1 | Italy | — |
| **Bonczarowska2023** | 1 | Denmark | — |

> [!NOTE]
> **Canonical references to always cite for ancient *Y. pestis***:
> - **Rasmussen K. et al. 2015 *Cell* 163(3): 571–582. DOI: `10.1016/j.cell.2015.10.009`** — founding Bronze Age plague paper
> - **Bos K.I. et al. 2011 *Nature* 478(7370): 506–510. DOI: `10.1038/nature10549`** — first complete ancient *Y. pestis* genome (East Smithfield, London 1348–1350)
> - **Wagner D.M. et al. 2014 *Lancet Infect Dis* 14(4): 319–326** — first Justinian plague genome (Aschheim)
> - **Feldman M. et al. 2016 *Mol Biol Evol* 33(11): 2911–2923. DOI: `10.1093/molbev/msw170`** — second Justinian genome (Altenerding)
> - **Keller M. et al. 2019 *PNAS* 116(25): 12363–12372. DOI: `10.1073/pnas.1820447116`** — 30-genome Justinian panel across Europe
> - **Spyrou M.A. et al. 2022 *Nature* 606: 718–724. DOI: `10.1038/s41586-022-04800-3`** — Issyk-Kul (Kyrgyzstan) Black Death origin

## Key columns — `ancientmetagenome-hostassociated_samples.tsv` (16 fields)

This table catalogues **shotgun metagenomes** of host-associated material —
not single-species reconstructions. Verified snapshot: **1,733 samples,
69 projects, 26 host species, 58 countries**.

| Column | Meaning |
|---|---|
| `project_name` | Short study tag |
| `publication_year`, `publication_doi` | Source publication |
| `site_name`, `latitude`, `longitude`, `geo_loc_name` | Geographic info |
| `sample_name` | Author-supplied sample label |
| `sample_host` | Host organism (binomial) |
| `sample_age`, `sample_age_doi` | Age in years BP and dating reference |
| `community_type` | Body site / community kind: **`oral`** / `gut` / `skeletal tissue` / `plant tissue` / `soft tissue` |
| `material` | Substrate: `dental calculus`, `tooth`, `bone`, `palaeofaeces`, `intestine`, `digestive tract contents`, … |
| `archive`, `archive_project`, `archive_accession` | ENA/SRA accession path |

### Verified composition (current snapshot)

**community_type breakdown** — 1,248 oral / 294 skeletal tissue /
81 plant tissue / 80 gut / 30 soft tissue.

**material top 10** — `dental calculus` (979), `tooth` (376), `bone` (143),
`leaf` (81), `palaeofaeces` (42), `rib` (33), `intestine` (14),
`sediment` (14), `digestive tract contents` (10), `unknown` (6).

**sample_host top 10** — *Homo sapiens* (1 327), *Ursus arctos* (85),
*Ambrosia artemisiifolia* (47), *Rangifer tarandus* (39),
*Arabidopsis thaliana* (34), ***Homo sapiens neanderthalensis*** (32),
*Pan troglodytes schweinfurthii* (26), *Mammuthus primigenius* (22),
*Gorilla beringei graueri* (21), *Gorilla beringei beringei* (17).

> [!NOTE]
> **Why this table matters for MTBC.** Dental calculus is the dominant
> source of ancient oral microbiome reconstructions, and oral microbiome
> shotgun reads are the substrate from which several ancient *Mycobacterium*
> screens have been done. The `oral` community alone holds **1 248 samples**
> — a vastly larger pool than the 16 single-genome MTBC entries in
> `ancientsinglegenome-hostassociated`. Use this table when **screening**
> for *Mycobacterium* reads in published shotgun data, not when looking
> for already-reconstructed pathogen genomes.

## Key columns — `ancientmetagenome-environmental_samples.tsv` (19 fields)

This table catalogues environmental shotgun metagenomes (sediments,
permafrost, lake cores, marine cores, cave sediments). Verified
snapshot: **803 samples, 40 projects, 35 countries**.

| Column | Meaning |
|---|---|
| `project_name` | Short study tag |
| `publication_year`, `publication_doi` | Source publication |
| `site_name`, `latitude`, `longitude`, `geo_loc_name` | Geographic info |
| `study_primary_focus` | What the original paper targeted: `faunal`, `floral`, `microbial`, or combinations |
| `sequence_name` | Sequence-level identifier |
| `depth` | Sampling depth in core / sediment column |
| `sample_name`, `sample_age`, `sample_age_doi` | Sample-level metadata |
| `feature` | Habitat: `lake`, `ocean`, `cave`, `midden`, `sea coast`, `swamp forest`, `archeological site`, `thermokarst`, … |
| `material` | `lake sediment`, `marine sediment`, `permafrost`, `soil`, `shell`, `midden`, … |
| `sampling_date` | Year of physical sampling |
| `archive`, `archive_project`, `archive_accession` | ENA/SRA accession path |

### Verified composition (current snapshot)

**feature top 10** — `lake` (258), `ocean` (228), `cave` (133),
`midden` (47), `sea coast` (44), `swamp forest` (29), `archeological site`
(17), `shell` (16), `thermokarst` (14), `rock shelter` (13).

**material top 10** — `lake sediment` (258), `sediment` (219),
`marine sediment` (188), `permafrost` (66), `shallow marine sediment` (36),
`shell` (16), `midden` (15), `soil` (5).

**study_primary_focus top 5** — `faunal,floral` (239), `faunal` (171),
`microbial` (106), `faunal,floral,microbial` (100), `floral` (67).

> [!NOTE]
> **MTBC relevance is indirect.** Environmental metagenomes do not
> typically yield human-adapted MTBC, but they can document **cave
> *Mycobacterium*** (relevant to bat-associated mycobacterial reservoirs)
> and **soil/sediment *Mycobacterium*** at archaeological sites (potential
> source of contamination or environmental signal). Use this table only
> for environmental-context arguments, not for primary host-pathogen claims.

## Data Access

### Option A — AMDirT (recommended)

**Install**:
```bash
# conda (preferred, pulls correct Python env)
conda create -n amdirt -c bioconda amdirt
conda activate amdirt

# or pip
pip install amdirt
```

**Typical commands** (see `amdirt --help` and
`https://amdirt.readthedocs.io/` for the authoritative reference):

```bash
# Launch the interactive Streamlit filter UI
amdirt viewer

# Validate a TSV against the AncientMetagenomeDir schema
amdirt validate \
  --schema ancientsinglegenome-hostassociated \
  my_table.tsv

# Convert a filtered TSV to ENA/SRA download scripts + nf-core/eager input
amdirt convert \
  --librarymetadata my_libraries.tsv \
  --output-dir ./downloads \
  --curl --eager
```

AMDirT outputs `curl`/`wget` download scripts plus ready-to-use samplesheets
for **nf-core/eager**, **aMeta**, and other ancient-DNA pipelines.

### Option B — Raw TSVs from GitHub

The TSVs are plain version-controlled files. Pull the repo, or fetch a single
file via `raw.githubusercontent.com`:

```bash
git clone https://github.com/SPAAM-community/AncientMetagenomeDir.git

# Or single-file fetch:
curl -LO https://raw.githubusercontent.com/SPAAM-community/AncientMetagenomeDir/master/ancientsinglegenome-hostassociated/samples/ancientsinglegenome-hostassociated_samples.tsv
```

Then load with pandas — see snippets below.

## Workflows

### Workflow 1 — Find every ancient MTBC sample published

```python
import pandas as pd
df = pd.read_csv(
    "ancientsinglegenome-hostassociated_samples.tsv",
    sep="\t", low_memory=False,
)
mtbc = df[df.singlegenome_species.str.contains("Mycobacterium tuberculosis|Mycobacterium pinnipedii|Mycobacterium canettii",
                                               regex=True, case=False, na=False)]
print(mtbc[["project_name", "site_name", "geo_loc_name",
            "sample_age", "material", "archive_accession"]])
```

### Workflow 2 — Pair an ancient MTBC sample with its AADR human host

Given an ancient pathogen sample from `spaam-ancient-metagenome-dir`:

1. Note its `project_name` + `sample_name`.
2. Load AADR `.anno` (see `aadr` skill).
3. Join:
   ```python
   joined = mtbc.merge(
       aadr_anno,
       left_on="sample_name",
       right_on="Genetic ID",
       how="left",
       suffixes=("_tb", "_host"),
   )
   ```
4. Rows with a matched AADR entry are **host–pathogen pairs from the same
   skeleton** — the strongest possible coevolution evidence.
5. Rows without a match usually mean the paper did not deposit a
   matching nuclear-genome dataset on AADR (check the paper directly).

### Workflow 3 — Build a region/period cohort for download

For a region + period of interest (e.g. Neolithic Anatolia):

```python
anatolia_neolithic = df[
    (df.geo_loc_name == "Turkey")
    & (df.sample_age.between(6000, 10000))
    & (df.singlegenome_species.str.contains("Mycobacterium", na=False))
]
anatolia_neolithic[["project_name", "site_name", "sample_age",
                    "archive", "archive_project", "archive_accession"]].to_csv(
    "anatolia_neolithic_mtbc.tsv", sep="\t", index=False,
)
```

Feed the output to `amdirt convert` to generate a download batch.

### Workflow 4 — Build a citations list for a manuscript section

```python
(mtbc[["project_name", "publication_year", "publication_doi"]]
     .drop_duplicates()
     .sort_values(["publication_year", "project_name"]))
```

Export → format as BibTeX (cross-reference with `bib-check`).

### Workflow 5 — Screen ancient dental calculus shotgun studies for *Mycobacterium*

Goal: identify published ancient oral-microbiome shotgun datasets that
could be re-screened for *Mycobacterium* (or specifically MTBC) reads —
something the 16-row pathogen single-genome table cannot tell you alone.

```python
import pandas as pd

ha = pd.read_csv(
    "ancientmetagenome-hostassociated_samples.tsv",
    sep="\t", low_memory=False,
)

oral_human = ha[
    (ha.community_type == "oral")
    & (ha.material.isin(["dental calculus", "tooth"]))
    & (ha.sample_host == "Homo sapiens")
]
print(f"{len(oral_human)} ancient human oral-microbiome samples")

# Group by region + period for a screening cohort
cohort = (oral_human
          .assign(period=pd.cut(oral_human.sample_age,
                                bins=[0, 500, 2000, 5000, 12000],
                                labels=["historical","medieval","iron-bronze","neolithic+"]))
          .groupby(["geo_loc_name","period"]).size()
          .sort_values(ascending=False))
print(cohort.head(20))
```

Then for each project of interest, fetch the libraries TSV via
`amdirt`, generate a download script, and run a *Mycobacterium*
screening pipeline (`nf-core/aMeta` or HOPS — see the
`spaam-community` skill for pipeline guidance).

This is an explicit instance of the **TBannotator-style "discover
unrecognised positives in published data"** workflow — the SPAAM
catalogue surfaces the substrate, an aMeta/HOPS run does the
screening, and any hit becomes a candidate for full reconstruction.

### Workflow 6 — Cave sediments as candidate environmental *Mycobacterium* sources

Goal: identify cave-sediment metagenomes that could carry environmental
or bat-associated *Mycobacterium* signal — a niche but defensible
side-channel for the constellation.

```python
env = pd.read_csv(
    "ancientmetagenome-environmental_samples.tsv",
    sep="\t", low_memory=False,
)

cave_microbial = env[
    (env.feature == "cave")
    & (env.study_primary_focus.fillna("").str.contains("microbial"))
]
print(cave_microbial[["project_name","site_name","geo_loc_name",
                      "sample_age","material","archive_accession"]])
```

> [!WARNING]
> Treat any *Mycobacterium* signal from cave sediments with extreme
> caution: environmental and saprophytic mycobacteria are abundant and
> easily confused with MTBC at the read level. Only species-level
> reference-based mapping plus damage authentication can support an
> ancient MTBC claim from this kind of substrate.

## Calcified nodules, dental calculus, bone — material strata

The `material` column tells you which tissue yielded the ancient genome. For
MTBC this matters because recovery differs sharply by substrate:

| Material | Typical yield for MTBC | Examples |
|---|---|---|
| Calcified nodules (Ghon focus, pleural) | **Very high** (Winstrup) | Sabin2020 |
| Vertebral / rib bone lesions | Moderate to high | Bos2014, Vagene2022, Jager2022 |
| Dental calculus | Low for MTBC, high for oral microbiome | Various oral-metagenome papers |
| Lung tissue (mummified / preserved soft tissue) | High but rare | Kay2015 (Vác) |
| Coprolite | Very low for MTBC | — |

Use this table to set expectations when suggesting a region/material for a
new ancient-TB prospecting study.

## Caveats

- **Voluntary curation.** The directory is maintained by volunteers; gaps and
  delays exist. Always spot-check against recent literature.
- **Snapshot in time.** Pin the Git commit hash or repo tag in your article's
  Methods to make your query reproducible.
- **Sample name ↔ AADR join is not guaranteed.** Papers do not always use the
  same individual identifier on both sides; fall back to `site_name` +
  `sample_age` + publication when the direct join fails.
- **Raw data can be unavailable.** Some studies restrict access via controlled-
  access archives (EGA) rather than public ENA/SRA. `archive_accession` may
  point to a study-level PRJ rather than an FTP path.
- **Citation requirement.** CC-BY requires citing **both** the directory paper
  and each original source paper you use data from.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`aadr`** | Host-side ancient human genomes — pair with this skill for host–pathogen evidence |
| **`p3k14c`** | Archaeological chronology to contextualize sample dates |
| **`slavevoyages`** | Post-colonial human movement — irrelevant before 1500 but complementary for recent ancient TB |
| **TBannotator MCP** | Modern TB comparator for phylogenetic placement of ancient genomes |
| **nf-core/eager, aMeta** | Pipelines consuming `amdirt convert` samplesheets |
| **TreeTime / BEAST** | Molecular dating with ancient tip-dates from this directory |
| **ENA / SRA** | Raw FASTQ retrieval from `archive_accession` |

## Citations

```bibtex
@article{fellowsyates2021spaam,
  title   = {Community-curated and standardised metadata of published ancient
             metagenomic samples with AncientMetagenomeDir},
  author  = {Fellows Yates, James A. and Andrades Valtue{\~n}a, Aida and
             V{\aa}gene, {\AA}shild J. and others},
  journal = {Scientific Data},
  volume  = {8},
  number  = {1},
  pages   = {31},
  year    = {2021},
  doi     = {10.1038/s41597-021-00816-y},
  note    = {License CC BY 4.0}
}

@article{fellowsyates2023amdirt,
  title   = {Facilitating accessible, rapid, and appropriate processing of
             ancient metagenomic data with AMDirT},
  author  = {Fellows Yates, James A. and others},
  journal = {F1000Research},
  volume  = {12},
  pages   = {926},
  year    = {2023}
}
```
