#!/usr/bin/env python3
"""Auto-citations d'un manuscrit : taux courant, manques probables, candidats classes.

Sert la Phase 6 de /bib-check. Repond a deux questions symetriques, et la seconde
compte autant que la premiere :

  1. SUR-citation -- combien d'auto-citations le manuscrit porte-t-il deja, et
     quelle part des references ? Un editeur regarde ce ratio.
  2. SOUS-citation -- quels travaux anterieurs de l'equipe portent sur ce que le
     manuscrit affirme, et ne sont PAS cites ? C'est le defaut le plus frequent
     quand la .bib a ete construite depuis la litterature externe : la provenance
     des donnees, du pipeline ou de la nomenclature devient introuvable pour le
     lecteur, alors meme qu'elle est publiee.

Le script CLASSE des candidats, il ne decide rien. Le tri se fait par le test du
tiers (« citerais-je ce papier ici s'il etait de quelqu'un d'autre ? »), qui n'est
pas mecanisable : voir la Phase 6 du SKILL.md.

Corpus par defaut : ~/docs/cv/references/{journals,conferences}.bib (entrees avec
resume, ce qui rend l'appariement thematique possible au-dela des titres).

Usage :
    python3 self_citation.py article/main.tex
    python3 self_citation.py article/main.tex --coauthor Sola --top 15
    python3 self_citation.py article/main.tex --emit mgs26:ij     # BibTeX pret a coller
    python3 self_citation.py article/main.tex --json
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

DEFAULT_CORPUS = [
    Path.home() / "docs/cv/references/journals.bib",
    Path.home() / "docs/cv/references/conferences.bib",
]
DEFAULT_AUTHOR = "Guyeux"

# Mots vides EN/FR + vocabulaire generique de la redaction scientifique. L'IDF
# ecarte deja ce qui est present partout dans le corpus ; cette liste evite qu'un
# terme frequent MAIS absent de la plupart des resumes (« manuscript », « herein »)
# ne fasse remonter un candidat sans rapport.
STOP = set("""
a an the of in on at to for with without by from as is are was were be been being
this that these those it its their our we us they he she his her which who whom
and or but not no nor if then than so such both each other more most many much
some any all can could may might must shall should will would do does did done
using used use based new novel study studies work works paper article manuscript
here herein results result show shows shown showed demonstrate present presented
approach method methods analysis analyses data dataset datasets model models
propose proposed proposes provide provides provided obtain obtained between among
however therefore thus also within during over under after before while when where
one two three first second third also several various different same
le la les des du de un une et ou dans pour par sur avec sans nous notre nos leur
est sont ete etre cette ces qui que dont plus moins tres entre lors afin ainsi
nouveau nouvelle etude etudes travail travaux article resultats resultat methode
methodes analyse analyses donnees modele modeles propose proposons montre montrons
""".split())

TOKEN = re.compile(r"[a-z][a-z0-9]*(?:[.\-][a-z0-9]+)*|[a-z]?\d+(?:\.\d+)+[a-z]*")


# ------------------------------- utilitaires ------------------------------------

def deaccent(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def tokens(text: str) -> list[str]:
    t = deaccent(text.lower())
    t = re.sub(r"\\[a-zA-Z]+\*?", " ", t)
    t = re.sub(r"[{}$\\]", " ", t)
    return [w for w in TOKEN.findall(t) if w not in STOP and len(w) > 2]


def match_brace(s: str, open_idx: int) -> int:
    depth, i = 0, open_idx
    while i < len(s):
        c = s[i]
        if c == "\\":
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def parse_bib(text: str) -> list[dict]:
    """Parseur BibTeX suffisant et sans dependance. Accolades comptees en profondeur
    (une regex `\\{[^}]*\\}` tronque au premier `}` interne : meme piege que
    doi_coherence.py et crossref_verify.py)."""
    out: list[dict] = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        kind, key = m.group(1).lower(), m.group(2)
        if kind in ("comment", "preamble", "string"):
            continue
        end = match_brace(text, text.index("{", m.start()))
        body = text[m.end(): end if end > 0 else len(text)]
        entry = {"_type": kind, "_key": key, "_raw": text[m.start(): (end + 1) if end > 0 else len(text)]}
        pos = 0
        while True:
            fm = re.compile(r"(\w+)\s*=\s*").search(body, pos)
            if not fm:
                break
            j = fm.end()
            if j < len(body) and body[j] == "{":
                k = match_brace(body, j)
                if k < 0:
                    break
                val, pos = body[j + 1: k], k + 1
            elif j < len(body) and body[j] == '"':
                k = body.find('"', j + 1)
                val, pos = body[j + 1: k if k > 0 else len(body)], (k + 1 if k > 0 else len(body))
            else:
                k = body.find(",", j)
                val, pos = body[j: k if k > 0 else len(body)], (k + 1 if k > 0 else len(body))
            entry[fm.group(1).lower()] = re.sub(r"\s+", " ", val).strip()
        out.append(entry)
    return out


def surnames(author_field: str) -> list[str]:
    """Noms de famille d'un champ `author`, quel que soit le format BibTeX."""
    names = []
    for chunk in re.split(r"\s+and\s+", author_field or ""):
        chunk = chunk.strip().strip("{}")
        if not chunk:
            continue
        names.append(deaccent(chunk.split(",")[0] if "," in chunk else chunk.split()[-1]).lower())
    return names


def norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", deaccent((t or "").lower()))


def norm_doi(d: str) -> str:
    d = (d or "").strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return d.rstrip(".")


# ------------------------------- manuscrit --------------------------------------

def resolve_inputs(path: Path, seen: set[Path] | None = None, depth: int = 0) -> str:
    seen = seen if seen is not None else set()
    path = path.resolve()
    if path in seen or depth > 6 or not path.exists():
        return ""
    seen.add(path)
    text = path.read_text(encoding="utf-8", errors="replace")

    def sub(m: re.Match) -> str:
        cand = path.parent / m.group(2).strip()
        for c in (cand, Path(str(cand) + ".tex")):
            if c.is_file():
                return "\n" + resolve_inputs(c, seen, depth + 1) + "\n"
        return ""

    return re.sub(r"\\(input|include)\{([^}]*)\}", sub, text)


def find_bib(tex: str, tex_path: Path) -> Path | None:
    m = re.search(r"\\(?:bibliography|addbibresource)\{([^}]*)\}", tex)
    if not m:
        cand = list(tex_path.parent.glob("*.bib"))
        return cand[0] if len(cand) == 1 else None
    for name in m.group(1).split(","):
        p = tex_path.parent / name.strip()
        for c in (p, Path(str(p) + ".bib")):
            if c.is_file():
                return c
    return None


# ------------------------------- appariement ------------------------------------

def build_index(corpus: list[dict]) -> tuple[dict[str, float], list[Counter]]:
    docs = [Counter(tokens(" ".join(filter(None, [
        e.get("title", ""), e.get("abstract", ""), e.get("keywords", ""),
        e.get("journal", ""), e.get("booktitle", "")]))))
        for e in corpus]
    df: Counter = Counter()
    for d in docs:
        df.update(d.keys())
    n = max(len(docs), 1)
    idf = {t: math.log(1 + n / (1 + c)) for t, c in df.items()}
    return idf, docs


def cosine(q: Counter, d: Counter, idf: dict[str, float]) -> tuple[float, list[str]]:
    if not d:
        return 0.0, []
    contrib = {t: (1 + math.log(q[t])) * (1 + math.log(d[t])) * idf.get(t, 0.0) ** 2
               for t in set(q) & set(d)}
    num = sum(contrib.values())
    if num <= 0:
        return 0.0, []
    nq = math.sqrt(sum(((1 + math.log(v)) * idf.get(t, 0.0)) ** 2 for t, v in q.items()))
    nd = math.sqrt(sum(((1 + math.log(v)) * idf.get(t, 0.0)) ** 2 for t, v in d.items()))
    score = num / (nq * nd) if nq and nd else 0.0
    top = [t for t, _ in sorted(contrib.items(), key=lambda kv: -kv[1])[:8]]
    return score, top


# ---------------------------------- rapport -------------------------------------

def run(tex_path: Path, corpus_paths: list[Path], author: str, coauthor: str | None,
        top: int) -> dict:
    tex = resolve_inputs(tex_path)
    bib_path = find_bib(tex, tex_path)
    manuscript_bib = parse_bib(bib_path.read_text(encoding="utf-8", errors="replace")) \
        if bib_path and bib_path.is_file() else []

    corpus: list[dict] = []
    missing: list[str] = []
    for p in corpus_paths:
        if p.is_file():
            for e in parse_bib(p.read_text(encoding="utf-8", errors="replace")):
                if e.get("title") and e.get("author"):
                    e["_source"] = str(p)
                    corpus.append(e)
        else:
            missing.append(str(p))

    a_low = deaccent(author).lower()
    cited_keys = set(re.findall(r"\\(?:no)?cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}", tex))
    cited_keys = {k.strip() for grp in cited_keys for k in grp.split(",") if k.strip()}

    used = [e for e in manuscript_bib if e["_key"] in cited_keys] or manuscript_bib
    self_cited = [e for e in used if a_low in surnames(e.get("author", ""))]

    seen_doi = {norm_doi(e.get("doi", "")) for e in manuscript_bib if e.get("doi")}
    seen_title = {norm_title(e.get("title", "")) for e in manuscript_bib}

    idf, docs = build_index(corpus)
    q = Counter(tokens(tex))

    cands = []
    for e, d in zip(corpus, docs):
        if norm_doi(e.get("doi", "")) and norm_doi(e["doi"]) in seen_doi:
            continue
        if norm_title(e.get("title", "")) in seen_title:
            continue
        co = surnames(e.get("author", ""))
        if coauthor and deaccent(coauthor).lower() not in co:
            continue
        score, terms = cosine(q, d, idf)
        if score <= 0:
            continue
        cands.append({
            "key": e["_key"], "score": round(score, 4),
            "year": e.get("year", ""), "title": e.get("title", ""),
            "venue": e.get("journal") or e.get("booktitle", ""),
            "doi": e.get("doi", ""), "authors": e.get("author", ""),
            "matched_terms": terms, "source": e.get("_source", ""),
        })
    cands.sort(key=lambda c: -c["score"])

    n_used = len(used)
    return {
        "tex": str(tex_path),
        "bib": str(bib_path) if bib_path else None,
        "corpus_missing": missing,
        "corpus_size": len(corpus),
        "current": {
            "references_cited": n_used,
            "self_citations": len(self_cited),
            "rate_percent": round(100 * len(self_cited) / n_used, 1) if n_used else 0.0,
            "entries": [{"key": e["_key"], "year": e.get("year", ""),
                         "title": e.get("title", "")[:110]} for e in self_cited],
        },
        "candidates": cands[:top],
    }


def emit(corpus_paths: list[Path], key: str) -> int:
    for p in corpus_paths:
        if not p.is_file():
            continue
        for e in parse_bib(p.read_text(encoding="utf-8", errors="replace")):
            if e["_key"] == key:
                # Champs de gestion CV (categorie, rang, HAL, financements...) : sans
                # objet dans une .bib d'article, et bruit pur pour un coauteur.
                drop = {"abstract", "category", "dixcitations", "funds", "hal", "keywords",
                        "order", "publiweb", "rank", "researchgate", "web", "arxiv", "note"}
                lines = [f"@{e['_type']}{{{e['_key']},"]
                for k, v in e.items():
                    if k.startswith("_") or k in drop or not v:
                        continue
                    # Le corpus CV stocke le DOI en URL complete et utilise `page` :
                    # normaliser ici, sinon crossref_verify.py ne resout pas l'entree
                    # et le style bibliographique perd la pagination.
                    if k == "doi":
                        v = norm_doi(v)
                    if k == "page":
                        k = "pages"
                    lines.append(f"  {k} = {{{v}}},")
                lines.append("}")
                print("\n".join(lines))
                return 0
    print(f"cle introuvable dans le corpus : {key}", file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Taux d'auto-citation et candidats classes (/bib-check Phase 6).")
    ap.add_argument("tex")
    ap.add_argument("--corpus", action="append", default=None,
                    help="fichier .bib de reference (repetable ; defaut : les 2 .bib du CV)")
    ap.add_argument("--author", default=DEFAULT_AUTHOR, help="nom de famille de l'auteur")
    ap.add_argument("--coauthor", default=None,
                    help="ne garder que les travaux co-signes avec ce nom (ex. Sola)")
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--emit", default=None, metavar="KEY",
                    help="imprimer l'entree BibTeX prete a coller, puis sortir")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    corpus_paths = [Path(c).expanduser() for c in a.corpus] if a.corpus else DEFAULT_CORPUS
    if a.emit:
        return emit(corpus_paths, a.emit)

    p = Path(a.tex)
    if not p.is_file():
        print(f"introuvable : {p}", file=sys.stderr)
        return 1
    res = run(p, corpus_paths, a.author, a.coauthor, a.top)

    if a.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    if res["corpus_missing"]:
        print("corpus absent (auto-citations non evaluables depuis le CV) :")
        for m in res["corpus_missing"]:
            print(f"  {m}")
    c = res["current"]
    print(f"Corpus de reference : {res['corpus_size']} entrees")
    print(f"References citees   : {c['references_cited']}")
    print(f"Auto-citations      : {c['self_citations']}  ({c['rate_percent']} %)")
    for e in c["entries"]:
        print(f"    {e['year']}  {e['key']:<22} {e['title']}")
    band = ("aucune -- verifier qu'aucune n'est DUE" if c["rate_percent"] == 0 else
            "usage courant" if c["rate_percent"] <= 15 else
            "eleve : chaque entree doit passer le test du tiers" if c["rate_percent"] <= 25 else
            "TRES eleve : un editeur le remarquera")
    print(f"                      -> {band}")

    print(f"\nCandidats non cites, classes par proximite thematique "
          f"(score = cosinus TF-IDF, PAS une recommandation) :")
    if not res["candidates"]:
        print("  aucun")
    for cd in res["candidates"]:
        print(f"  {cd['score']:.3f}  [{cd['key']}] {cd['year']}  {cd['title'][:88]}")
        print(f"          {cd['venue'][:70]}")
        print(f"          termes : {', '.join(cd['matched_terms'])}")
    print("\nTri obligatoire avant insertion : test du tiers (citerais-je ce papier ICI")
    print("s'il etait de quelqu'un d'autre ?) et point d'ancrage precis dans le texte.")
    print("Recuperer une entree : --emit <cle>. Puis crossref_verify.py sur la .bib.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
