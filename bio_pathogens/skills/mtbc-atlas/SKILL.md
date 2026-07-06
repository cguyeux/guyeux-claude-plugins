---
name: mtbc-atlas
description: >-
  Academic research toolkit for the Guyeux group (FEMTO-ST) MTBC pipeline: a
  resilient, stdlib-only client for the MTBC Gene Annotation Atlas REST API
  (https://mtbc.gclab.fr/api/v1), the re-annotation of the Mycobacterium
  tuberculosis complex proteome that takes over from the unmaintained
  Mycobrowser. Queries 3906 genes (anchored on the ancestral MTBC0 genome,
  joined to H37Rv NC_000962.3), each carrying a curated function, a verdict
  (requalified / family_assigned / dark) and up to ~35 evidence layers:
  orthology (eggNOG COG/EC/KO/GO/CAZy), UniProt, intra-MTBC conservation,
  AlphaFold/ESMFold structure + Foldseek, STRING interaction network, M-CSA
  catalytic sites, Tn-seq essentiality, CRISPRi vulnerability, PaxDb
  proteomics, DeepTMHMM localisation, operon/regulon, iModulon expression,
  PTM, Regions of Difference, mutant phenotypes, and the P8 integrative leads
  for dark genes.

  Use when: you need the current annotation / evidence for an MTBC gene by
  locus tag (e.g. Rv3222c), to search genes by name/product/function, to list
  every gene that carries a given evidence layer (e.g. all with CRISPRi
  vulnerability, or the still-dark genes with an integrative lead), to pull one
  specific layer (structure, conservation, string, vulnerability, ...), or to
  get dataset-wide counts (verdicts, per-layer coverage). This is the machine
  interface to the atlas served at mtbc.gclab.fr; prefer it over scraping the
  HTML pages or re-reading the local content/genes/*.json when the site is live.
argument-hint: "<stats|layers|get|search> ...   # e.g. get Rv3222c --layer conservation"
allowed-tools: Bash, Read
user-invocable: true
---

# /mtbc-atlas -- query the MTBC Gene Annotation Atlas REST API

Thin, dependency-free wrapper over the public API served at
`https://mtbc.gclab.fr/api/v1` (self-contained FastAPI sub-app; interactive
OpenAPI docs at `/api/v1/docs`, machine schema at `/api/v1/openapi.json`).
Read-only, CORS-open. The container scales to zero, so the *first* request after
idle may be slow — the client retries transient failures automatically.

## Invocation

Run the bundled client with `python3`:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/atlas_query.py" <subcommand> [args]
```

(`${CLAUDE_PLUGIN_ROOT}` resolves to this skill's directory. Override the
endpoint with `--base URL` or the env var `MTBC_ATLAS_API`, e.g. to hit a local
dev server `http://127.0.0.1:9624/api/v1`.)

## Subcommands

- `stats` — dataset counts: total genes, hypothetical, verdict breakdown, and
  the non-empty coverage of every evidence layer.
- `layers` — list the ~35 evidence layers with a one-line description of each.
- `get <Rv>` — full record for one gene (scalar fields + every non-empty layer,
  listed by name). Add `--layer <name>` to print just that layer's JSON
  (e.g. `get Rv2516c --layer vulnerability`).
- `search <query>` — search/filter genes, paginated summaries. Filters:
  `--verdict {requalified,family_assigned,dark}`, `--hypothetical`,
  `--has-layer <layer>` (only genes carrying that layer), `--limit N`,
  `--offset N`. An empty query with `--has-layer` lists all genes with that
  layer (e.g. every dark gene with an `integrative_lead`).

Add `--raw` to any command to print the raw JSON instead of the compact view.

## Examples

```bash
# current annotation + which layers a gene has
python3 "${CLAUDE_PLUGIN_ROOT}/atlas_query.py" get Rv3222c

# one specific layer
python3 "${CLAUDE_PLUGIN_ROOT}/atlas_query.py" get Rv3909 --layer struct_af

# the highly vulnerable dark drug-target candidates
python3 "${CLAUDE_PLUGIN_ROOT}/atlas_query.py" search "" --verdict dark --has-layer vulnerability --limit 500 --raw

# free-text search restricted to still-unknown genes
python3 "${CLAUDE_PLUGIN_ROOT}/atlas_query.py" search kinase --verdict dark

# dataset overview
python3 "${CLAUDE_PLUGIN_ROOT}/atlas_query.py" stats
```

## Notes

- The API is the SAME data that backs the web pages at `mtbc.gclab.fr/gene/<Rv>`
  and the `content/genes/<Rv>.json` fiches of the `annotation_mtbc` project.
- Layer names are exactly the JSON keys of the atlas record; `layers` prints the
  authoritative list. Unknown layers / genes return a clean 4xx the client
  reports verbatim.
- For WHOLE-PROTEOME batch work inside the pipeline, read the local
  `site/content/genes/*.json` directly; use this skill for occasional live
  lookups and for reproducing what a reader of the article would get.
- This API is the citable data-availability endpoint for the atlas manuscript
  (`Data availability: ... REST API at https://mtbc.gclab.fr/api/v1`).
