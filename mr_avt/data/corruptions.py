"""Evaluation-time audio/visual corruptions used in the manuscript."""

from __future__ import annotations

from typing import Optional

import torch
from torch.nn import functional as F


def add_gaussian_noise(waveform: torch.Tensor, snr_db: float) -> torch.Tensor:
    rms = waveform.pow(2).mean(dim=-1, keepdim=True).sqrt().clamp_min(1e-8)
    snr = 10 ** (snr_db / 10.0)
    noise_rms = rms / (snr ** 0.5)
    noise = torch.randn_like(waveform) * noise_rms
    return waveform + noise


def add_colored_noise(waveform: torch.Tensor, snr_db: float, kind: str = "pink") -> torch.Tensor:
    noise = torch.randn_like(waveform)
    if kind in {"pink", "traffic", "babble"}:
        # First-order coloring as a lightweight stand-in for named noise types.
        noise = torch.cumsum(noise, dim=-1)
        noise = noise / noise.std(dim=-1, keepdim=True).clamp_min(1e-8)
    return add_gaussian_noise(waveform, snr_db) * 0.0 + (
        waveform + _scale_noise(waveform, noise, snr_db)
    )


def _scale_noise(waveform: torch.Tensor, noise: torch.Tensor, snr_db: float) -> torch.Tensor:
    rms = waveform.pow(2).mean(dim=-1, keepdim=True).sqrt().clamp_min(1e-8)
    n_rms = noise.pow(2).mean(dim=-1, keepdim=True).sqrt().clamp_min(1e-8)
    snr = 10 ** (snr_db / 10.0)
    return noise * (rms / (n_rms * (snr ** 0.5)))


def apply_reverb(waveform: torch.Tensor, t60: float = 0.6, sample_rate: int = 16000) -> torch.Tensor:
    length = int(sample_rate * min(t60, 0.5))
    t = torch.arange(length, device=waveform.device, dtype=waveform.dtype)
    decay = torch.exp(-3.0 * t / max(length, 1))
    ir = decay * torch.randn(length, device=waveform.device, dtype=waveform.dtype)
    ir = ir / ir.norm().clamp_min(1e-8)
    bsz, samples = waveform.shape[0], waveform.shape[-1]
    wav = waveform.view(bsz, 1, samples)
    kernel = ir.view(1, 1, -1).flip(-1)
    padded = F.pad(wav, (kernel.size(-1) - 1, 0))
    out = F.conv1d(padded, kernel)
    return out.view_as(waveform)


def visual_frame_dropout(frames: torch.Tensor, drop_frac: float, frame_mask: Optional[torch.Tensor] = None):
    if drop_frac <= 0:
        mask = frame_mask if frame_mask is not None else torch.ones(frames.size(0), frames.size(1), dtype=torch.bool, device=frames.device)
        return frames, mask
    bsz, t = frames.size(0), frames.size(1)
    keep = torch.rand(bsz, t, device=frames.device) > drop_frac
    keep[:, 0] = True
    frames = frames * keep[:, :, None, None, None]
    return frames, keep
