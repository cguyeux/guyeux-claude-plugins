---
name: atlas-add-lineage
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST), peer-reviewed MTBC Atlas:
  scaffold a lineage page (`content/lineages/<id>/{meta.yaml, en.md, fr.md}`) from
  a sub-lineage characterisation project (`mtbc/<id>/article/main.tex` +
  `data/strains.csv`), then push it with `ingest.add_lineage`. Use when a
  characterised MTBC sub-lineage should reach the Atlas, or a fiche needs
  refreshing from an updated manuscript.
argument-hint: "<lineage-id> [--from <source-project>]"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
user-invocable: true
---

# /atlas-add-lineage -- Scaffold and publish an Atlas lineage page

This skill scaffolds a lineage page for the **MTBC Atlas** (`~/docs/codes/mtbc/en_cours/atlas_mtbc/`)
from an existing project of characterisation (`~/docs/codes/mtbc/<lineage>/`). The Atlas
publishes a normalised page per (sub-)lineage so that the diversity uncovered by brute-
force MTBC inventory can reach readers without waiting for journal peer-review.

## When to use

- A sub-lineage project (`mtbc/<id>/article/main.tex`, etc.) is mature enough to be
  exposed on the Atlas.
- An existing Atlas page must be refreshed from an updated manuscript.
- A new clade analysis (with strain counts, defining SPDIs, possibly dating and
  selection results) is ready to be made browsable.

**Do not use** for lineages with fewer than 5 strains (microvariation, not real
diversification, see the user-level feedback memory `feedback_minimum_sublineage_size`).

## What the skill does

1. **Reads the source project** at `~/docs/codes/mtbc/<lineage>/` :
   - `article/main.tex` (or `main_fr.tex`), abstract, claims, key numbers.
   - `CLAUDE.md` and `cahier_de_labo.md`, context, current state.
   - `data/strains.csv` and `data/ena_metadata.csv`, geography.
   - `data/spoligotypes.csv`, `data/thd_haplotypes.csv`, `data/mk_input_*.csv`,
     etc., specialised analyses, picked up where present.
   - `claim_check.md` (if present), verified facts.
2. **Looks up canonical phylogeny data** via the `mtbc-lineages` skill, against
   the authoritative registry `~/docs/codes/mtbc/en_cours/global_supplementary/barcoding_v2/barcode_complete.tsv`
   and the physical source `mtbc/bdd/actuelle/<id>/` (see `SOURCES_OF_TRUTH.md`).
   `lignees.py` is a marker bank only; do **not** read `snp_barcoding.csv` (obsolete v1).
3. **Drafts** `content/lineages/<id>/meta.yaml` with the 10 canonical sections
   (3 mandatory, 7 conditional; see `~/docs/codes/mtbc/en_cours/atlas_mtbc/content/lineages/README.md`).
   The structured fields drafted are **phylogeny, dating, drug-resistance,
   selection, codivergence, epidemiology, host, methods and references**, alongside
   the prose synthesis of step 4.
   Conditional sections (dating, drug-resistance, selection, codivergence, epidemiology,
   host) are populated only when the source project has publishable numbers
   (p-values, CIs, effectifs). The **`selection`** section's pathway-level narration is
   auto-drafted by `mtbc-gene` pathway mode (`--from-selection`) when the project ships a
   selection table (see *Populating the selection section* below).
4. **Drafts** `content/lineages/<id>/en.md` (and `fr.md` if the user requested
   bilingual). Prose is a synthesis of the abstract + key findings of the manuscript,
   written in the Atlas voice (concise, neutral, no marketing).
5. **Asks the user to review** the drafts before any commit. Never auto-commit.
6. **Runs ingestion** : `cd ~/docs/codes/mtbc/en_cours/atlas_mtbc && .venv/bin/python -m ingest.add_lineage <id>`,
   then `.venv/bin/python -m ingest.ingest_geography --lineage <id>` if `data/strains.csv`
   was found.
7. **Prints the URL** : `http://localhost:8000/lineage/<id>` and reminds how to
   start the dev server.

## Populating the selection section (pathway narration)

When the source project ships a selection table -- `data/mk_input_*.csv` (variant-level),
a per-gene `*dnds*.tsv/.csv`, or any table with a gene/locus column plus a dN/dS-style
statistic or `effect`/`impact` columns -- the `selection` section's pathway-level prose is
drafted automatically by **`mtbc-gene` (pathway mode, `--from-selection`)**. It maps the genes
the signal concerns onto the pathway catalogue and narrates the affected pathways curated-first
(annotation_mtbc: UniProt + EC + Pfam) and network-aware (STRING PPI cohesion):

```bash
SK=${CLAUDE_PLUGIN_ROOT}/skills/mtbc-gene
"$SK/run_pathway.sh" --from-selection ~/docs/codes/mtbc/<id>/data/mk_input_annotated.csv --lineage <id> --min-variants 3 --top 3 --paragraph
```

The trailing `--paragraph` seeds the prose of the `selection` section; the JSON
`pathway_hits[]` (each with `selected_in_pathway`, `fraction`, and a curated + network
`narration`) can be listed as structured detail beneath it. `selected_module` reports
whether the selected genes form a cohesive PPI module (a strong, pathway-coherent signal)
or a dispersed mutational load.

**The significance gate (mandatory check).** Prefer feeding a **McDonald-Kreitman output**
(`mk-ascertainment`: per-gene `alpha`/`DoS` or `Dn`/`Ds`/`Pn`/`Ps`). The tool then returns
`test_concluded`: write the `selection` section **only when `test_concluded` is true**. When
it is false the paragraph reads *"... did not yield a significant per-gene signal ... No
selection section should be written."* and the conditional section must be **omitted** (an MK
table dominated by negative alpha, NI > 1, means purifying selection / excess polymorphism,
not a claimable signal). This is the machine-checkable form of *No premature publication*.

This **reads** an existing selection result; it does **not** infer selection. Run the test
itself with `mk-ascertainment` / `convergent-evolution` first. At a low `--min-variants`, the
variant-level mode surfaces mutational load (PE/PPE, PDIM) rather than strict positive
selection -- prefer a gated MK table for a defensible claim.

## Sub-lineages handling

By convention, the Atlas hosts **one page per (sub-)lineage**, not one per clade.
When the source project covers `L4.13` and its descendants `L4.13.1`, `L4.13.2`,
the skill produces three sets of files :

- `content/lineages/L4.13/`, comparative analyses, full prose, all the
  conditional sections that apply to the whole clade.
- `content/lineages/L4.13.X/`, concise per-sub-lineage page : defining SPDI,
  geographic breakdown of *its* strains, epidemiological status if applicable,
  and a "See [parent](/lineage/L4.13) for comparative analyses" pointer.

The sub-lineage pages stay short on purpose : duplication of dating, selection,
methods, references would create maintenance burden and inconsistency. The
parent page is the source of truth for comparative facts.

## Conventions

- **Sources of truth.** Phylogeny / lineage definition : `mtbc/bdd/actuelle/<id>/`
  (physical source) + `mtbc/global_supplementary/barcoding_v2/barcode_complete.tsv`
  (authoritative derived registry; see `SOURCES_OF_TRUTH.md`). `lignees.py` =
  marker bank (may be stale for active clades); `snp_barcoding.csv` = obsolete v1,
  never read. Strains : `mtbc/bdd/actuelle/<id>/`. Geography :
  `mtbc/<lineage>/data/strains.csv`. Prose : the manuscript.
- **AUP framing.** Every paragraph of prose written by this skill must keep the
  Guyeux-group academic-research framing : `peer-reviewed`, `published research`,
  `scientific characterisation`. No clinical, surveillance, or operational tone.
- **Bilingual.** EN is the default. FR is only added if the user explicitly asks
  or if the source project already has `main_fr.tex` with publishable content.
- **No premature publication.** Conditional sections (drug-resistance, selection,
  codivergence, etc.) appear only when the source has p-values + CIs. A hunch is
  not a fact. The skill defaults to omitting a section when in doubt.
- **Markdown links between fiches.** `[L4.13](/lineage/L4.13)` for cross-fiche
  navigation. Internal Atlas paths only, no external links other than DOIs / PMIDs
  in the references block.

## Inputs the skill prompts for

If the source project is ambiguous or partial, the skill asks :

- Which manuscript / branch is canonical (default : the latest commit on
  `mtbc/<lineage>/article/`).
- Whether the FR page should be drafted (default : EN-only).
- Whether to publish sub-lineage pages or only the parent (default : both).

## Quick-start

```bash
# Scaffold L4.17 from its existing project
/atlas-add-lineage L4.17

# Refresh L4.13 from a recently-updated manuscript
/atlas-add-lineage L4.13 --from ~/docs/codes/mtbc/en_cours/L4.13

# Pre-flight check : list which conditional sections will be populated
/atlas-add-lineage L4.17 --dry-run
```

## Outputs

```
~/docs/codes/mtbc/en_cours/atlas_mtbc/content/lineages/<id>/
  meta.yaml          # structured fields (10-section schema)
  en.md              # editorial prose, English
  fr.md              # editorial prose, French (if requested)
  <id>.X/            # one sub-lineage subdir per descendant (if any)
    meta.yaml
    en.md
    fr.md            # if requested
```

Then in the Atlas database (`~/docs/codes/mtbc/en_cours/atlas_mtbc/data/db.sqlite`) :
- `Lineage` rows for `<id>` and each descendant (idempotent upsert).
- `Lineage.extra` populated from the `meta.yaml`.
- `Strain` rows linked from `bdd/actuelle/<id>/<SRA>/`.
- `Marker` rows for RD missing in ≥ 80 % of strains.
- `TaxonomyMap` rows for the Coll / Freschi / Napier equivalences.
- `Editorial` rows with rendered HTML.

## What this skill does not do

- It does not run new analyses (use `lineage-subdivision`, `molecular-clock`,
  `mk-ascertainment`, `thd`, etc. *before* invoking this skill).
- It does not validate scientific claims (use `claim-check` first, then this skill).
- It does not verify bibliographic references (use `bib-check`).
- It does not publish to a remote server (the Atlas is local for now; deployment is
  a separate concern).

## Workflow alignment

```
mtbc/<id>/article/main.tex  (manuscript)
    ↓ analyses skills (lineage-subdivision, molecular-clock, thd, mk-ascertainment, …)
    ↓ qualité skills (claim-check, bib-check, deai-latex, manuscript-review)
mtbc/<id>/  (consolidated project)
    ↓ /atlas-add-lineage  ← THIS SKILL
    └─ mtbc-gene (pathway --from-selection)  → drafts the `selection` section
atlas_mtbc/content/lineages/<id>/
    ↓ ingest.add_lineage
atlas_mtbc/data/db.sqlite  →  /lineage/<id> on the local Atlas server
```

The Atlas is a publication channel parallel to journal submission; the manuscript
remains the canonical scientific artefact (LaTeX, peer-review when possible), and
the Atlas page is its accessible reflection for browsing.
