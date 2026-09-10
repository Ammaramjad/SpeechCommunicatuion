"""Multi-resolution Mel spectrograms and resolution-specific audio transformers."""

from __future__ import annotations

from typing import Dict, Tuple

import torch
from torch import nn

try:
    import torchaudio
except ImportError:  # pragma: no cover
    torchaudio = None

from ..config import MRAVTConfig, ResolutionSpec
from .layers import PositionalEncoding, TransformerEncoder, masked_mean


def _mel_filterbank(n_fft: int, n_mels: int, sample_rate: int, device: torch.device) -> torch.Tensor:
    if torchaudio is not None:
        fb = torchaudio.functional.melscale_fbanks(
            n_freqs=n_fft // 2 + 1,
            f_min=0.0,
            f_max=float(sample_rate / 2),
            n_mels=n_mels,
            sample_rate=sample_rate,
            norm="slaney",
            mel_scale="htk",
        )
        return fb.to(device)
    freqs = torch.linspace(0, sample_rate / 2, n_fft // 2 + 1, device=device)
    mel = 2595.0 * torch.log10(1.0 + freqs / 700.0)
    mel_points = torch.linspace(mel[0], mel[-1], n_mels + 2, device=device)
    hz_points = 700.0 * (10 ** (mel_points / 2595.0) - 1.0)
    bins = torch.floor((n_fft + 1) * hz_points / sample_rate).long().clamp(0, n_fft // 2)
    fb = torch.zeros(n_fft // 2 + 1, n_mels, device=device)
    for m in range(n_mels):
        left, center, right = bins[m], bins[m + 1], bins[m + 2]
        if center > left:
            fb[left:center, m] = (torch.arange(left, center, device=device) - left) / (center - left).clamp_min(1)
        if right > center:
            fb[center:right, m] = (right - torch.arange(center, right, device=device)) / (right - center).clamp_min(1)
    return fb


def compute_log_mel(
    waveform: torch.Tensor,
    spec: ResolutionSpec,
    n_mels: int,
    sample_rate: int,
    max_frames: int,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Return log-Mel spectrograms ``[B, F, T]`` and valid-frame masks ``[B, T]``."""
    if waveform.dim() == 3:
        waveform = waveform.squeeze(1)
    window = torch.hann_window(spec.win_length, device=waveform.device, dtype=waveform.dtype)
    stft = torch.stft(
        waveform,
        n_fft=spec.n_fft,
        hop_length=spec.hop_length,
        win_length=spec.win_length,
        window=window,
        center=True,
        return_complex=True,
    )
    power = stft.abs().pow(2)
    fb = _mel_filterbank(spec.n_fft, n_mels, sample_rate, waveform.device)
    mel = torch.matmul(power.transpose(1, 2), fb).transpose(1, 2)
    log_mel = torch.log(mel.clamp_min(1e-6))
    if log_mel.size(-1) > max_frames:
        log_mel = log_mel[..., :max_frames]
    elif log_mel.size(-1) < max_frames:
        pad = max_frames - log_mel.size(-1)
        log_mel = torch.nn.functional.pad(log_mel, (0, pad))
    energy = log_mel.mean(dim=1)
    mask = energy > (energy.amin(dim=-1, keepdim=True) + 1e-4)
    # Always keep at least the first frame valid after padding.
    mask[:, 0] = True
    return log_mel, mask


class ResolutionBranch(nn.Module):
    def __init__(self, n_mels: int, cfg) -> None:
        super().__init__()
        self.proj = nn.Linear(n_mels, cfg.dim)
        self.pos = PositionalEncoding(cfg.dim)
        self.encoder = TransformerEncoder(cfg.dim, cfg.depth, cfg.heads, cfg.ffn_dim, cfg.dropout)
        self.norm = nn.LayerNorm(cfg.dim)

    def forward(self, spec: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        # spec: [B, M, T] -> [B, T, M]
        x = spec.transpose(1, 2)
        mean = x.mean(dim=(1, 2), keepdim=True)
        std = x.std(dim=(1, 2), keepdim=True).clamp_min(1e-5)
        x = (x - mean) / std
        x = self.pos(self.proj(x))
        key_padding = ~mask
        return self.encoder(x, key_padding_mask=key_padding)


class MultiResolutionAudioEncoder(nn.Module):
    def __init__(self, config: MRAVTConfig) -> None:
        super().__init__()
        self.config = config
        self.branches = nn.ModuleDict(
            {name: ResolutionBranch(config.n_mels, config.model) for name in config.resolutions}
        )
        self.pool_proj = nn.ModuleDict(
            {name: nn.Linear(config.model.dim, config.model.dim) for name in config.resolutions}
        )
        self.align_proj = nn.ModuleDict()
        names = list(config.resolutions)
        for i in names:
            for j in names:
                if i != j:
                    self.align_proj[f"{i}_{j}"] = nn.Linear(config.model.dim, config.model.dim, bias=False)
        self.query = nn.Parameter(torch.randn(config.model.dim) * 0.02)
        self.beta = 1.0

    def encode_all(
        self,
        spectrograms: Dict[str, torch.Tensor],
        masks: Dict[str, torch.Tensor],
        active: Dict[str, torch.Tensor] | None = None,
    ) -> Dict[str, torch.Tensor]:
        tokens: Dict[str, torch.Tensor] = {}
        for name, branch in self.branches.items():
            encoded = branch(spectrograms[name], masks[name])
            if active is not None:
                flag = active[name]
                if flag.dim() == 0:
                    flag = flag.view(1)
                encoded = encoded * flag.to(encoded.dtype).view(-1, 1, 1)
            tokens[name] = encoded
        return tokens

    def cross_resolution(
        self,
        tokens: Dict[str, torch.Tensor],
        masks: Dict[str, torch.Tensor],
        active_mask: torch.Tensor | None = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, torch.Tensor]]:
        names = list(self.branches.keys())
        summaries = []
        for name in names:
            pooled = masked_mean(tokens[name], masks[name])
            summaries.append(self.pool_proj[name](pooled))
        u = torch.stack(summaries, dim=1)  # [B, R, D]
        if active_mask is not None:
            u = u * active_mask.unsqueeze(-1)
        scale = self.config.model.dim ** 0.5
        logits = torch.matmul(u, u.transpose(1, 2)) / scale
        omega = torch.softmax(logits, dim=-1)
        identity = torch.eye(len(names), device=u.device).unsqueeze(0)
        off_diag = omega * (1.0 - identity)
        u_hat = u + torch.matmul(off_diag, u)

        align_terms = []
        for i, src in enumerate(names):
            for j, dst in enumerate(names):
                if src == dst:
                    continue
                mapped = self.align_proj[f"{src}_{dst}"](u_hat[:, i])
                align_terms.append((mapped - u_hat[:, j]).pow(2).mean(dim=-1))
        align_loss = torch.stack(align_terms, dim=0).mean(dim=0) if align_terms else u.new_zeros(u.size(0))

        scores = torch.matmul(u_hat, self.query)
        if active_mask is not None:
            scores = scores.masked_fill(active_mask < 0.5, -1e9)
        alpha = torch.softmax(scores, dim=-1)
        z_a = (alpha.unsqueeze(-1) * u_hat).sum(dim=1)
        branch_summaries = {name: u_hat[:, i] for i, name in enumerate(names)}
        return z_a, align_loss, branch_summaries
