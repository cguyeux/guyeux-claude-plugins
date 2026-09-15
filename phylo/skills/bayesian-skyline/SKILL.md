---
name: bayesian-skyline
description: >-
  Academic research toolkit for peer-reviewed phylodynamic research. BEAST Bayesian Skyline
  family (Bayesian Skyline Plot, Skyride, Skygrid, Birth-Death Skyline) to reconstruct
  effective population size Ne(t) or effective reproduction number Re(t) through time from
  dated genomes of a published study collection. Use when reconstructing the historical
  Ne(t) of an MTBC lineage, testing expansion against a human demographic transition
  (Neolithic, Bronze Age, Columbian contact), estimating Re(t) over a historical period, or
  producing a skyline figure for a scientific manuscript.
---

# Bayesian Skyline : Ne(t) and Re(t) Reconstruction from Sequence Data

> [!TIP]
> **Coût typique : des jours de CPU.** Répliquer plutôt qu'allonger : tableau de jobs Slurm sur `mh`
> (une chaîne par réplicat, `--array`), puis combiner les traces. `mp` pour une chaîne unique qui
> dépasse 8 jours. Environnement phylo sur `mh` : `/Work/Users/cguyeux/envs/phylo` (contenu et
> pièges dans `remote-compute`) ; Tracer, en revanche, reste à installer. Voir le skill `remote-compute` (sonde d'état, modèles `sbatch`, pièges). Prérequis : VPN monté (`sudo vpn up`).


## Overview

**Skyline plots** are a family of Bayesian phylodynamic methods for
reconstructing the **effective population size through time** `Ne(t)`
(coalescent-based) or the **effective reproduction number** `Re(t)`
(birth-death-based) of a pathogen from a dated phylogeny. They are
implemented as tree priors inside **BEAST v1** and **BEAST v2** and
share the same overall workflow as the broader **`beast2-phylogeography`**
skill, but with a distinct goal: **demographic dynamics**, not
geographic spread.

The skyline family has four main members, each with different
assumptions, smoothness, and features:

| Method | Key reference | Type | Smoothness |
|---|---|---|---|
| **Bayesian Skyline Plot (BSP)** | Drummond, Rambaut, Shapiro, Pybus (2005) *MBE* 22(5): 1185 | Coalescent | Piecewise constant on tree-interval bins (user picks number of bins) |
| **Bayesian Skyride** | Minin, Bloomquist, Suchard (2008) *MBE* 25(7): 1459 | Coalescent | Smooth via Gaussian Markov Random Field (GMRF) prior |
| **Bayesian Skygrid** | Gill, Lemey, Faria, Rambaut, Shapiro, Suchard (2013) *MBE* 30(3): 713 | Coalescent | User-defined time grid in calendar time; supports multilocus data and covariates |
| **Birth-Death Skyline (BDSKY)** | Stadler, Kühnert, Bonhoeffer, Drummond (2013) *PNAS* 110(1): 228 | Birth-death | Estimates **Re(t)**, become/sampling rate, not only Ne(t) |

- **Tutorial (authoritative)**: *Taming the BEAST : Skyline plots*
  by Nicola F. Müller and Louis du Plessis:
  `https://taming-the-beast.org/tutorials/Skyline-plots/`
- **BEAST2 platform**: `https://www.beast2.org/`
- **License**: LGPL (inherits from BEAST2)

## When to use this skill

- reconstructing the **historical effective population size** of an MTBC
  lineage;
- testing whether a lineage expansion **coincides with a human demographic
  transition** (Neolithic, Bronze Age, Columbian contact…);
- estimating the **effective reproduction number Re(t)** through time during
  an epidemic;
- producing a **skyline plot as a figure**, for a manuscript, a poster, or a
  seminar slide on pathogen dynamics.

## Why it matters for MTBC × anthropology

Skyline methods give you **quantitative pathogen demographic
trajectories**, the time-series counterpart to the phylogenetic tree.
For your TB and anthropology work, this enables three direct uses:

1. **MTBC Ne(t) vs human demographic transitions.** The canonical
   anthropology hypothesis is that human-adapted TB lineages expanded
   alongside human population expansions (Neolithic, Bronze Age,
   post-Columbian). A skyline plot on an MTBC lineage lets you
   directly test this: if Ne(lineage) and Ne(host population from
   `aadr` / `amtdb`) rise in register, the co-expansion is quantitative.
2. **Historical epidemic dynamics: Re(t) of pre-modern outbreaks.**
   BDSKY estimates the effective reproduction number through time,
   useful for discussing the Justinian plague waves, Black Death, or
   the 7th pandemic cholera (chained with `enterobase` and
   `spaam-ancient-metagenome-dir`).
3. **Detecting historical bottlenecks.** A drop in Ne(t) flagged by a
   skyline method can signal a selective sweep, a host bottleneck
   (e.g. Columbian population collapse in the Americas → impact on
   Andean *M. pinnipedii* diversity), or a demographic collapse of
   the host.

Skyline methods are the **second rigorous Bayesian tool** in the
constellation (after `beast2-phylogeography`), and they are
methodologically very close: same BEAST2 engine, same XML setup
workflow, but a different tree prior.

## Method comparison : which skyline to pick

| Question you're asking | Best method | Rationale |
|---|---|---|
| "Did this lineage expand or contract historically?" (qualitative) | **BSP** | Fast, well-tested, simple |
| "What does Ne(t) look like with minimal prior smoothing?" | **Skyride** | GMRF prior lets the data drive the shape |
| "What does Ne(t) look like over specific calendar time bins?" (e.g. centuries) | **Skygrid** | User-defined grid; also supports external covariates |
| "What is the effective reproduction number through time?" | **BDSKY** | Birth-death estimates Re(t) directly |
| "Multi-locus dataset (whole-genome genes concatenated)" | **Skygrid** | Only coalescent skyline designed for multilocus |
| "Epidemic with explicit sampling process through time" | **BDSKY** | Models sampling as part of the birth-death |

**Recommendation for MTBC lineage expansion questions**: start with
**Skygrid** (it gives you a calendar-time axis directly readable for
anthropology narratives). Use **BSP** for a fast first pass. Use
**BDSKY** when you specifically need Re(t) rather than Ne(t).

## Workflow outline (BEAUti, when a display is available)

Same general workflow as `beast2-phylogeography` : set up in **BEAUti**,
run with `beast`, diagnose with **Tracer**, extract the skyline:

```
alignment.fasta + metadata (tip dates)
        │
        ▼
BEAUti → load alignment → set tip dates
         → Site model: GTR + Γ + I
         → Clock: relaxed lognormal
         → Tree prior: CoalescentBayesianSkyline  (or Skyride / Skygrid / BDSKY)
         → MCMC: 10^8 – 10^9 steps
         → Save XML
        │
        ▼
beast <run>.xml          ── MCMC (hours–days)
        │
        ▼
Tracer                   ── open .log, check ESS ≥ 200 for all params,
                            inspect "coalescentBayesianSkyline.logPopSizes"
                            or equivalent
        │
        ▼
Tracer → Analysis → Bayesian Skyline Reconstruction
                   → exports a Ne(t) plot with 95% HPD envelope
```

### For Skygrid specifically

In the BEAUti *Priors* tab, pick **Skygrid** and configure:

- **Number of grid points** (typical: 50–200 depending on the number
  of sequences and the time span)
- **Cut-off time**, the most ancient time point for the grid (typically
  set to slightly beyond the expected root of the tree)
- **Prior on GMRF precision**, controls smoothness; default is usually fine

### For BDSKY specifically

Set the **birth rate**, **become noninfectious rate**, and
**sampling proportion** priors per epoch. Epochs are specified in
calendar time. This is more epidemiologically meaningful than the
coalescent but needs good priors on each parameter.

## Headless recipe (no BEAUti, no display)

BEAUti is a JavaFX application: on a server, or when an agent runs the
analysis, there is no display and the workflow above cannot be executed.
The skyline priors are ordinary BEAST2 XML blocks, so emit them from a
script instead. Everything in the headless section of
`beast2-phylogeography` applies unchanged (Java version, `setsid`,
resume, the ascertainment `siteWeights` correction, the two-chain rule);
only the tree-prior block differs. Read that section first, then
substitute one of the blocks below.

**Take an XML from a *Taming the BEAST* tutorial as the template and swap
the tree prior.** Writing a full BEAST2 XML from scratch is not worth the
time, and a hand-written one usually fails on an operator or a state node
that is easy to forget.

**Bayesian Skyline Plot (BSP).** `groupSizes` sets the number of
population-size intervals; keep it well below the number of coalescent
events or the intervals are unidentifiable, and `popSizes` must have the
same dimension.

```xml
<distribution id="BSP" spec="BayesianSkyline" treeIntervals="@TreeIntervals.t:aln">
  <parameter id="bPopSizes" spec="parameter.RealParameter"
             dimension="5" value="380"/>
  <parameter id="bGroupSizes" spec="parameter.IntegerParameter"
             dimension="5" value="1"/>
</distribution>
```

Operators BSP needs and that a coalescent-constant template does not have:

```xml
<operator spec="BitFlipOperator" parameter="@bGroupSizes" weight="1.0"/>
<operator spec="DeltaExchangeOperator" intparameter="@bGroupSizes"
          integer="true" weight="6.0"/>
<operator spec="ScaleOperator" parameter="@bPopSizes"
          scaleFactor="0.75" weight="15.0"/>
```

**Skygrid** (`BayesianSkyGrid` in the BEAST2 `bdsky`/`feast` distribution;
in BEAST 1 it is `GMRFSkyGridLikelihood`). The two numbers that matter are
the number of grid points and the cut-off, and the cut-off must be older
than the root or the oldest interval absorbs everything:

```xml
<distribution id="Skygrid" spec="BayesianSkyGrid"
              treeIntervals="@TreeIntervals.t:aln"
              cutOff="2000.0" numGridPoints="50">
  <parameter id="logPopSizes" spec="parameter.RealParameter"
             dimension="51" value="1.0"/>
  <parameter id="precision" spec="parameter.RealParameter" value="1.0"/>
</distribution>
```

**BDSKY** (`BirthDeathSkylineModel`, package `BDSKY`). Epoch boundaries go
in `birthRateChangeTimes`, expressed in time before present, with
`reverseTimeArrays` set so they are read in the same direction as the tip
dates:

```xml
<distribution id="BDSKY" spec="beast.base.evolution.speciation.BirthDeathSkylineModel"
              tree="@Tree.t:aln" origin="@origin">
  <reproductiveNumber spec="parameter.RealParameter" dimension="4" value="2.0"/>
  <becomeUninfectiousRate spec="parameter.RealParameter" value="1.0"/>
  <samplingProportion spec="parameter.RealParameter" value="0.01"/>
  <birthRateChangeTimes spec="parameter.RealParameter" value="0 50 150 400"/>
  <reverseTimeArrays spec="parameter.BooleanParameter"
                     value="true true true false false"/>
</distribution>
```

`samplingProportion` is the parameter that most often ruins a BDSKY run on
archive data: it is the fraction of infections that ended up sequenced,
which for MTBC is very small and very poorly known. Fix it from an
external estimate rather than letting it float, or Re(t) and the sampling
effort trade off against each other and neither is identified.

**Extracting the skyline without Tracer.** Tracer's Bayesian Skyline
Reconstruction dialog is a GUI. Headless, the trajectory is recoverable
from the `.log`: BSP logs `bPopSizes` and `bGroupSizes` per sample,
Skygrid logs `logPopSizes` on a fixed grid, which is the easier case since
the grid is the same at every sample.

```python
import numpy as np, pandas as pd

log = pd.read_csv("run.log", sep="\t", comment="#")
log = log.iloc[len(log) // 10:]                       # drop 10 % burn-in
cols = [c for c in log.columns if c.startswith("logPopSizes")]
ne = np.exp(log[cols].to_numpy())                      # samples x grid points

grid = np.linspace(0, 2000.0, ne.shape[1])             # cutOff, numGridPoints
traj = pd.DataFrame({
    "time_before_present": grid,
    "median": np.median(ne, axis=0),
    "hpd_low": np.percentile(ne, 2.5, axis=0),
    "hpd_high": np.percentile(ne, 97.5, axis=0),
})
```

Percentiles are a central credible interval, not a true HPD; for a skewed
posterior the two differ, so say which one the figure shows. For BSP the
same idea applies but the group sizes vary between samples, so each sample
must be mapped onto a common time grid before taking quantiles.

Check ESS on the skyline parameters, not only on the likelihood: a chain
can look converged overall while `logPopSizes` in the oldest intervals has
an ESS of 20, which is exactly where the interesting claim usually sits.
The autocorrelation estimator in `beast_harvest.py` (see
`beast2-phylogeography`) computes ESS per column from the `.log` with no
GUI.

Two independent chains, different seeds, separate directories, and an
overlay of the two reconstructed trajectories: if the envelopes do not
overlap, the result is not ready regardless of what ESS says.

## Interpreting the output

### Coalescent skylines (BSP / Skyride / Skygrid)

Tracer's **Bayesian Skyline Reconstruction** dialog produces:

- A PDF/PNG plot of **Ne(t)** with a 95% HPD envelope
- A CSV/TSV of the reconstructed trajectory (time, median Ne, 95% lower, 95% upper)

The **x-axis is time** (calendar time if tip dates are set). The
**y-axis is Ne** (effective population size × generation time).

### BDSKY

Tracer does not provide a built-in visualisation for BDSKY; you must
post-process the log file to extract **Re(t)** per epoch. The
community has R scripts for this (see the *Taming the BEAST* tutorial).

### Correcting for generation time

`Ne` from a coalescent is technically `Ne × generation_time`. For
MTBC, the generation time is not a strict biological concept but is
sometimes taken as the time between transmission events (~1 year) or
the time between mutations (~0.1 year at standard clock rates).
Always state the generation-time assumption in Methods.

## Workflows

### Workflow 1 : MTBC lineage Ne(t) vs human Neolithic transition

Goal: test whether human-adapted *M. tuberculosis* L4 expanded in
register with the Neolithic demographic transition.

1. Extract a representative L4 panel from TBannotator (e.g. 150 modern
   strains globally stratified).
2. Add any relevant ancient tips from `spaam-ancient-metagenome-dir`
   (Kay2015, Sabin2020, Jager2022, all < 500 BP though, so they only
   anchor the recent end).
3. Align, set up a BEAUti XML with **Skygrid** prior, run MCMC.
4. Extract Ne(t) from Tracer → get a time-series over ~10 000 years
   if the clock allows.
5. Overlay with the `neolithic-14c` SPD from EUROEVOL + NERD for the
   same time window.
6. Visual inspection: do the two trajectories correlate?
7. Formal test: correlation or Granger causality (if the time-series
   are long enough).

> [!WARNING]
> MTBC Ne(t) reconstructions beyond ~2 000 years are speculative
> because the molecular clock calibration is loose and the ancient
> tips are all < 1 000 BP. Report the uncertainty honestly.

### Workflow 2 : Re(t) of a historical plague wave with BDSKY

Goal: use BDSKY on the ancient Justinian plague *Y. pestis* genomes
, verified to be **35 individuals from 5 projects** in the SPAAM
catalogue (session-fetched), to reconstruct Re over the 541–750 CE
window.

1. Extract the Justinian plague *Y. pestis* genomes from
   `spaam-ancient-metagenome-dir` (filter on `Yersinia pestis` and
   age 1 200–1 600 BP). Expected yield: **35 samples** split as
   **Keller2019 (30)** + Wagner2014 (2, Aschheim-Bajuwarenring) +
   Feldman2016 (1, Altenerding) + Guellil2022 (1, Edix Hill) +
   deBarrosDamgaard2018 (1, Russia).
2. Add modern *Y. pestis* references to pin the root (the
   evolutionary backbone, from EnteroBase or from the published
   panels of Spyrou et al.). **Do NOT use only Zhou et al. 2020's
   56 ancients**, the SPAAM catalogue has since grown substantially.
3. Set up BDSKY in BEAUti with epochs corresponding to the historical
   waves: **536–541 CE** (LALIA onset + first outbreak at Pelusium),
   **541–560 CE** (first wave Mediterranean), **580–620 CE**
   (recurrent waves per Procopius/Evagrius), **660 CE** (end of LALIA
   according to Büntgen 2016). Use non-uniform epochs matching the
   historical record rather than round centuries.
4. Run MCMC. **Note**: 35 tips is at the low end of robustness for
   BDSKY, expect wide HPDs, report them honestly.
5. Extract Re(t) and plot against the **Büntgen 2016 LALIA
   temperature reconstruction** (see `paleoclimate` skill) and the
   Procopius/Evagrius written chronology.
6. Narrative: where did Re > 1 (growing epidemic) vs Re < 1 (waning)?
   **The testable hypothesis** : Re(t) peaks during the coldest
   LALIA years (540–550 CE) and declines after 660 CE, consistent
   with a climate-triggered vs climate-terminated epidemic dynamic.
   Sensitivity analysis by dropping the Kyrgyzstan / UK outlier
   samples.

> [!NOTE]
> For a **rhetorically stronger slide**, also fetch modern *Y. pestis*
> from Spyrou et al. 2022 *Nature* (Issyk-Kul Kara-Djigach cemeteries,
> 1338–1339 CE), they are ~800 years **after** the Justinian window
> but anchor the evolutionary backbone with a landmark dated reference.

### Workflow 3 : Detecting a historical bottleneck in *M. pinnipedii*

Goal: test whether the Columbian population collapse affected
Andean *M. pinnipedii* (Bos 2014 + Vagene 2022).

1. Combine the 6 ancient *M. pinnipedii* samples with modern
   *M. pinnipedii* references (few available, this is a small
   dataset).
2. Run Skygrid on the combined alignment.
3. Look for a dip in Ne(t) around 1500–1600 CE.
4. Sensitivity analysis: drop each ancient tip in turn and check if
   the result is robust.

> [!WARNING]
> With only 6 ancient tips and very few modern *M. pinnipedii*
> references, this analysis is strongly underpowered. Treat any
> result as exploratory, not confirmatory.

### Workflow 4 : Multi-locus Skygrid for whole-genome MTBC

Skygrid is the only coalescent skyline designed for multilocus data.
For an MTBC analysis using non-recombining SNPs partitioned by gene
region:

1. Partition the alignment by gene or chromosome segment.
2. In BEAUti, configure unlinked trees for each partition (if testing
   tree congruence) or a shared tree.
3. Use the **Skygrid** tree prior.
4. Run MCMC, extract Ne(t).

## Caveats

- **All the BEAST2 caveats apply.** Convergence (ESS ≥ 200), chain
  length, prior sensitivity, see the `beast2-phylogeography` skill.
- **Skyline methods are prior-sensitive.** The smoothness prior on
  Skyride and the grid choice on Skygrid affect the result.
  Run sensitivity analyses.
- **Sampling bias affects skylines.** A coalescent skyline assumes
  random sampling through time. If your sampling is concentrated in
  recent years, Ne(t) estimates for the distant past become poorly
  supported.
- **Ne is not census population size.** Effective population size is
  a statistical construct, not a count. It tracks genetic diversity,
  not clinical cases. The relationship Ne → census is
  pathogen-specific and uncertain.
- **MTBC clock rate is debated.** See `beast2-phylogeography` caveats.
  The same issue applies here and affects the time axis of the
  skyline directly.
- **BDSKY requires priors on sampling rate.** If your dataset is not
  a time-stratified epidemic sample, BDSKY is the wrong choice.
- **No built-in BDSKY plot in Tracer.** Budget time to post-process
  BDSKY output with R scripts from the Taming the BEAST tutorial.
- **Large datasets are slow.** For > 500 tips, a skyline analysis in
  BEAST2 can take days to weeks. Subsample.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`beast2-phylogeography`** | Shared BEAST2 engine and workflow : MASCOT / BASTA for *where*, skyline for *when* and *how much* |
| **`nextstrain`** | Fast exploration and tree construction before committing to a BEAST2 skyline |
| **`pastml`** | Orthogonal layer for ancestral state reconstruction; skylines answer a different question |
| **TBannotator MCP** | Source of modern MTBC sequences |
| **`spaam-ancient-metagenome-dir`** | Ancient tips for tip-calibrated skylines |
| **`enterobase`** | *Y. pestis* historical backbone for BDSKY of plague waves |
| **`p3k14c`** / **`neolithic-14c`** / **`card`** | Archaeological SPDs to compare against pathogen Ne(t) |
| **`aadr`** / **`amtdb`** | Human Ne(t) proxies from ancient human genomes, compare with pathogen Ne(t) |
| **`bovine-genomics`** | Cattle demographic history, compare with *M. bovis* Ne(t) |
| **Tracer** | Extract the skyline plot from the MCMC log |
| **R script suite** (Taming the BEAST) | Post-processing for BDSKY |

## Citations

```bibtex
@article{drummond2005skyline,
  title   = {Bayesian coalescent inference of past population dynamics
             from molecular sequences},
  author  = {Drummond, Alexei J. and Rambaut, Andrew and Shapiro, Beth
             and Pybus, Oliver G.},
  journal = {Molecular Biology and Evolution},
  volume  = {22},
  number  = {5},
  pages   = {1185--1192},
  year    = {2005},
  doi     = {10.1093/molbev/msi103}
}

@article{minin2008skyride,
  title   = {Smooth skyride through a rough skyline: Bayesian coalescent-
             based inference of population dynamics},
  author  = {Minin, Vladimir N. and Bloomquist, Erik W. and
             Suchard, Marc A.},
  journal = {Molecular Biology and Evolution},
  volume  = {25},
  number  = {7},
  pages   = {1459--1471},
  year    = {2008},
  doi     = {10.1093/molbev/msn090}
}

@article{gill2013skygrid,
  title   = {Improving Bayesian Population Dynamics Inference: A
             Coalescent-Based Model for Multiple Loci},
  author  = {Gill, Mandev S. and Lemey, Philippe and Faria, Nuno R. and
             Rambaut, Andrew and Shapiro, Beth and Suchard, Marc A.},
  journal = {Molecular Biology and Evolution},
  volume  = {30},
  number  = {3},
  pages   = {713--724},
  year    = {2013},
  doi     = {10.1093/molbev/mss265}
}

@article{stadler2013bdsky,
  title   = {Birth-death skyline plot reveals temporal changes of
             epidemic spread in HIV and hepatitis C virus (HCV)},
  author  = {Stadler, Tanja and K{\"u}hnert, Denise and Bonhoeffer, Sebastian
             and Drummond, Alexei J.},
  journal = {Proceedings of the National Academy of Sciences},
  volume  = {110},
  number  = {1},
  pages   = {228--233},
  year    = {2013},
  doi     = {10.1073/pnas.1207965110}
}
```

**Always cite** the specific skyline method you used (BSP, Skyride,
Skygrid, or BDSKY) plus the BEAST2 platform paper (Bouckaert 2019)
and the Taming the BEAST tutorial you followed.
