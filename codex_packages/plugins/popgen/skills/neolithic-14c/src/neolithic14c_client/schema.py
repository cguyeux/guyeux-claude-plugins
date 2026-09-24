"""NERD column map: stable name -> [candidate raw columns]."""

SCHEMA = {
    "date_id": ["DateID", "LabID"],
    "lab_id": ["LabID"],
    "age_bp": ["CRA", "C14Age", "Age"],
    "error": ["Error", "C14SD"],
    "material": ["Material"],
    "species": ["Species", "Taxa"],
    "site": ["SiteName", "Site"],
    "lat": ["Latitude", "Lat"],
    "lon": ["Longitude", "Long"],
    "country": ["Country"],
    "source": ["Source", "Reference"],
}
