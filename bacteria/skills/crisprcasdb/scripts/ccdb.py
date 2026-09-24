#!/usr/bin/env python3
"""Client en ligne de commande de la copie locale de CRISPRCasdb (CRISPR-Cas++, I2BC).

Aucune dépendance Python : tout passe par le client `psql` du système, en TCP sur
127.0.0.1:5433 (conteneur `crisprcasdb`), avec repli sur `docker exec` si le client
local est absent. Le conteneur est démarré automatiquement s'il est arrêté.

Sous-commandes : stats, strain, arrays, spacers, whohas, cas, taxon, sql.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

HOST = os.environ.get("CCDB_HOST", "127.0.0.1")
PORT = os.environ.get("CCDB_PORT", "5433")
DB = os.environ.get("CCDB_DB", "crisprcasdb")
USER = os.environ.get("CCDB_USER", "postgres")
PASSWORD = os.environ.get("CCDB_PASSWORD", "crispr")
CONTAINER = os.environ.get("CCDB_CONTAINER", "crisprcasdb")

SEP = "\t"

# Vocabulaires de region.category, vérifiés sur la base (2026-08-03).
DR, SPACER, LEADER, TRAILER = 1, 3, 5, 6
CATEGORY_LABEL = {DR: "DR", SPACER: "spacer", LEADER: "leader", TRAILER: "trailer"}
ORIENTATION_LABEL = {1: "+", 2: "-", 3: "ND"}


class CcdbError(RuntimeError):
    pass


def _container_running() -> bool:
    try:
        out = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=20,
        )
        return CONTAINER in out.stdout.split()
    except (OSError, subprocess.SubprocessError):
        return False


def _ensure_up() -> None:
    if _container_running():
        return
    if not shutil.which("docker"):
        raise CcdbError("docker introuvable et conteneur non démarré")
    subprocess.run(["docker", "start", CONTAINER], capture_output=True, text=True, timeout=60)
    for _ in range(60):
        probe = subprocess.run(
            ["docker", "exec", CONTAINER, "pg_isready", "-U", USER, "-q"],
            capture_output=True, timeout=20,
        )
        if probe.returncode == 0:
            return
    raise CcdbError(
        f"le conteneur '{CONTAINER}' ne répond pas ; voir "
        "~/docs/codes/mtbc/en_cours/crisprcasdb_local/bin/ccdb_service.sh start"
    )


def query(sql: str, params: dict | None = None) -> list[dict]:
    """Exécute une requête et renvoie des dictionnaires.

    Les paramètres sont passés par variables psql (:'nom'), mises entre quotes par
    psql lui-même : pas de concaténation de chaînes dans le SQL.

    Le résultat transite en JSON (une ligne par enregistrement) et non en TSV :
    6 689 noms d'organismes de la base contiennent des retours à la ligne hérités
    de GenBank, qui coupent silencieusement un enregistrement en deux en TSV.
    """
    params = params or {}
    sql = "SELECT row_to_json(_t) FROM (" + sql.strip().rstrip(";") + ") _t;"
    args_common = ["-v", "ON_ERROR_STOP=1", "-A", "-t", "-P", "footer=off"]
    for key, value in params.items():
        args_common += ["-v", f"{key}={value}"]

    # LC_ALL=C : les messages d'erreur de psql sont localisés, donc illisibles
    # pour toute detection par motif. On les force en anglais.
    env = dict(os.environ, PGPASSWORD=PASSWORD, LC_ALL="C")
    # Le SQL passe par stdin (-f -) et non par -c : psql n'interpole ses variables
    # que dans le flux lu, jamais dans une commande -c.
    if shutil.which("psql"):
        cmd = ["psql", "-h", HOST, "-p", PORT, "-U", USER, "-d", DB, *args_common, "-f", "-"]
    else:
        _ensure_up()
        cmd = ["docker", "exec", "-i", "-e", f"PGPASSWORD={PASSWORD}", CONTAINER,
               "psql", "-U", USER, "-d", DB, *args_common, "-f", "-"]

    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=600, input=sql)
    # Un echec alors que le serveur est a l'arret est un probleme de serveur, pas de
    # requete : on le relance et on rejoue une fois. Test sur l'etat du conteneur et
    # non sur le message d'erreur, qui depend de la locale.
    if proc.returncode != 0 and not _container_running():
        _ensure_up()
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env,
                              timeout=600, input=sql)
    if proc.returncode != 0:
        raise CcdbError(proc.stderr.strip() or "échec de la requête")

    rows = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _cell(row: dict, col: str) -> str:
    """Valeur affichable : les NULL deviennent une chaîne vide, les sauts un espace."""
    value = row.get(col)
    if value is None:
        return ""
    return " ".join(str(value).split())


def render(rows: list[dict], fmt: str) -> str:
    if fmt == "json":
        return json.dumps(rows, ensure_ascii=False, indent=2)
    if not rows:
        return "(aucun résultat)"
    cols = list(rows[0])
    if fmt == "tsv":
        return "\n".join([SEP.join(cols)] +
                         [SEP.join(_cell(r, c) for c in cols) for r in rows])
    widths = {c: max(len(c), *(len(_cell(r, c)) for r in rows)) for c in cols}
    out = ["  ".join(c.ljust(widths[c]) for c in cols),
           "  ".join("-" * widths[c] for c in cols)]
    out += ["  ".join(_cell(r, c).ljust(widths[c]) for c in cols) for r in rows]
    return "\n".join(out)


# --- sous-commandes ---------------------------------------------------------

def cmd_stats(_args) -> list[dict]:
    return query("""
        SELECT 'souches (génomes complets)' AS item, count(*)::text AS valeur FROM strain
        UNION ALL SELECT 'séquences (réplicons)', count(*)::text FROM sequence
        UNION ALL SELECT 'loci CRISPR (tous niveaux)', count(*)::text FROM crisprlocus
        UNION ALL SELECT 'loci CRISPR (evidence 4)', count(*)::text FROM crisprlocus WHERE evidencelevel=4
        UNION ALL SELECT 'clusters cas', count(*)::text FROM clustercas
        UNION ALL SELECT 'régions (DR+spacers+flancs)', count(*)::text FROM region
        UNION ALL SELECT 'spacers distincts', count(*)::text FROM region WHERE category=3
        UNION ALL SELECT 'DR distincts', count(*)::text FROM region WHERE category=1
        UNION ALL SELECT 'taille de la base', pg_size_pretty(pg_database_size(current_database()));
    """)


def cmd_strain(args) -> list[dict]:
    """Recherche de souches par nom d'organisme, accession d'assemblage ou de réplicon."""
    return query("""
        SELECT d.name AS organisme,
               st.genbank, st.refseq, st.taxon::text AS taxid,
               d.superkingdom AS regne, d.cas_type AS systeme_cas,
               d.crispr_all_sum::text AS n_loci_crispr,
               d.crispr4_all_sum::text AS n_loci_ev4,
               d.release AS version_genbank,
               (SELECT string_agg(e.name, ',') FROM sequence sq
                  JOIN entity e ON e.id = sq.id WHERE sq.strain = st.id) AS replicons
        FROM crisprcasdb d
        JOIN strain st ON st.id = d.id
        WHERE d.name ILIKE '%' || :'pattern' || '%'
           OR st.genbank ILIKE :'pattern' || '%'
           OR st.refseq ILIKE :'pattern' || '%'
           OR EXISTS (SELECT 1 FROM sequence sq JOIN entity e ON e.id = sq.id
                      WHERE sq.strain = st.id AND e.name ILIKE :'pattern' || '%')
        ORDER BY d.name
        LIMIT :limite;
    """, {"pattern": args.pattern, "limite": args.limit})


def _locus_filter(all_levels: bool) -> str:
    return "" if all_levels else " AND cl.evidencelevel = 4"


def cmd_arrays(args) -> list[dict]:
    """Loci CRISPR d'une souche, avec DR consensus et nombre de spacers."""
    return query(f"""
        SELECT e.name AS organisme, es.name AS replicon,
               cl.start::text AS debut, cl.length::text AS longueur,
               CASE cl.orientation WHEN 1 THEN '+' WHEN 2 THEN '-' ELSE 'ND' END AS sens,
               cl.evidencelevel::text AS evidence,
               round(cl.drconservation, 1)::text AS cons_dr,
               round(cl.spacerconservation, 1)::text AS cons_spacer,
               rd.sequence AS dr_consensus,
               (SELECT count(*) FROM crisprlocus_region lr JOIN region r ON r.id = lr.region
                 WHERE lr.crisprlocus = cl.id AND r.category = 3)::text AS n_spacers,
               cl.id::text AS locus_id
        FROM crisprlocus cl
        JOIN sequence sq ON sq.id = cl.sequence
        JOIN entity es ON es.id = sq.id
        JOIN strain st ON st.id = sq.strain
        JOIN entity e ON e.id = st.id
        LEFT JOIN region rd ON rd.id = cl.drconsensus
        WHERE (e.name ILIKE '%' || :'pattern' || '%'
               OR st.genbank ILIKE :'pattern' || '%'
               OR st.refseq ILIKE :'pattern' || '%'
               OR es.name ILIKE :'pattern' || '%')
              {_locus_filter(args.all_levels)}
        ORDER BY e.name, es.name, cl.start
        LIMIT :limite;
    """, {"pattern": args.pattern, "limite": args.limit})


def cmd_spacers(args) -> list[dict]:
    """Spacers (et DR si demandé) d'une souche, dans l'ordre génomique."""
    categories = "(1,3)" if args.with_dr else "(3)"
    return query(f"""
        SELECT es.name AS replicon, cl.start::text AS locus_debut,
               row_number() OVER (PARTITION BY cl.id ORDER BY lr.start)::text AS rang,
               lr.start::text AS position, r.category::text AS categorie,
               length(r.sequence)::text AS taille, r.sequence AS sequence,
               e.name AS organisme
        FROM crisprlocus cl
        JOIN crisprlocus_region lr ON lr.crisprlocus = cl.id
        JOIN region r ON r.id = lr.region
        JOIN sequence sq ON sq.id = cl.sequence
        JOIN entity es ON es.id = sq.id
        JOIN strain st ON st.id = sq.strain
        JOIN entity e ON e.id = st.id
        WHERE (e.name ILIKE '%' || :'pattern' || '%'
               OR st.genbank ILIKE :'pattern' || '%'
               OR st.refseq ILIKE :'pattern' || '%'
               OR es.name ILIKE :'pattern' || '%')
              AND r.category IN {categories}
              {_locus_filter(args.all_levels)}
        ORDER BY e.name, es.name, cl.start, lr.start
        LIMIT :limite;
    """, {"pattern": args.pattern, "limite": args.limit})


def cmd_whohas(args) -> list[dict]:
    """Recherche inverse : quels organismes portent ce spacer (ou ce DR) ?"""
    mode = "r.sequence = upper(:'seq')" if args.exact else "r.sequence ILIKE '%' || :'seq' || '%'"
    return query(f"""
        SELECT e.name AS organisme, es.name AS replicon, st.taxon::text AS taxid,
               d.cas_type AS systeme_cas, cl.start::text AS locus_debut,
               cl.evidencelevel::text AS evidence, r.category::text AS categorie,
               r.sequence AS sequence
        FROM region r
        JOIN crisprlocus_region lr ON lr.region = r.id
        JOIN crisprlocus cl ON cl.id = lr.crisprlocus
        JOIN sequence sq ON sq.id = cl.sequence
        JOIN entity es ON es.id = sq.id
        JOIN strain st ON st.id = sq.strain
        JOIN entity e ON e.id = st.id
        LEFT JOIN crisprcasdb d ON d.id = st.id
        WHERE {mode} AND r.category IN (1,3)
        ORDER BY e.name
        LIMIT :limite;
    """, {"seq": args.sequence, "limite": args.limit})


def cmd_cas(args) -> list[dict]:
    """Systèmes cas d'une souche : type de cluster et gènes détectés."""
    return query("""
        SELECT e.name AS organisme, es.name AS replicon,
               cc.class AS type_systeme, cc.start::text AS debut, cc.length::text AS longueur,
               (SELECT string_agg(cg.gene, ', ' ORDER BY cg.start)
                  FROM clustercas_gene cg WHERE cg.clustercas = cc.id) AS genes
        FROM clustercas cc
        JOIN sequence sq ON sq.id = cc.sequence
        JOIN entity es ON es.id = sq.id
        JOIN strain st ON st.id = sq.strain
        JOIN entity e ON e.id = st.id
        WHERE e.name ILIKE '%' || :'pattern' || '%'
           OR st.genbank ILIKE :'pattern' || '%'
           OR es.name ILIKE :'pattern' || '%'
        ORDER BY e.name, cc.start
        LIMIT :limite;
    """, {"pattern": args.pattern, "limite": args.limit})


def cmd_taxon(args) -> list[dict]:
    """Souches d'un clade, par descente récursive de l'arbre taxonomique NCBI.

    Le filtre par taxid est le seul fiable : un ILIKE sur le nom ramène des
    faux positifs d'autres genres (« bovis » attrape Streptococcus bovis).
    """
    return query("""
        WITH RECURSIVE clade AS (
            SELECT id, scientificname, rank FROM taxon WHERE id = :taxid
            UNION ALL
            SELECT t.id, t.scientificname, t.rank
              FROM taxon t JOIN clade c ON t.parent = c.id
        )
        SELECT d.name AS organisme, st.genbank, st.taxon::text AS taxid,
               c.scientificname AS taxon_ncbi, c.rank AS rang,
               d.cas_type AS systeme_cas, d.crispr4_all_sum::text AS n_loci_ev4
        FROM clade c
        JOIN strain st ON st.taxon = c.id
        JOIN crisprcasdb d ON d.id = st.id
        ORDER BY d.name
        LIMIT :limite;
    """, {"taxid": args.taxid, "limite": args.limit})


def cmd_sql(args) -> list[dict]:
    return query(args.query)


def to_fasta(rows: list[dict]) -> str:
    out = []
    for i, row in enumerate(rows, 1):
        seq = _cell(row, "sequence")
        if not seq:
            continue
        try:
            category = CATEGORY_LABEL.get(int(_cell(row, "categorie") or SPACER), "?")
        except ValueError:
            category = "?"
        label = [_cell(row, "organisme"), _cell(row, "replicon"),
                 f"locus{_cell(row, 'locus_debut')}", f"rang{_cell(row, 'rang') or i}",
                 category]
        out.append(">" + "|".join(p for p in label if p) + "\n" + seq)
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--format", choices=["table", "tsv", "json", "fasta"], default="table")
    parser.add_argument("--limit", type=int, default=100)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("stats", help="volumétrie de la base").set_defaults(func=cmd_stats)

    p = sub.add_parser("strain", help="chercher une souche (nom, GCA/GCF, accession réplicon)")
    p.add_argument("pattern"); p.set_defaults(func=cmd_strain)

    p = sub.add_parser("arrays", help="loci CRISPR d'une souche")
    p.add_argument("pattern")
    p.add_argument("--all-levels", action="store_true",
                   help="inclure les loci d'evidence 1-3 (bruit : faux positifs GC-riches)")
    p.set_defaults(func=cmd_arrays)

    p = sub.add_parser("spacers", help="spacers d'une souche, dans l'ordre génomique")
    p.add_argument("pattern")
    p.add_argument("--with-dr", action="store_true", help="inclure les DR")
    p.add_argument("--all-levels", action="store_true")
    p.set_defaults(func=cmd_spacers)

    p = sub.add_parser("whohas", help="quels organismes portent ce spacer ?")
    p.add_argument("sequence")
    p.add_argument("--exact", action="store_true", help="égalité stricte au lieu d'une sous-chaîne")
    p.set_defaults(func=cmd_whohas)

    p = sub.add_parser("cas", help="systèmes cas et gènes d'une souche")
    p.add_argument("pattern"); p.set_defaults(func=cmd_cas)

    p = sub.add_parser("taxon", help="souches d'un clade NCBI (récursif). MTBC = 77643")
    p.add_argument("taxid", type=int); p.set_defaults(func=cmd_taxon)

    p = sub.add_parser("sql", help="requête SQL libre (lecture seule recommandée)")
    p.add_argument("query"); p.set_defaults(func=cmd_sql)

    args = parser.parse_args()
    try:
        rows = args.func(args)
    except CcdbError as exc:
        print(f"erreur : {exc}", file=sys.stderr)
        return 1
    print(to_fasta(rows) if args.format == "fasta" else render(rows, args.format))
    return 0


if __name__ == "__main__":
    sys.exit(main())
