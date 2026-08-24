---

name: coevolution
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST): statistical tests of
  MTBC-human co-divergence and geographic structure for peer-reviewed
  publications. Mantel, partial Mantel, isolation by distance, PACo, FST
  (Weir & Cockerham), AMOVA.

  Use when: testing whether MTBC diversity correlates with geographic distance,
  comparing bacterial and human population structure, quantifying
  differentiation between MTBC populations by country.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres
---

# Coevolution : Tests statistiques de co-divergence MTBC-humains

Tests statistiques pour evaluer si la diversite genetique MTBC est structuree geographiquement et si elle co-diverge avec les populations humaines.

## Phase 1 : Decouverte (OBLIGATOIRE)

1. **Quel test ?**

   | Test | Question | Input |
   |------|----------|-------|
   | **Mantel** | La diversite MTBC correle-t-elle avec la distance geographique ? | 2 matrices de distances |
   | **Mantel partiel** | Idem en controlant un cofacteur (taille d'echantillon, periode) | 3 matrices |
   | **IBD** | Y a-t-il isolation par la distance ? | Distances genetiques + coordonnees |
   | **PACo** (Procrustean Approach to Cophylogeny) | MTBC co-diverge-t-il avec les populations humaines ? | Distances hote + parasite + liens |
   | **FST** | Quelle differenciation entre populations MTBC ? | Genotypes + groupes |
   | **AMOVA** | Comment la variance se repartit-elle hierarchiquement ? | Genotypes + hierarchie |

2. **Quelles donnees ?**
   - Matrice de distances genetiques MTBC (depuis `snp-distance`)
   - Coordonnees geographiques ou pays (depuis TBannotator)
   - Pour PACo : distances entre populations humaines (depuis `migration-data`)
   - Pour AMOVA : hierarchie geographique (pays -> region -> continent)

## Phase 2 : Extraction des donnees

### Depuis TBannotator

```sql
-- Coordonnees par souche (pays -> centroide)
SELECT m.strain_id, m.geo_country,
       c.lineage_code as lineage
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.strain_id
WHERE c.system_name = 'guyeux' AND c.lineage_code LIKE '4%'
  AND m.geo_country IS NOT NULL;
```

### Formats d'entree

**Matrice de distances (CSV carre) :**
```csv
,strain_A,strain_B,strain_C
strain_A,0,45,120
strain_B,45,0,98
strain_C,120,98,0
```

**Donnees geographiques :**
```csv
strain_id,country,latitude,longitude
ERR123456,France,46.2,2.2
SRR789012,South Africa,-30.6,22.9
```

**Liens hote-parasite (pour PACo) :**
```csv
strain_id,human_population
ERR123456,European
SRR789012,Southern_African
```

## Phase 3 : Tests

> **Self-check** : `python3 scripts/smoke_test.py` (Mantel sur des données à structure
> connue, hors-ligne). Mantel, Mantel partiel, PACo, FST et AMOVA sont tous implémentés
> ici : **c'est ce skill qui fait le test**, même quand la matrice de distances vient
> d'un autre skill. Pour tester si une sous-lignée MTBC suit le **coût de transport
> romain**, donner la matrice de distances ORBIS comme `distances.csv` :
> `python3 -m orbis_client matrix --sites roma,carthago,... --weight days --tsv` (skill
> `orbis`), puis Mantel contre la matrice de distances phylogénétiques.

### Script principal

```bash
# Test de Mantel
python3 scripts/coevolution.py distances.csv geo_data.csv \
  --test mantel --permutations 9999 -o mantel_results.csv -p mantel_plot.png

# Mantel partiel (controle par taille d'echantillon)
python3 scripts/coevolution.py distances.csv geo_data.csv \
  --test partial_mantel --covariate sample_size_matrix.csv -o partial_mantel.csv

# Isolation by distance
python3 scripts/coevolution.py distances.csv geo_data.csv \
  --test ibd -o ibd_results.csv -p ibd_scatter.png

# PACo (co-phylogenie)
python3 scripts/coevolution.py distances.csv geo_data.csv \
  --test paco --host-distances human_fst.csv \
  --host-parasite-links hp_links.csv -o paco_results.csv

# FST entre pays
python3 scripts/coevolution.py distances.csv geo_data.csv \
  --test fst --group-column country -o fst_results.csv

# AMOVA hierarchique
python3 scripts/coevolution.py distances.csv geo_data.csv \
  --test amova --hierarchy hierarchy.csv -o amova_results.csv
```

## Arguments du script

| Argument | Default | Description |
|----------|---------|-------------|
| `genetic_distances` | (requis) | Matrice de distances genetiques CSV |
| `geo_data` | (requis) | CSV avec strain_id et coordonnees/pays |
| `--test` | `mantel` | `mantel`, `partial_mantel`, `ibd`, `paco`, `fst`, `amova` |
| `--permutations` | `9999` | Nombre de permutations |
| `--covariate` | none | Matrice cofacteur pour Mantel partiel |
| `--host-distances` | none | Matrice distances populations humaines (PACo) |
| `--host-parasite-links` | none | CSV liens hote-parasite (PACo) |
| `--group-column` | `country` | Colonne de regroupement (FST/AMOVA) |
| `--hierarchy` | none | CSV hierarchie geographique (AMOVA) |
| `--correlation` | `pearson` | `pearson` ou `spearman` (Mantel) |
| `-o`, `--output` | none | Resultats CSV |
| `-p`, `--plot` | none | Figure(s) diagnostique |
| `--summary` | off | Resume JSON |

## Interpretation des resultats

| Test | Statistique | Seuil | Interpretation MTBC |
|------|-------------|-------|---------------------|
| Mantel r > 0, p < 0.05 | r de Pearson/Spearman | 0.05 | Diversite MTBC structuree geographiquement |
| IBD pente > 0, p < 0.05 | Regression + permutation | 0.05 | Dispersion limitee, pas de panmixie globale |
| PACo m² faible, p < 0.05 | Somme residus² de Procrustes | 0.05 | Co-divergence MTBC/humains significative |
| FST > 0.05 | Weir & Cockerham | 0.05-0.15 moderee, >0.15 forte | Populations MTBC differenciees entre pays |
| AMOVA % entre-regions > 20% | Partition de variance |, | Geographie explique une part majeure de la variance |

## Distances geographiques

Les distances sont calculees automatiquement :
- Si latitude/longitude fournies : distance de Haversine (km)
- Si seulement pays : centroides des pays (table integree)

## Integration

| Skill | Usage |
|-------|-------|
| `snp-distance` | Fournit la matrice de distances genetiques |
| `phylogeography` | Donnees geographiques, structure regionale |
| `ancestral-reconstruction` | Transitions migratoires pour comparaison |
| `migration-data` | Distances entre populations humaines pour PACo |
| `lineage-comparison` | Tests complementaires (Fisher, chi-squared) |

## Dependances

```bash
pip install numpy scipy pandas scikit-learn matplotlib
```

`scikit-learn` est utilise pour l'analyse de Procrustes dans PACo. Si indisponible, PACo est desactive avec un avertissement.

## Codex packaging note

This packaged copy targets Codex. MCP tool names in `allowed-tools` are prerequisites: verify them with `codex mcp list` in the active profile before relying on live queries.
