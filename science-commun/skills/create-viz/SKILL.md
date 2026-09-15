---
name: create-viz
description: >-
  Alias historique de `sci-figure`, conserve pour les skills qui l'invoquent
  encore par ce nom (slide-design, mtbc-bilan). Toute demande de figure
  d'article, de graphique de publication ou de visualisation de donnees doit
  etre traitee par `sci-figure`, qui porte les presets de revues et le style
  partage avec `geo-map`.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
user-invocable: true
---

# /create-viz : alias de `sci-figure`

Ce skill a fusionne dans **`sci-figure`** le 2026-07-30, avec `matplotlib`,
`matplotlib-pro`, `seaborn`, `plotly` et `data-visualization`.

**Que faire : lire et appliquer
`bio_population_genetics/skills/sci-figure/SKILL.md`.** Tout s'y trouve, y
compris `scripts/figstyle.py` qui partage largeur, police et resolution avec
`geo_map.py` pour qu'une figure et une carte du meme article soient coherentes.

## Pourquoi cet alias existe

Le nom `create-viz` reste cite par d'autres skills (notamment `slide-design`,
qui le nomme dans sa propre description en frontmatter, et `mtbc-bilan`).
Supprimer le nom aurait casse ces renvois. L'alias est donc une compatibilite
ascendante deliberee, pas un oubli de nettoyage.

Il est volontairement mince : il ne duplique aucun contenu, pour ne pas creer
deux sources de verite qui divergeraient. Le jour ou les renvois auront ete
recrits vers `sci-figure`, ce repertoire pourra partir a la corbeille.

## Changement de comportement a connaitre

L'ancien `create-viz` produisait du PNG a 150 dpi, sous les standards de
soumission. `sci-figure` produit du **PDF vectoriel par defaut**, le raster
haute resolution n'etant fourni que sur demande explicite. Un appelant qui
attendait un PNG doit desormais le demander.
