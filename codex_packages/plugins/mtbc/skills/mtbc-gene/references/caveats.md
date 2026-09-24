# mtbc-gene -- shared caveats, quirks and degradation behaviour

The **evidence-status rule on ESM Atlas SAE features is not here**: it lives in
`SKILL.md`, section *"Evidence status: what is citable and what is not"*, deliberately
kept in the always-loaded body because it gates what may be written in a manuscript.
This file holds the operational quirks that only matter once a command misbehaves.

## H37Rv catalogue and translation

- Genes are resolved against the H37Rv CDS fasta at
  `~/docs/codes/mtbc/en_cours/investigate_phylo/resources/NC_000962.3_CDS.fasta`, whose headers
  are parsed as `>lcl|... [gene=X] [locus_tag=Y] [protein=Z]`.
- Translation uses the MTBC table 11: `GTG` / `TTG` initiator codons are forced to `M`,
  all downstream codons follow the standard genetic code.
- Pseudogenes and frameshift-broken CDS are translated up to the first internal stop.
  `length_aa` reflects what was actually sent to ESM, and `truncated: true` is set when
  the translated protein is shorter than the conceptual CDS length / 3.

## Curated source first, offline

- With `annotation_mtbc` present, a full `function` answer needs no network and no ESM.
  Set `MTBC_ANNOTATION_DIR` if the project is not at `~/docs/codes/mtbc/en_cours/annotation_mtbc`.
- Per-gene channels read: `data/gene_xref_all.tsv`, `résultats/phase2e_uniprot`,
  `phase2b_pfam`, `phase2h_string`, `phase2f_conservation`, `phase2_esm`, and
  `data/structural_candidates_ext.tsv`.

## ESM Atlas quirks (inherited from `esm-atlas-cli`)

- For some genes the H37Rv reference protein is **its own cluster representative**:
  `lookup(hash)["cluster_rep_protein_hash"]` is then `None` and the `cluster` block of
  the output stays empty.
- The alpha API exposes no per-position structural confidence on demand (no pLDDT in the
  standard lookup); no mode gates its output on pLDDT.
- Global top-k SAE features are largely insensitive to point mutations (validated on
  `katG` S315T: identical top-20 between WT and mutant). That is why the SAE lens works
  on **per-residue** activations rather than on the global top-k.
- All interpretive feature labels come from the upstream Atlas; the skill paraphrases
  them and does not invent biological semantics.
- Responses go through the `esm-atlas-cli` disk cache (TTL 30 days for `feature_meta`,
  7 days for sequence lookups), so a repeat call on the same gene is instant.
- If a protein hash is not yet folded by the Atlas, the first call may trigger an
  on-demand fold and take a few seconds.

## Degradation when a source is unavailable

- `EsmAtlasUnavailable` -> `function` returns a partial payload (gene, locus tag,
  product, length, protein hash; no `top_features` / `cluster`), the summary falls back
  to the H37Rv `[protein=…]` annotation with an explicit
  *"(ESM Atlas unavailable, fall-back to H37Rv-only)"* note, and exit code `3`.
- Gene absent from the H37Rv fasta -> exit code `1`.
- `pathway`: a gene that fails annotation lands in `missing`, the rest of the set still
  gets a payload; Atlas downtime empties the per-gene `top_features` / `cluster` blocks
  but pathway-level metadata is still returned.
- `atlas`: **since 2026-09-06 the atlas is served as STATIC files, not by a container**
  (the serverless container degraded within ~90 s under even light traffic and could not
  be stabilised by any sizing). Every API URL still answers, but two things changed and
  `atlas_query.py` absorbs both:
  - `GET /genes/{rv}/{layer}` is **not** frozen (3974 x 54 files). The client falls back to
    the full record `GET /genes/{rv}` and reads the layer from its `layers` key, so
    `get --layer` keeps working; the returned `description` is then empty.
  - the search route no longer **filters** (a query string no longer selects the file
    served): it returns the COMPLETE collection and says so via a `static_note` field. The
    client re-applies `q`, `verdict` and `hypothetical` locally. `--has-layer` cannot be
    honoured this way (summaries carry no layers) and exits with a clear message rather
    than silently returning unfiltered rows.
  Responses are served with `Content-Type: text/html` rather than `application/json`; the
  body is still valid JSON. Unknown genes return a 404 reported verbatim.

## Scope limits

- Mutations are in **protein coordinates** only. SPDI to protein conversion is the job of
  `spdi-annotation`; run it first if you only hold a nucleotide SPDI.
- Insertions and deletions are not handled, only single-residue substitutions.
- No mode infers positive selection. `pathway --from-selection` **reads** an existing
  result; the tests themselves are `mk-ascertainment` / `convergent-evolution`.
- Mycobrowser is not queried directly. When a Mycobrowser client is added, the `function`
  mode is the natural place to merge its annotation.
