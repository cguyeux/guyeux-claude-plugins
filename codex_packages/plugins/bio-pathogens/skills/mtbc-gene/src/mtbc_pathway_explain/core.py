"""Narrate an MTBC gene SET as a pathway, curated-first and network-aware.

Resolves a gene set -- a predefined pathway (data/pathways.yaml), an explicit gene
list, or a network-derived set (a gene's neighbourhood from `mtbc-gene-network`) --
annotates each gene CURATED-FIRST via `mtbc-gene-function` (annotation_mtbc: UniProt
function + EC + Pfam + conservation), aggregates the dominant enzyme classes / domains,
and narrates the set together with its PPI network structure (cohesion, density, hub
gene). ESM Atlas is an optional enrichment (`use_esm=True`), never required.
"""
from __future__ import annotations

import csv
from collections import Counter
from dataclasses import asdict, dataclass, field
from importlib.resources import files
from pathlib import Path

import yaml

from mtbc_gene_function.core import GeneNotFound, annotate_gene

EC_TOP = {"1": "oxidoreductase", "2": "transferase", "3": "hydrolase", "4": "lyase",
          "5": "isomerase", "6": "ligase", "7": "translocase"}


class PathwayNotFound(Exception):
    pass


class SelectionInputError(Exception):
    """A lineage selection table could not be read or has no usable gene column."""


@dataclass
class PathwayReport:
    name: str
    description: str | None
    n_genes_total: int
    n_genes_annotated: int
    n_genes_missing: int
    missing: list = field(default_factory=list)
    genes: list = field(default_factory=list)
    ec_classes: list = field(default_factory=list)
    pfam_domains: list = field(default_factory=list)
    dark_genes: list = field(default_factory=list)
    esm_themes: list = field(default_factory=list)
    network: dict | None = None
    paragraph: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_catalogue(extra: Path | None = None) -> dict:
    bundled = Path(str(files("mtbc_pathway_explain").joinpath("data/pathways.yaml")))
    cat = _load_yaml(bundled)
    if extra is not None:
        cat.update(_load_yaml(Path(extra).expanduser()))
    return {k.upper(): v for k, v in cat.items()}


def _annotate_set(genes: list[str], *, use_esm: bool) -> tuple[list[dict], list[str]]:
    annotated, missing = [], []
    for g in genes:
        try:
            a = annotate_gene(g, use_esm=use_esm)
        except GeneNotFound:
            missing.append(g)
            continue
        annotated.append({
            "gene": a.gene, "locus_tag": a.locus_tag, "product": a.product,
            "ec": a.ec, "uniprot_function": (a.uniprot_function or "")[:200] or None,
            "pfam": [d.get("pfam_name") or d.get("description") for d in (a.pfam or [])][:3],
            "selection": (a.conservation or {}).get("selection"),
            "hypothetical": a.is_hypothetical,
            "esm_available": a.esm_available, "top_features": a.top_features,
        })
    return annotated, missing


def _ec_class(ec: str) -> str:
    top = ec.split(".")[0]
    return f"EC{top} {EC_TOP.get(top, '')}".strip()


def _themes(annotated: list[dict]) -> tuple[list[str], list[str]]:
    ec, pf = Counter(), Counter()
    for g in annotated:
        for e in g.get("ec") or []:
            ec[_ec_class(e)] += 1
        for d in g.get("pfam") or []:
            if d:
                pf[d] += 1
    return ([f"{k} (x{n})" for k, n in ec.most_common(4)],
            [f"{k} (x{n})" for k, n in pf.most_common(6)])


def _esm_themes(annotated: list[dict], top_n: int = 5) -> list[str]:
    counter: Counter[str] = Counter()
    for g in annotated:
        seen: set[str] = set()
        for f in g.get("top_features", []):
            lab = f.get("label") or f.get("description")
            if lab and lab not in seen:
                counter[lab] += 1
                seen.add(lab)
    return [lab for lab, _ in counter.most_common(top_n)]


def _network_context(genes: list[str], *, min_score: int = 400) -> dict | None:
    """PPI cohesion of the gene set, via mtbc-gene-network (lazy, optional)."""
    try:
        from mtbc_gene_network import GeneNetwork
        net = GeneNetwork(min_score=min_score)
        if not net.available():
            return None
        g = net.graph()
        rvs = []
        for x in genes:
            r = net.resolve(x)
            if r and r in g and r not in rvs:
                rvs.append(r)
        if len(rvs) < 2:
            return {"n_genes_in_network": len(rvs),
                    "note": "too few genes in the interactome for a subnetwork"}
        sub = g.subgraph(rvs)
        n, e = sub.number_of_nodes(), sub.number_of_edges()
        dmax = n * (n - 1) / 2
        density = round(e / dmax, 3) if dmax else 0.0
        degs = sorted(sub.degree, key=lambda kv: kv[1], reverse=True)
        hub = degs[0] if degs and degs[0][1] > 0 else None
        return {"n_genes_in_network": n, "n_internal_edges": e, "density": density,
                "hub": net.label(hub[0]) if hub else None,
                "hub_internal_degree": hub[1] if hub else 0,
                "cohesive": density >= 0.15}
    except Exception:
        return None


def _paragraph(r: PathwayReport) -> str:
    parts = [f"{r.name}: {r.n_genes_total} genes ({r.n_genes_annotated} annotated)."]
    if r.description:
        parts.append(r.description)
    if r.ec_classes:
        parts.append("Dominant enzyme classes: " + "; ".join(r.ec_classes) + ".")
    if r.pfam_domains:
        parts.append("Recurring Pfam domains: " + "; ".join(r.pfam_domains) + ".")
    if r.network and "density" in r.network:
        nw = r.network
        coh = "tightly" if nw.get("cohesive") else "loosely"
        hub = f", hub gene {nw['hub']}" if nw.get("hub") else ""
        parts.append(f"PPI structure: {coh} connected ({nw['n_internal_edges']} internal "
                     f"edges among {nw['n_genes_in_network']} genes, density {nw['density']}){hub}.")
    elif r.network and r.network.get("note"):
        parts.append("PPI: " + r.network["note"] + ".")
    if r.dark_genes:
        parts.append(f"{len(r.dark_genes)} uncharacterised gene(s): "
                     + ", ".join(r.dark_genes[:8]) + ".")
    if r.esm_themes:
        parts.append("ESM SAE recurring features: " + "; ".join(r.esm_themes) + ".")
    if r.missing:
        parts.append(f"{len(r.missing)} gene(s) unresolved: " + ", ".join(r.missing[:8]) + ".")
    return " ".join(parts)


def explain_gene_set(genes: list[str], *, name: str, description: str | None = None,
                     use_esm: bool = False, with_network: bool = True,
                     min_score: int = 400) -> PathwayReport:
    """Narrate an arbitrary gene set (curated-first), with PPI network context."""
    annotated, missing = _annotate_set(genes, use_esm=use_esm)
    ec_top, pf_top = _themes(annotated)
    dark = [(g["gene"] or g["locus_tag"]) for g in annotated if g.get("hypothetical")]
    net = None
    if with_network:
        net = _network_context([g["locus_tag"] or g["gene"] for g in annotated
                                if g.get("locus_tag") or g.get("gene")], min_score=min_score)
    report = PathwayReport(
        name=name, description=description, n_genes_total=len(genes),
        n_genes_annotated=len(annotated), n_genes_missing=len(missing), missing=missing,
        genes=annotated, ec_classes=ec_top, pfam_domains=pf_top, dark_genes=dark,
        esm_themes=_esm_themes(annotated) if use_esm else [], network=net,
    )
    report.paragraph = _paragraph(report)
    return report


def explain_pathway(pathway_id: str, *, catalogue_path: Path | None = None,
                    use_esm: bool = False, with_network: bool = True,
                    min_score: int = 400) -> PathwayReport:
    catalogue = load_catalogue(extra=catalogue_path)
    key = pathway_id.upper()
    if key not in catalogue:
        raise PathwayNotFound(
            f"Pathway {pathway_id!r} not in catalogue. Available: {sorted(catalogue)}"
        )
    entry = catalogue[key]
    return explain_gene_set(entry.get("genes") or [], name=pathway_id,
                            description=entry.get("description"), use_esm=use_esm,
                            with_network=with_network, min_score=min_score)


def genes_from_network(spec: str, *, min_score: int = 400) -> tuple[list[str], str]:
    """Resolve a network spec into (gene_list, label).

    spec: ``neighbors:GENE`` (a gene + its interaction partners = its functional
    neighbourhood) or a comma-separated explicit gene list (a subnetwork).
    """
    if spec.startswith(("neighbors:", "neighbours:")):
        gene = spec.split(":", 1)[1].strip()
        from mtbc_gene_network import GeneNetwork
        net = GeneNetwork(min_score=min_score)
        rv = net.resolve(gene)
        if rv is None:
            raise PathwayNotFound(f"{gene!r} is not in the interactome.")
        nbrs = net.neighbors(gene)
        genes = [net.label(rv)] + [(n["gene"] or n["rv"]) for n in nbrs]
        return genes, f"neighbourhood of {net.label(rv)}"
    genes = [x.strip() for x in spec.split(",") if x.strip()]
    return genes, "gene set"


# --------------------------------------------------------------------------- #
# From a lineage's selection signal up to the affected pathways.
#
# This does NOT recompute a selection test (that is `mk-ascertainment` /
# `convergent-evolution`). It READS an existing per-gene selection table for a
# lineage -- ideally the OUTPUT of `mk-ascertainment` (per-gene Dn/Ds/Pn/Ps,
# alpha = 1 - NI, DoS, Fisher p) -- extracts the gene set the signal concerns
# (drift-tolerant column resolution, like the data-access gabarit), and maps it
# onto the pathway catalogue. When the table carries McDonald-Kreitman statistics
# it applies a SIGNIFICANCE GATE (positive direction + BH-FDR-corrected p) so the
# Atlas only narrates a `selection` section when the test actually concluded.
# --------------------------------------------------------------------------- #

# Header candidates, resolved exact-(case-insensitive)-then-substring. Gene keys put
# the canonical locus tag first so a table carrying both Rv and a gene/protein name
# is keyed on the Rv. Short tokens (<=2 chars) never match by substring.
_GENE_COLS = ["locus_tag", "rv", "rv_id", "gene_name", "gene", "gene_id", "locus"]
_STAT_COLS = ["dn/ds", "dnds", "dn_ds", "dnds_ratio", "dnds_proxy", "omega"]
_P_COLS = ["fisher_p_vs_bg", "p_value", "pvalue", "p_adj", "padj", "qvalue", "q_value",
           "fdr", "p_2sided", "p_1sided_greater", "p"]
_EFFECT_COLS = ["effect", "consequence", "snpeff_effect", "variant_effect"]
_IMPACT_COLS = ["impact"]
_NONSYN_KW = ("missense", "stop_gain", "stop_lost", "start_lost", "frameshift",
              "inframe", "nonsense", "disruptive", "protein_altering")

# McDonald-Kreitman output columns (mk-ascertainment): the adaptive-substitution
# direction (alpha = 1 - NI, or DoS) and the raw contingency counts to recompute it.
_ALPHA_COLS = ["alpha", "alpha_mk", "prop_adaptive", "adaptive_fraction"]
_DOS_COLS = ["dos", "direction_of_selection"]
_MK_P_COLS = ["p_fisher", "mk_p", "fisher_p", "p_mk", "fisher_p_vs_bg", "p_value",
              "pvalue", "q_value", "qvalue", "fdr", "p_2sided", "p_1sided_greater", "p"]
_DN_COLS, _DS_COLS = ["dn", "d_n", "fixed_ns", "div_n"], ["ds", "d_s", "fixed_s", "div_s"]
_PN_COLS, _PS_COLS = ["pn", "p_n", "poly_ns"], ["ps", "p_s", "poly_s"]


@dataclass
class SelectionReport:
    lineage: str | None
    table: str
    selection: dict
    n_selected_genes: int
    selected_genes: list = field(default_factory=list)
    test_concluded: bool | None = None     # True/False for MK-gated tables; None otherwise
    gate: dict | None = None               # significance gate detail (MK mode)
    selected_module: dict | None = None
    n_pathways_hit: int = 0
    pathway_hits: list = field(default_factory=list)
    off_catalogue: list = field(default_factory=list)
    paragraph: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


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


def _to_float(v) -> float | None:
    if v is None:
        return None
    s = str(v).strip()
    if s in ("", "-", "NA", "na", "nan", "NaN", "None", "inf"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _to_int(v) -> int | None:
    f = _to_float(v)
    return int(round(f)) if f is not None else None


def _mk_stats(dn: int, ds: int, pn: int, ps: int, *, with_p: bool = True):
    """McDonald-Kreitman per-gene stats (same formulas as mk-ascertainment).

    Returns (DoS, alpha=1-NI, NI, p_fisher|None). p is computed via scipy if present
    (lazy import); without scipy it stays None and the gate falls back to FDR over the
    p-values that ARE in the table, or to a direction-only candidate flag.
    """
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
    return dos, alpha, ni, p


def _bh_fdr(items: list[tuple[str, float]]) -> dict[str, float]:
    """Benjamini-Hochberg q-values (stdlib). items = [(key, p)], p not None."""
    m = len(items)
    if m == 0:
        return {}
    ordered = sorted(items, key=lambda kv: kv[1])
    q: dict[str, float] = {}
    running = 1.0
    for rank in range(m, 0, -1):                    # largest p first, enforce monotonicity
        key, p = ordered[rank - 1]
        running = min(running, p * m / rank)
        q[key] = min(running, 1.0)
    return q


def _read_table(path: Path) -> tuple[list[str], list[dict]]:
    if not path.exists():
        raise SelectionInputError(f"Selection table not found: {path}")
    delim = "\t" if path.suffix.lower() in {".tsv", ".tab", ".txt"} else ","
    with path.open(encoding="utf-8", newline="") as f:
        lines = [ln for ln in f if not ln.lstrip().startswith("#")]
    reader = csv.DictReader(lines, delimiter=delim)
    header = list(reader.fieldnames or [])
    if not header:
        raise SelectionInputError(f"Empty / header-less table: {path}")
    return header, [dict(r) for r in reader]


def genes_under_selection(table_path, *, gene_col: str | None = None,
                          stat_col: str | None = None, p_col: str | None = None,
                          min_stat: float = 1.0, max_p: float = 0.05,
                          min_variants: int = 1, alpha_min: float = 0.0,
                          fdr: bool = True) -> tuple[list[str], dict, dict]:
    """Extract the gene SET a lineage's selection table flags + per-gene evidence.

    Auto-detects the table shape, highest-confidence first:
      * **McDonald-Kreitman output** (alpha / DoS, or Dn/Ds/Pn/Ps to recompute them,
        ideally from `mk-ascertainment`): a SIGNIFICANCE GATE keeps genes with a
        positive adaptive direction (``alpha > alpha_min`` or ``DoS > alpha_min``) AND
        ``p < max_p`` -- BH-FDR-corrected across genes when ``fdr`` and p-values exist.
        This is the gate that lets the Atlas write a `selection` section only when the
        test actually concluded;
      * a per-gene statistic column (dN/dS, dnds_proxy, omega): keep genes with
        ``stat > min_stat`` and (if a p-value column exists) ``p < max_p``;
      * variant-level (gene + effect/impact, no per-gene stat): aggregate per gene,
        keep genes with ``>= min_variants`` non-synonymous variants;
      * neither: return every gene in the table (a plain gene list), flagged in meta.

    Returns ``(genes, evidence, meta)``. ``meta['gate']`` is populated in MK mode.
    """
    header, rows = _read_table(Path(table_path))
    gcol = gene_col or _resolve_col(header, _GENE_COLS)
    if not gcol:
        raise SelectionInputError(
            f"No gene column in {Path(table_path).name} (headers: {header}). "
            "Pass gene_col= / --gene-col explicitly.")
    scol = stat_col or _resolve_col(header, _STAT_COLS)
    pcol = p_col or _resolve_col(header, _P_COLS)
    ecol = _resolve_col(header, _EFFECT_COLS)
    icol = _resolve_col(header, _IMPACT_COLS)

    # McDonald-Kreitman columns take precedence: they carry a real significance test.
    acol = _resolve_col(header, _ALPHA_COLS)
    doscol = _resolve_col(header, _DOS_COLS)
    dncol, dscol = _resolve_col(header, _DN_COLS), _resolve_col(header, _DS_COLS)
    pncol, pscol = _resolve_col(header, _PN_COLS), _resolve_col(header, _PS_COLS)
    have_counts = all((dncol, dscol, pncol, pscol))
    mkpcol = p_col or _resolve_col(header, _MK_P_COLS)
    is_mk = bool(acol or doscol or have_counts) and stat_col is None

    evidence: dict[str, dict] = {}
    gate = None
    if is_mk:
        mode = "mcdonald-kreitman(gated)"
        raw: dict[str, dict] = {}
        for r in rows:
            g = (r.get(gcol) or "").strip()
            if not g:
                continue
            alpha = _to_float(r.get(acol)) if acol else None
            dos = _to_float(r.get(doscol)) if doscol else None
            p = _to_float(r.get(mkpcol)) if mkpcol else None
            if alpha is None and dos is None and have_counts:
                dn, ds, pn, ps = (_to_int(r.get(dncol)), _to_int(r.get(dscol)),
                                  _to_int(r.get(pncol)), _to_int(r.get(pscol)))
                if dn is not None and ds is not None and pn is not None and ps is not None:
                    dos, alpha, _ni, pc = _mk_stats(dn, ds, pn, ps, with_p=(p is None))
                    if p is None:
                        p = pc
            direction = alpha if alpha is not None else dos
            if direction is None:
                continue
            d = {"alpha": alpha, "dos": dos, "p": p, "direction": round(direction, 4)}
            prev = raw.get(g)
            if prev is None or direction > prev["direction"]:   # strongest signal per gene
                raw[g] = d
        with_p = [(g, d["p"]) for g, d in raw.items() if d["p"] is not None]
        qmap = _bh_fdr(with_p) if fdr else {}
        n_no_p = sum(1 for d in raw.values() if d["p"] is None)
        for g, d in raw.items():
            if d["direction"] <= alpha_min:
                continue
            sig = qmap.get(g) if fdr else d["p"]
            if sig is None or sig >= max_p:                     # no significance -> not gated in
                continue
            evidence[g] = dict(d, q=qmap.get(g), significant=True, mode=mode)
        gate = {"alpha_min": alpha_min, "max_p": max_p, "fdr": bool(fdr),
                "alpha_col": acol, "dos_col": doscol, "p_col": mkpcol,
                "counts": [dncol, dscol, pncol, pscol] if have_counts else None,
                "n_tested": len(raw), "n_significant": len(evidence), "n_without_p": n_no_p}
    elif scol:
        mode = "per-gene-statistic"
        for r in rows:
            g = (r.get(gcol) or "").strip()
            sv = _to_float(r.get(scol))
            if not g or sv is None or sv <= min_stat:
                continue
            if pcol:
                pv = _to_float(r.get(pcol))
                if pv is not None and pv >= max_p:
                    continue
            prev = evidence.get(g)
            if prev is None or sv > prev["stat"]:
                evidence[g] = {"stat": sv, "p": _to_float(r.get(pcol)) if pcol else None,
                               "stat_col": scol, "mode": mode}
    elif ecol or icol:
        mode = "variant-count(non-synonymous)"
        counts: Counter[str] = Counter()
        for r in rows:
            g = (r.get(gcol) or "").strip()
            if not g:
                continue
            eff = (r.get(ecol) or "").lower() if ecol else ""
            imp = (r.get(icol) or "").upper() if icol else ""
            syn = "synonymous" in eff or imp == "LOW"
            nonsyn = (not syn) and (imp in {"MODERATE", "HIGH"}
                                    or any(k in eff for k in _NONSYN_KW))
            if nonsyn:
                counts[g] += 1
        for g, c in counts.items():
            if c >= min_variants:
                evidence[g] = {"n_nonsyn": c, "mode": mode}
    else:
        mode = "all-genes(no statistic/effect column)"
        for r in rows:
            g = (r.get(gcol) or "").strip()
            if g and g not in evidence:
                evidence[g] = {"mode": mode}

    meta = {"gene_col": gcol, "stat_col": scol, "p_col": pcol, "effect_col": ecol,
            "impact_col": icol, "mode": mode, "n_rows": len(rows),
            "min_stat": min_stat, "max_p": max_p, "min_variants": min_variants,
            "gate": gate}
    return list(evidence), evidence, meta


class _RvResolver:
    """gene/locus -> Rv, local-first via mtbc-gene-function (annotation_mtbc xref)."""

    def __init__(self):
        self._la = None
        self._cache: dict[str, str | None] = {}
        try:
            from mtbc_gene_function.local import LocalAnnotation
            la = LocalAnnotation()
            if la.available():
                self._la = la
        except Exception:
            self._la = None

    def rv(self, gene: str) -> str | None:
        if gene in self._cache:
            return self._cache[gene]
        out = None
        if self._la is not None:
            try:
                out = self._la.resolve_rv(gene)
            except Exception:
                out = None
        if out is None:                      # fall back to the CDS-fasta resolver
            try:
                out = annotate_gene(gene, use_esm=False).locus_tag
            except Exception:
                out = gene if gene[:2].lower() == "rv" else None
        self._cache[gene] = out
        return out


def _selection_paragraph(r: SelectionReport) -> str:
    lead = f"In {r.lineage}, the" if r.lineage else "The"
    g = r.gate
    if g is not None:                                   # McDonald-Kreitman, significance-gated
        corr = "BH-FDR " if g.get("fdr") else ""
        crit = f"alpha>{g['alpha_min']:g}, {corr}p<{g['max_p']:g}"
        if not r.test_concluded:
            extra = (f"; {g['n_without_p']} lacked a p-value" if g.get("n_without_p") else "")
            return (f"{lead} McDonald-Kreitman test did not yield a significant per-gene "
                    f"signal ({g['n_tested']} gene(s) tested; 0 pass {crit}{extra}). "
                    "No selection section should be written.")
        parts = [f"{lead} McDonald-Kreitman test flags {r.n_selected_genes} gene(s) under "
                 f"positive selection ({crit}; of {g['n_tested']} tested)."]
    else:
        parts = [f"{lead} selection signal concerns {r.n_selected_genes} gene(s) "
                 f"[{r.selection.get('mode')}]."]
    m = r.selected_module
    if m and "density" in m:
        coh = ("form a cohesive PPI module" if m.get("cohesive")
               else "are only loosely connected in the interactome")
        hub = f" (hub {m['hub']})" if m.get("hub") else ""
        parts.append(f"The selected genes {coh}{hub}: {m['n_internal_edges']} internal edges "
                     f"among {m['n_genes_in_network']} genes, density {m['density']}.")
    if r.n_pathways_hit and r.pathway_hits:
        top = r.pathway_hits[0]
        parts.append(f"{r.n_pathways_hit} catalogue pathway(s) are affected; most strongly "
                     f"{top['pathway']} ({top['n_selected']}/{top['n_pathway_genes']} genes: "
                     f"{', '.join(top['selected_in_pathway'][:6])}).")
        if top.get("narration"):
            parts.append(top["narration"])
    else:
        parts.append("No catalogue pathway is hit; the signal is off-catalogue.")
    if r.off_catalogue:
        parts.append(f"{len(r.off_catalogue)} selected gene(s) lie outside every catalogue "
                     f"pathway: " + ", ".join(r.off_catalogue[:8]) + ".")
    return " ".join(parts)


def from_selection(table_path, *, lineage: str | None = None,
                   catalogue_path: Path | None = None, use_esm: bool = False,
                   with_network: bool = True, min_score: int = 400, top: int | None = 5,
                   gene_col: str | None = None, stat_col: str | None = None,
                   p_col: str | None = None, min_stat: float = 1.0, max_p: float = 0.05,
                   min_variants: int = 1, alpha_min: float = 0.0,
                   fdr: bool = True) -> SelectionReport:
    """From a lineage's selection table → narration of the affected pathways.

    Reads the gene set under selection, resolves everything to Rv (local-first),
    maps it onto the pathway catalogue, narrates the top affected pathways in full
    (curated + PPI) while overlaying which genes carry the signal, checks whether the
    selected set is itself a cohesive PPI module, and lists off-catalogue hits.

    For a McDonald-Kreitman table (`mk-ascertainment` output), the genes are
    significance-GATED (positive direction + BH-FDR p < ``max_p``) and
    ``report.test_concluded`` reports whether any gene passed -- so a caller (the Atlas)
    can write a `selection` section only when the test actually concluded.
    """
    genes, _evidence, meta = genes_under_selection(
        table_path, gene_col=gene_col, stat_col=stat_col, p_col=p_col,
        min_stat=min_stat, max_p=max_p, min_variants=min_variants,
        alpha_min=alpha_min, fdr=fdr)
    is_mk = str(meta.get("mode", "")).startswith("mcdonald-kreitman")
    test_concluded = bool(genes) if is_mk else None

    catalogue = load_catalogue(extra=catalogue_path)
    resolver = _RvResolver()
    sel_rv: dict[str, str] = {}
    for g in genes:
        rv = resolver.rv(g)
        if rv:
            sel_rv.setdefault(rv, g)

    hits, covered = [], set()
    for pid, entry in catalogue.items():
        prv = {}
        for cg in entry.get("genes") or []:
            rv = resolver.rv(cg)
            if rv:
                prv[rv] = cg
        inter = sorted(prv[rv] for rv in prv if rv in sel_rv)
        if inter:
            covered.update(rv for rv in prv if rv in sel_rv)
            n_path = len(prv) or len(entry.get("genes") or [])
            hits.append({"pathway": pid, "description": entry.get("description"),
                         "n_pathway_genes": n_path, "n_selected": len(inter),
                         "fraction": round(len(inter) / n_path, 3) if n_path else 0.0,
                         "selected_in_pathway": inter})
    hits.sort(key=lambda h: (h["n_selected"], h["fraction"]), reverse=True)

    for h in (hits[:top] if top else hits):     # narrate the top hits in full
        try:
            rep = explain_pathway(h["pathway"], catalogue_path=catalogue_path,
                                  use_esm=use_esm, with_network=with_network,
                                  min_score=min_score)
            h.update(ec_classes=rep.ec_classes, pfam_domains=rep.pfam_domains,
                     dark_genes=rep.dark_genes, network=rep.network,
                     narration=rep.paragraph)
        except PathwayNotFound:
            pass

    off = sorted({sel_rv[rv] for rv in sel_rv if rv not in covered})
    module = (_network_context(list(sel_rv), min_score=min_score)
              if with_network and len(sel_rv) >= 2 else None)

    report = SelectionReport(
        lineage=lineage, table=str(table_path), selection=meta,
        n_selected_genes=len(genes), selected_genes=sorted(genes),
        test_concluded=test_concluded, gate=meta.get("gate"),
        selected_module=module, n_pathways_hit=len(hits), pathway_hits=hits,
        off_catalogue=off)
    report.paragraph = _selection_paragraph(report)
    return report
