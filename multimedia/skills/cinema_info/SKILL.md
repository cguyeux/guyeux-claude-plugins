---
name: cinema_info
description: >-
  Moteur unifié de renseignement et de recherche cinématographique multi-sources. Fédère IMDb, Wikipédia multilingue, film-documentaire.fr, le National Film Registry (NFR) et la sélection des 1001 Films pour fournir métadonnées complètes, synopses détaillés et analyses critiques. Use when: rechercher, identifier, comparer ou enrichir des informations sur un film.
version: 1.0.0
---

# Skill Cinéma Unifié (`cinema_info`)

Ce skill offre une passerelle de renseignement cinématographique fédérant les meilleures bases de données et sources critiques :

---

## Sources fédérées

1. **IMDb Cache Local** : notes moyennes, volume de votes, genres stricts, durées et identifiants `tt...`.
2. **Wikipédia Multilingue** : extraction des trames narratives complètes en français (avec traduction automatique des résumés détaillés en anglais quand la page française est un embryon).
3. **[film-documentaire.fr](https://www.film-documentaire.fr)** : fiches spécialisées pour les documentaires, mots-clés thématiques, palmarès de festivals (Lussas, Visions du Réel, etc.) et avis critiques (Tënk, La Cinetek).
4. **[1001films.org](https://www.1001films.org)** : critiques et analyses issues de l'ouvrage de référence *1001 films à voir avant de mourir* et des grands historiens du cinéma (David Thomson, etc.).
5. **National Film Registry (NFR / Library of Congress)** : reconnaissance patrimoniale américaine, année d'intronisation et essais historiques officiels.

---

## Utilisation en ligne de commande

### 1. Recherche complète d'un film
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/cinema_info/scripts/cinema_search.py" "Sunset Boulevard" --director "Billy Wilder" --year 1950
```

### 2. Recherche d'un documentaire
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/cinema_info/scripts/cinema_search.py" "Sans soleil" --director "Chris Marker" --year 1982 --doc
```

### 3. Sortie JSON (pour pipelines et RAG)
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/cinema_info/scripts/cinema_search.py" "Les Aventures de Robin des Bois" --orig-title "The Adventures of Robin Hood" --year 1938 --director "Michael Curtiz" --format json
```
