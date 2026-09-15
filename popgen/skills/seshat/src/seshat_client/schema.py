"""Seshat polity-record column map: stable name -> [candidate raw columns].

Seshat's long-format Social Complexity / Equinox tables key each record by
(NGA, Polity, time-slice, variable, value interval). Column spellings vary across
snapshots (Equinox vs the 2017 SC dataset vs CSV exports), so each stable name
lists several candidates; the base matches exact-first then case-insensitive
substring. Run ``python -m seshat_client inspect`` on a real snapshot to print its
actual header and reconcile anything that fails to resolve.
"""

SCHEMA = {
    "nga": ["NGA"],
    "polity": ["Polity", "PolityName", "PolID"],
    "start_year": ["start_year", "Period_start", "StartYear", "Start"],
    "end_year": ["end_year", "Period_end", "EndYear", "End"],
    "variable": ["variable", "Variable", "Variable_name"],
    "value_from": ["value_from", "Value_From", "ValueFrom"],
    "value_to": ["value_to", "Value_To", "ValueTo"],
    "source": ["source", "Reference"],
}
