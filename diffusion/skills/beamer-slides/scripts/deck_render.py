#!/usr/bin/env python3
"""Compile un deck Beamer et le rend en PNG, slide par slide.

Sert la boucle d'inspection visuelle : on ne declare jamais une slide finie
sans l'avoir REGARDEE. Le rendu par defaut suffit a juger la composition ;
les recadrages servent a verifier la lisibilite d'une legende ou d'un axe.

    python3 deck_render.py deck.tex                  # tout le deck, 110 dpi
    python3 deck_render.py deck.tex -p 4-7           # seulement ces slides
    python3 deck_render.py deck.tex -p 5 --crops     # + recadrages haute def
    python3 deck_render.py deck.tex --trio 5         # slides 4, 5 et 6

Les fichiers sortent dans <deck>_png/ et les chemins sont affiches, prets a
etre relus par l'outil de lecture d'images.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

DPI_APERCU = 110      # assez pour juger composition, equilibre, encombrement
DPI_CROP = 300        # assez pour juger la lisibilite d'un texte d'axe


def compile_deck(tex: str) -> str:
    d, f = os.path.dirname(os.path.abspath(tex)) or '.', os.path.basename(tex)
    pdf = os.path.join(d, os.path.splitext(f)[0] + '.pdf')
    besoin = (not os.path.exists(pdf)
              or os.path.getmtime(pdf) < os.path.getmtime(tex))
    if besoin:
        for _ in range(2):
            r = subprocess.run(['pdflatex', '-interaction=nonstopmode', f],
                               cwd=d, capture_output=True, text=True)
        if not os.path.exists(pdf):
            erreurs = [l for l in r.stdout.splitlines() if l.startswith('!')][:5]
            sys.exit("compilation impossible :\n  " + "\n  ".join(erreurs))
    return pdf


def pages_de(spec: str, total: int):
    if not spec:
        return list(range(1, total + 1))
    out = []
    for part in spec.split(','):
        if '-' in part:
            a, b = part.split('-')
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return [p for p in out if 1 <= p <= total]


def nb_pages(pdf: str) -> int:
    out = subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout
    m = re.search(r'Pages:\s+(\d+)', out)
    return int(m.group(1)) if m else 0


def rendre(pdf: str, out_dir: str, pages, dpi: int, prefixe='slide'):
    os.makedirs(out_dir, exist_ok=True)
    faits = []
    for p in pages:
        base = os.path.join(out_dir, f'{prefixe}-{p:03d}')
        subprocess.run(['pdftoppm', '-r', str(dpi), '-png', '-f', str(p), '-l', str(p),
                        '-singlefile', pdf, base], capture_output=True)
        if os.path.exists(base + '.png'):
            faits.append(base + '.png')
    return faits


def recadrer(png: str):
    """Quatre recadrages : les quatre endroits ou un defaut se cache.

    Le haut porte le titre, le bas ce qui deborde sous le cadre, et les deux
    moities horizontales servent a lire un axe ou une legende de figure.
    """
    from PIL import Image
    im = Image.open(png)
    w, h = im.size
    zones = {'haut': (0, 0, w, int(h * 0.22)),
             'bas': (0, int(h * 0.78), w, h),
             'gauche': (0, int(h * 0.15), w // 2, int(h * 0.9)),
             'droite': (w // 2, int(h * 0.15), w, int(h * 0.9))}
    out = []
    for nom, box in zones.items():
        c = im.crop(box)
        chemin = png.replace('.png', f'-{nom}.png')
        c.save(chemin)
        out.append(chemin)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('deck')
    ap.add_argument('-p', '--pages', default='', help='ex. 4-7 ou 2,5,9')
    ap.add_argument('--trio', type=int, help='slide n avec ses voisines n-1 et n+1')
    ap.add_argument('--crops', action='store_true', help='recadrages a %d dpi' % DPI_CROP)
    ap.add_argument('--dpi', type=int, default=DPI_APERCU)
    a = ap.parse_args()

    pdf = compile_deck(a.deck)
    total = nb_pages(pdf)
    spec = a.pages
    if a.trio:
        spec = ','.join(str(x) for x in (a.trio - 1, a.trio, a.trio + 1) if 1 <= x <= total)
    pages = pages_de(spec, total)
    out_dir = os.path.splitext(os.path.abspath(a.deck))[0] + '_png'

    faits = rendre(pdf, out_dir, pages, a.dpi)
    print(f"{len(faits)} slide(s) rendue(s) a {a.dpi} dpi dans {out_dir}")
    for f in faits:
        print(" ", f)
    if a.crops:
        for p in pages:
            hd = rendre(pdf, out_dir, [p], DPI_CROP, prefixe='hd')
            for png in hd:
                for c in recadrer(png):
                    print(" ", c)
                os.remove(png)


if __name__ == '__main__':
    main()
