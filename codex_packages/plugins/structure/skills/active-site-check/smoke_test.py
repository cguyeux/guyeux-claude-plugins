#!/usr/bin/env python3
"""Offline smoke test for active_site_check.py -- no network calls.

Locks in the 2026-08-01 fix (dark_enzymes P10.3): map_active_site() must return the QUERY
residue position (`query_resid`), not just its letter, and must honour a non-default `qstart`
for genuinely local (Foldseek-style) alignments. Before this fix, every caller had to re-walk
qaln/taln by hand to recover the query position -- exactly the tool debt this test guards against.

Usage: python3 smoke_test.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from active_site_check import map_active_site, _verdict, aa1  # noqa: E402


def check(label, cond):
    status = "ok" if cond else "FAIL"
    print(f"[{status}] {label}")
    return cond


def main():
    ok = True

    # --- aa1(): 3-letter -> 1-letter, already-1-letter passthrough, unknown -> "" ---
    ok &= check("aa1('CYS') == 'C'", aa1("CYS") == "C")
    ok &= check("aa1('C') == 'C'", aa1("C") == "C")
    ok &= check("aa1('') == ''", aa1("") == "")

    # --- map_active_site(): global alignment, qstart=1 (default) ---
    # target (UniProt numbering 1-based): positions 3 (Cys, nucleophile) and 7 (Arg) are catalytic.
    #   target : M K C D E F R H  (8 aa, positions 1..8)
    #   query  : M K C D - F R H  (a 1-residue deletion at target position 5, shifts what follows)
    taln = "MKCDEFRH"
    qaln = "MKCD-FRH"
    cat = [
        {"uniprot_resid": 3, "code": "CYS", "role": "nucleophile"},
        {"uniprot_resid": 7, "code": "ARG", "role": "electrostatic stabiliser"},
    ]
    rows, n, present, ident = map_active_site(qaln, taln, tstart=1, cat_resids=cat)
    ok &= check("n == 2", n == 2)
    ok &= check("both present and identical (Cys3, Arg7)", present == 2 and ident == 2)
    by_pos = {r["uniprot_resid"]: r for r in rows}
    ok &= check("Cys3 -> query_resid 3 (upstream of the gap)", by_pos[3]["query_resid"] == 3)
    # target pos 7 (R) is the 7th non-gap target char; the query has a gap at target position 5,
    # so by the time target reaches position 7 the query has only advanced 6 residues.
    ok &= check("Arg7 -> query_resid 6 (query is 1 residue shorter upstream)",
                by_pos[7]["query_resid"] == 6)

    # --- qstart != 1: a genuinely LOCAL alignment (Foldseek-style), query match starts at 10 ---
    rows2, n2, present2, ident2 = map_active_site(qaln, taln, tstart=1, cat_resids=cat, qstart=10)
    ok &= check("qstart=10 preserves n/present/ident", (n2, present2, ident2) == (2, 2, 2))
    by_pos2 = {r["uniprot_resid"]: r for r in rows2}
    ok &= check("qstart=10 shifts Cys3 -> query_resid 12", by_pos2[3]["query_resid"] == 12)
    ok &= check("qstart=10 shifts Arg7 -> query_resid 15", by_pos2[7]["query_resid"] == 15)

    # --- a catalytic residue in a query GAP has no query_resid ---
    taln3 = "MKCDEFRH"
    qaln3 = "MK-DEFRH"  # target Cys3 aligns to a query gap
    rows3, n3, present3, ident3 = map_active_site(qaln3, taln3, tstart=1, cat_resids=cat)
    by_pos3 = {r["uniprot_resid"]: r for r in rows3}
    ok &= check("Cys3 absent (query gap) -> present=False, query_resid=None",
                by_pos3[3]["present"] is False and by_pos3[3]["query_resid"] is None)
    ok &= check("n still 2, present now 1 (only Arg7), ident 1", (n3, present3, ident3) == (2, 1, 1))

    # --- verdict thresholds (unchanged behaviour, still exercised) ---
    ok &= check("_verdict: 2/2 identical -> ACTIVE-SITE CONSERVED",
                "ACTIVE-SITE CONSERVED" in _verdict(2, 2, 2))
    ok &= check("_verdict: 0/2 mapped -> no catalytic residues",
                "no catalytic residues" in _verdict(0, 0, 0))

    print("\n" + ("ALL OK" if ok else "SOME CHECKS FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
