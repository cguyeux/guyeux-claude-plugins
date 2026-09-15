"""ORBIS column maps: stable name -> [candidate raw columns].

Two tables. The base matches a candidate by exact header first, then
case-insensitive substring, so these resolve across the Stanford deposit, the
orbis_v2 GitHub CSVs, and gorbit exports. Run ``python -m orbis_client inspect``
on your real files to print their headers and reconcile anything unresolved.
"""

NODES_SCHEMA = {
    "id": ["id", "node_id", "w"],
    "label": ["label", "name"],
    "lon": ["x", "lon", "longitude"],
    "lat": ["y", "lat", "latitude"],
    "type": ["type", "category"],
}

EDGES_SCHEMA = {
    "source": ["source", "from", "start", "node_a"],
    "target": ["target", "to", "end", "node_b"],
    "distance_km": ["distance_km", "distance", "length_km", "km"],
    "cost": ["cost_denarii_per_kg", "cost", "expense", "denarii"],
    "days": ["duration_days", "days", "duration", "time"],
    "type": ["type", "mode"],
}
