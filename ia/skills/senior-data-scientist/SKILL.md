---
name: senior-data-scientist
description: >-
  Academic research toolkit for designing a statistically defensible analysis on
  genomic and population data before running it, and for routing to the right
  specialised skill. Use when the user asks how an analysis should be set up
  rather than asking to run one: which test or estimator fits the question,
  whether a result survives phylogenetic non-independence, how to correct for
  multiple testing across thousands of sites or genes, how to split data for
  cross-validation when isolates are clonal, whether an allele-frequency result
  is an ascertainment artefact, or what a reviewer will attack in the statistics
  of a peer-reviewed manuscript. Do not use to execute a fit or a plot: this
  skill dispatches to statsmodels, scikit-learn, statistical-analysis,
  causal-inference, mk-ascertainment or sci-figure for that.
allowed-tools: Read, Grep, Glob, Bash
---

# Analysis design review

This skill is a design gate, not an execution engine. It runs before the code, or
on a result that already exists but has not yet been defended. Its job is to catch
the four failure modes that most often invalidate a statistical claim on the kind
of data the Guyeux group works with (bacterial genomes with strong clonal
structure, ancient and modern human population panels, non-randomly sampled
archives), and then to hand off to the skill that actually does the work.

## 1. Route the question

| The user is asking | Go to |
|---|---|
| Descriptive statistics, a significance test, outlier detection | `statistical-analysis` |
| Regression, GLM, mixed models, time series, model diagnostics | `statsmodels` |
| Classification, clustering, cross-validation, pipelines | `scikit-learn`, `sklearn-advanced` |
| Gradient boosting, tuning a tabular predictor | `xgboost-iterative-optimizer` |
| Why a model predicts what it predicts | `sklearn-explainability`, `ml-model-explainer` |
| From association to causation (DAGs, ATE/CATE, refutation) | `causal-inference` |
| Selection on protein-coding genes, McDonald-Kreitman | `mk-ascertainment` |
| Diversity indices, ordination, distance matrices | `scikit-bio` |
| Simulation-based inference on demographic parameters | `abc-xgboost` |
| Which scientific question is worth attacking at all | `scientific-problem-selection` |
| Turning the result into a publication figure | `sci-figure` |

If the question maps cleanly onto one row and raises none of the hazards in
section 2, say so and hand off immediately. Do not add ceremony to a simple task.

## 2. The four hazards

### 2.1 Non-independence: the samples are not n independent draws

A clonal bacterial population is the archetypal violation. Two isolates from the
same transmission chain are close to the same observation counted twice. Treating
them as independent inflates every test statistic, and the inflation grows with
sample size, so a large dataset makes the problem worse rather than better. The
same applies to human population panels structured by shared ancestry, and to
languages or cultures related by descent (Galton's problem, which is exactly why
the `wals` and `d-place` skills exist).

Symptoms to look for: a p-value that is absurdly small for the effect size; a
genotype-phenotype association that disappears when one clade is dropped; an
association whose top hits are all in the same genomic neighbourhood or all from
the same country and year.

Remedies, in increasing order of rigour:

- Deduplicate to one isolate per transmission cluster (see `snp-distance` for the
  threshold) and re-run. If the signal dies, it was clonal, full stop.
- Add a random effect for lineage or cluster:
  `statsmodels.regression.mixed_linear_model.MixedLM`. This is the cheapest honest
  fix and it is what a reviewer will ask for.
- Count independent emergences rather than isolates: an allele that arose once and
  was inherited by 400 descendants is n = 1, not n = 400. Reconstruct the state on
  the tree (`pastml`, `ancestral-reconstruction`) and test the number of
  independent gains, which is the logic behind `convergent-evolution` and
  homoplasy-based association.
- Permute within clade rather than globally when building a null: a global
  permutation destroys the population structure and therefore produces a null that
  is far too easy to beat.

### 2.2 Multiple testing across sites, genes or traits

Bonferroni over 4 million genome positions is both too conservative and wrong in
its independence assumption, since linkage makes neighbouring sites redundant.

- Default to Benjamini-Hochberg FDR (`statsmodels.stats.multitest.multipletests`
  with `method="fdr_bh"`), and state the q-value threshold in the manuscript.
- When tests are positively dependent, `fdr_by` is the safe variant.
- Report the number of tests actually performed, including the ones abandoned
  after a first look. A threshold chosen after seeing the results is not a
  threshold.
- For a small number of pre-registered hypotheses, per-test alpha is fine and FDR
  is unnecessary ceremony. Say which regime you are in.

### 2.3 Ascertainment: who got sequenced, and why

Public genome archives are not random samples of the population. Isolates enter
them because there was an outbreak, because a treatment failed, because a country
had funding for a sequencing programme. Any statistic that depends on the
frequency spectrum, on branch lengths, or on the ratio of polymorphism to
divergence inherits that bias.

- Allele-frequency-based selection tests (Tajima's D, MK, dN/dS on a population
  sample) are the most exposed. `mk-ascertainment` exists specifically for this.
- Resistance-allele frequencies computed over a public archive estimate the
  frequency among sequenced isolates, not among circulating ones. Word the claim
  accordingly: this is a phrasing fix, not a statistical one, and it is what
  `claim-check` looks for.
- Dating with a molecular clock on a convenience sample can produce spurious
  temporal signal. Test it: a date-randomisation test is the standard control
  (`molecular-clock`, `iqtree-lsd2`).
- Before concluding that a lineage is geographically restricted, check whether
  anyone has sequenced anything elsewhere. Absence of evidence in a sampling map
  is usually absence of sampling.

### 2.4 Leakage through relatedness in predictive models

If a random `KFold` split puts two isolates from the same cluster on either side
of the train/test boundary, the model can memorise the clade instead of learning
the biology, and the reported accuracy is fiction. This is the single most common
reason a resistance-prediction accuracy fails to replicate.

- Split by group, not by row: `GroupKFold` or `StratifiedGroupKFold` with the
  clade, cluster or outbreak identifier as the group.
- The harder and more informative test is a leave-one-lineage-out split: train on
  lineages 1 to 3, test on lineage 4. Accuracy will drop. That drop is the honest
  estimate of transfer to a new population, and reporting it is a strength.
- Fit every preprocessing step inside the pipeline, never on the full matrix
  before splitting. `sklearn.pipeline.Pipeline` makes this automatic.
- With imbalanced classes, AUC flatters. Report precision at the operating point
  and the base rate. A classifier with AUC 0.95 on a 2 percent positive class can
  still be mostly wrong when it fires.

## 3. Reporting checklist

Before a number leaves for a manuscript:

- The effective sample size is stated, and it is the number of independent
  observations, not the number of rows.
- The correction for multiple testing is named, with the number of tests.
- The null model is described precisely enough to be reimplemented, including how
  permutations were constrained.
- Effect size and a confidence interval accompany every p-value.
- Sensitivity to the obvious analytic choices (deduplication threshold, outgroup,
  filtering cutoff) has been checked and the result is reported, not just the
  favourable one.
- The sampling frame is described, and the claim is scoped to it.

Numbers that reach the manuscript go through `claim-check` for cross-verification
against the source data, and figures through `fig-check`.

## 4. What this skill will tell you not to do

- Do not report a genotype-phenotype association from a clonal collection without
  a structure control. It will not survive review.
- Do not tune a threshold on the test set and then report test-set performance.
- Do not present an unadjusted p-value from a genome-wide scan.
- Do not read a correlation across lineages as a causal effect; if the causal
  claim is the point, go to `causal-inference` and state the DAG.
- Do not add a statistical apparatus that the question does not need. A clean
  descriptive result with an honest sampling caveat beats a mixed model fitted to
  make a weak signal cross a threshold.
