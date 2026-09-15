# Provenance

- Origine methodologique : relation algebra et laminarisation issues des travaux de Clement Lecarpentier, notamment `phylo/relations.py` et `phylo/why.py` dans `https://github.com/cdarthos/bi-clustering`.
- Code dans ce plugin : reexpression locale autonome pour matrices souche x marqueur et sorties de co-clustering, avec credit explicite dans `scripts/laminarity.py`.
- Dependances : numpy et scipy ; aucun code amont n'est embarque tel quel.

Garde-fou : la laminarisation choisit un retrait operationnel de marqueurs, pas une preuve du marqueur fautif. L'arbitre reste la verification biologique et l'arbre ML.
