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

Synthetise un fichier .mp3 a partir d'un fichier texte (.txt, .md, chapitre de livre) via trois moteurs. Par defaut Mistral/Voxtral (voxtral-mini-tts) : voix preregles multilingues dont six francaises en registres emotionnels, galerie de voix clonees depuis un enregistrement, clonage ponctuel par echantillon ; le ton se choisit par la variante de voix, Voxtral n'acceptant pas d'instructions de prosodie en texte libre. Alternative OpenAI gpt-4o-mini-tts quand on veut une prosodie pilotee par un prompt sur mesure ou davantage de voix. Kokoro-82M en local, gratuit et hors ligne. Avant synthese, Claude lit un echantillon, identifie auteur, genre, epoque et ton, puis choisit la voix.

Compétences : narrer un texte en audio ; generer un MP3 ou un livre audio ; lire un fichier a voix haute ; l'utilisateur mentionne TTS, synthese vocale, Voxtral, Kokoro, F5-TTS ou XTTS ; l'utilisateur dit Whisper en confondant avec la reconnaissance vocale

