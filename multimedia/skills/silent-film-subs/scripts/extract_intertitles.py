#!/usr/bin/env python3
"""
Détecte les intertitres (texte clair sur fond sombre) d'un film muet,
les océrise dans la langue choisie via Tesseract et écrit un .srt brut.

Pipeline :
  1. Lecture séquentielle du .mkv, échantillonnage à --sample-fps
  2. Heuristique luminance pour flagger les frames d'intertitres
  3. Regroupement strict (gap_factor 1.0 + min_frames_per_seg 3) en segments
  4. Extraction de 3 frames candidates par segment (start/mid/end)
  5. OCR de chaque candidate, on garde celle avec le plus de mots ≥3 lettres
  6. Filtre post-OCR (ratio script + nombre de "vrais" mots)

Le résultat est ensuite à corriger/traduire par Claude.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

# Plages Unicode par script attendu — élargir au besoin.
SCRIPTS = {
    "rus": r"[А-Яа-яЁё]",
    "ukr": r"[А-Яа-яЁёІіЇїЄєҐґ]",
    "eng": r"[A-Za-z]",
    "fra": r"[A-Za-zÀ-ÿ]",
    "deu": r"[A-Za-zÄÖÜäöüß]",
    "ita": r"[A-Za-zÀ-ÿ]",
    "spa": r"[A-Za-zÀ-ÿñÑ]",
    "ell": r"[Α-Ωα-ω]",
}


def is_intertitle(gray, light_thr=130, mean_max=80, light_min=0.008, light_max=0.30):
    """Heuristique : intertitre = fond sombre + zone de texte clair (gris-clair sur archive)."""
    total = gray.size
    light = np.count_nonzero(gray > light_thr) / total
    return gray.mean() < mean_max and light_min < light < light_max


def script_ratio(text, pattern):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    rx = re.compile(pattern)
    matches = sum(1 for c in letters if rx.match(c))
    return matches / len(letters)


def long_words(text, pattern, min_word_len=3):
    rx = re.compile(pattern + r"{%d,}" % min_word_len)
    return rx.findall(text)


def looks_like_real_text(text, pattern, min_words=2, min_word_len=3):
    return len(long_words(text, pattern, min_word_len)) >= min_words


def fingerprint(gray, size=32):
    """Signature compacte d'une frame, tolérante aux petites variations."""
    small = cv2.resize(gray, (size, size), interpolation=cv2.INTER_AREA)
    return small.astype(np.float32).flatten()


def similarity(a, b):
    """Corrélation Pearson entre deux fingerprints."""
    a = a - a.mean()
    b = b - b.mean()
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom > 0 else 0.0


def detect_segments(video_path, sample_fps, min_dur, det_args,
                    gap_factor=1.0, min_frames_per_seg=3,
                    sim_thr=0.85):
    """Splitte un segment dès que (a) on perd trop de frames flaggées
    consécutives, OU (b) la similarité visuelle entre frames flaggées
    consécutives chute (changement d'intertitre sans fade noir)."""
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, int(round(fps / sample_fps)))
    print(f"[detect] {fps:.2f} fps, {total} frames, step={step}, sim_thr={sim_thr}",
          flush=True)

    flagged = []  # (idx, fingerprint)
    idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % step == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if is_intertitle(gray, **det_args):
                flagged.append((idx, fingerprint(gray)))
            if (idx // step) % 200 == 0:
                print(f"[detect] {idx}/{total} ({idx/fps:.0f}s) flagged={len(flagged)}",
                      flush=True)
        idx += 1
    cap.release()

    if not flagged:
        return []
    gap_thr = max(1, int(step * gap_factor))
    raw_segments = []
    f0, fp0 = flagged[0]
    cur = [f0, f0, 1, fp0]
    for f, fp in flagged[1:]:
        sim = similarity(cur[3], fp)
        if f - cur[1] <= gap_thr and sim >= sim_thr:
            cur[1] = f
            cur[2] += 1
            cur[3] = fp
        else:
            raw_segments.append(tuple(cur[:3]))
            cur = [f, f, 1, fp]
    raw_segments.append(tuple(cur[:3]))

    out = []
    for s, e, count in raw_segments:
        dur = (e - s) / fps
        if dur < min_dur or count < min_frames_per_seg:
            continue
        mid = (s + e) // 2
        out.append((s / fps, e / fps, [s, mid, e]))
    return out


def extract_frames_for_segments(video_path, segments, frames_dir):
    """Extrait toutes les frames candidates (start/mid/end) en une passe séquentielle."""
    targets = {}
    for i, (_, _, candidates) in enumerate(segments, 1):
        for kind, fidx in zip(("a", "b", "c"), candidates):
            targets.setdefault(fidx, []).append((i, kind))
    cap = cv2.VideoCapture(str(video_path))
    out = {}
    idx = 0
    max_idx = max(targets) if targets else -1
    while idx <= max_idx:
        ok, frame = cap.read()
        if not ok:
            break
        if idx in targets:
            for i, kind in targets[idx]:
                raw = frames_dir / f"seg{i:03d}_{kind}.png"
                cv2.imwrite(str(raw), frame)
                out.setdefault(i, []).append((kind, raw, frame))
        idx += 1
    cap.release()
    return out


def preprocess_for_ocr(bgr, target_max_dim=1200):
    """Texte clair sur fond sombre → texte noir sur fond blanc, agrandi, débruité."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    scale = max(1, target_max_dim // max(h, w))
    if scale > 1:
        gray = cv2.resize(gray, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    bw = cv2.medianBlur(bw, 3)
    return bw


def ocr(image_path, lang, tessdata):
    env = os.environ.copy()
    if tessdata:
        env["TESSDATA_PREFIX"] = str(tessdata)
    res = subprocess.run(
        ["tesseract", str(image_path), "-", "-l", lang, "--psm", "6"],
        env=env, capture_output=True, text=True,
    )
    return res.stdout.strip()


def fmt_ts(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds - h * 3600 - m * 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def write_srt(entries, path):
    with open(path, "w", encoding="utf-8") as f:
        for i, (start, end, text) in enumerate(entries, 1):
            f.write(f"{i}\n{fmt_ts(start)} --> {fmt_ts(end)}\n{text}\n\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video", type=Path)
    ap.add_argument("--out", type=Path, default=None,
                    help="Chemin de sortie .srt (défaut: <video>.<lang>.auto.srt)")
    ap.add_argument("--lang", default="rus",
                    help="Code Tesseract (rus, eng, deu, ita, ell, ukr, ...)")
    ap.add_argument("--tessdata", type=Path, default=None,
                    help="Dossier tessdata local (sinon TESSDATA_PREFIX du système)")
    # Échantillonnage
    ap.add_argument("--sample-fps", type=float, default=4)
    ap.add_argument("--min-dur", type=float, default=1.0)
    # Détection
    ap.add_argument("--light-thr", type=int, default=130,
                    help="Seuil luminance pour 'pixel clair' (texte d'intertitre).")
    ap.add_argument("--mean-max", type=int, default=80)
    ap.add_argument("--light-min", type=float, default=0.008)
    ap.add_argument("--light-max", type=float, default=0.30)
    # Regroupement
    ap.add_argument("--gap-factor", type=float, default=1.34,
                    help="Multiplicateur du step pour fusionner les flags (plus petit = + de segments).")
    ap.add_argument("--min-frames-per-seg", type=int, default=2,
                    help="Nombre minimal de frames flaggées dans un segment.")
    ap.add_argument("--sim-thr", type=float, default=0.85,
                    help="Seuil de corrélation (0-1) entre frames flaggées consécutives ; "
                         "en dessous, on splitte le segment (= changement d'intertitre).")
    # Filtre OCR
    ap.add_argument("--min-script-ratio", type=float, default=0.6)
    ap.add_argument("--min-text-len", type=int, default=5)
    ap.add_argument("--min-real-words", type=int, default=2,
                    help="Nombre minimal de mots ≥ 3 lettres pour considérer le texte 'réel'.")
    # Cache
    ap.add_argument("--frames-dir", type=Path, default=Path("cache/frames"))
    ap.add_argument("--segments-json", type=Path, default=Path("cache/segments.json"))
    ap.add_argument("--skip-detect", action="store_true",
                    help="Réutilise segments.json existant (saute l'étape de détection).")
    args = ap.parse_args()

    pattern = SCRIPTS.get(args.lang, r"[A-Za-z]")
    args.frames_dir.mkdir(parents=True, exist_ok=True)
    args.segments_json.parent.mkdir(parents=True, exist_ok=True)
    out_srt = args.out or args.video.with_suffix(f".{args.lang}.auto.srt")

    det_args = {
        "light_thr": args.light_thr,
        "mean_max": args.mean_max,
        "light_min": args.light_min,
        "light_max": args.light_max,
    }

    if args.skip_detect and args.segments_json.exists():
        with open(args.segments_json) as f:
            segments = [tuple(s) for s in json.load(f)]
        print(f"[detect] réutilisation : {len(segments)} segments", flush=True)
    else:
        segments = detect_segments(args.video, args.sample_fps, args.min_dur,
                                   det_args, args.gap_factor, args.min_frames_per_seg,
                                   args.sim_thr)
        with open(args.segments_json, "w") as f:
            json.dump(segments, f)
        print(f"[detect] {len(segments)} segments -> {args.segments_json}", flush=True)

    print("[extract] frames candidates (start/mid/end)...", flush=True)
    frames = extract_frames_for_segments(args.video, segments, args.frames_dir)

    entries = []
    fps_const = 25.0  # raffiner si besoin via ffprobe
    for i, (start, end, cand_idx) in enumerate(segments, 1):
        if i not in frames:
            continue
        candidates = []
        for kind, raw, bgr in frames[i]:
            prep = args.frames_dir / f"seg{i:03d}_{kind}_prep.png"
            bw = preprocess_for_ocr(bgr)
            cv2.imwrite(str(prep), bw)
            text = " ".join(ocr(prep, args.lang, args.tessdata).split())
            sc = len(long_words(text, pattern))
            candidates.append((sc, text, kind))
        candidates.sort(reverse=True)
        best_score, text, best_kind = candidates[0]
        ratio = script_ratio(text, pattern)
        real = looks_like_real_text(text, pattern, args.min_real_words)
        kept = (len(text) >= args.min_text_len
                and ratio >= args.min_script_ratio
                and real
                and best_score >= args.min_real_words)
        flag = "OK  " if kept else "SKIP"
        # Centrer le sub sur la frame qui a donné le meilleur OCR.
        kind_to_idx = {"a": cand_idx[0], "b": cand_idx[1], "c": cand_idx[2]}
        best_t = kind_to_idx[best_kind] / fps_const
        entry_start = max(start, best_t - 1.5)
        entry_end = min(end, best_t + 2.5)
        if entry_end - entry_start < 1.5:
            entry_end = entry_start + 1.5
        print(f"[ocr {i:3d}/{len(segments)}] {fmt_ts(entry_start)} k={best_kind} "
              f"score={best_score} ratio={ratio:.2f} {flag} {text[:55]}",
              flush=True)
        if kept:
            entries.append((entry_start, entry_end, text))

    write_srt(entries, out_srt)
    print(f"[srt] {len(entries)} entrées -> {out_srt}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
