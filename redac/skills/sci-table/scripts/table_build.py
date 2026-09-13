#!/usr/bin/env python3
"""table_build.py — d'un CSV a un tableau LaTeX de qualite publication.

Fait les gestes qu'on oublie a la main, et DIT ce qu'il a fait : precision
homogene par colonne, unite remontee dans l'en-tete, colonne constante retiree,
p-values bornees, alignement decimal par siunitx, filets booktabs, legende
au-dessus, notes en threeparttable, et un verdict d'ancrage (colonne, pleine
largeur, rotation, longtable, supplementaire) fonde sur la largeur mesuree.

Usage
    python3 table_build.py data.csv --caption "..." --label tab:xxx
    python3 table_build.py data.csv --transpose --note "Les effectifs..." --preview
    python3 table_build.py data.csv --journal twocol --sig 3 --out table.tex

Options utiles
    --journal onecol|twocol|nature|plos   largeur cible
    --sig N            arrondi a N chiffres significatifs (defaut : precision homogene par colonne)
    --keep-constant    ne pas retirer les colonnes constantes
    --transpose        echanger lignes et colonnes
    --tabularray       sortir en tblr plutot qu'en tabular (voir skill latex-tables)
    --preview          compiler un PDF autonome et en tirer un PNG relisible

Sans dependance externe (csv, re, subprocess de la bibliotheque standard).
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import re
import statistics
import subprocess
import sys
import tempfile

# largeur utile en caracteres a 10 pt (voir table_lint.py)
TARGETS = {"onecol": 90, "twocol": 48, "nature": 85, "plos": 90, "elsevier": 48}

UNIT_RE = re.compile(r"^\s*([-+]?\d[\d\s,.]*)\s*(%|bp|kb|Mb|nt|aa|SNPs?|years?|ans|Gb|min|h|mm|cm|kg|g|x|\u00d7|\u00b0C)\s*$")
NUM_RE = re.compile(r"^[-+]?\d+(?:[.,]\d+)?(?:[eE][-+]?\d+)?$")
PVAL_HEAD = re.compile(r"\b(p|q|p-?val|q-?val|adj\.?\s*p|fdr)\b", re.I)


def latex_escape(s: str) -> str:
    if re.search(r"\\[a-zA-Z]+|\$", s):      # deja du LaTeX : ne pas y toucher
        return s
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"),
                 ("#", r"\#"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}"),
                 ("^", r"\textasciicircum{}")):
        s = s.replace(a, b)
    return s


def read_table(path):
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as fh:
        sample = fh.read(8192)
        fh.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        rows = [r for r in csv.reader(fh, dialect) if any(c.strip() for c in r)]
    if not rows:
        sys.exit("fichier vide")
    ncol = max(len(r) for r in rows)
    rows = [r + [""] * (ncol - len(r)) for r in rows]
    return rows[0], rows[1:]


def parse_num(cell):
    c = cell.strip().replace("\u00a0", "").replace(" ", "")
    if not c:
        return None
    m = UNIT_RE.match(cell)
    if m is not None:
        c = m.group(1).replace(" ", "")
    c = c.replace(",", ".") if c.count(",") == 1 and len(c.split(",")[-1]) != 3 else c.replace(",", "")
    if not NUM_RE.match(c):
        return None
    try:
        return float(c)
    except ValueError:
        return None


def decimals(cell):
    c = cell.strip().replace(" ", "")
    m = UNIT_RE.match(cell)
    if m is not None:
        c = m.group(1).replace(" ", "")
    if "e" in c.lower():
        return None
    m = re.search(r"[.,](\d+)$", c)
    return len(m.group(1)) if m else 0


def sig_round(x, sig):
    if x == 0 or not math.isfinite(x):
        return 0.0, 0
    d = max(0, sig - int(math.floor(math.log10(abs(x)))) - 1)
    return round(x, d), d


class Column:
    def __init__(self, head, cells):
        self.head = head.strip()
        self.raw = [c.strip() for c in cells]
        self.notes = []
        self.unit = None
        self.kind = "text"
        self.prec = 0
        self.analyse()

    def analyse(self):
        units = {UNIT_RE.match(c).group(2) for c in self.raw if UNIT_RE.match(c)}
        if len(units) == 1 and sum(1 for c in self.raw if UNIT_RE.match(c)) >= max(2, len(self.raw) // 2):
            self.unit = units.pop()
        nums = [parse_num(c) for c in self.raw]
        ok = [n for n in nums if n is not None]
        filled = [c for c in self.raw if c]
        if filled and len(ok) >= 0.7 * len(filled):
            self.kind = "pvalue" if PVAL_HEAD.search(self.head) else "num"
            decs = [decimals(c) for c in self.raw if parse_num(c) is not None]
            decs = [d for d in decs if d is not None]
            self.decs_observed = decs
            # homogeneiser vers le MAXIMUM inventerait des chiffres que la mesure
            # n'a pas ; vers le minimum jetterait de l'information reelle. La
            # mediane est le compromis, et l'ecart est signale a l'auteur.
            self.prec = int(statistics.median(sorted(decs))) if decs else 0
            self.values = nums
        else:
            self.values = [None] * len(self.raw)

    @property
    def constant(self):
        vals = [c for c in self.raw if c and c not in ("-", "--", "NA", "n/a")]
        return len(vals) >= 3 and len(set(vals)) == 1

    def format(self, sig=None, pmin=None):
        """Rend la liste des cellules formatees et fixe self.prec / self.fmt."""
        out = []
        if self.kind == "text":
            self.align = "l"
            return [latex_escape(c) if c else "---" for c in self.raw]

        if self.kind == "pvalue":
            floor = pmin if pmin else 1e-3
            for v, raw in zip(self.values, self.raw):
                if v is None:
                    out.append("---" if not raw else latex_escape(raw))
                elif v < floor:
                    out.append(f"$<{floor:g}$".replace("e-0", "e-"))
                elif v < 0.01:
                    out.append(f"{v:.3f}")
                else:
                    out.append(f"{v:.3f}")
            self.align = "c"
            return out

        vals = [v for v in self.values if v is not None]
        if sig:
            prec = max(sig_round(v, sig)[1] for v in vals) if vals else 0
        else:
            prec = self.prec
        self.prec = prec
        intdigits = max((len(str(abs(int(v)))) for v in vals), default=1)
        for v, raw in zip(self.values, self.raw):
            if v is None:
                out.append("---" if not raw else "{" + latex_escape(raw) + "}")
            else:
                out.append(f"{v:.{prec}f}")
        self.align = f"S[table-format={intdigits}.{prec}]" if prec else f"S[table-format={intdigits}.0]"
        return out

    def header_latex(self):
        h = latex_escape(self.head)
        if self.unit:
            u = {"%": r"\%"}.get(self.unit, self.unit)
            h = f"{h} ({u})"
        return h


def build(headers, rows, args):
    cols = [Column(h, [r[i] for r in rows]) for i, h in enumerate(headers)]
    log = []

    if not args.keep_constant:
        keep = []
        for c in cols:
            if c.constant:
                log.append(f"colonne {c.head!r} retiree : constante a {c.raw[0]!r} "
                           f"(a enoncer une fois dans la legende, pas {len(c.raw)} fois dans le tableau)")
            else:
                keep.append(c)
        cols = keep or cols

    body = [c.format(sig=args.sig, pmin=args.pmin) for c in cols]
    for c in cols:
        if c.unit:
            log.append(f"colonne {c.head!r} : unite {c.unit!r} remontee dans l'en-tete")
        if c.kind == "num":
            obs = getattr(c, "decs_observed", [])
            log.append(f"colonne {c.head!r} : {c.prec} decimale(s) partout, alignement decimal ({c.align})")
            if obs and max(obs) - min(obs) >= 2:
                log.append(f"  ATTENTION {c.head!r} : le fichier melange {min(obs)} a {max(obs)} decimales. "
                           f"{c.prec} est un compromis, PAS une mesure : fixer la precision reelle de "
                           "la mesure la moins precise, au besoin avec --sig")
        if c.kind == "pvalue":
            log.append(f"colonne {c.head!r} : p-values bornees a {args.pmin or 1e-3:g}")

    grid = [[c.header_latex() for c in cols]] + [list(t) for t in zip(*body)]
    aligns = [c.align for c in cols]

    if args.transpose:
        # l'analyse par colonne (type, unite, precision) a deja eu lieu : on
        # transpose le tableau FORMATE. Les colonnes du resultat melangent alors
        # les types, donc plus aucune colonne S : l'alignement decimal ne survit
        # pas a une transposition, c'est le prix a payer et il doit etre dit.
        grid = [list(r) for r in zip(*grid)]
        grid = [[re.sub(r"^\{(.*)\}$", r"\1", cell) for cell in row] for row in grid]
        aligns = ["l"] + ["r"] * (len(grid[0]) - 1)
        log.append("tableau transpose apres formatage : les colonnes melangent desormais "
                   "les types, l'alignement decimal (siunitx) ne s'applique plus")

    width = sum(max(len(re.sub(r"\\[a-zA-Z]+|[{}$]", "", cell)) for cell in col)
                for col in zip(*grid)) + 2 * (len(grid[0]) - 1)
    target = TARGETS[args.journal]

    verdict = []
    if width <= target:
        anchor = "table"
        verdict.append(f"largeur ~{width} car. pour une cible de {target} : tient dans la colonne de texte")
    elif width <= target * 1.6:
        anchor = "table*" if args.journal in ("twocol", "elsevier") else "table"
        verdict.append(f"largeur ~{width} car. > {target} : passer en pleine largeur ({anchor}), "
                       "ou retirer une colonne")
    else:
        anchor = "sidewaystable"
        verdict.append(f"largeur ~{width} car., soit plus de 1,6 fois la cible : rotation "
                       "(sidewaystable) ou, mieux, tableau a repenser (transposer, scinder, "
                       "ou verser le detail en supplementaire)")
    if len(grid) - 1 > 25:
        verdict.append(f"{len(grid)-1} lignes : au-dela d'une vingtaine, le lecteur consulte au lieu "
                       "de comparer ; longtable en supplementaire, et dans le corps la seule "
                       "statistique qui porte l'argument")

    colspec = " ".join(aligns)
    lines = []
    env = args.env or anchor
    lines.append(f"\\begin{{{env}}}[{args.placement}]")
    lines.append("  \\centering")
    if args.note:
        lines.append("  \\begin{threeparttable}")
    cap = args.caption or "TODO : ce qui est compte, sur quel effectif, dans quelle unite, quel test."
    lines.append(f"  \\caption{{{cap}}}")
    if args.label:
        lines.append(f"  \\label{{{args.label}}}")
    if args.tabularray:
        lines.append(f"  \\begin{{tblr}}{{colspec={{{colspec}}}, row{{1}}={{font=\\bfseries}},")
        lines.append("    hline{1,2,Z}={0.8pt}}")
    else:
        lines.append(f"  \\begin{{tabular}}{{{colspec}}}")
        lines.append("    \\toprule")
    head = " & ".join("{" + h + "}" if a.startswith("S") and not h.startswith("{") else h
                      for h, a in zip(grid[0], aligns))
    lines.append("    " + head + r" \\")
    if not args.tabularray:
        lines.append("    \\midrule")
    for i, row in enumerate(grid[1:]):
        lines.append("    " + " & ".join(row) + r" \\")
        if args.group and (i + 1) % args.group == 0 and i + 1 < len(grid) - 1:
            lines.append("    \\addlinespace")
    if not args.tabularray:
        lines.append("    \\bottomrule")
        lines.append("  \\end{tabular}")
    else:
        lines.append("  \\end{tblr}")
    if args.note:
        lines.append("  \\begin{tablenotes}[flushleft]\\footnotesize")
        for n in args.note:
            lines.append(f"    \\item {n}")
        lines.append("  \\end{tablenotes}")
        lines.append("  \\end{threeparttable}")
    lines.append(f"\\end{{{env}}}")
    return "\n".join(lines), log, verdict, cols


PREAMBLE = r"""\documentclass[10pt]{article}
\usepackage[T1]{fontenc}
\usepackage[margin=20mm%s]{geometry}
\usepackage{booktabs,siunitx,threeparttable,rotating,longtable,multirow%s}
\sisetup{detect-all, group-digits=integer, group-minimum-digits=5}
\pagestyle{empty}
\begin{document}
"""


def preview(tex, outdir, tabularray=False, landscape=False):
    """Compile un apercu autonome. Les flottants sont ancres sur place (float [H])
    et un `table*` est ramene a `table` : l'apercu montre le tableau a sa taille
    naturelle, ce qui suffit pour juger alignement, lisibilite et debordement,
    mais il ne reproduit pas la mise en page a deux colonnes du manuscrit."""
    os.makedirs(outdir, exist_ok=True)
    body = tex.replace("{table*}", "{table}").replace("{sidewaystable}", "{table}")
    body = re.sub(r"\\begin\{(table|longtable)\}\[[^\]]*\]", r"\\begin{\1}[H]", body)
    doc = PREAMBLE % (",landscape" if landscape else "", ",tabularray" if tabularray else "") \
        + body + "\n\\end{document}\n"
    doc = doc.replace("\\usepackage{booktabs", "\\usepackage{float}\n\\usepackage{booktabs")
    with tempfile.TemporaryDirectory() as td:
        tf = os.path.join(td, "preview.tex")
        open(tf, "w", encoding="utf-8").write(doc)
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tf],
                           cwd=td, capture_output=True, text=True)
        pdf = os.path.join(td, "preview.pdf")
        if not os.path.exists(pdf):
            log = r.stdout[-2500:]
            return None, log
        dst_pdf = os.path.join(outdir, "table_preview.pdf")
        # rogner les marges : un apercu pleine page est illisible en relecture
        cropped = os.path.join(td, "crop.pdf")
        if subprocess.run(["pdfcrop", "--margins", "12", pdf, cropped],
                          capture_output=True).returncode == 0 and os.path.exists(cropped):
            pdf = cropped
        subprocess.run(["cp", pdf, dst_pdf], check=True)
        subprocess.run(["pdftoppm", "-r", "200", "-png", "-singlefile", dst_pdf,
                        os.path.join(outdir, "table_preview")], check=False)
        overfull = [l for l in r.stdout.splitlines() if "Overfull" in l]
        return dst_pdf, "\n".join(overfull) if overfull else ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--caption")
    ap.add_argument("--label")
    ap.add_argument("--note", action="append", help="note de tableau (repetable) -> threeparttable")
    ap.add_argument("--journal", choices=sorted(TARGETS), default="onecol")
    ap.add_argument("--sig", type=int, help="arrondi a N chiffres significatifs")
    ap.add_argument("--pmin", type=float, help="borne d'affichage des p-values (defaut 1e-3)")
    ap.add_argument("--group", type=int, help="\\addlinespace toutes les N lignes")
    ap.add_argument("--transpose", action="store_true")
    ap.add_argument("--keep-constant", action="store_true")
    ap.add_argument("--tabularray", action="store_true")
    ap.add_argument("--env", help="forcer l'environnement (table, table*, sidewaystable)")
    ap.add_argument("--placement", default="htbp")
    ap.add_argument("--out", help="ecrire le .tex ici")
    ap.add_argument("--preview", metavar="DIR", nargs="?", const=".", help="compiler un apercu PDF + PNG")
    args = ap.parse_args()

    headers, rows = read_table(args.csv)
    tex, log, verdict, cols = build(headers, rows, args)

    if args.out:
        open(args.out, "w", encoding="utf-8").write(tex + "\n")
        print(f"# ecrit : {args.out}", file=sys.stderr)
    else:
        print(tex)

    print("\n% --- decisions prises -------------------------------------------", file=sys.stderr)
    for l in log:
        print("%   " + l, file=sys.stderr)
    print("% --- preambule requis -------------------------------------------", file=sys.stderr)
    pkgs = "booktabs" + (",siunitx" if "S[table-format" in tex else "") \
        + (",threeparttable" if args.note else "") + (",rotating" if "sideways" in tex else "") \
        + (",tabularray" if args.tabularray else "")
    print(f"%   \\usepackage{{{pkgs}}}", file=sys.stderr)
    if "siunitx" in pkgs:
        print("%   \\sisetup{detect-all, group-digits=integer, group-minimum-digits=5}", file=sys.stderr)
    print("% --- ancrage ----------------------------------------------------", file=sys.stderr)
    for v in verdict:
        print("%   " + v, file=sys.stderr)

    if args.preview:
        pdf, warn = preview(tex, args.preview, args.tabularray,
                            landscape="sideways" in tex)
        if pdf:
            print(f"% apercu : {pdf} et {pdf[:-4]}.png", file=sys.stderr)
            if warn:
                print("% ATTENTION, debordement signale par TeX :\n" + warn, file=sys.stderr)
        else:
            print("% la compilation de l'apercu a echoue :\n" + (warn or ""), file=sys.stderr)


if __name__ == "__main__":
    main()
