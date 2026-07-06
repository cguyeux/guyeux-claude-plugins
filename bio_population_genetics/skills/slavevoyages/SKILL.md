---
name: slavevoyages
description: >-
  Query slavevoyages.org (36k+ voyages, 1514-1866) to build phylogeographic
  scenarios for MTBC lineage articles. Correlates TB lineage distributions with
  trans-Atlantic trade routes, TMRCA estimates, and historical migration events.

  Use when: explaining New World presence of African TB lineages (L5, L6, L4),
  building a dispersal hypothesis for a lineage, or correlating TMRCA with
  historical population movements (Gold Coast → Americas, Bight of Benin, etc.).
---

# SlaveVoyages.org — Usage Guide for MTBC Phylogeography

## Overview

SlaveVoyages.org (Rice University / Emory University) is the definitive database on the
trans-Atlantic and intra-American slave trade. It documents **36,000+ voyages** (1514–1866),
with embarkation/disembarkation ports, number of enslaved people, and temporal data.

**Why it matters for MTBC**: Historical forced population movements are a major driver
of *M. tuberculosis* lineage dispersal. Correlating the geographic distribution of a
TB lineage with slave trade routes can:
- Explain New World presence of African-origin lineages (L5, L6, some L4 sub-lineages)
- Support TMRCA estimates with historical migration events
- Distinguish colonial-era introduction from modern migration

**Main URL**: `https://www.slavevoyages.org/`  
**Voyage Database**: `https://www.slavevoyages.org/voyage/database`  
**Interactive Map (Timelapse)**: `https://www.slavevoyages.org/voyage/maps`

> [!NOTE]
> The REST API (`api.slavevoyages.org`) requires authentication and is not publicly
> accessible. Use the **browser-based interface** for data extraction, or download
> the published datasets directly.

## Client (resilient, tool-first)

A **stdlib-only** client ships with this skill (`src/slavevoyages_client/`, nothing
to pip-install). Download the Trans-Atlantic Voyages CSV once, point the client at
it, and filter voyages / summarise a route without hand-rolling pandas over the SPSS
variable codes:

```bash
SRC=<this skill>/src          # absolute path to slavevoyages/src

export SLAVEVOYAGES_FILE=/path/to/tast_voyages.csv
# how much movement on a route, and when?
PYTHONPATH="$SRC" python3 -m slavevoyages_client summary --embark "Gold Coast" --disembark Brazil
# the individual voyages, as a stable TSV:
PYTHONPATH="$SRC" python3 -m slavevoyages_client voyages --embark "Gold Coast" --disembark Brazil --period 1700 1800 --tsv

# offline reproducibility / CI: runs against the bundled fixture, no network
PYTHONPATH="$SRC" python3 -m slavevoyages_client.smoke_test
```

Python API:

```python
from slavevoyages_client import SlaveVoyagesClient
sv = SlaveVoyagesClient()
summ = sv.route_summary(embark="Gold Coast", disembark="Brazil")
# -> {'voyages': N, 'embarked': ..., 'disembarked': ..., 'year_min': ..., 'year_max': ...}
# drop that volume + window straight into a phylogeography paragraph for an L4/L5/L6
# New-World presence, then check it against the lineage's TMRCA.
```

`embark` / `disembark` match (case-insensitive) the region OR the principal port, so
"Gold Coast", "Anomabu", "Brazil", "Bahia" all work. **Stable output columns**:
`voyage_id, year, embark_region, embark_port, disembark_region, disembark_port,
embarked, disembarked, flag`. **Resolution cascade**: `SLAVEVOYAGES_FILE` override
-> disk cache -> bundled fixture -> `DatasetUnavailable`; `SLAVEVOYAGES_OFFLINE=1`
forbids the network; `inspect` prints the real header (reconcile schema drift).

## Downloadable Datasets

The most reliable data access method is via published CSV/SPSS downloads:

| Dataset | URL | Records |
|---------|-----|---------|
| Trans-Atlantic Voyages | `https://www.slavevoyages.org/voyage/database#downloads` | ~36,000 |
| Intra-American Voyages | `https://www.slavevoyages.org/american/database#downloads` | ~11,000 |
| Enslaved People | `https://www.slavevoyages.org/past/database#downloads` | ~100,000 |

These datasets can be downloaded as CSV and analyzed locally with Python/pandas.

## Key Variables for MTBC Phylogeography

### Voyage Database Variables

| Variable | Description | MTBC Relevance |
|----------|-------------|----------------|
| `YEARAM` | Year of arrival | Correlate with TMRCA |
| `MAJBUYPT` | Principal port of embarkation (Africa) | Source region for lineage |
| `MAJSELPT` | Principal port of disembarkation (Americas) | Destination |
| `REGEM1`, `REGEM2`, `REGEM3` | Embarkation regions | Broad geographic matching |
| `REGDIS1`, `REGDIS2`, `REGDIS3` | Disembarkation regions | Broad geographic matching |
| `SLAXIMP` | Total embarked (imputed) | Volume of movement |
| `SLAMIMP` | Total disembarked (imputed) | Volume of movement |
| `NATINIMP` | Flag (national carrier) | Colonial power context |
| `FATE2` | Outcome of voyage | Filter successful arrivals |

### Geographic Regions in the Database

#### Embarkation (Africa)
| Code | Region | MTBC Lineages Present |
|------|--------|----------------------|
| Senegambia | Senegal, Gambia, Guinea-Bissau | L5, L6, L4 |
| Sierra Leone | Sierra Leone, Liberia | L5, L6 |
| Windward Coast | Ivory Coast | L5 |
| Gold Coast | Ghana | L4 (incl. L4.15 Clade A) |
| Bight of Benin | Togo, Benin, Nigeria | L5, L4 |
| Bight of Biafra | SE Nigeria, Cameroon | L4, L5 |
| West Central Africa | Congo, Angola | L4, L6 |
| Southeast Africa | Mozambique, Madagascar | L1, L3, L4 |

#### Disembarkation (Americas)
| Region | Modern Countries | Key TB Lineages |
|--------|-----------------|-----------------|
| Brazil (Bahia, Rio, Pernambuco) | Brazil | L4 (LAM family) |
| Caribbean (Jamaica, Haiti, Cuba) | Caribbean islands | L4, L2 |
| Mainland North America | USA (SE coast) | L4 |
| Río de la Plata | Argentina, Uruguay | L4 (incl. L4.15?) |
| Spanish Americas | Peru, Colombia, Venezuela | L4 (incl. L4.15) |

## Common Workflows for MTBC Articles

> Prefer the **client** (`python -m slavevoyages_client summary|voyages`, see above)
> over the browser/pandas steps below; the workflows here add the narrative and
> map-figure context the client does not produce.

### Workflow 1: Build an evolutionary scenario for a lineage

Given a TB lineage with known geographic distribution (from TBannotator), build a
plausible historical dispersal hypothesis:

1. **Extract lineage geography** from TBannotator MCP:
   ```sql
   SELECT country, COUNT(*) FROM mv_strain_metadata m
   JOIN mv_strain_classification c ON m.sra_id = c.sra_id
   WHERE c.system = 'Senelle' AND c.lineage_code = '4.15'
   GROUP BY country ORDER BY COUNT(*) DESC;
   ```

2. **Identify relevant trade routes** on SlaveVoyages:
   - Navigate to `https://www.slavevoyages.org/voyage/database`
   - Filter by embarkation region matching African source countries
   - Filter by disembarkation region matching American destination countries
   - Extract voyage counts and date ranges

3. **Cross-reference with TMRCA**:
   - If TMRCA ≈ 1600–1800 → strong slave trade hypothesis
   - If TMRCA ≈ 1900+ → likely modern migration instead
   - If TMRCA ≈ pre-1500 → pre-colonial dispersal

4. **Write the narrative**: "The presence of L4.X in both [African region] and
   [American region] is consistent with the trans-Atlantic slave trade, which
   transported an estimated [N] individuals from [embarkation] to [disembarkation]
   between [year range] (slavevoyages.org)."

### Workflow 2: Quantify trade volume between specific regions

For a specific pair (e.g., West Africa → Peru):

1. Navigate to the voyage database
2. Set embarkation filter: Region = relevant African coast
3. Set disembarkation filter: Region = relevant American port/country
4. Note: total embarked, total disembarked, year range
5. Use the "Timelapse" map for a visual representation

### Workflow 3: Seasonal/temporal analysis

The voyage database records arrival years. To correlate with molecular clock:
1. Download the full CSV dataset
2. Filter by relevant routes
3. Plot cumulative arrivals over time
4. Overlay with TMRCA confidence interval from TreeTime

## Example: L4.15 Evolutionary Scenario

L4.15 strains are found in: Ghana (Clade A), Peru, Argentina, Turkey, France, etc.

**Hypothesis building**:
- **Ghana → Americas**: The Gold Coast was a major embarkation region
  - ~1.2M people embarked from Gold Coast (1514–1866)
  - Major destinations: Caribbean, Brazil, mainland Americas
  - The presence of L4.15 Clade A in Ghana + related strains in Peru/Argentina
    could reflect trans-Atlantic dispersal
- **Turkey / France**: More likely reflects modern migration or colonial-era
  Mediterranean trade routes (not slave trade)
- **Timeline check**: If L4.15 TMRCA ≈ 1750–1850, consistent with peak trade period

## Interactive Map (Timelapse)

The animated map at `https://www.slavevoyages.org/voyage/maps` is excellent for:
- Visualizing trade intensity over time
- Identifying peak periods for specific routes
- Creating screenshots for article supplementary materials

## Browser Automation Tips

1. **Use `browser_subagent`** to navigate the SPA (React-based)
2. The database page loads dynamically — wait for table to render
3. Filters are applied via UI controls (dropdowns, sliders)
4. **Download CSV** is the most reliable extraction method
5. For programmatic analysis, download the full dataset once and analyze locally

## When NOT to use

- **Non-trans-Atlantic / non-1514-1866 movement.** This is the Atlantic slave-trade
  window. For Roman-era connectivity use `orbis`; for other Old-World routes
  `owtrad`; for ancient migration `aadr` + `migration-data`.
- **Causal proof of dispersal.** A route's volume is a *prior* for a lineage's
  New-World presence, not proof. Always cross-check the TMRCA (a 1900+ TMRCA points
  to modern migration, not the slave trade) and the lineage tree.
- **The Mantel / correlation test itself.** Use `coevolution`; this skill supplies
  the historical movement table.
- **Genomes.** Host = `aadr`, pathogen = `spaam-ancient-metagenome-dir` /
  TBannotator; SlaveVoyages is the historical-movement layer only.

## Citation

```bibtex
@misc{slavevoyages2024,
  title = {Slave Voyages: The Trans-Atlantic Slave Trade Database},
  url = {https://www.slavevoyages.org},
  year = {2024},
  note = {Accessed: [date]}
}
```

## Integration with Other Skills

| Tool | Purpose |
|------|---------|
| **TBannotator MCP** | Get lineage geographic distribution |
| **SITVIT2** | Cross-reference spoligotype clade geography |
| **SlaveVoyages** | Historical migration context |
| **PubMed** | Search for published phylogeographic studies |
| **TreeTime** | Molecular dating to anchor historical events |
