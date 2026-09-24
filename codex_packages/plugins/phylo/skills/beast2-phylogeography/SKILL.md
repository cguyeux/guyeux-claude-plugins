---

name: beast2-phylogeography
description: >-
  BEAST2 phylogeography packages (MASCOT, BASTA, DTA) for Bayesian molecular
  dating, tip-dating of ancient samples, and structured-coalescent inference,
  with full posteriors on topology, divergence times, migration rates and
  ancestral states.

  Use when: dating ancient MTBC tips with credible intervals, demographic
  model comparison, or when a Maximum-Likelihood / Nextstrain pipeline is not
  rigorous enough.
---

# BEAST2 Phylogeography : MASCOT, BASTA, and the Structured Coalescent

> [!TIP]
> **Calcul distant quasi obligatoire.** Un modèle phylogéographique discret ou continu multiplie le
> coût par chaîne : viser un tableau de jobs Slurm sur `mh` (`mpi`/`smp`, 8 jours) avec une chaîne par
> réplicat, ou `mp` pour une chaîne unique très longue (aucune limite de temps). Environnement
> phylo sur `mh` : `/Work/Users/cguyeux/envs/phylo` (voir `remote-compute` pour son contenu). Voir le skill `remote-compute` (sonde d'état, modèles `sbatch`, pièges). Prérequis : VPN monté (`sudo vpn up`).


## Overview

**BEAST2** (*Bayesian Evolutionary Analysis by Sampling Trees, version 2*)
is the reference open-source Bayesian framework for phylogenetic and
phylodynamic inference. Where **Nextstrain/Augur** and **PastML** give
you fast Maximum-Likelihood point estimates at scale, BEAST2 gives you
**full posterior distributions** on tree topology, divergence times,
migration rates, population sizes, and ancestral states, at the cost
of being slower (typically 10²–10³ tips is the sweet spot, not 10⁵).

- **Main reference**: Bouckaert R. et al. *BEAST 2.5: An Advanced
  Software Platform for Bayesian Evolutionary Analysis.* **PLOS
  Computational Biology** 15(4): e1006650 (2019).
  DOI: `10.1371/journal.pcbi.1006650`
- **Earlier reference**: Bouckaert R. et al. *BEAST 2: A Software
  Platform for Bayesian Evolutionary Analysis.* **PLOS Computational
  Biology** 10(4): e1003537 (2014). DOI: `10.1371/journal.pcbi.1003537`
- **Main site**: `https://www.beast2.org/`
- **Tutorials**: `https://taming-the-beast.org/`, community-maintained
  tutorial collection (Stadler lab, ETH Zürich)
- **Language**: Java (cross-platform; runs on Linux, macOS, Windows)
- **License**: **LGPL**

### When to use this skill

- **dating ancient MTBC tips** with full posterior confidence intervals
  (tip-dating);
- running a **structured-coalescent phylogeography** for a lineage of
  interest (MASCOT / BASTA);
- producing a **time-scaled Bayesian tree as a figure**, manuscript, poster,
  or seminar slide;
- **testing competing demographic models** by posterior model comparison;
- whenever a **Maximum-Likelihood / Nextstrain pipeline is not rigorous
  enough for a reviewer** and full posterior distributions are required.

### Core ecosystem

| Tool | Role |
|---|---|
| **BEAST2** | MCMC engine, reads an XML specification, produces posterior samples |
| **BEAUti** | Graphical XML generator, the recommended way to set up a run |
| **Tracer** | Visual inspection of MCMC chains, ESS, convergence |
| **TreeAnnotator** | Post-processing, produces a single MCC or target tree from the posterior |
| **DensiTree** | Visualizes the posterior tree distribution as overlaid trees |
| **FigTree** / **Icytree** | Final tree visualisation for figures |

### Relevant packages (installed via BEAUti's Package Manager)

| Package | Purpose | Key citation |
|---|---|---|
| **MASCOT** | Marginal Approximation of the Structured COalescenT, scalable structured-coalescent phylogeography | Müller N.F., Rasmussen D.A., Stadler T. (2018) *Bioinformatics* 34(22): 3843–3848, DOI `10.1093/bioinformatics/bty406` |
| **BASTA** | Bayesian Structured Coalescent Approximation, more exact but slower than MASCOT | De Maio N., Wu C.-H., O'Reilly K.M., Wilson D. (2015) *PLOS Genetics* 11(8): e1005421, DOI `10.1371/journal.pgen.1005421` |
| **BEAST_CLASSIC / DiscreteTraits** | The classical Lemey-style Discrete Trait Analysis (DTA, CTMC on the tree) | Lemey P., Rambaut A., Drummond A.J., Suchard M.A. (2009) *PLOS Computational Biology* 5(9): e1000520 |
| **StructuredCoalescent** | Exact structured coalescent (Ewing et al.), very slow, rarely used | Ewing G. et al. 2004 |
| **BDSKY** | Birth-Death Skyline, phylodynamic for time-varying populations | Stadler T. et al. 2013 |
| **SA** (Sampled Ancestors) | Correctly handles ancient tips as potentially ancestral | Gavryushkina A. et al. 2014 |
| **beast-classic** | Classical BEAST v1 models ported to BEAST2 |, |

## Why it matters for MTBC × anthropology

BEAST2 is the **rigorous Bayesian layer** above the fast ML tools
(`nextstrain`, `pastml`). Its specific contributions:

1. **Tip-dating ancient MTBC tips with honest uncertainty.** The 16
   ancient MTBC genomes in SPAAM (Bos, Kay, Sabin, Vagene, Jager)
   can be used as **calibrated tips** in a BEAST2 run that produces
   posterior divergence-time intervals, not just point estimates.
   This is the methodological standard a rigorous reviewer will
   expect for any TMRCA claim in an MTBC phylogeographic paper.
2. **Structured-coalescent phylogeography via MASCOT / BASTA.** These
   packages explicitly model **migration rates between demes**
   (countries, regions, hosts) rather than pretending the tree is
   generated by a discrete Markov chain on the tips (the DTA
   approach, which is known to be biased by sampling). For any
   publishable claim about where an MTBC lineage originated or how
   fast it dispersed, structured coalescent is the rigorous choice.
3. **Posterior model comparison.** BEAST2's marginal likelihood
   estimation (stepping-stone or path sampling) lets you compare
   alternative migration models or clock models, e.g. strict vs
   relaxed clock, constant vs time-varying deme sizes, with Bayes
   factors. PastML and Augur do not provide this.
4. **Sampled Ancestors for ancient tips.** The **SA package** lets
   ancient samples be treated as potentially ancestral (not just
   derived) lineages, which is biologically more honest for
   intermediate-age ancient DNA.

## MASCOT vs BASTA vs DTA : which to use

| Method | Speed | Accuracy | Sampling-bias correction | When to use |
|---|---|---|---|---|
| **DTA (Lemey 2009)** | Fast (CTMC on tips) | Low for phylogeography, known biases | **No**, assumes random sampling | Only for didactic comparison or initial exploration; **not** for the final manuscript claim |
| **MASCOT (Müller 2018)** | Moderate | Good approximation of structured coalescent | **Yes**, models migration explicitly | **Default choice** for structured-coalescent phylogeography with many demes |
| **BASTA (De Maio 2015)** | Slower than MASCOT | More accurate in some regimes | **Yes** | When the population structure is complex or when you need the reference baseline |
| **Exact structured coalescent** | Very slow | Most accurate | Yes | Rarely used, only for very small trees |

**Recommendation for your MTBC work**: use **MASCOT** by default.
Fall back to **BASTA** only if MASCOT's approximation is challenged by a
reviewer or if the number of demes is very small (≤4).

## Workflow outline (BEAUti GUI path)

BEAST2 is classically set up through **BEAUti** (the graphical XML
generator). For a headless / scripted recipe (no BEAUti, generate the
XML programmatically), see the next section. The canonical GUI flow is:

```
alignment.fasta + metadata (tip dates + trait)
        │
        ▼
Load in BEAUti, install MASCOT package
        │
        ▼
Set clock model (strict / relaxed lognormal)
Set substitution model (GTR + Γ + I)
Set tip dates from metadata
Set trait = country (or host), enable MASCOT prior
Set MCMC chain length (10^7–10^9 depending on dataset size)
        │
        ▼
Save as <run>.xml
        │
        ▼
beast <run>.xml                 ── MCMC sampling (hours to days)
        │
        ▼
Tracer                          ── check convergence, ESS > 200 for all parameters
        │
        ▼
TreeAnnotator                   ── burn-in + MCC tree
        │
        ▼
FigTree / Icytree / baltic      ── final visualisation
```

### Tutorials (authoritative)

The **Taming the BEAST** platform (`https://taming-the-beast.org/`)
maintained by the Stadler lab at ETH Zürich is the canonical hands-on
tutorial collection. Particularly relevant:

- **MASCOT Tutorial** (v3), `https://taming-the-beast.org/tutorials/Mascot-Tutorial/`
- **BASTA Tutorial**, also on the same platform
- **Sampled Ancestors Tutorial**, tip-dating with ancient samples
- **Introduction to BEAST2**, the onboarding course

These are reproducible end-to-end walkthroughs with example data, XML
files, and expected outputs. **Do not reinvent the BEAST2 pipeline; use
a tutorial XML as template and adapt it.**

## Headless / programmatic recipe (no BEAUti : tested 2026-06, BEAST 2.7)

When there is no display (server, agent) or you need to generate many
XMLs, **emit the XML from a script** and run BEAST headless. A complete,
working reference implementation (tip-dated GTR+Γ + UCLD relaxed clock +
node MRCA calibrations + SNP ascertainment) lives in the MTBC project
`mtbc/Bovis_emergence/analyses/build_beast_{panel,alignment,xml}.py` and
`beast_harvest.py`. The non-obvious lessons:

**Invocation (Java version matters).** BEAST 2.7.x classes are compiled
for Java 23 (class file v67); the default `java` is often Java 8/17/21 and
will fail with `UnsupportedClassVersionError`. The launcher also needs
JavaFX *even headless* (main class is `beastfx.app.beast.BeastMain`):

```
export JAVA_HOME=/usr/lib/jvm/java-23-openjdk   # JavaFX bundled here (java23-openjfx)
setsid beast2 -seed 101 -overwrite run.xml > run.log 2>&1 < /dev/null &
```

Use `setsid` so the run survives the controlling session/terminal closing
(plain `nohup &` got killed overnight). BEAST writes `run.xml.state`
periodically → `beast2 -resume run.xml` continues after any kill.

**SNP alignment ⇒ ascertainment is mandatory (else dates compress).** A
SNP-only alignment (variable sites only) makes BEAST overestimate the
per-site rate and **compress node dates toward the present** (we saw an
*M. bovis* MRCA pulled from ~835 BCE to ~1390 CE). The robust correction
is **not** the Felsenstein conditioning (4 constant columns +
`ascertained excludefrom/to`), fragile and it crashes the threaded
likelihood, but the **`siteWeights`** input of `Alignment`: prepend 4
constant columns (A,C,G,T) and weight them by the *true* invariant-site
counts of each base (computed over the reference, excluding masked and
variable positions), SNPs weight 1:

```xml
<data id="aln" spec="Alignment" dataType="nucleotide"
      weights="635290,1201655,1198202,635906,1,1,1,...">
   <sequence taxon="S1" totalcount="4" value="ACGT{snp_string}"/> ...
</data>
```

BEAST then loads the **whole genome** (`[taxa, patterns, 3,683,905
sites]`); the clock rate becomes the real per-site molecular rate
(~7e-8, Menardo range) and branches/dates are not inflated. **Two hard
constraints:** (1) `siteWeights` requires `spec="TreeLikelihood"`,
`ThreadedTreeLikelihood` splits into `FilteredAlignment`s that reject
weights (*"Cannot handle site weights in FilteredAlignment"*) and NPE
with ascertainment, so the likelihood is single-threaded (threading does
not help anyway : MCMC is operator-bound, ~50 min/Msample on ~100 tips);
(2) center the clock-rate prior on the whole-genome scale,
`M = ln(rate_SNP_per_genome_per_yr / genome_sites)` (e.g. `M≈-16.5`),
**not** on the variable-site scale.

**Node calibrations & dated clades, logged directly.** Calibrations =
`MRCAPrior monophyletic="true"` with a `Normal`/`Uniform` `distr` on the
clade age (calendar years; tip dates via a `date` TraitSet). To get
posterior dates of *un-calibrated* clades (e.g. a clonal complex) without
parsing trees, add **logging-only** `MRCAPrior monophyletic="false"` with
no `distr` and `<log idref="cal_X"/>`, the `.log` then carries a
`mrca.date(ts_X)` column. Convert a logged `clockRate` to SNP/genome/yr
via ×(modelled genome size), not ×(variable sites).

**Gotchas that cost hours.** (a) `NullPointerException
TreeLikelihood.requiresRecalculation null` is usually **two BEAST runs
writing the same output files** (a test still running), check `ps`
before launching, put each chain in its own directory. (b) Kill by PID;
never `pkill -f run.xml` (it matches the launching shell). (c) **Never
read rate/dates during burn-in** (ESS≈3-5, parameters still drifting),
let it pass several M samples first. (d) Run **≥2 independent chains**
(different seeds, separate dirs) and require ESS≥200 on all parameters
before any claim. (e) ESS + posterior date HPDs can be computed from the
`.log` with a tiny Python autocorrelation estimator (Tracer-style), no
GUI needed; see `beast_harvest.py`.

## Practical chain setup for ancient MTBC

### Clock model

For MTBC with a mix of modern and ancient tips, a **relaxed lognormal
clock** is the standard choice. It allows rate variation across
branches, which matters given the debated clock rate of MTBC.

Prior on the mean clock rate: lognormal centred on ~5e-8 subs/site/year
(Menardo 2019) with a broad sigma.

### Substitution model

**GTR + Γ + I** for whole-genome MTBC alignments is standard. If you
have called SNPs only, use the `ascertainment bias correction` feature
(ASC).

### Tip dates

Enable **Use tip dates** in BEAUti. For moderns, use sampling year. For
ancient tips, convert `sample_age_BP` to a calendar year relative to
1950: `year = 1950 - age_BP`. Set the **date direction** to "since some
time in the past".

### MASCOT prior

Enable the **MASCOT** prior after installing the package. Set the
**trait (deme)** to `country` or `region`. Prior on migration rates:
lognormal with a broad sigma. Prior on effective population sizes per
deme: lognormal.

### MCMC length

- **Dataset of 100 tips**: chain length 10⁸, log every 10⁴, expect
  hours on a workstation.
- **Dataset of 500 tips**: chain length 10⁹, log every 10⁵, expect
  days on a cluster.
- **Dataset of 2 000 tips**: probably too large for MASCOT; subsample
  or switch to Nextstrain/Augur for the tree and PastML for ancestral
  reconstruction.

### Convergence criteria

Run the chain and open `<run>.log` in **Tracer**. Require:

- **ESS ≥ 200** for all parameters (**≥ 1 000** is ideal)
- Trace plots look like "hairy caterpillars" with no obvious drift
- Multiple independent chains (at least 2) converge to similar posteriors

If ESS is low, extend the chain. If chains do not converge, there is a
real problem (model misspecification, poor mixing, too much data).

## Workflows

### Workflow 1 : Tip-dated Bayesian tree of ancient + modern MTBC

Goal: produce a Bayesian time-scaled tree that places the 5–6 ancient
MTBC projects (Bos, Kay, Sabin, Vagene, Jager) on a modern MTBC
backbone with full posterior confidence intervals on divergence times.

1. Assemble a modern MTBC reference panel (e.g. 100 strains spanning
   all lineages, from TBannotator).
2. Add the ancient genomes from `spaam-ancient-metagenome-dir` (fetch
   the FASTQs from ENA/SRA, assemble, call consensus).
3. Align with MAFFT or Mugsy → SNP-only alignment.
4. In BEAUti: load alignment, enable tip dates, enable MASCOT or
   Sampled Ancestors (SA) prior, set clock and substitution models.
5. Save XML, run with `beast <run>.xml`.
6. Post-process with TreeAnnotator to get the MCC tree.

### Workflow 2 : Structured-coalescent phylogeography of L4.15

Goal: reconstruct the migration history of L4.15 Clade A between
Ghana, Peru, Argentina, and Turkey (from your memory) with rigorous
posterior intervals on migration rates.

1. Assemble L4.15 alignment from TBannotator metadata.
2. In BEAUti: load alignment, enable MASCOT, set **country** as the
   deme.
3. Set the prior on migration rates: lognormal broad.
4. Run MCMC; inspect convergence.
5. Report the posterior mean and 95% HPD for each pairwise migration
   rate.
6. Discussion: the **strongest migration rate posterior** between
   Ghana and South America supports a trans-Atlantic trade dispersal
   hypothesis (then chain with `slavevoyages` for the historical
   evidence).

### Workflow 3 : Bayes-factor test of competing demographic models

Goal: test whether MTBC L4 population size has been constant, growing,
or declining over the last 5 000 years.

1. Set up three alternative MCMC runs with different tree priors:
   - **Constant Coalescent**
   - **Exponential Coalescent**
   - **Skyline / BDSKY**
2. For each run, compute the marginal likelihood via **path sampling**
   or **stepping-stone sampling** (BEAST2 built-in).
3. Compute Bayes factors between models.
4. Report the best-supported model and the effect size.

### Workflow 4 : Cross-validation with Nextstrain

Goal: use `nextstrain` for a fast ML tree, then port the alignment to
BEAST2 for a rigorous Bayesian replication on a subsample.

1. Run Augur on the full dataset (10³–10⁴ tips) → fast ML tree.
2. Extract a representative 100–200 tips (stratified by country and
   lineage).
3. Run BEAST2 with MASCOT on the subset.
4. Compare the two trees topologically (RF distance) and the
   divergence time estimates (Augur's TreeTime vs BEAST2's relaxed
   clock) for the same internal nodes.
5. If they agree, both strengthen the inference. If they disagree,
   investigate the source (clock model, sampling bias).

## Caveats

- **BEAST2 is slow.** A structured-coalescent run with MASCOT on 100–500
  tips takes **hours to days** on a workstation. Plan accordingly;
  ideally use a compute cluster.
- **BEAST2 is GUI-driven by default.** The XML produced by BEAUti is
  human-readable but complex. Do not hand-edit XML unless you are
  confident.
- **Convergence is non-trivial.** Claim no result before ESS ≥ 200 on
  all parameters across at least two independent chains. Many BEAST2
  papers have been retracted or corrected for bad convergence.
- **Clock rate priors matter.** MTBC's clock rate is debated (3e-8 to
  7e-8). Use a broad prior and report the posterior, not the prior.
- **Scaling limit.** Don't push BEAST2 beyond 500–1 000 tips for
  structured-coalescent analyses. For larger datasets, use Nextstrain/
  Augur and accept the ML point estimates.
- **DTA is biased.** The classical Lemey discrete-trait analysis
  over-weights the most heavily sampled regions. **Do not use DTA**
  for a publishable phylogeographic claim, use MASCOT / BASTA.
- **Ancient tips with low coverage are noisy.** Use only authenticated
  ancient genomes (see `spaam-community` for damage authentication);
  run sensitivity analyses dropping individual ancient tips.
- **LGPL license.** Permissive for academic use; no license concern.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`nextstrain`** | Fast ML exploration → then BEAST2 for rigorous Bayesian replication |
| **`pastml`** | Fast ancestral state reconstruction → BEAST2's structured coalescent is the rigorous counterpart |
| **TBannotator MCP** | Source of modern MTBC sequences + metadata |
| **`spaam-ancient-metagenome-dir`** | Ancient MTBC tips with dates → tip-dating calibration |
| **`molecular-clock` skill** | Catalogue of MTBC TMRCA-as-prior constraints (see section *Contraintes temporelles dérivées de phylogénies récentes*). Use these as soft `MRCAPrior` distributions in BEAST2 XML when your analysis includes a sub-clade with a previously-published TMRCA estimate (e.g. L4.6.2.2 Madagascar 1750-1900) |
| **`spaam-community`** | Damage authentication pipeline (HOPS, damageprofiler) for ancient tips before BEAST2 |
| **`pathogens-portal`**, **`enterobase`**, **`ncbi-pathogen-detection`** | Source of pathogen sequences |
| **TreeTime** | Fast alternative for tip-dating only (without full Bayesian posterior) |
| **Tracer** | Post-MCMC diagnostic |
| **TreeAnnotator** | MCC tree from posterior |
| **FigTree / Icytree / baltic** | Tree visualisation |
| **Taming the BEAST tutorials** | Canonical reference tutorials |

## Citations

```bibtex
@article{bouckaert2019beast,
  title   = {BEAST 2.5: An Advanced Software Platform for Bayesian
             Evolutionary Analysis},
  author  = {Bouckaert, Remco and Vaughan, Timothy G. and
             Barido-Sottani, Jo{\"e}lle and Duch{\^e}ne, Sebasti{\'a}n and
             Fourment, Mathieu and Gavryushkina, Alexandra and
             Heled, Joseph and Jones, Graham and K{\"u}hnert, Denise and
             De Maio, Nicola and Matschiner, Michael and others},
  journal = {PLOS Computational Biology},
  volume  = {15},
  number  = {4},
  pages   = {e1006650},
  year    = {2019},
  doi     = {10.1371/journal.pcbi.1006650}
}

@article{muller2018mascot,
  title   = {MASCOT: parameter and state inference under the marginal
             structured coalescent approximation},
  author  = {M{\"u}ller, Nicola F. and Rasmussen, David A. and Stadler, Tanja},
  journal = {Bioinformatics},
  volume  = {34},
  number  = {22},
  pages   = {3843--3848},
  year    = {2018},
  doi     = {10.1093/bioinformatics/bty406}
}

@article{demaio2015basta,
  title   = {New Routes to Phylogeography: A Bayesian Structured
             Coalescent Approximation},
  author  = {De Maio, Nicola and Wu, Chieh-Hsi and O'Reilly, Kathleen M.
             and Wilson, Daniel},
  journal = {PLOS Genetics},
  volume  = {11},
  number  = {8},
  pages   = {e1005421},
  year    = {2015},
  doi     = {10.1371/journal.pgen.1005421}
}

@article{lemey2009dta,
  title   = {Bayesian Phylogeography Finds Its Roots},
  author  = {Lemey, Philippe and Rambaut, Andrew and Drummond, Alexei J.
             and Suchard, Marc A.},
  journal = {PLOS Computational Biology},
  volume  = {5},
  number  = {9},
  pages   = {e1000520},
  year    = {2009},
  doi     = {10.1371/journal.pcbi.1000520}
}
```

**Always cite** (i) BEAST2 (Bouckaert 2019), (ii) the specific package
you used (MASCOT, BASTA, SA…), and (iii) the tutorial or paper that
inspired your XML setup.

## Codex packaging note

This packaged copy targets Codex. MCP tool names in `allowed-tools` are prerequisites: verify them with `codex mcp list` in the active profile before relying on live queries.
