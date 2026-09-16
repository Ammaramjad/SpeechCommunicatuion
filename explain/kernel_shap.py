"""Kernel SHAP on the fused feature vector (softmax class probabilities)."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np


def _kmeans_background(x: np.ndarray, k: int, rng: np.random.Generator) -> np.ndarray:
    k = min(k, len(x))
    centers = x[rng.choice(len(x), size=k, replace=False)].copy()
    for _ in range(8):
        d = ((x[:, None, :] - centers[None, :, :]) ** 2).sum(-1)
        assign = d.argmin(1)
        for i in range(k):
            members = x[assign == i]
            if len(members):
                centers[i] = members.mean(0)
    return centers


def kernel_shap(
    predict_fn: Callable[[np.ndarray], np.ndarray],
    x: np.ndarray,
    background: np.ndarray,
    n_samples: int = 512,
    seed: int = 0,
) -> np.ndarray:
    """Return phi of shape (n_classes, n_features) for a single instance x (1, D) or (D,).

    Kernel weights follow Lundberg & Lee. Coalitions replace absent features by
    background means.
    """
    rng = np.random.default_rng(seed)
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    bg = np.asarray(background, dtype=np.float64)
    if bg.ndim == 1:
        bg = bg[None, :]
    mu = bg.mean(axis=0)
    d = x.size
    # always include empty and full coalitions
    coalitions = [np.zeros(d, dtype=bool), np.ones(d, dtype=bool)]
    for _ in range(max(n_samples - 2, 0)):
        k = int(rng.integers(1, d)) if d > 1 else 1
        mask = np.zeros(d, dtype=bool)
        mask[rng.choice(d, size=k, replace=False)] = True
        coalitions.append(mask)
    masks = np.stack(coalitions, axis=0).astype(np.float64)
    synth = masks * x[None, :] + (1.0 - masks) * mu[None, :]
    y = np.asarray(predict_fn(synth.astype(np.float32)))
    if y.ndim == 1:
        y = y[:, None]
    # SHAP kernel
    msum = masks.sum(1)
    w = np.ones(len(masks))
    for i, s in enumerate(msum):
        if s == 0 or s == d:
            w[i] = 1e6
        else:
            w[i] = (d - 1) / (s * (d - s) + 1e-8)
    sqrtw = np.sqrt(w)[:, None]
    z = masks
    zc = z - z.mean(0, keepdims=True)
    yw = (y - y.mean(0, keepdims=True)) * sqrtw
    zw = zc * sqrtw
    # ridge
    xtx = zw.T @ zw + 1e-3 * np.eye(d)
    xty = zw.T @ yw
    phi = np.linalg.solve(xtx, xty)  # (D, C)
    return phi.T  # (C, D)


def modality_importance(phi: np.ndarray, slices: Dict[str, slice]) -> Dict[str, float]:
    """Eq. (modality importance): sum |phi| within each modality, L1-normalized."""
    abs_phi = np.abs(phi)
    if abs_phi.ndim == 2:
        abs_phi = abs_phi.mean(axis=0)
    totals = {m: float(abs_phi[sl].sum()) for m, sl in slices.items()}
    s = sum(totals.values()) + 1e-12
    return {m: 100.0 * v / s for m, v in totals.items()}


def feature_group_importance(phi: np.ndarray, groups: Dict[str, Sequence[int]]) -> Dict[str, float]:
    vec = np.abs(phi)
    if vec.ndim == 2:
        vec = vec.mean(0)
    out = {g: float(vec[list(idx)].mean()) for g, idx in groups.items()}
    return out


def shap_slices(audio_dim: int, video_dim: int, text_dim: int = 0) -> Dict[str, slice]:
    sl = {"audio": slice(0, audio_dim), "visual": slice(audio_dim, audio_dim + video_dim)}
    if text_dim:
        sl["textual"] = slice(audio_dim + video_dim, audio_dim + video_dim + text_dim)
    return sl


def bootstrap_modality_sd(
    phis: Sequence[np.ndarray],
    slices: Dict[str, slice],
    n_boot: int = 1000,
    seed: int = 0,
) -> Dict[str, float]:
    rng = np.random.default_rng(seed)
    arr = np.stack(phis, axis=0)
    recs = []
    n = arr.shape[0]
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        recs.append(modality_importance(arr[idx].mean(0), slices))
    keys = list(slices)
    return {k: float(np.std([r[k] for r in recs], ddof=1)) for k in keys}


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    if ra.std() == 0 or rb.std() == 0:
        return 1.0
    return float(np.corrcoef(ra, rb)[0, 1])
