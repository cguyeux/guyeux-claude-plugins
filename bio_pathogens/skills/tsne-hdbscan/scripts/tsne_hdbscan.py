#!/usr/bin/env python3
"""
t-SNE + HDBSCAN for MTBC Genomic Analysis

Dimensionality reduction (t-SNE) and density-based clustering (HDBSCAN)
for exploring M. tuberculosis complex genomic diversity from SNP profiles,
SPDI presence/absence matrices, or MIRU-VNTR haplotypes.

Dependencies: numpy, scipy, scikit-learn, hdbscan, matplotlib, pandas
"""

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

try:
    from sklearn.manifold import TSNE
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score
except ImportError:
    print("Error: scikit-learn required. pip install scikit-learn", file=sys.stderr)
    sys.exit(1)

try:
    import hdbscan
except ImportError:
    print("Error: hdbscan required. pip install hdbscan", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def detect_format(filepath: str) -> str:
    """Auto-detect input format: distance_matrix, binary_matrix, or haplotype_matrix."""
    with open(filepath) as f:
        reader = csv.reader(f)
        header = next(reader)
        first_row = next(reader)

    data_vals = first_row[1:]

    # Distance matrix: symmetric, first value is 0
    try:
        vals = [float(v) for v in data_vals]
        if len(vals) > 0 and vals[0] == 0.0:
            return "distance_matrix"
    except ValueError:
        pass

    # Binary matrix: all values are 0 or 1
    try:
        vals = [int(v) for v in data_vals if v.strip()]
        if all(v in (0, 1) for v in vals) and len(vals) > 10:
            return "binary_matrix"
    except ValueError:
        pass

    return "haplotype_matrix"


def load_data(filepath: str, fmt: str = "auto", group_column: str = None):
    """Load input data.

    Returns:
        ids: list of strain identifiers
        data: numpy array (n_samples x n_features) or distance matrix
        groups: list of group labels or None
        is_distance: True if data is a precomputed distance matrix
    """
    with open(filepath) as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    if fmt == "auto":
        fmt = detect_format(filepath)
        print(f"Auto-detected format: {fmt}", file=sys.stderr)

    ids = [r[0] for r in rows]

    # Extract groups if specified
    groups = None
    group_idx = None
    if group_column:
        try:
            group_idx = header.index(group_column)
            groups = [r[group_idx] for r in rows]
        except ValueError:
            print(f"Warning: group column '{group_column}' not found", file=sys.stderr)

    if fmt == "distance_matrix":
        data = np.array([[float(x) for x in r[1:]] for r in rows], dtype=np.float64)
        return ids, data, groups, True

    # Feature matrix: skip id and group columns
    skip = {0}
    if group_idx is not None:
        skip.add(group_idx)

    col_indices = [i for i in range(len(header)) if i not in skip]
    data = []
    for r in rows:
        row = []
        for ci in col_indices:
            val = r[ci].strip() if ci < len(r) else ""
            if val in ("", "NA", "nan", "?", "-"):
                row.append(np.nan)
            else:
                try:
                    row.append(float(val))
                except ValueError:
                    row.append(np.nan)
        data.append(row)

    data = np.array(data, dtype=np.float64)
    is_distance = False
    return ids, data, groups, is_distance


def impute_missing(data: np.ndarray) -> np.ndarray:
    """Replace NaN with column median (simple imputation for genomic data)."""
    result = data.copy()
    for j in range(result.shape[1]):
        col = result[:, j]
        mask = np.isnan(col)
        if np.any(mask):
            median = np.nanmedian(col)
            result[mask, j] = median
    return result


def compute_distance_matrix(data: np.ndarray, metric: str = "hamming") -> np.ndarray:
    """Compute pairwise distance matrix from feature matrix."""
    from scipy.spatial.distance import pdist, squareform

    if metric == "hamming":
        # For integer/categorical data: proportion of differing features
        dist = pdist(data, metric="hamming")
    elif metric == "euclidean":
        dist = pdist(data, metric="euclidean")
    elif metric == "jaccard":
        # For binary data
        dist = pdist(data, metric="jaccard")
    else:
        dist = pdist(data, metric=metric)

    return squareform(dist)


# ---------------------------------------------------------------------------
# t-SNE
# ---------------------------------------------------------------------------

def run_tsne(
    data: np.ndarray,
    is_distance: bool = False,
    perplexity: float = 30.0,
    learning_rate: float = 200.0,
    n_iter: int = 1000,
    random_state: int = 42,
    n_components: int = 2,
    early_exaggeration: float = 12.0,
    init: str = "pca",
) -> np.ndarray:
    """Run t-SNE dimensionality reduction.

    Args:
        data: Feature matrix (n x p) or distance matrix (n x n).
        is_distance: If True, data is a precomputed distance matrix.
        perplexity: Balance between local and global structure (5-50).
        learning_rate: Usually 10-1000.
        n_iter: Number of optimization iterations (≥250).
        random_state: For reproducibility.

    Returns:
        2D embedding array (n x 2).
    """
    metric = "precomputed" if is_distance else "euclidean"

    if is_distance:
        init_method = "random"  # PCA init not available for precomputed
    else:
        init_method = init

    # scikit-learn >= 1.6 renamed n_iter to max_iter
    import inspect
    tsne_params = inspect.signature(TSNE.__init__).parameters
    iter_key = "max_iter" if "max_iter" in tsne_params else "n_iter"

    tsne = TSNE(
        n_components=n_components,
        perplexity=perplexity,
        learning_rate=learning_rate,
        random_state=random_state,
        metric=metric,
        init=init_method,
        early_exaggeration=early_exaggeration,
        **{iter_key: n_iter},
    )

    embedding = tsne.fit_transform(data)
    return embedding


# ---------------------------------------------------------------------------
# HDBSCAN
# ---------------------------------------------------------------------------

def run_hdbscan(
    data: np.ndarray,
    is_distance: bool = False,
    min_cluster_size: int = 5,
    min_samples: int = None,
    cluster_selection_epsilon: float = 0.0,
    cluster_selection_method: str = "eom",
    allow_single_cluster: bool = False,
) -> dict:
    """Run HDBSCAN clustering.

    Can run on the t-SNE embedding (2D) or on the original distance/feature matrix.

    Args:
        data: Feature matrix, distance matrix, or t-SNE embedding.
        is_distance: If True, data is a precomputed distance matrix.
        min_cluster_size: Minimum number of samples in a cluster.
        min_samples: Minimum samples in a neighborhood. Defaults to min_cluster_size.
        cluster_selection_epsilon: Merge clusters closer than this distance.
        cluster_selection_method: "eom" (Excess of Mass) or "leaf".
        allow_single_cluster: Allow all points in one cluster.

    Returns:
        Dict with labels, probabilities, n_clusters, noise_count, outlier_scores.
    """
    metric = "precomputed" if is_distance else "euclidean"

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric=metric,
        cluster_selection_epsilon=cluster_selection_epsilon,
        cluster_selection_method=cluster_selection_method,
        allow_single_cluster=allow_single_cluster,
    )

    clusterer.fit(data)

    labels = clusterer.labels_
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    noise_count = int(np.sum(labels == -1))

    result = {
        "labels": labels.tolist(),
        "probabilities": clusterer.probabilities_.tolist(),
        "n_clusters": n_clusters,
        "noise_count": noise_count,
        "noise_ratio": round(noise_count / len(labels), 4),
    }

    # Outlier scores
    if hasattr(clusterer, "outlier_scores_") and clusterer.outlier_scores_ is not None:
        result["outlier_scores"] = clusterer.outlier_scores_.tolist()

    # Silhouette score (if >1 cluster and not all noise)
    if n_clusters > 1 and noise_count < len(labels):
        non_noise = labels != -1
        if np.sum(non_noise) > n_clusters:
            sil = silhouette_score(
                data[non_noise],
                labels[non_noise],
                metric="precomputed" if is_distance else "euclidean",
            )
            result["silhouette_score"] = round(float(sil), 4)

    return result


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------

def generate_plot(
    embedding: np.ndarray,
    ids: list,
    labels: list = None,
    groups: list = None,
    probabilities: list = None,
    output_path: str = "tsne_plot.png",
    title: str = "t-SNE + HDBSCAN",
    show_labels: bool = False,
    colormap: dict = None,
    figsize: tuple = (14, 6),
):
    """Generate publication-quality t-SNE plot with cluster coloring.

    Creates 1 or 2 panels:
    - Left: colored by HDBSCAN cluster (or uniform if no clustering)
    - Right: colored by group/lineage (if groups provided)
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.colors import to_rgba
    except ImportError:
        print("Warning: matplotlib not available, skipping plot.", file=sys.stderr)
        return

    n_panels = 2 if groups is not None else 1
    fig, axes = plt.subplots(1, n_panels, figsize=figsize, squeeze=False)

    x, y = embedding[:, 0], embedding[:, 1]

    # Panel 1: HDBSCAN clusters
    ax1 = axes[0, 0]
    if labels is not None:
        unique_labels = sorted(set(labels))
        # Color palette: noise = gray, clusters = tab10
        cmap = plt.cm.tab10
        colors = []
        for l in labels:
            if l == -1:
                colors.append((0.7, 0.7, 0.7, 0.5))
            else:
                colors.append(cmap(l % 10))

        ax1.scatter(x, y, c=colors, s=15, edgecolors="none")

        # Legend for clusters
        for l in unique_labels:
            if l == -1:
                c = (0.7, 0.7, 0.7, 1.0)
                label = f"Noise ({sum(1 for ll in labels if ll == -1)})"
            else:
                c = cmap(l % 10)
                label = f"Cluster {l} ({sum(1 for ll in labels if ll == l)})"
            ax1.scatter([], [], c=[c], s=30, label=label)
        ax1.legend(fontsize=7, loc="best", framealpha=0.8)
    else:
        ax1.scatter(x, y, c="steelblue", s=15, edgecolors="none")

    ax1.set_title("HDBSCAN Clusters", fontsize=11)
    ax1.set_xlabel("t-SNE 1", fontsize=9)
    ax1.set_ylabel("t-SNE 2", fontsize=9)
    ax1.tick_params(labelsize=8)

    # Panel 2: Groups/lineages
    if groups is not None:
        ax2 = axes[0, 1]
        unique_groups = sorted(set(groups))

        if colormap:
            group_colors = {g: colormap.get(g, "#9E9E9E") for g in unique_groups}
        else:
            cmap_g = plt.cm.tab20
            group_colors = {g: cmap_g(i % 20) for i, g in enumerate(unique_groups)}

        colors_g = [group_colors[g] for g in groups]
        ax2.scatter(x, y, c=colors_g, s=15, edgecolors="none")

        for g in unique_groups:
            c = group_colors[g]
            n = sum(1 for gg in groups if gg == g)
            ax2.scatter([], [], c=[c], s=30, label=f"{g} ({n})")
        ax2.legend(fontsize=7, loc="best", framealpha=0.8, ncol=max(1, len(unique_groups) // 15))

        ax2.set_title("Lineage", fontsize=11)
        ax2.set_xlabel("t-SNE 1", fontsize=9)
        ax2.set_ylabel("t-SNE 2", fontsize=9)
        ax2.tick_params(labelsize=8)

    # Optional strain labels
    if show_labels and len(ids) <= 100:
        for ax in axes[0]:
            for i, sid in enumerate(ids):
                ax.annotate(sid, (x[i], y[i]), fontsize=4, alpha=0.6)

    plt.suptitle(title, fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Plot saved to {output_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_output(
    ids: list,
    embedding: np.ndarray,
    cluster_result: dict,
    groups: list,
    output_path: str,
):
    """Write results to CSV."""
    labels = cluster_result.get("labels", [None] * len(ids))
    probs = cluster_result.get("probabilities", [None] * len(ids))
    outliers = cluster_result.get("outlier_scores", [None] * len(ids))

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        header = ["strain_id", "tsne_1", "tsne_2", "cluster", "cluster_probability"]
        if groups is not None:
            header.insert(1, "group")
        if outliers[0] is not None:
            header.append("outlier_score")
        writer.writerow(header)

        for i in range(len(ids)):
            row = [ids[i]]
            if groups is not None:
                row.append(groups[i])
            row.extend([
                f"{embedding[i, 0]:.6f}",
                f"{embedding[i, 1]:.6f}",
                labels[i],
                f"{probs[i]:.4f}" if probs[i] is not None else "",
            ])
            if outliers[0] is not None:
                row.append(f"{outliers[i]:.4f}" if outliers[i] is not None else "")
            writer.writerow(row)

    print(f"Results written to {output_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(
    filepath: str,
    fmt: str = "auto",
    group_column: str = None,
    distance_metric: str = "hamming",
    # t-SNE params
    perplexity: float = 30.0,
    learning_rate: float = 200.0,
    n_iter: int = 1000,
    random_state: int = 42,
    # HDBSCAN params
    min_cluster_size: int = 5,
    min_samples: int = None,
    cluster_on: str = "embedding",
    cluster_selection_method: str = "eom",
    cluster_selection_epsilon: float = 0.0,
    allow_single_cluster: bool = False,
    # Output
    output_csv: str = None,
    plot_path: str = None,
    plot_title: str = "t-SNE + HDBSCAN",
    show_labels: bool = False,
    lineage_colors: str = None,
):
    """Run the full t-SNE + HDBSCAN pipeline.

    Args:
        cluster_on: "embedding" (cluster on t-SNE 2D) or "original" (cluster on full data).
        lineage_colors: Path to JSON file with {lineage: hex_color} mapping.
    """
    # Load
    ids, data, groups, is_distance = load_data(filepath, fmt, group_column)
    n, p = data.shape
    print(f"Loaded {n} samples, {'distance matrix' if is_distance else f'{p} features'}", file=sys.stderr)

    # Handle missing values
    if not is_distance:
        nan_count = np.sum(np.isnan(data))
        if nan_count > 0:
            print(f"Imputing {nan_count} missing values (column median)", file=sys.stderr)
            data = impute_missing(data)

    # Auto-adjust perplexity
    max_perplexity = max(5.0, (n - 1) / 3.0)
    if perplexity > max_perplexity:
        print(f"Adjusting perplexity {perplexity} -> {max_perplexity:.0f} (n={n})", file=sys.stderr)
        perplexity = max_perplexity

    # Compute distance matrix if needed for t-SNE on distances
    if not is_distance and distance_metric != "euclidean":
        print(f"Computing {distance_metric} distance matrix...", file=sys.stderr)
        dist_matrix = compute_distance_matrix(data, distance_metric)
        tsne_input = dist_matrix
        tsne_is_distance = True
    elif is_distance:
        dist_matrix = data
        tsne_input = data
        tsne_is_distance = True
    else:
        tsne_input = StandardScaler().fit_transform(data)
        tsne_is_distance = False
        dist_matrix = None

    # t-SNE
    print(f"Running t-SNE (perplexity={perplexity}, n_iter={n_iter})...", file=sys.stderr)
    embedding = run_tsne(
        tsne_input,
        is_distance=tsne_is_distance,
        perplexity=perplexity,
        learning_rate=learning_rate,
        n_iter=n_iter,
        random_state=random_state,
    )

    # HDBSCAN
    if cluster_on == "embedding":
        hdb_input = embedding
        hdb_is_distance = False
    else:
        hdb_input = dist_matrix if dist_matrix is not None else data
        hdb_is_distance = dist_matrix is not None

    # Auto-adjust min_cluster_size
    effective_min_cluster = min(min_cluster_size, max(2, n // 10))
    if effective_min_cluster != min_cluster_size:
        print(f"Adjusting min_cluster_size {min_cluster_size} -> {effective_min_cluster}", file=sys.stderr)

    print(f"Running HDBSCAN (min_cluster_size={effective_min_cluster}, method={cluster_selection_method})...", file=sys.stderr)
    cluster_result = run_hdbscan(
        hdb_input,
        is_distance=hdb_is_distance,
        min_cluster_size=effective_min_cluster,
        min_samples=min_samples,
        cluster_selection_epsilon=cluster_selection_epsilon,
        cluster_selection_method=cluster_selection_method,
        allow_single_cluster=allow_single_cluster,
    )

    print(f"Found {cluster_result['n_clusters']} clusters, "
          f"{cluster_result['noise_count']} noise points "
          f"({cluster_result['noise_ratio']*100:.1f}%)", file=sys.stderr)
    if "silhouette_score" in cluster_result:
        print(f"Silhouette score: {cluster_result['silhouette_score']}", file=sys.stderr)

    # Cluster size distribution
    labels = cluster_result["labels"]
    cluster_sizes = {}
    for l in labels:
        cluster_sizes[l] = cluster_sizes.get(l, 0) + 1

    # Output CSV
    if output_csv:
        write_output(ids, embedding, cluster_result, groups, output_csv)

    # Plot
    if plot_path:
        colormap = None
        if lineage_colors:
            with open(lineage_colors) as f:
                colormap = json.load(f)

        generate_plot(
            embedding, ids,
            labels=labels,
            groups=groups,
            probabilities=cluster_result.get("probabilities"),
            output_path=plot_path,
            title=plot_title,
            show_labels=show_labels,
            colormap=colormap,
        )

    # Summary
    summary = {
        "n_samples": n,
        "n_features": p if not is_distance else f"{n}x{n} distance",
        "tsne": {
            "perplexity": perplexity,
            "learning_rate": learning_rate,
            "n_iter": n_iter,
        },
        "hdbscan": {
            "min_cluster_size": effective_min_cluster,
            "min_samples": min_samples,
            "cluster_on": cluster_on,
            "method": cluster_selection_method,
            "n_clusters": cluster_result["n_clusters"],
            "noise_count": cluster_result["noise_count"],
            "noise_ratio": cluster_result["noise_ratio"],
            "cluster_sizes": {
                str(k): v for k, v in sorted(cluster_sizes.items()) if k != -1
            },
        },
    }
    if "silhouette_score" in cluster_result:
        summary["hdbscan"]["silhouette_score"] = cluster_result["silhouette_score"]

    # Cross-tabulation with groups
    if groups is not None:
        crosstab = {}
        for g, l in zip(groups, labels):
            key = f"cluster_{l}" if l != -1 else "noise"
            if key not in crosstab:
                crosstab[key] = {}
            crosstab[key][g] = crosstab[key].get(g, 0) + 1
        summary["crosstab_cluster_vs_group"] = crosstab

    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="t-SNE + HDBSCAN for MTBC genomic analysis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Binary SPDI matrix, auto-detect
  python tsne_hdbscan.py spdi_matrix.csv -g lineage -o results.csv -p plot.png

  # Distance matrix with custom perplexity
  python tsne_hdbscan.py distances.csv -f distance_matrix --perplexity 50 -o results.csv

  # MIRU-VNTR with Hamming distance
  python tsne_hdbscan.py miru.csv --metric hamming --min-cluster-size 10 -p plot.png

  # Cluster on original data (not embedding)
  python tsne_hdbscan.py data.csv --cluster-on original -o results.csv -p plot.png
        """,
    )

    parser.add_argument("input_file", help="Input CSV (features, distances, or binary matrix)")
    parser.add_argument("--format", "-f", choices=["auto", "distance_matrix", "binary_matrix", "haplotype_matrix"],
                        default="auto")
    parser.add_argument("--group-column", "-g", default=None, help="Column for group coloring (e.g. lineage)")
    parser.add_argument("--metric", default="hamming", help="Distance metric (hamming, jaccard, euclidean)")

    # t-SNE
    tsne_g = parser.add_argument_group("t-SNE parameters")
    tsne_g.add_argument("--perplexity", type=float, default=30.0, help="Perplexity (5-50, default: 30)")
    tsne_g.add_argument("--learning-rate", type=float, default=200.0)
    tsne_g.add_argument("--n-iter", type=int, default=1000, help="Number of iterations (default: 1000)")
    tsne_g.add_argument("--seed", type=int, default=42, help="Random seed")

    # HDBSCAN
    hdb_g = parser.add_argument_group("HDBSCAN parameters")
    hdb_g.add_argument("--min-cluster-size", type=int, default=5)
    hdb_g.add_argument("--min-samples", type=int, default=None)
    hdb_g.add_argument("--cluster-on", choices=["embedding", "original"], default="embedding",
                       help="Cluster on t-SNE 2D or original data")
    hdb_g.add_argument("--cluster-method", choices=["eom", "leaf"], default="eom",
                       help="eom=Excess of Mass, leaf=leaf nodes")
    hdb_g.add_argument("--epsilon", type=float, default=0.0, help="Merge clusters closer than epsilon")
    hdb_g.add_argument("--allow-single", action="store_true", help="Allow single cluster")

    # Output
    out_g = parser.add_argument_group("Output")
    out_g.add_argument("--output", "-o", default=None, help="Output CSV path")
    out_g.add_argument("--plot", "-p", default=None, help="Output plot path (PNG/PDF)")
    out_g.add_argument("--title", default="t-SNE + HDBSCAN", help="Plot title")
    out_g.add_argument("--show-labels", action="store_true", help="Show strain IDs on plot (≤100)")
    out_g.add_argument("--lineage-colors", default=None, help="JSON file with lineage->color mapping")

    args = parser.parse_args()

    if not Path(args.input_file).exists():
        print(f"Error: file '{args.input_file}' not found.", file=sys.stderr)
        sys.exit(1)

    summary = run_pipeline(
        filepath=args.input_file,
        fmt=args.format,
        group_column=args.group_column,
        distance_metric=args.metric,
        perplexity=args.perplexity,
        learning_rate=args.learning_rate,
        n_iter=args.n_iter,
        random_state=args.seed,
        min_cluster_size=args.min_cluster_size,
        min_samples=args.min_samples,
        cluster_on=args.cluster_on,
        cluster_selection_method=args.cluster_method,
        cluster_selection_epsilon=args.epsilon,
        allow_single_cluster=args.allow_single,
        output_csv=args.output,
        plot_path=args.plot,
        plot_title=args.title,
        show_labels=args.show_labels,
        lineage_colors=args.lineage_colors,
    )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
