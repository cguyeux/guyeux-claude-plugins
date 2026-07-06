# Presets de narration

Ces fichiers sont des **exemples de référence** pour rédiger un prompt d'instructions de prosodie destiné à `gpt-4o-mini-tts`. Ils ne doivent **pas** être utilisés tels quels : chaque texte mérite un prompt sur mesure (un conte d'Andersen n'est pas un conte de Perrault, un polar de Simenon n'est pas un thriller américain).

## Anatomie d'un bon prompt de prosodie

Un prompt efficace de 5 à 15 lignes couvrant tout ou partie de :

1. **Rôle du narrateur** — "Vous êtes un narrateur de conte pour enfants", "Vous êtes un récitant de roman noir", etc. Une phrase contextuelle d'ouverture.
2. **Effet vocal / timbre** — voix grave/claire, légèrement rocailleuse/chaude, jeune/âgée, neutre/expressive.
3. **Tonalité générale** — sérieuse, légère, intime, solennelle, tendue, contemplative.
4. **Rythme** — lent, modéré, rapide ; variations selon les passages (dialogues vs description).
5. **Émotion** — contenue, chargée, distante, complice, mélancolique, ironique.
6. **Accentuation** — quels éléments souligner (indices d'enquête, beautés visuelles, abstractions, jeux sonores).
7. **Prononciation** — articulation précise, légère diction d'époque, souffle audible.
8. **Pauses** — silences lourds après révélations, respirations après descriptions, suspensions avant chutes.

## Voix OpenAI recommandées par genre

| Genre du texte | Voix par défaut | Variante alternative |
|---|---|---|
| Conte jeunesse (Andersen, Perrault, Grimm, La Fontaine) | `nova` (féminin clair) | `fable` (masculin chaleureux) |
| Conte oriental, Mille et une Nuits | `ballad` (féminin mélodieux) | `fable` |
| Roman littéraire classique (Balzac, Flaubert, Stendhal) | `coral` (féminin neutre) | `echo` (masculin neutre) |
| Polar, thriller, roman noir | `onyx` (masculin grave) | `ash` (masculin posé) |
| Science-fiction, fantastique | `echo` | `sage` (féminin posé) |
| Philosophie, essai réflexif | `sage` | `fable` |
| Essai scientifique, vulgarisation | `alloy` (neutre didactique) | `ash` |
| Poésie | `ballad` | `verse` (masculin expressif) |
| Théâtre, monologue | `verse` | `onyx` |
| Lettre intime, journal personnel | `coral` | `shimmer` (féminin pétillant si gai) |
| Correspondance historique, archive | `fable` | `sage` |
| Conférence, discours | `onyx` ou `nova` selon le sexe | `ash`, `coral` |

À toujours **tester sur un court extrait** (200-500 mots) avant d'engager un livre entier.

## Workflow recommandé

Quand Claude est invoqué pour narrer un fichier texte, il doit :

1. **Lire le texte** (ou un échantillon représentatif : début + 1-2 extraits aléatoires si > 5 000 caractères).
2. **Identifier** : auteur, genre, époque, ton dominant, public visé, langue.
3. **Choisir une voix** en s'appuyant sur le tableau ci-dessus.
4. **Rédiger** un prompt d'instructions sur mesure (5-15 lignes) en s'inspirant du preset le plus proche, en adaptant :
   - Les références culturelles (siècle de Balzac ≠ siècle de Houellebecq)
   - L'intensité émotionnelle (gravité d'un Andersen mélancolique ≠ légèreté d'un Daudet)
   - Les particularités stylistiques (phrases longues, dialogues abondants, alexandrins, etc.)
5. **Écrire** le prompt dans un fichier `<nom_du_texte>.narration.txt` à côté du texte source.
6. **Lancer** la synthèse :
   ```bash
   .venv/bin/python <skill>/scripts/tts_openai.py texte.txt -o sortie.mp3 \
       --voice <choisie> --instructions <nom_du_texte>.narration.txt
   ```
7. **Annoncer** à l'utilisateur le choix de voix et un résumé du prompt rédigé, pour qu'il puisse demander un ajustement avant de payer la synthèse complète.

## Index des exemples

- [`conte_jeunesse.txt`](conte_jeunesse.txt) — conte pour enfants (Andersen, Perrault, Grimm)
- [`polar.txt`](polar.txt) — roman policier, thriller, noir
- [`roman_litteraire.txt`](roman_litteraire.txt) — fiction littéraire XIXe-XXe
- [`philosophie.txt`](philosophie.txt) — essai philosophique, réflexion
- [`poesie.txt`](poesie.txt) — vers, prose poétique
- [`essai_scientifique.txt`](essai_scientifique.txt) — vulgarisation, non-fiction didactique
