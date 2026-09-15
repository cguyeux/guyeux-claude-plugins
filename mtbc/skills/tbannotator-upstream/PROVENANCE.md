# Provenance

- Amont surveille : groupe public GitLab `tbannotator/webapp`.
- Etat epingle local : `references/upstream_pinned.json`.
- Code importe : `scripts/check_upstream.py` est un script local original de veille, sans code amont embarque.
- Donnees lues : metadonnees publiques GitLab, OpenAPI public de l'instance vivante, et declarations TypeScript publiques du front.

Garde-fou : une derive de schema Elasticsearch peut transformer une requete biologique en resultat vide sans erreur. Toute derive reportee par le script doit etre relue avant de repinner.
