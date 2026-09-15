#!/usr/bin/env python3
"""
Lineage Comparison — Statistical tests for MTBC lineage comparisons

Compare traits (resistance, geography, mutations) between lineages
with proper statistical testing and multiple testing correction.

Usage:
    python3 lineage_comparison.py data.csv --group lineage --variable dr_type -o results.csv
    python3 lineage_comparison.py data.csv --group lineage --variable has_mutation --test fisher
"""

import argparse
import json
import sys
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats


def binomial_ci(k: int, n: int, alpha: float = 0.05) -> tuple:
    """Clopper-Pearson exact binomial confidence interval."""
    if n == 0:
        return (0.0, 0.0)
    lo = stats.beta.ppf(alpha / 2, k, n - k + 1) if k > 0 else 0.0
    hi = stats.beta.ppf(1 - alpha / 2, k + 1, n - k) if k < n else 1.0
    return (lo, hi)


def fisher_test_binary(g1_pos, g1_neg, g2_pos, g2_neg):
    """Fisher exact test on 2×2 table, returns OR, p-value, OR CI."""
    table = [[g1_pos, g1_neg], [g2_pos, g2_neg]]
    oddsratio, pvalue = stats.fisher_exact(table)

    # Exact CI for odds ratio (Cornfield method approximation via log-OR)
    if g1_pos > 0 and g1_neg > 0 and g2_pos > 0 and g2_neg > 0:
        log_or = np.log(oddsratio)
        se = np.sqrt(1 / g1_pos + 1 / g1_neg + 1 / g2_pos + 1 / g2_neg)
        or_lo = np.exp(log_or - 1.96 * se)
        or_hi = np.exp(log_or + 1.96 * se)
    else:
        or_lo, or_hi = 0.0, float("inf")

    return oddsratio, pvalue, or_lo, or_hi


def pairwise_comparisons_binary(
    df: pd.DataFrame, group_col: str, variable_col: str
) -> pd.DataFrame:
    """Pairwise Fisher exact tests for a binary variable between groups."""
    groups = sorted(df[group_col].unique())
    rows = []

    for g1, g2 in combinations(groups, 2):
        d1 = df[df[group_col] == g1]
        d2 = df[df[group_col] == g2]

        n1 = len(d1)
        n2 = len(d2)

        # Binary: 1 = positive, 0 = negative
        # Or categorical: count most common value vs rest
        if df[variable_col].dtype in (bool, np.bool_) or set(
            df[variable_col].dropna().unique()
        ).issubset({0, 1, True, False, "0", "1"}):
            pos1 = d1[variable_col].astype(int).sum()
            pos2 = d2[variable_col].astype(int).sum()
        else:
            # Treat as binary: most common value vs rest
            target_val = df[variable_col].value_counts().index[0]
            pos1 = (d1[variable_col] == target_val).sum()
            pos2 = (d2[variable_col] == target_val).sum()

        neg1 = n1 - pos1
        neg2 = n2 - pos2

        prop1 = pos1 / n1 if n1 > 0 else 0
        prop2 = pos2 / n2 if n2 > 0 else 0

        ci1 = binomial_ci(pos1, n1)
        ci2 = binomial_ci(pos2, n2)

        oddsratio, pvalue, or_lo, or_hi = fisher_test_binary(pos1, neg1, pos2, neg2)

        rows.append({
            "group_1": g1,
            "group_2": g2,
            "variable": variable_col,
            "n_1": n1,
            "n_2": n2,
            "count_1": pos1,
            "count_2": pos2,
            "prop_1": round(prop1, 4),
            "prop_2": round(prop2, 4),
            "ci95_1_lo": round(ci1[0], 4),
            "ci95_1_hi": round(ci1[1], 4),
            "ci95_2_lo": round(ci2[0], 4),
            "ci95_2_hi": round(ci2[1], 4),
            "odds_ratio": round(oddsratio, 3),
            "or_ci95_lo": round(or_lo, 3),
            "or_ci95_hi": round(or_hi, 3),
            "p_value": pvalue,
        })

    result = pd.DataFrame(rows)

    # FDR correction
    if len(result) > 1:
        from statsmodels.stats.multitest import multipletests
        _, pvals_corr, _, _ = multipletests(result["p_value"], method="fdr_bh")
        result["p_adjusted"] = pvals_corr
    elif len(result) == 1:
        result["p_adjusted"] = result["p_value"]
    else:
        return result

    result["significant"] = result["p_adjusted"] < 0.05
    return result


def chi_squared_test(df: pd.DataFrame, group_col: str, variable_col: str) -> dict:
    """Chi-squared test for independence between group and variable."""
    ct = pd.crosstab(df[group_col], df[variable_col])
    chi2, p, dof, expected = stats.chi2_contingency(ct)

    # Standardized residuals
    residuals = (ct - expected) / np.sqrt(expected)

    return {
        "chi2": round(chi2, 3),
        "p_value": p,
        "dof": dof,
        "contingency_table": ct.to_dict(),
        "residuals": residuals.to_dict(),
        "cramers_v": round(np.sqrt(chi2 / (ct.values.sum() * (min(ct.shape) - 1))), 3),
    }


def continuous_comparison(
    df: pd.DataFrame, group_col: str, variable_col: str
) -> pd.DataFrame:
    """Mann-Whitney U or Kruskal-Wallis for continuous variables."""
    groups = sorted(df[group_col].unique())
    data_by_group = {g: df[df[group_col] == g][variable_col].dropna().values for g in groups}

    rows = []

    if len(groups) == 2:
        g1, g2 = groups
        u_stat, pvalue = stats.mannwhitneyu(
            data_by_group[g1], data_by_group[g2], alternative="two-sided"
        )
        rows.append({
            "test": "Mann-Whitney U",
            "group_1": g1,
            "group_2": g2,
            "n_1": len(data_by_group[g1]),
            "n_2": len(data_by_group[g2]),
            "median_1": round(np.median(data_by_group[g1]), 4),
            "median_2": round(np.median(data_by_group[g2]), 4),
            "statistic": round(u_stat, 3),
            "p_value": pvalue,
        })
    else:
        # Kruskal-Wallis omnibus
        arrays = [data_by_group[g] for g in groups if len(data_by_group[g]) > 0]
        h_stat, pvalue = stats.kruskal(*arrays)
        rows.append({
            "test": "Kruskal-Wallis",
            "groups": ", ".join(groups),
            "statistic": round(h_stat, 3),
            "p_value": pvalue,
        })

        # Post-hoc pairwise Mann-Whitney with FDR
        pairwise_rows = []
        for g1, g2 in combinations(groups, 2):
            if len(data_by_group[g1]) > 0 and len(data_by_group[g2]) > 0:
                u, p = stats.mannwhitneyu(
                    data_by_group[g1], data_by_group[g2], alternative="two-sided"
                )
                pairwise_rows.append({
                    "test": "Mann-Whitney U (post-hoc)",
                    "group_1": g1,
                    "group_2": g2,
                    "n_1": len(data_by_group[g1]),
                    "n_2": len(data_by_group[g2]),
                    "median_1": round(np.median(data_by_group[g1]), 4),
                    "median_2": round(np.median(data_by_group[g2]), 4),
                    "statistic": round(u, 3),
                    "p_value": p,
                })

        if pairwise_rows:
            ph_df = pd.DataFrame(pairwise_rows)
            if len(ph_df) > 1:
                from statsmodels.stats.multitest import multipletests
                _, pvals_corr, _, _ = multipletests(ph_df["p_value"], method="fdr_bh")
                ph_df["p_adjusted"] = pvals_corr
            else:
                ph_df["p_adjusted"] = ph_df["p_value"]
            ph_df["significant"] = ph_df["p_adjusted"] < 0.05
            rows.extend(ph_df.to_dict("records"))

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Statistical comparison between MTBC lineages.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Binary variable (Fisher exact, pairwise)
  python3 lineage_comparison.py data.csv --group lineage --variable is_MDR -o results.csv

  # Categorical variable (chi-squared)
  python3 lineage_comparison.py data.csv --group lineage --variable dr_type --test chi2

  # Continuous variable (Mann-Whitney / Kruskal-Wallis)
  python3 lineage_comparison.py data.csv --group lineage --variable thd_20 --test continuous
        """,
    )

    parser.add_argument("input_file", help="CSV with group and variable columns")
    parser.add_argument("--group", required=True, help="Column name for grouping (e.g., lineage)")
    parser.add_argument("--variable", required=True, help="Column name for the variable to compare")
    parser.add_argument(
        "--test",
        default="auto",
        choices=["auto", "fisher", "chi2", "continuous"],
        help="Test type (default: auto-detect)",
    )
    parser.add_argument("-o", "--output", help="Output CSV path")
    parser.add_argument("--summary", action="store_true", help="Print JSON summary")

    args = parser.parse_args()

    df = pd.read_csv(args.input_file)

    if args.group not in df.columns:
        print(f"Error: column '{args.group}' not found.", file=sys.stderr)
        sys.exit(1)
    if args.variable not in df.columns:
        print(f"Error: column '{args.variable}' not found.", file=sys.stderr)
        sys.exit(1)

    # Auto-detect test type
    test_type = args.test
    if test_type == "auto":
        unique_vals = df[args.variable].dropna().unique()
        if df[args.variable].dtype in (float, np.float64, np.float32) and len(unique_vals) > 10:
            test_type = "continuous"
        elif len(unique_vals) == 2:
            test_type = "fisher"
        else:
            test_type = "chi2"

    print(f"Test: {test_type}, groups: {df[args.group].nunique()}, "
          f"variable: {args.variable} ({df[args.variable].nunique()} unique values)",
          file=sys.stderr)

    if test_type == "fisher":
        result = pairwise_comparisons_binary(df, args.group, args.variable)
    elif test_type == "chi2":
        chi2_result = chi_squared_test(df, args.group, args.variable)
        if args.summary:
            print(json.dumps(chi2_result, indent=2, default=str))
        result = pd.DataFrame([{
            "test": "chi-squared",
            "chi2": chi2_result["chi2"],
            "p_value": chi2_result["p_value"],
            "dof": chi2_result["dof"],
            "cramers_v": chi2_result["cramers_v"],
        }])
    elif test_type == "continuous":
        result = continuous_comparison(df, args.group, args.variable)

    if args.output:
        result.to_csv(args.output, index=False)
        print(f"Results saved: {args.output}", file=sys.stderr)
    else:
        result.to_csv(sys.stdout, index=False)

    if args.summary and test_type != "chi2":
        n_sig = result["significant"].sum() if "significant" in result.columns else 0
        summary = {
            "test_type": test_type,
            "n_comparisons": len(result),
            "n_significant": int(n_sig),
            "n_groups": df[args.group].nunique(),
        }
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
