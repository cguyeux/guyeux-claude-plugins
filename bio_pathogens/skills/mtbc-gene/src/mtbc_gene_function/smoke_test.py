"""Offline smoke test: curated annotation_mtbc as the PRIMARY source (no ESM, no net).

Validates that the skill answers from your own annotation_mtbc project first: the
curated UniProt function + EC, Pfam domains, and conservation regime for a well-known
gene (katG / Rv1908c), and that annotate_gene leads its summary with that curated
content. Skips cleanly (exit 0) if annotation_mtbc is not present.

    python3 -m mtbc_gene_function.smoke_test
"""
from __future__ import annotations

import sys

from mtbc_gene_function.core import annotate_gene
from mtbc_gene_function.local import LocalAnnotation


def main() -> int:
    local = LocalAnnotation()
    if not local.available():
        print(f"annotation_mtbc not found at {local.root}; skipping "
              "(set MTBC_ANNOTATION_DIR). Skill code is fine.", file=sys.stderr)
        return 0

    # 1. curated record for katG (Rv1908c)
    rec = local.record("katG")
    print(f"katG -> rv={rec.rv}; channels={rec.channels}")
    if rec.rv != "Rv1908c":
        print(f"FAIL: katG should resolve to Rv1908c, got {rec.rv}", file=sys.stderr)
        return 2
    pn = (rec.uniprot or {}).get("protein_name", "")
    if "peroxidase" not in pn.lower() or "1.11.1.21" not in ((rec.uniprot or {}).get("ec") or []):
        print(f"FAIL: expected curated UniProt catalase-peroxidase + EC, got {rec.uniprot}",
              file=sys.stderr)
        return 2
    if not any("peroxidase" in ((d.get("pfam_name") or "") + (d.get("description") or "")).lower()
               for d in rec.pfam):
        print(f"FAIL: expected a peroxidase Pfam domain, got {rec.pfam}", file=sys.stderr)
        return 2
    if not (rec.conservation and "purifying" in (rec.conservation.get("selection") or "")):
        print(f"FAIL: expected purifying-selection conservation, got {rec.conservation}",
              file=sys.stderr)
        return 2

    # 2. annotate_gene local-first, ESM off: summary led by the curated function
    ann = annotate_gene("Rv1908c", use_esm=False)
    print("summary:", ann.function_summary[:170])
    if not ann.local_available or ann.esm_available:
        print("FAIL: expected local_available and esm off", file=sys.stderr)
        return 2
    if "Catalase-peroxidase" not in (ann.product or "") or "UniProt" not in ann.function_summary:
        print(f"FAIL: summary should lead with curated UniProt function (product={ann.product})",
              file=sys.stderr)
        return 2

    # 3. name <-> rv resolution is consistent
    rv = local.resolve_rv("rpoB")
    if not rv or local.resolve_rv(rv) != rv:
        print(f"FAIL: resolve_rv inconsistent for rpoB ({rv})", file=sys.stderr)
        return 2

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
