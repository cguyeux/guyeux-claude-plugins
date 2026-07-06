---
name: text-to-speech
description: Synthétise un fichier `.mp3` à partir d'un fichier texte (`.txt`, `.md`, chapitre de livre...) via deux backends au choix, avec **rédaction automatique d'un prompt de narration sur mesure** adapté à l'auteur, au genre, au ton et au style du texte (conte d'Andersen ≠ polar de Simenon ≠ essai philosophique ≠ poésie). Avant la synthèse, Claude lit un échantillon du texte, identifie auteur/genre/époque/ton, choisit la voix OpenAI la plus adaptée, et rédige un prompt d'instructions de prosodie spécifique (rôle, timbre, rythme, émotion, accentuation, pauses). Backend par défaut **OpenAI `gpt-4o-mini-tts`** (qualité narration française très haute, supporte les instructions de prosodie ; payant ~$0.015/1k caractères, nécessite `OPENAI_API_KEY`). Backend alternatif **Kokoro-82M** offline et gratuit (Apache 2.0, qualité moindre en français : 1 seule voix `ff_siwis` grade B-, sans contrôle de prosodie). À utiliser quand l'utilisateur demande à "narrer ce texte en audio", "générer un MP3 / un livre audio", "transformer un chapitre en audio", "faire la synthèse vocale", "lire à voix haute ce fichier", "narration", "text-to-speech", "TTS", ou mentionne un modèle TTS (gpt-4o-mini-tts, tts-1-hd, Kokoro, F5-TTS, XTTS). NB : si l'utilisateur dit "Whisper", il confond avec un modèle TTS — Whisper est de la reconnaissance vocale (STT), pas de la synthèse ; basculer sur ce skill avec OpenAI ou Kokoro.
---

Pipeline texte → MP3 pour livre audio en français (et autres langues), avec **rédaction automatique d'un prompt de narration sur mesure** par Claude avant la synthèse, et choix entre un backend OpenAI cloud (qualité supérieure, payant) et un backend Kokoro local (offline, gratuit).

## Choix du backend

| Critère | OpenAI `gpt-4o-mini-tts` (défaut) | OpenAI `tts-1-hd` | Kokoro-82M |
|---|---|---|---|
| Qualité narration FR | très haute | haute | moyenne (grade B-) |
| Instructions de prosodie | ✅ ton, rythme, émotion, pauses | ❌ | ❌ |
| Voix françaises | 11 voix expressives | 11 voix expressives | 1 (ff_siwis) |
| Prix | ~$0.015 / 1k caractères | ~$0.030 / 1k caractères | gratuit |
| Réseau | requis | requis | aucun |
| Confidentialité | texte envoyé à OpenAI | idem | local |

**Règle de décision :**

- **Livre audio, fiction, polar, conte, narration soignée** → OpenAI `gpt-4o-mini-tts` avec instructions de prosodie. C'est le choix par défaut du skill.
- **Lecture neutre informative** sans contrainte de coût → OpenAI `tts-1-hd` ou `gpt-4o-mini-tts` sans instructions.
- **Texte confidentiel, pas de réseau, ou budget zéro** → Kokoro.
- **Voice cloning** (reproduire une voix précise) → ni l'un ni l'autre. Voir section "Alternatives".

## Quand utiliser ce skill

- Conversion d'un chapitre, d'une nouvelle, d'un livre entier en livre audio MP3.
- Génération de narration de qualité pour podcast, vidéo, démo.
- Pré-écoute d'un manuscrit qu'on rédige.
- Lecture d'articles, de notes, de courriers en audio.

## Workflow narration sur mesure (étape clé, à exécuter par Claude)

Le skill ne se contente pas de lire le texte avec une voix par défaut. Chaque texte mérite un prompt de narration adapté : un conte d'Andersen ne se lit pas comme un thriller de Lehane, qui ne se lit pas comme un essai de Bachelard.

**Quand Claude est invoqué pour narrer un fichier, il doit dérouler cette procédure avant de lancer la synthèse :**

### 1. Lire un échantillon représentatif

- Si le texte fait < 5 000 caractères : le lire en entier.
- Sinon : lire les 2 000 premiers caractères + un extrait du milieu (~1 000 chars) + les 500 derniers. Pour un livre découpé en chapitres, lire le premier chapitre + le titre des autres.

### 2. Identifier les paramètres narratifs

Repérer dans l'échantillon :

- **Auteur** (par recherche sur le contenu, le titre, ou demande explicite à l'utilisateur).
- **Genre** : conte, nouvelle, roman, polar, thriller, science-fiction, fantastique, essai, philosophie, poésie, lettre, journal, théâtre, conférence, vulgarisation, manuel.
- **Sous-genre** : conte jeunesse vs conte oriental ; polar classique vs hard-boiled ; vers réguliers vs prose poétique...
- **Époque** : siècle d'écriture, qui influence la diction et le vocabulaire.
- **Public visé** : enfants, adolescents, adultes, lecteurs cultivés, grand public.
- **Ton dominant** : doux-amer, mélancolique, tendu, ironique, solennel, intime, polémique, didactique, contemplatif.
- **Particularités stylistiques** : phrases longues à tenir d'un souffle, dialogues abondants, métrique en vers, vocabulaire archaïsant, alternance de registres.
- **Langue** (par défaut : français).

### 3. Choisir une voix OpenAI

Consulter le tableau dans [`presets/README.md`](presets/README.md). Résumé des choix typiques :

| Genre | Voix |
|---|---|
| Conte jeunesse, Andersen, Perrault | `nova` ou `fable` |
| Roman littéraire classique | `coral` ou `echo` |
| Polar, thriller, noir | `onyx` |
| Philosophie, essai réflexif | `sage` ou `fable` |
| Poésie, prose poétique | `ballad` ou `verse` |
| Vulgarisation scientifique | `alloy` ou `ash` |
| Théâtre, monologue | `verse` |
| Lettre, journal intime | `coral` ou `shimmer` |

### 4. Rédiger un prompt de prosodie sur mesure

S'inspirer du preset le plus proche dans [`presets/`](presets/) (`conte_jeunesse.txt`, `polar.txt`, `roman_litteraire.txt`, `philosophie.txt`, `poesie.txt`, `essai_scientifique.txt`), **et l'adapter** :

- Au siècle (Balzac ≠ Houellebecq).
- À la personnalité de l'auteur (un Andersen mélancolique ≠ un Perrault malicieux).
- Aux particularités du texte précis (un conte fantastique de Hoffmann ≠ un conte moral de Tolstoï).

Un bon prompt fait 8-15 lignes et couvre : rôle du narrateur, effet vocal/timbre, tonalité, rythme, émotion, accentuation, prononciation, pauses. Voir [`presets/README.md`](presets/README.md) pour l'anatomie complète.

### 5. Écrire le prompt dans un fichier

À côté du texte source : `<nom_du_texte>.narration.txt`.

### 6. Annoncer le choix à l'utilisateur avant de lancer la synthèse

Pour un livre entier, le coût peut atteindre plusieurs dollars. Avant `tts_openai.py`, présenter :

- L'analyse rapide du texte (auteur, genre, ton identifiés).
- La voix choisie (et pourquoi).
- Le prompt rédigé (en bloc).
- L'estimation de coût (`wc -c texte.txt` → caractères × 0,000015 $ pour gpt-4o-mini-tts).
- Une proposition de **test sur un extrait court** (500-1000 premiers caractères) avant d'engager le livre entier.

### 7. Lancer la synthèse

```bash
.venv/bin/python <skill>/scripts/tts_openai.py texte.txt -o sortie.mp3 \
    --voice <choisie> --instructions <nom_du_texte>.narration.txt
```

### Exemple complet : conte d'Andersen

```
1. Claude lit conte_petit_pin.txt → identifie Andersen, conte jeunesse, doux-amer, XIXe danois.
2. Voix : nova (féminin clair, narratrice jeunesse).
3. Prompt rédigé dans conte_petit_pin.narration.txt, adapté du preset conte_jeunesse.txt
   en insistant sur la dimension mélancolique propre à Andersen (le pin meurt à la fin).
4. Test sur 500 chars : .venv/bin/python ../scripts/tts_openai.py
   <(head -c 500 conte_petit_pin.txt) -o test.mp3 --voice nova
   --instructions conte_petit_pin.narration.txt
5. Validation par l'utilisateur, ajustement éventuel du prompt.
6. Synthèse complète.
```

## Dépendances

### Système

```bash
which ffmpeg python3                   # toujours requis
which espeak-ng                        # uniquement pour backend Kokoro
```

Sur Arch :

```bash
sudo pacman -S ffmpeg python espeak-ng    # tout
sudo pacman -S ffmpeg python              # OpenAI uniquement
```

### Python (venv local)

Le script `scripts/setup.sh` automatise tout :

```bash
bash scripts/setup.sh              # installe les deux backends
bash scripts/setup.sh --openai     # OpenAI uniquement
bash scripts/setup.sh --kokoro     # Kokoro uniquement
```

### Clé API OpenAI

Pour le backend OpenAI :

```bash
export OPENAI_API_KEY=sk-...
```

Pour la rendre persistante, l'ajouter à `~/.bashrc` ou `~/.config/fish/config.fish`.

## Usage — backend OpenAI (par défaut)

### Narration simple

```bash
.venv/bin/python scripts/tts_openai.py chapitre1.txt -o chapitre1.mp3
```

Utilise `gpt-4o-mini-tts`, voix `coral`, instructions de narration neutres par défaut.

### Narration avec instructions de prosodie sur-mesure

Préparer un fichier `polar.txt` :

```text
Vous êtes un narrateur de roman policier. Voix grave, légèrement rocailleuse,
timbre évoquant l'usure de longues nuits sans sommeil.
Tonalité sérieuse et tendue. Rythme modérément lent, accélérations dans
l'action et les dialogues. Pauses lourdes après révélations.
Soulignez les indices d'enquête importants.
```

Puis :

```bash
.venv/bin/python scripts/tts_openai.py chapitre1.txt -o chapitre1.mp3 \
    --voice onyx --instructions polar.txt
```

### Variantes utiles

```bash
# Voix féminine narratrice de conte
.venv/bin/python scripts/tts_openai.py conte.txt -o conte.mp3 --voice nova

# Modèle moins cher sans instructions (lecture neutre)
.venv/bin/python scripts/tts_openai.py article.md -o article.mp3 \
    --model tts-1 --no-instructions

# Modèle qualité maximale sans instructions
.venv/bin/python scripts/tts_openai.py article.md -o article.mp3 --model tts-1-hd

# Conserver les segments intermédiaires (pour reprise après interruption)
.venv/bin/python scripts/tts_openai.py livre.txt -o livre.mp3 \
    --tmp-dir cache/livre_segs --keep-segments
```

### Reprise après interruption

Si une longue synthèse plante (réseau, quota), relancer avec `--tmp-dir` et `--keep-segments` pointant sur le même dossier : les segments déjà produits ne sont pas re-synthétisés.

### Voix OpenAI disponibles

`alloy`, `ash`, `ballad`, `coral` (défaut, féminin neutre), `echo`, `fable`, `onyx` (masculin grave), `nova` (féminin clair), `sage`, `shimmer`, `verse`.

Toutes parlent un français correct. À tester sur un court extrait avant d'engager un livre entier.

## Usage — backend Kokoro (offline)

### Cas simple — français

```bash
.venv/bin/python scripts/tts_kokoro.py mon_texte.txt -o sortie.mp3 --lang f
```

### Autres langues

```bash
# Anglais US
.venv/bin/python scripts/tts_kokoro.py article.md -o article.mp3 --lang a --voice af_heart

# Espagnol
.venv/bin/python scripts/tts_kokoro.py texto.txt -o salida.mp3 --lang e

# Ajuster vitesse et silences
.venv/bin/python scripts/tts_kokoro.py texte.txt -o out.mp3 --lang f --speed 1.1 --gap-ms 350
```

### Voix Kokoro par langue

| Lang code | Langue | Voix recommandée |
|---|---|---|
| `a` | Anglais (US) | `af_heart`, `am_michael` |
| `b` | Anglais (GB) | `bf_emma`, `bm_george` |
| `f` | **Français** | **`ff_siwis`** (seule disponible) |
| `e` | Espagnol | `ef_dora`, `em_alex` |
| `i` | Italien | `if_sara`, `im_nicola` |
| `p` | Portugais (BR) | `pf_dora`, `pm_alex` |
| `h` | Hindi | `hf_alpha`, `hm_omega` |
| `j` | Japonais | `jf_alpha` (nécessite `pip install misaki[ja]`) |
| `z` | Mandarin | `zf_xiaoxiao` (nécessite `pip install misaki[zh]`) |

Liste complète : voir [VOICES.md sur Hugging Face](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md).

## Architecture interne (commune aux deux backends)

1. **Lecture** du texte UTF-8.
2. **Segmentation** : pour OpenAI, découpage à 3 000 caractères par défaut sur les fins de phrase françaises (regex `_SENT_END` qui détecte `.?!…` suivi d'une majuscule, « ou tiret cadratin). Pour Kokoro, la pipeline découpe automatiquement par groupes de souffle.
3. **Synthèse** segment par segment, MP3 individuels écrits dans un répertoire temporaire.
4. **Retries** : backoff exponentiel sur erreur réseau/API (5 tentatives par défaut côté OpenAI).
5. **Concaténation** : `pydub` pour OpenAI (avec silence configurable entre segments), `soundfile + ffmpeg` pour Kokoro.
6. **Export MP3** : VBR qualitatif (`-q:a 2` côté OpenAI, libmp3lame 192k côté Kokoro).

## Pièges connus

- **`OPENAI_API_KEY` non définie** : le script échoue immédiatement avec un message clair. Vérifier `echo $OPENAI_API_KEY`.
- **Coût qui dérape** : un roman de 80 000 mots ≈ 500 000 caractères ≈ 7,50 $ avec `gpt-4o-mini-tts`. Toujours estimer avec `wc -c fichier.txt` avant de lancer.
- **Quota OpenAI atteint** : le script retry avec backoff exponentiel, mais finit par échouer. Relancer avec `--tmp-dir` + `--keep-segments` pour reprendre là où ça a planté.
- **Segmentation FR ratée** : un texte sans majuscules (chat, transcription brute) n'est pas découpé sur les phrases ; le fallback brutal coupe tous les 3 000 caractères, ce qui peut couper un mot. Pré-traiter le texte pour avoir une ponctuation normale.
- **Instructions de prosodie ignorées** : seul `gpt-4o-mini-tts` les accepte. Avec `tts-1-hd` ou `tts-1`, le script affiche un avertissement et continue sans.
- **Voix qui change entre segments** : OpenAI maintient une bonne cohérence inter-segments, mais pas parfaite. Pour un livre entier, accepter une légère variation de timbre toutes les ~10 minutes.
- **Kokoro : première exécution lente** : le modèle (~330 MB) se télécharge depuis Hugging Face au premier appel. Cache ensuite dans `~/.cache/huggingface/`.
- **Kokoro : `espeak-ng` manquant** : la pipeline s'initialise sans erreur mais l'audio sort silencieux ou bruité pour les langues non-anglaises. Vérifier `espeak-ng --version`.
- **Kokoro : voix française unique** : `ff_siwis` peut paraître monotone sur un long texte. Pour du livre audio sérieux en français, basculer sur OpenAI.
- **Texte non-ASCII** : ouvrir systématiquement en UTF-8. Guillemets typographiques (« »), tirets cadratins (—), apostrophes courbes (') sont lus correctement par les deux backends.
- **Chunks vides** : si un segment ne contient que de la ponctuation, le script l'ignore pour éviter des erreurs de concat.
- **Pydub manquant** : nécessaire pour le backend OpenAI uniquement. Le `setup.sh` l'installe.
- **Python 3.13+ et `audioop`** : pydub dépend du module stdlib `audioop`, qui a été retiré en Python 3.13. Le `setup.sh` installe `audioop-lts` (le shim officiel) pour combler. Symptôme si oublié : `ModuleNotFoundError: No module named 'audioop'` ou `'pyaudioop'` au moment de la concaténation, après que la synthèse coûteuse a déjà été payée. Le script `tts_openai.py` met les segments en cache, donc relancer avec le même `--tmp-dir --keep-segments` ne re-paie pas la synthèse.

## Alternatives (autres modèles TTS)

Pour les cas où OpenAI et Kokoro ne suffisent pas.

### Voice cloning depuis un échantillon

**F5-TTS** (open-source, CC-BY-NC-4.0) — clone une voix depuis ~10 s de référence, qualité supérieure à Kokoro en français :

```bash
pip install f5-tts
# Voir https://github.com/SWivid/F5-TTS pour l'API CLI
```

**XTTS-v2** — multilingue natif + cloning, licence CPML (non commercial) :

```bash
pip install TTS
tts --text "Bonjour" --model_name tts_models/multilingual/multi-dataset/xtts_v2 \
    --speaker_wav reference.wav --language_idx fr --out_path out.wav
```

### Production studio / API commerciale

**Fish Audio S2 Pro** — actuellement #1 sur EmergentTTS-Eval, surpasse ElevenLabs. API payante.

**ElevenLabs** — qualité de référence pour voice cloning, plusieurs modèles et voix françaises.

## Estimation de coût et durée

### Backend OpenAI (`gpt-4o-mini-tts`)

| Texte | Caractères | Coût | Durée audio | Temps synthèse |
|---|---|---|---|---|
| Article 1 000 mots | ~6 000 | $0.09 | ~6 min | ~30 s |
| Nouvelle 10 000 mots | ~60 000 | $0.90 | ~1 h | ~5 min |
| Roman 80 000 mots | ~500 000 | $7.50 | ~8 h | ~45 min |

### Backend Kokoro

Gratuit. ~12× temps réel sur CPU 8 cœurs, ~70× temps réel sur GPU consumer.

## Suppression des fichiers intermédiaires

Conformément aux règles globales : **jamais `rm -rf`**, toujours `gio trash`. Les scripts suppriment leurs WAV/MP3 temporaires en fin d'exécution (sauf `--keep-segments`).

```bash
gio trash cache/livre_segs    # nettoyage manuel après reprise
```
