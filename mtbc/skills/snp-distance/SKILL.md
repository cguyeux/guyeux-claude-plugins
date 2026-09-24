---
name: snp-distance
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST) for peer-reviewed
  publications: pairwise SNP distance matrices for MTBC isolates from SPDI
  presence/absence data (TBannotator), metrics snp_count / hamming / jaccard.

  Use when: computing genetic distances between MTBC strains, preparing input
  for t-SNE+HDBSCAN or THD, identifying transmission clusters by SNP threshold,
  building distance matrices for NJ trees or population genetics.

  Scope: developed on the MTBC, applies to any clonal bacterial pathogen
  (Yersinia, Leptospira...) — the metrics operate on any strain x variant
  presence/absence matrix, whatever the reference genome.
argument-hint: "<input_csv or lineage> [-o distances.csv] [--metric hamming|jaccard|snp_count]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres
---

> [!WARNING]
> **[2026-09-08] TABLES ABSENTES du serveur tblearn.** Ce skill interroge 1 objet(s) qui
> n'existent plus depuis le remplacement du MCP TBannotator. Contrairement au filtre `system_name`,
> ces requêtes ne rendent pas un ensemble vide : elles **lèvent une erreur** `relation does not exist`.
>
> | table citée ici | remplacer par | fondement |
> |---|---|---|
> | `mv_strain_reference_snp_distance` | **la colonne snp_count de mv_strain_lineage ou tb_report_strain** | commentaire du schéma : « Distance to the H37Rv reference, in number of SNPs » |
>
> Correspondances établies en comparant les colonnes, pas devinées. Détail et schéma complet :
> `~/.agents/knowledge/tblearn-migration.md`.


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
> B=~/docs/environnement/plugins/mtbc/skills/bdd-bridge/scripts
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


# SNP Distance : Matrice de distances pairwise MTBC

> [!TIP]
> **Alternative pan-génome, pour les clusters de transmission.** Ce skill compare sur une référence
> unique, donc il est aveugle à ce qui est absent de H37Rv. **PANPASCO** (Jaenicke et al., *PLoS Comput
> Biol* 2020, `10.1371/journal.pcbi.1007527`, `gitlab.com/rki_bioinformatics/panpasco`) calcule des
> distances SNP par paires sur un **mapping pan-génome**, ce qui change les distances quand le génome
> accessoire compte. À utiliser en recoupement quand une distance décide d'un lien de transmission,
> jamais silencieusement à la place de l'autre : les deux échelles ne sont pas comparables.


> [!TIP]
> **Une matrice de distances est quadratique.** À 10 000 souches elle compte 5·10⁷ paires, à 100 000
> elle en compte 5·10⁹ : le calcul et la matrice elle-même débordent le portable bien avant la
> patience. Envoyer sur `mp` (125 Go, 64 threads, `/data` pour écrire la matrice) ou `mh` `bigmem`
> (1 To). Voir le skill `remote-compute` (sonde d'état, modèles `sbatch`, pièges). Prérequis : VPN monté (`sudo vpn up`).


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

### 1. Matrice SPDI binaire (pivot) : RECOMMANDÉ

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
  SELECT strain_id FROM mv_strain_classification
  WHERE system_name = 'guyeux' AND lineage_code LIKE '4.15%'
)
ORDER BY ss.strain_id, ss.spdi_id;
```

Sauvegarder le résultat en CSV, puis :

```bash
python3 scripts/snp_distance.py strain_spdi.csv -o distances.csv --summary
```

Le script détecte automatiquement le format (liste longue vs matrice) et pivote si nécessaire.

### Distances aux références (vue pré-calculée)

> ⚠ **`strain_id` est un ENTIER** (clé interne, ex. 167563) ; l'accession SRA/ENA est dans **`strain_name`**
> (ex. `ERR551415`). Un filtre `strain_id IN ('ERR…')` ne renvoie rien.

```sql
-- Distances SNP aux souches de référence (filtrer par ACCESSION = strain_name)
-- Validé 2026-07-31 : ERR551415 → SRR28393365 à 653 SNP ; SRR33638270 → 640.
SELECT strain_id, strain_name, reference_strain_name, snp_distance
FROM mv_strain_reference_snp_distance
WHERE strain_name IN ('ERR551415', 'SRR33638270');
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
