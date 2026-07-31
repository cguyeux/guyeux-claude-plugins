#!/usr/bin/env python3
"""
Caractérise une voix à partir d'un enregistrement : sexe (via la hauteur
fondamentale F0), registre, expressivité, et une suggestion de narration
adaptée. Sert à documenter chaque voix ajoutée à la galerie (--create-voice
de tts_mistral.py) : sexe + style + usage conseillé.

Méthode : mesure objective de F0 avec Praat (parselmouth). Le sexe est
INFÉRÉ de la hauteur médiane (repères adultes : homme ~100-135 Hz,
femme ~190-220 Hz) ; la zone 145-185 Hz est signalée comme ambiguë.

Dépendances (hors venv TTS par défaut) :
    pip install praat-parselmouth numpy      # ou setup.sh --analyse
    (ffmpeg requis pour l'extraction/conversion)

Usage :
    python analyse_voix.py enregistrement.mp3
    python analyse_voix.py livre.mp3 --start 120 --dur 30
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


def _to_wav(src: Path, start, dur) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="analyse_voix_")) / "s.wav"
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y"]
    if start is not None:
        cmd += ["-ss", str(start)]
    if dur is not None:
        cmd += ["-t", str(dur)]
    cmd += ["-i", str(src), "-ac", "1", "-ar", "16000", str(tmp)]
    subprocess.run(cmd, check=True)
    return tmp


def suggest_usage(sex: str, register: str, expressive: bool) -> str:
    if sex == "masculin" and register in ("grave", "médium-grave"):
        base = ("récit épique, aventure, fantasy, roman à souffle, "
                "textes dramatiques, gravité")
    elif sex == "féminin" and register == "aigu":
        base = ("récit vif et chaleureux, conte, chronique enjouée, "
                "jeunesse, roman de terroir")
    elif sex == "féminin":
        base = "roman littéraire, récit intime, correspondance, poésie"
    elif register == "grave":
        base = "documentaire grave, polar, noir, essai dense"
    else:
        base = "roman littéraire, lecture générale"
    if not expressive:
        base += " ; convient aussi à la lecture informative posée (essai, manuel)"
    return base


def analyse(path: Path, label: str) -> dict:
    import numpy as np
    import parselmouth
    from parselmouth.praat import call

    snd = parselmouth.Sound(str(path))
    pitch = snd.to_pitch(time_step=0.01, pitch_floor=60, pitch_ceiling=500)
    f0 = pitch.selected_array["frequency"]
    voiced = f0[f0 > 0]
    if len(voiced) == 0:
        raise SystemExit("Aucune trame voisée détectée (extrait silencieux ?).")
    med = float(np.median(voiced))
    mean = float(np.mean(voiced))
    p10, p90 = (float(x) for x in np.percentile(voiced, [10, 90]))
    st_range = 12 * np.log2(p90 / p10) if p10 > 0 else 0.0
    voiced_frac = len(voiced) / len(f0)
    intensity = snd.to_intensity()
    imean = call(intensity, "Get mean", 0, 0, "energy")

    if med < 145:
        sex = "masculin"
    elif med > 185:
        sex = "féminin"
    else:
        sex = f"ambigu ({med:.0f} Hz, tendance {'masculin' if mean < 165 else 'féminin'})"

    if med < 115:
        register = "grave"
    elif med < 155:
        register = "médium-grave"
    elif med < 200:
        register = "médium"
    else:
        register = "aigu"

    if st_range < 5:
        expr = "posé, peu modulé"
    elif st_range < 9:
        expr = "modulation modérée"
    else:
        expr = "très expressif, ample"
    expressive = st_range >= 9

    sex_key = "masculin" if sex.startswith("masculin") else (
        "féminin" if sex.startswith("féminin") else "ambigu")
    usage = suggest_usage(sex_key, register, expressive)

    print(f"=== {label} ===")
    print(f"  F0 médiane : {med:.0f} Hz | moyenne : {mean:.0f} Hz | "
          f"p10-p90 : {p10:.0f}-{p90:.0f} Hz ({st_range:.1f} demi-tons)")
    print(f"  fraction voisée : {voiced_frac:.0%} | intensité moy. : {imean:.0f} dB")
    print(f"  SEXE          : {sex}")
    print(f"  REGISTRE      : {register}")
    print(f"  EXPRESSIVITÉ  : {expr}")
    print(f"  STYLE (résumé): {register}, {expr}")
    print(f"  ADAPTÉ POUR   : {usage}")
    print()
    print("  Suggestions pour --create-voice :")
    print(f"    --gender {sex_key if sex_key != 'ambigu' else '<à confirmer>'} "
          f"--style \"{register}, {expr}\" --suited-for \"{usage}\"")
    return {"sex": sex_key, "register": register, "style": f"{register}, {expr}",
            "suited_for": usage}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Caractérise une voix (sexe, registre, style) via F0.")
    ap.add_argument("audio", type=Path, help="Enregistrement à analyser.")
    ap.add_argument("--start", type=float, default=None,
                    help="Début de l'extrait analysé (s).")
    ap.add_argument("--dur", type=float, default=None,
                    help="Durée de l'extrait analysé (s ; ~30 conseillé).")
    ap.add_argument("--label", default=None, help="Étiquette d'affichage.")
    args = ap.parse_args()

    if not args.audio.exists():
        print(f"ERREUR : introuvable : {args.audio}", file=sys.stderr)
        return 1
    wav = _to_wav(args.audio, args.start, args.dur)
    try:
        analyse(wav, args.label or args.audio.name)
    finally:
        wav.unlink(missing_ok=True)
        try:
            wav.parent.rmdir()
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
