---
name: host-pathogen-pair
description: >-
  Academic eco-anthropology research toolkit (Guyeux group, FEMTO-ST).
  Generates geo-temporal co-occurrence tables of ancient host–ancient
  microorganism pairs from two published open-science research corpora:
  SPAAM AncientMetagenomeDir (ancient microbial genomics, covering
  *Mycobacterium*, *Yersinia pestis*, *Salmonella*, etc.) and the AADR
  ancient human genome catalogue (Reich Lab, v66, 16,000+ individuals).
  Output: a TSV of candidate research pairs ranked by Haversine distance
  and temporal overlap, plus a per-project summary for the top co-located
  human groups. Used by the Guyeux group to plan peer-reviewed
  eco-anthropology host–microorganism co-evolution studies, to document
  data availability for a given research question, or to demonstrate
  data absence (a publishable negative finding).

  Utiliser quand : planifier un projet de recherche sur la co-evolution
  hote–microorganisme, valider les paires disponibles pour une
  region/periode donnee, preparer un seminaire ou une candidature
  academique, ou documenter l'absence de paires (cas negatif valorisable
  dans une publication scientifique).
---

# host-pathogen-pair -- Triangulation SPAAM x AADR

## Overview

Outil minimal pour croiser deux ressources publiques canoniques :

- **SPAAM AncientMetagenomeDir** (cote pathogene, 816 entrees, dont 67 *Mycobacterium*)
  -- Fellows Yates et al. 2021 *Scientific Data*, repo GitHub
  `SPAAM-community/AncientMetagenomeDir`, licence CC BY 4.0
- **AADR v66** (cote humain, 19 029 individus anciens) -- Mallick et al. 2024
  *Scientific Data*, Harvard Dataverse doi:10.7910/DVN/FFIDCW, licence CC BY 4.0

Pour chaque pathogene ancien, le skill trouve les humains anciens AADR
co-localises temporellement (delta annees BP) et geographiquement (km Haversine).
Sortie : TSV exhaustif des paires + resume par projet pathogene.

## Quick start

### Pre-requis (faits une fois)

```bash
# 1. Cloner SPAAM (1 MB)
git clone --depth=1 https://github.com/SPAAM-community/AncientMetagenomeDir.git

# 2. Telecharger AADR v66 .anno (14 MB) via API Dataverse
curl -sL "https://dataverse.harvard.edu/api/access/datafile/13663706" -o aadr_v66_1240K.anno
```

### Usage typique

```bash
# Toutes les paires Mycobacterium (default : 500 km, 200 ans BP)
python host_pathogen_pair.py --genus Mycobacterium

# MTBC strict, sortie TSV
python host_pathogen_pair.py --species "Mycobacterium tuberculosis" --out paires.tsv

# Fenetre relachee
python host_pathogen_pair.py --max-km 1000 --max-years 500

# Yersinia pestis (le plus dense, 214 individus SPAAM)
python host_pathogen_pair.py --genus Yersinia
```

### Sortie

TSV avec colonnes :

```
pathogen_project pathogen_species pathogen_site pathogen_country pathogen_age_bp
pathogen_accession pathogen_sample pathogen_material
human_id human_group human_locality human_country human_age_bp
distance_km delta_years
```

Resume console :

```
[SPAAM] 10 pathogenes anciens (filtre genre=Mycobacterium, espece=Mycobacterium tuberculosis)
[AADR ] 19029 humains anciens (age > 0 BP)
[PAIR ] 78 paires hote-pathogene avec distance <= 500.0 km et delta <= 200.0 ans

=== Resume par projet pathogene ===
  Kay2015      37 paires | sites: 1 | top groupes humains: [('Serbia_OttomanPeriod_Ottoman', 14), ...]
  Sabin2020    36 paires | sites: 1 | top groupes humains: [('Denmark_EarlyModern', 17), ...]
  Jager2022     5 paires | sites: 1 | top groupes humains: [('Serbia_OttomanPeriod_Ottoman', 2), ...]
```

## Cas typiques

### 1. Pre-Columbien Bolivien (Bos2014 *M. pinnipedii* x Tiwanaku)

```bash
python host_pathogen_pair.py --species "pinnipedii"
```

**Resultat marquant** : 12 paires `Bolivia_Akapana_1000BP_Tiwanaku` x `Bos2014`
avec delta = 0 ans et distance = 275 km. Le projet El Yaral livre *M. pinnipedii*,
Tiwanaku livre des genomes humains synchroniques. Bombshell pour eco-anthropo
andine.

### 2. Vac Hongrie (Kay2015 / Jager2022 x Serbia Ottoman)

```bash
python host_pathogen_pair.py --species "Mycobacterium tuberculosis"
```

**Resultat** : 16 paires Vac x Serbia Ottoman. La crypte dominicaine de Vac avec
genealogies nominatives + panel humain ottoman = projet de diffusion MTBC dans
l'aire balkanique.

### 3. Cas negatif (Afrique de l'Ouest)

Aucune paire detectee pour *Mycobacterium* avec humains anciens du Senegal,
Mali, Burkina, Ghana. Trou documente : ni MTBC ancien ouest-africain publie,
ni humains AADR ouest-africains < 500 BP. **Donnee negative valorisable** :
justifie un projet d'echantillonnage Ziehl-Neelsen WWI tirailleurs (cf.
cahier de labo 2026-05-16 entrees 42-44).

## Code source

Script Python single-file dans le repertoire de travail :

```python
# voir host_pathogen_pair.py (~150 lignes, dependances stdlib uniquement)
```

Repo de reference : `/home/christophe/docs/codes/mtbc/musee_de_lhomme/experiments/2026-05-16_host-pathogen-pair/`

## Limites connues

- SPAAM BP vs AADR BP "before 1950 CE" : ecart de 76 ans non corrige (marginal
  pour fenetres > 100 ans)
- Distance Haversine spherique, pas de cout topographique
- Pas de filtre par couverture humaine (tous les AADR equivalents)
- Pas de filtre par materiel SPAAM (bone / tooth / lung tissue / calcified
  nodule confondus)

## Extensions possibles

- Cartographie matplotlib + cartopy (1 jour de plus)
- Pairing par lignee MTBC (croisant TBannotator pour lien souches modernes
  apparentees aux ancestres anciens)
- Generation BibTeX automatique pour Methods d'article
- Frontend agentique (Claude prend une question en langage naturel, lance le
  script, produit un rapport)

## Citations a inclure si paire est utilisee

- **SPAAM AncientMetagenomeDir** : Fellows Yates et al. 2021 *Scientific Data*
  8:31 (doi:10.1038/s41597-021-00816-y) ET la paper source du projet specifique
  (Bos2014, Kay2015, Sabin2020, etc.)
- **AADR** : Mallick et al. 2024 *Scientific Data* 11:182
  (doi:10.1038/s41597-024-03031-7) avec la version exacte (v66 ici)
- **Compatibilite** : skill cite dans le manuscrit (commit hash recommande)
