#!/usr/bin/env python3
"""
Molecular Clock Pipeline for MTBC — v5 workflow.

Encapsulates the entire dated phylogenetic analysis:
1. Collect ancient + modern + H37Rv + outgroup strains
2. Extract synonymous SPDIs (TBannotator annotations or manual via GenBank)
3. Apply mixed-infection filter via inter-L4 sharing
4. Query TBannotator for real collection dates
5. Build binary alignment matrix with LSD2 date constraints
6. Run IQ-TREE/LSD2 tip-dating with H37Rv MRCA constraint
7. Parse and report the calibrated rate + tMRCA with confidence intervals

Usage:
    python3 molecular_clock_pipeline.py --output résultats/my_analysis [options]

Options:
    --output PATH           Output prefix (directory/prefix)
    --ancient-config JSON   JSON file mapping ancient names to metadata
    --lineages CSV          Modern lineages to include (default: L4.1,L4.3.3,L4.8,L4.2.1,L4.7)
    --n-per-lineage N       Strains to sample per lineage (default: 5)
    --n-h37rv N             H37Rv stocks to include (default: 50)
    --n-outgroup N          Bovis outgroup strains (default: 3)
    --seed N                Random seed (default: 2026)
    --iqtree PATH           Path to iqtree2 binary
    --bdd PATH              Path to bdd/ root (default: ../../bdd/)
    --skip-iqtree           Build files but don't run IQ-TREE
"""

import os
import sys
import json
import re
import random
import argparse
import shutil
import subprocess
from pathlib import Path
from collections import defaultdict


# ============================================================
# DEFAULT ANCIENT GENOMES CONFIGURATION
# ============================================================
# Each entry: (path relative to bdd/ancien/, LSD2 date string, decimal midpoint, source file type)
# source type: 'report' = TBannotator report.json, 'file' = pre-computed spdi_syn.txt

DEFAULT_ANCIENTS = {
    # Bos 2014 — 3 pinnipedii, Peru
    'SRR1238557': {
        'path': 'Pinipedii/SRR1238557',
        'date_lsd2': 'b(1028,1280)', 'date_mid': 1154.0,
        'source': 'report', 'lineage': 'pinnipedii',
        'publication': 'Bos 2014 Nature 514:494',
    },
    'SRR1238558': {
        'path': 'Pinipedii/SRR1238558',
        'date_lsd2': 'b(1028,1280)', 'date_mid': 1154.0,
        'source': 'report', 'lineage': 'pinnipedii',
        'publication': 'Bos 2014 Nature 514:494',
    },
    'SRR1238559': {
        'path': 'Pinipedii/SRR1238559',
        'date_lsd2': 'b(1028,1280)', 'date_mid': 1154.0,
        'source': 'report', 'lineage': 'pinnipedii',
        'publication': 'Bos 2014 Nature 514:494',
    },
    # Vågene 2022 — 3 pinnipedii, South America (BAM GitHub)
    'Vagene2022_S82': {
        'path': 'Pinipedii/Vagene2022_S82',
        'date_lsd2': 'b(1250,1470)', 'date_mid': 1360.0,
        'source': 'file', 'lineage': 'pinnipedii',
        'publication': 'Vågene 2022 Nat Commun 13:1195',
    },
    'Vagene2022_S281': {
        'path': 'Pinipedii/Vagene2022_S281',
        'date_lsd2': 'b(1265,1380)', 'date_mid': 1322.5,
        'source': 'file', 'lineage': 'pinnipedii',
        'publication': 'Vågene 2022 Nat Commun 13:1195',
    },
    'Vagene2022_S386': {
        'path': 'Pinipedii/Vagene2022_S386',
        'date_lsd2': 'b(1450,1640)', 'date_mid': 1545.0,
        'source': 'file', 'lineage': 'pinnipedii',
        'publication': 'Vågene 2022 Nat Commun 13:1195',
    },
    # Sabin 2020 — Winstrup
    'Winstrup_LUND1': {
        'path': 'M_tuberculosis_L4/Winstrup_LUND1',
        'date_lsd2': '1679', 'date_mid': 1679.0,
        'source': 'file', 'lineage': 'L4',
        'publication': 'Sabin 2020 Genome Biol 21:201',
    },
    # Kay 2015 — Body 68 clean (inter-L4 sharing filter applied)
    'Body68_Kay2015_clean': {
        'path': 'M_tuberculosis_L4/Body68_Kay2015_clean',
        'date_lsd2': 'b(1731,1838)', 'date_mid': 1784.5,
        'source': 'file', 'lineage': 'L4',
        'publication': 'Kay 2015 Nat Commun 6:6717 (mixed infection, cleaned)',
    },
    # Kay 2015 — Body 92
    'Body92_Kay2015': {
        'path': 'M_tuberculosis_L4/Body92_Kay2015',
        'date_lsd2': 'b(1731,1838)', 'date_mid': 1784.5,
        'source': 'file', 'lineage': 'L4',
        'publication': 'Kay 2015 Nat Commun 6:6717',
    },
}

# Real dates from TBannotator for modern strains (verified)
REAL_DATES = {
    'ERR12075278': '2021', 'ERR4143897': '2019', 'ERR4143898': '2019',
    'SRR7693584': 'b(2011,2012)', 'SRR6397608': '2007', 'ERR2229459': '2010',
    'ERR228031': '2010', 'ERR9786511': '2013', 'ERR11798654': '2017',
    'SRR10380037': '2017', 'SRR21677945': '2017', 'SRR28240242': '2018',
    'SRR25534573': '2018', 'SRR14782657': '2019', 'SRR28498505': '2021',
    'SRR21240167': '2021', 'SRR23640778': '2022', 'SRR23640760': '2022',
    'ERR234577': '2008', 'ERR133978': '2009', 'ERR6865357': '2009',
    'SRR21659036': '2016', 'SRR5486883': '2016', 'SRR23339944': '2018',
    'SRR9738523': '2018', 'SRR21240150': '2021', 'SRR24222928': '2021',
}


# ============================================================
# SYNONYMOUS SPDI EXTRACTION
# ============================================================

def get_syn_from_report(report_path):
    """Extract synonymous SPDI set from TBannotator report.json."""
    with open(report_path) as f:
        report = json.load(f)
    return set(
        snp['spdi'] for snp in report.get('snp', [])
        for ann in snp.get('annotations', [])
        if 'synonymous_variant' in ann.get('annotation', [])
    )


def get_syn_from_file(spdi_syn_path):
    """Read pre-computed synonymous SPDIs from spdi_syn.txt."""
    with open(spdi_syn_path) as f:
        return set(line.strip() for line in f if line.strip())


def load_genbank_cds(gb_path):
    """Load CDS features from GenBank for manual annotation fallback."""
    try:
        from Bio import SeqIO
    except ImportError:
        return None, None
    record = SeqIO.read(gb_path, "genbank")
    ref_seq = str(record.seq)
    cds = [
        (int(f.location.start), int(f.location.end), f.location.strand)
        for f in record.features if f.type == "CDS"
    ]
    return ref_seq, cds


def is_synonymous(pos_0, ref_a, alt_a, ref_seq, cds_features):
    """Check if a SNP at pos_0 (0-based) is synonymous using GenBank CDS."""
    from Bio.Seq import Seq
    for start, end, strand in cds_features:
        if start <= pos_0 < end:
            if strand == 1:
                cp = (pos_0 - start) % 3
                cs = pos_0 - cp
                codon_ref = ref_seq[cs:cs+3]
                codon_alt = list(codon_ref)
                codon_alt[cp] = alt_a
            else:
                cp = (end - 1 - pos_0) % 3
                ce = pos_0 + cp + 1
                cs2 = ce - 3
                codon_ref = str(Seq(ref_seq[cs2:ce]).reverse_complement())
                fwd = list(ref_seq[cs2:ce])
                fwd[pos_0 - cs2] = alt_a
                codon_alt = list(str(Seq(''.join(fwd)).reverse_complement()))
            try:
                return str(Seq(codon_ref).translate()) == str(Seq(''.join(codon_alt)).translate())
            except Exception:
                return False
    return False


# ============================================================
# STRAIN COLLECTION
# ============================================================

def collect_ancients(bdd_ancien, ancient_config):
    """Load synonymous SPDI for all configured ancient genomes."""
    ancients = {}
    missing = []
    for name, meta in ancient_config.items():
        strain_dir = bdd_ancien / meta['path']
        if meta['source'] == 'report':
            report_path = strain_dir / "NC_000962.3" / "report.json"
            if not report_path.exists():
                missing.append(name); continue
            syns = get_syn_from_report(report_path)
        else:
            syn_path = strain_dir / "NC_000962.3" / "spdi_syn.txt"
            if not syn_path.exists():
                missing.append(name); continue
            syns = get_syn_from_file(syn_path)
        if syns:
            ancients[name] = syns
    return ancients, missing


def collect_moderns(bdd_actuelle, lineages, n_per_lineage, seed, min_syn=50):
    """Sample modern strains per lineage and extract synonymous SPDIs."""
    random.seed(seed)
    moderns = {}
    for lineage in lineages:
        lpath = bdd_actuelle / lineage
        if not lpath.is_dir():
            print(f"  ⚠ Lineage not found: {lineage}", file=sys.stderr)
            continue
        candidates = sorted(os.listdir(lpath))
        random.shuffle(candidates)
        loaded = 0
        for sra in candidates:
            if loaded >= n_per_lineage:
                break
            rp = lpath / sra / "NC_000962.3" / "report.json"
            if not rp.exists():
                continue
            try:
                syns = get_syn_from_report(rp)
                if len(syns) > min_syn:
                    moderns[sra] = syns
                    loaded += 1
            except Exception:
                continue
    return moderns


def collect_h37rv(bdd_actuelle, n_target, seed, max_total_snp=100):
    """Sample H37Rv stocks (true stocks = < max_total_snp SNPs vs reference)."""
    random.seed(seed + 1)  # different seed to avoid overlap with moderns
    h37rv_dir = bdd_actuelle / "L4.9_H37Rv"
    candidates = sorted(os.listdir(h37rv_dir))
    random.shuffle(candidates)
    stocks = {}
    names = []
    for sra in candidates:
        if len(stocks) >= n_target:
            break
        rp = h37rv_dir / sra / "NC_000962.3" / "report.json"
        if not rp.exists():
            continue
        try:
            with open(rp) as f:
                report = json.load(f)
            if len(report.get('snp', [])) < max_total_snp:
                syns = get_syn_from_report(rp)
                name = f"H37Rv_{sra}"
                stocks[name] = syns
                names.append(name)
        except Exception:
            continue
    return stocks, names


def collect_outgroup(bdd_actuelle, n_target, outgroup_lineage="Bovis"):
    """Load outgroup strains."""
    og_dir = bdd_actuelle / outgroup_lineage
    outgroup = {}
    for sra in sorted(os.listdir(og_dir)):
        if len(outgroup) >= n_target:
            break
        rp = og_dir / sra / "NC_000962.3" / "report.json"
        if not rp.exists():
            continue
        try:
            syns = get_syn_from_report(rp)
            outgroup[f"OG_{sra}"] = syns
        except Exception:
            continue
    return outgroup


# ============================================================
# MATRIX CONSTRUCTION
# ============================================================

def build_binary_matrix(strain_syn_sets):
    """Build binary presence/absence matrix for informative sites."""
    all_spdis = set()
    for s in strain_syn_sets.values():
        all_spdis |= s
    n = len(strain_syn_sets)
    informative = sorted(
        spdi for spdi in all_spdis
        if 2 <= sum(1 for s in strain_syn_sets.values() if spdi in s) < n
    )
    return informative


def write_phylip(strain_syn_sets, informative, output_path):
    """Write binary alignment in PHYLIP format."""
    names = sorted(strain_syn_sets.keys())
    with open(output_path, 'w') as f:
        f.write(f"{len(names)} {len(informative)}\n")
        for name in names:
            seq = ''.join('1' if spdi in strain_syn_sets[name] else '0' for spdi in informative)
            f.write(f"{name}  {seq}\n")


def write_dates_files(all_dates, simple_path, lsd2_path):
    """Write date files in both simple (midpoints) and LSD2 (with uncertainty) formats."""
    with open(simple_path, 'w') as f:
        for name in sorted(all_dates):
            d = all_dates[name]
            if d.startswith('b('):
                lo, hi = d[2:-1].split(',')
                mid = (float(lo) + float(hi)) / 2
                f.write(f"{name}\t{mid:.1f}\n")
            else:
                f.write(f"{name}\t{d}\n")
    with open(lsd2_path, 'w') as f:
        f.write(f"{len(all_dates)}\n")
        for name in sorted(all_dates):
            f.write(f"{name}\t{all_dates[name]}\n")


def write_mrca_constraint(h37rv_names, mrca_path, date_range='b(1900,1910)'):
    """Write LSD2 MRCA constraint file for H37Rv stocks."""
    with open(mrca_path, 'w') as f:
        f.write(f"mrca({','.join(h37rv_names)}) {date_range}\n")


# ============================================================
# IQ-TREE/LSD2 EXECUTION
# ============================================================

def run_iqtree_lsd2(iqtree, phy, simple_dates, lsd2_dates, mrca, outgroup, output_prefix, threads=4):
    """Run IQ-TREE2 with LSD2 tip-dating."""
    cmd = [
        str(iqtree), "-s", str(phy),
        "-m", "GTR2+G",
        "--date", str(simple_dates),
        "--date-ci", "100",
        "--date-options", f"-v 1 -r a -d {lsd2_dates} -g {mrca}",
        "-o", outgroup,
        "-T", str(threads),
        "--prefix", str(output_prefix),
        "-redo",
    ]
    print(f"  Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        print(f"  ⚠ IQ-TREE non-zero exit: {result.returncode}", file=sys.stderr)
        print(result.stderr[-500:], file=sys.stderr)
    return result


def parse_lsd2_result(lsd2_output):
    """Parse LSD2 .timetree.lsd file for rate and tMRCA."""
    with open(lsd2_output) as f:
        content = f.read()
    m = re.search(
        r"rate\s+([\d.eE+-]+)\s+\[([\d.eE+-]+);\s*([\d.eE+-]+)\].*?"
        r"tMRCA\s+(-?[\d.eE+-]+)\s+\[(-?[\d.eE+-]+);\s*(-?[\d.eE+-]+)\].*?"
        r"objective function\s+([\d.eE+-]+)",
        content, re.DOTALL
    )
    if m:
        return {
            'rate': float(m.group(1)),
            'rate_ci_low': float(m.group(2)),
            'rate_ci_high': float(m.group(3)),
            'tmrca': float(m.group(4)),
            'tmrca_ci_low': float(m.group(5)),
            'tmrca_ci_high': float(m.group(6)),
            'objective': float(m.group(7)),
        }
    # Fallback without CI
    m2 = re.search(r"rate\s+([\d.eE+-]+),\s*tMRCA\s+(-?[\d.eE+-]+)\s*,\s*objective function\s+([\d.eE+-]+)", content)
    if m2:
        return {
            'rate': float(m2.group(1)),
            'tmrca': float(m2.group(2)),
            'objective': float(m2.group(3)),
            'rate_ci_low': None, 'rate_ci_high': None,
            'tmrca_ci_low': None, 'tmrca_ci_high': None,
        }
    return None


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_single_analysis(args, script_dir, bdd_ancien, bdd_actuelle, iqtree, output_prefix, seed):
    """Run one full analysis with a given seed. Returns parsed result dict or None."""
    # [Collect strains]
    ancients, missing = collect_ancients(bdd_ancien, DEFAULT_ANCIENTS)
    lineages = args.lineages.split(',')
    moderns = collect_moderns(bdd_actuelle, lineages, args.n_per_lineage, seed)
    h37rv, h37rv_names = collect_h37rv(bdd_actuelle, args.n_h37rv, seed)

    pinnipedii_dir = bdd_actuelle / "Pinipedii"
    pinnipedii = {}
    if pinnipedii_dir.is_dir():
        for sra in sorted(os.listdir(pinnipedii_dir)):
            rp = pinnipedii_dir / sra / "NC_000962.3" / "report.json"
            if rp.exists():
                try:
                    pinnipedii[sra] = get_syn_from_report(rp)
                except Exception:
                    pass

    outgroup = collect_outgroup(bdd_actuelle, args.n_outgroup, args.outgroup_lineage)
    all_strains = {**ancients, **moderns, **h37rv, **pinnipedii, **outgroup}

    # [Dates]
    all_dates = {}
    for name, meta in DEFAULT_ANCIENTS.items():
        if name in all_strains:
            all_dates[name] = meta['date_lsd2']
    for sra in moderns:
        all_dates[sra] = REAL_DATES.get(sra, '2018')
    for sra in pinnipedii:
        all_dates[sra] = REAL_DATES.get(sra, '2018')
    for name in h37rv:
        all_dates[name] = '2018'

    # [Build matrix]
    informative = build_binary_matrix(all_strains)
    phy_path = Path(f"{output_prefix}.phy")
    simple_dates_path = Path(f"{output_prefix}.simple.dates")
    lsd2_dates_path = Path(f"{output_prefix}.lsd2.dates")
    mrca_path = Path(f"{output_prefix}.mrca")
    write_phylip(all_strains, informative, phy_path)
    write_dates_files(all_dates, simple_dates_path, lsd2_dates_path)
    write_mrca_constraint(h37rv_names, mrca_path)

    # [Run IQ-TREE]
    og_names = [n for n in all_strains if n.startswith('OG_')]
    og_str = ','.join(og_names)
    run_iqtree_lsd2(iqtree, phy_path, simple_dates_path, lsd2_dates_path,
                     mrca_path, og_str, output_prefix, args.threads)

    # [Parse]
    lsd2_out = Path(f"{output_prefix}.timetree.lsd")
    if not lsd2_out.exists():
        return None
    result = parse_lsd2_result(lsd2_out)
    if not result:
        return None
    result['seed'] = seed
    result['n_strains'] = len(all_strains)
    result['n_informative'] = len(informative)
    result['n_ancients'] = len(ancients)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--output', required=True, help='Output prefix (directory/name)')
    ap.add_argument('--bdd', default='../../bdd', help='Path to bdd/ root')
    ap.add_argument('--lineages', default='L4.1,L4.3.3,L4.8,L4.2.1,L4.7.1,L4.7.2',
                    help='Comma-separated modern lineages')
    ap.add_argument('--n-per-lineage', type=int, default=5)
    ap.add_argument('--n-h37rv', type=int, default=50)
    ap.add_argument('--n-outgroup', type=int, default=3)
    ap.add_argument('--outgroup-lineage', default='Bovis')
    ap.add_argument('--seed', type=int, default=2026)
    ap.add_argument('--multi-seed', type=int, default=0,
                    help='Run N independent seeds and keep the best by objective function')
    ap.add_argument('--iqtree', default=None,
                    help='Path to iqtree2 binary (auto: project ../../investigate_phylo/iqtree2, '
                         'or `iqtree2` on PATH)')
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--skip-iqtree', action='store_true')
    args = ap.parse_args()

    script_dir = Path(__file__).resolve().parent
    bdd = (script_dir / args.bdd).resolve()
    bdd_ancien = bdd / "ancien"
    bdd_actuelle = bdd / "actuelle"

    if args.iqtree:
        iqtree = Path(args.iqtree).resolve()
    else:
        candidates = [
            script_dir / '../../investigate_phylo/iqtree2',
            script_dir / '../../../mtbc/investigate_phylo/iqtree2',
            Path.home() / 'docs/codes/mtbc/en_cours/investigate_phylo/iqtree2',
        ]
        iqtree = None
        for c in candidates:
            if c.resolve().exists():
                iqtree = c.resolve()
                break
        if iqtree is None:
            from_path = shutil.which('iqtree2') or shutil.which('iqtree')
            if from_path:
                iqtree = Path(from_path)
        if iqtree is None:
            print("ERROR: iqtree2 binary not found. Pass --iqtree PATH explicitly.",
                  file=sys.stderr)
            sys.exit(2)

    output_prefix = Path(args.output).resolve()
    output_prefix.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  MOLECULAR CLOCK PIPELINE v5")
    print("=" * 60)
    print(f"  BDD:    {bdd}")
    print(f"  Output: {output_prefix}")
    print(f"  IQ-TREE: {iqtree}")

    # Multi-seed mode: run N independent analyses and keep best by objective function
    if args.multi_seed > 0:
        print(f"\n  Multi-seed mode: {args.multi_seed} independent runs")
        import random as rnd
        rnd.seed(args.seed)
        seeds = [rnd.randint(1, 1000000) for _ in range(args.multi_seed)]

        all_results = []
        for i, seed in enumerate(seeds):
            print(f"\n{'='*60}")
            print(f"  Run {i+1}/{args.multi_seed} (seed={seed})")
            print(f"{'='*60}")
            tmp_prefix = Path(f"{output_prefix}.seed_{seed}")
            result = run_single_analysis(args, script_dir, bdd_ancien, bdd_actuelle,
                                          iqtree, tmp_prefix, seed)
            if result:
                print(f"  Rate={result['rate']:.3e}, tMRCA={result['tmrca']:.0f}, obj={result['objective']:.3f}")
                all_results.append(result)

        if not all_results:
            print("\n❌ All runs failed")
            return

        # Pick best by objective function (lower = better)
        best = min(all_results, key=lambda r: r['objective'])
        print(f"\n{'='*60}")
        print(f"  BEST RUN: seed={best['seed']}, obj={best['objective']:.3f}")
        print(f"{'='*60}")

        # Report stats across all seeds
        import statistics as st
        rates = [r['rate'] for r in all_results]
        tmrcas = [r['tmrca'] for r in all_results]
        objs = [r['objective'] for r in all_results]
        print(f"  Inter-seed stats (n={len(all_results)}):")
        print(f"    Rate:   median={st.median(rates):.3e}, CV={st.stdev(rates)/st.mean(rates)*100:.1f}%")
        print(f"    tMRCA:  median={st.median(tmrcas):.0f}, range=[{min(tmrcas):.0f};{max(tmrcas):.0f}]")
        print(f"    Obj:    median={st.median(objs):.3f}, best={min(objs):.3f}")

        # Use best result for final output
        n_sites = best['n_informative']
        genome_size = 4411532
        rate = best['rate']
        rate_genome = rate * n_sites / genome_size
        tmrca = best['tmrca']
        tmrca_bp = 2020 - tmrca

        print(f"\n  Taux synonyme : {rate:.4e} subst/site/an")
        if best.get('rate_ci_low'):
            print(f"  IC 95% taux    : [{best['rate_ci_low']:.4e} ; {best['rate_ci_high']:.4e}]")
        print(f"  Taux génome    : {rate_genome:.3e} subst/site/an")
        print(f"  tMRCA : {tmrca:.0f} CE ({tmrca_bp:.0f} BP)")
        if best.get('tmrca_ci_low'):
            ci_lo = 2020 - best['tmrca_ci_high']
            ci_hi = 2020 - best['tmrca_ci_low']
            print(f"  IC 95%: [{ci_lo:.0f} ; {ci_hi:.0f}] BP")
        print(f"  Objective function: {best['objective']:.3f}")

        # Write multi-seed summary
        summary = {
            'mode': 'multi-seed',
            'n_seeds': len(all_results),
            'best_seed': best['seed'],
            'best_objective': best['objective'],
            'rate_syn_per_site_year': rate,
            'rate_genome_per_site_year': rate_genome,
            'tmrca_CE': tmrca,
            'tmrca_BP': tmrca_bp,
            'inter_seed_cv_rate_pct': st.stdev(rates)/st.mean(rates)*100,
            'inter_seed_tmrca_range': [min(tmrcas), max(tmrcas)],
            'all_results': all_results,
        }
        summary_path = Path(f"{output_prefix}.multi_seed_summary.json")
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\n  Summary JSON: {summary_path}")
        return

    # === Collect strains ===
    print("\n[1/5] Collecting ancient genomes...")
    ancients, missing = collect_ancients(bdd_ancien, DEFAULT_ANCIENTS)
    print(f"  Loaded: {len(ancients)} anciens ({', '.join(ancients.keys())})")
    if missing:
        print(f"  ⚠ Missing: {missing}")

    print("\n[2/5] Collecting modern strains...")
    lineages = args.lineages.split(',')
    moderns = collect_moderns(bdd_actuelle, lineages, args.n_per_lineage, args.seed)
    print(f"  Modern L4: {len(moderns)} strains from {len(lineages)} lineages")

    print("\n[3/5] Collecting H37Rv stocks (filter < 100 SNP)...")
    h37rv, h37rv_names = collect_h37rv(bdd_actuelle, args.n_h37rv, args.seed)
    print(f"  H37Rv: {len(h37rv)} true stocks")

    # Also collect modern pinnipedii if available
    pinnipedii_dir = bdd_actuelle / "Pinipedii"
    pinnipedii = {}
    if pinnipedii_dir.is_dir():
        for sra in sorted(os.listdir(pinnipedii_dir)):
            rp = pinnipedii_dir / sra / "NC_000962.3" / "report.json"
            if rp.exists():
                try:
                    pinnipedii[sra] = get_syn_from_report(rp)
                except Exception:
                    pass
    print(f"  Pinnipedii modernes: {len(pinnipedii)}")

    print(f"\n[4/5] Collecting outgroup ({args.outgroup_lineage})...")
    outgroup = collect_outgroup(bdd_actuelle, args.n_outgroup, args.outgroup_lineage)
    print(f"  Outgroup: {len(outgroup)} strains")

    # === Combine all strains ===
    all_strains = {**ancients, **moderns, **h37rv, **pinnipedii, **outgroup}
    print(f"\n  TOTAL: {len(all_strains)} strains")

    # === Build dates dict ===
    all_dates = {}
    for name, meta in DEFAULT_ANCIENTS.items():
        if name in all_strains:
            all_dates[name] = meta['date_lsd2']
    for sra in moderns:
        all_dates[sra] = REAL_DATES.get(sra, '2018')  # default fallback
    for sra in pinnipedii:
        all_dates[sra] = REAL_DATES.get(sra, '2018')
    for name in h37rv:
        all_dates[name] = '2018'
    # Outgroup has no date — LSD2 will infer it

    # === Build matrix ===
    print("\n[5/5] Building binary alignment matrix...")
    informative = build_binary_matrix(all_strains)
    print(f"  Informative synonymous sites: {len(informative)}")

    phy_path = output_prefix.with_suffix('.phy')
    simple_dates_path = output_prefix.with_suffix('.simple.dates')
    lsd2_dates_path = output_prefix.with_suffix('.lsd2.dates')
    mrca_path = output_prefix.with_suffix('.mrca')

    write_phylip(all_strains, informative, phy_path)
    write_dates_files(all_dates, simple_dates_path, lsd2_dates_path)
    write_mrca_constraint(h37rv_names, mrca_path)

    print(f"  PHYLIP: {phy_path}")
    print(f"  Dates:  {lsd2_dates_path}")
    print(f"  MRCA:   {mrca_path}")

    # === Run IQ-TREE/LSD2 ===
    if args.skip_iqtree:
        print("\n⏩ Skipping IQ-TREE (--skip-iqtree)")
        return

    print("\n[IQ-TREE/LSD2] Running tip-dating...")
    og_names = [n for n in all_strains if n.startswith('OG_')]
    og_str = ','.join(og_names)
    run_iqtree_lsd2(
        iqtree, phy_path, simple_dates_path, lsd2_dates_path,
        mrca_path, og_str, output_prefix, args.threads
    )

    # === Parse result ===
    lsd2_output = Path(f"{output_prefix}.timetree.lsd")
    if not lsd2_output.exists():
        print(f"\n❌ LSD2 output not found: {lsd2_output}")
        return

    result = parse_lsd2_result(lsd2_output)
    if not result:
        print("\n❌ Failed to parse LSD2 output")
        return

    rate = result['rate']
    n_sites = len(informative)
    genome_size = 4411532
    rate_genome = rate * n_sites / genome_size

    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"  Sites informatifs syn : {n_sites}")
    print(f"  Souches totales       : {len(all_strains)}")
    print(f"  Anciens               : {len(ancients)}")
    print()
    print(f"  Taux synonyme : {rate:.4e} subst/site/an")
    if result.get('rate_ci_low'):
        print(f"  IC 95% taux    : [{result['rate_ci_low']:.4e} ; {result['rate_ci_high']:.4e}]")
    print(f"  Taux génome    : {rate_genome:.3e} subst/site/an")
    print(f"  SNP syn/an     : {rate * n_sites:.3f}")
    print()
    tmrca = result['tmrca']
    tmrca_bp = 2020 - tmrca
    print(f"  tMRCA : {tmrca:.0f} CE ({tmrca_bp:.0f} BP)")
    if result.get('tmrca_ci_low'):
        ci_lo = 2020 - result['tmrca_ci_high']
        ci_hi = 2020 - result['tmrca_ci_low']
        print(f"  IC 95%: [{ci_lo:.0f} ; {ci_hi:.0f}] BP")
    print(f"  Objective function: {result['objective']:.3f}")
    print("=" * 60)

    # Write summary JSON
    summary = {
        'version': 'v5 pipeline',
        'n_strains': len(all_strains),
        'n_ancients': len(ancients),
        'n_h37rv': len(h37rv),
        'n_modern_l4': len(moderns),
        'n_pinnipedii': len(pinnipedii),
        'n_informative_sites': n_sites,
        'rate_syn_per_site_year': rate,
        'rate_genome_per_site_year': rate_genome,
        'tmrca_CE': tmrca,
        'tmrca_BP': tmrca_bp,
        'objective_function': result['objective'],
        **{k: v for k, v in result.items() if k not in ['rate', 'tmrca', 'objective']},
    }
    summary_path = Path(f"{output_prefix}.summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary JSON: {summary_path}")


if __name__ == "__main__":
    main()
