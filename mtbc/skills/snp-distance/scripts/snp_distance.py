#!/usr/bin/env python3
"""
SNP Distance Matrix Calculator

Compute pairwise SNP distance matrices from SPDI presence/absence data.
Supports binary pivot matrices and long-format strain/SPDI lists.

Usage:
    python3 snp_distance.py spdi_matrix.csv -o distances.csv --summary
    python3 snp_distance.py strain_spdi_long.csv -o distances.csv --threshold 12
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform


def detect_format(df: pd.DataFrame) -> str:
    """Detect input format: 'binary_matrix' or 'long_format'.

    Binary matrix: many columns (>10), values are 0/1.
    Long format: exactly 2 columns (strain_id, spdi_id).
    """
    if df.shape[1] == 2:
        col_names = [c.lower() for c in df.columns]
        if any("strain" in c or "sra" in c for c in col_names) and any(
            "spdi" in c or "snp" in c for c in col_names
        ):
            return "long_format"

    if df.shape[1] > 5:
        # Check if most values are 0/1
        numeric_cols = df.select_dtypes(include=[np.number])
        if numeric_cols.shape[1] > 0:
            unique_vals = set()
            for col in numeric_cols.columns[:10]:
                unique_vals.update(numeric_cols[col].dropna().unique())
            if unique_vals.issubset({0, 1, 0.0, 1.0}):
                return "binary_matrix"

    # Default: treat as binary matrix with first column as ID
    return "binary_matrix"


def load_data(input_path: str, keep_nan: bool = False) -> pd.DataFrame:
    """Load input CSV and return a presence/absence matrix.

    Index = strain_id, columns = SPDI IDs, values = 0/1 (or NaN = no-call
    when keep_nan=True, i.e. position uncovered / deleted for that strain).

    NB scientifique : coder un no-call (position non couverte ou region RD
    deletee) comme 0 = "identique a la reference" SOUS-COMPTE les distances et
    fragilise le seuil de cluster de transmission (<=12 SNP). Avec keep_nan,
    les NaN sont preserves et la metrique pairwise-complete les ignore.
    """
    df = pd.read_csv(input_path)
    fmt = detect_format(df)

    if fmt == "long_format":
        print(f"Detected long format ({df.shape[0]} rows), pivoting...", file=sys.stderr)
        strain_col, spdi_col = df.columns[0], df.columns[1]
        matrix = df.pivot_table(
            index=strain_col, columns=spdi_col, aggfunc="size", fill_value=0
        )
        matrix = (matrix > 0).astype(int)
        print(
            f"  Pivoted: {matrix.shape[0]} strains x {matrix.shape[1]} SPDIs",
            file=sys.stderr,
        )
        return matrix

    # Binary matrix: first column is strain_id
    print(
        f"Detected binary matrix: {df.shape[0]} strains x {df.shape[1] - 1} features",
        file=sys.stderr,
    )
    id_col = df.columns[0]
    matrix = df.set_index(id_col)

    # Drop non-numeric columns (e.g., lineage, group)
    non_numeric = matrix.select_dtypes(exclude=[np.number]).columns.tolist()
    if non_numeric:
        print(f"  Dropping non-numeric columns: {non_numeric}", file=sys.stderr)
        matrix = matrix.drop(columns=non_numeric)

    if keep_nan:
        n_nan = int(matrix.isna().sum().sum())
        if n_nan:
            print(f"  {n_nan} cellules no-call (NaN) preservees", file=sys.stderr)
        return matrix
    matrix = matrix.fillna(0).astype(int)
    return matrix


def compute_distance_matrix(
    matrix: pd.DataFrame, metric: str = "snp_count"
) -> pd.DataFrame:
    """Compute pairwise distance matrix.

    Args:
        matrix: Binary presence/absence matrix (strains x SPDIs).
        metric: 'snp_count' (absolute), 'hamming' (proportion), 'jaccard'.

    Returns:
        Symmetric distance matrix as DataFrame.
    """
    values = matrix.values.astype(np.float64)
    n_strains = values.shape[0]
    n_features = values.shape[1]

    print(
        f"Computing {metric} distances for {n_strains} strains "
        f"({n_features} features)...",
        file=sys.stderr,
    )

    if metric == "snp_count_pairwise_complete":
        # SNP absolus en ignorant, pour CHAQUE paire, les positions no-call
        # (NaN) chez l'une ou l'autre souche. C'est la metrique correcte quand
        # la couverture est heterogene (aDNA, regions RD deletees).
        n = n_strains
        dm = np.zeros((n, n))
        n_shared = np.zeros((n, n), dtype=int)
        for i in range(n):
            for j in range(i + 1, n):
                both = ~np.isnan(values[i]) & ~np.isnan(values[j])
                k = int(both.sum())
                d = int(np.sum(values[i][both] != values[j][both]))
                dm[i, j] = dm[j, i] = d
                n_shared[i, j] = n_shared[j, i] = k
        strain_ids = matrix.index.tolist()
        # avertissement si des paires partagent peu de positions appelees
        if n > 1:
            offdiag = n_shared[np.triu_indices(n, 1)]
            if offdiag.size and offdiag.min() < 0.5 * n_features:
                print(
                    f"  ATTENTION: certaines paires ne partagent que "
                    f"{offdiag.min()}/{n_features} positions appelees — "
                    f"distances peu comparables entre paires.",
                    file=sys.stderr,
                )
        return pd.DataFrame(dm.astype(int), index=strain_ids, columns=strain_ids)

    if metric == "snp_count":
        # Hamming distance × number of features = absolute SNP count
        # NB : traite les NaN residuels comme des valeurs -> ne pas melanger
        # avec keep_nan ; utiliser snp_count_pairwise_complete dans ce cas.
        condensed = pdist(np.nan_to_num(values), metric="hamming") * n_features
        condensed = np.round(condensed).astype(int)
    elif metric == "hamming":
        condensed = pdist(values, metric="hamming")
    elif metric == "jaccard":
        condensed = pdist(values, metric="jaccard")
        # Handle NaN from zero vectors (strains with no SPDIs)
        condensed = np.nan_to_num(condensed, nan=1.0)
    else:
        raise ValueError(f"Unknown metric: {metric}. Use snp_count, hamming, or jaccard.")

    dist_matrix = squareform(condensed)
    strain_ids = matrix.index.tolist()

    return pd.DataFrame(dist_matrix, index=strain_ids, columns=strain_ids)


def identify_clusters(dist_matrix: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """Identify transmission clusters using single-linkage on distance threshold.

    Two strains are in the same cluster if their distance ≤ threshold.
    Uses union-find for efficient clustering.
    """
    strain_ids = dist_matrix.index.tolist()
    n = len(strain_ids)

    # Union-Find
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # Build clusters
    values = dist_matrix.values
    for i in range(n):
        for j in range(i + 1, n):
            if values[i, j] <= threshold:
                union(i, j)

    # Collect clusters (skip singletons)
    from collections import defaultdict

    clusters = defaultdict(list)
    for i in range(n):
        clusters[find(i)].append(i)

    # Filter: only clusters with ≥2 members
    real_clusters = {k: v for k, v in clusters.items() if len(v) >= 2}

    if not real_clusters:
        print(f"No clusters found at threshold ≤ {threshold}", file=sys.stderr)
        return pd.DataFrame(columns=["cluster_id", "strain_id", "cluster_size", "max_distance"])

    rows = []
    for cluster_idx, (_, members) in enumerate(sorted(real_clusters.items(), key=lambda x: -len(x[1]))):
        member_ids = [strain_ids[m] for m in members]
        # Max within-cluster distance
        sub = values[np.ix_(members, members)]
        max_dist = sub.max()
        for sid in member_ids:
            rows.append({
                "cluster_id": cluster_idx,
                "strain_id": sid,
                "cluster_size": len(members),
                "max_distance": max_dist,
            })

    return pd.DataFrame(rows)


def compute_summary(
    dist_matrix: pd.DataFrame,
    metric: str,
    n_features: int,
    clusters_df: pd.DataFrame = None,
    threshold: float = None,
) -> dict:
    """Compute summary statistics."""
    values = dist_matrix.values
    # Upper triangle (excluding diagonal)
    upper = values[np.triu_indices_from(values, k=1)]

    summary = {
        "n_strains": dist_matrix.shape[0],
        "n_spdis": n_features,
        "metric": metric,
        "distance_stats": {
            "min": float(np.min(upper)) if len(upper) > 0 else 0,
            "max": float(np.max(upper)) if len(upper) > 0 else 0,
            "mean": round(float(np.mean(upper)), 2) if len(upper) > 0 else 0,
            "median": round(float(np.median(upper)), 2) if len(upper) > 0 else 0,
            "q25": round(float(np.percentile(upper, 25)), 2) if len(upper) > 0 else 0,
            "q75": round(float(np.percentile(upper, 75)), 2) if len(upper) > 0 else 0,
        },
    }

    if threshold is not None and clusters_df is not None:
        n_clustered = clusters_df["strain_id"].nunique() if not clusters_df.empty else 0
        n_clusters = clusters_df["cluster_id"].nunique() if not clusters_df.empty else 0
        largest = int(clusters_df["cluster_size"].max()) if not clusters_df.empty else 0

        summary["transmission_clusters"] = {
            "threshold": threshold,
            "n_clusters": n_clusters,
            "n_clustered_strains": n_clustered,
            "n_singletons": dist_matrix.shape[0] - n_clustered,
            "largest_cluster": largest,
        }

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Compute pairwise SNP distance matrices from SPDI data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Binary matrix → SNP count distances
  python3 snp_distance.py spdi_matrix.csv -o distances.csv --summary

  # With transmission cluster detection
  python3 snp_distance.py spdi_matrix.csv -o distances.csv \\
    --threshold 12 --clusters-output clusters.csv --summary

  # Jaccard distance for sparse data
  python3 snp_distance.py spdi_matrix.csv -o distances.csv --metric jaccard

  # Long format (auto-pivot)
  python3 snp_distance.py strain_spdi_long.csv -o distances.csv
        """,
    )

    parser.add_argument("input_file", help="Input CSV (binary matrix or long format)")
    parser.add_argument("-o", "--output", default=None, help="Output distance matrix CSV")
    parser.add_argument(
        "--metric",
        default="snp_count",
        choices=["snp_count", "snp_count_pairwise_complete", "hamming", "jaccard"],
        help="Distance metric (default: snp_count). "
             "snp_count_pairwise_complete ignore les positions no-call (NaN) "
             "par paire — recommande quand la couverture est heterogene (aDNA, RD).",
    )
    parser.add_argument(
        "--no-call",
        action="store_true",
        help="Preserver les cellules vides comme no-call (NaN) au lieu de les "
             "coder 0=reference. Implique par --metric snp_count_pairwise_complete.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="SNP threshold for cluster identification (e.g., 12)",
    )
    parser.add_argument(
        "--clusters-output",
        default=None,
        help="CSV output for identified clusters",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print summary statistics as JSON to stdout",
    )

    args = parser.parse_args()

    # no-call preserve si demande explicitement ou implique par la metrique
    keep_nan = args.no_call or args.metric == "snp_count_pairwise_complete"

    # Load and process
    matrix = load_data(args.input_file, keep_nan=keep_nan)
    n_features = matrix.shape[1]

    dist_matrix = compute_distance_matrix(matrix, args.metric)

    # Save distance matrix
    if args.output:
        dist_matrix.index.name = "id"
        dist_matrix.to_csv(args.output)
        print(
            f"Distance matrix saved: {args.output} "
            f"({dist_matrix.shape[0]}x{dist_matrix.shape[1]})",
            file=sys.stderr,
        )
    else:
        dist_matrix.index.name = "id"
        dist_matrix.to_csv(sys.stdout)

    # Cluster identification
    clusters_df = None
    if args.threshold is not None:
        clusters_df = identify_clusters(dist_matrix, args.threshold)
        if args.clusters_output and not clusters_df.empty:
            clusters_df.to_csv(args.clusters_output, index=False)
            print(
                f"Clusters saved: {args.clusters_output} "
                f"({clusters_df['cluster_id'].nunique()} clusters, "
                f"{clusters_df['strain_id'].nunique()} strains)",
                file=sys.stderr,
            )

    # Summary
    if args.summary:
        summary = compute_summary(
            dist_matrix, args.metric, n_features, clusters_df, args.threshold
        )
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
