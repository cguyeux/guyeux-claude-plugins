#!/usr/bin/env python3
"""Per-gene McDonald-Kreitman table for an MTBC lineage.

The companion `mk_test_and_ascertainment.py` runs a single POOLED MK test
(genome-wide, Tier 1-2 fixed vs Tier 4 polymorphic). This script computes the SAME
test gene by gene and writes a tidy per-gene table -- the exact format that
`mtbc-pathway-explain --from-selection` consumes and significance-gates, so the chain

    annotate_spdis  ->  mk_per_gene  ->  mtbc-pathway-explain --from-selection  ->  Atlas

runs on a lineage without any manual step.

Input: a tier-annotated per-variant table (CSV/TSV) with a gene/locus column, a Tier
column and an Effect column -- e.g. `supplementary_table_S3_annotated.csv` or
`data/mk_input_annotated.csv`. Tier semantics follow the skill: fixed divergence =
Tier 1-2 (Dn/Ds), polymorphism = Tier 4 (Pn/Ps); NS = missense/stop_gained/stop_lost/
start_lost, S = synonymous; other effects are ignored (standard for the MK test).

Output columns (per gene): locus_tag, gene, Dn, Ds, Pn, Ps, DoS, NI, alpha, p_fisher,
q_value. The Fisher p uses scipy if available (lazy import); without scipy p_fisher/
q_value are left blank and `--from-selection` falls back to its own handling.

POOLING. Per-gene MK is underpowered within a lineage (most genes carry 1-2
substitutions). Pool the counts to gain power at the scale the Atlas actually narrates:
`--group-col COL` aggregates by an existing functional-category column, and
`--groups FILE` by an external gene->group map (a pathway catalogue YAML or a 2-column
gene<TAB>group TSV; a gene pools into every group it belongs to). Grouped output replaces
locus_tag/gene with `group` and `n_genes`. Significant catalogue pathways can then be
narrated with `mtbc-pathway-explain <PATHWAY_ID>`.

    python scripts/mk_per_gene.py data/mk_input_annotated.csv --out mk_per_gene.tsv
    python scripts/mk_per_gene.py table.csv --fixed-tiers 1,2 --poly-tiers 3,4 --min-count 3
    # pooled to pathway scale (one row per pathway, powered):
    python scripts/mk_per_gene.py table.csv --groups .../mtbc_pathway_explain/data/pathways.yaml
    python scripts/mk_per_gene.py table.csv --group-col Functional_Category
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

NS_EFFECTS = {"missense_variant", "stop_gained", "stop_lost", "start_lost"}
S_EFFECTS = {"synonymous_variant"}

_GENE_COLS = ["locus_tag", "rv", "rv_id", "gene", "gene_name", "gene_id", "locus"]
_NAME_COLS = ["gene_name", "gene", "name"]
_TIER_COLS = ["tier", "tier_level", "tier_class"]
_EFFECT_COLS = ["effect", "consequence", "snpeff_effect", "variant_effect", "annotation"]


def _resolve_col(header: list[str], candidates: list[str]) -> str | None:
    low = {h.lower(): h for h in header}
    for c in candidates:                       # exact, case-insensitive
        if c.lower() in low:
            return low[c.lower()]
    for c in candidates:                       # substring, skip short tokens
        if len(c) <= 2:
            continue
        for h in header:
            if c.lower() in h.lower():
                return h
    return None


def _read_table(path: Path) -> tuple[list[str], list[dict]]:
    delim = "\t" if path.suffix.lower() in {".tsv", ".tab", ".txt"} else ","
    with path.open(encoding="utf-8", newline="") as f:
        lines = [ln for ln in f if not ln.lstrip().startswith("#")]
    reader = csv.DictReader(lines, delimiter=delim)
    return list(reader.fieldnames or []), [dict(r) for r in reader]


def _load_groups(path) -> dict[str, set]:
    """gene/locus token (lowercased) -> set(group names), for `--groups`.

    Accepts either a pathway catalogue YAML (``pathway: {genes: [...]}`` -- e.g.
    mtbc-pathway-explain's `data/pathways.yaml`; a gene may belong to several
    pathways) or a 2-column gene->group TSV/CSV. A variant joins a group if its
    locus_tag OR its gene name matches one of the group's member tokens.
    """
    p = Path(path)
    m: dict[str, set] = {}
    if p.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError:
            raise SystemExit("ERROR: --groups <.yaml> needs pyyaml; pass a 2-column "
                             "gene<TAB>group TSV instead.")
        cat = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        for group, entry in cat.items():
            genes = entry.get("genes") if isinstance(entry, dict) else entry
            for g in (genes or []):
                m.setdefault(str(g).strip().lower(), set()).add(str(group))
    else:
        header, rows = _read_table(p)
        if len(header) < 2:
            raise SystemExit("ERROR: --groups TSV/CSV needs 2 columns: gene<TAB>group")
        gk, grp = header[0], header[1]
        for r in rows:
            g, k = (r.get(gk) or "").strip().lower(), (r.get(grp) or "").strip()
            if g and k:
                m.setdefault(g, set()).add(k)
    return m


def mk_stats(dn: int, ds: int, pn: int, ps: int, *, with_p: bool = True):
    """DoS, NI, alpha (= 1 - NI) and Fisher p, identical to mk_test_and_ascertainment."""
    if dn + ds == 0:
        dos = -pn / (pn + ps) if (pn + ps) > 0 else 0.0
    elif pn + ps == 0:
        dos = dn / (dn + ds)
    else:
        dos = dn / (dn + ds) - pn / (pn + ps)
    ni = ((pn + 0.5) / (ps + 0.5)) / ((dn + 0.5) / (ds + 0.5))
    alpha = 1.0 - ni
    p = None
    if with_p:
        try:
            from scipy import stats
            _, p = stats.fisher_exact([[dn, ds], [pn, ps]], alternative="two-sided")
        except Exception:
            p = None
    return dos, ni, alpha, p


def bh_fdr(items: list[tuple[str, float]]) -> dict[str, float]:
    """Benjamini-Hochberg q-values (stdlib). items = [(key, p)], p not None."""
    m = len(items)
    if m == 0:
        return {}
    ordered = sorted(items, key=lambda kv: kv[1])
    q, running = {}, 1.0
    for rank in range(m, 0, -1):
        key, p = ordered[rank - 1]
        running = min(running, p * m / rank)
        q[key] = min(running, 1.0)
    return q


def _tiers(spec: str) -> set[str]:
    return {t.strip() for t in spec.split(",") if t.strip()}


def compute_mk(table_path, *, gene_col=None, name_col=None, tier_col=None,
               effect_col=None, group_col=None, groups_map=None, fixed_tiers="1,2",
               poly_tiers="4", min_count=1, fdr=True) -> tuple[list[dict], dict]:
    """Per-gene (default) or per-group MK table.

    The aggregation key is the gene by default; with ``group_col`` it is the value of
    an existing column (a functional category), and with ``groups_map`` (gene -> groups,
    e.g. a pathway catalogue) a variant pools into every group its gene belongs to.
    Pooling raises the per-unit variant count and gives the MK test power at the
    pathway / category scale, where the per-gene test is underpowered.
    """
    header, rows = _read_table(Path(table_path))
    gcol = gene_col or _resolve_col(header, _GENE_COLS)
    tcol = tier_col or _resolve_col(header, _TIER_COLS)
    ecol = effect_col or _resolve_col(header, _EFFECT_COLS)
    ncol = name_col or _resolve_col(header, _NAME_COLS)
    if ncol == gcol:
        ncol = None
    missing = [n for n, c in [("gene", gcol), ("tier", tcol), ("effect", ecol)] if not c]
    if missing:
        raise SystemExit(f"ERROR: no {'/'.join(missing)} column in {Path(table_path).name} "
                         f"(headers: {header}). Use --gene-col / --tier-col / --effect-col.")
    gpcol = None
    if group_col:
        gpcol = _resolve_col(header, [group_col])
        if not gpcol:
            raise SystemExit(f"ERROR: group column {group_col!r} not in {header}.")
    grouping = bool(gpcol or groups_map)

    fixed, poly = _tiers(fixed_tiers), _tiers(poly_tiers)
    acc: dict[str, dict] = {}
    n_unassigned = 0
    for r in rows:
        g = (r.get(gcol) or "").strip()
        if not g:
            continue
        eff = (r.get(ecol) or "").strip().lower()
        kind = "NS" if eff in NS_EFFECTS else ("S" if eff in S_EFFECTS else None)
        if kind is None:
            continue
        tier = (r.get(tcol) or "").strip()
        slot = "fixed" if tier in fixed else ("poly" if tier in poly else None)
        if slot is None:
            continue
        nm = (r.get(ncol) or "").strip() if ncol else ""
        if gpcol:
            keys = [k for k in [(r.get(gpcol) or "").strip()] if k]
        elif groups_map is not None:
            toks = {t for t in (g.lower(), nm.lower()) if t}
            keys = sorted({grp for t in toks for grp in groups_map.get(t, ())})
            if not keys:
                n_unassigned += 1
        else:
            keys = [g]
        for k in keys:
            a = acc.setdefault(k, {"dn": 0, "ds": 0, "pn": 0, "ps": 0,
                                   "genes": set(), "name": nm})
            if slot == "fixed":
                a["dn" if kind == "NS" else "ds"] += 1
            else:
                a["pn" if kind == "NS" else "ps"] += 1
            a["genes"].add(g)

    out = []
    for k, a in acc.items():
        dn, ds, pn, ps = a["dn"], a["ds"], a["pn"], a["ps"]
        if dn + ds + pn + ps < min_count:
            continue
        dos, ni, alpha, p = mk_stats(dn, ds, pn, ps)
        row = {"_key": k, "Dn": dn, "Ds": ds, "Pn": pn, "Ps": ps, "DoS": round(dos, 4),
               "NI": round(ni, 4), "alpha": round(alpha, 4), "p_fisher": p, "q_value": None}
        if grouping:
            row["group"], row["n_genes"] = k, len(a["genes"])
        else:
            row["locus_tag"], row["gene"] = k, a["name"]
        out.append(row)
    if fdr:
        qmap = bh_fdr([(r["_key"], r["p_fisher"]) for r in out if r["p_fisher"] is not None])
        for r in out:
            r["q_value"] = qmap.get(r["_key"])
    out.sort(key=lambda r: (r["p_fisher"] if r["p_fisher"] is not None else 1.0, -r["alpha"]))
    for r in out:
        r.pop("_key", None)

    n_sig = sum(1 for r in out if r["alpha"] > 0 and r["q_value"] is not None
                and r["q_value"] < 0.05)
    unit = ("column:" + gpcol) if gpcol else ("groups-map" if groups_map is not None else "gene")
    meta = {"gene_col": gcol, "tier_col": tcol, "effect_col": ecol, "name_col": ncol,
            "fixed_tiers": sorted(fixed), "poly_tiers": sorted(poly), "unit": unit,
            "grouping": grouping, "n_units": len(out),
            "n_with_p": sum(1 for r in out if r["p_fisher"] is not None),
            "n_significant_pos": n_sig, "n_unassigned_variants": n_unassigned}
    return out, meta


_GENE_OUT = ["locus_tag", "gene", "Dn", "Ds", "Pn", "Ps", "DoS", "NI", "alpha",
             "p_fisher", "q_value"]
_GROUP_OUT = ["group", "n_genes", "Dn", "Ds", "Pn", "Ps", "DoS", "NI", "alpha",
              "p_fisher", "q_value"]


def _fmt(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="mk_per_gene", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("table", help="tier-annotated per-variant CSV/TSV")
    p.add_argument("--gene-col", default=None)
    p.add_argument("--name-col", default=None, help="optional gene-name column (alongside locus_tag)")
    p.add_argument("--tier-col", default=None)
    p.add_argument("--effect-col", default=None)
    p.add_argument("--group-col", default=None,
                   help="pool by this existing column (a functional category) -> one row per group")
    p.add_argument("--groups", type=Path, default=None,
                   help="pool by an external gene->group map: a pathway catalogue .yaml "
                        "(pathway: {genes:[...]}) or a 2-column gene<TAB>group TSV -> one row per group")
    p.add_argument("--fixed-tiers", default="1,2", help="tiers counted as fixed divergence (Dn/Ds)")
    p.add_argument("--poly-tiers", default="4", help="tiers counted as polymorphism (Pn/Ps)")
    p.add_argument("--min-count", type=int, default=1, help="min Dn+Ds+Pn+Ps per unit to test")
    p.add_argument("--no-fdr", action="store_true", help="skip BH-FDR q_value column")
    p.add_argument("--out", type=Path, default=None, help="output TSV (default: stdout)")
    args = p.parse_args(argv)

    groups_map = None
    if args.groups is not None and not args.group_col:
        groups_map = _load_groups(args.groups)

    rows, meta = compute_mk(args.table, gene_col=args.gene_col, name_col=args.name_col,
                            tier_col=args.tier_col, effect_col=args.effect_col,
                            group_col=args.group_col, groups_map=groups_map,
                            fixed_tiers=args.fixed_tiers, poly_tiers=args.poly_tiers,
                            min_count=args.min_count, fdr=not args.no_fdr)

    cols = _GROUP_OUT if meta["grouping"] else _GENE_OUT
    out = args.out.open("w", encoding="utf-8", newline="") if args.out else sys.stdout
    try:
        w = csv.writer(out, delimiter="\t")
        w.writerow(cols)
        for r in rows:
            w.writerow([_fmt(r[c]) for c in cols])
    finally:
        if args.out:
            out.close()

    label = "groups" if meta["grouping"] else "genes"
    print(f"[mk_per_gene] {meta['n_units']} {label} via {meta['unit']} "
          f"(Dn/Ds from tiers {meta['fixed_tiers']}, Pn/Ps from {meta['poly_tiers']}); "
          f"{meta['n_with_p']} with a Fisher p; {meta['n_significant_pos']} with alpha>0 & q<0.05"
          + (f"  ->  {args.out}" if args.out else ""), file=sys.stderr)
    if meta.get("n_unassigned_variants"):
        print(f"[mk_per_gene] note: {meta['n_unassigned_variants']} variants matched no group "
              "(gene absent from the --groups map).", file=sys.stderr)
    if not meta["n_with_p"]:
        print("[mk_per_gene] note: no Fisher p computed (scipy missing?); "
              "--from-selection will recompute it or fall back.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
