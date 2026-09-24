---

name: spaam-community
description: >-
  Index of the SPAAM (Standards, Precautions and Advances in Ancient
  Metagenomics) community ecosystem, the umbrella organisation for
  ancient metagenomics. Covers tools, pipelines, training materials,
  metadata standards, lab directories, and reference guides beyond the
  AncientMetagenomeDir catalogue itself. Use this as a meta-index when
  you need to find a tool, pipeline, tutorial, or reference resource
  for working with ancient microbial DNA.

  Use when: choosing an ancient-metagenomics pipeline (eager vs aMeta),
  finding a tutorial on ancient DNA damage patterns, validating metadata
  against the MInAS standard, identifying labs working on a specific
  ancient pathogen, looking up the canonical Introduction to Ancient
  Metagenomics textbook, or onboarding to the SPAAM community
  infrastructure.
---

# SPAAM Community : Ancient Metagenomics Ecosystem Index

## Overview

**SPAAM** (*Standards, Precautions and Advances in Ancient Metagenomics*)
is the umbrella community for ancient metagenomics, founded by **James A.
Fellows Yates** and now coordinated by an international group of ancient
DNA scientists. It produces and maintains a coherent ecosystem of:

- a curated **catalogue** of all published ancient metagenomic samples
  (`AncientMetagenomeDir`, covered separately by the
  **`spaam-ancient-metagenome-dir`** skill)
- a Python **toolkit** for that catalogue (`AMDirT`)
- **metadata standards** (MInAS extension to MIxS)
- a **textbook** and **summer school** for ancient metagenomics
- a **directory of labs** active in the field
- **community fora** (blog, monthly *SPAAMtisch* on Matrix)
- a **damage-pattern interpretation reference** (*Little Book of Smiley Plots*)

This skill is a **meta-index** of those resources. For interrogating the
sample catalogue itself, use `spaam-ancient-metagenome-dir`.

- **Community URL**: `https://www.spaam-community.org/`
- **GitHub organisation**: `https://github.com/SPAAM-community`
- **Founder / Lead**: Dr James A. Fellows Yates (Max Planck / Leipzig /
  Jena, Christina Warinner group)
- **Communication**: monthly online *SPAAMtisch* via Matrix,
  `https://matrix.to/#/#spaamtisch:matrix.org`

> [!NOTE]
> SPAAM is a **community**, not a single dataset. It does not have a
> central API. Each resource below has its own URL, license, and
> versioning. Always pin specific versions/commits in your Methods.

## Why it matters for MTBC × anthropology

For your TB / ancient pathogen work, SPAAM is the **right entry point
for everything ancient-DNA-microbial**. Specific value:

1. **Pipeline selection.** Choosing between `nf-core/eager`, `nf-core/aMeta`,
   `HOPS`, `MALT`, etc. is non-obvious; the SPAAM textbook and
   community-maintained intro chapters are the standard reference for
   that decision.
2. **Damage authentication.** Authenticating an ancient TB or *Y. pestis*
   genome requires reading C→T deamination plots correctly, the
   *Little Book of Smiley Plots* is the **only** dedicated visual
   reference for this kind of inspection.
3. **Metadata standardisation.** When publishing or sharing an ancient
   pathogen genome, the **MInAS** checklist (MIxS extension for ancient
   sequences) is the emerging community standard. Following it makes
   your data findable and reusable by the rest of the community,
   especially via `AncientMetagenomeDir`.
4. **Lab discovery.** The Ancient Metagenomics Labs directory is a
   maintained list of who is doing what, useful when looking for
   collaborators on ancient TB or for identifying who else in the
   community has worked on a specific pathogen.

## Resource catalogue

### 1. AncientMetagenomeDir + AMDirT (covered separately)

| Resource | URL |
|---|---|
| AncientMetagenomeDir (data catalogue) | `https://github.com/SPAAM-community/AncientMetagenomeDir` |
| AMDirT (Python toolkit) | `https://github.com/SPAAM-community/AMDirT` |
| AMDirT web UI | `https://spaam-community.github.io/amdirt/` |
| AMDirT docs | `https://amdirt.readthedocs.io/en/latest/` |

→ **Use the `spaam-ancient-metagenome-dir` skill** for sample lookups
in the catalogue.

### 2. Introduction to Ancient Metagenomics : the canonical textbook

| Item | Detail |
|---|---|
| Title | *Introduction to Ancient Metagenomics* |
| Authors | James A. Fellows Yates, Christina Warinner & contributors |
| Published | September 2024 |
| URL | `https://www.spaam-community.org/intro-to-ancient-metagenomics-book/` |
| Source | `https://github.com/SPAAM-community/intro-to-ancient-metagenomics-book` |
| Structure | **5 theoretical chapters + 12 practical exercise modules** |

This is the **standard reference** for the field. Cite it in any Methods
section involving ancient DNA preprocessing or authentication, and link to
the relevant chapter URL when explaining a step.

Notable chapters of high TB-relevance:

| Chapter | URL fragment | Why it matters |
|---|---|---|
| Introduction to Ancient DNA | `introduction-to-ancient-dna.html` | Onboarding for collaborators |
| Accessing Ancient Metagenomic Data | `accessing-ancient-metagenomic-data.html` | How to use AncientMetagenomeDir + AMDirT |
| Ancient Metagenomic Pipelines | `ancient-metagenomic-pipelines.html` | nf-core/eager + nf-core/aMeta side-by-side |
| Taxonomic Profiling, OTU Tables and Visualisation | `taxonomic-profiling.html` | Detection of MTBC reads in shotgun data |

All chapter URLs follow the pattern
`https://www.spaam-community.org/intro-to-ancient-metagenomics-book/<fragment>`

### 3. SPAAM Summer Schools

| Item | Detail |
|---|---|
| Repository | `https://github.com/SPAAM-community/wss-summer-school` |
| Website | `https://spaam-community.github.io/wss-summer-school/` |
| Format | Yearly practical block course (~1 week) |
| Audience | Graduate students and early-career researchers |
| Founder | James A. Fellows Yates |

The materials (slides, scripts, exercises) are open and reusable. They
share substantial content with the textbook but are organised as live
training sessions.

### 4. MInAS : MIxS extension for ancient sequences

| Item | Detail |
|---|---|
| URL | `https://www.mixs-minas.org/` |
| Purpose | Metadata checklist for ancient nucleic-acid sequences |
| Parent standard | MIxS (Minimum Information about any (x) Sequence), GSC consortium |

When publishing an ancient TB genome or submitting it to ENA/SRA, MInAS
defines the **minimum metadata fields** required for downstream
discoverability and reuse. Following it ensures your sample can be
ingested into AncientMetagenomeDir without extra editorial work.

### 5. Ancient Metagenomics Labs directory

| Item | Detail |
|---|---|
| Repository | `https://github.com/SPAAM-community/ancient-metagenomics-labs` |
| Website | `https://spaam-community.github.io/ancient-metagenomics-labs/` |
| Content | Curated directory of labs with topical tags |

Browse to find researchers working on a specific ancient pathogen
(e.g. ancient TB, ancient *Y. pestis*, ancient leprosy, dental calculus,
coprolites…).

### 6. Little Book of Smiley Plots : damage pattern interpretation

| Item | Detail |
|---|---|
| URL | `https://spaam-community.org/little-book-of-smiley-plots/` |
| Purpose | Reference guide for interpreting C→T deamination plots from ancient DNA |
| Format | Web book with annotated example plots |

This is the practical complement to the theoretical chapters of the
intro textbook. When inspecting a putative ancient *M. tuberculosis*
read mapping with `damageprofiler` / `mapDamage`, this is the visual
reference for "is this real ancient DNA or modern contamination?"

### 7. SPAAM Blog

| Item | Detail |
|---|---|
| URL | `https://spaam-community.github.io/category/blog/` |
| Purpose | Community posts on ancient metagenomics topics |

Less authoritative than the textbook but useful for catching new
methodological developments and community announcements.

### 8. SPAAMtisch : community channel

| Item | Detail |
|---|---|
| Channel | `https://matrix.to/#/#spaamtisch:matrix.org` |
| Format | Monthly informal online discussion + persistent chat |

The fastest path to ask a methodological question or get an opinion
from the active ancient metagenomics community.

## Companion / related infrastructure (not strictly SPAAM but standard)

| Tool | Role | URL |
|---|---|---|
| **nf-core/eager** | Reference Nextflow pipeline for ancient DNA preprocessing & authentication (Fellows Yates et al. 2021 *PeerJ*) | `https://nf-co.re/eager` |
| **nf-core/aMeta** | Nextflow pipeline for ancient-microbiome taxonomic profiling | `https://nf-co.re/ameta` |
| **HOPS** | Ancient pathogen detection pipeline (Hübler et al. 2019) | `https://github.com/rhuebler/HOPS` |
| **MALT** | Megan ALignment Tool, ancient DNA-aware metagenomic aligner | `https://software-ab.cs.uni-tuebingen.de/download/malt/` |
| **damageprofiler** | C→T damage profile generator | `https://github.com/Integrative-Transcriptomics/DamageProfiler` |
| **mapDamage** | Classical damage profile generator (Jónsson et al.) | `https://ginolhac.github.io/mapDamage/` |

These are the **canonical tools** the SPAAM textbook teaches and
recommends.

## Workflows

### Workflow 1 : Choose a pipeline for ancient TB / pinnipedii reads

Goal: pick the right Nextflow pipeline for processing raw ancient reads
suspected of containing MTBC.

1. Read the *Ancient Metagenomic Pipelines* chapter of the SPAAM
   textbook (URL above).
2. Decide between **`nf-core/eager`** (full preprocessing including
   adapter removal, alignment, deamination calling, variant calling)
   and **`nf-core/aMeta`** (specifically tuned for taxonomic profiling
   and pathogen detection in mixed samples).
3. For a known MTBC reference and a candidate ancient sample, **eager
   is the right call**: it produces an authenticated BAM that you can
   feed to `bcftools` / `gatk` / `vcftools` for downstream analysis.
4. For "is there *Mycobacterium* in this sample at all?", **aMeta is
   the right call**: it does the screening before you commit to a
   reference-based pipeline.
5. Configure either via an `amdirt convert`–generated samplesheet (see
   `spaam-ancient-metagenome-dir` skill).

### Workflow 2 : Authenticate an ancient *M. tuberculosis* read mapping

Goal: confirm a putative ancient TB result is real ancient DNA, not
modern contamination.

1. Run `damageprofiler` on the BAM to generate the damage plot.
2. Open the *Little Book of Smiley Plots* and compare your plot to the
   reference shapes.
3. Look for: (i) the characteristic 5′ C→T and 3′ G→A asymmetry, (ii)
   short fragment length distribution, (iii) edit distance distribution
   consistent with the species.
4. Cross-check the mapping coverage profile (uneven, sparse, edge-of-
   genome falloff = ancient; uniform high coverage everywhere = likely
   modern contamination).
5. Report the inspection in the Methods, citing both the *Little Book*
   and the original `damageprofiler` paper.

### Workflow 3 : Submit metadata for a new ancient TB genome

Goal: prepare a submission that will be cleanly ingested by
AncientMetagenomeDir and ENA/SRA.

1. Read the **MInAS checklist** (mixs-minas.org).
2. Map your sample's metadata to the MInAS-extended fields:
   `sample_name`, `geographic location`, `latitude`/`longitude`,
   `collection_date`, `sample_age`, `sample_age_doi`, `material`,
   `host`, `singlegenome_species`, `archive_accession`.
3. Validate the resulting TSV with `amdirt validate --schema
   ancientsinglegenome-hostassociated`.
4. Submit the genome to ENA/SRA, then open a pull request to
   AncientMetagenomeDir adding the row.

### Workflow 4 : Find collaborators on a niche ancient pathogen

Goal: identify labs working on, e.g., ancient *Mycobacterium leprae*
or pre-Columbian *M. pinnipedii*.

1. Browse the **Ancient Metagenomics Labs** directory.
2. Filter by tags or keyword search.
3. Cross-reference lab pages with author lists from
   `spaam-ancient-metagenome-dir` queries on the relevant pathogen.
4. Reach out via the listed contact email or via the SPAAMtisch chat.

## Caveats

- **This skill is a meta-index, not a data source.** It does not contain
  ancient DNA sequences or metadata; for those, use the appropriate
  per-resource skill (`spaam-ancient-metagenome-dir`, `aadr`, `amtdb`).
- **Resources are independently versioned.** The textbook, AMDirT,
  AncientMetagenomeDir, and the labs directory each evolve on their own
  schedule. Always pin the version or access date you used.
- **License heterogeneity.** Each resource has its own licence (CC BY,
  CC BY-NC, MIT for code, etc.). Check before redistributing.
- **The community is academic.** Tools and resources reflect best
  current practice but are not industrially supported. For critical
  pipelines, mirror locally and pin the commit hash.
- **MInAS adoption is incomplete.** Many published ancient pathogen
  papers do not yet follow MInAS, be ready to harmonise heterogeneous
  metadata when working at the corpus level.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`spaam-ancient-metagenome-dir`** | Catalogue lookups (the *data* skill SPAAM produces) |
| **`aadr`** | Host nuclear genomes, pair with SPAAM-pipeline-processed pathogen genomes |
| **`amtdb`** | Host mitochondrial genomes, same skeletons in many cases |
| **`enterobase`** | Modern bacterial reference data for placing ancient genomes phylogenetically |
| **`p3k14c`** | Independent radiocarbon dates for site context |
| **`pleiades`** | Resolve ancient site names |
| **`d-place`**, **`seshat`** | Cultural / political context of the populations |
| **TBannotator MCP** | Modern TB lineage comparison for ancient placement |
| **nf-core/eager**, **nf-core/aMeta**, **HOPS**, **MALT** | The canonical pipelines the SPAAM textbook teaches |
| **damageprofiler / mapDamage** | C→T damage authentication |

## Citation

When you use any SPAAM resource, the right citation depends on the
resource. The most general references are:

```bibtex
@article{fellowsyates2021spaam,
  title   = {Community-curated and standardised metadata of published
             ancient metagenomic samples with AncientMetagenomeDir},
  author  = {Fellows Yates, James A. and Andrades Valtue{\~n}a, Aida and
             V{\aa}gene, {\AA}shild J. and others},
  journal = {Scientific Data},
  volume  = {8},
  pages   = {31},
  year    = {2021},
  doi     = {10.1038/s41597-021-00816-y}
}

@article{fellowsyates2021eager,
  title   = {Reproducible, portable, and efficient ancient genome
             reconstruction with nf-core/eager},
  author  = {Fellows Yates, James A. and Lamnidis, Thiseas C. and Borry,
             Maxime and Andrades Valtue{\~n}a, Aida and Fagern{\"a}s,
             Zandra and Clayton, Stephen and Garcia, Maxime U. and
             Neukamm, Judith and Peltzer, Alexander},
  journal = {PeerJ},
  volume  = {9},
  pages   = {e10947},
  year    = {2021},
  doi     = {10.7717/peerj.10947}
}

@book{fellowsyates2024intro,
  title     = {Introduction to Ancient Metagenomics},
  author    = {Fellows Yates, James A. and Warinner, Christina and others},
  year      = {2024},
  publisher = {SPAAM Community},
  url       = {https://www.spaam-community.org/intro-to-ancient-metagenomics-book/}
}
```

## Codex packaging note

This packaged copy targets Codex. MCP tool names in `allowed-tools` are prerequisites: verify them with `codex mcp list` in the active profile before relying on live queries.
