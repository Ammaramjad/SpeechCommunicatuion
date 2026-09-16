"""68-point landmarks: Procrustes alignment, scale-normalized geometric descriptors."""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

import numpy as np

# Dlib 68-point subsets
JAW = list(range(0, 17))
RIGHT_EYEBROW = list(range(17, 22))
LEFT_EYEBROW = list(range(22, 27))
NOSE = list(range(27, 36))
RIGHT_EYE = list(range(36, 42))
LEFT_EYE = list(range(42, 48))
OUTER_LIP = list(range(48, 60))
INNER_LIP = list(range(60, 68))
RIGID = [36, 45, 27, 8]  # outer eye corners, nose bridge, chin


def _procrustes(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    src = src - src.mean(axis=0, keepdims=True)
    dst_c = dst - dst.mean(axis=0, keepdims=True)
    n = np.linalg.norm(src)
    if n < 1e-8:
        return src + dst.mean(axis=0, keepdims=True)
    src = src / n
    dst_n = dst_c / (np.linalg.norm(dst_c) + 1e-8)
    u, _, vt = np.linalg.svd(src.T @ dst_n)
    r = vt.T @ u.T
    if np.linalg.det(r) < 0:
        vt[-1] *= -1
        r = vt.T @ u.T
    scale = np.trace((src @ r).T @ dst_n) * (np.linalg.norm(dst_c) / (n + 1e-8)) * n
    aligned = (src * n) @ r * (scale / (n + 1e-8) * n / n)
    # simpler: apply rotation and scale to centered src then translate
    aligned = src * n @ r
    aligned = aligned * (np.linalg.norm(dst_c) / (np.linalg.norm(aligned) + 1e-8))
    return aligned + dst.mean(axis=0, keepdims=True)


CANONICAL = np.stack(
    [
        np.linspace(-1.0, 1.0, 68),
        np.concatenate(
            [
                np.linspace(0.8, -0.2, 17),
                np.linspace(1.0, 1.0, 5),
                np.linspace(1.0, 1.0, 5),
                np.linspace(0.6, 0.0, 9),
                np.linspace(0.55, 0.55, 6),
                np.linspace(0.55, 0.55, 6),
                np.linspace(-0.2, -0.2, 12),
                np.linspace(-0.35, -0.35, 8),
            ]
        )[:68],
    ],
    axis=1,
).astype(np.float64)


def normalize_landmarks(points: np.ndarray, canonical: Optional[np.ndarray] = None) -> np.ndarray:
    """Similarity-align 68 landmarks to a canonical mean face using rigid points."""
    pts = np.asarray(points, dtype=np.float64).reshape(68, 2)
    dst = canonical if canonical is not None else CANONICAL
    src_r = pts[RIGID]
    dst_r = dst[RIGID]
    # estimate similarity from rigid subset and apply to all points
    mu_s = src_r.mean(axis=0)
    mu_d = dst_r.mean(axis=0)
    s = pts - mu_s
    d = dst_r - mu_d
    ss = src_r - mu_s
    n = np.linalg.norm(ss)
    if n < 1e-8:
        return pts
    u, _, vt = np.linalg.svd(ss.T @ d)
    r = u @ vt
    if np.linalg.det(r) < 0:
        u[:, -1] *= -1
        r = u @ vt
    scale = np.trace(ss @ r @ d.T) / (np.sum(ss ** 2) + 1e-8)
    return (pts - mu_s) @ r * scale + mu_d


def inter_ocular(points: np.ndarray) -> float:
    # outer eye corners: 36 and 45
    return float(np.linalg.norm(points[36] - points[45]) + 1e-8)


def _aperture(eye: np.ndarray) -> float:
    v = np.linalg.norm(eye[1] - eye[5]) + np.linalg.norm(eye[2] - eye[4])
    h = np.linalg.norm(eye[0] - eye[3]) + 1e-8
    return float(v / (2.0 * h))


def _eyebrow_curvature(brow: np.ndarray) -> float:
    chord = brow[-1] - brow[0]
    length = np.linalg.norm(chord) + 1e-8
    mid = (brow[0] + brow[-1]) / 2.0
    apex = brow[len(brow) // 2]
    # signed displacement from chord, plus angle
    disp = float(chord[0] * (apex - brow[0])[1] - chord[1] * (apex - brow[0])[0]) / length
    ang = np.arctan2(disp, length)
    return float(disp), float(ang)


def geometric_from_landmarks(
    points: np.ndarray,
    neutral_ref: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Return 8-D geometric vector used in SHAP (scale- and subject-normalized)."""
    pts = normalize_landmarks(points)
    iod = inter_ocular(pts)
    left_brow_disp, left_brow_ang = _eyebrow_curvature(pts[LEFT_EYEBROW])
    right_brow_disp, right_brow_ang = _eyebrow_curvature(pts[RIGHT_EYEBROW])
    lip_l, lip_r = pts[48], pts[54]
    mouth_h = np.linalg.norm(lip_l - lip_r) / iod
    mouth_v = np.linalg.norm(pts[51] - pts[57]) / iod
    eye_l = _aperture(pts[LEFT_EYE])
    eye_r = _aperture(pts[RIGHT_EYE])
    brow_disp = 0.5 * (left_brow_disp + right_brow_disp) / iod
    brow_ang = 0.5 * (left_brow_ang + right_brow_ang)
    feat = np.array(
        [brow_disp, brow_ang, mouth_h, mouth_v, eye_l, eye_r, (lip_l[1] - lip_r[1]) / iod, (pts[21, 1] - pts[22, 1]) / iod],
        dtype=np.float64,
    )
    if neutral_ref is not None:
        feat = feat - np.asarray(neutral_ref, dtype=np.float64)
    return feat.astype(np.float32)


def subject_neutral_baseline(frame_features: Sequence[np.ndarray]) -> np.ndarray:
    arr = np.stack([np.asarray(f) for f in frame_features], axis=0)
    return np.median(arr, axis=0).astype(np.float32)


def gaussian_blur_frames(frames: np.ndarray, sigma: float) -> np.ndarray:
    """Separable Gaussian blur on (T, H, W, C) or (T, C, H, W) float images."""
    if sigma <= 0:
        return frames
    x = np.asarray(frames, dtype=np.float32)
    radius = max(1, int(3 * sigma))
    t = np.arange(-radius, radius + 1)
    k = np.exp(-(t ** 2) / (2 * sigma ** 2))
    k /= k.sum()
    # apply along last two spatial dims
    if x.ndim != 4:
        raise ValueError("frames must be 4-D")
    if x.shape[1] in (1, 3) and x.shape[-1] not in (1, 3):
        # NCHW
        y = x
        for ax in (2, 3):
            y = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), ax, y)
        return y
    y = x
    for ax in (1, 2):
        y = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), ax, y)
    return y
