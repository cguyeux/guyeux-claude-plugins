---
name: domestication-pathways
description: >-
  Aggregate domestication centres, dispersal routes and Neolithic transition data for
  coevolution studies with the M. tuberculosis complex. Wraps four families of open sources:
  zooarchaeology (ABMAP, AADR animal subset), archaeobotany (ADEMNES, BRAIN), ancient human
  DNA (AADR) and global radiocarbon (p3k14c, CONTEXT, AgriChange). Includes curated tables
  of origin centres (Fertile Crescent, Indus, Yangtze, Sahel, Mesoamerica, Andes, New
  Guinea, Ethiopia, Green Sahara, Amazonia), dispersal routes (LBK, Cardial, Bantu, Steppe,
  Austronesian, Lapita, Trans-Saharan, Columbian Exchange) and timeline events linked to
  MTBC emergence. Use when building the coevolutionary background of M. bovis, M. caprae or
  M. orygis, framing the emergence of M. tuberculosis sensu stricto from a M. canettii-like
  ancestor through Neolithic sedentarisation, relating MTBC TMRCA to agricultural
  transitions, or preparing figures linking livestock dispersal to zoonotic MTBC lineages.
argument-hint: "<command: centers|routes|timeline|parse|fetch> [options]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebFetch
---

# Domestication Pathways : Centres, routes et chronologies pour co-évolution MTBC

Skill complémentaire à `migration-data` (qui couvre les flux humains avec
liens MTBC à granularité large) et à `indian-ocean-voyages` (routes maritimes
historiques). Ici on cible le **paquet co-évolutif domestication** : centres
d'origine, routes de dispersion d'animaux et de plantes, et chronologie de
la néolithisation, articulés avec les lignées MTBC zoonotiques (*M. bovis*,
*M. caprae*, *M. orygis*) et l'émergence du *M. tuberculosis* moderne à partir
d'un ancêtre *M. canettii*-like.

## Phase 1 : Découverte (OBLIGATOIRE)

### 1. Quelle source ?

| Source | Contenu | Couverture | Format | Usage MTBC |
|--------|---------|------------|--------|------------|
| **ABMAP** | 61 k mesures, 24 700 os domestiques | Néolithique–moderne, Britain | CSV (ADS) | Zoométrie cheptel, *M. bovis* |
| **AADR** (humain + animal) | ~10 000 individus anciens génotypés | Mondiale, Pléistocène–historique | TSV/EIGENSTRAT | Ancrage chronologique des routes |
| **ADEMNES** | 533 sites est-méditerranéens, macrorestes | Épipaléo–Médiéval, Levant | XML/Web | Cadrage Néolithique levantin |
| **BRAIN** | 739 sites italo-méditerranéens | Holocène | CSV (Scientific Data 2024) | Cadrage Néolithique méditerranéen |
| **p3k14c** | 77 393 dates ¹⁴C globales | Mondiale, Pléistocène final–récent | CSV | Pivot chronologique néolithique |
| **CONTEXT** | Datations Néolithique européen | Europe | CSV (Köln) | Diffusion LBK, Cardial |
| **AgriChange** | ¹⁴C Méditerranée NO + Rhin | Néolithique | CSV/XLSX | Transition Méso-Néo locale |

### 2. Quelle période ?

- **Pléistocène final / pré-domestication** (-15 000 à -12 000) : mise en place des conditions, contexte climatique
- **Néolithique ancien** (-12 000 à -7 000) : domestications primaires (chèvre, mouton, bovin, blé, orge, riz, lentille)
- **Néolithique tardif / Âge du Bronze** (-7 000 à -2 000) : diffusions secondaires (LBK, Cardial, Bantu Stage I, Yamnaya/Steppe)
- **Âge du Fer / historique** (-2 000 à 1500) : routes commerciales (Soie, Trans-Saharan), expansions austronésiennes
- **Échange colombien** (1492-1700) : redistribution mondiale (porc, cheval, vache → Amériques ; pomme de terre, maïs → Vieux Monde)

### 3. Quel format de sortie ?

- `centers` : centres d'origine (taxon, lieu, lat/lon, période, lien MTBC)
- `routes` : routes de dispersion (from, to, taxon, période, mécanisme, source, lien MTBC)
- `timeline` : chronologie événementielle pour overlay TMRCA MTBC
- `parse <subcommand>` : parsing de fichiers téléchargés (ABMAP, ADEMNES, AADR, p3k14c, BRAIN)

## Phase 2 : Commandes

### Script principal

```bash
# 1. Centres d'origine curés
python3 scripts/domestication_pathways.py centers \
  --type animal --period -12000:-6000 -o animal_centers.csv
python3 scripts/domestication_pathways.py centers \
  --type plant --region "Old World" -o plant_centers_old.csv
python3 scripts/domestication_pathways.py centers \
  --type all -o all_centers.csv

# 2. Routes curées (filtrables par taxon ou période)
python3 scripts/domestication_pathways.py routes \
  --species cattle --period -8000:0 -o cattle_routes.csv
python3 scripts/domestication_pathways.py routes \
  --species "wheat,barley" -o cereal_routes.csv
python3 scripts/domestication_pathways.py routes \
  --mtbc-link "M. bovis" -o bovis_routes.csv

# 3. Timeline avec overlay TMRCA MTBC
python3 scripts/domestication_pathways.py timeline \
  --tmrca mtbc_tmrca.csv --period -12000:1500 -p timeline.png

# 4. Parser de bases externes
python3 scripts/domestication_pathways.py parse abmap \
  --input abmap.csv --species "cattle,sheep" -o abmap_summary.csv
python3 scripts/domestication_pathways.py parse aadr \
  --input v54.1.AADR.anno --period -8000:-3000 \
  --region Europe -o aadr_neolithic_eu.csv
python3 scripts/domestication_pathways.py parse p3k14c \
  --input p3k14c.csv --bbox 30,50,-10,30 \
  --period -8000:-3000 -o c14_neolithic_med.csv
python3 scripts/domestication_pathways.py parse ademnes \
  --input ademnes.csv -o ademnes_summary.csv
python3 scripts/domestication_pathways.py parse brain \
  --input brain.csv --period -6000:-2000 -o brain_italy.csv

# 5. URLs et instructions de téléchargement
python3 scripts/domestication_pathways.py fetch --source abmap
python3 scripts/domestication_pathways.py fetch --source aadr
python3 scripts/domestication_pathways.py fetch --source p3k14c
```

## Arguments par commande

### `centers`

| Argument | Description |
|----------|-------------|
| `--type` | `animal`, `plant`, `human`, `all` |
| `--region` | `Old World`, `New World`, ou région précise (`Fertile Crescent`...) |
| `--period` | Plage en années calibrées (ex. `-12000:-6000`, négatif = BCE) |
| `--mtbc-link` | Filtrer par lignée MTBC (`M. bovis`, `M. caprae`, `M. orygis`, `MTBC ancestor`) |

### `routes`

| Argument | Description |
|----------|-------------|
| `--species` | Filtrer par taxon (virgules : `cattle,sheep,goat`) |
| `--mechanism` | `demic`, `cultural`, `mixed`, `colonial` |
| `--period` | Plage en années calibrées |
| `--mtbc-link` | Filtrer par lignée MTBC |
| `--source-network` | `LBK`, `Cardial`, `Bantu`, `Steppe`, `Austronesian`, `Trans-Saharan`, `Columbian Exchange` |

### `timeline`

| Argument | Description |
|----------|-------------|
| `--tmrca` | CSV des TMRCA MTBC pour overlay (colonnes : `lineage,year_start,year_end,label`) |
| `--period` | Période d'affichage |
| `-p` | Figure (PNG/PDF) |

### `parse abmap`

| Argument | Description |
|----------|-------------|
| `--input` | CSV ABMAP téléchargé depuis ADS |
| `--species` | Filtrer par espèce |
| `--period` | Filtrer par période archéologique |

### `parse aadr`

| Argument | Description |
|----------|-------------|
| `--input` | Fichier `.anno` ou `.tsv` du dump AADR |
| `--period` | Filtrer sur `Date_BP` (calibré BP) |
| `--region` | Filtrer sur `Political_Entity` ou `Locality` |
| `--type` | `human` (par défaut), `animal` |

### `parse p3k14c`

| Argument | Description |
|----------|-------------|
| `--input` | CSV p3k14c |
| `--bbox` | `lat_min,lat_max,lon_min,lon_max` |
| `--period` | Plage en années calibrées BP ou BCE/CE |
| `--material` | Filtrer matériau (`charcoal`, `bone`, `seed`...) |

### `parse ademnes` / `parse brain`

| Argument | Description |
|----------|-------------|
| `--input` | CSV/XML téléchargé |
| `--period` | Filtre période |
| `--taxon` | Filtre taxon (e.g. `Triticum`, `Hordeum`) |

### `fetch`

| Argument | Description |
|----------|-------------|
| `--source` | `abmap`, `aadr`, `ademnes`, `brain`, `p3k14c`, `context`, `agrichange` |

### Arguments communs

| Argument | Default | Description |
|----------|---------|-------------|
| `-o` | none | Fichier CSV de sortie |
| `-p` | none | Figure (PNG/PDF) |
| `--summary` | off | Résumé JSON |

## Centres d'origine curés (intégrés dans le script)

Les coordonnées et périodes sont les meilleures estimations consensuelles de
la littérature (Zeder 2008, Larson et al. 2014, Fuller et al. 2014). Les sous-
espèces *Bos taurus* / *Bos indicus* sont distinctes (centres séparés).

### Centres animaux

| Taxon | Centre | Lat/Lon | Période | Lien MTBC |
|-------|--------|---------|---------|-----------|
| Goat (*Capra hircus*) | Zagros / Croissant fertile | 35.0, 47.0 | -10 500:-9 500 | *M. caprae* |
| Sheep (*Ovis aries*) | Croissant fertile (E. Anatolia) | 38.0, 43.0 | -10 500:-9 500 | *M. caprae* |
| Cattle taurine (*Bos taurus*) | Croissant fertile (Euphrate moyen) | 36.5, 38.5 | -10 800:-10 200 | *M. bovis* |
| Cattle indicine (*Bos indicus*) | Vallée de l'Indus | 28.0, 70.0 | -8 000:-7 000 | *M. bovis* (lignages indicins) |
| Pig (*Sus scrofa*) | Anatolie + Chine indépendamment | 39.0, 32.0 / 32.0, 110.0 | -10 500:-8 500 | (pas de lien MTBC connu) |
| Horse (*Equus caballus*) | Steppes pontiques (Botai/Yamnaya) | 50.0, 55.0 | -3 700:-3 000 | (pas de lien MTBC) |
| Donkey (*Equus asinus*) | Afrique NE (Nubie/Égypte) | 22.0, 32.0 | -5 000:-4 000 | (rares cas *M. bovis*) |
| Camel dromedary (*Camelus dromedarius*) | Arabie SE | 22.0, 55.0 | -3 000:-1 000 | (cas signalés *M. bovis*) |
| Camel Bactrian (*Camelus bactrianus*) | Asie centrale | 42.0, 72.0 | -2 500:-1 500 | (cas signalés) |
| Yak (*Bos grunniens*) | Plateau tibétain | 33.0, 90.0 | -3 000:-2 000 | (lien possible *M. bovis*) |
| Water buffalo (*Bubalus bubalis*) | Vallée de l'Indus + Chine | 28.0, 70.0 | -4 000:-3 000 | *M. bovis* signalé |
| Llama / Alpaca | Andes (Puna) | -16.0, -69.0 | -5 000:-3 500 | (pas de lien MTBC documenté) |
| Turkey (*Meleagris gallopavo*) | Mésoamérique | 19.0, -99.0 | -2 000:0 | (pas de lien MTBC) |
| Chicken (*Gallus gallus*) | Asie SE (vallée du Mékong) | 14.0, 105.0 | -6 000:-3 000 | (pas de lien MTBC humain) |
| Reindeer (*Rangifer tarandus*) | Sibérie + Fennoscandie | 65.0, 80.0 | -1 000:500 | (cas signalés *M. caprae*) |

### Centres végétaux

| Taxon | Centre | Lat/Lon | Période |
|-------|--------|---------|---------|
| Wheat einkorn / emmer | Croissant fertile (Karaca Dağ) | 37.5, 39.5 | -10 500:-9 500 |
| Barley (*Hordeum vulgare*) | Croissant fertile | 36.0, 38.0 | -10 500:-9 500 |
| Lentil, pea, chickpea | Croissant fertile | 36.0, 38.0 | -10 500:-9 500 |
| Rice (*Oryza sativa japonica*) | Yangtze moyen | 30.5, 113.0 | -9 000:-7 000 |
| Rice (*Oryza sativa indica*) | Gange / Indus | 25.0, 80.0 | -7 000:-5 000 |
| Foxtail / Broomcorn millet | Bassin du fleuve Jaune | 41.0, 120.0 | -8 000:-6 000 |
| Pearl millet (*Pennisetum*) | Sahel ouest-africain | 16.0, -2.0 | -4 500:-3 500 |
| Sorghum | Sahel central | 14.0, 25.0 | -5 000:-3 500 |
| Tef (*Eragrostis tef*) | Plateau éthiopien | 9.0, 39.0 | -3 000:-1 000 |
| Maize (*Zea mays*) | Mésoamérique (Balsas) | 18.0, -100.0 | -9 000:-6 000 |
| Bean, squash | Mésoamérique + Andes | 19.0, -99.0 | -8 000:-5 000 |
| Potato (*Solanum tuberosum*) | Andes (lac Titicaca) | -16.0, -69.0 | -8 000:-5 000 |
| Quinoa | Andes | -16.0, -68.0 | -5 000:-3 000 |
| Manioc (*Manihot esculenta*) | Amazonie SO | -10.0, -65.0 | -8 000:-6 000 |
| Sweet potato | Andes / Amérique tropicale | -10.0, -75.0 | -3 000:-1 000 |
| Banana / sugarcane / taro | Nouvelle-Guinée (Kuk) | -5.8, 144.3 | -7 000:-5 000 |
| Coffee (*Coffea arabica*) | Plateau éthiopien | 9.0, 39.0 | 600:1 000 (CE) |

### Centres humains (foyers néolithiques)

Les foyers humains correspondent aux sociétés où la transition a été
**autochtone** et qui ont ensuite essaimé. Ils recoupent en grande partie les
centres animaux/végétaux mais sont conceptuellement distincts.

| Foyer | Région | Lat/Lon | Période |
|-------|--------|---------|---------|
| Levant Sud / PPNB | Jericho, Mureybet | 32.0, 36.0 | -10 500:-8 500 |
| Anatolie centrale | Çatalhöyük, Aşıklı | 38.0, 33.0 | -8 500:-7 000 |
| Yangtze / Yellow River | Liangzhu, Daxi | 30.0, 113.0 | -7 000:-4 000 |
| Vallée de l'Indus | Mehrgarh | 29.0, 67.0 | -7 000:-5 000 |
| Sahel | Dhar Tichitt, Kintampo | 17.0, -10.0 | -4 000:-2 000 |
| Vallée du Nil | Fayum, Merimde | 29.5, 31.0 | -6 000:-4 500 |
| Plateau éthiopien | (pré-aksumite) | 9.0, 39.0 | -3 000:-500 |
| Mésoamérique | Vallée de Mexico, Oaxaca | 19.0, -99.0 | -8 000:-3 000 |
| Andes centrales | Bassin de Titicaca | -16.0, -69.0 | -8 000:-3 000 |
| Amazonie SO | Llanos de Mojos | -14.0, -65.0 | -8 000:-3 000 |
| Nouvelle-Guinée | Kuk Swamp | -5.8, 144.3 | -7 000:-4 000 |
| Eastern Woodlands | Mississippi moyen | 38.0, -90.0 | -3 000:-1 000 |

## Routes de dispersion curées (intégrées)

Format de sortie identique à `migration-data` et `indian-ocean-voyages` pour
permettre la concaténation des matrices :

```csv
from_region,to_region,taxon,mechanism,period_start,period_end,source_network,reference,mtbc_link
```

| De | Vers | Taxon | Mécanisme | Période | Réseau | Lien MTBC |
|----|------|-------|-----------|---------|--------|-----------|
| Croissant fertile | Anatolie ouest | Cattle, sheep, goat | demic | -7 000:-6 500 | LBK pré- | Diffusion *M. caprae*, *M. bovis* |
| Anatolie ouest | Balkans | Cattle, sheep, goat, wheat, barley | demic | -6 500:-6 000 | LBK / Starčevo | *M. bovis* + *M. caprae* en Europe SE |
| Balkans | Europe centrale (LBK) | Cattle, sheep, goat, cereals | demic | -5 500:-4 900 | Linearbandkeramik | Émergence *M. tuberculosis* moderne en Europe ? |
| Anatolie ouest | Méditerranée occidentale | Sheep, goat, cereals | maritime+demic | -6 000:-5 500 | Cardial / Impressed Ware | *M. caprae*, *M. bovis* en Iberia |
| Mésopotamie | Inde NO | Cattle taurine, wheat, barley | mixed | -5 000:-3 000 | (pré-Indus) | Hybridation taurine × indicine |
| Vallée de l'Indus | Asie SE | Cattle indicine, water buffalo | demic | -3 000:-1 500 | (Bronze Age) | *M. bovis* en Asie SE |
| Yangtze | Asie SE | Rice japonica, pig | demic | -4 000:-2 000 | Austroasiatic | (pas de lien MTBC direct) |
| Taïwan | Polynésie / Madagascar | Pig, chicken, taro, banana | maritime | -3 000:1 000 | Austronesian / Lapita | Liens L1 Madagascar |
| Sahel ouest | Forêt + Afrique centrale | Pearl millet, sorghum, cattle | demic | -3 000:-1 000 | Bantu Stage I | *M. africanum* L5/L6 + *M. bovis* africain |
| Afrique centrale | Afrique australe | Cattle, sorghum, millet | demic | -1 000:500 | Bantu Stage II | *M. bovis* / *M. tuberculosis* en Afrique australe |
| Steppes pontiques | Europe N | Horse, dairy, secondary products | demic+cultural | -3 000:-2 000 | Yamnaya / Corded Ware | (pas de lien MTBC direct mais brassage des cheptels) |
| Egypte | Sahara central | Cattle, sheep, goat | mixed | -7 000:-5 000 | Green Sahara | Cheptels nord-africains, *M. bovis* |
| Sahara central | Sahel | Cattle, ovins, caprins | demic | -5 000:-3 000 | Pastoral Sahara | Diffusion zoonotique au Sahel |
| Egypte | Nubie / Corne | Cattle, donkey, cereals | mixed | -4 000:-2 000 | Trans-Saharan early | Cheptels Corne de l'Afrique |
| Asie centrale | Chine N | Wheat, barley | cultural | -3 000:-1 500 | Steppe → Yangshao | (cadrage Néolithique tardif) |
| Méditerranée | Asie centrale | Sheep, goat, cereals | mixed | -3 000:1 500 | Silk Road précurseur | Brassage cheptels eurasiens |
| Mésoamérique | Amérique du Sud | Maize, beans, squash | cultural | -4 000:-1 000 | Pré-Columbian | (Amériques sans MTBC humain pré-colombien massif) |
| Andes | Amérique du Sud | Potato, quinoa, llama | demic | -3 000:0 | Pré-Columbian | (pas de lien MTBC) |
| Pacific NW | Mésoamérique | Turkey, dog | cultural | -2 000:1 500 | Pré-Columbian | (pas de lien MTBC) |
| Vieux Monde | Amériques | Cattle, sheep, pig, horse | colonial | 1492:1700 | Columbian Exchange | Introduction massive *M. bovis* aux Amériques |
| Amériques | Vieux Monde | Maize, potato, manioc | colonial | 1492:1700 | Columbian Exchange | Pression démographique post-colombienne |
| Indes orientales | Mascareignes / Cap | Cattle indicine, sheep | colonial | 1600:1800 | VOC / Carreira da Índia | *M. bovis* indicine vers océan Indien |
| Afrique de l'Est | Madagascar | Zebu, sheep | maritime | 800:1500 | Swahili-Arab | *M. bovis* à Madagascar |
| Croissant fertile | Égypte | Sheep, goat, wheat, barley | demic | -7 000:-5 500 | (Levant → Nil) | *M. caprae* en Égypte |
| Anatolie | Caucase / Iran | Cattle, sheep, goat, cereals | demic | -7 500:-6 000 | (early N. spread) | Cheptels du Caucase |

## Timeline événementielle (intégrée)

Événements clés pour overlay TMRCA MTBC :

| Événement | Période | Lien MTBC |
|-----------|---------|-----------|
| Domestication primaire animale Croissant fertile | -10 800:-9 500 | Émergence ancestrale *M. bovis*, *M. caprae* |
| Domestication primaire céréales Croissant fertile | -10 500:-9 500 | Sédentarisation, contexte d'émergence MTBC moderne |
| Domestication rice Yangtze | -9 000:-7 000 | (pas de lien direct mais sédentarisation) |
| Pre-Pottery Neolithic B (PPNB) | -8 500:-7 000 | Cheptels mixtes, contact intensif animal-humain |
| Émergence MTBC sensu stricto (TMRCA Bos & Comas) | -6 000:-4 000 | Émergence du clade *M. tuberculosis* depuis ancêtre canettii-like |
| LBK expansion Europe centrale | -5 500:-4 900 | Diffusion massive de cheptels et *M. bovis*/*M. caprae* en Europe |
| Cardial expansion Méditerranée occidentale | -6 000:-5 000 | *M. caprae* en Iberia, France méd. |
| Néolithique tardif égyptien | -5 500:-4 000 | Cheptels nord-africains, contact avec MTBC |
| Domestication Indus (cattle indicine) | -8 000:-7 000 | Lignage *M. bovis* indicin |
| Domestication horse (Botai) | -3 700:-3 000 | (pas de lien MTBC direct) |
| Yamnaya / Steppe expansion | -3 000:-2 500 | Brassage cheptels eurasiens |
| Bantu Stage I (West Africa → Central Africa) | -3 000:-1 000 | Diffusion L5/L6 + *M. bovis* africain |
| Bantu Stage II (Central → Southern Africa) | -1 000:500 | *M. bovis* en Afrique australe |
| Austronesian expansion (Taiwan → Pacific/Madagascar) | -3 000:1 000 | Liens L1 Madagascar (cf. indian-ocean-voyages) |
| Trans-Saharan caravan trade | -1 000:1 500 | Diffusion *M. bovis* via cheptels |
| Columbian Exchange | 1492:1700 | Introduction massive *M. bovis* aux Amériques |

## Articulation avec autres skills

Pour éviter la duplication avec `migration-data` (qui contient déjà l'expansion
bantoue et la transition néolithique européenne), la convention adoptée ici
est la suivante :
- `migration-data` → mouvements humains seuls, événements de niveau global
- `domestication-pathways` → couplage humain + animal + plante, granularité
  taxonomique fine, parsers de bases archéologiques spécialisées
- Quand les deux skills couvrent un même événement (ex. expansion bantoue),
  l'entrée de `domestication-pathways` apporte les **co-dispersés** (cheptel,
  cultivars) et le détail des stages I/II

| Skill | Usage |
|-------|-------|
| `migration-data` | Flux humains globaux (atlantique, Out-of-Africa, etc.) |
| `indian-ocean-voyages` | Routes maritimes océan Indien historique |
| `helicobacter-pylori-phylogeography` | Cadre théorique pathogène = traceur |
| `ancestral-reconstruction` | Matrice de transitions MTBC à comparer |
| `coevolution` | Test de Mantel entre routes domestication et phylogénie |
| `beast2-phylogeography` | TMRCA MTBC pour overlay sur timeline |
| `geo-map` | Cartes des centres et flèches de routes |
| `d-place` | Modes de subsistance contemporains des sociétés |

## Sources de données externes

| Source | URL | Format | Licence |
|--------|-----|--------|---------|
| ABMAP | https://archaeologydataservice.ac.uk/archives/view/abmap/ | CSV (web search) | ADS terms |
| AADR | https://reich.hms.harvard.edu/allen-ancient-dna-resource-aadr-downloadable-genotypes-present-day-and-ancient-dna-data | TSV/EIGENSTRAT | Open |
| ADEMNES | https://www.ademnes.de/ | XML/Web | Académique |
| BRAIN | https://www.nature.com/articles/s41597-024-03346-5 | CSV | CC-BY |
| p3k14c | https://www.nature.com/articles/s41597-022-01118-7 | CSV | CC0 |
| CONTEXT | http://context-database.uni-koeln.de/download.php | CSV | Académique |
| AgriChange | https://openarchaeologydata.metajnl.com/articles/10.5334/joad.72 | CSV/XLSX | CC-BY |

## Dépendances

```bash
pip install pandas numpy matplotlib requests openpyxl
```

## Notes méthodologiques

- **Sous-espèces *Bos taurus* / *Bos indicus*** : centres distincts (Croissant
  fertile vs Indus), à conserver séparés car les lignages *M. bovis* présentent
  une structure populationnelle différente entre les deux hôtes.
- **Domestications non-Old World** : llama, alpaca, turkey, manioc, maïs,
  pomme de terre intégrés. Pas de lien MTBC humain pré-colombien massif
  documenté, mais le **Columbian Exchange** redistribue le cheptel européen
  aux Amériques (introduction massive de *M. bovis*).
- **Émergence du MTBC moderne** : la TMRCA estimée (~6 000-4 000 BP) coïncide
  avec le Néolithique tardif. La sédentarisation (densité humaine + promiscuité
  avec le cheptel + tuberculose bovine) est le facteur d'émergence putatif
  principal. Voir Comas et al. 2013 Nat Genet, Bos et al. 2014 Nature.
- **Limites** : les centres et routes curés ici reflètent un consensus 2010-
  2025. La paléogénétique fait encore évoluer les estimations (cf. cattle
  introgression, multi-événement vs monocentriste). Toujours croiser avec une
  référence récente.
