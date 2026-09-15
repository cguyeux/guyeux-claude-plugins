#!/usr/bin/env python3
"""
Tests for the PGG (Principal Genetic Group) computation in
the mtbc-lineages skill (scripts/lineages.py).

Verifies:
  1. H37Rv reference state at katG codon 463 and gyrA codon 95
  2. SPDI → amino-acid computation on real strains from the BDD
  3. PGG label assignment logic
  4. Edge cases (no variants, Canettii divergence)

Run from the skill directory:
    python3 tests/test_pgg.py

Requires:
  - samtools on PATH (for fasta verification)
  - H37Rv reference at investigate_phylo/resources/NC_000962.3.fasta
  - BDD at mtbc/bdd/actuelle/
"""

import csv
import os
import subprocess
import sys
from pathlib import Path

# Add the parent directory so we can import the dispatch module
SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import lineages  # noqa: E402

HOME = Path.home()
FASTA = HOME / "docs/codes/mtbc/investigate_phylo/resources/NC_000962.3.fasta"
BDD = HOME / "docs/codes/mtbc/bdd/actuelle"


def samtools_base(fasta, chrom, pos_1based):
    """Read a single base from a fasta using samtools faidx (1-based)."""
    r = subprocess.check_output(
        ["samtools", "faidx", str(fasta), f"{chrom}:{pos_1based}-{pos_1based}"],
        text=True
    )
    return r.strip().split("\n")[-1].strip().upper()


def samtools_region(fasta, chrom, start, end):
    """Read a region from a fasta using samtools faidx (1-based, inclusive)."""
    r = subprocess.check_output(
        ["samtools", "faidx", str(fasta), f"{chrom}:{start}-{end}"],
        text=True
    )
    return "".join(r.strip().split("\n")[1:]).upper()


def load_spdis(lineage_name, strain_name):
    """Load a spdi.txt from the BDD."""
    p = BDD / lineage_name / strain_name / "NC_000962.3" / "spdi.txt"
    if not p.is_file():
        return None
    spdis = set()
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line and line.startswith("NC_"):
                spdis.add(line.split()[0])
    return spdis


# ── Test infrastructure ────────────────────────────────────────────────

passed = 0
failed = 0


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✓ {name}")
    else:
        failed += 1
        print(f"  ✗ {name}")
        if detail:
            print(f"    → {detail}")


# ── Tests ──────────────────────────────────────────────────────────────

def test_h37rv_reference_state():
    """Verify the H37Rv reference bases at the PGG codon positions,
    computed directly from NC_000962.3.fasta."""
    print("\n=== Test 1: H37Rv reference state (fasta verification) ===")
    if not FASTA.is_file():
        print("  SKIP: NC_000962.3.fasta not found")
        return

    # gyrA codon 95: 1-based [7584, 7585, 7586] → expected AGC (Ser)
    gyra = samtools_region(FASTA, "NC_000962.3", 7584, 7586)
    check("gyrA codon 95 + strand = AGC (Ser)",
          gyra == "AGC",
          f"got '{gyra}'")

    # katG codon 463: 1-based [2154723, 2154724, 2154725] → expected CCG
    katg_plus = samtools_region(FASTA, "NC_000962.3", 2154723, 2154725)
    check("katG codon 463 + strand = CCG",
          katg_plus == "CCG",
          f"got '{katg_plus}'")

    # katG minus-strand mRNA → rev-comp of CCG = CGG (Arg)
    rc = lineages.revcomp(katg_plus)
    check("katG codon 463 mRNA (rev-comp) = CGG (Arg)",
          rc == "CGG",
          f"got '{rc}'")

    # Sanity: katG codon 315 = Ser (the canonical S315T INH-R position)
    katg315_plus = samtools_region(FASTA, "NC_000962.3", 2155167, 2155169)
    katg315_mrna = lineages.revcomp(katg315_plus)
    katg315_aa = lineages.CODON_TABLE.get(katg315_mrna, "?")
    check("katG codon 315 = Ser (S315T sanity check)",
          katg315_aa == "S",
          f"got '{katg315_aa}' (+ strand={katg315_plus}, mRNA={katg315_mrna})")


def test_h37rv_as_sample():
    """Verify that a sample with no variants at katG/gyrA → same as H37Rv = PGG3."""
    print("\n=== Test 2: H37Rv-like sample (no variants) ===")
    empty_spdis = set()

    katg = lineages.compute_sample_aa(lineages.KATG_CODON_463, empty_spdis)
    check("katG463 with no variants = R (Arg, derived)",
          katg["aa"] == "R",
          f"got '{katg['aa']}' (codon={katg['mrna_codon']})")

    gyra = lineages.compute_sample_aa(lineages.GYRA_CODON_95, empty_spdis)
    check("gyrA95 with no variants = S (Ser, derived)",
          gyra["aa"] == "S",
          f"got '{gyra['aa']}' (codon={gyra['mrna_codon']})")

    label = lineages.pgg_label(katg["aa"], gyra["aa"])
    check("PGG label for R+S = PGG3 (H37Rv = both derived)",
          label == "PGG3",
          f"got '{label}'")


def test_real_strains():
    """Test PGG computation on real strains from the BDD.

    Expected (from variant survey):
      L1.1/CUS0000310  : both variants → Leu + Thr → PGG2
      L2.2.1/CUS0000026: both variants → Leu + Thr → PGG2
      L4.1/CUS0000008  : gyrA only     → Arg + Thr → PGG1
      L4.9/CUS0000175  : no variants   → Arg + Ser → non-canonical
      L4.15/ERR1023322 : no variants   → Arg + Ser → non-canonical
      L9/ERR181314     : both variants → Leu + Thr → PGG2
    """
    print("\n=== Test 3: Real strains from BDD ===")

    test_cases = [
        # (lineage, strain, expected_katg_aa, expected_gyra_aa, expected_pgg)
        ("L1.1", "CUS0000310", "L", "T", "PGG1"),       # ancestral at both
        ("L2.2.1", "CUS0000026", "L", "T", "PGG1"),     # proto-Beijing = PGG1
        ("L4.1", "CUS0000008", "R", "T", "PGG2"),         # intermediate L4 (R+T)
        ("L4.9", "CUS0000175", "R", "S", "PGG3"),        # H37Rv-like = PGG3
        ("L4.15", "ERR1023322", "R", "S", "PGG3"),       # H37Rv-like = PGG3
        ("L9", "ERR181314", "L", "T", "PGG1"),           # ancestral at both
    ]

    for lin, strain, exp_katg, exp_gyra, exp_pgg in test_cases:
        spdis = load_spdis(lin, strain)
        if spdis is None:
            print(f"  SKIP: {lin}/{strain} spdi.txt not found")
            continue

        katg = lineages.compute_sample_aa(lineages.KATG_CODON_463, spdis)
        gyra = lineages.compute_sample_aa(lineages.GYRA_CODON_95, spdis)
        label = lineages.pgg_label(katg["aa"], gyra["aa"])

        check(f"{lin}/{strain} katG463 = {exp_katg}",
              katg["aa"] == exp_katg,
              f"got '{katg['aa']}' (codon={katg['mrna_codon']}, applied={katg['applied']})")
        check(f"{lin}/{strain} gyrA95 = {exp_gyra}",
              gyra["aa"] == exp_gyra,
              f"got '{gyra['aa']}' (codon={gyra['mrna_codon']}, applied={gyra['applied']})")
        check(f"{lin}/{strain} PGG = {exp_pgg or 'non-canonical'}",
              label == exp_pgg,
              f"got '{label}'")


def test_pgg2_real_strain():
    """Verify PGG2 on a real L2.2.2 modern Beijing strain."""
    print("\n=== Test 3b: PGG2 real strain (L2.2.2 modern Beijing) ===")
    spdis = load_spdis("L2.2.2", "ERR4831569")
    if spdis is None:
        print("  SKIP: L2.2.2/ERR4831569 not found")
        return
    katg = lineages.compute_sample_aa(lineages.KATG_CODON_463, spdis)
    gyra = lineages.compute_sample_aa(lineages.GYRA_CODON_95, spdis)
    label = lineages.pgg_label(katg["aa"], gyra["aa"])
    check("L2.2.2/ERR4831569 katG463 = L (Leu, ancestral)",
          katg["aa"] == "L",
          f"got '{katg['aa']}'")
    check("L2.2.2/ERR4831569 gyrA95 = S (Ser, derived)",
          gyra["aa"] == "S",
          f"got '{gyra['aa']}'")
    check("L2.2.2/ERR4831569 = non-canonical (L+S, convergent gyrA)",
          label is None,
          f"got '{label}'")


def test_additional_l4_subtypes():
    """Verify L4 sub-lineages: those with gyrA variant only → non-canonical."""
    print("\n=== Test 4: Additional L4 sub-lineages ===")
    test_cases = [
        # These L4 sub-lineages have gyrA variant (→Thr) but NOT katG variant
        # → Arg + Thr = PGG2 (intermediate L4: katG already derived, gyrA reverted)
        ("L4.2", "CUS0000037", "R", "T", "PGG2"),
        ("L4.5", "CUS0000113", "R", "T", "PGG2"),
        ("L4.11", "SRR30679919", "R", "T", "PGG2"),
        ("L4.14", "DRR034452", "R", "T", "PGG2"),
    ]
    for lin, strain, exp_katg, exp_gyra, exp_pgg in test_cases:
        spdis = load_spdis(lin, strain)
        if spdis is None:
            print(f"  SKIP: {lin}/{strain} not found")
            continue
        katg = lineages.compute_sample_aa(lineages.KATG_CODON_463, spdis)
        gyra = lineages.compute_sample_aa(lineages.GYRA_CODON_95, spdis)
        label = lineages.pgg_label(katg["aa"], gyra["aa"])
        check(f"{lin}/{strain} = {exp_pgg} ({exp_katg}+{exp_gyra})",
              katg["aa"] == exp_katg and gyra["aa"] == exp_gyra and label == exp_pgg,
              f"got katG={katg['aa']}, gyrA={gyra['aa']}, PGG={label}")


def test_pgg_label_logic():
    """Unit test the PGG label assignment function.

    Corrected direction (Sreevatsan 1997, confirmed by literature):
      PGG1 = Leu + Thr (both ancestral)
      PGG2 = Leu + Ser (katG ancestral, gyrA derived)
      PGG3 = Arg + Ser (both derived — H37Rv state)
    """
    print("\n=== Test 5: PGG label logic ===")
    check("L+T = PGG1 (ancestral)",      lineages.pgg_label("L", "T") == "PGG1")
    check("R+T = PGG2 (intermediate L4)", lineages.pgg_label("R", "T") == "PGG2")
    check("R+S = PGG3 (derived/H37Rv)",  lineages.pgg_label("R", "S") == "PGG3")
    check("L+S = None (non-canonical)",   lineages.pgg_label("L", "S") is None)
    check("V+T = None (non-canonical)",   lineages.pgg_label("V", "T") is None)


def test_variant_application():
    """Verify that known SPDIs modify the right codon positions."""
    print("\n=== Test 6: SPDI variant application ===")

    # katG variant NC_000962.3:2154723:C:A should change codon 463
    # + strand CCG → CAG → mRNA CTG → Leu
    katg = lineages.compute_sample_aa(
        lineages.KATG_CODON_463,
        {"NC_000962.3:2154723:C:A"})
    check("katG SPDI 2154723:C:A → Leu (CTG)",
          katg["aa"] == "L" and katg["mrna_codon"] == "CTG",
          f"got aa={katg['aa']}, codon={katg['mrna_codon']}")

    # gyrA variant NC_000962.3:7584:G:C should change codon 95
    # + strand AGC → ACC → Thr
    gyra = lineages.compute_sample_aa(
        lineages.GYRA_CODON_95,
        {"NC_000962.3:7584:G:C"})
    check("gyrA SPDI 7584:G:C → Thr (ACC)",
          gyra["aa"] == "T" and gyra["mrna_codon"] == "ACC",
          f"got aa={gyra['aa']}, codon={gyra['mrna_codon']}")

    # Both together → PGG1 (ancestral at both positions)
    spdis = {"NC_000962.3:2154723:C:A", "NC_000962.3:7584:G:C"}
    katg = lineages.compute_sample_aa(lineages.KATG_CODON_463, spdis)
    gyra = lineages.compute_sample_aa(lineages.GYRA_CODON_95, spdis)
    label = lineages.pgg_label(katg["aa"], gyra["aa"])
    check("Both variants → PGG1 (Leu + Thr = ancestral)",
          label == "PGG1",
          f"got katG={katg['aa']}, gyrA={gyra['aa']}, PGG={label}")

    # gyrA variant only → PGG2 (intermediate L4: Arg + Thr)
    spdis_gyra_only = {"NC_000962.3:7584:G:C"}
    katg = lineages.compute_sample_aa(lineages.KATG_CODON_463, spdis_gyra_only)
    gyra = lineages.compute_sample_aa(lineages.GYRA_CODON_95, spdis_gyra_only)
    label = lineages.pgg_label(katg["aa"], gyra["aa"])
    check("gyrA variant only → PGG2 (Arg + Thr = intermediate L4)",
          label == "PGG2",
          f"got katG={katg['aa']}, gyrA={gyra['aa']}, PGG={label}")

    # katG variant only → non-canonical (Leu + Ser, e.g. L2.2.2 modern Beijing)
    spdis_katg_only = {"NC_000962.3:2154723:C:A"}
    katg = lineages.compute_sample_aa(lineages.KATG_CODON_463, spdis_katg_only)
    gyra = lineages.compute_sample_aa(lineages.GYRA_CODON_95, spdis_katg_only)
    label = lineages.pgg_label(katg["aa"], gyra["aa"])
    check("katG variant only → non-canonical (Leu + Ser, L2.2.2 convergent)",
          label is None,
          f"got katG={katg['aa']}, gyrA={gyra['aa']}, PGG={label}")


# ── Main ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("PGG COMPUTATION TEST SUITE — mtbc-lineages skill")
    print("=" * 60)

    test_h37rv_reference_state()
    test_h37rv_as_sample()
    test_pgg_label_logic()
    test_variant_application()
    test_real_strains()
    test_pgg2_real_strain()
    test_additional_l4_subtypes()

    print()
    print("=" * 60)
    total = passed + failed
    print(f"Results: {passed}/{total} passed, {failed}/{total} failed")
    if failed == 0:
        print("ALL TESTS PASSED ✓")
    else:
        print(f"FAILURES: {failed}")
    print("=" * 60)
    sys.exit(1 if failed else 0)
