#!/usr/bin/env python3
"""Balayer le registre bio.tools (ELIXIR) et ne rendre que ce que nous n'avons PAS deja.

POURQUOI CE SCRIPT EXISTE
-------------------------
bio.tools indexe ~30 000 outils. Interroger le registre est facile ; le probleme est
qu'une requete rend surtout ce qu'on connait deja, noye dans des outils hors sujet.
Ce script fait donc les trois choses qui ont de la valeur :

  1. il interroge plusieurs termes en une passe (le registre n'a pas de notion de
     « domaine MTBC », il faut balayer) ;
  2. il DIFFE le resultat contre le texte integral de nos SKILL.md et de la base de
     connaissances : un outil deja mentionne quelque part n'est pas une decouverte ;
  3. il trie sur les champs de qualite de la fiche (`homepage_status`, `maturity`,
     `publication`), parce qu'une entree bio.tools peut pointer un site mort.

Le diff est le coeur : sans lui, un balayage de 169 outils est illisible. Mesure du
2026-08-17 sur 16 termes : 169 outils distincts, dont 27 deja presents chez nous et
50 absents ET trouves par un terme ciblant nos organismes.

PIEGES DU REGISTRE, verifies
  * `q=` cherche dans TOUT le texte de la fiche, donc « lineage barcode » remonte des
    outils de code-barres CELLULAIRE (BARtab, CellDestiny, TedSim) qui n'ont rien a voir
    avec les barcodes de lignee bacterienne. Un terme technique polysemique doit etre
    lu comme du bruit potentiel, pas comme un resultat.
  * le domaine medical domine les requetes « tuberculosis » : radiologie, depistage,
    scores cliniques (DecXpert, Qure.ai, ScreenTB, mtTB, COTS). Sans filtrage, ils
    ecrasent la genomique.
  * `page=N` renvoie une erreur sur certaines requetes : suivre le champ `next` de la
    reponse, qui est la pagination fiable.
  * `count` peut plafonner : un `q=` large ne rend pas forcement tout, d'ou l'interet de
    plusieurs termes etroits plutot qu'un terme vague.

API : `https://bio.tools/api/tool/?q=<terme>&format=json`, sans authentification, plus
`.../api/tool/<biotoolsID>/?format=json` pour la fiche complete. Parametres verifies :
`q`, `name`, `topic`, `topicID` (EDAM, ex. `topic_3301`), `operation`.

USAGE
  python3 biotools_scan.py --preset mtbc
  python3 biotools_scan.py --preset yersinia --details
  python3 biotools_scan.py --termes "spoligotyping,MIRU-VNTR" --out rapport.md
  python3 biotools_scan.py --preset mycobacteries --json inventaire.json

CODES DE SORTIE : 0 = rien de neuf ; 1 = au moins un candidat inconnu ; 2 = registre
injoignable.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://bio.tools/api/tool"
REPO = pathlib.Path(__file__).resolve().parents[3]
KBS = (
    pathlib.Path.home() / ".Codex" / "knowledge",
    pathlib.Path.home() / ".claude" / "knowledge",
)

PRESETS = {
    "mtbc": ["Mycobacterium tuberculosis", "tuberculosis", "spoligotyping", "MIRU-VNTR",
             "lineage barcode", "drug resistance prediction", "regions of difference",
             "transmission cluster", "mixed infection"],
    "mycobacteries": ["Mycobacterium", "Mycobacterium abscessus", "Mycobacterium avium",
                      "Mycobacterium leprae", "nontuberculous", "mycobacterial"],
    "yersinia": ["Yersinia", "Yersinia pestis", "plague", "cgMLST", "Enterobacteriaceae"],
    "mobilome": ["insertion sequence", "transposon", "mobile genetic element", "IS element"],
}

# Noms trop generiques pour qu'une correspondance textuelle prouve quoi que ce soit.
TROP_GENERIQUE = {"yersinia", "mycobacterium", "tuberculosis", "galaxy", "blast", "bwa",
                  "kraken", "snippy", "spades", "prokka", "mash", "abricate"}


def api(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "biotools-scan/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def chercher(terme: str, max_pages: int = 3) -> list[dict]:
    """Suit le champ `next` plutot que d'incrementer `page` (qui erre sur certaines
    requetes)."""
    url = f"{API}/?q={urllib.parse.quote(terme)}&format=json"
    out, pages = [], 0
    while url and pages < max_pages:
        d = api(url)
        out.extend(d.get("list", []))
        nxt = d.get("next")
        url = (API + "/" + nxt.lstrip("?")) if nxt and nxt.startswith("?") else nxt
        pages += 1
        time.sleep(0.4)
    return out


def corpus_local(knowledge_dirs: tuple[pathlib.Path, ...] = KBS) -> str:
    """Tout notre texte : SKILL.md du depot + bases de connaissances Claude/Codex."""
    morceaux = []
    for p in REPO.rglob("SKILL.md"):
        if "/.git/" in str(p):
            continue
        try:
            morceaux.append(p.read_text(errors="replace"))
        except OSError:
            pass
    vus: set[pathlib.Path] = set()
    for kb in knowledge_dirs:
        if not kb.is_dir():
            continue
        for p in kb.glob("*.md"):
            try:
                resolved = p.resolve()
            except OSError:
                resolved = p
            if resolved in vus:
                continue
            vus.add(resolved)
            morceaux.append(p.read_text(errors="replace"))
    return "\n".join(morceaux).lower()


def deja_connu(nom: str, texte: str) -> bool:
    n = nom.lower().strip()
    if n in TROP_GENERIQUE or len(n) < 4:
        return True                       # indecidable : on ne le presente pas comme neuf
    motif = re.escape(n).replace(r"\-", "[-_ ]?").replace(r"\ ", "[-_ ]?")
    return re.search(motif, texte) is not None


def fiche(biotools_id: str) -> dict:
    try:
        return api(f"{API}/{urllib.parse.quote(biotools_id)}/?format=json")
    except Exception:                                            # noqa: BLE001
        return {}


def qualite(f: dict) -> str:
    """Signaux de fiabilite de la fiche. Une entree peut pointer un site mort."""
    bits = []
    hs = f.get("homepage_status")
    if hs not in (0, None):
        bits.append(f"HOMEPAGE_SUSPECTE({hs})")
    if f.get("maturity"):
        bits.append(str(f["maturity"]))
    pub = f.get("publication") or []
    dois = [p.get("doi") for p in pub if p.get("doi")]
    bits.append(f"{len(pub)} publi" + (f" ({dois[0]})" if dois else " sans DOI"))
    if f.get("license"):
        bits.append(str(f["license"]))
    return " | ".join(bits) if bits else "pas de signal"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preset", choices=sorted(PRESETS))
    ap.add_argument("--termes", help="liste de termes separes par des virgules")
    ap.add_argument("--details", action="store_true",
                    help="recuperer la fiche complete des candidats (lent, 1 appel chacun)")
    ap.add_argument("--out", help="rapport Markdown")
    ap.add_argument("--json", help="inventaire brut en JSON")
    args = ap.parse_args()

    termes = PRESETS.get(args.preset, []) + (args.termes.split(",") if args.termes else [])
    termes = [t.strip() for t in termes if t.strip()]
    if not termes:
        ap.error("donner --preset et/ou --termes")

    outils: dict[str, dict] = {}
    try:
        for t in termes:
            trouves = chercher(t)
            for o in trouves:
                nom = o.get("name")
                if not nom:
                    continue
                outils.setdefault(nom, {"id": o.get("biotoolsID"),
                                        "desc": (o.get("description") or "").replace("\n", " ")[:200],
                                        "termes": []})["termes"].append(t)
            print(f"  {t:34s} {len(trouves):4d} fiches", file=sys.stderr)
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"REGISTRE INJOIGNABLE : {exc}", file=sys.stderr)
        return 2

    texte = corpus_local()
    neufs = {n: m for n, m in outils.items() if not deja_connu(n, texte)}
    connus = len(outils) - len(neufs)

    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(outils, indent=1, ensure_ascii=False))

    lignes = [f"# Balayage bio.tools : {', '.join(termes)}", "",
              f"{len(outils)} outils distincts, {connus} deja presents dans nos skills ou notre KB, "
              f"**{len(neufs)} inconnus**.", "",
              "> Un outil « inconnu » n'est pas forcement pertinent : le registre melange genomique et "
              "clinique, et `q=` cherche dans tout le texte de la fiche. Trier a la main.", ""]
    for n, m in sorted(neufs.items()):
        q = f" — {qualite(fiche(m['id']))}" if args.details and m.get("id") else ""
        lignes.append(f"## {n}  `{m['id']}`{q}")
        lignes.append(f"{m['desc']}")
        lignes.append(f"*trouve via : {', '.join(sorted(set(m['termes'])))}*")
        lignes.append("")
        if args.details:
            time.sleep(0.3)

    rapport = "\n".join(lignes)
    if args.out:
        pathlib.Path(args.out).write_text(rapport)
        print(f"rapport -> {args.out}", file=sys.stderr)
    else:
        print(rapport)
    return 1 if neufs else 0


if __name__ == "__main__":
    sys.exit(main())
