#!/usr/bin/env python3
"""
Synthèse texte -> MP3 via l'API OpenAI TTS (gpt-4o-mini-tts par défaut).

Backend recommandé pour la narration française expressive (livres audio,
fiction, polar). Supporte les *prosody instructions* sur gpt-4o-mini-tts
pour contrôler ton, rythme, émotion, pauses.

Usage :
    export OPENAI_API_KEY=sk-...
    python tts_openai.py texte.txt -o sortie.mp3
    python tts_openai.py texte.txt -o sortie.mp3 --voice onyx --instructions polar.txt
    python tts_openai.py texte.txt -o sortie.mp3 --model tts-1-hd  # sans instructions
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Iterable, List, Optional

# Imports tardifs : on autorise --help sans dépendances installées.


# ---------- Voix et instructions par défaut ----------

VOICES = [
    "alloy", "ash", "ballad", "coral", "echo",
    "fable", "onyx", "nova", "sage", "shimmer", "verse",
]

MODELS_WITH_INSTRUCTIONS = {"gpt-4o-mini-tts"}

DEFAULT_INSTRUCTIONS = """Vous êtes un narrateur de livre audio en français.
Lisez le texte avec naturel, clarté, et une intonation soignée respectant la ponctuation.
Tonalité posée, rythme modéré, pauses respectées aux virgules et aux fins de phrase.
Articulation précise, sans emphase théâtrale excessive."""


# ---------- Segmentation française ----------

_SENT_END = re.compile(
    r"(?<=\S[.?!…])\s+(?=[A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸ«—\-])"
)


def split_text(text: str, maxlen: int) -> List[str]:
    """Découpe `text` en segments <= maxlen, en privilégiant les fins de phrase françaises."""
    text = text.strip()
    if len(text) <= maxlen:
        return [text]

    sentences = re.split(_SENT_END, text)
    parts: List[str] = []
    buf = ""
    for s in sentences:
        if not s:
            continue
        if buf and len(buf) + 1 + len(s) > maxlen:
            parts.append(buf)
            buf = s
        else:
            buf = f"{buf} {s}" if buf else s
    if buf:
        parts.append(buf)

    # Fallback brutal pour phrases pathologiquement longues.
    final: List[str] = []
    for chunk in parts:
        if len(chunk) <= maxlen:
            final.append(chunk)
        else:
            for i in range(0, len(chunk), maxlen):
                final.append(chunk[i:i + maxlen])
    return final


# ---------- Synthèse par segment avec retries ----------

def synth_segment(client, model: str, voice: str, text: str,
                  out_mp3: Path, instructions: Optional[str]) -> None:
    kwargs = dict(model=model, voice=voice, input=text, response_format="mp3")
    if instructions and model in MODELS_WITH_INSTRUCTIONS:
        kwargs["instructions"] = instructions
    resp = client.audio.speech.create(**kwargs)
    out_mp3.write_bytes(resp.read())


def synth_with_retries(client, model: str, voice: str, text: str,
                       out_mp3: Path, instructions: Optional[str],
                       max_retries: int = 5, backoff: float = 2.0) -> None:
    delay = 1.0
    last_exc: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            synth_segment(client, model, voice, text, out_mp3, instructions)
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


# ---------- Pipeline principale ----------

def tts_file_to_mp3(input_txt: Path, output_mp3: Path, *,
                    model: str, voice: str, instructions: Optional[str],
                    max_chars: int, silence_ms: int,
                    keep_segments: bool, tmp_dir: Optional[Path]) -> None:
    from openai import OpenAI
    from tqdm import tqdm

    text = input_txt.read_text(encoding="utf-8")
    segments = split_text(text, max_chars)
    print(f"[tts-openai] {len(text)} caractères -> {len(segments)} segments "
          f"(max {max_chars}/seg)", flush=True)

    client = OpenAI()  # lit OPENAI_API_KEY

    cleanup_tmp = False
    if tmp_dir is None:
        tmp_dir = Path(tempfile.mkdtemp(prefix="tts_segments_"))
        cleanup_tmp = not keep_segments
    tmp_dir.mkdir(parents=True, exist_ok=True)
    print(f"[tts-openai] segments -> {tmp_dir}", flush=True)

    seg_files: List[Path] = []
    try:
        for idx, seg in enumerate(tqdm(segments, desc="Synthèse")):
            seg_path = tmp_dir / f"seg_{idx:05d}.mp3"
            if seg_path.exists() and seg_path.stat().st_size > 0:
                seg_files.append(seg_path)
                continue
            synth_with_retries(client, model, voice, seg, seg_path,
                               instructions)
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


# ---------- CLI ----------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="TTS OpenAI -> MP3 concaténé (segmentation FR + retries).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("input", type=Path, help="Fichier texte UTF-8 source.")
    ap.add_argument("-o", "--output", type=Path, required=True,
                    help="MP3 final en sortie.")
    ap.add_argument("--model", default="gpt-4o-mini-tts",
                    choices=["gpt-4o-mini-tts", "tts-1-hd", "tts-1"],
                    help="Modèle OpenAI. gpt-4o-mini-tts supporte les "
                         "instructions de prosodie.")
    ap.add_argument("--voice", default="coral", choices=VOICES,
                    help="Voix OpenAI.")
    ap.add_argument("--instructions", type=Path, default=None,
                    help="Fichier texte d'instructions de prosodie "
                         "(uniquement gpt-4o-mini-tts). Si absent, "
                         "utilise des instructions par défaut.")
    ap.add_argument("--no-instructions", action="store_true",
                    help="Désactive complètement les instructions "
                         "(narration neutre).")
    ap.add_argument("--max-chars", type=int, default=3000,
                    help="Taille max par segment (caractères).")
    ap.add_argument("--silence-ms", type=int, default=120,
                    help="Silence inséré entre segments (ms).")
    ap.add_argument("--keep-segments", action="store_true",
                    help="Conserve les MP3 intermédiaires (utile pour "
                         "reprise après interruption).")
    ap.add_argument("--tmp-dir", type=Path, default=None,
                    help="Répertoire pour les segments (défaut : mktemp). "
                         "Précisez-le pour pouvoir reprendre une synthèse "
                         "interrompue.")
    return ap.parse_args()


def main() -> int:
    args = parse_args()

    if not args.input.exists():
        print(f"ERREUR : fichier introuvable : {args.input}", file=sys.stderr)
        return 1

    import os
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERREUR : variable OPENAI_API_KEY non définie.", file=sys.stderr)
        return 1

    if args.no_instructions:
        instructions = None
    elif args.instructions is not None:
        instructions = args.instructions.read_text(encoding="utf-8")
    else:
        instructions = DEFAULT_INSTRUCTIONS

    if instructions and args.model not in MODELS_WITH_INSTRUCTIONS:
        print(f"[tts-openai] note : le modèle {args.model} ignore les "
              f"instructions de prosodie (réservé à gpt-4o-mini-tts).",
              file=sys.stderr)

    tts_file_to_mp3(
        args.input, args.output,
        model=args.model, voice=args.voice, instructions=instructions,
        max_chars=args.max_chars, silence_ms=args.silence_ms,
        keep_segments=args.keep_segments, tmp_dir=args.tmp_dir,
    )

    size_mb = args.output.stat().st_size / (1024 * 1024)
    print(f"[tts-openai] OK : {args.output} ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
