#!/usr/bin/env python3
"""check_schema_drift — détecte les requêtes SQL périmées dans les SKILL.md (TBannotator).

POURQUOI. Le 2026-07-31, la migration du serveur TBannotator vers l'infra IDEEV a cassé
silencieusement les exemples SQL d'une quinzaine de skills : table `tb_report_snp` disparue,
colonnes `dr_type` / `sra_id` / `marker_type` inexistantes, `strain_id` devenu un ENTIER (les
accessions sont dans `strain_name`), et deux vues matérialisées présentes au schéma mais **non
peuplées**. Ces ruptures ne se voient PAS à la lecture : elles échouent (ou renvoient 0 ligne)
au moment où quelqu'un exécute l'exemple. Corriger les skills un par un traite le symptôme ;
cet outil traite la cause en rendant la dérive DÉTECTABLE avant qu'elle morde.

CE QUE ÇA FAIT. Extrait les blocs ```sql``` des SKILL.md, résout les alias (`FROM t a`,
`JOIN t a`), puis confronte au schéma RÉEL :
  - objets (tables/vues) référencés mais absents du schéma ;
  - colonnes qualifiées `alias.colonne` absentes de la table résolue ;
  - vues matérialisées NON PEUPLÉES (piège spécifique : elles existent, mais toute requête
    échoue avec « has not been populated »).

LIMITES ASSUMÉES (à lire avant de croire un rapport vert). Ce n'est pas un parseur SQL : les
colonnes non qualifiées (sans `alias.`), les CTE, les sous-requêtes et les alias de sortie ne
sont pas résolus — ils sont ignorés, jamais signalés à tort. L'outil détecte donc un
sous-ensemble des ruptures : un rapport vide ne prouve pas que tout marche, il prouve
seulement qu'aucune rupture DE CE TYPE ne subsiste. La validation ultime reste d'exécuter la
requête.

USAGE
  # 1) dumper le schéma courant (via le MCP tbannotator, outil tool_get_schema) dans un CSV
  # 2) auditer :
  python3 check_schema_drift.py --schema-csv schema.csv --skills-dir ~/docs/codes/claude_plugins
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

SQL_BLOCK = re.compile(r"```sql\s*(.*?)```", re.S | re.I)
# FROM/JOIN <objet> [AS] [alias]
# `(?!\s*\.)` écarte le FROM des fonctions SQL : EXTRACT(YEAR FROM m.col), SUBSTRING(x FROM y).
FROM_JOIN = re.compile(
    r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)(?!\s*\.)\s*(?:AS\s+)?([a-zA-Z_][a-zA-Z0-9_]*)?",
    re.I)
QUALIFIED = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\b")

SQL_KEYWORDS = {
    "select", "from", "where", "group", "order", "by", "having", "join", "on", "as", "and",
    "or", "not", "in", "is", "null", "count", "sum", "max", "min", "avg", "round", "case",
    "when", "then", "else", "end", "distinct", "limit", "with", "union", "all", "left",
    "right", "inner", "outer", "cross", "lateral", "coalesce", "nullif", "over", "partition",
    "asc", "desc", "like", "ilike", "between", "exists", "array_agg", "cast",
}


def load_schema(csv_path: Path) -> tuple[dict[str, set[str]], set[str]]:
    """CSV de tool_get_schema -> ({objet: {colonnes}}, {MV non peuplées}).

    Les MV non peuplées ne sont PAS déductibles du CSV de schéma : elles se lisent via
    `SELECT relname, relispopulated FROM pg_class WHERE relkind='m'`. On accepte donc une
    colonne optionnelle `populated` si l'appelant l'a jointe.
    """
    cols: dict[str, set[str]] = defaultdict(set)
    unpopulated: set[str] = set()
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            obj = (row.get("object_name") or "").strip()
            col = (row.get("column_name") or "").strip()
            if obj:
                if col:
                    cols[obj].add(col)
                else:
                    cols.setdefault(obj, set())
            pop = (row.get("populated") or "").strip().lower()
            if obj and pop in {"false", "f", "0", "no"}:
                unpopulated.add(obj)
    return cols, unpopulated


CTE_DEF = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)\s+AS\s*\(", re.I)


def audit_file(path: Path, schema: dict[str, set[str]], unpopulated: set[str]) -> list[str]:
    problems: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for block in SQL_BLOCK.findall(text):
        alias_of: dict[str, str] = {}
        objects: set[str] = set()
        # CTE définis n'importe où dans le bloc (`WITH x AS (`, `), y AS (`, multi-lignes).
        ctes = {m.group(1) for m in CTE_DEF.finditer(block)}
        for obj, alias in FROM_JOIN.findall(block):
            if obj.lower() in SQL_KEYWORDS:
                continue
            objects.add(obj)
            if alias and alias.lower() not in SQL_KEYWORDS:
                alias_of[alias] = obj
            alias_of.setdefault(obj, obj)      # table utilisable sans alias

        # Bloc visant une AUTRE base (ex. tbmonitor/SQLite : `papers`, `json_each`) :
        # si aucun objet du bloc n'appartient au schéma TBannotator, on ne l'audite pas.
        real = {o for o in objects if o not in ctes}
        if real and not (real & schema.keys()):
            continue

        for obj in sorted(objects):
            if obj in ctes:
                continue
            if obj not in schema:
                problems.append(f"objet INEXISTANT : {obj}")
            elif obj in unpopulated:
                problems.append(f"vue matérialisée NON PEUPLÉE (toute requête échouera) : {obj}")

        for alias, col in QUALIFIED.findall(block):
            table = alias_of.get(alias)
            if not table or table not in schema or not schema[table]:
                continue                        # alias inconnu / objet absent : déjà signalé
            if col not in schema[table]:
                problems.append(f"colonne INEXISTANTE : {alias}.{col}  (dans {table})")
    return sorted(set(problems))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--schema-csv", required=True, type=Path,
                    help="CSV produit par tool_get_schema (colonnes object_name/column_name ; "
                         "colonne optionnelle 'populated')")
    ap.add_argument("--skills-dir", required=True, type=Path,
                    help="racine à auditer (ex. ~/docs/codes/claude_plugins)")
    args = ap.parse_args()

    schema, unpopulated = load_schema(args.schema_csv)
    if not schema:
        print("schéma vide : vérifier le CSV", file=sys.stderr)
        return 2

    n_files = n_bad = 0
    for skill in sorted(args.skills_dir.rglob("SKILL.md")):
        problems = audit_file(skill, schema, unpopulated)
        n_files += 1
        if problems:
            n_bad += 1
            print(f"\n{skill.relative_to(args.skills_dir)}")
            for p in problems:
                print(f"   - {p}")

    print(f"\n{n_files} SKILL.md audités ; {n_bad} avec au moins une rupture détectée.")
    print("Rappel : détection PARTIELLE (colonnes non qualifiées, CTE et sous-requêtes non "
          "résolues). Un rapport vide ne prouve pas que les requêtes s'exécutent.")
    return 1 if n_bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
