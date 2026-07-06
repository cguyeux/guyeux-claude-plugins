---
name: europe-pmc
description: >-
  Query Europe PMC (EMBL-EBI) — the European biomedical literature
  repository covering PubMed abstracts, PMC full text, preprints from
  32+ servers (bioRxiv, medRxiv, Research Square, etc.), books, patents,
  clinical guidelines, and grants. Provides a REST API for search, full
  text retrieval, and pre-computed text-mining annotations (genes,
  diseases, chemicals, organisms, GO terms, accession numbers). The
  broadest open-access biomedical literature index, complementary to
  OpenAlex (bibliometric) and BioC-PMC (PMC OA only).

  Use when: searching biomedical literature including preprints, fetching
  full text of OA papers, retrieving pre-computed annotations in JSON
  or XML, building a TB corpus that includes preprints (bioRxiv /
  medRxiv), cross-linking publications to data accessions (ENA, UniProt,
  ChEMBL, PDB), or discovering related articles via citation graph.
  For PubMed-only TB literature (no preprints), `tbmonitor-papers` is
  a faster alternative: ~190k pre-indexed TB abstracts queryable in
  sub-second SQL with MeSH and keywords as JSON. Use Europe PMC when
  preprints, full-text, or non-PubMed sources are needed.
---

# Europe PMC — European Biomedical Literature + Annotations

## Overview

**Europe PMC** is the European open-access biomedical literature
platform operated by **EMBL-EBI** (Hinxton, UK) as part of the PMC
International network. It aggregates **~40 million abstracts**, the
**PMC full-text open-access subset**, **preprints from 32+ servers**
(bioRxiv, medRxiv, Research Square, ChemRxiv, and more), agricultural
research, books, patents, clinical guidelines, and funded-research
grants — all searchable through a unified REST API with
pre-computed text-mining annotations via **SciLite**.

Europe PMC is the **European counterpart** to NCBI PubMed/PMC but with
**broader coverage** (notably preprints, added starting in 2018 and
expanded in 2022+) and **integrated text-mining annotations** from
multiple NER pipelines shipped directly with each article.

- **Main portal**: `https://europepmc.org/`
- **RESTful API docs**: `https://europepmc.org/RestfulWebService`
- **Annotations API docs**: `https://europepmc.org/AnnotationsApi`
- **Articles API base**: `https://www.ebi.ac.uk/europepmc/webservices/rest/`
- **Annotations API base**: `https://www.ebi.ac.uk/europepmc/annotations_api/`
- **License**: metadata open; full-text terms inherit from source
  (PMC OA = CC-BY typically; preprints = per-server terms)
- **No API key** required for normal use; be polite

### Key references

- **Preprint integration (2024)**: Ferguson C. et al. *Enabling preprint
  discovery, evaluation, and analysis with Europe PMC.* **bioRxiv**
  2024.04.19.590240 (2024).
- **Annotations API launch (EMBL-EBI news)**: ebi.ac.uk/about/news/
  updates-from-data-resources/new-literature-api-europe-pmc-annotations/
- **Europe PMC history**: operated by EMBL-EBI with funding from the
  Europe PMC Funders' Group (a consortium of >30 European funders
  including Wellcome, ERC, MRC)

## Why it matters for MTBC × anthropology

Europe PMC fills specific niches in your text-mining stack:

1. **Preprint coverage.** NCBI PubMed indexes preprints sparingly
   (mostly post-publication). Europe PMC indexes **~30 preprint
   servers** including bioRxiv and medRxiv, making it the best single
   source for the **latest unpublished MTBC work** — crucial for
   keeping a seminar talking point up-to-date.
2. **Broader source list.** Europe PMC includes **agricultural
   research** (*M. bovis* cattle literature), **patents** (relevant
   for drug and diagnostic discovery), and **clinical guidelines**
   (WHO TB treatment guidelines). These are often missing from
   PubMed-only queries.
3. **Annotations bundled with the article.** The Annotations API
   returns pre-computed entity tags (genes, diseases, chemicals,
   organisms, GO terms, accession numbers) **directly with each
   article** — avoiding a separate PubTator fetch.
4. **Cross-linked data references.** Europe PMC SciLite links
   papers to **external data accessions** (ENA, UniProt, ChEMBL,
   PDB, EGA, PRIDE) automatically. For a paper that describes
   ancient MTBC sequencing, this gives you a direct link to the
   ENA study accession — faster than mining the text yourself.
5. **Grant information.** For the European funding landscape (ERC,
   H2020, Horizon Europe), Europe PMC tracks the grants that
   produced each publication — useful for mapping the funding
   ecosystem of your field.

Europe PMC is a **complement**, not a replacement, for the other
text-mining skills:

| Skill | Role |
|---|---|
| **`openalex`** | Global bibliometrics (209M works, all fields) |
| **`europe-pmc`** | **Biomedical focus + preprints + annotations + data links** |
| **`bioc-pmc`** | PMC OA full text in BioC format for NLP pipelines |
| **`pubtator`** | Pre-computed NER annotations (same family as Europe PMC annotations) |

## Data sources covered (verified)

As of 2024:

| Source | What it provides | Notes |
|---|---|---|
| PubMed | Biomedical abstracts | ~40M records |
| PubMed Central (PMC) | Full-text OA articles | Mirror of the NCBI PMC |
| **Preprints** | bioRxiv, medRxiv, ChemRxiv, Research Square, ArXiv Q-Bio, SSRN, etc. | 32+ servers as of April 2024 |
| Agricultural research | AGRICOLA | USDA-provided |
| Patents | — | Via the patents API endpoint |
| Clinical guidelines | — | WHO and national guidelines |
| Books | NCBI Bookshelf | Textbooks and reference works |

## Article REST API

Base URL: `https://www.ebi.ac.uk/europepmc/webservices/rest/`

### Search

```bash
# Search all Europe PMC sources for "Mycobacterium tuberculosis ancient DNA"
curl -sG "https://www.ebi.ac.uk/europepmc/webservices/rest/search" \
  --data-urlencode 'query=Mycobacterium tuberculosis ancient DNA' \
  --data-urlencode 'format=json' \
  --data-urlencode 'resultType=core' \
  --data-urlencode 'pageSize=25' \
  | python -m json.tool
```

Key query parameters:

| Parameter | Meaning |
|---|---|
| `query` | Free-text or field-specific query (see below) |
| `format` | `json`, `xml`, `dc` (Dublin Core) |
| `resultType` | `idlist` (just IDs), `lite` (core metadata), `core` (full metadata) |
| `pageSize` | Up to 1000 per page |
| `cursorMark` | Deep pagination (use `*` for first page) |
| `synonym` | `TRUE` to expand MeSH synonyms |
| `sort` | `CITED desc`, `P_PDATE_D desc`, etc. |

### Field-specific search syntax

Europe PMC supports a rich query syntax:

```
TITLE:"tuberculosis"
AUTH:"Guyeux C"
AFF:"Universit*"
PUB_YEAR:[2020 TO 2024]
JOURNAL:"Nature"
KW:"phylogeography"
SRC:PPR          # preprints only
SRC:MED          # PubMed only
SRC:PMC          # PMC only
HAS_FT:Y         # has full text
HAS_DATA:Y       # has linked data references
OPEN_ACCESS:Y    # open-access papers
```

Combine with boolean operators:

```bash
curl -sG "https://www.ebi.ac.uk/europepmc/webservices/rest/search" \
  --data-urlencode 'query=(TITLE:"Mycobacterium bovis" OR TITLE:"M. bovis") AND PUB_YEAR:[2020 TO 2024] AND SRC:PPR' \
  --data-urlencode 'format=json' \
  --data-urlencode 'resultType=lite'
```

### Fetch a specific article

```bash
# Full article metadata + abstract
curl -sL "https://www.ebi.ac.uk/europepmc/webservices/rest/article/MED/30715220?format=json"

# Full text if available (PMC XML)
curl -sL "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6748740/fullTextXML" -o PMC6748740.fulltext.xml

# Unicode full text
curl -sL "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6748740/unicode"
```

### Citation and reference endpoints

```bash
# Papers that cite this one
curl -sL "https://www.ebi.ac.uk/europepmc/webservices/rest/MED/30715220/citations?format=json&pageSize=100"

# Papers this one cites
curl -sL "https://www.ebi.ac.uk/europepmc/webservices/rest/MED/30715220/references?format=json&pageSize=100"
```

## Annotations API

Base URL: `https://www.ebi.ac.uk/europepmc/annotations_api/`

The Annotations API returns pre-computed entity annotations for each
article. Shipped by SciLite, they include:

| Annotation type | Meaning |
|---|---|
| **Gene/Proteins** | Normalised to UniProt / NCBI Gene |
| **Organisms** | Species normalised to NCBI Taxonomy |
| **Diseases** | MeSH / DOID |
| **Chemicals** | ChEMBL / ChEBI |
| **GO terms** | Functional annotations |
| **Accession numbers** | ENA, UniProt, PDB, ChEMBL, EGA, PRIDE, Rfam, BioModels, BioSamples, ArrayExpress |
| **Tissue / Cell types** | Controlled vocabularies |
| **Sentiment** | (experimental) |

### Example: get all annotations for an article

```bash
curl -sL "https://www.ebi.ac.uk/europepmc/annotations_api/annotationsByArticleIds?articleIds=MED:30715220&format=JSON" \
  | python -m json.tool
```

### Example: find all articles mentioning a specific gene

```bash
curl -sL "https://www.ebi.ac.uk/europepmc/annotations_api/annotationsByEntity?entity=GENE_PROTEIN&section=Abstract&format=JSON&pageSize=100&query=rpoB"
```

## Python wrapper

No official EMBL-EBI Python client, but the REST API is trivial to
wrap. Community options include `europepmc-api` and writing your own
thin helper:

```python
import requests

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"
POLITE_EMAIL = "your.email@example.org"

def europepmc_search(query, resultType="lite", pageSize=200, cursorMark="*"):
    params = {
        "query": query,
        "format": "json",
        "resultType": resultType,
        "pageSize": pageSize,
        "cursorMark": cursorMark,
    }
    headers = {"User-Agent": f"mtbc-research ({POLITE_EMAIL})"}
    r = requests.get(f"{BASE}/search", params=params, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()

# Search for preprints
r = europepmc_search(
    'Mycobacterium bovis AND SRC:PPR AND PUB_YEAR:[2023 TO 2024]',
    resultType="core",
)
for hit in r["resultList"]["result"]:
    print(hit.get("id"), hit.get("title"))
```

## Parallel calls

When running multiple searches, fetching several articles, or pulling
annotations for a batch, issue the REST calls in parallel (multiple tool
calls per message). Europe PMC endpoints are independent and idempotent —
concurrent WebFetch / curl calls give a significant speedup over sequential
loops. The Python wrapper above is synchronous; for bulk workflows prefer
direct parallel tool calls or wrap the wrapper in `concurrent.futures`.

## Workflows

### Workflow 1 — Latest MTBC preprints

Goal: catch every *M. tuberculosis* or *M. bovis* preprint from the
last 6 months.

```python
from datetime import date, timedelta
cutoff = (date.today() - timedelta(days=180)).isoformat()

q = (f'(TITLE:"Mycobacterium tuberculosis" OR TITLE:"Mycobacterium bovis" '
     f'OR ABSTRACT:"MTBC") AND SRC:PPR AND FIRST_PDATE:[{cutoff} TO 3000-01-01]')

r = europepmc_search(q, resultType="core", pageSize=200)
for hit in r["resultList"]["result"]:
    print(hit["firstPublicationDate"], hit.get("id"), hit.get("title")[:80])
```

This is **the** way to stay on top of the field for your seminar —
nothing beats a fresh preprint scan on an MNHN jury.

### Workflow 2 — Full text for an ancient MTBC paper

Goal: fetch the full text of Kay et al. 2015 for NLP processing.

```bash
# Kay 2015 (Vác mummies, Nat Commun 6:6717) — verified PMCID = PMC4396363
curl -sL "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4396363/unicode" -o kay2015.txt

# Or as PMC XML for structured parsing
curl -sL "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4396363/fullTextXML" -o kay2015.pmc.xml
```

### Workflow 3 — Follow the citation graph of a key paper

Goal: build a citation graph around Bos et al. 2014 (*M. pinnipedii*).

```python
# Bos 2014: MED/25141179
citations = requests.get(
    f"{BASE}/MED/25141179/citations",
    params={"format": "json", "pageSize": 1000},
).json()

# Each citation has id, source, authorString, pubYear, ...
# Iterate over all of them and follow further citations via recursion
```

### Workflow 4 — Extract ENA accessions referenced in the literature

Goal: for all MTBC papers in Europe PMC, extract the ENA study
accessions they reference via SciLite annotations.

```python
# Step 1: find all MTBC papers
r = europepmc_search('"Mycobacterium tuberculosis" AND HAS_DATA:Y', resultType="lite", pageSize=1000)

# Step 2: for each, query the annotations API
ena_by_paper = {}
for hit in r["resultList"]["result"]:
    art_id = f"{hit['source']}:{hit['id']}"
    ann = requests.get(
        f"https://www.ebi.ac.uk/europepmc/annotations_api/annotationsByArticleIds",
        params={"articleIds": art_id, "format": "JSON", "type": "Accession Numbers"},
    ).json()
    ena = [a["exact"] for a in ann[0].get("annotations", [])
           if a.get("type", "").startswith("Accession") and a.get("exact", "").startswith("PRJEB")]
    if ena:
        ena_by_paper[art_id] = ena
```

This gives you a **direct link from paper → ENA study accession**,
a massive time-saver vs manual curation.

### Workflow 5 — Grant mapping for European MTBC research

Goal: identify the ERC / Wellcome / Horizon grants that have funded
ancient-DNA MTBC research.

```python
r = europepmc_search(
    '("Mycobacterium tuberculosis" OR "Mycobacterium bovis") AND ("ancient DNA" OR "paleogenomic") AND GRANT_ID:*',
    resultType="core",
    pageSize=200,
)
for hit in r["resultList"]["result"]:
    grants = hit.get("grantsList", {}).get("grant", [])
    for g in grants:
        print(g.get("agency"), g.get("grantId"), "→", hit.get("title")[:60])
```

### Workflow 6 — Combine with OpenAlex for cross-validation

Goal: cross-check Europe PMC results against OpenAlex to estimate
coverage bias.

```python
# EPMC hits for a topic
epmc_hits = europepmc_search('TITLE:"Mycobacterium bovis phylogeography"')
epmc_dois = {r.get("doi") for r in epmc_hits["resultList"]["result"] if r.get("doi")}

# OpenAlex hits for the same topic
# (use the openalex skill)
openalex_hits = openalex_search("Mycobacterium bovis phylogeography")
oa_dois = {w.get("doi", "").replace("https://doi.org/", "") for w in openalex_hits["results"]}

only_epmc = epmc_dois - oa_dois
only_oa   = oa_dois - epmc_dois
print(f"EPMC-only: {len(only_epmc)}, OpenAlex-only: {len(only_oa)}, overlap: {len(epmc_dois & oa_dois)}")
```

## Caveats

- **Annotations are automated estimates.** The SciLite pipeline
  produces the annotations automatically; quality is good for
  common entities but imperfect for rare ones. Cross-check with
  PubTator for important claims.
- **Full-text access is gated by source.** PMC OA articles are
  fully accessible; subscription articles in PubMed return only
  metadata. Preprint full text availability varies per server.
- **Preprint coverage by server.** As of 2024, Europe PMC indexes
  **32+ preprint servers**, but coverage of the newest ones may lag
  by days to weeks.
- **Query syntax is Europe PMC-specific.** It is similar to PubMed's
  but not identical. Read the docs page; avoid assuming PubMed
  query syntax will work verbatim.
- **Cursor pagination for large results.** Don't use `offset` +
  `pageSize` for >10k results — use `cursorMark` instead.
- **Rate limit.** No hard limit announced, but the service is
  shared. Polite requests, exponential backoff, cached results.
- **Citation graph is incomplete.** Europe PMC tracks citations
  from its own indexed sources; closed-access journals may
  under-cite open-access ones in the graph.
- **Data accession normalisation imperfect.** Some extracted
  accessions are false positives (e.g. `PRJNA` patterns in
  unrelated contexts). Verify before bulk processing.
- **No LLM-style semantic search.** For semantic queries that go
  beyond keyword matching, use OpenAlex Topics or PubTator 3
  relation search.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`openalex`** | Broader (non-biomedical) bibliometric discovery — pair for cross-validation |
| **`bioc-pmc`** | PMC OA full text in BioC format for NLP — overlaps for PMC papers |
| **`pubtator`** | Pre-computed NER annotations — overlaps partly with Europe PMC SciLite |
| **`spaam-community`** | Ancient metagenomics resources — Europe PMC indexes their publications |
| **`pathogens-portal`** | Same EMBL-EBI ecosystem — ENA accessions link directly |
| **TBannotator MCP** | Text-mining backbone — Europe PMC is a canonical source |
| **`bib-check`** | Reference verification — Europe PMC metadata makes bibliography building reproducible |
| **Europe PMC Grist** | Internal EMBL-EBI tool for grant tracking |
| **ENA / UniProt / PDB / ChEMBL / EGA / PRIDE** | Data repositories cross-linked via SciLite |
| **MeSH** | Europe PMC supports MeSH synonym expansion in queries |

## Citation

```bibtex
@article{ferguson2024europepmcpreprints,
  title        = {Enabling preprint discovery, evaluation, and analysis
                  with Europe PMC},
  author       = {Ferguson, Catriona and Araújo, Daniel and Faulk, Laura
                  and others},
  journal      = {bioRxiv},
  year         = {2024},
  doi          = {10.1101/2024.04.19.590240}
}

@misc{europepmc,
  title        = {Europe PMC: a full-text literature database for the
                  life sciences},
  author       = {{Europe PMC Consortium}},
  howpublished = {https://europepmc.org/},
  publisher    = {European Bioinformatics Institute, EMBL-EBI},
  note         = {Cite the REST API access date; record the version of
                  the Annotations API used.}
}
```

**Remember**: in Methods, cite Europe PMC + the specific API endpoints
used + the access date, plus the source filters (`SRC:PPR`, `SRC:MED`,
etc.) you applied for reproducibility.
