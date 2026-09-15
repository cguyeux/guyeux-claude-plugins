# Provenance de `bactrline`

## Statut local

Ce répertoire contient un wrapper documentaire original du dépôt de Christophe
Guyeux. Il décrit comment utiliser bactRline dans un cadre de recherche, mais
n'embarque aucun code, environnement, base de données, image ou jeu de données
du projet amont.

La première preuve Git conservée est le commit
`63e6c18be595037db4f86ce5027728d95a996edc`, référence
`refs/claude/checkpoint-0858bd89`, datée du 2026-08-17 et attribuée à `Claude
Code <noreply@anthropic.com>` sur instruction de l'utilisateur. Le checkpoint
indépendant `2d6fe64edc5645a1c333ae90255d9026ba787b5a` contient le même fichier.
L'empreinte SHA-256 commune du `SKILL.md` initial est
`9ce074c427e45598582390eb6417cfaa2d988d7d079af19b5913be1e65707c6e`.
L'empreinte SHA-256 du `SKILL.md` audité et prêt à committer est
`b95b1bcf079323670899f272e6ee29a175049b4a372dc776a88c8d4e60be7724`.

## Amont audité

- Dépôt officiel : `https://github.com/bvalot/bactrline`.
- Commit épinglé : `b87e2b19198629f453a8c05607b18ae7aa8a80fb`.
- Date du commit : 2026-07-07.
- Licence déclarée : GPL-3.0-only, fichier `LICENSE.md` et mention du README.
- Empreinte SHA-256 de `LICENSE.md` :
  `867f00bc11d3ae962391e33ddb19737308077120033230029bf7f1bd03664522`.
- Empreinte SHA-256 du `README.md` :
  `6bca89fb0455a915e93cdb5550d37145b76611f4f955fe00dcc2539e0e672c0c`.

Le commit a été résolu par `git ls-remote` puis contrôlé dans un checkout
détaché le 2026-08-21. Le lanceur Snakemake système de la machine de migration
était incomplet (`ModuleNotFoundError: snakemake`) ; le dry-run biologique n'a
donc pas été présenté comme exécuté. Le contrat de commande officiel
`snakemake --use-conda --dry-run` et la présence des fichiers de configuration
ont été contrôlés au commit épinglé.

## Redistribution

La GPL-3.0-only s'applique au moteur bactRline récupéré séparément. Aucun de ses
fichiers n'est redistribué ici. Le texte local reste soumis à la politique de
licence du dépôt racine, qui ne possède pas encore de fichier `LICENSE`. Ce
constat autorise le commit local et l'installation locale, pas une publication
publique automatique du dépôt complet.
