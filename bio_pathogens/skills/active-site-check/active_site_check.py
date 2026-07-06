#!/usr/bin/env python3
"""active-site-check -- M-CSA catalytic-residue validation for structure-based function calls.

Turns a Foldseek "same fold" hit into "active enzyme vs fold-only" by checking whether the
catalytic residues of the matched M-CSA enzyme are ALIGNED and CONSERVED in the query protein.
This is the rigour that distinguishes a genuine enzyme requalification from a mere fold match
(the recurring need of the Guyeux-group MTBC annotation projects: annotation_mtbc, TA_repertoire,
dark_enzymes).

Data source: M-CSA (Mechanism and Catalytic Site Atlas, EBI, Thornton group), 1003 entries / 895 EC.
REST API: https://www.ebi.ac.uk/thornton-srv/m-csa/api/  (entries embed their catalytic residues).
Stdlib only (urllib + json + argparse). Cache under $MCSA_CACHE or ~/.cache/mcsa/.

Commands
  residues  --ec 3.5.1.5 | --uniprot P9WIE5 | --pdb 4txa | --mcsa 2
      Fetch and print the catalytic residues of the matching M-CSA enzyme(s).

  check  (--ec|--uniprot|--pdb|--mcsa ...)  --qaln <ALN> --taln <ALN> --tstart N
      Map those catalytic residues through a pairwise alignment (query<->target, in TARGET
      sequence coordinates) and report active-site conservation. qaln/taln are the aligned
      query/target strings (with '-' gaps); tstart is the UniProt residue number of the first
      aligned target residue. These come directly from Foldseek
      (--format-output query,target,qaln,taln,tstart,...) or from a BLAST/aligner.

Verdict heuristic: of the N catalytic residues, k are aligned (present, non-gap in query) and m
are identical. m/N high  -> active site conserved -> likely ACTIVE enzyme.  k/N low -> fold only.
"""
from __future__ import annotations
import argparse, hashlib, json, os, sys, urllib.error, urllib.request
from pathlib import Path

API = "https://www.ebi.ac.uk/thornton-srv/m-csa/api"
CACHE = Path(os.environ.get("MCSA_CACHE", Path.home() / ".cache" / "mcsa"))

# M-CSA residue codes are 3-letter (SER, LYS...); alignments are 1-letter. Normalise for identity.
_THREE2ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q", "GLU": "E",
    "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F",
    "PRO": "P", "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
}


def aa1(code: str) -> str:
    """Return the 1-letter code for a residue code that may be 1- or 3-letter."""
    if not code:
        return ""
    code = code.strip().upper()
    return code if len(code) == 1 else _THREE2ONE.get(code, "")


def _get(url: str):
    CACHE.mkdir(parents=True, exist_ok=True)
    key = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".json")
    if key.exists():
        return json.loads(key.read_text())
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                               "User-Agent": "active-site-check/1.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read())
    key.write_text(json.dumps(data))
    return data


def load_all_entries() -> list:
    """Fetch all M-CSA entries (paginated DRF list), cache, return list of entry dicts.
    Each entry embeds its catalytic residues under entry['residues']."""
    out, url = [], f"{API}/entries/?format=json"
    while url:
        page = _get(url)
        if isinstance(page, dict) and "results" in page:
            out.extend(page["results"])
            url = page.get("next")
        else:  # non-paginated fallback
            out.extend(page if isinstance(page, list) else [page])
            url = None
    return out


def _ec_of(entry) -> str:
    try:
        return (entry.get("reaction") or {}).get("ec") or ""
    except AttributeError:
        return ""


def catalytic_residues(entry) -> list[dict]:
    """Extract catalytic residues from an entry as flat dicts:
    {code, uniprot_resid, pdb_id, chain, pdb_resid, auth_resid, role}."""
    res = []
    for r in entry.get("residues", []) or []:
        chains = r.get("residue_chains") or [{}]
        seqs = r.get("residue_sequences") or [{}]
        c0, s0 = chains[0], seqs[0]
        res.append({
            "code": (c0.get("code") or s0.get("code") or "").upper(),
            "uniprot_resid": s0.get("resid"),
            "pdb_id": c0.get("pdb_id"),
            "chain": c0.get("chain_name"),
            "pdb_resid": c0.get("resid"),
            "auth_resid": c0.get("auth_resid"),
            "role": r.get("roles_summary") or "",
        })
    return res


def find_entries(entries, *, ec=None, uniprot=None, pdb=None, mcsa=None) -> list:
    sel = []
    for e in entries:
        if mcsa is not None and str(e.get("mcsa_id")) == str(mcsa):
            sel.append(e)
        elif ec and _ec_of(e) == ec:
            sel.append(e)
        elif uniprot and (e.get("reference_uniprot_id") or "").upper() == uniprot.upper():
            sel.append(e)
        elif pdb:
            for r in catalytic_residues(e):
                if (r["pdb_id"] or "").lower() == pdb.lower():
                    sel.append(e)
                    break
    return sel


def map_active_site(qaln: str, taln: str, tstart: int, cat_resids: list[dict]):
    """Walk a pairwise alignment in TARGET coordinates; for each catalytic target residue
    (keyed by uniprot_resid), record the aligned query residue and whether it is identical.
    Returns (rows, n_total, n_present, n_identical)."""
    want = {r["uniprot_resid"]: r for r in cat_resids if r.get("uniprot_resid") is not None}
    tpos = tstart - 1
    rows = []
    seen = {}
    for qc, tc in zip(qaln, taln):
        if tc != "-":
            tpos += 1
            if tpos in want and tpos not in seen:
                present = qc != "-"
                ident = present and qc.upper() == aa1(want[tpos]["code"])
                seen[tpos] = {"uniprot_resid": tpos, "target_aa": want[tpos]["code"],
                              "query_aa": qc if present else "-", "present": present,
                              "identical": ident, "role": want[tpos]["role"]}
    for rp in want:
        rows.append(seen.get(rp, {"uniprot_resid": rp, "target_aa": want[rp]["code"],
                                  "query_aa": None, "present": False, "identical": False,
                                  "role": want[rp]["role"]}))
    rows.sort(key=lambda x: (x["uniprot_resid"] is None, x["uniprot_resid"]))
    n = len(rows)
    return rows, n, sum(r["present"] for r in rows), sum(r["identical"] for r in rows)


def _verdict(n, present, ident) -> str:
    # Identity drives the call: a catalytic residue that is ALIGNED but SUBSTITUTED means the
    # active site is lost, not "present". So judge on ident/n, not present/n.
    if n == 0:
        return "no catalytic residues mapped (target not in M-CSA, or numbering mismatch)"
    fi = ident / n
    if fi >= 0.8:
        return f"ACTIVE-SITE CONSERVED ({ident}/{n} catalytic residues identical) -> likely active enzyme"
    if fi >= 0.5:
        return (f"PARTIAL ({ident}/{n} identical, {present}/{n} aligned) -> active site partly retained; "
                f"verify (possible distant homolog / weak alignment)")
    if present >= 0.5 * n:
        return (f"FOLD-ONLY ({ident}/{n} identical although {present}/{n} aligned: catalytic residues "
                f"SUBSTITUTED) -> same fold, active site NOT retained")
    return (f"FOLD-ONLY ({present}/{n} catalytic residues aligned, {ident}/{n} identical: absent or in "
            f"gaps) -> same fold, active site NOT retained")


def main(argv=None):
    p = argparse.ArgumentParser(description="M-CSA catalytic-residue validation (active-site-check).")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("residues", "check"):
        sp = sub.add_parser(name)
        g = sp.add_mutually_exclusive_group(required=True)
        g.add_argument("--ec")
        g.add_argument("--uniprot")
        g.add_argument("--pdb")
        g.add_argument("--mcsa")
        if name == "check":
            sp.add_argument("--qaln", required=True, help="aligned query string (with '-')")
            sp.add_argument("--taln", required=True, help="aligned target string (with '-')")
            sp.add_argument("--tstart", required=True, type=int,
                            help="UniProt residue number of first aligned target residue")
        sp.add_argument("--json", action="store_true")

    a = p.parse_args(argv)
    if a.mcsa:  # fast path: detail endpoint, no full-list fetch
        entry = _get(f"{API}/entries/{a.mcsa}/?format=json")
        hits = [entry] if entry else []
    else:
        hits = find_entries(load_all_entries(), ec=a.ec, uniprot=a.uniprot, pdb=a.pdb)
    if not hits:
        print("No M-CSA entry matched the selector.", file=sys.stderr)
        return 2
    entry = hits[0]
    cat = catalytic_residues(entry)
    header = {"mcsa_id": entry.get("mcsa_id"), "ec": _ec_of(entry),
              "uniprot": entry.get("reference_uniprot_id"),
              "enzyme": (entry.get("enzyme_name") or entry.get("enzyme") or "")}

    if a.cmd == "residues":
        if a.json:
            print(json.dumps({"entry": header, "catalytic_residues": cat}, indent=2))
        else:
            print(f"M-CSA {header['mcsa_id']}  EC {header['ec']}  UniProt {header['uniprot']}  {header['enzyme']}")
            for r in cat:
                print(f"  {r['code']}{r['uniprot_resid']}  (PDB {r['pdb_id']} {r['chain']}:{r['auth_resid']})  role: {r['role']}")
        return 0

    rows, n, present, ident = map_active_site(a.qaln, a.taln, a.tstart, cat)
    verdict = _verdict(n, present, ident)
    if a.json:
        print(json.dumps({"entry": header, "n_catalytic": n, "n_present": present,
                          "n_identical": ident, "verdict": verdict, "residues": rows}, indent=2))
    else:
        print(f"M-CSA {header['mcsa_id']}  EC {header['ec']}  UniProt {header['uniprot']}")
        for r in rows:
            mark = "==" if r["identical"] else ("~~" if r["present"] else "XX")
            print(f"  [{mark}] target {r['target_aa']}{r['uniprot_resid']}  query {r['query_aa']}  role: {r['role']}")
        print(f"\n  VERDICT: {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
