---
name: glottolog
description: >-
  Query Glottolog, the reference catalogue of the world's languages, language
  families, and dialects (8,238 languoids, 246 families, 183 isolates, 227
  sign languages). Provides stable Glottocode identifiers, genealogical
  classification, geographic coordinates, macroarea, ISO 639-3 mapping,
  endangerment status, and 460k+ bibliographic references. Foundation layer
  for any cross-linguistic or biology-language coevolution analysis.

  Use when: resolving a language name to a stable Glottocode, fetching the
  genealogical classification of a population's language, joining a genetic
  or pathogen dataset to linguistic metadata, building a language-family
  control for comparative analyses, or backing a D-PLACE / eco-anthropology
  workflow with authoritative language identifiers.
---

# Glottolog — Catalogue of the World's Languages

## Client (resilient, tool-first)

A stdlib-only client ships with this skill (`src/glottolog_client/`, nothing to
pip-install). Filter languoids without hand-rolling pandas:

```bash
SRC=<this skill>/src
export GLOTTOLOG_FILE=/path/to/glottolog-cldf/cldf/languages.csv
PYTHONPATH="$SRC" python3 -m glottolog_client languages --macroarea Africa --bbox -35 -20 15 52 --tsv
PYTHONPATH="$SRC" python3 -m glottolog_client.smoke_test   # offline, bundled fixture
```

`languages(macroarea=..., bbox=(S,W,N,E), level=..., name=...)` returns `list[dict]`
with stable keys `glottocode, name, level, family, macroarea, lat, lon, iso639`.
Glottolog encodes family as a parent Glottocode (not a name), so for a family-NAME
filter use `wals`. `inspect` prints the real header; reads .csv/.xlsx.

## Overview

**Glottolog** is the reference open catalogue of the world's languages,
language families, and dialects, maintained at the Max Planck Institute for
Evolutionary Anthropology (Leipzig) by Harald Hammarström, Robert Forkel,
Martin Haspelmath and Sebastian Bank. It assigns a **stable, persistent
identifier** (the *Glottocode*) to every language, family, and dialect and
provides a bibliographically backed genealogical classification — the
foundation on which most cross-linguistic databases (including **D-PLACE**,
**WALS**, **Phoible**, **Lexibank**) now stand.

- **Canonical citation**: Hammarström H., Forkel R., Haspelmath M. & Bank S.
  *Glottolog* [current version]. Max Planck Institute for Evolutionary
  Anthropology, Leipzig.
- **Current release**: **Glottolog 5.3** (March 2026) — confirm current
  version on `https://glottolog.org/` before citing
- **Web interface**: `https://glottolog.org/`
- **GitHub (raw)**: `https://github.com/glottolog/glottolog`
- **GitHub (CLDF)**: `https://github.com/glottolog/glottolog-cldf`
- **Zenodo (DOI-pinned releases)**: `https://zenodo.org/communities/glottolog`
- **License**: **CC BY 4.0**

> [!NOTE]
> Glottolog has no dynamic REST API. Access is via the website (HTML pages
> with stable URLs per Glottocode), the versioned GitHub repo, the CLDF
> distribution, or the `pyglottolog` / `pycldf` Python packages. Pin a
> version or commit hash when citing.

## Catalogue size (Glottolog 5.3)

| Category | Count |
|---|---|
| Spoken L1 languages | 7,674 |
| Sign languages | 227 |
| Language families | 246 |
| Isolates | 183 |
| Unclassifiable | 128 |
| Pidgins | 87 |
| Unattested | 68 |
| Artificial | 31 |
| Speech registers | 19 |
| Mixed languages | 4 |
| **Total languoids** | **8,238** |
| References | 460,382 |

## Why it matters for MTBC × anthropology

Glottolog is a **backbone** skill rather than a primary data source for
pathogens: it does not directly describe TB biology. Its value is to
provide the **authoritative linguistic identifier layer** for any
coevolution analysis that mixes language, genetics and pathogen data.

Concrete uses for your research:

1. **Stable join keys.** When cross-referencing ancient-human populations
   (AADR), cultural variables (D-PLACE), or pathogen sampling metadata,
   **Glottocode** is the only stable identifier that survives renaming.
   ISO 639-3 codes are not enough — many languages lack one, and dialects
   are not covered by ISO.
2. **Language-family control.** Many comparative analyses in
   eco-anthropology require controlling for descent from a common linguistic
   ancestor (Galton's problem). Glottolog's tree gives you the grouping
   structure; D-PLACE's Bayesian phylogenies give you the dated topologies.
3. **Geographic centroids.** Each languoid has coordinates (geographical
   centre or historical location), letting you do spatial joins between
   modern TB sampling locations and the languages historically spoken
   there.
4. **Macroareas.** Glottolog's six macroareas (Africa, Eurasia, Papunesia,
   Australia, North America, South America) are a standard coarse-scale
   grouping used in comparative linguistics and useful as a control covariate.
5. **Endangerment status (AES).** Endangered-language speakers often live
   in under-sampled, under-surveilled regions — useful context when
   discussing TB surveillance gaps in a narrative framing.

## Data model

### Languoid hierarchy

Glottolog organises all entities as **languoids**, a superset that includes:

- **Family**: a group sharing descent from a common ancestor
- **Language**: a distinct communication system with sufficient attestation
- **Dialect**: a mutually intelligible variety of a language (coverage uneven)
- **Isolate**: a language with no demonstrated relatives (treated as a family
  of one)

Every languoid has a parent (except top-level families), so the database
forms a **forest** (multiple trees, one per family).

### Glottocode

A stable identifier of the form `[a-z0-9]{4}[0-9]{4}`, e.g. `stan1293`
(Standard English), `nucl1301` (Nuclear Mbam), `tubu1245`. Glottocodes are
**never reused**; merging/splitting operations leave old codes as
redirects.

### Key fields per languoid

| Field | Meaning |
|---|---|
| `id` / `Glottocode` | Stable identifier |
| `name` | Glottolog canonical name |
| `level` | `family` / `language` / `dialect` |
| `category` | Spoken L1, sign, pidgin, mixed, artificial, etc. |
| `parent_id` | Glottocode of parent languoid (tree edge) |
| `classification` | Colon-separated path of ancestor Glottocodes |
| `subclassification` | Newick-formatted subtree beneath this languoid |
| `iso639P3code` | ISO 639-3 code (if any) |
| `macroarea` | Africa / Eurasia / Papunesia / Australia / N America / S America |
| `latitude`, `longitude` | Decimal degrees (WGS84), geographic or historical |
| `aes` | Agglomerated Endangerment Status (scale from Not Endangered → Extinct) |
| `med` | Most Extensive Description — the best descriptive reference |
| `bibliography` | All references keyed to this languoid |

## Data access

### Option A — Web lookup (browse, single-language)

Every languoid has a stable URL:
`https://glottolog.org/resource/languoid/id/<glottocode>`

Example: `https://glottolog.org/resource/languoid/id/stan1293`

The page exposes classification, coordinates, references, ISO code, and
descendants. Useful for a quick manual check.

### Option B — CLDF distribution (recommended for analysis)

```bash
git clone https://github.com/glottolog/glottolog-cldf.git
```

Load with `pycldf`:

```python
from pycldf import Dataset
ds = Dataset.from_metadata("glottolog-cldf/cldf/cldf-metadata.json")

# Language table
for lang in ds["LanguageTable"]:
    if lang["Macroarea"] == "Africa" and lang["Latitude"]:
        print(lang["ID"], lang["Name"], lang["Latitude"], lang["Longitude"])
```

The CLDF StructureDataset ships with these parameters encoded in
`ParametersTable`: `level`, `category`, `classification`, `subclassification`,
`med`, `medovertime`, `aes`, `bib`.

### Option C — `pyglottolog` (native Python API)

```bash
pip install pyglottolog
git clone https://github.com/glottolog/glottolog.git
```

```python
from pyglottolog import Glottolog
g = Glottolog("./glottolog")  # path to the cloned raw repo

english = g.languoid("stan1293")
print(english.classification)           # list of ancestors
print(english.macroareas)
print(english.latitude, english.longitude)
print([r.key for r in english.sources]) # bibliographic keys

# Iterate all languages in a family
for lang in g.languoid("indo1319").descendants:
    if lang.level.name == "language":
        print(lang.id, lang.name)
```

### Option D — Flat CSV exports

The raw Glottolog repo ships a `languoids.csv` under its distribution format,
and each CLDF release ships a versioned CSV dump. Both are easy to read
with pandas for ad-hoc joins.

## Workflows

### Workflow 1 — Resolve a population name to a Glottocode

You want to join a TB metadata row with `country = "Ghana"` and
`population = "Akan"` to Glottolog.

```python
from pyglottolog import Glottolog
g = Glottolog("./glottolog")

# Search by name (fuzzy)
matches = [l for l in g.languoids()
           if "akan" in (l.name or "").lower() and l.level.name == "language"]
for l in matches:
    print(l.id, l.name, l.macroareas, (l.latitude, l.longitude))
```

Always verify with the classification path — many names collide across
families.

### Workflow 2 — Build a family-level control covariate

For a set of TB samples with coordinates, tag each with the family of the
closest Glottolog language within a radius.

```python
import pandas as pd
from scipy.spatial import cKDTree

lang = pd.read_csv("glottolog-cldf/cldf/languages.csv")
lang = lang.dropna(subset=["Latitude", "Longitude"])

tree = cKDTree(lang[["Latitude", "Longitude"]].values)

tb_samples = pd.read_csv("tb_samples.tsv", sep="\t")
d, idx = tree.query(tb_samples[["lat", "lon"]].values, k=1)
tb_samples["glottocode"] = lang.iloc[idx]["ID"].values
tb_samples["family"] = lang.iloc[idx]["Family_ID"].values
```

Then use `family` as a random effect / block factor in downstream models
to control for linguistic non-independence.

### Workflow 3 — Geographic spread of a language family vs TB lineage

Goal: test whether the geographic footprint of an Indo-European (say) branch
coincides with the range of a TB sublineage.

1. Extract all languages with a given ancestor Glottocode (e.g. Indo-European
   `indo1319`).
2. Plot their coordinates on a world map (GeoPandas).
3. Overlay TB lineage sampling locations from TBannotator.
4. Quantify overlap (Jaccard or a point-pattern test).
5. Cross-reference with D-PLACE Bantu / Austronesian / Indo-European
   Bayesian phylogenies for a time-calibrated narrative.

### Workflow 4 — Link to D-PLACE societies

Glottolog is the **join table** between D-PLACE societies and language
classification.

```python
soc = pd.read_csv("dplace-data/csv/societies.csv")
lang = pd.read_csv("glottolog-cldf/cldf/languages.csv")

joined = soc.merge(lang, left_on="glottocode", right_on="ID", how="left")
```

Now `joined` has both the cultural/subsistence variables (D-PLACE) and the
linguistic classification (Glottolog), ready for coevolution tests.

### Workflow 5 — Historical / extinct languages for ancient contexts

When discussing ancient TB contexts, Glottolog is the only catalogue that
systematically includes **extinct** and **historically attested** languages
(Sumerian, Hittite, Classical Nahuatl, etc.) with coordinates. Useful for
framing pre-modern or ancient-DNA narratives.

## Caveats

- **Classifications change.** Glottolog updates taxonomy between releases.
  Pin the version in citations (e.g. *Glottolog 5.3, Zenodo DOI …*).
- **Dialect coverage is uneven.** Dialects are catalogued where authors
  have contributed data; absence does not mean non-existence.
- **Coordinates are centroids or attestation points.** They do not represent
  the full extent of a language's range — for range data, use WGS
  (Ethnologue) or WALS, or compute a convex hull over multiple dialect points.
- **No speaker counts in Glottolog itself.** Use Ethnologue or UNESCO Atlas
  if you need speaker numbers — but beware licensing.
- **AES endangerment scale ≠ Ethnologue EGIDS.** They are correlated but
  not identical; cite the scale used.
- **Not a lexical database.** For vocabulary/phonology, chain to Phoible,
  Lexibank, NorthEuraLex, or CLICS.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`d-place`** | Cultural + environmental variables keyed to Glottocodes |
| **`aadr`** | Ancient human genetic data joinable via inferred language of population |
| **`p3k14c`** | Archaeological sites joinable via modern-country + nearest languoid |
| **`spaam-ancient-metagenome-dir`** | Sample country → Glottolog macroarea for coarse grouping |
| **`enterobase`** | Modern bacterial samples joinable via country + nearest languoid |
| **`slavevoyages`** | Embarkation / disembarkation regions → African / American languoids |
| **`pyglottolog` / `pycldf`** | Native Python APIs |
| **D-PLACE Bayesian language phylogenies** | Time-calibrated trees for phylogenetic comparative methods |
| **WALS / Phoible / Lexibank** | Trait, phonology, lexical databases also keyed by Glottocode |

## Citation

```bibtex
@misc{hammarstrom2026glottolog,
  title     = {Glottolog 5.3},
  author    = {Hammarstr{\"o}m, Harald and Forkel, Robert and
               Haspelmath, Martin and Bank, Sebastian},
  year      = {2026},
  publisher = {Max Planck Institute for Evolutionary Anthropology},
  address   = {Leipzig},
  url       = {https://glottolog.org/},
  note      = {License CC BY 4.0. Version-pinned release on Zenodo.}
}
```

**Always pin the version** you used (e.g. 5.3) and prefer the Zenodo DOI
of that release for reproducibility.
