---
name: bioc-pmc
description: >-
  Use BioC-PMC, the PubMed Central Open Access and Author Manuscript subset in BioC format
  (NCBI/NLM): ~3 million full-text biomedical articles with structured sections (title,
  abstract, body, figures, tables) in XML or JSON, optimised for NLP pipelines. Use when
  building a full-text corpus for MTBC or M. bovis text mining, retrieving structured
  sections for named-entity recognition or relation extraction, bulk-downloading PMC OA
  articles in machine-readable form, or feeding PubTator or a custom NER model. For
  abstract-only TB workflows prefer tbmonitor-papers (~190k pre-indexed PubMed TB abstracts,
  sub-second SQL); BioC-PMC is the right tool when full body text, figures or tables are
  required.
---

# BioC-PMC : PMC Open Access in BioC Format

## Overview

**BioC-PMC** is the PubMed Central Open Access (PMC OA) + Author
Manuscript subset of biomedical literature converted into the **BioC
format**, a community-driven minimalist data structure for
biomedical text mining, published and maintained by the **NLM / NCBI
BioNLP research group** (led by **Donald C Comeau** and colleagues).
It provides **~3 million full-text articles** with structured sections
(title, abstract, body, figures, tables, references) in either
**XML** or **JSON**, ready for NLP pipelines without the usual
PMC-XML preprocessing pain.

- **BioC format reference**: Comeau D.C., Doğan R.I., Ciccarese P.,
  Cohen K.B., Krallinger M., Leitner F., Lu Z., Peng Y., Rinaldi F.,
  Torii M., Valencia A., Verspoor K., Wiegers T.C., Wu C.H., Wilbur W.J.
  *BioC: a minimalist approach to interoperability for biomedical text
  processing.* **Database (Oxford)** 2013: bat064 (2013). DOI:
  `10.1093/database/bat064`
- **PMC-in-BioC reference**: Comeau D.C., Wei C.-H., Doğan R.I., Lu Z.
  *PMC text mining subset in BioC: about three million full-text
  articles and growing.* **Bioinformatics** 35(18): 3533–3535 (2019).
  DOI: `10.1093/bioinformatics/btz070`
- **BioC-PMC landing page**: `https://www.ncbi.nlm.nih.gov/research/bionlp/APIs/BioC-PMC/`
- **BulK FTP**: `https://ftp.ncbi.nlm.nih.gov/pub/wilbur/BioC-PMC/`
- **BioC-PubMed (abstracts only)**: `https://www.ncbi.nlm.nih.gov/research/bionlp/APIs/BioC-PubMed/`
- **License**: inherits from PMC OA : CC-BY or other permissive per
  article. Author Manuscript subset has specific NIH re-use terms;
  check per-article.
- **Parsing libraries**: C++, Go, Java, **Python** (`pubtator-loader`,
  `bioc` PyPI package), Perl, Ruby

> [!NOTE]
> BioC-PMC is a **text-mining data source**, not an NER annotator.
> For pre-annotated biomedical entities, use **PubTator Central**
> (a sibling NCBI BioNLP resource, see `Related` section).

## Why it matters for MTBC × anthropology

For your seminar narrative on a **150 000-article text-mining corpus**,
BioC-PMC is **the canonical substrate** that:

1. **Backs the corpus claim with a public source.** BioC-PMC provides
   ~3 million full-text biomedical articles. A filter on TB/MTBC topics
   easily yields 10⁴–10⁵ relevant articles. You can state in Methods
   *"starting from the BioC-PMC snapshot of [date], we retained articles
   matching concept X…"*, reproducible and auditable.
2. **Gives you full text, not just abstracts.** OpenAlex's
   `abstract_inverted_index` gives you the abstract; BioC-PMC gives you
   the **full body, figures, tables**. This matters when you want to
   extract, e.g., reported *M. bovis* isolate counts from a Materials
   and Methods section, or geographical metadata buried in a table
   caption.
3. **Pre-structured for NLP.** BioC-PMC articles come as a tree of
   passages (title → abstract → introduction → methods → results → …)
   with explicit section labels. This is exactly what a named-entity
   recognition or relation-extraction pipeline wants as input.

## BioC format : structure in one paragraph

A BioC **collection** contains one or more **documents**. Each document
contains **passages** (sections of text). Each passage has an **offset**
in the document, a type (e.g. `title`, `abstract`, `paragraph`,
`section_title`), free text, and optional **annotations** (pre-tagged
entities with spans). Passages may contain **sentences**, and both
passages and sentences carry **infons** (key-value metadata) and
**relations** (links between annotations).

The design goals are minimalism and interoperability, any tool that
can read BioC can process any article in the collection without custom
parsing.

## Data access

### Option A : Bulk FTP (canonical bulk download)

```bash
mkdir -p ~/data/bioc-pmc && cd ~/data/bioc-pmc
# The FTP directory contains periodic snapshots as tarballs
curl -sL "https://ftp.ncbi.nlm.nih.gov/pub/wilbur/BioC-PMC/" | \
  grep -oE 'href="[^"]+\.tar\.gz"' | sed 's/href="//;s/"$//' | head
# Download a specific snapshot (check the directory listing for current names)
wget "https://ftp.ncbi.nlm.nih.gov/pub/wilbur/BioC-PMC/PMC-OA_<snapshot>.tar.gz"
tar xzf PMC-OA_<snapshot>.tar.gz
```

Each article becomes one XML or JSON file. Plan for tens of GB if you
download the full snapshot.

### Option B : Web API (per-article or small batches)

```bash
# Fetch a single PMC article by PMCID in BioC-XML
curl -sL "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC1234567/unicode" \
  -o PMC1234567.bioc.xml

# Same in JSON
curl -sL "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/PMC1234567/unicode" \
  -o PMC1234567.bioc.json
```

Two encoding options: `unicode` (original UTF-8) and `ascii`
(transliterated to 7-bit for legacy tools). Use `unicode` unless you
have a specific downstream constraint.

### Option C : `bioc` Python library

```bash
pip install bioc
```

```python
import bioc

# Parse a BioC XML file
with open("PMC1234567.bioc.xml", "r") as fp:
    collection = bioc.load(fp)

for document in collection.documents:
    for passage in document.passages:
        print(passage.infons.get("section_type"), "→", passage.text[:80])
```

The library provides classes for `Collection`, `Document`, `Passage`,
`Sentence`, `Annotation`, `Relation`, one-to-one with the BioC
schema.

### Option D : `pubtator-loader` / PubTator Central

For **pre-annotated** articles (gene, disease, chemical, mutation,
species entities already tagged), use **PubTator Central** instead of
raw BioC-PMC:

- Landing: `https://www.ncbi.nlm.nih.gov/research/pubtator3/`
- API: `https://www.ncbi.nlm.nih.gov/research/pubtator3/api`

PubTator Central ships annotations in the same BioC envelope.

## Parallel calls

When fetching multiple articles, PMC IDs, or annotation batches, issue the
requests in parallel (multiple tool calls within the same message). BioC-PMC
endpoints are idempotent and return independent payloads, so concurrent
WebFetch / curl calls give a 3-10x speedup over sequential loops. Apply this
to all workflows below.

## Workflows

### Workflow 1 : Build an MTBC full-text corpus from BioC-PMC

Goal: reproduce a "150k articles" MTBC corpus from a public, citable
source.

```python
# Pseudo-workflow:
# 1. Get PMC IDs of all MTBC-tagged articles via OpenAlex or Europe PMC
# 2. Fetch each in BioC format via the Web API
# 3. Parse with the bioc library
# 4. Extract the full text for downstream NER / LLM processing

import bioc, requests, time, json

POLITE_EMAIL = "your.email@example.org"

def fetch_bioc_xml(pmcid):
    url = (f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/"
           f"pmcoa.cgi/BioC_xml/{pmcid}/unicode")
    r = requests.get(url, timeout=60,
                     headers={"User-Agent": f"mtbc-corpus ({POLITE_EMAIL})"})
    r.raise_for_status()
    return r.text

def article_to_sections(xml_text):
    col = bioc.loads(xml_text)
    sections = {}
    for doc in col.documents:
        for p in doc.passages:
            section = p.infons.get("section_type", "other")
            sections.setdefault(section, []).append(p.text)
    return {k: " ".join(v) for k, v in sections.items()}

pmc_ids = ["PMC1234567", "PMC2345678"]  # from OpenAlex query
corpus = {}
for pid in pmc_ids:
    try:
        xml = fetch_bioc_xml(pid)
        corpus[pid] = article_to_sections(xml)
        time.sleep(0.3)   # polite pause
    except Exception as e:
        print(f"skip {pid}: {e}")

with open("mtbc_corpus.json", "w") as fp:
    json.dump(corpus, fp)
```

### Workflow 2 : Extract Methods-section text only

Goal: restrict NER or LLM processing to Methods sections where
*isolate counts*, *country of origin*, and *sampling dates* are
typically reported.

```python
def methods_only(collection):
    out = []
    for doc in collection.documents:
        in_methods = False
        for p in doc.passages:
            st = p.infons.get("section_type", "").lower()
            if st in {"methods", "materials_and_methods",
                      "materials|methods", "methods_and_materials"}:
                in_methods = True
                out.append(p.text)
            elif st in {"results", "discussion"}:
                in_methods = False
        # Fallback: any passage whose parent section title contains 'method'
    return " ".join(out)
```

### Workflow 3 : Cross-reference BioC-PMC with OpenAlex

Goal: use OpenAlex for topic discovery, then fetch full text from
BioC-PMC for the articles that are in the PMC OA subset.

```python
# From the openalex skill
works = openalex_search("Mycobacterium tuberculosis phylogeography")
pmc_ids = [
    w.get("ids", {}).get("pmcid")   # OpenAlex stores PMC IDs when available
    for w in works
]
pmc_ids = [p for p in pmc_ids if p]
# Then fetch each via BioC-PMC Web API (Workflow 1)
```

Not every OpenAlex work has a PMC ID, only open-access PMC articles.
For the rest, fall back to Europe PMC or the publisher's site.

### Workflow 4 : Feed PubTator Central annotations into your pipeline

```bash
# Fetch a PubTator Central BioC-XML with pre-annotated entities
curl -sL "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocxml?pmcids=PMC1234567" \
  -o PMC1234567.pubtator.xml
```

Parse with the same `bioc` library; the `annotations` field on each
passage contains pre-tagged genes, diseases, chemicals, mutations, and
species (including *Mycobacterium tuberculosis*). This saves you from
training your own NER model for common biomedical entities.

### Workflow 5 : BioC-PubMed for abstracts-only corpus

When you only need abstracts (much lighter than full text), BioC-PubMed
is the sibling resource:

```bash
curl -sL "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pubmed.cgi/BioC_xml/12345678/unicode" \
  -o pubmed_12345678.bioc.xml
```

PMID → BioC-PubMed; PMCID → BioC-PMC. The two are parallel services.

## Caveats

- **PMC OA is a subset of PMC.** Only the **open-access** subset + the
  **Author Manuscript** subset are available in BioC. A significant
  portion of the biomedical literature is PMC-indexed but **not** OA,
  and those articles are inaccessible via this route.
- **Snapshots lag.** BioC-PMC is updated periodically, not in real
  time. For the most recent papers (last few months), use the Web
  API per-PMCID instead of the bulk dump.
- **Section labels vary.** Papers use `methods`, `materials_and_methods`,
  `materials|methods`, or sometimes just `section` with the title in
  `infons.name`. Your filter must handle all variants.
- **Author Manuscript subset has specific NIH re-use terms.** Verify
  per-article before republishing.
- **Figures and tables are text-only.** Images are not embedded;
  table cells are reconstructed from the XML. For high-fidelity
  figure extraction, use the original PMC XML or PDF.
- **PubTator annotations are not ground truth.** They are produced
  by automated NER and have known errors for rare entities. Use as
  a strong baseline, not as gold labels.
- **Rate limit on the Web API.** Be polite: include your email in
  the `User-Agent`, sleep between requests, and prefer the bulk FTP
  for large jobs.
- **Encoding gotchas.** Use `unicode` variant unless you need the
  legacy 7-bit ASCII output.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`openalex`** | Bibliometric discovery, find PMC IDs for your topic, then fetch full text via BioC-PMC |
| **`spaam-community`** | Pointers to ancient-metagenomics papers whose PMCIDs can be fetched in BioC |
| **TBannotator MCP** | Consumes the text-mining corpus produced from BioC-PMC |
| **`bib-check`** | Reference verification, cross-reference DOIs/PMIDs before building a corpus |
| **Europe PMC** | Complementary full-text source (broader coverage, alternative API) |
| **PubTator Central** | Pre-annotated BioC envelope, saves you from training your own NER |
| **`bioc`** (Python) | Canonical BioC parser |
| **spaCy / scispaCy / BioBERT / PubMedBERT** | Downstream NLP models that consume BioC text |

## Citations

```bibtex
@article{comeau2013bioc,
  title   = {BioC: a minimalist approach to interoperability for
             biomedical text processing},
  author  = {Comeau, Donald C. and Do{\u g}an, Rezarta Islamaj and
             Ciccarese, Paolo and Cohen, Kevin Bretonnel and
             Krallinger, Martin and Leitner, Florian and Lu, Zhiyong and
             Peng, Yifan and Rinaldi, Fabio and Torii, Manabu and
             Valencia, Alfonso and Verspoor, Karin and Wiegers, Thomas C.
             and Wu, Cathy H. and Wilbur, W. John},
  journal = {Database (Oxford)},
  volume  = {2013},
  pages   = {bat064},
  year    = {2013},
  doi     = {10.1093/database/bat064}
}

@article{comeau2019biocpmc,
  title   = {PMC text mining subset in BioC: about three million
             full-text articles and growing},
  author  = {Comeau, Donald C. and Wei, Chih-Hsuan and
             Do{\u g}an, Rezarta Islamaj and Lu, Zhiyong},
  journal = {Bioinformatics},
  volume  = {35},
  number  = {18},
  pages   = {3533--3535},
  year    = {2019},
  doi     = {10.1093/bioinformatics/btz070}
}
```

**Remember**: cite the BioC format paper (Comeau 2013) and the PMC-in-BioC
paper (Comeau 2019), plus record the **snapshot date** you used
(visible in the FTP directory listing) for reproducibility.