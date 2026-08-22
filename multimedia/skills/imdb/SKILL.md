---
name: imdb
description: >-
  Pipeline de métadonnées de films, notes et résumés détaillés (RAG). Utilise les datasets officiels IMDb, Wikipedia multilingue, sources spécialisées et un algorithme de score de matching pour enrichir les films avec synopsis complets, genres, durées et notes. Use when: chercher une fiche IMDb, désambiguïser un titre ou enrichir des métadonnées de film.
version: 0.3.0
---

# Pipeline & Skill Cinéma Multi-Sources (IMDb, Wikipedia, RAG)

Ce skill fournit une chaîne complète d'acquisition de métadonnées cinématographiques et de génération de fiches documentaires riches pour l'indexation RAG et la recherche textuelle sémantique (*ripgrep*).

---

## Architecture Multi-Sources

1. **Cache local IMDb (Données structurelles & Notes)** :
   - Exploite `title.basics.tsv.gz` et `title.ratings.tsv.gz` dans SQLite (`~/.cache/imdb-skill/imdb.sqlite`).
   - Fournit les identifiants `tt...`, genres exacts (*Documentary, Animation, Film-Noir, Crime, Drama...*), durées précises, notes moyennes et volume de votes.
2. **Wikipedia Multilingue (Résumés détaillés, Thèmes & Contexte)** :
   - Interrogation via l'API MediaWiki (FR puis EN).
   - Extraction des sections *Synopsis / Résumé / Trame* et de l'introduction épurée (sans syntaxe wiki).
3. **Moteur de validation & Score de matching (0-100)** :
   - Calcul de similarité du titre (FR et titre original).
   - Validation stricte de l'année (tolérance +/- 1 an).
   - Vérification de la présence du nom du réalisateur dans la fiche source.
   - Détection des mots-clés de l'univers cinématographique et pénalisation des pages d'homonymies/listes.

---

## Scripts disponibles

### 1. Enrichissement d'un film individuel (`enrich_film_metadata.py`)
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/imdb/scripts/enrich_film_metadata.py" "Cléopâtre" --orig-title "Cleopatra" --year 1934 --director "Cecil B. DeMille"
```
Retourne :
- Score de matching & niveau de confiance (`HIGH`, `MODERATE`, `LOW`).
- Page source et URL vérifiée.
- Résumé / Synopsis extrait et nettoyé.

### 2. Cache IMDb local (`imdb_lookup.py`)
```bash
# Vérification ou mise à jour du cache
python3 "${CLAUDE_PLUGIN_ROOT}/skills/imdb/scripts/imdb_lookup.py" meta
python3 "${CLAUDE_PLUGIN_ROOT}/skills/imdb/scripts/imdb_lookup.py" update
```

---

## Bonnes pratiques pour l'indexation RAG
- **Fiches par film** : chaque œuvre possède sa fiche `.md` avec métadonnées YAML et texte structuré.
- **Préservation des mots-clés sémantiques** : les résumés détaillés permettent de retrouver les œuvres par thème (ex: *Égypte antique, pharaon, péplum* pour *Cléopâtre*).
- **Traitement par lots** : exécuter l'enrichissement par batches avec mise en cache locale pour éviter les requêtes redondantes.
