"""BERT [CLS] placeholder encoder + per-fold PCA (K=12 retains ~71.4% on IEMOCAP)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

import numpy as np

from lstm_eholf.config import TEXT_BERT_DIM, TEXT_PCA_K


def hash_embed_tokens(tokens: Sequence[str], dim: int = TEXT_BERT_DIM, seed: int = 0) -> np.ndarray:
    """Deterministic bag-of-token embedding used when a BERT checkpoint is unavailable.

    The shape and PCA interface match the manuscript: a 768-D [CLS] vector.
    When `transformers` is installed, `bert_cls` uses BERT-base instead.
    """
    rng0 = np.random.default_rng(seed)
    acc = np.zeros(dim, dtype=np.float64)
    if not tokens:
        tokens = ["[PAD]"]
    for tok in tokens:
        h = abs(hash((seed, tok))) % (2**32)
        acc += np.random.default_rng(h).normal(0, 1, size=dim)
    acc /= max(len(tokens), 1)
    # anisotropy: concentrate variance in a few directions, as in BERT [CLS]
    scale = np.linspace(3.0, 0.05, dim)
    return (acc * scale).astype(np.float32)


def bert_cls(text: str, seed: int = 0) -> np.ndarray:
    try:
        from transformers import AutoModel, AutoTokenizer
        import torch

        tok = AutoTokenizer.from_pretrained("bert-base-uncased")
        model = AutoModel.from_pretrained("bert-base-uncased")
        model.eval()
        enc = tok(text, return_tensors="pt", truncation=True, max_length=128)
        with torch.no_grad():
            out = model(**enc)
        return out.last_hidden_state[0, 0].cpu().numpy().astype(np.float32)
    except Exception:
        tokens = text.lower().split() if text else ["[PAD]"]
        return hash_embed_tokens(tokens, seed=seed)


@dataclass
class PCAModel:
    mean: np.ndarray
    components: np.ndarray  # (D, K)
    explained_variance_ratio: np.ndarray

    def transform(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=np.float64)
        if x.ndim == 1:
            return ((x - self.mean) @ self.components).astype(np.float32)
        return ((x - self.mean) @ self.components).astype(np.float32)

    @property
    def retained_variance(self) -> float:
        return float(self.explained_variance_ratio.sum() * 100.0)


def fit_pca(x: np.ndarray, k: int = TEXT_PCA_K) -> PCAModel:
    """PCA fitted on the training partition of a fold only."""
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 2:
        raise ValueError("PCA expects (N, D)")
    mean = x.mean(axis=0)
    xc = x - mean
    # SVD
    u, s, vt = np.linalg.svd(xc, full_matrices=False)
    k = min(k, vt.shape[0])
    components = vt[:k].T
    var = (s ** 2) / max(x.shape[0] - 1, 1)
    total = var.sum() + 1e-12
    evr = var[:k] / total
    return PCAModel(mean=mean.astype(np.float64), components=components, explained_variance_ratio=evr)


def bert_cls_pca(text: str, pca: PCAModel, seed: int = 0) -> np.ndarray:
    return pca.transform(bert_cls(text, seed=seed))
