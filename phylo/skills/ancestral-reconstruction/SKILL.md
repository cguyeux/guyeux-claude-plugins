---
name: ancestral-reconstruction
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST): ancestral geographic states
  on MTBC phylogenies, for peer-reviewed phylogeographic publications. Parsimony
  (Fitch), ML marginal posteriors (MPPA), stochastic mapping, BEAST DTA XML, iTOL
  migration arrows. Use when: dating and counting a lineage's migrations between
  regions, comparing them to human movements, annotating phylogenies, preparing
  BEAST DTA.
argument-hint: "<tree.nwk> <metadata.csv> [--method parsimony|ml|stochastic] [-o results.csv]"
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


# Ancestral Reconstruction : Reconstruction des etats ancestraux geographiques MTBC

Reconstruction des localisations ancestrales sur les phylogenies MTBC pour identifier les evenements de migration et les comparer aux mouvements humains historiques.

## Phase 1 : Decouverte (OBLIGATOIRE)

1. **Quelle methode ?**

   | Methode | Usage | Quand l'utiliser |
   |---------|-------|-----------------|
   | **Parcimonie** (Fitch) | Rapide, baseline | Exploration initiale, grands arbres |
   | **ML marginal** (MPPA) | Standard actuel | Article, probabilites par noeud |
   | **Stochastic mapping** | Echantillonnage | Quantifier l'incertitude, compter les transitions |
   | **BEAST DTA** | Bayesien | Datation + phylogeographie simultanee |

2. **Quelles donnees ?**
   - Arbre Newick (depuis RAxML, BEAST, ou NJ)
   - Metadonnees CSV avec `strain_id` et `country` (ou region)
   - Optionnel : dates de collecte pour BEAST DTA

3. **Quelle granularite geographique ?**
   - Pays (defaut), ideal si N > 50 par pays
   - Region OMS (6 regions), si donnees eparses
   - Continent, si tres peu de diversite geographique
   - Region personnalisee

## Phase 2 : Extraction des donnees

### Depuis TBannotator

```sql
-- Metadonnees geographiques pour les feuilles de l'arbre
-- NB : `strain_id` est un ENTIER ; les accessions SRA/ENA sont dans `strain_name`.
SELECT m.strain_id, m.strain_name, m.geo_country,
       c.lineage_code AS lineage
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.strain_id
WHERE c.system_name = 'guyeux'
  AND m.strain_name IN ('ERR551415', 'SRR33638270')
  AND m.geo_country IS NOT NULL;

-- Distribution par region pour choisir la granularite
SELECT m.geo_country, COUNT(*) as n
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.strain_id
WHERE c.system_name = 'guyeux' AND c.lineage_code LIKE '4%'
  AND m.geo_country IS NOT NULL
GROUP BY m.geo_country
ORDER BY n DESC;
```

### Format CSV attendu

```csv
strain_id,country
ERR123456,France
SRR789012,South Africa
ERR345678,India
```

## Phase 3 : Reconstruction

### Script principal

```bash
# Parcimonie (Fitch) — rapide, baseline
python3 scripts/ancestral_reconstruction.py tree.nwk metadata.csv \
  --method parsimony --location-column country \
  -o ancestral_states.csv

# ML marginal posteriors (MPPA) — standard pour article
python3 scripts/ancestral_reconstruction.py tree.nwk metadata.csv \
  --method ml --location-column country \
  -o ancestral_ml.csv -p ancestral_tree.png

# Stochastic mapping — quantification des transitions
python3 scripts/ancestral_reconstruction.py tree.nwk metadata.csv \
  --method stochastic --n-simulations 100 \
  --migration-counts migrations.csv -o stochastic_results.csv

# Export iTOL (branches colorees + fleches de migration)
python3 scripts/ancestral_reconstruction.py tree.nwk metadata.csv \
  --method ml --itol itol_annotations

# Generation BEAST DTA XML
python3 scripts/ancestral_reconstruction.py tree.nwk metadata.csv \
  --beast-xml beast_dta.xml --dates dates.csv
```

## Arguments du script

| Argument | Default | Description |
|----------|---------|-------------|
| `tree` | (requis) | Arbre Newick |
| `metadata` | (requis) | CSV avec strain_id et localisation |
| `--method` | `ml` | `parsimony`, `ml`, `stochastic` |
| `--location-column` | `country` | Colonne de localisation dans le CSV |
| `--n-simulations` | `100` | Nombre de simulations stochastiques |
| `-o`, `--output` | none | CSV des probabilites ancestrales par noeud |
| `-p`, `--plot` | none | Figure de l'arbre annote (PNG/PDF) |
| `--itol` | none | Prefixe pour fichiers iTOL |
| `--beast-xml` | none | Generer XML BEAST DTA |
| `--dates` | none | CSV dates pour BEAST (strain_id, date) |
| `--migration-counts` | none | CSV des transitions entre regions |
| `--model` | `F81` | Modele de substitution (`F81`, `equal`, `custom`) |
| `--summary` | off | Afficher un resume JSON |

## Sortie migration-counts (cle pour articles de co-evolution)

```csv
from,to,n_transitions,proportion,mean_time,ci95_lo,ci95_hi
West Africa,Americas,12,0.18,1720,1650,1790
East Africa,South Asia,3,0.05,1450,1200,1600
Europe,Americas,8,0.12,1850,1780,1920
```

Ce tableau permet la comparaison directe avec les matrices de flux migratoires humains produites par le skill `migration-data`.

## Export iTOL

Le script genere deux fichiers d'annotation :

1. **Branches colorees** (`_branch_colors.txt`), couleur par etat ancestral reconstruit
2. **Fleches de migration** (`_arrows.txt`) : DATASET_CONNECTION entre noeuds ou l'etat change

## Modeles de transition

| Modele | Description | Usage MTBC |
|--------|-------------|------------|
| `F81` | Frequences equilibre estimees des donnees, taux uniforme | Defaut, robuste |
| `equal` | Toutes transitions equiprobables | Baseline |
| `custom` | Matrice Q fournie en JSON | Quand on sait que certaines routes sont plus probables |

## Integration

| Skill | Usage |
|-------|-------|
| `raxml` | Fournit l'arbre phylogenetique ML |
| `molecular-clock` | Date l'arbre (TMRCA), necessaire pour BEAST DTA |
| `phylogeography` | Donnees pays x lignee, diversite geographique |
| `coevolution` | Mantel test entre transitions MTBC et flux migratoires |
| `migration-data` | Donnees de migration humaine pour comparaison |
| `geo-map` | Carte avec fleches de migration |
| `itol` | Annotation de l'arbre avec etats ancestraux |

## Dependances

```bash
pip install numpy scipy pandas matplotlib dendropy
```

`dendropy` est utilise pour la manipulation d'arbres phylogenetiques (traversal, annotation de noeuds internes). Si indisponible, un parseur Newick simplifie est utilise en fallback.
