---
name: string-db
description: >-
  Academic research toolkit for the Guyeux group (FEMTO-ST) MTBC pipeline:
  a resilient, stdlib-only client for the STRING v12 protein-association REST
  API (https://string-db.org), which aggregates known and predicted
  protein-protein associations decomposed into evidence channels
  (neighborhood, fusion, co-occurrence, co-expression, experimental, database,
  text-mining). Resolves locus tags to STRING ids, lists functional or physical
  interaction partners with per-channel scores, builds networks among a gene
  set, runs functional enrichment (GO/KEGG/Pfam/InterPro) and the PPI-enrichment
  test, and downloads network pictures. Default species is 83332
  (M. tuberculosis H37Rv) but works for any organism in STRING.

  Use when: you need a *guilt-by-association* second opinion on a gene
  (especially a hypothetical), to ask "what does this unknown gene work with?",
  to test whether a candidate operon/complex is significantly connected, or to
  get the functional enrichment of a small gene set. Reusable across coevolution,
  pathway-explanation, pangenome-enrichment and host-pathogen studies. For
  WHOLE-PROTEOME enrichment, do NOT use this skill (STRING's API is for
  occasional access): download the per-organism bulk files instead, as the
  annotation_mtbc `phase2h_string.py` pipeline does.
argument-hint: "<subcommand> <locus_tag|gene>...   # e.g. partners Rv1462 --required-score 400"
allowed-tools: Bash, Read, Write
user-invocable: true
---

# /string-db -- ad-hoc STRING v12 functional-association queries

This skill wraps the STRING REST API for **occasional, ad-hoc** queries: the
use STRING's own documentation endorses for the API. It is the live,
any-species complement to the offline whole-proteome STRING layer that the
`annotation_mtbc` gene atlas builds from bulk files.

What it adds over orthology (eggNOG), structure (Foldseek/ESMFold) and curated
function (UniProt): the **functional network context**. Those layers say "this
gene *is* in COG X / has this fold"; STRING says "this gene *works with* that
characterised operon". For an unknown gene, the genomic-context channels
(neighborhood, fusion, co-occurrence) are a prokaryote-strong, orthogonal
signal -- the citable seed of a function hypothesis.

## When to use it (and when NOT)

Use it for:
- a single gene's functional partners (`partners`), especially a hypothetical;
- testing if a candidate operon/complex is real (`ppi`);
- the enrichment of a small gene set (`enrichment`);
- a network picture for a figure (`image`).

Do NOT use it for whole-proteome annotation: the API is rate-limited and meant
for limited use. For that, download `83332.protein.links.detailed.v12.0.txt.gz`
once and parse locally (see `annotation_mtbc/analyses/phase2h_string.py`, which
also recomputes a text-mining-free combined score). This skill and that
pipeline are deliberately separate.

## Invocation

No install needed (stdlib only):

```
cd <skill>/src && python -m string_db <subcommand> ...
```

Or install the `string-db` console command into a venv:

```
pip install -e <skill>/src && string-db <subcommand> ...
```

Default species is 83332 (M. tuberculosis H37Rv); pass `--species <taxon>` for
another organism. Output is a compact TSV table, or raw JSON with `--json`.

## Subcommands

| Command | Purpose |
|---------|---------|
| `map <ids...>` | resolve gene names / locus tags to STRING ids + annotation |
| `partners <id> [--required-score N] [--limit N] [--physical] [--context-only]` | interaction partners, with per-channel scores and a `context` column (max of neighborhood/fusion/co-occurrence) |
| `network <ids...> [--required-score N] [--add-nodes N] [--physical]` | interactions among the input set |
| `enrichment <ids...> [--category KEGG Process Pfam ...] [--fdr F]` | functional enrichment with FDR |
| `annotation <ids...>` | per-protein functional annotation |
| `ppi <ids...>` | PPI-enrichment test: is the set more connected than random? |
| `image <ids...> -o out.png [--highres] [--svg] [--required-score N]` | rendered network picture |

Scores are 0-1000. Useful thresholds: 400 = medium, 700 = high, 900 = highest
confidence.

## Reading the partners output

```
partner   combined   context   channels(>=400)
furA      979        829       neighborhood:829 textmining:878
sodA      973        63        database:500 textmining:947
```

The **`context`** column is the key for unknown genes. A high `context` (carried
by neighborhood / fusion / co-occurrence) is a strong, literature-independent
association; a high `combined` with `context` near zero is text-mining-driven and
merely echoes the literature. For a hypothetical, the best `--context-only`
partner that is itself a characterised gene is the citable function hypothesis.
Example: `partners Rv1462 --required-score 400` returns the *suf* iron-sulfur
operon (Rv1461/1463/1465/1466, csd) with strong neighborhood + co-occurrence,
even though Rv1462 is annotated "hypothetical protein".

## Caveats

- **Association is a hypothesis, not proof.** Corroborate a context anchor with
  the operon structure and the primary literature before assigning a function.
  STRING is exploratory here, like ESM/Foldseek.
- **Text-mining for known genes is circular** (it re-states UniProt); for true
  hypotheticals it is empty. Lean on the genomic-context channels.
- **Coverage of hypotheticals is sparser** than of known genes -- that is a
  quality filter, not a defect.
- **The neighborhood channel is dense in prokaryotes** (conserved gene order),
  so it fires often; always show the channels, never sell a neighborhood-only
  edge as evidence.
- STRING data is CC-BY 4.0 (cite Szklarczyk et al. 2023, NAR,
  doi:10.1093/nar/gkac1000). Responses are disk-cached (static per release) and
  calls are rate-limited by default.

## Environment overrides

`STRING_SPECIES` (default 83332), `STRING_CALLER` (caller_identity sent to
STRING), `STRING_CACHE` (cache dir, default `~/.cache/string-db`),
`STRING_MIN_INTERVAL` (seconds between live calls), `STRING_API_ROOT`.
