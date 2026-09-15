#!/usr/bin/env python3
"""europepmc_fulltext.py — lire le PLEIN TEXTE d'un article open access, sans clé ni quota.

Pourquoi cet outil. Nos vérifications s'arrêtaient à l'abstract (`tbmonitor` indexe des résumés,
les E-utilities des métadonnées), alors qu'un `claim-check` sérieux doit lire les MÉTHODES, et
qu'une piste de recherche se clôt souvent sur la section Data Availability. Europe PMC (EMBL-EBI)
sert les deux gratuitement, sans authentification.

Quatre usages, dans l'ordre où ils servent :

  search    une requête (gène, terme, booléen)       ->  articles dont le PLEIN TEXTE la mentionne
  resolve   un DOI, un PMID, un PMCID ou un titre     ->  identifiants + drapeau open access
  sections  la table des matières du plein texte      ->  où chercher avant de tout lire
  fulltext  le texte, entier ou par section, avec --grep pour n'en tirer que le passage utile

POURQUOI `search`. La recherche par RÉSUMÉ (`tbmonitor`, E-utilities par défaut) rate tout ce qui
n'apparaît que dans le corps : un nom de gène, un locus tag, une méthode vivent dans les Méthodes ou
les Résultats, jamais dans l'abstract. Mesuré le 2026-08-10 : `esxV` renvoie **124 articles en plein
texte contre 19 en résumé seul** (×6,5) ; `ESX-5 AND tuberculosis` 2667 contre 115 (×23). C'est la
cause directe des gènes qui sortaient « sans littérature » alors que des dizaines d'articles OA les
mentionnent. `search` interroge le plein texte par défaut et AFFICHE l'écart résumé/plein texte pour
rendre le manque visible. Sur les 124 `esxV`, 91 ont un plein texte OA récupérable par `fulltext`.

PIÈGE PRINCIPAL, vérifié le 2026-08-10 : `/<PMCID>/fullTextXML` répond **200 avec un AUTRE article**
si le PMCID est faux (PMC8945347 au lieu de PMC8945471 a rendu un article de Biomedicines sans la
moindre erreur). Ne jamais deviner ni recopier un PMCID de mémoire : toujours le résoudre depuis le
DOI. Ce script recoupe systématiquement le DOI du XML reçu avec celui demandé et refuse de rendre un
texte qui ne correspond pas, sauf --force.

Portée : Europe PMC indexe le plein texte pour la RECHERCHE bien au-delà de l'OA, mais ne RÉCUPÈRE le
plein texte que pour l'open access (mesuré : 35 264 articles TB en OA). D'où le partage : `search`
trouve large (corps de tous les articles indexés), `fulltext` ne lit que l'OA (drapeau
`isOpenAccess` / `--oa`). Pour un article non-OA repéré par `search`, passer par la cascade légale
d'accès (Unpaywall, preprint, TDM institutionnel), hors de cet outil. `tbmonitor-papers` reste la
porte d'entrée du RECENSEMENT (il indexe aussi le non-OA en résumé) ; `search` sert le RAPPEL par le
corps du texte. Réflexe associé : MDPI et plusieurs éditeurs renvoient 403 à un fetch direct alors
que la version PMC passe, donc viser Europe PMC avant le site de l'éditeur.

Sans dépendance : bibliothèque standard seule. Réponses mises en cache dans ~/.cache/europepmc/.

Exemples :
  python3 europepmc_fulltext.py search "esxV" --oa --since 2020
  python3 europepmc_fulltext.py search "Rv1363c AND tuberculosis" --grep "Rv1363c" --limit 10
  python3 europepmc_fulltext.py resolve 10.3390/biom12030376
  python3 europepmc_fulltext.py sections 10.3390/biom12030376
  python3 europepmc_fulltext.py fulltext 10.3390/biom12030376 --section "data availability"
  python3 europepmc_fulltext.py fulltext PMC8945471 --grep "iEK1011"
"""
import argparse
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"
CACHE = Path.home() / ".cache" / "europepmc"
UA = "europepmc_fulltext.py (academic literature verification; FEMTO-ST)"
TIMEOUT = 60


def fetch(url):
    """GET avec cache disque. Le contenu d'un article publié ne bouge pas : le cache est sûr."""
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(url.encode()).hexdigest()[:32]
    path = CACHE / key
    if path.exists():
        return path.read_text(encoding="utf-8")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        body = r.read().decode("utf-8", errors="replace")
    path.write_text(body, encoding="utf-8")
    return body


def query_for(ident):
    """Construit la requête Europe PMC selon la forme de l'identifiant fourni."""
    ident = ident.strip()
    if re.fullmatch(r"PMC\d+", ident, re.I):
        # Pas de guillemets : Europe PMC renvoie 0 résultat pour PMCID:"PMCxxxx" (verifie
        # 2026-08-26) alors que PMCID:PMCxxxx (sans guillemets) fonctionne. DOI et EXT_ID
        # tolerent les guillemets, PMCID non.
        return f"PMCID:{ident.upper()}"
    if re.fullmatch(r"\d{6,9}", ident):
        return f'EXT_ID:{ident} AND SRC:MED'
    if ident.lower().startswith("10.") or "doi.org/" in ident.lower():
        doi = ident.split("doi.org/")[-1]
        return f'DOI:"{doi}"'
    return f'TITLE:"{ident}"'


def resolve(ident):
    """Identifiant quelconque -> enregistrement Europe PMC (ou None)."""
    url = (f"{BASE}/search?query={urllib.parse.quote(query_for(ident))}"
           f"&resultType=core&format=json&pageSize=5")
    data = json.loads(fetch(url))
    results = data.get("resultList", {}).get("result", [])
    return results[0] if results else None


def summarize(rec):
    return {
        "title": rec.get("title", "").strip(),
        "doi": rec.get("doi"),
        "pmid": rec.get("pmid"),
        "pmcid": rec.get("pmcid"),
        "journal": (rec.get("journalInfo") or {}).get("journal", {}).get("title"),
        "year": rec.get("pubYear"),
        "authors": rec.get("authorString"),
        "isOpenAccess": rec.get("isOpenAccess"),
        "inEPMC": rec.get("inEPMC"),
        "fullTextAvailable": bool(rec.get("pmcid")) and rec.get("isOpenAccess") == "Y",
    }


def get_xml(rec, force=False):
    """Plein texte JATS d'un enregistrement résolu, avec recoupement du DOI."""
    pmcid = rec.get("pmcid")
    if not pmcid:
        raise SystemExit("pas de PMCID : cet article n'est pas dans PMC "
                         "(non open access, ou hors couverture). Voir tbmonitor-papers "
                         "pour le résumé, ou le site de l'éditeur.")
    if rec.get("isOpenAccess") != "Y" and not force:
        raise SystemExit(f"{pmcid} n'est pas signalé open access : le plein texte sera refusé par "
                         "l'API. Relancer avec --force pour essayer quand même.")
    raw = fetch(f"{BASE}/{pmcid}/fullTextXML")
    if raw.lstrip().startswith("<error") or "<responseWrapper" in raw[:200]:
        raise SystemExit(f"Europe PMC ne sert pas le plein texte de {pmcid}.")
    root = ET.fromstring(raw)
    got = None
    for el in root.iter("article-id"):
        if el.get("pub-id-type") == "doi":
            got = (el.text or "").strip().lower()
            break
    want = (rec.get("doi") or "").strip().lower()
    if want and got and want != got and not force:
        raise SystemExit(
            f"INCOHÉRENCE : le XML de {pmcid} porte le DOI {got}, or on demandait {want}. "
            "C'est le piège du PMCID erroné (l'API répond 200 avec un autre article). "
            "Re-résoudre depuis le DOI, ou --force en connaissance de cause.")
    return root


def clean(text):
    return re.sub(r"[ \t]*\n[ \t]*", "\n", re.sub(r"[ \t]{2,}", " ", text)).strip()


def sections(root):
    """[(niveau, titre, texte)] pour le corps et l'arrière-texte (data availability y vit souvent)."""
    out = []

    def walk(node, level):
        for sec in node.findall("sec"):
            t = sec.find("title")
            title = clean("".join(t.itertext())) if t is not None else "(sans titre)"
            body = []
            for child in sec:
                if child.tag in ("sec", "title"):
                    continue
                body.append("".join(child.itertext()))
            txt = clean("\n".join(body))
            # Certains éditeurs (MDPI notamment) répètent le texte d'une sous-section dans sa
            # parente : sans ce garde, la même déclaration sort deux fois.
            if not any(txt and txt == prev for _, _, prev in out):
                out.append((level, title, txt))
            walk(sec, level + 1)

    for part in ("body", "back"):
        node = root.find(part)
        if node is not None:
            walk(node, 1)
    # Les notices de disponibilité des données vivent souvent hors <sec>. On ne les ajoute que si
    # leur texte n'a pas déjà été capté par une section, sinon l'article sort en double.
    seen = {t for _, _, t in out}
    for tag in ("notes", "fn-group", "ack"):
        for node in root.iter(tag):
            txt = clean("".join(node.itertext()))
            if txt and not any(txt in s or s in txt for s in seen):
                out.append((1, f"({tag})", txt))
                seen.add(txt)
    return out


def abstract(root):
    node = root.find(".//abstract")
    return clean("".join(node.itertext())) if node is not None else ""


# --- search : rappel par le CORPS du texte, pas par le résumé -----------------------------------

SORT_MAP = {"relevance": None, "cited": "CITED desc", "date": "P_PDATE_D desc"}


def hit_count(query):
    """Nombre d'articles pour une requête (une seule requête, pageSize=1)."""
    url = f"{BASE}/search?query={urllib.parse.quote(query)}&format=json&pageSize=1"
    try:
        return json.loads(fetch(url)).get("hitCount", 0)
    except Exception:
        return None


def build_search_query(user_query, oa=False, since=None, until=None):
    """Requête plein texte + filtres. L'utilisateur est mis entre parenthèses pour isoler ses ET/OU."""
    parts = [f"({user_query})"]
    if oa:
        parts.append("(OPEN_ACCESS:Y AND IN_EPMC:Y)")
    if since or until:
        lo = f"{since}-01-01" if since else "1800-01-01"
        hi = f"{until}-12-31" if until else "3000-12-31"
        parts.append(f"(FIRST_PDATE:[{lo} TO {hi}])")
    return " AND ".join(parts)


def paged_search(query, limit, sort="relevance"):
    """Pagination au curseur (cursorMark) jusqu'à `limit` résultats. Renvoie (hitCount, [records])."""
    got, cursor, total = [], "*", None
    sort_val = SORT_MAP.get(sort)
    while len(got) < limit:
        page = min(100, limit - len(got))
        url = (f"{BASE}/search?query={urllib.parse.quote(query)}"
               f"&resultType=core&format=json&pageSize={page}"
               f"&cursorMark={urllib.parse.quote(cursor)}")
        if sort_val:
            url += f"&sort={urllib.parse.quote(sort_val)}"
        data = json.loads(fetch(url))
        if total is None:
            total = data.get("hitCount", 0)
        batch = data.get("resultList", {}).get("result", [])
        got.extend(batch)
        nxt = data.get("nextCursorMark")
        if not batch or not nxt or nxt == cursor:
            break
        cursor = nxt
    return total, got[:limit]


def grep_record(rec, pattern):
    """Phrases du plein texte OA d'un article contenant `pattern`. [] si non-OA ou illisible."""
    if not (rec.get("pmcid") and rec.get("isOpenAccess") == "Y"):
        return None  # plein texte non récupérable : le signaler, ne pas confondre avec 0 occurrence
    try:
        root = get_xml(rec)
    except SystemExit:
        return None
    rx = re.compile(pattern, re.I)
    hits = []
    for _, title, txt in sections(root):
        for sent in re.split(r"(?<=[.!?])\s+", txt):
            if rx.search(sent):
                hits.append((title, sent.strip()))
    return hits


def cmd_search(args):
    query = build_search_query(args.query, oa=args.oa, since=args.since, until=args.until)
    total, recs = paged_search(query, args.limit, sort=args.sort)

    # Diagnostic de rappel : le même terme restreint au RÉSUMÉ (best-effort ; n/a si la requête
    # porte déjà des tags de champ que ABSTRACT: ne peut pas envelopper proprement).
    abs_q = build_search_query(f"ABSTRACT:({args.query})", oa=args.oa, since=args.since, until=args.until)
    abs_count = hit_count(abs_q)

    rows = [summarize(r) for r in recs]
    if args.grep:
        for row, rec in zip(rows, recs):
            row["grep"] = grep_record(rec, args.grep)

    if args.json:
        print(json.dumps({"query": query, "hitCount_fulltext": total,
                          "hitCount_abstract": abs_count, "results": rows},
                         ensure_ascii=False, indent=2))
        return

    gain = (f" (résumé seul : {abs_count} — le plein texte en trouve "
            f"{'×%.1f' % (total / abs_count) if abs_count else 'infiniment'} plus)"
            if abs_count is not None else "")
    print(f"# {total} articles, plein texte ⊇ résumé{gain}")
    print(f"# requête : {query}")
    print(f"# affichés : {len(rows)} (tri : {args.sort})\n")
    for row in rows:
        oa = "OA" if row["fullTextAvailable"] else "  "
        print(f"[{oa}] {row['year']}  {row['doi'] or row['pmid'] or row['pmcid']}"
              f"  {(row['title'] or '')[:90]}")
        if args.grep:
            g = row.get("grep")
            if g is None:
                print("       (plein texte non-OA : non lisible ici, passer par la cascade d'accès)")
            elif not g:
                print(f"       (aucune occurrence de « {args.grep} » dans le corps OA)")
            else:
                for title, sent in g[:args.grep_max]:
                    # Un tableau JATS se replie en une seule « phrase » énorme : on tronque à
                    # l'affichage (le motif y est, l'utilisateur ouvrira le fulltext pour la table).
                    if len(sent) > 320:
                        sent = sent[:300].rstrip() + " […tableau/passage long, cf. fulltext]"
                    print(f"       · [{title}] {sent}")
                if len(g) > args.grep_max:
                    print(f"       … +{len(g) - args.grep_max} autres occurrences")
    if not rows:
        print("(aucun article — élargir la requête, retirer --oa, ou vérifier l'orthographe)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("search", help="chercher un terme dans le CORPS des articles (pas le résumé)")
    ps.add_argument("query", help="terme, gène, locus tag, ou requête booléenne Europe PMC")
    ps.add_argument("--oa", action="store_true", help="ne garder que les articles au plein texte OA récupérable")
    ps.add_argument("--since", type=int, help="année de publication minimale (FIRST_PDATE)")
    ps.add_argument("--until", type=int, help="année de publication maximale")
    ps.add_argument("--limit", type=int, default=25, help="nombre d'articles listés (défaut 25)")
    ps.add_argument("--sort", choices=list(SORT_MAP), default="relevance",
                    help="relevance (défaut), cited (plus cités), date (plus récents)")
    ps.add_argument("--grep", help="extraire du plein texte OA les phrases contenant ce motif (regex)")
    ps.add_argument("--grep-max", type=int, default=5, dest="grep_max",
                    help="max de phrases affichées par article avec --grep (défaut 5)")
    ps.add_argument("--json", action="store_true", help="sortie JSON")

    for name in ("resolve", "sections", "fulltext"):
        p = sub.add_parser(name)
        p.add_argument("ident", help="DOI, PMID, PMCID ou titre exact")
        p.add_argument("--json", action="store_true", help="sortie JSON")
        p.add_argument("--force", action="store_true",
                       help="passer outre le recoupement du DOI et le drapeau open access")
        if name == "fulltext":
            p.add_argument("--section", help="ne rendre que les sections dont le titre contient ceci")
            p.add_argument("--grep", help="ne rendre que les phrases contenant ce motif (regex)")
            p.add_argument("--abstract", action="store_true", help="ajouter le résumé en tête")
    args = ap.parse_args()

    if args.cmd == "search":
        cmd_search(args)
        return

    rec = resolve(args.ident)
    if rec is None:
        raise SystemExit(f"aucun résultat Europe PMC pour « {args.ident} ». "
                         "Vérifier le DOI, ou chercher par titre.")
    info = summarize(rec)

    if args.cmd == "resolve":
        print(json.dumps(info, ensure_ascii=False, indent=2) if args.json else
              "\n".join(f"{k:<20} {v}" for k, v in info.items()))
        return

    root = get_xml(rec, force=args.force)
    secs = sections(root)

    if args.cmd == "sections":
        if args.json:
            print(json.dumps([{"level": l, "title": t, "chars": len(x)} for l, t, x in secs],
                             ensure_ascii=False, indent=2))
        else:
            print(f"{info['title']}\n{info['pmcid']} — {len(secs)} sections\n")
            for level, title, txt in secs:
                print(f"{'  ' * (level - 1)}- {title}  [{len(txt)} car.]")
        return

    keep = secs
    if args.section:
        needle = args.section.lower()
        keep = [s for s in secs if needle in s[1].lower()]
        if not keep:
            print(f"aucune section ne contient « {args.section} ». Titres disponibles :",
                  file=sys.stderr)
            for _, title, _ in secs:
                print(f"  - {title}", file=sys.stderr)
            raise SystemExit(1)

    print(f"# {info['title']}\n# {info['journal']} {info['year']} — "
          f"{info['doi']} — {info['pmcid']}\n")
    if getattr(args, "abstract", False):
        print(f"## Résumé\n{abstract(root)}\n")

    if args.grep:
        rx = re.compile(args.grep, re.I)
        hits = 0
        for _, title, txt in keep:
            for sent in re.split(r"(?<=[.!?])\s+", txt):
                if rx.search(sent):
                    print(f"[{title}] {sent.strip()}")
                    hits += 1
        if not hits:
            print(f"(aucune occurrence de « {args.grep} »)", file=sys.stderr)
            raise SystemExit(1)
        return

    for level, title, txt in keep:
        print(f"\n{'#' * (level + 1)} {title}\n\n{txt}")


if __name__ == "__main__":
    main()
