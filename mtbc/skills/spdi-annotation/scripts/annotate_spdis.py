#!/usr/bin/env python3
"""
SPDI Annotation — Functional annotation of MTBC variants.

Two-step strategy:
  1. Query TBannotator MCP for existing annotations (if available)
  2. Fall back to local GenBank/GFF3 annotation for missing SPDIs

CRITICAL: SPDI ref/alt are ALWAYS on the forward (+) strand.
          Never complement(alt) before revcomp — that causes double complementation.

Usage:
    python3 annotate_spdis.py input.csv --gff3 NC_000962.3.gff3 --genbank NC_000962.3.gb -o annotated.csv
    python3 annotate_spdis.py input.txt --skip-tbannotator -o annotated.csv
"""

import argparse
import bisect
import csv
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote


# ── Mycobrowser-derived functional categories ────────────────────────
FUNCTIONAL_CATEGORIES = {
    'PE_PGRS': 'PE/PPE', 'PE_': 'PE/PPE', 'PPE': 'PE/PPE',
    'fadD': 'Lipid metabolism', 'fadE': 'Lipid metabolism',
    'fadA': 'Lipid metabolism', 'fadB': 'Lipid metabolism',
    'fadH': 'Lipid metabolism', 'fas': 'Lipid metabolism',
    'pks': 'Lipid metabolism', 'accD': 'Lipid metabolism',
    'accA': 'Lipid metabolism', 'accE': 'Lipid metabolism',
    'desA': 'Lipid metabolism', 'mmaA': 'Lipid metabolism',
    'kasA': 'Lipid metabolism', 'kasB': 'Lipid metabolism',
    'mycP': 'Lipid metabolism', 'myc': 'Lipid metabolism',
    'mbt': 'Lipid metabolism',
    'rpoB': 'Information pathways', 'rpoC': 'Information pathways',
    'rpsL': 'Information pathways', 'rrs': 'Information pathways',
    'gyrA': 'Information pathways', 'gyrB': 'Information pathways',
    'rps': 'Information pathways', 'rpl': 'Information pathways',
    'mmpL': 'Cell wall & cell processes', 'mmpS': 'Cell wall & cell processes',
    'ecc': 'Cell wall & cell processes', 'esx': 'Cell wall & cell processes',
    'espA': 'Cell wall & cell processes', 'espB': 'Cell wall & cell processes',
    'espC': 'Cell wall & cell processes', 'espD': 'Cell wall & cell processes',
    'espK': 'Cell wall & cell processes',
    'murA': 'Cell wall & cell processes', 'murB': 'Cell wall & cell processes',
    'murC': 'Cell wall & cell processes', 'murD': 'Cell wall & cell processes',
    'murE': 'Cell wall & cell processes', 'murF': 'Cell wall & cell processes',
    'murG': 'Cell wall & cell processes', 'lprG': 'Cell wall & cell processes',
    'pbp': 'Cell wall & cell processes', 'sec': 'Cell wall & cell processes',
    'tat': 'Cell wall & cell processes', 'mce': 'Cell wall & cell processes',
    'lpp': 'Cell wall & cell processes',
    'glnA': 'Intermediary metabolism & respiration',
    'aroE': 'Intermediary metabolism & respiration',
    'sthA': 'Intermediary metabolism & respiration',
    'ilvB': 'Intermediary metabolism & respiration',
    'atsB': 'Intermediary metabolism & respiration',
    'cyd': 'Intermediary metabolism & respiration',
    'nuo': 'Intermediary metabolism & respiration',
    'nar': 'Intermediary metabolism & respiration',
    'nir': 'Intermediary metabolism & respiration',
    'ace': 'Intermediary metabolism & respiration',
    'frd': 'Intermediary metabolism & respiration',
    'prr': 'Regulatory proteins', 'sig': 'Regulatory proteins',
    'sir': 'Regulatory proteins', 'pkn': 'Regulatory proteins',
    'dev': 'Regulatory proteins', 'dos': 'Regulatory proteins',
    'whiB': 'Regulatory proteins', 'csp': 'Regulatory proteins',
}


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


def complement(base):
    return {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}.get(base.upper(), 'N')


def revcomp(s):
    return ''.join(complement(b) for b in reversed(s))


# ── GFF3 parsing ─────────────────────────────────────────────────────

def parse_gff3_attributes(attr_str):
    attrs = {}
    for item in attr_str.split(';'):
        if '=' in item:
            key, val = item.split('=', 1)
            attrs[key] = unquote(val)
    return attrs


def load_gene_index(gff3_path):
    """Build position-indexed gene database from GFF3."""
    genes = []
    with open(gff3_path) as f:
        for line in f:
            if line.startswith('#'):
                continue
            parts = line.strip().split('\t')
            if len(parts) < 9:
                continue
            seqid, source, ftype, start, end, score, strand, phase, attrs_str = parts
            if ftype not in ('gene', 'CDS', 'tRNA', 'rRNA', 'ncRNA', 'pseudogene'):
                continue
            attrs = parse_gff3_attributes(attrs_str)
            genes.append({
                'start': int(start), 'end': int(end), 'strand': strand,
                'gene': attrs.get('gene', attrs.get('Name', '')),
                'locus_tag': attrs.get('locus_tag', ''),
                'product': attrs.get('product', ''),
                'type': ftype,
                'pseudo': attrs.get('pseudo', '') == 'true',
            })

    # Deduplicate: prefer CDS over gene for same locus_tag
    by_locus = defaultdict(list)
    others = []
    for g in genes:
        lt = g['locus_tag']
        if lt:
            by_locus[lt].append(g)
        else:
            others.append(g)

    deduped = []
    for lt, entries in by_locus.items():
        cds = [e for e in entries if e['type'] == 'CDS']
        if cds:
            best = cds[0].copy()
            gene_entries = [e for e in entries if e['type'] == 'gene']
            if gene_entries and not best['gene']:
                best['gene'] = gene_entries[0]['gene']
            deduped.append(best)
        else:
            deduped.append(entries[0])
    deduped.extend(others)
    deduped.sort(key=lambda x: x['start'])
    return deduped


def find_gene_at_position(genes, pos):
    """Find gene at 1-based position using binary search."""
    starts = [g['start'] for g in genes]
    idx = bisect.bisect_right(starts, pos) - 1
    hits = []
    for i in range(max(0, idx - 1), min(len(genes), idx + 3)):
        g = genes[i]
        if g['start'] <= pos <= g['end']:
            hits.append(g)
    if hits:
        cds_hits = [h for h in hits if h['type'] == 'CDS']
        return (cds_hits[0] if cds_hits else hits[0]), False, None, None
    upstream = genes[idx] if idx >= 0 else None
    downstream = genes[idx + 1] if idx + 1 < len(genes) else None
    return None, True, upstream, downstream


# ── Genome sequence ──────────────────────────────────────────────────

def load_genome_sequence(gb_path):
    """Load genome sequence from GenBank file."""
    seq_lines = []
    in_seq = False
    with open(gb_path) as f:
        for line in f:
            if line.startswith('ORIGIN'):
                in_seq = True
                continue
            if line.startswith('//'):
                break
            if in_seq:
                seq_lines.append(re.sub(r'[\s\d]', '', line.strip()))
    return ''.join(seq_lines).upper()


# ── Codon change analysis ────────────────────────────────────────────

def get_codon_change(seq, gene_info, pos_1based, ref, alt):
    """
    Determine variant effect (missense/synonymous/stop/frameshift).

    CRITICAL: ref and alt in SPDI are ALWAYS on the forward (+) strand.
    For negative-strand genes, substitute alt directly into the forward codon,
    then revcomp the whole codon. NEVER complement(alt) before substitution.
    """
    if not gene_info or gene_info['type'] not in ('CDS', 'pseudogene'):
        return 'unknown', ''

    # Indels
    if len(ref) != 1 or len(alt) != 1:
        if len(ref) > len(alt):
            return 'deletion', ''
        elif len(ref) < len(alt):
            if (len(alt) - len(ref)) % 3 == 0:
                return 'inframe_insertion', ''
            return 'frameshift_variant', ''
        return 'complex', ''

    pos_0 = pos_1based - 1
    strand = gene_info['strand']
    gene_start_0 = gene_info['start'] - 1
    gene_end = gene_info['end']

    try:
        if strand == '+':
            cds_pos = pos_0 - gene_start_0
            codon_idx = cds_pos // 3
            codon_offset = cds_pos % 3
            codon_start = gene_start_0 + codon_idx * 3

            ref_codon = seq[codon_start:codon_start + 3]
            alt_codon = list(ref_codon)
            alt_codon[codon_offset] = alt.upper()
            alt_codon = ''.join(alt_codon)

        else:  # Minus strand
            cds_pos = gene_end - pos_1based
            codon_idx = cds_pos // 3
            codon_offset = cds_pos % 3
            codon_end_0 = gene_end - 1 - codon_idx * 3
            codon_start_0 = codon_end_0 - 2

            fwd_codon = seq[codon_start_0:codon_start_0 + 3]
            ref_codon = revcomp(fwd_codon)

            # CORRECT: alt is already on forward strand — substitute directly
            fwd_alt = list(fwd_codon)
            fwd_alt[2 - codon_offset] = alt.upper()  # NO complement() here!
            alt_codon = revcomp(''.join(fwd_alt))

        if len(ref_codon) != 3 or len(alt_codon) != 3:
            return 'unknown', ''

        ref_aa = CODON_TABLE.get(ref_codon, '?')
        alt_aa = CODON_TABLE.get(alt_codon, '?')
        aa_pos = (cds_pos // 3) + 1
        aa_change = f"{ref_aa}{aa_pos}{alt_aa}"

        if ref_aa == alt_aa:
            return 'synonymous_variant', aa_change
        elif alt_aa == '*':
            return 'stop_gained', aa_change
        elif ref_aa == '*':
            return 'stop_lost', aa_change
        else:
            return 'missense_variant', aa_change

    except (IndexError, KeyError):
        return 'unknown', ''


# ── Functional category ──────────────────────────────────────────────

def guess_functional_category(gene_name, product):
    if not gene_name and not product:
        return 'Unknown'
    name = gene_name or ''
    prod = (product or '').lower()
    for prefix, cat in FUNCTIONAL_CATEGORIES.items():
        if name.startswith(prefix):
            return cat
    if any(w in prod for w in ['hypothetical', 'uncharacterized', 'unknown function']):
        return 'Conserved hypotheticals'
    if any(w in prod for w in ['membrane', 'transporter', 'permease', 'efflux',
                                'secretion', 'cell division', 'cell wall']):
        return 'Cell wall & cell processes'
    if any(w in prod for w in ['kinase', 'regulator', 'transcription', 'repressor',
                                'activator', 'sigma']):
        return 'Regulatory proteins'
    if any(w in prod for w in ['ribosom', 'polymerase', 'helicase', 'topoisomerase']):
        return 'Information pathways'
    if any(w in prod for w in ['lipid', 'fatty', 'acyl', 'myco']):
        return 'Lipid metabolism'
    if any(w in prod for w in ['dehydrogenase', 'synthase', 'reductase', 'oxidase',
                                'transferase', 'hydrolase', 'isomerase', 'mutase']):
        return 'Intermediary metabolism & respiration'
    if any(w in prod for w in ['pe-pgrs', 'pe family', 'ppe family']):
        return 'PE/PPE'
    if any(w in prod for w in ['insertion', 'transposase', 'phage']):
        return 'Insertion sequences & phages'
    return 'Unknown'


# ── Promoteurs de resistance (positions H37Rv NC_000962.3, litterature revue) ──
# Region promotrice = fenetre en amont du start (sens du gene), ou des mutations
# regulatrices sont associees a la resistance mais tombent en "intergenique".
# Chaque entree : gene -> (drogue, gene_start, gene_strand). La fenetre par
# defaut est de PROMOTER_WINDOW pb en amont (5') du gene.
RESISTANCE_PROMOTERS = {
    'eis':   ('kanamycin/amikacin', 2715332, '-'),   # Rv2416c
    'pncA':  ('pyrazinamide',       2289241, '-'),   # Rv2043c
    'ethA':  ('ethionamide',        4326004, '-'),   # Rv3854c
    'whiB7': ('macrolides/aminoglyc', 3568402, '+'), # Rv3197A
    'ahpC':  ('isoniazid (compens.)', 2726192, '+'), # Rv2428
    'embA':  ('ethambutol',         4243186, '+'),   # Rv3794 (promoteur embCAB)
}
PROMOTER_WINDOW = 200  # pb en amont; -35/-10 et sites regulateurs connus


def check_resistance_promoter(pos):
    """Retourne (gene, drogue, dist_bp) si pos tombe dans un promoteur de
    resistance connu, sinon None. dist_bp = distance en amont du start."""
    for gene, (drug, start, strand) in RESISTANCE_PROMOTERS.items():
        if strand == '+':
            # promoteur = [start - WINDOW, start)
            if start - PROMOTER_WINDOW <= pos < start:
                return gene, drug, start - pos
        else:
            # gene sur brin -, "start" = extremite 5' = borne haute
            if start < pos <= start + PROMOTER_WINDOW:
                return gene, drug, pos - start
    return None


def classify_impact(effect):
    return {
        'missense_variant': 'MODERATE',
        'synonymous_variant': 'LOW',
        'stop_gained': 'HIGH',
        'stop_lost': 'HIGH',
        'frameshift_variant': 'HIGH',
        'inframe_insertion': 'MODERATE',
        'inframe_deletion': 'MODERATE',
        'deletion': 'MODERATE',
        'upstream_promoter_variant': 'MODERATE',  # promoteur de resistance
        'intergenic_region': 'MODIFIER',
        'complex': 'MODERATE',
        'unknown': 'MODIFIER',
    }.get(effect, 'MODIFIER')


# ── TBannotator query ────────────────────────────────────────────────

def query_tbannotator_annotations(spdis):
    """
    Query TBannotator MCP for existing SPDI annotations.
    Returns dict: spdi -> {gene, effect, aa_change, locus_tag}
    Returns empty dict if server unavailable.
    """
    if not spdis:
        return {}

    # Build SQL with batches of 500
    results = {}
    batch_size = 500
    spdi_list = list(spdis)

    for i in range(0, len(spdi_list), batch_size):
        batch = spdi_list[i:i + batch_size]
        quoted = ", ".join(f"'{s}'" for s in batch)
        sql = f"""
            SELECT DISTINCT ON (s.spdi)
                s.spdi, s.gene, s.effect, s.amino_acid_change, s.locus_tag
            FROM tb_report_snp s
            WHERE s.spdi IN ({quoted})
        """

        try:
            # Try MCP tool via claude CLI subprocess
            proc = subprocess.run(
                ['claude', '--print', '-p',
                 f'Use mcp__tbannotator__tool_query_postgres to run this SQL and return the raw results as JSON: {sql}'],
                capture_output=True, text=True, timeout=60
            )
            if proc.returncode == 0 and proc.stdout.strip():
                # Parse response — expect JSON rows
                try:
                    data = json.loads(proc.stdout)
                    if isinstance(data, list):
                        for row in data:
                            spdi = row.get('spdi', '')
                            if spdi:
                                results[spdi] = {
                                    'gene': row.get('gene', ''),
                                    'effect': row.get('effect', ''),
                                    'aa_change': row.get('amino_acid_change', ''),
                                    'locus_tag': row.get('locus_tag', ''),
                                }
                except json.JSONDecodeError:
                    pass
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            print("  [TBannotator] Server unavailable, using local annotation only",
                  file=sys.stderr)
            return {}

    return results


# ── Input parsing ────────────────────────────────────────────────────

def load_spdis(input_path):
    """Load SPDIs from CSV (with SPDI column) or plain text."""
    path = Path(input_path)
    rows = []

    with open(path, newline='', encoding='utf-8-sig') as f:
        first_line = f.readline().strip()
        f.seek(0)

        if ',' in first_line and 'SPDI' in first_line.upper():
            # CSV with header
            reader = csv.DictReader(f)
            for row in reader:
                spdi_key = next((k for k in row if k.upper() == 'SPDI'), None)
                if spdi_key and row[spdi_key]:
                    rows.append(dict(row))
        else:
            # Plain text, one SPDI per line
            f.seek(0)
            for line in f:
                spdi = line.strip()
                if spdi and not spdi.startswith('#'):
                    rows.append({'SPDI': spdi})

    return rows


# ── Main pipeline ────────────────────────────────────────────────────

def annotate(input_path, gff3_path, gb_path, output_path,
             use_tbannotator=True):
    """Main annotation pipeline."""

    print(f"Loading SPDIs from {input_path}...")
    rows = load_spdis(input_path)
    all_spdis = {r.get('SPDI', r.get('spdi', '')) for r in rows}
    print(f"  {len(rows)} SPDIs to annotate")

    # Step 1: Query TBannotator
    tba_annotations = {}
    if use_tbannotator:
        print("Querying TBannotator for existing annotations...")
        tba_annotations = query_tbannotator_annotations(all_spdis)
        print(f"  {len(tba_annotations)} annotations found in TBannotator")

    # Step 2: Local annotation for the rest
    missing = all_spdis - set(tba_annotations.keys())
    genes = None
    seq = None
    if missing:
        print(f"Local annotation for {len(missing)} remaining SPDIs...")
        print(f"  Loading GFF3: {gff3_path}")
        genes = load_gene_index(gff3_path)
        print(f"  Loading GenBank: {gb_path}")
        seq = load_genome_sequence(gb_path)
        print(f"  {len(genes)} gene features, {len(seq)} bp genome")

    # Annotate all rows
    annotated = []
    for row in rows:
        spdi = row.get('SPDI', row.get('spdi', ''))
        parts = spdi.split(':')
        if len(parts) != 4:
            print(f"  Warning: cannot parse SPDI: {spdi}", file=sys.stderr)
            continue

        pos_0based = int(parts[1])
        ref, alt = parts[2], parts[3]
        pos_1based = pos_0based + 1

        if spdi in tba_annotations:
            # Use TBannotator annotation
            tba = tba_annotations[spdi]
            gene_name = tba['gene'] or ''
            locus_tag = tba['locus_tag'] or ''
            effect = tba['effect'] or 'unknown'
            aa_change = tba['aa_change'] or ''
            product = ''
            strand = ''
            func_cat = guess_functional_category(gene_name, product)
            source = 'tbannotator'
        else:
            # Local annotation
            gene_info, is_intergenic, upstream, downstream = find_gene_at_position(
                genes, pos_1based)

            if is_intergenic:
                promo = check_resistance_promoter(pos_1based)
                if promo:
                    # Mutation dans un promoteur de resistance connu
                    pg, drug, dist = promo
                    gene_name = f"{pg} (promoteur)"
                    locus_tag = ''
                    product = f"Promoteur de {pg} — {drug} (-{dist} pb)"
                    effect = 'upstream_promoter_variant'
                    aa_change = f"c.-{dist}"
                    strand = ''
                    func_cat = 'Drug resistance (promoter)'
                else:
                    gene_name = 'intergenic'
                    locus_tag = ''
                    up_name = (upstream['gene'] or upstream['locus_tag']) if upstream else '?'
                    dn_name = (downstream['gene'] or downstream['locus_tag']) if downstream else '?'
                    product = f"Intergenic ({up_name} / {dn_name})"
                    effect = 'intergenic_region'
                    aa_change = ''
                    strand = ''
                    func_cat = 'Intergenic'
            else:
                gene_name = gene_info['gene'] or gene_info['locus_tag']
                locus_tag = gene_info['locus_tag']
                product = gene_info['product']
                strand = gene_info['strand']
                effect, aa_change = get_codon_change(seq, gene_info, pos_1based, ref, alt)
                func_cat = guess_functional_category(gene_name, product)
            source = 'local'

        impact = classify_impact(effect)

        annotated.append({
            **row,
            'Position': str(pos_1based),
            'Ref': ref,
            'Alt': alt,
            'Gene_name': gene_name,
            'Locus_tag': locus_tag,
            'Strand': strand,
            'Effect': effect,
            'Impact': impact,
            'AA_Change': aa_change,
            'Product': product,
            'Functional_Category': func_cat,
            'Annotation_Source': source,
        })

    # Write output
    if not annotated:
        print("No annotations produced.", file=sys.stderr)
        return []

    fieldnames = list(annotated[0].keys())
    out = open(output_path, 'w', newline='') if output_path else sys.stdout
    try:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(annotated)
    finally:
        if output_path:
            out.close()

    # Summary
    from collections import Counter
    effects = Counter(r['Effect'] for r in annotated)
    sources = Counter(r['Annotation_Source'] for r in annotated)
    print(f"\nAnnotation complete: {len(annotated)} SPDIs")
    print(f"  Sources: {dict(sources)}")
    print(f"  Effects: {dict(effects)}")

    return annotated


def main():
    parser = argparse.ArgumentParser(
        description="Annotate MTBC SPDI variants with gene, effect, and functional category.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 annotate_spdis.py spdis.csv --gff3 NC_000962.3.gff3 --genbank NC_000962.3.gb -o annotated.csv
  python3 annotate_spdis.py spdis.txt --skip-tbannotator -o annotated.csv
  python3 annotate_spdis.py markers.csv -o markers_annotated.csv
        """)

    parser.add_argument('input_file', help='CSV with SPDI column, or plain text (one SPDI per line)')
    parser.add_argument('--gff3', default='NC_000962.3.gff3', help='GFF3 annotation file')
    parser.add_argument('--genbank', default='NC_000962.3.gb', help='GenBank sequence file')
    parser.add_argument('-o', '--output', default=None, help='Output CSV path (default: stdout)')
    parser.add_argument('--skip-tbannotator', action='store_true',
                        help='Skip TBannotator query, annotate everything locally')

    args = parser.parse_args()

    annotate(
        input_path=args.input_file,
        gff3_path=args.gff3,
        gb_path=args.genbank,
        output_path=args.output,
        use_tbannotator=not args.skip_tbannotator,
    )


if __name__ == '__main__':
    main()
