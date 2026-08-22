#!/usr/bin/env python3
"""Economie du texte d'un manuscrit LaTeX, pour le skill /deai-latex (R14, R15, R16).

Repond a trois questions qu'une relecture lineaire ne sait PAS trancher, parce que
chacune exige de comparer des passages DISTANTS, chacun correct isolement :

  R14  Ou le texte raconte-t-il ce qui n'a PAS marche ?
       Un negatif informatif (modele nul, controle, claim publie refute, borne de
       validite) et une impasse de chantier (« nous avons d'abord essaye X, puis
       Y ») s'ecrivent avec EXACTEMENT le meme vocabulaire. Aucun script ne peut
       les distinguer : celui-ci remonte les passages, le tri est humain. C'est un
       SIGNAL, jamais un verdict -- cf. la doctrine de latex_metrics.py.

  R15  Le manuscrit repete-t-il ce qu'il a deja dit ?
       Deux mesures independantes, parce qu'elles attrapent deux redites de nature
       differente : les n-grammes partages entre sections (redite quasi verbatim,
       typique d'une Discussion qui recopie les Resultats) et la carte des jetons
       NUMERIQUES (un meme chiffre redonne dans trois sections = le raisonnement a
       ete refait, pas synthetise). La seconde attrape ce que la premiere rate,
       car reformuler un paragraphe casse les n-grammes mais garde les chiffres.

  R16  Combien pese le manuscrit, section par section, et qu'y a-t-il deja en
       supplementaire ? La limite d'une revue s'exprime tantot sur le texte seul,
       tantot resume inclus, presque jamais legendes et references incluses : un
       compte unique ne veut rien dire. On rend donc la decomposition, et la masse
       par section, qui dit OU couper.

Le comptage de mots reutilise count_rendered_words() de latex_metrics.py (meme
piege documente : une regex qui supprime \\emph{X} avec son argument SOUS-ESTIME,
un pdftotext sur un manuscrit charge en `lineno` SUR-ESTIME).

Usage :
    python3 content_economy.py main.tex
    python3 content_economy.py main.tex --limit 6500      # limite de la revue cible
    python3 content_economy.py main.tex --ngram 10 --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # voisinage latex_metrics.py
from latex_metrics import count_rendered_words, extract_abstract  # noqa: E402

# --------------------------------------------------------------------------
# R14 -- marqueurs de narratif d'essai infructueux.
#
# Volontairement LARGES : le tri se fait a la lecture du contexte, pas ici. Un
# marqueur peut annoncer un negatif parfaitement publiable (« the positive control
# failed to reproduce », « no hit was found », qui BORNE la conclusion) aussi bien
# qu'une impasse de chantier. Le script rend la phrase entiere pour que ce tri soit
# possible sans rouvrir le fichier.
# --------------------------------------------------------------------------
FAILURE_MARKERS = [
    # tentative anterieure abandonnee -- le motif le plus souvent purement narratif
    (r"\bwe (?:first|initially|originally) (?:tried|attempted|used|considered|explored)\b",
     "tentative anterieure"),
    (r"\b(?:initial|first|early|preliminary) (?:attempts?|efforts?|analyses|runs?|versions?)\b",
     "tentative anterieure"),
    (r"\bwe (?:then|subsequently|therefore) (?:turned to|switched to|moved to|abandoned|discarded)\b",
     "bascule de methode"),
    (r"\b(?:proved|turned out to be) (?:unreliable|unstable|impractical|inadequate|unusable)\b",
     "outil ecarte"),
    (r"\b(?:was|were) (?:abandoned|discarded|dropped|set aside|not pursued)\b",
     "piste abandonnee"),
    (r"\bthis (?:approach|strategy|route|avenue|attempt) (?:failed|did not|was not)\b",
     "piste abandonnee"),
    # resultat negatif -- peut etre informatif OU du remplissage
    (r"\b(?:failed to|did not (?:yield|reveal|detect|produce|converge|identify))\b",
     "resultat negatif"),
    (r"\b(?:no|without) (?:significant |detectable |clear )?(?:hit|match|signal|homolog\w*|"
     r"enrichment|difference|effect|association)\b",
     "resultat negatif"),
    (r"\b(?:unsuccessful|inconclusive|without success|to no avail)\b",
     "resultat negatif"),
    (r"\b(?:we were unable to|it was not possible to|could not be (?:obtained|computed|resolved))\b",
     "limite technique"),
    # peripeties d'ACCES a une ressource : quasi toujours du chantier, jamais un
    # resultat. Categorie ajoutee apres l'avoir vue survivre dans un manuscrit reel
    # (« the supplementary-file route and the PMC HTML page were both found to be
    # blocked »), ou elle racontait comment la donnee avait ete obtenue, pas ce
    # qu'elle disait.
    (r"\b(?:was|were|is|are) (?:both )?(?:found to be )?(?:blocked|unavailable|inaccessible|"
     r"paywalled|rate-limited|down|offline)\b",
     "acces a une ressource"),
    (r"\b(?:returned|yielded) (?:no|an? (?:error|empty|403|404|500))\b", "acces a une ressource"),
    (r"\b(?:timed out|time-outs?|as a workaround|we (?:fell|fall) back (?:on|to)|"
     r"fell back (?:on|to)|manual(?:ly)? download)\b",
     "acces a une ressource"),
    (r"\b(?:could not|was not able to) (?:be )?(?:access|download|retriev|fetch|reach)\w*\b",
     "acces a une ressource"),
    # francais
    (r"\bnous avons (?:d'abord|initialement|dans un premier temps) (?:essaye|tente|utilise)\b",
     "tentative anterieure"),
    (r"\b(?:cette|la) (?:piste|approche|strategie) (?:n'a (?:rien donne|pas abouti)|a ete abandonnee)\b",
     "piste abandonnee"),
    (r"\bn'a (?:pas|rien) (?:donne|abouti|permis|revele|detecte)\b", "resultat negatif"),
    (r"\bsans (?:succes|resultat|effet)\b", "resultat negatif"),
    (r"\b(?:inaccessible|indisponible|bloque[e]?|hors service)\b", "acces a une ressource"),
]

# --------------------------------------------------------------------------
# R15 -- jetons numeriques suivis a travers les sections.
#
# On ne suit PAS n'importe quel nombre : un numero de section, une annee, un
# effectif d'echantillon repete sont normaux et noieraient le signal. On garde ce
# qui porte un RESULTAT : pourcentage, p-value, decimale a >= 2 chiffres, entier
# long, nombre suivi d'une unite. Les annees (1900-2099) sont explicitement exclues.
# --------------------------------------------------------------------------
NUMERIC_PATTERNS = [
    r"\d+(?:[.,]\d+)?\s*(?:\\?%|percent)",
    r"[pqE]\s*[=<>]\s*\d*\.?\d+(?:\s*[eE]\s*-?\d+)?",
    r"\d+\.\d{2,}",
    r"\d+(?:[.,]\d+)?\s*(?:bp|kb|Mb|nt|aa|kDa|kcal|fold|x)\b",
    r"\b\d{3,}\b",
]
YEARLIKE = re.compile(r"^(?:19|20)\d{2}$")

# Mots vides : un n-gramme entierement fait de connecteurs n'est pas une redite de
# contenu, c'est de la prose ordinaire (« on the other hand, it is important to »).
STOPWORDS = {
    "the", "a", "an", "of", "in", "to", "and", "or", "for", "with", "that", "this",
    "is", "are", "was", "were", "be", "been", "by", "as", "at", "on", "from", "it",
    "its", "we", "our", "which", "than", "then", "not", "but", "all", "can", "may",
    "these", "those", "their", "has", "have", "had", "more", "most", "such", "also",
    "de", "la", "le", "les", "des", "du", "un", "une", "et", "en", "dans", "que",
    "qui", "pour", "par", "sur", "est", "sont", "ont", "ete", "aux", "au", "ce",
    "cette", "ces", "nous", "plus", "pas", "ne", "se", "son", "sa", "ses",
}


# ------------------------------ lecture du source -------------------------------

def resolve_inputs(path: Path, seen: set[Path] | None = None, depth: int = 0) -> str:
    """Concatene le .tex et ses \\input/\\include (Phase 0 du SKILL)."""
    seen = seen if seen is not None else set()
    path = path.resolve()
    if path in seen or depth > 6 or not path.exists():
        return ""
    seen.add(path)
    text = path.read_text(encoding="utf-8", errors="replace")

    def sub(m: re.Match) -> str:
        target = m.group(2).strip()
        cand = (path.parent / target)
        for c in (cand, cand.with_suffix(".tex"), Path(str(cand) + ".tex")):
            if c.exists() and c.is_file():
                return "\n" + resolve_inputs(c, seen, depth + 1) + "\n"
        return ""  # fichier absent : ne pas inventer de contenu

    return re.sub(r"\\(input|include)\{([^}]*)\}", sub, text)


def strip_comments(t: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", t)


def take_body(tex: str) -> str:
    """Corps entre \\begin{document} et la bibliographie (exclue du comptage)."""
    m = re.search(r"\\begin\{document\}(.*?)\\end\{document\}", tex, re.S)
    body = m.group(1) if m else tex
    cut = re.search(r"\\bibliography\{|\\printbibliography|\\begin\{thebibliography\}", body)
    return body[: cut.start()] if cut else body


def match_brace(s: str, open_idx: int) -> int:
    """Index de l'accolade fermante appariee. -1 si non appariee.

    Le compteur de profondeur est indispensable : une regex `\\{[^}]*\\}` tronque
    au premier `}` interne (meme correctif que doi_coherence.py cote bib-check).
    """
    depth = 0
    i = open_idx
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


FLOAT_ENVS = ("figure", "table", "sidewaysfigure", "sidewaystable", "longtable", "algorithm")


def split_floats(body: str) -> tuple[str, list[str], int]:
    """Separe le texte courant du contenu des flottants. Rend (texte, legendes, n_flottants)."""
    floats: list[str] = []
    pat = re.compile(
        r"\\begin\{(" + "|".join(FLOAT_ENVS) + r")\*?\}(.*?)\\end\{\1\*?\}", re.S
    )
    rest = pat.sub(lambda m: floats.append(m.group(2)) or " ", body)
    captions: list[str] = []
    for f in floats:
        for m in re.finditer(r"\\caption\*?\s*(?:\[[^\]]*\])?\{", f):
            end = match_brace(f, m.end() - 1)
            if end > 0:
                captions.append(f[m.end(): end])
    return rest, captions, len(floats)


def split_sections(body: str) -> list[tuple[str, str]]:
    """Decoupe en (titre, contenu) sur \\section. Le pre-ambule devient 'Front matter'."""
    marks = list(re.finditer(r"\\section\*?\s*(?:\[[^\]]*\])?\{", body))
    if not marks:
        return [("(document)", body)]
    out: list[tuple[str, str]] = []
    head = body[: marks[0].start()].strip()
    if count_rendered_words(head) > 20:
        out.append(("Front matter (avant la 1re section)", head))
    for i, m in enumerate(marks):
        end_title = match_brace(body, m.end() - 1)
        title = body[m.end(): end_title] if end_title > 0 else "?"
        start = (end_title + 1) if end_title > 0 else m.end()
        stop = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        out.append((re.sub(r"\s+", " ", title).strip(), body[start:stop]))
    return out


# ------------------------------- normalisation ----------------------------------

def to_words(chunk: str) -> list[str]:
    """Texte rendu, minuscule, ponctuation retiree. Base des n-grammes."""
    t = strip_comments(chunk)
    t = re.sub(r"\\(?:label|ref|cref|Cref|autoref|eqref|cite[a-z]*|nocite)\*?\{[^{}]*\}", " ", t)
    for _ in range(3):
        t = re.sub(r"\\(?:emph|textit|textbf|texttt|textsc|underline|mbox|text)\*?\{([^{}]*)\}",
                   r"\1", t)
    t = re.sub(r"\$\$?[^$]*\$\$?", " ", t)
    t = re.sub(r"\\begin\{[^}]*\}|\\end\{[^}]*\}", " ", t)
    t = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", t)
    t = re.sub(r"[^0-9A-Za-z\u00C0-\u017F\-']+", " ", t)
    return [w for w in t.lower().split() if w]


def numeric_tokens(chunk: str) -> set[str]:
    t = strip_comments(chunk)
    t = re.sub(r"\\(?:label|ref|cref|Cref|autoref|eqref|cite[a-z]*)\*?\{[^{}]*\}", " ", t)
    found: set[str] = set()
    for pat in NUMERIC_PATTERNS:
        for m in re.finditer(pat, t):
            tok = re.sub(r"\s+", "", m.group(0)).replace("\\%", "%").lower()
            bare = tok.strip("%")
            if YEARLIKE.match(bare):
                continue
            found.add(tok)
    return found


# --------------------------------- mesures --------------------------------------

def shared_ngrams(sections: list[tuple[str, str]], n: int) -> list[dict]:
    """n-grammes apparaissant dans >= 2 sections DIFFERENTES (redite quasi verbatim)."""
    index: dict[tuple[str, ...], set[str]] = defaultdict(set)
    for title, content in sections:
        words = to_words(content)
        for i in range(len(words) - n + 1):
            gram = tuple(words[i: i + n])
            if sum(1 for w in gram if w not in STOPWORDS) < n // 2:
                continue  # prose connective, pas du contenu
            index[gram].add(title)
    hits = [{"ngram": " ".join(g), "sections": sorted(s)}
            for g, s in index.items() if len(s) > 1]
    # Absorber les n-grammes inclus dans un plus long partageant les memes sections :
    # une redite de 20 mots ne doit pas etre rapportee 13 fois.
    hits.sort(key=lambda h: -len(h["ngram"]))
    kept: list[dict] = []
    for h in hits:
        if any(h["ngram"] in k["ngram"] and k["sections"] == h["sections"] for k in kept):
            continue
        kept.append(h)
    return kept


def numeric_spread(sections: list[tuple[str, str]], abstract_titles: set[str]) -> list[dict]:
    """Jetons numeriques presents dans plusieurs sections du CORPS.

    L'abstract est exclu du compte : il est autonome, il RE-dit legitimement les
    chiffres du corps. Le signal recherche est un chiffre redonne entre Resultats
    et Discussion (le raisonnement a ete refait au lieu d'etre synthetise).
    """
    where: dict[str, set[str]] = defaultdict(set)
    for title, content in sections:
        if title in abstract_titles:
            continue
        for tok in numeric_tokens(content):
            where[tok].add(title)
    out = [{"token": t, "n_sections": len(s), "sections": sorted(s)}
           for t, s in where.items() if len(s) > 1]
    out.sort(key=lambda d: (-d["n_sections"], d["token"]))
    return out


def failure_narrative(sections: list[tuple[str, str]]) -> list[dict]:
    hits: list[dict] = []
    for title, content in sections:
        flat = re.sub(r"\s+", " ", strip_comments(content))
        for pat, kind in FAILURE_MARKERS:
            for m in re.finditer(pat, flat, re.IGNORECASE):
                start = flat.rfind(". ", 0, m.start()) + 2
                end = flat.find(". ", m.end())
                end = end + 1 if end > 0 else min(len(flat), m.end() + 160)
                hits.append({"section": title, "kind": kind,
                             "marker": m.group(0),
                             "sentence": flat[max(start, 0): end].strip()[:320]})
    return hits


def supplementary_inventory(tex_path: Path, body: str, n_floats: int) -> dict:
    """Ce qui est DEJA en supplementaire, et ce que le corps promet."""
    pointers = re.findall(
        r"(?:Supplementary|Supplemental)\s+(?:Table|Figure|Fig\.|Note|Data|Text|Material|File)"
        r"[~\s]*S?\d*[.\d]*|\b(?:Table|Figure|Fig\.)~?\s?S\d+", body)
    proj = tex_path.resolve().parent
    files: list[str] = []
    for cand in ("supplementary_materials", "supplementary", "supp", "SI"):
        d = proj / cand
        if d.is_dir():
            files += [str(p.relative_to(proj)) for p in sorted(d.rglob("*")) if p.is_file()]
    return {
        "floats_in_main": n_floats,
        "pointer_mentions": len(pointers),
        "distinct_pointers": sorted(set(re.sub(r"\s+", " ", p).strip() for p in pointers)),
        "supplementary_files": files[:60],
        "n_supplementary_files": len(files),
    }


# ---------------------------------- rapport -------------------------------------

def build(tex_path: Path, ngram: int, limit: int | None) -> dict:
    raw = resolve_inputs(tex_path)
    abstract = extract_abstract(raw) or ""
    body = take_body(raw)
    text_only, captions, n_floats = split_floats(body)
    sections = split_sections(text_only)

    w_abstract = count_rendered_words(abstract)
    w_captions = sum(count_rendered_words(c) for c in captions)
    per_section = [{"title": t, "words": count_rendered_words(c)} for t, c in sections]
    abstract_titles = {p["title"] for p in per_section
                       if re.search(r"abstract|resum", p["title"], re.I)}
    # Le front matter contient l'abstract quand celui-ci n'est pas une section :
    # ne pas le compter deux fois dans le texte principal.
    w_sections = sum(p["words"] for p in per_section)
    w_main = max(w_sections - w_abstract, 0) if not abstract_titles else w_sections - w_abstract

    res: dict = {
        "file": str(tex_path),
        "length": {
            "abstract": w_abstract,
            "main_text_excl_abstract_captions_refs": w_main,
            "captions": w_captions,
            "with_abstract": w_main + w_abstract,
            "with_abstract_and_captions": w_main + w_abstract + w_captions,
            "per_section": sorted(per_section, key=lambda d: -d["words"]),
        },
        "redundancy": {
            "shared_ngrams": shared_ngrams(sections, ngram),
            "numeric_spread": numeric_spread(sections, abstract_titles),
            "ngram_size": ngram,
        },
        "failure_narrative": failure_narrative(sections),
        "supplementary": supplementary_inventory(tex_path, body, n_floats),
    }
    if limit:
        res["length"]["journal_limit"] = limit
        res["length"]["over_by"] = {
            "main_text_only": w_main - limit,
            "with_abstract": w_main + w_abstract - limit,
        }
    return res


def report(res: dict) -> None:
    L = res["length"]
    print("== R16  Longueur ==")
    print(f"  texte principal (hors resume, legendes, references) : {L['main_text_excl_abstract_captions_refs']} mots")
    print(f"  resume : {L['abstract']}   legendes : {L['captions']}")
    print(f"  resume inclus : {L['with_abstract']}   resume + legendes : {L['with_abstract_and_captions']}")
    print("  (une limite de revue s'exprime sur l'un de ces perimetres : VERIFIER lequel"
          " dans le guide auteurs, ne pas supposer)")
    if "journal_limit" in L:
        ov = L["over_by"]
        verdict = ("DEPASSEMENT" if ov["main_text_only"] > 0 else "conforme")
        print(f"  limite annoncee {L['journal_limit']} : {verdict} "
              f"({ov['main_text_only']:+d} sur le texte seul, {ov['with_abstract']:+d} resume inclus)")
    print("  masse par section :")
    for p in L["per_section"][:12]:
        print(f"    {p['words']:6d}  {p['title'][:70]}")

    R = res["redundancy"]
    print(f"\n== R15  Redites ==")
    ng = R["shared_ngrams"]
    print(f"  n-grammes de {R['ngram_size']} mots partages entre sections : {len(ng)}")
    for h in ng[:12]:
        print(f"    [{' | '.join(h['sections'])[:60]}] « {h['ngram'][:110]} »")
    ns = R["numeric_spread"]
    strong = [d for d in ns if d["n_sections"] >= 3]
    print(f"  jetons numeriques dans >= 3 sections du corps : {len(strong)} "
          f"(dans >= 2 sections : {len(ns)})")
    for d in strong[:15]:
        print(f"    {d['token']:>12}  ->  {', '.join(s[:28] for s in d['sections'])}")

    F = res["failure_narrative"]
    print(f"\n== R14  Narratif d'essai infructueux (SIGNAL, pas verdict) : {len(F)} passage(s) ==")
    for h in F[:20]:
        print(f"  [{h['kind']}] {h['section'][:40]}")
        print(f"      « {h['sentence'][:200]} »")
    if F:
        print("  Tri a faire a la lecture : un negatif qui BORNE une conclusion, refute un claim")
        print("  publie, ou sert de controle -> garder. Une impasse de chantier -> couper.")

    S = res["supplementary"]
    print(f"\n== R16b Supplementaire ==")
    print(f"  flottants dans le corps : {S['floats_in_main']}")
    print(f"  renvois au supplementaire : {S['pointer_mentions']} "
          f"({len(S['distinct_pointers'])} distincts)")
    print(f"  fichiers supplementaires sur disque : {S['n_supplementary_files']}")
    if S["distinct_pointers"]:
        print("  " + ", ".join(S["distinct_pointers"][:12]))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Longueur, redites, narratif d'echec et inventaire supplementaire "
                    "d'un manuscrit LaTeX (/deai-latex R14-R16).")
    ap.add_argument("tex")
    ap.add_argument("--ngram", type=int, default=8,
                    help="taille des n-grammes de redite (defaut 8 ; baisser = plus de bruit)")
    ap.add_argument("--limit", type=int, default=None,
                    help="limite de mots de la revue cible, VERIFIEE dans le guide auteurs")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    p = Path(a.tex)
    if not p.exists():
        print(f"introuvable : {p}", file=sys.stderr)
        return 1
    res = build(p, a.ngram, a.limit)
    if a.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        report(res)
    return 0


if __name__ == "__main__":
    sys.exit(main())
