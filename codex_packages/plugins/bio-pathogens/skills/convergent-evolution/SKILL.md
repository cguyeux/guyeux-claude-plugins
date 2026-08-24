---

name: convergent-evolution
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST), peer-reviewed MTBC
  phylogenomics: detects convergent / parallel evolution across MTBC lineages,
  genes mutated independently in several lineages, enrichment for PE/PPE, ESX,
  PKS/PDIM.

  Use when: comparing mutation patterns between animal and human lineages, genes
  under convergent selection, host adaptation signatures, ESX system evolution.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres
---

# Convergent Evolution : Évolution convergente MTBC

Détection d'évolution convergente (parallèle) entre lignées MTBC indépendantes. Identifie les gènes mutés de façon récurrente dans des lignées phylogénétiquement distinctes, signe de pression de sélection.

## Contexte biologique

Le MTBC présente des patterns d'évolution convergente remarquables, particulièrement entre les lignées animales (M. bovis, M. caprae, M. orygis, etc.) qui ont acquis des mutations similaires de façon indépendante. 333 gènes montrent des mutations convergentes entre espèces animales (base de connaissances TB).

### Systèmes clés

| Système | Rôle | Pattern attendu |
|---------|------|-----------------|
| **PE/PPE** | Interaction hôte, évasion immunitaire | Enrichi chez animales (p<0.002) |
| **ESX** (Type VII secretion) | Sécrétion de protéines de virulence | Réajustement fonctionnel, pas destruction |
| **PKS/PDIM** | Lipides de paroi, virulence | Sélection positive dans gènes auxiliaires |
| **Gènes de résistance** | Résistance aux antibiotiques | Convergence rpoB/katG/gyrA entre lignées MDR |

## Phase 1 : Découverte (OBLIGATOIRE)

1. **Quelles lignées comparer ?**
   - Animales vs humaines (classique)
   - Sous-lignées d'une lignée majeure (ex. sous-lignées L4 résistantes)
   - Lignées géographiquement distinctes (convergence par adaptation locale)

2. **Focus sur quel système ?**
   - `all` : tous les gènes (analyse exploratoire)
   - `pe_ppe` : famille PE/PPE uniquement
   - `esx` : systèmes ESX (ESX-1 à ESX-5)
   - `pks_pdim` : biosynthèse lipidique
   - `resistance` : gènes de résistance WHO
   - `custom` : liste de gènes fournie

3. **Seuil de convergence ?**
   - `--min-lineages 2` : mutation dans ≥2 lignées indépendantes (sensible)
   - `--min-lineages 3` : ≥3 lignées (défaut, plus spécifique)
   - `--min-lineages 5` : ≥5 lignées (très conservateur)

## Phase 2 : Extraction des données

### Marqueurs par lignée

```sql
-- SPDIs définissant chaque lignée (mv_lineage_markers : PAS de `marker_type`, `lineage`, `gene` ni `effect` ;
-- colonnes réelles = lineage_code, spdi_variant_name, spdi_variant_position ; le gène s'obtient par jointure)
SELECT m.lineage_code, m.spdi_variant_name,
       a.locus_tag, a.annotation_type
FROM mv_lineage_markers m
LEFT JOIN tb_report_spdi_annotations a ON a.spdi_variant_name = m.spdi_variant_name
WHERE m.lineage_code IN ('Bovis', 'Caprae', 'Orygis', '6', '9')   -- codes réels, pas 'M. bovis'
ORDER BY a.locus_tag, m.lineage_code;
```

### Mutations protéiques par lignée

> ⚠ **`mv_protein_position_mutations` n'est PAS peuplée** côté serveur (vérifié 2026-07-31) et elle est
> **agrégée** (pas de `strain_id`) : impossible d'y joindre des souches. Route valide :
> `tb_report_spdi_annotations` → `tb_report_spdi` → `tb_report_strain_spdi`. Les gènes y sont des
> **locus_tag `Rv####`** (pas de noms `PE`/`PPE`) : pour cibler PE/PPE, fournir la LISTE des Rv concernés
> (depuis l'atlas `annotation_mtbc`, catégorie fonctionnelle PE/PPE, ou via `mtbc-gene`), pas un `LIKE 'PE%'`.
> Champs : `hgvs_p`, `annotation_type` (missense_variant…), `impact` (LOW/MODERATE/HIGH).

```sql
-- Mutations protéiques d'un ensemble de gènes (ex. PE/PPE) ventilées par lignée
-- Coût élevé (426M lignes dans tb_report_strain_spdi) : restreindre la liste de locus_tag.
SELECT a.locus_tag, a.hgvs_p, a.annotation_type,
       c.lineage_code,
       COUNT(DISTINCT ss.strain_id) AS n_strains
FROM tb_report_spdi_annotations a
JOIN tb_report_spdi s           ON s.spdi_variant_name = a.spdi_variant_name
JOIN tb_report_strain_spdi ss   ON ss.spdi_id = s.spdi_id
JOIN mv_strain_classification c ON c.strain_id = ss.strain_id
WHERE c.system_name = 'guyeux'
  AND a.locus_tag IN ('Rv0442c', 'Rv1806', 'Rv3018c')   -- remplacer par la liste PE/PPE voulue
  AND a.annotation_type = 'missense_variant'
GROUP BY a.locus_tag, a.hgvs_p, a.annotation_type, c.lineage_code
HAVING COUNT(DISTINCT ss.strain_id) >= 10
ORDER BY a.locus_tag, c.lineage_code;
```

### Fréquence des SPDIs par lignée

```sql
-- Fréquence d'un SPDI dans chaque lignée majeure
SELECT c.lineage_code as lineage,
       COUNT(DISTINCT ss.strain_id) as n_with_spdi,
       (SELECT COUNT(DISTINCT strain_id) FROM mv_strain_classification
        WHERE system_name = 'guyeux' AND lineage_code = c.lineage_code) as n_total,
       ROUND(100.0 * COUNT(DISTINCT ss.strain_id) /
         (SELECT COUNT(DISTINCT strain_id) FROM mv_strain_classification
          WHERE system_name = 'guyeux' AND lineage_code = c.lineage_code), 2) as freq_pct
FROM tb_report_strain_spdi ss
JOIN mv_strain_classification c ON ss.strain_id = c.strain_id
WHERE c.system_name = 'guyeux'
  AND ss.spdi_id = 'NC_000962.3:761155:T:C'  -- exemple : rpoB S450L
GROUP BY c.lineage_code
ORDER BY freq_pct DESC;
```

## Phase 3 : Analyse de convergence

### Algorithme

1. **Pour chaque gène** : lister les lignées où il porte au moins une mutation non-synonyme à haute fréquence (>50% des souches de la lignée)
2. **Compter les lignées indépendantes** : utiliser la topologie MTBC pour vérifier que les lignées ne sont pas directement apparentées
3. **Score de convergence** : nombre de lignées indépendantes × diversité des mutations
4. **Enrichissement** : test hypergéométrique (ou Fisher) pour les familles de gènes

### Topologie MTBC pour l'indépendance

```
Canettii (outgroup)
├── Clade humain strict
│   ├── L1 (Indo-Oceanic)
│   ├── L7 (Ethiopian)
│   ├── L2 (East Asian)
│   ├── L3 (East African Indian)
│   └── L4 (Euro-American)
└── Grand clade
    ├── L5 (M. africanum I) — basale
    ├── Clade animal 1
    │   ├── M. bovis
    │   ├── M. caprae
    │   └── M. orygis
    ├── Clade animal 2
    │   ├── M. suricattae
    │   ├── Dassie bacillus
    │   └── M. mungi
    └── L6/L9/L10 (secondairement humains)
```

**Lignées indépendantes** = lignées dans des clades différents. Ex. M. bovis et M. suricattae sont dans deux clades animaux distincts → mutations partagées = convergence.

### Enrichissement par famille de gènes

Test de Fisher exact :

| | Convergent | Non-convergent |
|---|---|---|
| PE/PPE | a | b |
| Autres gènes | c | d |

p-value = Fisher(a, b, c, d). Odds ratio = (a×d)/(b×c).

## Phase 4 : Sortie

### CSV des gènes convergents

```csv
gene,gene_family,n_independent_lineages,lineages,mutations,convergence_score
PE35,PE,5,"L1,L4,M.bovis,M.caprae,L6","E99*,G45D,A12V",15
rpoB,core,4,"L2,L4,M.bovis,L6","S450L,H445Y,D435V",12
```

### Résumé JSON

```json
{
  "n_genes_analyzed": 4000,
  "n_convergent_genes": 333,
  "min_lineages_threshold": 3,
  "enrichment": {
    "PE_PPE": {"n_convergent": 45, "n_total": 169, "odds_ratio": 2.8, "p_value": 0.001},
    "ESX": {"n_convergent": 12, "n_total": 23, "odds_ratio": 3.1, "p_value": 0.003},
    "PKS_PDIM": {"n_convergent": 8, "n_total": 15, "odds_ratio": 2.5, "p_value": 0.01}
  },
  "top_convergent_genes": [...]
}
```

### Figure : heatmap de convergence

Matrice gènes (lignes, top 50) × lignées (colonnes), colorée par :
- Présence d'une mutation non-synonyme (oui/non)
- Ou fréquence de la mutation dans la lignée (gradient)

Annotée par famille de gènes (PE/PPE en violet, ESX en bleu, etc.).

## Interprétation

| Pattern | Interprétation |
|---------|----------------|
| Même position, même mutation dans ≥3 lignées | Forte convergence → probable sélection positive |
| Même gène, mutations différentes | Convergence fonctionnelle → gène sous pression |
| Famille enrichie (PE/PPE) | Adaptation hôte-spécifique systémique |
| Gene frameshift dans toutes les animales | Perte de fonction convergente → gène dispensable chez l'hôte animal |

## Intégration

| Skill | Usage |
|-------|-------|
| `tbannotator-mcp` | Source des données de mutations et classifications |
| `pangenome-enrichment` | Enrichissement KEGG des gènes convergents |
| `lineage-comparison` | Tests statistiques sur les fréquences de mutations |
| `itol` | Annoter les branches de la phylogénie par mutations convergentes |
| `tbmonitor-papers` | Vérifier si un gène convergent candidat a déjà été rapporté dans la littérature (et citer ces travaux dans la discussion) : ~190k résumés PubMed TB, SQL sub-seconde |

## Dépendances

```bash
pip install pandas numpy scipy matplotlib seaborn
```

## Codex packaging note

This packaged copy targets Codex. MCP tool names in `allowed-tools` are prerequisites: verify them with `codex mcp list` in the active profile before relying on live queries.
