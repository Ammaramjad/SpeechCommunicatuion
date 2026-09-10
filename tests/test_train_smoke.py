"""Synthetic end-to-end training smoke test (tiny architecture, CPU)."""

from __future__ import annotations

import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mr_avt.config import MRAVTConfig
from mr_avt.data.datasets import ManifestDataset, Sample, collate_batch
from mr_avt.engine import evaluate, train_one_epoch
from mr_avt.models.losses import MRAVTCriterion
from mr_avt.models.mr_avt import MRAVT


def test_one_epoch_synthetic(tmp_path: Path):
    cfg = MRAVTConfig.tiny(num_classes=3)
    cfg.train.batch_size = 4
    samples = []
    sr = cfg.sample_rate
    n = int(sr * 0.3)
    audio_dir = tmp_path / "audio"
    video_dir = tmp_path / "video"
    audio_dir.mkdir()
    video_dir.mkdir()
    for i in range(8):
        wav = torch.sin(2 * torch.pi * (80 + 20 * (i % 3)) * torch.linspace(0, 0.3, n))
        wav_path = audio_dir / f"{i}.pt"
        vid_path = video_dir / f"{i}.npy"
        torch.save(wav, wav_path)
        import numpy as np

        np.save(vid_path, torch.rand(cfg.num_visual_frames, 3, cfg.image_size, cfg.image_size).numpy())
        samples.append(Sample(str(wav_path), str(vid_path), i % 3, speaker=str(i), session="1", split="train"))

    # Bypass file loaders that expect wav: inject tensors via a thin dataset subclass.
    class TensorDataset(ManifestDataset):
        def __getitem__(self, index):
            item = self.samples[index]
            wav = torch.load(item.audio_path)
            if wav.numel() < n:
                wav = torch.nn.functional.pad(wav, (0, n - wav.numel()))
            frames = torch.from_numpy(__import__("numpy").load(item.video_path)).float()
            return {
                "waveform": wav,
                "frames": frames,
                "label": torch.tensor(item.label),
                "frame_mask": torch.ones(self.num_visual_frames, dtype=torch.bool),
            }

    ds = TensorDataset(samples, sample_rate=sr, max_audio_seconds=0.3, num_visual_frames=cfg.num_visual_frames, image_size=cfg.image_size)
    loader = DataLoader(ds, batch_size=4, collate_fn=collate_batch)
    device = torch.device("cpu")
    model = MRAVT(cfg).to(device)
    criterion = MRAVTCriterion(
        cfg.num_classes,
        cfg.model.dim,
        0.07,
        {"cls": 1, "con": 0.1, "aug": 0.1, "cm": 0.1, "align": 0.1, "gate": 0.05},
    )
    opt = torch.optim.AdamW(list(model.parameters()) + list(criterion.parameters()), lr=1e-3)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda _: 1.0)
    stats = train_one_epoch(model, criterion, loader, opt, sched, device, 1.0)
    assert stats["loss"] > 0
    metrics = evaluate(model, criterion, loader, device)
    assert 0.0 <= metrics["accuracy"] <= 100.0
