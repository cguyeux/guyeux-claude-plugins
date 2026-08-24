"""Glottolog languoid column map: stable name -> [candidate raw columns].

Resolves across the pyglottolog ``languoids.csv`` (lowercase id/name/...) and the
CLDF ``languages.csv`` (ID/Name/Glottocode/Family_ID/...).
"""

SCHEMA = {
    "glottocode": ["Glottocode", "id", "ID"],
    "name": ["Name", "name"],
    "level": ["level", "Level"],
    "family": ["Family_ID", "classification", "family_id"],
    "macroarea": ["Macroarea", "macroarea"],
    "lat": ["Latitude", "latitude", "Lat"],
    "lon": ["Longitude", "longitude", "Long"],
    "iso639": ["ISO639P3code", "iso639P3code", "ISO_codes"],
}
