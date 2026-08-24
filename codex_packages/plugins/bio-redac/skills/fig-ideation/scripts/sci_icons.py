#!/usr/bin/env python3
"""Recuperer une icone scientifique libre et la rendre utilisable dans une figure LaTeX.

Deux sources, choisies parce qu'elles sont libres, vectorielles et citables :

* PhyloPic (~10 000 silhouettes d'organismes, CC0 / CC BY / CC BY-SA) resolues
  par **taxid NCBI** — le meme identifiant qui designe deja l'organisme dans le
  pipeline, donc l'icone est indexee sur la biologie et non sur un mot-cle.
* Bioicons (~2 800 icones de biologie et chimie, CC0 / CC BY / MIT / BSD),
  cherchees par nom et par categorie (Microbiology, Genetics, Genomics, Animals,
  Lab_apparatus...).

Chaine de conversion SANS Inkscape, qui n'est pas installe ici :
    SVG -> (teinte par reecriture du fill) -> rsvg-convert -f pdf -> \\includegraphics

GARDE-FOU DE LICENCE. Une part des silhouettes PhyloPic est en **CC BY-SA**, un
share-alike que plusieurs editeurs refusent parce qu'il contamine la figure, donc
l'article. Le script affiche TOUJOURS la licence, et `--libre` ecarte les SA.
Une icone sans sa ligne d'attribution n'est pas utilisable : le script l'ecrit.

Usage :
    python3 sci_icons.py taxon 9913 --out cattle --tint "#D55E00"
    python3 sci_icons.py taxon 9606 9913 9925 9709 --outdir figures/icons --libre
    python3 sci_icons.py search bacteria --category Microbiology
    python3 sci_icons.py icon Bacillus_subtilis --out bacillus --tint "#0072B2"

Taxids MTBC utiles : 9606 humain, 9913 bovin, 9925 caprin, 9709 phocides,
1773 M. tuberculosis, 1765 M. bovis.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

PHYLOPIC = "https://api.phylopic.org"
BIOICONS_RAW = "https://raw.githubusercontent.com/duerrsimon/bioicons/main/static/icons"
BIOICONS_INDEX = f"{BIOICONS_RAW}/icons.json"
UA = {"User-Agent": "fig-ideation/1.0 (academic research, FEMTO-ST)"}
SHARE_ALIKE = re.compile(r"by-sa|sharealike", re.I)


def fetch(url: str, timeout: int = 40) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_json(url: str) -> dict:
    return json.loads(fetch(url).decode("utf-8"))


# --------------------------------------------------------------------------
# PhyloPic
# --------------------------------------------------------------------------
def phylopic_by_taxid(taxid: int) -> dict | None:
    """Resoudre un taxid NCBI vers sa silhouette primaire.

    L'API repond 307 pour injecter le numero de build : urllib suit la
    redirection, mais un client qui ne la suit pas recevra un corps vide.
    """
    url = (f"{PHYLOPIC}/resolve/ncbi.nlm.nih.gov/taxid/{taxid}"
           "?embed_primaryImage=true")
    try:
        d = fetch_json(url)
    except Exception as exc:
        print(f"  taxid {taxid} : echec API ({exc})", file=sys.stderr)
        return None
    img = (d.get("_embedded") or {}).get("primaryImage")
    if not img:
        print(f"  taxid {taxid} : aucune silhouette primaire", file=sys.stderr)
        return None
    links = img.get("_links", {})
    vec = (links.get("vectorFile") or {}).get("href")
    lic = (links.get("license") or {}).get("href", "")
    contrib = (links.get("contributor") or {}).get("title", "inconnu")
    return {"href": vec, "license": short_license(lic), "license_url": lic,
            "contributor": contrib, "taxid": taxid,
            "title": (links.get("self") or {}).get("title", "")}


def short_license(url: str) -> str:
    if "publicdomain/zero" in url:
        return "CC0 1.0"
    m = re.search(r"/licenses/([a-z-]+)/([\d.]+)", url)
    return f"CC {m.group(1).upper()} {m.group(2)}" if m else (url or "inconnue")


# --------------------------------------------------------------------------
# Bioicons
# --------------------------------------------------------------------------
_index_cache: list[dict] | None = None


def bioicons_index() -> list[dict]:
    global _index_cache
    if _index_cache is None:
        _index_cache = list(json.loads(fetch(BIOICONS_INDEX).decode("utf-8")))
    return _index_cache


def bioicons_url(entry: dict) -> str:
    """Le chemin reel est licence/Categorie/Auteur/Nom.svg — l'index seul ne suffit pas."""
    parts = [entry["license"], entry["category"], entry["author"],
             entry["name"] + ".svg"]
    return BIOICONS_RAW + "/" + "/".join(urllib.parse.quote(p) for p in parts)


def bioicons_search(query: str, category: str | None = None,
                    limit: int = 25) -> list[dict]:
    pat = re.compile(query, re.I)
    out = []
    for e in bioicons_index():
        if category and e.get("category", "").lower() != category.lower():
            continue
        if pat.search(e.get("name", "")) or pat.search(e.get("category", "")):
            out.append(e)
        if len(out) >= limit:
            break
    return out


# --------------------------------------------------------------------------
# Conversion
# --------------------------------------------------------------------------
def tint_svg(svg: bytes, colour: str) -> bytes:
    """Reecrire la couleur de remplissage.

    Une silhouette porte sa propre couleur (`fill="#000000"`) : envelopper le
    \\includegraphics d'un \\textcolor n'a AUCUN effet sur le PDF resultant.
    La teinte se fait donc ici, avant la conversion.
    """
    txt = svg.decode("utf-8", errors="replace")
    txt = re.sub(r'fill="(?!none)[^"]*"', f'fill="{colour}"', txt)
    txt = re.sub(r'fill:\s*(?!none)[^;"\']+', f"fill:{colour}", txt)
    return txt.encode("utf-8")


def svg_to_pdf(svg_path: Path, pdf_path: Path, height: int = 300) -> bool:
    if shutil.which("rsvg-convert") is None:
        print("rsvg-convert absent : installer librsvg2-bin", file=sys.stderr)
        return False
    r = subprocess.run(["rsvg-convert", "-f", "pdf", "-h", str(height),
                        "-o", str(pdf_path), str(svg_path)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"echec rsvg-convert : {r.stderr.strip()[:160]}", file=sys.stderr)
        return False
    # Un PDF portant un objet /Image serait un bitmap encapsule, pas du vectoriel.
    if b"/Image" in pdf_path.read_bytes():
        print(f"  attention : {pdf_path.name} contient un bitmap encapsule",
              file=sys.stderr)
    return True


def grab(href: str, out: Path, tint: str | None, height: int) -> bool:
    try:
        svg = fetch(href)
    except Exception as exc:
        print(f"  telechargement echoue : {exc}", file=sys.stderr)
        return False
    if tint:
        svg = tint_svg(svg, tint)
    svg_path = out.with_suffix(".svg")
    svg_path.write_bytes(svg)
    return svg_to_pdf(svg_path, out.with_suffix(".pdf"), height)


# --------------------------------------------------------------------------
def write_attribution(records: list[dict], path: Path) -> None:
    """Une icone sans attribution n'est pas utilisable : produire la ligne prete."""
    lines = ["% Attribution des icones — a reporter dans la legende ou les remerciements.",
             "% Genere par fig-ideation/scripts/sci_icons.py"]
    for r in records:
        src = "PhyloPic" if "taxid" in r else "Bioicons"
        who = r.get("contributor") or r.get("author", "?")
        ident = f"taxid {r['taxid']}" if "taxid" in r else r.get("name", "")
        lines.append(f"%   {r['file']} : {src}, {ident}, {who}, {r['license']}")
    sa = [r for r in records if SHARE_ALIKE.search(r["license"])]
    if sa:
        lines.append("% ATTENTION licence share-alike (contamine la figure, donc l'article) :")
        for r in sa:
            lines.append(f"%   {r['file']} — {r['license']}. Verifier la politique de la revue.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nattribution ecrite dans {path}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("taxon", help="silhouette PhyloPic par taxid NCBI")
    t.add_argument("taxids", nargs="+", type=int)
    t.add_argument("--out", default=None, help="nom de sortie (un seul taxid)")
    t.add_argument("--outdir", type=Path, default=Path("."))
    t.add_argument("--tint", default=None, help='couleur, ex "#D55E00"')
    t.add_argument("--height", type=int, default=300)
    t.add_argument("--libre", action="store_true",
                   help="refuser les licences share-alike (CC BY-SA)")

    s = sub.add_parser("search", help="chercher une icone Bioicons")
    s.add_argument("query")
    s.add_argument("--category", default=None)
    s.add_argument("--limit", type=int, default=25)

    i = sub.add_parser("icon", help="telecharger une icone Bioicons par nom exact")
    i.add_argument("name")
    i.add_argument("--out", default=None)
    i.add_argument("--outdir", type=Path, default=Path("."))
    i.add_argument("--tint", default=None)
    i.add_argument("--height", type=int, default=300)

    a = ap.parse_args()

    if a.cmd == "search":
        hits = bioicons_search(a.query, a.category, a.limit)
        if not hits:
            print("aucune icone. Categories : Microbiology, Genetics, Genomics, "
                  "Animals, Cell_types, Nucleic_acids, Lab_apparatus, Viruses...")
            return 1
        for e in hits:
            print(f"  {e['category']:<24} {e['name']:<38} {e['license']:<12} {e['author']}")
        print(f"\n{len(hits)} resultat(s). Telecharger : sci_icons.py icon <Nom>")
        return 0

    a.outdir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []

    if a.cmd == "taxon":
        for tx in a.taxids:
            meta = phylopic_by_taxid(tx)
            if not meta or not meta["href"]:
                continue
            if a.libre and SHARE_ALIKE.search(meta["license"]):
                print(f"  taxid {tx} : ECARTE, {meta['license']} (share-alike)")
                continue
            name = a.out if (a.out and len(a.taxids) == 1) else f"taxid{tx}"
            out = a.outdir / name
            if grab(meta["href"], out, a.tint, a.height):
                meta["file"] = out.with_suffix(".pdf").name
                records.append(meta)
                flag = "  <-- SHARE-ALIKE" if SHARE_ALIKE.search(meta["license"]) else ""
                print(f"  {out.with_suffix('.pdf')}  {meta['license']}  "
                      f"{meta['contributor']}{flag}")

    elif a.cmd == "icon":
        hits = [e for e in bioicons_index() if e["name"] == a.name]
        if not hits:
            print(f"icone '{a.name}' introuvable ; essayer : sci_icons.py search {a.name}")
            return 1
        e = hits[0]
        out = a.outdir / (a.out or e["name"])
        if grab(bioicons_url(e), out, a.tint, a.height):
            e = dict(e, file=out.with_suffix(".pdf").name)
            records.append(e)
            print(f"  {out.with_suffix('.pdf')}  {e['license']}  {e['author']}")

    if records:
        write_attribution(records, a.outdir / "ATTRIBUTION_icons.tex")
    return 0 if records else 1


if __name__ == "__main__":
    raise SystemExit(main())
