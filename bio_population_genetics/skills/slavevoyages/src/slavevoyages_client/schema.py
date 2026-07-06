"""SlaveVoyages Trans-Atlantic dataset column map: stable name -> [candidates].

The published CSV/SPSS uses short variable codes (YEARAM, REGEM1, MAJBUYPT,
SLAXIMP...). The base matches a candidate by exact header first, then
case-insensitive substring. Run ``python -m slavevoyages_client inspect`` on a real
download to print its header and reconcile anything that fails to resolve.
"""

SCHEMA = {
    "voyage_id": ["VOYAGEID", "voyageid", "id"],
    "year": ["YEARAM", "yearam", "year_of_arrival"],
    "embark_region": ["REGEM1", "embarkation_region"],
    "embark_port": ["MAJBUYPT", "principal_place_of_purchase"],
    "disembark_region": ["REGDIS1", "disembarkation_region"],
    "disembark_port": ["MAJSELPT", "principal_place_of_landing"],
    "embarked": ["SLAXIMP", "total_embarked"],
    "disembarked": ["SLAMIMP", "total_disembarked"],
    "flag": ["NATINIMP", "flag", "national_carrier"],
}
