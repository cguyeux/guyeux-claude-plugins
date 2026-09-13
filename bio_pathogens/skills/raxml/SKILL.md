---
name: raxml
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST): peer-reviewed
  phylogenomic inference with RAxML-NG. Matrix, clustering and
  contextual-placement modes. BROKEN PATH SINCE 2026-09-08: the job submission
  and NJ tree tools it relied on (mcp__tbannotator__tool_submit_raxml_job,
  tool_build_nj_tree) no longer exist -- the tblearn server that replaced
  TBannotator exposes only SQL. Build the alignment by SQL, then run RAxML-NG
  locally or on mp/mh via remote-compute. See ~/.agents/knowledge/tblearn-migration.md.

  Use when: building MTBC phylogenies, placing new strains on a reference
  tree, producing Newick files for iTOL annotation, running RAxML-NG for an
  article.
argument-hint: "<strain_sql or lineage> [--mode matrix|clustering|contextual] [--model GTR+G]"
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


> [!WARNING]
> **[2026-09-08] La voie de soumission décrite plus bas n'a plus de serveur derrière elle.**
> `mcp__tbannotator__tool_submit_raxml_job` et `mcp__tbannotator__tool_build_nj_tree` ont disparu
> avec l'ancien MCP TBannotator (endpoint mort, HTTP 404). Le serveur `tblearn` qui le remplace
> n'expose que `tool_query_postgres` et `tool_get_schema`, donc du SQL en lecture seule et rien
> d'autre : ni construction d'arbre NJ, ni soumission de job.
>
> Ce qui reste valable ici : la sélection des souches et la construction de la matrice binaire par
> requête SQL, les conventions de modèle (BIN+G pour les alignements SNP 0/1) et l'annotation iTOL.
> Ce qui doit changer : l'exécution de RAxML-NG passe désormais en local ou sur `mp`/`mh` via le
> skill `remote-compute`, et le skill `bdd-bridge` (`phylo_job.py`) fait déjà exactement cela depuis
> la base locale, sans dépendre d'aucun serveur distant.
>
> Détail de la migration : `~/.agents/knowledge/tblearn-migration.md`.

# RAxML-NG : Inférence phylogénétique MTBC

> [!TIP]
> **Trois routes de calcul, dans cet ordre.** (1) **Exécution locale** via `phylo_job.py run` du
> skill `bdd-bridge` : aucun transfert, la base est déjà sur le disque, et c'est la bonne route
> jusqu'à quelques milliers de souches. (La route historique, un job soumis au serveur TBannotator,
> n'existe plus : ce serveur est arrêté depuis le 2026-09-08.) (2) `mp` porte `raxmlHPC` dans
> `/usr/bin` (version ancienne, pas `raxml-ng`) et n'a aucune limite de temps. (3) `mh` (Slurm) pour du multi-nœuds : **`raxml-ng` 2.0.2 y est prêt** dans
> `/Work/Users/cguyeux/envs/phylo/bin`, mais il **exige**
> `LD_LIBRARY_PATH=/Work/Users/cguyeux/envs/phylo/lib` (le `libstdc++` de Rocky 8 est trop ancien ;
> ni `micromamba run` ni `micromamba activate` ne suffisent).
> Voir le skill `remote-compute` (sonde d'état, modèles `sbatch`, pièges). Prérequis : VPN monté (`sudo vpn up`).


Outil de recherche académique du groupe Guyeux, Institut FEMTO-ST (CNRS UMR 6174), Université Marie et Louis Pasteur (ex-Université de Franche-Comté), Besançon. Produit des inférences phylogénomiques destinées à des publications scientifiques évaluées par des pairs.

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

4. **Validation rapide de la sélection avant un long calcul ?**
   - La construction d'arbre NJ côté serveur n'existe plus (`tool_build_nj_tree`, arrêté le
     2026-09-08). Deux substituts, tous deux locaux : `bdd_query.py denominator <clade>` pour
     vérifier l'effectif réellement exploitable, et `/tsne-hdbscan` sur la matrice de distances
     pour voir la structure en quelques minutes au lieu d'attendre l'arbre.
   - Et d'abord `/phylo-forest`, pour savoir si l'arbre existe déjà.

5. **Filtrage des variants ?**
   - `all` : tous les variants (défaut)
   - `no_core0` : exclure les variants absents du core
   - `no_core0_excl0` : exclure aussi les exclus du core
   - `no_char0` : exclure les variants non caractéristiques

## Phase 2 : Alignement binaire

L'alignement se construit depuis la base LOCALE `bdd/actuelle/`, avec `phylo_job.py` du skill
`bdd-bridge`. Il n'y a plus de matrice distante à demander ni de job à faire construire.

```bash
B=~/docs/codes/claude_plugins/bio_pathogens/skills/bdd-bridge/scripts
export TBANNOTATOR_BDD=~/docs/codes/mtbc/bdd

python3 $B/phylo_job.py --out /tmp/arbre_L4.8 --min-frac 0.02 align L4.8
```

`--min-frac` fixe la fréquence minimale d'un variant pour entrer dans l'alignement ; c'est le
paramètre qui décide de la taille de la matrice, donc du temps de calcul. Contrôler ensuite le
nombre de souches et de sites retenus AVANT de lancer l'inférence : un alignement de trois sites
produira un arbre, et il ne voudra rien dire.

Pour connaître l'effectif exploitable d'un clade avant de commencer, et ne pas confondre nombre de
répertoires et nombre de souches réellement utilisables :

```bash
python3 $B/bdd_query.py clades                 # les 760 clades et leurs effectifs
python3 $B/bdd_query.py denominator L4.8       # garde-fou de dénominateur
```

## Phase 3 : Exécution de RAxML-NG

Deux voies, selon la taille. `detect-raxml` dit d'abord si un binaire est disponible localement.

```bash
python3 $B/phylo_job.py detect-raxml

# petit à moyen jeu : exécution locale
python3 $B/phylo_job.py --out /tmp/arbre_L4.8 --threads 8 --seed 12345 run L4.8

# gros jeu : paquet SLURM portable, à déposer sur mh
python3 $B/phylo_job.py --out /tmp/arbre_L4.8 --bs 100 submit L4.8
```

Le modèle reste **BIN+G** pour les alignements SNP binaires 0/1, conformément aux conventions du
dépôt ; c'est la valeur par défaut et il n'y a pas de raison de la changer sans motif écrit.

Pour le mode `submit`, le paquet produit est autonome et se transfère sur `mh` selon le skill
`remote-compute` (VPN requis, lancé par l'utilisateur avec `sudo vpn up`). Le suivi est celui de
SLURM (`squeue`, `sacct`), pas une table de jobs distante.

## Phase 4 : Récupération et contrôle

Le Newick est écrit dans le répertoire `--out`. Il n'y a plus ni téléchargement ni URL à composer.
Contrôler avant toute exploitation :

- le nombre de feuilles correspond au nombre de souches attendu ;
- aucune branche aberrante isolant une souche unique à très longue distance, signal classique de
  contamination ou de couverture défaillante — passer la souche suspecte au skill `strain-qc` ;
- la topologie est cohérente avec les marqueurs connus du clade, à croiser avec
  `bdd_query.py synapo <clade>`.

## Phase 5 : Enchaînement

1. **`/itol`** : annoter l'arbre (coloration par lignée, strips de métadonnées)
2. **`/thd`** : calculer le THD et le superposer en heatmap
3. **`/tsne-hdbscan`** : comparer la structure de clustering avec la phylogénie
4. **`/phylo-forest`** : verser l'arbre à la forêt, pour qu'il soit retrouvable et comparable

Et avant de lancer quoi que ce soit, l'inverse : **`/phylo-forest` d'abord**, pour vérifier qu'un
arbre équivalent n'existe pas déjà. C'est la raison d'être de ce skill.

## Ce que la migration du 2026-09-08 a changé, et ce qu'elle a résolu

L'ancienne voie passait par `tool_submit_raxml_job` et `tool_build_nj_tree` du MCP TBannotator, tous
deux disparus avec ce serveur. Les pièges qui lui étaient propres sont donc caducs, et l'un d'eux
méritait mieux qu'une note : la soumission distante **dédoublonnait silencieusement** sur
`strain_hash` + modèle **en ignorant la graine**, si bien que deux soumissions du même jeu avec des
`seed` différents rendaient le même job au lieu de deux. Cela rendait impossible toute mesure de
bruit d'inférence, c'est-à-dire la stabilité topologique entre exécutions identiques, sur un jeu
figé.

**L'exécution locale lève cette limite** : `--seed` y est réellement honoré, et des réplicats à
graines contrôlées redeviennent possibles. Ce qui était consigné comme un blocage sans contournement
propre est résolu par le changement de voie, non par un correctif.

Deuxième point caduc, à ne pas rechercher dans les nouvelles sorties : `snp_matrix_job_id`
n'identifiait pas un alignement particulier mais une matrice nucléotidique globale, ce qui trompait
quiconque essayait de figer un alignement entre deux soumissions. Ici l'alignement est un fichier,
sur le disque, et il se fige en le gardant.

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
SELECT strain_id AS strain_id
FROM mv_strain_classification
WHERE system_name = 'guyeux' AND lineage_code LIKE '4.15%';

-- Souches d'une lignée + contexte (lignées sœurs)
SELECT strain_id AS strain_id
FROM mv_strain_classification
WHERE system_name = 'guyeux'
  AND (lineage_code LIKE '4.15%' OR lineage_code LIKE '4.14%' OR lineage_code LIKE '4.16%');

-- Souches d'un pays
SELECT m.strain_id
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.strain_id
WHERE c.system_name = 'guyeux' AND c.lineage_code LIKE '4%'
  AND m.geo_country = 'France';

-- Souches MDR d'une lignée (pas de `dr_type` en v3.6 : MDR = INH-R ET RIF-R)
SELECT m.strain_id
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.strain_id
WHERE c.system_name = 'guyeux' AND c.lineage_code LIKE '2%'
  AND m.antibiogram_inh = 'INH-R' AND m.antibiogram_rif = 'RIF-R';

-- Vérifier le nombre de souches avant soumission
SELECT lineage_code, COUNT(*) as n
FROM mv_strain_classification
WHERE system_name = 'guyeux' AND lineage_code LIKE '4.15%'
GROUP BY lineage_code
ORDER BY lineage_code;
```

## Dépendances

```bash
pip install requests
```

Le calcul RAxML-NG s'exécute sur le serveur TBannotator, pas en local.
