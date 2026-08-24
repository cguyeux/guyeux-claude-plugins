#!/usr/bin/env python3
"""
Time-scaled Haplotypic Density (THD) Calculator

Implementation of the THD method from:
Rasigade et al. "Strain-specific estimation of epidemic success provides
insights into the transmission dynamics of tuberculosis"
Scientific Reports 7:45326 (2017). DOI: 10.1038/srep45326

Computes kernel density estimates on pairwise genetic distances using a
truncated geometric distribution, parameterized by a biologically meaningful
timescale (TMRCA50).
"""

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

try:
    from scipy.optimize import brentq
except ImportError:
    brentq = None


# ---------------------------------------------------------------------------
# Core mathematical functions
# ---------------------------------------------------------------------------

def compute_h50(t50: float, mu: float, m: int) -> float:
    """Compute median genetic distance h50 from timescale t50 via IAM.

    Under the Infinite Alleles Model:
        h50 = (1 - exp(-2 * mu * t50)) * m

    Args:
        t50: Timescale in years (TMRCA50).
        mu: Evolutionary rate (changes per locus per year).
        m: Number of markers (loci).

    Returns:
        Median genetic distance (possibly non-integer).
    """
    return (1.0 - math.exp(-2.0 * mu * t50)) * m


def solve_bandwidth(h50: float, m: int, tol: float = 1e-12) -> float:
    """Find bandwidth b* satisfying the median equation.

    Solves: (1 - b^h50) / (1 - b^m) = 1/2
    Rearranged: f(b) = (1 - b^h50) / (1 - b^m) - 0.5 = 0

    Args:
        h50: Median distance from compute_h50.
        m: Number of markers.
        tol: Tolerance for root-finding.

    Returns:
        Bandwidth b* in (0, 1).

    Raises:
        ValueError: If h50 is out of valid range or scipy is unavailable.
    """
    if brentq is None:
        raise ImportError(
            "scipy is required for bandwidth solving. "
            "Install with: pip install scipy"
        )

    if h50 <= 0:
        raise ValueError(f"h50 must be positive, got {h50:.6f}")
    if h50 >= m:
        raise ValueError(
            f"h50 ({h50:.4f}) must be < m ({m}). "
            f"Timescale too large for this number of markers."
        )

    def equation(b):
        # (1 - b^h50) / (1 - b^m) - 0.5
        # Use log-space for numerical stability
        b_h50 = math.pow(b, h50)
        b_m = math.pow(b, m)
        return (1.0 - b_h50) / (1.0 - b_m) - 0.5

    b_star = brentq(equation, 1e-15, 1.0 - 1e-15, xtol=tol)
    return b_star


def kernel_density(h: np.ndarray, b: float, m: int) -> np.ndarray:
    """Compute kernel density under the truncated geometric distribution.

    k(h|b,m) = ((1-b) / (1 - b^(m+1))) * b^h

    Args:
        h: Array of genetic distances (integers >= 0).
        b: Bandwidth parameter.
        m: Number of markers (truncation limit).

    Returns:
        Array of kernel density values.
    """
    log_b = math.log(b)
    log_norm = math.log(1.0 - b) - math.log(1.0 - math.pow(b, m + 1))
    log_k = log_norm + h.astype(np.float64) * log_b
    return np.exp(log_k)


def hamming_distance_matrix(data: np.ndarray) -> np.ndarray:
    """Compute pairwise Hamming distances (number of differing alleles).

    Handles NaN values by ignoring missing positions in each pair.

    Args:
        data: 2D array of shape (n_isolates, n_markers).

    Returns:
        Symmetric distance matrix of shape (n_isolates, n_isolates).
    """
    n = data.shape[0]
    dist = np.zeros((n, n), dtype=np.float64)

    has_nan = np.any(np.isnan(data))

    if not has_nan:
        # Fast path: no missing data
        for i in range(n):
            for j in range(i + 1, n):
                d = np.sum(data[i] != data[j])
                dist[i, j] = d
                dist[j, i] = d
    else:
        # Slow path: ignore NaN positions per pair
        for i in range(n):
            for j in range(i + 1, n):
                valid = ~(np.isnan(data[i]) | np.isnan(data[j]))
                if np.any(valid):
                    d = np.sum(data[i, valid] != data[j, valid])
                else:
                    d = np.nan
                dist[i, j] = d
                dist[j, i] = d

    return dist


def compute_thd(dist_matrix: np.ndarray, b: float, m: int) -> np.ndarray:
    """Compute THD for each isolate.

    THD_i = (1/n) * sum_j kernel(d_ij, b, m) for all j (including j=i).

    Args:
        dist_matrix: Pairwise distance matrix (n x n).
        b: Bandwidth parameter.
        m: Number of markers.

    Returns:
        Array of THD values, one per isolate.
    """
    n = dist_matrix.shape[0]
    thd = np.zeros(n, dtype=np.float64)

    for i in range(n):
        distances = dist_matrix[i, :]
        valid = ~np.isnan(distances)
        if np.any(valid):
            densities = kernel_density(distances[valid], b, m)
            thd[i] = np.mean(densities)
        else:
            thd[i] = np.nan

    return thd


def scale_thd(thd: np.ndarray, m: int) -> np.ndarray:
    """Scale THD by number of markers for cross-method comparability."""
    return thd * m


def log_thd(thd: np.ndarray) -> np.ndarray:
    """Log-transform THD values. Handles zeros by replacing with NaN."""
    with np.errstate(divide="ignore"):
        result = np.log(thd)
    result[np.isinf(result)] = np.nan
    return result


def normalize_thd(log_thd_values: np.ndarray) -> np.ndarray:
    """Normalize log-THD as Z-scores relative to the population."""
    valid = ~np.isnan(log_thd_values)
    if np.sum(valid) < 2:
        return np.full_like(log_thd_values, np.nan)
    mean = np.nanmean(log_thd_values)
    std = np.nanstd(log_thd_values, ddof=1)
    if std == 0:
        return np.zeros_like(log_thd_values)
    return (log_thd_values - mean) / std


# ---------------------------------------------------------------------------
# Input loading
# ---------------------------------------------------------------------------

def detect_format(filepath: str) -> str:
    """Auto-detect whether input is a haplotype matrix or distance matrix."""
    with open(filepath, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        first_row = next(reader)

    # If header[0] matches first_row[0] pattern and matrix is square-ish,
    # likely a distance matrix. Otherwise, haplotype matrix.
    n_cols = len(header)
    n_data_cols = len(first_row)

    # Distance matrix: first column is ID, remaining are numeric,
    # and header has same IDs as first column values
    try:
        values = [float(x) for x in first_row[1:]]
        # Check if diagonal-like (first value after ID is 0)
        if len(values) > 0 and values[0] == 0.0:
            return "distance_matrix"
    except (ValueError, IndexError):
        pass

    return "haplotype_matrix"


def load_haplotype_matrix(filepath: str, group_column: str = None):
    """Load a CSV haplotype matrix.

    Expected format: first column = isolate ID, remaining columns = loci.
    Optional group column for within-group THD.

    Returns:
        ids: List of isolate identifiers.
        data: numpy array (n_isolates x n_markers).
        m: Number of markers.
        groups: List of group labels (or None).
    """
    with open(filepath, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    ids = [r[0] for r in rows]

    # Identify group column index if specified
    group_idx = None
    groups = None
    if group_column:
        try:
            group_idx = header.index(group_column)
            groups = [r[group_idx] for r in rows]
        except ValueError:
            print(
                f"Warning: group column '{group_column}' not found in header. "
                f"Available columns: {header}",
                file=sys.stderr,
            )

    # Data columns: everything except ID and group
    skip_cols = {0}
    if group_idx is not None:
        skip_cols.add(group_idx)

    data_cols = [i for i in range(len(header)) if i not in skip_cols]
    data = []
    for r in rows:
        row_data = []
        for ci in data_cols:
            val = r[ci].strip()
            if val == "" or val.lower() in ("na", "nan", "?", "-"):
                row_data.append(np.nan)
            else:
                try:
                    row_data.append(float(val))
                except ValueError:
                    row_data.append(np.nan)
        data.append(row_data)

    data = np.array(data, dtype=np.float64)
    m = data.shape[1]

    return ids, data, m, groups


def load_distance_matrix(filepath: str, group_column: str = None):
    """Load a pre-computed distance matrix.

    Expected format: symmetric CSV with IDs in first row and first column.

    Returns:
        ids: List of isolate identifiers.
        dist_matrix: numpy distance matrix.
        groups: None (not supported for distance matrices without separate metadata).
    """
    with open(filepath, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    ids = [r[0] for r in rows]
    dist = np.array(
        [[float(x) for x in r[1:]] for r in rows],
        dtype=np.float64,
    )

    return ids, dist, None


# ---------------------------------------------------------------------------
# Main computation pipeline
# ---------------------------------------------------------------------------

def run_thd(
    filepath: str,
    timescales: list,
    mu: float,
    markers: int = None,
    input_format: str = "auto",
    group_column: str = None,
    do_normalize: bool = False,
    output_path: str = None,
    plot_path: str = None,
):
    """Run the full THD computation pipeline.

    Args:
        filepath: Path to input CSV file.
        timescales: List of timescales in years (e.g., [20, 200]).
        mu: Evolutionary rate (changes/locus/year).
        markers: Number of markers (auto-detected for haplotype matrices).
        input_format: "auto", "haplotype_matrix", or "distance_matrix".
        group_column: Column name for within-group THD (haplotype matrix only).
        do_normalize: Whether to compute normalized (Z-score) THD.
        output_path: Path for output CSV (default: stdout summary only).
        plot_path: Path for diagnostic plot (requires matplotlib).

    Returns:
        Dictionary with results and metadata.
    """
    # Step 1: Load input
    if input_format == "auto":
        input_format = detect_format(filepath)
        print(f"Auto-detected format: {input_format}", file=sys.stderr)

    if input_format == "haplotype_matrix":
        ids, data, m_detected, groups = load_haplotype_matrix(
            filepath, group_column
        )
        if markers is not None:
            m = markers
            if m != m_detected:
                print(
                    f"Warning: --markers={m} overrides detected {m_detected} loci",
                    file=sys.stderr,
                )
        else:
            m = m_detected

        # Check for ambiguous profiles
        nan_counts = np.sum(np.isnan(data), axis=1)
        if np.any(nan_counts > 0):
            n_ambiguous = np.sum(nan_counts > 0)
            print(
                f"Warning: {n_ambiguous} isolates have missing alleles. "
                f"Distances will be computed on available loci.",
                file=sys.stderr,
            )

        # Step 2: Compute distance matrix
        dist_matrix = hamming_distance_matrix(data)

    elif input_format == "distance_matrix":
        ids, dist_matrix, groups = load_distance_matrix(filepath, group_column)
        if markers is None:
            print(
                "Error: --markers is required for distance matrix input.",
                file=sys.stderr,
            )
            sys.exit(1)
        m = markers
    else:
        print(f"Error: unknown format '{input_format}'", file=sys.stderr)
        sys.exit(1)

    n = len(ids)
    print(f"Loaded {n} isolates, m={m} markers", file=sys.stderr)

    # Step 3-6: Compute THD for each timescale
    results = {"isolate_id": ids}
    if groups is not None:
        results["group"] = groups

    summary = {
        "n_isolates": n,
        "n_markers": m,
        "mu": mu,
        "timescales": {},
    }

    for t50 in timescales:
        # Step 3: Parameters
        h50 = compute_h50(t50, mu, m)

        # Validate h50
        if h50 >= m / 3:
            print(
                f"Warning: h50={h50:.4f} >= m/3={m/3:.1f} for t50={t50}y. "
                f"Homoplasy may bias results. Consider a shorter timescale.",
                file=sys.stderr,
            )

        if h50 >= m:
            print(
                f"Error: h50={h50:.4f} >= m={m} for t50={t50}y. "
                f"Timescale too large for this number of markers.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Step 4: Bandwidth
        b_star = solve_bandwidth(h50, m)

        print(
            f"Timescale t50={t50}y: h50={h50:.4f}, b*={b_star:.6f}",
            file=sys.stderr,
        )

        # Step 5: Global THD
        thd_values = compute_thd(dist_matrix, b_star, m)

        # Step 6: Scaling and transforms
        scaled = scale_thd(thd_values, m)
        log_vals = log_thd(thd_values)

        t_label = str(int(t50))
        results[f"thd_{t_label}"] = thd_values.tolist()
        results[f"scaled_thd_{t_label}"] = scaled.tolist()
        results[f"log_thd_{t_label}"] = log_vals.tolist()

        if do_normalize:
            norm = normalize_thd(log_vals)
            results[f"normalized_thd_{t_label}"] = norm.tolist()

        # Within-group THD
        if groups is not None:
            unique_groups = sorted(set(groups))
            wg_thd = np.full(n, np.nan)
            for grp in unique_groups:
                mask = np.array([g == grp for g in groups])
                idx = np.where(mask)[0]
                if len(idx) < 2:
                    continue
                sub_dist = dist_matrix[np.ix_(idx, idx)]
                sub_thd = compute_thd(sub_dist, b_star, m)
                for k, i in enumerate(idx):
                    wg_thd[i] = sub_thd[k]

            results[f"within_group_thd_{t_label}"] = wg_thd.tolist()
            wg_log = log_thd(wg_thd)
            results[f"within_group_log_thd_{t_label}"] = wg_log.tolist()

        # Summary statistics
        valid_thd = thd_values[~np.isnan(thd_values)]
        valid_log = log_vals[~np.isnan(log_vals)]
        summary["timescales"][t_label] = {
            "t50_years": t50,
            "h50": round(h50, 6),
            "bandwidth_b_star": round(b_star, 8),
            "thd_geometric_mean": round(
                float(np.exp(np.mean(valid_log))), 8
            ) if len(valid_log) > 0 else None,
            "scaled_thd_geometric_mean": round(
                float(np.exp(np.mean(valid_log)) * m), 8
            ) if len(valid_log) > 0 else None,
            "log_thd_mean": round(float(np.mean(valid_log)), 6)
            if len(valid_log) > 0 else None,
            "log_thd_std": round(
                float(np.std(valid_log, ddof=1)), 6
            ) if len(valid_log) > 1 else None,
        }

    # Step 7: Write output CSV
    if output_path:
        write_output_csv(results, output_path)
        print(f"Results written to {output_path}", file=sys.stderr)

    # Step 8: Diagnostic plot
    if plot_path:
        generate_plot(results, timescales, plot_path, groups)
        print(f"Plot saved to {plot_path}", file=sys.stderr)

    return summary


def write_output_csv(results: dict, output_path: str):
    """Write results dictionary to CSV."""
    keys = list(results.keys())
    n = len(results["isolate_id"])
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(keys)
        for i in range(n):
            row = []
            for k in keys:
                val = results[k][i]
                if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                    row.append("")
                elif isinstance(val, float):
                    row.append(f"{val:.8g}")
                else:
                    row.append(val)
            writer.writerow(row)


def generate_plot(results: dict, timescales: list, plot_path: str, groups=None):
    """Generate a diagnostic bar/strip plot of THD values."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print(
            "Warning: matplotlib not available, skipping plot.",
            file=sys.stderr,
        )
        return

    n_ts = len(timescales)
    fig, axes = plt.subplots(1, n_ts, figsize=(6 * n_ts, 5), squeeze=False)

    for idx, t50 in enumerate(timescales):
        ax = axes[0, idx]
        t_label = str(int(t50))
        key = f"log_thd_{t_label}"

        if key not in results:
            continue

        values = np.array(results[key], dtype=np.float64)
        ids = results["isolate_id"]

        if groups is not None:
            unique_groups = sorted(set(groups))
            colors = plt.cm.tab10(np.linspace(0, 1, len(unique_groups)))
            color_map = {g: colors[i] for i, g in enumerate(unique_groups)}
            c = [color_map[g] for g in groups]
        else:
            c = "steelblue"

        ax.bar(range(len(values)), values, color=c, width=0.8)
        ax.set_xlabel("Isolate")
        ax.set_ylabel("log-THD")
        ax.set_title(f"THD (t50 = {t_label}y)")

        if len(ids) <= 30:
            ax.set_xticks(range(len(ids)))
            ax.set_xticklabels(ids, rotation=45, ha="right", fontsize=8)

    plt.tight_layout()
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Time-scaled Haplotypic Density (THD) Calculator. "
        "Rasigade et al. Sci Rep 7:45326 (2017).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # MIRU-VNTR haplotype matrix, 20-year timescale
  python thd_compute.py haplotypes.csv --timescale 20 --mu 5e-4

  # Dual timescales with group column
  python thd_compute.py data.csv --timescale 20 200 --group-column lineage -o results.csv

  # Pre-computed distance matrix
  python thd_compute.py distances.csv --format distance_matrix --markers 15 --timescale 20

  # With normalization and plot
  python thd_compute.py data.csv --timescale 20 200 --normalize --plot thd_plot.png
        """,
    )

    parser.add_argument(
        "input_file",
        help="Input CSV file (haplotype matrix or distance matrix).",
    )
    parser.add_argument(
        "--timescale", "-t",
        type=float,
        nargs="+",
        default=[20],
        help="Timescale(s) in years (default: 20). E.g., --timescale 20 200",
    )
    parser.add_argument(
        "--mu",
        type=float,
        default=5e-4,
        help="Evolutionary rate in changes/locus/year (default: 5e-4 for MIRU-VNTR).",
    )
    parser.add_argument(
        "--markers", "-m",
        type=int,
        default=None,
        help="Number of markers. Auto-detected for haplotype matrices, "
        "required for distance matrices.",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["auto", "haplotype_matrix", "distance_matrix"],
        default="auto",
        help="Input format (default: auto-detect).",
    )
    parser.add_argument(
        "--group-column", "-g",
        default=None,
        help="Column name for within-group THD computation.",
    )
    parser.add_argument(
        "--normalize", "-n",
        action="store_true",
        help="Compute normalized (Z-score) THD.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output CSV file path.",
    )
    parser.add_argument(
        "--plot", "-p",
        default=None,
        help="Output plot file path (PNG/PDF).",
    )

    args = parser.parse_args()

    if not Path(args.input_file).exists():
        print(f"Error: file '{args.input_file}' not found.", file=sys.stderr)
        sys.exit(1)

    summary = run_thd(
        filepath=args.input_file,
        timescales=args.timescale,
        mu=args.mu,
        markers=args.markers,
        input_format=args.format,
        group_column=args.group_column,
        do_normalize=args.normalize,
        output_path=args.output,
        plot_path=args.plot,
    )

    # Print summary as JSON to stdout
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
