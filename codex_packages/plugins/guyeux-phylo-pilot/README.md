# Guyeux Phylo Pilot

Paquet Codex local de validation pour cinq skills canoniques de phylogenomique
MTBC : `tbmonitor-papers`, `mtbc-prospect`, `molecular-clock`, `raxml` et
`iqtree-lsd2`.

Les fichiers sont des copies materialisees des sources canoniques du depot,
afin que le paquet soit installable sans dependance a une arborescence Claude.
Les adaptations Codex restent limitees a ce paquet : ne pas les recopier dans
les skills canoniques sans revue explicite.

Prerequis fonctionnels :

- `tbmonitor-papers` demande le serveur MCP `tbmonitor` dans Codex.
- `molecular-clock` et `raxml` demandent le serveur MCP `tbannotator` ; leurs
  calculs distants restent conditionnels au skill `remote-compute` deja exporte.
- `mtbc-prospect` est volontairement borne a `--dry-run` tant que CCX-05 n'a pas
  porte le workflow append-only `pistes`.

Le paquet est en phase pilote et ne remplace pas encore les liens de skills
directement exportes dans le profil Codex personnel.
