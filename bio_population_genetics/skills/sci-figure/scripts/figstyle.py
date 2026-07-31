#!/usr/bin/env python3
"""Presets de revue partagés entre figures de données et cartes géographiques.

La table de presets appartient au skill `geo-map` : elle est définie sous le nom
`JOURNAL_PRESETS` dans `../../geo-map/scripts/geo_map.py`. Ce module la relit
directement depuis ce fichier (analyse syntaxique, sans importer geopandas ni le
reste de geo_map), de sorte qu'une figure de données et une carte du même article
partagent exactement la même largeur, la même police et le même dpi.

La copie `_VENDORED_PRESETS` n'est qu'un filet de sécurité si geo-map est absent
(skill utilisé hors du plugin bio_population_genetics). `--check-sync` compare les
deux et signale toute dérive.

Différence assumée avec geo-map : le champ `format` de chaque preset décrit le
format exigé par la revue au dépôt final, mais `save()` écrit toujours un PDF
vectoriel. Le raster n'est produit que sur demande explicite (`raster=True`).
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

MM_PER_INCH = 25.4

# Recopie de geo_map.py::JOURNAL_PRESETS, utilisée uniquement en repli.
_VENDORED_PRESETS = {
    "generic": {
        "width_mm": 174, "height_mm": 110, "dpi": 300, "format": "png",
        "title_size": 13, "subtitle_size": 10, "note_size": 7, "label_size": 8,
        "font_family": "DejaVu Sans",
    },
    "nature_single": {
        "width_mm": 89, "height_mm": 70, "dpi": 600, "format": "pdf",
        "title_size": 9, "subtitle_size": 8, "note_size": 6, "label_size": 7,
        "font_family": "Arial",
    },
    "nature_double": {
        "width_mm": 183, "height_mm": 110, "dpi": 600, "format": "pdf",
        "title_size": 10, "subtitle_size": 9, "note_size": 7, "label_size": 8,
        "font_family": "Arial",
    },
    "science": {
        "width_mm": 120, "height_mm": 80, "dpi": 600, "format": "pdf",
        "title_size": 10, "subtitle_size": 9, "note_size": 7, "label_size": 8,
        "font_family": "Helvetica",
    },
    "plos": {
        "width_mm": 174, "height_mm": 110, "dpi": 300, "format": "tiff",
        "title_size": 11, "subtitle_size": 10, "note_size": 8, "label_size": 9,
        "font_family": "Arial",
    },
    "cell": {
        "width_mm": 174, "height_mm": 110, "dpi": 300, "format": "pdf",
        "title_size": 10, "subtitle_size": 9, "note_size": 7, "label_size": 8,
        "font_family": "Helvetica",
    },
    "poster": {
        "width_mm": 400, "height_mm": 280, "dpi": 300, "format": "png",
        "title_size": 24, "subtitle_size": 18, "note_size": 12, "label_size": 14,
        "font_family": "DejaVu Sans",
    },
    "slide": {
        "width_mm": 330, "height_mm": 186, "dpi": 200, "format": "png",
        "title_size": 22, "subtitle_size": 16, "note_size": 10, "label_size": 14,
        "font_family": "DejaVu Sans",
    },
}

# Palettes sûres pour deutéranopie et protanopie (8 % des hommes).
# Le couple bleu/orange reste discriminable là où rouge/vert se confond.
PALETTE_CATEGORICAL = [
    "#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3", "#937860",
]
PALETTE_SEQUENTIAL = "YlOrRd"
PALETTE_DIVERGING = "RdBu_r"


def _geo_map_source() -> Path:
    """Chemin de geo_map.py, en résolvant les symlinks de plugin."""
    return Path(__file__).resolve().parent.parent.parent / "geo-map" / "scripts" / "geo_map.py"


def _load_presets_from_geo_map(path: Path | None = None) -> dict | None:
    """Relit JOURNAL_PRESETS dans geo_map.py sans exécuter le module.

    geo_map.py importe geopandas et matplotlib au chargement ; on veut les presets
    sans payer ces dépendances ni le coût d'un module de 2500 lignes.
    """
    path = path or _geo_map_source()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "JOURNAL_PRESETS":
                try:
                    return ast.literal_eval(node.value)
                except ValueError:
                    return None
    return None


_from_geo_map = _load_presets_from_geo_map()
PRESETS = _from_geo_map if _from_geo_map is not None else dict(_VENDORED_PRESETS)
PRESETS_SOURCE = "geo-map" if _from_geo_map is not None else "vendored"


def get_preset(name: str) -> dict:
    try:
        return dict(PRESETS[name])
    except KeyError:
        raise KeyError(
            f"preset inconnu : {name!r}. Disponibles : {', '.join(sorted(PRESETS))}"
        ) from None


def size_inches(preset: str = "generic", height_mm: float | None = None,
                width_mm: float | None = None) -> tuple[float, float]:
    """Taille en pouces. La largeur vient du preset et ne doit pas être forcée
    sans raison : c'est elle qui garantit qu'aucun redimensionnement n'aura lieu
    à la mise en page, donc que les corps de texte restent à la taille voulue."""
    p = get_preset(preset)
    w = width_mm if width_mm is not None else p["width_mm"]
    h = height_mm if height_mm is not None else p["height_mm"]
    return (w / MM_PER_INCH, h / MM_PER_INCH)


def apply_style(preset: str = "generic", usetex: bool = False, pgf: bool = False) -> dict:
    """Applique les rcParams du preset. À appeler avant toute création de figure."""
    import matplotlib
    # matplotlib réexporte bien `cycler`, mais l'importer depuis son paquet
    # d'origine lève l'ambiguïté (matplotlib dépend de `cycler`, il est donc
    # toujours présent).
    from cycler import cycler

    if pgf:
        matplotlib.use("pgf")
    import matplotlib.pyplot as plt  # noqa: F401  (force l'init du backend)

    p = get_preset(preset)
    params = {
        # fonttype 42 = TrueType : le texte reste sélectionnable et éditable dans
        # Illustrator ou Inkscape. Le défaut (Type 3) casse l'édition et plusieurs
        # revues le refusent.
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "font.family": "sans-serif",
        "font.sans-serif": [p["font_family"], "DejaVu Sans", "Helvetica", "Arial"],
        "font.size": p["label_size"],
        "axes.titlesize": p["subtitle_size"],
        "axes.labelsize": p["label_size"],
        "xtick.labelsize": p["note_size"],
        "ytick.labelsize": p["note_size"],
        "legend.fontsize": p["note_size"],
        "figure.titlesize": p["title_size"],
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linewidth": 0.5,
        "axes.axisbelow": True,
        "axes.linewidth": 0.8,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "lines.linewidth": 1.4,
        "figure.dpi": 100,
        "savefig.dpi": p["dpi"],
        # Surtout pas "tight" : il rogne la figure sur son contenu et fait perdre
        # la largeur exacte du preset (183 mm deviennent 182). C'est
        # constrained_layout qui ajuste le contenu à l'intérieur du format imposé.
        "savefig.bbox": "standard",
        "savefig.pad_inches": 0.0,
        "axes.prop_cycle": cycler(color=PALETTE_CATEGORICAL),
    }
    if usetex or pgf:
        params.update({
            "text.usetex": True,
            "font.family": "serif",
            "pgf.texsystem": "pdflatex",
            "pgf.rcfonts": False,
        })
    matplotlib.rcParams.update(params)
    return p


def new_figure(preset: str = "generic", height_mm: float | None = None,
               width_mm: float | None = None, usetex: bool = False):
    """Figure mono-panneau déjà au format de la revue."""
    p = apply_style(preset, usetex=usetex)
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=size_inches(preset, height_mm, width_mm),
                           constrained_layout=True)
    return fig, ax


def panel_grid(preset: str = "generic", nrows: int = 1, ncols: int = 2,
               height_mm: float | None = None, width_mm: float | None = None,
               usetex: bool = False, **gridspec_kw):
    """Figure multi-panneaux à largeur de revue conservée.

    Sans `height_mm`, la hauteur suit le nombre de lignes pour garder des
    panneaux de proportion à peu près constante.
    """
    p = apply_style(preset, usetex=usetex)
    import matplotlib.pyplot as plt

    if height_mm is None:
        height_mm = p["height_mm"] * (1 + 0.75 * (nrows - 1))
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=size_inches(preset, height_mm, width_mm),
                             constrained_layout=True, gridspec_kw=gridspec_kw or None)
    return fig, axes


def panel_labels(axes, labels: str = "abcdefghijklmnop", x: float = -0.02,
                 y: float = 1.04, weight: str = "bold", size=None) -> None:
    """Étiquettes a, b, c... en haut à gauche de chaque panneau, convention Nature.

    Sans `size`, reprend `figure.titlesize`, que `apply_style()` a déjà réglé sur
    le `title_size` du preset : les rcParams portent l'état, pas un attribut
    greffé sur la figure.
    """
    import matplotlib

    if hasattr(axes, "flat"):
        flat = list(axes.flat)
    elif isinstance(axes, (list, tuple)):
        flat = list(axes)
    else:
        flat = [axes]
    if size is None:
        size = matplotlib.rcParams["figure.titlesize"]
    for ax, letter in zip(flat, labels):
        ax.text(x, y, letter, transform=ax.transAxes, fontsize=size,
                fontweight=weight, va="bottom", ha="right")


def save(fig, stem, preset: str = "generic", raster: bool = False,
         pgf: bool = False) -> list[Path]:
    """Écrit toujours un PDF vectoriel ; ajoute un raster seulement si demandé.

    `raster=True` produit en plus le format exigé par la revue (`format` du
    preset) à son dpi, pour les dépôts qui refusent le vectoriel (PLOS en TIFF).
    Le PNG à 150 dpi de l'ancien `create-viz` était sous les standards de
    soumission ; il n'a pas de successeur ici.
    """
    stem = Path(stem)
    if stem.suffix:
        stem = stem.with_suffix("")
    stem.parent.mkdir(parents=True, exist_ok=True)
    p = get_preset(preset)
    written = [stem.with_suffix(".pdf")]
    fig.savefig(written[0], format="pdf")
    if raster:
        fmt = p["format"] if p["format"] != "pdf" else "png"
        out = stem.with_suffix("." + fmt)
        fig.savefig(out, format=fmt, dpi=p["dpi"])
        written.append(out)
    if pgf:
        out = stem.with_suffix(".pgf")
        fig.savefig(out, format="pgf")
        written.append(out)
    return written


def _cmd_list() -> int:
    print(f"Presets (source : {PRESETS_SOURCE})\n")
    head = f"{'nom':<15} {'largeur':>8} {'hauteur':>8} {'dpi':>5}  {'dépôt':<5} police"
    print(head)
    print("-" * len(head))
    for name, p in PRESETS.items():
        print(f"{name:<15} {p['width_mm']:>6} mm {p['height_mm']:>6} mm "
              f"{p['dpi']:>5}  {p['format']:<5} {p['font_family']}")
    print("\nsave() écrit un PDF vectoriel quel que soit le preset ; la colonne "
          "« dépôt » n'est produite qu'avec --raster.")
    return 0


def _cmd_check_sync() -> int:
    live = _load_presets_from_geo_map()
    src = _geo_map_source()
    if live is None:
        print(f"geo-map introuvable ou illisible ({src})")
        print("Repli sur la copie locale : les presets peuvent avoir dérivé.")
        return 2
    if live == _VENDORED_PRESETS:
        print(f"Synchronisé avec {src}")
        return 0
    print(f"DÉRIVE entre la copie locale et {src}")
    for name in sorted(set(live) | set(_VENDORED_PRESETS)):
        a, b = _VENDORED_PRESETS.get(name), live.get(name)
        if a != b:
            print(f"  {name}: local={a} geo-map={b}")
    print("\nCorriger _VENDORED_PRESETS dans figstyle.py (geo-map fait autorité).")
    return 1


def _cmd_demo(out: str, preset: str) -> int:
    import numpy as np

    fig, axes = panel_grid(preset, nrows=1, ncols=2)
    x = np.linspace(0, 10, 200)
    for i, k in enumerate((1.0, 1.6, 2.4)):
        axes[0].plot(x, np.sin(k * x) / k, label=f"k = {k}")
    axes[0].set_xlabel("Position (cM)")
    axes[0].set_ylabel("Amplitude")
    axes[0].legend(frameon=False)
    rng = np.random.default_rng(0)
    axes[1].hist(rng.normal(size=600), bins=28, color=PALETTE_CATEGORICAL[0],
                 edgecolor="white", linewidth=0.4)
    axes[1].set_xlabel("Écart normalisé")
    axes[1].set_ylabel("Effectif")
    panel_labels(axes)
    written = save(fig, out, preset)
    print("Écrit :", ", ".join(str(w) for w in written))
    return 0


def main(argv=None) -> int:
    # __doc__ vaut None sous `python3 -OO`, qui retire les docstrings.
    resume = (__doc__ or "Presets de revue pour figures d'article.").splitlines()[0]
    ap = argparse.ArgumentParser(description=resume)
    ap.add_argument("--list", action="store_true", help="lister les presets")
    ap.add_argument("--check-sync", action="store_true",
                    help="comparer la copie locale à geo-map")
    ap.add_argument("--demo", metavar="STEM", help="produire une figure de test")
    ap.add_argument("--preset", default="generic")
    args = ap.parse_args(argv)
    if args.check_sync:
        return _cmd_check_sync()
    if args.demo:
        return _cmd_demo(args.demo, args.preset)
    return _cmd_list()


if __name__ == "__main__":
    sys.exit(main())
