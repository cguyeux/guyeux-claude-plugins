# Stucki 2016 — MTBC Lineage 4 sub-lineages

## Citation

Stucki D, Brites D, Jeljeli L, Coscolla M, Liu Q, Trauner A, Fenner L,
Rutaihwa L, Borrell S, Luo T, Gao Q, Kato-Maeda M, Ballif M, Egger M,
Macedo R, Mardassi H, Moreno M, Tudo Vilanova G, Fyfe J, Globan M,
Thomas J, Jamieson F, Guthrie JL, Asante-Poku A, Yeboah-Manu D,
Wampande E, Ssengooba W, Joloba M, Boom WH, Basu I, Bower J, Saraiva M,
Vasconcellos SEG, Suffys P, Koch A, Wilkinson R, Gail-Bekker L, Malla B,
Ley SD, Beck HP, de Jong BC, Toit K, Sanchez-Padilla E, Bonnet M,
Gil-Brusola A, Frank M, Penlap Beng VN, Eisenach K, Alani I, Wangui
Ndung'u P, Revathi G, Gehre F, Akter S, Ntoumi F, Stewart-Isherwood L,
Ntinginya NE, Rachow A, Hoelscher M, Cirillo DM, Skenders G, Hoffner S,
Bakonyte D, Stakenas P, Diel R, Crudu V, Moldovan O, Al-Hajoj S,
Otero L, Barletta F, Carter EJ, Diero L, Supply P, Comas I, Niemann S,
Gagneux S. **Mycobacterium tuberculosis lineage 4 comprises globally
distributed and geographically restricted sublineages.**
*Nature Genetics* 48(12):1535–1543 (2016).
DOI: [10.1038/ng.3704](https://doi.org/10.1038/ng.3704)

PDF: `~/Documents/codes/MTBC/TBannotator/data/TB_Stucki_2016.pdf`
Supplementary: `TB_Stucki_2016-S1.pdf`

## Key facts

- Focused on **Lineage 4** (Euro-American), the most geographically
  widespread cause of human TB.
- Defined **10 sub-lineages of L4** (L4.1 through L4.10), with distinct
  geographic patterns.
- **Generalist sub-lineages** (globally distributed): L4.1.2 (Haarlem),
  L4.3 (LAM), L4.10 (PGG3).
- **Specialist sub-lineages** (geographically restricted):
  - L4.1.1 (X-type) → Americas
  - L4.5 → East Asia (Vietnam, China)
  - L4.6.1 (Uganda) → East Africa
  - L4.6.2 (Cameroon) → West/Central Africa
  - L4.4 → globally widespread but rarer
  - L4.2 → Eastern Europe / Russia
- **Sample size**: ~3,000 L4 isolates from worldwide collections.
- The split into generalist vs specialist correlates with **niche width** —
  generalists tolerate more host populations.

## How the system is named in TBannotator/lignees.py

System key: `"Stucki"` in `lignees.py`. Each entry is
`(lineage_code, defining_SPDI)` for the L4 sub-lineages defined in this paper.

## Notes

- Stucki 2016 is the **canonical reference for L4 sub-lineage definitions**.
- The original L4 sub-lineage codes (4.1 through 4.10) are derived from this
  paper but had been used informally before in earlier work.
- For sub-sub-lineages (L4.1.1.1, L4.4.1.2, etc.), refer to the
  **authoritative home registry `barcode_complete.tsv` (+ `bdd/actuelle`)**,
  which has the most refined hierarchy (see `SOURCES_OF_TRUTH.md`).
- Stucki 2016 does NOT cover L1, L2, L3, L5, L6, L7, L8, L9, L10 — for
  those, use Coll 2014, Napier 2020, or the home registry `barcode_complete.tsv`
  (not the obsolete `snp_barcoding.csv`).

## Strengths

- Largest coordinated L4 sampling at the time (~3,000 isolates).
- Robust geographic interpretation (generalist/specialist).
- Well-supported phylogenetics (RAxML, MEGA).

## Limitations

- L4-only — no information on other major lineages.
- Some sub-lineage codes have been refined or renamed in later work.
- Always cross-check with **Guyeux golden CSV** for current usage.
