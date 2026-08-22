# Claude Plugins : groupe Guyeux (FEMTO-ST)

Collection de plugins [Claude Code](https://docs.claude.com/en/docs/claude-code) développés par Christophe Guyeux (Institut FEMTO-ST, CNRS UMR 6174, Université Marie et Louis Pasteur, Besançon) pour la recherche scientifique académique : phylogénomique évolutive bactérienne, génétique des populations humaines, rédaction scientifique, et outillage transverse (bioinformatique, statistiques, visualisation, revue de littérature).

Documentation complète, skill par skill (raison d'être et compétences, sous l'angle M. tuberculosis) : **[dossier `docs/`](docs/README.md)**. Chaque plugin ci-dessous est aussi lié directement à sa page.

## Plugins

| Plugin | Rôle |
|--------|------|
| [bio_pathogens](docs/bio_pathogens.md) | Phylogénomique évolutive du MTBC stricto sensu : chaîne TBannotator, lignages, variants et littérature spécialisée, à des fins de publications évaluées par des pairs. |
| [bio_bacteria](docs/bio_bacteria.md) | Génomique bactérienne hors MTBC stricto sensu : assemblage, cgMLST, mobilome ab initio, mycobactéries non tuberculeuses et autres genres. |
| [bio_population_genetics](docs/bio_population_genetics.md) | Génétique des populations humaines anciennes et modernes, archéologie, paléoclimat, corpus de migrations, plus les outils génériques de phylogénétique, statistiques et fouille de littérature. |
| [bio_redac](docs/bio_redac.md) | Phase hybride analyse + rédaction (agrège les skills des autres plugins). |
| [redac](docs/redac.md) | Rédaction pure : LaTeX, slides, manuscrits, vérification de références et de figures. |
| [ia](docs/ia.md) | Intelligence artificielle, machine learning, data science. |
| [multimedia](docs/multimedia.md) | Sous-titrage de films muets, audio/vidéo, synthèse vocale, métadonnées de films. |
| [ops](docs/ops.md) | Projets PrédictOps, OptimOps, DoctrinOps. |
| [web](docs/web.md) | Développement et test d'applications web. |
| [maboss](docs/maboss.md) | MaBoSS / CoLoMoTo : modèles booléens `.bnd`/`.cfg` (grammaire refcard), API pyMaBoSS et évaluateur CCT (Oscar Dufossez), carte de l'écosystème (WebMaBoSS de Vincent Noël, dépôts de modèles, positionnement vs INDRA). Modélisation de la signalisation cancer, projet mabossDemo. |
| [droit](docs/droit.md) | Recherche juridique en droit français : conventions de notes et citations, vérification des décisions et textes normatifs aux sources officielles. |

Le répertoire `mes_skills/` conserve des ressources personnelles historiques pour iTOL et Rasigade. Il ne contient actuellement aucun `SKILL.md` actif et n'est pas empaqueté en plugin.

## Cartographie des skills

La collection s'organise comme la chaîne de production d'un article de phylogénomique évolutive du complexe *Mycobacterium tuberculosis* (MTBC), du choix du problème au dépôt final. Vue d'ensemble par étape :

| Étape d'un projet M. tuberculosis | Plugins mobilisés |
|-----------------------------------|-------------------|
| 1. Cadrage et revue de littérature | `ia`, `redac`, `bio_population_genetics` |
| 2. Acquisition des génomes et isolats publiés | `bio_pathogens`, `bio_population_genetics` |
| 3. Variants, résistance, assignation de lignée | `bio_pathogens` |
| 4. Phylogénie et datation moléculaire | `bio_population_genetics`, `bio_pathogens` |
| 5. Phylogéographie et contexte hôte | `bio_population_genetics` |
| 6. Modélisation, statistiques, machine learning | `ia`, `bio_population_genetics` |
| 7. Visualisation (figures, arbres, cartes) | `bio_population_genetics`, `redac` |
| 8. Rédaction du manuscrit | `redac`, `bio_redac` |
| 9. Vérification et réponse aux relecteurs | `redac` |
| 10. Valorisation et dépôt (DOI, Overleaf, financements) | `redac` |

Le catalogue complet est dans le [dossier `docs/`](docs/README.md) : une page par plugin, plus un index alphabétique des 188 noms de skills actifs. Les deux versions intentionnellement divergentes de `phylo-history` portent ce total à 189 répertoires canoniques. Les plugins `maboss` et `droit` relèvent de domaines séparés et y sont documentés à part.

## Installation

Ajouter ce dépôt comme marketplace, puis installer les plugins voulus :

```
/plugin marketplace add cguyeux/claude_plugins
/plugin install bio_pathogens@guyeux-claude-plugins
/plugin install redac@guyeux-claude-plugins
```

Pour Codex, le dépôt reste également la source canonique. Le fichier
`codex_skills.json` sélectionne les skills exposés dans les sessions et le
synchroniseur crée des liens vers leurs répertoires réels :

```
python3 _audit/tools/sync_codex_skills.py --apply
python3 _audit/tools/sync_codex_skills.py
```

La seconde commande doit indiquer zéro skill manquant et zéro conflit. Le
synchroniseur ne remplace jamais un fichier, un répertoire ou un lien divergent
déjà présent dans `~/.codex/skills`.

## Architecture des skills partagés

Beaucoup de skills sont mutualisés entre plugins via des **symlinks relatifs**. Chaque skill possède un unique répertoire canonique (le fichier réel) ; les autres plugins y accèdent par lien symbolique. Modifier le fichier canonique propage automatiquement le changement à tous les plugins. La table d'ownership canonique et les règles de synchronisation sont documentées dans `CLAUDE.md`.

`bio_redac/` ne contient que des symlinks (sauf `phylo-history`, maintenu en deux versions volontairement distinctes).

## Cadrage

L'ensemble de cet outillage est destiné à un usage de recherche scientifique académique. Les composants touchant aux pathogènes bactériens et à la résistance antimicrobienne relèvent exclusivement de la biologie évolutive, de la phylogénomique et de la littérature évaluée par des pairs.

## Auteur

Christophe Guyeux, Institut FEMTO-ST (CNRS UMR 6174), Université Marie et Louis Pasteur.
