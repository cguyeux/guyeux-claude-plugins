---
name: tbmonitor-papers
description: >-
  Search the tbmonitor MCP server, a pre-indexed read-only SQLite mirror
  of the PubMed tuberculosis corpus (~330 000 papers spanning 1848 to
  present, ~81 % TB-specific, source 100 % PubMed). Exposes title,
  abstract, DOI, PubMed link, journal, publication date, plus authors /
  keywords / MeSH terms / publication types / author affiliations /
  reference list as JSON arrays directly queryable via `json_each()`.
  Sub-second response on filtered fulltext-style searches. The corpus now
  reaches back to the founding TB literature (dense from ~1945), so it can
  date drug introductions and surface pre-1995 primary sources that earlier
  corpus snapshots missed.

  Use when: pulling TB-specific papers by author, MeSH term, keyword,
  journal or year range; assembling a BibTeX list for a review or grant;
  verifying that a literature claim has prior coverage; cross-linking
  tbannotator strain results with the published literature about them;
  or building a quick state-of-the-art before falling back to lit-review
  for deeper systematic work.
argument-hint: "<topic | --author NAME | --mesh TERM | --since YYYY> [--bibtex]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbmonitor__execute_sql, mcp__tbmonitor__show_schema
---

# /tbmonitor-papers — TB literature search via tbmonitor MCP

Targeted, low-latency searches against the tbmonitor PubMed corpus.
Companion of `tbannotator-mcp`: tbannotator answers genome/strain
questions, tbmonitor answers literature questions about those genomes.

## Prerequisite — local MCP registration

The tbmonitor server is **separate** from tbannotator. Before this
skill works, register it locally:

```bash
claude mcp add --transport http --scope user \
  tbmonitor https://tbmonitor.82.64.250.114.nip.io/mcp
claude mcp list   # confirm 'tbmonitor: ... ✓ Connected'
```

The URL is currently a `nip.io` alias on a personal IP and **will
migrate to a permanent domain** — re-run the `add` (or edit
`~/.claude/.claude.json`) when that happens.

If the MCP tools `mcp__tbmonitor__execute_sql` and
`mcp__tbmonitor__show_schema` are not available, abort and tell the
user to register the server.

## Server contract (must respect)

- Read-only SQLite. **One** statement per `execute_sql` call
  (`SELECT` / `WITH` / `PRAGMA` / `EXPLAIN`).
- `max_rows` defaults to 100. Cap higher only when needed.
- **Hard rule from the server**: when the result represents paper
  records, the `SELECT` list MUST include `title`, `doi`, `pdf_link`,
  `abstract`. Add other columns the user asks for.
- No FTS5 index — fulltext is `LIKE %...%`. Always combine with a
  `publication_date >= 'YYYY-MM-DD'` filter so SQLite uses
  `idx_papers_publication_date`. Without a date filter, full corpus
  scan still runs in ~0.5 s but degrades under load.

## Table — `papers` (330 240 rows, PubMed, 1848-04-01 → 2026)

(A second table `crawler_state` holds ingestion bookkeeping only — ignore it.)


| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Internal ID |
| `source` | TEXT | 100 % `pubmed` |
| `source_id` | TEXT | PMID (100 % numeric) |
| `title` | TEXT | Required in paper SELECT |
| `abstract` | TEXT | Required; ~57 % populated (pre-1980 papers usually have none — search `title` for old work) |
| `doi` | TEXT | Required; ~58 % populated (older papers predate DOIs) |
| `pdf_link` | TEXT | Required; 100 % populated — always `https://pubmed.ncbi.nlm.nih.gov/<source_id>/`, a PubMed URL, not a real PDF |
| `authors` | TEXT (JSON array of strings) | `["Last First", ...]`; 100 % valid JSON |
| `publication_date` | TEXT (`YYYY-MM-DD`) | 100 % normalised; range 1848-04-01 → present, dense from ~1945 (streptomycin era) |
| `keywords` | TEXT (JSON array) | Always populated, sorted alphabetically. Internal tag `"COMBINED"` is in ~99 % of rows but NOT necessarily first — filter by value, never by position |
| `journal` | TEXT | Full journal name (long, includes subtitle) |
| `reference_list` | TEXT (JSON array of raw citation strings) | Not parsed into DOI/author |
| `mesh_terms` | TEXT (JSON array) | Format `"Term/qualifier"` (e.g. `"Mycobacterium tuberculosis/genetics"`) |
| `publication_types` | TEXT (JSON array) | `"Journal Article"`, `"Review"`, `"Randomized Controlled Trial"`, ... |
| `author_affiliations` | TEXT (JSON array, positionally aligned with `authors`) | |
| `article_license` | TEXT | Sparse free-text copyright / CC string; mostly NULL or empty, present mainly on recent papers — a weak OA hint only, not a clean enum |
| `entry_date` | TIMESTAMP | When the row was loaded into tbmonitor |

All six list-valued columns (`authors`, `keywords`, `mesh_terms`,
`publication_types`, `reference_list`, `author_affiliations`) are
**100 % valid JSON** → `json_each()` / `json_extract()` always work.

Indexes: on `publication_date` (two) and on `(source, source_id)`.

## Recipe book

### A. By author (LIKE on JSON-serialised string — fast, ~0.6 s)

```sql
SELECT title, doi, pdf_link, abstract, publication_date, journal
FROM papers
WHERE authors LIKE '%Guyeux%'
ORDER BY publication_date DESC;
```

Refine with a second `LIKE` for an initial when the surname is common:
`AND authors LIKE '%Smith J%'`.

### B. Strict author match via `json_each` (slower but exact)

```sql
SELECT p.title, p.doi, p.pdf_link, p.abstract, p.publication_date
FROM papers p, json_each(p.authors) je
WHERE je.value = 'Christophe Guyeux'
ORDER BY p.publication_date DESC;
```

### C. By MeSH term (use `json_each` join — clean, ~0.3 s)

```sql
SELECT p.title, p.doi, p.pdf_link, p.abstract, p.publication_date
FROM papers p
JOIN json_each(p.mesh_terms) je
  ON je.value = 'Mycobacterium tuberculosis/genetics'
WHERE p.publication_date >= '2024-01-01'
  AND p.abstract IS NOT NULL
ORDER BY p.publication_date DESC
LIMIT 50;
```

### D. Fulltext — keyword in title or abstract (always with date filter)

```sql
SELECT title, doi, pdf_link, abstract, publication_date, journal
FROM papers
WHERE publication_date >= '2023-01-01'
  AND (title LIKE '%bedaquiline%' OR abstract LIKE '%bedaquiline%')
  AND abstract IS NOT NULL
ORDER BY publication_date DESC
LIMIT 50;
```

### E. By keyword tag (the curated `keywords` field)

Filter the meta-tag `"COMBINED"`:

```sql
SELECT p.title, p.doi, p.pdf_link, p.abstract, p.publication_date
FROM papers p, json_each(p.keywords) je
WHERE je.value = 'MDR-TB'
  AND je.value != 'COMBINED'
  AND p.publication_date >= '2024-01-01'
ORDER BY p.publication_date DESC
LIMIT 50;
```

### F. By journal

```sql
SELECT title, doi, pdf_link, abstract, publication_date, journal
FROM papers
WHERE journal LIKE '%Tuberculosis (Edinburgh%'
  AND publication_date >= '2024-01-01'
ORDER BY publication_date DESC;
```

### G. Reviews / RCTs / meta-analyses only

```sql
SELECT p.title, p.doi, p.pdf_link, p.abstract, p.publication_date
FROM papers p
JOIN json_each(p.publication_types) je ON je.value = 'Systematic Review'
WHERE p.publication_date >= '2022-01-01'
  AND (p.abstract LIKE '%lineage%' OR p.title LIKE '%lineage%')
ORDER BY p.publication_date DESC;
```

### H. Combine tbmonitor with tbannotator results

After tbannotator returns a lineage code or strain set, look for the
literature about that lineage:

```sql
SELECT title, doi, pdf_link, abstract, publication_date
FROM papers
WHERE publication_date >= '2018-01-01'
  AND (abstract LIKE '%L4.15%' OR abstract LIKE '%lineage 4.15%'
       OR title    LIKE '%L4.15%' OR title    LIKE '%lineage 4.15%')
ORDER BY publication_date DESC;
```

### I. References cited by a paper (raw text, not structured)

```sql
SELECT je.value AS citation
FROM papers p, json_each(p.reference_list) je
WHERE p.doi = '10.1016/j.tube.2023.102376'
LIMIT 50;
```

`reference_list` entries are free-text citations — extract DOIs with
a regex client-side (`10\.\d{4,9}/[^\s",]+`) when needed.

### J. Founding / historical literature & drug-introduction dating

The corpus now spans 1848–present (dense from ~1945), so it can bound when a
drug or concept first surfaced in the TB literature — a query that failed on
earlier snapshots floored at 1995/2021. Old papers usually have no abstract,
so search `title` and do **not** require `abstract IS NOT NULL`:

```sql
-- earliest literature mention of a drug (title), + yearly acceleration
SELECT MIN(publication_date) AS first_seen, COUNT(*) AS n
FROM papers
WHERE lower(title) LIKE '%bedaquiline%';

SELECT substr(publication_date,1,4) AS yr, COUNT(*) AS n
FROM papers
WHERE lower(title) LIKE '%pretomanid%' OR lower(abstract) LIKE '%pretomanid%'
GROUP BY yr ORDER BY yr;
```

A `MIN(publication_date)` is a *lower bound on literature coverage*, not the
true clinical-introduction date; for first-line drugs (pre-1966) cross-check
a programmatic source (WHO GDF/GLC). The deep corpus still makes this far more
informative than the 2021-floored `flux` snapshot, which made every
antitubercular look "introduced before 2021".

## Modes of invocation

| Mode | Effect |
|---|---|
| `/tbmonitor-papers <topic>` | Fulltext search on title+abstract since 2020, top 30 most recent |
| `/tbmonitor-papers --author "<name>"` | Author search (LIKE), ordered by date |
| `/tbmonitor-papers --mesh "<term>"` | MeSH term join, since 2020, top 50 |
| `/tbmonitor-papers --since YYYY` | Restrict any of the above to publications since YYYY |
| `--bibtex` (modifier) | Emit a BibTeX block usable for `references.bib` |

When invoked with `--bibtex`, build entries like:

```
@article{<firstauthor><year><firstword>,
  title   = {{<title>}},
  author  = {<authors joined by " and ">},
  journal = {<journal>},
  year    = {<year>},
  doi     = {<doi>},
  url     = {<pdf_link>},
}
```

(`pdf_link` is often a PubMed URL, not a real PDF — keep it as `url`,
not `pdf`.)

## Output formatting

For paper lists, default to a markdown table:

| Year | Authors (first) | Title | Journal | DOI |
|---|---|---|---|---|
| 2026-01-05 | Guyeux et al. | Migrations and Tuberculosis... | Tuberculosis (Edinburgh) | [10.1016/j.tube.2026.102734](https://doi.org/10.1016/j.tube.2026.102734) |

For each row, surface the abstract on demand (collapsible / appended
section) — tbmonitor returns it always, the user does not always
need it inline.

## Composition with other skills

| Companion | Why |
|---|---|
| `tbannotator-mcp` | The genomic counterpart — strains, SNPs, lineages, trees |
| `lit-review` | When systematic, multi-source, BibTeX-cumulative review is needed; tbmonitor becomes one of its sources |
| `claim-check` | Use tbmonitor first to verify a TB claim has literature backing |
| `pubmed-database` | Fall back here for non-TB topics or full E-utilities features |
| `bib-check` | Validate a manuscript's references against tbmonitor (DOI / title match) |
| `reviewer-response` | Find supporting refs when answering a reviewer demanding citations |
| `pubtator`, `europe-pmc`, `bioc-pmc` | Use these for full-text mining, NER, preprints — tbmonitor is abstract-only |

## Caveats

- **No FTS** → cap fulltext queries with a `publication_date` filter.
- **Sparse abstracts on old work**: only ~57 % of rows have an abstract,
  and pre-1980 papers almost never do. Requiring `abstract IS NOT NULL`
  silently drops the historical record — for old/founding literature search
  `title` and omit that filter.
- **Not 100 % TB**: ~81 % of rows mention tuberculosis/Mycobacterium; broad
  PubMed-TB queries on generic terms can surface adjacent non-TB papers.
- **`reference_list`** is unstructured text — DOI extraction is on the
  client.
- **`pdf_link`** is always the PubMed URL (`/<PMID>/`), not a real PDF.
- **`COMBINED`** keyword is an internal tag present in ~99 % of rows at a
  variable position; exclude it by value (`je.value != 'COMBINED'`), never
  assume it is first.
- **Snapshot** vs **live**: the corpus is a crawl (max date drifts; it
  reached 2026-06-11 at last check). Confirm with the user whether the
  corpus date matters before reporting counts that may drift.
- **Auth**: endpoint currently open at the `nip.io` URL above. If the
  deployment migrates to an auth-protected URL, update the registration
  accordingly.

## End-of-run

After producing results, briefly state:
- N papers returned, date range covered, query used
- Whether a BibTeX block was emitted (and where it should go)
- Suggested next step (e.g. "run `/lit-review <topic> --wide` for a
  full systematic pass" or "feed top-3 abstracts into
  `claim-check`").
