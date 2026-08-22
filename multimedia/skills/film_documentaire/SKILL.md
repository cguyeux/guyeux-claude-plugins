---
name: film_documentaire
description: >-
  Moteur de recherche et d'extraction de métadonnées pour le cinéma documentaire via la plateforme film-documentaire.fr. Extrait résumés complets, mots-clés thématiques, sélections en festivals, distinctions, durées et crédits. Use when: rechercher, identifier ou documenter un film documentaire.
version: 0.1.0
---

# Skill film-documentaire.fr (Cinéma Documentaire)

Ce skill permet d'interroger la base encyclopédique de référence [film-documentaire.fr](https://www.film-documentaire.fr) pour enrichir les fiches de films documentaires avec des métadonnées spécialisées :
- Résumés détaillés et synopsis analytiques en français.
- Mots-clés thématiques précis (ex: *Histoire, Mémoire, Société, Écologie, Géopolitique, Art...*).
- Sélections et distinctions en festivals (Visions du Réel, Lussas, Cinéma du Réel, IDFA, etc.).
- Informations de production, durées et formats de diffusion (DVD, VOD, Tënk).
- Score de correspondance et de validation (0-100).

---

## 🛠️ Utilisation en ligne de commande

### 1. Recherche par titre et réalisateur
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/film_documentaire/scripts/film_doc_lookup.py" "Sans soleil" --director "Chris Marker" --year 1982
```

### 2. Format JSON (pour intégration dans les pipelines RAG / scripts)
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/film_documentaire/scripts/film_doc_lookup.py" "Shoah" --director "Claude Lanzmann" --year 1985 --format json
```

---

## 📋 Données retournées
- `title` : Titre français
- `english_title` : Titre international / anglais
- `director` : Réalisateur / Réalisatrice
- `year` : Année de réalisation / sortie
- `runtime_minutes` : Durée en minutes
- `synopsis` : Synopsis complet et note d'intention
- `keywords` : Liste des mots-clés thématiques
- `festivals` : Liste des sélections et prix reçus
- `match_score` : Score de confiance (0 à 100)
