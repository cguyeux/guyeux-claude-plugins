"""Vocabulaire contrôlé partagé : normalisation des noms d'antibiotiques.

Les sources hétérogènes (OMS, CRyPTIC, PATRIC, tb-profiler, littérature) écrivent
les drogues différemment (Rifampicin / rifampin / RIF). On les ramène à un nom
canonique + un code à 3 lettres pour pouvoir joindre les sources.
"""

DRUG_CODE = {
    "amikacin": "AMK", "bedaquiline": "BDQ", "capreomycin": "CAP",
    "ciprofloxacin": "CIP", "clofazimine": "CFZ", "cycloserine": "CYC",
    "delamanid": "DLM", "ethambutol": "EMB", "ethionamide": "ETH",
    "isoniazid": "INH", "kanamycin": "KAN", "levofloxacin": "LEV",
    "linezolid": "LZD", "moxifloxacin": "MXF", "ofloxacin": "OFX",
    "para-aminosalicylic_acid": "PAS", "prothionamide": "PTO",
    "pyrazinamide": "PZA", "rifabutin": "RFB", "rifampicin": "RIF",
    "streptomycin": "STM", "aminoglycosides": "AMG",
    "fluoroquinolones": "FQS", "nicotinamide": "NIC",
}

_ALIASES = {
    "amk": "amikacin", "ami": "amikacin", "bdq": "bedaquiline",
    "cap": "capreomycin", "cip": "ciprofloxacin", "cfz": "clofazimine",
    "cs": "cycloserine", "cyc": "cycloserine", "dlm": "delamanid",
    "emb": "ethambutol", "eth": "ethionamide", "inh": "isoniazid",
    "kan": "kanamycin", "km": "kanamycin", "lev": "levofloxacin",
    "lfx": "levofloxacin", "lzd": "linezolid", "mxf": "moxifloxacin",
    "ofx": "ofloxacin", "ofl": "ofloxacin", "pas": "para-aminosalicylic_acid",
    "para-aminosalicylic acid": "para-aminosalicylic_acid",
    "para-aminosalicylic_acid": "para-aminosalicylic_acid",
    "para-aminosalisylic_acid": "para-aminosalicylic_acid",
    "pto": "prothionamide", "prothionamide": "prothionamide",
    "ethiomide": "ethionamide", "pza": "pyrazinamide", "rfb": "rifabutin",
    "rif": "rifampicin", "rmp": "rifampicin", "rifampin": "rifampicin",
    "rifampicin": "rifampicin", "sm": "streptomycin", "stm": "streptomycin",
    "str": "streptomycin",
}


def canonical_drug(name):
    """Renvoie (nom_canonique, code) pour une graphie quelconque."""
    if name is None:
        return None, None
    k = str(name).strip().lower()
    canon = _ALIASES.get(k, k)
    return canon, DRUG_CODE.get(canon, "?")
