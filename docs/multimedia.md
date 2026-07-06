# Plugin `multimedia`

> Outils multimédia : sous-titrage de films muets, manipulation audio/vidéo, synthèse vocale et métadonnées de films.

## Rôle dans un projet M. tuberculosis

Outillage périphérique (audio, vidéo, synthèse vocale, sous-titrage). Utile à la valorisation et à la communication d'un projet M. tuberculosis (séminaires, supports pédagogiques), pas à l'analyse génomique.

Skills propres (canoniques) : **3** ; skills partagés utilisés (symlinks) : **0**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [imdb](#imdb) ; [silent-film-subs](#silent-film-subs) ; [text-to-speech](#text-to-speech)

### imdb

This skill should be used when the user asks to "recuperer les notes IMDb", "chercher la note d'un film", "enrichir une liste de films avec IMDb", "classer des films par note IMDb", "trouver les informations d'un film", "identifier un film par titre et annee", or mentions IMDb, OMDb, TMDb, movie ratings, film metadata, votes, genres, runtime, director, cast, poster, or IMDb ids.

### silent-film-subs

Génère un sous-titrage français pour un film muet (.mkv/.mp4) en détectant automatiquement les intertitres (panneaux de texte clair sur fond sombre), en océrisant le texte source (russe par défaut, configurable) avec Tesseract, puis en confiant à Claude le nettoyage de l'OCR et la traduction française. Inclut le muxage final dans le conteneur. À

Compétences : l'utilisateur demande à compléter, créer ou réparer des sous-titres pour un film muet, à océriser des intertitres, à traduire des panneaux russes/anglais/allemands d'un film d'archive, ou quand un .srt existant est jugé incomplet par rapport aux panneaux affichés à l'écran

### text-to-speech

_(pas de description)_

