---
name: sitvitweb
description: >-
  Query the SITVIT2 spoligotype database (Institut Pasteur de Guadeloupe) for
  MTBC spoligotype assignments, SIT lookups, clade names (Beijing, LAM, Haarlem,
  T1...), and geographic distributions. Browser-only (no REST API).

  Use when: converting spoligotype octal to SIT number, identifying clade for
  a strain, finding geographic distribution of a SIT, or cross-referencing
  spol43/spol98 fields from TBannotator metadata.
argument-hint: "<SIT number, octal code, or clade name>"
user-invocable: true
---

# SITVITweb (SITVIT2) — Usage Guide

## Overview

SITVIT2 is the international spoligotyping database maintained by the Institut Pasteur de Guadeloupe. It catalogues **Spoligo International Types (SITs)** — standardised patterns of spacer presence/absence in the CRISPR Direct Repeat (DR) locus of MTBC strains.

**Base URL**: `http://www.pasteur-guadeloupe.fr:8081/SITVIT2/`

> [!IMPORTANT]
> SITVIT2 has **no REST API**. All queries require browser-based interaction
> (AJAX forms). Use the `browser_subagent` tool to automate queries.
> The server can be slow — always set generous timeouts.

## Core Concepts

| Term | Definition |
|------|-----------|
| **SIT** | Spoligo International Type — a unique numerical ID for each distinct 43-spacer pattern |
| **Spoligotype** | Binary (43 chars: ■/□ or 1/0) or octal (15 digits) representation of spacer presence/absence |
| **MIT** | MIRU International Type — analogous to SIT but for MIRU-VNTR patterns |
| **VIT** | VNTR International Type |
| **Clade** | Named phylogenetic family (Beijing, Haarlem, LAM, T, X, EAI, CAS, Bovis, etc.) |

## Spoligotype Formats

| Format | Example | Usage |
|--------|---------|-------|
| **Binary 43** | `1111111111111111111111110100111111111111111` | Internal representation |
| **Octal 15** | `777777777760771` | Most common query format |
| **Visual** | `■■■■■■■■■■■■■■■■■■■■■■■□■□□■■■■■■■■■■■■■■■■` | Display format |

### Conversion: Binary → Octal
Split binary into 14 groups of 3 + 1 final: each triplet → octal digit (0–7).

## Available Pages and Query Types

### 1. SEARCH — Individual Queries
**URL**: `http://www.pasteur-guadeloupe.fr:8081/SITVIT2/query`

The main search form accepts multiple criteria simultaneously:

| Field | CSS Selector | Description | Example |
|-------|-------------|-------------|---------|
| Spoligotype (Octal) | `#spoligoText` | 15-digit octal spoligotype | `777777777760771` |
| SIT Number | `#sitText` | SIT integer | `1` (= Beijing) |
| MIRU-12 | `#miruText12` | 12-locus MIRU pattern | |
| MIRU-15 | `#miruText15` | 15-locus MIRU pattern | |
| MIRU-24 | `#miruText24` | 24-locus MIRU pattern | |
| Clade/Lineage | `#cladeText` | Named clade | `T1`, `LAM9`, `Beijing` |
| Country of Origin | `#oriText` | Country name | `France` |
| Country of Isolation | `#isoText` | Country name | `Peru` |

**Workflow for browser automation**:
1. Navigate to `/query`
2. Fill the appropriate input field
3. Click "Submit" button
4. Wait for AJAX response (table loads dynamically)
5. Parse the results table or click "Export to Excel"

### 2. ANALYSIS — Batch Queries
**URL**: `http://www.pasteur-guadeloupe.fr:8081/SITVIT2/batch.jsp`

Upload an Excel file with spoligotype patterns to get:
- SIT assignments for each pattern
- Clade assignments
- Closest matches for orphan patterns

**Input format**: Excel (XLS) with columns using `o`/`n` notation (present/absent).

### 3. ONLINE TOOLS
**URL**: `http://www.pasteur-guadeloupe.fr:8081/SITVIT2/tools.jsp`

Sub-tools accessible via tabs:

| Tab | Function |
|-----|----------|
| **Genotyping markers** | Bulk SIT/MIT lookup via `#sitTextArea` |
| **Lineages** | Distribution analysis by lineage |
| **Cartography** | World maps for SIT geographic distribution |
| **Distributions** | Country/region statistics for a given SIT |
| **Potential evolution** | Spoligotype pattern evolution modelling |
| **Connection with other databases** | Cross-references |

### 4. OTHER STATISTICS
**URL**: `http://www.pasteur-guadeloupe.fr:8081/SITVIT2/stata.jsp`

Pre-computed statistics: global SIT distribution, top clades, etc.

## Common Use Cases for MTBC Articles

### Look up a spoligotype by octal code
```
1. Navigate to http://www.pasteur-guadeloupe.fr:8081/SITVIT2/query
2. Enter octal code in the spoligotype field (#spoligoText)
3. Submit and parse: SIT number, clade assignment, geographic distribution
```

### Get geographic distribution for a SIT
```
1. Navigate to /tools.jsp
2. Select the "Distributions" or "Cartography" tab
3. Enter SIT number
4. Extract country counts and percentages
```

### Identify clade for a known SIT
```
SIT → Clade mapping examples:
- SIT1 = Beijing
- SIT53 = T1
- SIT358 = T1 (historical: Bangladesh/East Africa)
- SIT42 = LAM9
- SIT50 = Haarlem3
- SIT33 = LAM3
```

### Cross-reference with TBannotator
The TBannotator MCP `mv_strain_metadata` view contains `spol43` and `spol98` fields.
Use SITVIT2 to convert these patterns to SIT numbers and named clades.

## Automation Tips

1. **Always use browser_subagent** — no HTTP API available
2. **Set long timeouts** — the server is on a Freebox, response can be slow (5–30s)
3. **Watch for AJAX** — results load dynamically; wait for table rows to appear
4. **Export to Excel** when available — structured data is easier to parse than HTML tables
5. **Cache results** — avoid repeated queries; SIT assignments are stable
6. **Handle errors gracefully** — the server may timeout or return 405 on direct HTTP requests

## Reference SIT Numbers for L4 Sub-Lineages

| SIT | Octal | Clade | Notes |
|-----|-------|-------|-------|
| 1 | `000000000003771` | Beijing | L2 reference |
| 53 | `777777777760771` | T1 | Common in L4 |
| 358 | `717777777760771` | T1 | Historical Bangladesh/East Africa |
| 42 | `777777607760771` | LAM9 | |
| 50 | `777777777720771` | Haarlem3 | |
| 52 | `777777777760731` | T2 | |
| 47 | `777777777760771` | Haarlem1 | Same octal as SIT53 (MIRU distinguishes) |

> [!NOTE]
> Multiple SITs can share the same octal pattern — they are distinguished by MIRU-VNTR profiles.
> Conversely, the same SIT can appear in multiple phylogenetic lineages (SNP-based classification ≠ spoligotype-based classification).
