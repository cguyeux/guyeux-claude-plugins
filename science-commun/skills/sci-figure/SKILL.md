---
name: sci-figure
description: >-
  Figures d'article aux normes des revues : presets Nature/Science/PLOS/Cell
  (largeur mm, dpi, police, PDF vectoriel), palettes compatibles daltonisme,
  multi-panneaux GridSpec, export PGF/LaTeX. Pour toute figure de manuscrit,
  poster ou slide depuis un CSV ou un DataFrame.
argument-hint: "<data.csv|DataFrame> [type de graphique] [--preset nature_double]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# sci-figure : Figures de données qualité publication

Produit des figures aux dimensions exactes exigées par la revue visée, en
partageant ses presets avec le skill `geo-map`. Une figure de données et une
carte du même article sortent ainsi à la même largeur, avec la même police et le
même dpi, sans réglage manuel.

Pour une carte géographique, utiliser `geo-map`. Pour un arbre phylogénétique
annoté, `itol`. Pour vérifier visuellement des figures déjà intégrées à un
manuscrit, `fig-check`.

## Le script

`scripts/figstyle.py` porte toute la mécanique. Il lit la table `JOURNAL_PRESETS`
directement dans `geo-map/scripts/geo_map.py` (analyse syntaxique, sans importer
geopandas), de sorte que les deux skills ne peuvent pas diverger. Une copie de
repli sert si `geo-map` est absent ; `--check-sync` signale toute dérive.

```bash
python3 scripts/figstyle.py --list          # presets disponibles
python3 scripts/figstyle.py --check-sync    # vérifier l'accord avec geo-map
python3 scripts/figstyle.py --demo essai --preset nature_double
```

| Preset | Largeur | dpi | Format de dépôt | Police |
|---|---|---|---|---|
| `nature_single` | 89 mm | 600 | PDF | Arial |
| `nature_double` | 183 mm | 600 | PDF | Arial |
| `science` | 120 mm | 600 | PDF | Helvetica |
| `plos` | 174 mm | 300 | TIFF | Arial |
| `cell` | 174 mm | 300 | PDF | Helvetica |
| `generic` | 174 mm | 300 | PNG | DejaVu Sans |
| `poster` | 400 mm | 300 | PNG | DejaVu Sans |
| `slide` | 330 mm | 200 | PNG | DejaVu Sans |

## Usage

```python
import sys; sys.path.insert(0, "<skill>/scripts")
import figstyle as fs
import pandas as pd

df = pd.read_csv("data/lineage_counts.csv")

fig, ax = fs.new_figure("nature_double")        # applique déjà les rcParams
ax.bar(df["lineage"], df["n"], color=fs.PALETTE_CATEGORICAL[0])
ax.set_xlabel("Lignée")
ax.set_ylabel("Isolats séquencés")
fs.save(fig, "figures/fig2", "nature_double")   # écrit figures/fig2.pdf
```

Multi-panneaux, avec les étiquettes `a`, `b`, `c` de la convention Nature :

```python
fig, axes = fs.panel_grid("nature_double", nrows=2, ncols=2)
...
fs.panel_labels(axes)
fs.save(fig, "figures/fig3", "nature_double")
```

`panel_grid` passe ses arguments supplémentaires à `gridspec_kw`, ce qui couvre
les panneaux de tailles inégales (`width_ratios=[2, 1]`).

## Sortie vectorielle par défaut

`save()` écrit **toujours** un PDF vectoriel. Le raster n'est produit qu'avec
`raster=True`, et alors au format et au dpi exigés par la revue (TIFF 300 dpi
pour PLOS). Il n'y a pas de sortie PNG basse résolution : les 150 dpi de
l'ancien `create-viz` étaient sous les standards de soumission.

```python
fs.save(fig, "figures/fig2", "plos", raster=True)   # fig2.pdf + fig2.tiff
fs.save(fig, "figures/fig2", "nature_double", pgf=True)  # + fig2.pgf
```

Deux réglages non négociables, appliqués par `apply_style()` :

- `pdf.fonttype = 42` (TrueType) : le texte reste sélectionnable et éditable dans
  Illustrator ou Inkscape. Le défaut Type 3 casse l'édition, et plusieurs revues
  le refusent.
- pas de `bbox_inches="tight"` à l'enregistrement : il rogne la figure sur son
  contenu et fait perdre la largeur du preset (183 mm ressortent à 182). C'est
  `constrained_layout` qui ajuste le contenu dans le format imposé.

Si Arial ou Helvetica ne sont pas installées, matplotlib retombe silencieusement
sur DejaVu Sans. Vérifier avec `pdffonts figure.pdf` avant un dépôt qui impose
la police.

## Choix du type de graphique

| Relation à montrer | Graphique |
|---|---|
| Évolution temporelle | Courbe |
| Comparaison entre catégories | Barres, horizontales si les libellés sont longs |
| Composition | Barres empilées ou aires ; camembert seulement sous 6 parts |
| Distribution | Histogramme, densité, ou boîte à moustaches |
| Corrélation | Nuage de points |
| Matrice de relations | Carte de chaleur |
| Classement | Barres horizontales triées par valeur |
| Distribution géographique | `geo-map` |

Avec seaborn, préférer les fonctions de niveau figure (`relplot`, `displot`,
`catplot`) : elles gèrent seules le facettage par `col` et `row`. Mais créer la
figure avec `fs.new_figure()` et tracer avec les fonctions de niveau axes
(`sns.scatterplot(..., ax=ax)`) quand le format de la revue doit être garanti,
car les fonctions de niveau figure créent leur propre figure et ignorent le
`figsize` du preset.

## Règles de lisibilité

- Palette `fs.PALETTE_CATEGORICAL` par défaut : le couple bleu/orange reste
  discriminable en deutéranopie, là où rouge/vert se confond (8 % des hommes).
  Séquentiel `YlOrRd`, divergent `RdBu_r`. Jamais `jet` ni `rainbow`, qui créent
  des gradients illusoires.
- Axe des ordonnées à zéro pour les barres ; toute rupture d'axe explicitée.
- Catégories triées par valeur, sauf ordre naturel (temps, lignées).
- Échelles identiques entre panneaux comparés.
- Titre d'axe avec l'unité ; pas de titre dans la figure elle-même quand la
  revue impose une légende séparée (`\caption`).
- Contrôler la taille du texte à la taille finale d'impression, pas à l'écran :
  un preset respecté garantit qu'aucune remise à l'échelle n'aura lieu.

## Intégration LaTeX

```latex
\includegraphics[width=\linewidth]{figures/fig2.pdf}
```

La largeur du preset correspondant à la colonne de la revue, `width=\linewidth`
ne redimensionne rien et les corps de texte restent à la taille voulue. Pour un
rendu typographique strictement identique au manuscrit, exporter en PGF
(`pgf=True`) et faire `\input{figures/fig2.pgf}`.
