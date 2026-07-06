---
name: mtbc-mutation-impact
description: >-
  Academic research toolkit for the Guyeux group (FEMTO-ST) MTBC pipeline:
  estimate the local functional impact of a point mutation in a
  Mycobacterium tuberculosis H37Rv gene by comparing ESM Atlas per-residue
  sparse-autoencoder activations between the wild-type and the mutated
  protein, at the position of the mutation. Useful when an Atlas lineage
  page mentions an antimicrobial-resistance allele or a non-synonymous
  SPDI under positive selection, and the Guyeux group wants a
  protein-language-model second opinion alongside the literature-derived
  resistance catalogue. Returns the WT and mutant SAE feature vectors
  restricted to the mutated residue, the deltas (gained / lost / amplified
  / attenuated features), and a short interpretive paragraph. The SAE deltas
  are exploratory only; for a validated, citable variant-effect score the
  bundled `llr` module computes the ESM-1v masked-marginal log-likelihood
  ratio (Meier et al. 2021).

  Use when: contextualising a published-research resistance allele (e.g.
  katG S315T for INH), characterising a non-synonymous SPDI flagged as
  defining for a sub-lineage, or sanity-checking a candidate adaptive
  substitution found by McDonald-Kreitman.
argument-hint: "<gene_or_locus> <mutation>   # e.g. katG S315T"
allowed-tools: Bash, Read
user-invocable: true
---

# /mtbc-mutation-impact -- ESM-based local impact of a point mutation

This skill answers the question: *if I change residue X to residue Y at
position N in this H37Rv gene, how does the ESM Atlas per-residue feature
profile at that exact position move ?* It is a hypothesis generator, not a
diagnostic.

> **Reporting a variant effect in a manuscript? Use the LLR mode, not the SAE deltas.**
> The SAE feature-delta output below is an interpretability lens with **no
> validated mapping to functional impact**; counting "flipped" features is not
> variant-effect evidence and was a documented over-claim (rehumanisation_L6L9L10,
> 2026-05-30). For a calibrated, citable score use the bundled
> `mtbc_mutation_impact.llr` module, which computes the **ESM-1v zero-shot
> masked-marginal log-likelihood ratio** (Meier et al. 2021, NeurIPS 34:29287) —
> the deep-mutational-scanning-validated approach. Confirm any domain claim with
> Pfam (`hmmscan --cut_ga`) rather than with SAE feature labels.
>
> ```python
> from mtbc_mutation_impact.llr import load_model, llr_of, score_many
> model, alphabet = load_model()
> llr_of("eccE1", "G346A", model, alphabet)   # {'llr': +0.18, ...}  -> tolerated
> score_many([("katG", "S315T"), ("rpoB", "S450L")])  # loads model once
> ```
> ```bash
> python -m mtbc_mutation_impact.llr eccE1 G346A
> ```
> Needs `torch` + `fair-esm` (heavy, optional deps). LLR << 0 = disfavoured,
> ~0 = tolerated drift, > 0 = favoured over WT. See the module docstring for the
> `--system-site-packages` venv recipe if a fresh-venv torch is broken.

## What it does

1. **Resolve** the gene via the `mtbc-gene-function` skill : H37Rv CDS →
   protein sequence + locus_tag + product.
2. **Validate the mutation** : the reference residue at position N must
   match the `ref` letter of the mutation string.
3. **Look up** the WT protein in ESM Atlas → fetch `per_residue_activations`
   (a sparse COO tensor of shape `[L, n_features]`).
4. **Mutate locally** (replace residue at position N), hash, look up the
   mutant → fetch its `per_residue_activations`.
5. **Restrict** both tensors to **row = N-1** and compare the per-feature
   activations.
6. **Return** WT and MT feature vectors at the mutated position, plus the
   set of features that
   - **gained** activation (> 0 in MT, ≤ 0 in WT),
   - **lost** activation (≤ 0 in MT, > 0 in WT),
   - **amplified** (both > 0, |MT| >> |WT|),
   - **attenuated** (both > 0, |MT| << |WT|).

The skill also queries `feature_meta(idx)` for each non-trivial feature to
attach a human-readable interpretation. This is rate-limited and cached on
disk by `esm-atlas-cli`.

## How to use

> **For a validated variant-effect score, use the ESM-1v LLR (Meier 2021), not the
> SAE deltas.** The SAE feature deltas (`impact_of`, below) are an interpretability
> lens / hypothesis generator, never manuscript variant-effect evidence. The
> calibrated score is the masked-marginal log-likelihood ratio (`llr`): LLR << 0
> means the substitution is disfavoured (candidate damaging / loss-of-function).

### Validated LLR (recommended) — turnkey launcher

`run_llr.sh` wires the 3-skill PYTHONPATH (mtbc-mutation-impact + mtbc-gene-function
+ esm-atlas-cli) and the dedicated torch+fair-esm venv, so **no project recreates a
/tmp venv** for variant-effect scoring:

```bash
cd <this skill> && ./run_llr.sh katG S315T       # one variant
./run_llr.sh eccE1 G346A
./run_llr.sh --smoke                              # torch-free self-check (no 2.6 GB download)
```

One-time venv (already created; recreate if missing): `python3 -m venv
--system-site-packages /home/christophe/venvs/esm1v && /home/christophe/venvs/esm1v/bin/pip
install --no-deps fair-esm` (inherits the system torch; the ESM-1v weights download on
first real score). From Python: `from mtbc_mutation_impact.llr import llr_of, score_many`.

### From a shell

```bash
/mtbc-mutation-impact katG S315T
/mtbc-mutation-impact rpoB S450L --topk 8
/mtbc-mutation-impact Rv1908c S315T   # locus tag accepted
```

### From Python

```python
from mtbc_mutation_impact import impact_of

report = impact_of("katG", "S315T")
print(report["paragraph"])
for f in report["gained"]:
    print(f["index"], f["wt_activation"], f["mt_activation"], f["label"])
```

## Inputs

- **`gene_or_locus`** : `katG`, `Rv1908c`, `rpoB`, `inhA`, etc. Case-insensitive.
- **`mutation`** : one-letter code `<REF><POS><ALT>` in protein coordinates
  (1-indexed). E.g. `S315T`, `D516V`, `H526Y`. Position is checked against
  the H37Rv protein.

## Outputs

```json
{
  "gene": "katG", "locus_tag": "Rv1908c", "product": "catalase-peroxidase",
  "mutation": "S315T",
  "ref": "S", "pos": 315, "alt": "T",
  "wt_hash": "d08e94...",   "mt_hash": "57c745...",
  "wt_vector": [{"index": 1234, "activation": 0.42, "label": "..."}],
  "mt_vector": [{"index": 1234, "activation": 0.21, "label": "..."}],
  "gained":     [{"index": 9999, "wt_activation": 0.0, "mt_activation": 0.7, "label": "..."}],
  "lost":       [...],
  "amplified":  [...],
  "attenuated": [...],
  "paragraph":  "katG S315T (catalase-peroxidase). Local ESM SAE …"
}
```

## Honesty caveats

- ESM Atlas SAE features are a **representational lens**, not a variant-effect
  predictor. A feature flip at the mutated position is a *hypothesis*, not a
  proof that the substitution alters function, and the count of flipped
  features has **no validated mapping to impact** — do not report it as
  quantitative evidence in a manuscript. For a calibrated score use the LLR
  mode (see the callout at the top of this file).
- The Atlas alpha API has no per-position structural confidence on demand
  (no pLDDT in the standard lookup). This skill does not gate output on
  pLDDT.
- The top-k global SAE features are largely insensitive to point mutations
  (validated on katG S315T: identical top-20 between WT and mutant). That
  is why this skill goes through the **per-residue** activations rather
  than the global top-k.
- All interpretive feature labels come from the upstream Atlas. The skill
  paraphrases them; it does not invent biological semantics.

## Workflow alignment

```
manuscript / Atlas fiche mentions a resistance allele or a defining SPDI
       │
       └─►  this skill   (per-residue WT vs MT)
              │
              └─►  contextual evidence + paragraph
              │       → drop into the lineage's drug_resistance / selection block
              │
              ⟂ literature corroboration via  tbmonitor-papers
              ⟂ structural follow-up via      esm-atlas-cli  (batch + include_structure)
```

## Limits

- Mutations must be in **protein coordinates**. SPDI → protein conversion
  is the job of `spdi-annotation` (planned). If you only have a nucleotide
  SPDI, run that first.
- Insertions / deletions are not handled. Only single-residue substitutions.
- If the protein hash is not yet folded by the Atlas, the first call may
  trigger an on-demand fold and take a few seconds; subsequent calls hit
  the disk cache.
