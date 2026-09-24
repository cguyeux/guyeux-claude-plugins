#!/usr/bin/env python3
"""
Objet: construire le panel d'un test INTER-DOMAINE à partir d'un domaine Pfam, ce que le
    `build_panel.py` du skill frère ne sait pas faire (il part de hits BLAST contre des génomes
    donneurs). Récupère par l'API InterPro les protéines portant le domaine dans chaque domaine
    du vivant, EXTRAIT le domaine à ses coordonnées — aligner un domaine de 143 aa contre des
    protéines eucaryotes de 1 200 aa est la façon la plus sûre de fabriquer un artefact —,
    équilibre l'échantillon par genre et rattache chaque séquence à son phylum par la taxonomie
    NCBI, jamais par devinette.
Entrées: --pfam (PF00856 pour le domaine SET), --group DOMAINE:taxid[:reviewed] répétable,
    --query-faa (la séquence testée, ajoutée au panel), --out.
Sorties: <out>/panel.faa (domaines extraits, dédupliqués), <out>/taxonomy.tsv
    (étiquette<TAB>domaine<TAB>phylum, prêt pour topology_test.py et read_interdomain.py),
    <out>/rapport.txt, <out>/genres_non_rattaches.txt s'il en reste.
Réutilisable: oui, c'est l'étape 1 du skill hgt-interdomain-check.
Projet: écrit pour environnement/pistes.md AG2, vérif (d).
Date: 2026-09-22.

Exigence de panel qui n'est pas une préférence de style. Le paradigme « les bactéries ont pris
leurs gènes à domaine SET chez leur hôte » tenait à ce que seules les bactéries PATHOGÈNES et
SYMBIOTIQUES étaient séquencées : élargir aux espèces libres et environnementales a suffi à le
retourner (Alvarez-Venegas et al. 2007, Mol. Biol. Evol., PMID 17148507). D'où l'équilibrage par
genre plutôt qu'un simple « les N premiers », et le rapport qui affiche la diversité obtenue :
un panel de trente *Legionella* et deux autres genres ne démontrerait rien, quelle que soit la
qualité de l'arbre qui en sortirait.
"""

import argparse
import json
import random
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

INTERPRO = "https://www.ebi.ac.uk/interpro/api"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
DOMAINES = ("BACTERIA", "EUKARYOTA", "ARCHAEA", "VIRUS", "AUTRE")


def get_json(url, essais=3, cache=None):
    """Cache disque par URL : l'API InterPro rend les séquences entières, donc une page coûte
    cher, et une relance du script (pour ajuster un quota, corriger une étiquette) re-paierait
    tout le téléchargement. Le cache rend la construction du panel rejouable pour rien."""
    fichier = None
    if cache is not None:
        import hashlib
        fichier = cache / (hashlib.sha1(url.encode()).hexdigest() + ".json")
        if fichier.exists():
            return json.loads(fichier.read_text(encoding="utf-8"))
    for k in range(essais):
        try:
            with urllib.request.urlopen(url, timeout=180) as r:
                brut = r.read().decode("utf-8")
            if fichier is not None:
                cache.mkdir(parents=True, exist_ok=True)
                fichier.write_text(brut, encoding="utf-8")
            return json.loads(brut)
        except Exception as e:
            if k == essais - 1:
                raise SystemExit(f"échec sur {url} : {e}")
            time.sleep(3 * (k + 1))


def collecte(pfam, taxid, reviewed, plafond, cache=None):
    """Parcourt la pagination InterPro et rend (accession, nom, organisme, taxid, séquence,
    coordonnées du domaine) pour chaque protéine."""
    base = f"{INTERPRO}/protein/{'reviewed' if reviewed else 'UniProt'}/entry/pfam/{pfam}"
    url = f"{base}/taxonomy/uniprot/{taxid}/?page_size=200&extra_fields=sequence"
    out, page = [], 0
    while url and len(out) < plafond:
        d = get_json(url, cache=cache)
        page += 1
        print(f"  ... taxid {taxid}, page {page}, {len(out)} protéines lues",
              file=sys.stderr, flush=True)
        for r in d.get("results", []):
            m, seq = r["metadata"], (r.get("extra_fields") or {}).get("sequence")
            loc = None
            for e in r.get("entries", []):
                for l in e.get("entry_protein_locations", []):
                    frags = l.get("fragments", [])
                    if frags:
                        deb = min(f["start"] for f in frags)
                        fin = max(f["end"] for f in frags)
                        # on garde le match le PLUS LONG : une protéine multi-domaines peut
                        # porter plusieurs copies partielles, et la plus longue est celle qui
                        # s'aligne le mieux sur un domaine isolé
                        if loc is None or (fin - deb) > (loc[1] - loc[0]):
                            loc = (deb, fin)
            if seq and loc:
                org = (m.get("source_organism") or {})
                out.append({"acc": m["accession"], "nom": m.get("name", ""),
                            "organisme": org.get("scientificName", "?"),
                            "taxid": org.get("taxId", ""), "seq": seq, "loc": loc})
        url = d.get("next")
    return out


def lignee_ncbi(taxids, rang, email=None, api_key=None):
    """Rattache chaque taxid au taxon du rang demandé, lu dans la taxonomie NCBI. Le
    rattachement doit être INSTRUIT : un genre oublié transforme une concordance en
    discordance, et c'est un piège déjà payé sur le cas fondateur du skill frère."""
    resultat = {}
    taxids = [t for t in dict.fromkeys(taxids) if t]
    for i in range(0, len(taxids), 200):
        lot = taxids[i:i + 200]
        params = {"db": "taxonomy", "id": ",".join(lot), "retmode": "xml"}
        if email:
            params["email"] = email
        if api_key:
            params["api_key"] = api_key
        url = EUTILS + "?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=180) as r:
            racine = ET.fromstring(r.read())
        for taxon in racine.findall("Taxon"):
            tid = (taxon.findtext("TaxId") or "").strip()
            trouve = None
            for t in taxon.iterfind("LineageEx/Taxon"):
                if (t.findtext("Rank") or "") == rang:
                    trouve = t.findtext("ScientificName")
            resultat[tid] = trouve
        time.sleep(0.4)
    return resultat


def etiquette(prefixe, acc, organisme):
    genre = (organisme or "?").split()[0]
    genre = re.sub(r"[^A-Za-z0-9]", "", genre) or "inconnu"
    return f"{prefixe}_{acc}_{genre}"


def echantillonne(entrees, max_par_genre, plafond, graine):
    """Un panel de trente souches du même genre n'est pas trente observations. On tire au sort
    à graine fixe, au plus `max_par_genre` par genre.

    Le plafond est une BORNE, pas une cible : on ne complète jamais avec les séquences
    écartées par le quota, sinon le genre le mieux séquencé — et ce sont les pathogènes qui le
    sont — reprendrait toute la place qu'on vient de lui retirer, et le panel déciderait du
    résultat. Pour un panel plus fourni, augmenter `--max-per-genus`, pas le plafond."""
    rnd = random.Random(graine)
    par_genre = {}
    for e in entrees:
        par_genre.setdefault((e["organisme"] or "?").split()[0], []).append(e)
    retenus = []
    for _genre, lot in sorted(par_genre.items(), key=lambda kv: kv[0]):
        lot = sorted(lot, key=lambda e: e["acc"])
        rnd.shuffle(lot)
        retenus += lot[:max_par_genre]
    rnd.shuffle(retenus)
    return retenus[:plafond], len(par_genre)


def main():
    p = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[1])
    p.add_argument("--pfam", required=True, help="identifiant Pfam, par exemple PF00856")
    p.add_argument("--group", action="append", required=True,
                   help="DOMAINE:taxid[:reviewed], répétable "
                        "(ex. BACTERIA:2, EUKARYOTA:2759:reviewed, ARCHAEA:2157)")
    p.add_argument("--query-faa", help="FASTA d'une séquence : la requête testée")
    p.add_argument("--query-label", default="QUERY")
    p.add_argument("--query-domain", default="BACTERIA")
    p.add_argument("--query-group", default="?", help="phylum de la requête")
    p.add_argument("--include-genus", action="append",
                   help="genre dont des représentants sont FORCÉS dans le panel, quel que soit "
                        "le tirage ; y mettre le genre de la requête, répétable")
    p.add_argument("--max-per-included-genus", type=int, default=8,
                   help="représentants forcés par genre, un par espèce (défaut 8)")
    p.add_argument("--max-per-genus", type=int, default=2)
    p.add_argument("--max-per-group", type=int, default=60)
    p.add_argument("--fetch-cap", type=int, default=6000,
                   help="plafond de protéines lues par groupe avant échantillonnage")
    p.add_argument("--margin", type=int, default=15, help="marge en résidus autour du domaine")
    p.add_argument("--min-aa", type=int, default=60)
    p.add_argument("--rank", default="phylum", help="rang du rattachement taxonomique")
    p.add_argument("--seed", type=int, default=20260922)
    p.add_argument("--email")
    p.add_argument("--api-key")
    p.add_argument("--cache", help="répertoire de cache des pages InterPro")
    p.add_argument("--out", required=True)
    a = p.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rapport = [f"PANEL INTER-DOMAINE — {a.pfam}", "=" * 78, ""]
    panel, taxonomie, vus = [], [], {}

    for spec in a.group:
        champs = spec.split(":")
        domaine, taxid = champs[0].upper(), champs[1]
        reviewed = len(champs) > 2 and champs[2].lower() == "reviewed"
        if domaine not in DOMAINES:
            raise SystemExit(f"domaine inconnu « {domaine} » ; attendus : " + ", ".join(DOMAINES))
        brut = collecte(a.pfam, taxid, reviewed, a.fetch_cap,
                        cache=Path(a.cache) if a.cache else None)
        retenus, n_genres = echantillonne(brut, a.max_per_genus, a.max_per_group, a.seed)
        rapport.append(f"{domaine:<11} taxid {taxid:<6} {'reviewed' if reviewed else 'tous':<9}"
                       f" : {len(brut)} protéines, {n_genres} genres -> {len(retenus)} retenues")

        # Les CONGÉNÈRES de la requête ne peuvent pas dépendre d'un tirage au sort. Sans eux,
        # la cohérence taxonomique du voisinage n'a rien à mesurer, et surtout on se prive de
        # la question la moins chère et la plus décisive : le domaine est-il présent chez les
        # espèces LIBRES du genre, ou seulement chez celles qui infectent un hôte ?
        rnd_f = random.Random(a.seed)
        forces, deja = [], {e["acc"] for e in retenus}
        for genre in a.include_genus or []:
            lot = sorted([e for e in brut
                          if (e["organisme"] or "").startswith(genre + " ")
                          and e["acc"] not in deja], key=lambda e: e["acc"])
            especes = sorted({" ".join((e["organisme"] or "").split()[:2]) for e in lot})
            if not lot:
                continue
            # un représentant par ESPÈCE, pas par souche : 185 génomes du même genre ne sont
            # pas 185 observations, mais 73 espèces en sont 73
            par_espece = {}
            for e in lot:
                par_espece.setdefault(" ".join((e["organisme"] or "").split()[:2]), []).append(e)
            choisis = [rnd_f.choice(v) for _k, v in sorted(par_espece.items())]
            rnd_f.shuffle(choisis)
            forces += choisis[:a.max_per_included_genus]
            rapport.append(f"{'':11} {'':12} {'':9}   + {min(len(choisis), a.max_per_included_genus)}"
                           f" forcée(s) pour {genre} ({len(especes)} espèces du genre portent le "
                           f"domaine)")
        retenus = forces + retenus
        for e in retenus:
            deb, fin = e["loc"]
            seq = e["seq"][max(0, deb - 1 - a.margin):min(len(e["seq"]), fin + a.margin)]
            if len(seq) < a.min_aa:
                continue
            if seq in vus:  # dédupliquer par SÉQUENCE, jamais par nom
                continue
            vus[seq] = e["acc"]
            nom = etiquette(domaine[:3], e["acc"], e["organisme"])
            panel.append((nom, seq))
            taxonomie.append((nom, domaine, e["taxid"], e["organisme"]))

    if a.query_faa:
        lignes = Path(a.query_faa).read_text(encoding="utf-8").splitlines()
        seq = "".join(l.strip() for l in lignes if not l.startswith(">"))
        if not seq:
            raise SystemExit(f"aucune séquence dans {a.query_faa}")
        panel.insert(0, (a.query_label, seq))
        taxonomie.insert(0, (a.query_label, a.query_domain.upper(), "", a.query_group))
        rapport.append(f"{'REQUÊTE':<11} {a.query_label} : {len(seq)} aa, ajoutée entière "
                       f"(elle EST le domaine, ou presque : vérifier avant de s'y fier)")

    # rattachement taxonomique, par la taxonomie NCBI et non par une liste écrite de mémoire
    phylums = lignee_ncbi([t[2] for t in taxonomie if t[2]], a.rank, a.email, a.api_key)
    non_rattaches = []
    lignes_tax = []
    for nom, domaine, taxid, organisme in taxonomie:
        grp = phylums.get(taxid) or (organisme if nom == a.query_label else None)
        if not grp:
            grp = "?"
            non_rattaches.append(f"{nom}\t{organisme}\t{taxid}")
        lignes_tax.append(f"{nom}\t{domaine}\t{grp}")

    (out / "panel.faa").write_text(
        "".join(f">{n}\n" + "\n".join(s[i:i + 60] for i in range(0, len(s), 60)) + "\n"
                for n, s in panel), encoding="utf-8")
    (out / "taxonomy.tsv").write_text("\n".join(lignes_tax) + "\n", encoding="utf-8")

    compte = {}
    for l in lignes_tax:
        compte[l.split("\t")[2]] = compte.get(l.split("\t")[2], 0) + 1
    rapport += ["", f"panel final : {len(panel)} séquences après extraction du domaine "
                    f"(marge {a.margin} aa) et déduplication par séquence",
                f"rangs « {a.rank} » représentés : {len(compte)}",
                "  " + ", ".join(f"{k} ({v})" for k, v in
                                 sorted(compte.items(), key=lambda x: -x[1])[:14])]
    if non_rattaches:
        (out / "genres_non_rattaches.txt").write_text("\n".join(non_rattaches) + "\n",
                                                      encoding="utf-8")
        rapport += ["", f"ATTENTION : {len(non_rattaches)} séquence(s) sans rang « {a.rank} » "
                        f"dans la taxonomie NCBI, écrites « ? ».",
                    f"  Les rattacher à la main dans taxonomy.tsv AVANT de lire une "
                    f"discordance de voisinage comme un fait ({out}/genres_non_rattaches.txt)."]
    rapport += ["", "Contrôle à faire à l'oeil avant d'engager le calcul : la liste des genres "
                    "bactériens contient-elle",
                "des espèces LIBRES et environnementales, ou seulement des pathogènes et des "
                "symbiotes ? Dans le",
                "second cas, le panel décidera du résultat à la place des données."]

    texte = "\n".join(rapport)
    (out / "rapport.txt").write_text(texte + "\n", encoding="utf-8")
    print(texte)
    print(f"\n[panel dans {out}/panel.faa, taxonomie dans {out}/taxonomy.tsv]", file=sys.stderr)


if __name__ == "__main__":
    main()
