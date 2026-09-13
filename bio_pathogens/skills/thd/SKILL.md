---
name: thd
description: >-
  Academic research toolkit for peer-reviewed molecular-epidemiology research (Guyeux group,
  FEMTO-ST). Computes Time-scaled Haplotypic Density (THD, Rasigade et al. 2017), a
  published measure of the relative expansion of bacterial lineages, by kernel density
  estimation on pairwise genetic distances parameterised by a timescale. Use when computing
  THD on MIRU-VNTR profiles, SNP distance matrices or WGS haplotypes from a research
  collection, comparing relative expansion across MTBC lineages in a study, associating the
  measure with study covariates, or separating recent from long-term signal for a scientific
  publication.
argument-hint: "<input_file> [--timescale 20] [--mu 5e-4] [--markers 15]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres
---

> [!WARNING]
> **[2026-09-08] Les requêtes de ce skill qui filtrent sur un système de lignée MAISON ne rendent
> plus rien.** Le MCP TBannotator est arrêté ; le serveur `tblearn` qui le remplace ne porte que
> huit systèmes **externes** (Coll, Coscolla, Freschi, Lipworth, Napier, Palittapongarnpim,
> Shitikov, Stucki). `system_name = 'guyeux'` et `system_name = 'tblearn'` y rendent **zéro ligne
> sans lever d'erreur**, ce qu'un script lira comme « aucune souche ne satisfait le critère ».
>
> **Substitution, décidée le 2026-09-08 :** les lignées maison se lisent désormais dans la base
> LOCALE `bdd/actuelle/`, qui fait déjà autorité selon
> `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`, via le skill `bdd-bridge` :
>
> ```bash
> B=~/docs/codes/claude_plugins/bio_pathogens/skills/bdd-bridge/scripts
> export TBANNOTATOR_BDD=~/docs/codes/mtbc/bdd
> python3 $B/bdd_query.py clades                # tous les clades et leurs effectifs
> python3 $B/bdd_query.py denominator <clade>   # effectif réellement exploitable
> python3 $B/bdd_query.py strains <clade>       # souches d'un clade
> ```
>
> `tblearn` reste utilisable pour tout le reste (SPDI, QC, métadonnées, RD, IS, CRISPR) et pour
> **comparer** à une taxonomie externe, mais ce n'est plus la source des lignées maison. Toute
> requête qui filtre sur `system_name` doit d'abord vérifier que le filtre a matché :
> `SELECT system_name, count(*) FROM mv_strain_lineage WHERE system_name = '<x>' GROUP BY 1;`
> — zéro ligne signifie « ce système n'existe pas ici », jamais « aucune souche ».
>
> Détail complet : `~/.agents/knowledge/tblearn-migration.md`.


# THD - Time-scaled Haplotypic Density

Compute isolate-level estimates of epidemic success from genetic distances between pathogen haplotypes, parameterized by a biologically meaningful timescale (TMRCA50).

**Reference**: Rasigade J-P et al. "Strain-specific estimation of epidemic success provides insights into the transmission dynamics of tuberculosis." *Scientific Reports* 7:45326 (2017). DOI: 10.1038/srep45326

## Arguments

```
thd_compute.py <input_file> [options]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `input_file` | (required) | CSV: haplotype matrix or distance matrix |
| `--timescale`, `-t` | `20` | Timescale(s) in years, e.g. `--timescale 20 200` |
| `--mu` | `5e-4` | Evolutionary rate (changes/locus/year) |
| `--markers`, `-m` | auto | Number of markers (required for distance matrices) |
| `--format`, `-f` | `auto` | `haplotype_matrix` or `distance_matrix` |
| `--group-column`, `-g` | none | Column name for within-group THD |
| `--normalize`, `-n` | off | Compute Z-score normalized THD |
| `--output`, `-o` | none | Output CSV path |
| `--plot`, `-p` | none | Output plot path (PNG/PDF) |

## Mathematical Foundation

### Kernel function (truncated geometric distribution)

For a genetic distance h (number of allelic differences) between two haplotypes, the kernel density is:

```
k(h|b,m) = ((1-b) / (1 - b^(m+1))) * b^h
```

- `b` : bandwidth (0 < b < 1), controls how fast density drops with distance
- `m` : number of markers (truncation limit)
- `h` : pairwise genetic distance (integer, 0 to m)

### THD (density for one isolate)

```
THD(y|X,b,m) = (1/n) * SUM_i k(h_i | b, m)
             = (1/n) * ((1-b) / (1 - b^(m+1))) * SUM_i b^(h_i)
```

Where h_i is the distance from isolate y to each isolate x_i in the sample X of size n.

### Timescale parameterization (Infinite Alleles Model)

The bandwidth `b` is unintuitive. The IAM converts it to a timescale t50 (TMRCA such that closer haplotypes contribute 50% of the density):

1. **Median distance**: `h50 = (1 - exp(-2 * mu * t50)) * m`
2. **Bandwidth**: solve `(1 - b*^h50) / (1 - b*^m) = 1/2` numerically via Brent's method

### Scaling and normalization

| Transform | Formula | Purpose |
|-----------|---------|---------|
| Scaled THD | `THD * m` | Invariant across different marker counts |
| log-THD | `log(THD)` | For linear models (group stats = geometric means) |
| Normalized THD | `(log_THD - mean) / std` | Z-score, comparable across timescales |

**Group statistics**: always use geometric means (= arithmetic mean of log-THD, then exponentiate).

## Input Formats

### 1. Haplotype matrix (CSV)

Rows = isolates, columns = loci. First column = isolate ID. Optional group column.

```csv
id,lineage,MIRU02,MIRU04,MIRU10,MIRU16,MIRU20,...
ERR123,L4.1,2,3,4,3,2,...
ERR456,L4.2,2,3,5,3,2,...
```

- Pairwise Hamming distances are computed automatically
- Missing values (`NA`, `?`, empty) are handled: distances computed on available loci

### 2. Distance matrix (CSV)

Pre-computed symmetric pairwise distance matrix. **`--markers` required**.

```csv
id,ERR123,ERR456,ERR789
ERR123,0,3,7
ERR456,3,0,5
ERR789,7,5,0
```

## Default Parameters

| Data type | m | mu | t50 short | t50 long | Max timescale |
|-----------|---|-----|-----------|----------|---------------|
| 15-loci MIRU-VNTR | 15 | 5e-4 /locus/year | 20y | 200y | ~400y |
| 24-loci MIRU-VNTR | 24 | 5e-4 /locus/year | 20y | 200y | ~250y |
| WGS SNPs | variable | ~1e-7 /site/year | 20y | 200y | varies |

**Constraint**: h50 should be < m/3 to limit homoplasy bias. The script warns when violated.

## Running the Script

The script is at `${CLAUDE_PLUGIN_ROOT}/skills/thd/scripts/thd_compute.py`. Dependencies: `numpy`, `scipy`.

```bash
# Basic: MIRU-VNTR haplotypes, 20-year timescale
python3 scripts/thd_compute.py haplotypes.csv --timescale 20 --mu 5e-4 -o results.csv

# Dual timescales (epidemicity + endemicity)
python3 scripts/thd_compute.py data.csv --timescale 20 200 -o results.csv

# With lineage groups and normalization
python3 scripts/thd_compute.py data.csv -t 20 200 -g lineage --normalize -o results.csv -p plot.png

# Pre-computed distance matrix
python3 scripts/thd_compute.py distances.csv -f distance_matrix -m 15 -t 20 200 -o results.csv
```

## Output Format

CSV columns per timescale t:

| Column | Description |
|--------|-------------|
| `isolate_id` | Isolate identifier |
| `group` | Group label (if `--group-column`) |
| `thd_{t}` | Raw THD value (probability) |
| `scaled_thd_{t}` | THD * m (cross-method comparable) |
| `log_thd_{t}` | log(THD) for linear models |
| `normalized_thd_{t}` | Z-score (if `--normalize`) |
| `within_group_thd_{t}` | THD computed within group only (if `--group-column`) |
| `within_group_log_thd_{t}` | log of within-group THD |

JSON summary printed to stdout with: n_isolates, n_markers, mu, and per-timescale stats (h50, b*, geometric means, log-THD mean/std).

## Interpretation Guide

### Short-term THD (t50 = 20y)
- **High THD20**: isolate belongs to a recent transmission cluster (epidemicity)
- Correlates with: younger patient age, AFB-positive sputum, pulmonary infection
- Reflects **recent epidemic success**

### Long-term THD (t50 = 200y)
- **High THD200**: isolate belongs to a lineage with long-term evolutionary success (endemicity)
- Correlates with: French-native patient status (endemic strains in region of origin)
- ~200y corresponds to the Industrial Revolution, coinciding with MTBC lineage expansions
- Reflects **endemic prevalence and persistence**

### Global vs within-group THD
- **Global THD**: computed against all strains. Captures both prevalence and genetic relatedness.
  - Euro-American lineage: high global THD200 due to high prevalence
- **Within-group THD**: computed within a lineage/family. Reflects clonality independent of prevalence.
  - East-Asian/Beijing: high within-group THD (clonal) despite lower prevalence

### Reading results
- Compare geometric means of THD across groups (not arithmetic means)
- Use log-THD as response variable in linear regression
- Normalized THD (Z-scores) allows comparing across different timescales within the same study

## TBannotator Integration

To compute THD from WGS data stored in TBannotator:

### Step 1: Query SPDI profiles for a lineage

```sql
SELECT ss.strain_id, array_agg(ss.spdi_id ORDER BY ss.spdi_id) as spdis
FROM tb_report_strain_spdi ss
JOIN mv_strain_classification c ON ss.strain_id = c.strain_id
WHERE c.system_name = 'guyeux' AND c.lineage_code = '4.15'
GROUP BY ss.strain_id;
```

### Step 2: Build binary presence/absence matrix

Convert SPDI profiles to a binary matrix (strains x SPDIs), then compute pairwise Hamming distances.

### Step 3: Run THD

```bash
python3 scripts/thd_compute.py spdi_matrix.csv -f haplotype_matrix -t 20 200 -o thd_results.csv
```

**Note**: for WGS data, set `--mu` to the per-site rate (~1e-7 /site/year for MTBC). The number of markers m is the number of informative SPDI positions.

**Performance**: O(n^2) pairwise distances. For >500 strains, consider sub-lineage analysis.

## Verification

### Quick sanity checks

For m=15, mu=5e-4:
- t50=20y: h50=0.297, b*=0.097 (very concentrated kernel)
- t50=200y: h50=2.719, b*=0.782 (broader kernel)

### Test case

A 5-haplotype test (mimicking Figure 1 of the paper):

```csv
id,L1,L2,L3,L4,L5,L6,L7,L8,L9,L10,L11,L12,L13,L14,L15
A,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
B,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2
C,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2
D,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2
E,1,1,1,1,1,1,1,2,2,2,2,2,2,2,3
```

Expected: At short timescale, A and B (close pair) have higher THD than C (no close neighbor). At long timescale, differences between clades become visible in within-group THD.

## Citation

```bibtex
@article{rasigade2017strain,
  title={Strain-specific estimation of epidemic success provides insights into
         the transmission dynamics of tuberculosis},
  author={Rasigade, Jean-Philippe and Barbier, Maxime and Dumitrescu, Oana
          and Pichat, Catherine and Carret, G{\'e}rard and others},
  journal={Scientific Reports},
  volume={7},
  pages={45326},
  year={2017},
  doi={10.1038/srep45326},
  publisher={Nature Publishing Group}
}
```
