"""Utterance-level fusion operators compared in Table 4."""

from __future__ import annotations

from typing import Optional

import numpy as np
import torch
import torch.nn as nn

from lstm_eholf.models import CrossModalAttentionFusion, LowRankTensorFusion


def concat_fuse(audio: np.ndarray, video: np.ndarray, text: Optional[np.ndarray] = None) -> np.ndarray:
    parts = [np.asarray(audio), np.asarray(video)]
    if text is not None:
        parts.append(np.asarray(text))
    return np.concatenate(parts, axis=-1).astype(np.float32)


class LateFusionHeads(nn.Module):
    def __init__(self, dim_a: int, dim_v: int, dim_t: int, n_classes: int):
        super().__init__()
        self.a = nn.Linear(dim_a, n_classes)
        self.v = nn.Linear(dim_v, n_classes)
        self.t = nn.Linear(dim_t, n_classes) if dim_t else None

    def forward(self, a, v, t=None):
        logits = self.a(a) + self.v(v)
        if self.t is not None and t is not None:
            logits = logits + self.t(t)
        n = 2 + int(self.t is not None and t is not None)
        return logits / n
