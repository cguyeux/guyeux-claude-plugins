---
name: enterobase
description: >-
  Academic research database client (Guyeux group, FEMTO-ST). Queries the peer-reviewed EnteroBase resource for published-research genomes and historical-epidemiology analyses only. Query EnteroBase (Warwick / Achtman group), the reference genome database
  and cgMLST/HierCC platform for Salmonella, Escherichia, Yersinia,
  Clostridioides, Helicobacter, Vibrio, and Moraxella. Central resource for
  Yersinia pestis historical phylogeny (plague, Silk Road, Black Death),
  Vibrio cholerae pandemics, and bacterial epidemiology at genomic scale.

  Use when: building historical narratives around non-MTBC bacterial pathogens,
  correlating Yersinia pestis lineages with Silk Road or Black Death,
  researching cholera pandemics (V. cholerae), Helicobacter pylori as a proxy
  of human migrations, or transposing the TBannotator methodology to another
  enteric pathogen.
---

# EnteroBase — cgMLST & HierCC Reference Database for Enteric Pathogens

## Overview

**EnteroBase** is the reference integrated platform for bacterial population
genomics of major enteric and zoonotic pathogens, maintained by Mark Achtman's
group at the University of Warwick. It assembles publicly deposited short
reads, computes **cgMLST** (core genome MLST) and **wgMLST** genotypes,
and exposes **HierCC** hierarchical clustering for multi-resolution phylogeny
and epidemiology.

- **Reference**: Zhou Z., Alikhan N.-F., Mohamed K., Fan Y., Agama Study Group,
  Achtman M. *The EnteroBase user's guide, with case studies on Salmonella
  transmissions, Yersinia pestis phylogeny, and Escherichia core genomic
  diversity.* **Genome Research** 30(1):138–152 (2020). DOI: `10.1101/gr.251678.119`
- **Main URL**: `https://enterobase.warwick.ac.uk`
- **Documentation**: `https://enterobase.readthedocs.io/`
- **API (Swagger UI)**: `https://enterobase.warwick.ac.uk/api/v2.0/swagger-ui`
- **Volume** (published baseline, Sept 2019): **~364,690** assembled genomes
  across 7 genera; catalogue has grown substantially since — always check
  current totals on the web UI.

> [!NOTE]
> **The REST API requires authorization**. Request access by emailing
> `enterobase@warwick.ac.uk` with your intended use. The web UI and GrapeTree
> visualization are freely accessible without an account for browsing, but
> account creation is required to save workspaces.

## Why it matters for historical epidemiology

EnteroBase is the pathogen-side counterpart to `slavevoyages`, `p3k14c`,
`aadr`, and `spaam-ancient-metagenome-dir` — but for **non-TB bacteria**. It
gives direct, immediately usable access to:

- ***Yersinia pestis* historical phylogeny** — at the time of the
  Zhou et al. 2020 paper, EnteroBase integrated **56 ancient + 622 modern**
  *Y. pestis* genomes. That was a snapshot. **As of the current SPAAM
  AncientMetagenomeDir release** (verified in session), the ancient corpus
  has grown to **214 individuals across 36 projects** spanning **~5 300
  years BP → modern**, with **65 Bronze Age / LNBA** samples (origin of
  plague), **35 Justinian / First Pandemic** samples, **47 Black Death /
  Medieval** samples, and 70 modern. See the `spaam-ancient-metagenome-dir`
  skill for the verified per-project breakdown. For the up-to-date
  ancient corpus, **always query SPAAM first** and use EnteroBase as the
  modern comparison backbone.
- ***Vibrio cholerae* pandemics** — the 7 classical cholera pandemics since
  1817 and the current 7PET clonal expansion are trackable via cgMLST/HierCC.
- ***Salmonella enterica*** — including the Paratyphi C lineage linked to
  post-contact Mexican *cocoliztli* (Vågene et al. 2018).
- ***Helicobacter pylori*** — classical proxy of human population movements
  (Linz et al. 2007 *Nature*) — EnteroBase includes a dedicated *Helicobacter*
  database.
- ***Escherichia* core genomic diversity** — context for zoonotic and
  commensal evolution.

For your seminar, EnteroBase lets you **generalize the TBannotator message**
beyond MTBC: the methodology (assemble → cgMLST → HierCC → phylogeography) is
transposable to any of these genera, and EnteroBase is the working proof of
that.

## Databases available

| Genus | Key uses |
|---|---|
| ***Salmonella*** | Largest genus in EnteroBase; serovar / cgMLST / outbreak tracing |
| ***Escherichia*** / Shigella | E. coli population structure, STEC, pathotypes |
| ***Yersinia*** | ***Y. pestis* historical phylogeny**, ***Y. enterocolitica*** |
| ***Clostridioides*** | *C. difficile* ribotyping and epidemiology |
| ***Helicobacter*** | ***H. pylori* as a human migration proxy** |
| ***Vibrio*** | ***V. cholerae* pandemics, V. parahaemolyticus*** |
| ***Moraxella*** | *M. catarrhalis* respiratory epidemiology |

## Key concepts

### cgMLST — core genome MLST
A genome-wide MLST scheme using hundreds to thousands of conserved genes
(e.g., ~3,000 loci for *Salmonella*, ~1,500 for *Y. pestis*), each assigned
an integer allele. Two genomes are compared by their **allelic distance**.

### HierCC — Hierarchical Clustering of cgMLST
A single-linkage clustering of cgMLST profiles at nested allelic-distance
thresholds, giving a hierarchy of cluster labels `HC0`, `HC2`, `HC5`,
`HC10`, ..., `HC2850`. The lower the number, the tighter the cluster.

| HierCC level | Typical meaning |
|---|---|
| `HC0` – `HC5` | Recent transmission chain / outbreak |
| `HC10` – `HC50` | Local / national population |
| `HC100` – `HC400` | Sub-lineage |
| `HC900` – `HC2850` | Superlineage / subspecies |

HierCC offers the same kind of multi-resolution readout that TBannotator
gives for MTBC lineages — just expressed as integer cluster codes instead
of a lineage naming system.

### Typical metadata fields (per strain)

| Field | Example |
|---|---|
| `UID` / `Barcode` | `SAL_XX0001AA` |
| `Strain` | Original strain identifier |
| `Collection Year` | 1347 (ancient) or 2019 (modern) |
| `Country` | ISO country |
| `Region` / `Province` | Sub-national |
| `Source Niche` / `Source Details` | Human / Bovine / Environment / … |
| `Serovar` | Typhi, Paratyphi C, … (*Salmonella*) |
| `ST` / `cgST` | MLST and cgMLST sequence types |
| `HC0` … `HC2850` | HierCC cluster codes at each level |
| `Experiment accession` | ENA / SRA accession |
| `Project accession` | PRJ... |
| `Latitude` / `Longitude` | When provided |
| `Release Status` | Public / private |

## Data access

### Option A — Web UI + GrapeTree (no credentials needed for browsing)

1. Navigate to `https://enterobase.warwick.ac.uk/`
2. Choose a genus (e.g., **Yersinia**)
3. Use the Search UI: filter by `Collection Year`, `Country`, `HierCC` level,
   `Source Niche`, etc.
4. Select strains → **Visualize → GrapeTree** for an interactive cgMLST-based
   minimum-spanning tree.
5. Export selection as TSV / Newick / FASTA.

GrapeTree (Zhou et al. 2018 *Genome Res*) handles 10⁴–10⁵ genomes at cgMLST
resolution — well beyond what BEAST or RAxML can ingest.

### Option B — REST API (requires authorization)

Request access by email: `enterobase@warwick.ac.uk`. Once approved, the
Swagger UI at `https://enterobase.warwick.ac.uk/api/v2.0/swagger-ui` lists
all endpoints.

Typical Python pattern (illustrative — verify endpoint names against the
current Swagger UI before relying on them):

```python
import requests
from requests.auth import HTTPBasicAuth

API_TOKEN = "your_token_here"   # obtained after approval
BASE = "https://enterobase.warwick.ac.uk/api/v2.0"
AUTH = HTTPBasicAuth(API_TOKEN, "")

# List Y. pestis strains from a given HC400 cluster
r = requests.get(
    f"{BASE}/yersinia/straindata",
    params={
        "limit": 1000,
        "scheme": "cgMLST_v1",
        "assembly_status": "Assembled",
        "my_strains": False,
        "HC400": 3,                # example cluster
    },
    auth=AUTH,
    timeout=60,
)
data = r.json()
```

> [!WARNING]
> The API is paginated and rate-limited. For large queries, always use `limit`
> + offset/cursor pagination as documented in the Swagger UI. Do not
> parallelize aggressively — the Warwick servers are shared.

### Option C — Bulk metadata dumps

Some EnteroBase tables and cgMLST schemes are periodically mirrored on
Zenodo / Figshare by the authors for reproducibility of specific papers
(e.g., the 678-genome *Y. pestis* dataset from Zhou et al. 2020). Search
Zenodo with the paper DOI for the exact archive.

## Workflows

### Workflow 1 — *Y. pestis* historical phylogeny for a Silk Road narrative

1. In the *Yersinia* database, restrict to `Yersinia pestis` via species
   filter.
2. Filter `Collection Year` to ancient (e.g., pre-1900) **or** select by
   HierCC superlineage (`HC2000` / `HC2850`).
3. Include ancient *Y. pestis* genomes. Zhou et al. 2020 integrated 56
   at the time; the current SPAAM catalogue has grown to **214** (query
   via `spaam-ancient-metagenome-dir`). For a Silk Road narrative
   specifically, pull **Spyrou et al. 2022 *Nature*** (Issyk-Kul /
   Kyrgyzstan, 1338–1339 CE) which identified the Lake Issyk-Kul
   cemeteries as the origin of the 14th-century Black Death — a
   landmark paper to cite in any EnteroBase + SPAAM combined analysis.
4. Visualize with GrapeTree; export Newick + metadata.
5. Map geographic origins against Silk Road trade corridors (can be
   cross-referenced with **p3k14c** for archaeological context) and against
   historical plague epidemic dates.
6. Narrative: anchor the emergence of each plague pandemic to the
   corresponding clade expansion.

### Workflow 2 — *V. cholerae* 7PET pandemic tracking

1. *Vibrio* database → `Vibrio cholerae`.
2. Use HierCC to isolate the 7PET (seventh pandemic El Tor) clade.
3. Group by `Country` and `Collection Year`.
4. Build a timeline of the three waves of 7PET dispersal (Mukherjee /
   Domman / Weill et al. frameworks).
5. Overlay with historical cholera records — narrate the transition from
   classical to El Tor biotype.

### Workflow 3 — *Helicobacter pylori* as a proxy for human migrations

1. *Helicobacter* database → filter by host (*Homo sapiens*) and country.
2. Retrieve MLST / cgMLST clusters by population.
3. Reference: Linz B. et al. 2007 *Nature* — *H. pylori* population structure
   mirrors human out-of-Africa migrations.
4. Cross-reference with **`aadr`** (human genetic ancestry in the same
   regions) for a double human + pathogen coevolution argument.

### Workflow 4 — Transposing the TBannotator methodology

Structural mapping:

| TBannotator concept | EnteroBase equivalent |
|---|---|
| MTBC lineage call (Senelle, Coll, etc.) | HierCC level (HC0–HC2850) |
| SPDI clustering | cgST + HierCC |
| Lineage curation via expert review | Agama Study Group curation |
| LLM-based metadata enrichment | No equivalent — opportunity to pitch |

**Seminar angle**: EnteroBase shows that the cgMLST/HierCC approach works at
>300k-genome scale for enterics. TBannotator does the same *with added
agentic-AI enrichment* (metadata cleaning, lineage curation, text-mining of
150k articles) for MTBC. The two platforms are complementary and speak to
an emerging paradigm in bacterial population genomics.

## Ancient pathogen cross-reference

For the ancient-DNA side of EnteroBase genera, pair this skill with
**`spaam-ancient-metagenome-dir`**:

| Genus | Notable ancient publications indexed in both |
|---|---|
| *Y. pestis* | Rasmussen 2015, Andrades Valtueña 2017/2022, Spyrou 2018/2019/2022, Bos 2011 |
| *S. enterica* Paratyphi C | Vågene et al. 2018 (Mexican cocoliztli) |
| *V. cholerae* | Dobson / Devault 2014 |
| *M. leprae* | Schuenemann et al. 2013 / 2018 (not EnteroBase: separate resources) |

## Caveats

- **API access is gated.** Plan ahead: email Warwick before you need the
  data, not the day of your analysis.
- **cgMLST ≠ SNP trees.** cgMLST counts allelic differences, not mutations.
  It is fast and scalable but less precise for tip-dating than SNP-based
  BEAST analyses. For ancient samples with tip-dating, use the raw reads
  via `spaam-ancient-metagenome-dir` + nf-core/eager + BEAST.
- **HierCC is single-linkage.** It can merge unrelated clusters via chaining.
  Always validate a HierCC cluster against a phylogeny built with a
  standard method (IQ-TREE, RAxML) before publishing it as a lineage.
- **Metadata are heterogeneous.** Source, host, and geographic fields are
  authoritative when curated by the Agama Study Group, heterogeneous
  otherwise. Always inspect the `Release Status` and curator annotations.
- **Rate limits & fair use.** EnteroBase is hosted on a shared academic
  infrastructure. Do not scrape.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`spaam-ancient-metagenome-dir`** | Raw ancient reads for *Y. pestis*, *V. cholerae*, *S. enterica* |
| **`aadr`** | Ancient human hosts for the same skeletons |
| **`p3k14c`** | Archaeological context for ancient pathogen sites |
| **`slavevoyages`** | Post-colonial dispersal (e.g., *V. cholerae* 7PET, *S. enterica*) |
| **TBannotator MCP** | Analogous platform for MTBC — compare methodologies |
| **GrapeTree** | Visualization of cgMLST/HierCC trees at 10⁵ genomes scale |
| **nf-core/bactmap**, **nf-core/eager** | Pipelines feeding EnteroBase-ready assemblies |

## Citation

```bibtex
@article{zhou2020enterobase,
  title   = {The EnteroBase user's guide, with case studies on Salmonella
             transmissions, Yersinia pestis phylogeny, and Escherichia core
             genomic diversity},
  author  = {Zhou, Zhemin and Alikhan, Nabil-Fareed and Mohamed, Khaled and
             Fan, Yulei and the Agama Study Group and Achtman, Mark},
  journal = {Genome Research},
  volume  = {30},
  number  = {1},
  pages   = {138--152},
  year    = {2020},
  doi     = {10.1101/gr.251678.119}
}

@article{zhou2018grapetree,
  title   = {GrapeTree: visualization of core genomic relationships among
             100,000 bacterial pathogens},
  author  = {Zhou, Zhemin and Alikhan, Nabil-Fareed and Sergeant, Martin J.
             and Luhmann, Nina and Vaz, C{\'a}tia and Francisco, Alexandre P.
             and Carri{\c{c}}o, Jo{\~a}o Andr{\'e} and Achtman, Mark},
  journal = {Genome Research},
  volume  = {28},
  number  = {9},
  pages   = {1395--1404},
  year    = {2018},
  doi     = {10.1101/gr.232397.117}
}
```
