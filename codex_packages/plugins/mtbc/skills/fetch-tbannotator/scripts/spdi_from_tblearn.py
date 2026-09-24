#!/usr/bin/env python3
"""spdi_from_tblearn.py — genere les spdi.txt d'un lot de souches depuis la base
tblearn, par AGREGATION DANS LA BASE, quand ni `mp` ni la route HTTP ne peuvent
les fournir.

Pourquoi ce script existe (mesure du 2026-09-15)
------------------------------------------------
Les deux routes documentees par le skill echouent pour les souches ingerees
recemment :

  * `mp:/data/current/run/results/` est une FENETRE GLISSANTE. Les 121 souches du
    BioProject PRJEB122814, ingerees dans tblearn les 12-14/09/2026, y sont
    absentes a 121/121 alors que la base tblearn porte leurs SPDI.
  * la route HTTP `…/mcp/download/report/{strain}` rend **404 avec un jeton
    valide**, y compris pour une souche presente sur `mp` : elle a disparu avec
    la migration TBannotator -> tblearn (cf. ~/.agents/knowledge/tblearn-migration.md).

Reste la base, dont le client MCP tronque toute reponse a 500 lignes. Un export
naif (une ligne par variant) est donc impossible : ~2 500 variants par souche.
La parade est celle que le depot prescrit deja — AGREGER DANS LA BASE : un
`string_agg` rend UNE ligne par souche, quel que soit son nombre de variants.
Mesure : ~60 ko et ~0,9 s par souche, soit ~9 s par lot de dix.

Ce que le script garantit, et qui est le vrai enjeu
---------------------------------------------------
Toutes les souches d'un meme appel passent par le MEME chemin, le MEME filtre et
la MEME date. C'est ce qui rend un alignement comparable : des `spdi.txt` ecrits
par des generations de pipeline differentes portent un ecart systematique (+3,3 %
mesure entre des fichiers d'avril-mai 2026 et la table de septembre 2026) qui se
lit ensuite comme un signal biologique.

Filtre par defaut : `is_snp` seul. Les variants non-SNP (indel, complex) sont
ceux dont la regle de selection historique est inconnue (un fichier local porte
~130 des ~200 variants complex sans qu'on sache lesquels) et ceux qui varient le
plus d'une version de pipeline a l'autre. `--all-variants` retablit le total.

ATTENTION, ce que le script ne corrige PAS : le traitement AMONT. Deux souches
annotees par deux versions de pipeline (`report_schema_version`) gardent leurs
variants tels qu'appeles. Le manifeste porte la version par souche, precisement
pour que ce confondant reste visible.

Usage
-----
    python3 spdi_from_tblearn.py --list ids.tsv --root /chemin/bdd/actuelle
    python3 spdi_from_tblearn.py --list ids.tsv --root ... --batch 10 --force
    python3 spdi_from_tblearn.py --list ids.tsv --root ... --all-variants

`ids.tsv` : une accession par ligne, deuxieme colonne facultative = repertoire de
clade (sinon `--default-clade`, defaut `a_ranger`). Lignes `#` ignorees.

Sorties : `<root>/<clade>/<acc>/NC_000962.3/spdi.txt` + `<root>/manifeste_export.tsv`
(accession, clade, n_ecrits, version de schema, snp_count de la table, date).

Projet : mtbc/ (transverse)  ·  Date : 2026-09-15
"""
import argparse
import csv
import datetime as dt
import importlib.util
import sys
from pathlib import Path

CLIENT = Path(__file__).resolve().parents[2] / "tbannotator-mcp/scripts/tblearn_client.py"

SQL = """
SELECT s.run_accession,
       s.report_schema_version,
       s.snp_count,
       count(*) FILTER (WHERE {flt}) AS n,
       string_agg(p.spdi_variant_name, ',') FILTER (WHERE {flt}) AS spdi
FROM tb_report_strain s
JOIN tb_report_strain_spdi ss ON ss.strain_id = s.strain_id
JOIN tb_report_spdi p ON p.spdi_id = ss.spdi_id
WHERE s.run_accession IN ({ids})
GROUP BY 1, 2, 3
"""


def query(sql, timeout=900):
    """Appelle tool_query_postgres et rend les lignes CSV (separateur ';')."""
    spec = importlib.util.spec_from_file_location("tblearn_client", CLIENT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.call("tool_query_postgres", {"sql": sql}, timeout=timeout)


def read_list(path, default_clade):
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.replace("\t", " ").split()
            acc = parts[0]
            clade = parts[1] if len(parts) > 1 else default_clade
            out.append((acc, clade))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", required=True, help="TSV accession[<TAB>clade]")
    ap.add_argument("--root", required=True, help="racine de sortie (bdd/actuelle ou bac a sable)")
    ap.add_argument("--default-clade", default="a_ranger")
    ap.add_argument("--batch", type=int, default=10)
    ap.add_argument("--all-variants", action="store_true",
                    help="ecrire aussi les variants non-SNP (indel, complex)")
    ap.add_argument("--force", action="store_true", help="reecrire un spdi.txt existant")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    flt = "TRUE" if args.all_variants else "p.is_snp"
    root = Path(args.root)
    targets = read_list(args.list, args.default_clade)
    todo = [(a, c) for a, c in targets
            if args.force or not (root / c / a / "NC_000962.3/spdi.txt").is_file()]
    print(f"{len(targets)} demandees, {len(todo)} a exporter "
          f"(filtre : {'tous variants' if args.all_variants else 'SNP seuls'})", flush=True)
    if args.dry_run or not todo:
        for a, c in todo[:20]:
            print(f"  {a}\t{c}")
        return 0

    stamp = dt.datetime.now().isoformat(timespec="seconds")
    manifest = root / "manifeste_export.tsv"
    new = not manifest.is_file()
    root.mkdir(parents=True, exist_ok=True)
    seen, written = set(), 0
    with open(manifest, "a", newline="") as mf:
        w = csv.writer(mf, delimiter="\t")
        if new:
            w.writerow(["accession", "clade", "n_ecrits", "report_schema_version",
                        "snp_count_table", "filtre", "exporte_le"])
        clade_of = dict(todo)
        for i in range(0, len(todo), args.batch):
            chunk = todo[i:i + args.batch]
            ids = ",".join("'%s'" % a for a, _ in chunk)
            txt = query(SQL.format(flt=flt, ids=ids))
            for row in txt.split("\n"):
                row = row.strip()
                if not row or row.startswith("run_accession;"):
                    continue
                parts = row.split(";")
                if len(parts) < 5:
                    continue
                acc, ver, snpc, n, spdi = parts[0], parts[1], parts[2], parts[3], parts[4]
                clade = clade_of.get(acc, args.default_clade)
                d = root / clade / acc / "NC_000962.3"
                d.mkdir(parents=True, exist_ok=True)
                variants = [v for v in spdi.split(",") if v]
                (d / "spdi.txt").write_text("\n".join(variants) + "\n")
                w.writerow([acc, clade, len(variants), ver, snpc,
                            "all" if args.all_variants else "snp", stamp])
                seen.add(acc)
                written += 1
            mf.flush()
            print(f"  lot {i // args.batch + 1}/{-(-len(todo) // args.batch)} : "
                  f"{written} ecrites", flush=True)

    manquants = [a for a, _ in todo if a not in seen]
    if manquants:
        print(f"ABSENTES DE LA BASE ({len(manquants)}) : {' '.join(manquants[:20])}",
              file=sys.stderr)
    print(f"Termine : {written} spdi.txt ecrits sous {root}")
    return 1 if manquants else 0


if __name__ == "__main__":
    sys.exit(main())
