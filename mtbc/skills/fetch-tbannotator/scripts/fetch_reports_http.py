#!/usr/bin/env python3
"""fetch_reports_http.py — recuperer `report.json` + `spdi.txt` par la route HTTP, en lot.

Route HTTP de TBannotator (`/mcp/download/report/<SRA>`), qui sert la base ANNOTEE. C'est la
route qui tient quand `mp` ne repond pas — et `mp` est une FENETRE GLISSANTE, donc une souche
peut y etre absente tout en etant parfaitement servie ici (verifie plusieurs fois : 47 souches
recuperees en HTTP alors que `mp` n'en avait aucune, temoin positif compris).

Pourquoi ce script existe : cinq projets portaient chacun leur variante de cette boucle
(`a_ranger_phylo/phase22b_fetch_pending.py`, `phase7_download_v2.py`, `Bovis_proto/phase0_...`,
`Oman/fetch_oman_public_genomes.py`, `Bovis_emergence/rdtype_...`), toutes couplees a leur
repertoire d'origine. Le geste est generique, il vit donc ici.

TROIS GARDE-FOUS, dont un appris le 2026-08-17

  IDENTITE. Le `report.json` porte un champ `strain_id`. On le COMPARE a l'accession demandee et
  on refuse d'ecrire en cas de desaccord. Sans ce test, une erreur de routage cote serveur, un
  cache mal invalide ou une redirection ecrivent le genome d'une autre souche sous le bon nom —
  la faute la plus couteuse possible dans une base de reference, et parfaitement silencieuse.
  (Le champ existe : il avait ete manque lors d'une premiere passe parce qu'un `sorted(keys)[:6]`
  le tronquait, et le controle avait alors du etre fait par un detour biologique sur les RD.)

  IDEMPOTENCE. Une souche qui a deja ses deux fichiers est sautee, sauf `--force`. Relancer le
  script sur une liste partiellement traitee ne redemande rien au serveur.

  ECRITURE ATOMIQUE PAR SOUCHE. Le JSON est valide et les SPDI extraits AVANT toute ecriture
  dans la base ; un echec ne laisse donc pas un repertoire a moitie peuple, qui compterait
  ensuite comme une souche presente dans tous les parcours (`rglob("spdi.txt")`).

Usage :
    python3 fetch_reports_http.py --file accessions.txt --dest ~/docs/codes/mtbc/bdd/a_ranger
    python3 fetch_reports_http.py ERR14185382 SRR8648477 --dest /tmp/essai
    python3 fetch_reports_http.py --file l.txt --dest D --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://tblearn.tbannotator.ideev.universite-paris-saclay.fr/mcp/download/report"
REF = "NC_000962.3"


def fetch(acc: str, timeout: int) -> tuple[dict | None, str]:
    """(report, message). `report` est None si la souche n'est pas exploitable."""
    try:
        with urllib.request.urlopen(f"{BASE}/{acc}", timeout=timeout) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        # 404 = absente de la base annotee -> candidate a l'ingestion (sra_to_add.py).
        # 503 / timeout = panne -> NE PAS conclure a l'absence, reessayer ou passer par mp.
        return None, f"HTTP {e.code}" + (" (absente de la base annotee)" if e.code == 404
                                         else " (panne : ne pas conclure a l'absence)")
    except (urllib.error.URLError, TimeoutError) as e:
        return None, f"reseau : {e} (panne : ne pas conclure a l'absence)"
    try:
        d = json.loads(raw)
    except json.JSONDecodeError as e:
        return None, f"JSON invalide ({e})"
    if not isinstance(d, dict) or not d:
        return None, "JSON vide ou de type inattendu"
    got = str(d.get("strain_id", "") or "")
    if got and got != acc:
        return None, f"IDENTITE : le report annonce strain_id={got!r}, demande {acc!r} — REFUS"
    if not got:
        return None, "IDENTITE : aucun champ strain_id, identite non verifiable — REFUS"
    if not isinstance(d.get("snp"), list):
        return None, "aucune liste `snp` : rien pour ecrire spdi.txt"
    return d, "ok"


def spdis_of(report: dict) -> list[str]:
    """SPDI d'une souche, dedoublonnes et ordonnes par position puis par chaine.

    Un `spdi.txt` ne liste que des PRESENCES, une par ligne, au format
    `NC_000962.3:<pos 0-based>:<ref>:<alt>`. L'ordre n'a pas de sens biologique mais un ordre
    STABLE rend les diffs lisibles quand une souche est refetchee.
    """
    out = {s["spdi"] for s in report["snp"] if isinstance(s, dict) and s.get("spdi")}

    def key(s: str):
        parts = s.split(":")
        try:
            return (int(parts[1]), s)
        except (IndexError, ValueError):
            return (1 << 62, s)

    return sorted(out, key=key)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accessions", nargs="*")
    ap.add_argument("--file", type=Path, help="un fichier d'accessions, une par ligne (1er champ)")
    ap.add_argument("--dest", type=Path, required=True,
                    help="repertoire d'accueil ; ecrit <dest>/<SRA>/" + REF + "/")
    ap.add_argument("--ref", default=REF)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--force", action="store_true", help="refetcher meme si deja present")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pause", type=float, default=0.0, help="secondes entre deux requetes")
    A = ap.parse_args()

    accs = list(A.accessions)
    if A.file:
        for line in A.file.read_text().splitlines():
            tok = line.split()[0].strip() if line.split() else ""
            if tok and not tok.startswith("#") and tok.lower() != "accession":
                accs.append(tok)
    accs = list(dict.fromkeys(accs))
    if not accs:
        sys.exit("aucune accession (donner des arguments ou --file)")

    deja = [a for a in accs
            if (A.dest / a / A.ref / "spdi.txt").is_file()
            and (A.dest / a / A.ref / "report.json").is_file()]
    todo = accs if A.force else [a for a in accs if a not in deja]
    print(f"[cible] {A.dest}")
    print(f"[lot] {len(accs)} accessions, {len(deja)} deja completes"
          f"{' (refetch force)' if A.force else ' (sautees)'}, {len(todo)} a traiter")
    if A.dry_run:
        for a in todo[:20]:
            print(f"    {a} -> {A.dest / a / A.ref}/")
        if len(todo) > 20:
            print(f"    ... et {len(todo)-20} autres")
        print("\n(simulation — retirer --dry-run pour ecrire)")
        return 0

    ok, echecs = [], []
    t0 = time.time()
    for i, acc in enumerate(todo, 1):
        rep, msg = fetch(acc, A.timeout)
        if rep is None:
            echecs.append((acc, msg))
            print(f"  [{i}/{len(todo)}] ECHEC {acc} : {msg}", flush=True)
            continue
        spdis = spdis_of(rep)
        d = A.dest / acc / A.ref
        d.mkdir(parents=True, exist_ok=True)
        (d / "report.json").write_text(json.dumps(rep))
        (d / "spdi.txt").write_text("\n".join(spdis) + ("\n" if spdis else ""))
        ok.append((acc, len(spdis)))
        if i % 10 == 0 or i == len(todo):
            print(f"  [{i}/{len(todo)}] {acc} : {len(spdis)} SPDI  "
                  f"({time.time()-t0:.0f}s)", flush=True)
        if A.pause:
            time.sleep(A.pause)

    print(f"\n[bilan] {len(ok)} recuperees, {len(echecs)} en echec, "
          f"{len(deja) if not A.force else 0} sautees  ({time.time()-t0:.0f}s)")
    if ok:
        n = [c for _, c in ok]
        n.sort()
        print(f"        SPDI par souche : mediane {n[len(n)//2]}, min {n[0]}, max {n[-1]}")
        # Un compte de SPDI aberrant est le premier signe d'une souche hors clade ou d'un
        # melange : on le signale ici plutot que de le laisser decouvrir par un arbre.
        suspects = [(a, c) for a, c in ok if c < 100 or c > 5000]
        if suspects:
            print(f"        /!\\ {len(suspects)} souche(s) au compte de SPDI ATYPIQUE "
                  f"(< 100 ou > 5000) : a passer au controle d'espece (skill `species-id`)")
            for a, c in suspects[:10]:
                print(f"            {a} : {c} SPDI")
    if echecs:
        print("\n[echecs]")
        for a, m in echecs:
            print(f"    {a} : {m}")
        n404 = sum(1 for _, m in echecs if "404" in m)
        if n404:
            print(f"\n  {n404} en 404 = absentes de la base annotee -> candidates a l'INGESTION "
                  f"(sra_to_add.py --check), pas au fetch.")
        if len(echecs) > n404:
            print(f"  {len(echecs)-n404} en panne/reseau : NE PAS conclure a l'absence, "
                  f"relancer (le script est idempotent) ou passer par mp.")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
