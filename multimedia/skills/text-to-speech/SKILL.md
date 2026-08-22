---
name: text-to-speech
description: >-
  Synthetise un fichier .mp3 a partir d'un fichier texte (.txt, .md, chapitre de livre) via
  trois backends. Par defaut Mistral/Voxtral (voxtral-mini-tts) : voix prereglees
  multilingues dont 6 francaises en registres emotionnels, galerie de voix clonees depuis un
  enregistrement, clonage ponctuel par echantillon ; le ton se choisit par la variante de
  voix, Voxtral n'acceptant pas d'instructions de prosodie en texte libre. Alternative
  OpenAI gpt-4o-mini-tts quand on veut une prosodie pilotee par un prompt sur mesure ou plus
  de voix. Kokoro-82M en local, gratuit et hors ligne. Avant synthese, Claude lit un
  echantillon, identifie auteur, genre, epoque et ton, puis choisit la voix. A utiliser
  quand l'utilisateur demande de narrer un texte en audio, de generer un MP3 ou un livre
  audio, de lire un fichier a voix haute, ou mentionne TTS, synthese vocale, Voxtral,
  Kokoro, F5-TTS ou XTTS. Si l'utilisateur dit Whisper il confond avec la reconnaissance
  vocale : basculer quand meme sur ce skill.
---

Pipeline texte → MP3 pour livre audio en français (et autres langues). Backend par défaut **Mistral/Voxtral** (voix préréglées, le ton se règle par le choix de la variante de voix) ; backend **OpenAI** quand on veut piloter la prosodie par un prompt sur mesure ; backend **Kokoro** local (offline, gratuit).

## Choix du backend

| Critère | Mistral `voxtral-mini-tts` (défaut) | OpenAI `gpt-4o-mini-tts` | Kokoro-82M |
|---|---|---|---|
| Qualité narration FR | haute | très haute | moyenne (grade B-) |
| Contrôle du ton | par **variante de voix** (6 registres FR) | par **instructions de prosodie** en texte libre | ❌ |
| Voix françaises | 1 locutrice « Marie », 6 variantes émotionnelles | 11 voix expressives (dont masculines) | 1 (`ff_siwis`) |
| Clonage vocal | ✅ `--ref-audio` / voix perso sauvegardée | ❌ | ❌ |
| Prix | payant (voir tarifs Mistral) | ~$0.015 / 1k caractères | gratuit |
| Réseau | requis | requis | aucun |
| Confidentialité | texte envoyé à Mistral | texte envoyé à OpenAI | local |

**Règle de décision :**

- **Livre audio, fiction, narration française, par défaut** → Mistral/Voxtral, voix `fr_marie_*` selon le registre voulu. C'est le choix par défaut du skill.
- **Narration finement pilotée** (prompt de prosodie sur mesure) ou **besoin d'une voix masculine / d'un plus grand choix de timbres** → OpenAI `gpt-4o-mini-tts` avec `--instructions`.
- **Texte confidentiel, pas de réseau, ou budget zéro** → Kokoro.
- **Cloner une voix précise** → Mistral `--ref-audio` (ou voix personnalisée sauvegardée), sinon voir section "Alternatives".

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

### 3. Choisir le backend et la voix

**Backend par défaut : Mistral/Voxtral.** Le ton vient de la VARIANTE de voix, pas d'un prompt. Choisir la variante de la voix française « Marie » selon le registre dominant identifié à l'étape 2 :

| Ton dominant | Voix Mistral |
|---|---|
| neutre, posé, informatif, réflexif | `fr_marie_neutral` |
| curieux, questionnant, dialogue socratique | `fr_marie_curious` |
| chaleureux, tendre, conte | `fr_marie_happy` |
| enjoué, vif, énergique | `fr_marie_excited` |
| mélancolique, grave, tragique | `fr_marie_sad` |
| tendu, indigné, polémique | `fr_marie_angry` |

Lister les voix (toutes langues) : `.venv/bin/python scripts/tts_mistral.py --list-voices` (`--lang fr` pour filtrer). Une seule locutrice française **préréglée** (féminine). Pour une voix masculine ou un timbre précis, deux options : cloner une voix depuis un enregistrement (voir « Galerie de voix » plus bas, `--list-voices --type custom` pour les voir), ou basculer sur le backend OpenAI.

**Backend OpenAI (si l'utilisateur veut une prosodie pilotée par prompt, ou une voix masculine).** Choisir une voix (voir [`presets/README.md`](presets/README.md)) :

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

### 4. (OpenAI uniquement) Rédiger un prompt de prosodie sur mesure

**Voxtral ignore les instructions de prosodie** : ne franchir cette étape que pour le backend OpenAI. S'inspirer du preset le plus proche dans [`presets/`](presets/) (`conte_jeunesse.txt`, `polar.txt`, `roman_litteraire.txt`, `philosophie.txt`, `poesie.txt`, `essai_scientifique.txt`), **et l'adapter** :

- Au siècle (Balzac ≠ Houellebecq).
- À la personnalité de l'auteur (un Andersen mélancolique ≠ un Perrault malicieux).
- Aux particularités du texte précis (un conte fantastique de Hoffmann ≠ un conte moral de Tolstoï).

Un bon prompt fait 8-15 lignes et couvre : rôle du narrateur, effet vocal/timbre, tonalité, rythme, émotion, accentuation, prononciation, pauses. Voir [`presets/README.md`](presets/README.md) pour l'anatomie complète. Écrire le prompt à côté du texte source : `<nom_du_texte>.narration.txt`.

### 5. Annoncer le choix à l'utilisateur avant de lancer la synthèse

Pour un livre entier, le coût peut atteindre plusieurs dollars/euros. Avant de lancer, présenter :

- L'analyse rapide du texte (auteur, genre, ton identifiés).
- Le backend et la voix choisis (et pourquoi).
- Pour OpenAI : le prompt de prosodie rédigé (en bloc).
- L'estimation de coût (`wc -c texte.txt`).
- Une proposition de **test sur un extrait court** (500-1000 premiers caractères) avant d'engager le livre entier.

### 6. Lancer la synthèse

Backend par défaut (Mistral/Voxtral) :

```bash
.venv/bin/python <skill>/scripts/tts_mistral.py texte.txt -o sortie.mp3 --voice fr_marie_neutral
```

Backend OpenAI (prosodie sur mesure) :

```bash
.venv/bin/python <skill>/scripts/tts_openai.py texte.txt -o sortie.mp3 \
    --voice <choisie> --instructions <nom_du_texte>.narration.txt
```

### Exemple complet : dialogue de Platon (backend par défaut)

```
1. Claude lit hipparque.txt → identifie Platon, dialogue socratique, ironie + réfutation.
2. Backend Mistral (défaut). Voix : fr_marie_curious (registre questionnant du dialogue).
3. Voxtral n'accepte pas de prompt de prosodie → pas de fichier .narration.txt.
4. Test sur 700 chars :
   .venv/bin/python scripts/tts_mistral.py <(head -c 700 hipparque.txt) -o test.mp3
   --voice fr_marie_curious
5. Validation par l'utilisateur, ajustement éventuel de la variante de voix.
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

Le script `scripts/setup.sh` automatise tout. Il choisit un interpréteur compatible : **mistralai casse l'installation sous Python 3.14**, le script préfère donc `python3.13` ou `python3.12` s'ils sont présents, et n'ajoute `audioop-lts` (requis par pydub) que sous Python 3.13+.

```bash
bash scripts/setup.sh              # installe mistral + openai (backends cloud)
bash scripts/setup.sh --mistral    # Mistral uniquement (défaut du skill)
bash scripts/setup.sh --openai     # OpenAI uniquement
bash scripts/setup.sh --kokoro     # Kokoro uniquement
bash scripts/setup.sh --all        # les trois (kokoro tire torch, plus lourd)
```

### Clés API

Backend Mistral (défaut) :

```bash
export MISTRAL_API_KEY=...   # déjà présent dans ~/.bashrc
```

Backend OpenAI :

```bash
export OPENAI_API_KEY=sk-...
```

Pour les rendre persistantes, les ajouter à `~/.bashrc` ou `~/.config/fish/config.fish`.

## Usage : backend Mistral/Voxtral (par défaut)

### Narration simple

```bash
.venv/bin/python scripts/tts_mistral.py chapitre1.txt -o chapitre1.mp3
```

Utilise `voxtral-mini-tts-2603`, voix `fr_marie_neutral` par défaut.

### Choisir le registre (variante de voix)

Le ton se règle uniquement par la voix (pas de prompt de prosodie) :

```bash
.venv/bin/python scripts/tts_mistral.py dialogue.txt -o dialogue.mp3 --voice fr_marie_curious
.venv/bin/python scripts/tts_mistral.py tragedie.txt -o tragedie.mp3 --voice fr_marie_sad
```

### Lister les voix

```bash
.venv/bin/python scripts/tts_mistral.py --list-voices           # toutes langues
.venv/bin/python scripts/tts_mistral.py --list-voices --lang fr # français seulement
```

### Galerie de voix (clonage depuis un enregistrement)

Voxtral clone une voix à partir d'un enregistrement. Deux usages.

**Voix sauvegardée (galerie).** Pour chaque voix : la caractériser (sexe, registre, style, usage), puis la créer avec ces métadonnées, puis l'appeler par son slug.

```bash
# 1. Caractériser la voix : sexe (via F0), registre, expressivité, usage conseillé
.venv/bin/python scripts/analyse_voix.py livre.mp3 --start 120 --dur 30

# 2. Créer la voix avec sexe + style + usage (l'étape 1 imprime des suggestions à coller)
.venv/bin/python scripts/tts_mistral.py --create-voice "Le retour du Roi (Tolkien)" \
    --from-audio livre.mp3 --sample-start 90 --sample-dur 30 \
    --slug fr_retour_du_roi --voice-lang fr_fr \
    --gender male --style "grave, très expressif" \
    --suited-for "récit épique, fantasy, aventure, textes dramatiques"

# 3. L'utiliser (par slug, nom de galerie, ou UUID)
.venv/bin/python scripts/tts_mistral.py texte.txt -o out.mp3 --voice fr_retour_du_roi

# 4. Lister la galerie (voix personnelles côté compte Mistral)
.venv/bin/python scripts/tts_mistral.py --list-voices --type custom
```

**Toujours renseigner sexe + style + usage.** Le sexe est INFÉRÉ de la hauteur fondamentale mesurée par `analyse_voix.py` (repères adultes : homme ~100-135 Hz, femme ~190-220 Hz ; zone 145-185 Hz signalée ambiguë), jamais deviné à l'oreille. `--style` et `--suited-for` sont mémorisés dans `voices_gallery.json` et intégrés à la description côté Mistral. `analyse_voix.py` nécessite `praat-parselmouth numpy` (`setup.sh --analyse`).

`--create-voice` extrait l'échantillon via ffmpeg (si `--sample-start/--sample-dur` sont donnés), l'encode en base64, appelle l'API, puis enregistre la provenance (source, offsets, id, slug, style, usage) dans `voices_gallery.json` à la racine du skill. La voix vit ensuite côté compte Mistral et se référence par son `slug` (mnémonique, à définir avec `--slug`) ou son UUID. Pour corriger après coup (ex. sexe mal estimé) : `client.audio.voices.update(voice_id=..., gender=..., description=...)`.

**Clonage ponctuel (sans sauvegarde).** Un échantillon fourni à chaque synthèse, aucune voix créée côté compte :

```bash
.venv/bin/python scripts/tts_mistral.py texte.txt -o out.mp3 --ref-audio echantillon.wav
```

Bon échantillon : une seule voix, au calme, mono, ~20-30 s de parole continue. Pour un enregistrement long, viser un passage de narration pure (éviter jingle/intro) avec `--sample-start`.

### Reprise après interruption

Comme pour OpenAI : `--tmp-dir cache/livre_segs --keep-segments` ; les segments déjà produits ne sont pas re-synthétisés (donc pas repayés).

### Faux positif de garde-fou

Un `403 guardrail_violation` ne se résout pas par les retries : le script arrête immédiatement la synthèse et enregistre le texte fautif dans `blocked_seg_XXXXX.txt` à côté du cache. Par défaut, basculer l'œuvre entière vers OpenAI pour préserver l'intégrité du texte et une voix constante. Si l'utilisateur exige explicitement Voxtral, ne jamais modifier le fichier source : reformuler fidèlement ce seul extrait pour l'audio, le synthétiser avec la même voix dans le cache sous le nom `seg_XXXXX.mp3`, puis relancer exactement la même commande.

### Particularités Voxtral

- **Pas d'instructions de prosodie** : `--instructions` est accepté mais ignoré (avertissement). Régler le ton par `--voice`.
- **< 300 mots par requête** : la segmentation est plafonnée en mots (`--max-words 250` par défaut) en plus des caractères.
- **Une seule locutrice FR** (« Marie », féminine). Pour une voix masculine, utiliser OpenAI.
- Le SDK renvoie l'audio en **base64** ; le script le décode automatiquement.

## Usage : backend OpenAI (prosodie sur mesure)

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

## Usage : backend Kokoro (offline)

### Cas simple : français

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

## Architecture interne (commune aux trois backends)

1. **Lecture** du texte UTF-8.
2. **Segmentation** : Mistral découpe sur les fins de phrase françaises avec un double plafond mots + caractères (`--max-words 250`, `--max-chars 1500`) pour respecter la limite ~300 mots de Voxtral ; OpenAI découpe à 3 000 caractères sur les mêmes fins de phrase (regex `_SENT_END` : `.?!…` suivi d'une majuscule, « ou tiret cadratin) ; Kokoro découpe automatiquement par groupes de souffle.
3. **Synthèse** segment par segment, MP3 individuels écrits dans un répertoire temporaire (Mistral décode chaque segment depuis le base64 renvoyé par l'API).
4. **Retries** : backoff exponentiel sur erreur réseau/API (5 tentatives par défaut côté Mistral et OpenAI).
5. **Concaténation** : `pydub` pour les lectures Mistral courtes (avec silence configurable) ; au-delà de 100 segments Mistral assemble et réencode linéairement par manifeste `ffconcat` et ffmpeg, afin d'éviter une croissance quadratique en mémoire. OpenAI utilise `pydub`, Kokoro `soundfile + ffmpeg`.
6. **Export MP3** : VBR qualitatif (`-q:a 2` côté Mistral/OpenAI, libmp3lame 192k côté Kokoro).

## Pièges connus

### Spécifiques à Mistral/Voxtral

- **`mistralai` casse sous Python 3.14** : l'installation laisse un arbre partiel (pas de `mistralai/__init__.py`), et l'import échoue. Créer le venv avec `python3.12`/`python3.13` (le `setup.sh` corrigé le fait automatiquement).
- **Import du client** : dans cette version du SDK (2.7.0), le client est `from mistralai.client import Mistral` (et non `from mistralai import Mistral`).
- **Pas de voix masculine française** : seule « Marie » (féminine) est disponible en preset FR. Pour un narrateur masculin, backend OpenAI.
- **Pas d'instructions de prosodie** : Voxtral n'a pas d'équivalent d'`--instructions`. Le ton passe par la variante de voix (`fr_marie_curious`, `fr_marie_sad`, ...).
- **Limite ~300 mots/requête** : dépassée, l'API renvoie une erreur. La segmentation `--max-words 250` la respecte ; ne pas la remonter au-delà de ~280.
- **Modèle daté obligatoire** : `voxtral-mini-tts` seul est rejeté ; utiliser `voxtral-mini-tts-2603` (défaut du script). Vérifier périodiquement si un identifiant plus récent est publié.
- **Audio en base64** : `speech.complete(...)` renvoie `resp.audio_data` (chaîne base64), pas des octets bruts ni un flux binaire ; le script décode via `base64.b64decode`.
- **Long livre** : ne pas assembler des centaines de MP3 avec `combined + segment` dans pydub : ce patron devient quadratique. Le script passe automatiquement par ffmpeg au-delà de 100 segments. Après un découpage de vingt minutes, vérifier avec `ffprobe` le MP3 maître et les fichiers de début, milieu et fin, puis décoder un court extrait médian. Ne mettre le cache à la corbeille qu'après ces contrôles.

### Galerie / clonage de voix (Voxtral)

- **Échantillon = fichier audio en base64** (`sample_audio` pour `voices.create`, `ref_audio` pour la synthèse ponctuelle). Passer aussi `sample_filename` pour que l'API détecte le format via l'extension. Le script s'en charge.
- **Extrait de clonage** : viser ~20-30 s de parole continue, une seule voix, au calme. Sur un enregistrement long avec intro/jingle (litteratureaudio, LibriVox), prendre le passage avec `--sample-start` pour éviter le générique.
- **La voix vit côté compte Mistral** : `voices.create` crée un objet persistant (visible via `--list-voices --type custom`), pas seulement local. Le manifeste `voices_gallery.json` ne fait qu'enregistrer la provenance (source, offsets) ; supprimer ce fichier n'efface pas la voix côté Mistral (utiliser `voices.delete`).
- **`retention_notice`** (défaut 30) : aucune date d'expiration n'est renvoyée dans l'objet voix, et les voix préréglées portent la même valeur tout en étant permanentes ; sémantique exacte non confirmée. En cas de doute sur une conservation longue, passer `--retention-days` à une valeur élevée.
- **Slug vs UUID** : une voix créée avec `--slug` s'appelle par ce slug comme `voice_id` ; sans slug (cas d'anciennes voix), seul l'UUID fonctionne. Le script résout aussi un `--voice <nom de galerie>` via `voices_gallery.json`.

### Spécifiques à OpenAI

- **`OPENAI_API_KEY` non définie** : le script échoue immédiatement avec un message clair. Vérifier `echo $OPENAI_API_KEY`.
- **Coût qui dérape** : un roman de 80 000 mots ≈ 500 000 caractères ≈ 7,50 $ avec `gpt-4o-mini-tts`. Toujours estimer avec `wc -c fichier.txt` avant de lancer.
- **Quota OpenAI atteint** : le script retry avec backoff exponentiel, mais finit par échouer. Relancer avec `--tmp-dir` + `--keep-segments` pour reprendre là où ça a planté.
- **Segmentation FR ratée** : un texte sans majuscules (chat, transcription brute) n'est pas découpé sur les phrases ; le fallback brutal coupe tous les 3 000 caractères, ce qui peut couper un mot. Pré-traiter le texte pour avoir une ponctuation normale.
- **Instructions de prosodie ignorées** : seul `gpt-4o-mini-tts` les accepte. Avec `tts-1-hd` ou `tts-1`, le script affiche un avertissement et continue sans.
- **Voix qui change entre segments** : OpenAI maintient une bonne cohérence inter-segments, mais pas parfaite. Pour un livre entier, accepter une légère variation de timbre toutes les ~10 minutes.
- **Kokoro : première exécution lente** : le modèle (~330 MB) se télécharge depuis Hugging Face au premier appel. Cache ensuite dans `~/.cache/huggingface/`.
- **Kokoro : `espeak-ng` manquant** : la pipeline s'initialise sans erreur mais l'audio sort silencieux ou bruité pour les langues non-anglaises. Vérifier `espeak-ng --version`.
- **Kokoro : voix française unique** : `ff_siwis` peut paraître monotone sur un long texte. Pour du livre audio sérieux en français, basculer sur OpenAI.
- **Texte non-ASCII** : ouvrir systématiquement en UTF-8. Guillemets typographiques (« »), tirets cadratins (,), apostrophes courbes (') sont lus correctement par les trois backends (Voxtral recommande toutefois un texte simple, nombres verbalisés).
- **Chunks vides** : si un segment ne contient que de la ponctuation, le script l'ignore pour éviter des erreurs de concat.
- **Pydub manquant** : nécessaire pour le backend OpenAI uniquement. Le `setup.sh` l'installe.
- **Python 3.13+ et `audioop`** : pydub dépend du module stdlib `audioop`, qui a été retiré en Python 3.13. Le `setup.sh` installe `audioop-lts` (le shim officiel) pour combler. Symptôme si oublié : `ModuleNotFoundError: No module named 'audioop'` ou `'pyaudioop'` au moment de la concaténation, après que la synthèse coûteuse a déjà été payée. Le script `tts_openai.py` met les segments en cache, donc relancer avec le même `--tmp-dir --keep-segments` ne re-paie pas la synthèse.

## Alternatives (autres modèles TTS)

Pour les cas où OpenAI et Kokoro ne suffisent pas.

### Voice cloning depuis un échantillon

**F5-TTS** (open-source, CC-BY-NC-4.0), clone une voix depuis ~10 s de référence, qualité supérieure à Kokoro en français :

```bash
pip install f5-tts
# Voir https://github.com/SWivid/F5-TTS pour l'API CLI
```

**XTTS-v2**, multilingue natif + cloning, licence CPML (non commercial) :

```bash
pip install TTS
tts --text "Bonjour" --model_name tts_models/multilingual/multi-dataset/xtts_v2 \
    --speaker_wav reference.wav --language_idx fr --out_path out.wav
```

### Production studio / API commerciale

**Fish Audio S2 Pro**, actuellement #1 sur EmergentTTS-Eval, surpasse ElevenLabs. API payante.

**ElevenLabs**, qualité de référence pour voice cloning, plusieurs modèles et voix françaises.

## Estimation de coût et durée

### Backend Mistral/Voxtral (`voxtral-mini-tts`)

Facturé par Mistral (voir la page de tarifs officielle ; non chiffré ici). Débit observé : ~5,6 s de synthèse par segment de ~250 mots. Repère : un dialogue de ~3 400 mots (19 k caractères) → 15 segments, ~1 min 25 s de calcul, MP3 mono de ~17 min. Toujours estimer avec `wc -w texte.txt` et tester un extrait avant un livre entier.

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
