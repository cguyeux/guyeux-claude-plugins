#!/usr/bin/env python3
"""
Pangenome Enrichment Analysis for MTBC

Classify genes into core/soft-core/shell/cloud by lineage,
identify differentially present genes, perform KEGG pathway enrichment.

Usage:
    python3 pangenome_enrichment.py gene_presence.csv --group-column lineage -o classification.csv
    python3 pangenome_enrichment.py gene_presence.csv --enrichment kegg -o enrichment.csv
"""

import argparse
import json
import sys
import time
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy import stats


# Default thresholds
CORE_THRESHOLD = 0.99
SOFT_CORE_THRESHOLD = 0.95
SHELL_THRESHOLD = 0.15

KEGG_BASE_URL = "https://rest.kegg.jp"
KEGG_RATE_LIMIT = 0.5  # seconds between requests


def classify_gene(freq: float, core=CORE_THRESHOLD, soft=SOFT_CORE_THRESHOLD, shell=SHELL_THRESHOLD) -> str:
    """Classify gene frequency into pangenome category."""
    if freq >= core:
        return "core"
    elif freq >= soft:
        return "soft_core"
    elif freq >= shell:
        return "shell"
    else:
        return "cloud"


def load_gene_matrix(path: str) -> tuple:
    """Load gene presence/absence matrix.

    Returns (matrix DataFrame, group_info dict or None)
    """
    df = pd.read_csv(path)
    id_col = df.columns[0]
    df = df.set_index(id_col)

    # Separate group column if present
    group_info = None
    non_numeric = df.select_dtypes(exclude=[np.number]).columns.tolist()
    if non_numeric:
        # First non-numeric column is likely the group
        group_col = non_numeric[0]
        group_info = df[group_col].to_dict()
        df = df.drop(columns=non_numeric)

    df = df.fillna(0).astype(int)
    return df, group_info


def pangenome_classification(
    matrix: pd.DataFrame,
    group_info: dict = None,
    thresholds: tuple = (CORE_THRESHOLD, SOFT_CORE_THRESHOLD, SHELL_THRESHOLD),
) -> pd.DataFrame:
    """Classify genes by pangenome category, optionally per group."""
    core_t, soft_t, shell_t = thresholds
    n_strains = matrix.shape[0]

    results = []
    for gene in matrix.columns:
        freq_overall = matrix[gene].mean()
        row = {
            "gene": gene,
            "freq_overall": round(freq_overall, 4),
            "n_present": int(matrix[gene].sum()),
            "n_total": n_strains,
            "category_overall": classify_gene(freq_overall, core_t, soft_t, shell_t),
        }

        if group_info:
            groups = pd.Series(group_info)
            for group_name in sorted(groups.unique()):
                mask = groups[groups == group_name].index
                mask = [m for m in mask if m in matrix.index]
                if len(mask) > 0:
                    freq = matrix.loc[mask, gene].mean()
                    row[f"freq_{group_name}"] = round(freq, 4)
                    row[f"cat_{group_name}"] = classify_gene(freq, core_t, soft_t, shell_t)

        results.append(row)

    return pd.DataFrame(results)


def find_differential_genes(
    matrix: pd.DataFrame,
    group_info: dict,
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Find genes differentially present between groups (Fisher exact test)."""
    groups = pd.Series(group_info)
    group_names = sorted(groups.unique())

    if len(group_names) < 2:
        print("Need ≥2 groups for differential analysis.", file=sys.stderr)
        return pd.DataFrame()

    results = []
    for gene in matrix.columns:
        # For each pair of groups
        for i, g1 in enumerate(group_names):
            for g2 in group_names[i + 1:]:
                mask1 = [m for m in groups[groups == g1].index if m in matrix.index]
                mask2 = [m for m in groups[groups == g2].index if m in matrix.index]

                n1_present = int(matrix.loc[mask1, gene].sum())
                n1_absent = len(mask1) - n1_present
                n2_present = int(matrix.loc[mask2, gene].sum())
                n2_absent = len(mask2) - n2_present

                freq1 = n1_present / len(mask1) if mask1 else 0
                freq2 = n2_present / len(mask2) if mask2 else 0

                # Only test if frequencies differ substantially
                if abs(freq1 - freq2) < 0.1:
                    continue

                table = [[n1_present, n1_absent], [n2_present, n2_absent]]
                _, p_value = stats.fisher_exact(table)

                results.append({
                    "gene": gene,
                    "group_1": g1,
                    "group_2": g2,
                    "freq_1": round(freq1, 4),
                    "freq_2": round(freq2, 4),
                    "n_1": len(mask1),
                    "n_2": len(mask2),
                    "p_value": p_value,
                })

    if not results:
        return pd.DataFrame()

    result = pd.DataFrame(results)

    # FDR correction
    if len(result) > 1:
        from statsmodels.stats.multitest import multipletests
        _, pvals_corr, _, _ = multipletests(result["p_value"], method="fdr_bh")
        result["p_adjusted"] = pvals_corr
    else:
        result["p_adjusted"] = result["p_value"]

    result["significant"] = result["p_adjusted"] < alpha
    result = result.sort_values("p_adjusted")

    return result


def kegg_enrichment(
    gene_set: set, background: set, organism: str = "mtu"
) -> pd.DataFrame:
    """KEGG pathway enrichment analysis with Fisher exact test.

    Requires internet access. Respects rate limiting.
    """
    try:
        import requests
    except ImportError:
        print("Warning: requests not available, skipping KEGG enrichment.", file=sys.stderr)
        return pd.DataFrame()

    # Cache: gene → pathways
    gene_pathways = defaultdict(set)
    pathway_names = {}

    print("Querying KEGG pathways (this may take a while)...", file=sys.stderr)

    # Get all gene-pathway links
    try:
        resp = requests.get(f"{KEGG_BASE_URL}/link/pathway/{organism}", timeout=30)
        if resp.status_code == 200:
            for line in resp.text.strip().split("\n"):
                parts = line.split("\t")
                if len(parts) == 2:
                    gene = parts[0].replace(f"{organism}:", "")
                    pathway = parts[1].replace("path:", "")
                    gene_pathways[gene].add(pathway)
        time.sleep(KEGG_RATE_LIMIT)
    except Exception as e:
        print(f"KEGG query failed: {e}", file=sys.stderr)
        return pd.DataFrame()

    # Get pathway names
    all_pathways = set()
    for paths in gene_pathways.values():
        all_pathways.update(paths)

    try:
        resp = requests.get(f"{KEGG_BASE_URL}/list/pathway/{organism}", timeout=30)
        if resp.status_code == 200:
            for line in resp.text.strip().split("\n"):
                parts = line.split("\t")
                if len(parts) == 2:
                    pid = parts[0].replace("path:", "")
                    pathway_names[pid] = parts[1].split(" - ")[0].strip()
        time.sleep(KEGG_RATE_LIMIT)
    except Exception:
        pass

    # Enrichment test for each pathway
    results = []
    for pathway in sorted(all_pathways):
        genes_in_pathway = {g for g, paths in gene_pathways.items() if pathway in paths}

        set_in = len(gene_set & genes_in_pathway)
        set_out = len(gene_set) - set_in
        bg_in = len(background & genes_in_pathway) - set_in
        bg_out = len(background) - len(gene_set) - bg_in

        if set_in == 0:
            continue

        table = [[set_in, bg_in], [set_out, bg_out]]
        _, p_value = stats.fisher_exact(table, alternative="greater")

        results.append({
            "pathway": pathway,
            "name": pathway_names.get(pathway, ""),
            "genes_in_set": set_in,
            "genes_in_pathway": len(genes_in_pathway),
            "set_size": len(gene_set),
            "background_size": len(background),
            "p_value": p_value,
        })

    if not results:
        return pd.DataFrame()

    result = pd.DataFrame(results)
    if len(result) > 1:
        from statsmodels.stats.multitest import multipletests
        _, pvals_corr, _, _ = multipletests(result["p_value"], method="fdr_bh")
        result["p_adjusted"] = pvals_corr
    else:
        result["p_adjusted"] = result["p_value"]

    result = result.sort_values("p_adjusted")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="MTBC pangenome classification and enrichment analysis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Classify genes
  python3 pangenome_enrichment.py gene_presence.csv --group-column lineage -o classification.csv

  # Find differential genes
  python3 pangenome_enrichment.py gene_presence.csv --group-column lineage --differential -o diff.csv

  # KEGG enrichment on differential genes
  python3 pangenome_enrichment.py gene_presence.csv --group-column lineage \\
    --differential --enrichment kegg -o enrichment.csv
        """,
    )

    parser.add_argument("input_file", help="Gene presence/absence matrix CSV")
    parser.add_argument("-o", "--output", help="Output CSV")
    parser.add_argument("--group-column", help="Column name for grouping (e.g., lineage)")
    parser.add_argument(
        "--thresholds",
        default="0.99,0.95,0.15",
        help="Core,soft-core,shell thresholds (default: 0.99,0.95,0.15)",
    )
    parser.add_argument("--differential", action="store_true", help="Find differential genes")
    parser.add_argument(
        "--enrichment",
        choices=["kegg", "none"],
        default="none",
        help="Enrichment analysis type",
    )
    parser.add_argument("--summary", action="store_true", help="Print JSON summary")

    args = parser.parse_args()

    matrix, group_info_from_matrix = load_gene_matrix(args.input_file)
    thresholds = tuple(float(t) for t in args.thresholds.split(","))

    group_info = group_info_from_matrix

    print(
        f"Loaded: {matrix.shape[0]} strains x {matrix.shape[1]} genes",
        file=sys.stderr,
    )

    # Classification
    classification = pangenome_classification(matrix, group_info, thresholds)

    if args.output and not args.differential:
        classification.to_csv(args.output, index=False)
        print(f"Classification saved: {args.output}", file=sys.stderr)

    # Differential analysis
    diff_genes = None
    if args.differential and group_info:
        diff_genes = find_differential_genes(matrix, group_info)
        n_sig = diff_genes["significant"].sum() if not diff_genes.empty else 0
        print(f"Differential genes: {n_sig} significant (FDR < 0.05)", file=sys.stderr)

        if args.output:
            diff_path = args.output.replace(".csv", "_differential.csv") if not args.differential else args.output
            diff_genes[diff_genes["significant"]].to_csv(diff_path, index=False)
            print(f"Differential genes saved: {diff_path}", file=sys.stderr)

    # KEGG enrichment
    if args.enrichment == "kegg" and diff_genes is not None and not diff_genes.empty:
        sig_genes = set(diff_genes[diff_genes["significant"]]["gene"].unique())
        all_genes = set(matrix.columns)
        enrichment = kegg_enrichment(sig_genes, all_genes)

        if not enrichment.empty:
            enrich_path = args.output.replace(".csv", "_kegg.csv") if args.output else "kegg_enrichment.csv"
            enrichment.to_csv(enrich_path, index=False)
            print(f"KEGG enrichment saved: {enrich_path}", file=sys.stderr)

    # Summary
    if args.summary:
        cat_counts = classification["category_overall"].value_counts().to_dict()
        summary = {
            "n_strains": matrix.shape[0],
            "n_genes": matrix.shape[1],
            "pangenome_categories": cat_counts,
        }

        if group_info:
            summary["n_groups"] = len(set(group_info.values()))
            summary["groups"] = sorted(set(group_info.values()))

        if diff_genes is not None and not diff_genes.empty:
            summary["n_differential_tested"] = len(diff_genes)
            summary["n_differential_significant"] = int(diff_genes["significant"].sum())

        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
