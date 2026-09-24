---
name: mtbc-gene
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST), peer-reviewed MTBC phylogenomics: the
  H37Rv gene and protein layer. From a gene name (katG) or Rv locus tag (Rv1908c): curated
  function offline-first (UniProt, EC, Pfam, STRING, conservation); ESM-1v log-likelihood-
  ratio impact of a point mutation (katG S315T); pathway or gene-set narration, including
  from a McDonald-Kreitman table; atlas-wide search, statistics and evidence layers through
  the mtbc.gclab.fr REST API. Use when asked what a gene or Rv locus does, whether a
  substitution is likely damaging, what an uncharacterised gene may be involved in, how to
  narrate a gene set or pathway for a manuscript, or when a gene name or Rv tag appears in a
  question about MTBC biology.
argument-hint: "<function|mutation|pathway|atlas> ...   # e.g. function katG --paragraph | mutation katG S315T"
allowed-tools: Bash, Read, Write, Edit
user-invocable: true
---

# /mtbc-gene -- the H37Rv gene and protein layer

> [!TIP]
> **Deux bases pour qualifier un gène au-delà de l'annotation.** **BacFITBase**
> (`tartaglialab.com/bacfitbase`, `10.1093/nar/gkz931`) recense la contribution des gènes bactériens
> **pendant l'infection d'un hôte**, ce qui est une question distincte de l'essentialité in vitro
> mesurée par TnSeq (dont les pièges de comptage de sites TA sont documentés dans
> `~/.claude/knowledge/tuberculosis.md`). **TuberQ** (`tuberq.proteinq.com.ar`,
> `10.1093/database/bau035`) donne la druggabilité des protéines de *M. tuberculosis*, utile pour
> juger si un gène « dark » a un intérêt thérapeutique déclaré. Les deux sont anciennes : citer la
> mesure, pas la base, et vérifier la publication d'origine.


Everything this skill does starts from **one H37Rv gene, named (`katG`) or given by
its locus tag (`Rv1908c`)**, and answers at a chosen granularity:

| Mode | Question | Granularity |
|---|---|---|
| `function` | what does this gene do? | one gene |
| `mutation` | what does this substitution do to it? | one residue |
| `pathway` | what does this gene set do, and how connected is it? | a gene set |
| `atlas` | what does the published atlas hold, dataset-wide? | the proteome |

The four modes share one Python source tree (`src/`), one H37Rv CDS catalogue and one
curated annotation project (`annotation_mtbc`), which is why they are one skill: a
pathway narration calls the per-gene annotator, and a mutation score resolves its gene
through the same resolver.

## Evidence status: what is citable and what is not

**This section gates what may be written in a manuscript. Read it before using
`mutation` or `pathway --esm`.**

> **ESM Atlas SAE features are an interpretability lens, never variant-effect evidence.**
> Counting features that "flip" between wild type and mutant at a position has **no
> validated mapping to functional impact**. Reporting such a count as evidence was a
> documented over-claim in this group's own work (`rehumanisation_L6L9L10`, 2026-05-30).
> The SAE output of the `mutation` mode (`impact_of`) and the `--esm` second opinion of
> the `pathway` mode are **hypothesis generators only**.
>
> **The citable variant-effect score is the ESM-1v zero-shot masked-marginal
> log-likelihood ratio** (Meier et al. 2021, NeurIPS 34:29287), the
> deep-mutational-scanning-validated approach, computed by the bundled
> `mtbc_mutation_impact.llr` module and by `./run_llr.sh`. LLR << 0 = disfavoured
> (candidate damaging / loss-of-function), ~0 = tolerated drift, > 0 = favoured over WT.
>
> **SAE feature labels are not domain assignments.** Before asserting a protein domain,
> fold or chemistry in a manuscript, confirm it with **Pfam (`hmmscan --cut_ga`)**. The
> same 2026-05-30 episode included an SAE read of **Rv0386 as an "AAA+ ATPase"** when the
> protein is in fact a **LuxR/GerE HTH regulator with no ATPase domain**. SAE narratives
> have been both confirmed and contradicted by Pfam; only Pfam settles the question.

The curated channels (UniProt function and EC, Pfam domains, STRING partners, pN/pS
conservation) carry their own provenance and are citable as such. The ESM Atlas layer is
enrichment or fallback, and every mode runs without it.

## Mode `function` -- curated functional annotation of a gene

Turns a gene name or locus tag into a structured functional annotation, answering from
the group's curated `annotation_mtbc` project **first** (per-gene UniProt function + EC,
Pfam domains, STRING partners, conservation/selection as **pN/pS**, Foldseek structural
leads for dark genes), then enriching or falling back to ESM Atlas SAE features via
`esm-atlas-cli`.

Use it when an Atlas lineage page mentions a gene (RD content, a defining SNP, a
resistance allele, a pathway gene) and needs an automatic functional blurb, or when an
exploratory analysis hits an unfamiliar `Rv` locus tag and you want a 30-second context
grounded in the group's own annotation work rather than in a generic database.

```bash
python3 -m mtbc_gene_function katG                 # PYTHONPATH=<this skill>/src
python3 -m mtbc_gene_function Rv1908c --paragraph
python3 -m mtbc_gene_function rpoB --json          # machine-readable only
python3 -m mtbc_gene_function katG --no-esm --paragraph   # fully offline
python3 -m mtbc_gene_function.smoke_test           # offline self-check
```

```python
from mtbc_gene_function import annotate_gene
ann = annotate_gene("katG")
print(ann["function_summary"])
```

What it does: resolve the gene against the H37Rv CDS fasta, translate the DNA CDS with
MTBC table 11, read the curated channels, optionally query ESM Atlas
(`lookup_sequence`, then `cluster` if a representative is known), and return:

```json
{
  "gene": "katG", "locus_tag": "Rv1908c", "product": "catalase-peroxidase",
  "protein_hash": "d08e94...", "length_aa": 740,
  "top_features": [{"index": 14273, "activation": 1.50, "label": "Folded alpha/beta domain cores"}],
  "cluster": {"size": 8431, "pct_characterized": 87},
  "function_summary": "Catalase-peroxidase (740 aa). …",
  "source": "H37Rv NC_000962.3 + curated annotation_mtbc (+ ESM Atlas, alpha)"
}
```

`--paragraph` adds a short prose block in the academic-neutral voice, ready to drop into
an Atlas fiche or a manuscript.

## Mode `mutation` -- local impact of a point mutation

Scores a single-residue substitution in an H37Rv protein. **Report the LLR, not the SAE
deltas** (see *Evidence status* above).

Use it when contextualising a published resistance allele (`katG` S315T for INH, `rpoB`
S450L for RIF) alongside the literature-derived catalogue and never in place of it, when
characterising a non-synonymous SPDI flagged as defining for a sub-lineage, or when
sanity-checking a candidate adaptive substitution from a McDonald-Kreitman analysis
(`mk-ascertainment`) before it is discussed as adaptive.

### Citable score: ESM-1v LLR (Meier 2021)

`run_llr.sh` wires this skill's `src/` plus `esm-atlas-cli` on the PYTHONPATH and the
dedicated torch + fair-esm venv, so **no project recreates a `/tmp` venv** for
variant-effect scoring:

```bash
cd <this skill> && ./run_llr.sh katG S315T
./run_llr.sh eccE1 G346A
./run_llr.sh --smoke              # torch-free self-check (no 2.6 GB download)
```

```python
from mtbc_mutation_impact.llr import load_model, llr_of, score_many
model, alphabet = load_model()
llr_of("eccE1", "G346A", model, alphabet)          # {'llr': +0.18, ...} -> tolerated
score_many([("katG", "S315T"), ("rpoB", "S450L")])  # loads the model once
```

Needs `torch` + `fair-esm` (heavy, optional). One-time venv (already created; recreate if
missing): `python3 -m venv --system-site-packages /home/christophe/venvs/esm1v && /home/christophe/venvs/esm1v/bin/pip install --no-deps fair-esm` (inherits the system torch;
ESM-1v weights download on the first real score). See the module docstring for the
`--system-site-packages` recipe when a fresh-venv torch is broken.

### Candidate complementary axis: structural ΔΔG (RaSP installed and confirmed 2026-09-08, not wired into this skill's CLI yet)

ESM-1v LLR scores evolutionary/sequence likelihood; it says nothing about structural
stability. Dissanayake et al. 2026 (BMC Microbiology, `10.1186/s12866-026-04876-1`,
pyrazinamide resistance in PncA via a GCN on AlphaFold2-predicted structures) found that
of all node features tested, a structure-based ΔΔG predictor, **DeepDDG** (Cao et al. 2019,
`10.1021/acs.jcim.8b00697`), had by far the highest gradient-based feature importance for
predicting resistance, ahead of RaSP, MAPP and SNAP2 and ahead of any raw structural/chemical
feature (their Fig. 7). DeepDDG itself has no installable official release (web server only,
`protein.org.cn/ddg`); its stand-in, **RaSP** (Blaabjerg et al. 2023 eLife), was installed on
`mp` via a lighter path than its own README documents (recipe in
`~/.agents/knowledge/bioinformatics.md`, [2026-09-08] entries) and tested end to end on PncA
itself (PDB 3PL1, H37Rv numbering, no offset): saturation-mutagenesis ΔΔG on the 364 unique
pncA missense variants of `Resistance_antibio`'s catalogue separates WHO R-associated from
S-associated calls at AUC=0.829 (Mann-Whitney p=7e-5), consistent with the univariate RaSP
AUC (73%) reported by Carter et al. on a different dataset. **Wired end to end into
`Resistance_antibio`'s operational PZA predictor** (`analyses/pnca_rasp_feature.py`,
`phase10_predict.py --rasp`): on the full 20413-strain PZA set, adding this ddG as one extra
feature alongside the genomic ones raises the residual XGBoost from AUC 0.784 to **0.855
(Δ+0.071)** and sensitivity at spec≥0.98 from 0.240 to **0.365 (Δ+0.125)** — the univariate
signal translates into a real, substantial gain, concentrated where the ML model was weakest,
even though the score only covers 14% of strains. Not done yet: wiring RaSP as a citable second
opinion in this skill's own `mutation` mode CLI (it currently requires a per-protein
saturation-mutagenesis run rather than a single on-demand call like ESM-1v LLR, so the
integration shape differs) — the PZA result lives in `Resistance_antibio`, not here. sbmlcore
(`github.com/fowler-lab/sbmlcore`), the per-residue chemical/structural feature package used by
the same article, remains unevaluated.

### Exploratory lens: per-residue SAE deltas

Answers *how does the per-residue SAE feature profile move at exactly this position?*
It resolves the gene, validates that the reference residue matches, looks up WT and
mutant proteins in ESM Atlas, restricts both `per_residue_activations` tensors to row
`N-1`, and reports features **gained**, **lost**, **amplified** and **attenuated**, each
with the `feature_meta` label. Hypothesis generator only.

```bash
python3 -m mtbc_mutation_impact katG S315T          # PYTHONPATH=<this skill>/src
python3 -m mtbc_mutation_impact rpoB S450L --topk 8
python3 -m mtbc_mutation_impact Rv1908c S315T       # locus tag accepted
```

```python
from mtbc_mutation_impact import impact_of
report = impact_of("katG", "S315T")
for f in report["gained"]:
    print(f["index"], f["wt_activation"], f["mt_activation"], f["label"])
```

Mutation syntax: `<REF><POS><ALT>` in protein coordinates, 1-indexed (`S315T`, `D516V`,
`H526Y`); the position is checked against the H37Rv protein.

## Mode `pathway` -- curated, network-aware narration of a gene set

Narrates a **gene set** as a pathway. The set can be a predefined pathway from the
bundled catalogue, a gene's **network neighbourhood** (`neighbors:katG`), or an
**explicit gene list**. Each gene is annotated curated-first through the `function` mode;
the narration aggregates dominant enzyme classes and Pfam domains, flags dark genes, and
adds PPI context from `mtbc-gene-network` (set cohesion, internal-edge density, hub gene).

```bash
cd <this skill> && ./run_pathway.sh ESX-2 --paragraph
./run_pathway.sh neighbors:furA --min-score 700 --paragraph
./run_pathway.sh katG,ahpC,sodA,sodC,furA --paragraph
./run_pathway.sh my-pathway --catalogue ./pathways.yaml
```

Offline self-check (needs `mtbc-gene-network` on the path as well, exactly as
`run_pathway.sh` wires it, otherwise the PPI assertions fail):

```bash
BP=/home/christophe/docs/environnement/plugins/mtbc/skills
PYTHONPATH="$BP/mtbc-gene/src:$BP/mtbc-gene-network/src" python3 -m mtbc_pathway_explain.smoke_test
```

It does **not** infer positive selection (that is `mk-ascertainment` /
`convergent-evolution`); it explains *what* the set does and *how connected* it is.
`--esm` adds the SAE second opinion, subject to *Evidence status* above.

### From a lineage's selection signal to the affected pathways

`--from-selection TABLE` **reads** an existing selection result for a lineage and narrates
the pathways the signal concerns. It never recomputes the test. Column resolution is
drift-tolerant, auto-detected highest-confidence first:

- **McDonald-Kreitman output** (`mk-ascertainment`): an `alpha` (= 1 - NI) or `DoS`
  column, or the raw `Dn`/`Ds`/`Pn`/`Ps` counts (alpha and DoS then recomputed with the
  same formulas, Fisher p via scipy if absent). A **significance gate** keeps a gene only
  if its adaptive direction is positive (`alpha > --alpha-min`, default 0) **and** its p
  clears `--max-p` (default 0.05), BH-FDR-corrected across genes unless `--no-fdr`;
- a **per-gene statistic** table (gene / `Locus_tag` column plus `dN/dS`, `dnds_proxy` or
  `omega`, optionally a p-value): genes with `stat > --min-stat` (default 1.0) and
  `p < --max-p` are kept;
- a **variant-level** table (gene plus `effect` / `impact`): non-synonymous variants are
  counted per gene, keeping genes with `>= --min-variants`;
- none present: every gene in the table is taken, flagged in `selection.mode`.

It then resolves every gene to its Rv (local-first), intersects with each catalogue
pathway, ranks hits by how much of the pathway is hit, narrates the top `--top` pathways
in full, reports whether the selected set is itself a cohesive PPI module
(`selected_module`), and lists off-catalogue selected genes.

```bash
./run_pathway.sh --from-selection mk_per_gene.tsv --lineage L4.13 --paragraph
./run_pathway.sh --from-selection mk_per_gene.tsv --alpha-min 0.1 --no-fdr
./run_pathway.sh --from-selection <table> --lineage L4.13 --min-variants 3 --top 3 --paragraph
./run_pathway.sh --from-selection <table> --gene-col Locus_tag --stat-col dnds_proxy --p-col fdr
```

**The significance gate (`test_concluded`).** For an MK table the output carries `gate`
(`alpha_min`, `max_p`, `fdr`, `n_tested`, `n_significant`, `n_without_p`) and a boolean
`test_concluded`, `True` only when at least one gene shows **positive** selection at the
corrected threshold. Otherwise it is `False` and the paragraph reads *"… did not yield a
significant per-gene signal … No selection section should be written."* A caller
(`atlas-add-lineage`) **must** check `test_concluded` before drafting a `selection`
section: this is the machine-checkable form of *no premature publication*. An MK table
dominated by negative alpha (NI > 1, purifying selection / excess polymorphism) correctly
concludes *nothing to claim*. For non-MK tables `test_concluded` is `null` (a gene list is
not a test). At a low `--min-variants` the variant-level mode reflects **mutational load**
(PE/PPE, PDIM) rather than strict positive selection; prefer a gated MK table for a
defensible claim.

### Pathway catalogue

Stored as YAML in `src/mtbc_pathway_explain/data/pathways.yaml`; each entry gives a
canonical ID, a one-line description and the composing H37Rv locus tags / gene names. The
keys of that file are the authoritative list:

- **secretion**, `ESX-1` … `ESX-5`;
- **envelope / lipids**, `PDIM`, `MYCO_ACID`, `PE_PPE_CORE`,
  `CELL_WALL_PEPTIDOGLYCAN`, `ARABINOGALACTAN`;
- **metabolism**, `GLYOXYLATE`, `CHOLESTEROL_CATABOLISM`, `MCE_TRANSPORTERS`,
  `IRON_ACQUISITION`, `NITROGEN_METABOLISM`, `SULFATE_ASSIMILATION`, `F420_REDOX`;
- **regulation / stress**, `DosR`, `SIGMA_FACTORS`, `TWO_COMPONENT`,
  `OXIDATIVE_STRESS`, `DNA_REPAIR`;
- **resistance**, `INH_RESISTANCE`, `RIF_RESISTANCE`, `FQ_RESISTANCE`,
  `INJECTABLE_RESISTANCE`, `LINEZOLID_BEDAQUILINE`;
- **comparative genomics**, `BCG_DELETIONS`.

Add a pathway with `--catalogue path/to/file.yaml`, same schema:

```yaml
my-pathway:
  description: "Custom pathway I want to explain."
  genes: [katG, Rv1908c]
```

## Mode `atlas` -- the published REST API, dataset-wide

Thin, dependency-free (stdlib-only) client over the public API at
`https://mtbc.gclab.fr/api/v1` (self-contained FastAPI sub-app; interactive OpenAPI docs
at `/api/v1/docs`, machine schema at `/api/v1/openapi.json`). Read-only, CORS-open.

The Gene Annotation Atlas is the group's re-annotation of the *M. tuberculosis* complex
proteome, taking over from the unmaintained **Mycobrowser**. It covers **3906 genes**,
anchored on the ancestral **MTBC0** genome and joined to **H37Rv NC_000962.3**. Every
gene carries a curated function and a **verdict** (`requalified`, a function established
for a previously hypothetical gene; `family_assigned`, placed in a family or fold without
a precise function; `dark`, still uncharacterised), plus up to **~35 evidence layers**:
orthology (eggNOG COG / EC / KO / GO / CAZy), uniprot, conservation, structure (AlphaFold
and ESMFold models plus Foldseek neighbours: `struct_af`, `struct_esm`), string, M-CSA
catalytic sites, essentiality (Tn-seq), vulnerability (CRISPRi), PaxDb abundance,
DeepTMHMM localisation, operon / regulon, iModulon modules, PTM, Regions of Difference,
mutant phenotypes, and `integrative_lead` (the P8 leads proposed for dark genes).

```bash
AQ="${CLAUDE_PLUGIN_ROOT}/skills/mtbc-gene/atlas_query.py"   # or <this skill>/atlas_query.py
python3 "$AQ" get Rv3222c
python3 "$AQ" get Rv3909 --layer struct_af
python3 "$AQ" search "" --verdict dark --has-layer vulnerability --limit 500 --raw
python3 "$AQ" search kinase --verdict dark
python3 "$AQ" stats
python3 "$AQ" layers
```

Subcommands: `stats` (dataset counts: total genes, hypothetical, verdict breakdown,
non-empty coverage of every layer), `layers` (the authoritative layer list with one-line
descriptions; layer names are exactly the JSON keys of the record), `get <Rv>` (full
record, `--layer <name>` for one layer), `search <query>` (paginated summaries, filters
`--verdict`, `--hypothetical`, `--has-layer`, `--limit`, `--offset`; an empty query with
`--has-layer` lists every gene carrying that layer). `--raw` prints raw JSON. Override
the endpoint with `--base URL` or `MTBC_ATLAS_API`.

The API serves the **same data** as the web pages at `mtbc.gclab.fr/gene/<Rv>` and the
`content/genes/<Rv>.json` fiches of `annotation_mtbc`, and is the citable data-availability
endpoint of the atlas manuscript (*Data availability: … REST API at
https://mtbc.gclab.fr/api/v1*). For **whole-proteome batch work inside the pipeline**,
read the local `site/content/genes/*.json` directly and use the `function` mode; the
`atlas` mode is for occasional live lookups and for reproducing what a reader of the
article would get.

## Workflow alignment

```
H37Rv CDS catalogue  +  annotation_mtbc (curated)          published REST API
(investigate_phylo/resources/NC_000962.3_CDS.fasta)        mtbc.gclab.fr/api/v1
       │                                                            │
       └──────────────►  mtbc-gene  ◄──────────────────────────────┘
                            │
   function ────────────────┤ per-gene curated annotation (+ optional SAE)
   mutation ────────────────┤ ESM-1v LLR (citable) | per-residue SAE deltas (exploratory)
   pathway  ────────────────┤ gene set → enzyme classes, Pfam, dark genes, PPI cohesion
   atlas    ────────────────┘ dataset-wide search, stats, evidence layers
                            │
        ├─► esm-atlas-cli        SAE lookup, cluster, structure
        ├─► mtbc-gene-network    STRING interactome, PPI cohesion (pathway mode)
        ├─► string-db            STRING API fallback
        │
        ▼
   Atlas backend /gene/<name> page   ·   atlas-add-lineage (lineage page sections)
   manuscript drafting               ·   mk-ascertainment ⇄ pathway --from-selection
   ⟂ literature corroboration via tbmonitor-papers
```

## What this skill does not do

- It does not run the McDonald-Kreitman test, nor infer selection: `mk-ascertainment`,
  `convergent-evolution`.
- It does not draft an Atlas fiche end to end: `atlas-add-lineage` (which calls this
  skill, once per gene it mentions, and for the `selection` section).
- It does not generate figures: `sci-figure`.
- It does not convert nucleotide SPDI to protein coordinates: `spdi-annotation`.
- It does not handle insertions or deletions, only single-residue substitutions.
- It does not settle domain assignments; Pfam does (see *Evidence status*).

## Further reading

`references/caveats.md`, translation quirks (table 11 initiators, pseudogene
truncation), curated-channel paths and `MTBC_ANNOTATION_DIR`, ESM Atlas quirks and
caching, exit codes and degradation behaviour when a source is unavailable.
