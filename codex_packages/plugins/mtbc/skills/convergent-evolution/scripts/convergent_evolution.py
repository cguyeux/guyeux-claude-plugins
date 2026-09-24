#!/usr/bin/env python3
"""
Convergent Evolution Detector for MTBC

Identify genes mutated independently in multiple MTBC lineages,
perform enrichment analysis for gene families (PE/PPE, ESX, PKS/PDIM).

Usage:
    python3 convergent_evolution.py mutations.csv --min-lineages 3 -o convergent.csv
    python3 convergent_evolution.py mutations.csv --focus pe_ppe --enrichment -o results.csv
"""

import argparse
import json
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy import stats


# MTBC phylogenetic clades for independence assessment
MTBC_CLADES = {
    "human_strict": ["L1", "L7", "L2", "L3", "L4"],
    "basal_grand": ["L5"],
    "animal_clade1": ["M. bovis", "M. caprae", "M. orygis"],
    "animal_clade2": ["M. suricattae", "Dassie bacillus", "M. mungi", "M. chimpanzee"],
    "secondary_human": ["L6", "L9", "L10"],
}

# Reverse: lineage → clade
LINEAGE_TO_CLADE = {}
for clade, lineages in MTBC_CLADES.items():
    for lin in lineages:
        LINEAGE_TO_CLADE[lin] = clade

# Gene family patterns
GENE_FAMILIES = {
    "PE": lambda g: g.startswith("PE") and not g.startswith("PPE"),
    "PPE": lambda g: g.startswith("PPE"),
    "PE_PPE": lambda g: g.startswith("PE") or g.startswith("PPE"),
    "ESX": lambda g: any(g.startswith(p) for p in ["esxA", "esxB", "esxC", "esxD",
                                                      "esxE", "esxF", "esxG", "esxH",
                                                      "esxI", "esxJ", "esxK", "esxL",
                                                      "esxM", "esxN", "esxO", "esxP",
                                                      "esxQ", "esxR", "esxS", "esxT",
                                                      "esxU", "esxV", "esxW",
                                                      "eccA", "eccB", "eccC", "eccD", "eccE",
                                                      "mycP", "espA", "espB", "espC",
                                                      "espD", "espE", "espF", "espG",
                                                      "espH", "espI", "espJ", "espK"]),
    "PKS_PDIM": lambda g: any(g.startswith(p) for p in ["pks", "ppsA", "ppsB", "ppsC",
                                                          "ppsD", "ppsE", "drrA", "drrB",
                                                          "drrC", "fadD", "mas", "mmpL7",
                                                          "papA5", "lppX"]),
    "mce": lambda g: g.startswith("mce") or g.startswith("yrbE"),
}


def classify_gene_family(gene: str) -> str:
    """Classify a gene into a functional family."""
    for family, test_fn in GENE_FAMILIES.items():
        if family == "PE_PPE":
            continue  # Skip combined, use individual
        if test_fn(gene):
            return family
    return "other"


def map_lineage_to_major(lineage_code: str) -> str:
    """Map a sub-lineage code to its major lineage for clade assignment."""
    if lineage_code.startswith("M.") or lineage_code.startswith("M "):
        return lineage_code
    # Extract major lineage number
    parts = lineage_code.replace("L", "").split(".")
    major = parts[0]
    return f"L{major}"


def count_independent_lineages(lineages: set) -> int:
    """Count the number of phylogenetically independent clades represented."""
    clades = set()
    for lin in lineages:
        major = map_lineage_to_major(lin)
        clade = LINEAGE_TO_CLADE.get(major, major)
        clades.add(clade)
    return len(clades)


def detect_convergence(
    df: pd.DataFrame, min_lineages: int = 3, min_freq: float = 0.5
) -> pd.DataFrame:
    """Detect genes with convergent mutations across independent lineages.

    Args:
        df: DataFrame with columns: gene, lineage, n_strains, n_total, effect
        min_lineages: Minimum independent lineages for convergence
        min_freq: Minimum frequency within a lineage to count

    Returns:
        DataFrame of convergent genes with details.
    """
    # Filter by frequency
    df = df.copy()
    df["freq"] = df["n_strains"] / df["n_total"]
    df_high = df[df["freq"] >= min_freq]

    # Group by gene
    results = []
    for gene, group in df_high.groupby("gene"):
        lineages = set(group["lineage"].unique())
        n_independent = count_independent_lineages(lineages)

        if n_independent >= min_lineages:
            mutations = group["effect"].unique().tolist() if "effect" in group.columns else []
            family = classify_gene_family(gene)

            results.append({
                "gene": gene,
                "gene_family": family,
                "n_lineages": len(lineages),
                "n_independent_clades": n_independent,
                "lineages": ",".join(sorted(lineages)),
                "mutations": ",".join(mutations),
                "mean_freq": round(group["freq"].mean(), 3),
                "convergence_score": n_independent * len(lineages),
            })

    result = pd.DataFrame(results)
    if not result.empty:
        result = result.sort_values("convergence_score", ascending=False)
    return result


def enrichment_test(
    convergent_genes: set, all_genes: set, family_test_fn
) -> dict:
    """Fisher exact test for enrichment of a gene family in convergent genes."""
    conv_in = sum(1 for g in convergent_genes if family_test_fn(g))
    conv_out = len(convergent_genes) - conv_in
    all_in = sum(1 for g in all_genes if family_test_fn(g))
    all_out = len(all_genes) - all_in

    # Adjust for overlap
    notconv_in = all_in - conv_in
    notconv_out = all_out - conv_out

    table = [[conv_in, notconv_in], [conv_out, notconv_out]]
    odds_ratio, p_value = stats.fisher_exact(table, alternative="greater")

    return {
        "n_convergent": conv_in,
        "n_total": all_in,
        "n_convergent_other": conv_out,
        "n_total_other": all_out,
        "odds_ratio": round(odds_ratio, 2),
        "p_value": p_value,
    }


def run_enrichment(convergent_df: pd.DataFrame, all_genes: set) -> dict:
    """Run enrichment tests for all gene families."""
    convergent_genes = set(convergent_df["gene"].unique())

    results = {}
    p_values = []
    family_names = []

    for family, test_fn in GENE_FAMILIES.items():
        res = enrichment_test(convergent_genes, all_genes, test_fn)
        results[family] = res
        p_values.append(res["p_value"])
        family_names.append(family)

    # FDR correction
    if len(p_values) > 1:
        from statsmodels.stats.multitest import multipletests
        _, pvals_corr, _, _ = multipletests(p_values, method="fdr_bh")
        for i, family in enumerate(family_names):
            results[family]["p_adjusted"] = pvals_corr[i]
            results[family]["significant"] = pvals_corr[i] < 0.05
    else:
        for family in family_names:
            results[family]["p_adjusted"] = results[family]["p_value"]
            results[family]["significant"] = results[family]["p_value"] < 0.05

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Detect convergent evolution across MTBC lineages.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Detect convergent genes (≥3 independent clades)
  python3 convergent_evolution.py mutations.csv --min-lineages 3 -o convergent.csv

  # With enrichment analysis
  python3 convergent_evolution.py mutations.csv --enrichment -o convergent.csv

  # Focus on PE/PPE family
  python3 convergent_evolution.py mutations.csv --focus pe_ppe --min-lineages 2

Input CSV format:
  gene,lineage,n_strains,n_total,effect
  PE35,L1,450,500,missense_variant
  PE35,M. bovis,120,150,stop_gained
        """,
    )

    parser.add_argument("input_file", help="CSV with gene, lineage, n_strains, n_total columns")
    parser.add_argument("-o", "--output", help="Output CSV")
    parser.add_argument(
        "--min-lineages",
        type=int,
        default=3,
        help="Min independent clades for convergence (default: 3)",
    )
    parser.add_argument(
        "--min-freq",
        type=float,
        default=0.5,
        help="Min frequency within lineage (default: 0.5)",
    )
    parser.add_argument("--enrichment", action="store_true", help="Run gene family enrichment")
    parser.add_argument(
        "--focus",
        choices=["all", "pe_ppe", "esx", "pks_pdim", "resistance"],
        default="all",
        help="Focus on specific gene family",
    )
    parser.add_argument("--summary", action="store_true", help="Print JSON summary")

    args = parser.parse_args()

    df = pd.read_csv(args.input_file)

    required = {"gene", "lineage", "n_strains", "n_total"}
    missing = required - set(df.columns)
    if missing:
        print(f"Error: missing columns: {missing}", file=sys.stderr)
        sys.exit(1)

    # Focus filter
    if args.focus != "all" and args.focus in GENE_FAMILIES:
        test_fn = GENE_FAMILIES[args.focus]
        df = df[df["gene"].apply(test_fn)]
        print(f"Filtered to {args.focus}: {df['gene'].nunique()} genes", file=sys.stderr)

    # Detect convergence
    convergent = detect_convergence(df, args.min_lineages, args.min_freq)
    print(
        f"Found {len(convergent)} convergent genes "
        f"(≥{args.min_lineages} independent clades, freq ≥{args.min_freq})",
        file=sys.stderr,
    )

    if args.output:
        convergent.to_csv(args.output, index=False)
        print(f"Saved: {args.output}", file=sys.stderr)
    elif not args.summary:
        convergent.to_csv(sys.stdout, index=False)

    # Enrichment
    if args.enrichment:
        all_genes = set(df["gene"].unique())
        enrichment = run_enrichment(convergent, all_genes)

        print("\nGene family enrichment:", file=sys.stderr)
        for family, res in enrichment.items():
            sig = "*" if res.get("significant") else ""
            print(
                f"  {family}: {res['n_convergent']}/{res['n_total']} "
                f"(OR={res['odds_ratio']}, p_adj={res['p_adjusted']:.4f}){sig}",
                file=sys.stderr,
            )

    # Summary
    if args.summary:
        summary = {
            "n_genes_analyzed": df["gene"].nunique(),
            "n_convergent_genes": len(convergent),
            "min_lineages_threshold": args.min_lineages,
            "min_freq_threshold": args.min_freq,
        }
        if not convergent.empty:
            summary["top_genes"] = convergent.head(20).to_dict("records")
            summary["family_distribution"] = (
                convergent["gene_family"].value_counts().to_dict()
            )
        if args.enrichment:
            summary["enrichment"] = enrichment
        print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
