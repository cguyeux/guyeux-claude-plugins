#!/usr/bin/env python3
"""
MTBC Phylogeography — Geographic distribution analysis

Analyze geographic distribution of MTBC lineages. Produces cross-tabulations,
stacked barplots, diversity indices, and choropleth maps.

Usage:
    python3 phylogeography.py distribution.csv -o summary.csv -p barplot.png
    python3 phylogeography.py distribution.csv --heatmap heatmap.png --min-strains 10
"""

import argparse
import json
import sys

import numpy as np
import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False

# WHO regions
WHO_REGIONS = {
    "AFR": ["South Africa", "Ethiopia", "Nigeria", "DR Congo", "Kenya", "Uganda",
            "Tanzania", "Mozambique", "Zimbabwe", "Malawi", "Ghana", "Cameroon",
            "Senegal", "Mali", "Burkina Faso", "Guinea", "Ivory Coast", "Niger",
            "Benin", "Togo", "Sierra Leone", "Liberia", "Gabon", "Congo",
            "Central African Republic", "Chad", "Rwanda", "Burundi", "Madagascar",
            "Zambia", "Botswana", "Namibia", "Eswatini", "Lesotho", "Angola"],
    "AMR": ["USA", "United States", "Brazil", "Peru", "Mexico", "Colombia",
            "Argentina", "Canada", "Chile", "Venezuela", "Ecuador", "Bolivia",
            "Paraguay", "Uruguay", "Guatemala", "Honduras", "El Salvador",
            "Nicaragua", "Costa Rica", "Panama", "Cuba", "Haiti",
            "Dominican Republic", "Jamaica", "Trinidad and Tobago"],
    "SEAR": ["India", "Indonesia", "Bangladesh", "Myanmar", "Thailand",
             "Nepal", "Sri Lanka", "Timor-Leste", "Bhutan", "Maldives",
             "North Korea"],
    "EUR": ["UK", "United Kingdom", "Russia", "Germany", "France", "Romania",
            "Spain", "Italy", "Portugal", "Netherlands", "Belgium", "Sweden",
            "Norway", "Denmark", "Finland", "Poland", "Czech Republic",
            "Slovakia", "Hungary", "Austria", "Switzerland", "Ireland",
            "Greece", "Turkey", "Ukraine", "Belarus", "Moldova",
            "Georgia", "Armenia", "Azerbaijan", "Lithuania", "Latvia",
            "Estonia", "Serbia", "Croatia", "Bosnia", "Montenegro",
            "North Macedonia", "Albania", "Kosovo", "Bulgaria", "Slovenia"],
    "EMR": ["Pakistan", "Afghanistan", "Somalia", "Sudan", "Iraq", "Iran",
            "Egypt", "Morocco", "Tunisia", "Libya", "Yemen", "Syria",
            "Jordan", "Lebanon", "Saudi Arabia", "UAE", "Oman", "Qatar",
            "Bahrain", "Kuwait", "Djibouti", "South Sudan"],
    "WPR": ["China", "Philippines", "Vietnam", "Papua New Guinea", "Japan",
            "South Korea", "Mongolia", "Cambodia", "Laos", "Malaysia",
            "Singapore", "Australia", "New Zealand", "Fiji"],
}

# Reverse mapping
COUNTRY_TO_REGION = {}
for region, countries in WHO_REGIONS.items():
    for country in countries:
        COUNTRY_TO_REGION[country.lower()] = region


def get_who_region(country: str) -> str:
    """Map country name to WHO region."""
    return COUNTRY_TO_REGION.get(country.lower().strip(), "Unknown")


def load_distribution(path: str) -> pd.DataFrame:
    """Load distribution CSV. Expects columns: country, lineage, n (or strain_id for raw data)."""
    df = pd.read_csv(path)
    cols_lower = {c: c.lower().strip() for c in df.columns}
    df = df.rename(columns={v: k for k, v in cols_lower.items() if k != v})

    # If raw data (strain-level), aggregate
    if "n" not in df.columns and "count" not in df.columns:
        if "country" in df.columns and "lineage" in df.columns:
            df = df.groupby(["country", "lineage"]).size().reset_index(name="n")
        elif "country" in df.columns and "lineage_code" in df.columns:
            df = df.rename(columns={"lineage_code": "lineage"})
            df = df.groupby(["country", "lineage"]).size().reset_index(name="n")

    return df


def diversity_indices(counts: np.ndarray) -> dict:
    """Compute geographic diversity indices from country counts."""
    total = counts.sum()
    if total == 0:
        return {"shannon": 0, "simpson": 0, "effective_countries": 0}

    props = counts / total
    props = props[props > 0]

    shannon = -np.sum(props * np.log(props))
    simpson = 1 - np.sum(props ** 2)
    effective = np.exp(shannon)

    return {
        "shannon": round(shannon, 3),
        "simpson": round(simpson, 3),
        "effective_countries": round(effective, 1),
    }


def plot_stacked_barplot(
    df: pd.DataFrame, output_path: str, title: str = None, min_strains: int = 5
) -> None:
    """Generate stacked barplot of lineage proportions by country."""
    if not HAS_PLOT:
        print("Warning: matplotlib not available, skipping plot.", file=sys.stderr)
        return

    # Filter countries with enough strains
    country_totals = df.groupby("country")["n"].sum()
    valid_countries = country_totals[country_totals >= min_strains].index
    df_plot = df[df["country"].isin(valid_countries)]

    # Pivot for stacked bar
    pivot = df_plot.pivot_table(index="country", columns="lineage", values="n", fill_value=0)
    # Normalize to proportions
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100
    # Sort by total count
    order = country_totals[valid_countries].sort_values(ascending=False).index
    pivot_pct = pivot_pct.reindex(order)

    fig, ax = plt.subplots(figsize=(max(10, len(order) * 0.6), 6))
    pivot_pct.plot(kind="bar", stacked=True, ax=ax, width=0.8)

    # Add total counts on top
    for i, country in enumerate(order):
        total = country_totals[country]
        ax.text(i, 101, str(total), ha="center", va="bottom", fontsize=7, fontweight="bold")

    ax.set_ylabel("Proportion (%)")
    ax.set_xlabel("")
    ax.set_ylim(0, 110)
    ax.legend(title="Lineage", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    if title:
        ax.set_title(title)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Barplot saved: {output_path}", file=sys.stderr)


def plot_heatmap(
    df: pd.DataFrame, output_path: str, title: str = None, min_strains: int = 5
) -> None:
    """Generate heatmap of country × lineage proportions."""
    if not HAS_PLOT:
        print("Warning: matplotlib not available, skipping plot.", file=sys.stderr)
        return

    country_totals = df.groupby("country")["n"].sum()
    valid_countries = country_totals[country_totals >= min_strains].index
    df_plot = df[df["country"].isin(valid_countries)]

    pivot = df_plot.pivot_table(index="country", columns="lineage", values="n", fill_value=0)
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    # Sort by total
    order = country_totals[valid_countries].sort_values(ascending=False).index
    pivot_pct = pivot_pct.reindex(order)

    fig, ax = plt.subplots(figsize=(max(8, pivot_pct.shape[1] * 1.2), max(6, len(order) * 0.4)))
    sns.heatmap(
        pivot_pct, annot=True, fmt=".0f", cmap="YlOrRd",
        linewidths=0.5, ax=ax, cbar_kws={"label": "%"},
    )
    if title:
        ax.set_title(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Heatmap saved: {output_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="MTBC phylogeographic distribution analysis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 phylogeography.py distribution.csv -o summary.csv -p barplot.png
  python3 phylogeography.py distribution.csv --heatmap heatmap.png --min-strains 10
  python3 phylogeography.py raw_strains.csv -o summary.csv --add-region
        """,
    )

    parser.add_argument("input_file", help="CSV (country, lineage, n) or raw strain data")
    parser.add_argument("-o", "--output", help="Summary CSV output")
    parser.add_argument("-p", "--plot", help="Stacked barplot output (PNG/PDF)")
    parser.add_argument("--heatmap", help="Heatmap output (PNG/PDF)")
    parser.add_argument("--min-strains", type=int, default=5, help="Min strains per country")
    parser.add_argument("--title", help="Plot title")
    parser.add_argument("--add-region", action="store_true", help="Add WHO region column")
    parser.add_argument("--summary", action="store_true", help="Print JSON summary")

    args = parser.parse_args()

    df = load_distribution(args.input_file)

    if "country" not in df.columns:
        print("Error: 'country' column required.", file=sys.stderr)
        sys.exit(1)

    # Add WHO region
    if args.add_region or args.summary:
        df["who_region"] = df["country"].apply(get_who_region)

    # Summary table
    if args.output:
        country_summary = df.groupby("country").agg(
            total=("n", "sum"),
            n_lineages=("lineage", "nunique"),
        ).sort_values("total", ascending=False)

        if args.add_region:
            country_summary["who_region"] = country_summary.index.map(
                lambda c: get_who_region(c)
            )

        country_summary.to_csv(args.output)
        print(f"Summary saved: {args.output}", file=sys.stderr)

    # Plots
    if args.plot:
        plot_stacked_barplot(df, args.plot, args.title, args.min_strains)

    if args.heatmap:
        plot_heatmap(df, args.heatmap, args.title, args.min_strains)

    # JSON summary with diversity indices
    if args.summary:
        country_counts = df.groupby("country")["n"].sum().values
        div = diversity_indices(country_counts)

        dominant_country = df.groupby("country")["n"].sum().idxmax()
        dominant_pct = round(
            100 * df.groupby("country")["n"].sum().max() / df["n"].sum(), 1
        )

        result = {
            "n_strains": int(df["n"].sum()),
            "n_countries": df["country"].nunique(),
            "n_lineages": df["lineage"].nunique() if "lineage" in df.columns else 0,
            **div,
            "dominant_country": dominant_country,
            "dominant_pct": dominant_pct,
        }

        if "who_region" in df.columns:
            region_counts = df.groupby("who_region")["n"].sum().to_dict()
            result["by_who_region"] = {k: int(v) for k, v in region_counts.items()}

        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
