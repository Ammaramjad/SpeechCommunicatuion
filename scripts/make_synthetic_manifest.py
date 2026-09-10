"""Create a tiny synthetic audio--visual manifest for smoke tests."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
import torch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/synthetic")
    parser.add_argument("--n-train", type=int, default=16)
    parser.add_argument("--n-val", type=int, default=8)
    parser.add_argument("--classes", type=int, default=4)
    parser.add_argument("--sr", type=int, default=16000)
    parser.add_argument("--seconds", type=float, default=0.5)
    parser.add_argument("--frames", type=int, default=4)
    parser.add_argument("--image-size", type=int, default=32)
    args = parser.parse_args()

    root = Path(args.out)
    audio_dir = root / "audio"
    video_dir = root / "video"
    audio_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    t = torch.linspace(0, args.seconds, int(args.sr * args.seconds))
    for split, n in (("train", args.n_train), ("val", args.n_val)):
        for i in range(n):
            label = i % args.classes
            freq = 120 + 40 * label
            wav = 0.2 * torch.sin(2 * np.pi * freq * t)
            audio_path = audio_dir / f"{split}_{i}.wav"
            video_path = video_dir / f"{split}_{i}.npy"
            try:
                import torchaudio

                torchaudio.save(str(audio_path), wav.unsqueeze(0), args.sr)
            except Exception:
                np.save(str(audio_path.with_suffix(".npy")), wav.numpy())
                audio_path = audio_path.with_suffix(".npy")
            video = np.random.rand(args.frames, 3, args.image_size, args.image_size).astype("float32")
            np.save(str(video_path), video)
            rows.append(
                {
                    "audio": str(audio_path),
                    "video": str(video_path),
                    "label": label,
                    "speaker": f"spk{i % 4}",
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
