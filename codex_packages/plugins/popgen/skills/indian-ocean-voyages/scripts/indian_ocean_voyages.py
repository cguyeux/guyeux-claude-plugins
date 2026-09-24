#!/usr/bin/env python3
"""
Indian Ocean Voyages — historical maritime data for M. tuberculosis L1
phylogeography studies.

Wraps four open-data sources (ESTA, GLOBALISE, CLIWOC, SlaveVoyages-IO) and
provides curated routes and port centroids. Output schema is compatible with
the migration-data skill so that matrices can be combined for Mantel tests
against MTBC pairwise distances.

Usage:
    python3 indian_ocean_voyages.py esta --input esta.csv -o esta_routes.csv
    python3 indian_ocean_voyages.py globalise --input g.csv -o voc_routes.csv
    python3 indian_ocean_voyages.py cliwoc --input CLIWOC21.csv \
        --bbox -40,-20,20,120 -o traj.csv
    python3 indian_ocean_voyages.py slavevoyages-io --input tast.csv \
        --indian-ocean-only -o sv_io.csv
    python3 indian_ocean_voyages.py routes -o curated.csv
    python3 indian_ocean_voyages.py timeline --tmrca l1.csv -p l1_overlay.png
    python3 indian_ocean_voyages.py fetch --source esta
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
# Curated Indian Ocean port centroids (lat, lon)
# ---------------------------------------------------------------------------

PORT_CENTROIDS = {
    # East African coast
    "Mombasa": (-4.05, 39.67),
    "Kilwa": (-8.95, 39.51),
    "Mozambique Island": (-15.03, 40.74),
    "Quelimane": (-17.88, 36.89),
    "Sofala": (-20.17, 34.72),
    "Zanzibar": (-6.17, 39.20),
    "Lamu": (-2.27, 40.90),
    "Inhambane": (-23.86, 35.38),
    # Red Sea / Persian Gulf
    "Mocha": (13.32, 43.25),
    "Aden": (12.78, 45.04),
    "Muscat": (23.59, 58.55),
    "Bandar Abbas": (27.18, 56.27),
    "Hormuz": (27.10, 56.45),
    "Bushehr": (28.97, 50.84),
    # Indian subcontinent
    "Surat": (21.17, 72.83),
    "Bombay": (18.94, 72.84),
    "Goa": (15.30, 73.93),
    "Cochin": (9.97, 76.27),
    "Calicut": (11.25, 75.78),
    "Madras": (13.08, 80.27),
    "Pondichery": (11.93, 79.83),
    "Tranquebar": (11.03, 79.85),
    "Calcutta": (22.57, 88.36),
    "Chittagong": (22.36, 91.78),
    "Masulipatam": (16.18, 81.13),
    # Southeast Asia
    "Aceh": (5.55, 95.32),
    "Malacca": (2.20, 102.25),
    "Batavia": (-6.13, 106.81),
    "Macassar": (-5.13, 119.41),
    "Banda Neira": (-4.52, 129.90),
    "Ternate": (0.79, 127.36),
    "Manila": (14.59, 120.98),
    "Macao": (22.20, 113.55),
    "Canton": (23.13, 113.27),
    "Bantam": (-6.04, 106.16),
    "Ayutthaya": (14.35, 100.57),
    # Mascarene Islands
    "Port Louis": (-20.16, 57.50),
    "Saint-Denis": (-20.88, 55.45),
    "Port-Saint-Louis": (-4.62, 55.45),  # Mahé, Seychelles
    "Rodrigues": (-19.70, 63.42),
    # Cape & Southern Africa
    "Cape Town": (-33.92, 18.42),
    "Saldanha": (-33.00, 17.95),
    "Algoa Bay": (-33.96, 25.61),
    # Madagascar
    "Tamatave": (-18.15, 49.40),
    "Antongil Bay": (-15.50, 49.80),
    "Saint-Augustin": (-23.55, 43.75),
    "Diego-Suarez": (-12.27, 49.29),
    "Foulpointe": (-17.70, 49.50),
    "Fort Dauphin": (-25.03, 46.99),
    # Other key nodes
    "Lisbon": (38.71, -9.14),
    "Amsterdam": (52.37, 4.90),
    "London": (51.51, -0.13),
    "Salvador": (-12.97, -38.51),
    "Rio de Janeiro": (-22.91, -43.17),
    "Recife": (-8.05, -34.88),
}


# ---------------------------------------------------------------------------
# Curated routes : compiled from secondary literature
# ---------------------------------------------------------------------------

CURATED_ROUTES = [
    # Pre-European: Swahili-Arab network (volumes are scholarly estimates)
    {
        "from_port": "Kilwa", "to_port": "Muscat",
        "from_country": "Tanzania", "to_country": "Oman",
        "volume": 200000, "period_start": 800, "period_end": 1500,
        "source": "Swahili-Arab",
        "reference": "Sheriff 1987; Alpers 2014 (estimates)",
        "mtbc_link": "L1 ancestrale, échanges côtiers",
    },
    {
        "from_port": "Mombasa", "to_port": "Aden",
        "from_country": "Kenya", "to_country": "Yemen",
        "volume": 150000, "period_start": 800, "period_end": 1500,
        "source": "Swahili-Arab",
        "reference": "Sheriff 1987",
        "mtbc_link": "L1 ancestrale, échanges côtiers",
    },
    # VOC routes (1602-1799)
    {
        "from_port": "Mozambique Island", "to_port": "Cape Town",
        "from_country": "Mozambique", "to_country": "South Africa",
        "volume": 12000, "period_start": 1652, "period_end": 1799,
        "source": "VOC",
        "reference": "Worden 1985; Shell 1994; ESTA",
        "mtbc_link": "L1 vers colonie hollandaise du Cap",
    },
    {
        "from_port": "Madras", "to_port": "Batavia",
        "from_country": "India", "to_country": "Indonesia",
        "volume": 8000, "period_start": 1602, "period_end": 1799,
        "source": "VOC",
        "reference": "Vink 2003; van Rossum 2015",
        "mtbc_link": "L1 indienne vers Asie SE",
    },
    {
        "from_port": "Cochin", "to_port": "Batavia",
        "from_country": "India", "to_country": "Indonesia",
        "volume": 5000, "period_start": 1602, "period_end": 1799,
        "source": "VOC",
        "reference": "GLOBALISE; Vink 2003",
        "mtbc_link": "L1 indienne vers Java",
    },
    {
        "from_port": "Bengal", "to_port": "Batavia",
        "from_country": "India", "to_country": "Indonesia",
        "volume": 12000, "period_start": 1620, "period_end": 1750,
        "source": "VOC",
        "reference": "van Rossum 2015 ESTA",
        "mtbc_link": "L1 Bengale vers Asie SE",
    },
    {
        "from_port": "Macassar", "to_port": "Batavia",
        "from_country": "Indonesia", "to_country": "Indonesia",
        "volume": 25000, "period_start": 1660, "period_end": 1799,
        "source": "VOC",
        "reference": "Knaap 1996; ESTA",
        "mtbc_link": "Mouvements internes Asie SE",
    },
    {
        "from_port": "Banda Neira", "to_port": "Batavia",
        "from_country": "Indonesia", "to_country": "Indonesia",
        "volume": 7000, "period_start": 1621, "period_end": 1799,
        "source": "VOC",
        "reference": "Hanna 1978; ESTA",
        "mtbc_link": "Banda → Java post-massacre",
    },
    {
        "from_port": "Cape Town", "to_port": "Batavia",
        "from_country": "South Africa", "to_country": "Indonesia",
        "volume": 4000, "period_start": 1652, "period_end": 1799,
        "source": "VOC",
        "reference": "GLOBALISE; van Rossum 2015",
        "mtbc_link": "Échanges Cap-Java",
    },
    # French Mascarenes routes (1670-1810)
    {
        "from_port": "Antongil Bay", "to_port": "Port Louis",
        "from_country": "Madagascar", "to_country": "Mauritius",
        "volume": 45000, "period_start": 1721, "period_end": 1810,
        "source": "French",
        "reference": "Allen 2014; Filliot 1974",
        "mtbc_link": "L1 Madagascar → Île de France",
    },
    {
        "from_port": "Tamatave", "to_port": "Saint-Denis",
        "from_country": "Madagascar", "to_country": "Réunion",
        "volume": 35000, "period_start": 1670, "period_end": 1810,
        "source": "French",
        "reference": "Filliot 1974; Allen 2014",
        "mtbc_link": "L1 Madagascar → Bourbon (Réunion)",
    },
    {
        "from_port": "Mozambique Island", "to_port": "Port Louis",
        "from_country": "Mozambique", "to_country": "Mauritius",
        "volume": 60000, "period_start": 1770, "period_end": 1810,
        "source": "French",
        "reference": "Allen 2014",
        "mtbc_link": "Mozambique → Mascareignes (volume tardif)",
    },
    {
        "from_port": "Mozambique Island", "to_port": "Saint-Denis",
        "from_country": "Mozambique", "to_country": "Réunion",
        "volume": 35000, "period_start": 1770, "period_end": 1810,
        "source": "French",
        "reference": "Allen 2014",
        "mtbc_link": "Mozambique → Bourbon",
    },
    {
        "from_port": "Pondichery", "to_port": "Port Louis",
        "from_country": "India", "to_country": "Mauritius",
        "volume": 8000, "period_start": 1721, "period_end": 1810,
        "source": "French",
        "reference": "Allen 2014",
        "mtbc_link": "Engagés et esclaves indiens vers Mascareignes",
    },
    # Portuguese Estado da Índia (1500-1700)
    {
        "from_port": "Goa", "to_port": "Mozambique Island",
        "from_country": "India", "to_country": "Mozambique",
        "volume": 15000, "period_start": 1500, "period_end": 1700,
        "source": "Portuguese",
        "reference": "Boxer 1969; Newitt 1995",
        "mtbc_link": "Échanges bilatéraux Inde-Afrique de l'Est",
    },
    {
        "from_port": "Lisbon", "to_port": "Goa",
        "from_country": "Portugal", "to_country": "India",
        "volume": 5000, "period_start": 1498, "period_end": 1700,
        "source": "Portuguese",
        "reference": "Boxer 1969",
        "mtbc_link": "Carreira da Índia, vecteur L4 vers l'Inde",
    },
    {
        "from_port": "Macao", "to_port": "Malacca",
        "from_country": "China", "to_country": "Malaysia",
        "volume": 3000, "period_start": 1557, "period_end": 1641,
        "source": "Portuguese",
        "reference": "Souza 1986",
        "mtbc_link": "Réseau portugais Asie SE",
    },
    # British Indian Ocean (1750-1900)
    {
        "from_port": "Bombay", "to_port": "Mombasa",
        "from_country": "India", "to_country": "Kenya",
        "volume": 50000, "period_start": 1830, "period_end": 1920,
        "source": "British",
        "reference": "Metcalf 2007; Allen 2014",
        "mtbc_link": "Diaspora indienne en Afrique de l'Est, transport L1/L3",
    },
    {
        "from_port": "Calcutta", "to_port": "Port Louis",
        "from_country": "India", "to_country": "Mauritius",
        "volume": 460000, "period_start": 1834, "period_end": 1910,
        "source": "British",
        "reference": "Carter 1995; Tinker 1974",
        "mtbc_link": "Engagisme indien — vecteur majeur de L1/L3 aux Mascareignes",
    },
    {
        "from_port": "Madras", "to_port": "Port Louis",
        "from_country": "India", "to_country": "Mauritius",
        "volume": 25000, "period_start": 1834, "period_end": 1910,
        "source": "British",
        "reference": "Carter 1995",
        "mtbc_link": "Engagisme tamoul",
    },
    {
        "from_port": "Calcutta", "to_port": "Durban",
        "from_country": "India", "to_country": "South Africa",
        "volume": 152000, "period_start": 1860, "period_end": 1911,
        "source": "British",
        "reference": "Bhana & Brain 1990",
        "mtbc_link": "Engagisme Natal — diaspora indienne en Afrique du Sud",
    },
    # Late slave trade (1810-1850, post-Atlantic)
    {
        "from_port": "Mozambique Island", "to_port": "Rio de Janeiro",
        "from_country": "Mozambique", "to_country": "Brazil",
        "volume": 280000, "period_start": 1810, "period_end": 1851,
        "source": "Brazilian",
        "reference": "Florentino 1995; SlaveVoyages",
        "mtbc_link": "Origine de la L1 brésilienne (vs L5/L6 atlantique)",
    },
    {
        "from_port": "Quelimane", "to_port": "Rio de Janeiro",
        "from_country": "Mozambique", "to_country": "Brazil",
        "volume": 85000, "period_start": 1810, "period_end": 1851,
        "source": "Brazilian",
        "reference": "Florentino 1995; SlaveVoyages",
        "mtbc_link": "Voie complémentaire Mozambique-Brésil",
    },
    {
        "from_port": "Inhambane", "to_port": "Salvador",
        "from_country": "Mozambique", "to_country": "Brazil",
        "volume": 45000, "period_start": 1810, "period_end": 1851,
        "source": "Brazilian",
        "reference": "Florentino 1995",
        "mtbc_link": "Mozambique → Bahia",
    },
    # Omani-Zanzibar empire (1830-1873)
    {
        "from_port": "Kilwa", "to_port": "Zanzibar",
        "from_country": "Tanzania", "to_country": "Tanzania",
        "volume": 600000, "period_start": 1810, "period_end": 1873,
        "source": "Omani-Swahili",
        "reference": "Sheriff 1987; Cooper 1977",
        "mtbc_link": "Concentration L1 sur côte est-africaine",
    },
    {
        "from_port": "Zanzibar", "to_port": "Muscat",
        "from_country": "Tanzania", "to_country": "Oman",
        "volume": 50000, "period_start": 1832, "period_end": 1873,
        "source": "Omani-Swahili",
        "reference": "Sheriff 1987",
        "mtbc_link": "Empire omano-zanzibarite",
    },
]


# ---------------------------------------------------------------------------
# Curated timeline events for L1 dispersal
# ---------------------------------------------------------------------------

L1_TIMELINE_EVENTS = [
    {
        "event": "Austronesian settlement of Madagascar",
        "period_start": 500, "period_end": 1000,
        "from_region": "Borneo / Indonesian archipelago",
        "to_region": "Madagascar",
        "l1_link": "Possible introduction d'une L1 austronésienne à Madagascar",
        "reference": "Cox et al. 2012 PRSB; Pierron et al. 2017",
    },
    {
        "event": "Swahili-Arab maritime trade",
        "period_start": 800, "period_end": 1500,
        "from_region": "Arabia, Persian Gulf",
        "to_region": "East African coast",
        "l1_link": "Concentration de L1 sur côte est-africaine, échanges bilatéraux",
        "reference": "Sheriff 1987; Alpers 2014; Boivin et al. 2013",
    },
    {
        "event": "Estado da Índia (Portuguese)",
        "period_start": 1498, "period_end": 1700,
        "from_region": "Portugal",
        "to_region": "Goa, Mozambique, Malacca, Macao",
        "l1_link": "Connexion Inde-Afrique de l'Est-Asie SE par voie portugaise",
        "reference": "Boxer 1969; Newitt 1995",
    },
    {
        "event": "VOC trade network",
        "period_start": 1602, "period_end": 1799,
        "from_region": "Cap, Inde, Asie SE",
        "to_region": "Batavia hub",
        "l1_link": "Diffusion L1 entre l'Inde, l'Indonésie et le Cap",
        "reference": "Vink 2003; van Rossum 2015; GLOBALISE",
    },
    {
        "event": "French Mascarenes plantation economy",
        "period_start": 1670, "period_end": 1810,
        "from_region": "Madagascar, Mozambique, India",
        "to_region": "Île de France (Maurice), Bourbon (Réunion)",
        "l1_link": "L1 madagascienne et mozambicaine concentrée aux Mascareignes",
        "reference": "Allen 2014; Filliot 1974",
    },
    {
        "event": "Brazilian slave trade reorientation",
        "period_start": 1810, "period_end": 1851,
        "from_region": "Mozambique",
        "to_region": "Brazil (Rio, Salvador, Recife)",
        "l1_link": "Origine de la L1 brésilienne (post-1810, vs L5/L6 atlantique précoce)",
        "reference": "Florentino 1995; Eltis & Richardson 2010; SlaveVoyages",
    },
    {
        "event": "Omani-Zanzibar empire",
        "period_start": 1832, "period_end": 1873,
        "from_region": "Mainland East Africa",
        "to_region": "Zanzibar, Oman, Persian Gulf",
        "l1_link": "Brassage L1 le long de la côte swahili",
        "reference": "Sheriff 1987; Cooper 1977",
    },
    {
        "event": "British Indian indenture system",
        "period_start": 1834, "period_end": 1920,
        "from_region": "Calcutta, Madras",
        "to_region": "Mauritius, Natal, Fiji, Caribbean",
        "l1_link": "Diffusion massive de L1/L3 indiennes vers Mascareignes et Afrique du Sud",
        "reference": "Carter 1995; Tinker 1974; Bhana & Brain 1990",
    },
]


# ---------------------------------------------------------------------------
# Source URLs and download instructions
# ---------------------------------------------------------------------------

SOURCE_INFO = {
    "esta": {
        "name": "ESTA — Exploring Slave Trade in Asia",
        "host": "International Institute of Social History (IISG), Amsterdam",
        "url_landing": "https://esta.iisg.nl/",
        "url_dataverse": "https://datasets.iisg.amsterdam/dataverse/IOMASTD",
        "format": "CSV/TSV via Dataverse, also browsable web UI",
        "license": "CC-BY",
        "coverage": "~5 300 voyages, ~440 000 enslaved persons, ca. 1500-1900",
        "fields_expected": [
            "voyage_id", "year", "port_of_departure", "port_of_arrival",
            "embarked", "disembarked", "vessel_name", "vessel_nationality",
        ],
        "instruction": (
            "1. Visit https://datasets.iisg.amsterdam/dataverse/IOMASTD\n"
            "2. Pick the dataset (e.g. 'Dutch VOC Trade in Asian Slaves')\n"
            "3. Click 'Access Dataset' → download CSV or TSV\n"
            "4. Pass the file via --input"
        ),
    },
    "globalise": {
        "name": "GLOBALISE — VOC archives",
        "host": "Huygens Institute / KNAW",
        "url_landing": "https://globalise.huygens.knaw.nl/",
        "url_dataverse": "https://datasets.iisg.amsterdam/dataverse/globalise",
        "format": "CSV, RDF, transcribed text",
        "license": "CC-BY",
        "coverage": "5 million pages of VOC archives, 1602-1799, events, commodities, places",
        "fields_expected": [
            "event_id", "date", "place", "actors", "commodity", "type",
        ],
        "instruction": (
            "1. Visit https://datasets.iisg.amsterdam/dataverse/globalise\n"
            "2. Select dataset (Thesaurus, General Missives, Place names...)\n"
            "3. Download CSV/RDF\n"
            "4. Pass via --input. Note that GLOBALISE is event-centric, not\n"
            "   voyage-centric : aggregation by route requires extra processing."
        ),
    },
    "cliwoc": {
        "name": "CLIWOC — Climatological Database for the World's Oceans",
        "host": "DANS / Library of Congress / HistoricalClimatology.com",
        "url_landing": "https://www.historicalclimatology.com/cliwoc.html",
        "url_dataverse": "https://phys-techsciences.datastations.nl/dataset.xhtml?persistentId=doi:10.17026/dans-2bx-dutg",
        "format": "ODS (OpenOffice), TSV, Geopackage",
        "license": "Open / CC0",
        "coverage": "287 114 daily logbook entries, 1750-1854, Dutch/English/French/Spanish",
        "fields_expected": [
            "ShipName", "Nationality", "Year", "Month", "Day",
            "Lat3", "Lon3", "WindDirection", "WindForce",
        ],
        "instruction": (
            "1. Visit https://www.historicalclimatology.com/cliwoc.html\n"
            "2. Download CLIWOC release 2.1 (TSV format recommended)\n"
            "3. Pass via --input. Note that the file is large (~150 MB) ;\n"
            "   filter with --bbox and --period to keep memory reasonable."
        ),
    },
    "slavevoyages": {
        "name": "SlaveVoyages — Trans-Atlantic + Indian Ocean subset",
        "host": "Rice University → Harvard (transition ongoing 2025)",
        "url_landing": "https://www.slavevoyages.org/",
        "url_dataverse": "https://www.slavevoyages.org/voyage/database#downloads",
        "format": "CSV, Excel",
        "license": "CC-BY-NC",
        "coverage": "~36 000 voyages total, ~1 000 with East Africa / Indian Ocean stops",
        "fields_expected": [
            "voyageid", "yearam", "ptdepimp", "majbuypt", "majselpt",
            "tslavesd", "national",
        ],
        "instruction": (
            "1. Visit https://www.slavevoyages.org/voyage/database\n"
            "2. Use filters or click 'Download' → Excel/CSV\n"
            "3. Pass via --input with --indian-ocean-only to filter East Africa stops."
        ),
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in km between two points."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * asin(sqrt(a)) * 6371.0


def filter_by_period(df, period_str, start_col, end_col=None):
    """Filter rows whose period overlaps [period_start, period_end]."""
    if not period_str:
        return df
    a, b = [int(x) for x in period_str.split(":")]
    if end_col is None:
        end_col = start_col
    mask = (df[end_col] >= a) & (df[start_col] <= b)
    return df[mask].copy()


def find_port_centroid(name):
    """Best-effort match of a port name against PORT_CENTROIDS."""
    if not isinstance(name, str):
        return None
    name = name.strip()
    if name in PORT_CENTROIDS:
        return PORT_CENTROIDS[name]
    lname = name.lower()
    for k, v in PORT_CENTROIDS.items():
        if k.lower() == lname or k.lower() in lname or lname in k.lower():
            return v
    return None


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_routes(args):
    """Output the curated routes table."""
    df = pd.DataFrame(CURATED_ROUTES)
    if args.period:
        df = filter_by_period(df, args.period, "period_start", "period_end")
    if args.source and args.source != "all":
        df = df[df["source"].str.lower().str.contains(args.source.lower())]
    if args.output:
        df.to_csv(args.output, index=False)
        print(f"Wrote {len(df)} curated routes -> {args.output}",
              file=sys.stderr)
    else:
        print(df.to_csv(index=False))
    return df


def cmd_esta(args):
    """Aggregate ESTA voyages into routes or matrix."""
    if not args.input:
        print("ERROR: --input required (download from ESTA Dataverse)",
              file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(args.input)

    cols = {c.lower(): c for c in df.columns}
    dep = cols.get("port_of_departure") or cols.get("departure_port") \
        or cols.get("port_dep") or cols.get("from")
    arr = cols.get("port_of_arrival") or cols.get("arrival_port") \
        or cols.get("port_arr") or cols.get("to")
    yr = cols.get("year") or cols.get("yearam") or cols.get("voyage_year")
    vol = cols.get("disembarked") or cols.get("embarked") \
        or cols.get("number_of_enslaved") or cols.get("volume")

    if not (dep and arr):
        print("ERROR: cannot find departure/arrival columns. "
              f"Found columns: {list(df.columns)}", file=sys.stderr)
        sys.exit(1)

    if yr and args.period:
        a, b = [int(x) for x in args.period.split(":")]
        df = df[(df[yr] >= a) & (df[yr] <= b)].copy()
    if args.from_region:
        df = df[df[dep].astype(str).str.contains(
            args.from_region, case=False, na=False)]
    if args.to_region:
        df = df[df[arr].astype(str).str.contains(
            args.to_region, case=False, na=False)]

    if args.format == "matrix":
        agg = df.groupby([dep, arr]).size().reset_index(name="voyages")
        if vol:
            sums = df.groupby([dep, arr])[vol].sum().reset_index(name="volume")
            agg = agg.merge(sums, on=[dep, arr], how="left")
        pivot = agg.pivot_table(
            index=dep, columns=arr,
            values="volume" if vol else "voyages",
            fill_value=0)
        if args.output:
            pivot.to_csv(args.output)
        else:
            print(pivot.to_csv())
        return pivot

    agg = df.groupby([dep, arr]).agg(
        voyages=(dep, "size"),
        volume=(vol, "sum") if vol else (dep, "size"),
        period_start=(yr, "min") if yr else (dep, "size"),
        period_end=(yr, "max") if yr else (dep, "size"),
    ).reset_index()
    agg = agg.rename(columns={dep: "from_port", arr: "to_port"})
    agg["source"] = "ESTA"

    if args.output:
        agg.to_csv(args.output, index=False)
        print(f"Wrote {len(agg)} ESTA routes -> {args.output}", file=sys.stderr)
    else:
        print(agg.to_csv(index=False))
    return agg


def cmd_globalise(args):
    """Aggregate GLOBALISE events. Best-effort schema detection."""
    if not args.input:
        print("ERROR: --input required (download from GLOBALISE Dataverse)",
              file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(args.input)
    cols = {c.lower(): c for c in df.columns}

    place = cols.get("place") or cols.get("location") or cols.get("toponym")
    date = cols.get("date") or cols.get("year")
    cmd = cols.get("commodity") or cols.get("good") or cols.get("category")

    if args.commodity and cmd:
        df = df[df[cmd].astype(str).str.contains(
            args.commodity, case=False, na=False)]
    if args.period and date:
        try:
            years = pd.to_numeric(df[date].astype(str).str[:4],
                                  errors="coerce")
            a, b = [int(x) for x in args.period.split(":")]
            df = df[(years >= a) & (years <= b)].copy()
        except Exception:
            pass

    out_cols = [c for c in [place, date, cmd] if c]
    out = df[out_cols].copy() if out_cols else df.copy()
    out["source"] = "GLOBALISE"

    if args.output:
        out.to_csv(args.output, index=False)
        print(f"Wrote {len(out)} GLOBALISE rows -> {args.output}",
              file=sys.stderr)
    else:
        print(out.head(50).to_csv(index=False))
        print(f"({len(out)} total rows)", file=sys.stderr)
    return out


def cmd_cliwoc(args):
    """Filter CLIWOC daily positions."""
    if not args.input:
        print("ERROR: --input required (download CLIWOC release 2.1)",
              file=sys.stderr)
        sys.exit(1)
    sep = "\t" if args.input.endswith(".tsv") or args.input.endswith(".txt") \
        else ","
    df = pd.read_csv(args.input, sep=sep, low_memory=False,
                     on_bad_lines="skip")

    cols = {c.lower(): c for c in df.columns}
    lat = cols.get("lat3") or cols.get("latitude") or cols.get("lat")
    lon = cols.get("lon3") or cols.get("longitude") or cols.get("lon")
    yr = cols.get("year")
    nat = cols.get("nationality")
    ship = cols.get("shipname") or cols.get("ship")

    if not (lat and lon):
        print(f"ERROR: latitude/longitude columns not found. "
              f"Available: {list(df.columns)[:30]}", file=sys.stderr)
        sys.exit(1)

    df[lat] = pd.to_numeric(df[lat], errors="coerce")
    df[lon] = pd.to_numeric(df[lon], errors="coerce")
    df = df.dropna(subset=[lat, lon])

    if args.bbox:
        lat_min, lat_max, lon_min, lon_max = [
            float(x) for x in args.bbox.split(",")]
        df = df[(df[lat] >= lat_min) & (df[lat] <= lat_max)
                & (df[lon] >= lon_min) & (df[lon] <= lon_max)].copy()

    if args.period and yr:
        a, b = [int(x) for x in args.period.split(":")]
        df = df[(df[yr] >= a) & (df[yr] <= b)].copy()

    if args.nationality and args.nationality != "all" and nat:
        df = df[df[nat].astype(str).str.contains(
            args.nationality, case=False, na=False)]

    if args.format == "trajectories":
        keep = [c for c in [ship, nat, yr, lat, lon] if c]
        out = df[keep].copy()
        out["source"] = "CLIWOC"
        if args.output:
            out.to_csv(args.output, index=False)
            print(f"Wrote {len(out)} CLIWOC positions -> {args.output}",
                  file=sys.stderr)
        else:
            print(out.head(50).to_csv(index=False))
            print(f"({len(out)} total positions)", file=sys.stderr)
        return out

    print("ERROR: --format routes for CLIWOC requires trajectory clustering "
          "(not yet implemented). Use --format trajectories for now.",
          file=sys.stderr)
    sys.exit(1)


def cmd_slavevoyages_io(args):
    """Filter Trans-Atlantic dataset for Indian Ocean stops."""
    if not args.input:
        print("ERROR: --input required (download from slavevoyages.org)",
              file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(args.input, low_memory=False)
    cols = {c.lower(): c for c in df.columns}

    # SlaveVoyages typical column names
    dep = cols.get("ptdepimp") or cols.get("port_of_departure")
    buy = cols.get("majbuypt") or cols.get("major_purchase_point")
    sell = cols.get("majselpt") or cols.get("major_sale_point")
    yr = cols.get("yearam") or cols.get("year_voyage_began")
    vol = cols.get("tslavesd") or cols.get("disembarked_total")

    if not (buy and sell):
        print(f"ERROR: cannot find purchase/sale columns. "
              f"Got: {list(df.columns)[:30]}", file=sys.stderr)
        sys.exit(1)

    if args.indian_ocean_only:
        # Indian Ocean / East Africa keywords
        io_keywords = (
            "Mozambique|Madagascar|Zanzibar|Mombasa|Kilwa|Quelimane|"
            "Mascarene|Mauritius|Réunion|Bourbon|East Africa|"
            "Indian Ocean|Sofala|Inhambane|Tamatave|Antongil"
        )
        mask = (
            df[buy].astype(str).str.contains(io_keywords, case=False,
                                             na=False, regex=True)
            | df[sell].astype(str).str.contains(io_keywords, case=False,
                                                na=False, regex=True)
        )
        if dep:
            mask = mask | df[dep].astype(str).str.contains(
                io_keywords, case=False, na=False, regex=True)
        df = df[mask].copy()

    agg = df.groupby([buy, sell]).agg(
        voyages=(buy, "size"),
        volume=(vol, "sum") if vol else (buy, "size"),
        period_start=(yr, "min") if yr else (buy, "size"),
        period_end=(yr, "max") if yr else (buy, "size"),
    ).reset_index()
    agg = agg.rename(columns={buy: "from_port", sell: "to_port"})
    agg["source"] = "SlaveVoyages-IO"

    if args.output:
        agg.to_csv(args.output, index=False)
        print(f"Wrote {len(agg)} routes -> {args.output}", file=sys.stderr)
    else:
        print(agg.to_csv(index=False))
    return agg


def cmd_timeline(args):
    """Build a chronological timeline figure with optional TMRCA overlay."""
    df = pd.DataFrame(L1_TIMELINE_EVENTS)
    if args.period:
        df = filter_by_period(df, args.period, "period_start", "period_end")

    if args.output:
        df.to_csv(args.output, index=False)
        print(f"Wrote {len(df)} timeline events -> {args.output}",
              file=sys.stderr)

    if args.plot:
        if not HAS_PLOT:
            print("ERROR: matplotlib not installed", file=sys.stderr)
            return df
        fig, ax = plt.subplots(figsize=(12, len(df) * 0.5 + 2))
        for i, row in df.iterrows():
            ax.barh(i, row["period_end"] - row["period_start"],
                    left=row["period_start"], height=0.7, alpha=0.7)
            ax.text(row["period_start"], i, " " + row["event"],
                    va="center", fontsize=9)
        ax.set_yticks([])
        ax.set_xlabel("Year")
        ax.set_title("Indian Ocean voyages — chronologie pour L1")

        if args.tmrca and Path(args.tmrca).exists():
            tmrca = pd.read_csv(args.tmrca)
            for _, t in tmrca.iterrows():
                year = t.get("year") or t.get("tmrca")
                label = t.get("label") or t.get("lineage") or ""
                if pd.notna(year):
                    ax.axvline(year, color="red", linestyle="--", alpha=0.6)
                    ax.text(year, len(df) - 0.5, str(label),
                            rotation=90, color="red", fontsize=8,
                            va="top")

        plt.tight_layout()
        plt.savefig(args.plot, dpi=200)
        print(f"Wrote figure -> {args.plot}", file=sys.stderr)
    return df


def cmd_fetch(args):
    """Print download instructions for a source."""
    src = args.source.lower()
    if src not in SOURCE_INFO:
        print(f"Unknown source: {src}. Available: {list(SOURCE_INFO.keys())}",
              file=sys.stderr)
        sys.exit(1)
    info = SOURCE_INFO[src]
    print(json.dumps(info, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        description="Indian Ocean Voyages — historical maritime data for "
                    "M. tuberculosis L1 phylogeography.")
    sub = p.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-o", "--output", help="Output CSV")
    common.add_argument("-p", "--plot", help="Output figure (PNG/PDF)")
    common.add_argument("--summary", action="store_true",
                        help="Print JSON summary")

    p_esta = sub.add_parser("esta", parents=[common],
                            help="Parse ESTA voyages CSV")
    p_esta.add_argument("--input", required=True)
    p_esta.add_argument("--period")
    p_esta.add_argument("--from-region")
    p_esta.add_argument("--to-region")
    p_esta.add_argument("--format", default="routes",
                        choices=["routes", "matrix"])

    p_glo = sub.add_parser("globalise", parents=[common],
                           help="Parse GLOBALISE events")
    p_glo.add_argument("--input", required=True)
    p_glo.add_argument("--commodity")
    p_glo.add_argument("--period")
    p_glo.add_argument("--format", default="events",
                       choices=["routes", "events"])

    p_cli = sub.add_parser("cliwoc", parents=[common],
                           help="Parse CLIWOC logbook positions")
    p_cli.add_argument("--input", required=True)
    p_cli.add_argument("--bbox", help="lat_min,lat_max,lon_min,lon_max")
    p_cli.add_argument("--period")
    p_cli.add_argument("--nationality", default="all")
    p_cli.add_argument("--format", default="trajectories",
                       choices=["trajectories", "routes"])

    p_sv = sub.add_parser("slavevoyages-io", parents=[common],
                          help="Filter TAST for Indian Ocean voyages")
    p_sv.add_argument("--input", required=True)
    p_sv.add_argument("--indian-ocean-only", action="store_true")

    p_routes = sub.add_parser("routes", parents=[common],
                              help="Output curated routes table")
    p_routes.add_argument("--period")
    p_routes.add_argument("--source", default="all")

    p_tl = sub.add_parser("timeline", parents=[common],
                          help="Build curated timeline (with TMRCA overlay)")
    p_tl.add_argument("--period")
    p_tl.add_argument("--tmrca", help="CSV of TMRCA estimates")

    p_fetch = sub.add_parser("fetch", parents=[common],
                             help="Print download URLs and instructions")
    p_fetch.add_argument("--source", required=True,
                         choices=list(SOURCE_INFO.keys()))

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    handlers = {
        "esta": cmd_esta,
        "globalise": cmd_globalise,
        "cliwoc": cmd_cliwoc,
        "slavevoyages-io": cmd_slavevoyages_io,
        "routes": cmd_routes,
        "timeline": cmd_timeline,
        "fetch": cmd_fetch,
    }
    handlers[args.command](args)


if __name__ == "__main__":
    main()
