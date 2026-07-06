---
name: bovine-genomics
description: >-
  Index of public-access cattle genomic resources for population
  genetics and phylogeographic studies: the 1000 Bull Genomes Project
  (~2,700 WGS cattle, ~90M variants), the Bovine HapMap Consortium
  (37,470 SNPs, 19 breeds), and the Bovine Genome Variation Database
  (BGVD, ~60M SNPs, 432 samples). Covers breed structure, the taurine
  vs indicine split, and the Neolithic cattle domestication signal.

  Use when: building a cattle-side phylogeographic reference,
  retrieving bovine WGS or SNP data, comparing taurine and indicine
  breed distributions, or anchoring a study on the Neolithic cattle
  domestication event.
---

# Bovine Genomics — Cattle Genome Resources

## Overview

This skill indexes the three main public-access cattle genomics
resources for population-genetics and phylogeographic studies:

| Resource | Scale | Key metric |
|---|---|---|
| **1000 Bull Genomes** | ~2,700 WGS cattle | ~90 million genetic variants |
| **Bovine HapMap** | 497 cattle, 19 breeds | 37,470 SNPs, breed structure |
| **BGVD** | 432 global samples | ~60.44M SNPs, ~6.86M indels, 76,634 CNV regions |

The skill provides the **cattle-side** reference structure needed for
any comparative study that pairs cattle population genetics with an
external dataset (other bacterial taxa, archaeological records, ancient
DNA, climate). The Bovine HapMap finding that taurine breeds carry
less SNP diversity than indicine breeds is consistent with the Indian
subcontinent as a secondary major domestication centre.

For the specific application of pairing cattle phylogeography with an
animal-associated bacterial taxon studied elsewhere in this
constellation, see the companion notes file
`COMPARATIVE_NOTES.md` in this skill's directory.

---

## 1. The 1000 Bull Genomes Project

### Summary

An international consortium (founded 2012 by **Ben Hayes**, now led by
**Hans Daetwyler**, La Trobe University / Agriculture Victoria,
Melbourne) that has whole-genome sequenced ~2,700 dairy and beef cattle
from **40+ partner institutions** worldwide, identifying ~90 million
genetic variants. The primary purpose is imputation for genomic
selection, but the population-scale WGS data are equally valuable for
phylogeography.

- **Key reference**: Hayes B.J. & Daetwyler H.D. *1000 Bull Genomes
  Project to Map Simple and Complex Genetic Traits in Cattle:
  Applications and Outcomes.* **Annual Review of Animal Biosciences**
  7: 89–102 (2019). DOI: `10.1146/annurev-animal-020518-115024`
- **Earlier paper**: Daetwyler H.D. et al. *Whole-genome sequencing of
  234 bulls facilitates mapping of monogenic and complex traits in
  cattle.* **Nature Genetics** 46: 858–865 (2014). DOI:
  `10.1038/ng.3034`
- **BioProject**: `PRJEB42783` (Run 8), `PRJEB56689` (Run 9)
- **Data deposition**: NCBI BioProject (via ENA/SRA) + Ag Data Commons
  (`https://agdatacommons.nal.usda.gov/`)

### Access

The consortium operates under a **data-sharing agreement**: raw reads
are publicly deposited on ENA/SRA, but the imputed variant calls and
curated metadata for internal runs require partnership. For external
researchers:

1. **Public BAM/FASTQ files**: available via the BioProject accessions.
2. **Run summaries and SNP call sets**: available on Ag Data Commons
   for some releases.
3. **Partnership**: for full access to the latest internal runs, contact
   the consortium (`https://www.1000bullgenomes.com/`).

### Breeds represented (subset)

Holstein, Angus, Simmental, Limousin, Charolais, Hereford, Jersey,
Brown Swiss, Brahman, Nelore (indicine), and many more — covering both
*Bos taurus* (taurine) and *Bos indicus* (indicine) lineages.

---

## 2. Bovine HapMap Consortium

### Summary

The reference study of **cattle breed genetic structure**, published
in **Science** in 2009. The Bovine HapMap Consortium genotyped 37,470
SNPs in **497 cattle from 19 geographically and biologically diverse
breeds**, producing the first population-structure map of cattle
analogous to the human HapMap.

- **Key reference**: *The Bovine HapMap Consortium. Genome-Wide Survey of
  SNP Variation Uncovers the Genetic Structure of Cattle Breeds.*
  **Science** 324(5926): 528–532 (2009). DOI: `10.1126/science.1167936`
- **SNP data**: deposited in NCBI **dbSNP** (bovine entries)
- **Complementary arrays**: BovineSNP50 (50K), BovineHD (770K) from
  Illumina — widely used for downstream GWAS and imputation

### Key finding

> *"SNP diversity within taurine breeds was similar to that of humans,
> but was significantly less than diversity within indicine breeds, which
> suggested that the Indian subcontinent was a major site of cattle
> domestication and predomestication diversity."* — The Bovine HapMap
> Consortium, 2009

### 19 breeds analysed

| Group | Breeds |
|---|---|
| European taurine | Angus, Brown Swiss, Charolais, Guernsey, Hereford, Holstein, Jersey, Limousin, Norwegian Red, Red Angus |
| African taurine | N'Dama, Sheko |
| Indicine | Brahman, Gir, Nelore |
| Composite / hybrid | Beefmaster, Santa Gertrudis |
| Other | Piedmontese, Romagnola |

---

## 3. Bovine Genome Variation Database (BGVD)

### Summary

The most comprehensive integrated database of bovine genomic variation,
compiled from 432 re-sequenced individuals worldwide.

- **Key reference**: Chen N. et al. *BGVD: An Integrated Database for
  Bovine Sequencing Variations and Selective Signatures.* **Genomics,
  Proteomics & Bioinformatics** (2020). DOI: `10.1016/j.gpb.2019.03.006`
- **Web portal**: `http://animal.omics.pro/code/index.php/BosVar`
  (verify — the URL has changed over time)
- **Content** (from the publication):
  - **~60.44 million SNPs**
  - **~6.86 million indels**
  - **76,634 CNV regions**
  - Signatures of selective sweeps across breeds
  - 432 samples from modern cattle worldwide

### Unique feature

BGVD integrates **selective sweep** signatures across cattle breeds.
These genomic regions reflect breed-specific demographic and adaptive
history and can be used as comparative landmarks against any external
breed-resolved dataset.

---

## Additional resources (briefly)

| Resource | Scope | URL |
|---|---|---|
| **DAD-IS** (FAO) | Domestic Animal Diversity Information System — breed distribution, conservation status | `https://www.fao.org/dad-is/` |
| **Decker et al. 2014** | Worldwide cattle ancestry, divergence, and admixture (800K SNPs, 134 breeds) — key phylogeography paper | `10.1371/journal.pgen.1004254` |
| **Cattle reference genome (ARS-UCD1.2)** | Current reference assembly for all bovine analyses | NCBI Assembly `GCF_002263795.1` |
| **AnimalQTLdb** | Cattle QTL database for production and health traits | `https://www.animalgenome.org/cgi-bin/QTLdb/BT/` |

---

## Workflows

### Workflow 1 — Build a cattle breed phylogeographic map

Goal: produce a regional ancestry composition map of modern cattle for
use as a reference layer.

1. From BovineHapMap / 1000 Bull Genomes / Decker 2014, compile per-region
   breed ancestry composition (taurine vs indicine fraction, and within
   taurine: European vs African taurine).
2. Project onto a world map using `geopandas` or `bio:geo-map`.
3. Save the resulting raster/vector for overlay with any external
   geocoded dataset.

### Workflow 2 — Taurine / indicine diversity gradient

Goal: reproduce the HapMap diversity finding as a quantitative
reference gradient.

1. From BovineHapMap (or BGVD), extract per-breed expected heterozygosity.
2. Rank breeds by taurine vs indicine ancestry.
3. Produce a diversity vs ancestry plot. The resulting curve serves as
   the host-side reference for any comparative diversity analysis.

### Workflow 3 — Anchor the Neolithic bovine domestication with p3k14c

Goal: combine this skill with `p3k14c` to place the cattle
domestication event in its archaeological context.

1. From **p3k14c**, extract all dates with `Taxa` containing
   `Bos` (cattle) in the Fertile Crescent and Indus Valley regions
   (see `p3k14c` Workflow for domesticate entries).
2. Overlay the earliest dated cattle-associated sites onto the
   1000 Bull Genomes breed-origin map.
3. Produce a combined chronological / geographic figure.

## Caveats

- **Access restrictions.** The 1000 Bull Genomes internal data requires
  consortium partnership for full access; only BioProject-deposited
  runs are fully public. BovineHapMap and BGVD are more open.
- **Breed ≠ population.** Commercial breeds are human-defined categories
  that imperfectly map onto continuous genetic variation. Within-breed
  variation can be large, especially for composite and crossbred
  animals.
- **Domestication is complex.** Recent work (Decker 2014, Verdugo 2019)
  shows that cattle domestication involved multiple centres,
  back-crossing with aurochs, and secondary introgressions — it is not
  a clean single-origin story. Frame your narrative accordingly.
- **No ancient cattle DNA in these resources.** They cover modern
  breeds. For ancient cattle genomes, the primary literature (Park et
  al. 2015, Verdugo et al. 2019 *Science*) and
  `spaam-ancient-metagenome-dir` / ENA are the sources.
- **BGVD URL may be unstable.** The web portal has changed URLs.
  Always verify the current URL or download the precomputed files from
  the paper's supplementary materials.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`p3k14c`** | Archaeological ¹⁴C dates for cattle domestication sites |
| **`d-place`** | Subsistence mode (pastoralism vs agriculture) — cultural context |
| **`owtrad`** | Transhumance routes for pastoralist cattle mobility |
| **`aadr`** | Ancient human genomes — human side of the triad |
| **`spaam-ancient-metagenome-dir`** | Ancient livestock metagenomes |
| **`seshat`** | Polity-level history of pastoralist states |
| **`glottolog`** | Linguistic identifiers for the human populations associated with specific cattle breeds |
| **`bio:geo-map`** | Publication-quality map rendering |
| **DAD-IS** (FAO) | Breed distribution and conservation status |

## Citations

```bibtex
@article{hayes2019bull,
  title   = {1000 Bull Genomes Project to Map Simple and Complex
             Genetic Traits in Cattle: Applications and Outcomes},
  author  = {Hayes, Ben J. and Daetwyler, Hans D.},
  journal = {Annual Review of Animal Biosciences},
  volume  = {7},
  pages   = {89--102},
  year    = {2019},
  doi     = {10.1146/annurev-animal-020518-115024}
}

@article{daetwyler2014bull234,
  title   = {Whole-genome sequencing of 234 bulls facilitates mapping
             of monogenic and complex traits in cattle},
  author  = {Daetwyler, Hans D. and Capitan, Aur{\'e}lien and Pausch, Hubert
             and others},
  journal = {Nature Genetics},
  volume  = {46},
  pages   = {858--865},
  year    = {2014},
  doi     = {10.1038/ng.3034}
}

@article{bovinehapmap2009,
  title   = {Genome-Wide Survey of SNP Variation Uncovers the Genetic
             Structure of Cattle Breeds},
  author  = {{The Bovine HapMap Consortium}},
  journal = {Science},
  volume  = {324},
  number  = {5926},
  pages   = {528--532},
  year    = {2009},
  doi     = {10.1126/science.1167936}
}

@article{chen2020bgvd,
  title   = {BGVD: An Integrated Database for Bovine Sequencing
             Variations and Selective Signatures},
  author  = {Chen, Ningbo and others},
  journal = {Genomics, Proteomics \& Bioinformatics},
  year    = {2020},
  doi     = {10.1016/j.gpb.2019.03.006}
}

@article{decker2014worldwide,
  title   = {Worldwide Patterns of Ancestry, Divergence, and Admixture
             in Domesticated Cattle},
  author  = {Decker, Jared E. and others},
  journal = {PLOS Genetics},
  volume  = {10},
  number  = {3},
  pages   = {e1004254},
  year    = {2014},
  doi     = {10.1371/journal.pgen.1004254}
}
```
