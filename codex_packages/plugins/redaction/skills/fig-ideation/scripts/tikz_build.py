#!/usr/bin/env python3
r"""Compiler une figure TikZ standalone, la rasteriser, et decouper ses zones denses.

La boucle qu'impose ce script est la seule qui attrape les defauts de figure :

    compiler -> rasteriser -> REGARDER -> corriger -> recompiler -> REGARDER ENCORE

Trois lecons du depot y sont cablees :

* `-halt-on-error` est OBLIGATOIRE. En `nonstopmode` seul, pdflatex signale l'erreur
  mais CONTINUE et produit un PDF defectueux avec un code de retour 0. Un
  `\\def\\xL8{...}` casse en silence et la branche est tracee n'importe ou.
* Le log se relit meme quand un PDF est produit : `doesn't match`, `Overfull`,
  `Missing`, `Undefined control sequence` ne stoppent pas toujours la compilation.
* La vue d'ensemble ne suffit pas. Les zones denses (legende, coins, centre) se
  recadrent et se relisent une par une : sur un cas reel, trois defauts sur six
  n'etaient identifiables que par recadrage.

Une quatrieme lecon, ajoutee apres coup (`variant_nucs`, fig1_mechanism_verdict, 2026-09-03) :
le PDF standalone rasterise a taille NATIVE (le seul que ce script produisait jusque-la) ne dit
RIEN de la lisibilite reelle. Une figure large-format (deux panneaux cote a cote) inseree ensuite
avec `width=\textwidth` dans un manuscrit etroit (a4, marges 2.5cm) est REDUITE d'autant, et du
texte en `\tiny`/`\scriptsize` (5-7pt a la source) tombe alors a 3-4pt effectifs -- illisible --
sans que rien dans la boucle native ne l'ait jamais signale : le rendu isole a taille native est
toujours net, quel que soit le DPI de rasterisation, parce que le DPI fixe la resolution des
pixels, pas la taille angulaire finale une fois la figure retrecie dans la page. Le defaut a
survecu a plusieurs tours de la boucle "compiler->regarder->corriger" precisement parce que
personne n'y regardait a l'echelle d'insertion reelle. `--embed-width-pt` ferme ce trou : il
simule l'insertion (page a la largeur cible, `\includegraphics[width=<cible>]{...}`), rasterise
CE rendu, et alerte si un des styles de police utilises tombe sous un seuil de lisibilite.

Usage :
    python3 tikz_build.py figures/fig1.tex [--dpi 220] [--crops] [--outdir DIR]
    python3 tikz_build.py figures/fig1.tex --check-only
    # simuler l'insertion reelle dans le manuscrit (largeur en pt de \\textwidth ou
    # de l'option width= utilisee par \\includegraphics ; voir la recette dans SKILL.md
    # pour obtenir ce nombre pour un documentclass/geometry donnes) :
    python3 tikz_build.py figures/fig1.tex --embed-width-pt 455.24 --crops

Sortie : chemins des PNG produits, un par ligne, a relire avec l'outil Read -- y compris,
des que `--embed-width-pt` est fourni, le PNG `*_embedpreview*` qui est le seul representatif
de la taille effective dans le manuscrit final.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

SUSPECT = re.compile(
    r"^! |doesn't match|Undefined control sequence|Missing \w+ inserted|"
    r"Overfull \\hbox \((\d{3,})|Underfull|Font shape .* undefined|"
    r"LaTeX Warning: Reference .* undefined", re.M)

# Tables de tailles standard (points) des classes LaTeX de base 10/11/12pt, indexees par
# nom de commande. Hypothese : les figures standalone de ce depot ne changent quasi jamais
# la taille de base (`\\documentclass[border=4pt]{standalone}` sans option Npt => 10pt).
FONT_SIZE_PT: dict[int, dict[str, float]] = {
    10: {"tiny": 5, "scriptsize": 7, "footnotesize": 8, "small": 9, "normalsize": 10,
         "large": 12, "Large": 14.4, "LARGE": 17.28, "huge": 20.74, "Huge": 24.88},
    11: {"tiny": 6, "scriptsize": 8, "footnotesize": 9, "small": 10, "normalsize": 10.95,
         "large": 12, "Large": 14.4, "LARGE": 17.28, "huge": 20.74, "Huge": 24.88},
    12: {"tiny": 6, "scriptsize": 8, "footnotesize": 10, "small": 10.95, "normalsize": 12,
         "large": 14.4, "Large": 17.28, "LARGE": 20.74, "huge": 24.88, "Huge": 24.88},
}


def run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def compile_tex(tex: Path, outdir: Path, engine: str) -> tuple[bool, list[str]]:
    """Compiler en -halt-on-error. Rend (succes, lignes suspectes du log)."""
    outdir.mkdir(parents=True, exist_ok=True)
    code, _ = run([engine, "-halt-on-error", "-interaction=nonstopmode",
                   f"-output-directory={outdir}", tex.name], cwd=tex.parent)
    log = outdir / (tex.stem + ".log")
    text = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
    suspects = [ln.strip() for ln in text.splitlines() if SUSPECT.search(ln)]
    pdf = outdir / (tex.stem + ".pdf")
    return (code == 0 and pdf.is_file()), suspects


def rasterize(pdf: Path, dpi: int, outdir: Path) -> list[Path]:
    stem = outdir / pdf.stem
    code, out = run(["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(stem)])
    if code != 0:
        print(f"echec pdftoppm : {out.strip()[:200]}", file=sys.stderr)
        return []
    return sorted(outdir.glob(f"{pdf.stem}-*.png"))


def pdf_page_size_pt(pdf: Path) -> tuple[float, float] | None:
    code, out = run(["pdfinfo", str(pdf)])
    if code != 0:
        return None
    m = re.search(r"Page size:\s*([\d.]+) x ([\d.]+) pts", out)
    return (float(m.group(1)), float(m.group(2))) if m else None


def detect_base_size(tex: Path) -> int:
    """Taille de classe (10/11/12pt) de la figure elle-meme -- defaut standalone : 10pt."""
    text = tex.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"\\documentclass\[([^\]]*)\]", text)
    for tok in (m.group(1).split(",") if m else []):
        tok = tok.strip()
        if tok in ("10pt", "11pt", "12pt"):
            return int(tok[:-2])
    return 10


def detect_font_sizes_used(tex: Path) -> set[str]:
    text = tex.read_text(encoding="utf-8", errors="replace")
    names = set(FONT_SIZE_PT[10])
    pattern = re.compile(r"\\(" + "|".join(sorted(names, key=len, reverse=True)) + r")\b")
    return {m.group(1) for m in pattern.finditer(text)}


def embed_preview(pdf: Path, embed_width_pt: float, outdir: Path, dpi: int) -> Path | None:
    """Simuler l'insertion reelle (`\\includegraphics[width=embed_width_pt]`) et rasteriser
    CE rendu -- le seul representatif de la lisibilite finale dans le manuscrit."""
    size = pdf_page_size_pt(pdf)
    if size is None:
        return None
    native_w, native_h = size
    embed_h = embed_width_pt * (native_h / native_w)
    wrapper = outdir / (pdf.stem + "_embedpreview.tex")
    wrapper.write_text(
        "\\documentclass{article}\n"
        f"\\usepackage[paperwidth={embed_width_pt}pt,paperheight={embed_h + 4}pt,"
        "margin=0pt]{geometry}\n"
        "\\usepackage{graphicx}\n"
        "\\pagestyle{empty}\n"
        "\\begin{document}\\noindent\n"
        f"\\includegraphics[width={embed_width_pt}pt]{{{pdf.resolve()}}}\n"
        "\\end{document}\n",
        encoding="utf-8")
    ok, _ = compile_tex(wrapper, outdir, "pdflatex")
    if not ok:
        print(f"echec de la simulation d'insertion : {wrapper.with_suffix('.log')}",
              file=sys.stderr)
        return None
    pngs = rasterize(outdir / wrapper.with_suffix(".pdf").name, dpi, outdir)
    return pngs[0] if pngs else None


def check_embed_legibility(tex: Path, pdf: Path, embed_width_pt: float,
                            min_effective_pt: float) -> list[str]:
    """Rendre (nom de style, pt source, pt effectif apres reduction) pour chaque taille de
    police utilisee dans la figure, et la liste des avertissements sous le seuil."""
    size = pdf_page_size_pt(pdf)
    if size is None:
        return ["impossible de lire la taille native du PDF (pdfinfo a echoue)"]
    native_w, _ = size
    scale = embed_width_pt / native_w
    base = detect_base_size(tex)
    table = FONT_SIZE_PT[base]
    warnings = []
    print(f"echelle d'insertion : {native_w:.1f}pt (natif) -> {embed_width_pt:.1f}pt "
          f"(manuscrit) = facteur {scale:.3f}", file=sys.stderr)
    for name in sorted(detect_font_sizes_used(tex), key=lambda n: table[n]):
        src_pt = table[name]
        eff_pt = src_pt * scale
        flag = " *** SOUS LE SEUIL ***" if eff_pt < min_effective_pt else ""
        print(f"  \\{name:<12s} {src_pt:5.2f}pt source -> {eff_pt:5.2f}pt effectif dans le "
              f"manuscrit{flag}", file=sys.stderr)
        if eff_pt < min_effective_pt:
            warnings.append(f"\\{name} : {eff_pt:.2f}pt effectif < seuil {min_effective_pt}pt")
    return warnings


def make_crops(png: Path, outdir: Path) -> list[Path]:
    """Cinq recadrages : les quatre coins denses et le centre.

    On ne recadre pas pour faire joli : on recadre parce qu'une legende posee sur
    des barres, un label efface par un cadre blanc ou deux annotations qui se
    touchent sont invisibles a l'echelle de la page.
    """
    magick = shutil.which("magick") or shutil.which("convert")
    if magick is None:
        print("ni magick ni convert : recadrages ignores", file=sys.stderr)
        return []
    _, out = run([shutil.which("identify") or magick, "-format", "%w %h", str(png)])
    try:
        w, h = (int(x) for x in out.split()[:2])
    except (ValueError, IndexError):
        return []
    cw, ch = int(w * 0.55), int(h * 0.55)
    zones = {
        "topleft": (0, 0), "topright": (w - cw, 0),
        "bottomleft": (0, h - ch), "bottomright": (w - cw, h - ch),
        "center": ((w - cw) // 2, (h - ch) // 2),
    }
    made = []
    for name, (x, y) in zones.items():
        dst = outdir / f"{png.stem}_{name}.png"
        rc, _ = run([magick, str(png), "-crop", f"{cw}x{ch}+{x}+{y}", "+repage", str(dst)])
        if rc == 0 and dst.is_file():
            made.append(dst)
    return made


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tex", type=Path, help="figure TikZ standalone")
    ap.add_argument("--dpi", type=int, default=220,
                    help="resolution de relecture (defaut 220 ; le livrable reste vectoriel)")
    ap.add_argument("--crops", action="store_true", help="produire les cinq recadrages")
    ap.add_argument("--outdir", type=Path, default=None, help="repertoire de build")
    ap.add_argument("--engine", default="pdflatex", help="pdflatex, lualatex, xelatex")
    ap.add_argument("--check-only", action="store_true", help="compiler sans rasteriser")
    ap.add_argument("--embed-width-pt", type=float, default=None,
                    help="largeur reelle (en pt) a laquelle la figure sera inseree dans le "
                         "manuscrit (typiquement \\the\\textwidth du documentclass/geometry "
                         "cible -- voir la recette dans SKILL.md). Sans cette option, la "
                         "boucle ne verifie QUE le rendu natif et peut valider une figure "
                         "illisible une fois retrecie a l'insertion.")
    ap.add_argument("--min-effective-pt", type=float, default=6.0,
                    help="seuil de lisibilite en pt effectifs apres reduction a "
                         "--embed-width-pt (defaut 6.0pt)")
    args = ap.parse_args()

    tex = args.tex.resolve()
    if not tex.is_file():
        print(f"introuvable : {tex}", file=sys.stderr)
        return 2
    outdir = (args.outdir or tex.parent / "_build").resolve()

    ok, suspects = compile_tex(tex, outdir, args.engine)
    if suspects:
        print("LOG SUSPECT (un PDF produit ne prouve pas un build propre) :",
              file=sys.stderr)
        for s in suspects[:15]:
            print(f"  {s[:160]}", file=sys.stderr)
    if not ok:
        print(f"echec de compilation : {outdir / (tex.stem + '.log')}", file=sys.stderr)
        return 1
    if args.check_only:
        print(outdir / (tex.stem + ".pdf"))
        return 0

    fig_pdf = outdir / (tex.stem + ".pdf")
    pngs = rasterize(fig_pdf, args.dpi, outdir)
    for p in pngs:
        print(p)
    if args.crops:
        for p in pngs:
            for c in make_crops(p, outdir):
                print(c)

    legibility_warnings: list[str] = []
    if args.embed_width_pt is not None:
        legibility_warnings = check_embed_legibility(
            tex, fig_pdf, args.embed_width_pt, args.min_effective_pt)
        preview = embed_preview(fig_pdf, args.embed_width_pt, outdir, dpi=300)
        if preview is not None:
            print(preview)
            if args.crops:
                for c in make_crops(preview, outdir):
                    print(c)
        else:
            print("echec de la generation du rendu simule a l'echelle d'insertion",
                  file=sys.stderr)

    if pngs:
        print("\nRelire chaque PNG avec l'outil Read AVANT de conclure. Une correction",
              file=sys.stderr)
        print("de figure n'est acquise qu'apres re-inspection : chaque deplacement",
              file=sys.stderr)
        print("d'element libere une zone et en occupe une autre.", file=sys.stderr)
    if args.embed_width_pt is None:
        print("\nATTENTION : --embed-width-pt non fourni -- ce build ne prouve la lisibilite",
              file=sys.stderr)
        print("qu'a taille NATIVE, jamais a la taille reelle d'insertion dans le manuscrit.",
              file=sys.stderr)
    elif legibility_warnings:
        print("\nLISIBILITE INSUFFISANTE a l'echelle d'insertion :", file=sys.stderr)
        for w in legibility_warnings:
            print(f"  {w}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
