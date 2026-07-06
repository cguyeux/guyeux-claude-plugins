---
name: mtbc-lineages
description: >-
  Authoritative source on Mycobacterium tuberculosis complex (MTBC) lineage
  definitions, sub-lineage hierarchies, and SNP/SPDI markers. The taxonomic
  source-of-truth hierarchy is fixed in
  global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md: the live placement in
  bdd/actuelle/ and its derived registry barcode_complete.tsv are authoritative;
  lignees.py (key "moi" = Guyeux) is a historical SPDI MARKER BANK, reliable for
  stable major lineages and for third-party system definitions, but possibly
  DESYNCHRONISED for any sub-lineage produced by the multi-signal cycle (L1.*,
  Bovis1.*, BCG.*, deep L6). When no system is specified, "moi" is the implicit
  default for a marker lookup, but for an authoritative definition/assignment of
  an active clade, consult bdd/actuelle + barcode_complete.tsv first.

  Use this skill WHENEVER you need to: (1) look up a lineage's defining
  marker, (2) find the parent of a sub-lineage, (3) determine which lineage
  a SPDI belongs to, (4) confirm the hierarchy of L1/L2/L3/L4/L5/L6/L7/L8/
  L9/L10 and their sub-lineages, (5) reconcile conflicting classifications
  across systems, (6) cite the original publication for a taxonomy. ALWAYS
  prefer this skill over TBannotator MCP queries, direct CSV reads, or
  ad-hoc literature lookups for lineage facts.

  For step (6) — citing the original publication — also consider the
  `tbmonitor-papers` skill once a candidate citation is in hand:
  tbmonitor lets you confirm the paper's title, authors, journal and DOI
  in sub-second time against the pre-indexed PubMed TB corpus.
allowed-tools: Bash, Read, Grep, Glob
user-invocable: true
---

# /mtbc-lineages -- MTBC Lineage Authority

## Source of truth (read SOURCES_OF_TRUTH.md first)

The taxonomic authority hierarchy is **fixed canonically** in
`mtbc/global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`. Order of precedence:

```
1. bdd/actuelle/<clade>/             ← physical source (existence + per-strain placement)
2. barcoding_v2/barcode_complete.tsv ← authoritative derived registry (SPDI)
   + rd_markers.json / is_markers.json / _marker_overrides.json / _marker_blacklist.json
3. TBannotator system='Senelle'      ← snapshot (= moi/Guyeux, may lag)
4. lignees.py key 'moi'              ← MARKER BANK (1 SPDI/clade, possibly stale)
5. snp_barcoding.csv, strain_lineages.csv  ← OBSOLETE, never authoritative on read
```

This skill's working file for **marker lookups** is the live module:

```
~/docs/codes/mtbc/investigate_phylo/lignees.py
```

It defines a `lignees` dictionary keyed by classification system. Key `"moi"`
(= Guyeux) is the user's own classification, stored as a list of tuples
`(lineage_code, defining_SPDI)` (one canonical SPDI per clade; short codes
WITHOUT the `L` prefix: `"1.2.1.1.2.4"`, `"Bovis La1"`).

**IMPORTANT — `lignees.py` is NOT the gold standard.** It is a historical marker
bank, frozen out of the cycle's write loop (state of 2026-05-15). It is reliable
for **stable major lineages** and for **third-party system definitions** (keys
`"Coll"`, `"Napier"`…), but for any clade touched by the multi-signal cycle
(all of L1.\*, all of Bovis1.\*/BCG.\*, deep L6) it returns a **stale** taxonomy
(depth ≤5 for L1; Loiseau "Bovis La1.x" naming instead of "Bovis1.x"; BCG absent).
For those clades the authority is `bdd/actuelle` + `barcode_complete.tsv`.

Structure (simplified) :

```python
lignees = {
    "moi":   [("1", "NC_000962.3:4014430:C:T"), ("1.1.1", "..."), ...],
    "Ates":              [(...), ...],    #  48 entries
    "Coll":              [(...), ...],    #  62 entries
    "Coll L1":           [(...), ...],    # 1106 entries (L1 deep barcode)
    "Coscolla":          [(...), ...],    # 935 entries
    "Freschi":           [(...), ...],    #  95 entries
    "Gisch":             [(...), ...],    #   8 entries
    "Lipworth":          [(...), ...],    # 13610 entries
    "Merker":            [(...), ...],    # 283 entries
    "Napier":            [(...), ...],    # 420 entries
    "Netikul":           [(...), ...],    # 1835 entries
    "Palittapongarnpim": [(...), ...],    # 2177 entries
    "Shitikov":          [(...), ...],    #  20 entries
    "Shitikov23":        [(...), ...],    # 213 entries
    "Shuaib":            [(...), ...],    # 638 entries
    "Stucki":            [(...), ...],    #  23 entries
    "Thawornwattana":    [(...), ...],    #  93 entries
    "Zwyer":             [(...), ...],    #  92 entries
}
```

Each entry is a tuple `(lineage_code, defining_SPDI)`. The `lignees.py`
file may be edited by the user at any moment; the skill must never cache
a stale copy. Loading is done live on each call via `exec()` in an
isolated namespace.

## Default behaviour (CRITICAL)

When a request does **not** specify a classification system explicitly,
the implicit default is **`"moi"`** (Guyeux). Example :

- "What is the defining SPDI of 4.9.1?" → look in `lignees["moi"]` first.
- "Which lineage does `NC_000962.3:119599:C:G` define?" → search
  `lignees["moi"]` first.
- "What is the parent of 4.11?" → walk the hierarchy in `lignees["moi"]`.

The skill must only look outside `"moi"` when :
- the user explicitly asks for another system (`Coll`, `Napier`, ...), or
- no answer is found in `"moi"` and a fallback chain is justified.

## Fallback chain (strict order)

Lineage lookups go through these sources, **in this exact order, stopping at the
first authoritative match**. This chain operationalises `SOURCES_OF_TRUTH.md`.

0. **`bdd/actuelle/<clade>/` + `barcode_complete.tsv`** — the authoritative
   source for the **existence** of a clade and the **defining marker / hierarchy**
   of any clade touched by the multi-signal cycle (L1.\*, Bovis1.\*, BCG.\*, deep
   L6). For BCG and other SPDI-marker-less clades, the marker lives in
   `rd_markers.json` / `is_markers.json` (BCG has **no** row in
   `barcode_complete.tsv`). **Consult this first for an authoritative definition
   or assignment.**

1. **`lignees["moi"]`** — Guyeux marker bank, loaded live. Convenient first stop
   for a **single defining SPDI of a stable major lineage**. NOT authoritative
   for active-cycle clades (it is stale there — see the caveat above); when its
   answer would contradict `bdd/actuelle`/`barcode_complete.tsv`, the latter win.

2. **Other systems in the same `lignees.py` file** — Coll, Napier, Freschi,
   Stucki, Coscolla, Shitikov, Zwyer, Palittapongarnpim, Thawornwattana, Shuaib,
   Gisch, Netikul, Lipworth, Ates, "Coll L1", Merker, etc. (enumerate the keys
   dynamically — do not hard-code the list). Consulted when the user asks for a
   published system, or `"moi"` has no entry.

3. **TBannotator PostgreSQL** (`mv_lineage_markers`, `mv_strain_classification`,
   `tb_lineage_marker`) — `system='Senelle'` IS the home system (= moi/Guyeux),
   used for per-strain assignment at scale. It is a **snapshot** that lags the
   live taxonomy; in case of conflict, `bdd/actuelle` + `barcode_complete.tsv`
   win.

4. **Reference notes** (`references/*.md`) — synthesised notes from the original
   papers. Used only for **citations, methodology, sample size, geographic scope**
   of a published taxonomy — never a source of truth for SPDIs or lineage codes.

5. **`snp_barcoding.csv`** / **`strain_lineages.csv`** — **OBSOLETE (v1 / stale
   export). NEVER read as a source of truth** for the defining SPDI, the
   hierarchy, or an assignment (`snp_barcoding.csv` lags on Bovis and still
   contains "proto-BCG"; `strain_lineages.csv` is from 2026-04-05 and lacks L9).
   `snp_barcoding.csv` remains a *live input protected by the cycle*, not a
   reference. At most, decorate output with a strain-count column, never a
   taxonomic fact.

## What this skill OVERRIDES

This skill's answers follow the authority hierarchy of `SOURCES_OF_TRUTH.md`.
It takes priority over :
- **TBannotator MCP** (`system='Senelle'` snapshot) when its output conflicts
  with `bdd/actuelle` + `barcode_complete.tsv`.
- **Direct reads** of `snp_barcoding.csv` / `strain_lineages.csv` (obsolete) as a
  primary source.
- **Web search results** and memory entries that contradict the current
  taxonomy in `bdd/actuelle` + `barcode_complete.tsv`.
- **Other skills** (`tbannotator-mcp`, `clade-finder`, `lineage-comparison`,
  `tb-cli`) when their output conflicts with this skill on lineage facts.

Conversely, **this skill must defer** to `bdd/actuelle` + `barcode_complete.tsv`
(and to `lineage-cycle`, the write authority) whenever its own `lignees.py`-based
answer would be stale for an active-cycle clade. The arbiter is
`SOURCES_OF_TRUTH.md`, not this skill.

## Triggering

```
/mtbc-lineages                                  # overview: file status, systems, counts
/mtbc-lineages lookup 4.9                       # default system = "moi"
/mtbc-lineages lookup 4.9 --system Coll         # explicit other system
/mtbc-lineages lookup L5.1.2                    # nested sub-lineage
/mtbc-lineages spdi NC_000962.3:3592708:C:T     # which lineage does this SPDI define?
/mtbc-lineages parents 5.1.2                    # full ancestry chain (in "moi")
/mtbc-lineages children 5                       # direct sub-lineages (in "moi")
/mtbc-lineages system Coll                      # list all markers in a published system
/mtbc-lineages compare 5 moi Coll Napier        # cross-taxonomy reconciliation
/mtbc-lineages cite Stucki                      # full bibliographic reference

# Classify a sample against ALL 18 taxonomy systems at once
/mtbc-lineages classify <spdi.txt|report.json|snps.vcf|dir>
/mtbc-lineages classify <path> --min-pct 50             # only show >=50% match
/mtbc-lineages classify <path> --system Palittapongarnpim  # restrict to one system

# Special-case lineage tests (see section below)
/mtbc-lineages is-l4.9 <spdi.txt | report.json>        # 57 inverse markers + IS6110
/mtbc-lineages is-l4.10 <spdi.txt | report.json>       # combinatorial presence/absence
/mtbc-lineages is-mtbc <report.json>                   # IS6110-based MTBC sensu lato
/mtbc-lineages ancestral-signature <report.json>       # L8/Canettii shared ancestry
/mtbc-lineages pgg                                     # PGG reference (Sreevatsan 1997)
```

The dispatch logic lives in `scripts/lineages.py` (run via
`python3 ${CLAUDE_PLUGIN_ROOT}/skills/mtbc-lineages/scripts/lineages.py <subcommand>`).

## Classify — multi-system lineage identification

The `classify` command takes a sample's SPDI set (from `spdi.txt`,
`report.json`, or `snps.vcf`) and checks it against **all 18 taxonomy
systems** in `lignees.py`. For each system, it reports every lineage
whose defining marker(s) match.

### Match percentage

When a lineage is defined by multiple SPDIs (e.g. Palittapongarnpim L1
has 550 markers), the command reports the fraction that match. This is
critical for systems like Palittapongarnpim, Coll L1, Lipworth, and
Netikul where lineages are defined by dozens to hundreds of markers.

A visual bar shows the match level:

```
Palittapongarnpim:
  1                     539/550  ███████████████████░   98.0%
  1.2.2                 147/150  ███████████████████░   98.0%
```

For systems where each lineage has a single defining SPDI (e.g. "moi",
Coll, Freschi), the lineage is simply listed without percentage (100%
implied by presence).

### Negative markers

Markers prefixed with `-` in `lignees.py` match when the SPDI is
**absent** from the sample. Example: `Coll:4` is defined by
`-NC_000962.3:931122:T:C` (absence of this SNP).

### Input formats

- `spdi.txt` — one SPDI per line (TBannotator standard)
- `report.json` — TBannotator report (SPDIs extracted by regex)
- `snps.vcf` — VCF format (position converted to 0-based SPDI)
- A directory containing any of the above

### Flags

- `--system <name>` — restrict to a single taxonomy system
- `--min-pct N` — hide matches below N% (useful for noisy systems
  with many markers, default: 0)

### Interpretation guidelines

- **"moi" (Guyeux) is always shown first** and is the authoritative
  classification.
- A match in "moi" at a given level (e.g. `1.2.2`) means the sample
  belongs to that lineage.
- Matches in other systems at <50% should be treated as noise.
- Discordance between systems is normal and expected — different
  authors define lineages differently.

---

## Classer un SRA (barcoding v2 — "moi" prioritaire)

When the task is **"classify this SRA / this strain / this `spdi.txt`"**
(rather than looking up a lineage definition), use the dedicated
**barcoder v2** instead of the in-skill `classify` dispatcher. The
barcoder applies the same precedence philosophy as this skill — the
Guyeux **"moi"** system is authoritative, published systems are
informative only — but it ships precomputed marker tables and a
cross-mapping table that make the SRA call fast, offline, and
reproducible.

### Tool

```
python3 /home/christophe/docs/codes/mtbc/global_supplementary/barcoding_v2/barcoder/barcode.py <spdi.txt>
python3 .../barcoder/barcode.py <spdi.txt> --json          # machine-readable
python3 .../barcoder/barcode.py --sra ERR4798406           # live TBannotator fetch (needs psycopg2 + TBANNOTATOR_DSN)
```

The standard offline workflow uses the Python standard library only.
Input is a `spdi.txt` (one `NC_000962.3:pos:ref:alt` per line), exactly
the format of `bdd/actuelle/<lineage>/<SRA>/NC_000962.3/spdi.txt`.
Equal-length multi-base substitutions are canonicalised to one SNP per
differing position, so matching is representation-independent.

### Precedence (same law as the rest of this skill)

1. **Non-MTBC screen first.** If the sample is not MTBC, do NOT force an MTBC
   lineage call. The strain is tested against near-MTBC *Mycobacterium* species
   signatures; if >50 % of a species' robust markers are carried, it is flagged
   as that species **before** any MTBC lineage call. A genus-wide recognition
   reference now exists — single entry point
   **`global_supplementary/RECOGNITION_STRATEGY.md`** — organised in three
   complementary levels (no single referential covers the whole genus):
   - **category** : `MTBC_founder_markers_19_*` (present ⇒ MTBC),
     `Canettii_ancestral_markers_*` (*M. canettii*), `hors_mtbc_species.tsv` (near-MTBC type strains + ANI);
   - **species** : rpoB BLAST DB `global_supplementary/conserved_gene_markers/`
     (robust species ID, the right tool for species DIVERGENT from H37Rv such as
     *leprae*/*gordonae*/*xenopi* where SPDI-vs-H37Rv panels fail) **+** SPDI panels
     `global_supplementary/species_markers/` (~48 species, 17 robust at n≥3; high
     resolution for species close to H37Rv) **+** `M_kansasii_robust_markers_*`;
   - **subspecies / complex** : `global_supplementary/species_markers/subtypes/`
     for complexes that have NO species-level core (MAC, MKC) — e.g. *M. avium*
     subsp. *paratuberculosis* (MAP) ships a panel; MAA/MAH and *M. intracellulare*/
     *chimaera* are paraphyletic / cross-labelled (re-type molecularly first).
   This supersedes the earlier state where only *M. kansasii* shipped a panel.
   Recognition limits (rpoB-indistinct complexes, 0-marker species) are listed in
   `RECOGNITION_STRATEGY.md`. Reference lives in `global_supplementary/` (single
   source); do not duplicate into the skill's `data/`.
2. **"moi" tree descent (authoritative).** The lineage is the deepest
   supported node of the Guyeux tree (representative SPDI carried **and**
   ≥70 % of the node's positive markers present). This is the answer.
3. **Cross-mapping (informative only).** The "moi" call is then mapped to
   each published system via `taxonomy_crossmap.tsv`, reporting
   `equal` / `moi<T` / `T<moi` / `overlap` plus Jaccard %. These are
   equivalences for context, **never** an override of the "moi" call.

### New sources of truth (barcoding v2)

These supersede the legacy `snp_barcoding.csv` for SRA classification.
They live both at the project root
(`global_supplementary/barcoding_v2/`) and, shipped with the tool, under
`barcoder/data/`:

| File | Role |
|------|------|
| `barcode_simple.tsv` | **one representative defining SPDI per (sub-)lineage** + `parent` + validation note. The tree skeleton of the "moi" system. |
| `barcode_complete.tsv` | **full positive/negative marker set per lineage** (`role` = positive/negative, with exclusivity/polarisation notes). Used for the ≥70 % majority support test. |
| `taxonomy_crossmap.tsv` | **CANONICAL "moi" → published-systems cross-map** (~19 systems incl. Ates, Coll, "Coll L1", Coscolla, Freschi, Gagneux, Gisch, Lipworth, Merker, Napier, Netikul, Palittapongarnpim, Shitikov, Shitikov23, Shuaib, Stucki, Thawornwattana, Zwyer — **enumerate the `system` column dynamically, do not hard-code**); columns `moi_lineage, system, best_match_code, relation, jaccard_pct, inclusion_dir, inclusion_pct, n_moi, n_T, n_inter`. This is THE source for any "moi vs Coll/Napier/…" comparison (population-level); per-strain, cross TBannotator `system='Senelle'` vs `system='Coll'`. `Gagneux` is a broad major-lineage system with no fine SPDI barcode in `lignees.py` — find it here / in TBannotator. |
| `hors_mtbc_species.tsv` | near-MTBC species reference metadata (11 type strains). |
| `M_kansasii_robust_markers.txt` | robust non-MTBC species panel (kansasii). |
| `RECOGNITION_STRATEGY.md` | **genus-wide recognition entry point** (3-level decision tree, MTBC + non-MTBC). Read for any non-MTBC sample. |
| `conserved_gene_markers/` (rpoB FASTA + BLAST DB + identity matrix) | **species ID by rpoB** (44 species; the tool for species divergent from H37Rv). `blastn -db conserved_gene_markers/rpoB`. |
| `species_markers/` (`<sp>_markers.txt` + SUMMARY + README) | per-species SPDI-vs-H37Rv core-exclusive panels (~48 species). |
| `species_markers/subtypes/` | sub-typing panels for NTM complexes (MAC: MAP; etc.). |

`barcode_simple.tsv` and `barcode_complete.tsv` are the **authoritative derived
registry** for the barcoder (see `SOURCES_OF_TRUTH.md`): the legacy
`snp_barcoding.csv` (`global_supplementary/snp_barcoding.csv`) is **obsolete v1**,
read-only, never a reference. When in doubt about a single defining marker the
authority is `bdd/actuelle` + `barcode_complete.tsv`; `lignees.py` key `"moi"` is
a marker bank that may be stale for active-cycle clades. For SPDI-marker-less
clades (e.g. BCG) the marker is in `rd_markers.json` / `is_markers.json`, not in
`barcode_complete.tsv`.

### Reading the output

The barcoder prints the SPDI count, the **Guyeux lineage** (the answer),
the full descent path with per-node `matched/total` marker fractions,
and the informative published equivalents. With `--json` it returns the
same as a structured object for downstream use. If no root branch is
supported, the strain is reported **unassigned** rather than guessed —
in that case fall back to the in-skill `classify` (multi-system) and the
`is-mtbc` / `ancestral-signature` special-case tests below to diagnose
whether it is non-MTBC, basal (L8/Canettii), or a coverage problem.

When a reviewer or downstream task needs the published-system label,
read it from `taxonomy_crossmap.tsv` (or the barcoder's "Informative
equivalents" block) — do **not** re-derive it from `snp_barcoding.csv`.

---

## Special cases (CRITICAL — do not try to normalise these)

Four MTBC classification problems cannot be solved by a simple
`(lineage_code → defining_SPDI)` lookup and require dedicated logic.
The skill provides a first-class command for each, with reference data
files in the `data/` subdirectory.

### Taxonomie Bovis (mise à jour 2026-06-30, nomenclature pointée)

> ⚠️ **La subdivision `s2.X.Y.Z` détaillée plus bas est SUPERSÉDÉE (datée 2026-05-16, pré-refonte).** La taxo
> *M. bovis* a été refondue en juin 2026 (re-encodage trichotomie 22-06 puis re-peignages 27-30 juin). Le chemin
> `bdd/actuelle/Bovis2.*` N'EXISTE PLUS (notation pointée : `bdd/actuelle/Bovis.2.*`). **Source autoritative
> courante = `bdd/actuelle/Bovis.*` (physique) + `global_supplementary/barcoding_v2/barcode_complete.tsv`
> (régénéré) ; atlas narratif = `Bovis_full/article/supplementary_materials/atlas_bovis_sublineages.md`.** L'arbre
> `s2.X.Y.Z` ci-dessous est conservé pour ses annotations BIOLOGIQUES (hôtes, géo, patterns wildlife-livestock,
> toujours valides), PAS pour ses labels (drifté).

**Structure courante (vérifiée par souches/RD, 2026-06-30) :**
- `Bovis.1` — proto basal est-africain (11 souches).
- couronne `Bovis.2`, trichotomie :
  - `Bovis.2.1` : Af2 est-africain (`Bovis.2.1.1`, 123) + radiation européenne (`Bovis.2.1.2.2.2.2`) + **clade
    vaccinal BCG = `Bovis.2.1.2.2.2.1`** (722, RD1-délété à 100 % ; sœur sauvage RD1-intacte `Bovis.2.1.2.2.2.2`).
  - `Bovis.2.2` : Af1 ouest-africain (`Bovis.2.2.1`, 97) + clade C ibéro-colonial (`Bovis.2.2.2.1`, incl. clade
    Kruger `Bovis.2.2.2.1.7.*`) + clade D ouest-européen (`Bovis.2.2.2.2.1`) + cœur Eu1 britannique (`Bovis.2.2.2.2.2`).
  - `Bovis.2.3` : eurasien à composante humaine (Chine ; Anatolie/Caucase/Levant).
- **Identifier une souche par les marqueurs de `barcode_complete.tsv` (courant) + RD via `report.json` (BCG =
  RD1-délété), JAMAIS par `markers_v2/` (pré-22-juin) ni par le label `s2.X` historique.**

---

#### [HISTORIQUE pré-22-juin, 2026-05-16] Subdivision pectinée `s2.X.Y.Z` — annotations biologiques valides, labels PÉRIMÉS

Nomenclature historique (convention : `.1` = clade émergent basal, `.2` = continuation pectinée). À lire pour les
associations hôte/géo, pas pour les labels (cf. bannière ci-dessus) :

```
Bovis2 (~5200 souches BDD)
├── s2.1 (Cameroun pastoral)
│   ├── .1.1 .1.2 — basale Bos taurus
│   └── .2 décomposée en 4 sous-clades pectines (Cameroon multi-host)
├── s2.2.1 (cosmopolite mondial 5 vagues)
│   ├── .1 sub1 ouest-africain sahélien basal
│   ├── .2.1 sub2 Pologne+bison Europe centrale
│   ├── .2.2.1 sub3 Ibéro-caraïbe (26 markers solides)
│   ├── .2.2.2.1 sub4 Méditerranéen ouest (20)
│   ├── .2.2.2.2.1 sub5 Maroc-Mexico hispano-colonial
│   ├── .2.2.2.2.2.1 sub6 SAfrica wildlife (26, 10 espèces)
│   ├── .2.2.2.2.2.2.1 sub7 USA-Mexico expansion clonale
│   └── .2.2.2.2.2.2.2 sub8 Ibérique focal Espagne
├── s2.2.2.1 (France-badger, 97 markers racine)
│   └── 8 sous-clades + sous-structure 178 expansion clonale (Meles meles dans 6 sub)
└── s2.2.2.2 (973+ expansion mondiale)
    ├── s2.2.2.2.1.* (Clade 1, 13 markers)
    │   ├── s2.2.2.2.1.1.* — UK-Badger #1 (40, 44 markers)
    │   ├── s2.2.2.2.1.1.1_cosmopolite — ancestral global (13, 24)
    │   ├── s2.2.2.2.1.2.1.* — UK-Badger #2 et #3 + NZ wildlife
    │   │   ├── .a_NZSAfricaWildlife
    │   │   ├── .b_UKBadgerSheep (Meles+Cervus+Ovis aries, 12 markers)
    │   │   ├── .c_UKBadger (0)
    │   │   └── .d_UKBadger (39)
    │   └── s2.2.2.2.1.2.2.* — Ireland-deer + NZ wildlife + Mex/USA
    │       ├── .emerge9_IrelandDeer (9, Cervus elaphus)
    │       ├── .a_USA_DomRep, .b_Mexico, .c_NZ_Argentina, .d_MexUSA_dominant
    └── s2.2.2.2.2.* (Clade 2, 2 markers)
        ├── s2.2.2.2.2.1.* (NZ+SAfrica wildlife le plus riche, 200+)
        │   ├── sub2_SAfricaBuffalo (Syncerus caffer pur, 90 markers !)
        │   ├── sub3_SAfricaWildlife (Lycaon+Panthera+Homo, 43)
        │   ├── sub4_NZ + sub6_NZ (NZ multi-hôte 9 espèces)
        ├── s2.2.2.2.2.2.1.* (Mex cattle ancestral)
        │   ├── .a_CanadaBison (12, *Bison bison athabascae* Wood Buffalo)
        │   ├── .b/c_Mex_clonal
        └── s2.2.2.2.2.2.2.* (Mex+USA industriel, expansion moderne)
            ├── sub1_MexUSAspillover (Cattle+Homo USA récent, 75)
            ├── sub5_MexDairyCheeseSpillover (Dairy+Cheese zoonose, 28)
            └── sub2/3/4/6
```

**Patterns wildlife-livestock universels** (10 clades indé sur 5 continents) :
France-badger, UK-badger ×3, Ireland-deer, NZ-multi 9 espèces,
SAfrica-Buffalo, SAfrica-Wildlife divers, SAfrica sub6 s2.2.1,
Canada Wood Buffalo Bison.

**2 patterns anthropiques spillover** : sub1 MexUSAspillover et
sub5_MexDairyCheeseSpillover (Homo USA/Mex 2011-2022, fromage 2018).

**2 routes historiques** : sub5 Maroc-Mexico hispano-colonial XVI-XVII
et basales Espagne→France post-médiévale.

**Pour identifier une souche Bovis (méthode COURANTE 2026-06-30)** : utiliser `barcode_complete.tsv` (marqueurs SPDI
exclusifs, régénéré) + RD via `report.json`/`large_rd` pour les clades RD-définis (BCG = RD1-délété). Les markers
`Bovis_full/data/markers_v2/Bovis2_*.txt` sont PÉRIMÉS (pré-22-juin) — ne plus les utiliser pour classer. 

**Voir aussi** : skill [[pectinated-subclade-mining]] pour la méthodo
de subdivision, mémoire utilisateur `project_bovis_taxonomy.md`
(1100+ lignes documentation complète).

### L4.9 — inverse-marker detection

L4.9 contains H37Rv, which is the reference genome. Because every SPDI
is defined relative to H37Rv, **L4.9 strains have no positive defining
marker** — their own lineage-specific variants become the reference
state and disappear from the SPDI list. The solution is **inverse
markers**: 57 pan-MTBC positions (present in all other lineages AND
Canettii) whose **absence** defines L4.9.

- **Data file** : `data/L4.9_reverse_markers.csv` (57 SPDIs, each with
  penetrance stats in L4.9 vs outgroup).
- **Threshold** : `<=10` of the 57 markers present → L4.9. `>=41`
  present → not L4.9. Gap of 31 markers between the two populations
  makes the criterion extremely robust (sensitivity 99.5%, specificity
  100% on 2 804 strains validated).
- **Subsidiary confirmation** : 4 IS6110 positions specific to L4.9
  (`889020`, `1541951`, `2365413`, `3890778`), with >=3/4 present
  giving additional confidence. Requires a `report.json` that carries
  insertion-sequence data.
- **Command** : `is-l4.9 <spdi.txt | report.json>`.
- **Why it matters** : without this, TBannotator and any Coll/Napier
  lookup will fail silently for L4.9. The defining SPDI in Coll
  (`-NC_000962.3:1759251:G:T`, dnaK A58A) is itself an absence
  criterion that misclassifies 2 464 non-L4.9 L4 strains.

### PGG — Principal Genetic Group (operational SPDI rule)

The PGG is determined by the presence/absence of exactly **two SPDIs**
in a sample's `spdi.txt`, relative to the H37Rv reference:

| SPDI | Gene | Effect |
|------|------|--------|
| `NC_000962.3:2154723:C:A` | katG codon 463 | mRNA CGG(Arg) → CTG(Leu) |
| `NC_000962.3:7584:G:C` | gyrA codon 95 | AGC(Ser) → ACC(Thr) |

**Decision rule** (grep-based, no computation needed):

```
PGG1 = katG PRESENT  + gyrA PRESENT   (Leu + Thr, ancestral)
PGG2 = katG ABSENT   + gyrA PRESENT   (Arg + Thr, intermediate L4)
PGG3 = katG ABSENT   + gyrA ABSENT    (Arg + Ser, H37Rv state)
n.c. = katG PRESENT  + gyrA ABSENT    (Leu + Ser, convergent)
```

**Evolutionary pathway** (both changes on the L4 branch):
PGG1 (L+T) → PGG2 (R+T, katG changes first) → PGG3 (R+S, then gyrA)

**Lineage correspondences** (verified on BDD, 42 tests):
- PGG1: L1, L2 proto-Beijing, L3, L5, L6, L9, Bovis
- PGG2: L4.1, L4.2, L4.5, L4.11, L4.14 (intermediate L4)
- PGG3: L4.8, L4.9, L4.15 (most derived L4, H37Rv-like)
- Non-canonical: L2.2.2 modern Beijing (convergent gyrA Thr→Ser)

**Command**: `pgg` (reference display) or `pgg <spdi.txt>` (computation).
The command simply greps for the two SPDIs and applies the table above.

### L4.10 — combinatorial criterion with PGG link

L4.10 is **not** definable by a single positive marker. The entries in
`lignees.py` split across 2 locations and combine presence AND
absence :

```
Line 739–740 (intermediate markers):
  ("4.10.i1", "NC_000962.3:1130525:G:A")      # must be PRESENT
  ("4.10.i2", "-NC_000962.3:1759251:G:T")     # must be ABSENT

Line 3009–3011 (additional absence conditions):
  ("4.10", "-NC_000962.3:1692140:A:C")        # must be ABSENT
  ("4.10", "-NC_000962.3:7584:C:G")           # must be ABSENT — gyrA95
  ("4.10", "-NC_000962.3:960283:A:C")         # must be ABSENT
```

A sample is L4.10 **only if all five conditions hold simultaneously**.
Position `7584` is very likely the `gyrA` codon-95 SNP, which links
L4.10 directly to the **Principal Genetic Group** (PGG) classification
from Sreevatsan 1997 — the absence condition means the sample is on
the ancestral Thr95 state.

- **Command** : `is-l4.10 <spdi.txt | report.json>`.
- **Related** : `pgg` command displays the PGG reference table
  (`data/PGG_markers.tsv`). A full PGG computation is **not** wired
  yet — the katG463 position is approximate and needs verification
  before firm use.

### IS6110 — MTBC sensu lato detection

TBannotator indexes all *Mycobacterium*, not just the MTBC complex.
When the research question concerns the MTBC **and its emergence** (so
including things that are *outside* the complex as negative controls),
a robust first-pass filter is IS6110 presence : this insertion
sequence is specific to the MTBC + *M. canettii* and absent from other
mycobacteria.

- **Data file** : `data/IS6110_H37Rv.tsv` (16 canonical copies in
  H37Rv, extracted from `investigate_phylo/resources/NC_000962.3.gff3`).
- **Decision rule** :
  - `0 copies` → outside MTBC complex
  - `1–2 copies` → borderline (some L6/Africanum have very few copies)
  - `≥3 copies + ≥3 canonical positions` → MTBC sensu lato
- **Command** : `is-mtbc <report.json>` (requires IS6110 insertion
  data, not available in a bare `spdi.txt`).
- **Caveat** : IS6110 alone does not separate MTBC from *M. canettii*.
  Use `ancestral-signature` or lineage markers to distinguish.

### L8 / Canettii ancestral signature (corrected)

L8 is the most basal MTBC lineage. Together with *M. canettii*, it
retains several **ancestral genomic features** that were lost in the
modern MTBC radiation (L1–L7, L9, L10). This provides an independent
phylogenetic signal — a sample carrying an intact `cobF`, full-length
`PPE50`, `pknH` island or split adenylate cyclase is **basal** and
most likely L8 or *M. canettii*, not modern MTBC.

- **Data file** : `data/L8_Canettii_ancestral.tsv` with six entries
  (genes / islands + H37Rv coordinates + biology).
- **Known ancestral features** :
  - `cobF_mutM_island` (4.0 kb, B12 biosynthesis + DNA repair)
  - `pknH_island` (4.5 kb, 5 ORFs including a PknH-like kinase)
  - `PPE50_ancestral` (full-length 382 aa vs truncated 132 aa in H37Rv)
  - `adenylate_cyclase_split` (ancestral unfused form)
  - `TbD1_region` (mycosine transport, deleted in L2/L3/L4)
  - `Rv3728_canettii_shared` SNP (single variant shared with 54.8% of
    Canettii)
- **Command** : `ancestral-signature <report.json>` — currently
  displays the reference table and asks for coverage-level data; a
  fully automated check requires reading coverage over these regions
  (methodology documented in `mtbc/L8/l8_results_draft.md`).

**Important correction of a common mix-up** : an earlier version of
this skill and associated notes referred to an "rpo gene" supposedly
shared between L8 and *M. canettii*. After thorough search of the
project codebase (`mtbc/L8/`, `mtbc/Canettii/`), no such shared rpoA/
B/C/D was found. The real shared ancestral features are **cobF,
PPE50, pknH, TbD1**, and (for a single SNP) **Rv3728**. If a specific
rpo variant is intended as a marker, it must be clarified and added
separately.

### Data files summary

| File | Purpose |
|------|---------|
| `data/L4.9_reverse_markers.csv` | 57 pan-MTBC inverse markers |
| `data/IS6110_H37Rv.tsv` | 16 canonical IS6110 copies in H37Rv |
| `data/L8_Canettii_ancestral.tsv` | L8/Canettii ancestral genes & islands |
| `data/PGG_markers.tsv` | PGG reference (unverified, use with care) |

These files are the skill's **local reference layer**. They are
updated by copying from their upstream sources in `mtbc/` when the
upstream versions change. Current upstream sources :

- `data/L4.9_reverse_markers.csv` ← `mtbc/L4.9/data/reverse_markers_primary.csv`
- `data/IS6110_H37Rv.tsv` ← extracted from `mtbc/investigate_phylo/resources/NC_000962.3.gff3`
- `data/L8_Canettii_ancestral.tsv` ← synthesised from `mtbc/L8/l8_results_draft.md`

## Mode `lookup <lineage>`

1. **Parse** the lineage code (normalise variants like `L4.9` vs `4.9`).
   For an **active-cycle clade** (L1.\*, Bovis1.\*, BCG.\*, deep L6), check
   `bdd/actuelle` + `barcode_complete.tsv` first — `lignees.py` is stale there.
2. **Search `lignees["moi"]` first** (for stable major lineages). If found, return :
   - lineage code
   - defining SPDI (from `lignees.py` marker bank)
   - parent (computed by walking the dotted code, e.g. `4.9.1` → `4.9`)
   - optional enrichment (strain count) — clearly labelled as "enrichment",
     read from `barcode_complete.tsv`, never `snp_barcoding.csv`.
   - Source tag : `Source: lignees.py ["moi"] (Guyeux marker bank, loaded YYYY-MM-DD HH:MM; verify against bdd/actuelle for active clades)`.
3. **If not in `"moi"`** and no `--system` flag : scan all other systems
   in the same file and list every match with its system name. Tag :
   `Source: lignees.py [<system>] (fallback — not in Guyeux "moi")`.
4. **If `--system` is specified** : search only that key in `lignees.py`.
5. **If still not found** : escalate to TBannotator PostgreSQL via MCP
   (query `mv_lineage_markers` and `mv_strain_classification`). Tag :
   `Source: TBannotator PostgreSQL (last resort — not in lignees.py)`.
6. **If still nothing** : return "Unknown lineage" and suggest closest
   matches by string similarity across all systems in `lignees.py`.

## Mode `spdi <spdi>`

1. **Search `lignees["moi"]` first** for an exact SPDI match. If found,
   return the lineage code. Source : Guyeux marker bank (verify against
   `bdd/actuelle`/`barcode_complete.tsv` for active-cycle clades).
2. **If not in `"moi"`** : scan all other systems in `lignees.py`.
   Return every `(system, lineage_code)` pair that uses this SPDI.
3. **If still nothing** : escalate to TBannotator PostgreSQL
   (`tb_lineage_marker`).
4. **If still nothing** : report "SPDI not used as a defining marker in
   any known taxonomy".

## Mode `parents <lineage>` and `children <lineage>`

Walk the dotted lineage code in `lignees["moi"]` to build the ancestry
chain. For `4.9.1` → `4.9` → `4` → `(root)`. At each level, fetch the
defining SPDI directly from `lignees["moi"]`. Return the chain root →
leaf (for `parents`) or the list of direct children (for `children`).

For non-`"moi"` systems (via `--system`), use the same dotted-code walk
in the requested system's list.

## Mode `system <name>`

Print all `(lineage_code, defining_SPDI)` tuples for a given system.
Systems are whatever keys exist in the live `lignees.py` — no hard-coded
whitelist. Aliases : `moi` == `guyeux`.

## Mode `compare <lineage> <system1> <system2> [...]`

Show how each requested system labels the conceptual lineage, or which
marker each system uses. Default systems if none given : `moi`, `Coll`,
`Napier`.

## Mode `cite <author>`

Print the full citation block for a published taxonomy from
`references/<author>*.md`. Returns : title, journal, year, DOI, sample
size, geographic scope, methodology summary, original PDF location.

## Reference notes available in `references/`

| File | Source |
|------|--------|
| `Coll_2014.md` | Coll et al., Nature Communications 2014 — 62-SNP barcode |
| `Stucki_2016.md` | Stucki et al., Nature Genetics 2016 — L4 sub-lineages |
| `Freschi_2021.md` | Freschi et al., Nature Communications 2021 — population structure |
| `Napier_2020.md` | Napier et al., Genome Medicine 2020 — robust barcoding |
| `INDEX.md` | Index of all reference notes |

These notes are **never** a source of truth for SPDIs or lineage codes.
Use them only for citation, context, and reading the original PDFs.

## Loading policy

- `lignees.py` is **read live** at every invocation. Path resolution :
  1. `~/docs/codes/mtbc/investigate_phylo/lignees.py` (canonical)
  2. Any project-relative `lignees.py` discoverable from `pwd` (fallback
     for when the user works from an unusual context)
- Loading is done by `exec()` in an isolated namespace, capturing only
  the `lignees` dict. Stdout from the source file is suppressed (the
  upstream file may contain debug prints).
- If the upstream file is **missing** : the skill warns loudly, degrades
  to the most recent local snapshot if available, and marks every
  response as `DEGRADED`.
- The local `references/lignees.py` snapshot is **only** a safety net
  for when the upstream file is unreachable. It is never the primary
  source, and the skill's `overview` mode reports its staleness in days.

## Why this skill exists

Lineage definitions are the foundation of every MTBC analysis. Multiple
classification systems coexist (Coll, Napier, Freschi, Stucki,
Coscolla, Shitikov, ...), each with its own naming conventions, marker
SPDIs, and hierarchical depth. The user maintains an evolving personal
classification (`"moi"` = Guyeux = `Senelle` in TBannotator). The
**newest lineages, reclassifications and corrections now live in
`bdd/actuelle` and its derived registry `barcode_complete.tsv`**, produced
by the multi-signal cycle (`lineage-cycle`); `lignees.py` key `"moi"` is a
**marker bank that lags** them (frozen 2026-05-15). TBannotator stores a
`Senelle` snapshot that drifts; `snp_barcoding.csv` / `strain_lineages.csv`
are obsolete; published taxonomies are frozen at publication time. This
skill enforces the precedence fixed in `SOURCES_OF_TRUTH.md`: **bdd/actuelle
+ barcode_complete.tsv first; lignees.py "moi" as a marker bank (verified for
active clades); TBannotator Senelle snapshot; reference notes for citation
only; obsolete CSVs never**.
