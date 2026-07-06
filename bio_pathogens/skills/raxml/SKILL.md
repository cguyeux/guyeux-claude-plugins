---
name: raxml
description: >-
  Academic research toolkit for the Guyeux group (FEMTO-ST, University of Franche-Comte). Runs peer-reviewed phylogenomic inference (RAxML-NG) for scientific publications. Submit and manage RAxML-NG phylogenetic inference jobs via TBannotator MCP.
  Supports direct matrix mode, clustering mode, and contextual placement.

  Use when: building MTBC phylogenies, placing new strains on reference trees,
  producing Newick files for iTOL annotation, running RAxML-NG for an article.
argument-hint: "<strain_sql or lineage> [--mode matrix|clustering|contextual] [--model GTR+G]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres, mcp__tbannotator__tool_submit_raxml_job, mcp__tbannotator__tool_build_nj_tree
---

# RAxML-NG — Inférence phylogénétique MTBC

Soumission, suivi et récupération de phylogénies RAxML-NG via le serveur MCP TBannotator. Produit des arbres Newick publication-quality pour annotation iTOL.

## Phase 1 : Découverte (OBLIGATOIRE)

Avant de lancer un job, **poser ces questions** à l'utilisateur :

1. **Quelles souches ?**
   - Une lignée complète (ex. `L4.15`, `L2`)
   - Une requête SQL personnalisée
   - Une liste de SRA IDs
   - Un sous-ensemble filtré (pays, résistance, etc.)

2. **Quel mode ?**
   - **Matrix** (défaut) : phylogénie standard à partir de la matrice SNP
   - **Clustering** : pour les gros jeux (>5000 souches), pré-clustering puis jobs RAxML par cluster
   - **Contextual** : placer de nouvelles souches sur un arbre de référence existant

3. **Modèle d'évolution ?**
   - `GTR+G` (défaut, recommandé pour MTBC)
   - `GTR+G4`, `GTR+I+G` pour plus de flexibilité

4. **NJ rapide d'abord ?**
   - Recommandé pour valider la sélection de souches avant un long job RAxML
   - `tool_build_nj_tree` : résultat en quelques minutes vs heures/jours pour RAxML

5. **Filtrage des variants ?**
   - `all` : tous les variants (défaut)
   - `no_core0` : exclure les variants absents du core
   - `no_core0_excl0` : exclure aussi les exclus du core
   - `no_char0` : exclure les variants non caractéristiques

## Phase 2 : Validation rapide (optionnel, recommandé)

### Neighbor-Joining exploratoire

```
tool_build_nj_tree(
  strain_sql = "SELECT sra_id AS strain_id FROM mv_strain_classification WHERE system='Senelle' AND lineage_code LIKE '4.15%'",
  max_strains = 5000,
  remove_invariant = true
)
```

**Retour** : Newick string. Vérifier :
- Le nombre de feuilles correspond au nombre attendu de souches
- Pas de branche aberrante (contamination, mauvaise classification)
- La topologie générale est plausible

Si le NJ est satisfaisant → lancer RAxML. Sinon, ajuster la sélection.

## Phase 3 : Soumission RAxML-NG

### Mode 1 — Matrix (standard)

```
tool_submit_raxml_job(
  strain_sql = "SELECT sra_id AS strain_id FROM mv_strain_classification WHERE system='Senelle' AND lineage_code LIKE '4.15%'",
  model = "GTR+G",
  starting_trees = "pars{2},rand{2}",
  seed = 42
)
```

**Retour** : `job_id` (entier). Le job tourne en arrière-plan sur le serveur.

### Mode 2 — Clustering (gros jeux)

Nécessite un `clustering_job_id` d'un job de clustering HDBSCAN déjà terminé.

```
tool_submit_raxml_job(
  clustering_job_id = 42,
  model = "GTR+G",
  hdbscan_min_cluster_size = 50,
  hdbscan_min_samples = 10,
  cluster_selection_epsilon = 0.5
)
```

Crée un job RAxML par cluster identifié. Utile pour >5000 souches.

### Mode 3 — Contextual (placement sur arbre existant)

```
tool_submit_raxml_job(
  strain_sql = "SELECT sra_id AS strain_id FROM mv_strain_classification WHERE system='Senelle' AND lineage_code = '4.15.1'",
  reference_raxml_job_id = 100,
  use_clustering = true,
  max_query_strains = 1000
)
```

Place les souches de la requête sur l'arbre de référence (job 100) en utilisant `--tree-constraint`.

## Phase 4 : Suivi du job

### Polling via SQL

```sql
SELECT id, status, strain_count, snp_count, model,
       created_at, started_at, completed_at, error_message
FROM job_raxml
WHERE id = {job_id};
```

| Status | Signification |
|--------|--------------|
| `pending` | En attente de traitement |
| `building_matrix` | Construction de la matrice SNP |
| `running` | RAxML-NG en cours d'exécution |
| `completed` | Terminé avec succès |
| `failed` | Erreur (voir `error_message`) |

### Durée estimée

| Nombre de souches | Durée typique |
|-------------------|---------------|
| < 100 | 5-30 min |
| 100-500 | 30 min - 2h |
| 500-2000 | 2-12h |
| 2000-5000 | 12-48h |
| > 5000 | Utiliser le mode clustering |

### Script de monitoring

```bash
python3 scripts/raxml_monitor.py --job-id {JOB_ID} \
  --poll-interval 60 --output tree.nwk --timeout 86400
```

Le script poll le statut et télécharge automatiquement le Newick quand le job est terminé.

## Phase 5 : Récupération du Newick

### Téléchargement

```bash
# Via le script
python3 scripts/raxml_monitor.py --job-id {JOB_ID} --output tree.nwk

# Via curl (URL directe)
curl -o tree.nwk "https://darthos.freeboxos.fr/mcp/download/tree_newick/{JOB_ID}"
```

### Vérification

```python
import re
with open("tree.nwk") as f:
    newick = f.read()
leaf_ids = re.findall(r'([A-Z]{3}\d+)', newick)
print(f"{len(leaf_ids)} feuilles dans l'arbre")
```

## Phase 6 : Enchaînement

Après récupération du Newick, proposer automatiquement :

1. **`/itol`** : annoter l'arbre (coloration par lignée, strips de métadonnées)
2. **`/thd`** : calculer le THD et le superposer en heatmap
3. **`/tsne-hdbscan`** : comparer la structure de clustering avec la phylogénie

## Lister les jobs existants

```sql
-- Derniers jobs RAxML
SELECT id, status, strain_count, snp_count, model,
       created_at, completed_at
FROM job_raxml
ORDER BY created_at DESC
LIMIT 20;

-- Jobs terminés avec succès pour une lignée
SELECT r.id, r.strain_count, r.completed_at
FROM job_raxml r
WHERE r.status = 'completed'
ORDER BY r.completed_at DESC;
```

## Paramètres RAxML-NG

### Modèle d'évolution

| Modèle | Description | Usage MTBC |
|--------|-------------|------------|
| `GTR+G` | General Time Reversible + Gamma | **Défaut, recommandé** |
| `GTR+G4` | GTR + 4 catégories Gamma | Plus précis, plus lent |
| `GTR+I+G` | GTR + sites invariants + Gamma | Rarement nécessaire pour MTBC |

### Starting trees

| Stratégie | Description |
|-----------|-------------|
| `pars{2},rand{2}` | 2 arbres parsimonie + 2 aléatoires (défaut, bon compromis) |
| `pars{5},rand{5}` | Plus de départs, meilleure exploration (plus lent) |
| `pars{1}` | Rapide, un seul départ |

### Filtrage des variants

| Filtre | Description | Quand l'utiliser |
|--------|-------------|-----------------|
| `all` | Tous les variants | Défaut |
| `no_core0` | Exclure les variants absents du core genome | Phylogénie stricte core |
| `no_core0_excl0` | + exclure les exclus du core | Plus conservateur |
| `no_char0` | Exclure les non-caractéristiques | Focus sur les variants informatifs |

## Intégration TBannotator

### Requêtes SQL utiles pour la sélection de souches

```sql
-- Toutes les souches d'une lignée
SELECT sra_id AS strain_id
FROM mv_strain_classification
WHERE system = 'Senelle' AND lineage_code LIKE '4.15%';

-- Souches d'une lignée + contexte (lignées sœurs)
SELECT sra_id AS strain_id
FROM mv_strain_classification
WHERE system = 'Senelle'
  AND (lineage_code LIKE '4.15%' OR lineage_code LIKE '4.14%' OR lineage_code LIKE '4.16%');

-- Souches d'un pays
SELECT m.strain_id
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.sra_id
WHERE c.system = 'Senelle' AND c.lineage_code LIKE '4%'
  AND m.country = 'France';

-- Souches MDR d'une lignée
SELECT m.strain_id
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.sra_id
WHERE c.system = 'Senelle' AND c.lineage_code LIKE '2%'
  AND m.dr_type IN ('MDR', 'XDR', 'pre-XDR');

-- Vérifier le nombre de souches avant soumission
SELECT lineage_code, COUNT(*) as n
FROM mv_strain_classification
WHERE system = 'Senelle' AND lineage_code LIKE '4.15%'
GROUP BY lineage_code
ORDER BY lineage_code;
```

## Dépendances

```bash
pip install requests
```

Le calcul RAxML-NG s'exécute sur le serveur TBannotator, pas en local.
