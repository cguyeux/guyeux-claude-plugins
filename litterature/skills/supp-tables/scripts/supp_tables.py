#!/usr/bin/env python3
"""supp_tables.py — chercher un gène (ou tout motif) dans les TABLES SUPPLÉMENTAIRES d'articles.

Pourquoi cet outil. La recherche plein texte a un angle mort que ni `tbmonitor` (résumés) ni
`europepmc_fulltext.py search` (corps) ne couvrent : **les identifications protéomiques, les
listes de hits GWAS, les tables d'essentialité et les sorties de cribles CRISPRi vivent dans des
classeurs Excel qu'Europe PMC n'indexe pas**. Un gène peut donc être absent du CORPS de tous les
articles pertinents et présent dans les TABLES de plusieurs d'entre eux. Mesuré le 2026-09-07 sur
`Rv2520c` : la chaîne n'apparaît dans le texte d'aucun des trois articles protéomiques qui portent
les seules données empiriques existantes sur sa topologie, et se trouve dans les tables des trois.

Quatre sous-commandes, dans l'ordre où elles servent :

  hunt      un motif + des DOI            ->  télécharge, décompresse, cherche, rend les lignes
  fetch     des DOI                       ->  télécharge et décompresse seulement
  grep      un répertoire + des motifs    ->  cherche dans ce qui est déjà sur disque
  rank      un fichier/feuille/colonne    ->  OÙ SE SITUE une valeur dans sa propre table

GARDE-FOU CENTRAL, et la raison d'être de `rank`. **Une ligne trouvée dans une table n'est pas un
résultat.** Deux erreurs coûteuses évitées de justesse en 2026-09 : un score de co-purification qui
était en réalité la médiane des protéines non caractérisées de sa propre table (rang 78/94), et un
rapport d'enrichissement de 6,10 qui plaçait le gène entre RpoC et RecA, deux protéines
cytoplasmiques. Dans les deux cas la valeur était réelle et la conclusion fausse. Après tout `hunt`
qui rend un hit numérique, passer `rank` sur la colonne concernée, et chercher le SEUIL que les
auteurs ont eux-mêmes appliqué dans le corps de leur article.

Deux routes de récupération, la seconde INDISPENSABLE :
  1. Europe PMC `/<PMCID>/supplementaryFiles` — la voie propre, mais elle rend une archive VIDE
     pour un article non OA.
  2. Repli **préprint bioRxiv/medRxiv** : la page `<doi>v1.supplementary-material` porte des liens
     `.../DC<n>/embed/media-<n>.xlsx?download=true` librement téléchargeables. PMC, lui, sert
     désormais les fichiers derrière une porte de type proof-of-work (page « Preparing to
     download », cookie + JS) infranchissable en ligne de commande ; un User-Agent ne suffit pas.

PIÈGE DE TRANSFERT, mesuré : `curl` rend des fichiers **tronqués avec un code de sortie 0** quand
le système de fichiers de destination est plein (1,4 Mo au lieu de 10,5 ; 16 Ko au lieu de 7 Mo).
Ce script vérifie donc la taille obtenue et refuse une archive qui ne s'ouvre pas.

Sans dépendance hors `openpyxl` (lecture des .xlsx) ; `.csv`, `.tsv`, `.txt` et `.docx` en
bibliothèque standard. Cache disque sous le répertoire de sortie.

Exemples :
  python3 supp_tables.py hunt Rv2520c --dois 10.1128/spectrum.02277-24,10.1016/j.mcpro.2026.101555
  python3 supp_tables.py hunt "Rv1908c,katG" --dois-file dois.txt --out /tmp/supp
  python3 supp_tables.py rank /tmp/supp/PMC11792546/table_s2.xlsx --sheet Proteins --col 17 --acc I6XEI0
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

UA = {"User-Agent": "supp-tables/1.0 (recherche academique)"}
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
TABLE_EXT = {".xlsx", ".xls", ".csv", ".tsv", ".txt", ".docx"}


def _get(url: str, timeout: int = 180) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


# --------------------------------------------------------------------- résolution

def resolve(ident: str) -> dict | None:
    """DOI, PMID, PMCID ou titre -> identifiants Europe PMC. Ne devine JAMAIS un PMCID."""
    ident = ident.strip()
    if ident.upper().startswith("PMC"):
        q = f'PMCID:{ident.upper()}'
    elif ident.isdigit():
        q = f"EXT_ID:{ident} AND SRC:MED"
    elif ident.startswith("10."):
        q = f'DOI:"{ident}"'
    else:
        q = f'TITLE:"{ident}"'
    url = f"{EPMC}/search?" + urllib.parse.urlencode(
        {"query": q, "format": "json", "resultType": "core", "pageSize": 1})
    try:
        res = json.loads(_get(url, 60))["resultList"]["result"]
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] résolution impossible pour {ident} ({exc})", file=sys.stderr)
        return None
    if not res:
        return None
    r = res[0]
    return dict(doi=r.get("doi"), pmid=r.get("pmid"), pmcid=r.get("pmcid"),
                title=r.get("title", "")[:120], oa=r.get("isOpenAccess"),
                authors=r.get("authorString", ""),
                journal=r.get("journalTitle"), year=r.get("pubYear"))


def find_preprint(meta: dict) -> str | None:
    """Retrouve le PRÉPRINT d'un article non OA. Repli indispensable, et plus difficile qu'il
    n'y paraît : AUCUNE des routes évidentes ne marche de façon fiable (mesuré 2026-09-08 sur
    Jaisinghani 2024) — la relation `has-preprint` de CrossRef est VIDE, `api.biorxiv.org/pubs/`
    ne connaît pas le DOI publié, et Europe PMC ne relie pas les deux enregistrements.
    Surtout, **le titre change souvent entre préprint et version publiée** (ici « Cell wall
    proteomics in live M. tuberculosis... » devient « Proteomics from compartment-specific APEX2
    labeling... »), donc une recherche par titre rend zéro et paraît concluante.
    La route qui marche : chercher les préprints du PREMIER AUTEUR sur une fenêtre d'années, puis
    confirmer par RECOUVREMENT DES LISTES D'AUTEURS. Une liste d'auteurs, elle, bouge peu."""
    authors = [a.strip() for a in (meta.get("authors") or "").replace(".", "").split(",") if a.strip()]
    if not authors:
        return None
    first = authors[0].split()[0]
    try:
        year = int(meta.get("year") or 0)
    except ValueError:
        return None
    years = " OR ".join(f"PUB_YEAR:{y}" for y in range(year - 3, year + 1))
    url = f"{EPMC}/search?" + urllib.parse.urlencode(
        {"query": f'SRC:PPR AND AUTH:"{first}" AND ({years})',
         "format": "json", "resultType": "core", "pageSize": 25})
    try:
        cands = json.loads(_get(url, 60))["resultList"]["result"]
    except Exception:  # noqa: BLE001
        return None
    ref = {a.split()[0].lower() for a in authors if a}
    best, best_score = None, 0.0
    for c in cands:
        doi = c.get("doi", "") or ""
        if not doi.startswith(("10.1101/", "10.21203/")):
            continue
        got = {a.split()[0].lower() for a in
               (c.get("authorString") or "").replace(".", "").split(",") if a.strip()}
        if not got:
            continue
        score = len(ref & got) / max(len(ref), 1)
        if score > best_score:
            best, best_score = doi, score
    if best and best_score >= 0.5:
        print(f"    preprint apparie par les auteurs (recouvrement {best_score:.0%}) : {best}")
        return best
    return None


# --------------------------------------------------------------------- récupération

def _save_checked(url: str, dest: Path, min_size: int = 2048) -> bool:
    """Télécharge en VÉRIFIANT la taille obtenue : un disque plein rend un fichier tronqué
    sans code d'erreur, piège mesuré le 2026-09-07."""
    data = None
    for attempt in range(4):
        try:
            data = _get(url)
            break
        except Exception as exc:  # noqa: BLE001
            # bioRxiv limite le débit (HTTP 429) dès deux fichiers demandés coup sur coup :
            # sans reprise, on perd silencieusement la moitié des tables d'un article.
            if attempt == 3:
                print(f"    [warn] {url.split('/')[-1]} : {exc}", file=sys.stderr)
                return False
            time.sleep(4 * (attempt + 1))
    if data is None:
        return False
    if len(data) < min_size:
        print(f"    [warn] réponse de {len(data)} octets, ignorée (archive vide ou page d'erreur)",
              file=sys.stderr)
        return False
    dest.write_bytes(data)
    if dest.stat().st_size != len(data):
        print(f"    [ERREUR] écriture tronquée : {dest.stat().st_size} au lieu de {len(data)} "
              f"— système de fichiers plein ?", file=sys.stderr)
        return False
    return True


def fetch_biorxiv(doi: str, outdir: Path) -> int:
    """Repli préprint : la page supplementary-material porte les liens media-<n>."""
    n = 0
    for ver in ("v1", "v2", "v3"):
        try:
            html = _get(f"https://www.biorxiv.org/content/{doi}{ver}.supplementary-material", 90)
        except Exception:  # noqa: BLE001
            continue
        links = re.findall(rb'href="(https://[^"]*?/DC\d+/embed/media-\d+\.[a-z]+[^"]*)"', html)
        for url in dict.fromkeys(links):
            u = url.decode()
            name = u.split("/")[-1].split("?")[0]
            if Path(name).suffix.lower() not in TABLE_EXT | {".pdf"}:
                continue
            if _save_checked(u, outdir / name):
                n += 1
        if n:
            return n
    return n


def fetch(ident: str, outdir: Path) -> Path | None:
    """Récupère les fichiers supplémentaires d'un article. Voie Europe PMC, puis repli préprint."""
    meta = resolve(ident)
    if not meta:
        print(f"  [{ident}] non résolu", file=sys.stderr)
        return None
    tag = meta["pmcid"] or (meta["doi"] or ident).replace("/", "_")
    d = outdir / tag
    d.mkdir(parents=True, exist_ok=True)
    print(f"  [{ident}] {meta['journal']} {meta['year']} · {meta['pmcid'] or 'sans PMCID'} · "
          f"OA={meta['oa']}")
    if any(p.suffix.lower() in TABLE_EXT for p in d.iterdir()):
        print("    déjà en cache")
        return d

    got = 0
    if meta["pmcid"]:
        z = d / "supp.zip"
        if _save_checked(f"{EPMC}/{meta['pmcid']}/supplementaryFiles", z):
            try:
                with zipfile.ZipFile(z) as zf:
                    zf.extractall(d)
                got = sum(1 for p in d.rglob("*") if p.suffix.lower() in TABLE_EXT)
            except zipfile.BadZipFile:
                print("    [warn] archive illisible", file=sys.stderr)
    if not got:
        pre = (meta["doi"] if (meta["doi"] or "").startswith("10.1101/")
               else find_preprint(meta))
        if pre:
            print(f"    repli préprint : {pre}")
            got = fetch_biorxiv(pre, d)
    print(f"    {got} fichier(s) de table récupéré(s)" if got
          else "    aucun fichier récupérable (non OA et sans préprint)")
    return d if got else None


# --------------------------------------------------------------------- fouille

def _scan_xlsx(path: Path, pats: list[str]):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for ws in wb.worksheets:
        header = None
        for i, row in enumerate(ws.iter_rows(values_only=True), 1):
            vals = ["" if v is None else str(v) for v in row]
            if header is None and sum(1 for v in vals if v) >= 2:
                header = vals
            low = " | ".join(vals).lower()
            if any(p in low for p in pats):
                yield ws.title, i, header, vals
    wb.close()


def _scan_text(path: Path, pats: list[str]):
    sep = "\t" if path.suffix.lower() in (".tsv", ".txt") else ","
    lines = path.read_text("utf8", "ignore").splitlines()
    header = lines[0].split(sep) if lines else None
    for i, line in enumerate(lines, 1):
        if any(p in line.lower() for p in pats):
            yield path.stem, i, header, line.split(sep)


def _scan_docx(path: Path, pats: list[str]):
    with zipfile.ZipFile(path) as z:
        txt = z.read("word/document.xml").decode("utf8", "ignore")
    plain = re.sub(r"<[^>]+>", " ", txt).lower()
    for p in pats:
        k = plain.find(p)
        if k >= 0:
            yield "document", 0, None, [" ".join(plain[max(0, k - 250):k + 250].split())]


def grep(root: Path, patterns: list[str], max_hits: int = 200) -> int:
    pats = [p.lower() for p in patterns]
    hits = 0
    for path in sorted(root.rglob("*")):
        ext = path.suffix.lower()
        if ext not in TABLE_EXT:
            continue
        try:
            scan = (_scan_xlsx if ext in (".xlsx", ".xls")
                    else _scan_docx if ext == ".docx" else _scan_text)
            for sheet, i, header, vals in scan(path, pats):
                hits += 1
                if hits > max_hits:
                    print(f"\n[...] plus de {max_hits} occurrences, sortie tronquée")
                    return hits
                rel = path.relative_to(root) if root in path.parents else path.name
                print(f"\n[HIT] {rel} :: feuille '{sheet}' :: ligne {i}")
                if header:
                    print("  en-têtes :", " | ".join(h[:26] for h in header[:14] if h))
                print("  ligne    :", " | ".join(v[:26] for v in vals[:14] if v))
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] {path.name} illisible : {exc}", file=sys.stderr)
    return hits


def sweep(root: Path, groups: dict[str, list[str]], min_hits: int = 1) -> dict:
    """Balaye PLUSIEURS motifs en ne parsant chaque classeur QU'UNE FOIS.

    `grep` rouvre et re-parse chaque fichier pour chaque jeu de motifs, ce qui est acceptable pour
    un gène et intenable pour vingt-quatre : sur trois jeux protéomiques dont un classeur de 47 000
    lignes, cela fait 72 parcours complets là qu'un seul suffit. Mesuré le 2026-09-08 : la version
    naive n'avait pas fini en 15 minutes.

    `groups` : {étiquette (un gène) -> motifs (locus tag, accessions, alias)}.
    Rend {étiquette -> {fichier -> {feuille -> [numéros de ligne]}}}.
    """
    norm = {label: [p.lower() for p in pats] for label, pats in groups.items()}
    out: dict[str, dict] = {label: {} for label in norm}
    for path in sorted(root.rglob("*")):
        ext = path.suffix.lower()
        if ext not in TABLE_EXT:
            continue
        rel = str(path.relative_to(root)) if root in path.parents else path.name
        try:
            if ext in (".xlsx", ".xls"):
                import openpyxl
                wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
                for ws in wb.worksheets:
                    for i, row in enumerate(ws.iter_rows(values_only=True), 1):
                        low = " | ".join("" if v is None else str(v) for v in row).lower()
                        if not low.strip():
                            continue
                        for label, pats in norm.items():
                            if any(p in low for p in pats):
                                out[label].setdefault(rel, {}).setdefault(ws.title, []).append(i)
                wb.close()
            elif ext in (".csv", ".tsv", ".txt"):
                for i, line in enumerate(path.read_text("utf8", "ignore").splitlines(), 1):
                    low = line.lower()
                    for label, pats in norm.items():
                        if any(p in low for p in pats):
                            out[label].setdefault(rel, {}).setdefault(path.stem, []).append(i)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] {path.name} illisible : {exc}", file=sys.stderr)
    return {k: v for k, v in out.items() if sum(len(r) for f in v.values() for r in f.values()) >= min_hits}


def rank(path: Path, sheet: str | None, col: int, needle: str) -> None:
    """LE GARDE-FOU. Où se situe la ligne trouvée dans la distribution de sa propre table ?"""
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb.active
    vals, mine = [], None
    for row in ws.iter_rows(values_only=True):
        cells = ["" if v is None else str(v) for v in row]
        try:
            x = float(cells[col])
        except (ValueError, IndexError):
            continue
        vals.append(x)
        if needle.lower() in " | ".join(cells).lower():
            mine = x
    wb.close()
    if not vals:
        print("colonne non numérique ou vide")
        return
    vals.sort(reverse=True)
    print(f"colonne {col} : n={len(vals)}  médiane={statistics.median(vals):.4g}  "
          f"q1={vals[3*len(vals)//4]:.4g}  q3={vals[len(vals)//4]:.4g}  max={vals[0]:.4g}")
    if mine is None:
        print(f"« {needle} » non trouvé dans cette feuille")
        return
    r = vals.index(mine) + 1
    print(f"« {needle} » = {mine:.4g}  ->  RANG {r}/{len(vals)} "
          f"({100 * r / len(vals):.0f}e centile par le haut)")
    print("\nRappel : un rang n'est pas non plus un résultat. Chercher le SEUIL que les auteurs\n"
          "ont appliqué dans le corps de leur article, et vérifier s'ils retiennent cette ligne.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("hunt", "fetch"):
        s = sub.add_parser(name)
        if name == "hunt":
            s.add_argument("patterns", help="motifs séparés par des virgules (ex. Rv2520c,I6XEI0)")
        s.add_argument("--dois", default="", help="DOI/PMID/PMCID séparés par des virgules")
        s.add_argument("--dois-file", help="fichier, un identifiant par ligne")
        s.add_argument("--out", default="./supp_tables_cache")
    s = sub.add_parser("grep")
    s.add_argument("dir"); s.add_argument("patterns")
    s = sub.add_parser("sweep")
    s.add_argument("dir")
    s.add_argument("--groups", required=True,
                   help="JSON {étiquette: [motifs]} ou chemin d'un fichier JSON")
    s = sub.add_parser("rank")
    s.add_argument("file"); s.add_argument("--sheet"); s.add_argument("--col", type=int, required=True)
    s.add_argument("--needle", required=True)
    a = ap.parse_args()

    if a.cmd == "sweep":
        raw = Path(a.groups).read_text() if Path(a.groups).exists() else a.groups
        res = sweep(Path(a.dir), json.loads(raw))
        for label, files in sorted(res.items()):
            tot = sum(len(r) for f in files.values() for r in f.values())
            print(f"\n{label} : {tot} ligne(s)")
            for f, sheets in files.items():
                for sh, rows in sheets.items():
                    print(f"   {f} :: {sh} :: lignes {rows[:8]}{'...' if len(rows) > 8 else ''}")
        print(f"\n=== {len(res)} étiquette(s) trouvée(s) ===")
        return
    if a.cmd == "rank":
        rank(Path(a.file), a.sheet, a.col, a.needle); return
    if a.cmd == "grep":
        n = grep(Path(a.dir), a.patterns.split(","))
        print(f"\n=== {n} occurrence(s) ==="); return

    idents = [x.strip() for x in a.dois.split(",") if x.strip()]
    if a.dois_file:
        idents += [l.strip() for l in Path(a.dois_file).read_text().splitlines() if l.strip()]
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    print(f"{len(idents)} article(s) -> {out}")
    dirs = [d for d in (fetch(i, out) for i in idents) if d]
    if a.cmd == "fetch":
        print(f"\n=== {len(dirs)} article(s) avec des tables ==="); return
    total = 0
    for d in dirs:
        total += grep(d, a.patterns.split(","))
    print(f"\n=== {total} occurrence(s) pour « {a.patterns} » sur {len(dirs)} article(s) ===")
    if total:
        print("Une ligne trouvée n'est PAS un résultat : passer `rank` sur la colonne numérique,\n"
              "et chercher le seuil appliqué par les auteurs.")


if __name__ == "__main__":
    main()
