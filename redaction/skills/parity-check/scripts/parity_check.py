#!/usr/bin/env python3
"""Verification de parite entre la version anglaise et la version francaise d'un
meme manuscrit LaTeX (piste Y2, `environnement`, 2026-09-22).

Pourquoi cet outil existe : les deux versions d'un manuscrit bilingue sont
verifiees separement (deux `/manuscript-review`, deux contre-expertises), et
personne ne verifie que les DEUX portent le meme fond. Cas fondateur, mesure le
2026-09-19 sur `lineage_subdivision_methods` : un correctif applique la veille
a `main_fr.tex` seul laissait dans `main.tex` un chiffre (96,91 %) cite en
Results sans qu'aucune section ni aucun tableau anglais ne le definisse -- dans
la seule version que liront les relecteurs. Aucune des deux relectures
independantes ne pouvait le voir : chacune ne lit que le fond d'UNE version.

Ce que fait le script :
  1. resout les `\\input`/`\\include` des deux fichiers ;
  2. decoupe chacun en sections top-level (`\\section{...}`) ;
  3. aligne les sections EN et FR entre elles -- par `\\label{}` partage
     d'abord (le plus fiable : un label est en general recopie a l'identique
     entre les deux versions pour que les `\\ref` internes fonctionnent),
     puis par ordre positionnel pour ce qui reste ;
  4. pour chaque paire alignee, compare les NOMBRES, les CITATIONS
     (`\\cite`/`\\citep`/`\\citet`), les RENVOIS internes (`\\ref`/`\\cref`/
     `\\eqref`) et les MENTIONS de supplementary (`Table Sx`, `Figure Sx`) --
     et signale tout element present d'un seul cote.

Le script NE JUGE PAS le fond des phrases (ce n'est pas une traduction
automatique verifiee) : c'est un filet MECANIQUE qui rattrape les divergences
CHIFFREES, BIBLIOGRAPHIQUES et STRUCTURELLES, moins couteuses a detecter que
la relecture complete des deux versions phrase a phrase -- qui reste necessaire
en complement pour les divergences purement redactionnelles (cf. SKILL.md).

Usage :
    python3 parity_check.py main.tex main_fr.tex
    python3 parity_check.py main.tex main_fr.tex --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

SECTION_RE = re.compile(r"\\(section|subsection)\*?\{([^}]*)\}")
LABEL_AFTER_SECTION = re.compile(r"\\label\{([^}]*)\}")
CITE_RE = re.compile(r"\\cite[pt]?\*?(?:\[[^\]]*\])?\{([^}]*)\}")
REF_RE = re.compile(r"\\(?:cref|Cref|eqref|ref)\{([^}]*)\}")
SUPP_MENTION_RE = re.compile(r"\b(?:Table|Figure|Fig\.)\s*S(\d+)\b")
# Nombres portes par une commande technique (numerotation, renvoi) : jamais un resultat.
IGNORE_CONTEXT = re.compile(
    r"\\(cite[pt]?|ref|cref|Cref|eqref|label|section|subsection|includegraphics|"
    r"documentclass|usepackage|newcommand|pageref|footnote)", re.I)
# Meme convention que claim-check/numeric_crosscheck.py : virgule anglaise des
# milliers, espace fine ou insecable LaTeX, virgule decimale francaise.
NUM = re.compile(r"(?<![\w.])(-|\u2212)?(\d{1,3}(?:(?:,|\\,|~)\d{3})+|\d+)([.,]\d+)?(?![\w])")


def resolve_inputs(path: Path, seen: set[Path] | None = None, depth: int = 0) -> str:
    """Concatene le .tex et ses \\input/\\include -- un manuscrit decoupe en
    squelette + sections doit etre lu dans son integralite, pas seulement le
    squelette."""
    seen = seen if seen is not None else set()
    path = path.resolve()
    if path in seen or depth > 6 or not path.exists():
        return ""
    seen.add(path)
    text = path.read_text(encoding="utf-8", errors="replace")

    def sub(m: re.Match) -> str:
        target = m.group(2).strip()
        cand = path.parent / target
        for c in (cand, cand.with_suffix(".tex"), Path(str(cand) + ".tex")):
            if c.exists() and c.is_file():
                return "\n" + resolve_inputs(c, seen, depth + 1) + "\n"
        return ""

    return re.sub(r"\\(input|include)\{([^}]*)\}", sub, text)


def is_decimal_comma(tex: str) -> bool:
    return bool(re.search(r"\\usepackage\[[^]]*\b(french|francais)\b", tex, re.I))


def _parse_number(sign: str | None, integer: str, frac: str | None, decimal_comma: bool) -> float | None:
    whole = re.sub(r"(,|\\,|~)", "", integer)
    if frac:
        whole += "." + frac[1:]
    elif decimal_comma and re.fullmatch(r"\d{1,3},\d{3}", integer):
        whole = integer.replace(",", ".")
    try:
        v = float(whole)
    except ValueError:
        return None
    return -v if sign else v


def split_sections(tex: str) -> list[dict]:
    """Sections top-level (`\\section`) en ordre document, avec leur span de
    texte jusqu'a la section suivante, `\\bibliography`, `\\appendix` ou la fin."""
    doc_start = tex.find("\\begin{document}")
    body_start = doc_start if doc_start >= 0 else 0
    end = len(tex)
    for stop_pat in (r"\\bibliography\{", r"\\appendix\b", r"\\end\{document\}"):
        m = re.search(stop_pat, tex[body_start:])
        if m:
            end = min(end, body_start + m.start())

    matches = [m for m in SECTION_RE.finditer(tex, body_start, end) if m.group(1) == "section"]
    sections = []
    for i, m in enumerate(matches):
        seg_start = m.end()
        seg_end = matches[i + 1].start() if i + 1 < len(matches) else end
        label_m = LABEL_AFTER_SECTION.search(tex[seg_start:seg_start + 200])
        sections.append({
            "index": i,
            "title": m.group(2).strip(),
            "label": label_m.group(1) if label_m else None,
            "text": tex[seg_start:seg_end],
            "line": tex[:m.start()].count("\n") + 1,
        })
    return sections


def extract_numbers(text: str, decimal_comma: bool) -> Counter:
    out = Counter()
    for line in text.split("\n"):
        if line.lstrip().startswith("%") or IGNORE_CONTEXT.search(line):
            continue
        for m in NUM.finditer(line):
            v = _parse_number(m.group(1), m.group(2), m.group(3), decimal_comma)
            if v is not None:
                out[round(v, 4)] += 1
    return out


def extract_keys(text: str, pattern: re.Pattern) -> Counter:
    out = Counter()
    for m in pattern.finditer(text):
        for k in m.group(1).split(","):
            k = k.strip()
            if k:
                out[k] += 1
    return out


def extract_supp_mentions(text: str) -> Counter:
    out = Counter()
    for m in SUPP_MENTION_RE.finditer(text):
        out[f"S{m.group(1)}"] += 1
    return out


def align_sections(en_secs: list[dict], fr_secs: list[dict]):
    """Aligne par `\\label` partage d'abord (le plus fiable), puis par ordre
    positionnel pour ce qui reste. Ce qui ne trouve pas de contrepartie est
    une divergence STRUCTURELLE, jamais forcee dans une paire."""
    en_by_label = {s["label"]: s for s in en_secs if s["label"]}
    fr_by_label = {s["label"]: s for s in fr_secs if s["label"]}
    shared_labels = [l for l in en_by_label if l in fr_by_label]

    pairs = []
    matched_en, matched_fr = set(), set()
    for l in shared_labels:
        e, f = en_by_label[l], fr_by_label[l]
        pairs.append((e, f, "label"))
        matched_en.add(e["index"])
        matched_fr.add(f["index"])

    remaining_en = [s for s in en_secs if s["index"] not in matched_en]
    remaining_fr = [s for s in fr_secs if s["index"] not in matched_fr]

    for e, f in zip(remaining_en, remaining_fr):
        pairs.append((e, f, "position"))

    unmatched = []
    if len(remaining_en) != len(remaining_fr):
        if len(remaining_en) > len(remaining_fr):
            side, extra = "en", remaining_en[len(remaining_fr):]
        else:
            side, extra = "fr", remaining_fr[len(remaining_en):]
        unmatched = [(side, s) for s in extra]

    pairs.sort(key=lambda p: p[0]["index"])
    return pairs, unmatched


def counter_diff(a: Counter, b: Counter) -> dict:
    """Elements de `a` en exces par rapport a `b` (compte)."""
    return dict(a - b)


def compare_documents(en_path: Path, fr_path: Path) -> dict:
    en_raw = resolve_inputs(en_path)
    fr_raw = resolve_inputs(fr_path)
    en_dc, fr_dc = is_decimal_comma(en_raw), is_decimal_comma(fr_raw)
    en_secs, fr_secs = split_sections(en_raw), split_sections(fr_raw)
    pairs, unmatched = align_sections(en_secs, fr_secs)

    report: dict = {
        "n_sections_en": len(en_secs),
        "n_sections_fr": len(fr_secs),
        "unmatched": [
            {"side": side, "index": s["index"], "title": s["title"], "line": s["line"]}
            for side, s in unmatched
        ],
        "pairs": [],
    }
    any_mismatch = bool(unmatched)

    for e, f, how in pairs:
        only_en_nums = counter_diff(extract_numbers(e["text"], en_dc), extract_numbers(f["text"], fr_dc))
        only_fr_nums = counter_diff(extract_numbers(f["text"], fr_dc), extract_numbers(e["text"], en_dc))
        only_en_cites = counter_diff(extract_keys(e["text"], CITE_RE), extract_keys(f["text"], CITE_RE))
        only_fr_cites = counter_diff(extract_keys(f["text"], CITE_RE), extract_keys(e["text"], CITE_RE))
        only_en_refs = counter_diff(extract_keys(e["text"], REF_RE), extract_keys(f["text"], REF_RE))
        only_fr_refs = counter_diff(extract_keys(f["text"], REF_RE), extract_keys(e["text"], REF_RE))
        only_en_supp = counter_diff(extract_supp_mentions(e["text"]), extract_supp_mentions(f["text"]))
        only_fr_supp = counter_diff(extract_supp_mentions(f["text"]), extract_supp_mentions(e["text"]))

        mismatch = any([only_en_nums, only_fr_nums, only_en_cites, only_fr_cites,
                         only_en_refs, only_fr_refs, only_en_supp, only_fr_supp])
        any_mismatch = any_mismatch or mismatch

        report["pairs"].append({
            "en_title": e["title"], "fr_title": f["title"], "how": how,
            "en_line": e["line"], "fr_line": f["line"],
            "status": "MISMATCH" if mismatch else "OK",
            "numbers_only_en": only_en_nums, "numbers_only_fr": only_fr_nums,
            "citations_only_en": only_en_cites, "citations_only_fr": only_fr_cites,
            "refs_only_en": only_en_refs, "refs_only_fr": only_fr_refs,
            "supp_only_en": only_en_supp, "supp_only_fr": only_fr_supp,
        })

    report["status"] = "MISMATCH" if any_mismatch else "OK"
    return report


def print_report(report: dict) -> None:
    print(f"Parite EN/FR : {report['n_sections_en']} sections EN, {report['n_sections_fr']} sections FR\n")

    if report["unmatched"]:
        print("STRUCTURE -- section(s) sans contrepartie :")
        for u in report["unmatched"]:
            print(f"  [{u['side'].upper()}] l.{u['line']:<5} {u['title']}")
        print()

    for p in report["pairs"]:
        tag = "OK      " if p["status"] == "OK" else "MISMATCH"
        print(f"[{tag}] EN l.{p['en_line']:<4} « {p['en_title']} »  <->  "
              f"FR l.{p['fr_line']:<4} « {p['fr_title']} »  ({p['how']})")
        if p["status"] != "MISMATCH":
            continue
        for label, key in (
            ("nombres seulement EN", "numbers_only_en"),
            ("nombres seulement FR", "numbers_only_fr"),
            ("citations seulement EN", "citations_only_en"),
            ("citations seulement FR", "citations_only_fr"),
            ("renvois seulement EN", "refs_only_en"),
            ("renvois seulement FR", "refs_only_fr"),
            ("mentions supp. seulement EN", "supp_only_en"),
            ("mentions supp. seulement FR", "supp_only_fr"),
        ):
            if p[key]:
                print(f"    {label} : {sorted(p[key])}")

    print()
    print("PARITE OK" if report["status"] == "OK" else "DIVERGENCES DETECTEES -- voir ci-dessus")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("en_tex", help="version anglaise (ou de reference) du manuscrit")
    ap.add_argument("fr_tex", help="version francaise a comparer")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    en_path, fr_path = Path(a.en_tex), Path(a.fr_tex)
    for p in (en_path, fr_path):
        if not p.exists():
            print(f"Fichier introuvable : {p}", file=sys.stderr)
            return 2

    report = compare_documents(en_path, fr_path)
    if a.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report)
    return 0 if report["status"] == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
