---
name: pangenome-enrichment
description: >-
  Pangenome analysis and functional enrichment by MTBC lineage.
  Core/soft-core/shell/cloud gene classification, KEGG pathway enrichment,
  lineage-specific gene content analysis.

  Use when: comparing gene content between lineages, identifying lineage-specific
  genes, performing KEGG enrichment on differential genes, analyzing pangenome
  structure for an article.
argument-hint: "<gene_matrix.csv or lineage> [--enrichment kegg] [--compare L4.15,L4.14]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres
---

# Pangenome Enrichment — Analyse du pangénome MTBC

Classification des gènes en core/soft-core/shell/cloud par lignée MTBC, enrichissement fonctionnel KEGG, et comparaison du contenu génique entre lignées.

## Concepts

### Classification des gènes

| Catégorie | Définition | Seuil | Interprétation MTBC |
|-----------|-----------|-------|---------------------|
| **Core** | Présent dans ≥99% des souches | ≥0.99 | Gènes essentiels, conservés |
| **Soft-core** | Présent dans 95-99% | 0.95-0.99 | Quasi-universels, quelques pertes |
| **Shell** | Présent dans 15-95% | 0.15-0.95 | Variables, souvent lignée-spécifiques |
| **Cloud** | Présent dans <15% | <0.15 | Rares, souvent acquis ou artefacts |

### MTBC vs autres bactéries

Le MTBC a un pangénome très fermé (peu de transfert horizontal). Les variations de contenu génique sont principalement dues à :
- **Régions de délétion (RD)** : grandes délétions lignée-spécifiques
- **Frameshifts** : pseudogénisation par mutations décalantes
- **PE/PPE** : famille très variable en nombre de copies et intégrité

## Phase 1 : Découverte (OBLIGATOIRE)

1. **Quelles lignées comparer ?**
   - Humaines vs animales
   - Sous-lignées d'une lignée majeure (ex. L4.15 vs L4.14)
   - Toutes les lignées majeures (vue d'ensemble)

2. **Source des données ?**
   - Matrice de gènes (CSV : strain_id × gene → 0/1)
   - Données SPDI depuis TBannotator (frameshifts, stop gains)
   - Régions de délétion (RD) depuis la littérature

3. **Type d'enrichissement ?**
   - **KEGG pathways** : voies métaboliques sur/sous-représentées
   - **Gene families** : PE/PPE, ESX, mce, lipid metabolism
   - **COG categories** : catégories fonctionnelles
   - Combinaison

## Phase 2 : Extraction des données

> **Source de vérité (cf. `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`)** : dans TBannotator, `system='Senelle'` EST le système maison (= moi/Guyeux), mais c'est un **snapshot** susceptible d'être en retard sur la taxonomie vivante. Pour tout clade récent du cycle multi-signal (L1.\*, Bovis1.\*, BCG.\*, L6 profond), recouper le label avec `bdd/actuelle/` + `barcoding_v2/barcode_complete.tsv`. Ne jamais lire `snp_barcoding.csv` (v1 obsolète) ni `strain_lineages.csv` (périmé) comme référence taxonomique.

### Gènes altérés (frameshifts/stops) par lignée depuis TBannotator

```sql
-- Gènes avec frameshifts lignée-spécifiques
SELECT p.gene, p.effect, c.lineage_code,
       COUNT(DISTINCT p.sra_id) as n_strains,
       (SELECT COUNT(DISTINCT sra_id) FROM mv_strain_classification
        WHERE system = 'Senelle' AND lineage_code = c.lineage_code) as n_total
FROM mv_protein_position_mutations p
JOIN mv_strain_classification c ON p.sra_id = c.sra_id
WHERE c.system = 'Senelle'
  AND p.effect IN ('frameshift_variant', 'stop_gained')
GROUP BY p.gene, p.effect, c.lineage_code
HAVING COUNT(DISTINCT p.sra_id) >= 10
ORDER BY n_strains DESC;
```

### Fréquence de pseudogénisation par gène

```sql
-- Proportion de souches avec gène pseudogénisé, par lignée
SELECT p.gene,
       c.lineage_code,
       COUNT(DISTINCT p.sra_id) as n_pseudogenized,
       ROUND(100.0 * COUNT(DISTINCT p.sra_id) /
         (SELECT COUNT(DISTINCT sra_id) FROM mv_strain_classification
          WHERE system = 'Senelle' AND lineage_code = c.lineage_code), 2) as pct
FROM mv_protein_position_mutations p
JOIN mv_strain_classification c ON p.sra_id = c.sra_id
WHERE c.system = 'Senelle'
  AND p.effect IN ('frameshift_variant', 'stop_gained')
GROUP BY p.gene, c.lineage_code
HAVING COUNT(DISTINCT p.sra_id) >=
  0.5 * (SELECT COUNT(DISTINCT sra_id) FROM mv_strain_classification
         WHERE system = 'Senelle' AND lineage_code = c.lineage_code)
ORDER BY p.gene, c.lineage_code;
```

### Diversité fonctionnelle par gène

```sql
-- Shannon/Simpson diversity of mutations per gene
SELECT gene, shannon_diversity, simpson_diversity,
       n_variants, n_strains
FROM mv_protein_effect_diversity
WHERE n_variants >= 5
ORDER BY shannon_diversity DESC
LIMIT 50;
```

## Phase 3 : Classification pangenome

### Script

```bash
python3 scripts/pangenome_enrichment.py gene_presence.csv \
  --group-column lineage --thresholds 0.99,0.95,0.15 \
  -o pangenome_classification.csv --summary
```

### Algorithme

Pour chaque gène et chaque groupe :
1. Calculer la fréquence (proportion de souches ayant le gène fonctionnel)
2. Classifier selon les seuils : core ≥ 99%, soft-core 95-99%, shell 15-95%, cloud < 15%
3. Identifier les gènes **différentiellement présents** entre groupes (Fisher exact)

## Phase 4 : Enrichissement KEGG

### API KEGG

```
GET https://rest.kegg.jp/link/pathway/mtu:{gene_name}
GET https://rest.kegg.jp/get/pathway:mtu00010
```

**Important** : respecter le rate limiting (0.5s entre requêtes). Utiliser un cache local.

### Test d'enrichissement

Pour chaque pathway KEGG :

| | Dans le set différentiel | Hors du set |
|---|---|---|
| Dans le pathway | a | b |
| Hors du pathway | c | d |

Test de Fisher exact. Correction FDR Benjamini-Hochberg sur l'ensemble des pathways testés.

### Pathways MTBC d'intérêt

| Pathway | ID KEGG | Pertinence MTBC |
|---------|---------|-----------------|
| Fatty acid metabolism | mtu00071 | Lipides de paroi, virulence |
| Biosynthesis of PDIM/PGL | — | Virulence, spécifique mycobactéries |
| Two-component systems | mtu02020 | Régulation adaptation environnement |
| ABC transporters | mtu02010 | Import/export, résistance |
| Beta-oxidation | mtu00071 | Source de carbone in vivo |
| Amino acid metabolism | mtu00250-00350 | Auxotrophies lignée-spécifiques |

## Phase 5 : Sortie

### CSV de classification

```csv
gene,overall_category,freq_L4.15,cat_L4.15,freq_L4.14,cat_L4.14,freq_M.bovis,cat_M.bovis,differential,p_value,p_adjusted
Rv0001,core,1.0,core,1.0,core,1.0,core,no,,
PE35,shell,0.85,shell,0.92,shell,0.45,shell,yes,0.001,0.01
pncA,soft-core,0.98,soft-core,0.97,soft-core,0.12,cloud,yes,<0.001,<0.001
```

### Résumé JSON

```json
{
  "n_genes": 4000,
  "pangenome_by_group": {
    "L4.15": {"core": 3650, "soft_core": 120, "shell": 180, "cloud": 50},
    "M.bovis": {"core": 3580, "soft_core": 100, "shell": 220, "cloud": 100}
  },
  "n_differential": 85,
  "kegg_enrichment": {
    "mtu00071": {"name": "Fatty acid degradation", "p_adjusted": 0.003, "genes": 8},
    "mtu02020": {"name": "Two-component system", "p_adjusted": 0.01, "genes": 5}
  }
}
```

### Figure : heatmap du pangénome

Matrice gènes différentiels (lignes) × lignées (colonnes), colorée par fréquence (0-1). Annoté par :
- Catégorie fonctionnelle (COG) en marge gauche
- Pathway KEGG enrichi en marge droite
- Dendrogramme de clustering sur les lignes

## Régions de délétion (RD) connues

| RD | Lignées | Gènes affectés | Impact |
|----|---------|-----------------|--------|
| RD1 | M. bovis BCG | esxA, esxB | Perte de virulence (BCG) |
| RD4 | M. bovis | Rv1508-1514 | Marqueur M. bovis |
| RD7 | L5, L6 | Rv1572-1587 | Marqueur M. africanum |
| RD9 | L5, L6, animales | Rv2073-2083 | Marqueur grand clade |
| RD10 | M. bovis, M. caprae | Rv3478-3487 | Spécifique animal clade 1 |
| RD12 | M. canettii absent | — | Marqueur MTBC vs canettii |
| TbD1 | L2, L3, L4 | mmpS6, mmpL6 | "Modern" lineages |

## Intégration

| Skill | Usage |
|-------|-------|
| `tbannotator-mcp` | Source des mutations, classifications |
| `convergent-evolution` | Identifier la convergence dans les gènes du pangénome |
| `lineage-comparison` | Tests statistiques pour les gènes différentiels |
| `create-viz` | Heatmaps et figures personnalisées |

## Dépendances

```bash
pip install pandas numpy scipy matplotlib seaborn requests
```

**KEGG API** : pas d'installation, REST pur. Respecter rate limiting 0.5s.
