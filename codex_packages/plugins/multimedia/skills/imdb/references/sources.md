# Sources et limites pour les donnees IMDb

## Source primaire recommandee

IMDb publie des jeux de donnees non commerciaux a l'adresse :

- `https://developer.imdb.com/non-commercial-datasets/`
- `https://datasets.imdbws.com/`

Fichiers utiles pour ce skill :

- `title.basics.tsv.gz` : identifiant IMDb (`tconst`), type de titre, titre principal, titre original, statut adulte, annee de debut, annee de fin, duree, genres.
- `title.ratings.tsv.gz` : identifiant IMDb, note moyenne IMDb, nombre de votes.
- `title.akas.tsv.gz` : titres alternatifs/localises. Non charge par defaut, mais utile pour les titres francais ou les titres d'exploitation.
- `title.crew.tsv.gz` et `name.basics.tsv.gz` : realisateurs, scenaristes et noms. Non charges par defaut, car l'etape de jointure est plus lourde.

Ces fichiers utilisent `\N` pour les valeurs manquantes. Les lignes sont separees par tabulation et compressees en gzip.

IMDb indique que ces datasets sont rafraichis quotidiennement et qu'une copie locale est autorisee pour un usage personnel et non commercial, sous reserve de ses conditions courantes. Ne pas redistribuer le cache SQLite comme s'il s'agissait d'une base libre.

## Services d'enrichissement optionnels

OMDb :

- `https://www.omdbapi.com/`
- Fournit une API simple par identifiant IMDb : `?i=tt...&apikey=...`.
- Champs souvent utiles : `Title`, `Year`, `Rated`, `Released`, `Runtime`, `Genre`, `Director`, `Writer`, `Actors`, `Plot`, `Language`, `Country`, `Poster`, `imdbRating`, `imdbVotes`, `Metascore`.
- Necessite une cle API. Respecter les quotas.

TMDb :

- `https://developer.themoviedb.org/reference/intro/getting-started`
- Utile pour affiches, synopsis, genres et credits, avec une base distincte de notes utilisateur.
- Necessite une cle API et une resolution d'identifiant TMDb ou une recherche par titre.

## Regles pratiques

- Ne pas scraper les pages HTML IMDb pour les notes et les metadonnees de base. Les datasets officiels sont plus stables, plus faciles a mettre en cache, et mieux adaptes a des traitements reproductibles.
- Respecter l'usage non commercial des datasets IMDb. Pour un usage public, commercial, massif ou redistribue, verifier les conditions courantes avant de publier les donnees derivees.
- Datation des notes : les notes et le nombre de votes changent. Indiquer la date de construction du cache pour les sorties analytiques.
- Titre francais : `title.basics.tsv.gz` contient surtout le titre principal et le titre original. Pour matcher des titres francais, ajouter `title.akas.tsv.gz` ou passer par OMDb/TMDb.
- Seuil de robustesse : pour recommander ou classer, imposer un seuil de votes. Une note 8.5 avec 25 votes n'a pas la meme valeur qu'une note 7.5 avec 300000 votes.
- Types : filtrer explicitement `movie`, `tvMovie`, `short`, `tvSeries`, etc. selon la demande. Melanger films, episodes et series rend les classements trompeurs.
