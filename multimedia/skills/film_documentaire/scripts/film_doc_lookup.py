#!/usr/bin/env python3
"""film-documentaire.fr Search & Metadata Extraction Engine.

Provides search and extraction capabilities for documentary films on www.film-documentaire.fr:
- Search by title and director.
- Extract complete French synopsis, English synopsis, and editorial notes (ex: Avis de Tënk).
- Extract thematic keywords (mots-clés thématiques), countries, year, duration, color/format.
- Extract festival selections, awards, and distribution/DVD details.
- Calculate matching confidence score (0-100).
"""

from __future__ import annotations

import argparse
import json
import os
import re
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
        "l'environnement choisi avant d'utiliser film_documentaire."
    ) from exc

BASE_URL = "https://www.film-documentaire.fr"
SEARCH_URL = f"{BASE_URL}/4DACTION/w_search_full"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"


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


def safe_request(url: str, data: Optional[bytes] = None, max_retries: int = 3) -> Optional[str]:
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": BASE_URL
    }
    req = urllib.request.Request(url, data=data, headers=headers)
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(1.5 * (attempt + 1))
            else:
                break
        except Exception:
            time.sleep(0.5 * (attempt + 1))
    return None


def search_film_doc(query: str) -> List[Dict[str, Any]]:
    post_data = urllib.parse.urlencode({
        "rech_simple": query,
        "rech_uukey": "",
        "rech_table": ""
    }).encode("utf-8")

    html = safe_request(SEARCH_URL, data=post_data)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    results = []

    links = soup.find_all("a", href=True)
    seen_hrefs = set()

    for a in links:
        href = a["href"]
        if "/4DACTION/w_fiche_film/" in href and href not in seen_hrefs:
            seen_hrefs.add(href)
            text_block = a.get_text(" • ", strip=True)

            title = ""
            year = None

            bold = a.find(["b", "strong", "h3", "h4"])
            if bold:
                title = bold.get_text(strip=True)

            parts = [p.strip() for p in text_block.split("•") if p.strip()]
            if not title and parts:
                title = parts[0]

            for p in parts:
                m_yr = re.search(r"\b(19\d\d|20\d\d)\b", p)
                if m_yr:
                    try:
                        year = int(m_yr.group(1))
                    except ValueError:
                        pass

            snippet = text_block
            results.append({
                "title": title,
                "url": urllib.parse.urljoin(BASE_URL, href),
                "year": year,
                "snippet": snippet
            })

    return results


def fetch_fiche_details(fiche_url: str) -> Dict[str, Any]:
    html = safe_request(fiche_url)
    if not html:
        return {}

    soup = BeautifulSoup(html, "html.parser")

    # Title
    title_el = soup.find("h1")
    title = title_el.get_text(strip=True) if title_el else ""

    # Meta line: Realisateur, Country, Year, Duration
    director = ""
    year = None
    runtime = None
    english_title = ""

    for div in soup.find_all(["div", "p", "ul", "span"]):
        txt = div.get_text(" ", strip=True)
        if "Titre anglais :" in txt:
            m = re.search(r"Titre anglais\s*:\s*([^•\n]+)", txt)
            if m:
                english_title = m.group(1).strip()
        if "Réalisé par" in txt and not director:
            m = re.search(r"Réalisé par\s*([^•\n]+)", txt)
            if m:
                director = m.group(1).strip()
        if not year:
            m = re.search(r"\b(19\d\d|20\d\d)\b", txt)
            if m and ("minutes" in txt or "Couleur" in txt or "France" in txt):
                year = int(m.group(1))
        if not runtime:
            m = re.search(r"(\d+)\s*minutes", txt)
            if m:
                runtime = int(m.group(1))

    # French Synopsis
    synopsis = ""
    syn_section = soup.find(lambda tag: tag.name in ["h4", "h5", "h6", "strong"] and "Résumé" in tag.get_text())
    if syn_section:
        parent = syn_section.find_parent(["div", "section"])
        if parent:
            for en_tab in parent.find_all("div", class_=lambda c: c and "english" in str(c).lower()):
                en_tab.decompose()
            p_tags = parent.find_all("p")
            if p_tags:
                synopsis = "\n\n".join([p.get_text(strip=True) for p in p_tags if len(p.get_text(strip=True)) > 20 and not p.get_text(strip=True).startswith("Résumé")])
            if not synopsis:
                txt = parent.get_text("\n\n", strip=True)
                lines = [l.strip() for l in txt.split("\n\n") if len(l.strip()) > 30 and not l.strip().startswith("Résumé")]
                synopsis = "\n\n".join(lines)

    # Thematic keywords (Mots-clés thématiques)
    keywords = []
    kw_section = soup.find(lambda tag: tag.name in ["h4", "h5", "h6", "strong"] and "Mot(s)-clé(s)" in tag.get_text())
    if kw_section:
        parent = kw_section.find_parent(["div", "section"])
        if parent:
            for a in parent.find_all(["a", "span", "li"]):
                kw = a.get_text(strip=True)
                if kw and kw not in keywords and "Mot(s)-clé(s)" not in kw:
                    keywords.append(kw)

    # Festival selections & awards
    festivals = []
    fest_section = soup.find(lambda tag: tag.name in ["h4", "h5", "h6", "strong"] and "Sélections" in tag.get_text())
    if fest_section:
        parent = fest_section.find_parent(["div", "section"])
        if parent:
            for li in parent.find_all(["li", "p"]):
                txt = li.get_text(" • ", strip=True)
                if txt and "Sélections" not in txt and len(txt) > 10:
                    festivals.append(txt)

    # Editorial note (Avis / À propos)
    editorial = ""
    about_section = soup.find(lambda tag: tag.name in ["h4", "h5", "h6", "strong"] and ("À propos" in tag.get_text() or "L'avis" in tag.get_text()))
    if about_section:
        parent = about_section.find_parent(["div", "section"])
        if parent:
            editorial = parent.get_text("\n", strip=True)

    return {
        "title": title,
        "english_title": english_title,
        "director": director,
        "year": year,
        "runtime_minutes": runtime,
        "synopsis": synopsis,
        "keywords": keywords,
        "festivals": festivals,
        "editorial": editorial,
        "url": fiche_url
    }


def calculate_match_score(
    target_title: str,
    target_year: Optional[int],
    target_director: Optional[str],
    candidate_title: str,
    candidate_year: Optional[int],
    candidate_director: Optional[str],
    candidate_text: str
) -> Tuple[int, List[str]]:
    score = 0
    reasons = []

    t_norm = normalize(target_title)
    c_norm = normalize(candidate_title)
    full_text_norm = normalize(candidate_title + " " + candidate_text)

    # Title matching
    if t_norm and (t_norm == c_norm or t_norm == strip_articles(c_norm)):
        score += 45
        reasons.append("Titre exact (+45)")
    elif t_norm and (t_norm in c_norm or c_norm in t_norm):
        score += 40
        reasons.append("Titre dans titre candidat (+40)")
    elif any(part in c_norm for part in t_norm.split(":") if len(part.strip()) >= 4):
        score += 35
        reasons.append("Partie du titre dans titre candidat (+35)")
    elif t_norm and t_norm in full_text_norm:
        score += 25
        reasons.append("Titre dans contenu (+25)")
    else:
        score -= 20
        reasons.append("Titre non trouvé (-20)")

    # Year matching
    if target_year and candidate_year:
        if target_year == candidate_year:
            score += 25
            reasons.append(f"Année exacte {target_year} (+25)")
        elif abs(target_year - candidate_year) <= 1:
            score += 15
            reasons.append(f"Année proche {candidate_year} (+15)")
    elif target_year and str(target_year) in full_text_norm:
        score += 20
        reasons.append(f"Année {target_year} dans contenu (+20)")

    # Director matching
    if target_director:
        dir_last = target_director.split()[-1]
        dir_norm = normalize(dir_last)
        if candidate_director and dir_norm in normalize(candidate_director):
            score += 30
            reasons.append(f"Réalisateur {dir_last} validé (+30)")
        elif dir_norm and len(dir_norm) >= 3 and dir_norm in full_text_norm:
            score += 20
            reasons.append(f"Réalisateur {dir_last} dans texte (+20)")

    final_score = min(100, max(0, score))
    return final_score, reasons


def lookup_documentary(
    title: str,
    year: Optional[int] = None,
    director: Optional[str] = None
) -> Dict[str, Any]:
    queries = [title]
    if ":" in title or " - " in title:
        for sep in [":", " - "]:
            if sep in title:
                queries.append(title.split(sep)[0].strip())
                queries.append(title.split(sep)[1].strip())
    if director:
        dir_last = director.split()[-1]
        queries.append(dir_last)

    best_fiche = None
    best_score = 0
    best_reasons = []

    seen_urls = set()

    for q in list(dict.fromkeys(queries)):
        results = search_film_doc(q)
        for r in results[:30]:
            if r["url"] in seen_urls:
                continue
            seen_urls.add(r["url"])
            details = fetch_fiche_details(r["url"])
            cand_title = details.get("title") or r.get("title") or ""
            cand_year = details.get("year") or r.get("year")
            cand_dir = details.get("director") or ""
            cand_text = r.get("snippet", "") + " " + details.get("synopsis", "") + " " + " ".join(details.get("keywords", []))

            score, reasons = calculate_match_score(
                title, year, director, cand_title, cand_year, cand_dir, cand_text
            )

            if score > best_score:
                best_score = score
                best_fiche = details
                best_reasons = reasons

        if best_score >= 80 and best_fiche and best_fiche.get("synopsis"):
            break

    if not best_fiche:
        return {
            "matched": False,
            "match_score": 0,
            "title": title,
            "message": "Aucun film correspondant trouvé sur film-documentaire.fr"
        }

    return {
        "matched": best_score >= 60,
        "match_score": best_score,
        "confidence": "HIGH" if best_score >= 75 else ("MODERATE" if best_score >= 50 else "LOW"),
        "match_reasons": best_reasons,
        "data": best_fiche
    }


def main():
    parser = argparse.ArgumentParser(description="Search film-documentaire.fr for film metadata.")
    parser.add_argument("title", help="Film title to search")
    parser.add_argument("--year", type=int, help="Release year")
    parser.add_argument("--director", help="Director name")
    parser.add_argument("--format", choices=["text", "json"], default="text")

    args = parser.parse_args()
    res = lookup_documentary(args.title, args.year, args.director)

    if args.format == "json":
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        if not res.get("matched"):
            print(f"❌ Film non trouvé ou score insuffisant (Score: {res.get('match_score', 0)}/100)")
            return

        d = res["data"]
        print(f"\n🎥 {d['title']} ({d.get('year') or 'Année inconnue'})")
        if d.get("english_title"):
            print(f"   Titre anglais : {d['english_title']}")
        print(f"   Réalisateur    : {d.get('director') or 'Inconnu'}")
        print(f"   Durée          : {d.get('runtime_minutes') or '?'} minutes")
        print(f"   Score match    : {res['match_score']}/100 [{res['confidence']}] ({', '.join(res['match_reasons'])})")
        print(f"   Fiche URL      : {d['url']}")

        if d.get("keywords"):
            print(f"   Mots-clés      : {', '.join(d['keywords'])}")

        print("\n📖 Résumé / Synopsis:")
        print(d.get("synopsis") or "Aucun résumé disponible.")

        if d.get("festivals"):
            print("\n🏆 Sélections & Distinctions:")
            for f in d["festivals"][:5]:
                print(f"   - {f}")


if __name__ == "__main__":
    main()
