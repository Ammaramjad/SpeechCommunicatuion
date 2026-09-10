"""Vision Transformer visual encoder with temporal smoothing."""

from __future__ import annotations

import torch
from torch import nn

from ..config import MRAVTConfig
from .layers import masked_mean


class PatchEmbed(nn.Module):
    def __init__(self, image_size: int, patch_size: int, dim: int, in_ch: int = 3) -> None:
        super().__init__()
        self.proj = nn.Conv2d(in_ch, dim, kernel_size=patch_size, stride=patch_size)
        n_patches = (image_size // patch_size) ** 2
        self.cls = nn.Parameter(torch.zeros(1, 1, dim))
        self.pos = nn.Parameter(torch.zeros(1, n_patches + 1, dim))
        nn.init.trunc_normal_(self.pos, std=0.02)
        nn.init.trunc_normal_(self.cls, std=0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.proj(x).flatten(2).transpose(1, 2)
        cls = self.cls.expand(x.size(0), -1, -1)
        x = torch.cat([cls, x], dim=1)
        return x + self.pos


class VisualEncoder(nn.Module):
    """Per-frame ViT followed by EMA temporal smoothing (Eq. for ``\\tilde H_t^v``)."""

    def __init__(self, config: MRAVTConfig) -> None:
        super().__init__()
        m = config.model
        self.eta = m.eta
        self.embed = PatchEmbed(m.image_size, m.patch_size, m.dim)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=m.dim,
            nhead=m.heads,
            dim_feedforward=m.ffn_dim,
            dropout=m.dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=m.depth, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(m.dim)

    def encode_frames(self, frames: torch.Tensor) -> torch.Tensor:
        """frames: [B, T, C, H, W] -> token sequences [B, T, D] (CLS)."""
        bsz, t, c, h, w = frames.shape
        x = frames.reshape(bsz * t, c, h, w)
        tokens = self.embed(x)
        tokens = self.norm(self.encoder(tokens))
        cls = tokens[:, 0]
        return cls.view(bsz, t, -1)

    def smooth(self, frame_tokens: torch.Tensor) -> torch.Tensor:
        smoothed = []
        prev = None
        for t in range(frame_tokens.size(1)):
            cur = frame_tokens[:, t]
            if prev is None:
                out = cur
            else:
                out = self.eta * cur + (1.0 - self.eta) * prev
            smoothed.append(out)
            prev = out
        return torch.stack(smoothed, dim=1)

    def forward(self, frames: torch.Tensor, frame_mask: torch.Tensor | None = None) -> tuple[torch.Tensor, torch.Tensor]:
        tokens = self.encode_frames(frames)
        tokens = self.smooth(tokens)
        pooled = masked_mean(tokens, frame_mask)
        return pooled, tokens
