#!/usr/bin/env python3
"""
McDonald-Kreitman Test and Ascertainment Bias Simulation for L4.15
===================================================================

Two complementary analyses to strengthen the dN/dS interpretation:

  Option A — McDonald-Kreitman-like test comparing fixed divergence
             (Tier 1-2) against within-lineage polymorphism (Tier 4).

  Option C — Genome-wide simulation quantifying the expected NS fraction
             after core-exclusive ascertainment filtering, under varying
             assumptions about differential sharing of synonymous vs
             non-synonymous variants with sister lineages.

Inputs:
  - supplementary_table_S3_annotated.csv (500 markers with tiers + effects)
  - NC_000962.3.gb (H37Rv genome sequence)
  - NC_000962.3.gff3 (gene coordinates)

Outputs:
  - Printed statistical results (MK test, DoS, simulation)
  - fig_mk_test_simulation.pdf (composite figure)

Usage:
  cd reproducibility/
  python scripts/mk_test_and_ascertainment.py
"""

import csv
import re
import sys
import os
from pathlib import Path
from collections import Counter, defaultdict

import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# ── Paths ────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = PROJECT_DIR / "résultats"
ARTICLE_DIR = PROJECT_DIR / "article"

S3_FILE = DATA_DIR / "supplementary_table_S3_annotated.csv"
GB_FILE = PROJECT_DIR / "NC_000962.3.gb"
GFF3_FILE = PROJECT_DIR / "NC_000962.3.gff3"


# ══════════════════════════════════════════════════════════════════════════
# PART A: McDONALD-KREITMAN TEST
# ══════════════════════════════════════════════════════════════════════════

def load_tier_data(filepath):
    """Load variant data and return NS/S counts per tier."""
    ns_effects = {'missense_variant', 'stop_gained', 'stop_lost'}
    s_effects = {'synonymous_variant'}

    tier_ns = Counter()
    tier_s = Counter()
    tier_total = Counter()

    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            tier = int(row['Tier'])
            effect = row['Effect']
            tier_total[tier] += 1
            if effect in ns_effects:
                tier_ns[tier] += 1
            elif effect in s_effects:
                tier_s[tier] += 1

    return tier_ns, tier_s, tier_total


def mk_test(dn, ds, pn, ps):
    """
    McDonald-Kreitman test.

    Parameters:
        dn: fixed non-synonymous (divergence)
        ds: fixed synonymous (divergence)
        pn: polymorphic non-synonymous
        ps: polymorphic synonymous

    Returns dict with Fisher p-value, DoS, NI, and alpha.
    """
    # 2×2 contingency table
    table = np.array([[dn, ds], [pn, ps]])
    odds_ratio, p_fisher = stats.fisher_exact(table, alternative='two-sided')

    # Direction of Selection (Stoletzki & Eyre-Walker 2011)
    # DoS = Dn/(Dn+Ds) - Pn/(Pn+Ps)
    # Handle division by zero with pseudo-counts
    if dn + ds == 0:
        dos = -pn / (pn + ps) if (pn + ps) > 0 else 0.0
    elif pn + ps == 0:
        dos = dn / (dn + ds)
    else:
        dos = dn / (dn + ds) - pn / (pn + ps)

    # Neutrality Index (NI = (Pn/Ps) / (Dn/Ds))
    # With 0 cells, use pseudo-count (+0.5) for NI only
    ni = ((pn + 0.5) / (ps + 0.5)) / ((dn + 0.5) / (ds + 0.5))

    # Proportion of adaptive substitutions (alpha = 1 - NI)
    alpha = 1.0 - ni

    return {
        'table': table,
        'p_fisher': p_fisher,
        'odds_ratio': odds_ratio,
        'DoS': dos,
        'NI': ni,
        'alpha': alpha,
    }


def bootstrap_dos(dn, ds, pn, ps, n_boot=10000, rng=None):
    """Bootstrap CI for DoS."""
    if rng is None:
        rng = np.random.default_rng(42)

    dos_values = []
    n_fixed = dn + ds
    n_poly = pn + ps

    if n_fixed == 0 or n_poly == 0:
        return np.nan, np.nan

    p_fixed_ns = dn / n_fixed
    p_poly_ns = pn / n_poly

    for _ in range(n_boot):
        # Resample from observed proportions
        boot_dn = rng.binomial(n_fixed, p_fixed_ns)
        boot_ds = n_fixed - boot_dn
        boot_pn = rng.binomial(n_poly, p_poly_ns)
        boot_ps = n_poly - boot_pn

        if (boot_dn + boot_ds) > 0 and (boot_pn + boot_ps) > 0:
            d = boot_dn / (boot_dn + boot_ds) - boot_pn / (boot_pn + boot_ps)
            dos_values.append(d)

    if len(dos_values) < 100:
        return np.nan, np.nan

    return np.percentile(dos_values, 2.5), np.percentile(dos_values, 97.5)


# ══════════════════════════════════════════════════════════════════════════
# PART C: ASCERTAINMENT BIAS SIMULATION
# ══════════════════════════════════════════════════════════════════════════

def load_genome_from_gb(filepath):
    """Extract raw DNA sequence from GenBank file."""
    seq_lines = []
    in_seq = False
    with open(filepath) as f:
        for line in f:
            if line.startswith('ORIGIN'):
                in_seq = True
                continue
            if line.startswith('//'):
                break
            if in_seq:
                seq_lines.append(re.sub(r'[\s\d]', '', line.strip()))
    return ''.join(seq_lines).upper()


def load_cds_from_gff3(filepath):
    """Parse GFF3 and return list of CDS features."""
    cds_list = []
    with open(filepath) as f:
        for line in f:
            if line.startswith('#'):
                continue
            parts = line.strip().split('\t')
            if len(parts) < 9:
                continue
            if parts[2] != 'CDS':
                continue
            start = int(parts[3])  # 1-based
            end = int(parts[4])    # 1-based inclusive
            strand = parts[6]
            attrs = parts[8]

            # Extract locus_tag
            lt_match = re.search(r'locus_tag=([^;]+)', attrs)
            locus_tag = lt_match.group(1) if lt_match else ''

            cds_list.append({
                'start': start,
                'end': end,
                'strand': strand,
                'locus_tag': locus_tag,
            })
    return cds_list


# Standard genetic code
CODON_TABLE = {
    'TTT': 'F', 'TTC': 'F', 'TTA': 'L', 'TTG': 'L',
    'CTT': 'L', 'CTC': 'L', 'CTA': 'L', 'CTG': 'L',
    'ATT': 'I', 'ATC': 'I', 'ATA': 'I', 'ATG': 'M',
    'GTT': 'V', 'GTC': 'V', 'GTA': 'V', 'GTG': 'V',
    'TCT': 'S', 'TCC': 'S', 'TCA': 'S', 'TCG': 'S',
    'CCT': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
    'ACT': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
    'GCT': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
    'TAT': 'Y', 'TAC': 'Y', 'TAA': '*', 'TAG': '*',
    'CAT': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
    'AAT': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
    'GAT': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
    'TGT': 'C', 'TGC': 'C', 'TGA': '*', 'TGG': 'W',
    'CGT': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
    'AGT': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
    'GGT': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G',
}

BASES = 'ACGT'

COMPLEMENT = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}


def revcomp(s):
    return ''.join(COMPLEMENT.get(b, 'N') for b in reversed(s))


def nei_gojobori_sites(codon):
    """
    Compute synonymous and non-synonymous sites for a single codon
    using the Nei-Gojobori (1986) method.

    Returns (n_syn_sites, n_nonsyn_sites) — each in [0, 3].
    """
    if len(codon) != 3 or codon not in CODON_TABLE:
        return 0.0, 0.0

    ref_aa = CODON_TABLE[codon]
    if ref_aa == '*':
        # Stop codons: convention is to count as 0 sites
        return 0.0, 0.0

    s_sites = 0.0
    for pos in range(3):
        n_syn = 0
        n_total = 0
        for alt_base in BASES:
            if alt_base == codon[pos]:
                continue
            alt_codon = codon[:pos] + alt_base + codon[pos+1:]
            alt_aa = CODON_TABLE.get(alt_codon, '?')
            if alt_aa == '?':
                continue
            n_total += 1
            if alt_aa == ref_aa:
                n_syn += 1
        if n_total > 0:
            s_sites += n_syn / n_total

    n_sites = 3.0 - s_sites
    return s_sites, n_sites


def compute_genome_wide_sites(genome_seq, cds_list):
    """
    Compute total synonymous and non-synonymous sites across all CDS
    in the H37Rv genome using Nei-Gojobori method.
    """
    total_syn = 0.0
    total_nonsyn = 0.0
    total_codons = 0
    coding_bp = 0

    for cds in cds_list:
        start_0 = cds['start'] - 1   # 0-based
        end_0 = cds['end']           # exclusive
        strand = cds['strand']
        cds_len = end_0 - start_0

        if cds_len % 3 != 0:
            continue  # skip non-standard CDS

        raw_seq = genome_seq[start_0:end_0]
        if strand == '-':
            raw_seq = revcomp(raw_seq)

        coding_bp += len(raw_seq)
        n_codons = len(raw_seq) // 3

        for i in range(n_codons):
            codon = raw_seq[i*3:(i+1)*3]
            if len(codon) != 3:
                continue
            s, ns = nei_gojobori_sites(codon)
            total_syn += s
            total_nonsyn += ns
            total_codons += 1

    return total_syn, total_nonsyn, total_codons, coding_bp


def simulate_ascertainment_bias(p_ns_genome, n_core_total, n_exclusive,
                                n_simulations=100_000, rng=None):
    """
    Simulate the ascertainment bias of the core-exclusive filter.

    Model:
    - n_core_total coding variants are fixed in L4.15
    - Their NS:S composition follows genome-wide expectation (p_ns_genome)
    - Each variant has a probability of being shared with sister lineages
    - Under null: sharing probability is identical for NS and S
    - Under alternative: S variants are shared more often (bias_factor × more)
    - After removing shared variants, we get n_exclusive variants
    - What is the expected NS fraction?

    We sweep bias_factor from 1.0 (no bias) to 3.0 (S shared 3× more).
    """
    if rng is None:
        rng = np.random.default_rng(42)

    # Calibrate: n_exclusive out of n_core_total survive the filter
    # Overall survival rate:
    survival_rate = n_exclusive / n_core_total

    bias_factors = np.arange(1.0, 4.1, 0.1)
    results = []

    for bias in bias_factors:
        # Under this bias model:
        # p_survive_NS * p_NS + p_survive_S * p_S = survival_rate
        # p_survive_S = p_survive_NS / bias
        # So: p_survive_NS * p_NS + (p_survive_NS / bias) * (1 - p_NS) = survival_rate
        # p_survive_NS * [p_NS + (1 - p_NS) / bias] = survival_rate
        # p_survive_NS = survival_rate / [p_NS + (1 - p_NS) / bias]

        p_ns = p_ns_genome
        p_s = 1.0 - p_ns

        denom = p_ns + p_s / bias
        if denom == 0:
            continue
        p_survive_ns = survival_rate / denom
        p_survive_s = p_survive_ns / bias

        # Clamp probabilities
        p_survive_ns = min(p_survive_ns, 1.0)
        p_survive_s = min(p_survive_s, 1.0)

        ns_fractions = []
        p_33_of_33 = []

        for _ in range(n_simulations):
            # Generate n_core_total coding variants
            n_ns = rng.binomial(n_core_total, p_ns)
            n_s = n_core_total - n_ns

            # Apply differential survival
            ns_surviving = rng.binomial(n_ns, p_survive_ns)
            s_surviving = rng.binomial(n_s, p_survive_s)

            total_surviving = ns_surviving + s_surviving
            if total_surviving > 0:
                frac = ns_surviving / total_surviving
                ns_fractions.append(frac)

        ns_fractions = np.array(ns_fractions)

        results.append({
            'bias_factor': bias,
            'p_survive_ns': p_survive_ns,
            'p_survive_s': p_survive_s,
            'mean_ns_frac': np.mean(ns_fractions),
            'median_ns_frac': np.median(ns_fractions),
            'ci95_lo': np.percentile(ns_fractions, 2.5),
            'ci95_hi': np.percentile(ns_fractions, 97.5),
            'p_all_ns': np.mean(ns_fractions >= 1.0),
            'p_ge_33_of_33': np.mean(ns_fractions >= 33/33),
        })

    return results


def simulate_random_snp_sets(p_ns_genome, n_variants=33, n_simulations=1_000_000,
                             rng=None):
    """
    Simple null: draw n_variants random coding SNPs from the genome,
    how often do we get 0 synonymous?
    """
    if rng is None:
        rng = np.random.default_rng(42)

    ns_counts = rng.binomial(n_variants, p_ns_genome, size=n_simulations)
    p_all_ns = np.mean(ns_counts == n_variants)
    p_ge_30 = np.mean(ns_counts >= 30)

    return p_all_ns, p_ge_30, ns_counts


# ══════════════════════════════════════════════════════════════════════════
# VISUALISATION
# ══════════════════════════════════════════════════════════════════════════

def plot_results(mk_results, sim_bias_results, null_ns_counts,
                 p_ns_genome, outpath):
    """Generate composite figure."""
    fig = plt.figure(figsize=(14, 10))
    gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.30)

    # ── Panel A: MK test contingency table ─────────────────────────
    ax_a = fig.add_subplot(gs[0, 0])
    table_data = mk_results['table']
    labels = [['Dn={}'.format(table_data[0, 0]), 'Ds={}'.format(table_data[0, 1])],
              ['Pn={}'.format(table_data[1, 0]), 'Ps={}'.format(table_data[1, 1])]]
    colors = np.array([
        [plt.cm.Reds(0.4), plt.cm.Blues(0.15)],
        [plt.cm.Reds(0.2), plt.cm.Blues(0.3)],
    ])
    ax_a.set_xlim(0, 2)
    ax_a.set_ylim(0, 2)
    for i in range(2):
        for j in range(2):
            ax_a.add_patch(plt.Rectangle((j, 1-i), 1, 1,
                                         facecolor=colors[i, j],
                                         edgecolor='black', linewidth=1.5))
            ax_a.text(j + 0.5, 1.5 - i, labels[i][j],
                      ha='center', va='center', fontsize=14, fontweight='bold')

    ax_a.set_xticks([0.5, 1.5])
    ax_a.set_xticklabels(['Non-synonymous', 'Synonymous'], fontsize=11)
    ax_a.set_yticks([0.5, 1.5])
    ax_a.set_yticklabels(['Polymorphic\n(Tier 4)', 'Fixed\n(Tier 1–2)'], fontsize=11)
    ax_a.set_title('A. McDonald-Kreitman Contingency Table', fontsize=12,
                    fontweight='bold', pad=10)
    p_val = mk_results['p_fisher']
    dos_val = mk_results['DoS']
    ax_a.text(1.0, -0.15, f"Fisher's exact $p$ = {p_val:.2e}\nDoS = {dos_val:+.3f}",
              ha='center', va='top', fontsize=10,
              transform=ax_a.transAxes, bbox=dict(boxstyle='round,pad=0.3',
                                                   facecolor='lightyellow', alpha=0.8))
    ax_a.tick_params(length=0)

    # ── Panel B: Null distribution of NS count ─────────────────────
    ax_b = fig.add_subplot(gs[0, 1])
    bins = np.arange(15.5, 34.5, 1)
    ax_b.hist(null_ns_counts, bins=bins, density=True, color='steelblue',
              alpha=0.7, edgecolor='white', linewidth=0.5)
    ax_b.axvline(33, color='red', linewidth=2, linestyle='--', label='Observed (33/33)')

    # Expected value
    expected = 33 * p_ns_genome
    ax_b.axvline(expected, color='orange', linewidth=1.5, linestyle=':',
                 label=f'Expected ({expected:.1f})')

    ax_b.set_xlabel('Number of non-synonymous variants (out of 33)', fontsize=11)
    ax_b.set_ylabel('Density', fontsize=11)
    ax_b.set_title('B. Null Distribution (genome-wide $p_{NS}$)', fontsize=12,
                    fontweight='bold', pad=10)
    ax_b.legend(fontsize=9, loc='upper left')

    # ── Panel C: Ascertainment bias sweep ──────────────────────────
    ax_c = fig.add_subplot(gs[1, 0])
    biases = [r['bias_factor'] for r in sim_bias_results]
    mean_fracs = [r['mean_ns_frac'] for r in sim_bias_results]
    ci_lo = [r['ci95_lo'] for r in sim_bias_results]
    ci_hi = [r['ci95_hi'] for r in sim_bias_results]

    ax_c.fill_between(biases, ci_lo, ci_hi, alpha=0.25, color='steelblue')
    ax_c.plot(biases, mean_fracs, 'o-', color='steelblue', markersize=3,
              label='Mean NS fraction (95% CI)')
    ax_c.axhline(1.0, color='red', linewidth=1.5, linestyle='--',
                 label='Observed (100% NS)')
    ax_c.axhline(p_ns_genome, color='orange', linewidth=1, linestyle=':',
                 label=f'Genome-wide expectation ({p_ns_genome:.3f})')

    ax_c.set_xlabel('Sharing bias factor (S shared $b×$ more than NS)', fontsize=11)
    ax_c.set_ylabel('Expected NS fraction after filtering', fontsize=11)
    ax_c.set_title('C. Ascertainment Bias Simulation', fontsize=12,
                    fontweight='bold', pad=10)
    ax_c.legend(fontsize=9, loc='upper left')
    ax_c.set_xlim(1.0, 4.0)
    ax_c.set_ylim(0.5, 1.05)

    # ── Panel D: P(all NS) vs bias factor ──────────────────────────
    ax_d = fig.add_subplot(gs[1, 1])
    p_all = [r['p_all_ns'] for r in sim_bias_results]
    ax_d.semilogy(biases, [max(p, 1e-6) for p in p_all], 'o-',
                  color='darkred', markersize=4)
    ax_d.axhline(0.05, color='grey', linewidth=1, linestyle='--',
                 label='$\\alpha$ = 0.05')
    ax_d.axhline(0.001, color='grey', linewidth=0.5, linestyle=':',
                 label='$\\alpha$ = 0.001')

    ax_d.set_xlabel('Sharing bias factor', fontsize=11)
    ax_d.set_ylabel('$P$(all NS among exclusive variants)', fontsize=11)
    ax_d.set_title('D. Significance Under Bias', fontsize=12,
                    fontweight='bold', pad=10)
    ax_d.legend(fontsize=9)
    ax_d.set_xlim(1.0, 4.0)

    fig.suptitle('McDonald-Kreitman Test and Ascertainment Bias Analysis — L4.15',
                 fontsize=14, fontweight='bold', y=0.98)

    plt.savefig(outpath, dpi=300, bbox_inches='tight')
    print(f"\nFigure saved: {outpath}")


# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════

def main():
    rng = np.random.default_rng(2025)

    # ── Check files ──────────────────────────────────────────────────
    for path, name in [(S3_FILE, "Supplementary Table S3"),
                       (GB_FILE, "H37Rv GenBank"),
                       (GFF3_FILE, "H37Rv GFF3")]:
        if not path.exists():
            print(f"ERROR: {name} not found at {path}", file=sys.stderr)
            sys.exit(1)

    # ══════════════════════════════════════════════════════════════════
    print("=" * 72)
    print("PART A: McDONALD-KREITMAN TEST")
    print("=" * 72)

    tier_ns, tier_s, tier_total = load_tier_data(S3_FILE)

    # Print tier summary
    print("\nNS/S counts per tier (from supplementary_table_S3_annotated.csv):")
    print(f"{'Tier':<6} {'Total':>6} {'NS':>6} {'S':>6} {'NS/(NS+S)':>10}")
    print("-" * 36)
    for t in sorted(tier_ns.keys() | tier_s.keys()):
        ns = tier_ns.get(t, 0)
        s = tier_s.get(t, 0)
        frac = ns / (ns + s) if (ns + s) > 0 else float('nan')
        print(f"  {t:<4} {tier_total.get(t, 0):>6} {ns:>6} {s:>6} {frac:>10.3f}")
    print("-" * 36)
    total_ns = sum(tier_ns.values())
    total_s = sum(tier_s.values())
    print(f"  All  {sum(tier_total.values()):>6} {total_ns:>6} {total_s:>6}"
          f" {total_ns/(total_ns+total_s):>10.3f}")

    # ── Primary MK test: Tier 1-2 (fixed) vs Tier 4 (polymorphic) ──
    dn = tier_ns.get(1, 0) + tier_ns.get(2, 0)
    ds = tier_s.get(1, 0) + tier_s.get(2, 0)
    pn = tier_ns.get(4, 0)
    ps = tier_s.get(4, 0)

    print(f"\n── Primary MK test: Fixed (Tier 1-2) vs Polymorphic (Tier 4) ──")
    print(f"  Fixed:       Dn = {dn}, Ds = {ds}")
    print(f"  Polymorphic: Pn = {pn}, Ps = {ps}")

    mk = mk_test(dn, ds, pn, ps)
    dos_lo, dos_hi = bootstrap_dos(dn, ds, pn, ps, n_boot=10_000, rng=rng)

    print(f"\n  Fisher's exact test (two-sided): p = {mk['p_fisher']:.4e}")
    print(f"  Odds ratio: {mk['odds_ratio']:.2f}")
    print(f"  Direction of Selection (DoS): {mk['DoS']:+.4f} "
          f"(95% bootstrap CI: [{dos_lo:+.4f}, {dos_hi:+.4f}])")
    print(f"  Neutrality Index (NI, +0.5 pseudo-count): {mk['NI']:.4f}")
    print(f"  Alpha (proportion adaptive substitutions): {mk['alpha']:+.4f}")
    print(f"\n  Interpretation: DoS > 0 indicates excess of non-synonymous")
    print(f"  fixation relative to polymorphism, consistent with")
    print(f"  positive selection driving lineage-defining mutations.")

    # ── Sensitivity: Tier 1-2 vs Tier 3-7 (all polymorphism) ────────
    print(f"\n── Sensitivity analyses ──")
    for poly_label, poly_tiers in [
        ("Tier 4 only", [4]),
        ("Tier 3-4", [3, 4]),
        ("Tier 3-7 (all non-core)", [3, 4, 5, 6, 7]),
        ("Tier 4-7 (excl. high-conf core)", [4, 5, 6, 7]),
    ]:
        pn_sens = sum(tier_ns.get(t, 0) for t in poly_tiers)
        ps_sens = sum(tier_s.get(t, 0) for t in poly_tiers)
        mk_sens = mk_test(dn, ds, pn_sens, ps_sens)
        print(f"  {poly_label:<32} Pn={pn_sens:>4} Ps={ps_sens:>4} "
              f"→ Fisher p = {mk_sens['p_fisher']:.4e}, "
              f"DoS = {mk_sens['DoS']:+.4f}")

    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("PART C: ASCERTAINMENT BIAS SIMULATION")
    print("=" * 72)

    # ── Step 1: Compute genome-wide NS/S sites ──────────────────────
    print("\nLoading H37Rv genome...")
    genome = load_genome_from_gb(GB_FILE)
    print(f"  Genome length: {len(genome):,} bp")

    print("Loading CDS annotations...")
    cds_list = load_cds_from_gff3(GFF3_FILE)
    print(f"  CDS features: {len(cds_list):,}")

    print("Computing genome-wide synonymous/non-synonymous sites (Nei-Gojobori)...")
    total_syn_sites, total_nonsyn_sites, total_codons, coding_bp = \
        compute_genome_wide_sites(genome, cds_list)

    p_syn_genome = total_syn_sites / (total_syn_sites + total_nonsyn_sites)
    p_ns_genome = total_nonsyn_sites / (total_syn_sites + total_nonsyn_sites)

    print(f"\n  Total coding: {coding_bp:,} bp ({total_codons:,} codons)")
    print(f"  Synonymous sites:     {total_syn_sites:,.1f}")
    print(f"  Non-synonymous sites: {total_nonsyn_sites:,.1f}")
    print(f"  p_syn (genome-wide):  {p_syn_genome:.4f}")
    print(f"  p_NS (genome-wide):   {p_ns_genome:.4f}")
    print(f"  (cf. manuscript: p_syn = 0.25 standard, 0.22 GC-adjusted)")

    # ── Step 2: Binomial test with exact p_syn ──────────────────────
    print(f"\n── Binomial test: P(0 S among 33 coding variants) ──")
    p_binom = stats.binom.pmf(0, 33, p_syn_genome)
    p_binom_cum = stats.binom.cdf(0, 33, p_syn_genome)  # P(X ≤ 0)
    print(f"  P(0 synonymous | n=33, p_syn={p_syn_genome:.4f}) = {p_binom:.4e}")
    print(f"  P(≤ 0 synonymous) = {p_binom_cum:.4e}")

    # ── Step 3: Null simulation (no ascertainment bias) ─────────────
    print(f"\n── Null simulation (n=1,000,000): random 33 coding SNPs ──")
    p_all_ns, p_ge_30, ns_counts = simulate_random_snp_sets(
        p_ns_genome, n_variants=33, n_simulations=1_000_000, rng=rng)
    print(f"  P(33/33 NS) = {p_all_ns:.6f}")
    print(f"  P(≥30/33 NS) = {p_ge_30:.6f}")
    print(f"  Mean NS count: {np.mean(ns_counts):.1f} ± {np.std(ns_counts):.1f}")

    # ── Step 4: Ascertainment bias sweep ────────────────────────────
    print(f"\n── Ascertainment bias sweep ──")
    print(f"  Model: {246} core coding SNPs, {39} survive exclusivity filter")
    print(f"  Varying sharing bias factor (S shared b× more than NS)")
    print(f"  n_simulations = 100,000 per bias value")

    # Use 246 core SNPs as starting pool (manuscript: 246 core, 39 exclusive)
    # But only ~207 are coding (246 total includes intergenic)
    # For coding variants: Tier 1-2 = 33 NS + 0 S = 33 coding exclusive
    # Total coding in all tiers: 265 NS + 144 S = 409
    # Estimate core coding: ~180 (conservative)
    # Better: use the data. All variants in S3 that are in any tier = 500.
    # Core variants (Tier 1-3): 8 + 31 + 27 = 66 total, of which
    #   NS: 6+27+16 = 49, S: 0+0+8 = 8, other: 66-49-8 = 9
    # If we use just coding: 49 NS + 8 S = 57 coding in Tier 1-3
    # Exclusive (Tier 1-2): 33 NS + 0 S = 33 out of 57 coding survive

    # For the simulation: use Tier 1-3 as the "core" pool
    n_core_coding = 49 + 8  # NS + S in Tier 1-3
    n_exclusive_coding = 33 + 0  # NS + S in Tier 1-2

    print(f"  Core coding variants (Tier 1-3): {n_core_coding}")
    print(f"  Exclusive coding variants (Tier 1-2): {n_exclusive_coding}")

    sim_results = simulate_ascertainment_bias(
        p_ns_genome, n_core_coding, n_exclusive_coding,
        n_simulations=100_000, rng=rng)

    print(f"\n  {'Bias':>6} {'Mean NS%':>9} {'95% CI':>20} {'P(all NS)':>12}")
    print(f"  {'-'*6} {'-'*9} {'-'*20} {'-'*12}")
    for r in sim_results:
        if r['bias_factor'] in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
            print(f"  {r['bias_factor']:>5.1f}× {r['mean_ns_frac']:>8.1%} "
                  f"[{r['ci95_lo']:.1%}, {r['ci95_hi']:.1%}]"
                  f" {r['p_all_ns']:>11.5f}")

    # Find critical bias where P(all NS) > 0.05
    critical_bias = None
    for r in sim_results:
        if r['p_all_ns'] >= 0.05:
            critical_bias = r['bias_factor']
            break

    if critical_bias:
        print(f"\n  ⚠ At bias = {critical_bias:.1f}×, P(all NS) first exceeds 0.05")
        print(f"    This means: synonymous variants would need to be shared with")
        print(f"    sister lineages {critical_bias:.1f}× more often than non-synonymous")
        print(f"    to explain the 33:0 ratio by ascertainment alone.")
    else:
        print(f"\n  ✓ P(all NS) remains < 0.05 across all bias values tested (up to 4.0×)")
        print(f"    The observed 33:0 ratio cannot be explained by ascertainment bias alone.")

    # ══════════════════════════════════════════════════════════════════
    # FIGURE
    # ══════════════════════════════════════════════════════════════════
    outpath = RESULTS_DIR / "fig_mk_test_simulation.pdf"
    os.makedirs(RESULTS_DIR, exist_ok=True)
    plot_results(mk, sim_results, ns_counts, p_ns_genome, outpath)

    # Also save to article/figures/
    article_path = ARTICLE_DIR / "figures" / "fig_mk_test_simulation.pdf"
    if ARTICLE_DIR.exists():
        plot_results(mk, sim_results, ns_counts, p_ns_genome, article_path)

    # ── Summary for manuscript integration ──────────────────────────
    print("\n" + "=" * 72)
    print("SUMMARY FOR MANUSCRIPT INTEGRATION")
    print("=" * 72)
    print(f"""
McDonald-Kreitman test (Tier 1-2 vs Tier 4):
  Fisher's exact p = {mk['p_fisher']:.4e}
  DoS = {mk['DoS']:+.3f} (95% CI: [{dos_lo:+.3f}, {dos_hi:+.3f}])
  Alpha = {mk['alpha']:+.3f}

Genome-wide Nei-Gojobori site computation (H37Rv):
  p_syn = {p_syn_genome:.4f} ({total_syn_sites:,.0f} syn sites / {total_syn_sites + total_nonsyn_sites:,.0f} total)
  p_NS  = {p_ns_genome:.4f}
  Binomial P(0 S | n=33, p_syn={p_syn_genome:.4f}) = {p_binom:.4e}

Ascertainment bias:
  Under no bias (b=1.0): P(33/33 NS) = {sim_results[0]['p_all_ns']:.6f}
  Critical bias to reach P > 0.05: {'b = ' + f'{critical_bias:.1f}×' if critical_bias else 'not reached (b > 4.0×)'}
""")


if __name__ == '__main__':
    main()
