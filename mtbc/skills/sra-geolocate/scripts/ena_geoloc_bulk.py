#!/usr/bin/env python3
"""
Objet   : geolocalisation EN MASSE d'une liste d'accessions de runs SRA/ENA, par lots
          contre le portail ENA (niveau 1 de la cascade du skill sra-geolocate : le
          champ country du BioSample lie, expose par le resultat read_run). Concu pour
          les cohortes de 10^3 a 10^5 accessions, ou la cascade agentique par accession
          (BioSample, puis BioProject, puis PubMed, puis supplementaires) coute trop
          cher pour etre lancee avant de savoir combien d'accessions resistent au
          niveau 1.
Entrees : un fichier TSV/CSV portant une colonne d'accessions (colonne nommee
          accession / run_accession / sra, sinon la premiere colonne)
Sorties : TSV accession, study_accession, sample_accession, country_raw, country,
          collection_date -- une ligne par accession INTERROGEE, y compris celles que
          l'ENA ne resout pas (country vide), parce que le taux de non-resolution est
          lui-meme un resultat a mesurer avant toute interpretation.
Reutilisable : oui, et c'est son objet. Aucune dependance au MTBC ni au projet.
          Candidat au versement dans le skill mtbc:sra-geolocate comme outil de
          niveau 1 en masse, en amont de la cascade.
Projet  : mixed_infections_multimarker (P7.3.o), ecrit le 2026-09-18

Trois points de methode.

1. L'API filereport n'accepte qu'UNE accession par appel ; le POST sur /search avec une
   disjonction run_accession="A" OR run_accession="B" en accepte plusieurs centaines.
   C'est la difference entre 15 000 requetes et 50.

2. Une accession absente de la reponse n'est pas une erreur du script : le run peut etre
   suppresse, prive, ou n'avoir jamais porte de champ geographique. Elle est ecrite avec
   un pays vide plutot que silencieusement omise, faute de quoi le denominateur d'un
   calcul d'enrichissement se retrouverait ampute sans trace.

3. country_raw est conserve tel quel a cote de country. L'ENA ecrit "China:lanzhou",
   "USA: Texas", "not applicable", "missing" ; ecraser ces valeurs a l'import interdit
   de distinguer plus tard un pays non renseigne d'un pays renseigne mais non normalise.
"""
import argparse
import csv
import pathlib
import sys
import time
import urllib.parse
import urllib.request

API = "https://www.ebi.ac.uk/ena/portal/api/search"
FIELDS = "study_accession,sample_accession,country,collection_date"
# Valeurs que l'ENA ecrit pour dire "pas de pays", et qui ne sont pas des pays.
NULLS = {"", "na", "n/a", "not applicable", "not collected", "missing",
         "unknown", "not provided", "none", "restricted access", "uncalculated"}


def read_accessions(path):
    with open(path, newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        delim = "\t" if "\t" in sample.splitlines()[0] else ","
        rows = list(csv.reader(f, delimiter=delim))
    if not rows:
        return []
    head = [h.strip().lower() for h in rows[0]]
    col = 0
    for name in ("accession", "run_accession", "sra"):
        if name in head:
            col = head.index(name)
            break
    else:
        # Pas d'en-tete reconnue : la premiere ligne est peut-etre deja une accession.
        if not rows[0][0].strip().lower().startswith(("srr", "err", "drr")):
            rows = rows[1:]
        return [r[0].strip() for r in rows if r and r[0].strip()]
    return [r[col].strip() for r in rows[1:] if len(r) > col and r[col].strip()]


def query_batch(accs, retries=4):
    q = " OR ".join(f'run_accession="{a}"' for a in accs)
    data = urllib.parse.urlencode(
        {"result": "read_run", "format": "tsv", "limit": 0,
         "fields": FIELDS, "query": q}).encode()
    text = ""
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(API, data=data, timeout=180) as r:
                text = r.read().decode()
            break
        except Exception as exc:  # reseau, 429, 500 : on retente en s'espacant
            if attempt == retries - 1:
                print(f"  ECHEC definitif sur un lot de {len(accs)} : {exc}",
                      file=sys.stderr, flush=True)
                return {}
            time.sleep(3 * (attempt + 1))
    out = {}
    lines = text.rstrip("\n").split("\n")
    for line in lines[1:]:
        c = line.split("\t")
        if len(c) >= 5:
            out[c[0]] = (c[1], c[2], c[3], c[4])
    return out


def norm_country(raw):
    """Pays au sens large, sans la subdivision. Ne tranche PAS les alias : c'est au
    calcul aval de le faire, avec la meme table que son denominateur."""
    c = (raw or "").split(":")[0].strip()
    return "" if c.lower() in NULLS else c


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="fichier d'accessions (TSV/CSV)")
    ap.add_argument("output", help="TSV de sortie")
    ap.add_argument("--batch", type=int, default=300)
    ap.add_argument("--sleep", type=float, default=0.3,
                    help="pause entre lots, politesse envers l'EBI")
    args = ap.parse_args()

    accs = read_accessions(args.input)
    print(f"{len(accs)} accessions a geolocaliser, lots de {args.batch}", flush=True)

    resolved = {}
    for i in range(0, len(accs), args.batch):
        batch = accs[i:i + args.batch]
        resolved.update(query_batch(batch))
        print(f"  [{min(i+args.batch, len(accs))}/{len(accs)}] "
              f"{len(resolved)} resolus", flush=True)
        time.sleep(args.sleep)

    n_geo = 0
    with open(args.output, "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["accession", "study_accession", "sample_accession",
                    "country_raw", "country", "collection_date"])
        for a in accs:
            study, samp, raw, date = resolved.get(a, ("", "", "", ""))
            c = norm_country(raw)
            n_geo += bool(c)
            w.writerow([a, study, samp, raw, c, date])

    print(f"ENA a rendu une ligne pour {len(resolved)}/{len(accs)} accessions "
          f"({100*len(resolved)/max(1,len(accs)):.1f} %)", flush=True)
    print(f"pays exploitable pour {n_geo}/{len(accs)} "
          f"({100*n_geo/max(1,len(accs)):.1f} %)", flush=True)
    print(f"sortie : {pathlib.Path(args.output).resolve()}", flush=True)


if __name__ == "__main__":
    main()
