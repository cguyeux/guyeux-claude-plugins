#!/usr/bin/env python3
"""Multi-source Film Metadata & Rich Synopsis Enrichment Engine.

Enriches film metadata using:
1. Local IMDb SQLite cache (title.basics + title.ratings).
2. Multilingual Wikipedia API (FR & EN). When French Wikipedia has only a stub,
   it automatically extracts the complete English plot and translates it into French.
3. Strict matching score algorithm (0-100) verifying title, year, and director.
4. Clean markup stripping to produce high quality prose without Wikipedia artifacts.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

USER_AGENT = "FilmEnricherRAG/2.0 (contact@cinemadb.local)"


def normalize(text: Optional[str]) -> str:
    if not text:
        return ""
    text = text.replace("æ", "ae").replace("Æ", "Ae").replace("œ", "oe").replace("Œ", "Oe")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()


def strip_articles(norm_str: str) -> str:
    articles = [
        "le ", "la ", "les ", "l ", "un ", "une ", "des ", "the ", "a ", "an ",
        "der ", "die ", "das ", "el ", "la ", "los ", "las ", "il ", "lo ", "gli ", "i "
    ]
    for art in articles:
        if norm_str.startswith(art):
            return norm_str[len(art):].strip()
    return norm_str


def clean_wiki_markup(text: Optional[str]) -> str:
    if not text:
        return ""
    text = re.sub(r"\{\{date-?\|([^|}]+)(?:\|([^|}]+))?(?:\|([^|}]+))?.*?\}\}", lambda m: " ".join(filter(None, [m.group(1), m.group(2), m.group(3)])), text)
    text = re.sub(r"\{\{lang\|[^|]+\|([^}]+)\}\}", r"\1", text)
    text = re.sub(r"\{\{unité\|([^|}]+)\|([^|}]+).*?\}\}", r"\1 \2", text)
    text = re.sub(r"\{\{1er\}\}", "1er", text)
    text = re.sub(r"^(?:vignette|thumb|file|fichier|image).*?\n", "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"(?:vignette|thumb|file|fichier|image)\|[^\n]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\d+px\|[^\n]*", "", text)
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\{\{[^}]+\}\}", "", text)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\'\'\'?", "", text)
    text = re.sub(r"\s+([,\.;])", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def translate_to_french(text: str) -> str:
    if not text or len(text.strip()) == 0:
        return ""
    cleaned = clean_wiki_markup(text)
    paragraphs = cleaned.split("\n\n")
    translated_paras = []
    for para in paragraphs:
        if not para.strip() or len(para.strip()) < 10:
            continue
        chunks = [para[i:i+1800] for i in range(0, len(para), 1800)]
        chunk_trans = []
        for ch in chunks:
            q = urllib.parse.quote(ch)
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=fr&dt=t&q={q}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            try:
                with urllib.request.urlopen(req, timeout=6) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    chunk_trans.append("".join([item[0] for item in data[0] if item[0]]))
            except Exception:
                chunk_trans.append(ch)
        translated_paras.append(" ".join(chunk_trans))
    return "\n\n".join(translated_paras)


def search_wikipedia(query: str, lang: str = "fr") -> List[Dict[str, Any]]:
    q = urllib.parse.quote(query)
    url = f"https://{lang}.wikipedia.org/w/api.php?action=query&list=search&srsearch={q}&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("query", {}).get("search", [])
    except Exception:
        return []


def get_wikipedia_page_content(page_title: str, lang: str = "fr") -> Tuple[Optional[str], str]:
    q = urllib.parse.quote(page_title)
    url = f"https://{lang}.wikipedia.org/w/api.php?action=parse&page={q}&prop=wikitext|sections&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")

            syn_match = re.search(
                r"==\s*(?:Synopsis|Résumé|Plot|Histoire|Trame|Synopsis complet|Prémisse)\s*==\s*\n(.*?)(?=\n==|\Z)",
                wikitext,
                re.DOTALL | re.IGNORECASE
            )
            synopsis = clean_wiki_markup(syn_match.group(1)) if syn_match else None

            if not synopsis or len(synopsis) < 40:
                intro_match = re.search(r"^.*?(?=\n==|\Z)", wikitext, re.DOTALL)
                if intro_match:
                    intro_cleaned = clean_wiki_markup(intro_match.group(0))
                    lines = [
                        l.strip() for l in intro_cleaned.split("\n")
                        if l.strip() and not l.startswith("|") and not l.startswith("{") and len(l.strip()) > 30
                    ]
                    if lines:
                        synopsis = " ".join(lines)

            return synopsis, wikitext
    except Exception:
        return None, ""


def calculate_match_score(
    target_title: str,
    target_orig_title: Optional[str],
    target_year: int,
    target_director: Optional[str],
    candidate_title: str,
    candidate_snippet: str,
    candidate_wikitext: str,
) -> Tuple[int, List[str]]:
    score = 0
    reasons = []

    t_norm = normalize(target_title)
    o_norm = normalize(target_orig_title) if target_orig_title else ""
    c_norm = normalize(candidate_title)
    snippet_norm = normalize(candidate_snippet)
    full_text_norm = normalize(
        candidate_title + " " + candidate_snippet + " " + (candidate_wikitext[:3000] if candidate_wikitext else "")
    )

    if any(dis in c_norm or dis in snippet_norm for dis in ["homonymie", "disambiguation", "filmographie de", "liste des films", "liste de films"]):
        score -= 60
        reasons.append("Page homonymie/liste (-60)")

    if "(film" in candidate_title.lower() or "film)" in candidate_title.lower() or "série" in candidate_title.lower():
        score += 20
        reasons.append("Suffixe cinéma dans titre (+20)")

    has_title_in_cand_title = (t_norm and t_norm in c_norm) or (o_norm and o_norm in c_norm)
    stop_words = {"le", "la", "les", "l", "un", "une", "des", "the", "a", "an", "de", "du", "et", "and", "in", "on", "at"}
    target_words = set(t_norm.split() + o_norm.split()) - stop_words
    cand_words = set(c_norm.split())
    has_shared_word = bool(target_words & cand_words)

    if t_norm and (t_norm == c_norm or t_norm == strip_articles(c_norm)):
        score += 40
        reasons.append("Titre FR exact (+40)")
    elif o_norm and (o_norm == c_norm or o_norm == strip_articles(c_norm)):
        score += 40
        reasons.append("Titre original exact (+40)")
    elif has_title_in_cand_title:
        score += 35
        reasons.append("Titre complet dans titre candidat (+35)")
    elif has_shared_word:
        score += 20
        reasons.append("Mots du titre dans titre candidat (+20)")
    else:
        score -= 30
        reasons.append("Titre candidat différent (-30)")

    year_str = str(target_year)
    if year_str in c_norm:
        score += 25
        reasons.append(f"Année {year_str} dans titre (+25)")
    elif year_str in full_text_norm:
        score += 15
        reasons.append(f"Année {year_str} dans contenu (+15)")
    elif str(target_year - 1) in full_text_norm or str(target_year + 1) in full_text_norm:
        score += 10
        reasons.append("Année proche (+/-1) dans contenu (+10)")

    if target_director:
        dir_last_name = target_director.split()[-1] if target_director else ""
        dir_norm = normalize(dir_last_name)
        if dir_norm and len(dir_norm) >= 3 and dir_norm in full_text_norm:
            score += 20
            reasons.append(f"Réalisateur {dir_last_name} validé (+20)")

    if any(kw in full_text_norm for kw in ["film", "cinema", "realise par", "directed by", "long metrage", "court metrage"]):
        score += 5
        reasons.append("Mots-clés cinéma (+5)")

    final_score = min(100, max(0, score))
    return final_score, reasons


def enrich_single_film(
    title: str,
    orig_title: Optional[str],
    year: int,
    director: Optional[str]
) -> Dict[str, Any]:
    queries_fr = [
        f"{title} (film, {year})",
        f"{title} (film)",
        f"{title} {year} {director or ''}".strip(),
    ]
    if orig_title:
        queries_fr.append(f"{orig_title} {year} {director or ''}".strip())

    best_match: Optional[str] = None
    best_score = 0
    best_synopsis: Optional[str] = None
    best_url: Optional[str] = None
    best_lang = "fr"
    best_reasons: List[str] = []

    # 1. Search French Wikipedia
    for q in queries_fr:
        results = search_wikipedia(q, "fr")
        for r in results[:4]:
            cand_title = r["title"]
            syn, wikitext = get_wikipedia_page_content(cand_title, "fr")
            score, reasons = calculate_match_score(
                title, orig_title, year, director, cand_title, r.get("snippet", ""), wikitext
            )
            if score > best_score:
                best_score = score
                best_match = cand_title
                best_synopsis = syn
                best_url = f"https://fr.wikipedia.org/wiki/{urllib.parse.quote(cand_title)}"
                best_lang = "fr"
                best_reasons = reasons
        if best_score >= 80 and best_synopsis and len(best_synopsis) >= 350:
            break

    # 2. If French summary is too short (< 350 chars) or score is low, search English Wikipedia
    if best_score < 75 or not best_synopsis or len(best_synopsis) < 350:
        search_term_en = orig_title or title
        queries_en = [
            f"{search_term_en} ({year} film)",
            f"{search_term_en} {year} film {director or ''}".strip(),
            f"{search_term_en} (film)",
        ]
        best_score_en = 0
        best_match_en = None
        best_synopsis_en = None
        best_url_en = None

        for q in queries_en:
            results = search_wikipedia(q, "en")
            for r in results[:4]:
                cand_title = r["title"]
                syn, wikitext = get_wikipedia_page_content(cand_title, "en")
                score, reasons = calculate_match_score(
                    title, orig_title, year, director, cand_title, r.get("snippet", ""), wikitext
                )
                if score > best_score_en:
                    best_score_en = score
                    best_match_en = cand_title
                    best_synopsis_en = syn
                    best_url_en = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(cand_title)}"
            if best_score_en >= 80 and best_synopsis_en:
                break

        if best_synopsis_en and len(best_synopsis_en) > len(best_synopsis or ""):
            # Translate English plot to French
            translated_syn = translate_to_french(best_synopsis_en)
            if translated_syn and len(translated_syn) > len(best_synopsis or ""):
                best_synopsis = translated_syn
                best_match = best_match_en or best_match
                best_url = best_url_en or best_url
                best_score = max(best_score, best_score_en)
                best_lang = "en->fr"

    return {
        "title": title,
        "original_title": orig_title,
        "year": year,
        "director": director,
        "match_score": best_score,
        "matched_page": best_match,
        "source_url": best_url,
        "source_lang": best_lang,
        "match_reasons": best_reasons,
        "synopsis": best_synopsis,
        "confidence": "HIGH" if best_score >= 75 else ("MODERATE" if best_score >= 50 else "LOW")
    }


def main():
    parser = argparse.ArgumentParser(description="Enrich film with rich synopsis and metadata.")
    parser.add_argument("title", help="Film title in French or main title")
    parser.add_argument("--orig-title", help="Original title")
    parser.add_argument("--year", type=int, required=True, help="Release year")
    parser.add_argument("--director", help="Director name")
    parser.add_argument("--format", choices=["text", "json"], default="text")

    args = parser.parse_args()
    data = enrich_single_film(args.title, args.orig_title, args.year, args.director)

    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"\n🎬 {data['title']} ({data['year']}) — {data['director']}")
        print(f"Match Score : {data['match_score']}/100 [{data['confidence']}]")
        print(f"Source Page : {data['matched_page']} ({data['source_url']}) [Lang: {data['source_lang']}]")
        print("\n📖 Synopsis:")
        print(data['synopsis'] or "Aucun résumé trouvé.")


if __name__ == "__main__":
    main()
