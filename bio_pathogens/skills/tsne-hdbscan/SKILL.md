---
name: tsne-hdbscan
description: >-
  t-SNE dimensionality reduction + HDBSCAN density-based clustering for MTBC
  genomic diversity. Input: SPDI presence/absence matrices, SNP distance
  matrices, or MIRU-VNTR profiles.

  Use when: exploring population structure, identifying transmission clusters,
  detecting outliers or misclassified lineages, 2D visualisation, unsupervised
  clustering without fixing the number of clusters.
argument-hint: "<input_file> [-g lineage] [-o results.csv] [-p plot.png]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres
---

# t-SNE + HDBSCAN : Exploration génomique MTBC

Réduction de dimension (t-SNE) et clustering par densité (HDBSCAN) pour explorer la diversité génomique de *M. tuberculosis complex*. Produit des visualisations 2D colorées par lignée et identifie automatiquement les clusters naturels sans spécifier leur nombre.

## Quand utiliser

- **Explorer la structure populationnelle** d'une collection de souches
- **Détecter des clusters de transmission** récents (souches très proches)
- **Identifier des outliers** ou des souches mal classifiées
- **Comparer la classification HDBSCAN vs classification par lignée** (cross-tabulation)
- **Visualiser** la diversité génomique pour un article ou une présentation
- **Compléter le THD** : le THD quantifie le succès épidémique par isolat, t-SNE+HDBSCAN visualise la structure globale

## Arguments

```
tsne_hdbscan.py <input_file> [options]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `input_file` | (requis) | CSV : matrice de features, de distances, ou binaire |
| `-f`, `--format` | `auto` | `distance_matrix`, `binary_matrix`, `haplotype_matrix` |
| `-g`, `--group-column` | none | Colonne pour colorer par groupe (ex. `lineage`) |
| `--metric` | `hamming` | Distance : `hamming`, `jaccard`, `euclidean` |

### t-SNE

| Argument | Default | Description |
|----------|---------|-------------|
| `--perplexity` | `30` | Balance local/global (5-50). Auto-ajusté si n est petit |
| `--learning-rate` | `200` | Vitesse d'optimisation (10-1000) |
| `--n-iter` | `1000` | Nombre d'itérations (≥250) |
| `--seed` | `42` | Graine aléatoire (reproductibilité) |

### HDBSCAN

| Argument | Default | Description |
|----------|---------|-------------|
| `--min-cluster-size` | `5` | Taille minimale d'un cluster. Auto-ajusté si n petit |
| `--min-samples` | auto | Densité minimale. Plus grand = plus conservateur |
| `--cluster-on` | `embedding` | `embedding` (2D t-SNE) ou `original` (données complètes) |
| `--cluster-method` | `eom` | `eom` (Excess of Mass) ou `leaf` (feuilles du dendrogramme) |
| `--epsilon` | `0` | Fusionne les clusters à distance < epsilon |
| `--allow-single` | off | Autoriser un seul cluster (sinon → tout est bruit) |

### Sortie

| Argument | Default | Description |
|----------|---------|-------------|
| `-o`, `--output` | none | CSV de résultats |
| `-p`, `--plot` | none | Figure PNG/PDF |
| `--title` | auto | Titre du plot |
| `--show-labels` | off | Afficher les IDs sur le plot (≤100 souches) |
| `--lineage-colors` | none | JSON `{lineage: "#hex"}` pour couleurs personnalisées |

## Formats d'entrée

### 1. Matrice binaire (SPDI présence/absence) : RECOMMANDÉ pour WGS

```csv
strain_id,lineage,SPDI_001,SPDI_002,SPDI_003,...
ERR551415,L4.7,1,0,1,...
SRR33638270,L4.8,1,1,0,...
```

Métrique recommandée : `jaccard` (meilleur que Hamming pour matrices creuses).

### 2. Matrice de distances pré-calculée

```csv
id,ERR551415,SRR33638270,DRR261083
ERR551415,0,42,187
SRR33638270,42,0,195
DRR261083,187,195,0
```

Le `--metric` est ignoré (distance précomputed).

### 3. Matrice d'haplotypes (MIRU-VNTR)

```csv
id,lineage,MIRU02,MIRU04,MIRU10,...
ERR123,L4.1,2,3,4,...
ERR456,L4.2,2,3,5,...
```

Métrique recommandée : `hamming`.

## Exemples d'utilisation

```bash
# Matrice SPDI binaire, coloré par lignée
python3 scripts/tsne_hdbscan.py spdi_matrix.csv -g lineage -o results.csv -p plot.png

# Matrice de distances SNP, perplexité ajustée
python3 scripts/tsne_hdbscan.py snp_distances.csv -f distance_matrix \
  --perplexity 50 --min-cluster-size 10 -o results.csv -p plot.png

# MIRU-VNTR, clustering sur données originales (pas l'embedding)
python3 scripts/tsne_hdbscan.py miru.csv --metric hamming \
  --cluster-on original --min-cluster-size 8 -p plot.png

# Avec couleurs MTBC personnalisées
python3 scripts/tsne_hdbscan.py data.csv -g lineage \
  --lineage-colors mtbc_colors.json -p figure.png --title "L4 population structure"
```

## Sortie

### CSV

| Colonne | Description |
|---------|-------------|
| `strain_id` | Identifiant de la souche |
| `group` | Groupe/lignée (si `--group-column`) |
| `tsne_1` | Coordonnée t-SNE axe 1 |
| `tsne_2` | Coordonnée t-SNE axe 2 |
| `cluster` | Cluster HDBSCAN (-1 = bruit/outlier) |
| `cluster_probability` | Probabilité d'appartenance au cluster (0-1) |
| `outlier_score` | Score d'outlier GLOSH (plus grand = plus isolé) |

### Résumé JSON (stdout)

```json
{
  "n_samples": 500,
  "hdbscan": {
    "n_clusters": 8,
    "noise_count": 23,
    "noise_ratio": 0.046,
    "silhouette_score": 0.67,
    "cluster_sizes": {"0": 125, "1": 89, ...}
  },
  "crosstab_cluster_vs_group": {
    "cluster_0": {"L4.7": 120, "L4.8": 5},
    "cluster_1": {"L4.8": 85, "L4.7": 4},
    "noise": {"L4.7": 15, "Unknown": 8}
  }
}
```

### Figure

Deux panneaux côte à côte :
- **Gauche** : points colorés par cluster HDBSCAN (bruit en gris)
- **Droite** : mêmes points colorés par lignée/groupe

## Guide des paramètres

### t-SNE : choisir la perplexité

| n (souches) | Perplexité recommandée | Explication |
|-------------|----------------------|-------------|
| < 50 | 5-10 | Peu de données, focus local |
| 50-500 | 15-30 | Bon défaut |
| 500-5000 | 30-50 | Plus de structure globale |
| > 5000 | 50-100 | Augmenter aussi n_iter |

**Règle** : perplexité < n/3. Le script ajuste automatiquement si nécessaire.

### HDBSCAN : choisir min_cluster_size

| Objectif | min_cluster_size | min_samples | Effet |
|----------|-----------------|-------------|-------|
| Clusters de transmission (proches) | 3-5 | 2-3 | Sensible, petits clusters |
| Lignées/sous-lignées | 10-20 | 5-10 | Modéré |
| Groupes majeurs | 20-50 | 10-20 | Conservateur, grands clusters |
| Détection d'outliers | 5 | 1 | Focus sur les points isolés |

### Cluster sur embedding vs original ?

| `--cluster-on` | Avantages | Inconvénients |
|----------------|-----------|---------------|
| `embedding` | Cohérent avec la visualisation, rapide | t-SNE peut distordre les distances |
| `original` | Distances fidèles | Peut ne pas correspondre au plot 2D |

**Recommandation** : `embedding` par défaut. Utiliser `original` quand les distances sont fiables (matrice SNP pré-calculée).

## Intégration TBannotator

### Construire une matrice SPDI depuis TBannotator

```sql
-- Étape 1 : Récupérer les SPDIs pour une lignée
SELECT ss.strain_id, ss.spdi_id
FROM tb_report_strain_spdi ss
JOIN mv_strain_classification c ON ss.strain_id = c.strain_id
WHERE c.system_name = 'guyeux' AND c.lineage_code LIKE '4.%'
ORDER BY ss.strain_id, ss.spdi_id;
```

Puis en Python, pivoter en matrice binaire :
```python
import pandas as pd

# Depuis le résultat SQL
df = pd.read_csv("spdi_query_result.csv")
matrix = df.pivot_table(index="strain_id", columns="spdi_id", aggfunc="size", fill_value=0)
matrix = (matrix > 0).astype(int)
matrix.to_csv("spdi_matrix.csv")
```

### Ajouter les classifications de lignée

> ⚠ **`strain_id` est un ENTIER** (clé interne) ; les accessions SRA/ENA sont dans **`strain_name`**.
> Filtrer une liste d'accessions par `strain_id` ne renvoie rien.

```sql
SELECT strain_id, strain_name, lineage_code AS lineage
FROM mv_strain_classification
WHERE system_name = 'guyeux' AND strain_name IN ('ERR551415', 'SRR33638270');
```

Joindre au CSV pour colorer par lignée avec `--group-column lineage`.

### Matrice de distances SNP depuis TBannotator

```sql
-- Distances aux souches de référence (limité à 10 refs)
SELECT * FROM mv_strain_reference_snp_distance
WHERE strain_name IN ('ERR551415', 'SRR33638270');
```

Note : cette vue ne contient que les distances à 10 références, pas les distances pairwise complètes. Pour les distances complètes, calculer depuis la matrice SPDI.

## Intégration avec d'autres skills

| Skill | Usage combiné |
|-------|--------------|
| `thd` | Calculer THD par isolat, puis superposer comme gradient sur le t-SNE |
| `itol` | Exporter les clusters comme annotation colorée sur l'arbre phylogénétique |
| `tbannotator-mcp` | Requêter les SPDIs, classifications et métadonnées |
| `tb-cli` | Recherche rapide de lignées pour construire l'input |

### Workflow typique : article de caractérisation de lignée

1. **Requêter TBannotator** : récupérer SPDIs pour la lignée d'intérêt + contexte
2. **t-SNE + HDBSCAN** : explorer la structure populationnelle, identifier les sous-groupes
3. **THD** : quantifier le succès épidémique de chaque sous-groupe
4. **iTOL** : produire l'arbre phylogénétique annoté avec couleurs par cluster/lignée
5. **Interpréter** : les clusters HDBSCAN correspondent-ils aux sous-lignées connues ? Y a-t-il des sous-groupes non décrits ?

## Interprétation des résultats

### Lecture du plot t-SNE
- **Groupes serrés** : souches génétiquement très proches (potentiel cluster de transmission)
- **Groupes éloignés** : lignées ou sous-lignées distinctes
- **Points isolés (bruit HDBSCAN)** : outliers, souches recombinantes, ou erreurs de séquençage
- **Attention** : les distances dans t-SNE ne sont PAS proportionnelles aux vraies distances génétiques. Seule la topologie (voisinage) est informative.

### Cross-tabulation clusters vs lignées
- **1 cluster = 1 lignée** : classification cohérente
- **1 cluster = plusieurs lignées** : sous-lignées très proches, ou frontière floue
- **1 lignée = plusieurs clusters** : sous-structure non capturée par la classification actuelle → potentielle nouvelle sous-lignée
- **Bruit concentré dans une lignée** : lignée très diverse ou avec beaucoup d'outliers

> **Garde-fou avant de conclure à une sous-lignée non décrite** : un cluster HDBSCAN qui scinde une lignée en deux n'est pas forcément nouveau. Avant d'annoncer une découverte, vérifier qu'il n'est pas DÉJÀ formalisé dans `bdd/actuelle/` (le cycle multi-signal a pu le créer entre-temps), sinon faux positif de découverte.
>
> **Source de vérité (cf. `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`)** : dans TBannotator, `system_name='guyeux'` EST le système maison (= moi/Guyeux), mais c'est un **snapshot** susceptible d'être en retard sur la taxonomie vivante. Pour tout clade récent du cycle multi-signal (L1.\*, Bovis1.\*, BCG.\*, L6 profond), recouper le label avec `bdd/actuelle/` + `barcoding_v2/barcode_complete.tsv`. Ne jamais lire `snp_barcoding.csv` (v1 obsolète) ni `strain_lineages.csv` (périmé) comme référence taxonomique.

### Score de silhouette
- **> 0.7** : clusters bien séparés
- **0.5-0.7** : structure raisonnable
- **0.25-0.5** : clusters chevauchants
- **< 0.25** : pas de structure claire

## Dépendances

```bash
pip install numpy scipy scikit-learn hdbscan matplotlib pandas
```

## Palette MTBC (fichier JSON pour --lineage-colors)

```json
{
  "L1": "#F5A623", "L2": "#D0021B", "L3": "#4A90D9",
  "L4": "#E03D31", "L5": "#7B2D8E", "L6": "#9B59B6",
  "L7": "#B8860B", "L8": "#1B9AAA", "L9": "#2D6A4F",
  "L10": "#52B788", "M. bovis": "#3D2B1F", "Unknown": "#9E9E9E"
}
```

Sauvegarder dans `mtbc_colors.json` et passer via `--lineage-colors mtbc_colors.json`.
