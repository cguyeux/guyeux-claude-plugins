# Claude Plugins — Groupe Guyeux (FEMTO-ST)

Collection de plugins [Claude Code](https://docs.claude.com/en/docs/claude-code) développés par Christophe Guyeux (Institut FEMTO-ST, CNRS UMR 6174, Université Marie et Louis Pasteur, Besançon) pour la recherche scientifique académique : phylogénomique évolutive bactérienne, génétique des populations humaines, rédaction scientifique, et outillage transverse (bioinformatique, statistiques, visualisation, revue de littérature).

## Plugins

| Plugin | Rôle |
|--------|------|
| `bio_pathogens` | Génomique computationnelle des pathogènes bactériens (MTBC, *M. leprae*, *Y. pestis*, *H. pylori*), lignages, allèles de résistance, bases de données spécialisées, à des fins de publications évaluées par des pairs. |
| `bio_population_genetics` | Génétique des populations humaines anciennes et modernes, archéologie, paléoclimat, corpus de migrations, plus les outils génériques de phylogénétique, statistiques et fouille de littérature. |
| `bio_redac` | Phase hybride analyse + rédaction (agrège les skills des autres plugins). |
| `redac` | Rédaction pure : LaTeX, slides, manuscrits, vérification de références et de figures. |
| `ia` | Intelligence artificielle, machine learning, data science. |
| `multimedia` | Sous-titrage de films muets, audio/vidéo, synthèse vocale, métadonnées de films. |
| `ops` | Projets PrédictOps, OptimOps, DoctrinOps. |
| `web` | Développement et test d'applications web. |

Le répertoire `mes_skills/` regroupe des skills personnels supplémentaires (itol, rasigade) non empaquetés en plugin.

## Installation

Ajouter ce dépôt comme marketplace, puis installer les plugins voulus :

```
/plugin marketplace add cguyeux/claude_plugins
/plugin install bio_pathogens@guyeux-claude-plugins
/plugin install redac@guyeux-claude-plugins
```

## Architecture des skills partagés

Beaucoup de skills sont mutualisés entre plugins via des **symlinks relatifs**. Chaque skill possède un unique répertoire canonique (le fichier réel) ; les autres plugins y accèdent par lien symbolique. Modifier le fichier canonique propage automatiquement le changement à tous les plugins. La table d'ownership canonique et les règles de synchronisation sont documentées dans `CLAUDE.md`.

`bio_redac/` ne contient que des symlinks (sauf `phylo-history`, maintenu en deux versions volontairement distinctes).

## Cadrage

L'ensemble de cet outillage est destiné à un usage de recherche scientifique académique. Les composants touchant aux pathogènes bactériens et à la résistance antimicrobienne relèvent exclusivement de la biologie évolutive, de la phylogénomique et de la littérature évaluée par des pairs.

## Auteur

Christophe Guyeux — Institut FEMTO-ST (CNRS UMR 6174), Université Marie et Louis Pasteur.
