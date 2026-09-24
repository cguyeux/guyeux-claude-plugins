---

name: spdi-annotation
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST), peer-reviewed MTBC
  phylogenomics: annotates SPDI variants (NC_000962.3:pos:ref:alt) with gene,
  effect (missense / synonymous / stop / frameshift), amino acid change, impact
  and Mycobrowser category. TBannotator first, local GenBank / GFF3 fallback.

  Use when: annotating SPDI variants for an MTBC article, supplementary tables
  of functional impact, classifying variants by effect.

  Scope: developed on the MTBC, applies to any clonal bacterial pathogen
  (Yersinia, Leptospira...) via the local GenBank/GFF3 path. To use it outside
  the MTBC: supply the genus reference GenBank/GFF3 and its accession
  (`--reference`); TBannotator lookup and Mycobrowser categories are MTBC-only.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres, mcp__tbannotator__tool_get_schema
---

> [!WARNING]
> **[2026-09-08] TABLES ABSENTES du serveur tblearn.** Ce skill interroge 2 objet(s) qui
> n'existent plus depuis le remplacement du MCP TBannotator. Contrairement au filtre `system_name`,
> ces requêtes ne rendent pas un ensemble vide : elles **lèvent une erreur** `relation does not exist`.
>
> | table citée ici | remplacer par | fondement |
> |---|---|---|
> | `mv_lineage_markers` | **tb_lineage_marker** | mêmes colonnes (`lineage_code`, `spdi_variant_name`, `lineage_level`, `lineage_parent`, `is_negative`) |
> | `mv_spdi_mutations` | **tb_report_spdi ⋈ tb_report_spdi_annotations sur spdi_id** | le variant dans la première, l'annotation (`locus_tag`, `hgvs_p`, `impact`) dans la seconde |
>
> Correspondances établies en comparant les colonnes, pas devinées. Détail et schéma complet :
> `~/.agents/knowledge/tblearn-migration.md`.


# SPDI Annotation : Functional annotation of MTBC variants

Annotate SPDI variants (format `NC_000962.3:pos:ref:alt`) with gene location, protein effect, amino acid change, impact severity, and Mycobrowser functional category.

## Strategy: TBannotator-first, local fallback

The annotation follows a **two-step strategy** to maximise accuracy and minimise redundant computation:

### Step 1: Query TBannotator (preferred)
Query `mv_spdi_mutations` or the raw SNP tables for existing annotations:

> ⚠ **Schéma v3.6 (vérifié 2026-07-31)** : il n'existe **pas** de table `tb_report_snp`, ni de colonnes
> `spdi` / `gene` / `effect` / `amino_acid_change`. Les annotations vivent dans
> **`tb_report_spdi_annotations`** : `spdi_variant_name` (le SPDI), `locus_tag` (Rv####, **pas** de nom de
> gène), `annotation_type` (missense_variant, synonymous_variant, frameshift_variant…), `impact`
> (LOW/MODERATE/HIGH), `hgvs_c`, `hgvs_p`, `protein_position`.

```sql
-- Batch lookup of SPDIs in TBannotator
SELECT DISTINCT
    a.spdi_variant_name,
    a.locus_tag,
    a.annotation_type,
    a.impact,
    a.hgvs_p
FROM tb_report_spdi_annotations a
WHERE a.spdi_variant_name IN ('NC_000962.3:42432:C:T', 'NC_000962.3:1004800:G:A');
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
classée « intergénique / MODIFIER », perdant une information
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
SELECT DISTINCT a.spdi_variant_name, a.locus_tag, a.annotation_type, a.impact, a.hgvs_p
FROM tb_report_spdi_annotations a
WHERE a.spdi_variant_name IN ($SPDI_LIST)
LIMIT 1000;
```

### Fréquence d'un SPDI (nombre de souches porteuses)
```sql
-- mv_spdi_mutations : colonnes réelles = spdi_variant_name, mutation, mutation_type, strain_count
-- (il n'y a ni `spdi`, ni `gene`, ni `effect`, ni `frequency`)
SELECT spdi_variant_name, mutation, mutation_type, strain_count
FROM mv_spdi_mutations
WHERE spdi_variant_name = 'NC_000962.3:42432:C:T';
```

### Annotations des marqueurs d'une lignée
```sql
-- mv_lineage_markers : colonnes réelles = lineage_code, spdi_variant_name, spdi_variant_position
-- (pas de `lineage`, pas de `marker_type` : les marqueurs stockés SONT les marqueurs définitoires du système)
SELECT m.lineage_code, m.spdi_variant_name,
       a.locus_tag, a.annotation_type, a.hgvs_p
FROM mv_lineage_markers m
LEFT JOIN tb_report_spdi_annotations a ON a.spdi_variant_name = m.spdi_variant_name
WHERE m.lineage_code = '4.15';
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
| Double complementation on minus strand | NEVER `complement(alt)`, alt is already fwd in SPDI |
| SPDI is 0-based, GFF3 is 1-based | Always convert: `pos_1based = spdi_pos + 1` |
| Gene boundaries off-by-one | GFF3 uses 1-based inclusive start and end |
| Missing CDS for RNA genes | Skip codon analysis for tRNA/rRNA/ncRNA |
| Frameshift detection | Compare ref/alt lengths: `len(alt) - len(ref)) % 3 != 0` |
| Complex variants (MNV) | Flag as `complex` rather than trying codon analysis |

## Workflow integration

Pour savoir si un variant SPDI (surtout un variant à fort impact) a déjà été
décrit dans la littérature, utile pour ajouter une colonne de citation à la
table supplémentaire, enchaîner avec le skill `tbmonitor-papers` et chercher
la chaîne SPDI, le nom du gène ou la notation HGVS_p dans les titres et
résumés.

```
fetch-tbannotator → spdi.txt
                         ↓
            spdi-annotation (this skill)
                         ↓
              annotated SPDI table
                         ↓
         snp-distance / convergent-evolution / lineage-comparison
```

## Codex packaging note

This packaged copy targets Codex. MCP tool names in `allowed-tools` are prerequisites: verify them with `codex mcp list` in the active profile before relying on live queries.
