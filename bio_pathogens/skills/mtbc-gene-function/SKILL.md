---
name: mtbc-gene-function
description: >-
  Academic research toolkit for the Guyeux group (FEMTO-ST) MTBC pipeline:
  produce a structured functional annotation for a Mycobacterium tuberculosis
  H37Rv gene (by gene name like `katG` or locus tag like `Rv1908c`). Answers from
  the group's OWN curated annotation_mtbc project FIRST -- per-gene UniProt function
  + EC, Pfam domains, STRING partners, conservation/selection (pN/pS), and Foldseek
  structural leads for dark genes -- and only enriches or falls back to the ESM Atlas
  API (via `esm-atlas-cli`) for what is not yet annotated. Works fully offline from
  the curated source. Returns gene + locus tag + product + EC + the evidence channels
  used + a short citable function paragraph (JSON plus optional prose).

  Use when: an Atlas lineage page mentions a gene (RD content, defining SNP,
  resistance allele, pathway gene) and needs an automatic functional blurb; an
  exploratory analysis hits an unfamiliar Rv locus tag and the Guyeux group wants a
  30-second context grounded in their own annotation work.
argument-hint: "<gene_or_locus> [--paragraph] [--json]"
allowed-tools: Bash, Read, Write, Edit
user-invocable: true
---

# /mtbc-gene-function -- Functional annotation of an H37Rv gene

This skill turns a gene name (`katG`) or a locus tag (`Rv1908c`) into a
structured functional annotation. It answers from the group's curated
`annotation_mtbc` project FIRST (per-gene UniProt function + EC, Pfam, STRING
partners, conservation/selection, and Foldseek structural leads for dark genes),
then enriches or falls back to the ESM Atlas SAE features via `esm-atlas-cli`.

**Curated-source-first (offline-capable).** With `annotation_mtbc` present a full
answer needs no network and no ESM: `mtbc-gene-function katG --no-esm --paragraph`.
Set `MTBC_ANNOTATION_DIR` if the project is not at `~/docs/codes/mtbc/annotation_mtbc`.
The per-gene channels read are `data/gene_xref_all.tsv`, `résultats/phase2e_uniprot`,
`phase2b_pfam`, `phase2h_string`, `phase2f_conservation`, `phase2_esm`, and
`data/structural_candidates_ext.tsv`. Self-check (offline):
`python3 -m mtbc_gene_function.smoke_test`.

## What it does

1. **Resolve** the gene name or locus tag against the H37Rv CDS fasta at
   `~/docs/codes/mtbc/investigate_phylo/resources/NC_000962.3_CDS.fasta`
   (parses the `>lcl|... [gene=X] [locus_tag=Y] [protein=Z]` headers).
2. **Translate** the DNA CDS with the MTBC translation table (table 11;
   GTG / TTG initiators → M, then standard genetic code).
3. **Query ESM Atlas** via the `esm-atlas-cli` Python client :
   - `client.lookup_sequence(protein)` → SAE features with descriptions,
     sequence stats, cluster representative hash.
   - `client.cluster(cluster_rep_hash)` if a rep is known → cluster size,
     `cluster_pct_characterized` (Pfam annotation rate).
4. **Return** a structured payload :
   ```json
   {
     "gene": "katG",
     "locus_tag": "Rv1908c",
     "product": "catalase-peroxidase",
     "protein_hash": "d08e94...",
     "length_aa": 740,
     "top_features": [
       {"index": 14273, "activation": 1.50, "label": "Folded alpha/beta domain cores"},
       {"index": 10758, "activation": 1.44, "label": "Secreted histidine-metal catalytic domains"},
       ...
     ],
     "cluster": {"size": 8431, "pct_characterized": 87},
     "function_summary": "Catalase-peroxidase (740 aa). ESM SAE flags the protein as a secreted enzyme with a histidine-metal catalytic site, consistent with the bundled H37Rv annotation as catalase-peroxidase.",
     "source": "H37Rv NC_000962.3 + ESM Atlas (alpha)"
   }
   ```
5. **Optional paragraph** (`--paragraph`) : a short human-readable prose
   block ready to drop into an Atlas fiche, written in the academic-neutral
   voice required by AUP.

## How to use

### From a shell

```bash
/mtbc-gene-function katG
/mtbc-gene-function Rv1908c --paragraph
/mtbc-gene-function rpoB --json   # JSON only, machine-readable
```

### From Python (called by the Atlas backend or by other skills)

```python
from mtbc_gene_function import annotate_gene

ann = annotate_gene("katG")
print(ann["function_summary"])
print(ann["top_features"][:3])
```

## Inputs

- **`gene_or_locus`** : `katG`, `rpoB`, `Rv1908c`, `Rv0667`. Case-insensitive.
- Optional flag `--paragraph` for the prose block.
- Optional flag `--json` to suppress the human-readable summary.

## Outputs

- JSON to stdout by default (always).
- An additional Markdown-friendly paragraph if `--paragraph` is set.
- A non-zero exit code if the gene is not found in H37Rv (`1`), or the
  ESM Atlas is unavailable (`3`, with the H37Rv-only fields still in JSON).

## Resilience

- If `esm-atlas-cli` raises `EsmAtlasUnavailable`, the skill returns a
  partial payload : gene name, locus tag, product, length, protein hash,
  but no `top_features` / `cluster`. The `function_summary` falls back
  to the H37Rv `[protein=…]` annotation alone, with an explicit "(ESM
  Atlas unavailable, fall-back to H37Rv-only)" note.
- All ESM responses go through the `esm-atlas-cli` disk cache (TTL 30 days
  for `feature_meta`, 7 days for sequence lookups). A repeat call on the
  same gene is instant.

## What this skill does not do

- It does not predict mutations' impacts (that's `mtbc-mutation-impact`).
- It does not narrate a pathway (that's `mtbc-pathway-explain`).
- It does not draft an Atlas fiche end-to-end (that's `atlas-add-lineage`,
  which can invoke this skill multiple times for each gene it mentions).
- It does not query Mycobrowser directly (today). When a Mycobrowser
  client is added, this skill is the natural place to merge its
  annotation with the ESM SAE features.
- The ESM SAE feature labels in `function_summary` are an **exploratory
  description**, not a validated domain assignment. Before stating a protein
  domain or fold in a manuscript, confirm it with **Pfam/`hmmscan --cut_ga`**
  (SAE narratives have been both confirmed and contradicted by Pfam:
  rehumanisation_L6L9L10, 2026-05-30, where an "AAA+ ATPase" SAE read of
  Rv0386 was in fact a LuxR/GerE HTH regulator with no ATPase domain).

## Quirks (inherited from `esm-atlas-cli` and from the H37Rv catalogue)

- A few CDS entries in `NC_000962.3_CDS.fasta` use `GTG` / `TTG` initiator
  codons. The translation routine forces those to `M` (as per genetic
  table 11). All downstream codons are translated by the standard rules.
- The H37Rv reference protein (e.g. `katG` in the alpha API) is **its own
  cluster representative** for some genes : `lookup(hash)["cluster_rep_protein_hash"]`
  is then `None`, and the `cluster` block of the output stays empty.
- Pseudogenes and frameshift-broken CDS are translated up to the first
  internal stop codon. The output `length_aa` reflects what was sent to
  ESM. The skill flags `truncated: true` in the output if the translated
  protein is shorter than the conceptual CDS length / 3.

## Workflow alignment

```
H37Rv CDS catalogue (investigate_phylo/resources/NC_000962.3_CDS.fasta)
       │
       └─►  this skill (mtbc-gene-function)
              │
              ├─►  esm-atlas-cli (lookup, cluster)
              │
              └─► structured JSON   →  Atlas backend  →  /gene/<name> HTML page
                                    →  mtbc-pathway-explain
                                    →  manuscript drafting
```
