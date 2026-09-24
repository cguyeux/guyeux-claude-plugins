---

name: modern-human-reference-panels
description: >-
  Open modern human reference panels: 1000 Genomes (1kGP, 2,504 / 26),
  Simons Genome Diversity Project (SGDP, 300 / 142), Human Genome Diversity
  Project (HGDP, 929 / 54), gnomAD. Canonical comparators for ADMIXTOOLS / qpAdm
  / f-statistics on AADR ancient genomes, and reference populations for
  H. pylori-style host phylogeography. Use when: an ADMIXTOOLS run, a PCA
  background for ancient samples, allele frequency lookups.
---

# Modern Human Reference Panels,1kGP, SGDP, HGDP, gnomAD

## Client (resilient, tool-first)

A stdlib-only client ships with this skill (`src/mhrp_client/`, nothing to
pip-install). Filter the harmonised HGDP+1kGP sample metadata without hand-rolling
pandas:

```bash
SRC=<this skill>/src
export MHRP_FILE=/path/to/hgdp_tgp_meta.tsv
PYTHONPATH="$SRC" python3 -m mhrp_client samples --project HGDP --region AFRICA --tsv
PYTHONPATH="$SRC" python3 -m mhrp_client.smoke_test   # offline, bundled fixture
```

`samples(population=..., region=..., project=..., bbox=(S,W,N,E))` returns
`list[dict]` with stable keys `sample, project, population, region, lat, lon, sex`.
Handy to pick representatives per population for a `d-place` join. This client handles
the sample-level METADATA, not the genotype VCFs (those live in gnomAD / 1kGP).
`inspect` prints the real header; reads .tsv/.csv/.xlsx.

## Compute a real inter-population FST matrix (1kGP genotypes, streamed)

The client above handles *metadata*. To get an actual **host genetic distance matrix** (FST)
from the public genotypes, without downloading whole VCFs, use `scripts/compute_fst_1kgp.py`.
It streams a genomic region from the public 1kGP phase-3 VCF via `bcftools` (remote, index-based),
subsets the requested populations, and computes pairwise Weir–Cockerham FST via `vcftools`. Output
is a CSV FST matrix, ready to feed the `coevolution` skill (Mantel / partial Mantel) as the HOST
side of a gene-for-gene co-divergence test (host-FST × pathogen-distance | geography).

```bash
SK=<this skill>/scripts
python3 $SK/compute_fst_1kgp.py --pops GWD,MSL,YRI,ESN \
    --labels GWD=Gambia,MSL=Sierra_Leone,YRI=Nigeria,ESN=Nigeria \
    --regions 22:20000000-32000000,21:20000000-30000000 --out host_fst.csv
```

Needs `bcftools`, `vcftools`, `tabix` (bioconda). 1kGP African pops: GWD (Gambia/Mandinka),
MSL (Sierra Leone/Mende), YRI (Nigeria/Yoruba), ESN (Nigeria/Esan), LWK (Kenya/Luhya), ACB, ASW.
Validated 2026-07-06: chr22:20-32Mb, 337 750 SNPs → GWD–MSL 0.0041, GWD–YRI 0.0081, YRI–ESN 0.0011
(west West-Africa vs Nigeria structure, mirroring the L6-west/L5-east M. africanum dichotomy).

**Extending beyond 1kGP** (Senegal-Mandenka, Central-African Bantu, …): HGDP and SGDP are equally
public (high-coverage VCFs on EBI/Sanger) and use the same `bcftools`+`vcftools` recipe, but
NEVER mix FST from different panels in one matrix (different SNP ascertainment → non-comparable
values). Keep a single coherent panel per matrix. No collaborator or private data required.

## Compute a UNIPARENTAL FST matrix (chrY + mtDNA, streamed) : the "meso" social-structure view

`compute_fst_1kgp.py` only does **autosomal** FST (vcftools Weir–Cockerham, which assumes
**diploid** genotypes). The Y chromosome and mtDNA are **haploid** (single-allele GT), and they
carry the **social-structure** signal (patrilocality via chrY, matrilocality via mtDNA) that the
genome-wide autosomal FST **averages out and misses**, this is the Verdu/Heyer (MNHN) approach.
Use `scripts/compute_uniparental_fst_1kgp.py`, which streams the public chrY/chrMT VCFs and computes
a **Hudson FST from allele frequencies** (the correct estimator for haploid markers).

```bash
SK=<this skill>/scripts
python3 $SK/compute_uniparental_fst_1kgp.py --pops GWD,MSL,YRI,ESN \
    --labels GWD=Gambia,MSL=Sierra_Leone,YRI=Nigeria,ESN=Nigeria2 \
    --marker both --out uniparental_fst.csv        # writes long CSV + <out>.Y.matrix.csv / .MT.matrix.csv
```

Needs `bcftools`, `tabix`. Validated 2026-07-06 on 4 West-African pops (60 315 chrY SNPs, 3 587 mtDNA
SNPs): **chrY FST 0.05–0.15 (10–20× the autosomal ~0.005), mtDNA ~0.01**. Two lessons: (1) the fine
ethnolinguistic structure IS in the human genome, but mainly in the Y (small Ne, non-recombining), an
autosomal-only test **misses** it; (2) the **sex-bias Y≫mtDNA is a direct patrilocality signature**
(men sedentary → structured Y; women exogamous → homogenised mtDNA). Resolution hierarchy for a
host–pathogen co-divergence: **macro (autosomal ancestry) < meso (uniparental social structure) <
micro (fast-clock pathogen)**. Do NOT conclude "no ethnolinguistic signal in the human genome" from a
low autosomal FST alone, recompute the uniparental FST first.

## Overview

Ancient human DNA analyses routinely require **modern reference
panels** as comparators, for PCA, ADMIXTURE, qpAdm, f-statistics,
and many other downstream analyses. The constellation has
**`aadr`** for the ancient side but had no dedicated skill for the
modern side. This skill closes that gap.

Four major open panels are in active use:

| Panel | N individuals | N populations | Coverage | Key reference |
|---|---|---|---|---|
| **1000 Genomes Project (1kGP)** | 2,504 (2015) / ~3,202 (expanded) | 26 populations, 5 super-populations | Low-coverage (~4×) + high-coverage re-sequencing | 1000 Genomes Project Consortium 2015 *Nature* |
| **Simons Genome Diversity Project (SGDP)** | 300 | 142 populations | **High coverage (~40×)** | Mallick et al. 2016 *Nature* |
| **Human Genome Diversity Project (HGDP)** | 929 (828 unrelated) | 54 populations | Now high-coverage (Bergström 2020) | Bergström et al. 2020 *Science*; earlier Cann et al. 2002 |
| **gnomAD** | 807,162 exomes + 76,156 genomes (v4) | Aggregated by continental group | Variable | Karczewski et al. 2020 *Nature*; Chen et al. 2024 *Nature* |

- **License**: all public-domain or open (CC-BY / NIH data use)
- **Combined dataset**: **HGDP + 1kGP** harmonised by Koenig et al.
  2024 *Cell Genomics*,4,094 whole genomes, >153M high-quality
  SNVs/indels/SVs

> [!NOTE]
> These panels are **sequence-level** resources. For ADMIXTOOLS
> analyses specifically, the AADR distribution **already includes**
> 1kGP and HGDP individuals at the standard 1240K SNP panel, so
> you usually don't need to download the raw VCFs yourself. See
> `aadr` skill Workflow 4.

## Why it matters for MTBC × anthropology

The use cases are indirect but essential:

1. **ADMIXTOOLS / qpAdm with AADR.** Any ancestry inference
   (e.g. "how much steppe ancestry does this Bronze Age Hungarian
   individual carry?") requires modern outgroups (Mbuti, Han, Papuan
   are the standard f-statistic outgroups, all from 1kGP or SGDP).
2. **Host side of host–pathogen phylogeography.** For an MTBC
   phylogeography claim ("lineage X follows population Y's
   dispersal"), you need a quantitative description of population Y
, which is what these panels provide.
3. **Anchor for Paul Verdu's methodology.** Verdu's work on
   admixture and linguistic-genetic co-variation relies heavily on
   HGDP, SGDP, and 1kGP as the canonical modern sample. Mentioning
   these in your methods signals methodological alignment.
4. **Helicobacter paradigm cross-reference.** The Linz 2007
   *H. pylori* populations (hpAfrica1, hpEurope, hpEastAsia, etc.)
   are indexed against modern human sampling locations, which
   correspond to specific 1kGP/SGDP populations. See the
   `helicobacter-pylori-phylogeography` skill.

## 1. 1000 Genomes Project (1kGP)

- **Phase 3 reference**: The 1000 Genomes Project Consortium. *A
  global reference for human genetic variation.* **Nature** 526:
  68–74 (2015). DOI: `10.1038/nature15393`
- **High-coverage re-sequencing**: Byrska-Bishop et al. *High-coverage
  whole-genome sequencing of the expanded 1000 Genomes Project
  cohort including 602 trios.* **Cell** 185(18): 3426–3440.e19 (2022).
  DOI: `10.1016/j.cell.2022.08.004`
- **Data portal**: `https://www.internationalgenome.org/data-portal/`
- **N individuals**: 2,504 (Phase 3, 2015) expanded to ~3,202 in the
  2022 high-coverage re-release
- **Populations**: 26 sampled populations grouped into 5 super-populations
  (AFR, AMR, EAS, EUR, SAS)

### The 26 populations

| Super-pop | Code | Population |
|---|---|---|
| AFR | ACB | African Caribbean (Barbados) |
| AFR | ASW | African ancestry (Southwest US) |
| AFR | ESN | Esan (Nigeria) |
| AFR | GWD | Gambian |
| AFR | LWK | Luhya (Kenya) |
| AFR | MSL | Mende (Sierra Leone) |
| AFR | YRI | Yoruba (Nigeria) |
| AMR | CLM | Colombian (Medellín) |
| AMR | MXL | Mexican Ancestry (Los Angeles) |
| AMR | PEL | Peruvian (Lima) |
| AMR | PUR | Puerto Rican |
| EAS | CDX | Dai Chinese |
| EAS | CHB | Han Chinese (Beijing) |
| EAS | CHS | Southern Han |
| EAS | JPT | Japanese |
| EAS | KHV | Kinh Vietnamese |
| EUR | CEU | Utah (N/W European) |
| EUR | FIN | Finnish |
| EUR | GBR | British |
| EUR | IBS | Iberian (Spain) |
| EUR | TSI | Tuscan (Italy) |
| SAS | BEB | Bengali |
| SAS | GIH | Gujarati Indian (Houston) |
| SAS | ITU | Indian Telugu (UK) |
| SAS | PJL | Punjabi (Lahore) |
| SAS | STU | Sri Lankan Tamil (UK) |

## 2. Simons Genome Diversity Project (SGDP)

- **Reference**: Mallick S., Li H., Lipson M. et al. *The Simons
  Genome Diversity Project: 300 genomes from 142 diverse populations.*
  **Nature** 538(7624): 201–206 (2016). DOI: `10.1038/nature18964`
- **Data portal (Reich Lab)**: `https://reichdata.hms.harvard.edu/pub/datasets/sgdp/`
- **N individuals**: 300 (all to high coverage ~40×)
- **Populations**: 142 diverse populations, explicitly chosen to
  cover the widest possible geographic and linguistic diversity,
  emphasising under-represented groups (San, Mbuti, Papua New
  Guinea highlanders, Australian Aborigines, Amazonian peoples,
  etc.)

SGDP is the **deep-coverage** complement to 1kGP/HGDP when you need
high-quality variant calls for small, under-represented populations.

## 3. Human Genome Diversity Project (HGDP)

- **Original**: Cann H.M. et al. 2002 *Science* 296: 261, *A human
  genome diversity cell line panel*
- **Whole-genome sequenced**: Bergström A., McCarthy S.A., Hui R.
  et al. *Insights into human genetic variation and population
  history from 929 diverse genomes.* **Science** 367(6484): eaay5012
  (2020). DOI: `10.1126/science.aay5012`
- **Data**: 929 individuals (828 unrelated) from 54 populations,
  curated by the CEPH (Centre d'Étude du Polymorphisme Humain) in
  Paris in the 1990s, sequenced to high coverage by Wellcome Sanger
  starting 2015
- **Access**: via EBI ENA, NCBI SRA, and the gnomAD HGDP+1kGP
  harmonised release

The **54 HGDP populations** cover 7 geographic regions: Africa,
Middle East, Europe, Central/South Asia, East Asia, Oceania,
Americas. Classic populations include Mbuti, San, Yoruba, Bedouin,
Druze, Palestinian, Uyghur, Han, Papuan, Karitiana, Pima, Maya.

**This is the panel most routinely used for ADMIXTOOLS analyses in
the Reich Lab tradition.**

## 4. gnomAD : Genome Aggregation Database

- **Reference (v2)**: Karczewski K.J. et al. *The mutational
  constraint spectrum quantified from variation in 141,456 humans.*
  **Nature** 581: 434–443 (2020). DOI: `10.1038/s41586-020-2308-7`
- **v4 reference**: Chen S. et al. *A genomic mutational constraint
  map using variation in 76,156 human genomes.* **Nature** 625:
  92–100 (2024). DOI: `10.1038/s41586-023-06045-0`
- **Portal**: `https://gnomad.broadinstitute.org/`
- **Content (v4)**: 807,162 exomes + 76,156 genomes aggregated from
  large exome/genome sequencing projects
- **Use case**: variant frequency lookups, constraint scores,
  population-specific allele frequencies, **not** a panel of
  individual genomes (privacy-preserving aggregation)

gnomAD is the right tool for **"what is the frequency of SNP X in
human populations?"** but not for ADMIXTOOLS, it does not provide
per-individual genotypes.

## 5. HGDP + 1kGP harmonised dataset

- **Reference**: Koenig D., Atkinson E.G., Martin A.R. *Structural
  variation and haplotype patterns in a harmonized resource of 4,094
  whole genomes from HGDP and 1kGP.* **Cell Genomics** (2024), or
  the gnomAD v3.1 secondary analysis release
- **Access**: `gs://gcp-public-data--gnomad/release/3.1/secondary_analyses/hgdp_1kg_v2/`
- **N**: 4,094 harmonised whole genomes
- **Content**: >153M high-quality SNVs, indels, and SVs; consistent
  variant calling across both panels

This is the **recommended combined panel** for modern analyses that
want both the breadth of 1kGP and the population coverage of HGDP.

## Data access

### Option A : Via AADR (easiest for ADMIXTOOLS users)

The AADR distribution already ships 1kGP, HGDP, and SGDP individuals
at the 1240K SNP panel, merged with the ancient samples. See the
`aadr` skill. **For ancient DNA work, this is almost always what you
want**, no need to download VCFs separately.

### Option B,1kGP FTP (IGSR)

```bash
# High-coverage Phase 3 re-release (2022)
mkdir -p ~/data/1kgp && cd ~/data/1kgp
curl -LO "https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage/data/index.html"

# Or a specific chromosome VCF
curl -LO "https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage/working/20201028_3202_phased/CCDG_14151_B01_GRM_WGS_2020-08-05_chr22.filtered.shapeit2-duohmm-phased.vcf.gz"
```

### Option C : SGDP (Reich Lab mirror)

```bash
# PLINK bed/bim/fam
curl -LO "https://reichdata.hms.harvard.edu/pub/datasets/sgdp/sgdp_v1.tar.gz"
tar xzf sgdp_v1.tar.gz
```

### Option D : HGDP + 1kGP harmonised on gnomAD

```bash
# Via Google Cloud Storage (gsutil required)
gsutil cp -r gs://gcp-public-data--gnomad/release/3.1/secondary_analyses/hgdp_1kg_v2/ ./hgdp_1kg/
```

### Option E : gnomAD for variant frequency

```bash
# Browser UI for exploration
open "https://gnomad.broadinstitute.org/variant/22-50788398-C-T?dataset=gnomad_r4"

# API (GraphQL)
curl -sX POST "https://gnomad.broadinstitute.org/api" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ variant(variantId: \"22-50788398-C-T\", dataset: gnomad_r4) { exome { af } genome { af } } }"}'
```

## Workflows

### Workflow 1 : ADMIXTOOLS / qpAdm setup with AADR + 1kGP + HGDP

Goal: infer the ancestry of an ancient Bronze Age individual using
modern outgroups and sources.

1. Use the AADR `.anno` file (see `aadr` skill), it already
   contains 1kGP and HGDP individuals at the 1240K panel.
2. Define outgroups: classical set is **Mbuti (HGDP), Papuan
   (HGDP), Han (1kGP CHB), Sardinian (HGDP)**.
3. Define sources: e.g. **Anatolia_Neolithic + Yamnaya + WHG** for
   a European Bronze Age target.
4. Run `admixtools::qpadm()` (R) or the original `qpAdm` from
   ADMIXTOOLS.
5. Report the feasible source combinations with their p-values.

### Workflow 2 : Anchor H. pylori populations to modern human samples

Goal: for each of the 7 *H. pylori* populations (see
`helicobacter-pylori-phylogeography`), identify the corresponding
human populations in 1kGP/HGDP/SGDP and compare genetic distances
with the pathogen distances.

1. From 1kGP: use the super-population level (AFR, EUR, EAS, SAS,
   AMR) as coarse match.
2. From HGDP: use the fine-grained populations (e.g. Yoruba ↔
   hpAfrica1-WA).
3. Compute pairwise Fst between modern human populations (from
   1kGP/HGDP) and between *H. pylori* populations (from literature).
4. Mantel test on the two distance matrices.

### Workflow 3 : Variant frequency lookup via gnomAD

Goal: for a candidate host-resistance variant in a TB paper
(e.g. `SLC11A1` polymorphism), check its allele frequency across
human populations.

1. Identify the variant (rs ID or chromosomal position).
2. Look up in gnomAD browser or API.
3. Report the frequency per super-population (AFR, NFE, AMR, EAS,
   SAS, etc.).
4. Contextualise in the paper's host genetics discussion.

### Workflow 4 : Build a PCA background for ancient samples

Goal: project ancient AADR samples onto a modern PCA space.

1. Extract modern individuals from 1kGP + HGDP (or use the AADR
   pre-merged file).
2. Compute PCA on the moderns (e.g. with `smartpca` from EIGENSOFT
   or `plink --pca`).
3. Project the ancient individuals onto the same PCA axes (using
   `smartpca`'s `lsqproject: YES` option).
4. Plot, a classical ancient-DNA figure showing ancients relative
   to modern diversity.

### Workflow 5 : Export a balanced subsample for cross-cultural analysis

Goal: pick 1 representative individual per HGDP population for a
balanced cross-cultural study linked to `d-place` societies.

```python
import pandas as pd

# Load HGDP metadata from gnomAD harmonised release or 1kGP kgp package
hgdp = pd.read_csv("hgdp_tgp_meta.tsv", sep="\t")
# Filter to HGDP
hgdp_only = hgdp[hgdp.project == "HGDP"]
# One individual per population
representatives = hgdp_only.drop_duplicates(subset="population")
print(len(representatives), "representative individuals")
```

Then link each representative to the corresponding D-PLACE society
via Glottocode or country.

## Caveats

- **These are modern panels.** For anything ancient, combine with
  `aadr` / `amtdb`, modern panels alone cannot answer ancient-DNA
  questions.
- **Population labels are coarse.** "Yoruba (Nigeria)" in 1kGP is
  sampled from a specific urban population and is not representative
  of all Yoruba speakers, let alone of the broader West African
  genetic landscape.
- **Sampling bias is substantial.** Europeans are over-represented;
  Africans and Americans are under-represented, though HGDP and
  SGDP deliberately attempted to correct for this.
- **Ethical context.** HGDP samples were collected in the 1990s
  under ethical frameworks that have since been criticised. Use
  with care, respect Indigenous data sovereignty principles where
  applicable, and cite the original collection papers.
- **Kin structure.** 1kGP Phase 3 contained some related
  individuals; the 2022 re-release re-identified them. Always use
  the unrelated individuals flag when computing allele frequencies
  or PCA.
- **Reference genome versions differ.** 1kGP Phase 3 was on GRCh37;
  the 2022 re-release is on GRCh38. HGDP high-coverage is on GRCh38.
  Align consistently before combining datasets.
- **gnomAD is aggregated.** You cannot retrieve per-individual
  genotypes from gnomAD, only summary statistics. For
  per-individual work, use 1kGP / HGDP / SGDP raw data.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`aadr`** | Already ships pre-merged with 1kGP and HGDP at 1240K SNPs, use that first |
| **`amtdb`** | Maternal lineage ancient panel; modern mtDNA references often come from the same 1kGP/HGDP individuals |
| **`helicobacter-pylori-phylogeography`** | *H. pylori* populations are anchored to modern human samples that overlap with these panels |
| **`d-place`** | Cultural variables; link via Glottocode or country to modern human populations |
| **`glottolog`** | Language identifiers for the populations |
| **ADMIXTOOLS 2 / qpAdm / smartpca** | Canonical analysis tools for these panels |
| **PLINK / BCFtools** | File format manipulation |
| **`kgp`** (R package) | 1kGP metadata as R data (Stephen Turner) |
| **NCBI Taxonomy / ontologies** | Species-level reference (all panels are *Homo sapiens*, NCBITaxon:9606) |

## Citations

```bibtex
@article{1kgp2015,
  title   = {A global reference for human genetic variation},
  author  = {{The 1000 Genomes Project Consortium}},
  journal = {Nature},
  volume  = {526},
  pages   = {68--74},
  year    = {2015},
  doi     = {10.1038/nature15393}
}

@article{byrskabishop2022highcoverage1kgp,
  title   = {High-coverage whole-genome sequencing of the expanded 1000
             Genomes Project cohort including 602 trios},
  author  = {Byrska-Bishop, Marta and Evani, Uday S. and Zhao, Xuefang and
             Basile, Anna O. and Abel, Haley J. and Regier, Allison A. and
             Corvelo, Andr{\'e} and Clarke, Wayne E. and others},
  journal = {Cell},
  volume  = {185},
  number  = {18},
  pages   = {3426--3440.e19},
  year    = {2022},
  doi     = {10.1016/j.cell.2022.08.004}
}

@article{mallick2016sgdp,
  title   = {The Simons Genome Diversity Project: 300 genomes from 142
             diverse populations},
  author  = {Mallick, Swapan and Li, Heng and Lipson, Mark and Mathieson,
             Iain and Gymrek, Melissa and Racimo, Fernando and Zhao, Mengyao
             and Chennagiri, Niru and Nordenfelt, Susanne and Tandon, Arti
             and others},
  journal = {Nature},
  volume  = {538},
  number  = {7624},
  pages   = {201--206},
  year    = {2016},
  doi     = {10.1038/nature18964}
}

@article{bergstrom2020hgdp,
  title   = {Insights into human genetic variation and population history
             from 929 diverse genomes},
  author  = {Bergström, Anders and McCarthy, Shane A. and Hui, Ruoyun and
             Almarri, Mohamed A. and Ayub, Qasim and Danecek, Petr and Chen, Yuan
             and Felkel, Sabine and Hallast, Pille and Kamm, Jack and others},
  journal = {Science},
  volume  = {367},
  number  = {6484},
  pages   = {eaay5012},
  year    = {2020},
  doi     = {10.1126/science.aay5012}
}

@article{karczewski2020gnomad,
  title   = {The mutational constraint spectrum quantified from variation
             in 141,456 humans},
  author  = {Karczewski, Konrad J. and Francioli, Laurent C. and Tiao, Grace
             and Cummings, Beryl B. and Alföldi, Jessica and Wang, Qingbo
             and Collins, Ryan L. and Laricchia, Kristen M. and others},
  journal = {Nature},
  volume  = {581},
  pages   = {434--443},
  year    = {2020},
  doi     = {10.1038/s41586-020-2308-7}
}
```
