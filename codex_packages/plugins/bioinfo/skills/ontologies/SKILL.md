---

name: ontologies
description: >-
  Index and access helper for the Open Biological and Biomedical Ontology
  Foundry (OBO Foundry, 150+ active ontologies) and its anchor resource,
  the NCBI Taxonomy. Provides canonical normalisation vocabularies for
  species and strains (NCBITaxon / LPSN), diseases (DOID), infectious
  disease concepts (IDO), environments (ENVO), chemicals (ChEBI),
  gazetteer places (GAZ), and host–microbiome interactions (OHMI).
  The glue that makes metadata from `aadr`, `enterobase`,
  `spaam-ancient-metagenome-dir`, `bacdive`, `pubtator`, and the
  anthropology-layer skills interoperable.

  Use when: normalizing a free-text species / strain / disease / host /
  environment / place field to a canonical identifier, adding
  ontology-coded metadata to a manuscript or dataset, checking whether
  a term is already in an existing OBO ontology, or producing
  Linked-Data-compliant annotations for a publication's supplementary
  material.
---

# Ontologies : OBO Foundry + NCBI Taxonomy

## Overview

The **Open Biological and Biomedical Ontology (OBO) Foundry** is the
reference open collaborative for biomedical ontologies, coordinated
by Barry Smith, Michael Ashburner, Suzanna Lewis, Chris Mungall and
colleagues. It hosts **150+ actively maintained ontologies** covering
every corner of biology and biomedicine, under a shared set of
principles: open licence, shared identifier space, stable URIs,
versioning, orthogonality.

The **NCBI Taxonomy** is the canonical taxonomic database of life at
the U.S. National Library of Medicine. Via the **NCBITaxon** OBO port,
it also functions as an ontology, the backbone for every species /
strain / lineage normalisation in biomedical data.

Together, OBO Foundry + NCBI Taxonomy form the **normalisation layer**
of your constellation: the shared vocabulary that makes free-text
metadata from disparate sources (SPAAM, AADR, EnteroBase, BacDive,
PubTator, D-PLACE) point to the same entities.

- **OBO Foundry portal**: `https://obofoundry.org/`
- **OBO Foundry GitHub org**: `https://github.com/OBOFoundry`
- **NCBI Taxonomy browser**: `https://www.ncbi.nlm.nih.gov/taxonomy`
- **NCBI Taxonomy FTP (bulk)**: `https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/`
- **NCBITaxon OBO port**: `https://obofoundry.org/ontology/ncbitaxon.html`
- **EBI Ontology Lookup Service (OLS)**: `https://www.ebi.ac.uk/ols4/`
, the unified web/API front-end to OBO ontologies

### Key references

- **OBO Foundry 2007 (founding paper)**: Smith B., Ashburner M.,
  Rosse C., Bard J., Bug W., Ceusters W., et al. *The OBO Foundry:
  coordinated evolution of ontologies to support biomedical data
  integration.* **Nature Biotechnology** 25(11): 1251–1255 (2007).
  DOI: `10.1038/nbt1346`
- **OBO Foundry 2021**: Jackson R., Matentzoglu N., Overton J.A.,
  Vita R., Balhoff J.P., Buttigieg P.L., et al. *OBO Foundry in 2021:
  operationalizing open data principles to evaluate ontologies.*
  **Database (Oxford)** 2021: baab069 (2021). DOI:
  `10.1093/database/baab069`
- **NCBI Taxonomy**: Schoch C.L., Ciufo S., Domrachev M., Hotton C.L.,
  Kannan S., Khovanskaya R., et al. *NCBI Taxonomy: a comprehensive
  update on curation, resources and tools.* **Database (Oxford)**
  2020: baaa062 (2020). DOI: `10.1093/database/baaa062`
- **License**: OBO ontologies, typically CC-BY or CC0, per ontology;
  NCBI Taxonomy, public domain

## Why it matters for MTBC × anthropology

Across the constellation's 27 other skills, each resource uses its
own metadata vocabulary: SPAAM uses `singlegenome_species` as
free-text strings, EnteroBase uses Warwick-internal names, BacDive
uses LPSN type-strain labels, AADR uses free-text `Group Label`,
PubTator uses NCBI Taxonomy IDs. **Ontologies are how you make all
of these talk to the same underlying concept.**

Concrete benefits for your TB / anthropology work:

1. **Species and strain normalisation.** A sample tagged
   `"Mycobacterium tuberculosis var. bovis"` in one paper,
   `"Mycobacterium bovis"` in another, and `"M. bovis BCG Pasteur"`
   in a third all resolve to **NCBITaxon:1765** (*M. bovis*), with
   deeper strain-level IDs when relevant.
2. **Disease normalisation.** Free-text "TB", "tuberculosis",
   "pulmonary tuberculosis", "active TB disease" all map to
   **DOID:552** (tuberculosis) or its more specific children, letting
   you aggregate across heterogeneous literature.
3. **Environment normalisation.** An archaeological context described
   as "cave sediment", "cave floor deposit", "karst cave", or
   "limestone cavern" all maps to the **ENVO** cave class, useful
   when filtering `spaam-ancient-metagenome-dir` environmental samples.
4. **Gazetteer for modern places.** The **GAZ** ontology provides
   hierarchical codes for countries, regions, and named places.
   For ancient places, use `pleiades` instead (they are complementary).
5. **Linked Data interoperability.** When publishing a dataset,
   coding metadata against OBO IRIs (e.g.
   `http://purl.obolibrary.org/obo/NCBITaxon_1773`) makes it
   FAIR-compliant out of the box.

## OBO ontologies most relevant to the constellation

| Prefix | Ontology | Coverage | Use in constellation |
|---|---|---|---|
| **NCBITaxon** | NCBI Taxonomy port | ~2.5M taxa, all cellular life + viruses | Species/strain for every pathogen skill |
| **LPSN** | List of Prokaryotic names with Standing in Nomenclature | ~19k validly published bacterial names | Complement to NCBITaxon for bacterial nomenclature; source maintained by DSMZ (same as BacDive) |
| **DOID** | Disease Ontology | ~10k diseases | TB (**DOID:552**), bovine TB, leprosy, plague |
| **IDO** | Infectious Disease Ontology | Pathogen + disease concepts | Host-pathogen interaction vocabulary |
| **ENVO** | Environment Ontology | Physical + biotic environments | Sample site context in SPAAM, p3k14c, card |
| **ChEBI** | Chemical Entities of Biological Interest | ~160k molecular entities | Drugs, metabolites (anti-TB: isoniazid, rifampicin, pyrazinamide, ethambutol) |
| **GAZ** | Gazetteer | Hierarchical places | Modern place normalisation |
| **GO** | Gene Ontology | Biological processes, functions, components | Functional annotation of TB genes |
| **UBERON** | Integrated anatomy ontology | Tissues, organs | Sample tissue origin (lung, bone, calculus…) |
| **CL** | Cell Ontology | Cell types | Host immune cells, bacterial cell types |
| **OHMI** | Ontology of Host-Microbiome Interactions | Host-microbe relations | Conceptual framework for coevolution narrative |
| **OBI** | Ontology of Biomedical Investigations | Experimental processes | Methods and assay descriptions |
| **SYMP** | Symptom Ontology | Clinical symptoms | Patient phenotype coding |

## Key concepts : NCBI Taxonomy for MTBC

The MTBC occupies a well-defined subtree under **NCBITaxon:77643**
(*Mycobacterium tuberculosis complex*):

| Rank | Taxon | NCBITaxon ID |
|---|---|---|
| Complex | *Mycobacterium tuberculosis complex* | 77643 |
| Species | *Mycobacterium tuberculosis* | **1773** |
| Species | *Mycobacterium africanum* | 33894 |
| Species | *Mycobacterium canettii* | 78331 |
| Species | *Mycobacterium bovis* | **1765** |
| Sub-species | *M. bovis* var. *bovis* BCG | 33892 |
| Species | *Mycobacterium caprae* | 158067 |
| Species | *Mycobacterium microti* | 1806 |
| Species | *Mycobacterium pinnipedii* | 175792 |
| Species | *Mycobacterium orygis* | 1305738 |
| Species | *Mycobacterium mungi* | 1844474 |

These IDs are the canonical join keys. When you extract a strain from
`spaam-ancient-metagenome-dir` or `enterobase` or TBannotator and want
to align with BacDive, NCBI Pathogen Detection, or PubTator
annotations, **always normalise first on NCBITaxon**.

### Individual strain IDs

For well-known reference strains, NCBI Taxonomy has dedicated taxa:

- **H37Rv** (reference MTBC lab strain) : NCBITaxon:83332
- **H37Ra** (attenuated) : NCBITaxon:419947
- **CDC1551** : NCBITaxon:83331
- **BCG Pasteur 1173P2** : NCBITaxon:410289

For custom field strains, NCBI Taxonomy normally does not provide
per-isolate IDs, use the species-level ID + the original sample
accession (`biosample_acc`, `strain`) as identifier.

## Data access

### Option A : Ontology Lookup Service (OLS4) at EMBL-EBI

The unified entry point to all OBO ontologies:

- **Web UI**: `https://www.ebi.ac.uk/ols4/`
- **API**: `https://www.ebi.ac.uk/ols4/api/`
- **Swagger**: `https://www.ebi.ac.uk/ols4/docs/api`

```bash
# Resolve a term by label
curl -sL "https://www.ebi.ac.uk/ols4/api/search?q=tuberculosis&ontology=doid&exact=true"

# Get a term by IRI
curl -sL "https://www.ebi.ac.uk/ols4/api/ontologies/doid/terms?iri=http://purl.obolibrary.org/obo/DOID_552"

# Get children of a term
curl -sL "https://www.ebi.ac.uk/ols4/api/ontologies/doid/terms/http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252FDOID_552/children"
```

### Option B : Direct download of OBO/OWL files

Each OBO Foundry ontology has a stable download URL:

```bash
# NCBITaxon as OWL
curl -sL "http://purl.obolibrary.org/obo/ncbitaxon.owl" -o ncbitaxon.owl

# Disease Ontology (DOID) as OBO
curl -sL "http://purl.obolibrary.org/obo/doid.obo" -o doid.obo

# ENVO
curl -sL "http://purl.obolibrary.org/obo/envo.owl" -o envo.owl
```

Files can be large (NCBITaxon OWL is several GB).

### Option C : `pronto` (Python)

`pronto` is a lightweight pure-Python OBO/OWL parser.

```bash
pip install pronto
```

```python
import pronto

doid = pronto.Ontology("http://purl.obolibrary.org/obo/doid.obo")

# Find tuberculosis
tb = doid["DOID:552"]
print(tb.name)            # "tuberculosis"
print([c.id for c in tb.subclasses(distance=1)])
# e.g. ['DOID:4945', 'DOID:12385', ...]
```

### Option D : `pyobo` / `bioregistry` (Python, Gyori / Hoyt lab)

For cross-ontology normalisation:

```bash
pip install pyobo bioregistry
```

```python
from pyobo import get_name_id_mapping
name2id = get_name_id_mapping("doid")
print(name2id.get("tuberculosis"))   # 'DOID:552'
```

### Option E : NCBI Taxonomy dedicated tools

- **NCBI Datasets CLI**: `conda install -c conda-forge ncbi-datasets-cli`
- **ete3** (Python): has a `NCBITaxa` class for programmatic access
- **TaxonKit** (Go): fast command-line manipulation of NCBI Taxonomy

```python
# ete3 example
from ete3 import NCBITaxa
ncbi = NCBITaxa()
# Get the lineage of M. bovis
lineage = ncbi.get_lineage(1765)
# [1, 131567, 2, 1783272, 201174, 85007, 1762, 1763, 77643, 1765]
names = ncbi.get_taxid_translator(lineage)
print([names[t] for t in lineage])
# ['root', 'cellular organisms', 'Bacteria', ..., 'Mycobacterium bovis']
```

## Workflows

### Workflow 1 : Normalise species across heterogeneous sources

Goal: produce a unified NCBITaxon-keyed table from SPAAM, EnteroBase,
BacDive, and TBannotator species names.

```python
from ete3 import NCBITaxa
ncbi = NCBITaxa()

def to_ncbitaxon(name):
    hit = ncbi.get_name_translator([name])
    if name in hit and hit[name]:
        return hit[name][0]
    # Try synonyms, fuzzy match, etc.
    return None

# Apply to a SPAAM extract
spaam["tax_id"] = spaam.singlegenome_species.map(to_ncbitaxon)
```

Entries that fail to resolve need manual curation (typos, dialectal
spelling, unvalidated species).

### Workflow 2 : Filter SPAAM or EnteroBase to MTBC

Goal: use the MTBC subtree (NCBITaxon:77643) to extract every
MTBC-related sample from a mixed catalogue.

```python
from ete3 import NCBITaxa
ncbi = NCBITaxa()

MTBC_ROOT = 77643
mtbc_descendants = set(ncbi.get_descendant_taxa(MTBC_ROOT, intermediate_nodes=True))
mtbc_descendants.add(MTBC_ROOT)

# Apply to any dataset with a tax_id column
mtbc_samples = df[df.tax_id.isin(mtbc_descendants)]
```

This is cleaner than string-matching on `"Mycobacterium"` because it
automatically handles all named species in the complex without
missing any.

### Workflow 3 : Disease normalisation for publication metadata

Goal: normalise disease mentions to DOID for cross-paper comparison.

```python
import pronto

doid = pronto.Ontology("http://purl.obolibrary.org/obo/doid.obo")
# Build a label → ID index (including synonyms)
label2id = {}
for term in doid.terms():
    label2id[term.name.lower()] = term.id
    for syn in term.synonyms:
        label2id[str(syn).lower()] = term.id

def normalise_disease(name):
    return label2id.get(name.lower())

normalise_disease("tuberculosis")          # 'DOID:552'
normalise_disease("bovine tuberculosis")   # 'DOID:0060153' (or similar)
```

### Workflow 4 : Environment normalisation for SPAAM environmental samples

Goal: map the `feature` / `material` fields from
`spaam-ancient-metagenome-dir` (environmental table) to ENVO terms.

```python
import pronto
envo = pronto.Ontology("http://purl.obolibrary.org/obo/envo.owl")

# Manual mapping table for the SPAAM controlled vocabulary
material_to_envo = {
    "lake sediment": "ENVO:00002007",     # lake sediment
    "marine sediment": "ENVO:00002004",   # marine sediment
    "permafrost": "ENVO:00000134",        # permafrost
    "cave sediment": "ENVO:00002011",     # ... (verify in ENVO)
    ...
}
```

This lets you publish SPAAM-derived datasets with ENVO-coded sample
contexts, required by many FAIR-compliant repositories.

### Workflow 5 : Build a manuscript-ready taxonomy appendix

Goal: for a TB phylogenomics paper, produce a table listing every
species and strain mentioned with its NCBITaxon ID and canonical name.

```python
species_list = list(df.singlegenome_species.dropna().unique())
hit = ncbi.get_name_translator(species_list)

table = []
for sp in species_list:
    tid = hit.get(sp, [None])[0]
    if tid is not None:
        lineage = ncbi.get_lineage(tid)
        rank = ncbi.get_rank([tid])[tid]
        table.append({"species": sp, "ncbitaxon": tid, "rank": rank,
                      "full_lineage": lineage})
```

## Caveats

- **Ontology coverage is uneven.** Well-maintained ontologies (GO,
  ChEBI, DOID, NCBITaxon) are comprehensive; smaller / newer
  ontologies may have gaps. Check via OLS before committing.
- **Name → ID mapping is fuzzy at the edges.** Synonyms, typos,
  dialectal spellings, and obsolete names all cause failures. Always
  budget manual curation for 1–10% of entries.
- **NCBI Taxonomy lags the bacterial nomenclature.** LPSN (DSMZ) is
  the official registry for bacterial names; NCBI Taxonomy
  sometimes takes months to add a new validly published name. For
  most recent bacterial work, cross-check LPSN.
- **Obsolete taxa / ontology drift.** OBO ontologies evolve; a term
  ID that existed in one version may be merged, split, or obsoleted
  in the next. Pin the version (release date or Git commit hash)
  in your Methods.
- **OBO vs OWL format choice.** OBO is easier for humans; OWL is
  more expressive. `pronto` parses both; some tools prefer one or
  the other.
- **Don't conflate NCBITaxon with formal taxonomy.** NCBITaxon is a
  database, not an authoritative classification. For bacteria, LPSN
  + the ICSP are the official bodies; for animals, ICZN; for plants,
  ICN. NCBITaxon mirrors these approximately.
- **GAZ is limited for ancient places.** The OBO GAZ ontology
  covers modern places primarily. For ancient/historical places,
  use `pleiades` instead.
- **Large ontologies stress memory.** NCBITaxon OWL is ~2.5 GB and
  `pronto`-parsing it requires significant RAM. Prefer `ete3` +
  NCBI Taxonomy SQLite dump for high-throughput work.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`bacdive`** | Uses LPSN + NCBI Taxonomy natively |
| **`enterobase`** | Genus-specific typing on NCBI Taxonomy subtrees |
| **`ncbi-pathogen-detection`** | NCBI ecosystem, same Taxonomy backbone |
| **`pathogens-portal`** | ENA uses NCBI Taxonomy IDs |
| **`spaam-ancient-metagenome-dir`** | Free-text species → NCBITaxon for joins |
| **`aadr`** | Host species field → NCBITaxon |
| **`pubtator`** | Species annotations normalised to NCBI Taxonomy |
| **`pleiades`** | Ancient place gazetteer (complementary to GAZ) |
| **`openalex`** | Concept tags (indirectly related to ontologies) |
| **`ete3`** / **`taxonkit`** | Canonical tools for NCBI Taxonomy lookups |
| **`pronto`** / **`pyobo`** / **`bioregistry`** | Python ontology libraries |
| **EMBL-EBI OLS4** | Unified ontology web/API front-end |
| **LPSN** | Bacterial nomenclature authority (DSMZ) |

## Citations

```bibtex
@article{smith2007obo,
  title   = {The OBO Foundry: coordinated evolution of ontologies to
             support biomedical data integration},
  author  = {Smith, Barry and Ashburner, Michael and Rosse, Cornelius and
             Bard, Jonathan and Bug, William and Ceusters, Werner and
             Goldberg, Louis J. and Eilbeck, Karen and Ireland, Amelia and
             Mungall, Christopher J. and The OBI Consortium and
             Leontis, Neocles and Rocca-Serra, Philippe and Ruttenberg, Alan
             and Sansone, Susanna-Assunta and Scheuermann, Richard H. and
             Shah, Nigam and Whetzel, Patricia L. and Lewis, Suzanna},
  journal = {Nature Biotechnology},
  volume  = {25},
  number  = {11},
  pages   = {1251--1255},
  year    = {2007},
  doi     = {10.1038/nbt1346}
}

@article{jackson2021obo,
  title   = {OBO Foundry in 2021: operationalizing open data principles
             to evaluate ontologies},
  author  = {Jackson, Rebecca and Matentzoglu, Nicolas and Overton, James A.
             and Vita, Randi and Balhoff, James P. and Buttigieg, Pier Luigi
             and others},
  journal = {Database (Oxford)},
  volume  = {2021},
  pages   = {baab069},
  year    = {2021},
  doi     = {10.1093/database/baab069}
}

@article{schoch2020ncbitaxonomy,
  title   = {NCBI Taxonomy: a comprehensive update on curation, resources
             and tools},
  author  = {Schoch, Conrad L. and Ciufo, Stacy and Domrachev, Mikhail and
             Hotton, Carol L. and Kannan, Sivakumar and Khovanskaya, Rogneda
             and Leipe, Detlef and McVeigh, Richard and O'Neill, Kathleen
             and Robbertse, Barbara and Sharma, Shobha and Soussov, Vladimir
             and Sullivan, John P. and Sun, Lu and Turner, Seán and
             Karsch-Mizrachi, Ilene},
  journal = {Database (Oxford)},
  volume  = {2020},
  pages   = {baaa062},
  year    = {2020},
  doi     = {10.1093/database/baaa062}
}
```

**Remember**: in Methods, cite the **specific ontologies and versions**
you used, plus the NCBI Taxonomy snapshot date. Ontologies drift;
reproducibility depends on pinning.
