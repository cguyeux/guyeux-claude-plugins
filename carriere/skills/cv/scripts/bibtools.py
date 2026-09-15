#!/usr/bin/env python3
"""Lecture, écriture et normalisation des BibTeX du CV de C. Guyeux.

Module commun aux outils du skill `cv`. Il connaît les conventions réelles du
dépôt `~/docs/cv/` et rien d'autre :

- `references/journals.bib` ne contient que des `@article`, `references/conferences.bib`
  que des `@inproceedings` ;
- chaque entrée liste ses champs par ordre alphabétique, un par ligne, sur le
  modèle de l'entrée `modele` présente en tête de chaque fichier ;
- la clé vaut initiales des auteurs + année sur deux chiffres + `:ij` (revue) ou
  `:ip` (conférence), un suffixe numérique départageant les collisions ;
- `affiliations.txt` porte une ligne `Nom, Prénom $ Affiliation $ Pays` par
  auteur, et `all.py` s'arrête brutalement si un auteur y manque.

Le parseur ne cherche pas à couvrir BibTeX en général : il compte les accolades,
ce qui suffit sur ces deux fichiers et évite la fragilité des `split()` en
chaîne de `all.py`.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

CV_DIR = Path.home() / "docs" / "cv"
JOURNALS_BIB = CV_DIR / "references" / "journals.bib"
CONFERENCES_BIB = CV_DIR / "references" / "conferences.bib"
AFFILIATIONS = CV_DIR / "affiliations.txt"

MONTHS_EN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Champs de l'entrée `modele`, dans l'ordre où le dépôt les écrit.
ARTICLE_FIELDS = [
    "abstract", "arxiv", "author", "category", "dixCitations", "doi", "funds",
    "hal", "journal", "keywords", "month", "note", "number", "order", "page",
    "publisher", "publiweb", "rank", "researchgate", "title", "url", "volume",
    "web", "year",
]

INPROCEEDINGS_FIELDS = [
    "abstract", "acronym", "alphabetic", "arxiv", "author", "best", "booktitle",
    "category", "city", "country", "day", "dixCitations", "doi", "editor",
    "hal", "keywords", "month", "note", "pages", "pdf", "poster", "presented",
    "proc", "publisher", "publiweb", "rank", "researchgate", "selection",
    "title", "volume", "web", "year",
]

# Champs sans lesquels le canevas Publiweb produit par all.py est inutilisable.
REQUIRED_FOR_PUBLIWEB = {
    "article": ["title", "author", "journal", "category", "year", "abstract", "doi"],
    "inproceedings": ["title", "author", "booktitle", "acronym", "category",
                      "year", "month", "day", "city", "country", "abstract"],
}

PUBLIWEB_VALUES = {"True", "False", "En cours"}


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #

@dataclass
class Entry:
    """Une entrée BibTeX du CV."""

    kind: str                       # "article" ou "inproceedings"
    key: str
    fields: dict[str, str] = field(default_factory=dict)
    raw: str = ""                   # texte source, tel quel
    source: Path | None = None

    def get(self, name: str, default: str = "") -> str:
        return self.fields.get(name, default)

    @property
    def authors(self) -> list[str]:
        """Auteurs au format `Nom, Prénom`, dans l'ordre de signature."""
        value = self.get("author").strip()
        if not value:
            return []
        return [a.strip() for a in re.split(r"\s+and\s+", value) if a.strip()]

    @property
    def publiweb(self) -> str:
        return self.get("publiweb").strip()

    @property
    def declared_in_publiweb(self) -> bool:
        """Reproduit la logique de `all.py` : `En cours` compte comme déclaré."""
        value = self.publiweb
        if value == "En cours":
            return True
        return value == "True"

    def to_bibtex(self) -> str:
        order = ARTICLE_FIELDS if self.kind == "article" else INPROCEEDINGS_FIELDS
        known = [f for f in order if f in self.fields]
        extra = sorted(f for f in self.fields if f not in order)
        lines = [f"@{self.kind}{{{self.key},"]
        for name in known + extra:
            lines.append(f"  {name} = {{{self.fields[name]}}},")
        lines.append("}")
        return "\n".join(lines)


def parse_bib(path: Path) -> list[Entry]:
    """Découpe un .bib en entrées, par comptage d'accolades."""
    text = path.read_text(encoding="utf-8")
    entries: list[Entry] = []
    for match in re.finditer(r"^@(\w+)\s*\{", text, re.MULTILINE):
        kind = match.group(1).lower()
        start = match.end()
        depth = 1
        pos = start
        while pos < len(text) and depth:
            if text[pos] == "{":
                depth += 1
            elif text[pos] == "}":
                depth -= 1
            pos += 1
        body = text[start:pos - 1]
        key = body.split(",", 1)[0].strip()
        entries.append(
            Entry(kind=kind, key=key, fields=_parse_fields(body),
                  raw=text[match.start():pos], source=path)
        )
    return entries


def _parse_fields(body: str) -> dict[str, str]:
    """Extrait les `nom = {valeur}` d'un corps d'entrée, valeurs multilignes comprises."""
    fields: dict[str, str] = {}
    for match in re.finditer(r"(?m)^\s*([A-Za-z][\w-]*)\s*=\s*\{", body):
        name = match.group(1)
        start = match.end()
        depth = 1
        pos = start
        while pos < len(body) and depth:
            if body[pos] == "{":
                depth += 1
            elif body[pos] == "}":
                depth -= 1
            pos += 1
        value = body[start:pos - 1]
        fields[name] = re.sub(r"\s+", " ", value).strip()
    return fields


def load_all() -> list[Entry]:
    """Toutes les entrées des deux .bib, `modele` exclu."""
    entries = []
    for path in (JOURNALS_BIB, CONFERENCES_BIB):
        if path.exists():
            entries.extend(e for e in parse_bib(path) if e.key != "modele")
    return entries


# --------------------------------------------------------------------------- #
# Affiliations
# --------------------------------------------------------------------------- #

def load_affiliations() -> dict[str, tuple[str, str]]:
    """`Nom, Prénom` -> (affiliation, pays)."""
    result: dict[str, tuple[str, str]] = {}
    if not AFFILIATIONS.exists():
        return result
    for line in AFFILIATIONS.read_text(encoding="utf-8").splitlines():
        if " $ " not in line:
            continue
        parts = [p.strip() for p in line.split(" $ ")]
        if len(parts) >= 3:
            result[parts[0]] = (parts[1], parts[2])
    return result


def add_affiliation(name: str, institution: str, country: str) -> bool:
    """Insère une ligne dans `affiliations.txt` en gardant le tri alphabétique.

    Renvoie False si le nom y figure déjà.
    """
    lines = AFFILIATIONS.read_text(encoding="utf-8").splitlines()
    for line in lines:
        if line.split(" $ ")[0].strip() == name:
            return False
    new_line = f"{name} $ {institution} $ {country}"
    key = _sort_key(name)
    position = len(lines)
    for index, line in enumerate(lines):
        if " $ " not in line:
            continue
        if _sort_key(line.split(" $ ")[0].strip()) > key:
            position = index
            break
    lines.insert(position, new_line)
    AFFILIATIONS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def _sort_key(name: str) -> str:
    return _strip_accents(name).lower()


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


# --------------------------------------------------------------------------- #
# Clés
# --------------------------------------------------------------------------- #

def make_key(authors: list[str], year: str, kind: str, existing: set[str]) -> str:
    """Clé maison : initiales des noms + année sur 2 chiffres + `:ij` / `:ip`.

    Le nom composé « Antar Soutou » donne `as` (une initiale par mot), ce qui
    reproduit les clés déjà en place comme `aangcs25:ige` ou `pdlg26:ip`.
    """
    initials = ""
    for author in authors:
        family = author.split(",")[0].strip()
        for word in re.split(r"[\s'-]+", family):
            if word:
                initials += _strip_accents(word)[0].lower()
    suffix = "ij" if kind == "article" else "ip"
    stem = f"{initials}{str(year)[-2:]}:{suffix}"
    if stem not in existing:
        return stem
    for n in range(2, 20):
        candidate = f"{initials}{str(year)[-2:]}:{suffix}{n}"
        if candidate not in existing:
            return candidate
    raise RuntimeError(f"impossible de forger une clé libre à partir de {stem}")


# --------------------------------------------------------------------------- #
# Doublons
# --------------------------------------------------------------------------- #

def normalize_title(title: str) -> str:
    text = _strip_accents(title).lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def normalize_doi(doi: str) -> str:
    doi = doi.strip().lower()
    doi = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", doi)
    return doi.rstrip("/")


def find_duplicates(entries: list[Entry], title: str, doi: str = "") -> list[Entry]:
    """Entrées déjà présentes portant ce DOI ou ce titre."""
    hits = []
    target_title = normalize_title(title)
    target_doi = normalize_doi(doi) if doi else ""
    for entry in entries:
        if target_doi and normalize_doi(entry.get("doi")) == target_doi:
            hits.append(entry)
        elif target_title and normalize_title(entry.get("title")) == target_title:
            hits.append(entry)
    return hits


# --------------------------------------------------------------------------- #
# Écriture
# --------------------------------------------------------------------------- #

def append_entry(entry: Entry) -> Path:
    """Ajoute une entrée en fin de fichier, séparée par une ligne vide."""
    path = JOURNALS_BIB if entry.kind == "article" else CONFERENCES_BIB
    text = path.read_text(encoding="utf-8").rstrip("\n")
    path.write_text(text + "\n\n\n" + entry.to_bibtex() + "\n", encoding="utf-8")
    return path


def blank_entry(kind: str) -> Entry:
    """Entrée neuve, tous les champs du modèle présents et vides."""
    fields_order = ARTICLE_FIELDS if kind == "article" else INPROCEEDINGS_FIELDS
    fields = {name: "" for name in fields_order}
    for name in ("dixCitations", "hal", "researchgate", "alphabetic", "best",
                 "poster", "presented"):
        if name in fields:
            fields[name] = "False"
    if "selection" in fields:
        fields["selection"] = "Full"
    fields["category"] = "ACL" if kind == "article" else "ACTI"
    fields["publiweb"] = "False"
    return Entry(kind=kind, key="", fields=fields)


# --------------------------------------------------------------------------- #
# Échappement LaTeX
# --------------------------------------------------------------------------- #

# Champs recopiés tels quels dans les .tex générés : ils doivent être LaTeX-safe.
# Le dépôt écrit déjà « 46.9\% » ou « Computers \& Security » dans les .bib.
ESCAPABLE_FIELDS = ("title", "journal", "booktitle", "publisher", "note",
                    "abstract", "keywords", "acronym", "editor", "rank")


def latex_escape(text: str) -> str:
    """Échappe & % # _ s'ils ne le sont pas déjà. Laisse le reste intact.

    N'échappe pas les accolades ni les antislashs : certaines valeurs du dépôt
    portent volontairement du LaTeX (`M\\`{e}rieux`, `\\emph{}`).
    """
    return re.sub(r"(?<!\\)([&%#_])", r"\\\1", text)


def escape_entry(entry: "Entry") -> None:
    """Applique `latex_escape` aux champs rendus, sur place."""
    for name in ESCAPABLE_FIELDS:
        if entry.fields.get(name):
            entry.fields[name] = latex_escape(entry.fields[name])
