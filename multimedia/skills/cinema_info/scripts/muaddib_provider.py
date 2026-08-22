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

            # Check matching title
            if (t_norm and t_norm in p_norm) or (o_norm and o_norm in p_norm):
                if not year or str(year) in p_norm or (abs(year - 1900) < 150):
                    # Fetch direct post page for complete text
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
