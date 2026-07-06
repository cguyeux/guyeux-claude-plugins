---
name: imdb
description: This skill should be used when the user asks to "recuperer les notes IMDb", "chercher la note d'un film", "enrichir une liste de films avec IMDb", "classer des films par note IMDb", "trouver les informations d'un film", "identifier un film par titre et annee", or mentions IMDb, OMDb, TMDb, movie ratings, film metadata, votes, genres, runtime, director, cast, poster, or IMDb ids.
version: 0.1.0
---

Pipeline de recuperation de notes et metadonnees de films a partir d'un cache local IMDb, avec enrichissement facultatif via OMDb ou TMDb quand une cle API est fournie.

## Principe

Utiliser d'abord les jeux de donnees officiels IMDb Non-Commercial Datasets, en particulier `title.basics.tsv.gz` et `title.ratings.tsv.gz`. Ces fichiers donnent les identifiants IMDb, titres, annees, durees, genres, notes moyennes et nombres de votes. Les telecharger une fois, construire un cache SQLite local, puis interroger ce cache sans refaire de requetes reseau.

Ne pas scraper les pages HTML d'IMDb pour recuperer les notes. Les pages IMDb changent souvent, peuvent imposer des limites d'acces, et le scraping direct n'est pas necessaire pour les donnees de base. Pour les champs non presents dans les datasets IMDb (resume, affiche, certification, certains credits detailles), utiliser un service prevu pour cela, typiquement OMDb ou TMDb, uniquement si l'utilisateur dispose d'une cle API.

## Workflow recommande

1. Identifier l'entree demandee : titre libre, annee, identifiant IMDb `tt...`, ou liste de films.
2. Verifier l'existence du cache SQLite local. Par defaut, utiliser `~/.cache/imdb-skill/imdb.sqlite`, ou un chemin de projet explicite si le resultat doit etre versionne avec une analyse.
3. Si le cache est absent ou ancien, lancer `scripts/imdb_lookup.py update`. Le telechargement peut etre long et consommer plusieurs centaines de Mo compresses.
4. Chercher par identifiant IMDb quand il est connu. Sinon, chercher par titre normalise et annee. Toujours afficher les alternatives proches si l'identification est ambigue.
5. Retourner au minimum : titre, annee, type, note IMDb, nombre de votes, duree, genres, identifiant IMDb, URL IMDb.
6. Appliquer un seuil de votes pour les classements. Une bonne valeur de depart est `--min-votes 1000` pour eviter de promouvoir des films quasi non notes.
7. Pour enrichir avec synopsis, affiche ou champs editoriaux, utiliser `omdb` avec `OMDB_API_KEY`, ou adapter la requete TMDb de facon explicite.

## Script fourni

Le script principal est `scripts/imdb_lookup.py`. Il est volontairement en bibliotheque standard Python uniquement (`urllib`, `gzip`, `csv`, `sqlite3`) pour fonctionner dans un environnement minimal.

### Construire ou rafraichir le cache

```bash
python3 scripts/imdb_lookup.py update --db ~/.cache/imdb-skill/imdb.sqlite
```

Par defaut, seuls les types `movie`, `tvMovie` et `short` sont indexes. Ajouter ou remplacer les types avec `--title-types movie,tvMovie,tvSeries,tvMiniSeries` si la demande porte aussi sur les series.

### Chercher un film par titre

```bash
python3 scripts/imdb_lookup.py lookup "The Ninth Gate" --year 1999 --db ~/.cache/imdb-skill/imdb.sqlite
```

### Chercher par identifiant IMDb

```bash
python3 scripts/imdb_lookup.py lookup --imdb-id tt0142688 --db ~/.cache/imdb-skill/imdb.sqlite --format json
```

### Classer une liste simple de titres

Creer un TSV avec les colonnes `title` et optionnellement `year`, puis lancer :

```bash
python3 scripts/imdb_lookup.py batch films.tsv --db ~/.cache/imdb-skill/imdb.sqlite --min-votes 1000 --format tsv
```

### Enrichissement OMDb facultatif

```bash
OMDB_API_KEY=... python3 scripts/imdb_lookup.py omdb --imdb-id tt0142688
```

Ne jamais inscrire une cle API dans le code, dans le skill, ou dans un fichier versionne. Lire la cle depuis l'environnement.

## Politique de sortie

Pour une reponse utilisateur courte, presenter les meilleurs resultats dans un tableau lisible :

- titre retenu ;
- annee ;
- note IMDb ;
- nombre de votes ;
- genres ;
- raison du choix si plusieurs homonymes existent.

Pour une sortie reutilisable, produire du TSV ou du JSON. Le TSV est preferable pour des listes de films a retraiter dans un tableur ou un script.

## Ambiguites et controles

Toujours signaler les cas ambigus :

- meme titre et plusieurs annees ;
- remake portant le meme titre ;
- titre localise absent de `title.basics.tsv.gz` ;
- film court, episode ou telefilm confondu avec un long metrage ;
- note fondee sur trop peu de votes.

Utiliser `--limit 10` pour afficher les candidats. Si un titre localise ne matche pas, consulter `title.akas.tsv.gz` manuellement ou etendre le script avant de conclure que le film est absent.

## Ressources additionnelles

Consulter `references/sources.md` pour les sources de donnees, les limites juridiques et les pieges de schema.
