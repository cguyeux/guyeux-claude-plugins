#!/usr/bin/env python3
"""
Synthèse texte -> MP3 (ou WAV) avec Kokoro-82M.

Usage minimal :
    python tts_to_mp3.py texte.txt -o sortie.mp3 --lang f
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf


DEFAULT_VOICES = {
    "a": "af_heart",     # American English, féminin, grade A
    "b": "bf_emma",      # British English, féminin
    "e": "ef_dora",      # Espagnol, féminin
    "f": "ff_siwis",     # Français, féminin (seule voix disponible)
    "h": "hf_alpha",     # Hindi, féminin
    "i": "if_sara",      # Italien, féminin
    "j": "jf_alpha",     # Japonais, féminin (nécessite misaki[ja])
    "p": "pf_dora",      # Portugais BR, féminin
    "z": "zf_xiaoxiao",  # Mandarin, féminin (nécessite misaki[zh])
}

SAMPLE_RATE = 24_000  # Kokoro émet en 24 kHz


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Synthèse texte -> MP3/WAV via Kokoro-82M.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("input", type=Path, help="Fichier texte source (UTF-8).")
    ap.add_argument("-o", "--output", type=Path, required=True,
                    help="Chemin de sortie (.mp3 ou .wav).")
    ap.add_argument("--lang", default="f",
                    choices=sorted(DEFAULT_VOICES.keys()),
                    help="Code langue Kokoro (f=FR, a=EN-US, b=EN-GB, ...).")
    ap.add_argument("--voice", default=None,
                    help="ID voix Kokoro (ex: ff_siwis, af_heart). "
                         "Défaut : voix recommandée pour la langue.")
    ap.add_argument("--speed", type=float, default=1.0,
                    help="Multiplicateur de débit (0.5..1.5).")
    ap.add_argument("--gap-ms", type=int, default=200,
                    help="Silence inséré entre chunks (ms).")
    ap.add_argument("--bitrate", default="192k",
                    help="Bitrate MP3 (ignoré pour WAV).")
    ap.add_argument("--list-voices", action="store_true",
                    help="Affiche les voix par défaut et quitte.")
    return ap.parse_args()


def list_voices() -> None:
    print("Voix par défaut par langue :")
    for code, voice in sorted(DEFAULT_VOICES.items()):
        print(f"  {code}  -> {voice}")
    print("\nListe complète : https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md")


def synthesize(text: str, lang: str, voice: str, speed: float,
               gap_ms: int) -> np.ndarray:
    """Synthétise le texte et renvoie un tableau float32 mono."""
    from kokoro import KPipeline  # import tardif pour --list-voices rapide

    pipeline = KPipeline(lang_code=lang)
    gap = np.zeros(int(SAMPLE_RATE * gap_ms / 1000), dtype=np.float32)

    chunks: list[np.ndarray] = []
    for i, (graphemes, _phonemes, audio) in enumerate(
        pipeline(text, voice=voice, speed=speed)
    ):
        audio = np.asarray(audio, dtype=np.float32)
        if audio.size == 0:
            continue
        chunks.append(audio)
        chunks.append(gap)
        preview = (graphemes or "").replace("\n", " ")[:70]
        print(f"  [chunk {i:03d}] {audio.size / SAMPLE_RATE:5.1f}s  {preview}",
              flush=True)

    if not chunks:
        raise RuntimeError("Aucun audio généré (texte vide ou non synthétisable).")

    return np.concatenate(chunks)


def encode_mp3(wav_path: Path, mp3_path: Path, bitrate: str) -> None:
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(wav_path),
        "-codec:a", "libmp3lame", "-b:a", bitrate,
        str(mp3_path),
    ]
    subprocess.run(cmd, check=True)


def main() -> int:
    args = parse_args()

    if args.list_voices:
        list_voices()
        return 0

    if not args.input.exists():
        print(f"ERREUR : fichier introuvable : {args.input}", file=sys.stderr)
        return 1

    voice = args.voice or DEFAULT_VOICES[args.lang]
    text = args.input.read_text(encoding="utf-8").strip()
    if not text:
        print("ERREUR : fichier vide.", file=sys.stderr)
        return 1

    print(f"[tts] entrée  : {args.input} ({len(text)} caractères)")
    print(f"[tts] langue  : {args.lang}  voix : {voice}  vitesse : {args.speed}")
    print(f"[tts] sortie  : {args.output}")
    print("[tts] synthèse en cours...")

    audio = synthesize(text, lang=args.lang, voice=voice,
                       speed=args.speed, gap_ms=args.gap_ms)
    duration = audio.size / SAMPLE_RATE
    print(f"[tts] audio total : {duration:.1f}s ({duration / 60:.1f} min)")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    suffix = args.output.suffix.lower()

    if suffix == ".wav":
        sf.write(args.output, audio, SAMPLE_RATE)
    elif suffix == ".mp3":
        if not shutil.which("ffmpeg"):
            print("ERREUR : ffmpeg requis pour la sortie MP3.", file=sys.stderr)
            return 1
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_tmp = Path(tmp.name)
        try:
            sf.write(wav_tmp, audio, SAMPLE_RATE)
            encode_mp3(wav_tmp, args.output, args.bitrate)
        finally:
            wav_tmp.unlink(missing_ok=True)
    else:
        print(f"ERREUR : extension non supportée : {suffix} "
              f"(utiliser .mp3 ou .wav)", file=sys.stderr)
        return 1

    size_kb = args.output.stat().st_size / 1024
    print(f"[tts] écrit : {args.output} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
