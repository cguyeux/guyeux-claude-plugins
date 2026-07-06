#!/usr/bin/env python3
"""geo_map.py — Publication-quality geographic maps for MTBC studies.

Backend: geopandas + matplotlib (no cartopy required).
Supported map types: choropleth, bubble, pie, points (GPS lat/lon),
arcs (phylogeo flows), multi-panel, layered.
Natural Earth public-domain data, cached locally.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import sys
import urllib.request
import warnings
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

try:
    import geopandas as gpd
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.colors import LogNorm, Normalize, to_rgba
    from matplotlib.lines import Line2D
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    from matplotlib.patheffects import Stroke, Normal, withStroke
    from shapely.geometry import Point, box
except ImportError as e:
    print(
        f"Error: required package missing ({e}). Install with:\n"
        "  pip install geopandas matplotlib shapely",
        file=sys.stderr,
    )
    sys.exit(1)

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

NE_BASE_URL = "https://naciscdn.org/naturalearth/{res}/{cat}/ne_{res}_{name}.zip"
NE_CACHE_DIR = Path(os.environ.get("GEO_MAP_CACHE", Path.home() / ".cache" / "geo_map"))
NE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

COUNTRY_ALIASES = {
    "usa": "United States of America",
    "united states": "United States of America",
    "uk": "United Kingdom",
    "united kingdom": "United Kingdom",
    "dr congo": "Dem. Rep. Congo",
    "democratic republic of the congo": "Dem. Rep. Congo",
    "drc": "Dem. Rep. Congo",
    "ivory coast": "Côte d'Ivoire",
    "cote d'ivoire": "Côte d'Ivoire",
    "south korea": "South Korea",
    "republic of korea": "South Korea",
    "north korea": "North Korea",
    "czech republic": "Czechia",
    "czechia": "Czechia",
    "eswatini": "eSwatini",
    "swaziland": "eSwatini",
    "burma": "Myanmar",
    "myanmar": "Myanmar",
    "timor-leste": "Timor-Leste",
    "east timor": "Timor-Leste",
    "russia": "Russia",
    "russian federation": "Russia",
    "iran": "Iran",
    "south sudan": "S. Sudan",
    "central african republic": "Central African Rep.",
    "bosnia and herzegovina": "Bosnia and Herz.",
    "bosnia": "Bosnia and Herz.",
    "north macedonia": "North Macedonia",
    "dominican republic": "Dominican Rep.",
    "equatorial guinea": "Eq. Guinea",
    "solomon islands": "Solomon Is.",
    "papua new guinea": "Papua New Guinea",
    "guinea-bissau": "Guinea-Bissau",
    "western sahara": "W. Sahara",
    "laos": "Laos",
    "vietnam": "Vietnam",
    "taiwan": "Taiwan",
    "hong kong": "Hong Kong",
    "tanzania": "Tanzania",
    "moldova": "Moldova",
    "macedonia": "North Macedonia",
}

MTBC_PALETTE = {
    "L1": "#F5A623", "L2": "#D0021B", "L3": "#4A90D9",
    "L4": "#E03D31", "L5": "#7B2D8E", "L6": "#9B59B6",
    "L7": "#B8860B", "L8": "#1B9AAA", "L9": "#2D6A4F",
    "L10": "#52B788",
    "M. bovis": "#3D2B1F", "M. caprae": "#6B4226",
    "M. africanum": "#7B2D8E", "M. canettii": "#5D4037",
    "Unknown": "#9E9E9E",
}

# Fallback palette (24 colors) pour groupes absents de MTBC_PALETTE.
# Couleurs distinctes basees sur tab20 + Set3 sans gris ni teinte trop pale.
_AUTO_FALLBACK = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#bcbd22", "#17becf", "#aec7e8",
    "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5", "#c49c94",
    "#f7b6d2", "#dbdb8d", "#9edae5", "#003f5c", "#bc5090",
    "#ffa600", "#58508d", "#ff6361", "#7a5195",
]

def resolve_palette(groups, palette):
    """Map every group to a distinct color.

    Use `palette` (typically MTBC_PALETTE) when the group is in it,
    otherwise cycle through _AUTO_FALLBACK so that legend handles and
    scatter points share the same color and no group ends up grey by
    default.
    Returns dict {group: color}.
    """
    resolved = {}
    fb_i = 0
    used_colors = set(palette.get(g) for g in groups if g in palette)
    for g in groups:
        if g in palette:
            resolved[g] = palette[g]
        else:
            # pick next fallback color not already used
            while fb_i < len(_AUTO_FALLBACK) and _AUTO_FALLBACK[fb_i] in used_colors:
                fb_i += 1
            if fb_i < len(_AUTO_FALLBACK):
                col = _AUTO_FALLBACK[fb_i]
                fb_i += 1
            else:
                # wrap around (>24 groups) — accept reuse rather than gray
                col = _AUTO_FALLBACK[len(resolved) % len(_AUTO_FALLBACK)]
            resolved[g] = col
            used_colors.add(col)
    return resolved

MTBC_PALETTE_CB = {
    "L1": "#E69F00", "L2": "#D55E00", "L3": "#0072B2",
    "L4": "#CC79A7", "L5": "#56B4E9", "L6": "#009E73",
    "L7": "#F0E442", "L8": "#999999", "L9": "#117733",
    "L10": "#88CCEE",
    "M. bovis": "#332288", "M. caprae": "#882255",
    "M. africanum": "#AA4499", "M. canettii": "#44AA99",
    "Unknown": "#BBBBBB",
}

REGIONS = {
    "world":          (-180, -60, 180, 85),
    "africa":         (-25, -38, 55, 38),
    "europe":         (-15, 34, 45, 72),
    "asia":           (25, -15, 155, 55),
    "east_asia":      (70, 15, 150, 55),
    "southeast_asia": (90, -15, 155, 30),
    "south_asia":     (60, 5, 100, 40),
    "middle_east":    (25, 10, 65, 45),
    "americas":       (-170, -60, -30, 75),
    "north_america":  (-170, 15, -50, 75),
    "south_america":  (-85, -58, -30, 15),
    "horn_africa":    (28, -5, 52, 20),
    "central_asia":   (45, 25, 90, 55),
    "mediterranean":  (-10, 28, 40, 48),
    "sub_saharan":    (-20, -38, 55, 18),
}

PROJECTIONS = {
    "platecarree":  "EPSG:4326",
    "robinson":     "ESRI:54030",
    "mollweide":    "ESRI:54009",
    "winkel":       "ESRI:54019",
    "eckert4":      "ESRI:54012",
    "mercator":     "EPSG:3857",
    "albers_africa":   "+proj=aea +lat_1=-18 +lat_2=24 +lat_0=3 +lon_0=20 +datum=WGS84",
    "albers_europe":   "+proj=aea +lat_1=43 +lat_2=62 +lat_0=50 +lon_0=10 +datum=WGS84",
    "albers_asia":     "+proj=aea +lat_1=15 +lat_2=45 +lat_0=30 +lon_0=95 +datum=WGS84",
    "albers_americas": "+proj=aea +lat_1=-20 +lat_2=50 +lat_0=15 +lon_0=-90 +datum=WGS84",
    "lambert_europe":  "EPSG:3035",
    "lambert_us":      "EPSG:5070",
    "equal_earth":     "+proj=eqearth +datum=WGS84",
}

REGION_DEFAULT_PROJECTION = {
    "world":          "robinson",
    "africa":         "albers_africa",
    "europe":         "lambert_europe",
    "asia":           "albers_asia",
    "east_asia":      "albers_asia",
    "southeast_asia": "albers_asia",
    "south_asia":     "albers_asia",
    "middle_east":    "albers_asia",
    "americas":       "albers_americas",
    "north_america":  "lambert_us",
    "south_america":  "albers_americas",
    "horn_africa":    "albers_africa",
    "central_asia":   "albers_asia",
    "mediterranean":  "lambert_europe",
    "sub_saharan":    "albers_africa",
}

# Color schemes for cartographic decoration
OCEAN_COLOR     = "#D6E6F2"
LAND_COLOR      = "#FAF7F2"
LAKE_COLOR      = "#BBD6E8"
RIVER_COLOR     = "#9CBED1"
COAST_COLOR     = "#5E7A8C"
BORDER_COLOR    = "#999999"
BORDER_DISPUTED = "#BBBBBB"
NO_DATA_COLOR   = "#ECECEC"

JOURNAL_PRESETS = {
    "generic": {
        "width_mm": 174, "height_mm": 110, "dpi": 300, "format": "png",
        "title_size": 13, "subtitle_size": 10, "note_size": 7, "label_size": 8,
        "font_family": "DejaVu Sans",
    },
    "nature_single": {
        "width_mm": 89,  "height_mm": 70, "dpi": 600, "format": "pdf",
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

# Small countries / islands that disappear at world scale — for inset maps
# Each entry is (lon_min, lat_min, lon_max, lat_max).
SMALL_COUNTRY_INSETS = {
    "Singapore":         (103.55, 1.16, 104.10, 1.50),
    "Maldives":          (72.0, -0.7, 74.0, 7.5),
    "Bahrain":           (50.2, 25.7, 50.9, 26.4),
    "eSwatini":          (30.7, -27.4, 32.2, -25.7),
    "Eswatini":          (30.7, -27.4, 32.2, -25.7),
    "Hong Kong":         (113.8, 22.15, 114.45, 22.6),
    "Mauritius":         (57.2, -20.6, 57.85, -19.95),
    "Cabo Verde":        (-25.5, 14.7, -22.5, 17.3),
    "Cape Verde":        (-25.5, 14.7, -22.5, 17.3),
    "Comoros":           (43.0, -13.0, 45.5, -11.3),
    "São Tomé and Príncipe": (6.4, -0.1, 7.5, 1.8),
    "Sao Tome and Principe": (6.4, -0.1, 7.5, 1.8),
    "Trinidad and Tobago": (-62.0, 10.0, -60.4, 11.5),
    "Jamaica":           (-78.5, 17.6, -76.0, 18.6),
    "Cyprus":            (32.0, 34.5, 34.7, 35.8),
    "Lebanon":           (35.0, 33.0, 36.7, 34.7),
    "Qatar":             (50.7, 24.4, 51.7, 26.2),
    "Kuwait":            (46.5, 28.5, 48.5, 30.1),
    "Brunei":            (114.0, 4.0, 115.4, 5.1),
    "Timor-Leste":       (124.0, -9.6, 127.5, -8.0),
    "Lesotho":           (27.0, -30.7, 29.5, -28.5),
    "Djibouti":          (41.7, 10.9, 43.4, 12.7),
    # DOM/TOM français (utiles pour études TB France)
    "Réunion":           (55.2, -21.4, 55.9, -20.85),
    "La Réunion":        (55.2, -21.4, 55.9, -20.85),
    "Reunion":           (55.2, -21.4, 55.9, -20.85),
    "Mayotte":           (45.0, -13.05, 45.35, -12.6),
    "Guadeloupe":        (-61.85, 15.85, -61.0, 16.55),
    "Martinique":        (-61.25, 14.35, -60.8, 14.9),
    "French Guiana":     (-54.7, 2.0, -51.6, 5.8),
    "Guyane":            (-54.7, 2.0, -51.6, 5.8),
    "New Caledonia":     (163.5, -22.8, 168.2, -19.5),
    "Nouvelle-Calédonie": (163.5, -22.8, 168.2, -19.5),
    "French Polynesia":  (-152.0, -18.0, -148.5, -16.0),
    "Polynésie française": (-152.0, -18.0, -148.5, -16.0),
    "Wallis and Futuna": (-178.3, -14.4, -176.0, -13.1),
    "Saint Pierre and Miquelon": (-56.5, 46.7, -56.1, 47.2),
    "Saint-Pierre-et-Miquelon":  (-56.5, 46.7, -56.1, 47.2),
    "Saint Martin":      (-63.2, 18.0, -63.0, 18.15),
    "Saint Barthélemy":  (-62.92, 17.85, -62.78, 17.97),
    "Saint-Barthélemy":  (-62.92, 17.85, -62.78, 17.97),
}

TROPICS = {
    "Tropic of Cancer":     23.4368,
    "Equator":              0.0,
    "Tropic of Capricorn": -23.4368,
}

# Resolution per region (default selection)
REGION_DEFAULT_RES = {
    "world": "110m", "africa": "50m", "europe": "50m",
    "asia": "50m", "east_asia": "50m", "southeast_asia": "50m",
    "south_asia": "50m", "middle_east": "50m",
    "americas": "50m", "north_america": "50m", "south_america": "50m",
    "horn_africa": "50m", "central_asia": "50m",
    "mediterranean": "50m", "sub_saharan": "50m",
}


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


# ----------------------------------------------------------------------
# Natural Earth loader
# ----------------------------------------------------------------------

def _ne_download(resolution: str, category: str, name: str) -> Path:
    """Download a Natural Earth shapefile, cache locally, return path to .shp."""
    cache_subdir = NE_CACHE_DIR / f"ne_{resolution}_{name}"
    shp_path = cache_subdir / f"ne_{resolution}_{name}.shp"
    if shp_path.exists():
        return shp_path
    cache_subdir.mkdir(parents=True, exist_ok=True)
    url = NE_BASE_URL.format(res=resolution, cat=category, name=name)
    _log(f"Downloading {url} ...")
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = resp.read()
    except Exception as e:
        raise RuntimeError(f"Failed to download {url}: {e}")
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zf.extractall(cache_subdir)
    if not shp_path.exists():
        candidates = list(cache_subdir.glob("*.shp"))
        if not candidates:
            raise RuntimeError(f"No .shp found after extracting {url}")
        shp_path = candidates[0]
    return shp_path


_LAYER_SPECS = {
    "countries":  ("cultural", "admin_0_countries"),
    "states":     ("cultural", "admin_1_states_provinces"),
    "cities":     ("cultural", "populated_places"),
    "ocean":      ("physical", "ocean"),
    "land":       ("physical", "land"),
    "lakes":      ("physical", "lakes"),
    "rivers":     ("physical", "rivers_lake_centerlines"),
    "coastline":  ("physical", "coastline"),
    "graticule":  ("physical", "graticules_15"),
}


def load_layer(name: str, resolution: str = "110m") -> gpd.GeoDataFrame:
    if name not in _LAYER_SPECS:
        raise ValueError(f"Unknown layer '{name}'. Available: {list(_LAYER_SPECS)}")
    cat, ne_name = _LAYER_SPECS[name]
    shp = _ne_download(resolution, cat, ne_name)
    gdf = gpd.read_file(shp)
    if "NAME" in gdf.columns and "name" not in gdf.columns:
        gdf = gdf.rename(columns={"NAME": "name"})
    if "NAME_LONG" in gdf.columns and "name_long" not in gdf.columns:
        gdf = gdf.rename(columns={"NAME_LONG": "name_long"})
    return gdf


def load_world(resolution: str = "110m") -> gpd.GeoDataFrame:
    world = load_layer("countries", resolution)
    world = world[world["name"] != "Antarctica"]
    return world


# ----------------------------------------------------------------------
# Data merging
# ----------------------------------------------------------------------

def normalize_country(name) -> str:
    if pd.isna(name):
        return ""
    s = str(name).strip()
    return COUNTRY_ALIASES.get(s.lower(), s)


def merge_data(world: gpd.GeoDataFrame, df: pd.DataFrame, country_col: str = "country") -> gpd.GeoDataFrame:
    df = df.copy()
    df["_country_norm"] = df[country_col].apply(normalize_country)
    merged = world.merge(df, left_on="name", right_on="_country_norm", how="left")
    user_set = set(df["_country_norm"].unique()) - {""}
    world_set = set(world["name"].unique())
    unmatched = user_set - world_set
    if unmatched:
        _log(f"Warning: {len(unmatched)} unmatched countries: {sorted(unmatched)[:10]}")
    return merged


# ----------------------------------------------------------------------
# Projection & extent
# ----------------------------------------------------------------------

def resolve_projection(name: str | None, region: str) -> str:
    if not name or name == "auto":
        name = REGION_DEFAULT_PROJECTION.get(region, "robinson")
    if name in PROJECTIONS:
        return PROJECTIONS[name]
    return name  # assume user passed a CRS string directly


def parse_extent(region: str) -> tuple[float, float, float, float]:
    if region in REGIONS:
        return REGIONS[region]
    parts = [float(x) for x in region.split(",")]
    if len(parts) != 4:
        raise ValueError(f"Region must be a known name or 'lon_min,lat_min,lon_max,lat_max'")
    return tuple(parts)  # type: ignore


def crop_to_extent(gdf: gpd.GeoDataFrame, extent_ll: tuple[float, float, float, float]) -> gpd.GeoDataFrame:
    lon_min, lat_min, lon_max, lat_max = extent_ll
    return gdf.cx[lon_min:lon_max, lat_min:lat_max]


def project_extent_to_axes(extent_ll, target_crs: str) -> tuple[float, float, float, float]:
    """Reproject a lon/lat bbox into the target CRS, return (xmin, ymin, xmax, ymax)."""
    lon_min, lat_min, lon_max, lat_max = extent_ll
    n = 40
    pts_x = list(np.linspace(lon_min, lon_max, n)) + [lon_max] * n + \
            list(np.linspace(lon_max, lon_min, n)) + [lon_min] * n
    pts_y = [lat_min] * n + list(np.linspace(lat_min, lat_max, n)) + \
            [lat_max] * n + list(np.linspace(lat_max, lat_min, n))
    gdf = gpd.GeoDataFrame(
        geometry=[Point(x, y) for x, y in zip(pts_x, pts_y)],
        crs="EPSG:4326",
    ).to_crs(target_crs)
    xs = gdf.geometry.x.values
    ys = gdf.geometry.y.values
    return float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())


# ----------------------------------------------------------------------
# Figure setup
# ----------------------------------------------------------------------

@dataclass
class Decorations:
    """Extra cartographic decorations that can be toggled per call."""
    insets: str = "none"            # "none" | "auto" | "country1,country2"
    insets_numbered: bool = False
    smart_labels: str = "none"      # "none" | "fast" | "quality"
    label_threshold: float | None = None
    show_cities: bool = False
    min_pop: int = 1_000_000
    hillshade: bool = False
    show_tropics: bool = False
    show_biomes: bool = False
    climate_raster: str | None = None


@dataclass
class MapStyle:
    preset: str = "generic"
    width_mm: float = 174
    height_mm: float = 110
    dpi: int = 300
    title_size: float = 13
    subtitle_size: float = 10
    note_size: float = 7
    label_size: float = 8
    font_family: str = "DejaVu Sans"
    ocean: str = OCEAN_COLOR
    land: str = LAND_COLOR
    lake: str = LAKE_COLOR
    river: str = RIVER_COLOR
    coast: str = COAST_COLOR
    border: str = BORDER_COLOR
    no_data: str = NO_DATA_COLOR

    @classmethod
    def from_preset(cls, preset: str) -> "MapStyle":
        if preset not in JOURNAL_PRESETS:
            _log(f"Warning: unknown preset '{preset}', falling back to 'generic'")
            preset = "generic"
        cfg = JOURNAL_PRESETS[preset]
        return cls(preset=preset, **{k: v for k, v in cfg.items() if k != "format"})


def _resolve_font(family: str) -> str:
    """Return `family` if a usable font is installed, else fall back to DejaVu Sans.

    Journal presets request Arial/Helvetica which are often not installed on Linux;
    without this the map still renders but matplotlib spams one 'findfont' warning per
    text element. We detect availability once, silence those warnings, and fall back."""
    import logging
    import matplotlib.font_manager as fm
    try:
        available = {f.name for f in fm.fontManager.ttflist}
    except Exception:
        available = set()
    if family in available:
        return family
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
    if family not in ("DejaVu Sans", "sans-serif"):
        _log(f"Font '{family}' not installed; falling back to DejaVu Sans "
             f"(install the font or use --preset generic for the requested typeface).")
    return "DejaVu Sans"


def setup_figure(style: MapStyle, figsize: tuple | None = None) -> tuple[plt.Figure, plt.Axes]:
    if figsize is None:
        w_in = style.width_mm / 25.4
        h_in = style.height_mm / 25.4
        figsize = (w_in, h_in)
    plt.rcParams["font.family"] = _resolve_font(style.font_family)
    plt.rcParams["font.size"] = style.label_size
    plt.rcParams["axes.titlesize"] = style.title_size
    plt.rcParams["legend.fontsize"] = style.label_size
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["ps.fonttype"] = 42
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    ax.set_aspect("equal")
    return fig, ax


# ----------------------------------------------------------------------
# Base cartographic layers
# ----------------------------------------------------------------------

def draw_base_layers(
    ax: plt.Axes,
    region: str,
    projection_crs: str,
    style: MapStyle,
    resolution: str = "auto",
    show_ocean: bool = True,
    show_land: bool = True,
    show_lakes: bool = True,
    show_rivers: bool = False,
    show_coastline: bool = True,
    show_borders: bool = True,
    border_lw: float = 0.3,
) -> gpd.GeoDataFrame:
    """Draw the base cartographic background; return the projected countries layer."""
    if resolution == "auto":
        resolution = REGION_DEFAULT_RES.get(region, "110m")
    extent_ll = parse_extent(region)

    # Frame: ocean rectangle in projected CRS
    xmin, ymin, xmax, ymax = project_extent_to_axes(extent_ll, projection_crs)
    if show_ocean:
        ax.add_patch(plt.Rectangle(
            (xmin, ymin), xmax - xmin, ymax - ymin,
            facecolor=style.ocean, edgecolor="none", zorder=0,
        ))

    if show_land:
        try:
            land = load_layer("land", resolution)
            land_crop = crop_to_extent(land, extent_ll).to_crs(projection_crs)
            land_crop.plot(ax=ax, color=style.land, edgecolor="none", zorder=1)
        except Exception as e:
            _log(f"Land layer skipped: {e}")

    countries = load_world(resolution)
    countries_crop = crop_to_extent(countries, extent_ll).to_crs(projection_crs)
    if show_borders:
        countries_crop.plot(
            ax=ax, facecolor="none", edgecolor=style.border,
            linewidth=border_lw, zorder=3,
        )

    if show_lakes:
        try:
            lakes = load_layer("lakes", resolution)
            lakes_crop = crop_to_extent(lakes, extent_ll).to_crs(projection_crs)
            lakes_crop.plot(ax=ax, color=style.lake, edgecolor="none", zorder=4)
        except Exception as e:
            _log(f"Lakes layer skipped: {e}")

    if show_rivers:
        try:
            rivers = load_layer("rivers", resolution)
            rivers_crop = crop_to_extent(rivers, extent_ll).to_crs(projection_crs)
            rivers_crop.plot(ax=ax, color=style.river, linewidth=0.3, zorder=4)
        except Exception as e:
            _log(f"Rivers layer skipped: {e}")

    if show_coastline:
        try:
            coast = load_layer("coastline", resolution)
            coast_crop = crop_to_extent(coast, extent_ll).to_crs(projection_crs)
            coast_crop.plot(ax=ax, color=style.coast, linewidth=0.4, zorder=5)
        except Exception as e:
            _log(f"Coastline layer skipped: {e}")

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_axis_off()
    return countries_crop


def reproject_countries(world: gpd.GeoDataFrame, region: str, projection_crs: str) -> gpd.GeoDataFrame:
    extent_ll = parse_extent(region)
    return crop_to_extent(world, extent_ll).to_crs(projection_crs)


# ----------------------------------------------------------------------
# Decorations: graticule, scale bar, north arrow, credits, title block
# ----------------------------------------------------------------------

def draw_graticule(
    ax: plt.Axes,
    region: str,
    projection_crs: str,
    step_lon: float | None = None,
    step_lat: float | None = None,
    color: str = "#B8C5CC",
    lw: float = 0.25,
    alpha: float = 0.7,
) -> None:
    lon_min, lat_min, lon_max, lat_max = parse_extent(region)
    span_lon = lon_max - lon_min
    span_lat = lat_max - lat_min
    if step_lon is None:
        step_lon = _nice_step(span_lon)
    if step_lat is None:
        step_lat = _nice_step(span_lat)

    n = 80
    # Meridians
    for lon in np.arange(_floor_to(lon_min, step_lon), lon_max + step_lon, step_lon):
        if lon < lon_min - 1 or lon > lon_max + 1:
            continue
        line = gpd.GeoSeries.from_xy(
            [lon] * n, np.linspace(lat_min, lat_max, n), crs="EPSG:4326",
        )
        line_proj = line.to_crs(projection_crs)
        ax.plot(line_proj.x, line_proj.y, color=color, linewidth=lw,
                alpha=alpha, zorder=2)
    # Parallels
    for lat in np.arange(_floor_to(lat_min, step_lat), lat_max + step_lat, step_lat):
        if lat < lat_min - 1 or lat > lat_max + 1:
            continue
        line = gpd.GeoSeries.from_xy(
            np.linspace(lon_min, lon_max, n), [lat] * n, crs="EPSG:4326",
        )
        line_proj = line.to_crs(projection_crs)
        ax.plot(line_proj.x, line_proj.y, color=color, linewidth=lw,
                alpha=alpha, zorder=2)


def _nice_step(span: float) -> float:
    for step in (1, 2, 5, 10, 15, 20, 30, 45, 60, 90):
        if span / step <= 8:
            return step
    return 90


def _floor_to(x: float, step: float) -> float:
    return math.floor(x / step) * step


def draw_scale_bar(
    ax: plt.Axes,
    region: str,
    projection_crs: str,
    style: MapStyle,
    length_km: float | None = None,
    location: str = "lower_left",
) -> None:
    lon_min, lat_min, lon_max, lat_max = parse_extent(region)
    span_lon_km = _haversine_km(lat_min, lon_min, lat_min, lon_max)
    if length_km is None:
        length_km = _nice_scale_km(span_lon_km / 4)

    # Anchor in projected coordinates
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    if location == "lower_left":
        x0_ll = lon_min + 0.05 * (lon_max - lon_min)
        y0_ll = lat_min + 0.05 * (lat_max - lat_min)
    elif location == "lower_right":
        x0_ll = lon_max - 0.05 * (lon_max - lon_min)
        y0_ll = lat_min + 0.05 * (lat_max - lat_min)
    else:
        x0_ll = lon_min + 0.05 * (lon_max - lon_min)
        y0_ll = lat_min + 0.05 * (lat_max - lat_min)

    p0 = gpd.GeoSeries([Point(x0_ll, y0_ll)], crs="EPSG:4326").to_crs(projection_crs)
    x0 = float(p0.x.iloc[0]); y0 = float(p0.y.iloc[0])

    # Compute proj length for length_km along east at center lat
    lat_mid = y0_ll
    lon_end_ll = x0_ll + (length_km / 111.32 / math.cos(math.radians(lat_mid)))
    if location == "lower_right":
        lon_end_ll = x0_ll - (length_km / 111.32 / math.cos(math.radians(lat_mid)))
    p1 = gpd.GeoSeries([Point(lon_end_ll, lat_mid)], crs="EPSG:4326").to_crs(projection_crs)
    x1 = float(p1.x.iloc[0]); y1 = float(p1.y.iloc[0])

    # Composite bar: two segments alternating black/white
    seg_x = [x0, (x0 + x1) / 2, x1]
    bar_h = (ymax - ymin) * 0.008
    for i in range(2):
        color = "black" if i % 2 == 0 else "white"
        rect = plt.Rectangle(
            (seg_x[i], y0), seg_x[i + 1] - seg_x[i], bar_h,
            facecolor=color, edgecolor="black", linewidth=0.5, zorder=10,
        )
        ax.add_patch(rect)
    # Labels
    for i, val in enumerate([0, length_km / 2, length_km]):
        label = f"{int(val)}" if val == int(val) else f"{val:.1f}"
        if i == 2:
            label = f"{int(length_km)} km"
        ax.text(seg_x[i], y0 - bar_h * 1.2, label,
                ha="center", va="top", fontsize=style.note_size, zorder=10,
                color="black")


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _nice_scale_km(approx: float) -> float:
    candidates = [10, 25, 50, 100, 200, 250, 500, 1000, 2000, 2500, 5000]
    for c in candidates:
        if c >= approx:
            return c
    return 5000


def draw_north_arrow(
    ax: plt.Axes,
    region: str,
    projection_crs: str,
    style: MapStyle,
    location: str = "upper_right",
) -> None:
    lon_min, lat_min, lon_max, lat_max = parse_extent(region)
    if location == "upper_right":
        x_ll = lon_max - 0.08 * (lon_max - lon_min)
        y_ll = lat_max - 0.10 * (lat_max - lat_min)
    elif location == "upper_left":
        x_ll = lon_min + 0.05 * (lon_max - lon_min)
        y_ll = lat_max - 0.10 * (lat_max - lat_min)
    else:
        x_ll = lon_max - 0.08 * (lon_max - lon_min)
        y_ll = lat_max - 0.10 * (lat_max - lat_min)

    p0 = gpd.GeoSeries([Point(x_ll, y_ll)], crs="EPSG:4326").to_crs(projection_crs)
    p_north = gpd.GeoSeries([Point(x_ll, y_ll + 0.05 * (lat_max - lat_min))],
                            crs="EPSG:4326").to_crs(projection_crs)
    x0 = float(p0.x.iloc[0]); y0 = float(p0.y.iloc[0])
    xn = float(p_north.x.iloc[0]); yn = float(p_north.y.iloc[0])

    arrow = FancyArrowPatch(
        (x0, y0), (xn, yn),
        arrowstyle="-|>", mutation_scale=12,
        color="black", linewidth=1.2, zorder=10,
    )
    ax.add_patch(arrow)
    ax.text(xn, yn, "N", ha="center", va="bottom",
            fontsize=style.label_size, fontweight="bold", zorder=10,
            path_effects=[withStroke(linewidth=2, foreground="white")])


def draw_title_block(
    fig: plt.Figure,
    title: str | None,
    subtitle: str | None,
    style: MapStyle,
) -> None:
    if title and subtitle:
        fig.text(0.5, 0.965, title, fontsize=style.title_size,
                 fontweight="bold", ha="center", va="top")
        fig.text(0.5, 0.915, subtitle, fontsize=style.subtitle_size,
                 color="#555555", ha="center", va="top", style="italic")
    elif title:
        fig.text(0.5, 0.965, title, fontsize=style.title_size,
                 fontweight="bold", ha="center", va="top")
    elif subtitle:
        fig.text(0.5, 0.96, subtitle, fontsize=style.subtitle_size,
                 color="#555555", ha="center", va="top", style="italic")


def draw_credits(
    fig: plt.Figure,
    style: MapStyle,
    note: str | None = None,
    show_naturalearth: bool = True,
) -> None:
    parts = []
    if show_naturalearth:
        parts.append("Basemap: Natural Earth (public domain)")
    if note:
        parts.append(note)
    if not parts:
        return
    fig.text(0.99, 0.01, " · ".join(parts),
             fontsize=style.note_size, color="#666666",
             ha="right", va="bottom")


# ----------------------------------------------------------------------
# Styled legend
# ----------------------------------------------------------------------

def styled_legend(
    ax: plt.Axes,
    handles: list,
    title: str | None = None,
    loc: str = "lower left",
    fontsize: float | None = None,
    title_fontsize: float | None = None,
    bbox_to_anchor: tuple | None = None,
) -> None:
    kwargs = dict(
        handles=handles, title=title, loc=loc,
        fontsize=fontsize, title_fontsize=title_fontsize,
        frameon=True, framealpha=0.92,
        edgecolor="#888888", facecolor="white",
        borderpad=0.6, labelspacing=0.5,
    )
    if bbox_to_anchor is not None:
        kwargs["bbox_to_anchor"] = bbox_to_anchor
    leg = ax.legend(**kwargs)
    leg.get_frame().set_linewidth(0.5)


# ----------------------------------------------------------------------
# Plot types
# ----------------------------------------------------------------------

def plot_choropleth(
    df: pd.DataFrame, value_col: str, output: str, *,
    region: str = "world",
    projection: str = "auto",
    cmap: str = "YlOrRd",
    title: str | None = None,
    subtitle: str | None = None,
    legend_title: str | None = None,
    log_scale: bool = False,
    vmin: float | None = None,
    vmax: float | None = None,
    center: float | None = None,
    sig_col: str | None = None,
    sig_threshold: float = 0.05,
    sig_style: str = "asterisk",
    sig_legend_loc: str = "lower left",
    show_labels: bool = False,
    label_threshold: float | None = None,
    style: MapStyle | None = None,
    resolution: str = "auto",
    note: str | None = None,
    figsize: tuple | None = None,
    decorations: Decorations | None = None,
) -> None:
    style = style or MapStyle()
    proj = resolve_projection(projection, region)
    fig, ax = setup_figure(style, figsize)
    _apply_pre_decorations(ax, region, proj, resolution, decorations)
    countries_proj = draw_base_layers(ax, region, proj, style, resolution=resolution)

    countries_unproj = load_world(REGION_DEFAULT_RES.get(region, "110m"))
    merged_unproj = merge_data(countries_unproj, df)
    merged = merged_unproj[merged_unproj.geometry.notna()].to_crs(proj)
    merged = crop_to_extent_proj(merged, region, proj)

    has_data = merged[merged[value_col].notna()]
    if has_data.empty:
        _log("Warning: no data matched to countries.")
    else:
        vals = has_data[value_col].dropna()
        if log_scale:
            norm = LogNorm(vmin=max(vmin or vals.min(), 1), vmax=vmax or vals.max())
            legend_kwds = {"label": legend_title or value_col, "shrink": 0.55, "pad": 0.02}
            has_data.plot(
                ax=ax, column=value_col, cmap=cmap, norm=norm,
                edgecolor="white", linewidth=0.4, zorder=6,
                legend=True, legend_kwds=legend_kwds,
            )
        else:
            if center is not None and vmin is None and vmax is None:
                dev = float((vals - center).abs().max()) or 1.0
                vmin, vmax = center - dev, center + dev
            kw = {"vmin": vmin, "vmax": vmax} if vmin is not None or vmax is not None else {}
            legend_kwds = {"label": legend_title or value_col, "shrink": 0.55, "pad": 0.02}
            has_data.plot(
                ax=ax, column=value_col, cmap=cmap,
                edgecolor="white", linewidth=0.4, zorder=6,
                legend=True, legend_kwds=legend_kwds, **kw,
            )

        if show_labels:
            thr = label_threshold or vals.quantile(0.5)
            for _, row in has_data.iterrows():
                if row[value_col] >= thr:
                    c = row.geometry.centroid
                    ax.annotate(
                        row["name"], xy=(c.x, c.y),
                        fontsize=style.note_size, ha="center", va="center",
                        color="black", zorder=8,
                        path_effects=[withStroke(linewidth=2, foreground="white")],
                    )

        if sig_col and sig_col in has_data.columns:
            def _is_sig(v):
                try:
                    return float(v) < sig_threshold
                except (TypeError, ValueError):
                    return False
            sig_rows = has_data[has_data[sig_col].apply(_is_sig)]
            if not sig_rows.empty:
                if sig_style == "hatch":
                    sig_rows.plot(ax=ax, facecolor="none", edgecolor="#222222",
                                  linewidth=0.4, hatch="////", zorder=7)
                elif sig_style == "edge":
                    sig_rows.plot(ax=ax, facecolor="none", edgecolor="black",
                                  linewidth=1.4, zorder=7)
                else:  # asterisk (default)
                    for _, row in sig_rows.iterrows():
                        c = row.geometry.centroid
                        ax.annotate(
                            "*", xy=(c.x, c.y),
                            fontsize=style.title_size, fontweight="bold",
                            ha="center", va="center", color="black", zorder=9,
                            path_effects=[withStroke(linewidth=2.5, foreground="white")],
                        )
                # Self-documenting legend vignette for the significance symbol,
                # placed in-figure (a corner cartouche) rather than only in the footer.
                from matplotlib.lines import Line2D
                from matplotlib.patches import Patch
                _slabel = f"{sig_col} < {sig_threshold:g}"
                if sig_style == "hatch":
                    _shandle = Patch(facecolor="none", edgecolor="#222222", hatch="////")
                elif sig_style == "edge":
                    _shandle = Patch(facecolor="none", edgecolor="black", linewidth=1.4)
                else:
                    _shandle = Line2D([], [], marker="*", color="black", markersize=11,
                                      linestyle="None", markeredgecolor="white",
                                      markeredgewidth=0.6)
                _sleg = ax.legend([_shandle], [_slabel], loc=sig_legend_loc,
                                  fontsize=style.note_size, frameon=True,
                                  framealpha=0.9, edgecolor="#cccccc", borderpad=0.6)
                _sleg.set_zorder(11)
                ax.add_artist(_sleg)

    draw_graticule(ax, region, proj)
    if region != "world":
        draw_scale_bar(ax, region, proj, style)
        draw_north_arrow(ax, region, proj, style)
    draw_title_block(fig, title, subtitle, style)
    draw_credits(fig, style, note=note)

    _apply_post_decorations(
        fig, ax, region, proj, style, decorations,
        countries_unproj=countries_unproj,
        data_layer=merged_unproj, value_col=value_col,
        cmap=cmap, log_scale=log_scale, vmin=vmin, vmax=vmax,
        df=df,
    )

    _save_figure(fig, output, style)


def crop_to_extent_proj(gdf: gpd.GeoDataFrame, region: str, projection_crs: str) -> gpd.GeoDataFrame:
    """Filter gdf (already in projection_crs) to projected extent of region."""
    extent_ll = parse_extent(region)
    xmin, ymin, xmax, ymax = project_extent_to_axes(extent_ll, projection_crs)
    bb = box(xmin, ymin, xmax, ymax)
    return gdf[gdf.geometry.intersects(bb)]


def plot_bubble(
    df: pd.DataFrame, value_col: str, output: str, *,
    region: str = "world",
    projection: str = "auto",
    color: str = "#E03D31",
    title: str | None = None,
    subtitle: str | None = None,
    legend_title: str | None = None,
    style: MapStyle | None = None,
    resolution: str = "auto",
    max_bubble: float = 400,
    note: str | None = None,
    figsize: tuple | None = None,
) -> None:
    style = style or MapStyle()
    proj = resolve_projection(projection, region)
    fig, ax = setup_figure(style, figsize)
    countries_proj = draw_base_layers(ax, region, proj, style, resolution=resolution)

    df = df.copy()
    df["_country_norm"] = df["country"].apply(normalize_country)
    centroids = {row["name"]: row.geometry.centroid for _, row in countries_proj.iterrows()}

    xs, ys, sizes = [], [], []
    vals = df[value_col].astype(float).values
    if len(vals) == 0:
        _log("Warning: empty data")
    max_val = max(vals.max(), 1) if len(vals) else 1
    for _, row in df.iterrows():
        if row["_country_norm"] in centroids:
            c = centroids[row["_country_norm"]]
            xs.append(c.x)
            ys.append(c.y)
            sizes.append(max(15, (row[value_col] / max_val) * max_bubble))

    if xs:
        ax.scatter(
            xs, ys, s=sizes, c=color, alpha=0.7,
            edgecolors="white", linewidth=1.2, zorder=8,
        )

    # Size legend
    handles = []
    for frac, label in [(0.25, max_val * 0.25), (0.5, max_val * 0.5), (1.0, max_val)]:
        handles.append(plt.scatter(
            [], [], s=frac * max_bubble, c=color, alpha=0.7,
            edgecolors="white", linewidth=1.2,
            label=f"{int(label)}",
        ))
    styled_legend(ax, handles, title=legend_title or value_col,
                  loc="lower left", fontsize=style.label_size,
                  title_fontsize=style.label_size)

    draw_graticule(ax, region, proj)
    if region != "world":
        draw_scale_bar(ax, region, proj, style)
        draw_north_arrow(ax, region, proj, style)
    draw_title_block(fig, title, subtitle, style)
    draw_credits(fig, style, note=note)

    _save_figure(fig, output, style)


def plot_pie_map(
    df: pd.DataFrame, group_col: str, output: str, *,
    region: str = "world",
    projection: str = "auto",
    palette: dict | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    style: MapStyle | None = None,
    resolution: str = "auto",
    min_total: int = 5,
    pie_scale: float = 1.0,
    note: str | None = None,
    figsize: tuple | None = None,
    legend_title: str = "Lineage",
) -> None:
    style = style or MapStyle()
    proj = resolve_projection(projection, region)
    palette = palette or MTBC_PALETTE
    fig, ax = setup_figure(style, figsize)
    countries_proj = draw_base_layers(ax, region, proj, style, resolution=resolution)

    df = df.copy()
    df["_country_norm"] = df["country"].apply(normalize_country)
    centroids = {row["name"]: row.geometry.centroid for _, row in countries_proj.iterrows()}

    groups = sorted(df[group_col].unique())
    resolved = resolve_palette(groups, palette)

    # Compute country totals for pie size scaling
    if "n" in df.columns:
        country_totals = df.groupby("_country_norm")["n"].sum()
    else:
        country_totals = df.groupby("_country_norm").size()

    if country_totals.empty:
        max_total = 1
    else:
        max_total = max(country_totals.max(), 1)

    # Map extent in projected units to size pies appropriately
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    base_radius = 0.018 * min(xmax - xmin, ymax - ymin) * pie_scale

    for country_norm, cdf in df.groupby("_country_norm"):
        if country_norm not in centroids:
            continue
        if "n" in cdf.columns:
            total = cdf["n"].sum()
        else:
            total = len(cdf)
        if total < min_total:
            continue
        c = centroids[country_norm]
        radius = base_radius * (0.5 + 0.5 * math.sqrt(total / max_total))

        # Halo
        ax.add_patch(plt.Circle(
            (c.x, c.y), radius * 1.08,
            facecolor="white", edgecolor="#333333", linewidth=0.4, zorder=7,
        ))

        # Slices
        values = []
        colors = []
        for g in groups:
            if "n" in cdf.columns:
                n = cdf[cdf[group_col] == g]["n"].sum()
            else:
                n = (cdf[group_col] == g).sum()
            if n > 0:
                values.append(n)
                colors.append(resolved[g])
        if not values:
            continue

        tot = sum(values)
        start = 90
        for v, col in zip(values, colors):
            angle = 360 * v / tot
            wedge = mpatches.Wedge(
                (c.x, c.y), radius, start, start + angle,
                facecolor=col, edgecolor="white", linewidth=0.4, zorder=8,
            )
            ax.add_patch(wedge)
            start += angle

    # Size legend (a few representative totals)
    size_handles = []
    for frac, label in [(0.25, max_total * 0.25), (0.5, max_total * 0.5), (1.0, max_total)]:
        size_handles.append(plt.scatter(
            [], [], s=(base_radius * (0.5 + 0.5 * math.sqrt(frac))) ** 2 * 80,
            facecolors="white", edgecolors="#333333", linewidth=0.4,
            label=f"{int(label)}",
        ))

    # Color legend
    color_handles = []
    for g in groups:
        if "n" in df.columns and df[df[group_col] == g]["n"].sum() == 0:
            continue
        color_handles.append(mpatches.Patch(facecolor=resolved[g], label=g))
    if len(color_handles) > 6:
        styled_legend(ax, color_handles, title=legend_title,
                      loc="center left", fontsize=style.label_size - 1,
                      bbox_to_anchor=(1.02, 0.5))
    else:
        styled_legend(ax, color_handles, title=legend_title, loc="lower left",
                      fontsize=style.label_size)

    draw_graticule(ax, region, proj)
    if region != "world":
        draw_scale_bar(ax, region, proj, style)
        draw_north_arrow(ax, region, proj, style)
    draw_title_block(fig, title, subtitle, style)
    draw_credits(fig, style, note=note)

    _save_figure(fig, output, style)


def plot_points(
    df: pd.DataFrame, output: str, *,
    lat_col: str = "lat",
    lon_col: str = "lon",
    value_col: str | None = None,
    group_col: str | None = None,
    region: str = "world",
    projection: str = "auto",
    palette: dict | None = None,
    color: str = "#E03D31",
    cmap: str = "YlOrRd",
    title: str | None = None,
    subtitle: str | None = None,
    legend_title: str | None = None,
    style: MapStyle | None = None,
    resolution: str = "auto",
    marker_size: float = 25,
    max_size: float = 250,
    alpha: float = 0.85,
    jitter: float = 0.0,
    note: str | None = None,
    figsize: tuple | None = None,
    decorations: Decorations | None = None,
) -> None:
    style = style or MapStyle()
    proj = resolve_projection(projection, region)
    palette = palette or MTBC_PALETTE
    fig, ax = setup_figure(style, figsize)
    _apply_pre_decorations(ax, region, proj, resolution, decorations)
    draw_base_layers(ax, region, proj, style, resolution=resolution)

    df = df.copy()
    df = df.dropna(subset=[lat_col, lon_col])
    if jitter > 0:
        rng = np.random.default_rng(42)
        df[lat_col] = df[lat_col] + rng.normal(0, jitter, len(df))
        df[lon_col] = df[lon_col] + rng.normal(0, jitter, len(df))

    points_gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
        crs="EPSG:4326",
    ).to_crs(proj)

    # Size determination
    if value_col and value_col in df.columns:
        vals = df[value_col].astype(float).values
        vmax = max(vals.max(), 1)
        sizes = marker_size + (vals / vmax) * (max_size - marker_size)
    else:
        sizes = np.full(len(df), marker_size)

    # Color determination
    legend_handles = []
    if group_col and group_col in df.columns:
        groups = sorted(df[group_col].unique())
        resolved = resolve_palette(groups, palette)
        colors = [resolved[g] for g in df[group_col]]
        ax.scatter(
            points_gdf.geometry.x, points_gdf.geometry.y,
            s=sizes, c=colors, alpha=alpha,
            edgecolors="white", linewidth=0.6, zorder=8,
        )
        for g in groups:
            legend_handles.append(plt.scatter(
                [], [], s=marker_size, c=resolved[g],
                alpha=alpha, edgecolors="white", linewidth=0.6,
                label=str(g),
            ))
        # Si beaucoup de groupes (>6), legend hors carte par defaut
        if len(groups) > 6:
            styled_legend(ax, legend_handles, title=legend_title or group_col,
                          loc="center left", fontsize=style.label_size - 1,
                          title_fontsize=style.label_size,
                          bbox_to_anchor=(1.02, 0.5))
        else:
            styled_legend(ax, legend_handles, title=legend_title or group_col,
                          loc="lower left", fontsize=style.label_size,
                          title_fontsize=style.label_size)
    elif value_col and value_col in df.columns:
        scatter = ax.scatter(
            points_gdf.geometry.x, points_gdf.geometry.y,
            s=sizes, c=df[value_col], cmap=cmap, alpha=alpha,
            edgecolors="white", linewidth=0.6, zorder=8,
        )
        cbar = plt.colorbar(scatter, ax=ax, shrink=0.55, pad=0.02)
        cbar.set_label(legend_title or value_col, fontsize=style.label_size)
    else:
        ax.scatter(
            points_gdf.geometry.x, points_gdf.geometry.y,
            s=sizes, c=color, alpha=alpha,
            edgecolors="white", linewidth=0.6, zorder=8,
        )

    draw_graticule(ax, region, proj)
    if region != "world":
        draw_scale_bar(ax, region, proj, style)
        draw_north_arrow(ax, region, proj, style)
    draw_title_block(fig, title, subtitle, style)
    draw_credits(fig, style, note=note)
    _apply_post_decorations(fig, ax, region, proj, style, decorations,
                            countries_unproj=load_world(REGION_DEFAULT_RES.get(region, "110m")),
                            df=df)
    _save_figure(fig, output, style)


def plot_arcs(
    df: pd.DataFrame, output: str, *,
    src_lat_col: str = "src_lat", src_lon_col: str = "src_lon",
    dst_lat_col: str = "dst_lat", dst_lon_col: str = "dst_lon",
    weight_col: str | None = None,
    region: str = "world",
    projection: str = "auto",
    color: str = "#D0021B",
    title: str | None = None,
    subtitle: str | None = None,
    style: MapStyle | None = None,
    resolution: str = "auto",
    min_width: float = 0.5,
    max_width: float = 3.0,
    alpha: float = 0.6,
    note: str | None = None,
    figsize: tuple | None = None,
) -> None:
    """Plot phylogeographic arrows between source and destination coordinates."""
    style = style or MapStyle()
    proj = resolve_projection(projection, region)
    fig, ax = setup_figure(style, figsize)
    draw_base_layers(ax, region, proj, style, resolution=resolution)

    df = df.copy().dropna(subset=[src_lat_col, src_lon_col, dst_lat_col, dst_lon_col])

    # Compute widths
    if weight_col and weight_col in df.columns:
        w = df[weight_col].astype(float).values
        wmax = max(w.max(), 1)
        widths = min_width + (w / wmax) * (max_width - min_width)
    else:
        widths = np.full(len(df), (min_width + max_width) / 2)

    src = gpd.GeoSeries.from_xy(df[src_lon_col], df[src_lat_col],
                                crs="EPSG:4326").to_crs(proj)
    dst = gpd.GeoSeries.from_xy(df[dst_lon_col], df[dst_lat_col],
                                crs="EPSG:4326").to_crs(proj)

    for i in range(len(df)):
        ax.annotate(
            "", xy=(dst.x.iloc[i], dst.y.iloc[i]),
            xytext=(src.x.iloc[i], src.y.iloc[i]),
            arrowprops=dict(
                arrowstyle="->", color=color,
                lw=widths[i], alpha=alpha,
                connectionstyle="arc3,rad=0.2",
            ),
            zorder=9,
        )
        ax.plot([src.x.iloc[i]], [src.y.iloc[i]], "o",
                color=color, markersize=4, alpha=alpha, zorder=8,
                markeredgecolor="white", markeredgewidth=0.5)

    draw_graticule(ax, region, proj)
    if region != "world":
        draw_scale_bar(ax, region, proj, style)
        draw_north_arrow(ax, region, proj, style)
    draw_title_block(fig, title, subtitle, style)
    draw_credits(fig, style, note=note)
    _save_figure(fig, output, style)


def plot_multi_panel(
    df: pd.DataFrame, value_col: str, facet_col: str, output: str, *,
    ncols: int = 2,
    region: str = "world",
    projection: str = "auto",
    cmap: str = "YlOrRd",
    title: str | None = None,
    style: MapStyle | None = None,
    log_scale: bool = False,
    resolution: str = "auto",
    note: str | None = None,
    figsize: tuple | None = None,
) -> None:
    style = style or MapStyle()
    proj = resolve_projection(projection, region)
    facets = sorted(df[facet_col].unique())
    nrows = int(math.ceil(len(facets) / ncols))

    plt.rcParams["font.family"] = _resolve_font(style.font_family)
    plt.rcParams["font.size"] = style.label_size

    if figsize is None:
        w_in = max(style.width_mm / 25.4, ncols * 3.5)
        h_in = max(nrows * 2.5, 4.5)
        figsize = (w_in, h_in)
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    axes = np.atleast_1d(axes).flatten() if nrows * ncols > 1 else np.array([axes])

    vmin = df[value_col].min()
    vmax = df[value_col].max()

    for i, facet in enumerate(facets):
        ax = axes[i]
        countries_proj = draw_base_layers(ax, region, proj, style, resolution=resolution)
        fdf = df[df[facet_col] == facet]
        merged = merge_data(load_world(REGION_DEFAULT_RES.get(region, "110m")), fdf)
        merged = merged[merged.geometry.notna()].to_crs(proj)
        merged = crop_to_extent_proj(merged, region, proj)
        has_data = merged[merged[value_col].notna()]
        if not has_data.empty:
            if log_scale:
                norm = LogNorm(vmin=max(vmin, 1), vmax=vmax)
                has_data.plot(ax=ax, column=value_col, cmap=cmap, norm=norm,
                              edgecolor="white", linewidth=0.3, zorder=6, legend=False)
            else:
                has_data.plot(ax=ax, column=value_col, cmap=cmap,
                              vmin=vmin, vmax=vmax,
                              edgecolor="white", linewidth=0.3, zorder=6, legend=False)
        ax.set_title(str(facet), fontsize=style.label_size, fontweight="bold")

    for j in range(len(facets), len(axes)):
        axes[j].set_visible(False)

    sm = plt.cm.ScalarMappable(
        cmap=cmap,
        norm=LogNorm(vmin=max(vmin, 1), vmax=vmax) if log_scale else Normalize(vmin=vmin, vmax=vmax),
    )
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=list(axes), shrink=0.5, pad=0.02)
    cbar.set_label(value_col, fontsize=style.label_size)

    if title:
        fig.suptitle(title, fontsize=style.title_size, fontweight="bold", y=0.995)
    draw_credits(fig, style, note=note)
    _save_figure(fig, output, style)


def plot_layered(
    spec: dict, output: str, *,
    region: str = "world",
    projection: str = "auto",
    title: str | None = None,
    subtitle: str | None = None,
    style: MapStyle | None = None,
    resolution: str = "auto",
    note: str | None = None,
    figsize: tuple | None = None,
) -> None:
    """Compose multiple layers on a single map.

    spec example:
      {
        "layers": [
          {"type": "choropleth", "csv": "country_n.csv", "value_col": "n",
           "cmap": "YlOrRd", "log_scale": true, "legend_title": "Strains"},
          {"type": "points", "csv": "samples.csv", "lat_col": "lat",
           "lon_col": "lon", "group_col": "lineage"},
          {"type": "arcs", "csv": "flows.csv", "weight_col": "n"}
        ]
      }
    """
    style = style or MapStyle()
    proj = resolve_projection(projection, region)
    fig, ax = setup_figure(style, figsize)
    countries_proj = draw_base_layers(ax, region, proj, style, resolution=resolution)

    legend_handles_per_group: list[tuple[str, list]] = []

    for layer in spec.get("layers", []):
        lt = layer["type"]
        df = pd.read_csv(layer["csv"])

        if lt == "choropleth":
            merged = merge_data(load_world(REGION_DEFAULT_RES.get(region, "110m")), df)
            merged = merged[merged.geometry.notna()].to_crs(proj)
            merged = crop_to_extent_proj(merged, region, proj)
            value_col = layer.get("value_col", "n")
            has = merged[merged[value_col].notna()]
            if not has.empty:
                cmap = layer.get("cmap", "YlOrRd")
                if layer.get("log_scale"):
                    norm = LogNorm(vmin=max(has[value_col].min(), 1),
                                   vmax=has[value_col].max())
                    has.plot(ax=ax, column=value_col, cmap=cmap, norm=norm,
                             edgecolor="white", linewidth=0.4, zorder=6,
                             legend=True,
                             legend_kwds={"label": layer.get("legend_title", value_col),
                                          "shrink": 0.55, "pad": 0.02})
                else:
                    has.plot(ax=ax, column=value_col, cmap=cmap,
                             edgecolor="white", linewidth=0.4, zorder=6,
                             legend=True,
                             legend_kwds={"label": layer.get("legend_title", value_col),
                                          "shrink": 0.55, "pad": 0.02})
        elif lt == "points":
            lat_col = layer.get("lat_col", "lat")
            lon_col = layer.get("lon_col", "lon")
            df = df.dropna(subset=[lat_col, lon_col])
            pts = gpd.GeoDataFrame(
                df, geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
                crs="EPSG:4326",
            ).to_crs(proj)
            palette = layer.get("palette", MTBC_PALETTE)
            group_col = layer.get("group_col")
            value_col = layer.get("value_col")
            ms_base = layer.get("marker_size", 25)
            if value_col and value_col in df.columns:
                vmax = max(df[value_col].max(), 1)
                sizes = ms_base + (df[value_col].astype(float) / vmax) * (layer.get("max_size", 200) - ms_base)
            else:
                sizes = np.full(len(df), ms_base)
            if group_col and group_col in df.columns:
                groups_layer = sorted(df[group_col].unique())
                resolved_layer = resolve_palette(groups_layer, palette)
                colors = [resolved_layer[g] for g in df[group_col]]
                ax.scatter(pts.geometry.x, pts.geometry.y, s=sizes,
                           c=colors, alpha=layer.get("alpha", 0.85),
                           edgecolors="white", linewidth=0.6, zorder=8)
                handles = [plt.scatter([], [], s=ms_base, c=resolved_layer[g],
                                       alpha=layer.get("alpha", 0.85),
                                       edgecolors="white", linewidth=0.6, label=str(g))
                           for g in groups_layer]
                legend_handles_per_group.append((layer.get("legend_title", group_col), handles))
            else:
                ax.scatter(pts.geometry.x, pts.geometry.y, s=sizes,
                           c=layer.get("color", "#E03D31"),
                           alpha=layer.get("alpha", 0.85),
                           edgecolors="white", linewidth=0.6, zorder=8)
        elif lt == "arcs":
            sc = layer.get("src_lat_col", "src_lat"); slo = layer.get("src_lon_col", "src_lon")
            dc = layer.get("dst_lat_col", "dst_lat"); dlo = layer.get("dst_lon_col", "dst_lon")
            df = df.dropna(subset=[sc, slo, dc, dlo])
            wcol = layer.get("weight_col")
            if wcol and wcol in df.columns:
                w = df[wcol].astype(float).values
                widths = layer.get("min_width", 0.5) + (w / max(w.max(), 1)) * (
                    layer.get("max_width", 3.0) - layer.get("min_width", 0.5))
            else:
                widths = np.full(len(df), 1.5)
            src = gpd.GeoSeries.from_xy(df[slo], df[sc], crs="EPSG:4326").to_crs(proj)
            dst = gpd.GeoSeries.from_xy(df[dlo], df[dc], crs="EPSG:4326").to_crs(proj)
            for i in range(len(df)):
                ax.annotate(
                    "", xy=(dst.x.iloc[i], dst.y.iloc[i]),
                    xytext=(src.x.iloc[i], src.y.iloc[i]),
                    arrowprops=dict(
                        arrowstyle="->", color=layer.get("color", "#D0021B"),
                        lw=widths[i], alpha=layer.get("alpha", 0.6),
                        connectionstyle="arc3,rad=0.2",
                    ), zorder=9,
                )

    # Place additional group legends.
    # Si une legende a > 6 handles, on la place hors carte (a droite) pour
    # eviter qu'elle ne masque la geographie.
    side_legends_placed = 0
    for i, (title_, handles) in enumerate(legend_handles_per_group):
        if len(handles) > 6:
            # legend hors carte (decalee pour empiler plusieurs)
            offset = 1.02 + side_legends_placed * 0.16
            styled_legend(ax, handles, title=title_, loc="center left",
                          fontsize=style.label_size - 1,
                          title_fontsize=style.label_size,
                          bbox_to_anchor=(offset, 0.5))
            side_legends_placed += 1
        else:
            loc = ["lower left", "lower right", "upper left"][i % 3]
            styled_legend(ax, handles, title=title_, loc=loc,
                          fontsize=style.label_size,
                          title_fontsize=style.label_size)

    draw_graticule(ax, region, proj)
    if region != "world":
        draw_scale_bar(ax, region, proj, style)
        draw_north_arrow(ax, region, proj, style)
    draw_title_block(fig, title, subtitle, style)
    draw_credits(fig, style, note=note)
    _save_figure(fig, output, style)


# ----------------------------------------------------------------------
# Extension: cities, hillshade, tropics, smart labels, insets, animation
# ----------------------------------------------------------------------

def draw_cities(
    ax: plt.Axes,
    region: str,
    projection_crs: str,
    style: MapStyle,
    resolution: str = "auto",
    min_pop: int = 1_000_000,
    max_cities: int = 40,
    label: bool = True,
) -> None:
    if resolution == "auto":
        resolution = REGION_DEFAULT_RES.get(region, "110m")
    try:
        cities = load_layer("cities", resolution)
    except Exception as e:
        _log(f"Cities layer skipped: {e}")
        return
    pop_col = None
    for c in ("POP_MAX", "POP_MIN", "pop_max", "POP_OTHER"):
        if c in cities.columns:
            pop_col = c
            break
    if pop_col is None:
        _log("Cities layer has no POP column; skipping")
        return
    cities = cities[cities[pop_col].fillna(0) >= min_pop]
    extent_ll = parse_extent(region)
    cities = crop_to_extent(cities, extent_ll)
    if cities.empty:
        return
    cities = cities.sort_values(pop_col, ascending=False).head(max_cities)
    cities_proj = cities.to_crs(projection_crs)

    sizes = np.clip(np.sqrt(cities[pop_col].fillna(0).astype(float) / 1e6) * 18,
                    6, 60)
    ax.scatter(cities_proj.geometry.x, cities_proj.geometry.y,
               s=sizes, marker="o", facecolor="#222222",
               edgecolor="white", linewidth=0.6, zorder=9)

    if label:
        name_col = None
        for c in ("NAME", "name", "NAMEASCII"):
            if c in cities.columns:
                name_col = c
                break
        if name_col is None:
            return
        for i, row in cities_proj.iterrows():
            ax.annotate(
                str(row[name_col]),
                xy=(row.geometry.x, row.geometry.y),
                xytext=(5, 4), textcoords="offset points",
                fontsize=style.note_size, color="#222222", zorder=10,
                path_effects=[withStroke(linewidth=2, foreground="white")],
            )


def draw_biomes(
    ax: plt.Axes,
    region: str,
    projection_crs: str,
    style: MapStyle,
    alpha: float = 0.16,
    show_labels: bool = True,
) -> None:
    """Approximate climate biomes by latitude bands (pedagogical, not Köppen).

    Tropical (|lat| <= 23.4), Subtropical/Arid (23.4 < |lat| <= 35),
    Temperate (35 < |lat| <= 60), Polar (|lat| > 60).
    """
    bands = [
        (-90,    -60,   "#D9E8F3", "Polar (S)"),
        (-60,    -35,   "#BBD6E8", "Temperate (S)"),
        (-35,    -23.4, "#F0D88A", "Arid/Subtropical (S)"),
        (-23.4,   23.4, "#9CD3A8", "Tropical"),
        ( 23.4,   35,   "#F0D88A", "Arid/Subtropical (N)"),
        ( 35,     60,   "#BBD6E8", "Temperate (N)"),
        ( 60,     90,   "#D9E8F3", "Polar (N)"),
    ]
    lon_min, lat_min, lon_max, lat_max = parse_extent(region)
    n = 60
    for lo, hi, color, label in bands:
        if hi <= lat_min or lo >= lat_max:
            continue
        lo_eff = max(lo, lat_min)
        hi_eff = min(hi, lat_max)
        lats = np.linspace(lo_eff, hi_eff, 12)
        lons = np.linspace(lon_min, lon_max, n)
        # Build a polygon by tracing top edge then bottom edge in lon/lat
        top_lon = list(lons)
        top_lat = [hi_eff] * n
        bot_lon = list(reversed(lons))
        bot_lat = [lo_eff] * n
        # Subdivide along sides too (for projection accuracy)
        side_n = max(len(lats), 4)
        right_lat = list(np.linspace(hi_eff, lo_eff, side_n))
        right_lon = [lon_max] * side_n
        left_lat = list(np.linspace(lo_eff, hi_eff, side_n))
        left_lon = [lon_min] * side_n
        poly_lon = top_lon + right_lon + bot_lon + left_lon
        poly_lat = top_lat + right_lat + bot_lat + left_lat
        poly = gpd.GeoSeries.from_xy(poly_lon, poly_lat, crs="EPSG:4326").to_crs(projection_crs)
        from matplotlib.patches import Polygon as MplPolygon
        verts = list(zip(poly.x, poly.y))
        patch = MplPolygon(verts, closed=True, facecolor=color,
                           edgecolor="none", alpha=alpha, zorder=1.5)
        ax.add_patch(patch)
        if show_labels:
            mid_lat = (lo_eff + hi_eff) / 2
            label_pt = gpd.GeoSeries([Point(lon_max - (lon_max - lon_min) * 0.02, mid_lat)],
                                     crs="EPSG:4326").to_crs(projection_crs)
            ax.text(
                float(label_pt.x.iloc[0]), float(label_pt.y.iloc[0]),
                label.replace(" (S)", "").replace(" (N)", ""),
                fontsize=style.note_size, color="#4A5C66",
                ha="right", va="center", zorder=2,
                alpha=0.85,
                path_effects=[withStroke(linewidth=1.5, foreground="white")],
            )


def draw_climate_raster(
    ax: plt.Axes,
    region: str,
    projection_crs: str,
    raster_path: str,
    alpha: float = 0.45,
) -> None:
    """Overlay a user-provided Köppen-Geiger raster (TIF/PNG).

    Expects a 5-class simplified map (A=Tropical, B=Arid, C=Temperate,
    D=Continental, E=Polar) or a full Beck et al. 2018 Köppen raster (1-30).
    The image is assumed to cover -180..180 / -90..90 in PlateCarrée.
    """
    try:
        from PIL import Image
    except ImportError:
        _log("Climate raster requires Pillow; skipping")
        return
    path = Path(raster_path)
    if not path.exists():
        _log(f"Climate raster not found: {raster_path}")
        return
    try:
        img = Image.open(path)
    except Exception as e:
        _log(f"Cannot open climate raster {path}: {e}")
        return
    # Build palette for 5-class or Köppen 1-30 → 5-class collapse
    KG_TO_CLASS = {}
    for k in (1, 2, 3):                                       KG_TO_CLASS[k] = 0  # Tropical
    for k in (4, 5, 6, 7):                                    KG_TO_CLASS[k] = 1  # Arid
    for k in range(8, 17):                                    KG_TO_CLASS[k] = 2  # Temperate
    for k in range(17, 29):                                   KG_TO_CLASS[k] = 3  # Continental
    for k in (29, 30):                                        KG_TO_CLASS[k] = 4  # Polar
    KG_COLORS = ["#9CD3A8", "#F0D88A", "#BBD6E8", "#C8B6D9", "#D9E8F3"]

    arr = np.array(img.convert("L"))
    H, W = arr.shape
    out = np.full((H, W, 4), 0, dtype=np.uint8)
    for raw, idx in KG_TO_CLASS.items():
        mask = (arr == raw)
        if not mask.any():
            continue
        rgba = matplotlib.colors.to_rgba(KG_COLORS[idx])
        out[mask] = [int(c * 255) for c in rgba[:3]] + [int(alpha * 255)]
    extent_ll = parse_extent(region)
    lon_min, lat_min, lon_max, lat_max = extent_ll
    px_lon_min = int((lon_min + 180) / 360 * W)
    px_lon_max = int((lon_max + 180) / 360 * W)
    px_lat_min = int((90 - lat_max) / 180 * H)
    px_lat_max = int((90 - lat_min) / 180 * H)
    crop = out[max(0, px_lat_min):min(H, px_lat_max),
               max(0, px_lon_min):min(W, px_lon_max)]
    xmin, ymin, xmax, ymax = project_extent_to_axes(extent_ll, projection_crs)
    ax.imshow(crop, extent=[xmin, xmax, ymin, ymax],
              origin="upper", zorder=1.5, interpolation="nearest")


def draw_tropics(
    ax: plt.Axes,
    region: str,
    projection_crs: str,
    style: MapStyle,
    show_labels: bool = True,
) -> None:
    lon_min, lat_min, lon_max, lat_max = parse_extent(region)
    n = 80
    for name, lat in TROPICS.items():
        if not (lat_min <= lat <= lat_max):
            continue
        line = gpd.GeoSeries.from_xy(
            np.linspace(lon_min, lon_max, n), [lat] * n, crs="EPSG:4326",
        ).to_crs(projection_crs)
        ls = "--" if "Equator" not in name else ":"
        ax.plot(line.x, line.y, color="#5E7A8C", linewidth=0.6,
                linestyle=ls, alpha=0.7, zorder=2)
        if show_labels:
            label_pt = gpd.GeoSeries.from_xy(
                [lon_max - (lon_max - lon_min) * 0.02], [lat],
                crs="EPSG:4326",
            ).to_crs(projection_crs)
            ax.text(float(label_pt.x.iloc[0]), float(label_pt.y.iloc[0]),
                    name, fontsize=style.note_size, color="#5E7A8C",
                    ha="right", va="bottom", zorder=2,
                    path_effects=[withStroke(linewidth=2, foreground="white")])


def draw_hillshade(
    ax: plt.Axes,
    region: str,
    projection_crs: str,
    resolution: str = "auto",
    alpha: float = 0.35,
) -> None:
    """Render Natural Earth grayscale shaded relief as a hillshade background.

    Downloads GRAY_*_SR raster if not cached. Best at 50m for regional maps.
    """
    try:
        from PIL import Image
    except ImportError:
        _log("Hillshade requires Pillow; skipping")
        return
    if resolution == "auto":
        resolution = REGION_DEFAULT_RES.get(region, "50m")
        if resolution == "110m":
            resolution = "50m"
    # Natural Earth ships grayscale shaded relief as e.g. GRAY_50M_SR.zip,
    # GRAY_LR_SR.zip (low-res for 110m equivalent), GRAY_HR_SR.zip (10m).
    if resolution == "10m":
        zip_name = "GRAY_HR_SR"
    elif resolution == "50m":
        zip_name = "GRAY_50M_SR"
    else:
        zip_name = "GRAY_LR_SR"
    cache_subdir = NE_CACHE_DIR / zip_name
    tif_paths = list(cache_subdir.rglob("*.tif")) if cache_subdir.exists() else []
    if not tif_paths:
        url = f"https://naciscdn.org/naturalearth/{resolution}/raster/{zip_name}.zip"
        cache_subdir.mkdir(parents=True, exist_ok=True)
        try:
            _log(f"Downloading hillshade {url} ...")
            req = urllib.request.Request(
                url, headers={"User-Agent": "geo_map.py/1.0"},
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = resp.read()
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                zf.extractall(cache_subdir)
        except Exception as e:
            _log(f"Hillshade download failed ({e}); skipping")
            return
        tif_paths = list(cache_subdir.rglob("*.tif"))
        if not tif_paths:
            _log("Hillshade extraction yielded no TIF; skipping")
            return
    tif_path = tif_paths[0]

    try:
        img = Image.open(tif_path).convert("L")
    except Exception as e:
        _log(f"Cannot open hillshade {tif_path}: {e}")
        return

    extent_ll = parse_extent(region)
    lon_min, lat_min, lon_max, lat_max = extent_ll
    # The Natural Earth SR rasters cover -180..180 / -90..90 in PlateCarrée
    w, h = img.size
    px_lon_min = int((lon_min + 180) / 360 * w)
    px_lon_max = int((lon_max + 180) / 360 * w)
    px_lat_min = int((90 - lat_max) / 180 * h)
    px_lat_max = int((90 - lat_min) / 180 * h)
    crop = img.crop((max(0, px_lon_min), max(0, px_lat_min),
                     min(w, px_lon_max), min(h, px_lat_max)))
    arr = np.array(crop)

    # Render the raster in PlateCarrée coordinates, then warp via projection
    # by sampling. To keep things simple here we use imshow on a regular grid
    # in lon/lat and reproject corners. This is approximate but visually good.
    # For accurate reprojection, use rasterio; we keep deps light.
    xmin, ymin, xmax, ymax = project_extent_to_axes(extent_ll, projection_crs)
    ax.imshow(
        arr, cmap="gray", extent=[xmin, xmax, ymin, ymax],
        origin="upper", alpha=alpha, zorder=0.5, interpolation="bilinear",
    )


def smart_label_placement(
    ax: plt.Axes,
    points: list[tuple[float, float, str]],
    style: MapStyle,
    mode: str = "fast",
) -> None:
    """Greedy non-overlapping label placement.

    `points` is a list of (x_proj, y_proj, text) in axes data coordinates.
    """
    if not points:
        return
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    placed_bboxes: list = []
    offsets = [(8, 4), (-8, 4), (8, -4), (-8, -4),
               (0, 10), (0, -10), (14, 0), (-14, 0),
               (12, 8), (-12, -8), (12, -8), (-12, 8)]

    iterations = 1 if mode == "fast" else 3

    for x, y, text in points:
        chosen = None
        for _ in range(iterations):
            for dx, dy in offsets:
                t = ax.annotate(
                    text, xy=(x, y),
                    xytext=(dx, dy), textcoords="offset points",
                    fontsize=style.note_size, color="black", zorder=11,
                    ha="left" if dx >= 0 else "right",
                    va="bottom" if dy >= 0 else "top",
                    path_effects=[withStroke(linewidth=2, foreground="white")],
                )
                bb = t.get_window_extent(renderer=renderer)
                overlap = any(bb.overlaps(b) for b in placed_bboxes)
                if not overlap:
                    placed_bboxes.append(bb)
                    chosen = t
                    break
                t.remove()
            if chosen is not None:
                break
        if chosen is None:
            # Fallback: place anyway with the first offset
            dx, dy = offsets[0]
            t = ax.annotate(
                text, xy=(x, y),
                xytext=(dx, dy), textcoords="offset points",
                fontsize=style.note_size, color="black", zorder=11,
                ha="left", va="bottom",
                path_effects=[withStroke(linewidth=2, foreground="white")],
            )
            placed_bboxes.append(t.get_window_extent(renderer=renderer))


def _resolve_inset_countries(
    insets_arg: str, data_countries: Iterable[str] | None = None,
) -> list[str]:
    if insets_arg in ("none", "", None):
        return []
    if insets_arg == "auto":
        if data_countries is None:
            return []
        out = []
        for c in data_countries:
            cn = normalize_country(c)
            if cn in SMALL_COUNTRY_INSETS:
                out.append(cn)
        return out
    out = []
    for raw in insets_arg.split(","):
        cn = normalize_country(raw.strip())
        if cn in SMALL_COUNTRY_INSETS:
            out.append(cn)
        else:
            _log(f"Inset country '{raw}' unknown — skipped")
    return out


def draw_insets(
    fig: plt.Figure,
    main_ax: plt.Axes,
    countries_unproj: gpd.GeoDataFrame,
    data_layer: gpd.GeoDataFrame | None,
    value_col: str | None,
    inset_names: list[str],
    style: MapStyle,
    cmap: str = "YlOrRd",
    vmin: float | None = None,
    vmax: float | None = None,
    log_scale: bool = False,
    palette: dict | None = None,
    group_col: str | None = None,
    numbered: bool = False,
    main_projection_crs: str | None = None,
) -> None:
    """Draw small inset axes for each country in inset_names."""
    if not inset_names:
        return
    # Force 50m resolution for inset countries (small features need finer geometry)
    try:
        countries_unproj = load_world("50m")
    except Exception as e:
        _log(f"Inset 50m load failed ({e}); using existing resolution")
    n = len(inset_names)
    inset_w = 0.10
    inset_h = 0.10
    gap = 0.012
    total_w = n * inset_w + (n - 1) * gap
    x0 = max(0.02, (1 - total_w) / 2)
    y0 = 0.02

    for i, name in enumerate(inset_names):
        bbox = SMALL_COUNTRY_INSETS.get(name)
        if bbox is None:
            continue
        ax_in = fig.add_axes([x0 + i * (inset_w + gap), y0, inset_w, inset_h])
        proj = "EPSG:3857"
        sub_country = countries_unproj[countries_unproj["name"] == name]
        if sub_country.empty:
            # DOM/TOM or other territory integrated in a larger country's
            # multipolygon: clip whichever country intersects the bbox.
            bx_min0, by_min0, bx_max0, by_max0 = bbox
            bbox_poly = box(bx_min0, by_min0, bx_max0, by_max0)
            sub_country = countries_unproj[countries_unproj.geometry.intersects(bbox_poly)].copy()
            if not sub_country.empty:
                sub_country.geometry = sub_country.geometry.intersection(bbox_poly)
                sub_country = sub_country[~sub_country.geometry.is_empty]
        if sub_country.empty:
            ax_in.set_visible(False)
            continue
        sub_proj = sub_country.to_crs(proj)
        # Background ocean
        bx_min, bx_max = bbox[0], bbox[2]
        by_min, by_max = bbox[1], bbox[3]
        rect_pts = gpd.GeoSeries([Point(bx_min, by_min), Point(bx_max, by_max)],
                                 crs="EPSG:4326").to_crs(proj)
        x_min_p, y_min_p = float(rect_pts.x.iloc[0]), float(rect_pts.y.iloc[0])
        x_max_p, y_max_p = float(rect_pts.x.iloc[1]), float(rect_pts.y.iloc[1])
        ax_in.add_patch(plt.Rectangle(
            (x_min_p, y_min_p), x_max_p - x_min_p, y_max_p - y_min_p,
            facecolor=style.ocean, edgecolor="none", zorder=0))
        sub_proj.plot(ax=ax_in, color=style.land, edgecolor=style.border,
                      linewidth=0.4, zorder=1)
        if data_layer is not None and value_col is not None:
            data_sub = data_layer[data_layer["name"] == name]
            if not data_sub.empty and data_sub[value_col].notna().any():
                if log_scale:
                    norm = LogNorm(vmin=max(vmin or 1, 1), vmax=vmax or data_sub[value_col].max())
                    data_sub.to_crs(proj).plot(
                        ax=ax_in, column=value_col, cmap=cmap, norm=norm,
                        edgecolor="white", linewidth=0.4, zorder=2)
                else:
                    data_sub.to_crs(proj).plot(
                        ax=ax_in, column=value_col, cmap=cmap,
                        vmin=vmin, vmax=vmax,
                        edgecolor="white", linewidth=0.4, zorder=2)
        ax_in.set_xlim(x_min_p, x_max_p)
        ax_in.set_ylim(y_min_p, y_max_p)
        ax_in.set_xticks([])
        ax_in.set_yticks([])
        for spine in ax_in.spines.values():
            spine.set_edgecolor("#666666")
            spine.set_linewidth(0.6)
        inset_title = f"{i+1}. {name}" if numbered else name
        ax_in.set_title(inset_title, fontsize=style.note_size,
                        fontweight="bold", pad=2)

        # If numbered, draw a marker + index on the main map at the territory's
        # location (centroid of the bbox), with halo, so the reader can locate it.
        if numbered and main_projection_crs is not None:
            cx_ll = (bbox[0] + bbox[2]) / 2
            cy_ll = (bbox[1] + bbox[3]) / 2
            p = gpd.GeoSeries([Point(cx_ll, cy_ll)],
                              crs="EPSG:4326").to_crs(main_projection_crs)
            xm = float(p.x.iloc[0]); ym = float(p.y.iloc[0])
            xlim = main_ax.get_xlim(); ylim = main_ax.get_ylim()
            if xlim[0] <= xm <= xlim[1] and ylim[0] <= ym <= ylim[1]:
                main_ax.scatter(
                    [xm], [ym], s=70, marker="o",
                    facecolor="white", edgecolor="black",
                    linewidth=0.8, zorder=11,
                )
                main_ax.text(
                    xm, ym, str(i + 1),
                    ha="center", va="center",
                    fontsize=style.note_size, fontweight="bold",
                    color="black", zorder=12,
                )


def _apply_pre_decorations(
    ax: plt.Axes, region: str, projection_crs: str,
    resolution: str, decorations: Decorations | None,
) -> None:
    if decorations is None:
        return
    if decorations.hillshade:
        draw_hillshade(ax, region, projection_crs, resolution=resolution)


def _apply_post_decorations(
    fig: plt.Figure, ax: plt.Axes, region: str, projection_crs: str,
    style: MapStyle, decorations: Decorations | None,
    countries_unproj: gpd.GeoDataFrame | None = None,
    data_layer: gpd.GeoDataFrame | None = None,
    value_col: str | None = None,
    cmap: str = "YlOrRd",
    log_scale: bool = False,
    vmin: float | None = None,
    vmax: float | None = None,
    df: pd.DataFrame | None = None,
) -> None:
    """data_layer is expected to be in EPSG:4326 (unprojected) and contain
    a 'name' column matching world['name']. Reprojection happens inside this
    function as needed."""
    if decorations is None:
        return
    if decorations.show_biomes:
        draw_biomes(ax, region, projection_crs, style)
    if decorations.climate_raster:
        draw_climate_raster(ax, region, projection_crs,
                            decorations.climate_raster)
    if decorations.show_tropics:
        draw_tropics(ax, region, projection_crs, style)
    if decorations.show_cities:
        draw_cities(ax, region, projection_crs, style,
                    min_pop=decorations.min_pop)
    if decorations.smart_labels != "none" and data_layer is not None and value_col is not None:
        thr = decorations.label_threshold
        has_data = data_layer[data_layer[value_col].notna()]
        if not has_data.empty:
            if thr is None:
                thr = has_data[value_col].quantile(0.5)
            picked = has_data[has_data[value_col] >= thr]
            picked_proj = picked.to_crs(projection_crs)
            pts = []
            for _, row in picked_proj.iterrows():
                if row.geometry is None or row.geometry.is_empty:
                    continue
                c = row.geometry.centroid
                pts.append((c.x, c.y, str(row["name"])))
            smart_label_placement(ax, pts, style, mode=decorations.smart_labels)
    if decorations.insets and decorations.insets != "none":
        if countries_unproj is None:
            return
        if df is not None and "country" in df.columns:
            inset_names = _resolve_inset_countries(decorations.insets,
                                                   df["country"].tolist())
        else:
            inset_names = _resolve_inset_countries(decorations.insets)
        draw_insets(fig, ax, countries_unproj, data_layer, value_col,
                    inset_names, style, cmap=cmap, vmin=vmin, vmax=vmax,
                    log_scale=log_scale,
                    numbered=decorations.insets_numbered,
                    main_projection_crs=projection_crs)


# ----------------------------------------------------------------------
# Animation
# ----------------------------------------------------------------------

def animate_choropleth(
    df: pd.DataFrame, value_col: str, frame_col: str, output: str, *,
    region: str = "world",
    projection: str = "auto",
    cmap: str = "YlOrRd",
    title: str | None = None,
    subtitle_template: str = "{frame}",
    legend_title: str | None = None,
    log_scale: bool = False,
    vmin: float | None = None,
    vmax: float | None = None,
    style: MapStyle | None = None,
    resolution: str = "auto",
    fps: int = 2,
    decorations: Decorations | None = None,
    note: str | None = None,
) -> None:
    """Animate a choropleth by iterating over distinct values of frame_col.

    Output extension determines format: .gif (Pillow), .mp4 (ffmpeg).
    """
    import tempfile
    style = style or MapStyle()
    proj = resolve_projection(projection, region)
    frames = sorted(df[frame_col].unique())
    if not frames:
        _log("Animation: no frames found")
        return

    if vmin is None:
        vmin = df[value_col].min()
    if vmax is None:
        vmax = df[value_col].max()

    out = Path(output)
    fmt = out.suffix.lower().lstrip(".")
    if fmt not in ("gif", "mp4"):
        _log(f"Unknown animation format '{fmt}', defaulting to gif")
        fmt = "gif"
        out = out.with_suffix(".gif")

    tmpdir = Path(tempfile.mkdtemp(prefix="geo_map_anim_"))
    frame_paths = []
    for f in frames:
        fdf = df[df[frame_col] == f]
        frame_out = tmpdir / f"frame_{f}.png"
        plot_choropleth(
            fdf, value_col, str(frame_out),
            region=region, projection=projection, cmap=cmap,
            title=title,
            subtitle=subtitle_template.format(frame=f),
            legend_title=legend_title, log_scale=log_scale,
            vmin=vmin, vmax=vmax,
            style=style, resolution=resolution,
            decorations=decorations, note=note,
        )
        frame_paths.append(frame_out)

    if fmt == "gif":
        from PIL import Image
        imgs = [Image.open(p) for p in frame_paths]
        imgs[0].save(
            out, save_all=True, append_images=imgs[1:],
            duration=int(1000 / fps), loop=0, optimize=True,
        )
        _log(f"Saved animation {out} ({len(imgs)} frames, {fps} fps)")
    else:  # mp4 via ffmpeg
        import subprocess
        cmd = [
            "ffmpeg", "-y", "-framerate", str(fps),
            "-i", str(tmpdir / "frame_%*.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            str(out),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            _log(f"ffmpeg failed: {proc.stderr[:300]}")
        else:
            _log(f"Saved animation {out}")

    # Cleanup tmpdir
    for p in frame_paths:
        try:
            p.unlink()
        except Exception:
            pass
    try:
        tmpdir.rmdir()
    except Exception:
        pass


# ----------------------------------------------------------------------
# Saving
# ----------------------------------------------------------------------

def _save_figure(fig: plt.Figure, output: str, style: MapStyle) -> None:
    fig.subplots_adjust(top=0.88, bottom=0.06, left=0.03, right=0.97)
    out = Path(output)
    if out.suffix.lower() == ".tex":
        try:
            import tikzplotlib
            tikzplotlib.save(
                str(out), figure=fig,
                axis_width=f"{style.width_mm}mm",
                axis_height=f"{style.height_mm}mm",
                strict=False,
                wrap=True,
            )
            _log(f"Saved {out} (TikZ; hillshade/raster overlays not exported)")
        except ImportError:
            fallback = out.with_suffix(".pdf")
            _log("tikzplotlib not installed — falling back to PDF. "
                 "Install with: pip install tikzplotlib")
            fig.savefig(fallback, dpi=style.dpi, bbox_inches="tight",
                        facecolor="white", edgecolor="none", pad_inches=0.15)
            _log(f"Saved {fallback} ({style.dpi} dpi, {style.preset})")
        except Exception as e:
            fallback = out.with_suffix(".pdf")
            _log(f"TikZ export failed ({e}) — falling back to PDF")
            fig.savefig(fallback, dpi=style.dpi, bbox_inches="tight",
                        facecolor="white", edgecolor="none", pad_inches=0.15)
            _log(f"Saved {fallback} ({style.dpi} dpi, {style.preset})")
    else:
        fig.savefig(out, dpi=style.dpi, bbox_inches="tight",
                    facecolor="white", edgecolor="none", pad_inches=0.15)
        _log(f"Saved {out} ({style.dpi} dpi, {style.preset})")
    plt.close(fig)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(
        description="Publication-quality geographic maps for MTBC studies.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Choropleth (Robinson projection on world)
  geo_map.py countries.csv -t choropleth -v n -o map.pdf --preset nature_double

  # Pie chart map (Africa, Albers projection)
  geo_map.py composition.csv -t pie -g lineage --region africa -o pie.pdf

  # Bubble map
  geo_map.py countries.csv -t bubble -v n --region asia -o bubble.png

  # GPS points (lat/lon)
  geo_map.py samples.csv -t points --lat-col lat --lon-col lon \\
      --group-column lineage --region southeast_asia -o samples.pdf

  # Phylogeographic arcs
  geo_map.py flows.csv -t arcs --weight-column n -o flows.pdf

  # Layered composition (choropleth + points + arcs)
  geo_map.py spec.json -t layered -o composite.pdf

  # Multi-panel atlas
  geo_map.py data.csv -t choropleth --facet-column lineage --ncols 3 \\
      --preset nature_double -o atlas.pdf
""",
    )
    p.add_argument("input_file", help="CSV or (for type=layered) JSON spec.")
    p.add_argument("-t", "--type",
                   choices=["choropleth", "gradient", "bubble", "pie",
                            "points", "arcs", "layered"],
                   default="choropleth")
    p.add_argument("-v", "--value-column", default="n")
    p.add_argument("-g", "--group-column")
    p.add_argument("--country-column", default="country")
    p.add_argument("--lat-col", default="lat")
    p.add_argument("--lon-col", default="lon")
    p.add_argument("--src-lat-col", default="src_lat")
    p.add_argument("--src-lon-col", default="src_lon")
    p.add_argument("--dst-lat-col", default="dst_lat")
    p.add_argument("--dst-lon-col", default="dst_lon")
    p.add_argument("--weight-column")
    p.add_argument("-r", "--region", default="world")
    p.add_argument("--projection", default="auto",
                   help="auto|robinson|mollweide|albers_africa|albers_europe|albers_asia|albers_americas|lambert_europe|lambert_us|equal_earth|mercator|platecarree|<EPSG/PROJ string>")
    p.add_argument("--resolution", default="auto",
                   choices=["auto", "110m", "50m", "10m"])
    p.add_argument("-c", "--cmap", default=None)
    p.add_argument("--title")
    p.add_argument("--subtitle")
    p.add_argument("--note")
    p.add_argument("--legend-title")
    p.add_argument("-o", "--output", default="map.png")
    p.add_argument("--preset",
                   choices=list(JOURNAL_PRESETS.keys()), default="generic")
    p.add_argument("--dpi", type=int, default=None)
    p.add_argument("--figsize")
    p.add_argument("--log-scale", action="store_true")
    p.add_argument("--show-labels", action="store_true")
    p.add_argument("--label-threshold", type=float)
    p.add_argument("--min-value", type=float, dest="vmin")
    p.add_argument("--max-value", type=float, dest="vmax")
    p.add_argument("--center", type=float, default=None,
                   help="Center for a diverging choropleth: auto-symmetrizes vmin/vmax "
                        "around this value (e.g. --center 0 with a diverging --cmap RdBu_r "
                        "for log-ratio / enrichment data). Ignored if --min/--max-value set.")
    p.add_argument("--sig-column", default=None,
                   help="CSV column (e.g. a Fisher p-value) used to mark significant "
                        "countries with a bold asterisk where value < --sig-threshold.")
    p.add_argument("--sig-threshold", type=float, default=0.05,
                   help="Threshold for --sig-column marking (default 0.05).")
    p.add_argument("--sig-style", default="asterisk",
                   choices=["asterisk", "hatch", "edge"],
                   help="How to mark significant countries: 'asterisk' (default), "
                        "'hatch' (diagonal hatching) or 'edge' (thick black outline). "
                        "A self-documenting legend vignette explaining the symbol is "
                        "added in-figure.")
    p.add_argument("--sig-legend-loc", default="lower left",
                   help="Corner for the significance legend vignette (matplotlib loc: "
                        "'lower left', 'lower right', 'upper left', 'upper right').")
    p.add_argument("--facet-column")
    p.add_argument("--ncols", type=int, default=2)
    p.add_argument("--palette",
                   help="JSON file/string with custom colors, or 'colorblind'")
    p.add_argument("--min-total", type=int, default=5)
    p.add_argument("--pie-scale", type=float, default=1.0)
    p.add_argument("--color", default="#E03D31")
    p.add_argument("--marker-size", type=float, default=25)
    p.add_argument("--max-size", type=float, default=250)
    p.add_argument("--alpha", type=float, default=0.85)
    p.add_argument("--jitter", type=float, default=0.0)
    p.add_argument("--min-width", type=float, default=0.5)
    p.add_argument("--max-width", type=float, default=3.0)

    # Extension decorations
    p.add_argument("--insets", default="none",
                   help="'none' | 'auto' (small countries in data) | comma-separated list")
    p.add_argument("--smart-labels", default="none",
                   choices=["none", "fast", "quality"],
                   help="Non-overlapping label placement for choropleth")
    p.add_argument("--show-cities", action="store_true",
                   help="Show major cities (Natural Earth populated_places)")
    p.add_argument("--min-pop", type=int, default=1_000_000,
                   help="Minimum population to display a city")
    p.add_argument("--hillshade", action="store_true",
                   help="Render Natural Earth shaded relief as background")
    p.add_argument("--show-tropics", action="store_true",
                   help="Draw Tropic of Cancer, Equator, Tropic of Capricorn")
    p.add_argument("--insets-numbered", action="store_true",
                   help="Number each inset and mark its location on the main map")
    p.add_argument("--show-biomes", action="store_true",
                   help="Overlay climate biomes approximated by latitude bands")
    p.add_argument("--climate-raster", default=None,
                   help="Path to a Köppen-Geiger raster (TIF/PNG) to overlay")

    # Animation
    p.add_argument("--animate-by", default=None,
                   help="Column to animate over (e.g. 'year'). Output extension picks format.")
    p.add_argument("--animate-fps", type=int, default=2)
    p.add_argument("--animate-subtitle", default="{frame}",
                   help="Subtitle template; {frame} is replaced by the current frame value")

    args = p.parse_args()

    style = MapStyle.from_preset(args.preset)
    if args.dpi:
        style.dpi = args.dpi

    figsize = None
    if args.figsize:
        figsize = tuple(float(x) for x in args.figsize.split(","))

    palette = MTBC_PALETTE
    if args.palette == "colorblind":
        palette = MTBC_PALETTE_CB
    elif args.palette:
        try:
            if Path(args.palette).exists():
                palette = json.loads(Path(args.palette).read_text())
            else:
                palette = json.loads(args.palette)
        except Exception as e:
            _log(f"Warning: invalid palette '{args.palette}' ({e})")

    cmap = args.cmap or ("Reds" if args.type == "gradient" else "YlOrRd")

    decorations = Decorations(
        insets=args.insets,
        insets_numbered=args.insets_numbered,
        smart_labels=args.smart_labels,
        label_threshold=args.label_threshold,
        show_cities=args.show_cities,
        min_pop=args.min_pop,
        hillshade=args.hillshade,
        show_tropics=args.show_tropics,
        show_biomes=args.show_biomes,
        climate_raster=args.climate_raster,
    )

    # Animation branch — overrides normal plotting for choropleth-like data
    if args.animate_by:
        if args.type not in ("choropleth", "gradient"):
            print(f"Error: --animate-by only supports choropleth/gradient.", file=sys.stderr)
            return 1
        df_anim = pd.read_csv(args.input_file)
        if args.country_column != "country" and args.country_column in df_anim.columns:
            df_anim = df_anim.rename(columns={args.country_column: "country"})
        animate_choropleth(
            df_anim, args.value_column, args.animate_by, args.output,
            region=args.region, projection=args.projection, cmap=cmap,
            title=args.title,
            subtitle_template=args.animate_subtitle,
            legend_title=args.legend_title,
            log_scale=args.log_scale, vmin=args.vmin, vmax=args.vmax,
            style=style, resolution=args.resolution,
            fps=args.animate_fps,
            decorations=decorations, note=args.note,
        )
        return 0

    if args.type == "layered":
        spec = json.loads(Path(args.input_file).read_text())
        plot_layered(
            spec, args.output,
            region=args.region, projection=args.projection,
            title=args.title, subtitle=args.subtitle, style=style,
            resolution=args.resolution, note=args.note, figsize=figsize,
        )
        return 0

    if args.type == "arcs":
        df = pd.read_csv(args.input_file)
        plot_arcs(
            df, args.output,
            src_lat_col=args.src_lat_col, src_lon_col=args.src_lon_col,
            dst_lat_col=args.dst_lat_col, dst_lon_col=args.dst_lon_col,
            weight_col=args.weight_column,
            region=args.region, projection=args.projection,
            color=args.color, title=args.title, subtitle=args.subtitle,
            style=style, resolution=args.resolution,
            min_width=args.min_width, max_width=args.max_width,
            alpha=args.alpha, note=args.note, figsize=figsize,
        )
        return 0

    df = pd.read_csv(args.input_file)
    if args.country_column != "country" and args.country_column in df.columns:
        df = df.rename(columns={args.country_column: "country"})

    if args.facet_column:
        if "country" not in df.columns:
            print("Error: 'country' column required.", file=sys.stderr)
            return 1
        plot_multi_panel(
            df, args.value_column, args.facet_column, args.output,
            ncols=args.ncols, region=args.region, projection=args.projection,
            cmap=cmap, title=args.title, style=style,
            log_scale=args.log_scale, resolution=args.resolution,
            note=args.note, figsize=figsize,
        )
        return 0

    if args.type == "points":
        plot_points(
            df, args.output,
            lat_col=args.lat_col, lon_col=args.lon_col,
            value_col=args.value_column if args.value_column in df.columns else None,
            group_col=args.group_column,
            region=args.region, projection=args.projection,
            palette=palette, color=args.color, cmap=cmap,
            title=args.title, subtitle=args.subtitle,
            legend_title=args.legend_title,
            style=style, resolution=args.resolution,
            marker_size=args.marker_size, max_size=args.max_size,
            alpha=args.alpha, jitter=args.jitter,
            note=args.note, figsize=figsize,
            decorations=decorations,
        )
        return 0

    if "country" not in df.columns:
        print("Error: 'country' column required.", file=sys.stderr)
        return 1

    if args.type == "pie":
        if not args.group_column:
            print("Error: --group-column required for pie maps.", file=sys.stderr)
            return 1
        plot_pie_map(
            df, args.group_column, args.output,
            region=args.region, projection=args.projection, palette=palette,
            title=args.title, subtitle=args.subtitle, style=style,
            resolution=args.resolution, min_total=args.min_total,
            pie_scale=args.pie_scale, note=args.note, figsize=figsize,
            legend_title=args.legend_title or "Lineage",
        )
        return 0

    if args.type == "bubble":
        plot_bubble(
            df, args.value_column, args.output,
            region=args.region, projection=args.projection, color=args.color,
            title=args.title, subtitle=args.subtitle,
            legend_title=args.legend_title,
            style=style, resolution=args.resolution,
            note=args.note, figsize=figsize,
        )
        return 0

    # choropleth / gradient
    plot_choropleth(
        df, args.value_column, args.output,
        region=args.region, projection=args.projection, cmap=cmap,
        title=args.title, subtitle=args.subtitle,
        legend_title=args.legend_title, log_scale=args.log_scale,
        vmin=args.vmin, vmax=args.vmax,
        center=args.center, sig_col=args.sig_column, sig_threshold=args.sig_threshold,
        sig_style=args.sig_style, sig_legend_loc=args.sig_legend_loc,
        show_labels=args.show_labels, label_threshold=args.label_threshold,
        style=style, resolution=args.resolution,
        note=args.note, figsize=figsize,
        decorations=decorations,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
