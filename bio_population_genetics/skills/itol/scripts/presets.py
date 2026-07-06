"""
MTBC export presets, comparison configurations, and legend definitions for iTOL.

Used by itol_pipeline.py to provide standardized, publication-ready export parameters.
"""

# --- Export presets ---
# Each preset maps to iTOL batch export API parameter names.

EXPORT_PRESETS = {
    "article": {
        "format": "svg",
        "display_mode": "2",  # circular
        "line_width": "2",
        "current_font_size": "12",
        "align_labels": "1",
        "dashed_lines": "1",
        "bootstrap_display": "1",
        "bootstrap_type": "2",  # symbols
        "bootstrap_slider_min": "70",
        "internal_scale": "1",
        "range_mode": "2",
        "include_ranges_legend": "1",
    },
    "supplement": {
        "format": "pdf",
        "display_mode": "1",  # rectangular
        "line_width": "1",
        "current_font_size": "10",
        "align_labels": "1",
        "bootstrap_display": "1",
        "bootstrap_type": "1",  # text
        "bootstrap_slider_min": "60",
    },
    "presentation": {
        "format": "png",
        "display_mode": "2",  # circular
        "line_width": "3",
        "current_font_size": "14",
        "align_labels": "1",
    },
    "poster": {
        "format": "svg",
        "display_mode": "2",  # circular
        "line_width": "2",
        "current_font_size": "16",
        "align_labels": "1",
        "bootstrap_display": "1",
        "bootstrap_type": "2",  # symbols
        "bootstrap_slider_min": "80",
    },
}

# --- Comparison configurations ---
# datasets_visible indices are 0-based, matching the upload order:
#   0 = tree_colors, 1 = lineage_strip, 2 = country_strip,
#   3 = dr_status_strip, 4 = dr_binary, 5 = thd20_bars, 6 = thd150_bars

COMPARISON_CONFIGS = {
    "lineage_overview": {
        "label": "Lineage Overview",
        "datasets_visible": "0,1",
        "suffix": "lineage",
    },
    "dr_profile": {
        "label": "Drug Resistance",
        "datasets_visible": "0,1,2,3,4",
        "suffix": "dr",
    },
    "phylogeography": {
        "label": "Phylogeography",
        "datasets_visible": "0,1,2,5,6",
        "suffix": "phylogeo",
    },
    "epidemiology": {
        "label": "Epidemiology (THD)",
        "datasets_visible": "0,1,5,6",
        "suffix": "epi",
    },
}

# --- MTBC legend definitions ---
# Format compatible with iTOL batch export legend parameters.
# legend_shapes: 1=square, 2=circle, 3=star

MTBC_LEGENDS = {
    "lineage": {
        "legend_title": "MTBC Lineage",
        "legend_shapes": "1,1,1,1,1,1,1,1,1,1",
        "legend_colors": (
            "#F5A623,#D0021B,#4A90D9,#E03D31,"
            "#7B2D8E,#9B59B6,#B8860B,#1B9AAA,#2D6A4F,#52B788"
        ),
        "legend_labels": "L1,L2,L3,L4,L5,L6,L7,L8,L9,L10",
    },
    "lineage_animal": {
        "legend_title": "MTBC Lineage (incl. animal)",
        "legend_shapes": "1,1,1,1,1,1,1,1,1,1,1,1,1",
        "legend_colors": (
            "#F5A623,#D0021B,#4A90D9,#E03D31,"
            "#7B2D8E,#9B59B6,#B8860B,#1B9AAA,#2D6A4F,#52B788,"
            "#3D2B1F,#6B4226,#808080"
        ),
        "legend_labels": (
            "L1,L2,L3,L4,L5,L6,L7,L8,L9,L10,"
            "M. bovis,M. caprae,M. orygis"
        ),
    },
    "drug_resistance": {
        "legend_title": "Drug Resistance",
        "legend_shapes": "2,2",
        "legend_colors": "#333333,#cccccc",
        "legend_labels": "Resistant,Susceptible",
    },
    "dr_type": {
        "legend_title": "DR Classification",
        "legend_shapes": "1,1,1,1",
        "legend_colors": "#2ecc71,#f39c12,#e74c3c,#8e44ad",
        "legend_labels": "Susceptible,Mono-R,MDR,XDR",
    },
}

# Format extensions for each export format
FORMAT_EXTENSIONS = {
    "svg": ".svg",
    "pdf": ".pdf",
    "png": ".png",
    "eps": ".eps",
    "ps": ".ps",
    "newick": ".nwk",
    "nexus": ".nex",
}
