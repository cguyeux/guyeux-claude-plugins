---
name: pubtator
description: >-
  Query PubTator 3.0 / PubTator Central (NCBI BioNLP), the reference
  service for pre-computed biomedical entity annotations on PubMed
  abstracts and PMC full-text articles. Uses state-of-the-art NER
  (AIONER) to tag six entity types: genes/proteins, diseases,
  chemicals, species, genetic variants, and cell lines. Optional
  relation extraction in v3. Saves you from training your own
  biomedical NER for any MTBC / TB text-mining project.

  Use when: pre-annotating MTBC abstracts or full-text articles with
  standardised biomedical entities, extracting mentions of specific
  genes/variants/drugs from a TB paper, building a gene-disease
  association graph from the literature, or accelerating a text-mining
  pipeline that would otherwise require training BioBERT / PubMedBERT
  on your own corpus. For TB-only corpora, build the abstract list with
  `tbmonitor-papers` (PubMed TB pre-filtered, ~190k papers, MeSH/keywords
  as JSON) before passing PMIDs to PubTator — this is faster than
  re-querying PubMed directly.
---

# PubTator 3.0 — Pre-Computed Biomedical Entity Annotations

## Overview

**PubTator 3.0** (formerly **PubTator Central**) is the NCBI BioNLP
group's reference service for **pre-computed biomedical entity
annotations** on PubMed abstracts and PMC Open Access full-text
articles. It is maintained by **Zhiyong Lu**'s group at the
**U.S. National Library of Medicine (NLM)**, synchronised daily with
PubMed and PMC, and freely accessible without registration.

Version 3.0 (released 2024) uses **AIONER** — a state-of-the-art
unified NER model — to tag six entity types across the full biomedical
corpus. Crucially, v3 also provides **relation extraction** between
entities, enabling semantic search beyond simple entity mentions.

- **Reference (v3)**: Wei C.-H., Allot A., Lai P.-T., Leaman R.,
  Tian S., Luo L., Jin Q., Wang Z., Chen Q., Lu Z. *PubTator 3.0: an
  AI-powered literature resource for unlocking biomedical knowledge.*
  **Nucleic Acids Research** 52(W1): W540–W546 (2024). DOI:
  `10.1093/nar/gkae235`
- **Reference (PubTator Central, 2019)**: Wei C.-H., Allot A., Leaman R.,
  Lu Z. *PubTator central: automated concept annotation for biomedical
  full text articles.* **Nucleic Acids Research** 47(W1): W587–W593
  (2019). DOI: `10.1093/nar/gkz389`
- **v3 portal**: `https://www.ncbi.nlm.nih.gov/research/pubtator3/`
- **v2 portal (still active)**: `https://www.ncbi.nlm.nih.gov/research/pubtator/`
- **v3 API**: `https://www.ncbi.nlm.nih.gov/research/pubtator3-api/`
- **v2 API**: `https://www.ncbi.nlm.nih.gov/research/pubtator/api/`
- **License**: public domain — NCBI/NLM standard re-use terms
- **No API key required**; be polite with email in `User-Agent`

> [!NOTE]
> PubTator 3 and PubTator Central (v2) both run in parallel as of 2025.
> v3 is **recommended for new work** (better models, relation
> extraction, expanded coverage). v2 is still accessible for
> reproducibility of earlier analyses.

## Entity types covered

| Type | What it tags | NER backbone |
|---|---|---|
| **Gene/Protein** | Gene and protein mentions, normalised to NCBI Gene IDs | GNorm2 → AIONER |
| **Disease** | Disease and phenotype mentions, normalised to MeSH / OMIM | TaggerOne → AIONER |
| **Chemical** | Drugs, metabolites, reagents, normalised to MeSH / ChEBI | TaggerOne → AIONER |
| **Species** | Organisms, normalised to NCBI Taxonomy IDs (incl. ***Mycobacterium tuberculosis*** tax ID 1773) | SR4GN → AIONER |
| **Mutation / Variant** | Genetic variants in multiple formats (HGVS, rs#, protein mutation) | tmVar → AIONER |
| **CellLine** | Cell lines, normalised to Cellosaurus / ATCC | — |

All annotations carry **span offsets** into the original text, so you
can highlight them in the original abstract/article or feed them to
downstream tools.

## v3 novelty — Relation Extraction

PubTator 3 adds **relation triples** between entities, e.g.:

- **Gene–Disease**: `katG` — *treats / resistance to* — *tuberculosis*
- **Chemical–Disease**: `isoniazid` — *treats* — *tuberculosis*
- **Chemical–Gene**: `rifampicin` — *interacts with* — `rpoB`
- **Gene–Gene**: `katG` — *regulates* — `inhA`
- **Variant–Disease**: `rpoB S450L` — *associated with* — *tuberculosis*

This turns PubTator from a tagging service into a **knowledge graph
builder** — with semantic queries directly available over the output.

## Why it matters for MTBC × anthropology

1. **Ready-made NER for MTBC papers.** Instead of training BioBERT or
   PubMedBERT on your own corpus, fetch the PubTator-tagged version
   of every MTBC paper and you get gene, drug, resistance mutation,
   and species annotations for free.
2. **Filter by species.** For a global NER pipeline, filtering to
   articles where *Mycobacterium tuberculosis* (tax ID 1773) is a
   tagged entity gives you a clean cohort — no false positives from
   "tuberculosis" as a lay term.
3. **Resistance mutation extraction.** Variant mentions in PubTator
   are already normalised. Filtering for `rpoB`, `katG`, `inhA`, etc.
   gives you a resistance-mutation frequency table across the entire
   TB literature.
4. **Relation extraction for resistance scenarios.** v3's Gene–Disease
   and Variant–Disease relations let you build a **resistance
   knowledge graph** directly from papers — a compelling slide for
   a seminar on AI-augmented literature mining.

## Data access

### Option A — PubTator 3 Web API (recommended)

Base URL: `https://www.ncbi.nlm.nih.gov/research/pubtator3-api/`

**Per-paper annotations** in BioC XML:

```bash
# Abstract-level (PMID) — canonical route, verified April 2026
curl -sL "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocxml?pmids=30715220" \
  -o PMID30715220.pubtator.xml

# Batch: up to 100 IDs in one call
curl -sL "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocxml?pmids=30715220,31114887,24048470"
```

> [!WARNING]
> **PubTator 3 API accepts only `pmids`**, not `pmcids`. Empirically
> verified (April 2026): `?pmcids=PMC1234567` returns
> `["pmids is a mandatory parameter."]` regardless of whether the
> `PMC` prefix is present. If you only have a PMCID, first convert
> it to a PMID via NCBI's ID converter
> (`https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/`) or
> `eutils esearch`, then feed the PMID to PubTator. This is a
> difference vs BioC-PMC which does accept `pmcids`.

**Search for entity**:

```bash
# Find all papers mentioning an entity (PubTator 3 semantic search)
curl -sL "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/search/?text=@DISEASE_tuberculosis&size=50" \
  | python -m json.tool
```

The `@<TYPE>_<name>` syntax scopes the search to a specific entity
type. Available scopes: `@GENE_`, `@DISEASE_`, `@CHEMICAL_`,
`@SPECIES_`, `@VARIANT_`, `@CELLLINE_`.

**Relation search**:

```bash
# Find papers that report a relation between an entity and any other
curl -sL "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/relations?e1=@GENE_katG"
```

### Option B — PubTator Central v2 Web API

Base URL: `https://www.ncbi.nlm.nih.gov/research/pubtator/api/v1/`

Still useful for reproducibility of pre-2024 analyses. Endpoints
roughly parallel to v3 but without relation extraction.

### Option C — Bulk FTP dumps

PubTator ships periodic bulk dumps of the entire corpus:

- FTP: `https://ftp.ncbi.nlm.nih.gov/pub/lu/PubTator3/`
- Per-entity-type files (one per annotation type, TSV or BioC)
- Full BioC-PMC subset with annotations

Plan for several GB to tens of GB depending on which dumps you
download.

### Option D — Python wrappers

```bash
pip install pubtator-loader   # lightweight parser
# or
pip install bioc              # same parser used for BioC-PMC
```

```python
import bioc, requests

r = requests.get(
    "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocxml",
    params={"pmids": "30715220"},
    headers={"User-Agent": "mtbc-mining (your.email@example.org)"},
    timeout=60,
)
collection = bioc.loads(r.text)

for doc in collection.documents:
    for passage in doc.passages:
        for ann in passage.annotations:
            etype = ann.infons.get("type", "?")
            norm = ann.infons.get("identifier", "?")
            print(f"{etype:10s}  {ann.text:30s}  →  {norm}")
```

## Parallel calls

When annotating or retrieving a batch of PMIDs/PMCIDs, dispatch the
requests in parallel (multiple tool calls per message). PubTator v3
endpoints return independent payloads and tolerate concurrent requests.
Sequential loops over >10 IDs are the main latency bottleneck; batching
via the bulk endpoint or firing concurrent WebFetch calls gives a 5-10x
speedup.

## Workflows

### Workflow 1 — Extract all MTBC resistance mutations from the TB literature

Goal: build a table of reported resistance mutations in MTBC across
all of PubMed.

```python
# 1. Use PubTator 3 search to find all papers with DISEASE=tuberculosis
#    and any VARIANT annotation
import requests, bioc, time, collections

def pubtator_search_pmids(entity_query, size=200, offset=0):
    r = requests.get(
        "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/search/",
        params={"text": entity_query, "size": size, "offset": offset},
        timeout=60,
    )
    return r.json()

def fetch_annotations(pmids):
    r = requests.get(
        "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocxml",
        params={"pmids": ",".join(pmids)},
        timeout=120,
    )
    return bioc.loads(r.text)

# 2. Iterate and collect variant mentions
mutation_counts = collections.Counter()
pmids = pubtator_search_pmids("@DISEASE_tuberculosis")["results"]
for batch_start in range(0, len(pmids), 100):
    batch = [str(p["pmid"]) for p in pmids[batch_start:batch_start+100]]
    col = fetch_annotations(batch)
    for doc in col.documents:
        for passage in doc.passages:
            for ann in passage.annotations:
                if ann.infons.get("type") == "Mutation":
                    mutation_counts[ann.text] += 1
    time.sleep(0.5)

for mut, count in mutation_counts.most_common(30):
    print(f"{count:5d}  {mut}")
```

Expected top hits for TB: *rpoB S450L*, *katG S315T*, *inhA C-15T*,
*embB M306V*, etc.

### Workflow 2 — Species-filtered corpus for MTBC text mining

Goal: restrict your mining to papers that explicitly mention
*Mycobacterium tuberculosis* (tax ID 1773) as an annotated entity
— avoiding noise from papers that use "tuberculosis" as a lay term.

```python
# Filter via PubTator search with @SPECIES scope
pmids = pubtator_search_pmids("@SPECIES_Mycobacterium_tuberculosis")
```

This is cleaner than a free-text PubMed search because PubTator has
already normalised the entity and will not return papers that mention
"TB patients" without referencing the pathogen species specifically.

### Workflow 3 — Resistance knowledge graph from Gene–Disease relations

Goal: build a directed graph `Gene → Disease / Drug Resistance` from
PubTator 3 relations.

```python
# Pseudo-workflow using the relations endpoint
import networkx as nx

def pubtator_relations(entity):
    r = requests.get(
        "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/relations",
        params={"e1": entity},
        timeout=60,
    )
    return r.json()

G = nx.DiGraph()
# Seed with known TB resistance genes
for gene in ["katG", "rpoB", "inhA", "pncA", "embB", "gyrA"]:
    rels = pubtator_relations(f"@GENE_{gene}")
    for rel in rels.get("relations", []):
        G.add_edge(rel["entity1"], rel["entity2"],
                   type=rel.get("type", ""),
                   pmid=rel.get("pmid"))

print(G.number_of_nodes(), "nodes,", G.number_of_edges(), "edges")
```

### Workflow 4 — Combined with BioC-PMC and OpenAlex

Full text-mining chain for the 150k-article corpus:

1. **OpenAlex** → find all papers tagged with *Mycobacterium
   tuberculosis* concept (list of DOIs / PMCIDs)
2. **BioC-PMC** → fetch full text in BioC format for the PMC OA subset
3. **PubTator 3** → fetch pre-computed annotations for the same PMC IDs
4. **Merge** → each article now has full text (BioC-PMC) + entities
   and relations (PubTator 3)
5. Feed the merged corpus to your TBannotator-style LLM pipeline

### Workflow 5 — PubTator annotations for a single-paper deep dive

When you want to extract everything from one specific paper (e.g.
Bos et al. 2014 on ancient *M. pinnipedii*):

```bash
# Bos 2014 PMID: 25141179
curl -sL "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocxml?pmids=25141179" \
  -o bos2014.pubtator.xml
```

Parse and tabulate the entities to populate a fact-extraction table
(species, genes, mutations, geographic mentions).

## Caveats

- **Entities only, not full meaning.** PubTator tags mentions; it
  does not do coreference resolution or complex event extraction
  beyond the relations in v3. For deeper semantics, feed the tagged
  text to an LLM.
- **Normalisation is imperfect.** NCBI Gene IDs are reliable; MeSH
  normalisation for diseases sometimes fails; HGVS mutation
  normalisation is approximate. Always spot-check before building a
  knowledge graph at scale.
- **Species coverage is uneven.** Tax IDs for common pathogens are
  well-handled; rare organisms may be missed or mis-tagged.
- **v2 and v3 differ in coverage and normalisation.** If you combine
  data from both, document which version each record came from.
- **Relation extraction in v3 is an automated estimate.** Relations
  are predicted, not curated. Sensitivity and specificity depend on
  the relation type. Cite Wei 2024 and use as a strong baseline, not
  a gold standard.
- **Rate limit.** Polite requests; prefer batch endpoints (up to 100
  PMIDs/PMCIDs per call) over single-ID fetches.
- **Latency.** The API is responsive (< 1 s per call) but at scale
  (10⁴+ papers), use bulk FTP dumps instead.
- **PubTator is an automated service.** Manual curation efforts (e.g.
  BioCreative annotated corpora) remain gold standards for NER
  benchmarking.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`bioc-pmc`** | PubTator outputs are in BioC format — same parser applies |
| **`openalex`** | Bibliometric discovery — find PMCIDs to feed to PubTator |
| **TBannotator MCP** | Consumes the pre-annotated corpus produced by PubTator |
| **Europe PMC** | Alternative source of full text for papers not in PMC OA |
| **NCBI Gene / Taxonomy / MeSH / ChEBI / Cellosaurus** | Reference databases for PubTator's normalisation targets |
| **BERN2** | Independent neural biomedical NER — use for cross-validation |
| **scispaCy / BioBERT / PubMedBERT** | Downstream NLP models that can consume PubTator tags as features |
| **`bioc`** (Python) | Canonical parser |
| **AIONER** | The underlying NER model in v3 — same group |

## Citations

```bibtex
@article{wei2024pubtator3,
  title   = {PubTator 3.0: an AI-powered literature resource for
             unlocking biomedical knowledge},
  author  = {Wei, Chih-Hsuan and Allot, Alexis and Lai, Po-Ting and
             Leaman, Robert and Tian, Shubo and Luo, Ling and
             Jin, Qiao and Wang, Zhizheng and Chen, Qingyu and Lu, Zhiyong},
  journal = {Nucleic Acids Research},
  volume  = {52},
  number  = {W1},
  pages   = {W540--W546},
  year    = {2024},
  doi     = {10.1093/nar/gkae235}
}

@article{wei2019pubtatorcentral,
  title   = {PubTator central: automated concept annotation for
             biomedical full text articles},
  author  = {Wei, Chih-Hsuan and Allot, Alexis and Leaman, Robert and
             Lu, Zhiyong},
  journal = {Nucleic Acids Research},
  volume  = {47},
  number  = {W1},
  pages   = {W587--W593},
  year    = {2019},
  doi     = {10.1093/nar/gkz389}
}
```

**Always cite** Wei 2024 (PubTator 3) for any new analysis, and Wei
2019 (PubTator Central) if you used the v2 endpoints. Record the
access date and note whether you used the API or a bulk FTP dump.
