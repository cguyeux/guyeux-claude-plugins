---

name: scanpy
description: >-
  Scalable toolkit for single-cell gene expression analysis, built on AnnData: quality
  control, normalisation, dimensionality reduction, clustering, trajectory inference and
  plotting. Use when working with an .h5ad or AnnData object, running a single-cell RNA-seq
  pipeline (Leiden/Louvain clustering, UMAP, marker genes, pseudotime), or when the user
  mentions scanpy, AnnData, scVI or single-cell transcriptomics. For bulk expression
  matrices or general clustering, prefer scikit-learn.
license: BSD-3-Clause
---

# Scanpy - Single-Cell Analysis

Scanpy processes high-dimensional biological data, reducing it via PCA/UMAP to identify rare cell populations in tissues or microbiomes.

## When to Use

- Analyzing single-cell RNA sequencing (scRNA-seq) data.
- Identifying cell types and states in heterogeneous tissues.
- Reconstructing developmental trajectories.
- Comparing cell populations between conditions.
- Discovering rare cell types.

## Core Principles

### AnnData Format

Scanpy uses AnnData objects that store expression matrix, cell metadata, and gene annotations together.

### Dimensionality Reduction

High-dimensional gene expression (20,000+ genes) is reduced to 2D/3D for visualization (PCA → UMAP/t-SNE).

### Clustering

Cells are grouped by similarity in gene expression space to identify cell types.

## Quick Reference

### Standard Imports

```python
import scanpy as sc
import pandas as pd
import numpy as np
```

### Basic Patterns

```python
# 1. Load dataset (AnnData object)
adata = sc.read_h5ad("cells.h5ad")
# Or: adata = sc.read_10x_mtx("path/to/mtx")
adata.var_names_make_unique()          # 10x matrices contain duplicate symbols

# 2. QC: compute the metrics before filtering on them
adata.var["mt"] = adata.var_names.str.startswith(("MT-", "mt-"))
sc.pp.calculate_qc_metrics(adata, qc_vars=["mt"], inplace=True, log1p=False)
# inspect first, then choose thresholds from the distributions
sc.pl.violin(adata, ["n_genes_by_counts", "total_counts", "pct_counts_mt"],
             multi_panel=True)
adata = adata[adata.obs.pct_counts_mt < 20].copy()
sc.pp.filter_cells(adata, min_genes=200)
sc.pp.filter_genes(adata, min_cells=3)

# 3. Normalisation. Keep the normalised counts before scaling: plots and
#    differential expression must read them, not the scaled values.
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)
adata.raw = adata

# 4. Feature selection, scaling, PCA
sc.pp.highly_variable_genes(adata, n_top_genes=2000)
adata = adata[:, adata.var.highly_variable].copy()
sc.pp.scale(adata, max_value=10)
sc.tl.pca(adata, svd_solver="arpack")
sc.pl.pca_variance_ratio(adata, n_pcs=50)   # pick n_pcs from the elbow

# 5. Neighbour graph: MANDATORY before umap and leiden
sc.pp.neighbors(adata, n_neighbors=15, n_pcs=30)

# 6. Embedding and clustering
sc.tl.umap(adata)
sc.tl.leiden(adata, resolution=0.5, flavor="igraph", n_iterations=2)
sc.pl.umap(adata, color=["leiden", "gene_A"])
```

**`sc.pp.neighbors` is not optional.** Calling `sc.tl.umap` or `sc.tl.leiden`
without it fails with `KeyError: 'neighbors'`, and it is the single most common
reason a copied scanpy snippet does not run. The order is always: PCA, then
neighbours, then embedding and clustering.

Two further version notes. Since scanpy 1.10 `sc.tl.leiden` warns unless
`flavor="igraph"` is given, the default `leidenalg` path being deprecated. And
`adata.raw` is what `sc.pl.umap(color="gene")` and `sc.tl.rank_genes_groups` read
by default: setting it after log-normalisation but before scaling is what makes
expression plots show interpretable values instead of z-scores.

## Critical Rules

### ✅ DO

- **Set scanpy settings** - Use `sc.settings.verbosity = 3` for progress info.
- **Filter low-quality cells** - Remove cells with too few genes or high mitochondrial content.
- **Normalize before analysis** - Account for sequencing depth differences.
- **Use highly variable genes** - Focus analysis on informative genes.

### ❌ DON'T

- **Don't skip QC** - Low-quality cells can dominate clustering.
- **Don't use raw counts for PCA** - Always normalize and log-transform first.
- **Don't ignore batch effects** - Use batch correction (e.g., `sc.pp.harmony_integrate`) when combining datasets.

## Advanced Patterns

### Trajectory Inference

```python
import cellrank as cr

# Reconstruct developmental trajectories
sc.tl.paga(adata)
sc.pl.paga(adata)
adata.uns['iroot'] = np.flatnonzero(adata.obs['cell_type'] == 'stem')[0]
sc.tl.dpt(adata)
```

### Differential Expression

```python
# Find marker genes for each cluster
sc.tl.rank_genes_groups(adata, 'leiden', method='wilcoxon')
sc.pl.rank_genes_groups(adata, n_genes=20)
```

## Using AnnData outside single-cell work

The AnnData container (a sparse matrix plus aligned row and column metadata) and
the PCA to neighbours to Leiden to UMAP chain are not specific to transcriptomics.
They apply directly to a matrix of isolates by variants, where rows are genomes,
columns are SNPs or genes, and `obs` carries lineage, country and collection date.

```python
import anndata as ad

adata = ad.AnnData(X=snp_matrix,                     # isolates x SNPs, sparse 0/1
                   obs=metadata.set_index("strain_id"),
                   var=variants.set_index("spdi_id"))
sc.pp.pca(adata, n_comps=50)
sc.pp.neighbors(adata, metric="jaccard")             # binary data: not euclidean
sc.tl.leiden(adata, resolution=0.5, flavor="igraph")
sc.tl.umap(adata)
sc.pl.umap(adata, color=["lineage", "leiden"])
```

Three adjustments are mandatory in this register, and skipping them produces a
picture that looks convincing and means nothing:

- **Skip the transcriptomics preprocessing.** `normalize_total`, `log1p`,
  `highly_variable_genes` and `scale` all model sequencing depth. A presence
  or absence matrix has no depth, and applying them fabricates structure.
- **Change the metric.** Jaccard or Hamming on binary genotypes, not Euclidean.
- **Do not read the clusters as evolutionary groups.** Leiden on a genotype
  matrix recovers population structure, which is real, but a UMAP embedding
  distorts distances and cannot support a claim about relatedness or divergence
  order. The tree is the authority; the embedding is a display.

For the group's clustering work on strain matrices, `tsne-hdbscan` already
encodes these choices and is the intended entry point. Reach for scanpy here only
when the AnnData container itself is what you need, for instance to carry rich
per-isolate metadata alongside a large sparse matrix.

Scanpy has revolutionized single-cell biology, enabling researchers to map the cellular diversity of tissues and understand how cells differentiate and function.
