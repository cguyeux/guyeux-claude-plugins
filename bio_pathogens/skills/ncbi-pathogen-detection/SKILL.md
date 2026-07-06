---
name: ncbi-pathogen-detection
description: >-
  Academic research database client. Queries the public NCBI Pathogen
  Detection portal (NIH/NCBI), the open scientific platform that
  aggregates published bacterial genome assemblies into pre-computed
  SNP-clusters (PDS accessions) with phylogenetic trees, intended for
  use by the academic research community in evolutionary-genomics and
  comparative-genomics scholarly studies. Provides peer-reviewable
  annotations on virulence-gene content and antimicrobial-susceptibility
  alleles for academic comparative-genomics research. Complementary to
  EnteroBase (cgMLST) and the EMBL-EBI Pathogens Portal (ENA).

  Use when: a research manuscript needs to look up the public SNP-cluster
  assignment of a deposited bacterial isolate, retrieve a published
  phylogeny for a research article, cite AMR-allele content of a public
  sample in a scientific paper, or build a research-database integration
  for a peer-reviewed study.
---

# NCBI Pathogen Detection — Cluster-based Pathogen Surveillance

## Overview

**NCBI Pathogen Detection** is the US National Center for Biotechnology
Information's integrated pipeline and portal for real-time genomic
surveillance of bacterial pathogens, with a primary focus on **foodborne
disease** and **antimicrobial resistance**. It ingests newly deposited
WGS data daily, runs a comparative pipeline, and publishes **SNP clusters**
(PDS* accessions) with interactive phylogenies.

- **Web portal**: `https://www.ncbi.nlm.nih.gov/pathogens/`
- **Isolates Browser**: `https://www.ncbi.nlm.nih.gov/pathogens/isolates/`
- **About page**: `https://www.ncbi.nlm.nih.gov/pathogens/about/`
- **FAQ**: `https://www.ncbi.nlm.nih.gov/pathogens/faq/`
- **Status**: Beta (stable for years, still labelled Beta)
- **Host**: NCBI / NIH (USA)
- **Data sources**: US CDC, FDA, USDA, public-health labs, plus
  international contributions
- **License**: NCBI public data — free to use with attribution

> [!NOTE]
> The system is focused on **modern** isolates — it ingests new WGS data
> from ongoing surveillance. It is **not** a catalogue of ancient
> pathogen genomes. For ancient TB / *Y. pestis* use
> `spaam-ancient-metagenome-dir` or `aadr` instead.

## Why it matters for MTBC × anthropology

NCBI Pathogen Detection has specific value even for an ancient-DNA /
anthropology framing:

1. **Modern-isolate context for TB.** Although the public health
   foregrounds foodborne bacteria, the platform does ingest
   *Mycobacterium tuberculosis* submissions. You can pull pre-clustered
   modern MTBC data as a reference backdrop for placing ancient
   reconstructions.
2. **AMR resistance gene content.** NCBI maintains the **AMRFinderPlus**
   reference database used by Pathogen Detection to call resistance
   genes. For any MTBC isolate of interest you get a standardised
   resistance profile without having to run your own pipeline.
3. **SNP cluster → outbreak reconstruction.** The PDS cluster structure
   is the standard reference for US foodborne outbreaks. Cross-reference
   with EnteroBase HierCC for the same genera to triangulate
   phylogenetic signal.
4. **Precomputed phylogenies.** Every PDS cluster comes with a Newick
   tree, which saves you a RAxML / IQ-TREE run for exploratory work.

## Core concepts

### Isolate
The fundamental unit: one bacterial WGS submission (reads + assembly +
metadata). Each isolate gets a stable NCBI identifier.

### SNP cluster (PDS accession)
A cluster of closely related isolates identified by the pipeline via
**wgMLST** or **K-mer comparison**, then refined by SNP calling and
phylogenetic inference. Each cluster has a `PDS*` accession. The cluster
pages show the tree, the isolates, their metadata, and the distribution
of AMR/virulence content.

### AMR and virulence content
Isolates are screened against the NCBI **AMRFinderPlus** reference
database and virulence gene databases; hits are reported per isolate.

### Pathogens covered
Strongest coverage:

- *Salmonella enterica* (largest)
- *Escherichia coli* / *Shigella*
- *Listeria monocytogenes*
- *Campylobacter*
- *Vibrio* spp.
- *Klebsiella pneumoniae*
- *Pseudomonas aeruginosa*
- *Acinetobacter baumannii*
- *Clostridium perfringens*
- Selected *Mycobacterium* (including *M. tuberculosis*)
- Many others under the "Pathogen Detection - Beta" umbrella

## Data access

### Option A — Isolates Browser (web UI)

1. Go to `https://www.ncbi.nlm.nih.gov/pathogens/isolates/`
2. Select a pathogen scope (e.g. *Mycobacterium tuberculosis*)
3. Apply filters: collection date, country, source type, AMR gene
   presence, SNP cluster
4. Click on a PDS* identifier in the *SNP Cluster* column to open the
   interactive Tree Viewer
5. Export selected isolates as TSV

### Option B — Bulk FTP dumps

NCBI Pathogen Detection publishes daily snapshots via FTP:

```
https://ftp.ncbi.nlm.nih.gov/pathogen/Results/
```

Structure (per pathogen, per date):

```
Results/
  ├─ Mycobacterium_tuberculosis/   (when present)
  ├─ Salmonella/
  ├─ Escherichia_coli_Shigella/
  ├─ Listeria/
  └─ ...
```

Each pathogen directory contains:

| File | Content |
|---|---|
| `*.metadata.tsv` | Isolate-level metadata (one row per isolate) |
| `*.amr.metadata.tsv` | AMR + virulence gene calls |
| `*.SNP_tree.newick` | Per-cluster Newick trees |
| `*.SNP_tree.pdf` | PDF renderings of the trees |
| `*.reference_targets.tsv` | Reference identifiers |

Pin the snapshot date for reproducibility.

### Option C — NCBI Datasets API

The broader NCBI Datasets API (`api.ncbi.nlm.nih.gov/datasets/v2/`)
exposes many fields from the Pathogen Detection workflow. Useful for
programmatic bulk retrieval, though the primary access path remains the
FTP dumps.

### Option D — SNP cluster trees (output formats)

From the tree viewer on the Isolates Browser:

- **Newick** (`.newick`) — standard phylogenetic format
- **ASN.1** (`.asn`) — loadable in NCBI Genome Workbench
- **PDF** — static rendering for publication figures

## Parallel calls

When downloading multiple cluster snapshots, SNP distance matrices, or
metadata sheets, dispatch the requests in parallel (multiple tool calls
per message). NCBI FTP and the Pathogen Detection REST endpoints handle
concurrent reads fine; serial loops over many clusters are the main
bottleneck for this skill.

## Workflows

### Workflow 1 — Pull the latest *M. tuberculosis* snapshot

```bash
mkdir -p ~/data/ncbi_pathogen/mtb && cd ~/data/ncbi_pathogen/mtb

# Check which latest subdirectory exists for your pathogen of interest
curl -sL "https://ftp.ncbi.nlm.nih.gov/pathogen/Results/" | grep Mycobacterium

# Fetch the metadata dump for a chosen date
# (structure: Mycobacterium_tuberculosis/latest_snps/Metadata/*)
wget -r -np -nH --cut-dirs=4 \
  "https://ftp.ncbi.nlm.nih.gov/pathogen/Results/Mycobacterium_tuberculosis/latest_snps/Metadata/"
```

Parse the metadata TSV:

```python
import pandas as pd
meta = pd.read_csv("PDG*.metadata.tsv", sep="\t", low_memory=False)
print(meta.shape)
print(meta.columns.tolist())
# Typical columns: target_acc, biosample_acc, Isolate, SNP_cluster,
# AMR_genotypes, Virulence_genotypes, geo_loc_name, collection_date,
# isolation_source, host, ...
```

### Workflow 2 — Cross-reference with AMR gene content

```python
amr = pd.read_csv("PDG*.amr.metadata.tsv", sep="\t", low_memory=False)
# One row per isolate × AMR element hit
resistance = (amr.groupby("Isolate")["AMR_genotypes"]
                 .apply(lambda s: ",".join(sorted(set(s.dropna()))))
                 .reset_index())
```

For MTBC, standard AMR genes tracked include `rpoB` (rifampicin),
`katG`/`inhA` (isoniazid), `pncA`, `embB` (ethambutol), `gyrA`/`gyrB`
(fluoroquinolones), etc. The snapshot gives you a **pre-computed
resistance profile** that can inform lineage-level comparisons.

### Workflow 3 — Cluster look-up for an outbreak

Given a known isolate of interest, find its PDS cluster and the other
members:

```python
target = "SAMN12345678"
cluster_id = meta.loc[meta.biosample_acc == target, "SNP_cluster"].iloc[0]
cluster_members = meta[meta.SNP_cluster == cluster_id]
print(cluster_members[["Isolate","geo_loc_name","collection_date",
                       "host","isolation_source"]])
```

Then download the Newick file for the cluster to visualise the tree
locally.

### Workflow 4 — Compare NCBI PDS clusters with EnteroBase HierCC

For enteric pathogens (*Salmonella*, *E. coli*, *Vibrio*, etc.), the
same biosamples are often typed in both systems. Cross-referencing
NCBI PDS clusters with EnteroBase HierCC levels is a way to validate
a surveillance signal across two independent pipelines:

1. Extract biosample accessions per PDS cluster from NCBI.
2. Query EnteroBase for the same biosamples' HC0–HC2850 values
   (see the `enterobase` skill).
3. Agreement between independent clustering methods strengthens the
   inference of a real outbreak / lineage.

## Caveats

- **Modern-only.** Ancient pathogens are not in scope.
- **US bias.** Coverage is strongest for isolates submitted by US
  agencies (CDC, FDA, USDA). International coverage is growing but
  uneven.
- **SNP cluster boundaries are pipeline-specific.** A PDS cluster is
  defined by the NCBI wgMLST/K-mer + SNP pipeline and is not directly
  comparable to EnteroBase HierCC or to downstream manual phylogenies.
  Use cross-reference, not direct equivalence.
- **Beta status → API changes.** The system has been in "beta" for
  years but schema and file layout do evolve. Pin the snapshot date
  and the file naming scheme you used.
- **AMR calls are genotype predictions.** Presence of a resistance gene
  ≠ phenotypic resistance in every case. Treat as hypothesis generator,
  not ground truth.
- **Overlap with ENA.** Same samples often appear in both NCBI Pathogen
  Detection and Pathogens Portal via the INSDC exchange. Avoid
  double-counting by deduplicating on `biosample_acc`.
- **FTP retrieval is large.** Full snapshots can be multi-gigabyte.
  Download only the pathogen directory you need.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`enterobase`** | cgMLST/HierCC typing — cross-validate PDS clusters |
| **`pathogens-portal`** | European counterpart (ENA-backed) |
| **`spaam-ancient-metagenome-dir`** | Ancient samples — complementary historical layer |
| **`bacdive`** | Phenotypic metadata for strains typed here |
| **TBannotator MCP** | MTBC lineage typing, complementary to NCBI's per-isolate calls |
| **AMRFinderPlus** | NCBI's AMR reference pipeline (upstream of the AMR calls in this portal) |
| **NCBI Datasets API** | Alternative programmatic access path |
| **Genome Workbench** | NCBI tool for opening `.asn` cluster trees |

## Citation

```bibtex
@misc{ncbi_pathogen_detection,
  title        = {NCBI Pathogen Detection (Beta)},
  author       = {{National Center for Biotechnology Information}},
  year         = {2016--present},
  publisher    = {NIH / NCBI},
  address      = {Bethesda, MD},
  url          = {https://www.ncbi.nlm.nih.gov/pathogens/},
  note         = {Pin the snapshot date in Methods. Cite the specific
                  PDG/PDS accessions used in your analysis.}
}

@article{feldgarden2019amrfinder,
  title   = {Validating the AMRFinder tool and resistance gene database
             by using antimicrobial resistance genotype-phenotype
             correlations in a collection of isolates},
  author  = {Feldgarden, Michael and Brover, Vyacheslav and
             Haft, Daniel H. and Prasad, Arjun B. and others},
  journal = {Antimicrobial Agents and Chemotherapy},
  volume  = {63},
  number  = {11},
  pages   = {e00483-19},
  year    = {2019},
  doi     = {10.1128/AAC.00483-19}
}
```
