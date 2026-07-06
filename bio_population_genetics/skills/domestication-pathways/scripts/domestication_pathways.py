#!/usr/bin/env python3
"""
Domestication Pathways — centres, routes and chronologies for MTBC
co-evolution studies.

Wraps zooarchaeological (ABMAP), archaeobotanical (ADEMNES, BRAIN), ancient
DNA (AADR) and radiocarbon (p3k14c, CONTEXT, AgriChange) open-data sources,
and provides curated tables of origin centres, dispersal routes and timeline
events linked to MTBC zoonotic lineages and to the emergence of M. tuberculosis
sensu stricto from a M. canettii-like ancestor.

Usage:
    python3 domestication_pathways.py centers --type animal -o c.csv
    python3 domestication_pathways.py routes --species cattle -o r.csv
    python3 domestication_pathways.py timeline --tmrca tmrca.csv -p t.png
    python3 domestication_pathways.py parse abmap --input abmap.csv -o out.csv
    python3 domestication_pathways.py fetch --source aadr
"""

import argparse
import json
import sys
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
# Curated origin centres
# ---------------------------------------------------------------------------

ANIMAL_CENTERS = [
    {"taxon": "Capra hircus", "common": "Goat",
     "center": "Zagros / Fertile Crescent", "lat": 35.0, "lon": 47.0,
     "period_start": -10500, "period_end": -9500,
     "region": "Old World",
     "mtbc_link": "M. caprae",
     "reference": "Daly et al. 2018 Science; Zeder 2008"},
    {"taxon": "Ovis aries", "common": "Sheep",
     "center": "Eastern Anatolia / Fertile Crescent",
     "lat": 38.0, "lon": 43.0,
     "period_start": -10500, "period_end": -9500,
     "region": "Old World",
     "mtbc_link": "M. caprae",
     "reference": "Chessa et al. 2009 Science; Zeder 2008"},
    {"taxon": "Bos taurus", "common": "Cattle (taurine)",
     "center": "Middle Euphrates Valley",
     "lat": 36.5, "lon": 38.5,
     "period_start": -10800, "period_end": -10200,
     "region": "Old World",
     "mtbc_link": "M. bovis (taurine lineages)",
     "reference": "Bollongino et al. 2012; Helmer et al. 2005"},
    {"taxon": "Bos indicus", "common": "Cattle (indicine / zebu)",
     "center": "Indus Valley",
     "lat": 28.0, "lon": 70.0,
     "period_start": -8000, "period_end": -7000,
     "region": "Old World",
     "mtbc_link": "M. bovis (indicine lineages)",
     "reference": "Chen et al. 2010; Loftus et al. 1994"},
    {"taxon": "Sus scrofa (Anatolian)", "common": "Pig (Near East)",
     "center": "Anatolia",
     "lat": 39.0, "lon": 32.0,
     "period_start": -10500, "period_end": -8500,
     "region": "Old World",
     "mtbc_link": "(no documented MTBC link)",
     "reference": "Larson et al. 2007 PNAS"},
    {"taxon": "Sus scrofa (Chinese)", "common": "Pig (East Asia)",
     "center": "Yellow / Yangtze valleys",
     "lat": 32.0, "lon": 110.0,
     "period_start": -10500, "period_end": -8500,
     "region": "Old World",
     "mtbc_link": "(no documented MTBC link)",
     "reference": "Larson et al. 2007 PNAS"},
    {"taxon": "Equus caballus", "common": "Horse",
     "center": "Pontic-Caspian steppe (Botai/Yamnaya)",
     "lat": 50.0, "lon": 55.0,
     "period_start": -3700, "period_end": -3000,
     "region": "Old World",
     "mtbc_link": "(no MTBC link)",
     "reference": "Librado et al. 2021 Nature; Outram et al. 2009"},
    {"taxon": "Equus asinus", "common": "Donkey",
     "center": "NE Africa (Nubia / Egypt)",
     "lat": 22.0, "lon": 32.0,
     "period_start": -5000, "period_end": -4000,
     "region": "Old World",
     "mtbc_link": "rare M. bovis cases",
     "reference": "Beja-Pereira et al. 2004; Rossel et al. 2008"},
    {"taxon": "Camelus dromedarius", "common": "Dromedary",
     "center": "SE Arabia",
     "lat": 22.0, "lon": 55.0,
     "period_start": -3000, "period_end": -1000,
     "region": "Old World",
     "mtbc_link": "M. bovis cases reported",
     "reference": "Almathen et al. 2016 PNAS"},
    {"taxon": "Camelus bactrianus", "common": "Bactrian camel",
     "center": "Central Asia",
     "lat": 42.0, "lon": 72.0,
     "period_start": -2500, "period_end": -1500,
     "region": "Old World",
     "mtbc_link": "M. bovis cases reported",
     "reference": "Burger 2016"},
    {"taxon": "Bos grunniens", "common": "Yak",
     "center": "Tibetan Plateau",
     "lat": 33.0, "lon": 90.0,
     "period_start": -3000, "period_end": -2000,
     "region": "Old World",
     "mtbc_link": "M. bovis suspected",
     "reference": "Qiu et al. 2012; Wang et al. 2014"},
    {"taxon": "Bubalus bubalis", "common": "Water buffalo",
     "center": "Indus / South China",
     "lat": 28.0, "lon": 70.0,
     "period_start": -4000, "period_end": -3000,
     "region": "Old World",
     "mtbc_link": "M. bovis reported",
     "reference": "Kumar et al. 2007"},
    {"taxon": "Lama glama", "common": "Llama",
     "center": "Andean Puna",
     "lat": -16.0, "lon": -69.0,
     "period_start": -5000, "period_end": -3500,
     "region": "New World",
     "mtbc_link": "M. tuberculosis pinnipedii lineage (related to seals)",
     "reference": "Wheeler 1995; Bos et al. 2014 Nature (pre-Columbian TB)"},
    {"taxon": "Vicugna pacos", "common": "Alpaca",
     "center": "Andean Puna",
     "lat": -16.0, "lon": -69.0,
     "period_start": -5000, "period_end": -3500,
     "region": "New World",
     "mtbc_link": "(no documented MTBC link)",
     "reference": "Wheeler 1995"},
    {"taxon": "Meleagris gallopavo", "common": "Turkey",
     "center": "Mesoamerica",
     "lat": 19.0, "lon": -99.0,
     "period_start": -2000, "period_end": 0,
     "region": "New World",
     "mtbc_link": "(no MTBC link)",
     "reference": "Speller et al. 2010 PNAS"},
    {"taxon": "Gallus gallus", "common": "Chicken",
     "center": "SE Asia (Mekong valley)",
     "lat": 14.0, "lon": 105.0,
     "period_start": -6000, "period_end": -3000,
     "region": "Old World",
     "mtbc_link": "(no human MTBC link)",
     "reference": "Wang et al. 2020; Peters et al. 2022"},
    {"taxon": "Rangifer tarandus", "common": "Reindeer",
     "center": "Siberia + Fennoscandia",
     "lat": 65.0, "lon": 80.0,
     "period_start": -1000, "period_end": 500,
     "region": "Old World",
     "mtbc_link": "M. caprae cases reported",
     "reference": "Røed et al. 2008; Bjørnstad et al. 2013"},
]

PLANT_CENTERS = [
    {"taxon": "Triticum monococcum/dicoccum", "common": "Einkorn / Emmer wheat",
     "center": "Karaca Dağ (SE Turkey)", "lat": 37.5, "lon": 39.5,
     "period_start": -10500, "period_end": -9500,
     "region": "Old World",
     "mtbc_link": "Sedentarisation context for MTBC emergence",
     "reference": "Heun et al. 1997 Science; Fuller et al. 2014"},
    {"taxon": "Hordeum vulgare", "common": "Barley",
     "center": "Fertile Crescent", "lat": 36.0, "lon": 38.0,
     "period_start": -10500, "period_end": -9500,
     "region": "Old World",
     "mtbc_link": "Sedentarisation context",
     "reference": "Badr et al. 2000; Fuller et al. 2014"},
    {"taxon": "Lens / Pisum / Cicer", "common": "Lentil/pea/chickpea",
     "center": "Fertile Crescent", "lat": 36.0, "lon": 38.0,
     "period_start": -10500, "period_end": -9500,
     "region": "Old World",
     "mtbc_link": "Founder crop package",
     "reference": "Zohary et al. 2012"},
    {"taxon": "Oryza sativa japonica", "common": "Rice (japonica)",
     "center": "Middle Yangtze", "lat": 30.5, "lon": 113.0,
     "period_start": -9000, "period_end": -7000,
     "region": "Old World",
     "mtbc_link": "Sedentarisation East Asia",
     "reference": "Fuller et al. 2009; Gross & Zhao 2014 PNAS"},
    {"taxon": "Oryza sativa indica", "common": "Rice (indica)",
     "center": "Ganges / Indus", "lat": 25.0, "lon": 80.0,
     "period_start": -7000, "period_end": -5000,
     "region": "Old World",
     "mtbc_link": "Sedentarisation South Asia",
     "reference": "Fuller et al. 2010; Wang et al. 2018"},
    {"taxon": "Setaria italica / Panicum miliaceum",
     "common": "Foxtail / broomcorn millet",
     "center": "Yellow River basin", "lat": 41.0, "lon": 120.0,
     "period_start": -8000, "period_end": -6000,
     "region": "Old World",
     "mtbc_link": "Sedentarisation East Asia",
     "reference": "Lu et al. 2009 PNAS; Zhao 2011"},
    {"taxon": "Pennisetum glaucum", "common": "Pearl millet",
     "center": "West African Sahel", "lat": 16.0, "lon": -2.0,
     "period_start": -4500, "period_end": -3500,
     "region": "Old World",
     "mtbc_link": "Bantu founder crop, co-dispersed with cattle",
     "reference": "Manning et al. 2011; Burgarella et al. 2018"},
    {"taxon": "Sorghum bicolor", "common": "Sorghum",
     "center": "Central Sahel", "lat": 14.0, "lon": 25.0,
     "period_start": -5000, "period_end": -3500,
     "region": "Old World",
     "mtbc_link": "Bantu founder crop",
     "reference": "Winchell et al. 2017; Fuller & Stevens 2018"},
    {"taxon": "Eragrostis tef", "common": "Tef",
     "center": "Ethiopian highlands", "lat": 9.0, "lon": 39.0,
     "period_start": -3000, "period_end": -1000,
     "region": "Old World",
     "mtbc_link": "Highland Ethiopian context (L7)",
     "reference": "D'Andrea 2008; Hassen et al. 2018"},
    {"taxon": "Zea mays", "common": "Maize",
     "center": "Balsas Basin (Mesoamerica)", "lat": 18.0, "lon": -100.0,
     "period_start": -9000, "period_end": -6000,
     "region": "New World",
     "mtbc_link": "Pre-Columbian sedentarisation",
     "reference": "Piperno et al. 2009 PNAS; Matsuoka et al. 2002"},
    {"taxon": "Phaseolus / Cucurbita", "common": "Bean / squash",
     "center": "Mesoamerica + Andes", "lat": 19.0, "lon": -99.0,
     "period_start": -8000, "period_end": -5000,
     "region": "New World",
     "mtbc_link": "(no MTBC link)",
     "reference": "Smith 1997; Bitocchi et al. 2012"},
    {"taxon": "Solanum tuberosum", "common": "Potato",
     "center": "Lake Titicaca / Andes", "lat": -16.0, "lon": -69.0,
     "period_start": -8000, "period_end": -5000,
     "region": "New World",
     "mtbc_link": "Andean sedentarisation, pinnipedii contact",
     "reference": "Spooner et al. 2005 PNAS"},
    {"taxon": "Chenopodium quinoa", "common": "Quinoa",
     "center": "Andes", "lat": -16.0, "lon": -68.0,
     "period_start": -5000, "period_end": -3000,
     "region": "New World",
     "mtbc_link": "(no MTBC link)",
     "reference": "Bruno 2006"},
    {"taxon": "Manihot esculenta", "common": "Manioc / cassava",
     "center": "SW Amazonia", "lat": -10.0, "lon": -65.0,
     "period_start": -8000, "period_end": -6000,
     "region": "New World",
     "mtbc_link": "(no MTBC link)",
     "reference": "Olsen & Schaal 1999 PNAS"},
    {"taxon": "Ipomoea batatas", "common": "Sweet potato",
     "center": "Tropical Americas", "lat": -10.0, "lon": -75.0,
     "period_start": -3000, "period_end": -1000,
     "region": "New World",
     "mtbc_link": "(no MTBC link)",
     "reference": "Roullier et al. 2013 PNAS"},
    {"taxon": "Musa / Saccharum / Colocasia",
     "common": "Banana / sugarcane / taro",
     "center": "Kuk Swamp (New Guinea)", "lat": -5.8, "lon": 144.3,
     "period_start": -7000, "period_end": -5000,
     "region": "Old World",
     "mtbc_link": "Austronesian co-dispersal package",
     "reference": "Denham et al. 2003 Science; Fuller et al. 2014"},
    {"taxon": "Coffea arabica", "common": "Coffee",
     "center": "Ethiopian highlands", "lat": 9.0, "lon": 39.0,
     "period_start": 600, "period_end": 1000,
     "region": "Old World",
     "mtbc_link": "(historical commodity, no direct MTBC link)",
     "reference": "Anthony et al. 2002"},
]

HUMAN_CENTERS = [
    {"taxon": "Homo sapiens (PPNB)", "common": "Levant Neolithic",
     "center": "Jericho / Mureybet", "lat": 32.0, "lon": 36.0,
     "period_start": -10500, "period_end": -8500,
     "region": "Old World",
     "mtbc_link": "Putative emergence context for modern MTBC",
     "reference": "Bar-Yosef 2002; Goring-Morris & Belfer-Cohen 2011"},
    {"taxon": "Homo sapiens (Anatolian N)", "common": "Anatolian Neolithic",
     "center": "Çatalhöyük / Aşıklı", "lat": 38.0, "lon": 33.0,
     "period_start": -8500, "period_end": -7000,
     "region": "Old World",
     "mtbc_link": "Source of European Neolithic farmers (LBK, Cardial)",
     "reference": "Hofmanová et al. 2016 PNAS; Lazaridis et al. 2016"},
    {"taxon": "Homo sapiens (Yangtze N)", "common": "Yangtze Neolithic",
     "center": "Liangzhu / Daxi", "lat": 30.0, "lon": 113.0,
     "period_start": -7000, "period_end": -4000,
     "region": "Old World",
     "mtbc_link": "East Asian sedentarisation",
     "reference": "Yang et al. 2020 Science"},
    {"taxon": "Homo sapiens (Indus N)", "common": "Indus Neolithic",
     "center": "Mehrgarh", "lat": 29.0, "lon": 67.0,
     "period_start": -7000, "period_end": -5000,
     "region": "Old World",
     "mtbc_link": "South Asian sedentarisation context",
     "reference": "Jarrige et al. 2008; Narasimhan et al. 2019"},
    {"taxon": "Homo sapiens (Sahel N)", "common": "Sahel Neolithic",
     "center": "Dhar Tichitt / Kintampo", "lat": 17.0, "lon": -10.0,
     "period_start": -4000, "period_end": -2000,
     "region": "Old World",
     "mtbc_link": "Bantu source area",
     "reference": "Manning 2011; Stojanowski 2013"},
    {"taxon": "Homo sapiens (Nile N)", "common": "Nile Valley Neolithic",
     "center": "Fayum / Merimde", "lat": 29.5, "lon": 31.0,
     "period_start": -6000, "period_end": -4500,
     "region": "Old World",
     "mtbc_link": "Egyptian context, ancient TB cases (mummies)",
     "reference": "Wendrich 2010; Zink et al. 2003"},
    {"taxon": "Homo sapiens (Ethiopian)", "common": "Ethiopian highlands",
     "center": "(pre-Aksumite)", "lat": 9.0, "lon": 39.0,
     "period_start": -3000, "period_end": -500,
     "region": "Old World",
     "mtbc_link": "Highland L7 context",
     "reference": "D'Andrea 2008; Phillipson 2012"},
    {"taxon": "Homo sapiens (Mesoam)", "common": "Mesoamerican Formative",
     "center": "Mexico Valley / Oaxaca", "lat": 19.0, "lon": -99.0,
     "period_start": -8000, "period_end": -3000,
     "region": "New World",
     "mtbc_link": "Pre-Columbian context (limited human MTBC)",
     "reference": "Flannery 1986; Piperno 2011"},
    {"taxon": "Homo sapiens (Andean)", "common": "Andean Formative",
     "center": "Lake Titicaca basin", "lat": -16.0, "lon": -69.0,
     "period_start": -8000, "period_end": -3000,
     "region": "New World",
     "mtbc_link": "Pinnipedii TB pre-Columbian (Bos et al. 2014)",
     "reference": "Aldenderfer 2008; Bos et al. 2014 Nature"},
    {"taxon": "Homo sapiens (Amazon)", "common": "Amazonian Formative",
     "center": "Llanos de Mojos", "lat": -14.0, "lon": -65.0,
     "period_start": -8000, "period_end": -3000,
     "region": "New World",
     "mtbc_link": "(no MTBC link)",
     "reference": "Lombardo et al. 2020 Nature"},
    {"taxon": "Homo sapiens (Papua)", "common": "Highland New Guinea",
     "center": "Kuk Swamp", "lat": -5.8, "lon": 144.3,
     "period_start": -7000, "period_end": -4000,
     "region": "Old World",
     "mtbc_link": "(no MTBC link)",
     "reference": "Denham et al. 2003 Science"},
    {"taxon": "Homo sapiens (Eastern Woodlands)",
     "common": "Eastern North America", "center": "Middle Mississippi",
     "lat": 38.0, "lon": -90.0,
     "period_start": -3000, "period_end": -1000,
     "region": "New World",
     "mtbc_link": "Pre-Columbian Eastern Woodlands",
     "reference": "Smith 2006 PNAS"},
]

# ---------------------------------------------------------------------------
# Curated dispersal routes
# ---------------------------------------------------------------------------

CURATED_ROUTES = [
    {"from_region": "Fertile Crescent", "to_region": "Western Anatolia",
     "taxon": "cattle, sheep, goat, wheat, barley", "mechanism": "demic",
     "period_start": -7000, "period_end": -6500,
     "source_network": "pre-LBK",
     "reference": "Hofmanová et al. 2016 PNAS",
     "mtbc_link": "M. caprae, M. bovis diffusion to Anatolia"},
    {"from_region": "Western Anatolia", "to_region": "Balkans",
     "taxon": "cattle, sheep, goat, wheat, barley", "mechanism": "demic",
     "period_start": -6500, "period_end": -6000,
     "source_network": "Starčevo / pre-LBK",
     "reference": "Mathieson et al. 2018 Nature",
     "mtbc_link": "M. bovis + M. caprae arrive in SE Europe"},
    {"from_region": "Balkans", "to_region": "Central Europe",
     "taxon": "cattle, sheep, goat, cereals", "mechanism": "demic",
     "period_start": -5500, "period_end": -4900,
     "source_network": "Linearbandkeramik (LBK)",
     "reference": "Bramanti et al. 2009 Science; Haak et al. 2015 Nature",
     "mtbc_link": "Demic spread of M. bovis/M. caprae; possibly M. tuberculosis"},
    {"from_region": "Western Anatolia", "to_region": "Western Mediterranean",
     "taxon": "sheep, goat, cereals", "mechanism": "maritime+demic",
     "period_start": -6000, "period_end": -5500,
     "source_network": "Cardial / Impressed Ware",
     "reference": "Olalde et al. 2015 MBE; Manen et al. 2019",
     "mtbc_link": "M. caprae, M. bovis introduced into Iberia / S. France"},
    {"from_region": "Mesopotamia", "to_region": "NW India",
     "taxon": "cattle taurine, wheat, barley", "mechanism": "mixed",
     "period_start": -5000, "period_end": -3000,
     "source_network": "(pre-Indus)",
     "reference": "Fuller 2006; Petrie & Bates 2017",
     "mtbc_link": "Taurine × indicine introgression in cattle"},
    {"from_region": "Indus Valley", "to_region": "Southeast Asia",
     "taxon": "cattle indicine, water buffalo", "mechanism": "demic",
     "period_start": -3000, "period_end": -1500,
     "source_network": "Bronze Age",
     "reference": "Loftus et al. 1994; Bellwood 2013",
     "mtbc_link": "M. bovis indicine lineages in SE Asia"},
    {"from_region": "Yangtze", "to_region": "Southeast Asia",
     "taxon": "rice japonica, pig", "mechanism": "demic",
     "period_start": -4000, "period_end": -2000,
     "source_network": "Austroasiatic",
     "reference": "Fuller et al. 2011; Bellwood 2013",
     "mtbc_link": "(no direct MTBC link)"},
    {"from_region": "Taiwan", "to_region": "Polynesia / Madagascar",
     "taxon": "pig, chicken, taro, banana", "mechanism": "maritime",
     "period_start": -3000, "period_end": 1000,
     "source_network": "Austronesian / Lapita",
     "reference": "Gray et al. 2009 Science; Skoglund et al. 2016 Nature",
     "mtbc_link": "L1 link to Madagascar (cf. indian-ocean-voyages)"},
    {"from_region": "West African Sahel", "to_region": "Central Africa",
     "taxon": "pearl millet, sorghum, cattle", "mechanism": "demic",
     "period_start": -3000, "period_end": -1000,
     "source_network": "Bantu Stage I",
     "reference": "Russell et al. 2014; Grollemund et al. 2015 PNAS",
     "mtbc_link": "L5/L6 + M. bovis Africa diffusion"},
    {"from_region": "Central Africa", "to_region": "Southern Africa",
     "taxon": "cattle, sorghum, millet", "mechanism": "demic",
     "period_start": -1000, "period_end": 500,
     "source_network": "Bantu Stage II",
     "reference": "Grollemund et al. 2015 PNAS; Russell et al. 2014",
     "mtbc_link": "M. bovis / M. tuberculosis arrival in Southern Africa"},
    {"from_region": "Pontic-Caspian Steppe", "to_region": "Northern Europe",
     "taxon": "horse, dairying, secondary products", "mechanism": "demic+cultural",
     "period_start": -3000, "period_end": -2000,
     "source_network": "Yamnaya / Corded Ware",
     "reference": "Haak et al. 2015 Nature; Allentoft et al. 2015 Nature",
     "mtbc_link": "Cattle population mixing Eurasia"},
    {"from_region": "Egypt", "to_region": "Central Sahara",
     "taxon": "cattle, sheep, goat", "mechanism": "mixed",
     "period_start": -7000, "period_end": -5000,
     "source_network": "Green Sahara",
     "reference": "Manning & Timpson 2014; di Lernia 2018",
     "mtbc_link": "North African cattle, M. bovis"},
    {"from_region": "Central Sahara", "to_region": "Sahel",
     "taxon": "cattle, sheep, goat", "mechanism": "demic",
     "period_start": -5000, "period_end": -3000,
     "source_network": "Pastoral Sahara",
     "reference": "di Lernia 2018; Holl 1998",
     "mtbc_link": "Zoonotic diffusion to Sahel"},
    {"from_region": "Egypt", "to_region": "Nubia / Horn of Africa",
     "taxon": "cattle, donkey, cereals", "mechanism": "mixed",
     "period_start": -4000, "period_end": -2000,
     "source_network": "Trans-Saharan early",
     "reference": "Marshall & Hildebrand 2002 J World Prehist",
     "mtbc_link": "Horn of Africa cattle, MTBC L7 area"},
    {"from_region": "Central Asia", "to_region": "Northern China",
     "taxon": "wheat, barley", "mechanism": "cultural",
     "period_start": -3000, "period_end": -1500,
     "source_network": "Steppe → Yangshao",
     "reference": "Liu et al. 2017; Stevens et al. 2016",
     "mtbc_link": "(Late Neolithic context)"},
    {"from_region": "Mediterranean", "to_region": "Central Asia",
     "taxon": "sheep, goat, cereals", "mechanism": "mixed",
     "period_start": -3000, "period_end": 1500,
     "source_network": "Silk Road precursor",
     "reference": "Frachetti 2012; Spengler 2019",
     "mtbc_link": "Eurasian livestock mixing"},
    {"from_region": "Mesoamerica", "to_region": "South America",
     "taxon": "maize, beans, squash", "mechanism": "cultural",
     "period_start": -4000, "period_end": -1000,
     "source_network": "Pre-Columbian",
     "reference": "Piperno 2011; Pearsall 2008",
     "mtbc_link": "(no Pre-Columbian human MTBC mass spread)"},
    {"from_region": "Andes", "to_region": "South American lowlands",
     "taxon": "potato, quinoa, llama", "mechanism": "demic",
     "period_start": -3000, "period_end": 0,
     "source_network": "Pre-Columbian",
     "reference": "Wheeler 1995; Bruno 2006",
     "mtbc_link": "(no MTBC link)"},
    {"from_region": "Pacific NW Mexico", "to_region": "Mesoamerica",
     "taxon": "turkey, dog", "mechanism": "cultural",
     "period_start": -2000, "period_end": 1500,
     "source_network": "Pre-Columbian",
     "reference": "Speller et al. 2010 PNAS",
     "mtbc_link": "(no MTBC link)"},
    {"from_region": "Old World", "to_region": "Americas",
     "taxon": "cattle, sheep, pig, horse", "mechanism": "colonial",
     "period_start": 1492, "period_end": 1700,
     "source_network": "Columbian Exchange",
     "reference": "Crosby 1972; Anderson 2004",
     "mtbc_link": "Massive M. bovis introduction to Americas"},
    {"from_region": "Americas", "to_region": "Old World",
     "taxon": "maize, potato, manioc, sweet potato", "mechanism": "colonial",
     "period_start": 1492, "period_end": 1700,
     "source_network": "Columbian Exchange",
     "reference": "Crosby 1972; Mann 2011",
     "mtbc_link": "Post-Columbian demographic pressure"},
    {"from_region": "South Asia", "to_region": "Mascarenes / Cape",
     "taxon": "cattle indicine, sheep", "mechanism": "colonial",
     "period_start": 1600, "period_end": 1800,
     "source_network": "VOC / Carreira da Índia",
     "reference": "Allen 2014; Filliot 1974",
     "mtbc_link": "M. bovis indicine into Indian Ocean"},
    {"from_region": "East Africa", "to_region": "Madagascar",
     "taxon": "zebu, sheep", "mechanism": "maritime",
     "period_start": 800, "period_end": 1500,
     "source_network": "Swahili-Arab",
     "reference": "Sheriff 1987; Beaujard 2007",
     "mtbc_link": "M. bovis introduction to Madagascar"},
    {"from_region": "Fertile Crescent", "to_region": "Egypt",
     "taxon": "sheep, goat, wheat, barley", "mechanism": "demic",
     "period_start": -7000, "period_end": -5500,
     "source_network": "Levant → Nile",
     "reference": "Wendrich 2010; Linseele et al. 2014",
     "mtbc_link": "M. caprae arrives in Egypt"},
    {"from_region": "Anatolia", "to_region": "Caucasus / Iran",
     "taxon": "cattle, sheep, goat, cereals", "mechanism": "demic",
     "period_start": -7500, "period_end": -6000,
     "source_network": "(early Neolithic spread)",
     "reference": "Decaix et al. 2019; Marciniak 2008",
     "mtbc_link": "Caucasus / Iranian livestock"},
]


# ---------------------------------------------------------------------------
# Curated timeline events (for TMRCA overlay)
# ---------------------------------------------------------------------------

DOMESTICATION_TIMELINE = [
    {"event": "Primary animal domestication (Fertile Crescent)",
     "period_start": -10800, "period_end": -9500,
     "mtbc_link": "Ancestral M. bovis / M. caprae emergence",
     "reference": "Zeder 2008; Bollongino 2012"},
    {"event": "Primary cereal domestication (Fertile Crescent)",
     "period_start": -10500, "period_end": -9500,
     "mtbc_link": "Sedentarisation context for modern MTBC",
     "reference": "Heun 1997; Fuller et al. 2014"},
    {"event": "Rice domestication (Yangtze)",
     "period_start": -9000, "period_end": -7000,
     "mtbc_link": "(East Asian sedentarisation)",
     "reference": "Fuller et al. 2009"},
    {"event": "Pre-Pottery Neolithic B (PPNB)",
     "period_start": -8500, "period_end": -7000,
     "mtbc_link": "Mixed herding, intensified animal-human contact",
     "reference": "Bar-Yosef 2002; Köhler-Rollefson 1992"},
    {"event": "Indus cattle domestication (B. indicus)",
     "period_start": -8000, "period_end": -7000,
     "mtbc_link": "Indicine M. bovis lineage emergence",
     "reference": "Chen 2010"},
    {"event": "Cardial / Impressed Ware spread",
     "period_start": -6000, "period_end": -5000,
     "mtbc_link": "M. caprae in Western Mediterranean",
     "reference": "Manen 2019"},
    {"event": "Late Egyptian Neolithic",
     "period_start": -5500, "period_end": -4000,
     "mtbc_link": "North African livestock, MTBC contact",
     "reference": "Wendrich 2010; Zink 2003 (TB mummies)"},
    {"event": "LBK expansion (Central Europe)",
     "period_start": -5500, "period_end": -4900,
     "mtbc_link": "Mass diffusion of livestock and zoonotic MTBC in Europe",
     "reference": "Bramanti 2009; Haak 2015"},
    {"event": "Modern MTBC TMRCA (Bos & Comas)",
     "period_start": -6000, "period_end": -4000,
     "mtbc_link": "Emergence of M. tuberculosis sensu stricto from canettii-like",
     "reference": "Comas 2013 Nat Genet; Bos 2014 Nature"},
    {"event": "Horse domestication (Botai)",
     "period_start": -3700, "period_end": -3000,
     "mtbc_link": "(no direct MTBC link)",
     "reference": "Outram 2009; Librado 2021"},
    {"event": "Yamnaya / Steppe expansion",
     "period_start": -3000, "period_end": -2500,
     "mtbc_link": "Eurasian livestock mixing",
     "reference": "Haak 2015"},
    {"event": "Bantu Stage I (West → Central Africa)",
     "period_start": -3000, "period_end": -1000,
     "mtbc_link": "L5/L6 + M. bovis Africa diffusion",
     "reference": "Grollemund 2015"},
    {"event": "Bantu Stage II (Central → Southern Africa)",
     "period_start": -1000, "period_end": 500,
     "mtbc_link": "M. bovis arrives Southern Africa",
     "reference": "Russell 2014"},
    {"event": "Austronesian expansion (Taiwan → Madagascar)",
     "period_start": -3000, "period_end": 1000,
     "mtbc_link": "L1 Madagascar (cf. indian-ocean-voyages)",
     "reference": "Skoglund 2016"},
    {"event": "Trans-Saharan caravan trade",
     "period_start": -1000, "period_end": 1500,
     "mtbc_link": "M. bovis diffusion via livestock",
     "reference": "Mitchell 2005"},
    {"event": "Columbian Exchange",
     "period_start": 1492, "period_end": 1700,
     "mtbc_link": "Massive M. bovis introduction to Americas",
     "reference": "Crosby 1972"},
]


# ---------------------------------------------------------------------------
# Source URLs and download instructions
# ---------------------------------------------------------------------------

SOURCE_INFO = {
    "abmap": {
        "name": "ABMAP — Animal Bone Metrical Archive Project",
        "host": "Archaeology Data Service (University of York)",
        "url_landing": "https://archaeologydataservice.ac.uk/archives/view/abmap/",
        "format": "CSV (web search interface, downloadable results)",
        "license": "ADS terms of use",
        "coverage": "61 000 measurements, 24 700 bones, Neolithic to modern, Britain. "
                    "Cattle, sheep/goat, pig, horse, dog, chicken, goose.",
        "fields_expected": [
            "Element", "Species", "Measurement", "Value", "Date", "County",
        ],
        "instruction": (
            "1. Visit https://archaeologydataservice.ac.uk/archives/view/abmap/\n"
            "2. Use the search form (species, element, measurement, date, county)\n"
            "3. Download tailored CSV results\n"
            "4. Pass via --input"
        ),
    },
    "aadr": {
        "name": "AADR — Allen Ancient DNA Resource",
        "host": "Reich Lab, Harvard Medical School",
        "url_landing": ("https://reich.hms.harvard.edu/"
                        "allen-ancient-dna-resource-aadr-downloadable-genotypes-"
                        "present-day-and-ancient-dna-data"),
        "format": "TSV (.anno) + EIGENSTRAT (.geno/.snp/.ind)",
        "license": "Open (cite AADR releases)",
        "coverage": "~10 000 ancient individuals (humans + some animals), "
                    "Pleistocene to historical, calibrated dates.",
        "fields_expected": [
            "Genetic_ID", "Date_BP", "Political_Entity", "Locality",
            "Lat", "Long", "Group_ID",
        ],
        "instruction": (
            "1. Visit the AADR landing page\n"
            "2. Download the latest release tarball (e.g. v54.1)\n"
            "3. Extract the .anno file (TSV with one row per individual)\n"
            "4. Pass via --input"
        ),
    },
    "ademnes": {
        "name": "ADEMNES — Archaeobotanical database of the Eastern Mediterranean and Near East",
        "host": "Universities of Freiburg & Tübingen",
        "url_landing": "https://www.ademnes.de/",
        "format": "Web interface; XML on request",
        "license": "Academic use",
        "coverage": "533 sites, Aegean Greece, Turkey, W. Iran, Iraq, Syria, "
                    "Lebanon, Israel, Jordan, N. Egypt, "
                    "Epipalaeolithic to Medieval, focus Bronze Age.",
        "fields_expected": [
            "site", "period", "taxon", "context", "count",
        ],
        "instruction": (
            "1. Visit https://www.ademnes.de/\n"
            "2. Note: web-based search; XML extracts available on request\n"
            "3. The successor 'CLaSS' (Durham) is in development\n"
            "4. Pass exported CSV via --input (best-effort schema detection)"
        ),
    },
    "brain": {
        "name": "BRAIN — Botanical Records of Archaeobotany Italian Network",
        "host": "Italian universities consortium",
        "url_landing": "https://www.nature.com/articles/s41597-024-03346-5",
        "format": "CSV (Scientific Data 2024 supplementary)",
        "license": "CC-BY",
        "coverage": "739 sites, Italy + nearby Mediterranean, all plant records.",
        "fields_expected": [
            "site", "period", "taxon", "category", "region",
        ],
        "instruction": (
            "1. Visit the Scientific Data article (Nature)\n"
            "2. Download supplementary CSV from the article\n"
            "3. Pass via --input"
        ),
    },
    "p3k14c": {
        "name": "p3k14c — global archaeological radiocarbon database",
        "host": "Various academic institutions (open data)",
        "url_landing": "https://www.nature.com/articles/s41597-022-01118-7",
        "format": "CSV",
        "license": "CC0",
        "coverage": "77 393 archaeological 14C dates, global, "
                    "Pleistocene to recent.",
        "fields_expected": [
            "Lab_ID", "Age", "Error", "Material", "Lat", "Long", "Country",
        ],
        "instruction": (
            "1. Visit the Scientific Data 2022 article\n"
            "2. Download the p3k14c CSV (supplementary or GitHub mirror)\n"
            "3. Pass via --input. Use --bbox and --period to filter."
        ),
    },
    "context": {
        "name": "CONTEXT — radiocarbon database for Neolithic Europe",
        "host": "University of Cologne",
        "url_landing": "http://context-database.uni-koeln.de/download.php",
        "format": "CSV",
        "license": "Academic",
        "coverage": "Neolithic European 14C dates.",
        "fields_expected": [
            "site", "lab_id", "age_bp", "error", "material",
        ],
        "instruction": (
            "1. Visit http://context-database.uni-koeln.de/download.php\n"
            "2. Download CSV\n"
            "3. Pass via --input (use parse p3k14c with --schema context if "
            "schema differs)"
        ),
    },
    "agrichange": {
        "name": "AgriChange — radiocarbon database for NW Mediterranean Neolithic",
        "host": "Journal of Open Archaeology Data",
        "url_landing": "https://openarchaeologydata.metajnl.com/articles/10.5334/joad.72",
        "format": "CSV / XLSX / FileMaker",
        "license": "CC-BY",
        "coverage": "NW Mediterranean Arch + High Rhine, ~5900-2000 cal BC.",
        "fields_expected": [
            "site", "lab_id", "age_bp", "error", "material", "context",
        ],
        "instruction": (
            "1. Visit the J. Open Archaeol Data article\n"
            "2. Download CSV/XLSX/FileMaker\n"
            "3. Pass via --input"
        ),
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def filter_period(df, period_str, start_col="period_start",
                  end_col="period_end"):
    if not period_str:
        return df
    a, b = [int(x) for x in period_str.split(":")]
    if end_col not in df.columns:
        end_col = start_col
    return df[(df[end_col] >= a) & (df[start_col] <= b)].copy()


def filter_contains(df, col, value):
    if not value or col not in df.columns:
        return df
    parts = [p.strip() for p in value.split(",")]
    pattern = "|".join(parts)
    return df[df[col].astype(str).str.contains(
        pattern, case=False, na=False, regex=True)].copy()


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_centers(args):
    frames = []
    if args.type in ("animal", "all"):
        frames.append(pd.DataFrame(ANIMAL_CENTERS).assign(type="animal"))
    if args.type in ("plant", "all"):
        frames.append(pd.DataFrame(PLANT_CENTERS).assign(type="plant"))
    if args.type in ("human", "all"):
        frames.append(pd.DataFrame(HUMAN_CENTERS).assign(type="human"))
    if not frames:
        print(f"Unknown --type: {args.type}", file=sys.stderr)
        sys.exit(1)
    df = pd.concat(frames, ignore_index=True)

    df = filter_period(df, args.period)
    df = filter_contains(df, "region", args.region)
    df = filter_contains(df, "mtbc_link", args.mtbc_link)

    if args.output:
        df.to_csv(args.output, index=False)
        print(f"Wrote {len(df)} centers -> {args.output}", file=sys.stderr)
    else:
        print(df.to_csv(index=False))
    return df


def cmd_routes(args):
    df = pd.DataFrame(CURATED_ROUTES)
    df = filter_period(df, args.period)
    df = filter_contains(df, "taxon", args.species)
    df = filter_contains(df, "mechanism", args.mechanism)
    df = filter_contains(df, "mtbc_link", args.mtbc_link)
    df = filter_contains(df, "source_network", args.source_network)

    if args.output:
        df.to_csv(args.output, index=False)
        print(f"Wrote {len(df)} routes -> {args.output}", file=sys.stderr)
    else:
        print(df.to_csv(index=False))
    return df


def cmd_timeline(args):
    df = pd.DataFrame(DOMESTICATION_TIMELINE)
    df = filter_period(df, args.period)

    if args.output:
        df.to_csv(args.output, index=False)
        print(f"Wrote {len(df)} timeline events -> {args.output}",
              file=sys.stderr)

    if args.plot:
        if not HAS_PLOT:
            print("ERROR: matplotlib not installed", file=sys.stderr)
            return df
        fig, ax = plt.subplots(figsize=(13, len(df) * 0.45 + 2))
        for i, row in df.iterrows():
            ax.barh(i, row["period_end"] - row["period_start"],
                    left=row["period_start"], height=0.7, alpha=0.6)
            ax.text(row["period_start"], i, " " + row["event"],
                    va="center", fontsize=8)
        ax.set_yticks([])
        ax.set_xlabel("Year (BCE/CE, negative = BCE)")
        ax.set_title("Domestication pathways — chronologie pour MTBC")

        if args.tmrca and Path(args.tmrca).exists():
            tmrca = pd.read_csv(args.tmrca)
            for _, t in tmrca.iterrows():
                year = (t.get("year_start") if "year_start" in t
                        else t.get("year") if "year" in t else None)
                end = (t.get("year_end") if "year_end" in t else year)
                label = (t.get("label") or t.get("lineage") or "")
                if pd.notna(year):
                    ax.axvspan(year, end if pd.notna(end) else year,
                               color="red", alpha=0.15)
                    ax.text(year, len(df) - 0.2, str(label),
                            rotation=90, color="red", fontsize=8, va="top")

        plt.tight_layout()
        plt.savefig(args.plot, dpi=200)
        print(f"Wrote figure -> {args.plot}", file=sys.stderr)
    return df


def cmd_parse_abmap(args):
    if not args.input:
        print("ERROR: --input required (download from ADS)", file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(args.input, low_memory=False)
    cols = {c.lower(): c for c in df.columns}
    species = cols.get("species") or cols.get("taxon") or cols.get("genus")
    element = cols.get("element") or cols.get("bone")
    measure = cols.get("measurement") or cols.get("measure_type")
    value = cols.get("value") or cols.get("mm")
    date = cols.get("date") or cols.get("period")

    if args.species and species:
        df = filter_contains(df, species, args.species)
    if args.period and date:
        df = filter_contains(df, date, args.period)

    keep = [c for c in [species, element, measure, value, date] if c]
    out = df[keep].copy() if keep else df.copy()
    out["source"] = "ABMAP"

    if args.output:
        out.to_csv(args.output, index=False)
        print(f"Wrote {len(out)} ABMAP rows -> {args.output}", file=sys.stderr)
    else:
        print(out.head(50).to_csv(index=False))
        print(f"({len(out)} total rows)", file=sys.stderr)
    return out


def cmd_parse_aadr(args):
    if not args.input:
        print("ERROR: --input required (download AADR .anno file)",
              file=sys.stderr)
        sys.exit(1)
    sep = "\t" if args.input.endswith(".anno") or args.input.endswith(".tsv") \
        else ","
    df = pd.read_csv(args.input, sep=sep, low_memory=False)
    cols = {c.lower(): c for c in df.columns}

    date = cols.get("date_bp") or cols.get("mean_date_bp") \
        or cols.get("date in bp")
    region = cols.get("political_entity") or cols.get("country") \
        or cols.get("locality")
    lat = cols.get("lat") or cols.get("latitude")
    lon = cols.get("long") or cols.get("longitude")
    gid = cols.get("genetic_id") or cols.get("group_id")

    if args.period and date:
        try:
            ages = pd.to_numeric(df[date], errors="coerce")
            a, b = [int(x) for x in args.period.split(":")]
            # AADR Date_BP is years before 1950, so a date '8000 BP' = 6050 BCE
            # We interpret args.period as BCE/CE (negative = BCE) and convert:
            df = df[(1950 - ages >= a) & (1950 - ages <= b)].copy()
        except Exception as e:
            print(f"WARNING: period filter failed: {e}", file=sys.stderr)
    if args.region and region:
        df = filter_contains(df, region, args.region)

    keep = [c for c in [gid, date, region, lat, lon] if c]
    out = df[keep].copy() if keep else df.copy()
    out["source"] = "AADR"

    if args.output:
        out.to_csv(args.output, index=False)
        print(f"Wrote {len(out)} AADR rows -> {args.output}", file=sys.stderr)
    else:
        print(out.head(30).to_csv(index=False))
        print(f"({len(out)} total rows)", file=sys.stderr)
    return out


def cmd_parse_p3k14c(args):
    if not args.input:
        print("ERROR: --input required (download p3k14c CSV)",
              file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(args.input, low_memory=False)
    cols = {c.lower(): c for c in df.columns}

    age = cols.get("age") or cols.get("c14_age") or cols.get("age_bp")
    err = cols.get("error") or cols.get("c14_error")
    mat = cols.get("material") or cols.get("c14_material")
    lat = cols.get("lat") or cols.get("latitude")
    lon = cols.get("long") or cols.get("longitude")
    country = cols.get("country") or cols.get("region")

    if args.bbox and lat and lon:
        lat_min, lat_max, lon_min, lon_max = [
            float(x) for x in args.bbox.split(",")]
        df[lat] = pd.to_numeric(df[lat], errors="coerce")
        df[lon] = pd.to_numeric(df[lon], errors="coerce")
        df = df.dropna(subset=[lat, lon])
        df = df[(df[lat] >= lat_min) & (df[lat] <= lat_max)
                & (df[lon] >= lon_min) & (df[lon] <= lon_max)].copy()
    if args.period and age:
        try:
            a, b = [int(x) for x in args.period.split(":")]
            ages = pd.to_numeric(df[age], errors="coerce")
            # p3k14c Age is 14C BP. Convert to BCE/CE: 1950 - BP
            df = df[(1950 - ages >= a) & (1950 - ages <= b)].copy()
        except Exception as e:
            print(f"WARNING: period filter failed: {e}", file=sys.stderr)
    if args.material and mat:
        df = filter_contains(df, mat, args.material)

    keep = [c for c in [age, err, mat, lat, lon, country] if c]
    out = df[keep].copy() if keep else df.copy()
    out["source"] = "p3k14c"

    if args.output:
        out.to_csv(args.output, index=False)
        print(f"Wrote {len(out)} p3k14c dates -> {args.output}",
              file=sys.stderr)
    else:
        print(out.head(30).to_csv(index=False))
        print(f"({len(out)} total dates)", file=sys.stderr)
    return out


def cmd_parse_ademnes(args):
    return _parse_archaeobotany(args, "ADEMNES")


def cmd_parse_brain(args):
    return _parse_archaeobotany(args, "BRAIN")


def _parse_archaeobotany(args, source_name):
    if not args.input:
        print(f"ERROR: --input required ({source_name})", file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(args.input, low_memory=False)
    cols = {c.lower(): c for c in df.columns}
    site = cols.get("site") or cols.get("location")
    period = cols.get("period") or cols.get("phase")
    taxon = cols.get("taxon") or cols.get("species") or cols.get("genus")

    if args.period and period:
        df = filter_contains(df, period, args.period)
    if args.taxon and taxon:
        df = filter_contains(df, taxon, args.taxon)

    keep = [c for c in [site, period, taxon] if c]
    out = df[keep].copy() if keep else df.copy()
    out["source"] = source_name

    if args.output:
        out.to_csv(args.output, index=False)
        print(f"Wrote {len(out)} {source_name} rows -> {args.output}",
              file=sys.stderr)
    else:
        print(out.head(30).to_csv(index=False))
        print(f"({len(out)} total rows)", file=sys.stderr)
    return out


def cmd_fetch(args):
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
        description="Domestication Pathways — centres, routes and "
                    "chronologies for MTBC co-evolution.")
    sub = p.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-o", "--output", help="Output CSV")
    common.add_argument("-p", "--plot", help="Output figure (PNG/PDF)")
    common.add_argument("--summary", action="store_true",
                        help="Print JSON summary")

    p_c = sub.add_parser("centers", parents=[common],
                         help="Curated origin centres")
    p_c.add_argument("--type", default="all",
                     choices=["animal", "plant", "human", "all"])
    p_c.add_argument("--region")
    p_c.add_argument("--period")
    p_c.add_argument("--mtbc-link")

    p_r = sub.add_parser("routes", parents=[common],
                         help="Curated dispersal routes")
    p_r.add_argument("--species")
    p_r.add_argument("--mechanism")
    p_r.add_argument("--period")
    p_r.add_argument("--mtbc-link")
    p_r.add_argument("--source-network")

    p_t = sub.add_parser("timeline", parents=[common],
                         help="Curated chronology with TMRCA overlay")
    p_t.add_argument("--period")
    p_t.add_argument("--tmrca")

    p_p = sub.add_parser("parse", help="Parse an external dataset")
    p_p_sub = p_p.add_subparsers(dest="subcommand", required=True)

    p_pa = p_p_sub.add_parser("abmap", parents=[common])
    p_pa.add_argument("--input", required=True)
    p_pa.add_argument("--species")
    p_pa.add_argument("--period")

    p_paadr = p_p_sub.add_parser("aadr", parents=[common])
    p_paadr.add_argument("--input", required=True)
    p_paadr.add_argument("--period",
                         help="In BCE/CE notation (negative = BCE). "
                              "AADR Date_BP is auto-converted.")
    p_paadr.add_argument("--region")
    p_paadr.add_argument("--type", default="human",
                         choices=["human", "animal"])

    p_pp = p_p_sub.add_parser("p3k14c", parents=[common])
    p_pp.add_argument("--input", required=True)
    p_pp.add_argument("--bbox", help="lat_min,lat_max,lon_min,lon_max")
    p_pp.add_argument("--period",
                      help="In BCE/CE notation (negative = BCE).")
    p_pp.add_argument("--material")

    for src_name in ("ademnes", "brain"):
        ps = p_p_sub.add_parser(src_name, parents=[common])
        ps.add_argument("--input", required=True)
        ps.add_argument("--period")
        ps.add_argument("--taxon")

    p_f = sub.add_parser("fetch", parents=[common],
                         help="Print download URLs and instructions")
    p_f.add_argument("--source", required=True,
                     choices=list(SOURCE_INFO.keys()))

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.command == "centers":
        cmd_centers(args)
    elif args.command == "routes":
        cmd_routes(args)
    elif args.command == "timeline":
        cmd_timeline(args)
    elif args.command == "fetch":
        cmd_fetch(args)
    elif args.command == "parse":
        sub = args.subcommand
        if sub == "abmap":
            cmd_parse_abmap(args)
        elif sub == "aadr":
            cmd_parse_aadr(args)
        elif sub == "p3k14c":
            cmd_parse_p3k14c(args)
        elif sub == "ademnes":
            cmd_parse_ademnes(args)
        elif sub == "brain":
            cmd_parse_brain(args)
        else:
            print(f"Unknown parse subcommand: {sub}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
