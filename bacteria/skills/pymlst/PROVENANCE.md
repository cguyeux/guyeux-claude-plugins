# Provenance de `pymlst`

## Statut local

Ce répertoire contient un wrapper documentaire original du dépôt de Christophe
Guyeux. Il décrit l'emploi scientifique de pyMLST sans embarquer le code, les
tests, les schémas, les assemblages ou les données du projet amont.

La première preuve Git conservée est le commit
`63e6c18be595037db4f86ce5027728d95a996edc`, référence
`refs/claude/checkpoint-0858bd89`, datée du 2026-08-17 et attribuée à `Claude
Code <noreply@anthropic.com>` sur instruction de l'utilisateur. Le checkpoint
indépendant `2d6fe64edc5645a1c333ae90255d9026ba787b5a` contient le même fichier.
L'empreinte SHA-256 commune du `SKILL.md` initial est
`1b2d017d1466d45f3ba80fe41b999f9e38a348b7203e870377d7f9d92c0c2103`.
L'empreinte SHA-256 du `SKILL.md` audité et prêt à committer est
`b7322eac43793449422d7cd52b3601635265dd225732679722c77ebed9e64c8d`.

## Amont audité

- Dépôt officiel : `https://github.com/bvalot/pyMLST`.
- Commit épinglé : `389679b18dad9f92c3f212b98fb6d9878f95bb5a`.
- Date du commit : 2026-06-16.
- Version dans `pymlst/version.py` : 2.3.2.
- Licence déclarée : GPL-3.0-or-later dans `LICENSE`, avec `GPLv3` dans
  `setup.py`. L'API GitHub renvoie `NOASSERTION`, ce qui ne remplace pas la
  lecture du fichier de licence.
- Empreinte SHA-256 de `LICENSE` :
  `cb3a985a30bc652ef2862302eaca3cc37373a9e867f49d74e9e154f7d32ad6f6`.
- Empreinte SHA-256 du `README.md` :
  `449a8f91341be83fc9f12d6a698b94c37b5e6c32400d6e36e8c94b3c54370020`.
- Empreinte SHA-256 de `setup.py` :
  `8832d6b23d585fc6462f3ef307e6e34e034bc2f90f86f1fc9e6845f9e6d05514`.
- Empreinte SHA-256 de `pymlst/version.py` :
  `dd658a247997bd244508ed7cfc1a9ade94ec1525e44beda4b0bc4936de37038a`.

Le commit a été résolu par `git ls-remote`, installé dans un environnement
Python 3.8 temporaire et testé le 2026-08-21. `wgMLST create` a initialisé une
base jouet de deux gènes, puis `stats`, `gene`, `mlst` et `distance` ont réussi.
Les 25 tests de `tests/test_wg.py` du dépôt amont ont également réussi. Le test
d'ajout d'assemblages par `wgMLST add` reste conditionné à BLAT, absent de la
machine de migration ; cette réserve est explicite dans le test local.

## Redistribution

La GPL-3.0-or-later s'applique au moteur pyMLST récupéré séparément. Aucun de
ses fichiers n'est redistribué ici. Le texte local reste soumis à la politique
de licence du dépôt racine, qui ne possède pas encore de fichier `LICENSE`. Ce
constat autorise le commit local et l'installation locale, pas une publication
publique automatique du dépôt complet.
