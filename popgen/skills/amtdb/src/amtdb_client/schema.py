"""AmtDB column map: stable name -> [candidate raw columns]."""

SCHEMA = {
    "id": ["id"],
    "country": ["country"],
    "continent": ["continent"],
    "lat": ["latitude", "lat"],
    "lon": ["longitude", "lon"],
    "culture": ["culture"],
    "epoch": ["epoch"],
    "site": ["site"],
    "mt_hg": ["mt_hg", "mtdna_haplogroup", "haplogroup"],
    "year_from": ["year_from"],
    "year_to": ["year_to"],
    "bp": ["bp"],
    "reference": ["reference_name", "reference"],
}
