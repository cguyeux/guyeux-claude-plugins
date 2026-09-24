"""HGDP+1kGP sample-metadata column map: stable name -> [candidate raw columns]."""

SCHEMA = {
    "sample": ["sample", "s", "sample_id", "Sample"],
    "project": ["project", "panel", "dataset", "study"],
    "population": ["population", "pop", "Population"],
    "region": ["region", "genetic_region", "geographic_region"],
    "lat": ["latitude", "lat", "Latitude"],
    "lon": ["longitude", "lon", "Longitude"],
    "sex": ["sex", "Sex"],
}
