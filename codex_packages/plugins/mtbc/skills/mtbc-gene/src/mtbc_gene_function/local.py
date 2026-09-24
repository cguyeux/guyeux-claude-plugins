"""Curated local annotation from the annotation_mtbc project (the PRIMARY source).

annotation_mtbc holds a multi-source, per-gene functional annotation already computed
once over the whole H37Rv proteome, keyed by Rv locus tag:

  data/gene_xref_all.tsv                 product, hypothetical flag, length, strand (3943 genes)
  resultats/phase2e_uniprot/uniprot.json curated UniProt function text + EC + protein name
  resultats/phase2b_pfam/pfam.json       Pfam domains
  resultats/phase2h_string/string.json   STRING partners (guilt-by-association)
  resultats/phase2f_conservation/...     pN/pS, selection regime, pseudogene flag
  resultats/phase2_esm/Rv####.json       local ESM run (partial)
  data/structural_candidates_ext.tsv     Foldseek structural suggestion (for dark genes)

This module reads that consolidated knowledge so the skill answers from your own
validated work first, and only falls back to the ESM Atlas API for what is not yet
annotated. Graceful: if the project is not present, ``available()`` returns False and
the skill stays in ESM-only mode.
"""
from __future__ import annotations

import csv
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

ANNOTATION_DIR = Path(
    os.environ.get("MTBC_ANNOTATION_DIR", "~/docs/codes/mtbc/en_cours/annotation_mtbc")
).expanduser()


class LocalAnnotationUnavailable(Exception):
    """Raised when the annotation_mtbc project (or its xref table) is not present."""


@dataclass
class LocalGeneRecord:
    rv: str
    gene: str | None = None
    product: str | None = None
    product_pgap: str | None = None
    is_hypothetical: bool | None = None
    length_aa: int | None = None
    strand: str | None = None
    uniprot: dict | None = None             # {acc, protein_name, ec, function, reviewed}
    pfam: list = field(default_factory=list)
    string: dict | None = None              # {n_partners, partners[...]}
    conservation: dict | None = None        # {pN_pS, selection, pseudogene_flag, ...}
    structural_candidate: dict | None = None  # {tm, evalue, suggested}
    esm_local: bool = False
    channels: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class LocalAnnotation:
    """Lazy reader/index over the annotation_mtbc per-gene outputs."""

    def __init__(self, root: Path | None = None):
        self.root = Path(root or ANNOTATION_DIR)
        self._xref: dict[str, dict] | None = None
        self._name_to_rv: dict[str, str] = {}
        self._np_to_rv: dict[str, str] = {}
        self._cache: dict[str, dict] = {}
        self._structural: dict[str, dict] | None = None

    # ── availability + resolution ────────────────────────────────────────────

    def _xref_path(self) -> Path:
        return self.root / "data" / "gene_xref_all.tsv"

    def available(self) -> bool:
        return self._xref_path().exists()

    def _load_xref(self) -> dict[str, dict]:
        if self._xref is not None:
            return self._xref
        p = self._xref_path()
        if not p.exists():
            raise LocalAnnotationUnavailable(
                f"annotation_mtbc not found at {self.root} "
                "(set MTBC_ANNOTATION_DIR to its path)."
            )
        xref: dict[str, dict] = {}
        with p.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                rv = (row.get("rv") or "").strip()
                if not rv:
                    continue
                xref[rv] = row
                gene = (row.get("gene") or "").strip().lower()
                if gene:
                    self._name_to_rv.setdefault(gene, rv)
                npid = (row.get("np_id") or "").strip()
                if npid:
                    self._np_to_rv.setdefault(npid, rv)
        self._xref = xref
        return xref

    def resolve_rv(self, query: str) -> str | None:
        """Map an Rv locus tag, a gene name, or an NP_ accession to its Rv id."""
        xref = self._load_xref()
        q = query.strip()
        if q in xref:
            return q
        ql = q.lower()
        if ql in self._name_to_rv:
            return self._name_to_rv[ql]
        if q in self._np_to_rv:
            return self._np_to_rv[q]
        for rv in xref:
            if rv.lower() == ql:
                return rv
        return None

    # ── per-phase loaders (cached) ───────────────────────────────────────────

    def _phase(self, relpath: str) -> dict:
        if relpath not in self._cache:
            p = self.root / "résultats" / relpath
            try:
                self._cache[relpath] = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self._cache[relpath] = {}
        return self._cache[relpath]

    def _structural_table(self) -> dict[str, dict]:
        if self._structural is None:
            self._structural = {}
            for name in ("structural_candidates_ext.tsv", "structural_candidates.tsv"):
                p = self.root / "data" / name
                if not p.exists():
                    continue
                with p.open(encoding="utf-8", newline="") as f:
                    for row in csv.DictReader(f, delimiter="\t"):
                        rv = (row.get("rv") or "").strip()
                        if rv:
                            self._structural.setdefault(rv, {
                                "tm": row.get("tm"), "evalue": row.get("evalue"),
                                "suggested": row.get("suggested"),
                            })
        return self._structural

    def _esm_local(self, rv: str) -> bool:
        return (self.root / "résultats" / "phase2_esm" / f"{rv}.json").exists()

    # ── the consolidated record ──────────────────────────────────────────────

    def record(self, query: str) -> LocalGeneRecord:
        """Consolidated curated annotation for a gene, or raise GeneNotFound-style None."""
        rv = self.resolve_rv(query)
        if rv is None:
            raise LocalAnnotationUnavailable(f"{query!r} not in annotation_mtbc gene_xref")
        row = self._load_xref()[rv]
        hyp = (row.get("is_hypothetical_h37rv") or "").strip().lower()
        try:
            length = int(float(row.get("len_aa") or 0)) or None
        except ValueError:
            length = None

        rec = LocalGeneRecord(
            rv=rv,
            gene=(row.get("gene") or "").strip() or None,
            product=(row.get("product_h37rv") or "").strip() or None,
            product_pgap=(row.get("product_mtbc0_pgap") or "").strip() or None,
            is_hypothetical=(hyp in {"1", "true", "yes", "y"}) if hyp else None,
            length_aa=length,
            strand=(row.get("strand") or "").strip() or None,
        )
        up = self._phase("phase2e_uniprot/uniprot.json").get(rv)
        if up:
            rec.uniprot = {k: up.get(k) for k in ("acc", "protein_name", "ec", "function", "reviewed")}
            rec.channels.append("uniprot")
        pf = self._phase("phase2b_pfam/pfam.json").get(rv)
        if pf:
            rec.pfam = pf
            rec.channels.append("pfam")
        st = self._phase("phase2h_string/string.json").get(rv)
        if st:
            rec.string = {"n_partners": st.get("n_partners"), "partners": (st.get("partners") or [])[:5]}
            rec.channels.append("string")
        cons = self._phase("phase2f_conservation/conservation.json").get(rv)
        if cons:
            rec.conservation = cons
            rec.channels.append("conservation")
        struct = self._structural_table().get(rv)
        if struct:
            rec.structural_candidate = struct
            rec.channels.append("structural")
        if self._esm_local(rv):
            rec.esm_local = True
            rec.channels.append("esm_local")
        return rec
