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

            if any(bad in p_text for bad in ["Aucun message correspondant", "triés par pertinence pour la requête"]):
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
