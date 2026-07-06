"""Offline smoke test: narrate a real gene set curated-first + with network context.

Uses the oxidative-stress regulon (katG, ahpC, furA, sodA, sodC) -- all real genes in
annotation_mtbc and the interactome -- and checks the narration aggregates curated
enzyme classes / Pfam domains and reports a cohesive PPI subnetwork. Skips cleanly if
annotation_mtbc is not present. Needs mtbc-gene-function (+ mtbc-gene-network) on
PYTHONPATH (use run_pathway.sh).

    python3 -m mtbc_pathway_explain.smoke_test
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from mtbc_pathway_explain.core import (explain_gene_set, from_selection,
                                       genes_from_network, genes_under_selection)


def _selection_checks() -> int:
    """from_selection on synthetic tables: per-gene dN/dS, then variant-level."""
    with tempfile.TemporaryDirectory() as d:
        # 1. per-gene statistic table: katG/ahpC/furA pass (dN/dS>1, p<.05), sodA/gyrA not.
        t1 = Path(d) / "dnds.tsv"
        t1.write_text("gene\tdN/dS\tfisher_p_vs_bg\n"
                      "katG\t1.8\t0.01\nahpC\t1.5\t0.02\nsodA\t0.6\t0.40\n"
                      "furA\t2.1\t0.03\ngyrA\t0.5\t0.50\n", encoding="utf-8")
        genes, _ev, meta = genes_under_selection(t1)
        print(f"per-gene: selected {sorted(genes)} via {meta['stat_col']}/{meta['p_col']}")
        if sorted(genes) != ["ahpC", "furA", "katG"]:
            print(f"FAIL: per-gene filter should keep katG/ahpC/furA, got {genes}", file=sys.stderr)
            return 2
        rep = from_selection(t1, lineage="L-TEST", top=3)
        print(f"per-gene: {rep.n_pathways_hit} pathway(s) hit; "
              f"top={rep.pathway_hits[0]['pathway'] if rep.pathway_hits else None}")
        if rep.n_selected_genes != 3:
            print(f"FAIL: expected 3 selected genes, got {rep.n_selected_genes}", file=sys.stderr)
            return 2
        if rep.n_pathways_hit:                      # mapping needs annotation_mtbc / CDS fasta
            hit_genes = {g for h in rep.pathway_hits for g in h["selected_in_pathway"]}
            if "katG" not in hit_genes:
                print(f"FAIL: katG should map onto a pathway, got {hit_genes}", file=sys.stderr)
                return 2
            print(f"per-gene: katG mapped; paragraph -> {rep.paragraph[:90]}...")
        else:
            print("(no pathway mapping: annotation_mtbc/CDS fasta absent; resolution skipped)")

        # 2. variant-level table: count non-synonymous per gene; LOW/synonymous excluded.
        t2 = Path(d) / "variants.csv"
        t2.write_text("Locus_tag,Gene_name,Effect,Impact\n"
                      "Rv1908c,katG,missense_variant,MODERATE\n"
                      "Rv1908c,katG,synonymous_variant,LOW\n"
                      "Rv2428,ahpC,missense_variant,MODERATE\n"
                      "Rv0667,rpoB,synonymous_variant,LOW\n", encoding="utf-8")
        gv, _e2, mv = genes_under_selection(t2)
        print(f"variant-level: selected {sorted(gv)} via {mv['mode']} (col {mv['gene_col']})")
        if sorted(gv) != ["Rv1908c", "Rv2428"]:
            print(f"FAIL: variant mode should keep Rv1908c/Rv2428 (non-syn), got {gv}", file=sys.stderr)
            return 2

        # 3. McDonald-Kreitman table, significance-GATED (alpha + p, BH-FDR).
        t3 = Path(d) / "mk.tsv"
        t3.write_text("gene\talpha\tp_fisher\n"
                      "katG\t0.95\t0.0001\nahpC\t0.80\t0.002\n"
                      "gyrA\t0.05\t0.60\nsodA\t-0.20\t0.90\n", encoding="utf-8")
        rep3 = from_selection(t3, lineage="L-MK")
        print(f"MK gate: concluded={rep3.test_concluded}; selected={rep3.selected_genes}; "
              f"gate n_sig={rep3.gate['n_significant']}/{rep3.gate['n_tested']}")
        if rep3.test_concluded is not True or sorted(rep3.selected_genes) != ["ahpC", "katG"]:
            print(f"FAIL: MK gate should keep katG/ahpC (alpha>0, FDR<.05), got {rep3.selected_genes}",
                  file=sys.stderr)
            return 2
        if "McDonald-Kreitman test flags 2" not in rep3.paragraph:
            print(f"FAIL: paragraph should report the MK gate verdict: {rep3.paragraph[:120]}",
                  file=sys.stderr)
            return 2

        # 4. MK table where nothing passes -> test did not conclude (no section to write).
        t4 = Path(d) / "mk_ns.tsv"
        t4.write_text("gene\talpha\tp_fisher\nkatG\t0.9\t0.20\nahpC\t0.8\t0.30\n", encoding="utf-8")
        rep4 = from_selection(t4, lineage="L-NS")
        print(f"MK gate (null): concluded={rep4.test_concluded}; "
              f"para -> {rep4.paragraph[:80]}...")
        if rep4.test_concluded is not False or rep4.n_selected_genes != 0:
            print(f"FAIL: MK gate should NOT conclude when nothing is significant", file=sys.stderr)
            return 2
        if "No selection section should be written" not in rep4.paragraph:
            print("FAIL: not-concluded paragraph must advise against writing the section",
                  file=sys.stderr)
            return 2

        # 5. MK from raw counts (Dn/Ds/Pn/Ps): alpha recomputed offline, p supplied.
        t5 = Path(d) / "mk_counts.tsv"
        t5.write_text("gene\tDn\tDs\tPn\tPs\tp_fisher\nkatG\t33\t0\t10\t12\t0.0001\n", encoding="utf-8")
        g5, ev5, m5 = genes_under_selection(t5)
        a = ev5.get("katG", {}).get("alpha")
        print(f"MK counts: selected={g5}; recomputed alpha(katG)={a:.3f} via {m5['mode']}"
              if a is not None else f"MK counts: selected={g5} (alpha not recomputed)")
        if g5 != ["katG"] or a is None or a < 0.9:
            print(f"FAIL: counts->alpha should be high & gated in, got {g5}, alpha={a}", file=sys.stderr)
            return 2
    return 0


def main() -> int:
    genes = ["katG", "ahpC", "furA", "sodA", "sodC"]
    rep = explain_gene_set(genes, name="oxidative-stress", use_esm=False, with_network=True)
    print(f"annotated {rep.n_genes_annotated}/{rep.n_genes_total}; "
          f"ec={rep.ec_classes}; pfam={rep.pfam_domains[:3]}")
    print("network:", rep.network)

    if rep.n_genes_annotated < 4 or not (rep.ec_classes or rep.pfam_domains):
        print("annotation_mtbc not available (no curated EC/Pfam); skipping deep checks.",
              file=sys.stderr)
        return 0

    if not (rep.network and rep.network.get("n_internal_edges", 0) >= 1):
        print(f"FAIL: the oxidative-stress set should be PPI-connected, got {rep.network}",
              file=sys.stderr)
        return 2
    if "PPI" not in rep.paragraph:
        print("FAIL: paragraph should narrate the PPI structure", file=sys.stderr)
        return 2

    try:
        nb, label = genes_from_network("neighbors:katG")
        print(f"neighbors:katG -> {len(nb)} genes ({label})")
        if "katG" not in nb or len(nb) < 2:
            print(f"FAIL: neighbors:katG should include katG + partners, got {nb[:5]}",
                  file=sys.stderr)
            return 2
    except Exception as e:  # network optional
        print(f"(network neighbourhood check skipped: {e})", file=sys.stderr)

    rc = _selection_checks()
    if rc:
        return rc

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
