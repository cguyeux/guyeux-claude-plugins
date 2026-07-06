---
name: bacdive
description: >-
  Academic research database client (Guyeux group, FEMTO-ST). Queries the peer-reviewed BacDive strain metadatabase for published-research isolates. Query BacDive, the DSMZ Bacterial Diversity Metadatabase — the world's
  largest structured repository of bacterial and archaeal strain
  information. Covers 97,000+ strains with 2.6 million data points across
  1,000+ fields: taxonomy, morphology, physiology, metabolism, cultivation,
  isolation source, biosafety level, antibiotic susceptibility, fatty
  acid profiles, and API® test results. The canonical resource for
  phenotypic and ecological metadata of type strains.

  Use when: retrieving phenotypic data for a bacterial species relevant
  to your TB / historical pathogen work, looking up cultivation
  conditions, checking biosafety level, finding type-strain reference
  for a taxon, or enriching a genomic analysis with phenotypic context.
---

# BacDive — The Bacterial Diversity Metadatabase

## Overview

**BacDive** is the reference open database of **structured bacterial and
archaeal strain metadata**, maintained at the **Leibniz Institute DSMZ**
(German Collection of Microorganisms and Cell Cultures GmbH, Braunschweig,
Germany). It aggregates taxonomic, morphological, physiological,
metabolic, cultivation, isolation, biosafety, fatty-acid, antibiotic
susceptibility and API® test data for the worldwide community, with a
focus on **type strains** and reference collections.

- **Reference (current)**: Reimer L.C., Vetcininova A., Söhngen C. et al.
  *BacDive in 2025: the core database for prokaryotic strain data.*
  **Nucleic Acids Research** 53(D1): D748–D756 (2025). DOI:
  `10.1093/nar/gkae1080`
- **Earlier reference**: Reimer L.C. et al. *BacDive in 2019: bacterial
  phenotypic data for high-throughput biodiversity analysis.* **Nucleic
  Acids Research** 47(D1): D631–D636 (2019). DOI: `10.1093/nar/gky879`
- **Web portal**: `https://bacdive.dsmz.de/`
- **API documentation**: `https://api.bacdive.dsmz.de/`
- **R package**: `BacDiveR` — `https://tibhannover.github.io/BacDiveR/`
- **Host**: Leibniz Institute DSMZ, Braunschweig
- **License**: Data are open; cite the DSMZ and the current BacDive paper.

### Content (verified from BacDive 2025 paper)

- **97,334 strains**
- **20,060 type strains**
- **2.6 million data points**
- **1,000+ data fields**
- **15,357 API® test results** for **27,634 strains** — the worldwide
  largest API® biochemical test collection
- Fatty acid profiles and antibiotic susceptibility data integrated

> [!NOTE]
> As of **February 2026**, the BacDive API is **free to use without
> registration** (previously required a DSMZ Keycloak account). Always
> re-check the API docs for the current policy before deploying a
> programmatic pipeline.

## Why it matters for MTBC × anthropology

BacDive is the **phenotypic / ecological metadata layer** that sits on
top of the pure genomic resources. For your TB work its niches are:

1. **Cultivation and biosafety for TB work.** The *Mycobacterium
   tuberculosis* type strain H37Rv (DSM 43636) and related MTBC
   reference strains are all catalogued with their cultivation
   conditions, biosafety level (BSL-3 for MTBC), growth media,
   temperature, and atmospheric requirements. Useful when writing
   materials and methods, or when reconciling a historical culture
   description with modern practice.
2. **Isolation source metadata.** Every type strain has an explicit
   `isolation_source` field that is structured, not free text. For
   comparative analyses of human vs animal vs environmental
   mycobacteria, BacDive gives you a clean slice.
3. **Non-MTBC *Mycobacterium* context.** *M. bovis*, *M. caprae*,
   *M. microti*, *M. pinnipedii*, *M. avium*, *M. leprae*, the MAC and
   NTM groups are all catalogued with their reference strains.
   Essential background when discussing environmental vs zoonotic vs
   obligate human-adapted mycobacteria.
4. **Fatty-acid profiles and biochemistry.** Rarely the focus of a TB
   paper but occasionally decisive for discussing metabolic
   adaptation / niche differentiation between clades.

BacDive is **not** a primary source for phylogeography or surveillance
— it's the **reference phenotype database** that gives your phylogenetic
trees and AMR profiles a concrete biological interpretation.

## Data model

### Strain
The fundamental unit. Each strain has a unique BacDive ID and a canonical
DSMZ (or other culture collection) accession.

### Top-level fields (summary of the ~1,000-field schema)

| Category | Example fields |
|---|---|
| **Taxonomy** | Domain, phylum, class, order, family, genus, species, strain designation; LPSN status; valid publication |
| **Morphology** | Cell shape, size, Gram stain, motility, flagellation, spore formation |
| **Culture & growth** | Optimal temperature, pH, salinity, oxygen tolerance, growth medium (with DSMZ recipes) |
| **Physiology & metabolism** | Substrate utilisation, enzyme tests, fermentation products, **API® 20E / API® 50CH** test panels |
| **Isolation source** | Structured isolation info: host, organ, country, sampling date |
| **Biosafety** | BSL1 / BSL2 / BSL3 / BSL4 classification |
| **Genome** | Links to NCBI genome accessions, 16S rRNA sequence |
| **Fatty acids** | Quantitative fatty acid profile |
| **Antibiotic susceptibility** | MIC values where available |
| **Literature** | Linked publications describing the strain |
| **Culture collections** | DSMZ, ATCC, JCM, NBRC, CCM, etc. accession numbers |

## Data access

### Option A — Web UI (exploratory)

Search at `https://bacdive.dsmz.de/` by:
- Free text
- Taxonomic hierarchy (domain → species)
- Isolation source
- Country / geography
- Growth conditions
- Presence of specific phenotypic traits

Each strain page is a rich HTML record; export as PDF or copy fields.

### Option B — REST API (recommended for programmatic use)

Base URL: `https://api.bacdive.dsmz.de/`

As of February 2026, **no registration** is required.

Typical Python access pattern:

```python
import requests

BASE = "https://api.bacdive.dsmz.de"

# Look up by DSMZ ID
r = requests.get(f"{BASE}/fetch/dsm/43636")  # M. tuberculosis H37Rv
record = r.json()

# Search by taxonomy
r = requests.get(f"{BASE}/taxon/Mycobacterium/tuberculosis")
hits = r.json()
```

> [!NOTE]
> The exact endpoint structure and field names may have evolved — always
> verify against the live docs at `https://api.bacdive.dsmz.de/` before
> writing a long script.

### Option C — `BacDiveR` R package

For R users, `BacDiveR` (TIB Hannover) wraps the API with convenience
functions. See `https://tibhannover.github.io/BacDiveR/` for usage.

### Option D — Bulk query by strain list

For batch retrieval, concatenate strain IDs and iterate:

```python
ids = ["DSM 43636", "DSM 43990", "DSM 45120"]
records = []
for sid in ids:
    dsm_num = sid.replace("DSM ", "")
    r = requests.get(f"{BASE}/fetch/dsm/{dsm_num}")
    if r.ok:
        records.append(r.json())
```

Always include a polite rate limit (`time.sleep(0.2)` between calls)
and respect the DSMZ servers.

## Workflows

### Workflow 1 — Reference phenotype profile for an MTBC ecotype

Goal: for each MTBC ecotype (*M. tuberculosis*, *M. bovis*, *M. caprae*,
*M. africanum*, *M. microti*, *M. pinnipedii*, *M. canettii*, *M. orygis*),
retrieve the canonical phenotypic reference.

```python
species = [
    "Mycobacterium tuberculosis",
    "Mycobacterium bovis",
    "Mycobacterium caprae",
    "Mycobacterium africanum",
    "Mycobacterium microti",
    "Mycobacterium pinnipedii",
    "Mycobacterium canettii",
    "Mycobacterium orygis",
]
for sp in species:
    genus, epithet = sp.split(" ")
    r = requests.get(f"{BASE}/taxon/{genus}/{epithet}")
    # Extract growth temperature, BSL, typical host, isolation source, ...
```

Produces a reference table you can drop into the Methods / Discussion
of an MTBC phylogenomic paper.

### Workflow 2 — Biosafety lookup

Goal: check the BSL classification of a bacterial species before
planning lab work or writing a protocol.

```python
r = requests.get(f"{BASE}/taxon/Mycobacterium/tuberculosis")
strains = r.json()
# Extract the 'Risk assessment' / 'Biosafety level' field per strain
```

MTBC → BSL-3; *M. leprae* → BSL-2 (traditionally, though it is not
routinely culturable); NTMs → mostly BSL-2.

### Workflow 3 — Isolation source analysis across a genus

Goal: for the whole genus *Mycobacterium*, summarise where type
strains have been isolated (host, environment, geography).

```python
r = requests.get(f"{BASE}/taxon/Mycobacterium")
# Parse all species records, extract isolation_source fields
# Tabulate by category: human clinical, animal, environmental (soil/water), ...
```

This is the classic host-range argument for the genus, at a resolution
individual papers cannot easily provide.

### Workflow 4 — Enriching a modern TB isolate list with phenotype

Given a list of modern TB samples from TBannotator / EnteroBase,
enrich each species / subspecies record with BacDive phenotype data
for the reference strain of that taxon. Useful when a reviewer asks
*"what is the known phenotype of this lineage's closest reference?"*

## Caveats

- **Type strains, not field isolates.** BacDive's bread-and-butter is
  type strains and deposited reference collections. For per-isolate
  modern surveillance data use NCBI Pathogen Detection or EnteroBase.
- **Not a genomic database.** BacDive cross-links to NCBI for genome
  data but does not itself host sequences. For WGS you still need
  ENA / SRA.
- **Field richness is uneven.** The 1,000-field schema is aspirational;
  any given strain typically has only a subset populated. Filter on
  `field_is_present` before statistical aggregation.
- **API surface evolves.** Pin the API version and snapshot date in
  Methods. The endpoint layout changed between the pre-2024 and
  post-2024 versions.
- **"API®" = bioMérieux biochemistry test, not a web API.** Don't
  confuse the two: "API® tests" in BacDive refer to the bioMérieux
  microbial identification strips; "the BacDive API" refers to the web
  service. BacDive has 15 357 results of the former.
- **License nuances.** Data are open for academic use but cite the
  DSMZ and the BacDive publication in any derivative work.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`enterobase`** | Per-isolate WGS/cgMLST typing of the same species |
| **`ncbi-pathogen-detection`** | US surveillance data for modern isolates |
| **`pathogens-portal`** | European ENA-backed counterpart |
| **`spaam-ancient-metagenome-dir`** | Ancient samples — BacDive provides the phenotype of their modern references |
| **TBannotator MCP** | MTBC lineage typing — BacDive provides reference phenotypes per ecotype |
| **NCBI Taxonomy** | Canonical taxonomic IDs for cross-linking |
| **LPSN (List of Prokaryotic names with Standing in Nomenclature)** | Upstream taxonomic authority also maintained by DSMZ |
| **`BacDiveR`** (R package) | Alternative programmatic access |
| **AMRFinderPlus** | AMR gene calls that complement BacDive's antibiotic susceptibility fields |

## Citation

```bibtex
@article{reimer2025bacdive,
  title   = {BacDive in 2025: the core database for prokaryotic strain data},
  author  = {Reimer, Lorenz Christian and Vetcininova, Anastasia and
             S{\"o}hngen, Carola and others},
  journal = {Nucleic Acids Research},
  volume  = {53},
  number  = {D1},
  pages   = {D748--D756},
  year    = {2025},
  doi     = {10.1093/nar/gkae1080}
}

@article{reimer2019bacdive,
  title   = {BacDive in 2019: bacterial phenotypic data for
             high-throughput biodiversity analysis},
  author  = {Reimer, Lorenz Christian and Vetcininova, Anastasia and
             Carbasse, Joaquim Sardà and others},
  journal = {Nucleic Acids Research},
  volume  = {47},
  number  = {D1},
  pages   = {D631--D636},
  year    = {2019},
  doi     = {10.1093/nar/gky879}
}
```
