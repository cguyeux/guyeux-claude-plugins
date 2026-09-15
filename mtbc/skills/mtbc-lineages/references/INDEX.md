# References — MTBC lineage taxonomies

This directory contains synthesised notes from the original publications,
plus a local copy of `lignees.py`. The **authoritative home taxonomy**
(Guyeux/"moi") is NOT stored here. Its source-of-truth hierarchy is fixed in
`mtbc/global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`: authority =
`bdd/actuelle/` (physical) + `barcoding_v2/barcode_complete.tsv` (derived
registry). `lignees.py` key `"moi"` is a marker bank that may be stale for
active-cycle clades; `snp_barcoding.csv` is **obsolete v1, never a reference**.

## Synthesised notes

| File | Author | Year | Scope | Markers |
|------|--------|------|-------|---------|
| `Coll_2014.md` | Coll et al. | 2014 | All 7 lineages, 55 sub-lineages | 62 SNPs |
| `Stucki_2016.md` | Stucki et al. | 2016 | L4 sub-lineages only | ~30 SNPs |
| `Freschi_2021.md` | Freschi et al. | 2021 | L1, L2, L3, L4, focus on biogeography | 95 SNPs |
| `Napier_2020.md` | Napier et al. | 2020 | 9 lineages + bovis/caprae/orygis | 90/421 SNPs |

## Other taxonomies (in lignees.py only, no synthesised note)

- **Coscolla** — *M. africanum* phylogenomics (L5/L6 sub-lineages)
- **Palittapongarnpim** — Lineage 1 in Thailand (480 isolates)
- **Shitikov** — Lineage 2 East-Asian classification
- **Shitikov23** — Updated 2023 East-Asian classification
- **Zwyer** — Livestock-associated MTBC nomenclature (M. bovis, etc.)
- **Thawornwattana** — Revised L2 nomenclature 2021
- **Shuaib** — Lineage 3 origin and global expansion
- **Gisch** — L1 sub-lineage phenolic glycolipid patterns
- **Netikul** — L1 in Asia and Africa, WGS phylogeny

To get the entries for one of these systems, run:
```
python3 scripts/lineages.py system <name>
```

## Adding a new note

When ingesting a new published taxonomy:
1. Place the PDF in `~/Documents/codes/MTBC/TBannotator/data/`
2. Convert: `pdftotext -layout <pdf> /tmp/<name>.txt`
3. Create `<author>_<year>.md` here with:
   - Citation block (authors, journal, year, DOI, PDF path)
   - Key facts (sample size, geographic scope, # markers, methodology)
   - System key in `lignees.py` (if added there)
   - Strengths and limitations
   - Always end with: "Cross-check with the authoritative registry
     `barcode_complete.tsv` (+ `bdd/actuelle`) for current usage; see
     `SOURCES_OF_TRUTH.md`."
4. Update this `INDEX.md` table.

## Local lignees.py

`lignees.py` is a **manual local copy** of
`~/docs/codes/mtbc/investigate_phylo/lignees.py`. The skill
script warns if the upstream is newer. Re-sync with:

```bash
cp ~/docs/codes/mtbc/investigate_phylo/lignees.py \
   $(dirname $0)/lignees.py
```

The `"moi"` key in this file is used as a **marker bank** for stable major
lineages and for third-party system definitions. It is NOT authoritative for
active-cycle clades (L1.\*, Bovis1.\*, BCG.\*, deep L6), where it is stale —
there the authority is `bdd/actuelle` + `barcode_complete.tsv` (see
`SOURCES_OF_TRUTH.md`). `snp_barcoding.csv` is obsolete and never a reference.
