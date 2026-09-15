#!/usr/bin/env python3
"""substitution_route.py -- v2 of the active-site-check SUBSTITUTION ROUTE (no M-CSA entry).

M-CSA (active_site_check.py) only covers ~895 EC numbers. Measured twice (1/3906 in the
annotation_mtbc atlas; 0/8 AFDB targets of Rv3909, 2026-08-10): the MAJORITY case is a Foldseek
"same fold" hit whose target has NO M-CSA entry. This module factors the reference procedure that
covers that case -- built ad hoc twice (mtbc/Rv3909/analyses/phase2_active_site_aaapu.py,
annotation_mtbc/analyses/phase_deepdive10_active_site_rv3031.py) with the same shape both times --
into functions a per-gene script can call instead of re-copying ~300 lines.

Procedure (see SKILL.md "route de substitution" for the full rationale):
  1. Pick a template of the SAME family solved WITH its ligand (substrate/analogue/inhibitor),
     found via the family literature, not via the original Foldseek hit. `check_template_published`
     rejects "To be published" entries before any of the rest runs (they carry no citable residue).
  2. Define the site GEOMETRICALLY: residues within `contact_cutoff` of a non-solvent het group --
     but only het groups that themselves contact the template's PUBLISHED site (`define_site`'s
     anchor rule). Filtering het groups by name alone (drop GOL/SO4/...) is not enough: in PDB 3n98
     the catalytic pocket is occupied by glycerol while cocrystallised glucoses sit in distal
     subsites, so a name-only filter silently swaps in the wrong pocket. The anchor rule catches
     that because it asks geometry, not chemistry, "is this near a residue already known to matter".
  3. Align the query to that template with Foldseek (`run_foldseek`), enforce BOTH numbering
     guards (`define_site` checks the template structure carries the published residues at their
     published `auth_seq_id`; `analyse_pair` checks the Foldseek-aligned string matches the
     structure's own resolved-residue sequence) -- cheap (a few lines), and the only thing standing
     between a correct report and a confidently wrong one (caught a dyad attributed to the wrong of
     two homonymous GH57 amylopullulanases in the Rv3909 pass).
  4. Score conservation against the NULL, never in the absolute: `analyse_pair` computes the
     site's identity fraction AND the alignment's background identity (site positions excluded from
     the background), then `binom_tail` gives P(>= observed | site no more conserved than
     background). A site is only "conserved" if it clears that null, not just if it looks familiar.
  5. Where sequence alignment reports a gap at a site position, `spatial_probe` answers the question
     an alignment cannot: gap is "not resolved here", not "absent" -- superpose the query onto the
     template (validated on already-aligned pairs first, not assumed) and ask what sits nearest in
     space to each published-site atom.

What stays PER-GENE, on purpose (not factored here): which templates, which published site, which
positive/negative/context witnesses, and the verdict thresholds -- those are scientific judgment
calls that belong in the calling script, spelled out and citable, not hidden in a library default.

Stdlib + subprocess (Foldseek) only. Requires a local Foldseek binary (see the `foldseek` skill).
"""
from __future__ import annotations

import json
import math
import subprocess
import urllib.request
from pathlib import Path
from typing import Any, Callable

RCSB_ENTRY = "https://data.rcsb.org/rest/v1/core/entry"
PDB_FILES = "https://files.rcsb.org/download"

RES3TO1 = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
    "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
    "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
    "TYR": "Y", "VAL": "V",
}
DEFAULT_SOLVENT: frozenset[str] = frozenset({"HOH", "DOD"})
DEFAULT_CONTACT_CUTOFF = 4.0
Point = tuple[float, float, float]


class SubstitutionRouteError(RuntimeError):
    """Raised on anything that would make the verdict unsafe to report: an unpublished template,
    a numbering mismatch, a failed superposition control, a missing chain. Callers should let this
    propagate to a hard failure -- there is no safe fallback for a wrong residue mapping."""


# --- template selection ---------------------------------------------------------------------

def check_template_published(pdb_id: str, *, timeout: int = 30) -> tuple[bool, str]:
    """RCSB citation title for `pdb_id`. `(False, "To be published")`-style entries carry no
    citable catalytic residue and must be rejected before use as a template (case 7E1Y)."""
    url = f"{RCSB_ENTRY}/{pdb_id.lower()}"
    with urllib.request.urlopen(url, timeout=timeout) as r:
        data = json.load(r)
    citations = data.get("citation") or []
    title = (citations[0].get("title") if citations else "") or ""
    if not title or title.strip().lower() in ("to be published", "unpublished"):
        return False, title or "no citation"
    return True, title


def fetch_cif(pdb_id: str, cache_dir: Path, *, user_agent: str = "active-site-check/2.0",
              timeout: int = 120) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    dest = cache_dir / f"{pdb_id.lower()}.cif"
    if dest.exists() and dest.stat().st_size > 10_000:
        return dest
    req = urllib.request.Request(f"{PDB_FILES}/{pdb_id.lower()}.cif",
                                  headers={"User-Agent": user_agent})
    dest.write_bytes(urllib.request.urlopen(req, timeout=timeout).read())
    return dest


# --- mmCIF parsing (stdlib only, no gemmi/biopython dependency) -----------------------------

def parse_atoms(cif_path: Path) -> list[dict]:
    """ATOM + HETATM rows of model 1, altloc '.' or 'A', as dicts keyed by mmCIF column name."""
    cols: list[str] = []
    atoms: list[dict] = []
    in_loop = started = False
    for ln in cif_path.read_text().splitlines():
        s = ln.strip()
        if s.startswith("_atom_site."):
            in_loop = True
            cols.append(s.split(".")[1])
            continue
        if in_loop and not started:
            if s.startswith("#") or not s:
                continue
            started = True
        if started:
            if s.startswith("#") or s.startswith("loop_") or s.startswith("_"):
                break
            f = s.split()
            if len(f) < len(cols):
                continue
            r = dict(zip(cols, f))
            if r.get("pdbx_PDB_model_num", "1") != "1":
                continue
            if r.get("label_alt_id", ".") not in (".", "A"):
                continue
            atoms.append(r)
    return atoms


def chain_residues(atoms: list[dict], chain: str) -> list[tuple[int, str]]:
    """Resolved protein residues of `chain`, in order: [(auth_seq_id, aa1), ...]."""
    seen: set[int] = set()
    out: list[tuple[int, str]] = []
    for r in atoms:
        if r.get("group_PDB") != "ATOM" or r.get("auth_asym_id") != chain:
            continue
        if r.get("label_atom_id") != "CA":
            continue
        rid = int(r["auth_seq_id"])
        if rid in seen:
            continue
        seen.add(rid)
        out.append((rid, RES3TO1.get(r["label_comp_id"], "X")))
    return out


def het_groups(atoms: list[dict], *, solvent: frozenset[str] = DEFAULT_SOLVENT
               ) -> dict[tuple[str, str, str], list[Point]]:
    """{(comp_id, chain, auth_seq_id): [xyz, ...]} for non-solvent HETATM groups."""
    groups: dict[tuple[str, str, str], list[Point]] = {}
    for r in atoms:
        if r.get("group_PDB") != "HETATM" or r.get("label_comp_id") in solvent:
            continue
        key = (r["label_comp_id"], r.get("auth_asym_id", "?"), r.get("auth_seq_id", "?"))
        groups.setdefault(key, []).append(
            (float(r["Cartn_x"]), float(r["Cartn_y"]), float(r["Cartn_z"])))
    return groups


def residues_within(atoms: list[dict], chain: str, xyz: list[tuple[float, float, float]],
                     cutoff: float) -> set[int]:
    c2 = cutoff * cutoff
    close: set[int] = set()
    for r in atoms:
        if r.get("group_PDB") != "ATOM" or r.get("auth_asym_id") != chain:
            continue
        x, y, z = float(r["Cartn_x"]), float(r["Cartn_y"]), float(r["Cartn_z"])
        for hx, hy, hz in xyz:
            if (x - hx) ** 2 + (y - hy) ** 2 + (z - hz) ** 2 <= c2:
                close.add(int(r["auth_seq_id"]))
                break
    return close


# --- geometric site definition (the anchor rule that avoids the glycerol trap) --------------

def define_site(cif_path: Path, chain: str, published_site: dict[int, str], *,
                 contact_cutoff: float = DEFAULT_CONTACT_CUTOFF,
                 solvent: frozenset[str] = DEFAULT_SOLVENT) -> dict[str, Any]:
    """Geometric active site: residues near a het group, but a het group only DEFINES the site
    if it itself contacts >=1 residue of the template's PUBLISHED site (`published_site`, e.g.
    {256: "E", 352: "D"}). Filtering het groups by name (drop GOL/SO4/PEG/...) is not equivalent:
    it can silently keep a distal-subsite ligand and miss the catalytic pocket occupied by a
    cryoprotectant (3n98). This rule asks geometry instead of chemistry.

    Raises SubstitutionRouteError if the chain is absent or the structure does not carry the
    published amino acid at its published `auth_seq_id` (numbering guard #1 -- the structure vs.
    its own publication)."""
    atoms = parse_atoms(cif_path)
    resolved = chain_residues(atoms, chain)
    if not resolved:
        raise SubstitutionRouteError(f"{cif_path.name}: no chain {chain}")
    auth2aa = dict(resolved)

    for auth, aa in published_site.items():
        obs = auth2aa.get(auth)
        if obs != aa:
            raise SubstitutionRouteError(
                f"{cif_path.name} chain {chain}: published residue {aa}{auth} expected, "
                f"observed {obs} -- numbering or structure does not match the publication.")

    kept, rejected, site = {}, {}, set()
    for key, xyz in sorted(het_groups(atoms, solvent=solvent).items()):
        near = residues_within(atoms, chain, xyz, contact_cutoff)
        anchors = sorted(near & set(published_site))
        rec = {"het": key[0], "auth_chain": key[1], "auth_seq": key[2],
               "n_contacts": len(near),
               "contacts": [f"{auth2aa.get(r, '?')}{r}" for r in sorted(near)],
               "published_anchors": [f"{published_site[r]}{r}" for r in anchors]}
        if anchors:
            kept[f"{key[0]}_{key[1]}{key[2]}"] = rec
            site |= near
        elif near:
            rejected[f"{key[0]}_{key[1]}{key[2]}"] = rec
    return {"atoms": atoms, "resolved": resolved, "auth2aa": auth2aa,
            "site_ligand": sorted(site), "kept_het": kept, "rejected_het": rejected}


# --- Foldseek alignment -----------------------------------------------------------------------

FOLDSEEK_COLS = ("query,target,evalue,prob,fident,alnlen,qstart,qend,tstart,tend,"
                 "qcov,tcov,alntmscore,qtmscore,ttmscore,lddt,qaln,taln")


def safe_tag(tag: str) -> str:
    """Sanitise `tag` for use as a bare filesystem path COMPONENT (never a path itself): any
    `/` (or `os.sep` on non-POSIX) silently turns a one-level `out_dir / f"..._{tag}_..."` into
    a multi-level path whose parent was never created, so Foldseek fails opening the .m8 with a
    generic "could not open for writing" that gives no hint the cause is the tag, not the run
    (hit with a gene label like "Rv3130c/tgs1" -- caught 2026-08-31, mtbc/Rv1125 P1.6.a)."""
    import os
    return tag.replace("/", "_").replace(os.sep, "_")


def run_foldseek(foldseek_bin: Path, query_files: list[Path], target_files: list[Path],
                  out_dir: Path, tag: str, *, extra_args: list[str] | None = None) -> list[dict]:
    """`foldseek easy-search` between `query_files` and `target_files`, parsed into row dicts.

    Copies inputs into per-run query/target dirs under `out_dir` (Foldseek indexes by directory).
    `tag` is sanitised via `safe_tag` -- pass any label (including one with "/") safely."""
    tag = safe_tag(tag)
    qdir, tdir = out_dir / f"_fs_{tag}_q", out_dir / f"_fs_{tag}_t"
    for d in (qdir, tdir):
        d.mkdir(parents=True, exist_ok=True)
    for src, d in [(f, qdir) for f in query_files] + [(f, tdir) for f in target_files]:
        (d / src.name).write_bytes(src.read_bytes())
    m8 = out_dir / f"foldseek_{tag}.m8"
    cmd = [str(foldseek_bin), "easy-search", str(qdir), str(tdir), str(m8),
           str(out_dir / f"_fs_{tag}_tmp"), "--format-output", FOLDSEEK_COLS,
           "-e", "1000", "--max-seqs", "500"] + (extra_args or [])
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise SubstitutionRouteError(f"foldseek failed (code {res.returncode}): {res.stderr[-800:]}")
    names = FOLDSEEK_COLS.split(",")
    rows: list[dict[str, Any]] = [dict(zip(names, ln.split("\t")))
                                   for ln in m8.read_text().splitlines() if ln.strip()]
    for r in rows:
        for k in ("evalue", "prob", "fident", "qcov", "tcov", "alntmscore",
                  "qtmscore", "ttmscore", "lddt"):
            r[k] = float(r[k])
        for k in ("alnlen", "qstart", "qend", "tstart", "tend"):
            r[k] = int(r[k])
    return rows


def map_alignment(qaln: str, taln: str, qstart: int, tstart: int
                   ) -> list[tuple[int, str, int, str]]:
    """[(query_resid, query_aa, target_resid, target_aa), ...] for non-gap-non-gap columns."""
    qi, ti = qstart, tstart
    pairs: list[tuple[int, str, int, str]] = []
    for qc, tc in zip(qaln, taln):
        if qc != "-" and tc != "-":
            pairs.append((qi, qc, ti, tc))
        if qc != "-":
            qi += 1
        if tc != "-":
            ti += 1
    return pairs


def binom_tail(k: int, n: int, p: float) -> float | None:
    """P(X >= k), X ~ Bin(n, p): the null 'the site is no more conserved than the background'."""
    if n == 0:
        return None
    p = min(max(p, 1e-12), 1 - 1e-12)
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


# --- conservation scoring, against the null, numbering guard #2 -----------------------------

def analyse_site(row: dict, tdef: dict[str, Any], site_auth: list[int], name: str
                  ) -> dict[str, Any]:
    """Conservation of `site_auth` (template auth_seq_ids) in the query side of Foldseek `row`,
    scored against the background identity of the REST of the alignment (site positions
    excluded). `row` must carry qaln/taln/qstart/tstart/tend and, from `analyse_pair`, come
    already through numbering guard #2."""
    resolved, auth2aa = tdef["resolved"], tdef["auth2aa"]
    tidx2auth = {i + 1: a for i, (a, _) in enumerate(resolved)}
    auth2idx = {a: i for i, a in tidx2auth.items()}
    qidx2auth = row["_qidx2auth"]

    pairs = row["_pairs"]
    t2q = {t: (qidx2auth[q], qa) for (q, qa, t, _) in pairs}

    det, k, m = [], 0, 0
    for auth in site_auth:
        taa = auth2aa.get(auth)
        ti = auth2idx.get(auth)
        rec: dict[str, Any] = {"template_res": f"{taa}{auth}"}
        if ti is not None and ti in t2q:
            q, qa = t2q[ti]
            rec.update(query_resid=q, query_aa=qa, identical=(qa == taa))
            k += 1
            m += int(qa == taa)
        else:
            inside = row["tstart"] <= (ti or -1) <= row["tend"]
            rec.update(query_resid=None, query_aa=None, identical=False,
                       status="gap in query" if inside else "outside aligned span")
        det.append(rec)

    site_idx = {auth2idx.get(a) for a in site_auth}
    bg = [(qa, ta) for (_, qa, t, ta) in pairs if t not in site_idx]
    n_bg, n_bg_id = len(bg), sum(1 for qa, ta in bg if qa == ta)
    p_bg = n_bg_id / n_bg if n_bg else 0.0
    return {
        "site": name, "n_site": len(site_auth), "n_present": k, "n_identical": m,
        "frac_identical": round(m / k, 4) if k else None,
        "background": {"n": n_bg, "n_identical": n_bg_id, "frac": round(p_bg, 4)},
        "p_binomial_vs_background": (float(f"{binom_tail(m, k, p_bg):.3g}") if k else None),
        "residues": det,
    }


def analyse_pair(row: dict, tdef: dict[str, Any], qres: list[tuple[int, str]]) -> dict:
    """Numbering guard #2 + alignment-index bookkeeping, mutating `row` in place with the pieces
    `analyse_site` needs (`_pairs`, `_qidx2auth`). Call once per (query, target) row, then call
    `analyse_site` for each site/dyad/etc you want scored against that same alignment.

    Guard: Foldseek numbers BOTH sides by resolved-residue index (1..N), not auth_seq_id; this
    checks the aligned substring actually matches the structure's own resolved sequence at the
    reported start, so a stale/mismatched target file cannot silently misattribute residues (this
    caught a dyad attributed to the wrong of two homonymous GH57 amylopullulanases)."""
    resolved = tdef["resolved"]
    qidx2auth = {i + 1: a for i, (a, _) in enumerate(qres)}

    for side, aln, start, end, res in (
            ("target", row["taln"], row["tstart"], row["tend"], resolved),
            ("query", row["qaln"], row["qstart"], row["qend"], qres)):
        obs = aln.replace("-", "")
        expect = "".join(aa for _, aa in res)[start - 1: end]
        if obs != expect:
            raise SubstitutionRouteError(
                f"{row['query']} vs {row['target']}: aligned {side} sequence does not match its "
                f"resolved-residue sequence (start={start}). Foldseek={obs[:40]}... / "
                f"structure={expect[:40]}...")

    row["_qidx2auth"] = qidx2auth
    row["_pairs"] = map_alignment(row["qaln"], row["taln"], row["qstart"], row["tstart"])
    return row


# --- spatial probe: what sits, in 3-D, opposite a site position the alignment gapped out ----

def load_residue_atoms(path: Path, chain: str | None) -> dict[int, dict]:
    """{auth_seq_id: {"aa": X, "atoms": [(name, (x,y,z)), ...]}} from a mmCIF or PDB file."""
    out: dict[int, dict] = {}
    if path.suffix == ".cif":
        for d in parse_atoms(path):
            if d.get("group_PDB") != "ATOM" or (chain is not None and d.get("auth_asym_id") != chain):
                continue
            rid = int(d["auth_seq_id"])
            out.setdefault(rid, {"aa": RES3TO1.get(d["label_comp_id"], "X"), "atoms": []})
            out[rid]["atoms"].append((d["label_atom_id"],
                                       (float(d["Cartn_x"]), float(d["Cartn_y"]), float(d["Cartn_z"]))))
    else:
        for ln in path.read_text().splitlines():
            if not ln.startswith("ATOM"):
                continue
            rid = int(ln[22:26])
            out.setdefault(rid, {"aa": RES3TO1.get(ln[17:20].strip(), "X"), "atoms": []})
            out[rid]["atoms"].append((ln[12:16].strip(),
                                       (float(ln[30:38]), float(ln[38:46]), float(ln[46:54]))))
    return out


def superposition(foldseek_bin: Path, qfile: Path, qname: str, tcif: Path, out_dir: Path, tag: str
                   ) -> Callable[[Point], Point]:
    """Foldseek (u, t) rigid transform bringing the TEMPLATE into the query's frame, as a callable.
    The u/t convention is not documented unambiguously by Foldseek, so `spatial_probe` validates it
    on already-aligned pairs before trusting it -- never assumed. `tag` is sanitised via
    `safe_tag`."""
    tag = safe_tag(tag)
    m8 = out_dir / f"_sup_{tag}.m8"
    cmd = [str(foldseek_bin), "easy-search", str(qfile), str(tcif), str(m8),
           str(out_dir / f"_sup_{tag}_tmp"), "--format-output", "query,target,u,t",
           "-e", "100", "--max-seqs", "20"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise SubstitutionRouteError(f"foldseek (superposition {tag}) failed: {res.stderr[-400:]}")
    for ln in m8.read_text().splitlines():
        f = ln.split("\t")
        if f[0] != qname:
            continue
        u = [float(x) for x in f[2].split(",")]
        t = [float(x) for x in f[3].split(",")]
        U = (u[0:3], u[3:6], u[6:9])

        def apply_t(p: Point, U: tuple = U, t: list[float] = t) -> Point:
            rows = [sum(U[i][j] * p[j] for j in range(3)) + t[i] for i in range(3)]
            return rows[0], rows[1], rows[2]

        return apply_t
    raise SubstitutionRouteError(f"superposition {tag}: no Foldseek row for chain {qname}")


def spatial_probe(foldseek_bin: Path, qfile: Path, qname: str, qchain: str | None,
                   tcif: Path, tchain: str, published_site: dict[int, str],
                   aligned_pairs: list[tuple[int, int]], out_dir: Path, tag: str,
                   *, control_max_dist_A: float = 2.5) -> dict:
    """What does the query place, in space, opposite each published-site residue? Answers where
    a sequence alignment only says "gap" -- a gap is non-resolution, not absence. Only meaningful
    compared to witnesses run through the identical procedure.

    Raises SubstitutionRouteError if the superposition control (median CA distance on already-
    aligned pairs) exceeds `control_max_dist_A` -- the transform convention or chain was wrong."""
    apply_t = superposition(foldseek_bin, qfile, qname, tcif, out_dir, tag)
    qat = load_residue_atoms(qfile, qchain)
    tat = load_residue_atoms(tcif, tchain)

    d_ctl = sorted(math.dist(qat[q]["atoms"][0][1], apply_t(tat[t]["atoms"][0][1]))
                   for q, t in aligned_pairs if q in qat and t in tat)
    if not d_ctl:
        raise SubstitutionRouteError(f"{tag}: no aligned pair to validate the superposition")
    med = d_ctl[len(d_ctl) // 2]
    if med > control_max_dist_A:
        raise SubstitutionRouteError(
            f"{tag}: invalid superposition (median CA distance {med:.1f} A over {len(d_ctl)} "
            f"already-aligned pairs) -- wrong u/t convention or chain.")

    probes = {}
    for auth, aa in sorted(published_site.items()):
        atoms = dict(tat[auth]["atoms"])
        head = next((n for n in ("OH", "NE1", "OE1", "OD1", "CZ", "CA") if n in atoms), "CA")
        ref = apply_t(atoms[head])
        near = sorted((min(math.dist(xyz, ref) for _, xyz in rec["atoms"]), rid, rec["aa"])
                      for rid, rec in qat.items())
        probes[f"{aa}{auth}"] = {
            "probe_atom": head,
            "nearest": [{"query_res": f"{a}{r}", "min_dist_A": round(d, 2)}
                        for d, r, a in near[:3]],
        }
    return {"control_median_CA_dist_A": round(med, 2), "n_control_pairs": len(d_ctl),
            "probes": probes}


# --- verdict heuristic (thresholds are a parameter, not a hidden constant) ------------------

def verdict(site_scores: list[dict], dyad_score: dict, *,
            p_threshold: float = 0.01, frac_threshold: float = 0.7,
            fold_only_frac: float = 0.4) -> str:
    """`site_scores`: one or more `analyse_site` results (e.g. ligand-defined site, published
    site) to require jointly; `dyad_score`: the minimal catalytic dyad/triad, required intact."""
    ps = [s["p_binomial_vs_background"] for s in site_scores if s["p_binomial_vs_background"] is not None]
    if not ps:
        return "inconclusive (no scoreable site)"
    p = min(ps)
    dyad_ok = dyad_score["n_identical"] == dyad_score["n_site"]
    frac = max((s["frac_identical"] or 0) for s in site_scores)
    if dyad_ok and p < p_threshold and frac >= frac_threshold:
        return "active site conserved (enzyme likely active)"
    if not dyad_ok and frac < fold_only_frac:
        return "fold-only (active site not retained)"
    return "ambiguous"
