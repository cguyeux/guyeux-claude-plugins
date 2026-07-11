---
name: sitvitweb
description: >-
  Query the SITVIT spoligotype database (Institut Pasteur de Guadeloupe) for
  MTBC spoligotype assignments, SIT lookups, clade names (Beijing, LAM, Haarlem,
  T1...), and geographic distributions (country, city, patient origin, year,
  strain holder). The online server (port 8081) is OFTEN DOWN: a full LOCAL COPY
  of 62 996 isolates ships at ~/Documents/codes/MTBC/TB-tools/data/SIT.xls — use
  it first. Also carries the recipe to compute IN SILICO spoligotypes from the mp
  pipeline (136k strains, ESP* spacer entries), and the warning that SITVIT's
  Clade column is spoligotype-derived: filter it by HAMMING DISTANCE to genome-confirmed
  consensus profiles (~12% of AFRI labels are wrong), never by exact octal match.

  Use when: converting spoligotype octal to SIT number, identifying clade for
  a strain, finding the geographic/subnational distribution of a SIT, tracing
  patient origin vs isolation country, or computing in-silico spoligotypes for
  WGS strains. (NB: TBannotator has NO spoligotype in its database — no spol43,
  no spol98, no DR entries. Compute them from mp.)
argument-hint: "<SIT number, octal code, or clade name>"
user-invocable: true
---

# SITVITweb (SITVIT2) — Usage Guide

## Overview

SITVIT2 is the international spoligotyping database maintained by the Institut Pasteur de Guadeloupe. It catalogues **Spoligo International Types (SITs)** — standardised patterns of spacer presence/absence in the CRISPR Direct Repeat (DR) locus of MTBC strains.

**Base URL**: `http://www.pasteur-guadeloupe.fr:8081/SITVIT2/`

> [!CAUTION]
> **LE SERVEUR EST SOUVENT INJOIGNABLE — commencer par la COPIE LOCALE, pas par le site.**
> Vérifié 2026-07-11 : le domaine résout et le port 80 répond, mais le **port 8081 (la base) time-out
> au niveau TCP** (il tourne sur une Freebox). N'y perdez pas 20 minutes.
>
> **✅ COPIE LOCALE COMPLÈTE — `~/Documents/codes/MTBC/TB-tools/data/SIT.xls`**
> **62 996 isolats**, format `.xls` OLE (⚠ nécessite `xlrd` : `python3 -m venv /tmp/v && /tmp/v/bin/pip install
> xlrd pandas`, car PEP 668 bloque `pip install` en global sur Arch).
> Colonnes : `IsoNumber, Nb Strains, Spoligotype Binary, Spoligotype Octal, 12/15/24-loci MIRU, VNTR, SIT,
> 12/15/24-MIT, VIT, Clade, Latitude, Longitude, Origin Country, Isolation Country, Year, Drug Resistance,
> Sex, Age, HIV, Investigator, **City of Isolation**, Remarks`.
> ⚠ **`Origin Country` ≠ `Isolation Country`** : le premier est le pays d'ORIGINE du patient (migrant ou non),
> le second le lieu du diagnostic. C'est LA colonne qui distingue un cas autochtone d'une importation.
> ⚠ **Piège pandas** : la colonne octal est lue en **int64** → les zéros de tête sautent
> (`060000777777671` → `60000777777671`) et toute jointure renvoie 0 ligne. Toujours
> `dtype=str` + `.str.zfill(15)` **des deux côtés**.
>
> Autres fichiers utiles au même endroit : `sit_to_lineage.pkl`, `lineage_to_sit.pkl`, `sit_to_sra.pkl`,
> et `~/Documents/codes/MTBC/Spolgraph/SITVIT23882_PHELAN_SNPBASEDLIN_SORTED.xlsx` (23 882 souches
> séquencées : octal ↔ SIT ↔ lignée SNP).

> [!IMPORTANT]
> Si le site répond : SITVIT2 has **no REST API**. All queries require browser-based interaction
> (AJAX forms). Use the `browser_subagent` tool to automate queries.
> The server can be slow — always set generous timeouts.

---

## ⚠⚠ RÈGLE D'OR — VÉRIFIER LE `Clade` DE SITVIT, MAIS AVEC LE BON CRITÈRE

Le `Clade` de SITVIT est déduit **du spoligotype seul**. Or les familles définies par des **absences de
spacers** (AFRI, BOV) sont des **attracteurs de convergence** : une souche LAM/T/H qui perd les bons spacers
y tombe. Le seul marqueur licite de *M. africanum* est **RD9** (LSP), jamais le spoligotype.

**Taux d'erreur réel, mesuré 2026-07-11 (projet L5L6, 709 isolats `AFRI`)** : **~12 % de faux** (6 % au profil
L4 caractérisé + 7 % trop éloignés), 6 % ambigus, et **82 % confirmés**. Le label est donc **globalement bon,
mais il faut le filtrer**.

> [!WARNING]
> **NE PAS filtrer par correspondance EXACTE de l'octal** (erreur commise puis corrigée : elle donnait un faux
> taux d'erreur de 32 %). Les appels de spoligotype in silico ont **~10 % de dropout par spacer**, donc un vrai
> profil Maf peut légitimement ne pas figurer dans le jeu d'octals observés. **Filtrer par DISTANCE.**

### ✅ La bonne méthode — critère STRUCTURAL, pas lexical

1. Établir la lignée par **SNP/SPDI** (`bdd/actuelle/`), jamais par une étiquette texte.
2. Calculer les **profils CONSENSUS** de sous-lignée (spoligo in silico + vote majoritaire — voir plus bas).
3. Classer chaque isolat SITVIT par **distance de Hamming** (sur les 43 bits) au consensus le plus proche :
   - **d ≤ 3 → CONFIRMÉ.** Spécificité mesurée : seuls **0,02 %** des 62 287 isolats **non-AFRI** de SITVIT
     sont à d≤3 (leur médiane est d = 10). Critère très discriminant.
   - d 4-6 → ambigu. d ≥ 7 → exclu.
4. **VERROU STRUCTURAL, décisif** : ***M. africanum* CONSERVE les spacers 33-36**, que **L4 a perdus**.
   Un isolat dont les spacers **33-36 sont TOUS absents est un profil L4** — exclure sans discussion,
   **quelle que soit** son étiquette SITVIT.

**Faux positif documenté, qui aurait fait un beau résultat faux** : SIT 1476 (`736177607700171`), étiqueté
`AFRI_2`, compte **7 isolats à Lima tous d'origine péruvienne** (1999-2005, trois investigateurs indépendants)
+ 2 à Buenos Aires. Cela ressemble à un **foyer sud-américain autochtone de *M. africanum***. Ce n'en est pas
un : **Hamming = 10** du profil Maf le plus proche, et **spacers 33-36 = `0000`** (signature L4). Ses MIRU
sont « Orphan ». Réfuté structurellement.

Validation de la méthode : consensus in silico **L6.1.1/L6.1.2 = `770777777777671` = SIT 181**
(= le SIT rapporté par Rabahi et al. 2020 pour la souche brésilienne) ; **L5.2.2.2 = `774077607777071` =
SIT 331**. Les profils in silico tombent exactement sur les SIT de SITVIT.

---

## Spoligotype IN SILICO depuis le pipeline `mp` (136 822 souches)

> [!WARNING]
> **NE PAS utiliser `known_coverage/DR*` du `report.json` : c'est du BRUIT.** Le locus DR y est à profondeur
> médiane ~2x quand le génome est à 100-190x (les reads du DR, répétitif, sont jetés par le filtre mapq).
> Preuve en 30 s : huit souches Beijing à >100x donnent **huit motifs DR différents**, alors que le
> spoligotype Beijing est invariant.

> [!TIP]
> **Le caller est écrit, calibré et testé : `scripts/spoligo_insilico.py`** (livré avec ce skill).
> Ne pas le réécrire. Il doit tourner **sur mp** (c'est là que sont les résultats du pipeline) :
> ```
> scp <skill>/scripts/spoligo_insilico.py mp:/tmp/
> ssh mp 'python3 /tmp/spoligo_insilico.py --calibrate /tmp/beijing.txt'   # ⚠ CQ obligatoire
> ssh mp 'python3 /tmp/spoligo_insilico.py /tmp/sras.txt > /tmp/spolo.csv' # appels individuels
> ssh mp 'python3 /tmp/spoligo_insilico.py --consensus /tmp/groupes.tsv'   # profils par sous-lignée
> ```
> `--calibrate` doit rendre **30-40 %** d'octals Beijing exacts (validé : 13/40 = 32 %). Si c'est **0 %**,
> le mapping spacer→ESP est faux et **rien n'est exploitable**.

**La bonne source** : `mp:/data/current/run/results/<SRA>/known_coverage_stats.tsv`, colonnes
`#rname startpos endpos numreads covbases coverage meandepth meanbaseq meanmapq`.
Y chercher les **493 entrées `ESP*`** (*espaceurs*), numérotées 1-68 avec variants alléliques
(`ESP21_1`, `ESP21_2`…).

⚠ **Les 43 spacers standards ne sont PAS `ESP1..ESP43`** — ils sont un **sous-ensemble dispersé** des 68.
Correspondance établie par appariement de **séquences** avec
`~/Documents/codes/MTBC/TB-tools/data/fastas/spoligo_old.fasta` (les 43) et `spoligo_new.fasta` (les 98) :

```python
SPACER_TO_ESP = {1:2, 2:3, 3:4, 4:12, 5:13, 6:14, 7:15, 8:18, 9:19, 10:20, 11:21, 12:22,
                 13:23, 14:24, 15:25, 16:26, 17:27, 18:28, 19:29, 20:30, 21:31, 22:32,
                 23:33, 24:34, 25:35, 26:36, 27:37, 28:38, 29:39, 30:40, 31:41, 32:42,
                 33:43, 34:44, 35:46, 36:47, 37:51, 38:52, 39:53, 40:62, 41:63, 42:64, 43:65}
```

**Règle d'appel** : spacer présent ssi **un quelconque** de ses variants (`ESPn`, `ESPn_1`, …) a **≥1 read**
(prendre le `max` des `numreads` sur les variants). Puis binaire 43 bits → octal (14 triplets + 1 bit).

**Calibration obligatoire sur Beijing** (octal canonique `000000000003771`) : sensibilité par spacer ≈ **90 %**,
donc l'octal exact ne sort que dans **~40 %** des cas (0,90⁹ — Beijing n'a que 9 spacers présents).
⇒ **Le dropout est un biais de FAUSSE ABSENCE : il s'annule par VOTE MAJORITAIRE.** L'appel est fiable
**en consensus de sous-lignée**, PAS souche par souche. Ne jamais tirer de conclusion d'un octal individuel.

**Profils consensus *M. africanum* obtenus (1 351 appels fiables, 2026-07-11)** :

| sous-lignée | octal consensus | SIT |
|---|---|---|
| L5.2.2.2 | `774077607777071` | **331** |
| L6.1.1 / L6.1.2 | `770777777777671` | **181** |
| L6.2 | `670777707777671` | — |

Signatures : **L5 perd les spacers 8-12 et 21-24** ; **L6 perd 7-9** ; **les deux CONSERVENT 33-36**, que L4 a
perdus (marqueur classique de *M. africanum*).

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

> [!CAUTION]
> **FAUX (corrigé 2026-07-11) : la vue `mv_strain_metadata` ne contient AUCUN champ `spol43`/`spol98`.**
> Vérifié sur `information_schema` : il n'existe **aucune** colonne contenant `spol`/`spacer`/`sit` dans la
> base PostgreSQL de TBannotator, et le catalogue `tb_report_rd_catalog` ne contient **aucune** entrée `DR*`.
> **Il n'y a pas de spoligotype en base** — il faut le calculer depuis `mp` (section ci-dessus).

Ce qui EXISTE en base et qui est utile :
- **`tb_ncbi_biosample.genotype`** — le champ `genotype` déposé par les soumetteurs NCBI. Sur **247 753**
  BioSamples, seuls **7 582** le renseignent et **80** portent un octal 15 chiffres — et ils viennent **tous
  du même dépôt** (l'État de Hawaï : Manila 25, Beijing 23…). **Inutilisable pour un criblage global.**
- ⚠ **Piège de sous-chaîne** : `WHERE genotype ILIKE '%AFRI%'` ramène 142 lignes dont **~140 faux positifs** —
  `East-African-Indian` (EAI) **contient** « AFRI ». Toujours ancrer le motif ou filtrer sur l'octal.

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
