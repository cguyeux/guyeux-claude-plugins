"""AADR `.anno` column map: stable name -> [candidate raw column names].

The base client matches a candidate by exact header first, then case-insensitive
substring, so the terse names below also match AADR's verbose real headers
(e.g. ``"Date mean in BP"`` matches ``"Date mean in BP in years before 1950 CE ..."``).
Where AADR renamed a column across versions, list both spellings as candidates
(``"Group ID"`` is the recent name, ``"Group Label"`` the older one).

Run ``python -m aadr_client inspect`` on a real download to print its actual
header and reconcile any column that fails to resolve.
"""

SCHEMA = {
    "genetic_id": ["Genetic ID"],
    "master_id": ["Master ID"],
    "group": ["Group ID", "Group Label"],
    "country": ["Political Entity"],
    "locality": ["Locality"],
    "lat": ["Lat."],
    "lon": ["Long."],
    "date_bp": ["Date mean in BP"],
    "date_sd_bp": ["Date standard deviation in BP"],
    "publication": ["Publication", "Data source"],
    "coverage": ["Coverage", "1240k coverage"],
    "sex": ["Molecular Sex"],
    "qc": ["Assessment", "ASSESSMENT"],
}
