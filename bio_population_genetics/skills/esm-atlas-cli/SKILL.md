---
name: esm-atlas-cli
description: >-
  Academic research toolkit for the Guyeux group (FEMTO-ST) protein-evolution
  studies: a resilient Python client for the EvolutionaryScale × BioHub
  Protein Atlas API (https://biohub.ai/esm/protein/atlas/), which exposes
  ESMC sparse-autoencoder (SAE) features and ESMFold2 structures across
  6.8 billion proteins. Provides lookup by content hash, similarity search
  by amino-acid sequence, SAE-feature interpretation, cluster metadata
  (Pfam annotation rate), and 3-D structure / thumbnail retrieval, with a
  disk cache and graceful fallback when the alpha API is degraded.
  Reusable across any peer-reviewed published research project that maps
  a protein sequence to a functional annotation: phylogenomic
  characterisation, codivergence studies, antimicrobial-resistance allele
  interpretation in the Guyeux group MTBC pipeline, or comparative protein
  analyses in population genetics.

  Use when: a project step needs to translate a protein sequence into a
  biological function summary, retrieve a predicted structure, find
  ESM-space homologs, or compare two sequences (wild-type vs variant)
  via SAE feature differences.
argument-hint: "<subcommand> [args]   # lookup | similarity | features | feature | cluster | structure | thumbnail | hash"
allowed-tools: Bash, Read, Write, Edit
user-invocable: true
---

# /esm-atlas-cli -- ESM Atlas client (lookups, structures, SAE features)

A thin, defensive client around the **alpha** ESM Atlas API. Wraps the seven
endpoints documented at `https://biohub.ai/esm/protein/atlas/api-docs/` behind
a stable Python interface, caches every response on disk, retries on transient
failures, and degrades gracefully when the API is down so a project pipeline
never breaks just because the alpha API is misbehaving.

## Endpoints covered

| Atlas endpoint | Python method | What it returns |
|---|---|---|
| `GET /proteins/{hash}` | `lookup(hash)` | Sequence, metadata, top-k SAE features |
| `POST /proteins/batch` | `batch_lookup(hashes)` | ZIP (or async job) for ≤ 500 hashes |
| `GET /similarity-search` | `similarity_search(seq)` | Top-k proteins ranked by ESM-space similarity |
| `GET /features` | `features()` | List of all SAE features (index → label) |
| `GET /features/{idx}` | `feature_meta(idx)` | Full SAE feature description + activator proteins |
| `GET /clusters/{hash}` | `cluster(hash)` | Cluster membership, % Pfam-annotated |
| `GET /proteins/{hash}/thumbnail/{type}` | `thumbnail(hash, type)` | PNG bytes |

Plus utilities :

- `hash_sequence(seq)` — local MD5 of an amino-acid sequence (the Atlas
  identifier scheme).
- `mutate_and_compare(seq, mutations)` — apply point mutations and call
  `lookup` on both, returning the SAE feature delta. Useful for variant
  impact estimation.

## How to use

### From a shell

```bash
/esm-atlas-cli hash MTEEKVSLDEALDFLDQGADIPDLG          # → MD5 hex
/esm-atlas-cli lookup <hash>                          # → JSON
/esm-atlas-cli similarity "MTEE...XYZ" --topk 10
/esm-atlas-cli feature 1234                           # → SAE feature meta
/esm-atlas-cli cluster <hash>
/esm-atlas-cli structure <hash> --out katG.pdb
```

### From Python (the canonical interface for downstream skills)

```python
from esm_atlas_cli import EsmAtlasClient

client = EsmAtlasClient()                              # disk cache under ~/.cache/esm-atlas-cli/
data = client.lookup_sequence("MTEE...XYZ")            # hash + lookup in one call
print(data["topk_features"][:5])

# Wild-type vs variant
delta = client.mutate_and_compare("MTEE...XYZ", ["S315T"])
print(delta["gained_features"], delta["lost_features"])
```

## Resilience

- **Disk cache** under `~/.cache/esm-atlas-cli/` keyed by endpoint + params,
  TTL 30 days for stable resources (feature meta, cluster info), 7 days for
  sequence-derived lookups. Set `ESM_ATLAS_CACHE_TTL_DAYS=0` to bypass.
- **Retries** : exponential backoff on 502/503/504 (3 attempts).
- **Fallback** : on connection failure or 4xx unexpected, raises
  `EsmAtlasUnavailable`. Caller-side skills (`mtbc-gene-function`,
  `mtbc-mutation-impact`) catch this and degrade to Mycobrowser-only
  annotation, with an explicit "ESM Atlas unavailable" note in the output.
- **Async jobs** : `batch_lookup` polls the job endpoint up to a configurable
  deadline (default 5 min), then surfaces a `EsmAtlasPending` exception with
  the job_id so the caller can resume later.

## Inputs the skill prompts for

- Subcommand and its required positional argument.
- For `similarity` / `lookup_sequence` : either a hash or a sequence file
  (FASTA accepted).

## What this skill does not do

- It does not embed proteins itself — only fetches what the Atlas already has.
- It does not visualise structures (use `pymol`, `nglview`, or the `itol`
  skill for trees; the thumbnail PNG is for fiche embedding only).
- It does not paraphrase SAE feature descriptions into Atlas-fiche prose —
  that's the role of `mtbc-gene-function` and `mtbc-pathway-explain`.

## Limits & honesty

- The Atlas is **alpha** : endpoints, schemas and behaviour may change
  without notice. The client logs the API version it saw at install.
- **No authentication** today; rate is not formally documented. Treat each
  invocation as best-effort.
- SAE features are an **interpretation tool**, not a diagnostic. A divergence
  in feature activation between two sequences is a hypothesis, not a proof
  that function is altered.
- **Do not use SAE features as a variant-effect predictor or as a domain
  annotation in a manuscript.** They have no validated mapping to functional
  impact (documented over-claim, rehumanisation_L6L9L10, 2026-05-30). For a
  calibrated variant effect use the **ESM-1v masked-marginal LLR** (Meier
  et al. 2021), exposed by `mtbc-mutation-impact` (`from
  mtbc_mutation_impact.llr import llr_of`); to assign protein domains use
  **Pfam/`hmmscan --cut_ga`**. Treat SAE labels as exploratory colour only.

### Observed quirks (alpha API, 2026-05)

The doc reference page advertises `topk_features` as the response field; the
live API returns them under `sae_features` instead. The client accepts both.

`GET /proteins/{hash}` returns **only** sequence + SAE features +
`cluster_rep_protein_hash`. The PDB structure, pLDDT and pTM are returned by
the **batch endpoint** with `include_structure: true`, not by the single-
protein lookup. Use `client.batch_lookup([hash], include_structure=True)` to
get a ZIP with structure.

`mutate_and_compare()` based on top-k features is **insensitive to most
point mutations**. A change like `katG S315T` (the canonical INH resistance
SNP) leaves the top-20 SAE features identical between WT and mutant. The
fine-grained signal of a point mutation lives in `per_residue_activations`
at the mutated position, not in the top-k. For mutation-impact reasoning,
prefer comparing `per_residue_activations[i-1]` vectors and watch for sign
flips on a handful of features local to the mutated site.

`GET /clusters/{hash}` returns 404 if the queried hash is not a cluster
representative. Use `lookup(hash)["cluster_rep_protein_hash"]` first to find
the representative, then query that. If the field is `None`, the protein
is either uncharacterised or itself the representative (the docs do not
disambiguate yet).

## Quick install / test

The client is **stdlib-only** (urllib): there is nothing to `pip install`, and it
runs on the system Python as-is. Just put `src/` on `PYTHONPATH` (or `pip install -e .`
into a venv if you prefer an entry-point script).

```bash
# run smoke test against H37Rv katG (live API)
SRC=$(dirname "$(readlink -f "$0")")/src
PYTHONPATH="$SRC" python3 -m esm_atlas_cli.smoke_test

# offline reproducibility check: validates local logic + graceful degradation,
# no network needed (exit 0 when the client raises a clean EsmAtlasUnavailable)
PYTHONPATH="$SRC" ESM_ATLAS_OFFLINE=1 python3 -m esm_atlas_cli.smoke_test
```

The smoke test fetches `katG` (Rv1908c) from `~/docs/codes/mtbc/investigate_phylo/resources/NC_000962.3_CDS.fasta`, hashes it, and exercises `lookup`, `feature_meta`, and `cluster`. Output prints the top 5 SAE features with their functional descriptions, the cluster size, and the Pfam annotation rate.

**Resilience contract (for downstream skills).** Every GET is disk-cached under
`~/.cache/esm-atlas-cli` (TTL via `ESM_ATLAS_CACHE_TTL_DAYS`). Unrecoverable
network failures raise `EsmAtlasUnavailable`, which callers (`mtbc-gene-function`,
`mtbc-mutation-impact`, `mtbc-pathway-explain`, `resistance-explain`,
`active-site-check`) must catch and degrade gracefully (e.g. Mycobrowser-only
annotation with an explicit "ESM Atlas unavailable" note). Set `ESM_ATLAS_OFFLINE=1`
to force cache-only mode for reproducible runs.

## Workflow alignment

This skill is the **shared infrastructure layer** for any project that touches
proteins. It is consumed by :

- `mtbc-gene-function` — annotate a single gene with ESM features + structure.
- `mtbc-mutation-impact` — interpret a resistance or LoF mutation.
- `mtbc-pathway-explain` — narrate a positive-selection signal at the pathway
  level.

Outside MTBC, it can also serve population-genetics skills (host-side
adaptations, ESM-space homology of immune genes).
