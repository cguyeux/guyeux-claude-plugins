#!/usr/bin/env python3
"""
Synthèse texte -> MP3 via l'API Mistral TTS (Voxtral, voxtral-mini-tts).

Backend PAR DÉFAUT du skill. Voix préréglées ("preset") multilingues, dont
6 voix françaises (locutrice « Marie » en 6 variantes émotionnelles), voix
personnalisées clonées depuis un enregistrement (galerie, voir --create-voice),
et clonage ponctuel via un échantillon de référence (--ref-audio).

Différence clé avec le backend OpenAI : Voxtral n'accepte PAS d'instructions
de prosodie en texte libre. Le ton se choisit par la VARIANTE de voix
(fr_marie_neutral, fr_marie_curious, fr_marie_sad, ...), pas par un prompt.

Contrainte API : garder chaque requête sous ~300 mots -> segmentation
plafonnée en mots (et en caractères par sécurité).

Usage :
    export MISTRAL_API_KEY=...            # présent dans ~/.bashrc
    python tts_mistral.py texte.txt -o sortie.mp3
    python tts_mistral.py texte.txt -o sortie.mp3 --voice fr_marie_curious
    python tts_mistral.py --list-voices --lang fr
    python tts_mistral.py --list-voices --type custom      # galerie (voix clonées)

Galerie de voix (clonage depuis un enregistrement) :
    python tts_mistral.py --create-voice "Colas Breugnon" \
        --from-audio livre.mp3 --sample-start 120 --sample-dur 30 \
        --slug fr_colas_breugnon --gender male --voice-lang fr_fr
    python tts_mistral.py texte.txt -o out.mp3 --voice fr_colas_breugnon
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Iterable, List, Optional

# Imports tardifs (mistralai/pydub) : on autorise --help sans dépendances.

DEFAULT_MODEL = "voxtral-mini-tts-2603"
DEFAULT_VOICE = "fr_marie_neutral"

# Manifeste local de la galerie (voix clonées), à la racine du skill.
GALLERY_PATH = Path(__file__).resolve().parents[1] / "voices_gallery.json"

# Voix françaises préréglées connues (au 2026-03). La liste à jour vient de
# --list-voices ; celle-ci sert d'aide et de repli hors-ligne.
FR_PRESET_VOICES = [
    "fr_marie_neutral", "fr_marie_curious", "fr_marie_happy",
    "fr_marie_excited", "fr_marie_sad", "fr_marie_angry",
]


# ---------- Segmentation française (bornée en mots ET en caractères) ----------

_SENT_END = re.compile(
    r"(?<=\S[.?!…])\s+(?=[A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸ«—\-0-9])"
)


def _nwords(s: str) -> int:
    return len(s.split())


def split_text(text: str, max_words: int, max_chars: int) -> List[str]:
    """Découpe en segments <= max_words ET <= max_chars, aux fins de phrase FR."""
    text = text.strip()
    if _nwords(text) <= max_words and len(text) <= max_chars:
        return [text]

    sentences = [s.strip() for s in re.split(_SENT_END, text) if s and s.strip()]
    parts: List[str] = []
    buf = ""
    for s in sentences:
        cand = f"{buf} {s}".strip() if buf else s
        if buf and (_nwords(cand) > max_words or len(cand) > max_chars):
            parts.append(buf)
            buf = s
        else:
            buf = cand
    if buf:
        parts.append(buf)

    # Repli brutal pour une phrase seule trop longue : découpe par mots.
    final: List[str] = []
    for chunk in parts:
        if _nwords(chunk) <= max_words and len(chunk) <= max_chars:
            final.append(chunk)
        else:
            words = chunk.split()
            for i in range(0, len(words), max_words):
                final.append(" ".join(words[i:i + max_words]))
    return final


# ---------- Synthèse par segment avec retries ----------

def synth_segment(client, model: str, text: str, out_mp3: Path,
                  voice_id: Optional[str], ref_audio_b64: Optional[str]) -> None:
    kwargs: dict = dict(model=model, input=text, response_format="mp3")
    if ref_audio_b64 is not None:
        kwargs["ref_audio"] = ref_audio_b64
    else:
        kwargs["voice_id"] = voice_id
    resp = client.audio.speech.complete(**kwargs)
    out_mp3.write_bytes(base64.b64decode(resp.audio_data))


def synth_with_retries(client, model: str, text: str, out_mp3: Path,
                       voice_id: Optional[str], ref_audio_b64: Optional[str],
                       max_retries: int = 5, backoff: float = 2.0) -> None:
    delay = 1.0
    last_exc: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            synth_segment(client, model, text, out_mp3, voice_id, ref_audio_b64)
            return
        except Exception as exc:  # noqa: BLE001 — on relogue tout
            last_exc = exc
            if attempt >= max_retries:
                break
            print(f"  ! tentative {attempt}/{max_retries} échouée "
                  f"({type(exc).__name__}), retry dans {delay:.1f}s",
                  file=sys.stderr, flush=True)
            time.sleep(delay)
            delay *= backoff
    raise RuntimeError(f"Échec après {max_retries} tentatives") from last_exc


# ---------- Concaténation MP3 ----------

def concat_mp3(files: Iterable[Path], out_mp3: Path, silence_ms: int) -> None:
    from pydub import AudioSegment

    silence = AudioSegment.silent(duration=silence_ms)
    combined = None
    for f in files:
        seg = AudioSegment.from_file(f, format="mp3")
        combined = seg if combined is None else combined + silence + seg
    if combined is None:
        raise ValueError("Aucun segment audio à concaténer.")
    combined.export(out_mp3, format="mp3", parameters=["-q:a", "2"])


# ---------- Galerie de voix (manifeste local) ----------

def _load_gallery() -> dict:
    if GALLERY_PATH.exists():
        try:
            return json.loads(GALLERY_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {"voices": []}
    return {"voices": []}


def _save_gallery(g: dict) -> None:
    GALLERY_PATH.write_text(json.dumps(g, ensure_ascii=False, indent=2),
                            encoding="utf-8")


def resolve_voice(voice: str) -> str:
    """Si `voice` correspond au NOM d'une entrée de galerie, renvoie son id ;
    sinon renvoie `voice` tel quel (un slug ou un UUID sert de voice_id)."""
    g = _load_gallery()
    for v in g.get("voices", []):
        if voice in (v.get("name"), v.get("slug"), v.get("id")):
            return v.get("slug") or v.get("id") or voice
    return voice


# ---------- Pipeline principale ----------

def tts_file_to_mp3(input_txt: Path, output_mp3: Path, *,
                    model: str, voice_id: Optional[str],
                    ref_audio_b64: Optional[str],
                    max_words: int, max_chars: int, silence_ms: int,
                    keep_segments: bool, tmp_dir: Optional[Path]) -> None:
    from mistralai.client import Mistral
    from tqdm import tqdm
    import os

    text = input_txt.read_text(encoding="utf-8")
    segments = split_text(text, max_words, max_chars)
    label = "ref_audio" if ref_audio_b64 is not None else voice_id
    print(f"[tts-mistral] {len(text)} caractères ({_nwords(text)} mots) "
          f"-> {len(segments)} segments (<= {max_words} mots / {max_chars} car.)",
          flush=True)
    print(f"[tts-mistral] modèle={model} voix={label}", flush=True)

    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    cleanup_tmp = False
    if tmp_dir is None:
        tmp_dir = Path(tempfile.mkdtemp(prefix="tts_mistral_segments_"))
        cleanup_tmp = not keep_segments
    tmp_dir.mkdir(parents=True, exist_ok=True)
    print(f"[tts-mistral] segments -> {tmp_dir}", flush=True)

    seg_files: List[Path] = []
    try:
        for idx, seg in enumerate(tqdm(segments, desc="Synthèse")):
            seg_path = tmp_dir / f"seg_{idx:05d}.mp3"
            if seg_path.exists() and seg_path.stat().st_size > 0:
                seg_files.append(seg_path)
                continue
            synth_with_retries(client, model, seg, seg_path,
                               voice_id, ref_audio_b64)
            seg_files.append(seg_path)

        output_mp3.parent.mkdir(parents=True, exist_ok=True)
        concat_mp3(seg_files, output_mp3, silence_ms)
    finally:
        if cleanup_tmp:
            for p in seg_files:
                p.unlink(missing_ok=True)
            try:
                tmp_dir.rmdir()
            except OSError:
                pass


# ---------- Création d'une voix (clonage depuis un enregistrement) ----------

def _extract_sample(from_audio: Path, start: Optional[float],
                    dur: Optional[float]) -> Path:
    """Extrait un extrait mono MP3 propre pour le clonage (via ffmpeg)."""
    tmp = Path(tempfile.mkdtemp(prefix="tts_sample_")) / "sample.mp3"
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y"]
    if start is not None:
        cmd += ["-ss", str(start)]
    if dur is not None:
        cmd += ["-t", str(dur)]
    cmd += ["-i", str(from_audio), "-ac", "1",
            "-c:a", "libmp3lame", "-q:a", "4", str(tmp)]
    subprocess.run(cmd, check=True)
    return tmp


def create_voice(name: str, from_audio: Path, *, slug: Optional[str],
                 gender: Optional[str], languages: Optional[List[str]],
                 description: Optional[str], tags: Optional[List[str]],
                 style: Optional[str], suited_for: Optional[str],
                 sample_start: Optional[float], sample_dur: Optional[float],
                 retention_days: Optional[int], keep_sample: bool) -> int:
    import os
    from mistralai.client import Mistral

    if not from_audio.exists():
        print(f"ERREUR : enregistrement introuvable : {from_audio}", file=sys.stderr)
        return 1

    tmp_sample: Optional[Path] = None
    if sample_start is not None or sample_dur is not None:
        print(f"[tts-mistral] extraction d'un extrait "
              f"(start={sample_start}, dur={sample_dur}) via ffmpeg...", flush=True)
        tmp_sample = _extract_sample(from_audio, sample_start, sample_dur)
        sample_path = tmp_sample
    else:
        sample_path = from_audio

    b64 = base64.b64encode(sample_path.read_bytes()).decode()
    print(f"[tts-mistral] échantillon : {sample_path.name} "
          f"({len(b64) // 1024} KB en base64)", flush=True)

    # Description enrichie côté API : on y intègre style et usage conseillé.
    full_desc = "; ".join(x for x in [
        description,
        f"style : {style}" if style else None,
        f"pour : {suited_for}" if suited_for else None,
    ] if x)

    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    kwargs: dict = dict(name=name, sample_audio=b64, sample_filename=sample_path.name)
    if slug:
        kwargs["slug"] = slug
    if gender:
        kwargs["gender"] = gender
    if languages:
        kwargs["languages"] = languages
    if full_desc:
        kwargs["description"] = full_desc
    if tags:
        kwargs["tags"] = tags
    if retention_days is not None:
        kwargs["retention_notice"] = retention_days

    resp = client.audio.voices.create(**kwargs)
    d = resp.model_dump() if hasattr(resp, "model_dump") else dict(resp)
    vid, vslug = d.get("id"), d.get("slug")
    print(f"[tts-mistral] voix créée : id={vid} slug={vslug} "
          f"name={d.get('name')} gender={d.get('gender')} "
          f"langues={d.get('languages')} rétention={d.get('retention_notice')}")

    entry = {
        "name": name, "id": vid, "slug": vslug,
        "gender": d.get("gender"), "languages": d.get("languages"),
        "style": style, "suited_for": suited_for,
        "description": d.get("description"), "created_at": str(d.get("created_at")),
        "source_audio": str(from_audio),
        "sample_start": sample_start, "sample_dur": sample_dur,
    }
    g = _load_gallery()
    g["voices"] = [v for v in g.get("voices", []) if v.get("id") != vid] + [entry]
    _save_gallery(g)
    print(f"[tts-mistral] galerie mise à jour : {GALLERY_PATH}")
    print(f"[tts-mistral] utiliser : --voice {vslug or vid}")

    if tmp_sample is not None and not keep_sample:
        tmp_sample.unlink(missing_ok=True)
        try:
            tmp_sample.parent.rmdir()
        except OSError:
            pass
    return 0


# ---------- Utilitaire : liste des voix ----------

def list_voices(lang: Optional[str], type_: str) -> int:
    import os
    from mistralai.client import Mistral
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    items = []
    off = 0
    while True:
        batch = client.audio.voices.list(
            type_=type_, limit=100, offset=off).model_dump().get("items", [])
        items += batch
        if len(batch) < 100:
            break
        off += 100
    if lang:
        items = [it for it in items
                 if any(lang.lower() in (l or "").lower()
                        for l in (it.get("languages") or []))]
    kind = {"preset": "préréglées", "custom": "personnelles (galerie)",
            "all": "(toutes)"}.get(type_, type_)
    print(f"{len(items)} voix {kind}"
          + (f" (langue ~ '{lang}')" if lang else "") + " :")
    for it in items:
        print(f"  {str(it.get('slug')):<24} {str(it.get('name')):<24} "
              f"{it.get('gender')}  {it.get('languages')}  {it.get('tags')}")
    return 0


# ---------- CLI ----------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="TTS Mistral/Voxtral -> MP3 (segmentation FR + retries) "
                    "+ galerie de voix clonées.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("input", type=Path, nargs="?",
                    help="Fichier texte UTF-8 source.")
    ap.add_argument("-o", "--output", type=Path, default=None,
                    help="MP3 final en sortie.")
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    help="Modèle Mistral TTS (identifiant daté obligatoire).")
    ap.add_argument("--voice", default=DEFAULT_VOICE,
                    help="voice_id : slug préréglé (ex. fr_marie_neutral), slug "
                         "d'une voix de galerie, nom de galerie, ou UUID.")
    ap.add_argument("--ref-audio", type=Path, default=None,
                    help="[ponctuel] Fichier audio de référence pour clonage "
                         "sans sauvegarde (prioritaire sur --voice).")

    # Consultation / galerie
    ap.add_argument("--list-voices", action="store_true",
                    help="Liste les voix et quitte.")
    ap.add_argument("--type", dest="voice_type", default="preset",
                    choices=["preset", "custom", "all"],
                    help="Type de voix pour --list-voices "
                         "(custom = galerie de voix clonées).")
    ap.add_argument("--lang", default=None,
                    help="Filtre de langue pour --list-voices (ex. fr).")

    # Création de voix (clonage depuis un enregistrement)
    ap.add_argument("--create-voice", metavar="NOM", default=None,
                    help="Crée une voix clonée depuis --from-audio et quitte.")
    ap.add_argument("--from-audio", type=Path, default=None,
                    help="Enregistrement source pour --create-voice.")
    ap.add_argument("--sample-start", type=float, default=None,
                    help="Début de l'extrait de clonage (s).")
    ap.add_argument("--sample-dur", type=float, default=None,
                    help="Durée de l'extrait de clonage (s, ~20-30 conseillé).")
    ap.add_argument("--slug", default=None,
                    help="Slug mnémonique de la voix créée (ex. fr_colas_breugnon).")
    ap.add_argument("--gender", default=None, help="male / female (métadonnée).")
    ap.add_argument("--voice-lang", default=None,
                    help="Langue(s) de la voix créée, séparées par des virgules "
                         "(ex. fr_fr).")
    ap.add_argument("--description", default=None,
                    help="Description de la voix créée.")
    ap.add_argument("--style", default=None,
                    help="Style vocal (ex. 'grave, très expressif'). "
                         "Voir scripts/analyse_voix.py pour le mesurer.")
    ap.add_argument("--suited-for", default=None,
                    help="Narration conseillée (ex. 'récit épique, fantasy').")
    ap.add_argument("--tags", default=None,
                    help="Tags de la voix créée, séparés par des virgules.")
    ap.add_argument("--retention-days", type=int, default=None,
                    help="Rétention côté Mistral (jours ; défaut API si absent).")
    ap.add_argument("--keep-sample", action="store_true",
                    help="Conserve l'extrait de clonage extrait.")

    # Compat + synthèse
    ap.add_argument("--instructions", type=Path, default=None,
                    help="[ignoré] Voxtral n'accepte pas d'instructions de "
                         "prosodie ; conservé pour compatibilité d'appel.")
    ap.add_argument("--max-words", type=int, default=250,
                    help="Mots max par segment (contrainte API < 300).")
    ap.add_argument("--max-chars", type=int, default=1500,
                    help="Caractères max par segment (sécurité).")
    ap.add_argument("--silence-ms", type=int, default=120,
                    help="Silence inséré entre segments (ms).")
    ap.add_argument("--keep-segments", action="store_true",
                    help="Conserve les MP3 intermédiaires (reprise possible).")
    ap.add_argument("--tmp-dir", type=Path, default=None,
                    help="Répertoire des segments (défaut : mktemp).")
    return ap.parse_args()


def main() -> int:
    args = parse_args()

    import os
    if not os.environ.get("MISTRAL_API_KEY"):
        print("ERREUR : variable MISTRAL_API_KEY non définie "
              "(elle est normalement exportée par ~/.bashrc).", file=sys.stderr)
        return 1

    # --- Création de voix (galerie) ---
    if args.create_voice is not None:
        if args.from_audio is None:
            print("ERREUR : --create-voice exige --from-audio ENREGISTREMENT.",
                  file=sys.stderr)
            return 1
        languages = ([s.strip() for s in args.voice_lang.split(",")]
                     if args.voice_lang else None)
        tags = ([s.strip() for s in args.tags.split(",")] if args.tags else None)
        return create_voice(
            args.create_voice, args.from_audio,
            slug=args.slug, gender=args.gender, languages=languages,
            description=args.description, tags=tags,
            style=args.style, suited_for=args.suited_for,
            sample_start=args.sample_start, sample_dur=args.sample_dur,
            retention_days=args.retention_days, keep_sample=args.keep_sample,
        )

    # --- Liste de voix ---
    if args.list_voices:
        return list_voices(args.lang, args.voice_type)

    # --- Synthèse ---
    if args.input is None or args.output is None:
        print("ERREUR : préciser un fichier d'entrée et -o SORTIE.mp3 "
              "(ou utiliser --list-voices / --create-voice).", file=sys.stderr)
        return 1
    if not args.input.exists():
        print(f"ERREUR : fichier introuvable : {args.input}", file=sys.stderr)
        return 1

    if args.instructions is not None:
        print("[tts-mistral] note : --instructions est ignoré (Voxtral ne "
              "prend pas d'instructions de prosodie ; choisir plutôt une "
              "variante de voix, ex. fr_marie_curious).", file=sys.stderr)

    ref_audio_b64 = None
    if args.ref_audio is not None:
        if not args.ref_audio.exists():
            print(f"ERREUR : ref-audio introuvable : {args.ref_audio}",
                  file=sys.stderr)
            return 1
        ref_audio_b64 = base64.b64encode(args.ref_audio.read_bytes()).decode()

    voice_id = resolve_voice(args.voice)

    tts_file_to_mp3(
        args.input, args.output,
        model=args.model,
        voice_id=voice_id,
        ref_audio_b64=ref_audio_b64,
        max_words=args.max_words, max_chars=args.max_chars,
        silence_ms=args.silence_ms,
        keep_segments=args.keep_segments, tmp_dir=args.tmp_dir,
    )

    size_mb = args.output.stat().st_size / (1024 * 1024)
    print(f"[tts-mistral] OK : {args.output} ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
