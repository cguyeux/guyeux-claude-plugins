#!/usr/bin/env python3
"""
mtbc-lineages -- MTBC lineage authority dispatch script.

Usage:
    python3 lineages.py overview
    python3 lineages.py lookup <lineage> [--system <name>]
    python3 lineages.py spdi <spdi>
    python3 lineages.py parents <lineage> [--system <name>]
    python3 lineages.py children <lineage> [--system <name>]
    python3 lineages.py system <name>
    python3 lineages.py compare <lineage> <system1> [<system2> ...]
    python3 lineages.py cite <author>
    python3 lineages.py classify <spdi.txt|report.json|snps.vcf|dir>
                                 [--system <name>] [--min-pct N]

Source of truth (strict order, first match wins):
    1. lignees.py ["moi"]  — Guyeux 'moi' marker bank, read live
    2. lignees.py [other]  — Coll, Napier, Freschi, Stucki, ... (same file)
    3. TBannotator PostgreSQL (invoked by Claude via MCP, not here)
    4. references/*.md     — published-taxonomy citations only

Enrichment-only (never source of truth):
    - mtbc/global_supplementary/snp_barcoding.csv — strain counts, stats
"""

import csv
import io
import contextlib
import sys
from datetime import datetime
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REFERENCES_DIR = SKILL_DIR / "references"
LOCAL_LIGNEES_FALLBACK = REFERENCES_DIR / "lignees.py"

HOME = Path.home()
UPSTREAM_LIGNEES = HOME / "Documents" / "docs" / "codes" / "mtbc" / \
                   "investigate_phylo" / "lignees.py"

# Enrichment (never source of truth)
ENRICHMENT_CSV = HOME / "Documents" / "docs" / "codes" / "mtbc" / \
                 "global_supplementary" / "snp_barcoding.csv"

# Special-case data files (in this skill's data/ subdir)
DATA_DIR = SKILL_DIR / "data"
L49_REVERSE_MARKERS = DATA_DIR / "L4.9_reverse_markers.csv"
IS6110_REF = DATA_DIR / "IS6110_H37Rv.tsv"
ANCESTRAL_REF = DATA_DIR / "L8_Canettii_ancestral.tsv"
PGG_REF = DATA_DIR / "PGG_markers.tsv"

# L4.9-specific IS6110 positions (from L4.9 cahier — 4 insertion sites with
# >90% penetrance in L4.9 and ~0% in outgroup L4.1-L4.8, L1, L3)
L49_IS6110_POSITIONS = [889020, 1541951, 2365413, 3890778]

# L4.9 inverse-marker threshold: <=10 of the 57 pan-MTBC markers present
# means the sample is L4.9. Gap >= 31 (max L4.9 = 10, min outgroup = 41).
L49_THRESHOLD = 10


# ── Loaders ─────────────────────────────────────────────────────────────

def resolve_lignees_path():
    """Return (path, degraded_flag). The upstream path is canonical; the
    local snapshot is only used if upstream is unreachable."""
    if UPSTREAM_LIGNEES.is_file():
        return UPSTREAM_LIGNEES, False
    if LOCAL_LIGNEES_FALLBACK.is_file():
        return LOCAL_LIGNEES_FALLBACK, True
    return None, True


def load_lignees():
    """Load the live lignees dict (all systems, including 'moi').

    Returns (lignees_dict, source_path, mtime, degraded_bool).
    Reads via exec() in an isolated namespace. Suppresses stdout from
    the source file (some versions have debug prints).
    """
    path, degraded = resolve_lignees_path()
    if path is None:
        return {}, None, None, True

    namespace = {}
    devnull = io.StringIO()
    try:
        with open(path) as f:
            with contextlib.redirect_stdout(devnull):
                exec(f.read(), namespace)
    except Exception as e:
        print(f"ERROR: failed to parse lignees.py at {path}: {e}",
              file=sys.stderr)
        return {}, path, None, True

    lignees = namespace.get("lignees", {})
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return lignees, path, mtime, degraded


def load_enrichment():
    """Load snp_barcoding.csv for ENRICHMENT only (strain counts, stats).
    Never a source of truth. Returns a dict keyed by Lineage code, or
    empty dict if the file is unavailable."""
    if not ENRICHMENT_CSV.is_file():
        return {}
    by_code = {}
    try:
        with open(ENRICHMENT_CSV, newline='') as f:
            reader = csv.DictReader(f)
            for r in reader:
                code = (r.get("Lineage") or "").strip()
                if code:
                    by_code[code] = {k: (v.strip() if v else "") for k, v in r.items()}
    except Exception as e:
        print(f"WARNING: failed to read enrichment CSV: {e}", file=sys.stderr)
    return by_code


# ── Lineage code normalisation ──────────────────────────────────────────

def lineage_variants(code):
    """Return plausible variants of a lineage code (with/without L prefix,
    trailing/leading whitespace already stripped)."""
    code = code.strip()
    variants = {code}
    if code.startswith("L") and len(code) > 1 and code[1].isdigit():
        variants.add(code[1:])
    elif code and code[0].isdigit():
        variants.add("L" + code)
    return variants


def lookup_in_system(lignees, system, code):
    """Return list of (stored_code, spdi) matches for a code within a
    single system. Tolerates whitespace and L-prefix variants."""
    if system not in lignees:
        return []
    variants = lineage_variants(code)
    matches = []
    for stored_code, spdi in lignees[system]:
        if stored_code.strip() in variants:
            matches.append((stored_code.strip(), spdi))
    return matches


def parent_of(code):
    """Compute the parent of a dotted lineage code (e.g. '4.9.1' -> '4.9',
    '4' -> '', '4.9' -> '4'). Animal lineages without dots return ''."""
    code = code.strip()
    if "." not in code:
        return ""
    return code.rsplit(".", 1)[0]


def enrich_row(code, enrichment):
    """Return a one-line annotation string from the enrichment CSV, or
    empty string if nothing matches."""
    row = None
    for variant in lineage_variants(code):
        if variant in enrichment:
            row = enrichment[variant]
            break
    if not row:
        return ""
    parts = []
    if row.get("N_strains"):
        parts.append(f"n_strains={row['N_strains']}")
    stats = []
    if row.get("Mean_SPDI"): stats.append(f"mean={row['Mean_SPDI']}")
    if row.get("Min_SPDI"): stats.append(f"min={row['Min_SPDI']}")
    if row.get("Max_SPDI"): stats.append(f"max={row['Max_SPDI']}")
    if stats:
        parts.append("spdi_stats=" + "/".join(stats))
    return "  [" + ", ".join(parts) + "]" if parts else ""


def normalise_system_name(lignees, name):
    """Map 'moi' and 'guyeux' to the 'moi' key, case-insensitive match
    against available keys."""
    if not name:
        return "moi"
    if name.lower() in ("moi", "guyeux"):
        return "moi"
    for k in lignees:
        if k.lower() == name.lower():
            return k
    return None


# ── Argument parsing helper ─────────────────────────────────────────────

def extract_system_flag(args):
    """Consume --system <name> from args list and return (system, args')."""
    system = None
    out = []
    i = 0
    while i < len(args):
        if args[i] == "--system" and i + 1 < len(args):
            system = args[i + 1]
            i += 2
        else:
            out.append(args[i])
            i += 1
    return system, out


# ── Sub-commands ────────────────────────────────────────────────────────

def cmd_overview():
    print("=" * 70)
    print("MTBC LINEAGE AUTHORITY (mtbc-lineages skill)")
    print("=" * 70)

    lignees, path, mtime, degraded = load_lignees()
    print("\nmoi (Guyeux) (loaded live):")
    print(f"  File    : {path}")
    if degraded and path == LOCAL_LIGNEES_FALLBACK:
        print("  ⚠ DEGRADED MODE: upstream lignees.py unreachable,")
        print(f"    using local fallback snapshot at {path}")
    elif not path:
        print("  ⛔ FATAL: no lignees.py found (upstream nor local).")
        return

    if lignees:
        systems = sorted(lignees.keys())
        print(f"  Status  : OK, {len(lignees)} systems loaded")
        print(f"  Modified: {mtime:%Y-%m-%d %H:%M}")
        print(f"  Systems : {', '.join(systems)}")
        if "moi" in lignees:
            n_moi = len(lignees["moi"])
            print(f"  \"moi\"   : {n_moi} lineages (Guyeux — DEFAULT SYSTEM)")
        else:
            print("  ⚠ WARNING: no \"moi\" key found in lignees.py")
    else:
        print("  ⛔ parse failed or dict empty")
        return

    print("\nEnrichment layer (NOT source of truth):")
    print(f"  File   : {ENRICHMENT_CSV}")
    if ENRICHMENT_CSV.is_file():
        enr = load_enrichment()
        em = datetime.fromtimestamp(ENRICHMENT_CSV.stat().st_mtime)
        print(f"  Status : OK, {len(enr)} enriched lineages ({em:%Y-%m-%d})")
    else:
        print("  Status : absent (enrichment will be skipped)")

    print("\nReference notes (citations only):")
    if REFERENCES_DIR.is_dir():
        for n in sorted(REFERENCES_DIR.glob("*.md")):
            print(f"  - {n.name}")

    print("\n" + "=" * 70)
    print("PRECEDENCE: lignees.py[\"moi\"] > lignees.py[other] > TBannotator > notes")
    print("Default system when unspecified: \"moi\" (Guyeux)")
    print("=" * 70)


def cmd_lookup(args):
    system_flag, args = extract_system_flag(args)
    if not args:
        print("usage: lookup <lineage> [--system <name>]")
        return
    code = args[0]

    lignees, _, mtime, degraded = load_lignees()
    if not lignees:
        print("ERROR: could not load lignees.py")
        return

    enrichment = load_enrichment()
    stamp = f"(loaded {mtime:%Y-%m-%d %H:%M}"
    if degraded:
        stamp += " — DEGRADED"
    stamp += ")"

    # Explicit system flag: search only that system.
    if system_flag is not None:
        sys_name = normalise_system_name(lignees, system_flag)
        if sys_name is None:
            print(f"Unknown system: '{system_flag}'")
            print(f"Available: {', '.join(sorted(lignees.keys()))}")
            return
        matches = lookup_in_system(lignees, sys_name, code)
        if not matches:
            print(f"Lineage '{code}' not found in system '{sys_name}'.")
            return
        label = "moi (Guyeux)" if sys_name == "moi" else f"system {sys_name}"
        print(f"=== {code} ===")
        print(f"Source: lignees.py [\"{sys_name}\"] ({label}) {stamp}")
        print()
        for stored, spdi in matches:
            enr = enrich_row(stored, enrichment) if sys_name == "moi" else ""
            parent = parent_of(stored)
            parent_disp = parent if parent else "(root)"
            print(f"  Code          : {stored}")
            print(f"  Defining SPDI : {spdi}")
            print(f"  Parent        : {parent_disp}")
            if enr:
                print(f"  Enrichment    :{enr}")
        return

    # No system flag: "moi" first, then fall back to other systems.
    moi_matches = lookup_in_system(lignees, "moi", code)
    if moi_matches:
        print(f"=== {code} ===")
        print(f"Source: lignees.py [\"moi\"] (Guyeux 'moi' marker bank) {stamp}")
        print()
        for stored, spdi in moi_matches:
            enr = enrich_row(stored, enrichment)
            parent = parent_of(stored)
            parent_disp = parent if parent else "(root)"
            print(f"  Code          : {stored}")
            print(f"  Defining SPDI : {spdi}")
            print(f"  Parent        : {parent_disp}")
            if enr:
                print(f"  Enrichment    :{enr}")
        return

    # Not in "moi": scan every other system in the file.
    fallback_matches = []
    for sys_name in lignees:
        if sys_name == "moi":
            continue
        for stored, spdi in lookup_in_system(lignees, sys_name, code):
            fallback_matches.append((sys_name, stored, spdi))

    if fallback_matches:
        print(f"=== {code} ===")
        print(f"Source: lignees.py [fallback — not in \"moi\"] {stamp}")
        print()
        for sys_name, stored, spdi in fallback_matches:
            print(f"  {sys_name:25} {stored:15} {spdi}")
        print()
        print("  (If an answer in \"moi\" is expected, check lignees.py or ")
        print("   consult TBannotator PostgreSQL as a last-resort fallback.)")
        return

    # Nothing found anywhere in lignees.py.
    print(f"Lineage '{code}' not found in any system of lignees.py.")
    print("Last-resort fallback: query TBannotator PostgreSQL via MCP")
    print("  (mcp__tbannotator__tool_query_postgres on mv_lineage_markers")
    print("   or mv_strain_classification).")

    # Closest-match suggestions.
    all_codes = set()
    for sys_items in lignees.values():
        for stored, _ in sys_items:
            all_codes.add(stored.strip())
    import difflib
    suggestions = difflib.get_close_matches(code, all_codes, n=5, cutoff=0.6)
    if suggestions:
        print(f"\nDid you mean: {', '.join(suggestions)} ?")


def cmd_spdi(args):
    if not args:
        print("usage: spdi <spdi>")
        return
    spdi = args[0]

    lignees, _, mtime, degraded = load_lignees()
    if not lignees:
        print("ERROR: could not load lignees.py")
        return

    stamp = f"(loaded {mtime:%Y-%m-%d %H:%M}"
    if degraded:
        stamp += " — DEGRADED"
    stamp += ")"

    # 1. "moi" first
    moi_matches = [(code, s) for code, s in lignees.get("moi", [])
                   if s == spdi]
    if moi_matches:
        print(f"{spdi}")
        print(f"  Source: lignees.py [\"moi\"] (Guyeux 'moi' marker bank) {stamp}")
        for code, _ in moi_matches:
            parent = parent_of(code.strip())
            parent_disp = parent if parent else "root"
            print(f"  → {code.strip()}  (parent: {parent_disp})")
        return

    # 2. Other systems in the same file
    other_matches = []
    for sys_name, items in lignees.items():
        if sys_name == "moi":
            continue
        for code, s in items:
            if s == spdi:
                other_matches.append((sys_name, code.strip()))

    if other_matches:
        print(f"{spdi}")
        print(f"  (not in Guyeux \"moi\"; found in other systems of lignees.py:)")
        for sys_name, code in other_matches:
            print(f"  → {sys_name}: {code}")
        return

    # 3. Nothing in lignees.py
    print(f"{spdi}")
    print("  Not used as a defining marker in any system of lignees.py.")
    print("  Last-resort fallback: query TBannotator PostgreSQL via MCP")
    print("  (mcp__tbannotator__tool_query_postgres on tb_lineage_marker).")


def cmd_parents(args):
    system_flag, args = extract_system_flag(args)
    if not args:
        print("usage: parents <lineage> [--system <name>]")
        return
    code = args[0]

    lignees, _, _, _ = load_lignees()
    if not lignees:
        print("ERROR: could not load lignees.py")
        return

    sys_name = normalise_system_name(lignees, system_flag) if system_flag else "moi"
    if sys_name is None or sys_name not in lignees:
        print(f"Unknown system: '{system_flag}'")
        return

    # Index the chosen system for fast lookup by code.
    index = {}
    for stored, spdi in lignees[sys_name]:
        index[stored.strip()] = spdi

    variants = lineage_variants(code)
    canonical = None
    for v in variants:
        if v in index:
            canonical = v
            break
    if canonical is None:
        print(f"Lineage '{code}' not found in system '{sys_name}'.")
        return

    chain = []
    cur = canonical
    while cur:
        spdi = index.get(cur, "(unknown)")
        chain.append((cur, spdi))
        parent = parent_of(cur)
        if not parent:
            break
        cur = parent

    print(f"Ancestry chain for {canonical} (root → leaf) in system '{sys_name}':")
    for c, s in reversed(chain):
        print(f"  {c:20} {s}")


def cmd_children(args):
    system_flag, args = extract_system_flag(args)
    if not args:
        print("usage: children <lineage> [--system <name>]")
        return
    code = args[0]

    lignees, _, _, _ = load_lignees()
    if not lignees:
        print("ERROR: could not load lignees.py")
        return

    sys_name = normalise_system_name(lignees, system_flag) if system_flag else "moi"
    if sys_name is None or sys_name not in lignees:
        print(f"Unknown system: '{system_flag}'")
        return

    variants = lineage_variants(code)
    # Pick canonical form present in the system
    canonical = None
    for stored, _ in lignees[sys_name]:
        if stored.strip() in variants:
            canonical = stored.strip()
            break
    if canonical is None:
        # Allow children query even if the parent code itself is not a
        # listed marker (e.g. root nodes). Use the requested code as-is.
        canonical = code.strip()

    children = []
    for stored, spdi in lignees[sys_name]:
        stored = stored.strip()
        if parent_of(stored) == canonical:
            children.append((stored, spdi))

    if not children:
        print(f"No direct children of '{canonical}' in system '{sys_name}'.")
        return

    enrichment = load_enrichment() if sys_name == "moi" else {}
    print(f"Direct children of {canonical} in system '{sys_name}':")
    for c, s in sorted(children):
        enr = enrich_row(c, enrichment) if enrichment else ""
        print(f"  {c:20} {s}{enr}")


def cmd_system(args):
    if not args:
        print("usage: system <name>")
        return
    name = args[0]

    lignees, _, mtime, degraded = load_lignees()
    if not lignees:
        print("ERROR: could not load lignees.py")
        return

    sys_name = normalise_system_name(lignees, name)
    if sys_name is None or sys_name not in lignees:
        print(f"System '{name}' not found.")
        print(f"Available: {', '.join(sorted(lignees.keys()))}")
        return

    items = lignees[sys_name]
    stamp = f"(loaded {mtime:%Y-%m-%d %H:%M}"
    if degraded:
        stamp += " — DEGRADED"
    stamp += ")"
    label = "moi (Guyeux)" if sys_name == "moi" else "published taxonomy"
    print(f"=== System: {sys_name} ({label}) {stamp} ===")
    print(f"{len(items)} entries\n")
    for code, spdi in items:
        print(f"  {code.strip():20} {spdi}")


def cmd_compare(args):
    if not args:
        print("usage: compare <lineage> [systems...]")
        return
    lineage = args[0]
    systems = args[1:] or ["moi", "Coll", "Napier"]

    lignees, _, _, _ = load_lignees()
    if not lignees:
        print("ERROR: could not load lignees.py")
        return

    print(f"=== Comparing {lineage} across systems ===\n")
    for raw in systems:
        sys_name = normalise_system_name(lignees, raw)
        if sys_name is None or sys_name not in lignees:
            print(f"  {raw:25} → unknown system")
            continue
        matches = lookup_in_system(lignees, sys_name, lineage)
        if matches:
            for stored, spdi in matches:
                label = "★" if sys_name == "moi" else " "
                print(f" {label} {sys_name:23} → {spdi}  ({stored})")
        else:
            print(f"   {sys_name:23} → not found")


def cmd_cite(args):
    if not args:
        print("usage: cite <author>")
        return
    author = args[0]

    if not REFERENCES_DIR.is_dir():
        print("No references directory.")
        return

    candidates = list(REFERENCES_DIR.glob(f"{author}*.md"))
    if not candidates:
        candidates = [p for p in REFERENCES_DIR.glob("*.md")
                      if author.lower() in p.stem.lower()]
    if not candidates:
        print(f"No reference note found for '{author}'.")
        avail = sorted(p.stem for p in REFERENCES_DIR.glob("*.md"))
        if avail:
            print(f"Available: {', '.join(avail)}")
        return

    for c in candidates:
        print(f"=== {c.name} ===")
        with open(c) as f:
            print(f.read())
        print()


# ── Special-case helpers ────────────────────────────────────────────────

def read_spdi_set(path):
    """Read a spdi.txt or report.json and return a set of SPDI strings."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"no such file: {path}")
    spdis = set()
    if p.suffix == ".json":
        import json
        with open(p) as f:
            data = json.load(f)
        # Heuristic: TBannotator report.json typically has a list of variants
        # under various keys; grab any string that matches NC_000962.3:n:ref:alt
        import re
        pat = re.compile(r'NC_000962\.3:\d+:[ACGT\-]+:[ACGT\-]+')
        for m in pat.finditer(json.dumps(data)):
            spdis.add(m.group())
    elif p.suffix == ".vcf":
        with open(p) as f:
            for line in f:
                if line.startswith("NC_"):
                    cols = [c for c in line.strip().split('\t') if c != '.'][:4]
                    if len(cols) >= 4:
                        ref, pos, a, b = cols
                        spdis.add(f"{ref}:{int(pos)-1}:{a}:{b}")
    else:
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line and line.startswith("NC_"):
                    spdis.add(line.split()[0])
    return spdis


def load_l49_markers():
    """Return the list of 57 pan-MTBC inverse markers whose ABSENCE defines
    L4.9. Read live from the skill's data/ directory."""
    if not L49_REVERSE_MARKERS.is_file():
        return []
    markers = []
    with open(L49_REVERSE_MARKERS) as f:
        reader = csv.DictReader(f)
        for row in reader:
            s = (row.get("SPDI") or "").strip()
            if s:
                markers.append(s)
    return markers


def load_is6110_ref():
    """Return list of (start, end, name) for canonical H37Rv IS6110 copies."""
    if not IS6110_REF.is_file():
        return []
    rows = []
    with open(IS6110_REF) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            try:
                rows.append((int(r["start"]), int(r["end"]), r.get("locus_tag", "")))
            except (ValueError, KeyError):
                continue
    return rows


def load_ancestral_ref():
    """Return list of dicts for L8/Canettii ancestral genes/islands."""
    if not ANCESTRAL_REF.is_file():
        return []
    rows = []
    with open(ANCESTRAL_REF) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            rows.append(r)
    return rows


# ── Special-case sub-commands ───────────────────────────────────────────

def cmd_is_l49(args):
    """Apply the L4.9 inverse-marker criterion to a spdi.txt or report.json.

    Criterion: count how many of the 57 pan-MTBC inverse markers are
    present in the sample. If <=10, the sample is L4.9 (sensitivity 99.5%,
    specificity 100%, gap >=31 from min outgroup count).
    """
    if not args:
        print("usage: is-l4.9 <spdi.txt | report.json>")
        return
    path = args[0]
    markers = load_l49_markers()
    if not markers:
        print(f"ERROR: reverse markers file missing at {L49_REVERSE_MARKERS}")
        return
    try:
        sample = read_spdi_set(path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return

    present = [m for m in markers if m in sample]
    count = len(present)
    verdict = "L4.9" if count <= L49_THRESHOLD else ("probable non-L4.9" if count >= 41 else "BORDERLINE")

    print(f"=== L4.9 inverse-marker test ===")
    print(f"Sample     : {path}")
    print(f"SPDI count : {len(sample)}")
    print()
    print(f"Pan-MTBC inverse markers tested : {len(markers)}")
    print(f"Markers present in sample       : {count}")
    print(f"Threshold                       : <=10 = L4.9, >=41 = not L4.9")
    print()
    print(f"Verdict : {verdict}")
    if count > L49_THRESHOLD and count < 41:
        print("  ⚠ BORDERLINE — sample falls in the 11-40 range, which should")
        print("    not normally occur. Check sample quality or review manually.")
        print(f"    Markers present: {', '.join(sorted(present)[:10])}{' ...' if len(present) > 10 else ''}")

    # Optional IS6110 confirmation if report.json carries insertion data
    if path.endswith(".json"):
        import json
        try:
            with open(path) as f:
                data = json.load(f)
            # Look for insertion_sequences / IS6110 positions
            is_positions = []
            def walk(obj):
                if isinstance(obj, dict):
                    if obj.get("name") == "IS6110" and "position" in obj:
                        is_positions.append(obj["position"])
                    for v in obj.values():
                        walk(v)
                elif isinstance(obj, list):
                    for v in obj:
                        walk(v)
            walk(data)
            if is_positions:
                l49_hits = sum(1 for p in L49_IS6110_POSITIONS
                               if any(abs(int(q) - p) < 20 for q in is_positions))
                print()
                print(f"IS6110 subsidiary check: {l49_hits}/4 L4.9-specific positions hit")
                if l49_hits >= 3:
                    print("  ✓ IS6110 confirms L4.9 (>=3 of the 4 L4.9-specific positions)")
                elif l49_hits >= 1:
                    print("  ≈ Partial IS6110 support")
        except Exception:
            pass  # non-fatal


def cmd_is_l410(args):
    """Apply the L4.10 combinatorial criterion.

    L4.10 is NOT defined by a single positive marker. In lignees.py:
      - 4.10.i1 : NC_000962.3:1130525:G:A (presence required)
      - 4.10.i2 : -NC_000962.3:1759251:G:T (absence required)
      - 4.10    : -NC_000962.3:1692140:A:C (absence)
      - 4.10    : -NC_000962.3:7584:C:G (absence — likely gyrA95)
      - 4.10    : -NC_000962.3:960283:A:C (absence)

    The intersection of these conditions = L4.10. The gyrA95 position
    (7584) makes this a de facto PGG-linked criterion (sample must be
    PGG1 on that position, i.e. reference C).
    """
    if not args:
        print("usage: is-l4.10 <spdi.txt | report.json>")
        return
    path = args[0]

    present_required = ["NC_000962.3:1130525:G:A"]
    absent_required = [
        "NC_000962.3:1759251:G:T",  # frdA S524S (shared with some Coll L4.9 markers)
        "NC_000962.3:1692140:A:C",
        "NC_000962.3:7584:C:G",     # gyrA95 region — PGG-linked
        "NC_000962.3:960283:A:C",
    ]

    try:
        sample = read_spdi_set(path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return

    print(f"=== L4.10 combinatorial test ===")
    print(f"Sample : {path}")
    print()
    print("Required PRESENT markers:")
    all_pres_ok = True
    for m in present_required:
        ok = m in sample
        all_pres_ok &= ok
        print(f"  {'✓' if ok else '✗'} {m}")
    print()
    print("Required ABSENT markers:")
    all_abs_ok = True
    for m in absent_required:
        absent = m not in sample
        all_abs_ok &= absent
        mark = "✓" if absent else "✗"
        extra = "" if absent else " (PRESENT in sample — violates L4.10)"
        print(f"  {mark} {m}{extra}")
    print()

    if all_pres_ok and all_abs_ok:
        verdict = "L4.10 (all presence/absence conditions satisfied)"
    elif all_pres_ok and not all_abs_ok:
        verdict = "NOT L4.10 (presence markers OK but absence conditions violated)"
    elif not all_pres_ok and all_abs_ok:
        verdict = "NOT L4.10 (absence conditions OK but required presence markers missing)"
    else:
        verdict = "NOT L4.10"

    print(f"Verdict : {verdict}")
    print()
    print("Note: L4.10 is notoriously tricky. The gyrA95 position (7584) links")
    print("this criterion to the Principal Genetic Group classification")
    print("(Sreevatsan 1997). See 'cmd_pgg' for a separate PGG computation.")
    print("Combine with 'lookup 4.10' to see the raw entries in lignees.py.")


def cmd_is_mtbc(args):
    """Decide whether a sample belongs to the MTBC sensu lato (MTBC +
    Canettii) based on IS6110 presence. IS6110 is a lineage-specific
    insertion sequence found in MTBC and Canettii but absent in other
    mycobacteria. TBannotator indexes all Mycobacterium, so this test
    is useful to filter out samples that fall outside the complex.

    Requires a report.json with insertion_sequences data. A spdi.txt
    alone cannot be used since IS6110 is not encoded as SPDIs.
    """
    if not args:
        print("usage: is-mtbc <report.json>")
        return
    path = args[0]
    p = Path(path)
    if not p.is_file():
        print(f"ERROR: no such file: {path}")
        return
    if p.suffix != ".json":
        print("ERROR: is-mtbc requires a report.json (IS6110 data is not in spdi.txt)")
        return

    import json
    with open(p) as f:
        data = json.load(f)

    is6110_positions = []
    def walk(obj):
        if isinstance(obj, dict):
            if obj.get("name") == "IS6110" and "position" in obj:
                is6110_positions.append(obj["position"])
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
    walk(data)

    n = len(is6110_positions)
    canonical_hits = 0
    ref = load_is6110_ref()
    for pos in is6110_positions:
        try:
            ipos = int(pos)
        except (TypeError, ValueError):
            continue
        for start, end, _ in ref:
            if start - 50 <= ipos <= end + 50:
                canonical_hits += 1
                break

    print(f"=== IS6110 presence test (MTBC sensu lato detection) ===")
    print(f"Sample : {path}")
    print()
    print(f"IS6110 copies detected  : {n}")
    print(f"Hits on canonical H37Rv : {canonical_hits}/16 reference positions")
    print()

    if n == 0:
        verdict = "OUTSIDE MTBC complex (no IS6110 detected)"
        detail = "Likely another Mycobacterium species (non-TB, non-Canettii)."
    elif n <= 2:
        verdict = "BORDERLINE — very low IS6110 copy number"
        detail = ("Some MTBC strains have very few IS6110 copies (e.g. certain "
                  "L6/Africanum). Confirm via lineage-specific markers.")
    elif canonical_hits >= 3:
        verdict = "MTBC sensu lato (MTBC or M. canettii)"
        detail = ("Multiple canonical IS6110 positions detected. Use lineage-"
                  "specific markers (e.g. 'lookup' or 'is-l4.9') to narrow down.")
    else:
        verdict = "POSSIBLE MTBC sensu lato"
        detail = ("IS6110 present but at non-canonical positions. Could be a "
                  "divergent MTBC strain or an IS6110-bearing non-MTBC "
                  "mycobacterium (rare).")

    print(f"Verdict : {verdict}")
    print(f"  {detail}")
    print()
    print("Note: IS6110 alone cannot distinguish MTBC from M. canettii.")
    print("Use 'ancestral-signature' to check for L8/Canettii ancestral genes,")
    print("or query lineage markers for a precise assignment.")


def cmd_ancestral_signature(args):
    """Check whether a sample carries L8/Canettii ancestral genomic
    signatures (cobF, PPE50 ancestral form, pknH island, ...) that were
    lost in the modern MTBC radiation (L1-L7, L9, L10).

    This test is informative for emergence / phylogenetic basalness.
    It does NOT assign a lineage on its own; combine with 'lookup' or
    'is-l4.9' for a full picture.
    """
    if not args:
        print("usage: ancestral-signature <report.json>")
        return
    path = args[0]
    p = Path(path)
    if not p.is_file():
        print(f"ERROR: no such file: {path}")
        return

    ref = load_ancestral_ref()
    if not ref:
        print(f"ERROR: ancestral reference file missing at {ANCESTRAL_REF}")
        return

    # Attempt to read the report.json and look for CNV / deletion signals
    # over the ancestral regions. The user's TBannotator schema for this is
    # project-specific; we provide a structured report of what to check.
    print(f"=== L8/Canettii ancestral-signature check ===")
    print(f"Sample : {path}")
    print()
    print("Ancestral regions (present in L8 and M. canettii, LOST in modern")
    print("MTBC lineages L1-L7, L9, L10):")
    print()

    for r in ref:
        name = r.get("name", "?")
        kind = r.get("kind", "?")
        start = r.get("start_h37rv", "—")
        end = r.get("end_h37rv", "—")
        notes = r.get("notes", "")
        print(f"  ● {name} ({kind})")
        print(f"    H37Rv coords: {start}–{end}")
        # Clip note to 2 lines
        short = notes[:200] + ("..." if len(notes) > 200 else "")
        print(f"    {short}")
        print()

    print("How to interpret:")
    print("  - If the sample has INTACT ancestral regions (cobF, pknH island,")
    print("    full-length PPE50, split adenylate cyclase), it is basal:")
    print("    most likely L8 or M. canettii.")
    print("  - If the regions are DELETED (matching H37Rv), the sample belongs")
    print("    to the modern MTBC radiation (L1-L7, L9, L10).")
    print()
    print("Note: a full automated check requires coverage/assembly data not")
    print("typically in a TBannotator report.json. This command displays the")
    print("reference regions and their coordinates; an explicit ancestral")
    print("detection pipeline (reading coverage over these regions) is needed")
    print("for a final verdict. See mtbc/L8/l8_results_draft.md for the full")
    print("analysis methodology.")
    print()
    print("CORRECTION: The user initially mentioned an 'rpo' gene shared")
    print("between L8 and Canettii. After thorough search of the project")
    print("codebase, no such shared rpoA/B/C/D was found. The actual shared")
    print("ancestral features are cobF, PPE50, pknH, and TbD1 (see above).")
    print("If you meant a specific rpo variant, please clarify.")


# ── PGG computation core ────────────────────────────────────────────────

# Verified coordinates (see data/PGG_markers.tsv for provenance).
# All positions are 1-based (GFF3 convention).
GYRA_CODON_95 = {
    "gene": "gyrA",
    "strand": "+",
    "positions_1based": (7584, 7585, 7586),  # + strand, read directly as codon
    "h37rv_codon": "AGC",
    "h37rv_aa": "S",  # Ser95
}
KATG_CODON_463 = {
    "gene": "katG",
    "strand": "-",
    "positions_1based": (2154723, 2154724, 2154725),  # + strand; rev-comp to get mRNA
    "h37rv_plus_strand": "CCG",
    "h37rv_codon": "CGG",     # reverse complement
    "h37rv_aa": "R",  # Arg463
}

CODON_TABLE = {
    'TTT':'F','TTC':'F','TTA':'L','TTG':'L',
    'CTT':'L','CTC':'L','CTA':'L','CTG':'L',
    'ATT':'I','ATC':'I','ATA':'I','ATG':'M',
    'GTT':'V','GTC':'V','GTA':'V','GTG':'V',
    'TCT':'S','TCC':'S','TCA':'S','TCG':'S',
    'CCT':'P','CCC':'P','CCA':'P','CCG':'P',
    'ACT':'T','ACC':'T','ACA':'T','ACG':'T',
    'GCT':'A','GCC':'A','GCA':'A','GCG':'A',
    'TAT':'Y','TAC':'Y','TAA':'*','TAG':'*',
    'CAT':'H','CAC':'H','CAA':'Q','CAG':'Q',
    'AAT':'N','AAC':'N','AAA':'K','AAG':'K',
    'GAT':'D','GAC':'D','GAA':'E','GAG':'E',
    'TGT':'C','TGC':'C','TGA':'*','TGG':'W',
    'CGT':'R','CGC':'R','CGA':'R','CGG':'R',
    'AGT':'S','AGC':'S','AGA':'R','AGG':'R',
    'GGT':'G','GGC':'G','GGA':'G','GGG':'G',
}

_RC = str.maketrans("ACGT", "TGCA")
def revcomp(seq):
    return seq.translate(_RC)[::-1]


def parse_spdi(spdi):
    """Parse an NCBI SPDI string 'NC_000962.3:pos:ref:alt' into
    (pos_0based_int, ref, alt). Returns None on parse failure.
    lignees.py uses 0-based positions (NCBI standard)."""
    if not spdi:
        return None
    s = spdi.lstrip("-").strip()
    parts = s.split(":")
    if len(parts) < 4:
        return None
    try:
        pos = int(parts[1])
    except ValueError:
        return None
    ref = parts[2]
    alt = parts[3]
    return (pos, ref, alt)


def apply_variants_to_codon(codon_positions_1based, ref_plus_strand,
                             sample_spdis):
    """Given the + strand codon positions (1-based), the H37Rv + strand
    reference codon (3 bases), and a set of SPDI strings from a sample,
    return the sample's + strand codon after applying any variants that
    fall within the codon.

    Assumes lignees.py / spdi.txt SPDIs are 0-based (verified via the
    L4.9.1 marker NC_000962.3:119599:C:G matching H37Rv base at 1-based
    119600).

    Only simple single-base substitutions are applied; indels are ignored
    with a warning returned alongside the codon."""
    codon = list(ref_plus_strand)
    # Convert codon positions to 0-based SPDI coordinates
    codon_0based = set(p - 1 for p in codon_positions_1based)
    applied = []
    warnings = []
    for spdi in sample_spdis:
        parsed = parse_spdi(spdi)
        if parsed is None:
            continue
        pos0, ref, alt = parsed
        if pos0 not in codon_0based:
            continue
        # Only apply substitutions (len(ref) == len(alt) == 1)
        if len(ref) != 1 or len(alt) != 1:
            warnings.append(f"indel at position {pos0+1} in codon, not applied: {spdi}")
            continue
        # Position within the codon (0, 1 or 2)
        offset = (pos0 + 1) - codon_positions_1based[0]
        if offset < 0 or offset > 2:
            continue
        # Sanity: the ref base should match the H37Rv + strand base
        if codon[offset] != ref:
            warnings.append(
                f"SPDI ref mismatch at 1-based {pos0+1}: SPDI says ref='{ref}' "
                f"but H37Rv + strand has '{codon[offset]}' — variant ignored")
            continue
        codon[offset] = alt
        applied.append(spdi)
    return "".join(codon), applied, warnings


def compute_sample_aa(gene_def, sample_spdis):
    """Compute the amino acid at the target codon for a sample.

    gene_def is one of GYRA_CODON_95 or KATG_CODON_463.
    sample_spdis is an iterable of SPDI strings.
    Returns dict with: plus_strand_codon, mrna_codon, aa, applied, warnings.
    """
    if gene_def["strand"] == "+":
        ref_plus = gene_def["h37rv_codon"]
    else:
        ref_plus = gene_def["h37rv_plus_strand"]

    plus_codon, applied, warnings = apply_variants_to_codon(
        gene_def["positions_1based"], ref_plus, sample_spdis)

    if gene_def["strand"] == "+":
        mrna = plus_codon
    else:
        mrna = revcomp(plus_codon)

    aa = CODON_TABLE.get(mrna, "?")
    return {
        "plus_strand_codon": plus_codon,
        "mrna_codon": mrna,
        "aa": aa,
        "applied": applied,
        "warnings": warnings,
    }


def pgg_label(katg_aa, gyra_aa):
    """Return the Sreevatsan 1997 PGG label for a (katG463, gyrA95)
    amino-acid pair. Returns None for non-canonical combinations.

    CRITICAL: the evolutionary direction is:
      - katG463: Leu (ancestral) → Arg (derived)
      - gyrA95:  Thr (ancestral) → Ser (derived)

    H37Rv (NC_000962.3 reference) carries the MOST DERIVED state:
      Arg463 + Ser95 = PGG3.

    Verified against Sreevatsan 1997 and confirmed by WebSearch:
      "H37Rv strain is grouped into PGG3 with KatG463 CGG (Arg) and
       GyrA95 AGC (Ser)."
    """
    # PGG1 = Leu + Thr (both ancestral — pre-L4 state)
    if katg_aa == "L" and gyra_aa == "T":
        return "PGG1"
    # PGG2 = Arg + Thr (katG derived, gyrA still ancestral — intermediate L4)
    if katg_aa == "R" and gyra_aa == "T":
        return "PGG2"
    # PGG3 = Arg + Ser (both derived — most derived L4, H37Rv state)
    if katg_aa == "R" and gyra_aa == "S":
        return "PGG3"
    # Leu + Ser = non-canonical (ancestral katG + derived gyrA —
    # seen in L2.2.2 modern Beijing, convergent gyrA change)
    return None


def cmd_pgg(args):
    """Compute the Principal Genetic Group (Sreevatsan 1997) from a
    spdi.txt / report.json. Without argument, display the reference
    positions and H37Rv state."""
    if not args:
        # Display reference
        print("=== PGG (Principal Genetic Group) — Sreevatsan 1997 ===")
        print()
        print("PGG classifies MTBC strains by the amino-acid state at two")
        print("loci:")
        print("  - katG codon 463 : Arg (ancestral) vs Leu (derived)")
        print("  - gyrA codon 95  : Thr (ancestral) vs Ser (derived)")
        print()
        print("Canonical groups:")
        print("  PGG1 = Leu463 + Thr95   (most ancestral, pre-L4)")
        print("  PGG2 = Arg463 + Thr95   (katG derived, gyrA still ancestral)")
        print("  PGG3 = Arg463 + Ser95   (both derived — H37Rv state)")
        print()
        print("Evolutionary pathway (both changes on the L4 branch):")
        print("  PGG1 (L+T) → PGG2 (R+T, katG changes first) → PGG3 (R+S)")
        print("  katG463: Leu (ancestral) → Arg (derived)")
        print("  gyrA95 : Thr (ancestral) → Ser (derived)")
        print()
        print("Verified H37Rv reference state (from NC_000962.3):")
        print(f"  katG Rv1908c (- strand) codon 463:")
        print(f"    + strand 1-based [{KATG_CODON_463['positions_1based'][0]},"
              f"{KATG_CODON_463['positions_1based'][1]},"
              f"{KATG_CODON_463['positions_1based'][2]}] = "
              f"{KATG_CODON_463['h37rv_plus_strand']}")
        print(f"    mRNA codon (rev-comp)                = "
              f"{KATG_CODON_463['h37rv_codon']} → "
              f"{KATG_CODON_463['h37rv_aa']} (Arg = DERIVED)")
        print(f"  gyrA Rv0006 (+ strand) codon 95:")
        print(f"    + strand 1-based [{GYRA_CODON_95['positions_1based'][0]},"
              f"{GYRA_CODON_95['positions_1based'][1]},"
              f"{GYRA_CODON_95['positions_1based'][2]}] = "
              f"{GYRA_CODON_95['h37rv_codon']} → "
              f"{GYRA_CODON_95['h37rv_aa']} (Ser = DERIVED)")
        print()
        print("H37Rv = Arg463 + Ser95 = PGG3 (both derived)")
        print()
        print("Lineage ↔ PGG correspondences (from BDD survey):")
        print("  PGG1 (L+T): L1, L2, L3, L5, L6, L9, Bovis (pre-L4)")
        print("  PGG2 (R+T): L4.1, L4.2, L4.5, L4.11, L4.14 (intermediate L4)")
        print("  PGG3 (R+S): L4.8, L4.9, L4.15 (most derived L4 = H37Rv)")
        print("  Non-canonical (L+S): L2.2.2 modern Beijing (convergent gyrA)")
        print()
        print("Usage: /mtbc-lineages pgg <spdi.txt | report.json>")
        return

    path = args[0]
    try:
        sample = read_spdi_set(path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return

    katg_result = compute_sample_aa(KATG_CODON_463, sample)
    gyra_result = compute_sample_aa(GYRA_CODON_95, sample)
    label = pgg_label(katg_result["aa"], gyra_result["aa"])

    print(f"=== PGG computation ===")
    print(f"Sample : {path}")
    print(f"SPDI count : {len(sample)}")
    print()
    print("katG codon 463 (Rv1908c, - strand):")
    print(f"  + strand codon (H37Rv)  : {KATG_CODON_463['h37rv_plus_strand']}")
    print(f"  + strand codon (sample) : {katg_result['plus_strand_codon']}")
    print(f"  mRNA codon (sample)     : {katg_result['mrna_codon']}")
    print(f"  Amino acid (sample)     : {katg_result['aa']}")
    if katg_result['applied']:
        print(f"  Variants applied        : {', '.join(katg_result['applied'])}")
    for w in katg_result['warnings']:
        print(f"  ⚠ {w}")
    print()
    print("gyrA codon 95 (Rv0006, + strand):")
    print(f"  + strand codon (H37Rv)  : {GYRA_CODON_95['h37rv_codon']}")
    print(f"  + strand codon (sample) : {gyra_result['plus_strand_codon']}")
    print(f"  Amino acid (sample)     : {gyra_result['aa']}")
    if gyra_result['applied']:
        print(f"  Variants applied        : {', '.join(gyra_result['applied'])}")
    for w in gyra_result['warnings']:
        print(f"  ⚠ {w}")
    print()

    if label:
        print(f"Verdict : {label} (katG {katg_result['aa']}463 + gyrA {gyra_result['aa']}95)")
    else:
        print(f"Verdict : NON-CANONICAL (katG {katg_result['aa']}463 + gyrA {gyra_result['aa']}95)")
        print("  This combination does not map to PGG1, PGG2, or PGG3.")
        print("  Note: H37Rv itself is non-canonical (Arg463 + Ser95).")


# ── Classify ─────────────────────────────────────────────────────────────

def cmd_classify(args):
    """Classify a sample against ALL taxonomy systems in lignees.py.

    Usage:
        python3 lineages.py classify <spdi.txt|report.json|snps.vcf|dir>
            [--system <name>]  # restrict to one system (default: all)
            [--min-pct 0]      # minimum match percentage to display

    For each system, lists every lineage whose defining marker(s) match,
    with a percentage when a lineage has multiple defining SPDIs.
    Negative markers (prefixed with '-') are handled: the marker matches
    when the SPDI is ABSENT from the sample.

    Output is grouped by system, with "moi" (Guyeux) shown first.
    """
    if not args:
        print("Usage: lineages.py classify <spdi.txt|report.json|snps.vcf|dir>"
              " [--system <name>] [--min-pct N]")
        return

    # Parse flags
    target = args[0]
    restrict_system = None
    min_pct = 0.0
    i = 1
    while i < len(args):
        if args[i] == "--system" and i + 1 < len(args):
            restrict_system = args[i + 1]
            i += 2
        elif args[i] == "--min-pct" and i + 1 < len(args):
            min_pct = float(args[i + 1])
            i += 2
        else:
            i += 1

    # Resolve input: if it's a directory, look for spdi.txt or snps.vcf
    target_path = Path(target)
    if target_path.is_dir():
        candidates = ["spdi.txt", "report.json", "snps.vcf"]
        for c in candidates:
            p = target_path / c
            if p.is_file():
                target_path = p
                break
        else:
            print(f"ERROR: no spdi.txt, report.json, or snps.vcf in {target}")
            return

    # Load sample SPDIs
    try:
        sample_spdis = read_spdi_set(str(target_path))
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return

    if not sample_spdis:
        print(f"ERROR: no SPDIs found in {target_path}")
        return

    # Load lignees
    lignees, path, mtime, degraded = load_lignees()
    if not lignees:
        print("ERROR: could not load lignees.py")
        return

    stamp = f"(lignees.py loaded {mtime:%Y-%m-%d %H:%M}"
    if degraded:
        stamp += " — DEGRADED"
    stamp += ")"

    print(f"=== Classify: {target_path.name} ===")
    print(f"Sample SPDIs: {len(sample_spdis)}")
    print(f"Source: {path} {stamp}")

    if restrict_system:
        # Normalise system name
        norm = normalise_system_name(lignees, restrict_system)
        if norm is None:
            print(f"ERROR: unknown system '{restrict_system}'")
            print(f"Available: {', '.join(sorted(lignees.keys()))}")
            return
        systems_to_check = [norm]
    else:
        # "moi" first, then alphabetical
        systems_to_check = ["moi"] + sorted(
            k for k in lignees.keys() if k != "moi"
        )

    for sys_name in systems_to_check:
        if sys_name not in lignees:
            continue
        entries = lignees[sys_name]

        # Group entries by lineage code
        from collections import defaultdict
        by_lineage = defaultdict(list)
        for code, spdi in entries:
            by_lineage[code.strip()].append(spdi)

        # Check each lineage
        matches = []
        for code, spdi_list in by_lineage.items():
            total = len(spdi_list)
            matched = 0
            for spdi in spdi_list:
                if spdi.startswith('-'):
                    # Negative marker: matches when ABSENT
                    if spdi[1:] not in sample_spdis:
                        matched += 1
                else:
                    # Positive marker: matches when PRESENT
                    if spdi in sample_spdis:
                        matched += 1

            if matched > 0:
                pct = matched / total * 100.0
                if pct >= min_pct:
                    matches.append((code, matched, total, pct))

        if not matches:
            continue

        # Sort: 100% first, then by percentage descending, then by code
        matches.sort(key=lambda x: (-x[3], x[0]))

        # Display
        label = f" (moi (Guyeux))" if sys_name == "moi" else ""
        print(f"\n--- {sys_name}{label} ---")

        for code, matched, total, pct in matches:
            if total == 1:
                print(f"  {code}")
            else:
                bar_len = 20
                filled = int(pct / 100 * bar_len)
                bar = "█" * filled + "░" * (bar_len - filled)
                print(f"  {code:<20s} {matched:>4d}/{total:<4d} "
                      f"{bar} {pct:6.1f}%")

    print()


# ── Main ────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        cmd_overview()
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    dispatch = {
        "overview":  lambda: cmd_overview(),
        "lookup":    lambda: cmd_lookup(args),
        "spdi":      lambda: cmd_spdi(args),
        "parents":   lambda: cmd_parents(args),
        "children":  lambda: cmd_children(args),
        "system":    lambda: cmd_system(args),
        "compare":   lambda: cmd_compare(args),
        "cite":      lambda: cmd_cite(args),
        # Special cases
        "is-l4.9":   lambda: cmd_is_l49(args),
        "is-l49":    lambda: cmd_is_l49(args),
        "is-l4.10":  lambda: cmd_is_l410(args),
        "is-l410":   lambda: cmd_is_l410(args),
        "is-mtbc":   lambda: cmd_is_mtbc(args),
        "ancestral-signature": lambda: cmd_ancestral_signature(args),
        "ancestral": lambda: cmd_ancestral_signature(args),
        "pgg":       lambda: cmd_pgg(args),
        "classify":  lambda: cmd_classify(args),
    }

    if cmd in dispatch:
        dispatch[cmd]()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
