#!/usr/bin/env python3
"""
Molecular Clock Analysis for MTBC

Root-to-tip regression, temporal signal evaluation, and BEAST XML helpers
for MTBC phylogenies with typically weak clock signal.

Usage:
    python3 molecular_clock.py root-to-tip tree.nwk dates.csv -o results.csv -p plot.png
    python3 molecular_clock.py nexus-to-newick mcc_tree.nex -o dated_tree.nwk
"""

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False

try:
    from Bio import Phylo
    from io import StringIO
    HAS_BIOPYTHON = True
except ImportError:
    HAS_BIOPYTHON = False


def parse_newick_distances(newick_path: str) -> dict:
    """Parse Newick tree and compute root-to-tip distances.

    Returns dict: {leaf_name: root_to_tip_distance}
    """
    if HAS_BIOPYTHON:
        tree = Phylo.read(newick_path, "newick")
        distances = {}
        for leaf in tree.get_terminals():
            dist = tree.distance(leaf)
            distances[leaf.name] = dist
        return distances

    # Fallback: simple Newick parser for branch lengths
    with open(newick_path) as f:
        newick = f.read().strip()

    # Extract leaf names
    leaf_pattern = re.compile(r"([A-Za-z][A-Za-z0-9_.]+):([0-9.eE+-]+)")
    matches = leaf_pattern.findall(newick)

    if not matches:
        raise ValueError("Could not parse leaf names and branch lengths from Newick.")

    # Approximate: use terminal branch length as proxy
    # (proper root-to-tip requires full tree traversal)
    distances = {}
    for name, bl in matches:
        distances[name] = float(bl)

    print(
        f"Warning: using terminal branch lengths as proxy "
        f"(install biopython for true root-to-tip distances).",
        file=sys.stderr,
    )
    return distances


def load_dates(dates_path: str) -> dict:
    """Load collection dates. Returns {strain_id: decimal_year}."""
    df = pd.read_csv(dates_path)
    # Normalize columns
    col_map = {}
    for col in df.columns:
        cl = col.lower().strip()
        if cl in ("strain_id", "sra_id", "id", "name", "taxon"):
            col_map[col] = "strain_id"
        elif cl in ("date", "collection_date", "year", "decimal_date"):
            col_map[col] = "date"
    df = df.rename(columns=col_map)

    if "strain_id" not in df.columns or "date" not in df.columns:
        raise ValueError("Dates CSV must have 'strain_id' and 'date' columns.")

    dates = {}
    for _, row in df.iterrows():
        sid = str(row["strain_id"])
        date_val = row["date"]

        if pd.isna(date_val):
            continue

        # Parse various date formats
        date_str = str(date_val).strip()
        try:
            # Already decimal (e.g., 2015.5)
            decimal = float(date_str)
            dates[sid] = decimal
        except ValueError:
            # Try YYYY-MM-DD or YYYY-MM
            parts = date_str.split("-")
            year = int(parts[0])
            month = int(parts[1]) if len(parts) > 1 else 6
            day = int(parts[2]) if len(parts) > 2 else 15
            decimal = year + (month - 1) / 12 + (day - 1) / 365.25
            dates[sid] = round(decimal, 3)

    return dates


def root_to_tip_regression(
    distances: dict, dates: dict
) -> dict:
    """Perform root-to-tip regression.

    Returns dict with regression results.
    """
    # Match strain IDs between tree and dates
    common = set(distances.keys()) & set(dates.keys())
    if len(common) < 3:
        raise ValueError(
            f"Only {len(common)} strains in common between tree ({len(distances)}) "
            f"and dates ({len(dates)}). Need ≥3."
        )

    x = np.array([dates[s] for s in common])
    y = np.array([distances[s] for s in common])
    strain_ids = list(common)

    # Linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    # Residuals
    predicted = slope * x + intercept
    residuals = y - predicted

    # Outlier detection (>2 SD)
    resid_std = np.std(residuals)
    outliers = [strain_ids[i] for i in range(len(common)) if abs(residuals[i]) > 2 * resid_std]

    # Bootstrap 95% CI on the clock rate (resample strains with replacement).
    # More honest than the analytic CI when n is small / the signal is weak.
    rng = np.random.default_rng(42)
    n_common = len(common)
    boot_slopes = []
    if n_common >= 4:
        for _ in range(1000):
            samp = rng.integers(0, n_common, n_common)
            if len(np.unique(x[samp])) < 2:
                continue
            bs = float(stats.linregress(x[samp], y[samp])[0])  # type: ignore[arg-type]
            if np.isfinite(bs):
                boot_slopes.append(bs)
    rate_boot_lo = float(np.percentile(boot_slopes, 2.5)) if boot_slopes else None
    rate_boot_hi = float(np.percentile(boot_slopes, 97.5)) if boot_slopes else None

    # Convert slope to SNP/genome/year
    # slope is in substitutions/site/year if branch lengths are in subs/site
    # For SNP trees, slope ≈ SNPs/year directly

    result = {
        "n_samples": len(common),
        "n_tree": len(distances),
        "n_dates": len(dates),
        "rate_per_year": slope,
        "rate_ci95_lo": slope - 1.96 * std_err,
        "rate_ci95_hi": slope + 1.96 * std_err,
        "rate_boot_ci95_lo": rate_boot_lo,
        "rate_boot_ci95_hi": rate_boot_hi,
        "intercept": intercept,
        "r_squared": r_value ** 2,
        "r_value": r_value,
        "p_value": p_value,
        "std_error": std_err,
        "root_date_estimate": -intercept / slope if slope != 0 else None,
        "date_range": [float(x.min()), float(x.max())],
        "distance_range": [float(y.min()), float(y.max())],
        "n_outliers": len(outliers),
        "outliers": outliers[:10],  # Top 10
    }

    # Signal quality assessment
    r2 = r_value ** 2
    if r2 > 0.3:
        result["signal_quality"] = "strong (unusual for MTBC)"
    elif r2 > 0.1:
        result["signal_quality"] = "moderate"
    elif r2 > 0.01:
        result["signal_quality"] = "weak (typical for MTBC) — BEAST recommended"
    else:
        result["signal_quality"] = "undetectable — multi-constraint calibration needed"

    return result, strain_ids, x, y, predicted, residuals


def plot_rtt(
    strain_ids, x, y, predicted, residuals, result, output_path
):
    """Generate root-to-tip regression plot."""
    if not HAS_PLOT:
        print("Warning: matplotlib not available.", file=sys.stderr)
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: regression plot
    ax = axes[0]
    resid_std = np.std(residuals)
    outlier_mask = np.abs(residuals) > 2 * resid_std

    ax.scatter(x[~outlier_mask], y[~outlier_mask], s=15, alpha=0.6, c="#2196F3", label="Samples")
    ax.scatter(x[outlier_mask], y[outlier_mask], s=25, alpha=0.8, c="#F44336",
               marker="x", label="Outliers (>2σ)")
    ax.plot(x, predicted, "k-", linewidth=1.5, label=f"R²={result['r_squared']:.4f}")
    ax.set_xlabel("Collection date (decimal year)")
    ax.set_ylabel("Root-to-tip distance")
    ax.set_title(f"Root-to-tip regression (n={result['n_samples']})")
    ax.legend(fontsize=9)

    # Annotation
    rate_text = f"Rate: {result['rate_per_year']:.2e} ± {result['std_error']:.2e}"
    ax.text(0.02, 0.98, rate_text, transform=ax.transAxes, fontsize=8,
            verticalalignment="top", bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

    # Right: residuals
    ax2 = axes[1]
    ax2.scatter(x, residuals, s=15, alpha=0.6, c="#9C27B0")
    ax2.axhline(0, color="k", linewidth=0.5)
    ax2.axhline(2 * resid_std, color="r", linewidth=0.5, linestyle="--", alpha=0.5)
    ax2.axhline(-2 * resid_std, color="r", linewidth=0.5, linestyle="--", alpha=0.5)
    ax2.set_xlabel("Collection date")
    ax2.set_ylabel("Residual")
    ax2.set_title("Residuals")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Plot saved: {output_path}", file=sys.stderr)


def date_randomization_test(distances: dict, dates: dict, n_perm: int = 1000,
                            seed: int = 42) -> dict:
    """Test de randomisation des dates (DRT) — garde-fou AVANT de lancer BEAST.

    Permute les dates entre souches et recompte la pente racine-vs-temps à
    chaque permutation. S'il y a un vrai signal temporel, la pente observée
    doit sortir du nuage des pentes permutées (H0 = pas de structure
    temporelle). Sur arbre fixe, on permute les dates sur les distances
    racine→feuille observées (variante rapide du DRT de Duchêne et al. 2015).

    Retourne un dict avec la pente observée, le nuage permuté, et un p-value
    unilatéral (pente observée > permutées).
    """
    common = sorted(set(distances) & set(dates))
    if len(common) < 4:
        raise ValueError(f"DRT : {len(common)} souches communes, besoin de ≥4.")
    x = np.array([dates[s] for s in common], dtype=float)
    y = np.array([distances[s] for s in common], dtype=float)
    obs = stats.linregress(x, y)
    rng = np.random.default_rng(seed)
    perm = np.array([stats.linregress(rng.permutation(x), y).slope
                     for _ in range(n_perm)])
    # p unilatéral : proportion de permutations aussi extrêmes que l'observé
    p_drt = (np.sum(perm >= obs.slope) + 1) / (n_perm + 1)
    passed = bool(p_drt < 0.05 and obs.slope > 0)
    return {
        "n_samples": len(common),
        "n_perm": n_perm,
        "observed_slope": float(obs.slope),
        "observed_r_squared": float(obs.rvalue ** 2),
        "observed_p": float(obs.pvalue),
        "perm_slope_median": float(np.median(perm)),
        "perm_slope_ci95_lo": float(np.percentile(perm, 2.5)),
        "perm_slope_ci95_hi": float(np.percentile(perm, 97.5)),
        "drt_p_value": float(p_drt),
        "temporal_signal": passed,
        "verdict": ("signal temporel présent (obs hors du nuage permuté)"
                    if passed else
                    "PAS de signal distinguable — dater est hasardeux"),
        "_perm": perm, "_x": x, "_y": y, "_obs": obs, "_common": common,
    }


def plot_drt(drt: dict, output_path: str):
    """Figure DRT : régression observée + histogramme des pentes permutées."""
    if not HAS_PLOT:
        print("Warning: matplotlib not available.", file=sys.stderr)
        return
    x, y, obs, perm = drt["_x"], drt["_y"], drt["_obs"], drt["_perm"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    ax = axes[0]
    anc = x < 1900
    ax.scatter(x[~anc], y[~anc], s=15, alpha=0.7, c="#1f6f6f", label="modernes")
    ax.scatter(x[anc], y[anc], s=30, facecolor="none", edgecolor="#c1440e",
               linewidth=1.0, label="aDNA")
    xs = np.array([x.min(), x.max()])
    ax.plot(xs, obs.slope * xs + obs.intercept, "-", c="#c1440e", linewidth=1.5)
    ax.set_xlabel("Date de prélèvement (année)")
    ax.set_ylabel("Distance racine→feuille")
    ax.set_title(f"Régression (R²={drt['observed_r_squared']:.3f}, "
                 f"p={drt['observed_p']:.3f})")
    ax.legend(fontsize=8)
    ax2 = axes[1]
    ax2.hist(perm, bins=40, color="#999999", alpha=0.75, label="dates permutées (H₀)")
    ax2.axvline(obs.slope, color="#c1440e", linewidth=1.6, label="pente observée")
    ax2.set_xlabel("Pente d'horloge (subst/site/an)")
    ax2.set_ylabel("Fréquence")
    ax2.set_title(f"DRT : p={drt['drt_p_value']:.3f}")
    ax2.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Plot saved: {output_path}", file=sys.stderr)


def nexus_to_newick(nexus_path: str, output_path: str):
    """Convert BEAST Nexus tree to Newick format."""
    if HAS_BIOPYTHON:
        tree = Phylo.read(nexus_path, "nexus")
        with open(output_path, "w") as f:
            Phylo.write(tree, f, "newick")
        print(f"Converted: {nexus_path} → {output_path}", file=sys.stderr)
        return

    # Fallback: extract tree string manually
    with open(nexus_path) as f:
        content = f.read()

    # Find tree block
    tree_match = re.search(r"tree\s+\w+\s*=\s*\[&[^\]]*\]\s*(.+);", content, re.IGNORECASE)
    if not tree_match:
        tree_match = re.search(r"tree\s+\w+\s*=\s*(.+);", content, re.IGNORECASE)

    if not tree_match:
        raise ValueError("Could not find tree in Nexus file.")

    newick = tree_match.group(1).strip()
    # Remove BEAST annotations [&...]
    newick = re.sub(r"\[&[^\]]*\]", "", newick)

    with open(output_path, "w") as f:
        f.write(newick + ";\n")
    print(f"Converted: {nexus_path} → {output_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Molecular clock analysis for MTBC phylogenies.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Root-to-tip regression
  python3 molecular_clock.py root-to-tip tree.nwk dates.csv -o rtt.csv -p rtt.png

  # Convert BEAST Nexus to Newick
  python3 molecular_clock.py nexus-to-newick mcc_tree.nex -o dated.nwk
        """,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Root-to-tip
    p_rtt = subparsers.add_parser("root-to-tip", help="Root-to-tip regression")
    p_rtt.add_argument("tree", help="Newick tree file")
    p_rtt.add_argument("dates", help="CSV with strain_id and date columns")
    p_rtt.add_argument("-o", "--output", help="Results CSV output")
    p_rtt.add_argument("-p", "--plot", help="Plot output (PNG/PDF)")
    p_rtt.add_argument("--summary", action="store_true", help="Print JSON summary")

    # Date randomization test (DRT)
    p_drt = subparsers.add_parser("date-randomization",
                                  help="Test de randomisation des dates (garde-fou avant BEAST)")
    p_drt.add_argument("tree", help="Newick tree file")
    p_drt.add_argument("dates", help="CSV with strain_id and date columns")
    p_drt.add_argument("-n", "--n-perm", type=int, default=1000, dest="n_perm")
    p_drt.add_argument("--seed", type=int, default=42)
    p_drt.add_argument("-p", "--plot", help="Plot output (PNG/PDF)")
    p_drt.add_argument("--midpoint", action="store_true",
                       help="enraciner l'arbre au midpoint avant de mesurer les distances")

    # Nexus to Newick
    p_nex = subparsers.add_parser("nexus-to-newick", help="Convert Nexus to Newick")
    p_nex.add_argument("nexus", help="Input Nexus file")
    p_nex.add_argument("-o", "--output", required=True, help="Output Newick file")

    args = parser.parse_args()

    if args.command == "root-to-tip":
        distances = parse_newick_distances(args.tree)
        dates = load_dates(args.dates)

        result, strain_ids, x, y, predicted, residuals = root_to_tip_regression(
            distances, dates
        )

        # Output CSV
        if args.output:
            rows = []
            common = set(distances.keys()) & set(dates.keys())
            for i, sid in enumerate(strain_ids):
                rows.append({
                    "strain_id": sid,
                    "date": x[i],
                    "root_to_tip_distance": y[i],
                    "predicted": predicted[i],
                    "residual": residuals[i],
                })
            pd.DataFrame(rows).to_csv(args.output, index=False)
            print(f"Results saved: {args.output}", file=sys.stderr)

        # Plot
        if args.plot:
            plot_rtt(strain_ids, x, y, predicted, residuals, result, args.plot)

        # Summary
        if args.summary or (not args.output and not args.plot):
            # Round floats for display
            display = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in result.items()}
            print(json.dumps(display, indent=2, default=str))

    elif args.command == "date-randomization":
        if not HAS_BIOPYTHON:
            sys.exit("date-randomization requiert biopython (distances racine→feuille exactes).")
        tree = Phylo.read(args.tree, "newick")
        if args.midpoint:
            tree.root_at_midpoint()
        distances = {t.name: tree.distance(tree.root, t) for t in tree.get_terminals()}
        dates = load_dates(args.dates)
        drt = date_randomization_test(distances, dates, n_perm=args.n_perm, seed=args.seed)
        if args.plot:
            plot_drt(drt, args.plot)
        display = {k: (round(v, 8) if isinstance(v, float) else v)
                   for k, v in drt.items() if not k.startswith("_")}
        print(json.dumps(display, indent=2, default=str))

    elif args.command == "nexus-to-newick":
        nexus_to_newick(args.nexus, args.output)


if __name__ == "__main__":
    main()
