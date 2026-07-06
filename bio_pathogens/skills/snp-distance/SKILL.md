---
name: snp-distance
description: >-
  Academic research toolkit for the Guyeux group (FEMTO-ST, University of Franche-Comte). Computes pairwise SNP distances on published-research MTBC isolates for peer-reviewed publications. Compute pairwise SNP distance matrices from SPDI presence/absence data.
  Queries TBannotator for SPDI profiles, builds Hamming/Jaccard distance matrix.

  Use when: computing genetic distances between MTBC strains, preparing input
  for t-SNE+HDBSCAN or THD, identifying transmission clusters by SNP threshold,
  building distance matrices for NJ trees or population genetics analyses.
argument-hint: "<input_csv or lineage> [-o distances.csv] [--metric hamming|jaccard|snp_count]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres
---

# SNP Distance — Matrice de distances pairwise MTBC

Calcul de matrices de distances SNP pairwise à partir de données SPDI binaires. Produit des matrices symétriques prêtes pour t-SNE+HDBSCAN, THD, arbres NJ, ou identification de clusters de transmission.

## Quand utiliser

- **Préparer l'input pour t-SNE+HDBSCAN** : matrice de distances → `--format distance_matrix`
- **Préparer l'input pour THD** : matrice de distances (alternative à la matrice d'haplotypes)
- **Identifier des clusters de transmission** : seuil ≤12 SNPs entre souches récemment transmises
- **Comparer des souches** : distance génétique entre deux souches ou groupes
- **Construire un arbre NJ local** : matrice de distances → `scipy` ou `Bio.Phylo`

## Arguments

```
snp_distance.py <input_file> [options]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `input_file` | (requis) | CSV : matrice SPDI binaire ou liste strain_id/spdi_id |
| `-o`, `--output` | stdout | Fichier CSV de sortie (matrice de distances) |
| `--metric` | `snp_count` | `snp_count` (nombre absolu), `hamming` (proportion), `jaccard` |
| `--threshold` | none | Seuil pour identifier les clusters (ex. `12` pour transmission récente) |
| `--clusters-output` | none | CSV des clusters identifiés par le seuil |
| `--summary` | off | Afficher un résumé JSON sur stdout |

## Formats d'entrée

### 1. Matrice SPDI binaire (pivot) — RECOMMANDÉ

```csv
strain_id,SPDI_001,SPDI_002,SPDI_003,...
ERR551415,1,0,1,...
SRR33638270,1,1,0,...
DRR261083,0,1,1,...
```

Chaque colonne = un SPDI, chaque cellule = 1 (présent) ou 0 (absent).

### 2. Liste longue strain_id / spdi_id

```csv
strain_id,spdi_id
ERR551415,SPDI_001
ERR551415,SPDI_003
SRR33638270,SPDI_001
SRR33638270,SPDI_002
```

Le script pivote automatiquement en matrice binaire.

## Métriques

| Métrique | Formule | Usage |
|----------|---------|-------|
| `snp_count` | Nombre de positions différentes | **Défaut**. Distances en nombre absolu de SNPs. Standard MTBC. |
| `hamming` | Positions différentes / total positions | Proportion (0-1). Pour THD et comparaisons normalisées. |
| `jaccard` | 1 - (intersection / union) | Meilleur pour matrices très creuses. |

## Sortie

### Matrice de distances CSV

```csv
id,ERR551415,SRR33638270,DRR261083
ERR551415,0,42,187
SRR33638270,42,0,195
DRR261083,187,195,0
```

Matrice symétrique avec diagonale à 0. Compatible avec :
- `tsne_hdbscan.py -f distance_matrix`
- `thd_compute.py` (en mode matrice de distances)
- `tool_build_nj_tree` (après conversion)

### Clusters de transmission (si `--threshold`)

```csv
cluster_id,strain_id,cluster_size,max_distance
0,ERR551415,3,8
0,SRR33638270,3,8
0,DRR261083,3,8
1,ERR789012,2,5
1,ERR789013,2,5
```

### Résumé JSON (si `--summary`)

```json
{
  "n_strains": 500,
  "n_spdis": 12345,
  "metric": "snp_count",
  "distance_stats": {
    "min": 1,
    "max": 2340,
    "mean": 567.3,
    "median": 512.0,
    "q25": 234.0,
    "q75": 890.0
  },
  "transmission_clusters": {
    "threshold": 12,
    "n_clusters": 15,
    "n_clustered_strains": 67,
    "n_singletons": 433,
    "largest_cluster": 8
  }
}
```

## Exemples d'utilisation

```bash
# Matrice SPDI binaire → distances SNP count
python3 scripts/snp_distance.py spdi_matrix.csv -o distances.csv --summary

# Avec identification de clusters de transmission (≤12 SNPs)
python3 scripts/snp_distance.py spdi_matrix.csv -o distances.csv \
  --threshold 12 --clusters-output clusters.csv

# Distance Jaccard pour données creuses
python3 scripts/snp_distance.py spdi_matrix.csv -o distances.csv --metric jaccard

# Liste longue → matrice (pivot automatique)
python3 scripts/snp_distance.py strain_spdi_long.csv -o distances.csv
```

## Intégration TBannotator

### Construire la matrice SPDI depuis TBannotator

```sql
-- Étape 1 : Récupérer les paires strain/SPDI
SELECT ss.strain_id, ss.spdi_id
FROM tb_report_strain_spdi ss
WHERE ss.strain_id IN (
  SELECT sra_id FROM mv_strain_classification
  WHERE system = 'Senelle' AND lineage_code LIKE '4.15%'
)
ORDER BY ss.strain_id, ss.spdi_id;
```

Sauvegarder le résultat en CSV, puis :

```bash
python3 scripts/snp_distance.py strain_spdi.csv -o distances.csv --summary
```

Le script détecte automatiquement le format (liste longue vs matrice) et pivote si nécessaire.

### Distances aux références (vue pré-calculée)

```sql
-- Distances SNP aux 10 souches de référence
SELECT sra_id, ref_strain_id, snp_distance
FROM mv_strain_reference_snp_distance
WHERE sra_id IN ('ERR551415', 'SRR33638270');
```

**Note** : cette vue ne contient que les distances à 10 références, pas les distances pairwise complètes. Pour les distances pairwise, utiliser le script `snp_distance.py`.

## Seuils MTBC de référence

| Seuil SNP | Interprétation |
|-----------|---------------|
| 0-5 | Transmission directe très probable |
| 6-12 | Cluster de transmission récent |
| 13-50 | Même sous-lignée, transmission possible |
| 50-200 | Même lignée, pas de transmission récente |
| > 200 | Lignées différentes |

Ces seuils sont indicatifs et dépendent du taux de mutation estimé (~0.5 SNP/génome/an pour MTBC).

## Intégration avec d'autres skills

| Skill | Usage combiné |
|-------|--------------|
| `tsne-hdbscan` | `snp_distance.py` → matrice → `tsne_hdbscan.py -f distance_matrix` |
| `thd` | `snp_distance.py --metric hamming` → matrice → `thd_compute.py` |
| `raxml` | Validation : comparer distances SNP avec longueurs de branches |
| `itol` | Annoter l'arbre avec les clusters de transmission identifiés |

## Dépendances

```bash
pip install numpy scipy pandas
```
