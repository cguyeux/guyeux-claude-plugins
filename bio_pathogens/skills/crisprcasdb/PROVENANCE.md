# Provenance

- Source scientifique : CRISPRCasdb, Pourcel et al., Nucleic Acids Research 2020, 48(D1):D535-D544.
- Service source : CRISPR-Cas++ / CRISPRCasdb, I2BC, Universite Paris-Saclay.
- Code dans ce plugin : `scripts/ccdb.py` est un client local original vers une copie PostgreSQL locale.
- Donnees : aucune base PostgreSQL n'est embarquee dans ce plugin ; il suppose le conteneur local `crisprcasdb`.

Configuration locale : les variables `CCDB_HOST`, `CCDB_PORT`, `CCDB_DB`, `CCDB_USER`, `CCDB_PASSWORD` et `CCDB_CONTAINER` permettent de surcharger les valeurs par defaut du conteneur local de recherche.

Garde-fou : filtrer `evidencelevel = 4` par defaut. Les niveaux 1 a 3 contiennent beaucoup de repetitions non CRISPR, notamment chez les genomes riches en GC.
