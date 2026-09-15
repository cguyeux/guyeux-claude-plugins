---
name: iqtree-lsd2
description: >-
  IQ-TREE 2 with integrated LSD2 (Least-Squares Dating 2): fast
  Maximum-Likelihood inference plus molecular dating, the pragmatic alternative
  to BEAST2 for a time-scaled tree on 10^3–10^5 tips. ModelFinder, UFBoot2,
  tip-date calibration.

  Use when: building an ML MTBC tree with model selection and bootstrap
  support, dating it from tip dates, scaling to thousands of genomes, or
  making a starting tree for BEAST2.
---

# IQ-TREE 2 + LSD2 : Fast ML Phylogenetics with Tip-Dating

> [!TIP]
> **Où faire tourner IQ-TREE.** `-T AUTO` sur le portable plafonne vite : au-delà de quelques
> centaines de taxons, ou avec `-B 1000` sur un alignement large, le calcul appartient aux machines
> distantes. `mh` partition `smp` (32 à 48 c, 93 à 251 Go) ou `mpi` (24 c/nœud), 8 jours maximum ;
> `mp` sinon (64 threads, aucune limite de temps). **IQ-TREE 3.1.3 est prêt sur `mh`** dans
> `/Work/Users/cguyeux/envs/phylo/bin`, où le binaire s'appelle **`iqtree`** et non `iqtree2` :
> adapter les commandes de ce skill en conséquence. Rien sur `mp`.
> Voir le skill `remote-compute` (sonde d'état, modèles `sbatch`, pièges). Prérequis : VPN monté (`sudo vpn up`).


## Overview

**IQ-TREE 2** is the reference open-source Maximum-Likelihood
phylogenetic inference package, developed by **Bui Quang Minh**,
**Heiko Schmidt**, **Olga Chernomor**, **Dominik Schrempf**, **Michael
Woodhams**, **Arndt von Haeseler**, **Robert Lanfear** and
contributors. It integrates three high-value steps in a single
command-line tool:

1. **ModelFinder**, ultrafast automated substitution model selection
   (10–100× faster than jModelTest / ProtTest)
2. **Fast ML tree search**, parsimony + NJ starting trees optimised
   by hill-climbing NNI
3. **UFBoot2**, ultrafast bootstrap approximation with unbiased
   branch support values

Recent versions also integrate **LSD2** (*Least-Squares Dating 2*) from
**Thu-Hien To**, **Matthieu Jung**, **Stéphane Guindon** and **Olivier
Gascuel** at the Institut Pasteur, a fast non-Bayesian dating method
that converts ML branch lengths into a time-scaled tree via a
least-squares criterion, orders of magnitude faster than BEAST2.

The IQ-TREE + LSD2 combination is the **pragmatic workhorse** of the
constellation's analytical layer: it does in minutes what BEAST2 does
in days, at the cost of point estimates instead of posterior
distributions. It is the reference pipeline for large-scale bacterial /
MTBC phylogenetics where BEAST2 does not scale, and the natural choice for
quick-turnaround time-scaled trees used in **exploratory analysis**.

- **IQ-TREE 2 reference**: Minh B.Q., Schmidt H.A., Chernomor O.,
  Schrempf D., Woodhams M.D., von Haeseler A., Lanfear R. *IQ-TREE 2:
  New Models and Efficient Methods for Phylogenetic Inference in the
  Genomic Era.* **Molecular Biology and Evolution** 37(5): 1530–1534
  (2020). DOI: `10.1093/molbev/msaa015`
- **ModelFinder reference**: Kalyaanamoorthy S., Minh B.Q., Wong T.K.F.,
  von Haeseler A., Jermiin L.S. *ModelFinder: fast model selection for
  accurate phylogenetic estimates.* **Nature Methods** 14: 587–589
  (2017). DOI: `10.1038/nmeth.4285`
- **UFBoot2 reference**: Hoang D.T., Chernomor O., von Haeseler A.,
  Minh B.Q., Vinh L.S. *UFBoot2: Improving the Ultrafast Bootstrap
  Approximation.* **Molecular Biology and Evolution** 35(2): 518–522
  (2018). DOI: `10.1093/molbev/msx281`
- **LSD2 reference**: To T.-H., Jung M., Lycett S., Gascuel O. *Fast
  dating using least-squares criteria and algorithms.* **Systematic
  Biology** 65(1): 82–97 (2016). DOI: `10.1093/sysbio/syv068` (the
  LSD1 paper; LSD2 is a subsequent refinement with updated variance
  handling)
- **Main site**: `https://iqtree.github.io/` (IQ-TREE 3 / ongoing) and
  `http://www.iqtree.org/` (classical)
- **Dating tutorial** (source of the `--date-*` options documented below,
  checked 2026-09-14): `https://iqtree.github.io/doc/Dating`. Some `--date-*`
  flags exist only in `iqtree2 --help` / the `iqtree2` man page and are
  **absent from this tutorial page** — flagged explicitly where relevant.
- **GitHub**: `https://github.com/iqtree/iqtree2`
- **LSD2 GitHub** (source for the standalone `lsd2` options table below):
  `https://github.com/tothuhien/lsd2`. No PDF manual or extended doc file in
  the repo; the README points to `lsd2 -h` for the exhaustive option list.
- **License**: **GPL**
- **Current versions** (verified April 2026 via GitHub API):
  - **`iqtree/iqtree2`** → **v2.4.0** (Feb 2025), stable line
  - **`iqtree/iqtree3`** → **v3.1.1**, parallel major line with
    expanded features
  - LSD2 is integrated into both as the `--date` option.

## Why it matters for MTBC × anthropology

IQ-TREE + LSD2 fills the **"fast rigorous middle"** between Nextstrain
(accessible but Augur-flavoured) and BEAST2 (rigorous but slow):

1. **Scale to thousands of MTBC genomes.** IQ-TREE routinely handles
   10³–10⁴ bacterial genomes in hours on a workstation. BEAST2 tops
   out at ~500 tips for structured analyses; IQ-TREE + LSD2 scales
   10–100× further for point-estimate dating.
2. **Model selection honesty.** ModelFinder prevents the "default GTR
   without justification" anti-pattern and produces a reviewer-proof
   Methods section entry.
3. **Tip-dating in one command.** For ancient MTBC tips from SPAAM,
   LSD2's `--date` option reads a simple TSV of sampling years and
   produces a dated tree in minutes. No BEAUti XML editing, no
   MCMC convergence worries.
4. **Starting tree for BEAST2.** The IQ-TREE ML tree + LSD2 dating
   is an excellent **starting tree** for a subsequent BEAST2 refinement
   on a subset, it dramatically reduces BEAST2 burn-in time.

## Core pipeline in one command

```bash
iqtree2 \
  -s alignment.fasta \
  -m MFP \                    # ModelFinder Plus (best model)
  -B 1000 \                   # UFBoot2 ultrafast bootstrap (1000 replicates)
  -alrt 1000 \                # SH-aLRT branch test (1000 replicates)
  -T AUTO \                   # auto-detect CPU threads
  --prefix mtbc_run \         # output prefix
  --date dates.tsv \          # LSD2 tip-dating
  --date-tip 0 \              # present (tips) at t=0 for LSD2 timescale convention
  --date-ci 100 \             # 100 bootstrap replicates for LSD2 confidence intervals
  --date-outlier 3            # detect date outliers with 3-sigma threshold
```

### Inputs

- **`alignment.fasta`**, aligned multi-FASTA (nucleotide or amino
  acid). For MTBC use a reference-based whole-genome alignment or a
  core-SNP alignment.
- **`dates.tsv`**, two-column TSV: tip name and sampling year (or
  `b(min,max)` for uncertain dates, e.g. `b(-1050,-950)` for an
  ancient tip with ±50 year uncertainty).

### Outputs (with `--prefix mtbc_run`)

| File | Content |
|---|---|
| `mtbc_run.iqtree` | Main log: best model, likelihood, parameter estimates |
| `mtbc_run.treefile` | Final ML tree (Newick) |
| `mtbc_run.contree` | Consensus tree with UFBoot support values |
| `mtbc_run.splits.nex` | Split supports for SplitsTree |
| `mtbc_run.bionj` | Starting BioNJ tree |
| `mtbc_run.model.gz` | ModelFinder output |
| `mtbc_run.timetree.nex` | **LSD2 time-scaled tree** (when `--date` is used) |
| `mtbc_run.timetree.nwk` | Same as Newick |
| `mtbc_run.lsd` | LSD2 log with substitution rate estimate, root date, CI |

## Installation

```bash
# Option A — Conda (recommended)
conda install -c bioconda iqtree

# Option B — pre-built binary
wget https://github.com/iqtree/iqtree2/releases/download/v2.4.0/iqtree-2.4.0-Linux-intel.tar.gz
tar xzf iqtree-2.4.0-Linux-intel.tar.gz
export PATH=$PWD/iqtree-2.4.0-Linux-intel/bin:$PATH
# Or for IQ-TREE 3.x (parallel major line with additional features):
# wget https://github.com/iqtree/iqtree3/releases/download/v3.1.1/iqtree-3.1.1-Linux-intel.tar.gz

# Option C — via nf-core pipelines (for large-scale reproducible builds)
```

Verify:

```bash
iqtree2 --version
iqtree2 --help | head -30
```

## ModelFinder : the substitution model layer

ModelFinder tests a library of models (GTR, HKY, TN, TIM, K3P, SYM, …
× base frequencies × Γ or I rate variation × ±FreeRate) and selects
the best under BIC / AIC / AICc.

```bash
# Default: ModelFinder Plus — find best model + FreeRate + partition
iqtree2 -s aln.fasta -m MFP

# Restrict to nucleotide models for bacteria
iqtree2 -s aln.fasta -m "GTR+I+G,TN+I+G,HKY+I+G"

# Skip model selection and use a specific model
iqtree2 -s aln.fasta -m GTR+G+I
```

For MTBC whole-genome alignments, **GTR+I+G** is the near-universal
best model per ModelFinder. Run ModelFinder once and cite the specific
output in Methods.

## UFBoot2 : the branch support layer

UFBoot2 replaces bootstrap replicates (~1000 independent tree searches)
with an approximation that is orders of magnitude faster. Use
`-B 1000` as the default.

**Important**: UFBoot2 values are *unbiased* but interpret ≥ 95% as
"strong support", not ≥ 70% as with standard bootstrap. This difference
catches many researchers off-guard.

Complement with `-alrt 1000` (SH-aLRT branch test) for a second
independent support measure, a branch with both SH-aLRT ≥ 80% **and**
UFBoot2 ≥ 95% is considered strongly supported.

## LSD2 : the tip-dating layer

LSD2 converts ML branch lengths (substitutions per site) into calendar
time using tip dates and a least-squares criterion. It is:

- **Fast**: seconds to minutes for 10³–10⁴ tips
- **Non-Bayesian**: point estimates, not posteriors (confidence
  intervals come from bootstrap on the dates, not from MCMC)
- **Rate-heterogeneous aware**: can use a relaxed clock via LSD's
  variance model

### Date file format

Two columns, tab- or space-separated:

```
SRR12345678   2018
SRR23456789   2019-06-15
Kay2015_S1    b(-1950,-1850)
Sabin2020     -1700
Bos2014_S1    b(-1100,-900)
```

- **Integer or float**: interpreted as calendar year (negative = BCE
  or, more commonly in tip-dating, years before present depending on
  the `--date-tip` convention).
- **`b(min,max)`**: bounded interval; LSD2 treats the date as uniform
  on `[min, max]`.
- **Unknown tip**: omit from the file; LSD2 treats it as undated.

### Running LSD2 standalone

LSD2 can also be run as a standalone binary on an existing tree:

```bash
lsd2 -i mtbc.treefile -d dates.tsv -o mtbc_lsd2 -f 100 -c
# -f : bootstrap replicates for CI
# -c : confidence intervals
```

### Outlier detection

`--date-outlier 3` flags tips whose dates are inconsistent with the
tree topology by more than 3 standard deviations (Z-score cutoff on
the root-to-tip residual). It is documented on the official tutorial
page (`iqtree.github.io/doc/Dating`, section *Full list of LSD2
options*) as `--date-outlier NUM` — "Z-score cutoff to remove outlier
tips/nodes". Outliers are usually:
- Modern contamination in an ancient sample
- Misidentified sequencing dates
- Real accelerated / decelerated lineages

Report any detected outliers in the Methods and investigate before
removing. **`--date-outlier` self-removes ingroup tips before LSD2
runs** — it replaces a manual exclusion list (accessions identified
beforehand by a separate TreeTime run) that does not generalise across
a multi-clade panel: point it at the same panel used for the final
dating run instead of re-deriving a fixed blacklist per subset.

> [!WARNING]
> **`--date-outlier` cannot fix a structural conflict at the root — only
> individual point outliers.** The Z-score residual it computes presupposes
> that an initial clock fit is already achievable; if the failure is a
> genuine ordering conflict (an ancestor forced younger than a descendant,
> typically from an outgroup on an incompatible timescale, see
> `--date-no-outgroup` below), no per-tip removal threshold will fix it,
> because the diagnostic that would flag the guilty tip cannot itself be
> computed before the conflict is resolved. Verified case (Bovis_full,
> 2026-09-14): an IQR×3 filter on 1633 root-to-tip residuals found only 2
> candidate outliers, and removing them changed nothing — the true cause was
> the outgroup's dates (see below), identical failure at three widely
> different fixed rates (0.147 / 0.35 / 0.65 SNP/genome/year), which itself
> is the tell that the problem is a temporal *ordering* conflict rather than
> a scale/rate problem.

### Conflit outgroup / ingroup sur une horloge différente : `--date-no-outgroup`

**Symptôme.** `iqtree2 --date ... -te tree.nwk -o outgroup1,outgroup2 ...`
échoue net avec :

```
Error: There's conflict or not enough signal in the input temporal constraints.
```

au stade précis, visible dans le log, « Estimating the root position on the
branch defined by given outgroups ». Le message ne dit pas quel tip est en
cause, et l'échec survient **après** l'étape la plus coûteuse du calcul
(l'optimisation ML des longueurs de branche sous topologie fixée, `-te`) —
voir la technique de diagnostic par reprise de checkpoint ci-dessous pour
itérer sans repayer cette étape à chaque essai.

**Cause typique : un outgroup emprunté à une autre lignée/espèce, daté sur
la même échelle de collecte que l'ingroup.** Un outgroup phylogénétiquement
éloigné (ex. *M. caprae* utilisé pour enraciner et dater un panel
*M. bovis*) porte des dates de COLLECTE modernes comme n'importe quel tip de
l'ingroup, mais sa branche mesure une divergence INTER-lignées bien plus
ancienne que ce que l'horloge INTRA-espèce appliquée à l'ingroup peut
représenter. Verser ses dates dans la même contrainte temporelle que
l'ingroup force donc un ordre impossible à la racine. Cas vérifié
(`Bovis_full/analyses/phaseP13_3_lsd2_squelette.py`, 2401 tips, outgroup
*M. caprae* 12 tips, 2026-09-14) : l'échec est **identique au mot près** à
trois taux très éloignés testés isolément, ce qui prouve d'emblée un
conflit d'ordre temporel, pas un problème d'échelle.

**Correctif** : `--date-no-outgroup`. D'après le manpage IQ-TREE2 (option
absente de la page tutoriel `iqtree.github.io/doc/Dating`, trouvée en
creusant `iqtree2 --help`) :

```
--date-no-outgroup    Exclude outgroup from time tree
```

Comportement observé sur le cas ci-dessus (`clade_dating.py::dater()`,
`lineage_navigator/`) : la topologie garde l'outgroup pour placer la racine
(`-o`/`-g`, comme d'habitude), mais ses PROPRES dates de tips sont retirées
de la contrainte temporelle appliquée par LSD2. Le calcul est passé du
premier coup une fois cette option ajoutée, sans autre changement. La
description terse du `--help` ("exclude outgroup from time tree") est plus
ambiguë que ce comportement observé — vérifier sur `timetree.nwk`/`.nex` en
sortie si l'outgroup y figure encore avant de présumer l'un ou l'autre sur
un nouveau jeu de données.

**Règle transposable** : avant de dater un panel avec un outgroup emprunté à
une AUTRE lignée ou espèce (nécessaire à la topologie, pas forcément à la
même échelle temporelle que le clade qu'on date), retirer PAR PRINCIPE ses
dates de la contrainte temporelle plutôt que de les y laisser par défaut.
L'échec, quand il vient de là, ne pointe jamais vers l'outgroup dans le
message d'erreur, et se distingue mal d'un problème d'outlier individuel
sans avoir isolé les deux hypothèses par élimination (voir l'encadré
`--date-outlier` ci-dessus). Détail complet, mesures et code de production :
`~/.agents/knowledge/bioinformatics.md` (entrée 2026-09-14, « LSD2 …
échoue sec … `--date-no-outgroup` corrige ») et
`lineage_navigator/analyses/clade_dating.py::dater()` (paramètres
`date_outlier`, `date_no_outgroup`).

### Diagnostic rapide par reprise de checkpoint (sans `-redo`)

Relancer IQ-TREE **sans** `-redo` sur le même `--prefix` reprend directement
à l'étape de dating (LSD2) sans repayer l'optimisation ML des longueurs de
branche sous topologie fixée (`-te`), qui est l'étape la plus coûteuse.
Mesuré sur un panel de 2401 tips / 61959 colonnes : ~5 minutes de
branch-length optimization contre 2-3 secondes pour rejouer LSD2 seul depuis
le checkpoint. Méthode de débogage standard pour tout script de datation
IQ-TREE+LSD2, pas seulement pour le cas outgroup ci-dessus : elle permet de
tester plusieurs hypothèses (outliers, `--date-no-outgroup`, plusieurs taux
via `--date-options "-w fichier_taux"`) en quelques secondes chacune plutôt
qu'en plusieurs minutes. **Attention** : ceci ne fonctionne que si
l'alignement, la topologie (`-te`) et le modèle sont inchangés d'un run à
l'autre — tout run avec `-redo` explicite ou une entrée modifiée repaie
l'étape complète.

### Autres options `--date-*` et LSD2 repérées mais non exploitées ici

Non intégrées faute de cas d'usage concret actuel dans le pipeline MTBC,
listées pour mémoire (sources : `iqtree.github.io/doc/Dating`, manpage
`iqtree2`, `github.com/tothuhien/lsd2` README + `lsd2 -h`) :

| Option | Where | Description (verbatim quand citée) |
|---|---|---|
| `--date-root STRING` | IQ-TREE | Root date as a real number or YYYY-MM-DD |
| `--clock-sd NUM` | IQ-TREE | Std-dev for lognormal relaxed clock (default: 0.2) — équivalent LSD2 `-q` |
| `--dating mcmctree` (IQ-TREE 3) | IQ-TREE | Bascule sur MCMCtree (datation bayésienne PAML) au lieu de LSD2 : workflow en 3 étapes (arbre ML → génération de la matrice Hessienne → run MCMCtree), clock models EQUAL/IND/CORR, calibrations fossiles sur nœuds internes. Alternative rigoureuse mais lourde à LSD2 ; se recouvre avec `beast2-dating`/`beast2-phylogeography` côté bayésien complet. |
| `-c` (LSD2 natif) | LSD2 standalone | Contraintes temporelles (activées par défaut) |
| `-v 0\|1\|2` (LSD2 natif) | LSD2 standalone | Mode de variance des longueurs de branche ; ce skill et `molecular-clock` n'utilisent que `-v 1` |
| `-e NUM` (LSD2 natif) | LSD2 standalone | Seuil Z-score outlier — équivalent natif LSD2 de `--date-outlier`, accessible via `--date-options "-e N"` si l'on veut un seuil différent sans repasser par le flag IQ-TREE |
| `-u`, `-U` (LSD2 natif) | LSD2 standalone | Longueur de branche minimale, interne / externe, dans l'arbre chronologique produit |
| `-S NUM` (LSD2 natif) | LSD2 standalone | Seuil de valeur de support en dessous duquel une branche est traitée comme non résolue |
| `-l NUM` (LSD2 natif) | LSD2 standalone | Seuil de longueur de branche non-informative (défaut 0.5/longueur de séquence) |
| `-G` / `-k` (LSD2 natif) | LSD2 standalone | Suppression vs conservation explicite des outgroups dans l'arbre chronologique final — distinct de `--date-no-outgroup` côté IQ-TREE (celui-ci agit sur la contrainte temporelle, pas sur la présence dans l'arbre) |
| `-R NUM` (LSD2 natif) | LSD2 standalone | Facteur d'arrondi des dates estimées |
| Fichier de calibration ancestrale (IQ-TREE) | IQ-TREE | Format alternatif à `mrca(...) b(min,max)` : `taxon1,taxon2<TAB>-50` (une valeur ponctuelle par groupe de tips, pas d'espace dans la liste), utilisé avec `--date-tip 0` |

Aucun de ces mécanismes n'a été mesuré sur un jeu MTBC par ce skill ; les
introduire demande une validation dédiée avant citation en Methods.

## Workflows

### Workflow 1 : Build a tip-dated MTBC L4 tree at scale

Goal: produce a time-scaled L4 tree of 2 000 MTBC isolates in an
afternoon.

```bash
# 1. Align with a reference-based pipeline (e.g. snippy, MTBseq, bactmap)
#    → produces core_snps.fasta + reference H37Rv

# 2. Build dates.tsv from TBannotator metadata
cut -f1,4 metadata.tsv > dates.tsv   # strain + year

# 3. Run IQ-TREE 2 + LSD2 in one command
iqtree2 \
  -s core_snps.fasta \
  -m GTR+I+G \
  -B 1000 -alrt 1000 \
  -T AUTO \
  --prefix L4_timetree \
  --date dates.tsv \
  --date-ci 100 \
  --date-outlier 3

# 4. Inspect: mtbc_run.lsd gives the substitution rate + root date + CI
cat L4_timetree.lsd

# 5. Visualise with FigTree / Icytree / TreeViewer
```

A few hours on a workstation, two weeks of equivalent BEAST2 time.

### Workflow 2 : Ancient-tip anchored dating

Goal: use the 16 ancient MTBC genomes from SPAAM as tip calibration
for the root date of a lineage.

1. Assemble a panel: 16 ancient tips + ~200 balanced modern tips.
2. Build `dates.tsv` with moderns at their sampling year and ancients
   at bounded intervals (`b(year - uncertainty, year + uncertainty)`).
3. Run IQ-TREE + LSD2 with `--date-ci 100 --date-outlier 3`.
4. The LSD log will report:
   - Mean substitution rate (should be ~5e-8 per site per year for MTBC)
   - Root date with 95% CI
   - Any ancient tip flagged as an outlier
5. Compare with independent BEAST2 runs on the same dataset for
   cross-validation.

### Workflow 3 : Pre-process for BEAST2

Goal: use IQ-TREE to generate a good starting tree for BEAST2
refinement.

1. Run IQ-TREE as above on the full dataset.
2. Extract the ML tree (`L4_timetree.treefile`) or time-scaled tree
   (`L4_timetree.timetree.nwk`).
3. In BEAUti, **load the IQ-TREE tree as the starting tree** (File →
   Set Starting Tree) for the BEAST2 run.
4. BEAST2 burn-in is typically 10× shorter starting from a good ML
   tree vs from random.

### Workflow 4 : Model selection for MTBC whole genomes

Goal: formally justify the substitution model for a Methods section.

```bash
iqtree2 -s mtbc_aln.fasta -m MF -T AUTO --prefix model_selection
# -m MF : only run ModelFinder, no tree search
```

Open `model_selection.iqtree` and cite the BIC-best model in your
Methods. For MTBC this is almost always **GTR+I+G** but the formal
report is stronger than the default assumption.

### Workflow 5 : Partition analysis

For whole-genome MTBC with coding and non-coding regions, you can
partition the alignment and let each partition have its own model:

```bash
iqtree2 -s mtbc_aln.fasta -p mtbc.partitions.nex -m MFP+MERGE -B 1000
# -p : partition file (Nexus or RAxML format)
# MFP+MERGE : find best model per partition AND merge similar partitions
```

## Caveats

- **Point estimates, not posteriors.** LSD2 gives you a mean + CI via
  bootstrap, not a posterior distribution like BEAST2. For papers
  where full posterior quantification is required (BDSKY, structured
  coalescent), use BEAST2 instead (or in addition).
- **UFBoot2 thresholds differ from standard bootstrap.** Use ≥ 95%,
  not ≥ 70%.
- **Tip-date outliers must be investigated.** Do not remove flagged
  outliers automatically, they are often signal, not noise.
- **Alignment quality matters.** IQ-TREE is only as good as the input
  alignment. For MTBC, use a reference-based pipeline (snippy, MTBseq,
  nf-core/bactmap) to generate the alignment, not *de novo* assembly
  + MSA.
- **Clock rate is a single estimate.** LSD2 returns one rate (or a
  relaxed rate per branch), not a prior-posterior comparison. Report
  it as a point estimate.
- **No structured coalescent.** IQ-TREE + LSD2 is not a substitute
  for MASCOT / BASTA when you need rigorous structured-coalescent
  phylogeography.
- **No skyline plot.** For Ne(t) trajectories, use `bayesian-skyline`
  (BEAST2) instead.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`nextstrain`** | Augur internally wraps IQ-TREE / FastTree / RAxML, this skill documents IQ-TREE standalone |
| **`pastml`** | Takes an IQ-TREE+LSD2 time-scaled tree as input for ancestral state reconstruction |
| **`beast2-phylogeography`** | Use IQ-TREE tree as starting tree for BEAST2 refinement |
| **`bayesian-skyline`** | Use IQ-TREE tree as starting tree for BEAST2 skyline analysis |
| **TBannotator MCP** | Source of modern MTBC sequences and dates for `--date` input |
| **`spaam-ancient-metagenome-dir`** | Ancient tips for tip-calibrated LSD2 dating |
| **`molecular-clock` skill** | Catalogue of MTBC TMRCA-as-prior constraints (see section *Contraintes temporelles dérivées de phylogénies récentes*). Format LSD2 `-g constraints.txt` lines provided per sub-clade (e.g. L4.6.2.2 Madagascar `b(1750,1900)`). Also see its per-lineage outgroup/calibration strategy table when choosing an outgroup across lineages — cross-check against `--date-no-outgroup` above if that outgroup sits on a different timescale. |
| **snippy, MTBseq, nf-core/bactmap** | Reference-based alignment pipelines feeding IQ-TREE |
| **FigTree / Icytree / baltic** | Tree visualisation |
| **gotree / nw_utils** | Newick manipulation utilities |
| **SplitsTree** | Network analysis of IQ-TREE splits output |

## Citations

```bibtex
@article{minh2020iqtree2,
  title   = {IQ-TREE 2: New Models and Efficient Methods for
             Phylogenetic Inference in the Genomic Era},
  author  = {Minh, Bui Quang and Schmidt, Heiko A. and Chernomor, Olga
             and Schrempf, Dominik and Woodhams, Michael D. and
             von Haeseler, Arndt and Lanfear, Robert},
  journal = {Molecular Biology and Evolution},
  volume  = {37},
  number  = {5},
  pages   = {1530--1534},
  year    = {2020},
  doi     = {10.1093/molbev/msaa015}
}

@article{kalyaanamoorthy2017modelfinder,
  title   = {ModelFinder: fast model selection for accurate
             phylogenetic estimates},
  author  = {Kalyaanamoorthy, Subha and Minh, Bui Quang and Wong, Thomas K.F.
             and von Haeseler, Arndt and Jermiin, Lars S.},
  journal = {Nature Methods},
  volume  = {14},
  pages   = {587--589},
  year    = {2017},
  doi     = {10.1038/nmeth.4285}
}

@article{hoang2018ufboot2,
  title   = {UFBoot2: Improving the Ultrafast Bootstrap Approximation},
  author  = {Hoang, Diep Thi and Chernomor, Olga and von Haeseler, Arndt
             and Minh, Bui Quang and Vinh, Le Sy},
  journal = {Molecular Biology and Evolution},
  volume  = {35},
  number  = {2},
  pages   = {518--522},
  year    = {2018},
  doi     = {10.1093/molbev/msx281}
}

@article{to2016lsd,
  title   = {Fast dating using least-squares criteria and algorithms},
  author  = {To, Thu-Hien and Jung, Matthieu and Lycett, Samantha and
             Gascuel, Olivier},
  journal = {Systematic Biology},
  volume  = {65},
  number  = {1},
  pages   = {82--97},
  year    = {2016},
  doi     = {10.1093/sysbio/syv068}
}
```

**Always cite** (i) IQ-TREE 2 (Minh 2020), (ii) ModelFinder
(Kalyaanamoorthy 2017) if you use model selection, (iii) UFBoot2
(Hoang 2018) if you use `-B`, and (iv) LSD (To 2016) if you use
`--date`.
