#!/usr/bin/env python3
"""access_cascade.py — trouver la meilleure voie LÉGALE d'accès au plein texte d'un article.

Donné un DOI (ou PMID/PMCID/titre), interroge en cascade les sources d'accès ouvert et rend une
liste ORDONNÉE de voies légales, de la plus directe (lisible ici même) à la plus indirecte (URL de
PDF à récupérer), et à défaut un substitut (résumé enrichi / TLDR) plutôt que rien.

Ce que ce script fait, et ce qu'il NE fait PAS :
  - il TROUVE des accès légaux et ouverts (Europe PMC OA, Unpaywall green/gold OA, OpenAlex,
    Semantic Scholar) ; il ne contourne AUCUN paywall.
  - il ne télécharge pas les PDF d'éditeurs : il rend l'URL légale, à charge de l'humain (accès
    institutionnel sous licence) ou d'un fetch autorisé de la suivre.
  - pour le plein texte réellement lisible et grep-able, la voie de référence reste
    `europepmc_fulltext.py` (Europe PMC OA JATS) ; ce script sert à SAVOIR quelle voie existe.

Cascade des voies (rang = priorité) :
  1. europepmc_oa   plein texte JATS lisible/grep-able ICI (via europepmc_fulltext.py)     [le meilleur]
  2. hal            dépôt HAL green OA (souvent le manuscrit auteur ; fourni pour FEMTO-ST/uFC) + PDF
  2. unpaywall      meilleure localisation OA légale (manuscrit auteur green, ou gold) + URL PDF
  3. openalex       statut OA + oa_url (recoupe Unpaywall, parfois une source de plus)
  4. semanticscholar openAccessPdf + TLDR (résumé généré) = SUBSTITUT quand pas de plein texte
  0. (aucune)       -> émet le HAND-OFF : cascade légale hors-OA (TDM institutionnel, biblio, auteur)

Aucune clé requise pour ces quatre sources. E-mail de politesse (Unpaywall/OpenAlex l'exigent) :
variable d'environnement UNPAYWALL_EMAIL, défaut ci-dessous. Cache disque ~/.cache/litaccess/.

Exemples :
  python3 access_cascade.py 10.1016/S0140-6736(15)00151-8      # un Lancet "payant" -> copie PMC OA
  python3 access_cascade.py 10.1038/s41467-024-45058-9 --json
"""
import argparse
import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

CACHE = Path.home() / ".cache" / "litaccess"
EMAIL = os.environ.get("UNPAYWALL_EMAIL", "christophe.guyeux@univ-fcomte.fr")
UA = f"access_cascade.py (academic OA access; FEMTO-ST; {EMAIL})"
TIMEOUT = 45


def fetch(url):
    """GET avec cache disque et User-Agent. Renvoie le corps, ou None sur échec réseau/HTTP."""
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(url.encode()).hexdigest()[:32]
    path = CACHE / key
    if path.exists():
        return path.read_text(encoding="utf-8")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read().decode("utf-8", errors="replace")
    except Exception:
        return None
    path.write_text(body, encoding="utf-8")
    return body


def norm_doi(ident):
    """Extrait un DOI nu de plusieurs formes ; None si l'entrée n'est pas un DOI."""
    ident = ident.strip()
    if "doi.org/" in ident.lower():
        ident = ident.split("doi.org/")[-1]
    return ident if ident.lower().startswith("10.") else None


def resolve_doi(ident):
    """Identifiant quelconque -> DOI, via Europe PMC si ce n'est pas déjà un DOI. None sinon."""
    doi = norm_doi(ident)
    if doi:
        return doi
    if re.fullmatch(r"PMC\d+", ident, re.I):
        q = f'PMCID:"{ident.upper()}"'
    elif re.fullmatch(r"\d{6,9}", ident):
        q = f"EXT_ID:{ident} AND SRC:MED"
    else:
        q = f'TITLE:"{ident}"'
    url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
           f"query={urllib.parse.quote(q)}&resultType=core&format=json&pageSize=1")
    body = fetch(url)
    if not body:
        return None
    try:
        res = json.loads(body).get("resultList", {}).get("result", [])
        return res[0].get("doi") if res else None
    except Exception:
        return None


def via_europepmc(doi):
    url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
           f"query={urllib.parse.quote(f'DOI:\"{doi}\"')}&resultType=core&format=json&pageSize=1")
    body = fetch(url)
    if not body:
        return None
    try:
        res = json.loads(body).get("resultList", {}).get("result", [])
    except Exception:
        return None
    if not res:
        return None
    rec = res[0]
    if rec.get("pmcid") and rec.get("isOpenAccess") == "Y":
        return {"source": "europepmc_oa", "rank": 1, "readable_here": True,
                "pmcid": rec["pmcid"],
                "note": "plein texte JATS lisible/grep-able via europepmc_fulltext.py",
                "url": f"https://europepmc.org/article/PMC/{rec['pmcid']}"}
    return None


def via_hal(doi):
    """HAL (archives-ouvertes.fr) : dépôt OA institutionnel français, souvent le manuscrit auteur.
    API publique documentée, sans clé. Particulièrement fourni pour FEMTO-ST / uFC."""
    url = ("https://api.archives-ouvertes.fr/search/?"
           f'q=doiId_s:"{urllib.parse.quote(doi)}"'
           "&fl=title_s,fileMain_s,uri_s,openAccess_bool&wt=json&rows=1")
    body = fetch(url)
    if not body:
        return None
    try:
        docs = json.loads(body).get("response", {}).get("docs", [])
    except Exception:
        return None
    if not docs:
        return None
    d = docs[0]
    pdf = d.get("fileMain_s")
    if not pdf:  # notice HAL sans plein texte déposé : pas une voie d'accès
        return None
    return {"source": "hal", "rank": 2, "readable_here": False,
            "url": pdf, "notice": d.get("uri_s"),
            "note": "dépôt HAL (green OA, souvent manuscrit auteur) — PDF direct"}


def via_unpaywall(doi):
    body = fetch(f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={EMAIL}")
    if not body:
        return None
    try:
        d = json.loads(body)
    except Exception:
        return None
    if not d.get("is_oa"):
        return None
    loc = d.get("best_oa_location") or {}
    return {"source": "unpaywall", "rank": 2, "readable_here": False,
            "url": loc.get("url_for_pdf") or loc.get("url"),
            "host_type": loc.get("host_type"), "version": loc.get("version"),
            "n_oa_locations": len(d.get("oa_locations") or []),
            "note": f"OA {loc.get('host_type')}/{loc.get('version')} — URL légale à récupérer"}


def via_openalex(doi):
    body = fetch(f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}?mailto={EMAIL}")
    if not body:
        return None
    try:
        d = json.loads(body)
    except Exception:
        return None
    oa = d.get("open_access") or {}
    if not oa.get("oa_url"):
        return None
    return {"source": "openalex", "rank": 3, "readable_here": False,
            "url": oa.get("oa_url"), "oa_status": oa.get("oa_status"),
            "note": f"OA {oa.get('oa_status')} — recoupe/complète Unpaywall"}


def via_semanticscholar(doi):
    body = fetch("https://api.semanticscholar.org/graph/v1/paper/"
                 f"DOI:{urllib.parse.quote(doi)}?fields=title,tldr,openAccessPdf,citationCount")
    if not body:
        return None
    try:
        d = json.loads(body)
    except Exception:
        return None
    pdf = (d.get("openAccessPdf") or {}).get("url")
    tldr = (d.get("tldr") or {}).get("text")
    if not pdf and not tldr:
        return None
    out = {"source": "semanticscholar", "rank": 4, "readable_here": False,
           "citationCount": d.get("citationCount")}
    if pdf:
        out["url"] = pdf
        out["note"] = "openAccessPdf Semantic Scholar"
    if tldr:
        out["tldr"] = tldr
        out.setdefault("note", "TLDR seul (SUBSTITUT de plein texte, pas une preuve)")
    return out


HANDOFF = """\
Aucune voie OA trouvée. Cascade LÉGALE hors-OA, dans l'ordre :
  1. Résolveur BU (Ariane / Primo VE, Université Marie et Louis Pasteur). Construire le lien
     OpenURL et l'ouvrir dans un navigateur AUTHENTIFIÉ (geste humain, sous licence) :
       https://ariane.umlp.fr/discovery/openurl?institution=33UBFC_INST&vid=33UBFC_INST:openview&rft.doi=<DOI>
     Il pointe la copie sous licence de l'abonnement. Déposer ensuite le PDF dans le dossier
     d'ingestion (cf. SKILL.md « dernier kilomètre ») pour le rendre lisible ici.
  2. TDM institutionnel — si une clé API de fouille de texte (Elsevier insttoken, Springer,
     Wiley) est configurée pour ce compte : voie automatisable et LÉGALE (droit TDM inclus dans
     l'abonnement UMLP). À demander au pôle numérique du SCD (pole-numerique-scd@univ-fcomte.fr),
     ce n'est pas un MCP mais une clé.
  3. Preprint — chercher une version bioRxiv/medRxiv/arXiv (souvent identique sur le fond).
  4. Contact auteur — l'auteur correspondant a le droit d'envoyer son propre article.
"""


def cascade(ident):
    doi = resolve_doi(ident)
    if not doi:
        return {"input": ident, "doi": None, "routes": [],
                "message": "DOI non résolu (titre trop ambigu ?) — fournir le DOI."}
    routes = []
    for fn in (via_europepmc, via_hal, via_unpaywall, via_openalex, via_semanticscholar):
        r = fn(doi)
        if r:
            routes.append(r)
    routes.sort(key=lambda r: r["rank"])
    return {"input": ident, "doi": doi, "routes": routes}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ident", help="DOI (idéal), ou PMID / PMCID / titre exact")
    ap.add_argument("--json", action="store_true", help="sortie JSON")
    args = ap.parse_args()

    res = cascade(args.ident)
    if args.json:
        if not res["routes"]:
            res["handoff"] = HANDOFF
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    if not res["doi"]:
        print(res.get("message"))
        raise SystemExit(1)
    print(f"# DOI {res['doi']}")
    if not res["routes"]:
        print("# aucune voie OA légale trouvée.\n")
        print(HANDOFF)
        return
    best = res["routes"][0]
    readable = " ← LISIBLE ICI (europepmc_fulltext.py)" if best.get("readable_here") else ""
    print(f"# {len(res['routes'])} voie(s) légale(s), meilleure = {best['source']}{readable}\n")
    for r in res["routes"]:
        head = f"[{r['rank']}] {r['source']}"
        print(f"{head:<22} {r.get('note','')}")
        if r.get("url"):
            print(f"{'':<22} {r['url']}")
        if r.get("tldr"):
            print(f"{'':<22} TLDR: {r['tldr']}")
    if not any(r.get("readable_here") for r in res["routes"]):
        print("\n(aucune voie n'est lisible directement ici : suivre une URL sous accès autorisé, "
              "ou déposer le PDF dans le dossier d'ingestion — cf. SKILL.md.)")


if __name__ == "__main__":
    main()
