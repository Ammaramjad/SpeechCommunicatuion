"""Uncertainty-aware fusion and pre-gating of temporal audio branches."""

from __future__ import annotations

from typing import Dict, Tuple

import torch
from torch import nn
from torch.nn import functional as F


class UncertaintyAwareFusion(nn.Module):
    def __init__(self, dim: int) -> None:
        super().__init__()
        self.audio_unc = nn.Sequential(nn.Linear(dim, dim // 2), nn.GELU(), nn.Linear(dim // 2, 1))
        self.visual_unc = nn.Sequential(nn.Linear(dim, dim // 2), nn.GELU(), nn.Linear(dim // 2, 1))

    def forward(self, f_a: torch.Tensor, f_v: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        sigma_a = F.softplus(self.audio_unc(f_a)).squeeze(-1)
        sigma_v = F.softplus(self.visual_unc(f_v)).squeeze(-1)
        rho_a = torch.exp(-sigma_a)
        rho_v = torch.exp(-sigma_v)
        denom = (rho_a + rho_v).clamp_min(1e-8)
        w_a = rho_a / denom
        w_v = rho_v / denom
        fused = w_a.unsqueeze(-1) * f_a + w_v.unsqueeze(-1) * f_v
        weights = torch.stack([w_a, w_v], dim=-1)
        uncertainties = torch.stack([sigma_a, sigma_v], dim=-1)
        return fused, weights, uncertainties


class BranchGate(nn.Module):
    """Lightweight preview gate over the three audio temporal branches."""

    def __init__(self, n_mels: int, dim: int, hidden: int | None = None) -> None:
        super().__init__()
        hidden = hidden or max(32, dim // 4)
        self.preview = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.GELU(),
            nn.AdaptiveAvgPool2d((4, 4)),
            nn.Flatten(),
            nn.Linear(16 * 16, hidden),
            nn.GELU(),
        )
        self.classifier = nn.Linear(hidden, 3)

    def forward(self, spectrogram: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """spectrogram: [B, M, T] short-term Mel. Returns F0 and branch logits."""
        f0 = self.preview(spectrogram.unsqueeze(1))
        logits = self.classifier(f0)
        return f0, logits

    @staticmethod
    def select_branches(logits: torch.Tensor, delta: float = 0.5) -> torch.Tensor:
        """Return [B, 3] binary execution mask with argmax fallback."""
        gamma = torch.softmax(logits, dim=-1)
        active = gamma > delta
        none = ~active.any(dim=-1)
        if none.any():
            fallback = torch.zeros_like(active)
            fallback.scatter_(1, gamma.argmax(dim=-1, keepdim=True), True)
            active = torch.where(none.unsqueeze(-1), fallback, active)
        return active
