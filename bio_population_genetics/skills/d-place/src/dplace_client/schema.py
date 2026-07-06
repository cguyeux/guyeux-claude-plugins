"""D-PLACE societies.csv column map: stable name -> [candidate raw columns]."""

SCHEMA = {
    "id": ["id", "soc_id"],
    "name": ["pref_name_for_society", "Name", "name"],
    "glottocode": ["glottocode", "Glottocode"],
    "lat": ["Lat", "Latitude", "origLat"],
    "lon": ["Long", "Longitude", "origLong"],
    "family": ["Family", "family"],
    "dataset": ["Dataset", "source", "xd_id"],
}
