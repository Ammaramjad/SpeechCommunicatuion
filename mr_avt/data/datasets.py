"""Dataset adapters for AFEW5.0, BAUM-1s, and IEMOCAP."""

from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset

AFEW_EMOTIONS = ["Angry", "Disgust", "Fear", "Happy", "Neutral", "Sad", "Surprise"]
BAUM_EMOTIONS = ["Anger", "Disgust", "Fear", "Happiness", "Sadness", "Surprise"]
IEMOCAP_EMOTIONS = ["ang", "hap", "neu", "sad"]  # excited merged into hap


@dataclass
class Sample:
    audio_path: str
    video_path: Optional[str]
    label: int
    speaker: str = ""
    session: str = ""
    split: str = "train"


def _resample_linear(wav: torch.Tensor, src_sr: int, dst_sr: int) -> torch.Tensor:
    if src_sr == dst_sr or wav.numel() == 0:
        return wav
    duration = wav.numel() / float(src_sr)
    new_len = max(1, int(round(duration * dst_sr)))
    x = wav.view(1, 1, -1)
    y = torch.nn.functional.interpolate(x, size=new_len, mode="linear", align_corners=False)
    return y.view(-1)


def _read_wav_file(path: Path) -> tuple[torch.Tensor, int]:
    try:
        import torchaudio

        wav, sr = torchaudio.load(str(path))
        if wav.size(0) > 1:
            wav = wav.mean(dim=0, keepdim=True)
        return wav.squeeze(0), int(sr)
    except Exception:
        import wave

        with wave.open(str(path), "rb") as handle:
            sr = handle.getframerate()
            n_ch = handle.getnchannels()
            width = handle.getsampwidth()
            raw = handle.readframes(handle.getnframes())
        if width == 2:
            audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        elif width == 1:
            audio = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        else:
            audio = np.frombuffer(raw, dtype=np.float32)
        if n_ch > 1:
            audio = audio.reshape(-1, n_ch).mean(axis=1)
        return torch.from_numpy(np.ascontiguousarray(audio)), int(sr)


def _load_waveform(path: str, sample_rate: int, max_seconds: float) -> torch.Tensor:
    file_path = Path(path)
    wav = torch.zeros(0)
    src_sr = sample_rate
    if file_path.exists():
        suffix = file_path.suffix.lower()
        if suffix == ".npy":
            wav = torch.from_numpy(np.load(file_path)).float().view(-1)
        elif suffix == ".pt":
            wav = torch.load(file_path, weights_only=False)
            if not torch.is_tensor(wav):
                wav = torch.as_tensor(wav)
            wav = wav.float().view(-1)
        else:
            wav, src_sr = _read_wav_file(file_path)
            wav = wav.float().view(-1)
        wav = _resample_linear(wav, src_sr, sample_rate)
    if wav.numel() == 0:
        wav = torch.zeros(int(sample_rate * min(1.0, max_seconds)))
    max_len = int(sample_rate * max_seconds)
    if wav.numel() > max_len:
        wav = wav[:max_len]
    elif wav.numel() < max_len:
        wav = torch.nn.functional.pad(wav, (0, max_len - wav.numel()))
    return wav


def _load_frames(path: Optional[str], num_frames: int, image_size: int) -> torch.Tensor:
    if path is None or not Path(path).exists():
        return torch.zeros(num_frames, 3, image_size, image_size)
    suffix = Path(path).suffix.lower()
    frames: List[torch.Tensor] = []
    try:
        if suffix in {".npy"}:
            arr = np.load(path)
            tensor = torch.from_numpy(arr).float()
            if float(tensor.max()) > 1.5:
                tensor = tensor / 255.0
            if tensor.dim() == 4 and tensor.size(-1) == 3:
                tensor = tensor.permute(0, 3, 1, 2)
            frames = [tensor[i] for i in range(min(num_frames, tensor.size(0)))]
        else:
            from PIL import Image
            import torchvision.transforms.functional as TF

            img = Image.open(path).convert("RGB")
            img = TF.resize(img, [image_size, image_size])
            frames = [TF.to_tensor(img)]
    except Exception:
        frames = []
    if not frames:
        return torch.zeros(num_frames, 3, image_size, image_size)
    while len(frames) < num_frames:
        frames.append(frames[-1])
    stacked = torch.stack(frames[:num_frames], dim=0)
    if stacked.shape[-1] != image_size or stacked.shape[-2] != image_size:
        stacked = torch.nn.functional.interpolate(
            stacked, size=(image_size, image_size), mode="bilinear", align_corners=False
        )
    return stacked


class ManifestDataset(Dataset):
    """CSV/JSON manifest with columns: audio, video, label, speaker, session, split."""

    def __init__(
        self,
        samples: Sequence[Sample],
        sample_rate: int = 16000,
        max_audio_seconds: float = 8.0,
        num_visual_frames: int = 16,
        image_size: int = 224,
        augment: bool = False,
        spec_augment: bool = True,
    ) -> None:
        self.samples = list(samples)
        self.sample_rate = sample_rate
        self.max_audio_seconds = max_audio_seconds
        self.num_visual_frames = num_visual_frames
        self.image_size = image_size
        self.augment = augment
        self.spec_augment = spec_augment

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> Dict[str, torch.Tensor]:
        item = self.samples[index]
        wav = _load_waveform(item.audio_path, self.sample_rate, self.max_audio_seconds)
        frames = _load_frames(item.video_path, self.num_visual_frames, self.image_size)
        if self.augment:
            if random.random() < 0.5:
                frames = torch.flip(frames, dims=[-1])
            wav = wav + 0.005 * torch.randn_like(wav)
        frame_mask = torch.ones(self.num_visual_frames, dtype=torch.bool)
        return {
            "waveform": wav,
            "frames": frames,
            "label": torch.tensor(item.label, dtype=torch.long),
            "frame_mask": frame_mask,
            "speaker": item.speaker,
            "session": item.session,
        }


def _resolve_media_path(root: Path, value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    media = Path(value)
    if not media.is_absolute():
        media = root / media
    return str(media)


def load_manifest(path: str | Path) -> List[Sample]:
    path = Path(path)
    root = path.parent
    samples: List[Sample] = []
    if path.suffix == ".json":
        rows = json.loads(path.read_text(encoding="utf-8"))
        for row in rows:
            samples.append(
                Sample(
                    audio_path=_resolve_media_path(root, row["audio"]) or "",
                    video_path=_resolve_media_path(root, row.get("video")),
                    label=int(row["label"]),
                    speaker=row.get("speaker", ""),
                    session=str(row.get("session", "")),
                    split=row.get("split", "train"),
                )
            )
        return samples
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            samples.append(
                Sample(
                    audio_path=_resolve_media_path(root, row["audio"]) or "",
                    video_path=_resolve_media_path(root, row.get("video")),
                    label=int(row["label"]),
                    speaker=row.get("speaker", ""),
                    session=row.get("session", ""),
                    split=row.get("split", "train"),
                )
            )
    return samples


def filter_split(samples: Sequence[Sample], split: str) -> List[Sample]:
    return [s for s in samples if s.split == split]


def iemocap_session_folds(samples: Sequence[Sample]) -> List[Tuple[List[Sample], List[Sample]]]:
    """Five-fold leave-one-session-out."""
    sessions = sorted({s.session or s.speaker for s in samples})
    if not sessions:
        sessions = [str(i) for i in range(5)]
        tagged = []
        for i, s in enumerate(samples):
            tagged.append(Sample(s.audio_path, s.video_path, s.label, s.speaker, str(i % 5), s.split))
        samples = tagged
        sessions = [str(i) for i in range(5)]
    folds = []
    for held in sessions:
        train = [s for s in samples if (s.session or s.speaker) != held]
        test = [s for s in samples if (s.session or s.speaker) == held]
        if train and test:
            folds.append((train, test))
    return folds


def baum_losgo_folds(samples: Sequence[Sample], n_folds: int = 5) -> List[Tuple[List[Sample], List[Sample]]]:
    speakers = sorted({s.speaker for s in samples})
    if not speakers:
        speakers = [str(i) for i in range(n_folds)]
        samples = [
            Sample(s.audio_path, s.video_path, s.label, str(i % n_folds), s.session, s.split)
            for i, s in enumerate(samples)
        ]
        speakers = sorted({s.speaker for s in samples})
    folds = []
    groups = np.array_split(speakers, n_folds)
    for held in groups:
        held_set = set(held.tolist())
        train = [s for s in samples if s.speaker not in held_set]
        test = [s for s in samples if s.speaker in held_set]
        if train and test:
            folds.append((train, test))
    return folds


def collate_batch(batch: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
    return {
        "waveform": torch.stack([b["waveform"] for b in batch], dim=0),
        "frames": torch.stack([b["frames"] for b in batch], dim=0),
        "label": torch.stack([b["label"] for b in batch], dim=0),
        "frame_mask": torch.stack([b["frame_mask"] for b in batch], dim=0),
    }
