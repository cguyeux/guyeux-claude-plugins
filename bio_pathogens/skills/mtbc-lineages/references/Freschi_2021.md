# Freschi 2021 — Population structure and biogeography of MTB

## Citation

Freschi L, Vargas R Jr, Husain A, Kamal SMM, Skrahina A, Tahseen S,
Ismail N, Barbova A, Niemann S, Cirillo DM, Dean AS, Zignol M, Farhat MR.
**Population structure, biogeography and transmissibility of Mycobacterium
tuberculosis.** *Nature Communications* 12:6099 (2021).
DOI: [10.1038/s41467-021-26248-1](https://doi.org/10.1038/s41467-021-26248-1)

PDF: `~/Documents/codes/MTBC/TBannotator/data/TB_Freschi_2021.pdf`

## Key facts

- Re-evaluation of MTB population structure using **phylogenetics +
  dimensionality reduction** (UMAP).
- Sample sizes:
  - **Training set**: 4,939 pan-susceptible strains
  - **Validation set**: 4,645 independent isolates
- Defined **30 new genetically distinct clades**, validated independently.
- Focused on:
  - Ancient **L1** (Indo-Oceanic)
  - Modern **L3** (Central Asian)
  - Expanded view of **L2** and **L4**
- **20 groups** identified with consistent geographic patterns
  (restricted or unrestricted).
- Three new groups within **L1** specifically.
- Provided an **expanded barcode of 95 SNPs** discriminating:
  - 69 MTB sub-lineages
  - 26 additional internal groups

## Key findings on transmissibility

- Distribution of terminal branch lengths supports the hypothesis that
  **L2 and L4 are more transmissible** than L3 and L1 on a global scale.

## How the system is named in TBannotator/lignees.py

System key: `"Freschi"` in `lignees.py`. Contains the 95 SNPs barcode plus
fine sub-lineage codes for L1, L2, L3, L4.

## Notes

- Freschi 2021 is **the most refined published taxonomy for L1 and L3**.
- Use it for L1 sub-lineage queries (3 new groups defined here).
- For L2, prefer **Thawornwattana 2021** or **Shitikov 2017** which have
  finer East-Asian sub-typing.
- For L4, prefer **Stucki 2016** for the canonical sub-lineages, or the
  Guyeux golden CSV for the most current refinement.

## Strengths

- Large independent training/validation split.
- Pan-susceptible strain selection avoids drug-resistance bias.
- New phylogenetic + UMAP approach captures sub-clades missed by tree-only
  methods.
- Validated barcode usable in clinical pipelines.

## Limitations

- Pan-susceptible only — does not represent the full global epidemic.
- Animal lineages (M. bovis, caprae, orygis, etc.) excluded.
- L5–L10 not in scope.
