# Plugin `multimedia`

> Outils multimédia : sous-titrage de films muets, manipulation audio/vidéo, synthèse vocale et métadonnées de films.

## Rôle dans un projet M. tuberculosis

Outillage périphérique (audio, vidéo, synthèse vocale, sous-titrage). Utile à la valorisation et à la communication d'un projet M. tuberculosis (séminaires, supports pédagogiques), pas à l'analyse génomique.

Skills propres (canoniques) : **3** ; skills partagés utilisés (symlinks) : **0**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [imdb](#imdb) ; [silent-film-subs](#silent-film-subs) ; [text-to-speech](#text-to-speech)

### imdb

À utiliser pour récupérer des notes IMDb, chercher la note d'un film, enrichir une liste de films, classer des films par note, ou trouver les informations d'un film (identification par titre et année). Couvre IMDb, OMDb, TMDb : notes, votes, genres, durée, réalisateur, distribution, affiche.

Compétences : récupérer ou classer des notes de films ; enrichir une liste de films avec des métadonnées ; identifier un film par titre et année

### silent-film-subs

Génère un sous-titrage français pour un film muet (.mkv/.mp4) en détectant automatiquement les intertitres (panneaux de texte clair sur fond sombre), en océrisant le texte source (russe par défaut, configurable) avec Tesseract, puis en confiant à Claude le nettoyage de l'OCR et la traduction française. Inclut le muxage final dans le conteneur.

Compétences : compléter, créer ou réparer les sous-titres d'un film muet ; océriser des intertitres ; traduire des panneaux russes/anglais/allemands d'un film d'archive ; quand un .srt existant est jugé incomplet par rapport aux panneaux à l'écran

### text-to-speech

Synthèse vocale : convertit un texte en fichier audio parlé, avec choix de voix et de langue.

Compétences : produire une piste audio à partir d'un texte ; générer une narration ou un support audio

