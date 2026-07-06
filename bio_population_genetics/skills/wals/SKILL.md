---
name: wals
description: >-
  Query WALS, the World Atlas of Language Structures (Dryer & Haspelmath
  eds., Max Planck Institute) — the reference open database of typological
  features (phonology, morphology, syntax, word order, lexicon) for ~3,500
  languages worldwide. Provides 192 typological parameters with ~76,000
  codings, all keyed to Glottocodes for joining with the rest of the
  linguistic-anthropology constellation.

  Use when: testing whether a linguistic typological feature correlates
  with the geographic distribution of an MTBC lineage, building a
  language-typology covariate for cross-cultural eco-anthropology
  analyses, controlling for typological similarity in comparative
  studies, or producing a typological profile of populations relevant
  to a phylogeographic narrative.
---

# WALS — World Atlas of Language Structures

## Client (resilient, tool-first)

A stdlib-only client ships with this skill (`src/wals_client/`, nothing to
pip-install). Filter languages without hand-rolling pandas:

```bash
SRC=<this skill>/src
export WALS_FILE=/path/to/wals-cldf/cldf/languages.csv
PYTHONPATH="$SRC" python3 -m wals_client languages --family Niger-Congo --macroarea Africa --tsv
PYTHONPATH="$SRC" python3 -m wals_client.smoke_test   # offline, bundled fixture
```

`languages(family=..., genus=..., macroarea=..., bbox=(S,W,N,E))` returns `list[dict]`
with stable keys `id, name, glottocode, family, subfamily, genus, macroarea, lat,
lon, iso639` (the geo + genealogy table). For per-feature values, join the WALS
`values.csv` separately. `inspect` prints the real header; reads .csv/.xlsx.

## Overview

**WALS** (*The World Atlas of Language Structures*) is the reference open
database of cross-linguistic typological features, edited by **Matthew S.
Dryer** and **Martin Haspelmath** at the **Max Planck Institute for
Evolutionary Anthropology** (Leipzig). Originally published in book form
by Oxford University Press in 2005 (Haspelmath, Dryer, Gil & Comrie eds.),
it has since been continuously expanded as **WALS Online** (2008–present)
with versioned CLDF releases on GitHub.

WALS catalogues structural properties — phonological, morphological,
syntactic, lexical — gathered from descriptive grammars and assigned
discrete categorical values, allowing systematic typological comparison
at the global scale. Every WALS language is keyed to a **Glottocode**,
making WALS the canonical typological-trait layer of the
Glottolog-anchored ecosystem.

- **Canonical reference**: Dryer M.S. & Haspelmath M. (eds.). *The World
  Atlas of Language Structures Online.* Leipzig: Max Planck Institute for
  Evolutionary Anthropology, 2013 (and successive CLDF releases).
- **Web portal**: `https://wals.info/`
- **CLDF dataset (recommended)**: `https://github.com/cldf-datasets/wals`
- **License**: **CC BY 4.0**
- **Verified content** (current CLDF release inspected for this skill):
  - **3,573 languages**
  - **192 typological parameters** ("features")
  - **76,475 coded values**
  - **152 chapters** (including introductory and meta chapters)
  - **11 thematic areas**

> [!NOTE]
> WALS has **no public REST API**. Access is by per-feature stable URL on
> `wals.info`, or — recommended for analysis — by downloading the CLDF
> StructureDataset from GitHub. Pin the release tag for reproducibility.

## Why it matters for MTBC × anthropology

WALS is **more peripheral** to direct TB research than `glottolog` or
`d-place`, but it adds two distinct things to the constellation:

1. **Typological features as quantitative covariates.** Phylogenetic
   comparative analyses of cross-cultural traits often need a
   *typological similarity* term to control for areal diffusion (Galton's
   problem in disguise: linguistic neighbours influence each other
   structurally). WALS gives you this in 192 dimensions.
2. **A bridge from Glottocode to grammar.** When you say *"the populations
   speaking Bantu languages of the Sabaki branch"* in a TB phylogeography
   narrative, WALS tells you what those languages actually look like
   structurally — not just how they're classified. Useful when arguing
   that cultural neighbours and linguistic neighbours co-vary with TB
   neighbours.

WALS is **not** a primary scientific resource for TB work — its inclusion
is justified mainly because it shares the Glottocode backbone and is
trivially joinable to `d-place`, `glottolog`, `aadr`, `seshat`, and the
ancient-pathogen catalogues via the language identifier layer.

## Data model

### CLDF table layout (verified)

WALS is published as a CLDF StructureDataset with the following tables:

| Table | Rows | Key columns |
|---|---|---|
| `languages.csv` | 3,573 | ID, Name, Macroarea, Latitude, Longitude, **Glottocode**, ISO639P3code, Family, Subfamily, Genus, Samples_100, Samples_200, Country_ID |
| `parameters.csv` | 192 | ID, Name, Description, Chapter_ID |
| `chapters.csv` | 152 | ID, Number, Name, Description, Contributor, Citation, Area_ID |
| `codes.csv` | — | ID, Parameter_ID, Name, Description, Number — i.e. the discrete value labels for each parameter |
| `values.csv` | 76,475 | ID, Language_ID, Parameter_ID, Value, Code_ID, Comment, Source, Example_ID |
| `examples.csv` | — | ID, Language_ID, Primary_Text, Analyzed_Word, Gloss, Translated_Text |
| `genealogy.csv` | — | Family-level genealogical metadata (some with phylogenies) |
| `areas.csv` | **11** | Top-level thematic groupings of chapters |
| `countries.csv`, `language_names.csv`, `media.csv`, `contributors.csv` | — | Auxiliary tables |

### The 11 thematic areas

| ID | Area |
|---|---|
| 1 | **Phonology** (e.g. consonant inventories, tone systems) |
| 2 | **Morphology** (e.g. case marking, fusion of selected inflectional formatives) |
| 3 | **Nominal Categories** (e.g. number, gender, definiteness) |
| 4 | **Nominal Syntax** |
| 5 | **Verbal Categories** (e.g. tense, aspect, mood, evidentials) |
| 6 | **Word Order** (the famous SVO/SOV/etc. typology) |
| 7 | **Simple Clauses** |
| 8 | **Complex Sentences** |
| 9 | **Lexicon** (e.g. numeral bases, colour terms) |
| 10 | **Sign Languages** |
| 11 | Other |

### Sampling subsets

The `Samples_100` and `Samples_200` columns flag the **WALS 100-language
sample** and **WALS 200-language sample** — globally balanced subsets
designed by Dryer to maximise typological and genealogical diversity.
These are the canonical reference sets for testing global typological
hypotheses with controlled non-independence.

### Key column: Glottocode

Every WALS language carries a `Glottocode` — the join key to **`glottolog`**,
**`d-place`**, and any other Glottocode-aware resource in the constellation.
This is the single most important column for integration.

## Data access

### Option A — CLDF dataset on GitHub (recommended)

```bash
git clone https://github.com/cldf-datasets/wals.git
# Or fetch a single release archive
curl -LO https://github.com/cldf-datasets/wals/archive/refs/tags/v2020.tar.gz
```

The cldf/ subdirectory contains the StructureDataset with all the tables
listed above. Pin a release tag (e.g. `v2020`) when citing.

```python
import pandas as pd

lang  = pd.read_csv("cldf/languages.csv")
par   = pd.read_csv("cldf/parameters.csv")
val   = pd.read_csv("cldf/values.csv", low_memory=False)
codes = pd.read_csv("cldf/codes.csv")

# Each (language, parameter) coding is one row in val:
print(val.head())
#    ID Language_ID Parameter_ID Value Code_ID ...
```

### Option B — `pycldf` for canonical access

```python
from pycldf import Dataset
ds = Dataset.from_metadata("wals/cldf/StructureDataset-metadata.json")
for v in ds["ValueTable"]:
    if v["Parameter_ID"] == "81A":  # Order of Subject, Object and Verb
        print(v["Language_ID"], v["Value"])
```

### Option C — Per-feature web pages on wals.info

Each parameter has a stable URL of the form:

```
https://wals.info/feature/<NN>A
```

e.g. `https://wals.info/feature/81A` for "Order of Subject, Object and
Verb". Each page includes a global map, the value distribution, the
language list, and the prose chapter.

### Option D — `lingtypology` (R)

For R users, the `lingtypology` package wraps WALS / Glottolog / Phoible /
AfBo into a unified typology toolkit and is the easiest route for
comparative-method work in R.

## Workflows

### Workflow 1 — Join WALS to D-PLACE for cross-cultural analysis

Goal: combine WALS typological features with D-PLACE cultural/environmental
variables for the same societies, via the Glottocode backbone.

```python
import pandas as pd
wals = pd.read_csv("cldf/languages.csv")          # 17 cols incl. Glottocode
dpl  = pd.read_csv("dplace-data/csv/societies.csv")  # has glottocode column

joined = dpl.merge(
    wals[["Glottocode","Family","Macroarea","Samples_100","Samples_200"]],
    left_on="glottocode", right_on="Glottocode", how="left",
)
# Now each D-PLACE society can be linked to its WALS coverage
```

### Workflow 2 — Test correlation between a typological feature and an MTBC lineage

Goal (illustrative, not a serious claim): is lineage X over-represented
in populations speaking SOV languages?

```python
val = pd.read_csv("cldf/values.csv", low_memory=False)
lang = pd.read_csv("cldf/languages.csv")

# Order of Subject Object Verb = parameter 81A
sov = val[(val.Parameter_ID == "81A")].merge(
    lang[["ID","Glottocode","Latitude","Longitude","Macroarea","Family"]],
    left_on="Language_ID", right_on="ID",
)
# Snap each TB sample to the nearest WALS-coded language
# and tabulate value distributions
```

> [!WARNING]
> This kind of analysis is at risk of being **methodologically meaningless**
> if you don't control for areal and genealogical effects. Always (i)
> restrict to the WALS 100- or 200-language sample, (ii) include `Family`
> as a random effect, and (iii) report effect sizes with confidence
> intervals derived from a phylogenetic comparative model — not raw
> chi-squared tests.

### Workflow 3 — Build a typological profile of a population

Goal: for a population whose Glottocode you know, dump the full WALS
typological profile to feed into a narrative or a slide.

```python
def profile(glottocode):
    lang = pd.read_csv("cldf/languages.csv")
    par  = pd.read_csv("cldf/parameters.csv")
    val  = pd.read_csv("cldf/values.csv", low_memory=False)
    codes = pd.read_csv("cldf/codes.csv")

    lid = lang[lang.Glottocode == glottocode]["ID"].iloc[0]
    rows = (val[val.Language_ID == lid]
            .merge(par.rename(columns={"ID":"Parameter_ID","Name":"Feature"}),
                   on="Parameter_ID")
            .merge(codes.rename(columns={"ID":"Code_ID","Name":"Value_Label"}),
                   on="Code_ID"))
    return rows[["Feature","Value_Label"]]

profile("akan1250")  # Twi (Akan), Ghana — relevant to L4.15 Clade A
```

### Workflow 4 — Use the WALS 100/200 sample as a globally balanced reference

Goal: avoid overfitting to well-studied languages (English, French,
German, Russian — the top of the values count).

```python
lang = pd.read_csv("cldf/languages.csv")
sample100 = lang[lang.Samples_100 == 1]   # ~100 globally balanced languages
sample200 = lang[lang.Samples_200 == 1]   # ~200 globally balanced languages
```

These sets are the canonical reference for testing global typological
claims and minimise the bias toward Standard Average European.

## Caveats

- **WALS is descriptive linguistics, not biology.** Resist the temptation
  to over-interpret a linguistic-feature ↔ pathogen correlation as
  causal — the chain language → cultural practice → pathogen exposure has
  many missing links and the more parsimonious interpretations (areal
  diffusion, ascertainment bias) usually win.
- **Coverage is uneven.** The most-coded languages (English: 159 features,
  French: 158, German: 157, Russian, Finnish, Hungarian, Spanish, Greek,
  Turkish, Mandarin: 153–155) are heavily over-represented compared to
  most of WALS's 3,573 languages, many of which carry only a handful of
  features. Filter on `Samples_100` / `Samples_200` for analyses where
  coverage symmetry matters.
- **Discrete categorical coding is reductive.** A WALS feature value is a
  one-out-of-N choice; real linguistic systems are messier. Read the
  prose chapter (`chapters.csv`) and look at examples (`examples.csv`)
  before drawing strong conclusions.
- **Static snapshot, not a living typology.** WALS is updated rarely
  compared to Glottolog. Some features and codings reflect 2005-era
  consensus that has since shifted in linguistic typology.
- **Areal autocorrelation is severe.** WALS features cluster strongly by
  geographic area (linguistic areas, *Sprachbund* effects). Standard
  statistical tests on raw WALS values are misleading without explicit
  spatial controls.
- **Glottocodes occasionally drift.** Some WALS records use slightly
  outdated Glottocodes that have been merged or split since. When the
  join with `glottolog` fails, retry against the Glottolog redirect
  table.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`glottolog`** | Backbone language identifier; **the join key** for WALS |
| **`d-place`** | Cultural variables (subsistence, kinship, religion) — joinable via Glottocode |
| **`pleiades`** | Ancient toponyms for the populations studied |
| **`seshat`** | Polity histories of the regions where WALS languages are spoken |
| **`aadr`** | Ancient human genomes for the same populations (loose link via region) |
| **`p3k14c`** | Archaeological context |
| **`spaam-ancient-metagenome-dir`** | Ancient pathogen samples — same populations |
| **`lingtypology`** (R) | Comparative typology toolkit wrapping WALS / Phoible / Glottolog |
| **`pycldf`** (Python) | Canonical CLDF loader |
| **D-PLACE Bayesian phylogenies** | Time-calibrated language trees for comparative phylogenetic methods on WALS features |

## Citation

```bibtex
@misc{dryer2013wals,
  title     = {The World Atlas of Language Structures Online},
  editor    = {Dryer, Matthew S. and Haspelmath, Martin},
  year      = {2013},
  publisher = {Max Planck Institute for Evolutionary Anthropology},
  address   = {Leipzig},
  url       = {https://wals.info/},
  note      = {License CC BY 4.0. CLDF release on GitHub: cldf-datasets/wals.}
}

@book{haspelmath2005wals,
  title     = {The World Atlas of Language Structures},
  editor    = {Haspelmath, Martin and Dryer, Matthew S. and Gil, David and
               Comrie, Bernard},
  year      = {2005},
  publisher = {Oxford University Press},
  address   = {Oxford}
}
```
