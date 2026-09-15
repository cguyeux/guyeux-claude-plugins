#!/usr/bin/env python3
"""Situe la vitrine d'un manuscrit dans le corpus reel de la revue visee.

Repond a une seule question : le titre et le resume candidats ressemblent-ils a ce
que cette revue publie, ou detonnent-ils ? La reponse n'est PAS un verdict, c'est une
mesure. Un ecart mesure ici est un point a instruire, jamais une consigne de
reecriture : c'est la simulation de rejet editorial (voir SKILL.md, temps 2) et la
lecture des clauses d'exclusion qui tranchent.

Trois sous-commandes :

    fetch <cle>      recolte les articles des N derniers mois via Europe PMC et les
                     met en cache (le corpus du critere 2 de choix-revue, conserve
                     au lieu d'etre jete)
    profile <cle>    rend la distribution reelle de la revue : longueur et forme des
                     titres, longueur et structuration des resumes, vocabulaire
    situate <cle>    place le titre et le resume candidats dans ces distributions et
                     liste les ecarts

Le cache vit hors du skill, avec le reste des donnees de revues :
`~/.agents/knowledge/journals/corpus/<cle>.json`.

Les heuristiques de forme (titre interrogatif, methode en tete, resume structure)
sont grossieres par construction : elles servent a reperer un ecart FRANC, du genre
un titre interrogatif dans une revue qui n'en publie aucun. Un ecart faible n'est pas
un signal.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import median

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
CACHE = Path.home() / ".agents" / "knowledge" / "journals" / "corpus"
UA = "cadrage-editorial/1.0 (FEMTO-ST; academic use)"

# Termes qui, dans un titre, annoncent la METHODE plutot que l'objet. Le critere 2 de
# choix-revue documente pourquoi ce reperage compte : les revues qui excluent le
# travail sans paillasse le font sur la methode affichee, et un titre qui la met en
# avant offre le motif de rejet sur un plateau.
METHODE = re.compile(
    r"\b(in silico|computational(ly)?|bioinformatic(s|al)?|machine learning|deep learning|"
    r"data[- ]driven|genome[- ]wide|comparative genomic(s)?|phylogenomic(s)?|"
    r"molecular dynamic(s)?|docking|meta[- ]analysis|reanalysis|re-analysis)\b", re.I)

# Verbes qui font d'un titre une AFFIRMATION de resultat plutot qu'une etiquette de
# sujet. Les deux formes existent, mais une revue penche presque toujours d'un cote.
DECLARATIF = re.compile(
    r"\b(is|are|was|were|reveals?|shows?|drives?|suggests?|identifies|defines?|"
    r"explains?|predicts?|confirms?|underlies|contributes?|associates?|"
    r"correlates?|expands?|redefines?)\b", re.I)

STRUCTURE = re.compile(
    r"\b(background|objectives?|introduction|methods?|materials and methods|"
    r"results?|conclusions?|significance|importance)\b\s*[:.]", re.I)

BINOME = re.compile(r"^[A-Z][a-z]{3,}\s+[a-z]{3,}\b")


def unmarkup(text: str) -> str:
    """Retire le balisage des titres et resumes rendus par Europe PMC.

    Indispensable, et decouvert au rodage du 2026-09-09 : 207 des 300 titres de
    Microbial Genomics portent des balises d'italique ECHAPPEES (`&lt;i&gt;`). Sans ce
    nettoyage, chaque entite compte comme un mot (longueurs de titre et de resume
    gonflees), un nom d'espece en italique en tete de titre echappe a la detection de
    binome, et toute recherche lexicale d'une expression a cheval sur une balise rend
    zero par artefact -- « Mycobacterium tuberculosis complex » comptait 0 occurrence
    dans un corpus qui en porte, parce que la balise fermante tombe entre le second et
    le troisieme mot.
    """
    for ent, char in (("&lt;", "<"), ("&gt;", ">"), ("&amp;", "&"),
                      ("&quot;", '"'), ("&apos;", "'"), ("&#x2019;", "'")):
        text = text.replace(ent, char)
    text = re.sub(r"<[^>]{0,40}>", "", text)
    return re.sub(r"\s+", " ", text).strip()


# --------------------------------------------------------------------------
# base de revues
# --------------------------------------------------------------------------

def journal_name(key: str) -> str | None:
    """Nom exact de la revue, lu dans la base partagee (jamais retape de memoire)."""
    scripts = Path(__file__).resolve().parents[2] / "soumission" / "scripts"
    sys.path.insert(0, str(scripts))
    try:
        import journals  # noqa: PLC0415
    except ImportError:
        return None
    row = next((r for r in journals.load() if r.get("key") == key), None)
    return row.get("name") if row else None


# --------------------------------------------------------------------------
# recolte
# --------------------------------------------------------------------------

def fetch_corpus(name: str, months: int, cap: int) -> list[dict]:
    """Recolte titres et resumes des `months` derniers mois d'une revue.

    Europe PMC plutot que PubMed parce qu'il rend les resumes en masse, ce que le
    critere 2 de choix-revue avait deja etabli. La pagination par cursorMark est la
    seule fiable au-dela de 1 000 hits.
    """
    fin = date.today()
    debut = fin - timedelta(days=int(months * 30.44))
    query = (f'(JOURNAL:"{name}") AND (FIRST_PDATE:[{debut:%Y-%m-%d} TO {fin:%Y-%m-%d}])'
             ' AND (SRC:"MED")')
    out: list[dict] = []
    cursor = "*"
    while len(out) < cap:
        params = urllib.parse.urlencode({
            "query": query, "format": "json", "resultType": "core",
            "pageSize": min(100, cap - len(out)), "cursorMark": cursor,
        })
        req = urllib.request.Request(f"{EPMC}?{params}", headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                payload = json.load(r)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise SystemExit(f"Europe PMC injoignable : {exc}") from exc
        rows = payload.get("resultList", {}).get("result", [])
        for row in rows:
            title = (row.get("title") or "").strip().rstrip(".")
            if not title:
                continue
            out.append({
                "pmid": row.get("pmid") or row.get("id"),
                "doi": row.get("doi"),
                "year": row.get("pubYear"),
                "type": (row.get("pubTypeList", {}) or {}).get("pubType") or [],
                "title": unmarkup(title),
                "abstract": unmarkup((row.get("abstractText") or "").strip()),
            })
        nxt = payload.get("nextCursorMark")
        if not rows or not nxt or nxt == cursor:
            break
        cursor = nxt
    return out


def is_research(rec: dict) -> bool:
    """Ecarte editoriaux, errata et lettres : ils faussent toutes les distributions."""
    types = " ".join(t.lower() for t in rec.get("type", []) if isinstance(t, str))
    if re.search(r"editorial|erratum|correction|retract|comment|news|obituary", types):
        return False
    return bool(rec.get("abstract"))


# --------------------------------------------------------------------------
# mesures
# --------------------------------------------------------------------------

def words(text: str) -> int:
    return len([w for w in re.split(r"\s+", text) if re.search(r"[A-Za-z]", w)])


def title_shape(title: str) -> dict:
    return {
        "mots": words(title),
        # Un "?" INTERNE compte : "Homoplasy or artefact? Re-examining..." est un titre
        # interrogatif, et un test sur la seule fin de chaine le manque (releve au rodage
        # du 2026-09-09 sur variant_nucs, ou c'est justement la forme employee).
        "interrogatif": "?" in title,
        "deux_points": ":" in title,
        "binome_en_tete": bool(BINOME.match(title)),
        "methode_affichee": bool(METHODE.search(title)),
        "declaratif": bool(DECLARATIF.search(title)),
    }


def quantiles(vals: list[int]) -> dict:
    if not vals:
        return {}
    s = sorted(vals)
    def q(p: float) -> int:
        return s[min(len(s) - 1, max(0, int(round(p * (len(s) - 1)))))]
    return {"min": s[0], "p10": q(0.10), "median": int(median(s)),
            "p90": q(0.90), "max": s[-1], "n": len(s)}


def percentile_of(val: int, vals: list[int]) -> int:
    if not vals:
        return -1
    return round(100 * sum(1 for v in vals if v <= val) / len(vals))


def profile(records: list[dict], terms: list[str]) -> dict:
    recs = [r for r in records if is_research(r)]
    shapes = [title_shape(r["title"]) for r in recs]
    n = len(recs) or 1
    prof = {
        "n_articles": len(recs),
        "titre_mots": quantiles([s["mots"] for s in shapes]),
        "resume_mots": quantiles([words(r["abstract"]) for r in recs]),
        "part_interrogatifs": round(100 * sum(s["interrogatif"] for s in shapes) / n),
        "part_deux_points": round(100 * sum(s["deux_points"] for s in shapes) / n),
        "part_binome_en_tete": round(100 * sum(s["binome_en_tete"] for s in shapes) / n),
        "part_methode_affichee": round(100 * sum(s["methode_affichee"] for s in shapes) / n),
        "part_declaratifs": round(100 * sum(s["declaratif"] for s in shapes) / n),
        "part_resumes_structures": round(
            100 * sum(bool(STRUCTURE.search(r["abstract"])) for r in recs) / n),
    }
    if terms:
        blob = " ".join(f"{r['title']} {r['abstract']}" for r in recs).lower()
        prof["vocabulaire"] = {t: blob.count(t.lower()) for t in terms}
    return prof


def cache_path(key: str) -> Path:
    return CACHE / f"{key}.json"


def load_cache(key: str) -> dict:
    f = cache_path(key)
    if not f.exists():
        raise SystemExit(f"aucun corpus en cache pour {key} : lancer d'abord "
                         f"`corpus_fit.py fetch {key}`")
    cache = json.loads(f.read_text(encoding="utf-8"))
    # Nettoyage aussi a la LECTURE, et pas seulement a la recolte : les caches ecrits
    # avant l'ajout d'`unmarkup` portent encore leur balisage, et une mesure fausse est
    # pire qu'une mesure absente.
    for rec in cache.get("records", []):
        rec["title"] = unmarkup(rec.get("title", ""))
        rec["abstract"] = unmarkup(rec.get("abstract", ""))
    return cache


# --------------------------------------------------------------------------
# extraction de la vitrine du manuscrit
# --------------------------------------------------------------------------

def vitrine_from_tex(tex_path: Path) -> tuple[str, str]:
    """Titre et resume tels que l'editeur les lira, extraits du LaTeX.

    Volontairement independant de preflight.py : ce script doit tourner meme si le
    skill soumission n'est pas installe a cote.
    """
    raw = tex_path.read_text(encoding="utf-8", errors="replace")
    raw = "\n".join(re.sub(r"(?<!\\)%.*$", "", line) for line in raw.splitlines())
    mt = re.search(r"\\title\s*\{(.+?)\}\s*(?:\n|\\)", raw, flags=re.S)
    title = mt.group(1) if mt else ""
    ma = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", raw, flags=re.S)
    if not ma:
        ma = re.search(r"\\abstract\s*\{(.*?)\n\s*\}\s*\n", raw, flags=re.S)
    abstract = ma.group(1) if ma else ""
    return clean_tex(title), clean_tex(abstract)


def clean_tex(text: str) -> str:
    text = re.sub(r"\\(cite|ref|label)\w*\s*(\[[^\]]*\])?\{[^}]*\}", " ", text)
    text = re.sub(r"\\(emph|textit|textbf|texttt|textsc)\s*\{([^{}]*)\}", r"\2", text)
    text = re.sub(r"\\[a-zA-Z@]+\*?", " ", text)
    text = re.sub(r"[{}$&~^_\\]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# --------------------------------------------------------------------------
# situer
# --------------------------------------------------------------------------

def situate(cache: dict, title: str, abstract: str, terms: list[str]) -> list[str]:
    recs = [r for r in cache["records"] if is_research(r)]
    if not recs:
        return ["corpus vide apres filtrage : aucune mesure possible"]
    shapes = [title_shape(r["title"]) for r in recs]
    n = len(recs)
    prof = profile(cache["records"], terms)
    cand = title_shape(title)
    ecarts: list[str] = []

    tl = [s["mots"] for s in shapes]
    pc = percentile_of(cand["mots"], tl)
    if pc <= 5 or pc >= 95:
        ecarts.append(f"longueur du titre atypique : {cand['mots']} mots, percentile "
                      f"{pc} (revue : median {prof['titre_mots']['median']}, "
                      f"p10-p90 {prof['titre_mots']['p10']}-{prof['titre_mots']['p90']})")

    if abstract:
        al = [words(r["abstract"]) for r in recs]
        pa = percentile_of(words(abstract), al)
        if pa <= 5 or pa >= 95:
            ecarts.append(f"longueur du resume atypique : {words(abstract)} mots, "
                          f"percentile {pa} (revue : median "
                          f"{prof['resume_mots']['median']}, p10-p90 "
                          f"{prof['resume_mots']['p10']}-{prof['resume_mots']['p90']})")
        struct = bool(STRUCTURE.search(abstract))
        part = prof["part_resumes_structures"]
        if struct and part < 20:
            ecarts.append(f"resume structure (Background/Methods/Results) alors que "
                          f"{part} % seulement le sont dans la revue")
        if not struct and part > 80:
            ecarts.append(f"resume non structure alors que {part} % le sont dans la "
                          "revue : verifier si le gabarit l'impose")

    for cle, libelle, seuil in (
            ("interrogatif", "titre interrogatif", "part_interrogatifs"),
            ("methode_affichee", "methode affichee dans le titre", "part_methode_affichee"),
            ("binome_en_tete", "nom d'espece en tete de titre", "part_binome_en_tete"),
    ):
        part = prof[seuil]
        if cand[cle] and part <= 5:
            ecarts.append(f"{libelle} : {part} % du corpus le fait "
                          f"({round(part * n / 100)} article(s) sur {n})")

    if cand["declaratif"] and prof["part_declaratifs"] <= 20:
        ecarts.append(f"titre affirmant un resultat alors que {prof['part_declaratifs']} % "
                      "des titres de la revue le font (elle nomme plutot le sujet)")
    if not cand["declaratif"] and prof["part_declaratifs"] >= 70:
        ecarts.append(f"titre en etiquette de sujet alors que {prof['part_declaratifs']} % "
                      "des titres de la revue affirment un resultat")

    if terms:
        low_title, low_abs = title.lower(), abstract.lower()
        for term, count in (prof.get("vocabulaire") or {}).items():
            if count:
                continue
            t = term.lower()
            if t in low_title:
                ecarts.append(f"« {term} » est dans le TITRE candidat et n'apparait dans "
                              f"aucun des {n} articles du corpus : soit la revue ne publie "
                              "pas sur cet objet (mauvaise cible), soit elle le nomme "
                              "autrement (verifier ses variantes avant de rien changer)")
            elif t in low_abs:
                ecarts.append(f"« {term} » est dans le resume candidat et absent des {n} "
                              "articles du corpus")
    return ecarts


# --------------------------------------------------------------------------
# sortie
# --------------------------------------------------------------------------

def print_profile(cache: dict, prof: dict) -> None:
    print(f"Revue   : {cache['journal_name']} ({cache['key']})")
    print(f"Fenetre : {cache['window']}, recolte le {cache['fetched']}")
    print(f"Corpus  : {prof['n_articles']} articles de recherche avec resume "
          f"(sur {len(cache['records'])} references recoltees)")
    print()
    tm, rm = prof["titre_mots"], prof["resume_mots"]
    print(f"Titres  : {tm['median']} mots median, p10-p90 {tm['p10']}-{tm['p90']}, "
          f"etendue {tm['min']}-{tm['max']}")
    print(f"          interrogatifs {prof['part_interrogatifs']} %, "
          f"deux-points {prof['part_deux_points']} %, "
          f"espece en tete {prof['part_binome_en_tete']} %")
    print(f"          methode affichee {prof['part_methode_affichee']} %, "
          f"affirmant un resultat {prof['part_declaratifs']} %")
    print(f"Resumes : {rm['median']} mots median, p10-p90 {rm['p10']}-{rm['p90']} ; "
          f"structures {prof['part_resumes_structures']} %")
    if prof.get("vocabulaire"):
        print("Lexique : " + ", ".join(f"{t} × {c}" for t, c in prof["vocabulaire"].items()))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="recolter et mettre en cache le corpus recent")
    f.add_argument("key")
    f.add_argument("--journal-name", help="nom exact si la base ne connait pas la cle")
    f.add_argument("--months", type=int, default=12)
    f.add_argument("--max", type=int, default=400, dest="cap")

    pr = sub.add_parser("profile", help="distribution reelle de la revue")
    pr.add_argument("key")
    pr.add_argument("--terms", default="", help="termes de vocabulaire a compter, "
                                               "separes par des virgules")

    st = sub.add_parser("situate", help="placer la vitrine candidate dans le corpus")
    st.add_argument("key")
    st.add_argument("--tex", help="chemin du main.tex (titre et resume en sont extraits)")
    st.add_argument("--title", help="titre candidat, si pas de --tex")
    st.add_argument("--abstract-file", help="fichier texte du resume candidat")
    st.add_argument("--terms", default="")

    a = p.parse_args()

    if a.cmd == "fetch":
        name = a.journal_name or journal_name(a.key)
        if not name:
            print(f"cle {a.key} inconnue de la base : passer --journal-name",
                  file=sys.stderr)
            return 1
        records = fetch_corpus(name, a.months, a.cap)
        CACHE.mkdir(parents=True, exist_ok=True)
        fin = date.today()
        debut = fin - timedelta(days=int(a.months * 30.44))
        cache_path(a.key).write_text(json.dumps({
            "key": a.key, "journal_name": name,
            "window": f"{debut:%Y-%m-%d} a {fin:%Y-%m-%d}",
            "fetched": f"{datetime.now():%Y-%m-%d}",
            "records": records,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        kept = sum(1 for r in records if is_research(r))
        print(f"{len(records)} references recoltees pour {name}, {kept} exploitables "
              f"→ {cache_path(a.key)}")
        if kept < 20:
            print("ATTENTION : corpus trop maigre pour une distribution (< 20). "
                  "Verifier le nom exact de la revue, ou elargir --months.")
        return 0

    terms = [t.strip() for t in getattr(a, "terms", "").split(",") if t.strip()]
    cache = load_cache(a.key)

    if a.cmd == "profile":
        print_profile(cache, profile(cache["records"], terms))
        return 0

    if a.tex:
        title, abstract = vitrine_from_tex(Path(a.tex))
    else:
        title = a.title or ""
        abstract = (Path(a.abstract_file).read_text(encoding="utf-8")
                    if a.abstract_file else "")
    if not title:
        print("aucun titre candidat : passer --tex ou --title", file=sys.stderr)
        return 1

    prof = profile(cache["records"], terms)
    print_profile(cache, prof)
    print()
    print(f"Candidat : « {title} »")
    print(f"           titre {words(title)} mots, resume {words(abstract)} mots")
    print()
    ecarts = situate(cache, title, abstract, terms)
    if not ecarts:
        print("Aucun ecart franc de forme. La forme ne prouve rien sur le fond : "
              "passer a la simulation de rejet editorial.")
        return 0
    print(f"{len(ecarts)} ecart(s) a instruire, non a corriger d'office :")
    for e in ecarts:
        print(f"  - {e}")
    print()
    print("Un ecart peut etre delibere et juste. Ce qui le tranche est la simulation "
          "de rejet editorial et les clauses d'exclusion, jamais ce tableau.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
