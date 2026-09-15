#!/usr/bin/env python3
"""
Atlantic Voyages — historical maritime data for M. tuberculosis L5/L6/L4
phylogeography studies.

Wraps six open-data sources (SlaveVoyages Trans-Atlantic, AfricanOrigins,
Liberated Africans, Intra-American Voyages, Voyages to Liberty, Slavery
Abolition portal) and provides curated routes and port centroids for the
Atlantic basin. Output schema is compatible with the migration-data and
indian-ocean-voyages skills so that matrices can be combined for Mantel
tests against MTBC pairwise distances.

Usage:
    python3 atlantic_voyages.py slavevoyages --input tast.csv -o sv_routes.csv
    python3 atlantic_voyages.py african-origins --input ao.csv -o ao.csv
    python3 atlantic_voyages.py liberated --input la.csv -o la.csv
    python3 atlantic_voyages.py intra-american --input ia.csv -o ia.csv
    python3 atlantic_voyages.py returnees -o returnees.csv
    python3 atlantic_voyages.py routes --source "Gold Coast,Bight of Benin" \
        --dest "Bahia,Jamaica" --format matrix -o routes.csv
    python3 atlantic_voyages.py timeline --tmrca l5l6.csv -p timeline.png
    python3 atlantic_voyages.py fetch --source trans-atlantic
"""

import argparse
import json
import sys
from math import radians, cos, sin, asin, sqrt
from pathlib import Path

import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False


# ---------------------------------------------------------------------------
# Curated Atlantic port centroids (lat, lon)
# ---------------------------------------------------------------------------

PORT_CENTROIDS = {
    # West African coast — Senegambia
    "Gorée": (14.67, -17.40),
    "Saint-Louis": (16.03, -16.50),
    "James Fort (Gambia)": (13.32, -16.36),
    "Bissau": (11.86, -15.58),
    "Cacheu": (12.27, -16.16),

    # Sierra Leone + Windward Coast
    "Freetown": (8.48, -13.23),
    "Bance Island": (8.55, -13.05),
    "Cape Mount (Liberia)": (6.75, -11.37),
    "Cape des Palmes": (4.37, -7.73),

    # Gold Coast (Ghana)
    "Elmina": (5.08, -1.35),
    "Cape Coast": (5.10, -1.25),
    "Anomabu": (5.16, -1.12),
    "Christiansborg/Accra": (5.55, -0.20),
    "Whydah/Keta": (5.92, 0.98),

    # Bight of Benin
    "Ouidah": (6.36, 2.08),
    "Lagos": (6.45, 3.40),
    "Porto-Novo": (6.50, 2.62),
    "Badagry": (6.42, 2.88),
    "Allada": (6.66, 2.15),

    # Bight of Biafra
    "Bonny": (4.42, 7.17),
    "Calabar": (4.95, 8.32),
    "New Calabar (Elem Kalabari)": (4.65, 7.05),
    "Bimbia (Cameroon)": (3.97, 9.32),
    "Cameroon River": (4.05, 9.70),

    # West-Central Africa
    "Luanda": (-8.84, 13.23),
    "Benguela": (-12.58, 13.40),
    "Cabinda": (-5.55, 12.20),
    "Loango": (-4.65, 11.83),
    "Ambriz": (-7.85, 13.12),
    "Soyo (Kongo)": (-6.13, 12.37),

    # European ports
    "Lisbon": (38.72, -9.14),
    "Bristol": (51.45, -2.58),
    "Liverpool": (53.41, -2.98),
    "Nantes": (47.22, -1.55),
    "Bordeaux": (44.84, -0.58),
    "Amsterdam": (52.37, 4.90),
    "Sevilla": (37.39, -5.99),
    "Cadiz": (36.53, -6.30),

    # Cape Verde + Atlantic islands
    "Praia (Cape Verde)": (14.92, -23.51),
    "Santiago de Cabo Verde": (15.13, -23.61),
    "Madeira": (32.65, -16.91),
    "Açores": (37.74, -25.67),
    "São Tomé": (0.34, 6.73),

    # Brazil
    "Salvador (Bahia)": (-12.97, -38.51),
    "Recife (Pernambuco)": (-8.05, -34.88),
    "Rio de Janeiro": (-22.91, -43.17),
    "Belém (Pará)": (-1.46, -48.50),
    "São Luís (Maranhão)": (-2.53, -44.30),

    # Caribbean
    "Kingston (Jamaica)": (17.97, -76.79),
    "Bridgetown (Barbados)": (13.10, -59.62),
    "Cap-Haïtien (Saint-Domingue)": (19.76, -72.20),
    "Port-au-Prince": (18.59, -72.30),
    "Havana": (23.13, -82.38),
    "Santiago de Cuba": (20.02, -75.83),
    "San Juan (Puerto Rico)": (18.47, -66.10),
    "Saint-Pierre (Martinique)": (14.74, -61.18),
    "Pointe-à-Pitre (Guadeloupe)": (16.24, -61.53),
    "Cartagena (Colombia)": (10.39, -75.51),
    "Veracruz (Mexico)": (19.20, -96.13),

    # Guianas
    "Paramaribo (Suriname)": (5.85, -55.20),
    "Cayenne (French Guiana)": (4.93, -52.33),
    "Georgetown (Guyana)": (6.81, -58.16),

    # USA South + Atlantic seaboard
    "Charleston": (32.78, -79.93),
    "Savannah": (32.08, -81.10),
    "New Orleans": (29.95, -90.07),
    "Annapolis": (38.98, -76.49),
    "Norfolk": (36.85, -76.29),
    "New York": (40.71, -74.01),
}


# ---------------------------------------------------------------------------
# Curated trans-Atlantic routes (Eltis et al. estimates 2010)
# ---------------------------------------------------------------------------

CURATED_ROUTES = [
    # source region, destination region, period, volume estimate,
    # main sources, expected L5/L6 sub-clades
    ("Senegambia", "USA Sud", "1700-1808", 145_000,
     "Gorée, James Fort", "L6.1.1 Mande, L6.1.2.1.2 Mel_Atlantic"),
    ("Sierra Leone", "USA Sud", "1750-1808", 120_000,
     "Bance Island, Freetown", "L6.1.2.1.2 Mel_Atlantic"),
    ("Senegambia + Sierra Leone", "Caraïbes britanniques", "1650-1830", 250_000,
     "Gorée + Bance", "L6.1.1 Mande, L6.1.2"),
    ("Windward Coast", "Caraïbes françaises", "1700-1820", 150_000,
     "Cap des Palmes", "L5.2.2.1 Tano"),
    ("Gold Coast", "Caraïbes britanniques (Jamaïque)", "1650-1800", 600_000,
     "Elmina, Cape Coast, Anomabu",
     "L5.2.2.1.1.2.1.x Akan, L5.2.2.x Tano"),
    ("Gold Coast", "Suriname", "1670-1815", 180_000,
     "Elmina + Anomabu", "L5.2.2.1.1.2.1.x Akan"),
    ("Bight of Benin", "Brésil (Bahia)", "1670-1810", 1_100_000,
     "Ouidah, Lagos, Badagry",
     "L5.2.1.1.1 Gbe (Dahomey), L5.2.x Yoruba"),
    ("Bight of Benin", "Saint-Domingue", "1700-1791", 400_000,
     "Ouidah, Allada", "L5.2.1.1.1 Gbe + L5.2.x Yoruba"),
    ("Bight of Biafra", "USA Sud (Virginie)", "1700-1808", 95_000,
     "Bonny, Calabar", "L5.2.x Igbo"),
    ("Bight of Biafra", "Caraïbes britanniques", "1730-1830", 850_000,
     "Bonny, Calabar", "L5.2.x Igbo"),
    ("Bight of Biafra", "Cuba (tardif)", "1820-1860", 200_000,
     "Old Calabar", "L5.2.x Igbo + L5.2.1.1.2"),
    ("West-Central Africa", "Brésil (Rio/Sudeste)", "1550-1860", 2_100_000,
     "Luanda, Benguela, Cabinda, Loango",
     "L5.2.1.1.2 Bantu_Central (record P2)"),
    ("West-Central Africa", "Brésil (Bahia)", "1700-1860", 500_000,
     "Luanda + Cabinda", "L5.2.1.1.2 + L5.2.2.1.1.2.1.2 Gabon"),
    ("West-Central Africa", "Saint-Domingue", "1700-1791", 350_000,
     "Cabinda + Loango", "L5.2.1.1.2 Bantu_Central"),
    ("West-Central Africa", "Cuba (tardif)", "1790-1870", 580_000,
     "Cabinda + Soyo", "L5.2.1.1.2 + L5.2.2.x"),
    ("West-Central Africa", "Suriname", "1670-1815", 120_000,
     "Loango + Cabinda", "L5.2.1.1.2 + L5.2.2.1.1.2.1.2"),
    ("West-Central Africa", "Caraïbes françaises", "1670-1820", 200_000,
     "Cabinda + Loango", "L5.2.1.1.2 + L5.2.x"),
    # Southeast Africa routes covered by indian-ocean-voyages skill
]


# ---------------------------------------------------------------------------
# Returnees (post-1808 reverse migrations)
# ---------------------------------------------------------------------------

RETURNEE_ROUTES = [
    ("Caraïbes britanniques (Nova Scotia loyalists)", "Sierra Leone (Freetown)",
     "1792", 1_192, "Krio formation"),
    ("USA Sud (free Black emigrants)", "Liberia (Monrovia)", "1820-1860",
     16_000, "Americo-Liberian foundation"),
    ("Brésil (Bahia)", "Bight of Benin (Lagos, Ouidah, Porto-Novo)",
     "1835-1900", 8_000, "Aguda/Brazilian returnees"),
    ("Cuba (emancipados)", "Sierra Leone + Cape Verde", "1820-1865",
     20_000, "Slave Trade Suppression"),
    ("UK (abolitionist resettlement)", "Sierra Leone", "1787-1808",
     500, "Sierra Leone Company"),
]


# ---------------------------------------------------------------------------
# Data fetchers
# ---------------------------------------------------------------------------

DATASET_URLS = {
    "trans-atlantic": "https://www.slavevoyages.org/voyage/database#downloads",
    "intra-american": "https://www.slavevoyages.org/american/database#downloads",
    "african-origins": "https://www.african-origins.org/african-data/",
    "liberated": "https://liberatedafricans.org/",
    "enslaved": "https://www.slavevoyages.org/past/database#downloads",
}


# ---------------------------------------------------------------------------
# Geodesic distance
# ---------------------------------------------------------------------------

def haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in km between two points."""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * R * asin(sqrt(a))


def route_distance(src, dst):
    """Approximate distance for a curated source-destination pair."""
    if src not in PORT_CENTROIDS or dst not in PORT_CENTROIDS:
        return None
    lat1, lon1 = PORT_CENTROIDS[src]
    lat2, lon2 = PORT_CENTROIDS[dst]
    return haversine(lat1, lon1, lat2, lon2)


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------

def cmd_slavevoyages(args):
    """Process SlaveVoyages Trans-Atlantic CSV download."""
    if not Path(args.input).exists():
        print(f"Error: input file {args.input} not found", file=sys.stderr)
        print(f"Download from: {DATASET_URLS['trans-atlantic']}", file=sys.stderr)
        return 1
    df = pd.read_csv(args.input, low_memory=False)
    print(f"Loaded {len(df)} voyages from SlaveVoyages Trans-Atlantic")
    # Standard columns vary; try common names
    cols_year = next((c for c in df.columns
                       if "year" in c.lower() and "arriv" in c.lower()), None)
    cols_emb = next((c for c in df.columns
                      if "embark" in c.lower() or "majsel" in c.lower()), None)
    cols_dis = next((c for c in df.columns
                      if "disembark" in c.lower() or "majbu" in c.lower()), None)
    cols_vol = next((c for c in df.columns
                      if "slaximp" in c.lower() or "tot" in c.lower()), None)
    print(f"  Year col: {cols_year}, Embark: {cols_emb}, "
          f"Disembark: {cols_dis}, Volume: {cols_vol}")
    if args.year_min:
        df = df[df[cols_year].astype(float) >= args.year_min]
    if args.year_max:
        df = df[df[cols_year].astype(float) <= args.year_max]
    if args.region:
        df = df[df[cols_emb].astype(str).str.contains(args.region,
                                                      case=False, na=False)]
    if args.destination:
        df = df[df[cols_dis].astype(str).str.contains(args.destination,
                                                       case=False, na=False)]
    if args.aggregate == "decade":
        df["decade"] = (df[cols_year].astype(float) // 10) * 10
        agg = df.groupby(["decade", cols_emb, cols_dis])[cols_vol].sum().reset_index()
    else:
        agg = df[[cols_year, cols_emb, cols_dis, cols_vol]]
    if args.output:
        agg.to_csv(args.output, index=False)
        print(f"Saved {len(agg)} rows to {args.output}")
    else:
        print(agg.head(20).to_string())
    return 0


def cmd_routes(args):
    """Build origin-destination matrix or list from curated routes."""
    rows = []
    sources = args.source.split(",") if args.source else None
    dests = args.dest.split(",") if args.dest else None
    for r in CURATED_ROUTES:
        src, dst, period, vol, ports, sublineages = r
        if sources and not any(s.strip().lower() in src.lower() for s in sources):
            continue
        if dests and not any(d.strip().lower() in dst.lower() for d in dests):
            continue
        rows.append({
            "source_region": src,
            "destination_region": dst,
            "period": period,
            "estimated_volume": vol,
            "main_ports": ports,
            "expected_L5L6_sublineages": sublineages,
        })
    df = pd.DataFrame(rows)
    if args.format == "matrix":
        pivot = df.pivot_table(values="estimated_volume",
                               index="source_region",
                               columns="destination_region",
                               aggfunc="sum", fill_value=0)
        out = pivot.reset_index()
    else:
        out = df
    if args.output:
        out.to_csv(args.output, index=False)
        print(f"Saved {len(out)} rows to {args.output}")
    else:
        print(out.to_string())
    return 0


def cmd_returnees(args):
    """List documented reverse migration routes."""
    df = pd.DataFrame(RETURNEE_ROUTES, columns=[
        "source_region", "destination_region", "period",
        "estimated_volume", "note"
    ])
    if args.output:
        df.to_csv(args.output, index=False)
        print(f"Saved {len(df)} returnee routes to {args.output}")
    else:
        print(df.to_string())
    return 0


def cmd_timeline(args):
    """Build timeline of voyage volumes overlaid with TMRCA estimates."""
    if not HAS_PLOT:
        print("matplotlib required", file=sys.stderr)
        return 1
    df_routes = pd.DataFrame(CURATED_ROUTES, columns=[
        "source", "dest", "period", "volume", "ports", "sublineages"])
    df_routes["start"] = df_routes["period"].str.split("-").str[0].astype(int)
    df_routes["end"] = df_routes["period"].str.split("-").str[1].astype(int)
    fig, ax = plt.subplots(figsize=(12, 6))
    for i, row in df_routes.iterrows():
        ax.barh(i, row["end"] - row["start"], left=row["start"],
                color="#1f77b4", alpha=0.6,
                edgecolor="black", linewidth=0.5)
        ax.text(row["end"] + 5, i,
                f"{row['source']} → {row['dest']} "
                f"(~{row['volume']/1000:.0f}k)",
                va="center", fontsize=7)
    if args.tmrca and Path(args.tmrca).exists():
        df_t = pd.read_csv(args.tmrca)
        if "year_BP" in df_t.columns and "lineage" in df_t.columns:
            for _, row in df_t.iterrows():
                ax.axvline(row["year_BP"], color="red", linestyle="--",
                           alpha=0.5, label=row["lineage"])
            ax.legend(fontsize=8)
    ax.set_xlabel("Year CE")
    ax.set_ylabel("Curated routes")
    ax.set_yticks([])
    ax.set_xlim(1450, 1900)
    ax.set_title("Atlantic slave trade routes — curated timeline")
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    out = args.plot if args.plot else "atlantic_timeline.png"
    plt.tight_layout()
    plt.savefig(out, dpi=300)
    print(f"Saved timeline to {out}")
    return 0


def cmd_fetch(args):
    """Print download instructions for a dataset."""
    if args.source not in DATASET_URLS:
        print(f"Unknown source. Available: {list(DATASET_URLS.keys())}",
              file=sys.stderr)
        return 1
    print(f"Download {args.source} from:")
    print(f"  {DATASET_URLS[args.source]}")
    print("\nNote: SlaveVoyages provides CSV/SPSS exports under the")
    print("'Downloads' tab of each database page. Anonymous browsing is OK")
    print("for the public datasets.")
    return 0


def cmd_african_origins(args):
    """Stub for AfricanOrigins processing (requires manual CSV download)."""
    if not Path(args.input).exists():
        print(f"Download African Origins data first:", file=sys.stderr)
        print(f"  {DATASET_URLS['african-origins']}", file=sys.stderr)
        return 1
    df = pd.read_csv(args.input)
    print(f"Loaded {len(df)} African Origins records")
    if args.ethnicity:
        col = next((c for c in df.columns if "modern" in c.lower()
                    and "ethn" in c.lower()), None)
        if col:
            df = df[df[col].astype(str).str.contains(args.ethnicity,
                                                     case=False, na=False)]
    if args.year_min:
        col_y = next((c for c in df.columns if "year" in c.lower()), None)
        if col_y:
            df = df[df[col_y].astype(float) >= args.year_min]
    if args.output:
        df.to_csv(args.output, index=False)
        print(f"Saved {len(df)} to {args.output}")
    else:
        print(df.head(20).to_string())
    return 0


def cmd_liberated(args):
    """Stub for Liberated Africans Database."""
    if not Path(args.input).exists():
        print(f"Download Liberated Africans data first:", file=sys.stderr)
        print(f"  {DATASET_URLS['liberated']}", file=sys.stderr)
        return 1
    df = pd.read_csv(args.input)
    print(f"Loaded {len(df)} Liberated Africans records")
    if args.port:
        col = next((c for c in df.columns if "port" in c.lower()), None)
        if col:
            df = df[df[col].astype(str).str.contains(args.port,
                                                     case=False, na=False)]
    if args.year:
        col_y = next((c for c in df.columns if "year" in c.lower()), None)
        if col_y:
            df = df[(df[col_y].astype(float) >= args.year - 5) &
                    (df[col_y].astype(float) <= args.year + 5)]
    if args.output:
        df.to_csv(args.output, index=False)
        print(f"Saved {len(df)} to {args.output}")
    else:
        print(df.head(20).to_string())
    return 0


def cmd_intra_american(args):
    """Process Intra-American Voyages dataset."""
    if not Path(args.input).exists():
        print(f"Download Intra-American Voyages first:", file=sys.stderr)
        print(f"  {DATASET_URLS['intra-american']}", file=sys.stderr)
        return 1
    df = pd.read_csv(args.input, low_memory=False)
    print(f"Loaded {len(df)} Intra-American voyages")
    if args.output:
        df.to_csv(args.output, index=False)
    else:
        print(df.head(20).to_string())
    return 0


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Atlantic Voyages — historical maritime data for "
                    "MTBC L5/L6/L4 phylogeography studies"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("slavevoyages",
                       help="Process SlaveVoyages Trans-Atlantic CSV")
    p.add_argument("--input", "-i", required=True)
    p.add_argument("--output", "-o")
    p.add_argument("--region", help="Filter by source region")
    p.add_argument("--destination", help="Filter by destination")
    p.add_argument("--year-min", type=int)
    p.add_argument("--year-max", type=int)
    p.add_argument("--aggregate", choices=["decade", "century"])

    p = sub.add_parser("african-origins",
                       help="Process AfricanOrigins CSV")
    p.add_argument("--input", "-i", required=True)
    p.add_argument("--output", "-o")
    p.add_argument("--ethnicity")
    p.add_argument("--year-min", type=int)

    p = sub.add_parser("liberated",
                       help="Process Liberated Africans Database")
    p.add_argument("--input", "-i", required=True)
    p.add_argument("--output", "-o")
    p.add_argument("--port")
    p.add_argument("--year", type=int)

    p = sub.add_parser("intra-american",
                       help="Process Intra-American Voyages")
    p.add_argument("--input", "-i", required=True)
    p.add_argument("--output", "-o")

    p = sub.add_parser("returnees",
                       help="List documented reverse migration routes")
    p.add_argument("--output", "-o")

    p = sub.add_parser("routes",
                       help="Build O-D matrix from curated routes")
    p.add_argument("--source", help="Comma-separated source regions")
    p.add_argument("--dest", help="Comma-separated destination regions")
    p.add_argument("--format", choices=["od", "matrix"], default="od")
    p.add_argument("--output", "-o")

    p = sub.add_parser("timeline",
                       help="Build timeline overlay with TMRCA")
    p.add_argument("--tmrca", help="CSV with year_BP and lineage columns")
    p.add_argument("--plot", "-p")

    p = sub.add_parser("fetch",
                       help="Print download instructions for a dataset")
    p.add_argument("--source", required=True,
                   choices=list(DATASET_URLS.keys()))

    args = parser.parse_args()
    cmd_map = {
        "slavevoyages": cmd_slavevoyages,
        "african-origins": cmd_african_origins,
        "liberated": cmd_liberated,
        "intra-american": cmd_intra_american,
        "returnees": cmd_returnees,
        "routes": cmd_routes,
        "timeline": cmd_timeline,
        "fetch": cmd_fetch,
    }
    return cmd_map[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
