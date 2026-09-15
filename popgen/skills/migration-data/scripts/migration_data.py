#!/usr/bin/env python3
"""
Human Migration Data Aggregation for MTBC Co-evolution Studies

Aggregate and format migration data from multiple sources for comparison
with MTBC dispersal patterns. Curated tables of historical events, country
centroids, HGDP structure, and geographic distance computation.

Usage:
    python3 migration_data.py slave-trade --input slavevoyages.csv -o routes.csv
    python3 migration_data.py ancient --format timeline -o events.csv
    python3 migration_data.py hgdp -o hgdp_structure.csv
    python3 migration_data.py timeline --tmrca tmrca.csv -p timeline.png
    python3 migration_data.py distances --countries "France,India,South Africa" -o dist.csv
"""

import argparse
import json
import sys
from collections import defaultdict
from math import radians, cos, sin, asin, sqrt

import numpy as np
import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False


# ---------------------------------------------------------------------------
# Curated migration events linked to MTBC lineage dispersal
# ---------------------------------------------------------------------------

MIGRATION_EVENTS = [
    {
        "event": "Out of Africa",
        "period_start": -70000, "period_end": -40000,
        "from_region": "East Africa", "to_region": "Eurasia",
        "volume": None,
        "mtbc_link": "Divergence L1-L7 du clade humain strict",
        "mtbc_lineages": "L1,L2,L3,L4,L7",
        "references": "Comas et al. 2013 Nat Genet; Bos et al. 2014",
    },
    {
        "event": "Neolithic expansion",
        "period_start": -10000, "period_end": -5000,
        "from_region": "Fertile Crescent", "to_region": "Europe, South Asia",
        "volume": None,
        "mtbc_link": "Expansion du L4 ancestral, possible origine proche-orientale",
        "mtbc_lineages": "L4",
        "references": "Brynildsrud et al. 2018 Sci Adv; Stucki et al. 2016",
    },
    {
        "event": "Bantu expansion",
        "period_start": -3000, "period_end": -500,
        "from_region": "West Africa", "to_region": "Central Africa, Southern Africa",
        "volume": None,
        "mtbc_link": "Dispersion L5/L6 (M. africanum) en Afrique subsaharienne",
        "mtbc_lineages": "L5,L6",
        "references": "de Jong et al. 2010; Yeboah-Manu et al. 2017",
    },
    {
        "event": "Arab trade networks",
        "period_start": 700, "period_end": 1500,
        "from_region": "Middle East", "to_region": "East Africa, South Asia",
        "volume": None,
        "mtbc_link": "Dispersion possible de L3 (Delhi/CAS) via routes commerciales",
        "mtbc_lineages": "L3",
        "references": "Malakmadze et al. 2023; Freschi et al. 2021",
    },
    {
        "event": "European colonization",
        "period_start": 1500, "period_end": 1900,
        "from_region": "Europe",
        "to_region": "Americas, Asia, Africa, Oceania",
        "volume": 55000000,
        "mtbc_link": "Expansion globale de L4 (sous-lignees europeennes)",
        "mtbc_lineages": "L4",
        "references": "Brynildsrud et al. 2018; Stucki et al. 2016",
    },
    {
        "event": "Trans-Atlantic slave trade",
        "period_start": 1514, "period_end": 1866,
        "from_region": "West Africa, Central Africa",
        "to_region": "Americas, Caribbean",
        "volume": 12500000,
        "mtbc_link": "Introduction L5/L6 en Ameriques, emergence L4 Clade A",
        "mtbc_lineages": "L5,L6,L4",
        "references": "Homolka et al. 2012; Brynildsrud et al. 2018; SlaveVoyages.org",
    },
    {
        "event": "Indian indenture system",
        "period_start": 1834, "period_end": 1920,
        "from_region": "India",
        "to_region": "Caribbean, East Africa, Fiji, Mauritius",
        "volume": 2000000,
        "mtbc_link": "Introduction L1/L3 dans les Caraibes et Afrique de l'Est",
        "mtbc_lineages": "L1,L3",
        "references": "Chatterjee et al. 2022; Zwyer et al. 2021",
    },
    {
        "event": "Modern global migration",
        "period_start": 1950, "period_end": 2025,
        "from_region": "Global South",
        "to_region": "Europe, North America, Gulf States",
        "volume": 281000000,
        "mtbc_link": "Import de lignees non-L4 en Europe, diversification urbaine",
        "mtbc_lineages": "L1,L2,L3",
        "references": "Stucki et al. 2016; Walker et al. 2018; UN DESA 2020",
    },
]


# ---------------------------------------------------------------------------
# HGDP K=7 population structure (curated from published data)
# ---------------------------------------------------------------------------

HGDP_STRUCTURE = [
    {"population": "San", "region": "Southern Africa", "lat": -21.0, "lon": 20.0,
     "K_Africa": 0.98, "K_Europe": 0.0, "K_MiddleEast": 0.0, "K_CSAsia": 0.01,
     "K_EAsia": 0.0, "K_Americas": 0.0, "K_Oceania": 0.01},
    {"population": "Yoruba", "region": "West Africa", "lat": 7.4, "lon": 3.9,
     "K_Africa": 0.99, "K_Europe": 0.0, "K_MiddleEast": 0.01, "K_CSAsia": 0.0,
     "K_EAsia": 0.0, "K_Americas": 0.0, "K_Oceania": 0.0},
    {"population": "Mandenka", "region": "West Africa", "lat": 12.0, "lon": -12.0,
     "K_Africa": 0.99, "K_Europe": 0.0, "K_MiddleEast": 0.01, "K_CSAsia": 0.0,
     "K_EAsia": 0.0, "K_Americas": 0.0, "K_Oceania": 0.0},
    {"population": "Biaka Pygmy", "region": "Central Africa", "lat": 4.0, "lon": 17.0,
     "K_Africa": 0.97, "K_Europe": 0.0, "K_MiddleEast": 0.0, "K_CSAsia": 0.02,
     "K_EAsia": 0.0, "K_Americas": 0.0, "K_Oceania": 0.01},
    {"population": "Mbuti Pygmy", "region": "Central Africa", "lat": 1.0, "lon": 29.0,
     "K_Africa": 0.98, "K_Europe": 0.0, "K_MiddleEast": 0.0, "K_CSAsia": 0.01,
     "K_EAsia": 0.0, "K_Americas": 0.0, "K_Oceania": 0.01},
    {"population": "French", "region": "Europe", "lat": 46.2, "lon": 2.2,
     "K_Africa": 0.0, "K_Europe": 0.82, "K_MiddleEast": 0.15, "K_CSAsia": 0.03,
     "K_EAsia": 0.0, "K_Americas": 0.0, "K_Oceania": 0.0},
    {"population": "Sardinian", "region": "Europe", "lat": 40.0, "lon": 9.0,
     "K_Africa": 0.0, "K_Europe": 0.85, "K_MiddleEast": 0.13, "K_CSAsia": 0.02,
     "K_EAsia": 0.0, "K_Americas": 0.0, "K_Oceania": 0.0},
    {"population": "Tuscan", "region": "Europe", "lat": 43.0, "lon": 11.3,
     "K_Africa": 0.0, "K_Europe": 0.78, "K_MiddleEast": 0.18, "K_CSAsia": 0.04,
     "K_EAsia": 0.0, "K_Americas": 0.0, "K_Oceania": 0.0},
    {"population": "Russian", "region": "Europe", "lat": 61.0, "lon": 73.0,
     "K_Africa": 0.0, "K_Europe": 0.72, "K_MiddleEast": 0.10, "K_CSAsia": 0.14,
     "K_EAsia": 0.04, "K_Americas": 0.0, "K_Oceania": 0.0},
    {"population": "Basque", "region": "Europe", "lat": 43.0, "lon": -1.0,
     "K_Africa": 0.0, "K_Europe": 0.88, "K_MiddleEast": 0.10, "K_CSAsia": 0.02,
     "K_EAsia": 0.0, "K_Americas": 0.0, "K_Oceania": 0.0},
    {"population": "Palestinian", "region": "Middle East", "lat": 32.0, "lon": 35.0,
     "K_Africa": 0.04, "K_Europe": 0.30, "K_MiddleEast": 0.55, "K_CSAsia": 0.11,
     "K_EAsia": 0.0, "K_Americas": 0.0, "K_Oceania": 0.0},
    {"population": "Druze", "region": "Middle East", "lat": 33.0, "lon": 35.5,
     "K_Africa": 0.02, "K_Europe": 0.35, "K_MiddleEast": 0.52, "K_CSAsia": 0.11,
     "K_EAsia": 0.0, "K_Americas": 0.0, "K_Oceania": 0.0},
    {"population": "Bedouin", "region": "Middle East", "lat": 31.0, "lon": 35.0,
     "K_Africa": 0.05, "K_Europe": 0.22, "K_MiddleEast": 0.60, "K_CSAsia": 0.13,
     "K_EAsia": 0.0, "K_Americas": 0.0, "K_Oceania": 0.0},
    {"population": "Balochi", "region": "Central/South Asia", "lat": 30.0, "lon": 67.0,
     "K_Africa": 0.0, "K_Europe": 0.10, "K_MiddleEast": 0.35, "K_CSAsia": 0.53,
     "K_EAsia": 0.02, "K_Americas": 0.0, "K_Oceania": 0.0},
    {"population": "Pathan", "region": "Central/South Asia", "lat": 33.0, "lon": 71.0,
     "K_Africa": 0.0, "K_Europe": 0.12, "K_MiddleEast": 0.28, "K_CSAsia": 0.56,
     "K_EAsia": 0.04, "K_Americas": 0.0, "K_Oceania": 0.0},
    {"population": "Sindhi", "region": "Central/South Asia", "lat": 26.0, "lon": 69.0,
     "K_Africa": 0.0, "K_Europe": 0.08, "K_MiddleEast": 0.30, "K_CSAsia": 0.58,
     "K_EAsia": 0.04, "K_Americas": 0.0, "K_Oceania": 0.0},
    {"population": "Han (North)", "region": "East Asia", "lat": 40.0, "lon": 116.4,
     "K_Africa": 0.0, "K_Europe": 0.0, "K_MiddleEast": 0.0, "K_CSAsia": 0.01,
     "K_EAsia": 0.99, "K_Americas": 0.0, "K_Oceania": 0.0},
    {"population": "Han (South)", "region": "East Asia", "lat": 23.0, "lon": 113.0,
     "K_Africa": 0.0, "K_Europe": 0.0, "K_MiddleEast": 0.0, "K_CSAsia": 0.01,
     "K_EAsia": 0.99, "K_Americas": 0.0, "K_Oceania": 0.0},
    {"population": "Japanese", "region": "East Asia", "lat": 36.0, "lon": 138.0,
     "K_Africa": 0.0, "K_Europe": 0.0, "K_MiddleEast": 0.0, "K_CSAsia": 0.01,
     "K_EAsia": 0.99, "K_Americas": 0.0, "K_Oceania": 0.0},
    {"population": "Yakut", "region": "East Asia", "lat": 62.0, "lon": 130.0,
     "K_Africa": 0.0, "K_Europe": 0.02, "K_MiddleEast": 0.0, "K_CSAsia": 0.05,
     "K_EAsia": 0.93, "K_Americas": 0.0, "K_Oceania": 0.0},
    {"population": "Cambodian", "region": "East Asia", "lat": 12.6, "lon": 105.0,
     "K_Africa": 0.0, "K_Europe": 0.0, "K_MiddleEast": 0.0, "K_CSAsia": 0.01,
     "K_EAsia": 0.99, "K_Americas": 0.0, "K_Oceania": 0.0},
    {"population": "Maya", "region": "Americas", "lat": 19.0, "lon": -90.0,
     "K_Africa": 0.0, "K_Europe": 0.0, "K_MiddleEast": 0.0, "K_CSAsia": 0.01,
     "K_EAsia": 0.04, "K_Americas": 0.95, "K_Oceania": 0.0},
    {"population": "Pima", "region": "Americas", "lat": 29.0, "lon": -110.0,
     "K_Africa": 0.0, "K_Europe": 0.0, "K_MiddleEast": 0.0, "K_CSAsia": 0.0,
     "K_EAsia": 0.02, "K_Americas": 0.98, "K_Oceania": 0.0},
    {"population": "Colombian", "region": "Americas", "lat": 3.0, "lon": -73.0,
     "K_Africa": 0.0, "K_Europe": 0.0, "K_MiddleEast": 0.0, "K_CSAsia": 0.01,
     "K_EAsia": 0.04, "K_Americas": 0.95, "K_Oceania": 0.0},
    {"population": "Karitiana", "region": "Americas", "lat": -10.0, "lon": -63.0,
     "K_Africa": 0.0, "K_Europe": 0.0, "K_MiddleEast": 0.0, "K_CSAsia": 0.0,
     "K_EAsia": 0.01, "K_Americas": 0.99, "K_Oceania": 0.0},
    {"population": "Surui", "region": "Americas", "lat": -11.0, "lon": -61.0,
     "K_Africa": 0.0, "K_Europe": 0.0, "K_MiddleEast": 0.0, "K_CSAsia": 0.0,
     "K_EAsia": 0.01, "K_Americas": 0.99, "K_Oceania": 0.0},
    {"population": "Papuan", "region": "Oceania", "lat": -6.0, "lon": 147.0,
     "K_Africa": 0.0, "K_Europe": 0.0, "K_MiddleEast": 0.0, "K_CSAsia": 0.01,
     "K_EAsia": 0.15, "K_Americas": 0.0, "K_Oceania": 0.84},
    {"population": "Melanesian", "region": "Oceania", "lat": -9.0, "lon": 160.0,
     "K_Africa": 0.0, "K_Europe": 0.0, "K_MiddleEast": 0.0, "K_CSAsia": 0.0,
     "K_EAsia": 0.20, "K_Americas": 0.0, "K_Oceania": 0.80},
]


# ---------------------------------------------------------------------------
# Country centroids (imported from coevolution module, but self-contained here)
# ---------------------------------------------------------------------------

COUNTRY_CENTROIDS = {
    "Afghanistan": (33.9, 67.7), "Algeria": (28.0, 1.7), "Angola": (-11.2, 17.9),
    "Argentina": (-38.4, -63.6), "Australia": (-25.3, 133.8), "Bangladesh": (23.7, 90.4),
    "Belgium": (50.8, 4.5), "Benin": (9.3, 2.3), "Bolivia": (-16.3, -63.6),
    "Botswana": (-22.3, 24.7), "Brazil": (-14.2, -51.9), "Burkina Faso": (12.4, -1.6),
    "Burundi": (-3.4, 29.9), "Cambodia": (12.6, 105.0), "Cameroon": (7.4, 12.4),
    "Canada": (56.1, -106.3), "Central African Republic": (6.6, 20.9),
    "Chad": (15.5, 18.7), "Chile": (-35.7, -71.5), "China": (35.9, 104.2),
    "Colombia": (4.6, -74.3), "Congo": (-0.2, 15.8), "Costa Rica": (9.7, -83.8),
    "Cuba": (21.5, -77.8), "DR Congo": (-4.0, 21.8), "Denmark": (56.3, 9.5),
    "Djibouti": (11.8, 42.6), "Dominican Republic": (18.7, -70.2),
    "Ecuador": (-1.8, -78.2), "Egypt": (26.8, 30.8), "El Salvador": (13.8, -88.9),
    "Eritrea": (15.2, 39.8), "Ethiopia": (9.1, 40.5), "Fiji": (-17.7, 178.1),
    "Finland": (61.9, 25.7), "France": (46.2, 2.2), "Gabon": (-0.8, 11.6),
    "Gambia": (13.4, -16.6), "Germany": (51.2, 10.4), "Ghana": (7.9, -1.0),
    "Greece": (39.1, 21.8), "Guatemala": (15.8, -90.2), "Guinea": (9.9, -9.7),
    "Guinea-Bissau": (12.0, -15.2), "Guyana": (5.0, -58.9), "Haiti": (19.0, -72.3),
    "Honduras": (15.2, -86.2), "India": (20.6, 78.9), "Indonesia": (-0.8, 113.9),
    "Iran": (32.4, 53.7), "Iraq": (33.2, 43.7), "Ireland": (53.4, -8.2),
    "Israel": (31.0, 34.9), "Italy": (41.9, 12.6), "Ivory Coast": (7.5, -5.5),
    "Jamaica": (18.1, -77.3), "Japan": (36.2, 138.3), "Jordan": (31.0, 36.8),
    "Kazakhstan": (48.0, 68.0), "Kenya": (-0.0, 37.9), "Kuwait": (29.3, 47.5),
    "Laos": (19.9, 102.5), "Lebanon": (33.9, 35.9), "Lesotho": (-29.6, 28.2),
    "Liberia": (6.4, -9.4), "Libya": (26.3, 17.2), "Madagascar": (-18.8, 46.9),
    "Malawi": (-13.3, 34.3), "Malaysia": (4.2, 101.9), "Mali": (17.6, -4.0),
    "Mauritania": (21.0, -10.9), "Mauritius": (-20.3, 57.6), "Mexico": (23.6, -102.6),
    "Morocco": (31.8, -7.1), "Mozambique": (-18.7, 35.5), "Myanmar": (21.9, 96.0),
    "Namibia": (-22.6, 17.1), "Nepal": (28.4, 84.1), "Netherlands": (52.1, 5.3),
    "New Zealand": (-40.9, 174.9), "Niger": (17.6, 8.1), "Nigeria": (9.1, 8.7),
    "North Korea": (40.3, 127.5), "Norway": (60.5, 8.5), "Pakistan": (30.4, 69.3),
    "Panama": (8.5, -80.8), "Papua New Guinea": (-6.3, 143.9),
    "Paraguay": (-23.4, -58.4), "Peru": (-9.2, -75.0), "Philippines": (12.9, 121.8),
    "Poland": (51.9, 19.1), "Portugal": (39.4, -8.2), "Romania": (45.9, 25.0),
    "Russia": (61.5, 105.3), "Rwanda": (-1.9, 29.9), "Saudi Arabia": (23.9, 45.1),
    "Senegal": (14.5, -14.5), "Sierra Leone": (8.5, -11.8), "Singapore": (1.4, 103.8),
    "Somalia": (5.2, 46.2), "South Africa": (-30.6, 22.9),
    "South Korea": (35.9, 128.0), "South Sudan": (6.9, 31.3),
    "Spain": (40.5, -3.7), "Sri Lanka": (7.9, 80.8), "Sudan": (12.9, 30.2),
    "Suriname": (4.0, -56.0), "Sweden": (60.1, 18.6), "Switzerland": (46.8, 8.2),
    "Syria": (34.8, 38.9), "Taiwan": (23.7, 121.0), "Tanzania": (-6.4, 34.9),
    "Thailand": (15.9, 101.0), "Togo": (8.6, 1.2),
    "Trinidad and Tobago": (10.7, -61.2), "Tunisia": (33.9, 9.5),
    "Turkey": (38.9, 35.2), "Uganda": (1.4, 32.3), "Ukraine": (48.4, 31.2),
    "United Arab Emirates": (23.4, 53.8), "United Kingdom": (55.4, -3.4),
    "United States": (37.1, -95.7), "USA": (37.1, -95.7), "UK": (55.4, -3.4),
    "Uruguay": (-32.5, -55.8), "Venezuela": (6.4, -66.6), "Vietnam": (14.1, 108.3),
    "Yemen": (15.6, 48.5), "Zambia": (-13.1, 27.8), "Zimbabwe": (-19.0, 29.2),
}


# ---------------------------------------------------------------------------
# Haversine distance
# ---------------------------------------------------------------------------

def haversine(lat1, lon1, lat2, lon2):
    """Haversine distance in km."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 6371 * 2 * asin(sqrt(a))


def haversine_distance_matrix(countries: list) -> pd.DataFrame:
    """Build a distance matrix (km) between countries using centroids."""
    n = len(countries)
    mat = np.zeros((n, n))
    for i in range(n):
        c1 = COUNTRY_CENTROIDS.get(countries[i])
        if not c1:
            print(f"Warning: no centroid for '{countries[i]}'.", file=sys.stderr)
            c1 = (0, 0)
        for j in range(i + 1, n):
            c2 = COUNTRY_CENTROIDS.get(countries[j])
            if not c2:
                c2 = (0, 0)
            d = haversine(c1[0], c1[1], c2[0], c2[1])
            mat[i, j] = round(d, 1)
            mat[j, i] = round(d, 1)
    return pd.DataFrame(mat, index=countries, columns=countries)


# ---------------------------------------------------------------------------
# SlaveVoyages aggregation
# ---------------------------------------------------------------------------

# SlaveVoyages column mapping (common columns in the downloadable CSV)
SV_COLUMNS = {
    "YEARAM": "year_arrival",
    "YEAR5": "year_5yr",
    "MJBYPTIMP": "embarkation_region",
    "MJSLPTIMP": "disembarkation_region",
    "REGISREG": "registration_region",
    "SLAXIMP": "embarked_total",
    "SLAMIMP": "disembarked_total",
    "FATE2": "fate",
}

# SlaveVoyages region codes to names
SV_REGIONS_EMBARK = {
    60100: "Senegambia", 60200: "Sierra Leone", 60300: "Windward Coast",
    60400: "Gold Coast", 60500: "Bight of Benin", 60600: "Bight of Biafra",
    60700: "West Central Africa", 60800: "Southeast Africa",
}

SV_REGIONS_DISEMBARK = {
    31100: "Amazonia", 31200: "Bahia", 31300: "Pernambuco",
    31400: "Southeast Brazil", 31500: "Other Brazil",
    40100: "Caribbean", 40200: "Jamaica", 40300: "Barbados",
    40400: "Guadeloupe", 40500: "Martinique", 40600: "Saint-Domingue",
    40700: "Cuba", 40800: "Puerto Rico", 40900: "Other Caribbean",
    50100: "Spanish Mainland", 50200: "British North America",
    50300: "United States", 50400: "Dutch Americas",
}


def aggregate_slave_trade(
    input_path: str, period_start: int = None, period_end: int = None,
    from_region: str = None, to_region: str = None
) -> pd.DataFrame:
    """Aggregate SlaveVoyages data by embarkation-disembarkation route."""
    df = pd.read_csv(input_path, low_memory=False)

    # Rename columns if they match known SlaveVoyages headers
    rename = {}
    for old, new in SV_COLUMNS.items():
        if old in df.columns:
            rename[old] = new
    if rename:
        df = df.rename(columns=rename)

    # Determine year column
    year_col = None
    for candidate in ["year_arrival", "YEARAM", "year", "Year"]:
        if candidate in df.columns:
            year_col = candidate
            break
    if year_col is None:
        print("Warning: no year column found, using all data.", file=sys.stderr)

    # Filter by period
    if year_col and period_start is not None:
        df = df[df[year_col] >= period_start]
    if year_col and period_end is not None:
        df = df[df[year_col] <= period_end]

    # Determine embarkation/disembarkation columns
    emb_col = None
    for c in ["embarkation_region", "MJBYPTIMP", "embark_region"]:
        if c in df.columns:
            emb_col = c
            break
    dis_col = None
    for c in ["disembarkation_region", "MJSLPTIMP", "disembark_region"]:
        if c in df.columns:
            dis_col = c
            break

    if emb_col is None or dis_col is None:
        print("Warning: could not identify embarkation/disembarkation columns.",
              file=sys.stderr)
        print(f"Available columns: {list(df.columns)[:20]}", file=sys.stderr)
        return pd.DataFrame()

    # Volume column
    vol_col = None
    for c in ["embarked_total", "SLAXIMP", "disembarked_total", "SLAMIMP"]:
        if c in df.columns:
            vol_col = c
            break

    # Map region codes to names
    if df[emb_col].dtype in [np.int64, np.float64]:
        df[emb_col] = df[emb_col].map(SV_REGIONS_EMBARK).fillna(df[emb_col].astype(str))
    if df[dis_col].dtype in [np.int64, np.float64]:
        df[dis_col] = df[dis_col].map(SV_REGIONS_DISEMBARK).fillna(df[dis_col].astype(str))

    # Filter by region
    if from_region:
        df = df[df[emb_col].str.contains(from_region, case=False, na=False)]
    if to_region:
        df = df[df[dis_col].str.contains(to_region, case=False, na=False)]

    # Aggregate
    if vol_col:
        agg = df.groupby([emb_col, dis_col]).agg(
            n_voyages=("id" if "id" in df.columns else emb_col, "count"),
            total_embarked=(vol_col, "sum"),
        ).reset_index()
        agg.columns = ["from", "to", "n_voyages", "volume"]
    else:
        agg = df.groupby([emb_col, dis_col]).size().reset_index(name="n_voyages")
        agg.columns = ["from", "to", "n_voyages"]
        agg["volume"] = agg["n_voyages"]  # proxy

    agg = agg.sort_values("volume", ascending=False)

    if period_start or period_end:
        agg["period_start"] = period_start or "?"
        agg["period_end"] = period_end or "?"

    return agg


# ---------------------------------------------------------------------------
# Modern migration (UN data)
# ---------------------------------------------------------------------------

def load_un_migration(input_path: str, period_start: int = None, period_end: int = None) -> pd.DataFrame:
    """Load UN Migration Stock data from Excel."""
    try:
        import openpyxl
    except ImportError:
        print("Error: openpyxl required for Excel files. pip install openpyxl", file=sys.stderr)
        return pd.DataFrame()

    df = pd.read_excel(input_path, engine="openpyxl")
    print(f"UN Migration data: {df.shape[0]} rows, {df.shape[1]} columns", file=sys.stderr)
    return df


# ---------------------------------------------------------------------------
# WHO TB burden
# ---------------------------------------------------------------------------

def load_who_burden(input_path: str) -> pd.DataFrame:
    """Load WHO TB burden data."""
    df = pd.read_csv(input_path, low_memory=False)
    # Select relevant columns
    keep_cols = []
    for col in df.columns:
        cl = col.lower()
        if any(k in cl for k in ["country", "iso", "year", "incidence", "mortality", "prevalence"]):
            keep_cols.append(col)
    if keep_cols:
        df = df[keep_cols]
    print(f"WHO TB burden: {df.shape[0]} rows", file=sys.stderr)
    return df


# ---------------------------------------------------------------------------
# Timeline overlay
# ---------------------------------------------------------------------------

def build_timeline(tmrca_path: str = None) -> pd.DataFrame:
    """Build a combined timeline of migration events and MTBC TMRCA estimates."""
    rows = []
    for evt in MIGRATION_EVENTS:
        rows.append({
            "type": "migration",
            "event": evt["event"],
            "period_start": evt["period_start"],
            "period_end": evt["period_end"],
            "from": evt["from_region"],
            "to": evt["to_region"],
            "volume": evt.get("volume"),
            "mtbc_link": evt["mtbc_link"],
            "mtbc_lineages": evt["mtbc_lineages"],
        })

    if tmrca_path:
        tmrca = pd.read_csv(tmrca_path)
        for _, row in tmrca.iterrows():
            rows.append({
                "type": "mtbc_tmrca",
                "event": f"TMRCA {row.get('lineage', row.get('node', '?'))}",
                "period_start": row.get("tmrca", row.get("date", 0)),
                "period_end": row.get("tmrca", row.get("date", 0)),
                "from": None, "to": None, "volume": None,
                "mtbc_link": str(row.get("lineage", "")),
                "mtbc_lineages": str(row.get("lineage", "")),
            })

    return pd.DataFrame(rows).sort_values("period_start")


def plot_timeline(timeline: pd.DataFrame, output_path: str):
    """Plot a combined timeline of migrations and MTBC events."""
    if not HAS_PLOT:
        print("Warning: matplotlib not available.", file=sys.stderr)
        return

    fig, ax = plt.subplots(figsize=(16, 8))

    migration_events = timeline[timeline["type"] == "migration"]
    mtbc_events = timeline[timeline["type"] == "mtbc_tmrca"]

    # Plot migration events as horizontal bars
    y_positions = {}
    y = 0
    for _, row in migration_events.iterrows():
        start = row["period_start"]
        end = row["period_end"]
        ax.barh(y, end - start, left=start, height=0.6, color="#4A90D9", alpha=0.7)
        label = row["event"]
        if len(label) > 25:
            label = label[:25] + "..."
        ax.text(start, y, f" {label}", va="center", fontsize=8, fontweight="bold")
        y_positions[row["event"]] = y
        y += 1

    # Plot MTBC TMRCA as vertical lines
    for _, row in mtbc_events.iterrows():
        tmrca = row["period_start"]
        ax.axvline(tmrca, color="#E03D31", linewidth=1, alpha=0.6, linestyle="--")
        ax.text(tmrca, y + 0.2, row["event"], rotation=45, fontsize=7, color="#E03D31")

    ax.set_xlabel("Year (negative = BCE)")
    ax.set_yticks(range(len(migration_events)))
    ax.set_yticklabels([])
    ax.set_title("Human Migrations and MTBC Divergence Timeline")
    ax.invert_yaxis()

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Timeline plot saved: {output_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Human migration data for MTBC co-evolution studies.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # SlaveVoyages aggregation
  python3 migration_data.py slave-trade --input slavevoyages.csv -o routes.csv

  # Ancient migration events (curated)
  python3 migration_data.py ancient --format timeline -o events.csv

  # HGDP population structure
  python3 migration_data.py hgdp -o hgdp.csv

  # Combined timeline with MTBC TMRCA overlay
  python3 migration_data.py timeline --tmrca tmrca.csv -p timeline.png

  # Geographic distance matrix
  python3 migration_data.py distances --countries "France,India,South Africa,Brazil"
        """,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # slave-trade
    p_st = subparsers.add_parser("slave-trade", help="Aggregate SlaveVoyages data")
    p_st.add_argument("--input", required=True, help="SlaveVoyages CSV file")
    p_st.add_argument("--period", help="Period filter (e.g., 1700:1800)")
    p_st.add_argument("--from-region", help="Source region filter")
    p_st.add_argument("--to-region", help="Destination region filter")
    p_st.add_argument("--format", default="routes", choices=["routes", "matrix"])
    p_st.add_argument("-o", "--output", help="Output CSV")

    # modern
    p_mod = subparsers.add_parser("modern", help="Load UN migration stock data")
    p_mod.add_argument("--input", required=True, help="UN Migration Excel file")
    p_mod.add_argument("--period", help="Period filter (e.g., 2000:2020)")
    p_mod.add_argument("-o", "--output", help="Output CSV")

    # hgdp
    p_hgdp = subparsers.add_parser("hgdp", help="HGDP K=7 population structure")
    p_hgdp.add_argument("--populations", help="Filter populations (comma-separated)")
    p_hgdp.add_argument("-o", "--output", help="Output CSV")

    # ancient
    p_anc = subparsers.add_parser("ancient", help="Curated ancient migration events")
    p_anc.add_argument("--period", help="Period filter (e.g., -70000:-3000)")
    p_anc.add_argument("--format", default="timeline", choices=["timeline", "routes"])
    p_anc.add_argument("-o", "--output", help="Output CSV")

    # who-burden
    p_who = subparsers.add_parser("who-burden", help="WHO TB burden data")
    p_who.add_argument("--input", required=True, help="WHO TB data CSV")
    p_who.add_argument("-o", "--output", help="Output CSV")

    # timeline
    p_tl = subparsers.add_parser("timeline", help="Combined migration + MTBC timeline")
    p_tl.add_argument("--tmrca", help="MTBC TMRCA estimates CSV")
    p_tl.add_argument("--period", help="Period to display (e.g., -70000:2025)")
    p_tl.add_argument("-o", "--output", help="Output CSV")
    p_tl.add_argument("-p", "--plot", help="Timeline plot output")

    # distances
    p_dist = subparsers.add_parser("distances", help="Geographic distance matrix")
    p_dist.add_argument("--countries", required=True,
                        help="Comma-separated list of countries or path to CSV")
    p_dist.add_argument("-o", "--output", help="Output CSV")

    # Common
    for sp in [p_st, p_mod, p_hgdp, p_anc, p_who, p_tl, p_dist]:
        sp.add_argument("--summary", action="store_true", help="Print JSON summary")

    args = parser.parse_args()

    if args.command == "slave-trade":
        period_start, period_end = None, None
        if args.period:
            parts = args.period.split(":")
            period_start = int(parts[0])
            period_end = int(parts[1]) if len(parts) > 1 else None

        result = aggregate_slave_trade(
            args.input, period_start, period_end, args.from_region, args.to_region
        )

        if args.format == "matrix" and not result.empty:
            pivot = result.pivot_table(
                index="from", columns="to", values="volume", fill_value=0
            )
            if args.output:
                pivot.to_csv(args.output)
            else:
                pivot.to_csv(sys.stdout)
        else:
            if args.output:
                result.to_csv(args.output, index=False)
            elif not result.empty:
                result.to_csv(sys.stdout, index=False)

        print(f"Slave trade routes: {len(result)} routes", file=sys.stderr)

    elif args.command == "modern":
        result = load_un_migration(args.input)
        if args.output and not result.empty:
            result.to_csv(args.output, index=False)

    elif args.command == "hgdp":
        df = pd.DataFrame(HGDP_STRUCTURE)
        if args.populations:
            pops = [p.strip() for p in args.populations.split(",")]
            df = df[df["population"].isin(pops) | df["region"].isin(pops)]

        if args.output:
            df.to_csv(args.output, index=False)
        else:
            df.to_csv(sys.stdout, index=False)
        print(f"HGDP structure: {len(df)} populations", file=sys.stderr)

    elif args.command == "ancient":
        events = MIGRATION_EVENTS
        if args.period:
            parts = args.period.split(":")
            p_start = int(parts[0])
            p_end = int(parts[1]) if len(parts) > 1 else 2025
            events = [e for e in events if e["period_end"] >= p_start and e["period_start"] <= p_end]

        df = pd.DataFrame(events)
        if args.output:
            df.to_csv(args.output, index=False)
        else:
            df.to_csv(sys.stdout, index=False)
        print(f"Ancient events: {len(df)} events", file=sys.stderr)

    elif args.command == "who-burden":
        result = load_who_burden(args.input)
        if args.output and not result.empty:
            result.to_csv(args.output, index=False)

    elif args.command == "timeline":
        timeline = build_timeline(args.tmrca)

        if args.period:
            parts = args.period.split(":")
            p_start = int(parts[0])
            p_end = int(parts[1]) if len(parts) > 1 else 2025
            timeline = timeline[
                (timeline["period_end"] >= p_start) & (timeline["period_start"] <= p_end)
            ]

        if args.output:
            timeline.to_csv(args.output, index=False)
        if args.plot:
            plot_timeline(timeline, args.plot)
        if not args.output and not args.plot:
            timeline.to_csv(sys.stdout, index=False)
        print(f"Timeline: {len(timeline)} events", file=sys.stderr)

    elif args.command == "distances":
        if args.countries.endswith(".csv"):
            countries_df = pd.read_csv(args.countries)
            countries = countries_df.iloc[:, 0].astype(str).tolist()
        else:
            countries = [c.strip() for c in args.countries.split(",")]

        dist = haversine_distance_matrix(countries)
        if args.output:
            dist.to_csv(args.output)
        else:
            dist.to_csv(sys.stdout)
        print(f"Distance matrix: {len(countries)} x {len(countries)} countries", file=sys.stderr)

    # Summary
    if hasattr(args, "summary") and args.summary:
        summary = {
            "command": args.command,
            "n_curated_events": len(MIGRATION_EVENTS),
            "n_hgdp_populations": len(HGDP_STRUCTURE),
            "n_country_centroids": len(COUNTRY_CENTROIDS),
        }
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
