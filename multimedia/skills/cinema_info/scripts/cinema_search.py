#!/usr/bin/env python3
"""Unified Cinema Information & Multi-Source Intelligence Engine (`cinema_info`).

Federates metadata, detailed synopses, and critical reception across:
1. IMDb Local SQLite Cache (Ratings, Votes, Genres, Runtime, tconst).
2. Multilingual Wikipedia (FR + EN plot auto-translated into natural French).
3. film-documentaire.fr (Documentaries, thematic tags, festival distinctions, Tënk reviews).
4. 1001films.org (1001 Movies You Must See Before You Die essays & critical analyses).
5. National Film Registry / Library of Congress (NFR preservation status & essays).
6. Muad'Dib Sci-Fi & Fantastique Hub (https://muaddib-sci-fi.blogspot.com/).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from bs4 import BeautifulSoup
except ImportError as exc:
    raise SystemExit(
        "Dependance manquante: beautifulsoup4. Installez-la explicitement dans "
        "l'environnement choisi avant d'utiliser cinema_info."
    ) from exc

IMDB_DB_PATH = Path("~/.cache/imdb-skill/imdb.sqlite").expanduser()
USER_AGENT = "CinemaIntelligenceHub/2.0 (contact@cinemadb.local)"


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


def safe_fetch_json(url: str, max_retries: int = 3) -> Optional[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(1.0 * (attempt + 1))
            else:
                break
        except Exception:
            time.sleep(0.5 * (attempt + 1))
    return None


def safe_fetch_html(url: str, post_data: Optional[bytes] = None, max_retries: int = 3) -> Optional[str]:
    headers = {"User-Agent": USER_AGENT}
    req = urllib.request.Request(url, data=post_data, headers=headers)
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(1.2 * (attempt + 1))
            else:
                break
        except Exception:
            time.sleep(0.5 * (attempt + 1))
    return None


# ----------------------------------------------------------------------
# 1. IMDb Provider
# ----------------------------------------------------------------------
def query_imdb_cache(title: str, orig_title: Optional[str], year: Optional[int]) -> Dict[str, Any]:
    if not IMDB_DB_PATH.exists():
        return {}
    conn = sqlite3.connect(IMDB_DB_PATH)
    cur = conn.cursor()

    cands = [normalize(title), strip_articles(normalize(title))]
    if orig_title:
        cands.extend([normalize(orig_title), strip_articles(normalize(orig_title))])
    cands = list(dict.fromkeys([c for c in cands if c]))

    placeholders = ",".join(["?"] * len(cands))
    query = f"""
        SELECT t.tconst, t.primary_title, t.original_title, t.title_type, t.runtime_minutes, t.genres, r.average_rating, r.num_votes
        FROM titles t
        LEFT JOIN ratings r ON t.tconst = r.tconst
        WHERE t.norm_title IN ({placeholders})
    """
    params: List[Any] = list(cands)
    if year:
        query += " AND (t.start_year BETWEEN ? AND ?)"
        params.extend([year - 2, year + 2])

    query += " ORDER BY r.num_votes DESC NULLS LAST LIMIT 1"
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()

    if not row:
        return {}

    tconst, p_title, o_title, t_type, runtime, genres, rating, votes = row
    return {
        "imdb_id": tconst,
        "primary_title": p_title,
        "original_title": o_title,
        "title_type": t_type,
        "runtime_minutes": runtime,
        "genres": [g.strip() for g in genres.split(",")] if genres else [],
        "rating": rating,
        "votes": votes
    }


# ----------------------------------------------------------------------
# 2. National Film Registry Provider (NFR)
# ----------------------------------------------------------------------
NFR_CACHE: List[Dict[str, Any]] = []

def load_nfr_registry() -> List[Dict[str, Any]]:
    global NFR_CACHE
    if NFR_CACHE:
        return NFR_CACHE

    url = "https://en.wikipedia.org/wiki/National_Film_Registry"
    html = safe_fetch_html(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="wikitable")
    if not table:
        return []

    for r in table.find_all("tr")[1:]:
        cols = [td.get_text(" ", strip=True) for td in r.find_all(["td", "th"])]
        if len(cols) >= 4:
            title = cols[0]
            film_type = cols[1]
            yr_match = re.search(r"\b(18\d\d|19\d\d|20\d\d)\b", cols[2])
            ind_match = re.search(r"\b(19\d\d|20\d\d)\b", cols[3])
            yr = int(yr_match.group(1)) if yr_match else None
            ind_yr = int(ind_match.group(1)) if ind_match else None

            NFR_CACHE.append({
                "title": title,
                "norm_title": normalize(title),
                "year": yr,
                "induction_year": ind_yr,
                "film_type": film_type
            })
    return NFR_CACHE


def check_nfr(title: str, orig_title: Optional[str], year: Optional[int]) -> Optional[Dict[str, Any]]:
    registry = load_nfr_registry()
    t_norm = normalize(title)
    o_norm = normalize(orig_title) if orig_title else ""

    for item in registry:
        if (item["norm_title"] in [t_norm, o_norm, strip_articles(t_norm), strip_articles(o_norm)]):
            if not year or not item["year"] or abs(item["year"] - year) <= 1:
                return item
    return None


# ----------------------------------------------------------------------
# 3. 1001 Films You Must See Provider (`1001films.org`)
# ----------------------------------------------------------------------
def search_1001_films(title: str, orig_title: Optional[str], director: Optional[str]) -> Optional[Dict[str, Any]]:
    queries = [title]
    if orig_title and orig_title != title:
        queries.append(orig_title)
    if director:
        dir_last = director.split()[-1]
        queries.insert(0, f"{dir_last} {title}")
        if orig_title and orig_title != title:
            queries.insert(1, f"{dir_last} {orig_title}")

    t_norm = normalize(title)
    o_norm = normalize(orig_title) if orig_title else ""

    for q in list(dict.fromkeys(queries)):
        url = f"https://www.1001films.org/search?q={urllib.parse.quote(q)}"
        html = safe_fetch_html(url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        posts = soup.find_all("div", class_=lambda c: c and ("post" in str(c) or "article" in str(c) or "post-outer" in str(c)))
        for p in posts:
            title_el = p.find(["h3", "h2", "h1"], class_=lambda c: c and "title" in str(c).lower())
            p_title = title_el.get_text(strip=True) if title_el else ""
            body_el = p.find("div", class_=lambda c: c and "body" in str(c).lower())
            p_text = body_el.get_text(" ", strip=True) if body_el else ""

            if any(bad in p_text for bad in ["Aucun message correspondant", "triés par pertinence", "Afficher tous les messages"]):
                continue

            p_norm = normalize(p_title + " " + p_text[:400])

            if (t_norm and t_norm in p_norm) or (o_norm and o_norm in p_norm):
                if len(p_text) > 100:
                    link_el = title_el.find("a", href=True) if title_el else None
                    post_url = link_el["href"] if link_el else url
                    return {
                        "matched": True,
                        "post_title": p_title,
                        "review": p_text,
                        "url": post_url
                    }
    return None


# ----------------------------------------------------------------------
# 4. Muad'Dib Sci-Fi & Fantastique Provider
# ----------------------------------------------------------------------
def search_muaddib_scifi(title: str, orig_title: Optional[str], year: Optional[int], director: Optional[str]) -> Optional[Dict[str, Any]]:
    queries = [title]
    if orig_title and orig_title != title:
        queries.append(orig_title)
    if director:
        dir_last = director.split()[-1]
        queries.append(f"{dir_last} {title}")

    t_norm = normalize(title)
    o_norm = normalize(orig_title) if orig_title else ""

    for q in list(dict.fromkeys(queries)):
        url = f"https://muaddib-sci-fi.blogspot.com/search?q={urllib.parse.quote(q)}"
        html = safe_fetch_html(url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        posts = soup.find_all("div", class_=lambda c: c and ("post" in str(c) or "article" in str(c) or "post-outer" in str(c)))

        for p in posts:
            title_el = p.find(["h3", "h2", "h1"], class_=lambda c: c and "title" in str(c).lower())
            p_title = title_el.get_text(strip=True) if title_el else ""
            link_el = title_el.find("a", href=True) if title_el else None
            post_url = link_el["href"] if link_el else url

            p_norm = normalize(p_title)

            if (t_norm and t_norm in p_norm) or (o_norm and o_norm in p_norm):
                full_post_html = safe_fetch_html(post_url) if link_el else None
                if full_post_html:
                    p_soup = BeautifulSoup(full_post_html, "html.parser")
                    b_el = p_soup.find("div", class_=lambda c: c and "post-body" in str(c).lower()) or p_soup.find("article")
                    full_text = b_el.get_text("\n", strip=True) if b_el else ""
                else:
                    body_el = p.find("div", class_=lambda c: c and "body" in str(c).lower())
                    full_text = body_el.get_text("\n", strip=True) if body_el else ""

                if len(full_text) > 80:
                    return {
                        "matched": True,
                        "post_title": p_title,
                        "review": full_text,
                        "url": post_url
                    }
    return None


# ----------------------------------------------------------------------
# 5. film-documentaire.fr Provider
# ----------------------------------------------------------------------
def search_film_documentaire(title: str, year: Optional[int], director: Optional[str]) -> Optional[Dict[str, Any]]:
    try:
        from film_doc_lookup import lookup_documentary
        res = lookup_documentary(title, year, director)
        if res.get("matched"):
            return res
    except Exception:
        pass
    return None


# ----------------------------------------------------------------------
# 6. Multilingual Wikipedia Provider with Clean Markup
# ----------------------------------------------------------------------
def clean_wiki_markup(text: Optional[str]) -> str:
    if not text:
        return ""
    text = re.sub(r"\{\{date-?\|([^|}]+)(?:\|([^|}]+))?(?:\|([^|}]+))?.*?\}\}", lambda m: " ".join(filter(None, [m.group(1), m.group(2), m.group(3)])), text)
    text = re.sub(r"\{\{lang\|[^|]+\|([^}]+)\}\}", r"\1", text)
    text = re.sub(r"\{\{unité\|([^|}]+)\|([^|}]+).*?\}\}", r"\1 \2", text)
    text = re.sub(r"\{\{1er\}\}", "1er", text)
    text = re.sub(r"^(?:vignette|thumb|file|fichier|image).*?\n", "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"(?:vignette|thumb|file|fichier|image)\|[^\n]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[\[(?:Fichier|File|Image):[^\]]+\]\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\d+px\|[^\n]*", "", text)
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\{\{[^}]+\}\}", "", text)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\'\'\'?", "", text)
    text = re.sub(r"\s+([,\.;])", r"\1", text)
    text = re.sub(r"[\[\]]", "", text)
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
            data = safe_fetch_json(url)
            if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                chunk_trans.append("".join([item[0] for item in data[0] if item and item[0]]))
            else:
                chunk_trans.append(ch)
        translated_paras.append(" ".join(chunk_trans))
    return "\n\n".join(translated_paras)


def get_wikipedia_synopsis(title: str, orig_title: Optional[str], year: Optional[int], director: Optional[str]) -> Dict[str, Any]:
    queries_fr = [
        f"{title} (film, {year})" if year else f"{title} (film)",
        f"{title} (film)",
        f"{title} {year} {director or ''}".strip(),
    ]
    if orig_title:
        queries_fr.append(f"{orig_title} (film, {year})" if year else f"{orig_title} (film)")

    best_syn = None
    best_url = None
    best_lang = "fr"

    for q in queries_fr:
        url = f"https://fr.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(q)}&format=json"
        data = safe_fetch_json(url)
        if not data:
            continue
        for r in data.get("query", {}).get("search", [])[:3]:
            cand_title = r["title"]
            page_url = f"https://fr.wikipedia.org/w/api.php?action=parse&page={urllib.parse.quote(cand_title)}&prop=wikitext&format=json"
            p_data = safe_fetch_json(page_url)
            if not p_data:
                continue
            wikitext = p_data.get("parse", {}).get("wikitext", {}).get("*", "")
            syn_match = re.search(r"==\s*(?:Synopsis|Résumé|Plot|Histoire|Trame)\s*==\s*\n(.*?)(?=\n==|\Z)", wikitext, re.DOTALL | re.IGNORECASE)
            syn = clean_wiki_markup(syn_match.group(1)) if syn_match else None
            if syn and len(syn) >= 300:
                best_syn = syn
                best_url = f"https://fr.wikipedia.org/wiki/{urllib.parse.quote(cand_title)}"
                best_lang = "fr"
                break
        if best_syn:
            break

    # English Fallback + Translation
    if not best_syn or len(best_syn) < 300:
        search_en = orig_title or title
        queries_en = [
            f"{search_en} ({year} film)" if year else f"{search_en} (film)",
            f"{search_en} (film)",
        ]
        for q in queries_en:
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(q)}&format=json"
            data = safe_fetch_json(url)
            if not data:
                continue
            for r in data.get("query", {}).get("search", [])[:3]:
                cand_title = r["title"]
                page_url = f"https://en.wikipedia.org/w/api.php?action=parse&page={urllib.parse.quote(cand_title)}&prop=wikitext&format=json"
                p_data = safe_fetch_json(page_url)
                if not p_data:
                    continue
                wikitext = p_data.get("parse", {}).get("wikitext", {}).get("*", "")
                syn_match = re.search(r"==\s*(?:Plot|Synopsis|Premise)\s*==\s*\n(.*?)(?=\n==|\Z)", wikitext, re.DOTALL | re.IGNORECASE)
                syn = clean_wiki_markup(syn_match.group(1)) if syn_match else None
                if syn and len(syn) > len(best_syn or ""):
                    translated = translate_to_french(syn)
                    if translated and len(translated) > len(best_syn or ""):
                        best_syn = translated
                        best_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(cand_title)}"
                        best_lang = "en->fr"
                        break
            if best_syn and len(best_syn) >= 400:
                break

    return {
        "synopsis": best_syn,
        "source_url": best_url,
        "source_lang": best_lang
    }


# ----------------------------------------------------------------------
# Unified Search Function
# ----------------------------------------------------------------------
def cinema_search(
    title: str,
    orig_title: Optional[str] = None,
    year: Optional[int] = None,
    director: Optional[str] = None,
    is_doc_hint: bool = False
) -> Dict[str, Any]:
    start_time = time.time()
    intel: Dict[str, Any] = {
        "query": {
            "title": title,
            "original_title": orig_title,
            "year": year,
            "director": director
        },
        "imdb": {},
        "wikipedia": {},
        "film_documentaire": None,
        "nfr": None,
        "one_thousand_one_films": None,
        "muaddib_scifi": None,
        "elapsed_seconds": 0
    }

    # 1. Query IMDb Cache
    imdb_data = query_imdb_cache(title, orig_title, year)
    if imdb_data:
        intel["imdb"] = imdb_data
        if not orig_title and imdb_data.get("original_title"):
            orig_title = imdb_data["original_title"]

    # 2. Check NFR Registry
    nfr_data = check_nfr(title, orig_title, year)
    if nfr_data:
        intel["nfr"] = nfr_data

    # 3. Check 1001 Films
    one_k_data = search_1001_films(title, orig_title, director)
    if one_k_data:
        intel["one_thousand_one_films"] = one_k_data

    # 4. Check Muad'Dib Sci-Fi & Fantastique (for SF/Fantasy/Horror or general)
    muaddib_data = search_muaddib_scifi(title, orig_title, year, director)
    if muaddib_data:
        intel["muaddib_scifi"] = muaddib_data

    # 5. Check film-documentaire.fr (if doc hint or category)
    is_doc = is_doc_hint or (imdb_data.get("genres") and "Documentary" in imdb_data["genres"])
    if is_doc or not intel["imdb"]:
        doc_data = search_film_documentaire(title, year, director)
        if doc_data:
            intel["film_documentaire"] = doc_data

    # 6. Multilingual Wikipedia Synopsis
    wiki_data = get_wikipedia_synopsis(title, orig_title, year, director)
    intel["wikipedia"] = wiki_data

    intel["elapsed_seconds"] = round(time.time() - start_time, 2)
    return intel


def main():
    parser = argparse.ArgumentParser(description="Unified Cinema Information & Intelligence Hub.")
    parser.add_argument("title", help="Film title to search")
    parser.add_argument("--orig-title", help="Original title")
    parser.add_argument("--year", type=int, help="Release year")
    parser.add_argument("--director", help="Director name")
    parser.add_argument("--doc", action="store_true", help="Force documentary search")
    parser.add_argument("--format", choices=["text", "json"], default="text")

    args = parser.parse_args()
    data = cinema_search(args.title, args.orig_title, args.year, args.director, is_doc_hint=args.doc)

    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        q = data["query"]
        print(f"\n🎬 {q['title']}" + (f" ({q['year']})" if q.get("year") else "") + (f" — {q['director']}" if q.get("director") else ""))
        if q.get("original_title"):
            print(f"   Titre original : {q['original_title']}")

        # IMDb
        imdb = data.get("imdb", {})
        if imdb:
            rating_str = f"⭐ {imdb.get('rating')}/10 ({imdb.get('votes'):,} votes)" if imdb.get("rating") else "Non noté"
            print(f"\n📌 IMDb : {rating_str} | Durée : {imdb.get('runtime_minutes')} min | Genres : {', '.join(imdb.get('genres', []))}")
            print(f"   Lien IMDb : https://www.imdb.com/title/{imdb.get('imdb_id')}/")

        # NFR
        if data.get("nfr"):
            n = data["nfr"]
            print(f"\n🏛️ National Film Registry (NFR) : Sélectionné en {n['induction_year']} (Catégorie : {n['film_type']})")

        # 1001 Films
        if data.get("one_thousand_one_films"):
            k = data["one_thousand_one_films"]
            print(f"\n📚 1001 Films à voir avant de mourir :")
            print(f"   {k['post_title']}")
            print(f"   {k['review'][:300]}...")

        # Muad'Dib Sci-Fi
        if data.get("muaddib_scifi"):
            m = data["muaddib_scifi"]
            print(f"\n🚀 Muad'Dib Sci-Fi & Fantastique :")
            print(f"   Titre fiche : {m['post_title']}")
            print(f"   Détails     :\n{m['review'][:350]}...")
            print(f"   Lien blog   : {m['url']}")

        # film-documentaire.fr
        if data.get("film_documentaire"):
            doc = data["film_documentaire"]["data"]
            print(f"\n🎥 film-documentaire.fr :")
            print(f"   Mots-clés : {', '.join(doc.get('keywords', []))}")
            if doc.get("festivals"):
                print(f"   Sélections : {doc['festivals'][0]}")

        # Wikipedia Synopsis
        wiki = data.get("wikipedia", {})
        if wiki.get("synopsis"):
            print(f"\n📖 Résumé & Synopsis Détaillé ({wiki.get('source_lang')}) :")
            print(wiki["synopsis"][:600] + ("..." if len(wiki["synopsis"]) > 600 else ""))
            print(f"   Source : {wiki.get('source_url')}")

        print(f"\n⏱️ Temps d'exécution : {data['elapsed_seconds']}s")


if __name__ == "__main__":
    main()
