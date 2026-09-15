---
name: card
description: >-
  Query CARD 2.0 (Canadian Archaeological Radiocarbon Database), the
  reference compilation of archaeological radiocarbon dates for North
  America, ~50,000 dates plus an additional ~104,000 dates from the
  lower 48 US states, covering archaeological, paleontological, and
  geological contexts, with expanding coverage into Central and South
  America. Operated jointly by the Canadian Museum of History and the
  UBC Laboratory of Archaeology under Andrew Martindale. The Americas
  counterpart to EUROEVOL (Europe) and NERD (Near East) for
  chronological anchoring.

  Use when: building a chronological backdrop for pre-Columbian and
  colonial-era narratives in the Americas, contextualizing the
  M. pinnipedii pre-Columbian Andean host-jump (Bos2014, Vagene2022),
  extracting site-level dates for regions underrepresented in p3k14c,
  or cross-referencing North American ancient-DNA samples with a
  regional chronology.
---

# CARD 2.0 : Canadian Archaeological Radiocarbon Database

## Overview

**CARD 2.0** is the reference compilation of archaeological ¹⁴C dates
for **North America**, with expanding coverage into Central and South
America. The current version is a partnership between the **Canadian
Museum of History** and the **UBC Laboratory of Archaeology**,
established in July 2014 and led by **Andrew Martindale**. It
includes archaeological, paleontological, and geological samples and
is the deepest chronological resource for the Americas in the
constellation.

- **Key reference**: Gajewski K., Muñoz S., Peros M., Viau A., Morlan R.
  & Betts M. *The Canadian Archaeological Radiocarbon Database (CARD):
  Archaeological ¹⁴C Dates in North America and Their Paleoenvironmental
  Context.* **Radiocarbon** 53(3): 371–394 (2011).
  DOI: `10.1017/S0033822200056654`
- **Revival paper**: Martindale A. et al. *The Revival of the Canadian
  Archaeological Radiocarbon Database (CARD).* tDAR deposit 395548.
- **Web portal**: `https://www.canadianarchaeology.ca/`
- **Pandora Data entry**: `https://pandoradata.earth/dataset/card-2-0`
- **Institutional hosts**: Canadian Museum of History + University of
  British Columbia (Advanced Research Computing / Laboratory of
  Archaeology)
- **Maintainer**: Andrew Martindale (UBC)
- **Size**: **~50,000 original CARD dates** + **~104,000 additional
  dates** from the lower 48 US states (recent expansion, an
  order-of-magnitude increase for that region)
- **Coverage**: Canada, contiguous US, Alaska, with growing
  Central / South American records

> [!WARNING]
> **Ethical notice, ancestral remains.** CARD has publicly stated that
> several Indigenous communities in North America informed the
> maintainers that the database contained data from ancestors and their
> burials collected **without permission** and in **violation of
> community policies**. In response, **all 1,702 dates associated with
> ancestral remains have been removed**. This is a first-class
> consideration for anyone working with North American archaeological
> datasets, respect the decision, do not attempt to reconstruct
> removed entries from older published sources, and consult the
> relevant Indigenous community / regulatory body if your work touches
> human remains. This is an ethical baseline, not a technical nicety.

> [!NOTE]
> **Two-tier access model.**
> - **Public access**: location data are **fuzzed to 1:2,000,000
>   scale**, useful for regional/continental visualisation but not for
>   precise spatial joins.
> - **Researcher access**: requires a **security account** at an
>   accredited institution; grants access to precise coordinates and
>   batch up/download tools.
> Plan your analysis around the tier you can legitimately access. Do
> not attempt to de-fuzz locations.

## Why it matters for MTBC × anthropology

Only **one** MTBC story in the ancient record is currently
robustly documented: the **pre-Columbian Andean ***M. pinnipedii***
hypothesis** (Bos et al. 2014, *Nature*; Vagene et al. 2022, *Nat
Commun*), where human skeletons in coastal Peru and Colombia yielded
genomes of a seal/sea-lion-associated MTBC lineage dating ~500–1 000 BP.

CARD provides the **only dense, curated chronological backdrop** for
this story, and for the broader pre-Columbian population dynamics of
the Americas. Specific uses:

1. **Site-level chronology for Andean *M. pinnipedii* sites.** El Yaral,
   El Algodonal, Chiribaya Alta (Bos 2014) and Moquegua / Bogotá
   (Vagene 2022) are all in regions where CARD now has strong coverage
   via the US-states expansion and growing Central/South American
   records.
2. **Pre-contact population dynamics.** The same SPD-based demographic
   analyses that EUROEVOL enabled for Neolithic Europe can be done
   with CARD for pre-Columbian North America, testing whether specific
   lineage emergences align with demographic expansions or collapses.
3. **Post-contact transition chronology.** The 16th–17th century
   epidemiological catastrophe in the Americas (smallpox, measles,
   *Salmonella* paratyphi C via Vågene 2018) is bounded by the
   pre-contact baseline + the colonial archaeological record, both
   visible in CARD.

CARD is **the Americas counterpart** to EUROEVOL (Europe) and NERD
(Near East) for the `neolithic-14c` index, and it extends `p3k14c`
with higher regional resolution in North America.

## Data access

### Option A : Public web interface (fuzzed locations)

1. Go to `https://www.canadianarchaeology.ca/`
2. Use the search UI: filter by country, province/state, date range,
   material, species, site type.
3. Results show **fuzzed coordinates** (1:2,000,000 scale).
4. Export selected records as CSV.

This tier is sufficient for:
- Regional and continental SPD analyses
- Chronological range queries by country/state
- Counting dates per period × region

It is **not** sufficient for:
- Point-level spatial joins with genomic or environmental data
- Nearest-neighbour queries
- Publication-grade maps with precise locations

### Option B : Researcher access (precise locations)

Full access requires a **security account** granted to researchers at
accredited institutions. Contact:

- The CARD web portal (request access form)
- Andrew Martindale / UBC Laboratory of Archaeology

This tier grants:
- Precise coordinates
- Batch up/download tools
- Dynamic search with advanced filters
- Spatial-join quality data

### Option C : Pandora Data dataset (partial)

The Pandora Data platform (`pandoradata.earth/dataset/card-2-0`) offers
a static snapshot of CARD 2.0, useful for reproducibility-pinning a
historical state of the database.

### Option D : Indirect via p3k14c

CARD is one of the source databases integrated into `p3k14c`. For
rough global-scale analyses that include the Americas, `p3k14c` is a
faster entry point. For regional precision or the latest curated
state, query CARD directly.

## Workflows

### Workflow 1 : Pre-Columbian chronological backdrop for *M. pinnipedii*

Goal: build a regional ¹⁴C density map around the Andean *M. pinnipedii*
sites.

1. In the CARD public UI, filter by country = Peru / Chile and date
   range 500–2 000 BP.
2. Export the CSV.
3. Count dates per 500-year bin, this is your "population activity"
   proxy for the region at the time of the host-jump.
4. Overlay the 6 Bos2014 + Vagene2022 samples (from
   `spaam-ancient-metagenome-dir`).
5. If coverage is sparse (researcher tier unavailable), fall back to
   `p3k14c` for the same region.

### Workflow 2 : North American population SPD

Goal: compute a summed probability distribution for pre-contact North
America, analogous to the Shennan/Timpson European SPD, to discuss
demographic context for any hypothesised pathogen story.

1. Export CARD dates for a region (e.g. US Pacific Northwest).
2. Calibrate with `rcarbon::calibrate(calCurves = "intcal20")`
   (Northern Hemisphere).
3. Compute `rcarbon::spd(timeRange = c(13000, 500))` to cover the
   entire human occupation window.
4. Identify boom-bust signals and discuss the ecological / pathogen
   implications.

```r
library(rcarbon)
card_pnw <- read.csv("card_pnw_export.csv")  # your CARD export
dates <- calibrate(x = card_pnw$Age, errors = card_pnw$Error,
                   calCurves = "intcal20")
spd_out <- spd(dates, timeRange = c(13000, 500))
plot(spd_out)
```

### Workflow 3 : Post-contact archaeological chronology

Goal: use CARD to quantify the colonial-era archaeological footprint
(16th–18th c.) for overlay with Vagene 2018 (*Salmonella enterica*
Paratyphi C, Mexican cocoliztli 1545 CE).

1. Filter CARD for dates 200–500 BP across Central America.
2. Classify sites by type (settlement, mission, burial, etc.).
3. Overlay with the Vagene 2018 Teposcolula-Yucundaa location and the
   broader *cocoliztli* literature.
4. Discuss the correspondence (or lack thereof) between CARD's site
   density and documented epidemic outbreaks.

### Workflow 4 : Gap analysis vs p3k14c

Goal: identify regions where CARD has substantially more dates than
`p3k14c`, i.e. where CARD is worth querying directly.

```python
import pandas as pd
p3k = pd.read_csv("p3k14c_raw.csv", low_memory=False)

# For a bounding box (e.g. US Pacific Northwest), count dates
pnw = p3k[
    (p3k.Latitude.between(42, 49))
    & (p3k.Longitude.between(-125, -116))
]
print("p3k14c PNW:", len(pnw))
# Compare against CARD export counts for the same bbox
```

If CARD has substantially more dates than p3k14c for a region, prefer
CARD for focused regional work.

## Caveats

- **Ethical baseline.** See the ethics warning at the top of this skill.
  Ancestral remains have been removed; respect that boundary.
- **Location fuzzing in public tier.** Do not attempt to de-fuzz
  coordinates. If you need precision, request researcher access
  through legitimate channels.
- **Uneven regional coverage.** Canada is the best-covered area; the
  lower 48 US states are now well-covered after the recent expansion;
  Central and South America are growing but still sparse compared to
  North America proper.
- **Overlap with p3k14c.** CARD is one of the sources p3k14c integrates.
  Avoid double-counting when combining.
- **Uncalibrated BP ages.** Like EUROEVOL / NERD / p3k14c, CARD ages
  are typically stored as uncalibrated BP. Calibrate with `rcarbon`
  + IntCal20 (Northern Hemisphere) or SHCal20 (Southern Hemisphere)
  before reporting in calendar years.
- **License not explicitly stated.** The public portal does not
  prominently display a dataset license. Cite the Gajewski et al. 2011
  paper, the specific snapshot, and contact the maintainers if you
  plan to republish or redistribute the data.
- **Not a primary source for ancient DNA.** CARD catalogues dates, not
  sequences. For ancient human or pathogen DNA from the same sites,
  use `aadr`, `amtdb`, `spaam-ancient-metagenome-dir`.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`p3k14c`** | Global counterpart, partially integrates CARD |
| **`neolithic-14c`** | Eurasian regional counterparts (EUROEVOL + NERD + RADON + NeoNet) |
| **`aadr`** | Ancient human genomes from North/South America |
| **`amtdb`** | Ancient human mtDNA from the same regions |
| **`spaam-ancient-metagenome-dir`** | Ancient pathogen samples : Bos2014 and Vagene2022 (*M. pinnipedii*) and Vagene 2018 (*Salmonella*) |
| **`pleiades`** | Not relevant (Pleiades is Mediterranean/Classical), complementary by exclusion |
| **`seshat`** | Polity-level history for pre-contact and colonial Americas (limited coverage) |
| **`d-place`** | Cultural variables of North American ethnographic-present populations |
| **`glottolog`** | Language classification for North American populations |
| **`rcarbon`** (R) | Calibration and SPD analysis |
| **`c14bazAAR`** (R) | Unified ¹⁴C database downloader (may include CARD) |
| **TBannotator MCP** | Modern TB lineage distribution in the Americas |

## Citation

```bibtex
@article{gajewski2011card,
  title   = {The Canadian Archaeological Radiocarbon Database (CARD):
             Archaeological ${}^{14}$C Dates in North America and Their
             Paleoenvironmental Context},
  author  = {Gajewski, Konrad and Mu{\~n}oz, Samuel and Peros, Matthew and
             Viau, Andre and Morlan, Richard and Betts, Matthew},
  journal = {Radiocarbon},
  volume  = {53},
  number  = {3},
  pages   = {371--394},
  year    = {2011},
  doi     = {10.1017/S0033822200056654}
}

@misc{martindale_card2,
  title        = {The Revival of the Canadian Archaeological Radiocarbon Database (CARD)},
  author       = {Martindale, Andrew and others},
  year         = {2016--present},
  publisher    = {Canadian Museum of History and University of British Columbia},
  url          = {https://www.canadianarchaeology.ca/},
  note         = {Cite the specific snapshot / access date.
                  Respect the removal of ancestral-remains-associated dates.}
}
```

**Remember**: in Methods, specify CARD 2.0 + your access date + your
access tier (public or researcher), and acknowledge the removal of
ancestral-remains-associated entries.
