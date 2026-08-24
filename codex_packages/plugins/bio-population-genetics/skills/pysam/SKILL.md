---

name: pysam
description: >-
  Read, manipulate and write genomic alignment formats (SAM/BAM/CRAM) and variant files
  (VCF/BCF) from Python; a wrapper over htslib. Use when inspecting read depth or coverage
  at a genome position, extracting reads over an interval, building a pileup to genotype a
  site by hand, filtering or merging BAM files, parsing a VCF programmatically rather than
  with bcftools, or checking mapping quality and read support behind a variant call. Note
  for bacterial work: MTBC references such as NC_000962.3 are single-contig with no 'chr'
  prefix, and fetch()/pileup() coordinates are 0-based half-open while VCF and SPDI are
  1-based.
license: MIT
---

# Pysam - Genomic Alignments

Used for high-throughput sequencing pipelines. It allows efficient access to billions of DNA fragments aligned to a reference genome.

## When to Use

- Processing next-generation sequencing (NGS) data.
- Analyzing genomic variants (SNPs, indels).
- Extracting reads from specific genomic regions.
- Building custom bioinformatics pipelines.
- Quality control of sequencing data.

## Core Principles

### Indexed Access

BAM files must be indexed (.bai) for efficient random access to genomic regions.

### Coordinate System

This is the single most common source of off-by-one errors, so state it precisely
rather than "0-based or 1-based depending on context":

| Interface | Convention |
|---|---|
| `fetch(contig, start, stop)`, `pileup(...)`, `count_coverage(...)` | **0-based, half-open**: `fetch("NC_000962.3", 761154, 761155)` returns the reads over 1-based position 761155 |
| `read.reference_start` | 0-based |
| `read.reference_end` | 0-based, exclusive |
| `column.reference_pos` (pileup) | 0-based |
| `rec.pos` on a `VariantRecord` | **1-based** (as printed in the VCF) |
| `rec.start` / `rec.stop` on a `VariantRecord` | 0-based, half-open |
| Region strings, e.g. `fetch(region="NC_000962.3:761155-761155")` | **1-based, inclusive**, like samtools |
| SPDI, HGVS, and every coordinate in the group's database | 1-based |

Rule of thumb: everything expressed as separate `start, stop` arguments is
0-based half-open; everything parsed from a text region string or read out of a
VCF field is 1-based. Convert once, at the boundary, and never inside a loop.

### Reference Naming

MTBC references are single-contig and carry no `chr` prefix. The reference name is
whatever is written in the BAM header, usually `NC_000962.3` for H37Rv, sometimes
`H37Rv`, `AL123456.3` or `Chromosome` depending on the pipeline that produced it.
Do not hard-code it:

```python
bam = pysam.AlignmentFile(path, "rb")
(contig,) = bam.references          # single-contig genome: exactly one name
print(contig, bam.lengths[0])       # e.g. NC_000962.3 4411532
```

A `fetch()` that returns nothing on a file you know has coverage is almost always
a contig-name mismatch, not an empty region.

### Read Attributes

Each read contains sequence, quality scores, alignment position, and flags.

## Quick Reference

### Standard Imports

```python
import pysam
```

### Basic Patterns

```python
# 1. Open BAM file
samfile = pysam.AlignmentFile("aligned_reads.bam", "rb")

# 2. Iterate over reads covering a specific genomic position.
#    H37Rv 1-based 2155168 is the katG S315T site, so the 0-based half-open
#    window for that single position is 2155167:2155168.
for read in samfile.fetch("NC_000962.3", 2155167, 2155168):
    print(f"Read: {read.query_name}, MAPQ: {read.mapping_quality}")
    print(f"Sequence: {read.query_sequence}")
    print(f"Start (0-based): {read.reference_start}")

# 3. Variant analysis (VCF). rec.pos is 1-based; fetch() bounds are 0-based.
vcf = pysam.VariantFile("mutations.vcf")
for rec in vcf.fetch("NC_000962.3", 2155167, 2155168):
    print(f"Pos: {rec.pos}, Ref: {rec.ref}, Alt: {rec.alts}")
    print(f"Genotype: {rec.samples['sample1']['GT']}")

# 4. Writing aligned reads
outfile = pysam.AlignmentFile("output.bam", "wb", template=samfile)
for read in samfile:
    if read.mapping_quality > 30:
        outfile.write(read)
outfile.close()
```

## Critical Rules

### ✅ DO

- **Always use indexed files** - Create index with `pysam.index("file.bam")` for fast access.
- **Check read flags** - Use `read.is_paired`, `read.is_unmapped` to filter reads.
- **Handle unmapped reads** - Unmapped reads have `reference_start = -1`.
- **Close files explicitly** - Use context managers or `.close()` to avoid resource leaks.

### ❌ DON'T

- **Don't iterate over entire BAM** - Use `fetch()` with regions for efficiency.
- **Don't ignore quality scores** - Low-quality bases can cause false variants.
- **Don't mix coordinate systems** - Be consistent with 0-based vs 1-based indexing.

## Advanced Patterns

### Genotyping a Position by Hand (pileup)

The workhorse for checking what the reads actually say at a resistance position,
independently of whatever the variant caller decided. Note the two arguments that
matter more than any other: `truncate=True` restricts the columns to the requested
window (without it, pysam returns every column touched by any overlapping read),
and `max_depth` must be raised above its default or deep bacterial data is
silently downsampled.

```python
def base_counts(bam_path, contig, pos1, min_bq=20, min_mapq=30):
    """Allele counts at a 1-based position. Returns {'A': n, 'C': n, ...}."""
    counts = {"A": 0, "C": 0, "G": 0, "T": 0}
    with pysam.AlignmentFile(bam_path, "rb") as bam:
        for col in bam.pileup(contig, pos1 - 1, pos1,
                              truncate=True,          # only the requested column
                              max_depth=100000,       # default 8000 truncates
                              min_base_quality=min_bq,
                              min_mapping_quality=min_mapq,
                              ignore_overlaps=True):  # don't count a pair twice
            for base in col.get_query_sequences(add_indels=False):
                base = base.upper()
                if base in counts:
                    counts[base] += 1
    return counts

c = base_counts("isolate.bam", "NC_000962.3", 2155168)   # katG S315T site
total = sum(c.values())
print(c, "depth", total)
if total:
    major = max(c, key=c.get)
    print("major allele", major, f"{c[major] / total:.1%}")
```

An intermediate frequency here (roughly 10 to 90 percent) is the signature of a
mixed or contaminated sample rather than a heterozygous site: a bacterial isolate
is haploid, so there is no biological reason for two alleles at one position. Feed
that observation to `strain-qc` rather than calling a variant.

`get_query_sequences()` returns `*` for a deletion and, with
`add_indels=True`, strings like `A+2CT` for insertions. Filtering `if base in
counts` above therefore silently drops indel evidence, which is the right default
for a substitution check and the wrong one if the question is about an indel.

### Coverage Over a Region

`count_coverage` is much faster than a pileup when only depth matters. It returns
four arrays, one per base, in ACGT order.

```python
import numpy as np

with pysam.AlignmentFile("isolate.bam", "rb") as bam:
    (contig,) = bam.references
    acgt = bam.count_coverage(contig, 0, bam.lengths[0],
                              quality_threshold=20)
depth = np.sum(np.array(acgt), axis=0)     # per-position depth, 0-based index

print("median depth", np.median(depth))
print("breadth at >=10x", (depth >= 10).mean())
print("uncovered positions", int((depth == 0).sum()))
```

Breadth of coverage is the number that matters for a phylogeny: positions with no
reads are not reference, they are unknown, and treating them as reference is
exactly the bias that `snp-distance` corrects with its no-call handling.

### Counting Reads per Gene

```python
# genes: gene_name -> (contig, start0, end0), 0-based half-open
counts = {gene: 0 for gene in genes}
for gene, (contig, start0, end0) in genes.items():
    # count() applies the same region semantics as fetch()
    counts[gene] = samfile.count(contig, start0, end0,
                                 read_callback=lambda r: (
                                     not r.is_unmapped
                                     and not r.is_secondary
                                     and not r.is_supplementary
                                     and not r.is_duplicate
                                     and r.mapping_quality >= 30))
```

Counting by iterating the whole BAM and testing each read against every gene is
quadratic and, for a read spanning a gene boundary, ambiguous. Let the index do
the work with one `count()` per interval. For a dense annotation (~4000 genes on
one 4.4 Mb contig) a single pass with an interval tree is faster still, but only
once the number of intervals is large enough to matter.

### Variant Filtering

```python
# Filter variants by quality and depth
for rec in vcf.fetch():
    sample = rec.samples['sample1']
    depth = sample.get('DP')
    qual = rec.qual
    if depth is not None and qual is not None and depth > 10 and qual > 20:
        # Process high-quality variant
        pass
```

`DP` and `QUAL` are both optional in the VCF specification and are absent from
some callers' output, so `rec.samples['s']['DP']` returns `None` rather than
raising. Compare explicitly against `None` before the numeric test, or a
missing-annotation record silently raises a `TypeError` in the middle of a long
run.

### Writing a Filtered VCF

```python
vcf_in = pysam.VariantFile("in.vcf.gz")
vcf_out = pysam.VariantFile("out.vcf.gz", "w", header=vcf_in.header)
for rec in vcf_in:
    if rec.qual and rec.qual >= 30:
        vcf_out.write(rec)
vcf_out.close()
pysam.tabix_index("out.vcf.gz", preset="vcf", force=True)
```

The output header must come from the input (`header=vcf_in.header`), otherwise
contig and FORMAT definitions are missing and the file is unreadable by
downstream tools even though it looks fine as text.

## Interaction with the group's pipeline

- Positions in the group's database and in SPDI are 1-based; every `fetch` and
  `pileup` bound in this skill is 0-based. Convert at the call site, as in
  `base_counts` above.
- To map a variant to a gene and a functional consequence, hand the SPDI to
  `spdi-annotation` rather than re-deriving coordinates here.
- To decide whether an isolate should enter the database at all, the pileup
  evidence above is an input to `strain-qc`, not a verdict on its own.

Pysam provides the low-level access needed for genomic data processing, enabling researchers to work directly with the raw data of life itself.
