---
name: mtbc-pathway-explain
description: >-
  Academic research toolkit for the Guyeux group (FEMTO-ST) MTBC pipeline:
  produce a structured, CURATED-FIRST narration of a gene set as a pathway -- a
  predefined pathway from the bundled catalogue (ESX-1..5, PDIM, mycolic-acid, DosR,
  oxidative stress, resistance pathways...), a gene's network neighbourhood
  (`neighbors:GENE`), or an explicit gene list. Annotates each gene curated-first via
  `mtbc-gene-function` (annotation_mtbc: UniProt function + EC + Pfam + conservation),
  aggregates the dominant enzyme classes and Pfam domains across the set, flags the
  uncharacterised (dark) genes, and narrates it with the PPI network structure
  (cohesion, density, hub gene) from `mtbc-gene-network`. ESM Atlas is an optional
  enrichment. Output JSON + a short paragraph for an Atlas page.

  Use when: a lineage shows a positive-selection signal on a pathway and the group
  wants a pathway-level narration that names the proteins, their functions, and how
  tightly they interact; or when a network module / a gene's neighbourhood needs to
  be read as a functional unit; or, given a lineage's selection table
  (`--from-selection`, e.g. McDonald-Kreitman output from `mk-ascertainment`), to map the
  signal onto the catalogue and narrate the affected pathways -- significance-gated
  (positive alpha + BH-FDR p) so a `selection` section is written only when the test
  concluded. It reads an existing result, it does not run the selection test.
argument-hint: "<pathway_id | neighbors:GENE | gene,gene,...> | --from-selection TABLE [--lineage L] [--paragraph]"
allowed-tools: Bash, Read, Write
user-invocable: true
---

# /mtbc-pathway-explain -- curated, network-aware pathway narration

This skill narrates a **gene set** as a pathway. The set can be a predefined pathway
from the bundled catalogue, a gene's **network neighbourhood** (`neighbors:katG`), or
an **explicit gene list** (`katG,ahpC,furA,...`). Each gene is annotated
**curated-first** via `mtbc-gene-function` (UniProt function + EC + Pfam from
annotation_mtbc); the skill aggregates the dominant enzyme classes and Pfam domains,
flags the dark genes, and adds the **PPI network context** from `mtbc-gene-network`
(how cohesive the set is, its internal-edge density, and its hub gene). It returns a
JSON payload + a short paragraph for an Atlas page.

```bash
cd <this skill> && ./run_pathway.sh ESX-2 --paragraph
./run_pathway.sh neighbors:furA --min-score 700 --paragraph   # a gene's neighbourhood as a pathway
./run_pathway.sh katG,ahpC,sodA,sodC,furA --paragraph         # an explicit subnetwork
./run_pathway.sh --from-selection ~/docs/codes/mtbc/L4.13/data/mk_input_annotated.csv --lineage L4.13 --min-variants 3 --top 3 --paragraph
python3 -m mtbc_pathway_explain.smoke_test                    # offline self-check
```

It does **not** infer positive selection itself (that is `mk-ascertainment` /
`convergent-evolution`); it explains *what* the set does and *how connected* it is.
ESM Atlas SAE features are an optional second opinion (`--esm`).

## From a lineage's selection signal to the affected pathways (`--from-selection`)

`--from-selection TABLE` is the lineage-level entry point: it **reads** an existing
selection result for a lineage and narrates the pathways the signal concerns. It does
not recompute the test. The table is format-tolerant (drift-tolerant column resolution,
like the data-access skills), auto-detected highest-confidence first:

- **McDonald-Kreitman output** (`mk-ascertainment`): an `alpha` (= 1 - NI) or `DoS`
  column, or the raw `Dn`/`Ds`/`Pn`/`Ps` counts (alpha + DoS are then recomputed with the
  same formulas as `mk-ascertainment`, the Fisher p via scipy if a p-value is not already
  in the table). A **significance gate** keeps a gene only if its adaptive direction is
  positive (`alpha > --alpha-min`, default 0) **and** its p clears `--max-p` (default 0.05),
  BH-FDR-corrected across genes unless `--no-fdr`. This is the mode that lets the Atlas
  write a `selection` section only when the test concluded (see below);
- a **per-gene statistic** table (a gene/`Locus_tag` column + `dN/dS` / `dnds_proxy` /
  `omega`, optionally a p-value): genes with `stat > --min-stat` (default 1.0) and
  `p < --max-p` are kept;
- a **variant-level** table (gene + `effect`/`impact`, e.g. `data/mk_input_annotated.csv`):
  non-synonymous variants are counted per gene, keeping genes with `>= --min-variants`;
- none present: every gene in the table is taken (flagged in the output `selection.mode`).

It then resolves every gene to its Rv (local-first via `mtbc-gene-function`), intersects
with each catalogue pathway, ranks the hits by how much of the pathway is hit, narrates the
top `--top` pathways in full (curated + PPI), reports whether the selected set is itself a
**cohesive PPI module** (`selected_module`), and lists off-catalogue selected genes.

```bash
# McDonald-Kreitman output, significance-gated (the canonical lineage-level use):
./run_pathway.sh --from-selection mk_per_gene.tsv --lineage L4.13 --paragraph
./run_pathway.sh --from-selection mk_per_gene.tsv --alpha-min 0.1 --no-fdr   # gate tuning

# a per-gene dN/dS or a variant-level table also work:
./run_pathway.sh --from-selection <table> --lineage L4.13 --min-variants 3 --top 3 --paragraph
./run_pathway.sh --from-selection <table> --gene-col Locus_tag --stat-col dnds_proxy --p-col fdr
```

### The significance gate (`test_concluded`)

For an MK table the output carries `gate` (`alpha_min`, `max_p`, `fdr`, `n_tested`,
`n_significant`, `n_without_p`) and a boolean `test_concluded`. `test_concluded` is `True`
only when at least one gene shows **positive** selection (`alpha > alpha_min`) at the
corrected significance threshold; otherwise it is `False` and the paragraph reads *"... did
not yield a significant per-gene signal ... No selection section should be written."* A
caller (`atlas-add-lineage`) must check `test_concluded` before drafting the `selection`
section. This enforces the *no premature publication* rule: an MK table dominated by
**negative** alpha (NI > 1, excess polymorphism / purifying selection) correctly concludes
*nothing to claim* rather than narrating a pathway. For non-MK tables `test_concluded` is
`null` (a gene list is not a test).

Caveat: at a low `--min-variants`, the variant-level mode reflects **mutational load**
(PE/PPE, PDIM) rather than strict positive selection. Prefer a gated MK table when you need
a defensible claim. This entry point is what `atlas-add-lineage` calls to draft a lineage
page's `selection` section.

## Pathway catalogue

The skill ships a small built-in catalogue of MTBC pathways, stored as
YAML in `mtbc_pathway_explain/data/pathways.yaml`. Each pathway entry
gives :

- a canonical ID (`ESX-2`, `PDIM`, …),
- a one-line description,
- the list of H37Rv locus tags / gene names that compose the pathway.

To add a pathway not yet bundled, pass a YAML file with the same schema:

```yaml
my-pathway:
  description: "Custom pathway I want to explain."
  genes:
    - katG
    - Rv1908c
```

via `--catalogue path/to/file.yaml`.

## How to use

### From a shell

```bash
/mtbc-pathway-explain ESX-2
/mtbc-pathway-explain PDIM --paragraph
/mtbc-pathway-explain my-pathway --catalogue ./pathways.yaml
```

### From Python

```python
from mtbc_pathway_explain import explain_pathway

narr = explain_pathway("ESX-2")
print(narr.paragraph)
for g in narr.genes:
    print(g["gene"], g["top_features"][:2])
```

## Outputs

```json
{
  "pathway": "ESX-2",
  "description": "Accessory type VII secretion system.",
  "n_genes_total": 12,
  "n_genes_annotated": 11,
  "n_genes_missing":  1,
  "missing": ["Rv1234"],
  "genes": [
    {
      "gene": "esxC", "locus_tag": "Rv3890c", "product": "...",
      "top_features": [...], "cluster": {...}
    }
  ],
  "common_themes": [
    "Secreted enzyme active sites",
    "Surface loops near active sites"
  ],
  "paragraph": "ESX-2 (12 H37Rv genes). ESM SAE consistently flags…"
}
```

## What this skill does not do

- It does not run the McDonald-Kreitman test. Use `mk-ascertainment`.
- It does not generate figures. Use `data-visualization` /
  `matplotlib-pro` afterwards.
- It does not draft the Atlas fiche section. The output paragraph is a
  starting point; the editor selects and rewrites for context.
- The per-gene narrative rests on ESM SAE features, which are **exploratory,
  not validated**. Before asserting a gene's domain / fold / chemistry in a
  manuscript, confirm it with **Pfam/`hmmscan --cut_ga`**, and for any
  variant on a pathway gene use the **ESM-1v LLR** (`mtbc-mutation-impact`'s
  `llr` module), not SAE feature counts (rehumanisation_L6L9L10, 2026-05-30).

## Resilience

- A pathway with all genes successfully annotated returns `n_genes_missing = 0`.
- If `mtbc-gene-function` fails for a gene (e.g. locus tag not in H37Rv
  fasta), the gene is added to `missing` and the rest of the pathway
  still gets a payload.
- ESM Atlas downtime degrades the per-gene blocks (no `top_features`,
  no `cluster`) but the pathway-level metadata still gets returned.

## Workflow alignment

```
upstream selection test  (mk-ascertainment / convergent-evolution)
       │   → a per-gene / per-variant selection table for a lineage
       ▼
this skill   mtbc-pathway-explain --from-selection <table> --lineage <id>
       │     (or directly: <pathway_id> | neighbors:GENE | gene,gene,...)
       ├─►  mtbc-gene-function   curated annotation per gene (annotation_mtbc: UniProt/EC/Pfam)
       ├─►  mtbc-gene-network    PPI cohesion of the set (STRING interactome)
       └─►  esm-atlas-cli        optional SAE second opinion (--esm)
       ▼
ranked pathway hits + per-pathway narration + paragraph
       →  atlas-add-lineage   drafts the lineage page's `selection` section
       →  manuscript "Discussion: functional implications"
```
