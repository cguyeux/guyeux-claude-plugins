#!/usr/bin/env python3
"""triangulate.py -- skeleton du skill triangulate-route.

USAGE :
  python triangulate.py --country "Madagascar" --output triangulation.tsv
  python triangulate.py --country "Brazil" --top-n 20 --output brazil_triangulation.tsv

Pour usage agentique : ce script suppose que l'utilisateur l'execute dans un
contexte où le MCP TBannotator est accessible. Sinon, il sort les requetes SQL
à executer.
"""

import argparse
import sys
from pathlib import Path

# Liste des pays diaspora moderne à exclure (immigration, biaise les voisinages)
DIASPORA_EXCLUDE = [
    'USA', 'United Kingdom', 'Australia', 'Canada', 'Sweden', 'Italy', 'Germany',
    'Netherlands', 'France', 'Belgium', 'Switzerland', 'Norway', 'Denmark',
    'Finland', 'Ireland', 'Spain', 'Portugal',
]

# Mapping voisinages -> bassins historiques
BASIN_PATTERNS = {
    "Asie SE / austronésien": ["Indonesia", "Malaysia", "Philippines", "Borneo", "Vietnam", "Thailand", "Cambodia", "Myanmar"],
    "Asie du Sud / arabo-indienne": ["India", "Bangladesh", "Pakistan", "Sri Lanka", "Nepal", "Iran"],
    "Afrique Est / arabo-swahili": ["Tanzania", "Kenya", "Malawi", "Mozambique", "Uganda", "Ethiopia", "Djibouti", "Somalia"],
    "Bantou Afrique centrale/Ouest": ["Nigeria", "Ghana", "Cameroon", "Cote d'Ivoire", "Democratic Republic of the Congo", "Rwanda", "Burundi", "Central African Republic", "Gambia", "Senegal"],
    "Traite atlantique (Amériques)": ["Peru", "Brazil", "Argentina", "Bolivia", "Colombia", "Venezuela", "Mexico", "Haiti", "Jamaica", "Cuba", "Dominican Republic"],
    "Asie de l'Est (Beijing globalisé)": ["China", "Taiwan", "Japan", "South Korea", "North Korea"],
    "Routes silk road (Asie Centrale)": ["Kazakhstan", "Uzbekistan", "Kyrgyzstan", "Tajikistan", "Russia", "Georgia", "Mongolia"],
    "Maghreb / Méditerranée": ["Morocco", "Algeria", "Tunisia", "Libya", "Egypt", "Turkey"],
}


def classify_country(geo_loc_name):
    """Classer un pays voisin dans un bassin historique."""
    for basin, countries in BASIN_PATTERNS.items():
        for c in countries:
            if c.lower() in geo_loc_name.lower():
                return basin
    return "Autre / non classifié"


def emit_inventory_query(country):
    """SQL pour inventaire MTBC du pays cible."""
    return f"""SELECT sc.lineage_level_1, sc.lineage_code, COUNT(DISTINCT sc.strain_id) as n
FROM mv_strain_classification sc
JOIN mv_strain_metadata sm ON sc.strain_id = sm.strain_id
WHERE sm.geo_loc_name ILIKE '{country}%'
  AND sm.species_group = 'M. tuberculosis'
  AND sc.system_name = 'Coll'
GROUP BY sc.lineage_level_1, sc.lineage_code
ORDER BY n DESC;"""


def emit_neighbors_query(country, sub_lineage, top_n=20):
    """SQL pour voisinages mondiaux d'une sous-lignée."""
    diaspora_list = "', '".join(DIASPORA_EXCLUDE)
    return f"""WITH target_strains AS (
  SELECT sc.strain_id, sc.lineage_code as target_lineage
  FROM mv_strain_classification sc
  JOIN mv_strain_metadata sm ON sc.strain_id = sm.strain_id
  WHERE sm.geo_loc_name ILIKE '{country}%' AND sm.species_group = 'M. tuberculosis'
    AND sc.system_name = 'Shitikov23' AND sc.lineage_code = '{sub_lineage}'
)
SELECT sm.geo_loc_name, COUNT(DISTINCT sc.strain_id) as n
FROM target_strains ts
JOIN mv_strain_classification sc ON sc.lineage_code = ts.target_lineage AND sc.system_name = 'Shitikov23'
JOIN mv_strain_metadata sm ON sc.strain_id = sm.strain_id
WHERE sm.species_group = 'M. tuberculosis'
  AND sm.geo_loc_name NOT ILIKE '{country}%'
  AND sm.geo_loc_name IS NOT NULL AND sm.geo_loc_name != ''
  AND sm.geo_loc_name NOT IN ('{diaspora_list}')
GROUP BY sm.geo_loc_name
ORDER BY n DESC
LIMIT {top_n};"""


def main():
    ap = argparse.ArgumentParser(description="Triangulate-route : SQL queries skeleton for MTBC × historical archives.")
    ap.add_argument("--country", required=True, help="Pays cible (ILIKE pattern, ex: 'Madagascar', 'Cabo Verde', 'Brazil')")
    ap.add_argument("--sub-lineage", default=None, help="Sous-lignée Shitikov23 spécifique (ex: '1.1.2', '4.6.2'). Si absent, génère seulement l'inventaire.")
    ap.add_argument("--top-n", type=int, default=20, help="Top N pays voisins (defaut 20)")
    ap.add_argument("--output", default=None, help="Fichier de sortie (defaut stdout)")
    args = ap.parse_args()

    out = open(args.output, "w") if args.output else sys.stdout

    out.write(f"# Triangulate-route -- {args.country}\n\n")
    out.write(f"## Etape 1 : Inventaire MTBC {args.country}\n\n```sql\n")
    out.write(emit_inventory_query(args.country))
    out.write("\n```\n\n")

    if args.sub_lineage:
        out.write(f"## Etape 2 : Voisins mondiaux sous-lignee {args.sub_lineage}\n\n```sql\n")
        out.write(emit_neighbors_query(args.country, args.sub_lineage, args.top_n))
        out.write("\n```\n\n")
        out.write(f"## Etape 3 : Classification voisinages -> bassins historiques\n\n")
        out.write(f"Apres execution de la requete Etape 2, classer chaque pays voisin via la fonction `classify_country()` :\n")
        for basin, countries in BASIN_PATTERNS.items():
            out.write(f"- **{basin}** : {', '.join(countries[:5])}\n")
        out.write(f"\n")
    else:
        out.write(f"## Etape 2 : sous-lignees a investiguer\n\n")
        out.write(f"Apres execution de la requete Etape 1, pour chaque sous-lignee avec n >= 5 :\n")
        out.write(f"  python triangulate.py --country '{args.country}' --sub-lineage <CODE>\n\n")

    out.write(f"## Etape 4 : Validation historique\n\n")
    out.write(f"Pour chaque bassin historique identifie :\n\n")
    out.write(f"- **Traite atlantique** -> `bio_redac:slavevoyages` (port embarquement / debarquement)\n")
    out.write(f"- **Routes pre-modernes** -> `bio_redac:owtrad` (Silk Road, swahili, etc.)\n")
    out.write(f"- **Bantou ouest-africain L4.6.2** -> Sahal-Senelle-Guyeux-Sola 2023 PLOS NTD\n")
    out.write(f"- **Austronesien** -> Crowther 2016 PNAS, Beaujard 2011\n")
    out.write(f"- **Colonial europeen** -> Histoire coloniale du pays\n")
    out.write(f"- **Autres** -> `bio_redac:lit-review` + WebSearch ciblé\n\n")

    out.write(f"## Etape 5 : Format de sortie publication\n\n")
    out.write(f"Tableau a 4 colonnes (modele Madagascar Z30) :\n\n")
    out.write(f"| Route MTBC | n_target | Voisins TBannotator | Source historique | Validation |\n")
    out.write(f"|---|---|---|---|---|\n")
    out.write(f"| ... | ... | Top 3 pays | Reference | Pourquoi coherent |\n\n")

    out.write(f"## Cas tests pré-validés\n\n")
    out.write(f"- Madagascar (entrees 59-62 cahier_de_labo musee_de_lhomme)\n")
    out.write(f"- Brésil L1 (papier Guyeux 2026, cas 2 du deck)\n")
    out.write(f"- A tester : Cap Vert, Antilles, Comores, Maurice, Reunion\n")

    if args.output:
        out.close()
        print(f"[out] {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
