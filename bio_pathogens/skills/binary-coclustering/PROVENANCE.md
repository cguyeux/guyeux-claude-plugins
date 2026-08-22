# Provenance

- Origine scientifique et logicielle : travaux de Clement Lecarpentier sur le co-clustering binaire TB, depot `https://github.com/cdarthos/bi-clustering`.
- Usage amont attendu : cloner le depot localement et pointer `BICLUSTERING_REPO` vers ce clone.
- Code importe : `scripts/fit_coclustering.py` pilote le moteur amont via import local ; `build_matrix.py` et `place_strains.py` sont des adaptateurs locaux pour matrices souche x marqueur.
- Redistribution : aucun code du depot `bi-clustering` n'est embarque dans ce plugin.

Garde-fou : un bloc de co-clustering n'est pas un clade. Toute lecture taxonomique doit passer par `marker-laminarity` et par un arbre ML independant avant publication.
