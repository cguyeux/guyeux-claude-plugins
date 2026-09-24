---

name: migration-data
description: >-
  Aggregate and format human migration data for comparison with MTBC patterns.
  SlaveVoyages, UN migration stock, HGDP genetic structure, ancient DNA events,
  WHO TB burden, and curated historical migration timeline.

  Use when: comparing MTBC lineage dispersal to human movements, building
  migration matrices for Mantel tests, overlaying TMRCA with migration
  chronology, preparing figures linking bacterial and human history.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# Migration Data : Donnees de migration humaine pour etudes MTBC

Agregation et formatage de donnees de migration humaine pour comparaison directe avec les patterns de dispersion des lignees MTBC.

## Phase 1 : Decouverte (OBLIGATOIRE)

1. **Quelle source ?**

   | Source | Donnees | Periode | Usage MTBC |
   |--------|---------|---------|------------|
   | **SlaveVoyages** | 36k voyages, routes, volumes | 1514-1866 | L5/L6 en Ameriques, L4 Clade A |
   | **UN Migration Stock** | Migrants par pays origine/destination | 1990-2020 | Import lignees non-L4 en Europe |
   | **HGDP** | Structure genetique K=7 par population | Contemporain | Comparaison PACo hote-parasite |
   | **Ancient DNA** | Evenements prehistoriques | -70000 a present | Out-of-Africa, Neolithique, Bantu |
   | **WHO TB Burden** | Incidence TB par pays/annee | 2000-2023 | Contexte epidemiologique |
   | **Timeline** | Chronologie combinee | Toutes periodes | Vue synthetique, overlay TMRCA |

2. **Quelle periode ?**
   - Prehistorique (-70000 a -3000) : Out-of-Africa, Neolithique
   - Antique/Medieval (-3000 a 1500) : Bantu, commerce arabe
   - Moderne (1500-1900) : colonisation, traite des esclaves
   - Contemporain (1900-present) : migrations modernes

3. **Quel format de sortie ?**
   - `routes` : liste de routes (from, to, volume, period)
   - `matrix` : matrice bilaterale de flux (pays x pays)
   - `timeline` : chronologie avec liens MTBC

## Phase 2 : Commandes

### Script principal

```bash
# Agreger les donnees SlaveVoyages par route
python3 scripts/migration_data.py slave-trade \
  --input slavevoyages.csv --period 1514:1866 \
  --format routes -o slave_routes.csv

# Migration moderne (matrice UN)
python3 scripts/migration_data.py modern \
  --input un_migration.xlsx --period 1990:2020 \
  --format matrix -o modern_matrix.csv

# Structure genetique HGDP (table curee integree)
python3 scripts/migration_data.py hgdp -o hgdp_structure.csv

# Evenements de migration anciens (table curee integree)
python3 scripts/migration_data.py ancient --format timeline -o ancient_events.csv

# Incidence TB par pays (WHO)
python3 scripts/migration_data.py who-burden \
  --input who_tb_data.csv -o tb_burden.csv

# Timeline combinee : overlay avec TMRCA MTBC
python3 scripts/migration_data.py timeline \
  --tmrca tmrca_estimates.csv --period -70000:2025 \
  -o full_timeline.csv -p timeline_figure.png

# Matrice de distances geographiques entre pays
python3 scripts/migration_data.py distances \
  --countries "France,Germany,India,South Africa,Brazil" \
  -o geo_distances.csv
```

## Arguments par commande

### `slave-trade`
| Argument | Description |
|----------|-------------|
| `--input` | CSV SlaveVoyages (telecharge depuis slavevoyages.org) |
| `--period` | Periode (ex. `1700:1800`) |
| `--from-region` | Filtrer par region source |
| `--to-region` | Filtrer par region destination |
| `--format` | `routes` ou `matrix` |

### `modern`
| Argument | Description |
|----------|-------------|
| `--input` | Excel UN Migration Stock |
| `--period` | Periode (ex. `2000:2020`) |
| `--format` | `matrix` (bilaterale) |

### `hgdp`
| Argument | Description |
|----------|-------------|
| `--populations` | Filtrer par populations (ex. `European,African`) |
| Aucun input requis | Table curee integree |

### `ancient`
| Argument | Description |
|----------|-------------|
| `--period` | Filtrer par periode |
| `--format` | `timeline` ou `routes` |
| Aucun input requis | Table curee integree |

### `timeline`
| Argument | Description |
|----------|-------------|
| `--tmrca` | CSV des TMRCA MTBC pour overlay |
| `--period` | Periode d'affichage |
| `-p` | Figure de chronologie |

### `distances`
| Argument | Description |
|----------|-------------|
| `--countries` | Liste de pays (virgules) ou CSV |
| `--method` | `haversine` (defaut) |

### Arguments communs
| Argument | Default | Description |
|----------|---------|-------------|
| `-o` | none | Fichier de sortie CSV |
| `-p` | none | Figure (PNG/PDF) |
| `--summary` | off | Resume JSON |

## Evenements de migration cures (integres dans le script)

| Evenement | Periode | De | Vers | Lien MTBC |
|-----------|---------|----|----|-----------|
| Out of Africa | -70000:-40000 | Afrique de l'Est | Eurasie | Divergence L1-L7 du clade humain strict |
| Expansion neolithique | -10000:-5000 | Croissant fertile | Europe, Asie du Sud | Expansion L4 ancestral ? |
| Expansion bantoue | -3000:-500 | Afrique de l'Ouest | Afrique centrale/australe | Dispersion L5/L6 |
| Commerce arabe | 700:1500 | Moyen-Orient | Afrique de l'Est, Asie du Sud | Dispersion L3 ? |
| Colonisation europeenne | 1500:1900 | Europe | Ameriques, Asie, Afrique | Expansion globale L4 |
| Traite transatlantique | 1514:1866 | Afrique Ouest/Centrale | Ameriques | L5/L6 Ameriques, L4 Clade A |
| Engagisme indien | 1834:1920 | Inde | Caraibes, Afrique Est, Fidji | L1/L3 dans les Caraibes |
| Migration moderne | 1950:present | Sud global | Europe, Amerique du Nord | Import de lignees non-L4 |

## Format de sortie : matrice de flux comparable

La sortie cle est une matrice de flux migratoires dans le meme format que la matrice de transitions MTBC produite par `ancestral-reconstruction` :

```csv
from,to,volume,period_start,period_end
West Africa,Caribbean,2500000,1514,1866
West Africa,Brazil,4800000,1514,1866
Central Africa,Caribbean,800000,1600,1850
Europe,Americas,55000000,1500,1900
```

Cela permet une comparaison directe :
```
Correlation(transitions_MTBC[1500-1900], flux_humains[1500-1900]) -> Mantel test
```

## Centroides des pays (integres)

Table de ~200 pays avec latitude/longitude du centroide, utilisee pour :
- Calculer les distances geographiques (Haversine)
- Positionner les pays sur les cartes de migration
- Fournir des coordonnees quand seul le nom du pays est disponible

## Integration

| Skill | Usage |
|-------|-------|
| `ancestral-reconstruction` | Produit les transitions MTBC a comparer |
| `coevolution` | Mantel test entre flux humains et transitions MTBC |
| `slavevoyages` | Source de donnees brutes pour la traite |
| `geo-map` | Cartes avec fleches de migration |
| `molecular-clock` | TMRCA pour overlay chronologique |
| `phylogeography` | Distribution geographique actuelle des lignees |

## Sources de donnees externes

| Source | URL | Format |
|--------|-----|--------|
| SlaveVoyages | slavevoyages.org/voyage/database#downloads | CSV |
| UN Migration Stock | data.un.org | Excel |
| World Bank Bilateral | worldbank.org/en/topic/migration | CSV |
| WHO TB Burden | who.int/teams/global-tuberculosis-programme/data | CSV |

## Dependances

```bash
pip install pandas numpy matplotlib requests openpyxl
```

`openpyxl` est necessaire pour lire les fichiers Excel UN. `requests` pour le telechargement eventuel de donnees.
