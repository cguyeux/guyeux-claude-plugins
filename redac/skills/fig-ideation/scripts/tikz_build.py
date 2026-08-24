#!/usr/bin/env python3
"""Compiler une figure TikZ standalone, la rasteriser, et decouper ses zones denses.

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

Usage :
    python3 tikz_build.py figures/fig1.tex [--dpi 220] [--crops] [--outdir DIR]
    python3 tikz_build.py figures/fig1.tex --check-only

Sortie : chemins des PNG produits, un par ligne, a relire avec l'outil Read.
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

    pngs = rasterize(outdir / (tex.stem + ".pdf"), args.dpi, outdir)
    for p in pngs:
        print(p)
    if args.crops:
        for p in pngs:
            for c in make_crops(p, outdir):
                print(c)
    if pngs:
        print("\nRelire chaque PNG avec l'outil Read AVANT de conclure. Une correction",
              file=sys.stderr)
        print("de figure n'est acquise qu'apres re-inspection : chaque deplacement",
              file=sys.stderr)
        print("d'element libere une zone et en occupe une autre.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
