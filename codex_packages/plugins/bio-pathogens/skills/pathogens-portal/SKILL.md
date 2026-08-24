---

name: pathogens-portal
description: >-
  Academic research database client. Queries the EMBL-EBI Pathogens
  Portal, the public European scientific gateway to FAIR bacterial-
  genome biomolecular data hosted on the European Nucleotide Archive
  (ENA). Launched in July 2023, it indexes 200,000+ species and strains
  deposited in published research studies, served via standard ENA Data
  Hubs. The European peer-reviewed-research counterpart to NCBI
  Pathogen Detection.

  Use when: a research project needs to retrieve ENA/SRA-deposited
  ancient or modern bacterial-genome sequences for downstream academic
  comparative-genomics or phylogenomics analysis, locate all ENA
  projects associated with a research species, or build a Europe-centric
  scientific data-access workflow for a publication.
---

# Pathogens Portal : EMBL-EBI Gateway to Public Pathogen Data

## Overview

**Pathogens Portal** is the unified European entry point to public
pathogen biomolecular data, operated by **EMBL-EBI** and built on the
**European Nucleotide Archive (ENA)** Data Hubs infrastructure. Launched
in **July 2023**, it was designed to make pathogen data **FAIR** and to
federate the many pathogen-related datasets hosted at EMBL-EBI into a
single search-and-retrieval interface.

- **Web portal**: `https://www.pathogensportal.org/`
- **Training course**: `https://www.ebi.ac.uk/training/online/courses/pathogens-portal/`
- **Contact**: `ena-path-collabs@ebi.ac.uk`
- **Hosting**: EMBL-EBI (Hinxton, UK) on the ENA Data Hubs infrastructure
- **Launch**: July 2023
- **Coverage** (as reported at launch): data spanning **200,000+** pathogen
  species and strains
- **License**: ENA data follow the ENA/INSDC policy, public, no
  restrictions on reuse beyond attribution of the depositors

## Why it matters for MTBC × anthropology

Pathogens Portal is the **European counterpart** to `enterobase` (Warwick,
cgMLST-focused) and NCBI Pathogen Detection (`ncbi-pathogen-detection`,
cluster-focused). Its specific niche:

1. **Structured ENA pathogen search.** ENA is the European mirror of the
   INSDC (with GenBank and DDBJ). For any published ancient MTBC genome
   deposited in ENA (e.g. `Kay2015` → `PRJEB7454`), Pathogens Portal
   gives you the canonical metadata record without scraping the flat
   ENA browser.
2. **Federated coverage.** The portal aggregates data across ENA
   projects, EGA (European Genome-phenome Archive), and partner
   repositories. Useful when a paper deposits part of its data at EGA
   with controlled access and the rest on public ENA.
3. **Downstream analytical pipelines.** EMBL-EBI provides a growing set
   of analytical services on top of the portal (BLAST, phylogenetic
   placement, variant calling for ENA-hosted pathogens) that can save
   you from running the pipeline yourself for quick sanity checks.

For the MTBC ecosystem specifically, Pathogens Portal is a **lookup and
retrieval layer**, not a typing database, use it in tandem with
EnteroBase (which does cgMLST/HierCC) and TBannotator (which does
MTBC-specific typing).

## Data model and scope

Pathogens Portal aggregates:

| Data type | Source |
|---|---|
| Raw reads | ENA / SRA (INSDC) |
| Assemblies | ENA (assembly archive) |
| Annotated genomes | ENA (WGS) |
| Variants | ENA variation calls (when available) |
| Metadata | Sample, experiment, study, run tables (ENA schema) |

### Metadata schema (ENA sample + experiment tables)

The portal exposes the standard ENA schema for each record:

| Field | Meaning |
|---|---|
| `accession` | ENA sample/experiment/run ID (e.g. `ERR1234567`, `SAMEA…`) |
| `study_accession` | Parent project (`PRJEB…` / `PRJNA…`) |
| `sample_alias` | Free-text alias from submitter |
| `tax_id` / `scientific_name` | NCBI taxonomy ID + binomial |
| `host`, `host_scientific_name` | Host organism (when host-associated) |
| `collection_date`, `country`, `geographic_location (region)` | Sampling info |
| `isolation_source` | Substrate (sputum, blood, water…) |
| `sequencing_technology`, `library_strategy` | How the data were produced |
| `center_name` | Submitting institution |
| Many optional fields following MIxS-Path / MIGS-BA extensions | |

### Portal features

- Free-text search with faceted filters
- Integrated BLAST against the pathogen subset
- Per-species landing pages with counts and data availability
- Download cart for bulk retrieval
- Links to ENA Browser records for raw data

## Data access

### Option A : Pathogens Portal web UI

1. Go to `https://www.pathogensportal.org/`
2. Search by species, host, collection date, country, or study
3. Apply faceted filters
4. Export the filtered list as TSV / JSON
5. Follow the ENA links for raw data retrieval

### Option B : ENA Portal API (recommended for programmatic access)

Pathogens Portal is backed by the **ENA Discovery / Portal API** at
`https://www.ebi.ac.uk/ena/portal/api/`. This is the reproducible path
for batch queries:

```bash
# Search all ENA samples where scientific_name is Mycobacterium tuberculosis
# and the host is Homo sapiens, restricted to a country and date range.
curl -sL "https://www.ebi.ac.uk/ena/portal/api/search" \
  --data-urlencode 'result=sample' \
  --data-urlencode 'query=tax_id=1773 AND host="Homo sapiens" AND country="Ghana" AND collection_date>=2015' \
  --data-urlencode 'fields=accession,sample_alias,collection_date,country,host,isolation_source' \
  --data-urlencode 'format=tsv' \
  --data-urlencode 'limit=0' \
  -o mtb_ghana.tsv
```

Result types relevant to pathogens:

| `result=` | What it returns |
|---|---|
| `sample` | Sample-level metadata |
| `read_run` | Run-level metadata (one row per sequencing run) |
| `read_experiment` | Experiment-level metadata |
| `analysis` | Submitted analyses (e.g. variant calls, assemblies) |
| `assembly` | Assembly records |
| `taxon` | Taxonomic information |
| `study` | Study-level metadata |

### Option C : ENA Browser API (raw data retrieval by accession)

For fast downloads of specific records by accession:

```bash
# Get FASTQ URL(s) for a run accession
curl -sL "https://www.ebi.ac.uk/ena/browser/api/fasta/ERR1234567?lineLimit=1000"
curl -sL "https://www.ebi.ac.uk/ena/browser/api/xml/ERR1234567"
```

The Browser API is focused on retrieval; the Portal API is the right
tool for search.

## Workflows

### Workflow 1 : List all ENA samples for a species

Goal: enumerate every *Mycobacterium tuberculosis* sample in ENA with
its minimal metadata.

```python
import requests
import pandas as pd
import io

url = "https://www.ebi.ac.uk/ena/portal/api/search"
params = {
    "result": "sample",
    "query": "tax_id=1773",            # M. tuberculosis taxid
    "fields": "accession,sample_alias,tax_id,scientific_name,"
              "host,country,collection_date,isolation_source",
    "format": "tsv",
    "limit": 0,
}
r = requests.get(url, params=params, timeout=300)
df = pd.read_csv(io.StringIO(r.text), sep="\t")
print(len(df), "samples")
```

Feed this list to TBannotator, or intersect with a country/date filter
for a focused cohort.

### Workflow 2 : Retrieve an ancient TB study by project accession

Given `Kay2015` (Vác mummies, ENA project `PRJEB7454`), list every run:

```python
params = {
    "result": "read_run",
    "query": "study_accession=PRJEB7454",
    "fields": "run_accession,sample_accession,sample_alias,"
              "library_strategy,instrument_model,"
              "fastq_ftp,fastq_md5,read_count,base_count",
    "format": "tsv",
    "limit": 0,
}
runs = pd.read_csv(io.StringIO(requests.get(url, params=params).text),
                   sep="\t")
```

The `fastq_ftp` field gives you the direct FTP URLs for each FASTQ
file, ready to `wget`.

### Workflow 3 : Cross-check `spaam-ancient-metagenome-dir` accessions

For each SPAAM row with an ENA `archive_project`, verify that the
project still exists and retrieve the current run list:

```python
spaam = pd.read_csv("amdir_singlegenome_samples.tsv", sep="\t")
ena_projects = spaam[spaam.archive == "ENA"].archive_project.unique()

for proj in ena_projects:
    r = requests.get(url, params={
        "result": "read_run",
        "query": f"study_accession={proj}",
        "fields": "run_accession,sample_alias,library_strategy",
        "format": "tsv", "limit": 0,
    })
    print(proj, r.text.count("\n") - 1, "runs")
```

### Workflow 4 : Faceted exploration for lineage discovery

Goal: find countries with the most MTBC ENA samples in a given window,
to identify under-sampled regions worth prospecting.

```python
params = {
    "result": "sample",
    "query": 'tax_id=1773 AND collection_date>=2018 AND collection_date<2024',
    "fields": "accession,country",
    "format": "tsv",
    "limit": 0,
}
recent = pd.read_csv(io.StringIO(requests.get(url, params=params).text),
                     sep="\t")
print(recent.country.value_counts().head(20))
```

## Caveats

- **Search quality is metadata-bound.** If submitters did not fill
  `country` or `collection_date`, the records are invisible to your
  filters. Always include a null-tolerant fallback (`collection_date IS
  NULL`) when you care about completeness.
- **EGA controlled-access data are not fully exposed.** Some studies
  deposit part of their data on EGA with restricted access; Pathogens
  Portal will not return the raw reads for those without proper
  authorisation.
- **Taxonomic depth varies.** Filtering by `tax_id=1773` gives you
  *Mycobacterium tuberculosis* sensu stricto but not the whole MTBC
  (which also includes *M. bovis*, *M. africanum*, etc. at different
  taxids). Use the taxonomy API or a taxid list to cover the whole
  complex.
- **Pagination on very large queries.** Use `limit=0` for full results,
  but expect large downloads (tens of MB) for high-volume species.
- **Rate limits.** The ENA Portal API is tolerant but not unlimited.
  Space out heavy queries and use `limit` + offset for pagination in
  production code.
- **Overlap with NCBI.** ENA and SRA exchange data daily, but accession
  prefixes differ (ERR/ERS vs SRR/SRS). The same biological sample can
  appear under both; cross-reference via `sample_alias`.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`enterobase`** | cgMLST/HierCC typing of the same ENA samples |
| **`ncbi-pathogen-detection`** | US counterpart, cluster-based surveillance |
| **`spaam-ancient-metagenome-dir`** | Source of ancient pathogen ENA accessions |
| **TBannotator MCP** | MTBC-specific typing of the retrieved samples |
| **`bacdive`** | Phenotypic metadata for typed strains (complement to sequence data) |
| **ENA Browser** | Canonical raw-data retrieval |
| **BLAST (EMBL-EBI)** | Sequence search against the pathogen subset |

## Citation

Pathogens Portal itself does not have a single reference paper yet. Cite
the ENA:

```bibtex
@article{yuan2024ena,
  title     = {The European Nucleotide Archive in 2024},
  author    = {Yuan, Dai and others},
  journal   = {Nucleic Acids Research},
  volume    = {52},
  number    = {D1},
  pages     = {D92--D97},
  year      = {2024},
  doi       = {10.1093/nar/gkad1067}
}
```

Plus a URL citation for the portal itself:

> Pathogens Portal. EMBL-EBI, Hinxton, UK. `https://www.pathogensportal.org/`
> (accessed YYYY-MM-DD).

## Codex packaging note

This packaged copy targets Codex. MCP tool names in `allowed-tools` are prerequisites: verify them with `codex mcp list` in the active profile before relying on live queries.
