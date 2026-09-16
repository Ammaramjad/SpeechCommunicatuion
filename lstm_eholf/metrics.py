"""Speaker-independent metrics used throughout the manuscript."""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np


def confusion_matrix(y_true: Sequence[int], y_pred: Sequence[int], n_classes: int) -> np.ndarray:
    cm = np.zeros((n_classes, n_classes), dtype=np.int64)
    for t, p in zip(y_true, y_pred):
        cm[int(t), int(p)] += 1
    return cm


def weighted_accuracy(y_true: Sequence[int], y_pred: Sequence[int]) -> float:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    if y_true.size == 0:
        return 0.0
    return float((y_true == y_pred).mean() * 100.0)


def unweighted_accuracy(y_true: Sequence[int], y_pred: Sequence[int], n_classes: int) -> float:
    cm = confusion_matrix(y_true, y_pred, n_classes)
    recalls = []
    for c in range(n_classes):
        tot = cm[c].sum()
        recalls.append(cm[c, c] / tot if tot else 0.0)
    return float(np.mean(recalls) * 100.0)


def precision_recall_f1(y_true: Sequence[int], y_pred: Sequence[int], n_classes: int) -> Dict[str, float]:
    cm = confusion_matrix(y_true, y_pred, n_classes)
    precs, recs, f1s = [], [], []
    for c in range(n_classes):
        tp = cm[c, c]
        fp = cm[:, c].sum() - tp
        fn = cm[c, :].sum() - tp
        p = tp / (tp + fp) if (tp + fp) else 0.0
        r = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) else 0.0
        precs.append(p)
        recs.append(r)
        f1s.append(f1)
    return {
        "precision": float(np.mean(precs) * 100.0),
        "recall": float(np.mean(recs) * 100.0),
        "macro_f1": float(np.mean(f1s) * 100.0),
    }


def _trapz(y: np.ndarray, x: np.ndarray) -> float:
    if hasattr(np, "trapezoid"):
        return float(np.trapezoid(y, x))
    return float(np.trapz(y, x))


def roc_auc_ovr(y_true: Sequence[int], proba: np.ndarray) -> Tuple[float, np.ndarray]:
    """Micro-average and per-class one-vs-rest AUC (trapezoid)."""
    y_true = np.asarray(y_true)
    n_classes = proba.shape[1]
    aucs = []
    for c in range(n_classes):
        y = (y_true == c).astype(np.float64)
        scores = proba[:, c]
        order = np.argsort(-scores)
        y = y[order]
        tps = np.cumsum(y)
        fps = np.cumsum(1.0 - y)
        if tps[-1] == 0 or fps[-1] == 0:
            aucs.append(0.5)
            continue
        tpr = np.r_[0.0, tps / tps[-1], 1.0]
        fpr = np.r_[0.0, fps / fps[-1], 1.0]
        aucs.append(float(_trapz(tpr, fpr)))
    # micro
    y_bin = np.eye(n_classes)[y_true]
    scores = proba.ravel()
    y = y_bin.ravel()
    order = np.argsort(-scores)
    y = y[order]
    tps = np.cumsum(y)
    fps = np.cumsum(1.0 - y)
    tpr = np.r_[0.0, tps / max(tps[-1], 1.0), 1.0]
    fpr = np.r_[0.0, fps / max(fps[-1], 1.0), 1.0]
    micro = float(_trapz(tpr, fpr))
    return micro, np.asarray(aucs)


def fold_std(values: Iterable[float]) -> Tuple[float, float]:
    arr = np.asarray(list(values), dtype=np.float64)
    if arr.size <= 1:
        return float(arr.mean() if arr.size else 0.0), 0.0
    return float(arr.mean()), float(arr.std(ddof=1))


def paired_ttest(a: Sequence[float], b: Sequence[float]) -> Dict[str, float]:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    d = a - b
    n = d.size
    mean = float(d.mean())
    sd = float(d.std(ddof=1)) if n > 1 else 0.0
    se = sd / np.sqrt(n) if n else 1.0
    t = mean / se if se else 0.0
    df = n - 1
    # two-sided p via regularized incomplete beta (no scipy required)
    p = _student_t_sf(abs(t), df) * 2.0
    dz = mean / sd if sd else 0.0
    return {"t": float(t), "df": float(df), "p": float(min(1.0, p)), "cohen_dz": float(dz), "mean_diff": mean}


def _student_t_sf(t: float, df: float) -> float:
    if df <= 0:
        return 1.0
    x = df / (df + t * t)
    # regularized incomplete beta I_x(df/2, 1/2) / 2 is the one-sided tail
    return 0.5 * _reg_inc_beta(x, df / 2.0, 0.5)


def _reg_inc_beta(x: float, a: float, b: float) -> float:
    """Continued-fraction regularized incomplete beta (sufficient for small df)."""
    x = min(max(x, 1e-12), 1 - 1e-12)
    ln_beta = _log_gamma(a) + _log_gamma(b) - _log_gamma(a + b)
    front = np.exp(a * np.log(x) + b * np.log(1 - x) - ln_beta)
    # Lentz CF for Ix
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > 1e-30 else 1e-30)
    f = d
    for m in range(1, 200):
        m2 = 2 * m
        num = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + num * d
        c = 1.0 + num / c
        d = 1.0 / (d if abs(d) > 1e-30 else 1e-30)
        f *= d * c
        num = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + num * d
        c = 1.0 + num / c
        d = 1.0 / (d if abs(d) > 1e-30 else 1e-30)
        delta = d * c
        f *= delta
        if abs(delta - 1.0) < 1e-8:
            break
    return front * f / a


def _log_gamma(z: float) -> float:
    import math

    return float(math.lgamma(z))


def holm_bonferroni(pvalues: Sequence[float]) -> List[float]:
    m = len(pvalues)
    order = np.argsort(pvalues)
    adj = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        val = (m - rank) * pvalues[idx]
        running = max(running, val)
        adj[idx] = min(1.0, running)
    return adj


def class_weights(labels: Sequence[int], n_classes: int) -> np.ndarray:
    counts = np.bincount(np.asarray(labels, dtype=int), minlength=n_classes).astype(np.float64)
    counts = np.maximum(counts, 1.0)
    w = 1.0 / counts
    w *= n_classes / w.sum()
    return w
