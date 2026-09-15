---
name: amtdb
description: >-
  Query AmtDB, the Ancient mtDNA Database (Charles University Prague,
  Ehler et al. 2019), the reference open repository of ancient human
  mitochondrial genomes (2,548 samples in v1.009, late Paleolithic →
  Iron Age, mostly Eurasian) with rich metadata: maternal haplogroup,
  Y-chromosome haplogroup when available, archaeological culture, site,
  radiocarbon date, and mitochondrial pathological mutations. Lightweight,
  matrilineally focused complement to the AADR.

  Use when: tracking maternal lineage histories of populations relevant
  to a TB phylogeographic argument, retrieving ancient mtDNA when AADR
  has no nuclear-genome record for a skeleton, building a Neolithic /
  Bronze Age maternal lineage map for a region, or correlating
  mitochondrial pathological mutations with ancient samples in
  paleopathology contexts.
---

# AmtDB : Ancient mtDNA Database

## Client (resilient, tool-first)

A stdlib-only client ships with this skill (`src/amtdb_client/`, nothing to
pip-install). Filter ancient mtDNA samples without hand-rolling pandas:

```bash
SRC=<this skill>/src
export AMTDB_FILE=/path/to/amtdb_samples.csv
PYTHONPATH="$SRC" python3 -m amtdb_client samples --bbox 35 -10 60 40 --period -3000 0 --haplogroup H --tsv
PYTHONPATH="$SRC" python3 -m amtdb_client.smoke_test   # offline, bundled fixture
```

`samples(bbox=(S,W,N,E), period=(lo,hi), haplogroup=...)` returns `list[dict]` with
stable keys `id, country, lat, lon, culture, epoch, site, mt_hg, year_from, year_to,
bp, reference`. `period` is calendar years (BCE negative); `haplogroup` is a prefix
match on `mt_hg` (so `H` matches H, H1, H5a). `inspect` prints the real header.

## Overview

**AmtDB** is the reference open database of **ancient human mitochondrial
genomes**, created and maintained by **Edvard Ehler**, Jan Novotný, Anna
Juras, Maciej Chyleński, Ondřej Moravčík, and Jan Pačes at **Charles
University Prague** and partner institutions. Published in 2018, it is
the first dedicated repository of curated ancient human mtDNA sequences
with structured metadata, designed for fast lookups and reusable
phylogeographic analysis.

- **Reference**: Ehler E., Novotný J., Juras A., Chyleński M., Moravčík O.,
  Pačes J. *AmtDB: a database of ancient human mitochondrial genomes.*
  **Nucleic Acids Research** 47(D1): D29–D32 (2019). DOI:
  `10.1093/nar/gky843`
- **Web portal**: `https://amtdb.org/`
- **Help / changelog**: `https://amtdb.org/help`
- **Current release**: **v1.009** (28 February 2024), **2,548 samples**
- **License**: **CC BY 4.0**
- **Hosting**: Charles University Prague (Czech Republic)

> [!NOTE]
> AmtDB has **no public REST API**. Access is via the web UI (interactive
> map + advanced search) and direct **CSV + FASTA downloads**. The
> downloads are small enough that you should mirror them locally and
> pin the version (v1.009 / 2024-02-28) in your Methods.

## Why it matters for MTBC × anthropology

AmtDB is **complementary to `aadr`**, not a replacement, and serves three
specific niches:

1. **Skeletons with only mtDNA published.** Many ancient-DNA papers (especially
   pre-2015) reported mitochondrial sequences without producing nuclear
   genomes. Those individuals are catalogued in AmtDB but **not in AADR**
   (which is restricted to nuclear-genome reconstructions). AmtDB is the
   way to recover them for cross-referencing.
2. **Maternal lineage cleanliness.** Mitochondrial haplogroups (`mt_hg`)
   are simpler to interpret than autosomal admixture components, a
   single matrilineal trajectory rather than a probabilistic mix. For
   narrative slides on population history this is often more readable
   than ADMIXTOOLS output.
3. **Lightweight and fast.** The full database is small (a CSV + a FASTA
   bundle, both downloadable in seconds) and trivial to query in pandas.
   For exploratory work and prototyping, it is much faster than the
   full AADR EIGENSTRAT pipeline.

AmtDB does **not** carry pathogen data, for that, you still need
`spaam-ancient-metagenome-dir`. Its role in the TB constellation is the
**maternal-lineage host context** for ancient samples.

## Coverage (verified, v1.009)

- **2,548 ancient human samples** with mitochondrial sequences and metadata
- Temporal range: **late Paleolithic → Iron Age**, with the bulk in
  Neolithic and Bronze Age
- Geographic focus: **Eurasia**, dominated by Europe; smaller numbers from
  Central Asia, Middle East, Near East, and Africa
- Latest update added 406 FASTA files from older studies : Gamba, Haak,
  Lazaridis, Lipson, Mathieson, Olalde et al. (2014–2019)

## Metadata fields (verified from AmtDB documentation)

The CSV download is wide and richly annotated. Key columns:

| Field | Meaning |
|---|---|
| `id`, `id_alt` | Sample identifier(s) |
| `country`, `continent`, `geo_group` | Modern administrative geography |
| `latitude`, `longitude` | Decimal coordinates (WGS84) |
| `culture`, `epoch` | Archaeological culture and broad period (e.g. *LBK*, *Bell Beaker*, *Yamnaya*) |
| `site`, `site_detail` | Excavation site name and specifics |
| `mt_hg` | **Mitochondrial haplogroup** (PhyloTree nomenclature) |
| `ychr_hg`, `ychr_snps` | Y-chromosome haplogroup and supporting SNPs (when sex permits) |
| `year_from`, `year_to` | Calendar-year range (BCE/CE) |
| `date_detail` | Free-text dating notes |
| `bp` | Years before present |
| `c14_lab_code` | Radiocarbon laboratory code (when available) |
| `c14_sample_tag`, `c14_layer_tag` | Radiocarbon flags |
| `sex` | Genetic sex |
| `comment` | Free-text notes |
| `reference_name` | Source publication (short tag) |
| `reference_link` | DOI or URL of source paper |
| `data_link` | Link to raw sequence (ENA / SRA / NCBI) |
| `mitopatho_alleles`, `mitopatho_positions`, `mitopatho_locus`, `mitopatho_diseases`, `mitopatho_statuses`, `mitopatho_homoplasms`, `mitopatho_heteroplasms` | **Pathological mtDNA mutations** with disease associations |
| `sequence_source` | Where the sequence comes from (whole-genome capture, mt-capture, etc.) |
| `avg_coverage` | Mean coverage of the mt sequence |

The `mitopatho_*` family of columns is **unique** in the constellation,
no other ancient-DNA database catalogues mitochondrial pathological
mutations at the per-sample level. Useful for niche paleopathology
arguments.

## Data access

### Option A : Web UI (interactive)

1. Go to `https://amtdb.org/`.
2. Use the search panel to filter by country, culture, epoch, haplogroup,
   coordinates, etc.
3. Display the selected samples on the interactive world map.
4. Export the selection as CSV (metadata) and FASTA (sequences).

### Option B : Bulk download + pandas

The full database is a single CSV + a FASTA bundle, small enough to
inspect locally:

```bash
mkdir -p ~/data/amtdb && cd ~/data/amtdb
# Direct download links are exposed on amtdb.org under "Download all"
# (verify the current URL on the site — they have changed across versions)
```

Then:

```python
import pandas as pd
df = pd.read_csv("amtdb_samples_v1.009.csv", low_memory=False)
print(df.shape, list(df.columns))
print(df.country.value_counts().head(15))
print(df.mt_hg.value_counts().head(15))
```

### Option C : Reading the FASTA sequences

The sequences are standard mtDNA FASTA, headers keyed by `id`. Load with
Biopython:

```python
from Bio import SeqIO
seqs = {rec.id: str(rec.seq) for rec in SeqIO.parse("amtdb_v1.009.fasta", "fasta")}
print(len(seqs), "sequences")
```

## Workflows

### Workflow 1 : Maternal lineage profile of a region

Goal: build a per-period, per-region distribution of mitochondrial
haplogroups for a cultural area relevant to your TB narrative.

```python
import pandas as pd
df = pd.read_csv("amtdb_samples_v1.009.csv", low_memory=False)

bell_beaker_central_europe = df[
    (df.culture.str.contains("Beaker", na=False))
    & (df.country.isin(["Germany","Czechia","Hungary","Austria","Poland"]))
]
print(bell_beaker_central_europe
      .groupby(["country","mt_hg"]).size()
      .unstack(fill_value=0))
```

Then compare to the same region's modern population mt-haplogroup
distribution (e.g. from MITOMAP or Behar 2008) to assess maternal
continuity vs replacement.

### Workflow 2 : Pair AmtDB samples with SPAAM ancient-pathogen samples

Goal: when SPAAM has an ancient *Y. pestis* or *M. tuberculosis* sample
without an AADR nuclear-genome match, check whether AmtDB at least
catalogues the mtDNA of the same skeleton.

```python
spaam = pd.read_csv("amdir_singlegenome_samples.tsv", sep="\t", low_memory=False)
amt   = pd.read_csv("amtdb_samples_v1.009.csv", low_memory=False)

# Join on best-effort: site name + age window
def find_amt_match(row):
    cand = amt[
        (amt.site.fillna("").str.lower().str.contains(str(row.site_name).lower()[:6]))
        & (amt.bp.between(row.sample_age - 50, row.sample_age + 50))
    ]
    return cand.id.iloc[0] if len(cand) else None

spaam["amtdb_id"] = spaam.apply(find_amt_match, axis=1)
print(spaam[["project_name","site_name","sample_age","amtdb_id"]].dropna(subset=["amtdb_id"]))
```

### Workflow 3 : Map of an mt-haplogroup over time

Goal: visualise the spatiotemporal distribution of a specific maternal
lineage of interest.

```python
import geopandas as gpd
H1 = df[df.mt_hg.str.startswith("H1", na=False)].dropna(subset=["latitude","longitude"])
gdf = gpd.GeoDataFrame(H1, geometry=gpd.points_from_xy(H1.longitude, H1.latitude),
                       crs="EPSG:4326")
gdf["period"] = pd.cut(gdf.bp, bins=[-1, 3000, 5000, 7000, 12000],
                       labels=["IronAge_BronzeAge","Neolithic","Mesolithic","UpperPaleo"])
# then plot per period
```

### Workflow 4 : Mitochondrial pathological mutations in ancient samples

Goal: leverage the unique `mitopatho_*` fields to surface ancient
individuals carrying known disease-associated mtDNA variants.

```python
patho = df[df.mitopatho_diseases.fillna("").str.len() > 0]
print(len(patho), "samples with at least one pathological annotation")
print(patho[["id","country","epoch","mitopatho_diseases"]].head(20))
```

This is a very niche but unique angle, at the boundary between
paleogenetics and paleopathology, that AmtDB enables out of the box.

## Caveats

- **mtDNA only.** AmtDB tracks only the maternal line; for paternal or
  autosomal ancestry use `aadr` (Y-haplogroups, ADMIXTOOLS, qpAdm…).
- **Curation cadence is irregular.** v1.009 (Feb 2024) was preceded by a
  long gap. Always pin the version, and periodically check for newer
  releases.
- **No REST API.** Don't try to scrape the search UI; download the bulk
  CSV/FASTA instead and filter locally.
- **Eurasia-biased.** African and Asian samples exist but are far less
  numerous than European ones. Plan around the bias.
- **Haplogroup nomenclature drift.** PhyloTree updates can cause
  haplogroup labels to be re-categorised over time. Use HaploGrep on the
  raw FASTA to re-derive haplogroups consistently if you mix AmtDB with
  newer published mtDNA.
- **Site/name matching with SPAAM and AADR is fuzzy.** AmtDB does not
  share an explicit identifier scheme with the other ancient-DNA
  resources, so cross-references rely on `site` + `bp` + paper, with
  manual verification.
- **Pathological annotations are inherited from MitoMap.** They are not
  ground-truth disease attributions for the ancient individual, only
  flags for known associations in the modern literature. Treat with
  caution when telling a paleopathology story.
- **Coverage values matter.** For analytic use, filter on `avg_coverage`
  to exclude very low-coverage sequences with high uncertainty.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`aadr`** | Autosomal/nuclear-genome counterpart for the same skeletons (when both exist) |
| **`spaam-ancient-metagenome-dir`** | Ancient pathogen samples, pair via `site_name` + age |
| **`p3k14c`** | Independent radiocarbon chronology of the sites |
| **`pleiades`** | Toponymic resolution for ancient site names in `site` field |
| **`d-place`** | Cultural context for the population the skeleton belonged to |
| **`glottolog`** | Linguistic family of the population (loose link via region/culture) |
| **`seshat`** | Polity context for samples within the historical period |
| **TBannotator MCP** | Modern TB lineage geography for downstream coevolution arguments |
| **HaploGrep / Haplofind** | Tools for re-deriving mtDNA haplogroups consistently |
| **MitoMap** | Reference catalogue of mtDNA pathological variants, source of `mitopatho_*` annotations |

## Citation

```bibtex
@article{ehler2019amtdb,
  title   = {AmtDB: a database of ancient human mitochondrial genomes},
  author  = {Ehler, Edvard and Novotn{\'y}, Jan and Juras, Anna and
             Chyle{\'n}ski, Maciej and Morav{\v c}{\'i}k, Ond{\v r}ej and
             Pa{\v c}es, Jan},
  journal = {Nucleic Acids Research},
  volume  = {47},
  number  = {D1},
  pages   = {D29--D32},
  year    = {2019},
  doi     = {10.1093/nar/gky843},
  note    = {License CC BY 4.0. Always pin the database version
             (e.g. v1.009, 2024-02-28).}
}
```
