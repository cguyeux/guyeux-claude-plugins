"""Pleiades places-dump column map: stable name -> [candidate raw columns]."""

SCHEMA = {
    "id": ["id"],
    "title": ["title"],
    "lat": ["reprLat", "latitude"],
    "lon": ["reprLong", "longitude"],
    "feature_type": ["featureTypes", "featureType"],
    "time_periods": ["timePeriods"],
    "min_date": ["minDate"],
    "max_date": ["maxDate"],
    "geo_context": ["geoContext"],
    "precision": ["locationPrecision"],
}
