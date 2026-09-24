"""Offline smoke test for the ESM-1v LLR module.

Exercises the torch-free logic (mutation parsing, context windowing) and REPORTS
whether torch + fair-esm are importable, WITHOUT loading the ~2.6 GB model. Easiest run
is `mtbc-gene/run_llr.sh --smoke`, which wires everything; by hand it needs this skill's
src/ on PYTHONPATH and a torch+fair-esm interpreter:

    SK=/home/christophe/docs/environnement/plugins/mtbc/skills
    PYTHONPATH="$SK/mtbc-gene/src" \\
      /home/christophe/venvs/esm1v/bin/python -m mtbc_mutation_impact.smoke_test
"""
from __future__ import annotations

import sys

from mtbc_mutation_impact.llr import LLRError, _require_esm, _window, llr_of


def main() -> int:
    # 1. context window: a >MAXLEN sequence is clipped to <=1022 and the mutated
    #    residue is preserved at the returned index.
    seq = "MA" + "K" * 2000
    sub, idx = _window(seq, 1500)
    if len(sub) > 1022 or sub[idx] != seq[1500]:
        print(f"FAIL: window broken (len={len(sub)}, idx={idx})", file=sys.stderr)
        return 2
    short, idx2 = _window("ABCDE", 2)
    if short != "ABCDE" or idx2 != 2:
        print("FAIL: short sequence should pass through unchanged", file=sys.stderr)
        return 2

    # 2. malformed mutation must raise LLRError (no torch / no CDS needed).
    try:
        llr_of("katG", "not_a_mutation")
        print("FAIL: a malformed mutation should raise LLRError", file=sys.stderr)
        return 2
    except LLRError:
        pass

    # 3. report torch + fair-esm availability (do NOT download model weights).
    try:
        _require_esm()
        print("torch + fair-esm: AVAILABLE — ready to score (weights download on first use)")
    except LLRError as exc:
        print(f"torch + fair-esm: NOT available — {exc}")
        print("  (run via /home/christophe/venvs/esm1v/bin/python to score for real)")

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
