"""p3k14c column map: stable name -> [candidate raw columns]."""

SCHEMA = {
    "date_id": ["LabID"],
    "age_bp": ["Age"],
    "error": ["Error"],
    "material": ["Material"],
    "species": ["Taxa", "Species"],
    "site": ["SiteName", "SiteID"],
    "lat": ["Latitude", "Lat"],
    "lon": ["Longitude", "Long"],
    "country": ["Country"],
    "continent": ["Continent"],
    "source": ["Source", "Reference"],
}
