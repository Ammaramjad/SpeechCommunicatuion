"""Audio--video temporal alignment on the 10 ms audio grid (Section 3.3 / 3.4)."""

from __future__ import annotations

from typing import Literal, Optional, Tuple

import numpy as np


def piecewise_linear_resample(values: np.ndarray, src_t: np.ndarray, dst_t: np.ndarray) -> np.ndarray:
    """Interp each feature dimension of (T, D) from src_t onto dst_t."""
    values = np.asarray(values, dtype=np.float64)
    src_t = np.asarray(src_t, dtype=np.float64)
    dst_t = np.asarray(dst_t, dtype=np.float64)
    if values.ndim == 1:
        return np.interp(dst_t, src_t, values)
    out = np.empty((dst_t.shape[0], values.shape[1]), dtype=np.float64)
    for d in range(values.shape[1]):
        out[:, d] = np.interp(dst_t, src_t, values[:, d])
    return out


def nearest_resample(values: np.ndarray, src_t: np.ndarray, dst_t: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    src_t = np.asarray(src_t, dtype=np.float64)
    dst_t = np.asarray(dst_t, dtype=np.float64)
    idx = np.searchsorted(src_t, dst_t, side="left")
    idx = np.clip(idx, 0, len(src_t) - 1)
    # choose closer neighbour
    idx_l = np.clip(idx - 1, 0, len(src_t) - 1)
    choose_left = np.abs(src_t[idx_l] - dst_t) <= np.abs(src_t[idx] - dst_t)
    idx = np.where(choose_left, idx_l, idx)
    return values[idx]


def audio_timeline(n_audio_frames: int, hop_s: float = 0.010) -> np.ndarray:
    return np.arange(n_audio_frames, dtype=np.float64) * hop_s


def video_timeline(n_video_frames: int, fps: float = 30.0) -> np.ndarray:
    return np.arange(n_video_frames, dtype=np.float64) / fps


def align_audio_video(
    audio_frames: np.ndarray,
    video_frames: np.ndarray,
    *,
    hop_s: float = 0.010,
    fps: float = 30.0,
    method: Literal["linear", "nearest"] = "linear",
    video_offset_s: float = 0.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """Project video onto the 10 ms audio grid. Text is NOT interpolated.

    Returns aligned (audio, video) with the same T.
    """
    a = np.asarray(audio_frames, dtype=np.float64)
    v = np.asarray(video_frames, dtype=np.float64)
    if a.ndim == 1:
        a = a[:, None]
    if v.ndim == 1:
        v = v[:, None]
    t_a = audio_timeline(a.shape[0], hop_s)
    t_v = video_timeline(v.shape[0], fps) + video_offset_s
    fn = piecewise_linear_resample if method == "linear" else nearest_resample
    v_al = fn(v, t_v, t_a)
    return a.astype(np.float32), v_al.astype(np.float32)


def zscore_train_apply(
    train: np.ndarray, test: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mu = train.mean(axis=0)
    sd = train.std(axis=0)
    sd = np.where(sd < 1e-8, 1.0, sd)
    return (train - mu) / sd, (test - mu) / sd, mu, sd


def pool_utterance(aligned_audio: np.ndarray, aligned_video: np.ndarray) -> np.ndarray:
    """Mean and std pooling over the unified timeline, then concatenate A||V."""
    a = np.asarray(aligned_audio)
    v = np.asarray(aligned_video)
    a_pool = np.concatenate([a.mean(axis=0), a.std(axis=0)])
    v_pool = np.concatenate([v.mean(axis=0), v.std(axis=0)])
    return np.concatenate([a_pool, v_pool]).astype(np.float32)


def fuse_with_text(audio_visual_pool: np.ndarray, text_vec: Optional[np.ndarray]) -> np.ndarray:
    if text_vec is None:
        return np.asarray(audio_visual_pool, dtype=np.float32)
    return np.concatenate([audio_visual_pool, np.asarray(text_vec, dtype=np.float32)])


def shift_video(video_frames: np.ndarray, fps: float, offset_s: float) -> np.ndarray:
    """Circular-shift-free pad/crop approximating a playback delay of offset_s."""
    shift = int(round(offset_s * fps))
    if shift == 0:
        return video_frames
    v = np.asarray(video_frames)
    if shift > 0:
        pad = np.repeat(v[:1], shift, axis=0)
        return np.concatenate([pad, v], axis=0)[:-shift] if shift < len(v) else pad[: len(v)]
    shift = -shift
    pad = np.repeat(v[-1:], shift, axis=0)
    return np.concatenate([v[shift:], pad], axis=0)
