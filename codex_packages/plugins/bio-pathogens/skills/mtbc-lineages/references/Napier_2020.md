# Napier 2020 — Robust barcoding for MTBC lineages

## Citation

Napier G, Campino S, Merid Y, Abebe M, Woldeamanuel Y, Aseffa A,
Hibberd ML, Phelan J, Clark TG. **Robust barcoding and identification of
Mycobacterium tuberculosis lineages for epidemiological and clinical
studies.** *Genome Medicine* 12:114 (2020).
DOI: [10.1186/s13073-020-00817-3](https://doi.org/10.1186/s13073-020-00817-3)

PDF: `~/Documents/codes/MTBC/TBannotator/data/TB_Napier_2020.pdf`

## Key facts

- **Update of Coll 2014** by the same group (TG Clark, LSHTM).
- **Sample size**: 35,298 MTBC isolates (~1 million SNPs).
- Coverage: **9 main lineages + 3 animal-related species**:
  - M. tuberculosis var. **bovis**
  - M. tuberculosis var. **caprae**
  - M. tuberculosis var. **orygis**
- Partitioned into:
  - Training: N = 17,903 (50.7%)
  - Test: N = 17,395 (49.3%)
- Identified **90 lineages or sub-lineages or species**, of which **30 are new**.
- Found **421 robust barcoding mutations** by combining phylogenetics +
  population differentiation (FST).
- Selected a **minimal set of 90 markers**, including **20 from the original
  Coll 2014 barcode** for backwards compatibility.
- Validated on the test set with **perfect discrimination** of 86 sub-lineages.

## Where it lives

- Integrated into the **TB-Profiler** informatics platform
  ([github.com/jodyphelan/TBProfiler](https://github.com/jodyphelan/TBProfiler)).

## How the system is named in TBannotator/lignees.py

System key: `"Napier"` in `lignees.py`. Contains the 90 barcoding markers
plus the 421 extended set for fine resolution.

## Notes

- Napier 2020 is the **default reference for TB-Profiler** users.
- It is the **first published barcode to include animal lineages
  (bovis, caprae, orygis)** at scale.
- Includes lineage 8 (described after Coll 2014) but published before
  L9, L10 were widely accepted.
- For **L9, L10** use the Guyeux golden CSV.
- For **animal lineage finer sub-classifications** (Bovis_La1,
  Caprae1_La2, Orygis_La3, Pinipedii, etc.) use the Guyeux golden CSV
  or **Zwyer 2021** (livestock-associated nomenclature).

## Strengths

- Largest sample size of any MTBC barcoding paper to date.
- Backwards compatible with Coll 2014 (20 shared markers).
- Includes animal lineages.
- Integrated into widely-used tooling (TB-Profiler).
- Train/test split provides independent validation.

## Limitations

- Does not include L9, L10.
- Some animal sub-lineages are coarse (no Bovis_La1 vs Bovis_La1.x).
- Use the **Guyeux golden CSV** for the latest refinements.
