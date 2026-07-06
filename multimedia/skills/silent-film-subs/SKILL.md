---
name: silent-film-subs
description: Génère un sous-titrage français pour un film muet (.mkv/.mp4) en détectant automatiquement les intertitres (panneaux de texte clair sur fond sombre), en océrisant le texte source (russe par défaut, configurable) avec Tesseract, puis en confiant à Claude le nettoyage de l'OCR et la traduction française. Inclut le muxage final dans le conteneur. À utiliser quand l'utilisateur demande à compléter, créer ou réparer des sous-titres pour un film muet, à océriser des intertitres, à traduire des panneaux russes/anglais/allemands d'un film d'archive, ou quand un .srt existant est jugé incomplet par rapport aux panneaux affichés à l'écran.
---

Pipeline de sous-titrage pour films muets : détection des intertitres → OCR → nettoyage IA → traduction → muxage.

## Quand utiliser ce skill

- Un film muet a des intertitres dans une langue non maîtrisée par l'utilisateur (russe, allemand, italien, etc.) et il manque (ou il manque partiellement) un sous-titrage français.
- Un `.srt` existant est jugé incomplet (panneaux affichés sans traduction).
- L'utilisateur veut générer un `.fr.srt` à partir de zéro pour un film d'archive.

## Vue d'ensemble du pipeline

1. **Détection** des frames d'intertitres (heuristique luminance : fond sombre + zone de texte clair).
2. **Regroupement à deux critères** : (a) gap maximum entre frames flaggées consécutives + (b) **similarité visuelle** (corrélation Pearson sur signature 32×32). On splitte dès qu'un des deux critères casse → un intertitre = un segment, même si les transitions entre intertitres sont des fondus très courts (< 0.2 s).
3. **Extraction** de 3 frames candidates par segment (début / milieu / fin).
4. **OCR** des 3 candidates avec Tesseract, on garde celle avec le plus de mots ≥ 3 lettres dans le script cible.
5. **Filtrage** post-OCR (ratio script + nombre de "vrais" mots).
6. **Timing centré** sur la frame qui a donné le meilleur OCR (start = best_t − 1.5 s, end = best_t + 2.5 s) — robuste aux fusions résiduelles.
7. **Production** d'un fichier `.<lang>.auto.srt` brut.
8. **Nettoyage IA** : Claude relit chaque entrée et corrige les erreurs OCR en s'appuyant sur le contexte du film (synopsis, références internet, .srt existant éventuel).
9. **Traduction** : Claude traduit en français en bloc, soignée, en respectant le ton.
10. **Muxage** : `mkvmerge` ajoute la nouvelle piste FR au .mkv sans réencoder.

## Dépendances

Vérifier la présence des outils — installer ce qui manque avant de lancer :

```bash
which ffmpeg ffprobe tesseract mkvmerge python3
tesseract --list-langs
```

Pour le russe spécifiquement, télécharger `rus.traineddata` localement (sans toucher au système) :

```bash
mkdir -p tessdata
curl -fsSL -o tessdata/rus.traineddata \
  https://github.com/tesseract-ocr/tessdata_best/raw/main/rus.traineddata
```

Côté Python (venv local) :

```bash
python3 -m venv .venv
.venv/bin/pip install opencv-python-headless numpy
```

Le script `scripts/setup.sh` automatise ces étapes.

## Le script principal

Le script `scripts/extract_intertitles.py` fait tout le travail jusqu'à l'étape 7. Paramètres recommandés (calibrés sur du film d'archive russe en 25 fps) :

```bash
.venv/bin/python -u scripts/extract_intertitles.py FILM.mkv \
  --tessdata tessdata \
  --lang rus \
  --sample-fps 8 --min-dur 1.0 \
  --gap-factor 1.34 --min-frames-per-seg 2 --sim-thr 0.85 \
  --frames-dir cache/frames \
  --segments-json cache/segments.json \
  --out FILM.ru.auto.srt
```

Sorties :
- `FILM.ru.auto.srt` — sous-titres bruts (avec beaucoup de bruit que Claude triera ensuite).
- `cache/frames/segNNN_{a,b,c}.png` + `_prep.png` — 3 frames candidates par segment (audit visuel).
- `cache/segments.json` — timestamps des segments (réutilisable via `--skip-detect`).

### Calibration de la détection

Les seuils de `is_intertitle()` (luminance > 130, mean < 80, ratio de pixels clairs entre 0.8 % et 30 %) sont calibrés pour des films d'archive en N&B où le texte des panneaux est gris-clair (140-180), pas blanc pur. Si les détections sont mauvaises sur un film donné, échantillonner manuellement quelques frames d'intertitres connus et ajuster :

```python
import cv2, numpy as np
img = cv2.imread("frame_known_intertitle.png")
g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
print(f"mean={g.mean():.1f}")
for thr in [100, 130, 150, 180, 200]:
    print(f">{thr}: {np.count_nonzero(g>thr)/g.size*100:.2f}%")
```

Le seuil `--light-thr` doit attraper au moins 1-2 % de pixels sur un vrai intertitre, et 0 sur un écran noir/scène nocturne.

### Calibration du splitting des segments

Le paramètre clé est `--sim-thr` (corrélation entre frames flaggées consécutives) :
- **0.85** (défaut) : sépare des intertitres successifs ayant des contenus différents même sans fade noir entre eux.
- Plus bas (0.70) : autorise des intertitres qui changent légèrement (animations, fade).
- Plus haut (0.92) : split plus agressif, risque de couper un intertitre en deux.

`--gap-factor 1.34` avec `--sample-fps 8` donne un seuil temporel de ~5 frames (200 ms) — il faut au moins 200 ms d'écran noir entre deux intertitres pour qu'ils soient séparés par le critère temporel seul. La similarité visuelle attrape les cas plus courts.

## Étape de nettoyage par Claude

Une fois `.<lang>.auto.srt` produit, **Claude doit le relire et corriger** (étape qui ne peut pas être automatisée par script) :

1. Lire le `.<lang>.auto.srt`.
2. Identifier le film (recherche internet : titre, réalisateur, année, synopsis, intertitres connus).
3. Lire en référence : un `.srt` existant dans une autre langue (souvent l'anglais est intégré au .mkv via `ffmpeg -map 0:s:0 out.en.srt`), ou un `.fr.srt` partiel.
4. Pour chaque entrée OCR :
   - Si le texte est cohérent : corriger les erreurs de caractères (ex. К→П, Х→ЙФ©) en s'appuyant sur le contexte.
   - Si le texte est manifestement du bruit (peu de mots > 3 lettres, séquences cyrilliques aléatoires) : le supprimer.
5. **Vérifier visuellement les timestamps** suspects en extrayant la frame correspondante avec ffmpeg :
   ```bash
   ffmpeg -y -ss <SEC> -i FILM.mkv -frames:v 1 /tmp/check.png
   ```
   Le sous-titre doit tomber pile sur le panneau visible.

## Étape de traduction par Claude

Traduire le `.<lang>.cleaned.srt` en bloc, en respectant :
- Le ton du film (épique, intime, comique).
- L'époque du film (vocabulaire d'époque pour un film de 1926).
- La concision (sous-titres : 35 caractères max par ligne, max 2 lignes).
- Conserver les timestamps SubRip à l'identique.

Sortir `.fr.srt` en UTF-8 **avec terminaisons CRLF** (voir Pièges).

## Muxage final

Le script `scripts/mux_subtitles.sh` simplifie le mux en gérant la locale :

```bash
bash scripts/mux_subtitles.sh FILM.mkv FILM.fr.srt fre "Sous-titres FR (auto)"
```

Produit `FILM.muxed.mkv` avec la nouvelle piste FR comme piste par défaut.

## Pièges connus (et solutions)

- **Encodage CRLF obligatoire pour VLC** : un `.srt` UTF-8 avec terminaisons LF (Unix) peut être ignoré silencieusement par VLC, qui n'affiche aucun sous-titre. Toujours convertir : `sed -i 's/$/\r/' file.srt`. Tester avec `file file.srt` → on doit voir "with CRLF line terminators". (mpv, lui, lit le LF sans broncher.)
- **mkvmerge crashe avec `locale::facet::_S_create_c_locale`** : forcer `LC_ALL=C.UTF-8 LANG=C.UTF-8` avant l'appel. Le wrapper `mux_subtitles.sh` le fait déjà.
- **Désynchronisation d'un `.srt` existant** : un `.fr.srt` qu'on pense complet peut en réalité avoir des entrées qui tombent sur des écrans noirs dans la vidéo (preuve qu'il vient d'une autre version du film). Vérifier l'alignement avec ffmpeg avant de s'y fier.
- **Faux positifs de détection** : des scènes de nuit avec une lampe peuvent ressembler à un intertitre. `min_frames_per_seg=2` et `looks_like_real_text` éliminent la plupart. Le filtre `min_real_words` ≥ 2 (mots ≥ 3 caractères dans le script cible) supprime le bruit OCR aléatoire.
- **Texte stylisé du titre** : les titres de générique avec font artistique sont souvent mal océrisés (ex. "Крылья холопа" → "Прылья йФЛ©Па"). Claude doit corriger en s'appuyant sur le titre connu du film.
- **Long écran noir entre intertitres** : normal pour les films muets ; ne pas confondre avec un bug.
- **Texte gris-clair au lieu de blanc pur** : sur archive numérisée, le texte des panneaux a souvent une luminance 130-180, pas > 200. Toujours utiliser `--light-thr=130`, jamais 200.
- **Fusion titre + générique en un seul long segment** : si plusieurs intertitres successifs (titre, ministère, générique d'équipe...) sont séparés par moins d'une frame d'écran noir, le critère temporel ne les sépare pas. C'est le critère **similarité visuelle** (`--sim-thr`) qui les distingue. Sans ce critère, les timestamps OCR finissent placés en début de segment, ce qui décale tous les sous-titres de plusieurs secondes.
- **Timing OCR centré sur la frame "best"** : pour un long segment fusionné, le sous-titre serait à `start_segment` alors que le panneau OCRisé est en réalité à la frame médiane ou de fin. Le code recale automatiquement sur la frame qui a donné le meilleur OCR.
- **Pré-traitement OCR** : le script binarise (Otsu inverse) après agrandissement ×N pour amener la hauteur du texte autour de 40-60 px (sweet spot Tesseract).
- **OCR multi-frame** : pour chaque segment, le script extrait start/mid/end et garde l'OCR avec le plus de mots ≥ 3 lettres. Cela compense les segments où la frame médiane tombe entre deux intertitres ou sur une scène. Les 3 frames sont conservées pour audit visuel (`segNNN_a/b/c.png`).
- **OpenCV `CAP_PROP_POS_MSEC` est correct mais lent** : la lecture séquentielle assure que `idx * 1/fps` = PTS réel (vérifié sur H.264 avec B-frames). Pas besoin d'utiliser POS_MSEC.

## Workflow de débogage si VLC n'affiche rien

Si l'utilisateur dit "aucun sous-titre n'apparaît" alors que le `.srt` semble correct :

1. **Tester avec mpv** : `mpv FILM.muxed.mkv`. Si mpv affiche les subs mais VLC non, c'est un problème VLC (encodage, configuration).
2. **Vérifier les line endings** : `file FILM.fr.srt` doit dire "with CRLF line terminators".
3. **Test de sanité** : générer un `.srt` de test avec un sous-titre par seconde (`>>> SECONDE 00 <<<`) et muxer pour vérifier que VLC lit la piste.
4. **Vérifier la synchro** : extraire la frame à un timestamp donné par ffmpeg et confirmer que l'intertitre y est bien :
   ```bash
   ffmpeg -y -ss 54.5 -i FILM.mkv -frames:v 1 /tmp/check.png
   ```

## Estimation de coût

Pour un film de 73 min en 25 fps :
- Détection (lecture séquentielle, sample-fps=8) : ~10 min
- OCR (3 candidates × ~500 segments × 3 s) : ~25-30 min (le splitting fin produit beaucoup de segments)
- Nettoyage + traduction par Claude : 10-20 min selon la qualité OCR
- Total : ~45-60 min

**Optimisation** : si la détection a déjà produit `cache/segments.json`, utiliser `--skip-detect` pour rejouer uniquement l'OCR. Très utile pour ajuster le filtrage post-OCR sans relancer 10 min de détection.

## Suppression des fichiers intermédiaires

Conformément aux règles globales : **jamais `rm -rf`**, toujours `gio trash` sur les caches.

```bash
gio trash cache/frames cache/segments.json cache/run.log
```
