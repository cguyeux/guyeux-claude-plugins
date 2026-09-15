#!/usr/bin/env python3
"""Veille des appels a projets ouverts : sujet et date limite, sans instruire.

Interroge des portails agregateurs d'AAP pour reperer ce qui est ouvert ou a venir,
avant meme qu'un mail de financeur n'arrive. Ne touche jamais calls.tsv : c'est une
liste de candidats a evaluer, pas un registre instruit. Un dispositif qui merite
d'aller plus loin passe ensuite par le geste 1 du skill (calls.py add / set), avec
l'URL trouvee ici comme source de depart pour lire le reglement complet.

Sources integrees (voir references/sources.md pour le contrat de chacune) :
    appelsprojetsrecherche  portail agregateur francais (ANR, ADEME, ANRS MIE,
                            Inserm, Anses, INCa) ; filtrable par organisme
    eu-funding-tenders      portail officiel de la Commission europeenne (Horizon
                            Europe, ERC, EDIH, Digital Europe, LIFE, MSCA...) ;
                            pas de filtre par organisme (tout est geme par la CE)
    bpifrance               liste "Appels a projets et concours" de Bpifrance ;
                            pas de recherche plein texte cote serveur (filtrage
                            des mots-cles fait cote client sur titre+description)

Sous-commandes
    search    interroge une source (ou --source all), sujet + date limite par resultat
    due       raccourci : appels OUVERTS dont la cloture approche (N jours)

Zero dependance externe (stdlib seule) : urllib pour le HTTP (y compris le corps
multipart/form-data du portail europeen, encode a la main), re pour extraire les
champs du HTML retourne quand la source ne sert pas de JSON propre — voir
references/sources.md pour le contrat exact de chaque source.
"""

from __future__ import annotations

import argparse
import html as html_module
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import date, timedelta

USER_AGENT = "Mozilla/5.0 (compatible; aap-veille/1.0)"

_MONTHS_FR = {
    "janv": 1, "fevr": 2, "mars": 3, "avr": 4, "mai": 5, "juin": 6,
    "juil": 7, "aout": 8, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}


class SourceError(Exception):
    """Une source a echoue (reseau ou forme de reponse inattendue)."""


def _strip_accents(s: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _strip_tags(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    text = html_module.unescape(text)
    return re.sub(r"[ \t]+", " ", text).strip()


def _parse_french_date(text: str) -> date | None:
    """'16 nov. 2026, 13:00:00 UTC+1' -> date(2026, 11, 16). None si pas une date."""
    m = re.search(r"(\d{1,2})\s+([a-zA-Z]+)\.?\s+(\d{4})", _strip_accents(text.strip()))
    if not m:
        return None
    day, month_raw, year = m.groups()
    month = _MONTHS_FR.get(month_raw.lower()[:4].rstrip("."))
    if month is None:
        month = _MONTHS_FR.get(month_raw.lower()[:3])
    if month is None:
        return None
    try:
        return date(int(year), month, int(day))
    except ValueError:
        return None


def _parse_iso_date(text: str) -> date | None:
    """'2026-11-16T15:00:00.000+0000' -> date(2026, 11, 16)."""
    try:
        return date.fromisoformat(text[:10])
    except (ValueError, TypeError):
        return None


def _parse_dmy_date(text: str) -> date | None:
    """'21/09/2026' -> date(2026, 9, 21)."""
    try:
        d, m, y = text.strip().split("/")
        return date(int(y), int(m), int(d))
    except (ValueError, AttributeError):
        return None


def _sort_by_deadline(hits: list[CallHit], descending: bool) -> list[CallHit]:
    dated = [h for h in hits if h.deadline_date]
    undated = [h for h in hits if not h.deadline_date]
    dated.sort(key=lambda h: h.deadline_date, reverse=descending)
    return dated + undated


@dataclass
class CallHit:
    source: str
    title: str
    funder: str
    status: str          # open | upcoming | closed | unknown
    deadline_text: str   # tel qu'affiche par la source
    deadline_date: date | None
    url: str
    subject: str          # texte de description disponible, pour --full ou matching


def _http_post_form(url: str, data: dict[str, object]) -> bytes:
    body = urllib.parse.urlencode(data, doseq=True).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={
            "User-Agent": USER_AGENT,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read()
    except urllib.error.URLError as exc:
        raise SourceError(f"echec reseau vers {url} : {exc}") from exc


def _multipart_encode(fields: dict[str, str]) -> tuple[bytes, str]:
    """Encode des champs en multipart/form-data, un champ JSON par partie
    ("filename=blob" + Content-Type application/json), comme le fait le
    portail europeen. Stdlib pure, pas de dependance a `requests`."""
    boundary = "----aapveille" + uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        parts.append(
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="{name}"; filename="blob"\r\n'
            f'Content-Type: application/json\r\n\r\n'
            f'{value}\r\n'
        )
    parts.append(f'--{boundary}--\r\n')
    return "".join(parts).encode("utf-8"), f"multipart/form-data; boundary={boundary}"


def _http_post_multipart(url: str, fields: dict[str, str]) -> bytes:
    body, content_type = _multipart_encode(fields)
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={
            "User-Agent": USER_AGENT,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": content_type,
            "Accept": "application/json",
            "Referer": "https://ec.europa.eu/",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.read()
    except urllib.error.URLError as exc:
        raise SourceError(f"echec reseau vers {url} : {exc}") from exc


def _http_get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise SourceError(f"echec reseau vers {url} : {exc}") from exc


# ---------------------------------------------------------------------------
# Source 1 : appelsprojetsrecherche.fr (portail francais, ANR/ADEME/ANRS-MIE/
# Anses/INCa). Fragment HTML encapsule dans du JSON — voir references/sources.md.

APR_BASE_URL = "https://www.appelsprojetsrecherche.fr"

_APR_CARD_SPLIT = re.compile(r'<div class="col px-0 px-md-4[^"]*">\s*<div class="card-call-for-proposal')
_APR_TITLE_RE = re.compile(r'<h3 class="card-title[^"]*">(.*?)</h3>', re.S)
_APR_FUNDER_RE = re.compile(r'<p class="text-primary[^"]*">(.*?)</p>', re.S)
_APR_SUBJECT_RE = re.compile(r'<div class="card-text fs-5">(.*?)<div class="card-footer', re.S)
_APR_FOOTER_RE = re.compile(r'<div class="card-footer.*', re.S)
_APR_BADGE_RE = re.compile(r'class="badge[^"]*"\s*>\s*<span>(.*?)</span>', re.S)
_APR_HREF_RE = re.compile(r'href="(/appel/[^"]+)"')


def _parse_apr_cards(fragment_html: str) -> list[CallHit]:
    chunks = _APR_CARD_SPLIT.split(fragment_html)[1:]  # [0] est le prefixe avant la 1ere carte
    hits = []
    for chunk in chunks:
        title_m = _APR_TITLE_RE.search(chunk)
        funder_m = _APR_FUNDER_RE.search(chunk)
        subject_m = _APR_SUBJECT_RE.search(chunk)
        footer_m = _APR_FOOTER_RE.search(chunk)
        href_m = _APR_HREF_RE.search(chunk)
        if not (title_m and footer_m and href_m):
            continue  # carte mal formee : ignoree plutot que de planter la veille
        badge_m = _APR_BADGE_RE.search(footer_m.group(0))
        badge_text = _strip_tags(badge_m.group(1)) if badge_m else ""
        deadline = _parse_french_date(badge_text)
        if deadline is not None:
            status = "open"
        elif _strip_accents(badge_text.lower()).startswith("a venir"):
            status = "upcoming"
        elif "clos" in badge_text.lower():
            status = "closed"
        else:
            status = "unknown"
        hits.append(CallHit(
            source="appelsprojetsrecherche",
            title=_strip_tags(title_m.group(1)),
            funder=_strip_tags(funder_m.group(1)) if funder_m else "unknown",
            status=status,
            deadline_text=badge_text or "unknown",
            deadline_date=deadline,
            url=APR_BASE_URL + href_m.group(1),
            subject=_strip_tags(subject_m.group(1)) if subject_m else "",
        ))
    return hits


def search_appelsprojetsrecherche(terms: str, statuses: list[str], sort: str,
                                   partners: list[str], limit: int) -> list[CallHit]:
    data: dict[str, object] = {
        "call_for_proposal_search[terms]": terms,
        "call_for_proposal_search[sort]": sort,
    }
    if statuses:
        data["call_for_proposal_search[status][]"] = statuses
    if partners:
        data["call_for_proposal_search[partners][]"] = partners
    url = f"{APR_BASE_URL}/ajax/search-call-for-proposals?page=1&nbElementsPerPage={max(limit, 1)}"
    raw = _http_post_form(url, data)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SourceError("reponse non JSON depuis appelsprojetsrecherche.fr "
                           "(voir references/sources.md)") from exc
    if "call_for_proposals" not in payload:
        raise SourceError(f"reponse JSON sans le champ attendu 'call_for_proposals' : "
                           f"{list(payload)}")
    hits = _parse_apr_cards(payload["call_for_proposals"])
    total = payload.get("pagination", {}).get("total")
    if isinstance(total, int) and total > limit:
        print(f"# appelsprojetsrecherche : {total} resultats au total, {limit} affiches "
              f"(--limit pour en voir plus)", file=sys.stderr)
    return hits[:limit]


# ---------------------------------------------------------------------------
# Source 2 : EU Funding & Tenders Portal (Commission europeenne : Horizon
# Europe, ERC, EDIH, Digital Europe, LIFE, MSCA...). API JSON directe (search-api
# SEDIA), corps multipart/form-data — voir references/sources.md.

EU_SEARCH_URL = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"

EU_STATUS_CODES = {"upcoming": "31094501", "open": "31094502", "closed": "31094503"}
EU_STATUS_CODES_REV = {v: k for k, v in EU_STATUS_CODES.items()}
EU_SORT_FIELDS = {
    "applyClosingDate": "deadlineDate",
    "applyOpeningDate": "startDate",
    "publicationBeginDate": "startDate",  # pas de date de publication distincte cote EU
}
EU_DISPLAY_FIELDS = ["type", "identifier", "reference", "callccm2Id", "title", "status",
                      "caName", "projectAcronym", "startDate", "deadlineDate",
                      "deadlineModel", "frameworkProgramme", "typesOfAction"]


def search_eu_funding_tenders(terms: str, statuses: list[str], sort: str,
                               partners: list[str], limit: int) -> list[CallHit]:
    if partners:
        print("# eu-funding-tenders : --partners ignore, tout ce portail est gere "
              "par la Commission europeenne", file=sys.stderr)
    base, _, direction = sort.rpartition("-")
    field = EU_SORT_FIELDS.get(base, "startDate")
    order = "DESC" if direction == "desc" else "ASC"
    status_codes = [EU_STATUS_CODES[s] for s in statuses if s in EU_STATUS_CODES] \
        or list(EU_STATUS_CODES.values())
    query = {"bool": {"must": [
        {"terms": {"type": ["1", "2", "8"]}},
        {"terms": {"status": status_codes}},
        {"terms": {"DATASOURCE": ["SEDIA"]}},
        {"terms": {"language": ["en"]}},
    ]}}
    fields = {
        "sort": json.dumps({"order": order, "field": field}),
        "query": json.dumps(query),
        "languages": json.dumps(["en"]),
        "displayFields": json.dumps(EU_DISPLAY_FIELDS),
    }
    text = terms if terms else "***"
    url = (f"{EU_SEARCH_URL}?apiKey=SEDIA&text={urllib.parse.quote(text)}"
           f"&pageSize={max(limit, 1)}&pageNumber=1")
    raw = _http_post_multipart(url, fields)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SourceError("reponse non JSON depuis le EU Funding & Tenders Portal "
                           "(voir references/sources.md)") from exc
    if "results" not in payload:
        raise SourceError(f"reponse JSON sans le champ attendu 'results' : {list(payload)}")

    hits = []
    for r in payload["results"]:
        md = r.get("metadata", {})
        ident = (md.get("identifier") or [r.get("reference", "?")])[0]
        title = r.get("summary") or ident
        raw_status = (md.get("status") or [""])[0]
        status = EU_STATUS_CODES_REV.get(raw_status, "unknown")
        deadlines_raw = md.get("deadlineDate") or []
        deadlines = [_parse_iso_date(d) for d in deadlines_raw]
        deadlines = [d for d in deadlines if d]
        hits.append(CallHit(
            source="eu-funding-tenders",
            title=f"{title} ({ident})",
            funder="Commission européenne",
            status=status,
            deadline_text=", ".join(deadlines_raw) if deadlines_raw else "unknown",
            deadline_date=min(deadlines) if deadlines else None,
            url=r.get("url", ""),
            # l'API ne renvoie pas de description distincte du titre pour ce type
            # de contenu ; le vrai texte est sur la page /topic-details/<id>.
            subject=title,
        ))
    total = payload.get("totalResults")
    if isinstance(total, int) and total > limit:
        print(f"# eu-funding-tenders : {total} resultats au total, {limit} affiches "
              f"(--limit pour en voir plus)", file=sys.stderr)
    return hits[:limit]


# ---------------------------------------------------------------------------
# Source 3 : Bpifrance, liste "Appels a projets et concours". HTML statique
# pagine (Drupal Views), aucune recherche plein texte cote serveur — voir
# references/sources.md.

BPI_BASE_URL = "https://www.bpifrance.fr"
BPI_LIST_PATH = "/nos-appels-a-projets-concours"

_BPI_DATE_RE = re.compile(r'<span class="card-date">([^<]*)</span>')
_BPI_TITLE_RE = re.compile(r'<h3>\s*<a href="([^"]+)">([^<]*)</a>')
_BPI_DESC_RE = re.compile(r'<p><a href="[^"]+">([^<]*)</a></p>')
_BPI_RUBRIQUE_RE = re.compile(r'class="rubrique[^"]*">(.*?)</span>', re.S)


def search_bpifrance(terms: str, statuses: list[str], sort: str,
                      partners: list[str], limit: int) -> list[CallHit]:
    if partners:
        print("# bpifrance : --partners ignore, ce portail n'a qu'un seul financeur",
              file=sys.stderr)
    wanted_statuses = set(statuses) if statuses else {"open"}
    terms_norm = _strip_accents(terms.lower()) if terms else ""
    today = date.today()
    hits: list[CallHit] = []
    page = 0
    while len(hits) < limit and page < 30:  # garde-fou : jamais vu plus de 4 pages en pratique
        html_page = _http_get(f"{BPI_BASE_URL}{BPI_LIST_PATH}?page={page}")
        chunks = html_page.split('class="article-card card-our-project')[1:]
        if not chunks:
            break
        for chunk in chunks:
            title_m = _BPI_TITLE_RE.search(chunk)
            date_m = _BPI_DATE_RE.search(chunk)
            if not (title_m and date_m):
                continue  # carte mal formee : ignoree plutot que de planter la veille
            href, title = title_m.groups()
            title = _strip_tags(title)
            open_txt, _, close_txt = date_m.group(1).partition(" au ")
            open_date = _parse_dmy_date(open_txt)
            close_date = _parse_dmy_date(close_txt)
            if close_date and today > close_date:
                status = "closed"
            elif open_date and today < open_date:
                status = "upcoming"
            else:
                status = "open"
            if status not in wanted_statuses:
                continue
            desc_m = _BPI_DESC_RE.search(chunk)
            subject = _strip_tags(desc_m.group(1)) if desc_m else ""
            if terms_norm and terms_norm not in _strip_accents((title + " " + subject).lower()):
                continue
            hits.append(CallHit(
                source="bpifrance",
                title=title,
                funder="Bpifrance",
                status=status,
                deadline_text=close_txt.strip() or "unknown",
                deadline_date=close_date,
                url=BPI_BASE_URL + href,
                subject=subject,
            ))
            if len(hits) >= limit:
                break
        if len(chunks) < 9:  # taille de page habituelle : moins que ca = derniere page
            break
        page += 1
    if sort.startswith("applyClosingDate"):
        hits = _sort_by_deadline(hits, descending=sort.endswith("desc"))
    return hits[:limit]


SOURCES = {
    "appelsprojetsrecherche": search_appelsprojetsrecherche,
    "eu-funding-tenders": search_eu_funding_tenders,
    "bpifrance": search_bpifrance,
}


def _search_all(terms: str, statuses: list[str], sort: str,
                 partners: list[str], limit: int) -> list[CallHit]:
    hits: list[CallHit] = []
    for name, fn in SOURCES.items():
        try:
            hits.extend(fn(terms, statuses, sort, partners, limit))
        except SourceError as exc:
            print(f"# {name} : {exc}", file=sys.stderr)
    return hits


def _print_hit(h: CallHit, full: bool) -> None:
    deadline = h.deadline_date.isoformat() if h.deadline_date else h.deadline_text
    print(f"\n[{h.source}] [{h.status:8}] cloture {deadline:12}  {h.funder}")
    print(f"  {h.title}")
    print(f"  {h.url}")
    if h.subject:
        text = h.subject if full else (h.subject[:280] + ("…" if len(h.subject) > 280 else ""))
        print(f"  sujet : {text}")


def cmd_search(a) -> int:
    statuses = [s.strip() for s in a.status.split(",") if s.strip()]
    partners = [p.strip() for p in a.partners.split(",") if p.strip()] if a.partners else []
    terms = a.terms or ""
    if a.source == "all":
        hits = _search_all(terms, statuses, a.sort, partners, a.limit)
    else:
        try:
            hits = SOURCES[a.source](terms, statuses, a.sort, partners, a.limit)
        except SourceError as exc:
            sys.exit(str(exc))
    if a.json:
        print(json.dumps([{
            "source": h.source, "title": h.title, "funder": h.funder, "status": h.status,
            "deadline": h.deadline_date.isoformat() if h.deadline_date else None,
            "deadline_text": h.deadline_text, "url": h.url, "subject": h.subject,
        } for h in hits], ensure_ascii=False, indent=2))
        return 0
    if not hits:
        print("aucun resultat.")
        return 0
    for h in hits:
        _print_hit(h, a.full)
    print(f"\n{len(hits)} resultat(s). Un appel a instruire : calls.py add <key> "
          f"--name '...' --funder '...' --source page-appel, puis lire le reglement complet "
          f"(pas ce resume) avant tout verdict go/no-go.")
    return 0


def cmd_due(a) -> int:
    terms = a.terms or ""
    if a.source == "all":
        hits = _search_all(terms, ["open"], "applyClosingDate-asc", [], a.limit)
    else:
        try:
            hits = SOURCES[a.source](terms, ["open"], "applyClosingDate-asc", [], a.limit)
        except SourceError as exc:
            sys.exit(str(exc))
    today = date.today()
    horizon = today + timedelta(days=a.days)
    due = [(h.deadline_date, h) for h in hits
           if h.deadline_date and today <= h.deadline_date <= horizon]
    if not due:
        print(f"aucune cloture connue dans les {a.days} prochains jours"
              + (f" pour '{terms}'" if terms else "") + ".")
        return 0
    for deadline, h in sorted(due, key=lambda t: t[0]):
        d = (deadline - today).days
        print(f"J-{d:<4} {deadline.isoformat()}  [{h.source:24}] {h.funder:24} {h.title[:60]}")
        print(f"        {h.url}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    source_choices = [*SOURCES, "all"]

    q = s.add_parser("search", help="interroger une source, sujet + date limite")
    q.add_argument("--terms", default="", help="mots-cles (vide = tout)")
    q.add_argument("--status", default="open",
                    help="open,upcoming,closed (defaut open)")
    q.add_argument("--partners", default="",
                    help="filtrer par organisme(s) (uniquement appelsprojetsrecherche), "
                         "separes par des virgules (ex. 'ANR,ADEME'), noms exacts du portail")
    q.add_argument("--sort", default="applyClosingDate-asc",
                    choices=["publicationBeginDate-asc", "publicationBeginDate-desc",
                             "applyClosingDate-asc", "applyClosingDate-desc",
                             "applyOpeningDate-asc", "applyOpeningDate-desc"])
    q.add_argument("--source", default="appelsprojetsrecherche", choices=source_choices,
                    help="'all' interroge toutes les sources et concatene")
    q.add_argument("--limit", type=int, default=50)
    q.add_argument("--full", action="store_true", help="sujet integral, pas tronque a 280 car.")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_search)

    q = s.add_parser("due", help="appels ouverts dont la cloture approche")
    q.add_argument("--days", type=int, default=90)
    q.add_argument("--terms", default="")
    q.add_argument("--source", default="all", choices=source_choices)
    q.add_argument("--limit", type=int, default=200)
    q.set_defaults(func=cmd_due)

    a = p.parse_args()
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
