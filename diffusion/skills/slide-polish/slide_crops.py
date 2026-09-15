#!/usr/bin/env python3
"""slide_crops.py -- generer 5 crops obligatoires pour audit propreté §7.5.2.a.

Usage:
  python slide_crops.py <slide.png>                 # 5 crops cote-a-cote
  python slide_crops.py <main.pdf> --page N         # extrait page N puis crops
  python slide_crops.py <main.pdf> --page N --dpi 280

Sorties (meme repertoire que l'input):
  <basename>_top.png      bande superieure (1/8 hauteur)
  <basename>_bottom.png   bande inferieure (1/8 hauteur)
  <basename>_left.png     bande gauche (1/8 largeur)
  <basename>_right.png    bande droite (1/8 largeur)
  <basename>_center.png   carre central (1/2 x 1/2)

A lire chacun avec l'outil Read (capacite multimodale) avant de valider items
A1 (texte hors slide), A5 (footer pousse), C10 (collision nodes) du score §7.5.

Regle bloquante du skill : ces 3 items ne peuvent jamais etre declares NON
sans crops 7.5.2.a effectues au prealable.
"""

import argparse
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERREUR : PIL/Pillow requis. Installer via `pip install Pillow`.", file=sys.stderr)
    sys.exit(1)


def make_crops(png_path: Path) -> dict:
    """Genere les 5 crops obligatoires pour audit propreté §7.5.2.a."""
    im = Image.open(png_path)
    w, h = im.size
    base = png_path.with_suffix("")
    outputs = {
        "top":    (0, 0, w, h // 8),
        "bottom": (0, h * 7 // 8, w, h),
        "left":   (0, 0, w // 8, h),
        "right":  (w * 7 // 8, 0, w, h),
        "center": (w // 4, h // 4, w * 3 // 4, h * 3 // 4),
    }
    paths = {}
    for name, box in outputs.items():
        out = Path(f"{base}_{name}.png")
        im.crop(box).save(out)
        paths[name] = out
    return {"size": (w, h), "crops": paths}


def render_page(pdf_path: Path, page: int, dpi: int) -> Path:
    """Rend la page PDF en PNG haute resolution via pdftoppm."""
    out_prefix = pdf_path.with_suffix("").name + f"_p{page}"
    out_dir = pdf_path.parent
    cmd = [
        "pdftoppm",
        "-f", str(page), "-l", str(page),
        "-r", str(dpi),
        str(pdf_path),
        str(out_dir / out_prefix),
        "-png",
    ]
    subprocess.run(cmd, check=True)
    # pdftoppm genere <prefix>-NN.png (NN = page zero-padded)
    candidates = sorted(out_dir.glob(f"{out_prefix}-*.png"))
    if not candidates:
        print(f"ERREUR : pdftoppm n'a generé aucun PNG pour {pdf_path} page {page}", file=sys.stderr)
        sys.exit(2)
    return candidates[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("input", help="Slide PNG ou main.pdf")
    ap.add_argument("--page", type=int, help="Page PDF a extraire (si input est .pdf)")
    ap.add_argument("--dpi", type=int, default=280, help="Resolution pdftoppm (def: 280)")
    args = ap.parse_args()

    inp = Path(args.input)
    if not inp.exists():
        print(f"ERREUR : {inp} introuvable", file=sys.stderr)
        sys.exit(1)

    if inp.suffix.lower() == ".pdf":
        if args.page is None:
            print("ERREUR : --page requis pour input PDF", file=sys.stderr)
            sys.exit(1)
        png = render_page(inp, args.page, args.dpi)
        print(f"[render] page {args.page} -> {png}")
    else:
        png = inp

    result = make_crops(png)
    print(f"[size  ] {result['size'][0]} x {result['size'][1]} px")
    print(f"[crops ] 5 crops generes :")
    for name, path in result["crops"].items():
        print(f"  {name:8s} -> {path}")
    print()
    print("Lire chaque crop avec l'outil Read (capacite multimodale) et repondre :")
    print("  top    : Le titre tient-il ? Aucun element touchant le bord haut ?")
    print("  bottom : Le footer X/N est-il visible avec >=1 ligne de blanc avant ?")
    print("           Aucun mot ni accolade ne touche le bord bas ?")
    print("  left   : Aucun node/image/texte ne touche le bord gauche ?")
    print("  right  : Aucun node TikZ/etiquette/bloc ne touche ou depasse le bord droit ?")
    print("  center : Les elements centraux sont integres ? Aucun chevauchement node sur node ?")


if __name__ == "__main__":
    main()
