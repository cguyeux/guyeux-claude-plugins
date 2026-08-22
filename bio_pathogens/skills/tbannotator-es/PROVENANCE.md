# Provenance et acces

- Origine : client local en lecture pour les indices Elasticsearch de TBannotator, derive du schema observe dans la webapp du groupe.
- Code amont suivi : depot TBannotator Remix, commit de reference `f5bd62942422ae3f63947ece96b27e66d3d9a943` pour le calcul d'exclusivite.
- Redistribution : aucun document Elasticsearch, identifiant ou secret n'est embarque.
- Configuration : URL et authentification sont lues uniquement depuis l'environnement ou `~/.config/tbannotator_es.env`.

## Garde-fou

L'acces est strictement en lecture. Le certificat ne peut etre ignore que par configuration explicite et locale. Un resultat vide doit etre croise avec les autres sources TBannotator avant interpretation.
