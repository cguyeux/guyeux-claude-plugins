---
name: nextstrain
description: >-
  Academic research toolkit for peer-reviewed phylogeographic research. Nextstrain (Augur,
  Auspice, TreeTime, Nextclade) for phylogeographic analysis and interactive visualisation
  of published pathogen genome collections. Augur is the Python toolkit that chains
  filtering, alignment, tree building, time scaling, ancestral reconstruction and discrete
  trait (geography) inference into a reproducible pipeline, producing JSON for the Auspice
  viewer. Use when building a reproducible phylogeographic pipeline over a research dataset,
  time-scaling a tree with TreeTime, inferring ancestral geography, or producing an
  interactive tree to accompany a scientific publication.
---

# Nextstrain : Real-Time Phylogeography & Interactive Visualization

## Overview

**Nextstrain** is an open-source platform for real-time tracking of
pathogen evolution, developed since 2017 by the groups of **Richard
Neher** (Biozentrum, Basel) and **Trevor Bedford** (Fred Hutch, Seattle)
with a large distributed team (Hadfield, Huddleston, Hodcroft, Lee,
Lin, McCrone, Roemer, Aksamentov, and many contributors). It is the
de-facto standard for phylogeographic surveillance of viral pathogens
(Ebola, Zika, SARS-CoV-2) and has strong community builds for
bacterial pathogens including **MTBC**.

### The four-piece stack

| Piece | Role | Language | URL |
|---|---|---|---|
| **Augur** | Bioinformatics pipeline (filter → align → tree → date → annotate → export) | Python | `https://github.com/nextstrain/augur` |
| **Auspice** | Interactive web visualization (zoomable trees + map + timeslider) | JavaScript | `https://github.com/nextstrain/auspice` |
| **Nextclade** | Clade assignment + QC for new sequences | Rust + JavaScript | `https://github.com/nextstrain/nextclade` |
| **Nextstrain CLI** | Orchestration wrapper, Docker/Conda/Singularity runner | Python | `https://github.com/nextstrain/cli` |

### Key references

- Hadfield J., Megill C., Bell S.M., Huddleston J., Potter B., Callender C.,
  Sagulenko P., Bedford T., Neher R.A. *Nextstrain: real-time tracking
  of pathogen evolution.* **Bioinformatics** 34(23): 4121–4123 (2018).
  DOI: `10.1093/bioinformatics/bty407`
- Huddleston J. et al. *Augur: a bioinformatics toolkit for phylogenetic
  analyses of human pathogens.* **Journal of Open Source Software**
  6(57): 2906 (2021). DOI: `10.21105/joss.02906`
- **Main site**: `https://nextstrain.org/` (live public builds)
- **Documentation**: `https://docs.nextstrain.org/`
- **License**: **AGPL-3.0** for the Augur and Auspice codebases

## Why it matters for MTBC × anthropology

Nextstrain is the **analysis and visualization layer** that sits on top
of the retrieval-oriented skills in your constellation (EnteroBase,
Pathogens Portal, NCBI Pathogen Detection, SPAAM, TBannotator). For your
seminar it offers three concrete deliverables:

1. **Publication-grade time-scaled phylogeography.** Given a set of
   MTBC genomes (modern from TBannotator, ancient from SPAAM), Augur
   reconstructs a dated tree with geographic ancestral states in one
   pipeline, exactly the figure that convinces an MNHN /
   eco-anthropology jury that your claims about lineage dispersal are
   empirically grounded.
2. **Interactive Auspice views for slides.** Auspice produces
   zoomable, time-sliding, filter-on-click views that are directly
   embeddable in a browser. A Neher/Bedford-style interactive tree on
   a seminar slide is **immediately recognisable as state-of-the-art**
   to anyone who has followed public-health genomics since COVID-19.
3. **Reproducible Snakemake builds.** The whole pipeline is a
   single-command `nextstrain build`, with inputs as a FASTA + TSV
   pair and all parameters in a Snakefile. This is the reproducibility
   standard the TB community is moving toward.

## Augur pipeline : the canonical subcommand chain

The typical Augur workflow chains small commands, each doing one thing:

```
sequences.fasta + metadata.tsv
        │
        ▼
augur filter          ── restrict by country, date, quality, subsample
        │
        ▼
augur align           ── MAFFT alignment to reference
        │
        ▼
augur tree            ── IQ-TREE / RAxML / FastTree
        │
        ▼
augur refine          ── time-scaled tree via TreeTime, branch length smoothing
        │
        ▼
augur ancestral       ── reconstruct ancestral nucleotide states
        │
        ▼
augur translate       ── codon-level amino acid changes
        │
        ▼
augur traits          ── discrete trait inference (geography, host, lineage)
        │
        ▼
augur export v2       ── bundle everything into Auspice JSON
        │
        ▼
Auspice  ◄──  auspice/mtbc.json
```

### Inputs

- **`sequences.fasta`**, genome FASTA, one record per isolate. Headers
  must match `strain` values in the metadata.
- **`metadata.tsv`** : TSV with at minimum `strain`, `date`, `country`,
  and any additional fields you want as colouring dimensions (lineage,
  lineage_code, host, source, …).
- **`reference.gb`** or **`.fasta`**, reference genome for alignment.
- **Optional**: `exclude.txt` (strains to drop), `include.txt` (strains
  to force in), `colors.tsv` (colour scheme), `lat_longs.tsv` (for
  geographic projection).

### Outputs

- **`tree.nwk`** : Newick tree (midpoint)
- **`branch_lengths.json`**, **`nt_muts.json`**, **`aa_muts.json`**,
  **`traits.json`**, per-step annotation layers
- **`auspice/<name>.json`**, the **final Auspice bundle**, the single
  file Auspice loads for visualization

## Installation

```bash
# Option A — Conda (recommended; pulls all dependencies including IQ-TREE, MAFFT)
conda create -n nextstrain -c bioconda -c conda-forge nextstrain-cli nextstrain-augur nextstrain-auspice
conda activate nextstrain
nextstrain check-setup

# Option B — Pip (lighter; you'll need to install IQ-TREE / MAFFT / TreeTime separately)
pip install nextstrain-augur

# Option C — Docker / Singularity (most reproducible)
nextstrain setup --set-default-method docker
```

Verify:

```bash
augur --version
augur --help
```

## Minimal MTBC build : walkthrough

### Directory layout

```
mtbc-build/
├── config/
│   ├── reference.gb              # H37Rv (NC_000962.3)
│   ├── colors.tsv
│   └── lat_longs.tsv
├── data/
│   ├── sequences.fasta           # your MTBC isolates
│   └── metadata.tsv              # strain, date, country, lineage, ...
├── Snakefile
└── auspice/                      # output
```

### `metadata.tsv` schema (required fields bold)

| Column | Example |
|---|---|
| **`strain`** | `SRR12345678` |
| **`date`** | `2018-04-15` (YYYY-MM-DD or YYYY) |
| **`country`** | `Ghana` |
| `region` | `West Africa` |
| `lineage` | `L4.15` |
| `sublineage` | `L4.15.A` |
| `host` | `Homo sapiens` |
| `source_database` | `tbannotator` |
| `age_bp` | (for ancient samples) |
| `material` | (for ancient samples) |

### Minimal Snakefile

```python
rule all:
    input: "auspice/mtbc.json"

rule filter:
    input:
        seq = "data/sequences.fasta",
        meta = "data/metadata.tsv",
    output: "results/filtered.fasta"
    shell: """
        augur filter \
            --sequences {input.seq} \
            --metadata {input.meta} \
            --output {output} \
            --min-length 4000000 \
            --group-by country year \
            --subsample-max-sequences 2000
    """

rule align:
    input:
        seq = "results/filtered.fasta",
        ref = "config/reference.gb",
    output: "results/aligned.fasta"
    shell: """
        augur align \
            --sequences {input.seq} \
            --reference-sequence {input.ref} \
            --output {output} \
            --nthreads 8
    """

rule tree:
    input: "results/aligned.fasta"
    output: "results/tree_raw.nwk"
    shell: """
        augur tree --alignment {input} --output {output} --nthreads 8
    """

rule refine:
    input:
        tree = "results/tree_raw.nwk",
        aln = "results/aligned.fasta",
        meta = "data/metadata.tsv",
    output:
        tree = "results/tree.nwk",
        node_data = "results/branch_lengths.json",
    shell: """
        augur refine \
            --tree {input.tree} \
            --alignment {input.aln} \
            --metadata {input.meta} \
            --output-tree {output.tree} \
            --output-node-data {output.node_data} \
            --timetree \
            --coalescent opt \
            --clock-rate 5e-8 \
            --clock-std-dev 1e-8 \
            --date-confidence
    """

rule traits:
    input:
        tree = "results/tree.nwk",
        meta = "data/metadata.tsv",
    output: "results/traits.json"
    shell: """
        augur traits \
            --tree {input.tree} \
            --metadata {input.meta} \
            --output-node-data {output} \
            --columns country region \
            --confidence
    """

rule export:
    input:
        tree = "results/tree.nwk",
        meta = "data/metadata.tsv",
        bl = "results/branch_lengths.json",
        traits = "results/traits.json",
    output: "auspice/mtbc.json"
    shell: """
        augur export v2 \
            --tree {input.tree} \
            --metadata {input.meta} \
            --node-data {input.bl} {input.traits} \
            --output {output} \
            --color-by-metadata country lineage \
            --geo-resolutions country \
            --title "MTBC phylogeography"
    """
```

Run:

```bash
nextstrain build --cpus 8 mtbc-build
nextstrain view mtbc-build/auspice   # opens Auspice locally on :4000
```

### Molecular clock rate for MTBC

Standard values to plug into `augur refine --clock-rate`:

| Lineage class | Rate (subs/site/year) | Source |
|---|---|---|
| Global MTBC | ~5e-8 | Menardo et al. 2019 |
| L4 sublineages | ~4.6e-8 | Various |
| L2 Beijing | ~6.7e-8 | Merker et al. 2015 |

Always cite the clock rate source explicitly in Methods.

## Workflows

### Workflow 1 : Time-scaled phylogeography of an MTBC sublineage

Goal: produce an Auspice figure of the geographic dispersal of a lineage
over time.

1. Extract the sublineage from TBannotator (strain list + metadata).
2. Fetch FASTAs from ENA via `pathogens-portal` (Workflow 1).
3. Run the Snakefile above.
4. Open `auspice/mtbc.json` in Auspice. Use the **time slider** to
   animate the dispersal; use the **map view** to show concrete
   geographic spread.
5. Screenshot the time slider at key moments for slides; embed the
   live JSON in a web page for interactive review by collaborators.

### Workflow 2 : Ancient + modern combined tree

Goal: place ancient MTBC genomes from SPAAM (Bos2014, Kay2015, Sabin2020,
Vagene2022, Jager2022) onto a tree with modern references as tips with
explicit tip dates.

1. Prepare a metadata TSV with `date = year_CE` for moderns and
   `date = "1950 - sample_age_BP"` for ancients (negative years allowed).
2. Include all 16 ancient genomes in the FASTA.
3. In `augur refine`, use `--date-confidence` and allow a prior on tip
   dates via `--keep-polytomies` and the clock model.
4. Export. The resulting tree will show the ancient tips in their
   correct temporal position, letting you test tip-dating consistency
   against the molecular clock.

> [!WARNING]
> Tip-dating with small numbers of ancient tips (16 in our case) is
> **underpowered**. Report a tempest/regression test (`TreeTime
> clock` subcommand) and show the temporal signal before committing
> to strong TMRCA claims.

### Workflow 3 : Discrete trait transmission matrix

Goal: reconstruct most-likely historical transmission events between
countries for an MTBC sublineage.

```bash
augur traits \
  --tree results/tree.nwk \
  --metadata data/metadata.tsv \
  --columns country \
  --output-node-data results/country_traits.json \
  --confidence \
  --sampling-bias-correction 2.5
```

The output JSON contains posterior-probability-weighted ancestral
country assignments at each internal node. Summarise into a
transmission matrix: for each branch where the parent and child have
different country assignments, increment a count, that is your
directed migration count.

### Workflow 4 : Subsampling to avoid pseudo-replication

When you have 10 000 modern isolates concentrated in 3 countries and 20
isolates from the rest of the world, a naïve build will be dominated by
the oversampled countries.

```bash
augur filter \
  --sequences sequences.fasta \
  --metadata metadata.tsv \
  --output subsampled.fasta \
  --group-by country year \
  --sequences-per-group 50 \
  --min-length 4000000 \
  --exclude-where "country=?"
```

`--group-by country year` + `--sequences-per-group 50` enforces a
balanced representation, essential for any phylogeographic claim.

### Workflow 5 : Publish the Auspice JSON

Once you have `auspice/mtbc.json`, there are several ways to share it:

- **Locally**: `nextstrain view auspice/` → browser at
  `http://localhost:4000`.
- **Community build**: push the JSON to a GitHub repo structured as
  `auspice/<build>.json`, it becomes accessible at
  `nextstrain.org/community/<github_user>/<repo>/<build>`.
- **Nextstrain Groups**: for institutional / lab hosting.
- **Download and archive**: the JSON is the reproducible artefact; pin
  the Augur + Auspice versions in your Methods.

## Caveats

- **Scale limits.** Augur scales comfortably to ~10,000–50,000 genomes
  with a 2–8h runtime on a workstation. For 300,000+ MTBC genomes
  (your corpus), you must **subsample** per country/year, or use a
  cgMLST-based representation instead (see EnteroBase).
- **MTBC clock rate is debated.** Different studies yield different
  rates (~3e-8 to 7e-8 sub/site/year). Always cite the one you use and
  run a tempest test.
- **Discrete trait inference is model-bound.** The model assumes
  stationary Markov transitions between states (countries), this is
  a simplification. Use `--sampling-bias-correction` and report its
  value.
- **Ancient tips are rare and noisy.** Only 16 ancient MTBC genomes
  exist in SPAAM (see `spaam-ancient-metagenome-dir`); tip-dating with
  this sample size is underpowered for strong claims.
- **Auspice displays Mercator-projected maps by default.** For
  publication-grade maps with accurate areas and distances, export the
  tree and render separately with GeoPandas or cartopy.
- **AGPL-3.0 copyleft.** If you build a web service on top of Augur /
  Auspice that exposes users to the software, you must publish your
  modifications. For internal research use this is a non-issue.
- **Not a primary data repository.** Nextstrain is an **analysis and
  visualization layer**, the sequences and metadata always come from
  upstream skills (ENA, SRA, TBannotator, SPAAM, EnteroBase).

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **TBannotator MCP** | Source of modern MTBC sequences + lineage metadata |
| **`pathogens-portal`** | Retrieve FASTAs from ENA for inclusion in a build |
| **`ncbi-pathogen-detection`** | Retrieve FASTAs from SRA |
| **`enterobase`** | cgMLST-based complement at larger scale (>50k genomes) |
| **`spaam-ancient-metagenome-dir`** | Ancient MTBC tips for tip-dating |
| **`bacdive`** | Phenotypic reference for lineage representatives |
| **`p3k14c`**, **`neolithic-14c`**, **`card`** | Chronological anchors for ancient tip dates |
| **`pleiades`**, **`orbis`**, **`owtrad`** | Historical geographic context for Auspice map overlays |
| **TreeTime** | Standalone TreeTime is also available (same authors) : Augur wraps it |
| **IQ-TREE / RAxML / FastTree** | Tree-building backends for `augur tree` |
| **MAFFT** | Alignment backend for `augur align` |
| **Snakemake** | Workflow orchestration, all Nextstrain builds are Snakemake projects |

## Citation

```bibtex
@article{hadfield2018nextstrain,
  title   = {Nextstrain: real-time tracking of pathogen evolution},
  author  = {Hadfield, James and Megill, Colin and Bell, Sidney M. and
             Huddleston, John and Potter, Barney and Callender, Charlton and
             Sagulenko, Pavel and Bedford, Trevor and Neher, Richard A.},
  journal = {Bioinformatics},
  volume  = {34},
  number  = {23},
  pages   = {4121--4123},
  year    = {2018},
  doi     = {10.1093/bioinformatics/bty407}
}

@article{huddleston2021augur,
  title   = {Augur: a bioinformatics toolkit for phylogenetic analyses
             of human pathogens},
  author  = {Huddleston, John and Hadfield, James and Sibley, Thomas R. and
             Lee, Jover and Fay, Kairsten and Ilcisin, Misja and
             Harkins, Elias and Bedford, Trevor and Neher, Richard A. and
             Hodcroft, Emma B.},
  journal = {Journal of Open Source Software},
  volume  = {6},
  number  = {57},
  pages   = {2906},
  year    = {2021},
  doi     = {10.21105/joss.02906}
}

@article{sagulenko2018treetime,
  title   = {TreeTime: Maximum-likelihood phylodynamic analysis},
  author  = {Sagulenko, Pavel and Puller, Vadim and Neher, Richard A.},
  journal = {Virus Evolution},
  volume  = {4},
  number  = {1},
  pages   = {vex042},
  year    = {2018},
  doi     = {10.1093/ve/vex042}
}
```
