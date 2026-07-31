# Rapport de fusion — skills visualisation et bibliothèques Python scientifiques

Onze des treize skills du groupe sont des fiches de documentation de bibliothèques publiques, sans une seule ligne de code (`n_py: 0` dans `skill_health.json`, aucun répertoire `references/`). Seuls `geo-map` et `itol` embarquent du code. Le groupe coûte 5314 caractères de description permanents pour 769 caractères de valeur réelle.

## 1. Nature réelle de chaque skill

| Skill | Plugin | Nature réelle | Code | Verdict |
|---|---|---|---|---|
| geo-map | bio_pop_gen (+symlink redac) | Conventions maison + outil | `scripts/geo_map.py`, 105 Ko, ~2500 lignes | Conserver intact |
| itol | bio_pop_gen | Vrai outil, wrapper API iTOL | 3 scripts, 41 Ko | Conserver intact |
| matplotlib-pro | ia **et** redac (md5 identiques) | Fiche de doc, 1 pépite PGF/LaTeX | 0 | Absorber |
| create-viz | bio_pop_gen (+symlinks ia, redac) | Fiche BI + surface d'invocation utile | 0 | Absorber, garder comme alias |
| data-visualization | ia | Fiche dataviz business | 0 | Écarter |
| matplotlib | ia **et** redac (md5 identiques) | Fiche de doc | 0 | Écarter |
| seaborn | bio_pop_gen (+symlink redac) | Fiche de doc | 0 | Écarter |
| plotly | redac | Fiche de doc | 0 | Écarter |
| geopandas | ia | Fiche de doc | 0 | Écarter |
| shapely | ia | Fiche de doc | 0 | Écarter |
| networkx | ia | Fiche de doc, hors sujet viz | 0 | Écarter |
| statsmodels | ia **et** bio_pop_gen (md5 identiques) | Fiche de doc, hors sujet viz | 0 | Écarter |
| statistical-analysis | ia | Fiche stats business, hors sujet viz | 0 | Écarter |

Symlinks confirmés dans `redac/skills/` : `create-viz`, `geo-map`, `read-scientific-pdf`, `seaborn` pointent vers `bio_population_genetics/skills/`. En revanche `matplotlib`, `matplotlib-pro` et `statsmodels` sont de vraies copies dupliquées (`md5sum` identiques), pas des symlinks : environ 30 Ko de doublons stricts entre plugins.

## 2. Groupe fusionnable et plan concret

Fusionner `matplotlib`, `matplotlib-pro`, `seaborn`, `plotly`, `create-viz` et `data-visualization` en un skill unique.

**Nom** : `sci-figure`, créé dans `bio_population_genetics/skills/` (maison canonique de `geo-map`), symliqué vers `redac/skills/` selon la convention déjà en place.

**Structure** : `SKILL.md` de 150 lignes maximum, plus `scripts/figstyle.py`.

**Condition de réussite** : qu'il livre du code et ne soit pas une douzième fiche de documentation. Le `figstyle.py` doit exposer les presets de revue en réutilisant la table `PRESETS` déjà écrite dans `geo_map.py` lignes 222 à 257 : Nature single 89 mm, Nature double 183 mm à 600 dpi PDF Arial, Science 120 mm Helvetica, PLOS 174 mm TIFF, Cell 174 mm PDF Helvetica, poster 400 mm, slide 330 mm. Bénéfice concret : une figure de données et une carte du même article partagent alors exactement la même largeur, la même police et le même dpi, ce qu'aucune documentation publique ne fournit.

**Ce qu'on préserve de chaque original** :

- `matplotlib-pro` : le backend PGF et la recette `fonttype 42` pour les polices embarquées, plus les layouts GridSpec multi-panneaux.
- `matplotlib` : les `rcParams` de publication.
- `create-viz` : la surface d'invocation (`argument-hint`, `user-invocable: true`), car six skills délèguent vers ce nom.
- `data-visualization` : la table de sélection de graphique et la palette compatible daltonisme, réduites, parce que le skill natif `dataviz` couvre déjà ce terrain avec un déclenchement plus agressif.
- `seaborn` : une ligne sur la grammaire `relplot` / `displot` / `catplot`.
- `plotly` : rien. L'interactif, le 3D et Dash sont hors sujet pour une figure imprimée.

**Description proposée, 271 caractères** :

Figures d'article aux normes des revues : presets Nature/Science/PLOS/Cell (largeur mm, dpi, police, PDF vectoriel), palettes compatibles daltonisme, multi-panneaux GridSpec, export PGF/LaTeX. Pour toute figure de manuscrit, poster ou slide depuis un CSV ou un DataFrame.

## 3. Écartables définitivement — preuves tirées du contenu

**Les six fiches de bibliothèque** (`geopandas`, `shapely`, `networkx`, `statsmodels`, `seaborn`, `plotly`) partagent un plan strictement identique, généré en série : *When to Use, Reference Documentation, Core Principles, Quick Reference, Critical Rules, Anti-Patterns (NEVER)*. Leur section « Reference Documentation » ne renvoie vers rien de local, seulement vers l'URL officielle publique (`https://geopandas.org/` pour geopandas). C'est la définition d'un aide-mémoire sur une bibliothèque que le modèle connaît nativement.

**`data-visualization`** est du conseil dataviz d'entreprise : un formateur de devises `$1.2B` / `$1.5M`, l'exemple de titre « Revenue grew 23% YoY », des sections KPI et dashboard. Il double le skill natif `dataviz`, présent dans le listing avec un déclenchement plus fort.

**`create-viz`** renvoie dès sa ligne 8 vers `../../CONNECTORS.md`, fichier absent des deux plugins : lien mort vérifié. Son cadrage est BI (data warehouse, données NPS, table `orders`, audience « executives ») et il enregistre en `savefig(..., dpi=150)` PNG, sous les standards de soumission. Détail révélateur : `mtbc-bilan` ligne 1631 l'appelle en annonçant « sortie PDF », capacité que le skill n'a pas. La fusion corrige cet écart.

**`statistical-analysis`** contient une section « Percentiles for Business Context » et n'est pas un skill de visualisation ; **`statsmodels`** non plus. Les deux relèvent d'un éventuel groupe statistiques, pas d'ici.

**`matplotlib`** et **`matplotlib-pro`** sont dupliqués à l'octet près entre `ia` et `redac`. `matplotlib-pro` se termine par du boilerplate à en-têtes emoji et une phrase de conclusion générée.

**`geopandas`** et **`shapely`** sont déjà encapsulés derrière la CLI validée de `geo-map`, qui les mentionne comme simples dépendances pip ligne 535. **`networkx`** sert `mtbc-gene-network`, qui embarque son propre code.

## 4. À garder absolument

**`geo-map`** est l'archétype exact du skill à préserver. Il encode des conventions de publication vérifiées, pas de l'API : largeurs de colonne, dpi et format de sortie par revue, et surtout des projections cartographiques validées avec leurs codes EPSG (Robinson pour le monde, Albers Equal Area pour l'Afrique, ETRS89-LAEA EPSG:3035 pour l'Europe), avec mention explicite que Mercator est déconseillé en publication. Ce savoir ne s'improvise pas et ne figure dans aucune documentation de bibliothèque.

**`itol`** est un pipeline d'API réel, pas une fiche : upload d'arbre Newick, pistes d'annotation (`DATASET_COLORSTRIP`, `TREE_COLORS`, `DATASET_SYMBOL`), export SVG/PDF/PNG, presets article / supplement / presentation / poster, légendes MTBC. Il est cité comme cible par `raxml`, `molecular-clock`, `convergent-evolution`, `phylogeography` et `mtbc-gene-network`. Son usage faible tient à sa dépendance à un abonnement iTOL, pas à un défaut du skill.

Note de fiabilité des métriques : `skill_health.json` marque `itol` comme `NO_SKILL_MD` à tort, son `SKILL.md` existe bien (4564 octets).

## 5. Gain chiffré et dépendances croisées

**Descriptions du groupe, par nom unique** : geopandas 592, shapely 566, statsmodels 575, networkx 502, seaborn 501, plotly 453, itol 436, matplotlib 388, geo-map 333, create-viz 273, statistical-analysis 255, data-visualization 255, matplotlib-pro 185. **Total 5314 caractères.**

Les onze noms écartés pèsent **4545 caractères**, remplacés par **271**, soit un **gain net de 4274 caractères**. Le groupe passe de 5314 à 1040 caractères, `geo-map` et `itol` conservant leurs 769 caractères inchangés.

Sur le disque : 3141 lignes et 105 Ko de Markdown disparaissent, plus environ 30 Ko de doublons stricts entre plugins.

**Restriction utile** : dans la session courante, seul le plugin `redac` est chargé, et les skills de `ia` n'apparaissent déjà plus dans le listing, ce qui confirme l'éviction. Le gain immédiatement ressenti porte donc sur les cinq fiches visibles via `redac` (create-viz 273, matplotlib 388, matplotlib-pro 185, plotly 453, seaborn 501), soit **1800 caractères ramenés à 271, gain de 1529 à chaque session de rédaction**. Le reste se matérialisera au rechargement de `ia`.

### Dépendances croisées à réparer avant toute suppression

Sept fichiers citent les noms écartés comme cibles de délégation :

| Fichier | Lignes | Noms cités |
|---|---|---|
| `redac/skills/slide-design/SKILL.md` | 3 (dans sa propre description), 127, 150, 252, 650, 658 | create-viz, seaborn, matplotlib-pro, plotly |
| `redac/skills/slide-polish/SKILL.md` | 276, 924 | create-viz, seaborn, matplotlib-pro, plotly |
| `bio_pathogens/skills/mtbc-bilan/SKILL.md` | 1630, 1631, 1642, 1643 | seaborn, create-viz |
| `bio_pathogens/skills/mtbc-pathway-explain/SKILL.md` | 175, 176 | data-visualization, matplotlib-pro |
| `bio_pathogens/skills/pangenome-enrichment/SKILL.md` | 214 | create-viz |
| `bio_pathogens/skills/phylogeography/SKILL.md` | 192 | create-viz |
| `bio_population_genetics/skills/geo-map/SKILL.md` | 530 | create-viz |

Point d'attention : la **description** de `slide-design` (ligne 3 du frontmatter) nomme elle-même `create-viz` et `seaborn`. Un renommage sec la rendrait incohérente.

En revanche, toutes les occurrences de `geopandas`, `shapely` et `networkx` hors de leurs propres répertoires sont des mentions de bibliothèque (`pip install`, `import`), jamais des appels de skill : leur suppression est sans effet de bord.

**Économie de réparation** : conserver `create-viz` comme alias de `sci-figure` neutralise six des sept réparations.
