#!/usr/bin/env python3
"""
MTBC Drug Resistance Profiler

Analyze drug resistance profiles for MTBC strain collections.
Produces summary tables, cross-tabulations, iTOL binary datasets,
and supplementary article tables.

Usage:
    python3 resistance_profiler.py metadata.csv -o summary.csv --itol resistance.txt
    python3 resistance_profiler.py metadata.csv --supplement supplement.csv
"""

import argparse
import json
import sys

import numpy as np
import pandas as pd
from scipy import stats


# WHO-endorsed resistance genes by drug
RESISTANCE_GENES = {
    "RIF": ["rpoB"],
    "INH": ["katG", "inhA"],
    "EMB": ["embB"],
    "PZA": ["pncA"],
    "SM": ["rpsL", "rrs"],
    "FQ": ["gyrA", "gyrB"],
    "AMI": ["rrs", "tlyA"],
    "ETH": ["ethA", "inhA"],
}

# iTOL colors for drugs
DRUG_COLORS = {
    "RIF": "#ff0000",
    "INH": "#ff6600",
    "EMB": "#0066ff",
    "PZA": "#009933",
    "SM": "#9933ff",
    "FQ": "#ff3399",
    "AMI": "#663300",
    "ETH": "#336699",
}

DR_TYPE_ORDER = ["susceptible", "mono-R", "poly-R", "MDR", "pre-XDR", "XDR"]


def load_metadata(path: str) -> pd.DataFrame:
    """Load strain metadata CSV with dr_type and lineage columns."""
    df = pd.read_csv(path)
    # Normalize column names
    col_map = {}
    for col in df.columns:
        cl = col.lower().strip()
        if cl in ("strain_id", "sra_id", "id"):
            col_map[col] = "strain_id"
        elif cl in ("lineage", "lineage_code"):
            col_map[col] = "lineage"
        elif cl in ("dr_type", "resistance"):
            col_map[col] = "dr_type"
    df = df.rename(columns=col_map)
    return df


def summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """Compute resistance summary by lineage with CI95."""
    rows = []
    for lineage, group in df.groupby("lineage"):
        total = len(group)
        dr_counts = group["dr_type"].value_counts()

        row = {"lineage": lineage, "total": total}
        for dr in DR_TYPE_ORDER:
            n = dr_counts.get(dr, 0)
            row[dr] = n
            row[f"{dr}_pct"] = round(100 * n / total, 1) if total > 0 else 0

        # Any resistance
        n_susceptible = dr_counts.get("susceptible", 0)
        n_any_r = total - n_susceptible
        row["any_R"] = n_any_r
        row["any_R_pct"] = round(100 * n_any_r / total, 1) if total > 0 else 0

        # CI95 for any_R (Clopper-Pearson)
        if total > 0:
            lo, hi = stats.binom.ppf([0.025, 0.975], total, n_any_r / total) / total
            row["any_R_ci95_lo"] = round(100 * lo, 1)
            row["any_R_ci95_hi"] = round(100 * hi, 1)

        rows.append(row)

    return pd.DataFrame(rows).sort_values("total", ascending=False)


def crosstab_lineage_resistance(df: pd.DataFrame) -> pd.DataFrame:
    """Cross-tabulation lineage × dr_type with counts and percentages."""
    ct = pd.crosstab(df["lineage"], df["dr_type"], margins=True)
    # Add percentage columns
    for col in ct.columns:
        if col != "All":
            ct[f"{col}_pct"] = (100 * ct[col] / ct["All"]).round(1)
    return ct


def generate_itol_binary(
    df: pd.DataFrame, drugs: list, output_path: str
) -> None:
    """Generate iTOL DATASET_BINARY file for drug resistance."""
    drug_list = [d for d in drugs if d in DRUG_COLORS]
    colors = "\t".join(DRUG_COLORS[d] for d in drug_list)
    labels = "\t".join(drug_list)
    shapes = "\t".join(["2"] * len(drug_list))

    lines = [
        "DATASET_BINARY",
        "SEPARATOR TAB",
        f"DATASET_LABEL\tDrug Resistance ({', '.join(drug_list)})",
        "COLOR\t#ff0000",
        f"FIELD_SHAPES\t{shapes}",
        f"FIELD_LABELS\t{labels}",
        f"FIELD_COLORS\t{colors}",
        "LEGEND_TITLE\tDrug Resistance",
        "LEGEND_SHAPES\t2\t2",
        "LEGEND_COLORS\t#333333\t#cccccc",
        "LEGEND_LABELS\tResistant\tSusceptible",
        "DATA",
    ]

    for _, row in df.iterrows():
        strain_id = row["strain_id"]
        dr = str(row.get("dr_type", "susceptible")).lower()
        # Simple binary encoding based on dr_type
        values = []
        for drug in drug_list:
            if drug == "RIF" and dr in ("mdr", "pre-xdr", "xdr"):
                values.append("1")
            elif drug == "INH" and dr in ("mdr", "pre-xdr", "xdr"):
                values.append("1")
            elif drug == "FQ" and dr in ("pre-xdr", "xdr"):
                values.append("1")
            elif drug == "AMI" and dr == "xdr":
                values.append("1")
            elif drug in ("RIF", "INH") and dr == "mono-r":
                # mono-R could be either, mark as unknown (0)
                values.append("0")
            else:
                values.append("0")
        lines.append(f"{strain_id}\t{chr(9).join(values)}")

    with open(output_path, "w") as f:
        f.write("\n".join(lines) + "\n")


def pairwise_fisher(df: pd.DataFrame) -> pd.DataFrame:
    """Pairwise Fisher exact test for any_R between lineages."""
    lineages = sorted(df["lineage"].unique())
    rows = []

    for i, l1 in enumerate(lineages):
        for l2 in lineages[i + 1 :]:
            g1 = df[df["lineage"] == l1]
            g2 = df[df["lineage"] == l2]

            n1 = len(g1)
            n2 = len(g2)
            r1 = (g1["dr_type"] != "susceptible").sum()
            r2 = (g2["dr_type"] != "susceptible").sum()

            table = [[r1, n1 - r1], [r2, n2 - r2]]
            oddsratio, pvalue = stats.fisher_exact(table)

            rows.append({
                "group_1": l1,
                "group_2": l2,
                "n_1": n1,
                "n_2": n2,
                "r_1": r1,
                "r_2": r2,
                "pct_1": round(100 * r1 / n1, 1) if n1 > 0 else 0,
                "pct_2": round(100 * r2 / n2, 1) if n2 > 0 else 0,
                "odds_ratio": round(oddsratio, 3),
                "p_value": pvalue,
            })

    result = pd.DataFrame(rows)
    if not result.empty and len(result) > 1:
        from statsmodels.stats.multitest import multipletests
        _, pvals_corr, _, _ = multipletests(result["p_value"], method="fdr_bh")
        result["p_adjusted"] = pvals_corr
        result["significant"] = result["p_adjusted"] < 0.05
    elif not result.empty:
        result["p_adjusted"] = result["p_value"]
        result["significant"] = result["p_value"] < 0.05

    return result


def main():
    parser = argparse.ArgumentParser(
        description="MTBC drug resistance profiler.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 resistance_profiler.py metadata.csv -o summary.csv
  python3 resistance_profiler.py metadata.csv --itol resistance.txt
  python3 resistance_profiler.py metadata.csv --fisher -o fisher.csv
  python3 resistance_profiler.py metadata.csv --supplement supplement.csv
        """,
    )

    parser.add_argument("input_file", help="CSV with strain_id, lineage, dr_type columns")
    parser.add_argument("-o", "--output", help="Summary table CSV output")
    parser.add_argument("--itol", help="iTOL binary dataset output path")
    parser.add_argument("--supplement", help="Supplementary table CSV output")
    parser.add_argument(
        "--drugs",
        default="RIF,INH,EMB,PZA",
        help="Comma-separated drug list (default: RIF,INH,EMB,PZA)",
    )
    parser.add_argument("--fisher", action="store_true", help="Run pairwise Fisher tests")
    parser.add_argument("--summary", action="store_true", help="Print JSON summary to stdout")

    args = parser.parse_args()

    df = load_metadata(args.input_file)
    drugs = [d.strip() for d in args.drugs.split(",")]

    if "lineage" not in df.columns or "dr_type" not in df.columns:
        print(
            "Error: input CSV must have 'lineage' and 'dr_type' columns.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Summary table
    summary = summary_table(df)
    if args.output:
        summary.to_csv(args.output, index=False)
        print(f"Summary saved: {args.output}", file=sys.stderr)
    elif not args.itol and not args.supplement and not args.fisher:
        summary.to_csv(sys.stdout, index=False)

    # iTOL binary dataset
    if args.itol:
        if "strain_id" not in df.columns:
            print("Warning: no strain_id column, skipping iTOL output.", file=sys.stderr)
        else:
            generate_itol_binary(df, drugs, args.itol)
            print(f"iTOL binary dataset saved: {args.itol}", file=sys.stderr)

    # Supplement table
    if args.supplement:
        ct = crosstab_lineage_resistance(df)
        ct.to_csv(args.supplement)
        print(f"Cross-tabulation saved: {args.supplement}", file=sys.stderr)

    # Fisher tests
    if args.fisher:
        fisher_results = pairwise_fisher(df)
        if args.output:
            fisher_path = args.output.replace(".csv", "_fisher.csv")
        else:
            fisher_path = "fisher_results.csv"
        fisher_results.to_csv(fisher_path, index=False)
        print(f"Fisher test results saved: {fisher_path}", file=sys.stderr)

    # JSON summary
    if args.summary:
        total = len(df)
        n_susceptible = (df["dr_type"] == "susceptible").sum()
        result = {
            "n_strains": total,
            "n_with_dr_type": df["dr_type"].notna().sum(),
            "n_lineages": df["lineage"].nunique(),
            "any_resistance_pct": round(100 * (total - n_susceptible) / total, 1)
            if total > 0
            else 0,
            "dr_type_distribution": df["dr_type"].value_counts().to_dict(),
        }
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
