---
name: spdi-annotation
description: >-
  Academic research toolkit for the Guyeux group (FEMTO-ST, University of Franche-Comte). Annotates MTBC variants for peer-reviewed phylogenomic publications. Annotate MTBC SPDI variants with gene, effect (missense/synonymous/stop/frameshift),
  amino acid change, and functional category. First queries TBannotator for existing
  annotations, then falls back to local GenBank/GFF3 annotation for missing variants.
  To check whether a SPDI variant (especially a high-impact one)
  has already been described in the literature — useful to add a
  citation column to the supplementary table — pair with
  `tbmonitor-papers` and search for the SPDI string, gene name, or
  HGVS_p notation in title/abstract.

  Use when: annotating a list of SPDI variants for an MTBC article, building
  supplementary tables with functional impact, or classifying variants by effect type.
argument-hint: "<spdi_list.csv or spdi_list.txt> [-o annotated.csv] [--reference NC_000962.3]"
user-invocable: true
disable-model-invocation: false
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres, mcp__tbannotator__tool_get_schema
---

# SPDI Annotation — Functional annotation of MTBC variants

Annotate SPDI variants (format `NC_000962.3:pos:ref:alt`) with gene location, protein effect, amino acid change, impact severity, and Mycobrowser functional category.

## Strategy: TBannotator-first, local fallback

The annotation follows a **two-step strategy** to maximise accuracy and minimise redundant computation:

### Step 1: Query TBannotator (preferred)
Query `mv_spdi_mutations` or the raw SNP tables for existing annotations:

```sql
-- Batch lookup of SPDIs in TBannotator
SELECT DISTINCT
    s.spdi,
    s.gene,
    s.effect,
    s.amino_acid_change,
    s.locus_tag
FROM tb_report_snp s
WHERE s.spdi IN ('NC_000962.3:42432:C:T', 'NC_000962.3:1004800:G:A', ...)
```

If the MCP server is unavailable or SPDIs are missing, proceed to Step 2.

### Step 2: Local annotation (fallback)
For SPDIs not found in TBannotator, annotate locally using the H37Rv reference:
- **GFF3** for gene boundaries, strand, locus_tag, product
- **GenBank** (.gb) for genome sequence and codon-level analysis

Run the provided script:
```bash
python3 scripts/annotate_spdis.py input_spdis.csv \
    --gff3 NC_000962.3.gff3 \
    --genbank NC_000962.3.gb \
    -o annotated.csv
```

## CRITICAL: Negative-strand annotation rule

**SPDI format stores ref and alt on the FORWARD (+) strand, always.**

When annotating a variant in a gene on the **negative (-) strand**:

1. Extract the codon on the forward strand
2. Substitute the alt allele **DIRECTLY** (no complement!) at the correct position
3. Then reverse-complement the entire modified codon to get the coding-strand codon
4. Translate the coding-strand codon to amino acid

```python
# CORRECT — alt is already on forward strand
fwd_alt = list(fwd_codon)
fwd_alt[2 - codon_offset] = alt.upper()      # Direct substitution
alt_codon = revcomp(''.join(fwd_alt))

# WRONG — double complementation bug!
# fwd_alt[2 - codon_offset] = complement(alt.upper())  # BUG: alt is already fwd!
# alt_codon = revcomp(''.join(fwd_alt))                 # revcomp applies complement again
```

**Why this matters:** The double-complementation bug produces incorrect amino acids for ALL negative-strand genes (~47% of H37Rv genes). Known consequences:
- cas1 (Rv2817c): G337R missense falsely reported as G337* stop-gained
- ftsK (Rv2748c): Y394Y synonymous falsely reported as Y394* stop-gained
- 147/500 annotations affected in the L4.15 study

## Arguments

```
annotate_spdis.py <input_file> [options]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `input_file` | (required) | CSV with `SPDI` column, or plain text (one SPDI per line) |
| `--gff3` | `NC_000962.3.gff3` | GFF3 annotation file |
| `--genbank` | `NC_000962.3.gb` | GenBank sequence file |
| `-o`, `--output` | stdout | Output CSV path |
| `--tbannotator-first` | `true` | Query TBannotator before local annotation |
| `--skip-tbannotator` | `false` | Skip TBannotator, annotate everything locally |

## Input format

### CSV with SPDI column
```csv
SPDI,Tier,Exclusivity
NC_000962.3:42432:C:T,1,1.000
NC_000962.3:1004800:G:A,1,1.000
```

### Plain text (one SPDI per line)
```
NC_000962.3:42432:C:T
NC_000962.3:1004800:G:A
```

## Output columns

| Column | Description |
|--------|-------------|
| `SPDI` | Original SPDI identifier |
| `Position` | 1-based genomic position |
| `Ref` | Reference allele (fwd strand) |
| `Alt` | Alternative allele (fwd strand) |
| `Gene_name` | Gene name (e.g., `prrB`, `eccC2`) |
| `Locus_tag` | Rv number (e.g., `Rv0902c`) |
| `Strand` | Gene strand (`+` or `-`) |
| `Effect` | `missense_variant`, `synonymous_variant`, `stop_gained`, `frameshift_variant`, `upstream_promoter_variant`, `intergenic_region` |
| `Impact` | `HIGH`, `MODERATE`, `LOW`, `MODIFIER` |

### Promoteurs de résistance (annotation locale)

Une mutation qui tombe en amont (5′) d'un gène de résistance connu était
classée « intergénique / MODIFIER » — perdant une information
pharmacologiquement importante. Le fallback local détecte désormais les
**promoteurs de résistance** (`eis`, `pncA`, `ethA`, `whiB7`, `ahpC`, `embA`,
fenêtre de 200 pb en amont) et les reclasse en `upstream_promoter_variant`
(impact MODERATE), avec la drogue et la distance au start (`c.-N`).

> ⚠️ **À valider avant usage clinique.** Les coordonnées de start dans
> `RESISTANCE_PROMOTERS` (script `annotate_spdis.py`) sont dérivées des
> positions H37Rv `NC_000962.3` mais **n'ont pas été revérifiées contre le
> GFF3 du dépôt**. Confirmer chaque `(gene, start, strand)` et ajuster
> `PROMOTER_WINDOW` selon les régions -35/-10 documentées avant de s'appuyer
> dessus pour un rapport de résistance.
| `AA_Change` | e.g., `R660H`, `G337R`, `Y394Y` |
| `Product` | Gene product description |
| `Functional_Category` | Mycobrowser category |
| `Annotation_Source` | `tbannotator` or `local` |

All input columns are preserved in the output.

## Functional categories (Mycobrowser-derived)

| Category | Gene name patterns |
|----------|-------------------|
| PE/PPE | PE_PGRS*, PE_*, PPE* |
| Lipid metabolism | fadD*, pks*, accD*, mmaA*, kas* |
| Cell wall & cell processes | mmpL*, ecc*, esx*, esp*, mur*, sec*, tat* |
| Information pathways | rpoB, gyrA, rpsL, rrs, rpl* |
| Regulatory proteins | prr*, sig*, whiB*, pkn*, dev*, dos* |
| Intermediary metabolism & respiration | glnA*, aroE*, cyd*, nuo*, nar*, nir* |
| Conserved hypotheticals | product contains "hypothetical" |
| Insertion sequences & phages | product contains "transposase", "phage" |
| Intergenic | Between genes |

## TBannotator query examples

### Batch annotation lookup
```sql
SELECT DISTINCT s.spdi, s.gene, s.effect, s.amino_acid_change, s.locus_tag
FROM tb_report_snp s
WHERE s.spdi IN ($SPDI_LIST)
LIMIT 1000;
```

### Check if annotation exists for a specific SPDI
```sql
SELECT spdi, gene, effect, frequency
FROM mv_spdi_mutations
WHERE spdi = 'NC_000962.3:42432:C:T';
```

### Get all annotations for a lineage's markers
```sql
SELECT m.spdi, s.gene, s.effect, s.amino_acid_change
FROM mv_lineage_markers m
JOIN tb_report_snp s ON m.spdi = s.spdi
WHERE m.lineage = 'L4.15' AND m.marker_type = 'core_exclusive';
```

## Validation

After annotation, verify negative-strand genes with BioPython:

```python
from Bio import SeqIO
from Bio.Seq import Seq

record = SeqIO.read("NC_000962.3.gb", "genbank")
genome = str(record.seq)

# Example: cas1 (Rv2817c, complement strand)
# SPDI: NC_000962.3:3123974:C:T
pos_0 = 3123974
ref, alt = 'C', 'T'

# Find the CDS feature for Rv2817c
for feat in record.features:
    if feat.type == 'CDS' and feat.qualifiers.get('locus_tag', [''])[0] == 'Rv2817c':
        cds_seq = feat.extract(record.seq)
        # Determine codon position and verify amino acid change
        cds_pos = feat.location.end - pos_0 - 1  # for complement strand
        codon_idx = cds_pos // 3
        print(f"Codon {codon_idx + 1}: {cds_seq[codon_idx*3:codon_idx*3+3]}")
        break
```

## Common pitfalls

| Pitfall | Solution |
|---------|----------|
| Double complementation on minus strand | NEVER `complement(alt)` — alt is already fwd in SPDI |
| SPDI is 0-based, GFF3 is 1-based | Always convert: `pos_1based = spdi_pos + 1` |
| Gene boundaries off-by-one | GFF3 uses 1-based inclusive start and end |
| Missing CDS for RNA genes | Skip codon analysis for tRNA/rRNA/ncRNA |
| Frameshift detection | Compare ref/alt lengths: `len(alt) - len(ref)) % 3 != 0` |
| Complex variants (MNV) | Flag as `complex` rather than trying codon analysis |

## Workflow integration

```
fetch-tbannotator → spdi.txt
                         ↓
            spdi-annotation (this skill)
                         ↓
              annotated SPDI table
                         ↓
         snp-distance / convergent-evolution / lineage-comparison
```
