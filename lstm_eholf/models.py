"""LSTM classifier and protocol-matched baselines (RNN, GRU, TNN, GAN)."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class LSTMClassifier(nn.Module):
    def __init__(self, input_dim: int, hidden: int = 128, layers: int = 2, dropout: float = 0.32, n_classes: int = 4):
        super().__init__()
        self.lstm = nn.LSTM(
            input_dim,
            hidden,
            num_layers=layers,
            batch_first=True,
            dropout=dropout if layers > 1 else 0.0,
        )
        self.drop = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden, n_classes)

    def forward(self, x: torch.Tensor, lengths: Optional[torch.Tensor] = None) -> torch.Tensor:
        packed = x
        if lengths is not None:
            packed = nn.utils.rnn.pack_padded_sequence(x, lengths.cpu(), batch_first=True, enforce_sorted=False)
        out, (h, _) = self.lstm(packed)
        hidden = h[-1]
        return self.fc(self.drop(hidden))


class RNNClassifier(nn.Module):
    def __init__(self, input_dim: int, hidden: int = 128, layers: int = 2, dropout: float = 0.32, n_classes: int = 4):
        super().__init__()
        self.rnn = nn.RNN(input_dim, hidden, num_layers=layers, batch_first=True, nonlinearity="tanh", dropout=dropout if layers > 1 else 0.0)
        self.drop = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden, n_classes)

    def forward(self, x, lengths=None):
        _, h = self.rnn(x)
        return self.fc(self.drop(h[-1]))


class GRUClassifier(nn.Module):
    def __init__(self, input_dim: int, hidden: int = 128, layers: int = 2, dropout: float = 0.32, n_classes: int = 4):
        super().__init__()
        self.gru = nn.GRU(input_dim, hidden, num_layers=layers, batch_first=True, dropout=dropout if layers > 1 else 0.0)
        self.drop = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden, n_classes)

    def forward(self, x, lengths=None):
        _, h = self.gru(x)
        return self.fc(self.drop(h[-1]))


class TNNClassifier(nn.Module):
    """Transformer neural network baseline used in Table 10 / Table 12."""

    def __init__(self, input_dim: int, hidden: int = 128, layers: int = 2, dropout: float = 0.32, n_classes: int = 4, nhead: int = 4):
        super().__init__()
        d_model = hidden
        nhead = nhead if d_model % nhead == 0 else 1
        self.proj = nn.Linear(input_dim, d_model)
        enc = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, dim_feedforward=d_model * 2, dropout=dropout, batch_first=True)
        self.tr = nn.TransformerEncoder(enc, num_layers=layers)
        self.fc = nn.Linear(d_model, n_classes)

    def forward(self, x, lengths=None):
        z = self.tr(self.proj(x))
        if lengths is not None:
            mask = torch.arange(z.size(1), device=z.device)[None, :] < lengths[:, None]
            z = (z * mask.unsqueeze(-1)).sum(1) / mask.sum(1, keepdim=True).clamp_min(1)
        else:
            z = z.mean(1)
        return self.fc(z)


class GANClassifier(nn.Module):
    """Adversarial feature classifier used as the GAN baseline in Table 10."""

    def __init__(self, input_dim: int, hidden: int = 128, layers: int = 2, dropout: float = 0.32, n_classes: int = 4):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.LeakyReLU(0.2),
            nn.Dropout(dropout),
            nn.Linear(hidden, hidden),
            nn.LeakyReLU(0.2),
        )
        self.disc = nn.Linear(hidden, 1)
        self.cls = nn.Linear(hidden, n_classes)
        self.gen = nn.Sequential(nn.Linear(hidden, hidden), nn.ReLU(), nn.Linear(hidden, input_dim))

    def forward(self, x, lengths=None):
        pooled = x.mean(1)
        h = self.encoder(pooled)
        return self.cls(h)

    def adversarial_step(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        pooled = x.mean(1)
        z = torch.randn(pooled.size(0), pooled.size(1), device=x.device)
        fake = self.gen(z)
        d_real = self.disc(self.encoder(pooled))
        d_fake = self.disc(self.encoder(fake.detach()))
        return d_real, d_fake


class CrossModalAttentionFusion(nn.Module):
    def __init__(self, dim_a: int, dim_v: int, dim_t: int = 0, hidden: int = 128):
        super().__init__()
        self.qa = nn.Linear(dim_a, hidden)
        self.kv = nn.Linear(dim_v + dim_t, hidden)
        self.out = nn.Linear(hidden, dim_a + dim_v + dim_t)

    def forward(self, a, v, t=None):
        ctx = v if t is None else torch.cat([v, t], dim=-1)
        q = self.qa(a)
        k = self.kv(ctx)
        w = torch.softmax(q * k / (q.size(-1) ** 0.5), dim=-1)
        fused = torch.cat([a, v] if t is None else [a, v, t], dim=-1)
        return fused + self.out(w)


class LowRankTensorFusion(nn.Module):
    def __init__(self, dim_a: int, dim_v: int, dim_t: int = 0, rank: int = 16, out_dim: Optional[int] = None):
        super().__init__()
        out_dim = out_dim or (dim_a + dim_v + dim_t)
        self.fa = nn.Linear(dim_a, rank)
        self.fv = nn.Linear(dim_v, rank)
        self.ft = nn.Linear(dim_t, rank) if dim_t else None
        self.out = nn.Linear(rank, out_dim)

    def forward(self, a, v, t=None):
        z = self.fa(a) * self.fv(v)
        if self.ft is not None and t is not None:
            z = z * self.ft(t)
        return self.out(z)


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def build_classifier(name: str, input_dim: int, hidden: int, layers: int, dropout: float, n_classes: int) -> nn.Module:
    name = name.lower()
    mapping = {
        "lstm": LSTMClassifier,
        "rnn": RNNClassifier,
        "gru": GRUClassifier,
        "tnn": TNNClassifier,
        "gan": GANClassifier,
    }
    if name not in mapping:
        raise ValueError(name)
    return mapping[name](input_dim, hidden, layers, dropout, n_classes)
