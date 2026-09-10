"""Write a small in-repo demo corpus so training can run without licensed datasets."""

from __future__ import annotations

import argparse
import csv
import math
import wave
from pathlib import Path

import numpy as np


def write_wav(path: Path, audio: np.ndarray, sample_rate: int) -> None:
    pcm = np.clip(audio, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())


def make_clip(label: int, index: int, seconds: float, sample_rate: int, frames: int, image_size: int):
    t = np.linspace(0.0, seconds, int(sample_rate * seconds), endpoint=False, dtype=np.float32)
    freq = 180.0 + 70.0 * label
    vib = 3.0 + 0.4 * label
    audio = 0.25 * np.sin(2 * math.pi * freq * t) * (1.0 + 0.2 * np.sin(2 * math.pi * vib * t))
    audio = audio.astype(np.float32)
    rng = np.random.default_rng(1000 * label + index)
    video = np.zeros((frames, image_size, image_size, 3), dtype=np.uint8)
    color = {
        0: (200, 40, 40),
        1: (40, 180, 60),
        2: (40, 80, 200),
        3: (200, 180, 40),
    }[label % 4]
    for f in range(frames):
        video[f] = rng.integers(0, 40, size=(image_size, image_size, 3), dtype=np.uint8)
        x0 = 4 + (f * 2) % max(1, image_size - 12)
        y0 = 4 + (label * 3) % max(1, image_size - 12)
        video[f, y0 : y0 + 8, x0 : x0 + 8] = color
    return audio, video


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/demo")
    parser.add_argument("--n-train", type=int, default=32)
    parser.add_argument("--n-val", type=int, default=16)
    parser.add_argument("--classes", type=int, default=4)
    parser.add_argument("--sr", type=int, default=16000)
    parser.add_argument("--seconds", type=float, default=1.0)
    parser.add_argument("--frames", type=int, default=8)
    parser.add_argument("--image-size", type=int, default=32)
    args = parser.parse_args()

    root = Path(args.out)
    audio_dir = root / "audio"
    video_dir = root / "video"
    audio_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for split, n in (("train", args.n_train), ("val", args.n_val)):
        for i in range(n):
            label = i % args.classes
            audio, video = make_clip(label, i, args.seconds, args.sr, args.frames, args.image_size)
            audio_rel = f"audio/{split}_{i:03d}.wav"
            video_rel = f"video/{split}_{i:03d}.npy"
            write_wav(root / audio_rel, audio, args.sr)
            np.save(root / video_rel, video)
            rows.append(
                {
                    "audio": audio_rel,
                    "video": video_rel,
                    "label": label,
                    "speaker": f"spk{i % 8}",
                    "session": str((i % 5) + 1),
                    "split": split,
                }
            )
    manifest = root / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {manifest} ({len(rows)} clips)")


if __name__ == "__main__":
    main()
