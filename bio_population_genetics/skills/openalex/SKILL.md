---
name: openalex
description: >-
  Query OpenAlex — the fully open scholarly knowledge graph (307M works,
  118M authors, 124k institutions, 281k sources, 65k concepts, 4.5k topics — April 2026 snapshot)
  published by OurResearch
  as the successor to Microsoft Academic Graph. Free REST API with
  email-based polite pool, CC0 metadata, and bulk dumps. The reference
  bibliometric substrate for lit-reviews, co-author-network analysis,
  institution mapping, and concept-based discovery — complementary to
  PubMed/Europe PMC (which have biomedical focus) and to Google Scholar
  (which has no API).

  Use when: building a literature review from a topic query, mapping
  co-authorship networks around an MTBC lineage or a paper, listing
  all publications of a given lab or researcher, resolving institution
  IDs across publications, computing citation metrics without
  institutional Web of Science access, or enriching a manuscript
  bibliography with concept / topic tags.
---

# OpenAlex — Open Scholarly Knowledge Graph

## Overview

**OpenAlex** is the free, fully open scholarly knowledge graph produced
by **OurResearch** (the nonprofit behind **Unpaywall**), led by
**Jason Priem** and colleagues. It launched on **1 January 2022** as
the direct successor to the **Microsoft Academic Graph (MAG)** when
Microsoft discontinued MAG, and has since become the de-facto
open-science replacement for expensive closed citation databases
(Web of Science, Scopus).

OpenAlex indexes (verified April 2026 via REST API):
**307 million works** (journal articles, books, preprints, datasets,
theses), **118 million unique authors**, **124,000 institutions**,
**281,000 sources** (journals, repositories), **65,000 Wikidata-linked
concepts** (legacy, stable since launch), and **4,516 topics** (the
new hierarchical taxonomy replacing concepts). The database grows
rapidly — these numbers are ~50%+ higher than at the 2022 launch, and
~3× higher for authors and sources. Always re-fetch `meta.count` from
the API when citing absolute counts in a manuscript.

- **Reference**: Priem J., Piwowar H., Orr R. *OpenAlex: A fully-open
  index of scholarly works, authors, venues, institutions, and
  concepts.* **arXiv** 2205.01833 (2022).
- **Documentation**: `https://docs.openalex.org/`
- **API base**: `https://api.openalex.org/`
- **Web interface**: `https://openalex.org/`
- **Blog / changelog**: `https://blog.openalex.org/`
- **License**: **CC0** — public domain metadata (completely unrestricted
  reuse including commercial)
- **Rate limit**: 100,000 requests per day + 10/sec, keyed to your API key

> [!IMPORTANT]
> **OpenAlex now requires an API key on every request** — keyless calls
> are rejected (HTTP 409/429). The old keyless "polite pool" via a `mailto`
> query parameter is gone: **do not send `mailto`** to `api.openalex.org`.
> Pass the key as the `api_key` query parameter instead. Get a free key at
> `https://openalex.org/` (account settings). In an environment that injects
> it, read `OPENALEX_API_KEY`; never hard-code a key in the skill or an
> artifact.

## Why it matters for MTBC × anthropology

Your seminar foregrounds a "150 000 articles" text-mining corpus
(from the session's context on your research). OpenAlex is the
**logical substrate** for that corpus. Specific uses:

1. **Topic-based lit-review at scale.** A single query on OpenAlex
   can retrieve all publications tagged with a concept like
   *Mycobacterium tuberculosis*, *ancient DNA*, or
   *phylogeography* — instantly, with CC0 metadata.
2. **Co-authorship network mapping.** OpenAlex exposes author IDs,
   institution IDs, and co-authorship edges. You can build a
   network graph of everyone who has published on *M. bovis* in
   the last 10 years in a few minutes — useful for targeting
   collaborators, identifying review candidates, or building a
   slide on your field's community structure.
3. **Institution resolution.** Each work lists institutional
   affiliations with ROR IDs. You can filter publications by
   **Max Planck Institute Leipzig**, **Institut Pasteur**, or
   **UCL** without string-matching freeform affiliation text.
4. **Concept discovery.** Each work is tagged with up to ~10
   concepts (hierarchical, Wikidata-linked). Useful for discovering
   papers you would not find with a keyword search alone.
5. **Auditable bibliometry.** Unlike Web of Science or Scopus, the
   metadata are open — anyone can reproduce your figures.

OpenAlex is the **bibliographic layer** of your constellation,
complementary to the biomedical-focused **Europe PMC** / **PubMed**
and to the pathogen-focused **spaam-community** meta-index.

## Core entities

OpenAlex organises the scholarly world into **six first-class entity
types**, each with its own endpoint:

| Entity | Endpoint | Count (mid-2024) | Content |
|---|---|---|---|
| **Works** | `/works` | **~307M** | Papers, books, preprints, datasets, etc. |
| **Authors** | `/authors` | **~118M** | Disambiguated author identities |
| **Sources** | `/sources` | **~281k** | Journals, conferences, repositories |
| **Institutions** | `/institutions` | **~124k** | Universities, labs, companies (with ROR IDs) |
| **Topics** | `/topics` | **~4,516** | Hierarchical topic clustering (the new taxonomy) |
| **Concepts** | `/concepts` | ~65k | Wikidata-linked subject tags (legacy, being replaced by Topics) |
| **Publishers** | `/publishers` | — | Publishing entities |
| **Funders** | `/funders` | — | Funding organisations with grants |

> [!NOTE]
> OpenAlex is **migrating from "Concepts" to "Topics"**. As of 2024–2025,
> both are available. For new work, prefer **Topics** (they are
> better-defined, hierarchical, and maintained). Cite the migration
> note in your Methods if precision matters.

### Key work fields

Selected useful fields of a Work object:

| Field | Meaning |
|---|---|
| `id` | OpenAlex stable ID (e.g. `W2741809807`) |
| `doi` | DOI |
| `title` | Paper title |
| `publication_year`, `publication_date` | Publication metadata |
| `type` | `article`, `book`, `preprint`, `dataset`, … |
| `authorships` | List of author + institution affiliations |
| `primary_location`, `locations` | Where the work appears (venues) |
| `open_access` | OA status, URL to free full text |
| `topics`, `primary_topic` | Hierarchical topics |
| `concepts` | Legacy concept tags (still populated) |
| `cited_by_count` | Number of citations |
| `referenced_works` | Works this paper cites (outgoing links) |
| `related_works` | Similar works |
| `abstract_inverted_index` | **Abstract as positional index** (due to copyright considerations) |
| `sustainable_development_goals` | UN SDG tags |

**Important**: the `abstract_inverted_index` is a positional index,
not the raw text. You must reconstruct the abstract from positions
before running NLP on it (a 5-line Python helper).

## Data access

### Option A — REST API (recommended for targeted queries)

API key required on every request (do NOT send `mailto`):

```python
import os, requests

API_KEY = os.environ["OPENALEX_API_KEY"]   # injected; never hard-code
BASE = "https://api.openalex.org"

def openalex(path, **params):
    params["api_key"] = API_KEY            # keyed access; no mailto
    r = requests.get(f"{BASE}{path}", params=params, timeout=60)
    r.raise_for_status()
    return r.json()

# Search for Mycobacterium tuberculosis phylogeography papers
r = openalex(
    "/works",
    search="Mycobacterium tuberculosis phylogeography",
    per_page=200,
)
for w in r["results"]:
    print(w["id"], w["publication_year"], w["title"])
```

### Option B — Filter-based queries (canonical form)

OpenAlex's API supports rich filters via the `filter` parameter, e.g.:

```python
# All papers citing a specific work, from 2020–2024, English only
r = openalex(
    "/works",
    filter="cites:W2741809807,publication_year:2020-2024,language:en",
    per_page=200,
)
```

Multiple filters are comma-separated; the syntax is documented at
`docs.openalex.org/api-entities/works/filter-works`.

### Option C — Pagination

For more than 200 results, use **cursor pagination** (efficient) or
**offset pagination** (for small result sets):

```python
cursor = "*"
all_works = []
while cursor:
    r = openalex(
        "/works",
        filter="concepts.id:C23498923",     # M. tuberculosis concept
        per_page=200,
        cursor=cursor,
    )
    all_works.extend(r["results"])
    cursor = r["meta"].get("next_cursor")
    if not r["results"]: break
print(len(all_works), "works")
```

### Option D — Group-by (for aggregates without fetching records)

```python
# How many MTBC papers per year?
r = openalex(
    "/works",
    filter="concepts.id:C23498923",
    group_by="publication_year",
)
for g in r["group_by"]:
    print(g["key"], g["count"])
```

### Option E — `pyalex` (Python wrapper)

```bash
pip install pyalex
```

```python
from pyalex import Works, Authors, Institutions, Concepts, Topics, config
config.email = "your.email@example.org"

# Fluent filter syntax
works = (
    Works()
    .filter(institutions={"country_code": "fr"})
    .filter(publication_year=2022)
    .search("tuberculosis ancient")
    .get()
)
```

### Option F — Bulk dump (monthly snapshot)

A full monthly dump of all entities is available as
gzipped JSON files on Amazon S3 (free). Useful if you want to run
large-scale offline analyses without hammering the API.

- Snapshot URL: `https://docs.openalex.org/download-all-data/download-to-your-machine`
- Size: hundreds of GB compressed; plan storage accordingly
- Updated monthly

## Parallel calls

When querying multiple OpenAlex entities, concepts, or institutions,
dispatch the REST calls in parallel (multiple tool calls per message).
The API handles concurrent requests well within the documented rate
limits (10 req/s anonymous, 100 req/s with a polite pool email).
Batch-mode cursor pagination is still sequential by design, but independent
queries (e.g. several works or authors) should fire concurrently.

## Workflows

### Workflow 1 — Lit-review of ancient MTBC papers

Goal: enumerate all papers on ancient *Mycobacterium tuberculosis*
published 2010–2024 with their full metadata.

```python
r = openalex(
    "/works",
    search='"ancient DNA" "Mycobacterium tuberculosis"',
    filter="publication_year:2010-2024,type:article",
    per_page=200,
    sort="cited_by_count:desc",
)
for w in r["results"][:20]:
    aus = ", ".join(a["author"]["display_name"] for a in w["authorships"][:3])
    print(f"{w['publication_year']} | {w['cited_by_count']:4d} | {aus} — {w['title']}")
```

Use this to surface highly cited papers you might have missed and
populate a `bib-check`-compatible BibTeX export.

### Workflow 2 — Co-authorship network for *M. bovis* research

Goal: build a graph of researchers who have co-authored papers on
*Mycobacterium bovis* to identify key labs and connectors.

```python
import networkx as nx

r = openalex(
    "/works",
    filter="concepts.id:C24546623,publication_year:2015-2024",  # M. bovis concept
    per_page=200,
)
# Iterate all pages via cursor...
G = nx.Graph()
for w in r["results"]:
    authors = [a["author"]["display_name"] for a in w["authorships"]]
    for i, a1 in enumerate(authors):
        for a2 in authors[i+1:]:
            if G.has_edge(a1, a2):
                G[a1][a2]["weight"] += 1
            else:
                G.add_edge(a1, a2, weight=1)

# Top-10 most connected authors
top = sorted(G.degree(weight="weight"), key=lambda x: -x[1])[:10]
for name, deg in top:
    print(f"{deg:4d}  {name}")
```

Useful for identifying collaborators, reviewers, and for a "field
landscape" slide.

### Workflow 3 — Institution-filtered publication list

Goal: list all publications of the **Max Planck Institute for
Evolutionary Anthropology, Leipzig** on ancient DNA topics.

```python
# Institution lookup via ROR or name
inst_r = openalex("/institutions", search="Max Planck Evolutionary Anthropology")
mpi_id = inst_r["results"][0]["id"]      # e.g. https://openalex.org/I149899117

# All ancient-DNA works from that institution
r = openalex(
    "/works",
    filter=f"institutions.id:{mpi_id},concepts.display_name.search:ancient DNA",
    per_page=200,
)
```

### Workflow 4 — Reconstruct abstracts from `abstract_inverted_index`

```python
def inverted_to_text(inv_idx):
    """Convert OpenAlex abstract_inverted_index to plain text."""
    if not inv_idx: return ""
    positions = []
    for word, posns in inv_idx.items():
        for p in posns:
            positions.append((p, word))
    positions.sort()
    return " ".join(w for _, w in positions)

work = openalex("/works/W2741809807")
abstract = inverted_to_text(work.get("abstract_inverted_index"))
```

Feed `abstract` to your text-mining pipeline (the "150 000 articles"
corpus of your seminar).

### Workflow 5 — Sustainable Development Goals tagging

OpenAlex annotates works with UN SDG tags. Useful for framing a
tuberculosis paper in a global-health context:

```python
r = openalex(
    "/works",
    filter='concepts.id:C23498923,sustainable_development_goals.id:3',
    # SDG 3: Good Health and Well-being
    per_page=10,
    sort="cited_by_count:desc",
)
```

### Workflow 6 — Group-by aggregate for a field landscape

Count MTBC papers per country per year (for a histogram slide):

```python
r = openalex(
    "/works",
    filter="concepts.id:C23498923,publication_year:2015-2024",
    group_by="authorships.institutions.country_code",
)
```

## Caveats

- **Topics ≠ Concepts.** The legacy "Concepts" taxonomy is being
  replaced by "Topics". For new analyses, use Topics; for historical
  consistency, stick with one or the other.
- **Author disambiguation is imperfect.** Two researchers with the
  same name at different institutions may or may not be separated
  correctly. Verify via ORCID when possible.
- **Institution hierarchy is flat.** OpenAlex does not model
  departments or labs within an institution — all affiliations are
  at the top institution level.
- **Abstract inverted index is a legal compromise.** You must
  reconstruct the abstract from the positional index; the raw text
  is not provided due to copyright considerations. Non-fatal but
  adds one preprocessing step.
- **Citation counts lag slightly.** OpenAlex updates monthly; very
  recent citations may be underestimated compared to real-time
  sources.
- **Polite pool is not a contract.** If you spike your request rate,
  you may still be rate-limited. Implement exponential backoff.
- **No full text.** OpenAlex provides metadata + OA URLs when
  available, not the full text itself. Combine with Unpaywall (same
  organisation) for PDF access.
- **No guarantee of completeness.** Coverage is strongest for
  indexed journals with DOIs. Grey literature, non-English
  publications, and very recent preprints may be under-represented.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`spaam-community`** | Meta-index for ancient metagenomics — OpenAlex fills the bibliometric layer around it |
| **`bib-check`** | Reference verification — OpenAlex metadata can pre-populate BibTeX entries |
| **`bacdive`**, **`enterobase`**, **`pathogens-portal`**, **`ncbi-pathogen-detection`** | Each publication in these resources has an OpenAlex entry — join on DOI |
| **TBannotator MCP** | OpenAlex is the bibliometric counterpart to TBannotator's 150k-articles text-mining corpus |
| **Europe PMC / PubMed** | Biomedical-focused alternatives — use together with OpenAlex for cross-validation |
| **Unpaywall** | Same organisation (OurResearch) — OA PDF access |
| **ORCID** | Author identifiers — resolve OpenAlex authors to ORCIDs when disambiguation matters |
| **ROR** (Research Organization Registry) | Institution identifiers — OpenAlex uses these |
| **`pyalex`** (Python) | Canonical Python client |
| **`openalexR`** (R) | Canonical R client |

## Citation

```bibtex
@misc{priem2022openalex,
  title        = {OpenAlex: A fully-open index of scholarly works,
                  authors, venues, institutions, and concepts},
  author       = {Priem, Jason and Piwowar, Heather and Orr, Richard},
  year         = {2022},
  eprint       = {2205.01833},
  archivePrefix = {arXiv},
  primaryClass = {cs.DL},
  url          = {https://arxiv.org/abs/2205.01833},
  note         = {License CC0 for metadata. Cite alongside any
                  downstream analysis.}
}
```

**Always pin** your access date and record the OpenAlex snapshot
month (visible at `https://api.openalex.org/` in the
`updated_date` field of results) for reproducibility.
